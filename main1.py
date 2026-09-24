import os
import csv
import logging
from pathlib import Path
from collections import defaultdict

import cv2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from ultralytics import YOLO
from dotenv import load_dotenv

from db import insert_challan, insert_detection
from services import make_challan_no, send_email, read_plate_from_frame
from privacy import blur_faces


load_dotenv()


MODEL_PATH = os.getenv("MODEL_PATH", "AdvHelmet.pt")
VIDEO_DIR = Path(os.getenv("VIDEO_DIR", "videos"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "results"))

CONFIDENCE = float(os.getenv("CONFIDENCE", "0.25"))
FINE_AMOUNT = float(os.getenv("FINE_AMOUNT", "500"))

VIDEO_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Report folder
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


logging.basicConfig(
    filename=OUTPUT_DIR / "audit.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# =========================================================
# HELMET CLASS HELPERS
# =========================================================

def norm(s):
    return (
        str(s)
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .strip()
    )


def no_helmet(s):
    n = norm(s)

    return (
        "no helmet" in n
        or "nohelmet" in n
        or "without helmet" in n
    )


def helmet(s):
    n = norm(s)

    return (
        "helmet" in n
        and not no_helmet(n)
    )


# =========================================================
# CONFIDENCE HEATMAP
# =========================================================

def generate_confidence_heatmap(csv_path, output_path):

    print(
        f"\nGenerating confidence heatmap..."
    )

    try:

        df = pd.read_csv(csv_path)

        if df.empty:

            print(
                "No detection data available for heatmap."
            )

            return

        # Convert values to numeric
        df["confidence"] = pd.to_numeric(
            df["confidence"],
            errors="coerce"
        )

        df["timestamp"] = pd.to_numeric(
            df["timestamp"],
            errors="coerce"
        )

        df = df.dropna(
            subset=[
                "confidence",
                "timestamp"
            ]
        )

        if df.empty:

            print(
                "No valid confidence data found."
            )

            return

        # -------------------------------------------------
        # Create 1-second time bins
        # -------------------------------------------------

        df["time_second"] = (
            df["timestamp"]
            .astype(float)
            .round()
            .astype(int)
        )

        # Average confidence per second
        confidence_by_time = (
            df.groupby("time_second")["confidence"]
            .mean()
        )

        if confidence_by_time.empty:

            print(
                "Could not calculate confidence timeline."
            )

            return

        # -------------------------------------------------
        # Create heatmap
        # -------------------------------------------------

        data = np.array(
            [confidence_by_time.values]
        )

        plt.figure(
            figsize=(14, 3)
        )

        plt.imshow(
            data,
            aspect="auto",
            cmap="RdYlGn",
            vmin=0,
            vmax=1
        )

        plt.colorbar(
            label="Confidence"
        )

        plt.yticks(
            [0],
            ["Model Confidence"]
        )

        # -------------------------------------------------
        # X-axis
        # -------------------------------------------------

        number_of_points = len(
            confidence_by_time
        )

        if number_of_points > 1:

            step = max(
                1,
                number_of_points // 10
            )

            tick_positions = np.arange(
                0,
                number_of_points,
                step
            )

            tick_labels = [
                f"{int(confidence_by_time.index[i])}s"
                for i in tick_positions
            ]

            plt.xticks(
                tick_positions,
                tick_labels
            )

        plt.xlabel(
            "Video Timeline"
        )

        plt.title(
            "YOLO Helmet Detection Confidence Heatmap"
        )

        plt.tight_layout()

        plt.savefig(
            output_path,
            dpi=200,
            bbox_inches="tight"
        )

        plt.close()

        print(
            f"Confidence heatmap created: {output_path}"
        )

    except Exception as e:

        print(
            "HEATMAP ERROR:",
            e
        )

        logging.error(
            "Heatmap error: %s",
            e
        )


# =========================================================
# PROCESS VIDEO
# =========================================================

def process_video(path, model, show_window=True):

    cap = cv2.VideoCapture(
        str(path)
    )

    if not cap.isOpened():

        print(
            f"Cannot open {path}"
        )

        return

    fps = (
        cap.get(cv2.CAP_PROP_FPS)
        or 25
    )

    w = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    h = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    out_path = (
        OUTPUT_DIR /
        f"{path.stem}_detected.mp4"
    )

    csv_path = (
        OUTPUT_DIR /
        f"{path.stem}_detections.csv"
    )

    # New heatmap output
    heatmap_path = (
        OUTPUT_DIR /
        f"{path.stem}_confidence_heatmap.png"
    )

    out = cv2.VideoWriter(
        str(out_path),
        cv2.VideoWriter_fourcc(
            *"mp4v"
        ),
        fps,
        (w, h)
    )

    cf = open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    )

    cw = csv.writer(cf)

    cw.writerow([
        "frame",
        "timestamp",
        "class",
        "confidence",
        "track_id",
        "x1",
        "y1",
        "x2",
        "y2"
    ])

    frame_no = 0

    # =====================================================
    # TRACK IDs THAT ALREADY GOT CHALLAN
    # =====================================================

    challaned_ids = set()

    challans = 0

    # =====================================================
    # CONFIDENCE TIMELINE
    # =====================================================

    confidence_timeline = []

    while True:

        ok, frame = cap.read()

        if not ok:
            break

        frame_no += 1

        ts = frame_no / fps

        # =================================================
        # YOLO TRACKING
        # =================================================

        try:

            result = model.track(
                frame,
                conf=CONFIDENCE,
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False
            )[0]

        except Exception:

            result = model.predict(
                frame,
                conf=CONFIDENCE,
                verbose=False
            )[0]

        helmets = []

        violations = []

        # Confidence values for this frame
        frame_confidences = []

        # =================================================
        # PROCESS DETECTIONS
        # =================================================

        if result.boxes is not None:

            for b in result.boxes:

                cid = int(
                    b.cls[0]
                    .cpu()
                    .numpy()
                )

                conf = float(
                    b.conf[0]
                    .cpu()
                    .numpy()
                )

                # Save confidence for this frame
                frame_confidences.append(
                    conf
                )

                name = str(
                    model.names[cid]
                )

                x1, y1, x2, y2 = (
                    b.xyxy[0]
                    .cpu()
                    .numpy()
                    .astype(int)
                )

                # Track ID
                tid = (
                    int(
                        b.id[0]
                        .cpu()
                        .numpy()
                    )
                    if b.id is not None
                    else None
                )

                # -----------------------------------------
                # Save EVERY detection to CSV
                # -----------------------------------------

                cw.writerow([
                    frame_no,
                    round(ts, 2),
                    name,
                    round(conf, 4),
                    tid,
                    x1,
                    y1,
                    x2,
                    y2
                ])

                # -----------------------------------------
                # Save detection to PostgreSQL
                # -----------------------------------------

                try:

                    insert_detection({

                        "video_name": path.name,

                        "frame_number": frame_no,

                        "timestamp_seconds": ts,

                        "class_name": name,

                        "confidence": conf,

                        "track_id": tid
                    })

                except Exception as e:

                    logging.error(
                        "Detection DB: %s",
                        e
                    )

                item = {

                    "confidence": conf,

                    "track_id": tid
                }

                if no_helmet(name):

                    violations.append(
                        item
                    )

                elif helmet(name):

                    helmets.append(
                        item
                    )

        # =================================================
        # CALCULATE FRAME CONFIDENCE
        # =================================================

        if frame_confidences:

            avg_confidence = (
                sum(frame_confidences)
                /
                len(frame_confidences)
            )

        else:

            avg_confidence = 0.0

        # Save confidence timeline
        confidence_timeline.append({

            "frame": frame_no,

            "timestamp": ts,

            "confidence": avg_confidence
        })

        # =================================================
        # SIGNAL
        # =================================================

        signal = (
            "RED"
            if violations
            else
            "GREEN"
        )

        # =================================================
        # CHALLAN LOGIC
        # =================================================

        if violations:

            # Highest confidence violation
            best = max(
                violations,
                key=lambda x: x["confidence"]
            )

            track_id = best["track_id"]

            should_create_challan = False

            # =================================================
            # ONE CHALLAN PER TRACK ID
            # =================================================

            if track_id is not None:

                if track_id not in challaned_ids:

                    should_create_challan = True

            else:

                # If tracking failed
                if "unknown" not in challaned_ids:

                    should_create_challan = True

                    track_id = "unknown"

            # =================================================
            # CREATE CHALLAN ONLY ONCE
            # =================================================

            if should_create_challan:

                plate = (
                    read_plate_from_frame(frame)
                    or "NOT_READ"
                )

                challan = make_challan_no()

                msg = (
                    "Traffic Violation\n"
                    "No Helmet Detected\n"
                    f"Vehicle: {plate}\n"
                    f"Fine: Rs.{int(FINE_AMOUNT)}\n"
                    f"Challan: {challan}\n"
                    "Educational simulation"
                )

                # =================================================
                # EMAIL
                # =================================================

                _, email_status = send_email(
                    msg
                )

                # =================================================
                # DATABASE
                # =================================================

                try:

                    insert_challan({

                        "challan_no": challan,

                        "video_name": path.name,

                        "frame_number": frame_no,

                        "timestamp_seconds": ts,

                        "vehicle_number": plate,

                        "violation": "NO_HELMET",

                        "fine_amount": FINE_AMOUNT,

                        "signal_status": "RED",

                        "confidence": best[
                            "confidence"
                        ],

                        "message_status": email_status,

                        "payment_status": "SIMULATED",

                        "notes": (
                            "Educational prototype; "
                            "no real money deducted."
                        )
                    })

                except Exception as e:

                    logging.error(
                        "Challan DB: %s",
                        e
                    )

                # =================================================
                # MARK TRACK AS CHALLANED
                # =================================================

                challaned_ids.add(
                    track_id
                )

                challans += 1

                print(
                    f"\n🚨 CHALLAN GENERATED"
                    f"\nVideo: {path.name}"
                    f"\nTrack ID: {track_id}"
                    f"\nFrame: {frame_no}"
                    f"\nFine: Rs.{int(FINE_AMOUNT)}"
                    f"\nChallan: {challan}"
                    f"\nEmail Status: {email_status}\n"
                )

        # =================================================
        # DRAW YOLO RESULT
        # =================================================

        annotated = result.plot()

        if os.getenv(
            "BLUR_FACES",
            "true"
        ).lower() in {
            "1",
            "true",
            "yes"
        }:

            annotated = blur_faces(
                annotated
            )

        # =================================================
        # TOP INFORMATION PANEL
        # =================================================

        cv2.rectangle(
            annotated,
            (0, 0),
            (w, 175),
            (30, 30, 30),
            -1
        )

        color = (
            (0, 0, 255)
            if signal == "RED"
            else
            (0, 200, 0)
        )

        # SIGNAL
        cv2.putText(
            annotated,
            f"SIGNAL: {signal}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            color,
            3
        )

        # HELMET COUNT
        cv2.putText(
            annotated,
            f"Helmet: {len(helmets)}   "
            f"No Helmet: {len(violations)}",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        # E-CHALLAN
        text = (
            f"E-CHALLAN: Rs.{int(FINE_AMOUNT)} | SIMULATED"
            if violations
            else
            "NO VIOLATION - GREEN LIGHT"
        )

        cv2.putText(
            annotated,
            text,
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (
                (0, 180, 255)
                if violations
                else
                (0, 220, 0)
            ),
            2
        )

        # =================================================
        # CONFIDENCE %
        # =================================================

        confidence_percent = int(
            avg_confidence * 100
        )

        cv2.putText(
            annotated,
            f"Confidence: {confidence_percent}%",
            (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (255, 255, 255),
            2
        )

        # =================================================
        # CONFIDENCE BAR
        # =================================================

        bar_x = 220

        bar_y = 118

        bar_width = min(
            400,
            max(100, w - 250)
        )

        bar_height = 22

        # Background
        cv2.rectangle(
            annotated,
            (bar_x, bar_y),
            (
                bar_x + bar_width,
                bar_y + bar_height
            ),
            (80, 80, 80),
            -1
        )

        filled_width = int(
            bar_width *
            avg_confidence
        )

        # Confidence color
        if avg_confidence >= 0.75:

            bar_color = (
                0,
                200,
                0
            )

        elif avg_confidence >= 0.50:

            bar_color = (
                0,
                200,
                255
            )

        else:

            bar_color = (
                0,
                0,
                255
            )

        cv2.rectangle(
            annotated,
            (bar_x, bar_y),
            (
                bar_x + filled_width,
                bar_y + bar_height
            ),
            bar_color,
            -1
        )

        # =================================================
        # CONFIDENCE TIMELINE
        # =================================================

        timeline_y = 155

        timeline_x = 220

        timeline_width = min(
            400,
            max(100, w - 250)
        )

        timeline_height = 10

        # Background
        cv2.rectangle(
            annotated,
            (
                timeline_x,
                timeline_y
            ),
            (
                timeline_x +
                timeline_width,
                timeline_y +
                timeline_height
            ),
            (70, 70, 70),
            -1
        )

        # Current position in video
        total_frames = int(
            cap.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        if total_frames > 0:

            progress = (
                frame_no /
                total_frames
            )

        else:

            progress = 0

        progress_x = int(
            timeline_width *
            progress
        )

        cv2.rectangle(
            annotated,
            (
                timeline_x,
                timeline_y
            ),
            (
                timeline_x +
                progress_x,
                timeline_y +
                timeline_height
            ),
            (255, 255, 255),
            -1
        )

        cv2.putText(
            annotated,
            "Timeline",
            (
                20,
                165
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (200, 200, 200),
            1
        )

        # =================================================
        # WRITE VIDEO
        # =================================================

        out.write(
            annotated
        )

        # =================================================
        # SHOW WINDOW
        # =================================================

        if show_window:

            cv2.imshow(
                "No Helmet - No Green Light",
                annotated
            )

            if (
                cv2.waitKey(1) & 0xFF
                == ord("q")
            ):

                break

    # =====================================================
    # RELEASE VIDEO
    # =====================================================

    cap.release()

    out.release()

    cf.close()

    if show_window:

        cv2.destroyAllWindows()

    # =====================================================
    # GENERATE CONFIDENCE HEATMAP
    # =====================================================

    generate_confidence_heatmap(
        csv_path,
        heatmap_path
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {

        "video": path.name,

        "output_video": str(
            out_path
        ),

        "detections_csv": str(
            csv_path
        ),

        "confidence_heatmap": str(
            heatmap_path
        ),

        "challans": challans
    }


# =========================================================
# GENERATE REPORT
# =========================================================

def generate_report():

    print(
        "\nGenerating report..."
    )

    csv_files = list(
        OUTPUT_DIR.glob(
            "*_detections.csv"
        )
    )

    all_rows = []

    for csv_file in csv_files:

        try:

            df = pd.read_csv(
                csv_file
            )

            if df.empty:

                continue

            # =================================================
            # TRACKED DETECTIONS
            # =================================================

            tracked_df = df[
                df["track_id"].notna()
            ].copy()

            unknown_df = df[
                df["track_id"].isna()
            ].copy()

            # =================================================
            # TRACKED PEOPLE
            # =================================================

            for track_id, group in tracked_df.groupby(
                "track_id"
            ):

                best_row = group.loc[
                    group[
                        "confidence"
                    ].idxmax()
                ]

                class_name = str(
                    best_row["class"]
                )

                # =================================================
                # NO HELMET
                # =================================================

                if no_helmet(
                    class_name
                ):

                    all_rows.append({

                        "video":
                            csv_file.stem.replace(
                                "_detections",
                                ""
                            ),

                        "track_id":
                            track_id,

                        "frame":
                            best_row["frame"],

                        "timestamp":
                            best_row["timestamp"],

                        "violation":
                            "NO_HELMET",

                        "confidence":
                            best_row["confidence"],

                        "fine_amount":
                            FINE_AMOUNT
                    })

                # =================================================
                # HELMET
                # =================================================

                elif helmet(
                    class_name
                ):

                    all_rows.append({

                        "video":
                            csv_file.stem.replace(
                                "_detections",
                                ""
                            ),

                        "track_id":
                            track_id,

                        "frame":
                            best_row["frame"],

                        "timestamp":
                            best_row["timestamp"],

                        "violation":
                            "HELMET",

                        "confidence":
                            best_row["confidence"],

                        "fine_amount":
                            0
                    })

            # =================================================
            # UNKNOWN DETECTIONS
            # =================================================

            if not unknown_df.empty:

                no_helmet_unknown = (
                    unknown_df[
                        unknown_df[
                            "class"
                        ].apply(
                            no_helmet
                        )
                    ]
                )

                if not no_helmet_unknown.empty:

                    best = no_helmet_unknown.loc[
                        no_helmet_unknown[
                            "confidence"
                        ].idxmax()
                    ]

                    all_rows.append({

                        "video":
                            csv_file.stem.replace(
                                "_detections",
                                ""
                            ),

                        "track_id":
                            "unknown",

                        "frame":
                            best["frame"],

                        "timestamp":
                            best["timestamp"],

                        "violation":
                            "NO_HELMET",

                        "confidence":
                            best["confidence"],

                        "fine_amount":
                            FINE_AMOUNT
                    })

        except Exception as e:

            logging.error(
                "Report error for %s: %s",
                csv_file,
                e
            )

    # =========================================================
    # CREATE DATAFRAME
    # =========================================================

    if all_rows:

        report_df = pd.DataFrame(
            all_rows
        )

    else:

        report_df = pd.DataFrame(
            columns=[
                "video",
                "track_id",
                "frame",
                "timestamp",
                "violation",
                "confidence",
                "fine_amount"
            ]
        )

    # =========================================================
    # EXPORT CSV
    # =========================================================

    report_csv = (
        REPORT_DIR /
        "challans_export.csv"
    )

    report_df.to_csv(
        report_csv,
        index=False
    )

    # =========================================================
    # STATISTICS
    # =========================================================

    total = len(
        report_df
    )

    no_helmet_count = int(
        report_df[
            "violation"
        ]
        .astype(str)
        .str.upper()
        .eq("NO_HELMET")
        .sum()
    )

    helmet_count = max(
        total -
        no_helmet_count,
        0
    )

    compliance = (
        round(
            100 *
            helmet_count /
            total,
            2
        )
        if total > 0
        else 0
    )

    total_fine = float(
        pd.to_numeric(
            report_df[
                "fine_amount"
            ],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    # =========================================================
    # HTML REPORT
    # =========================================================

    report_html = (
        REPORT_DIR /
        "traffic_summary.html"
    )

    table = (
        report_df.to_html(
            index=False
        )
        if not report_df.empty
        else
        "<p>No records.</p>"
    )

    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<title>Traffic Safety Report</title>

<style>

body {{
    font-family: Arial;
    margin: 40px;
    background: #f5f5f5;
}}

.card {{
    display: inline-block;
    background: white;
    padding: 20px;
    margin: 10px;
    border-radius: 10px;
    box-shadow: 0 2px 8px #ccc;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
}}

th, td {{
    padding: 10px;
    border: 1px solid #ddd;
}}

th {{
    background: #eee;
}}

</style>

</head>

<body>

<h1>🚦 AI Traffic Safety Report</h1>

<div class="card">
<h3>Total</h3>
<h2>{total}</h2>
</div>

<div class="card">
<h3>Helmet</h3>
<h2>{helmet_count}</h2>
</div>

<div class="card">
<h3>No Helmet</h3>
<h2>{no_helmet_count}</h2>
</div>

<div class="card">
<h3>Compliance</h3>
<h2>{compliance}%</h2>
</div>

<div class="card">
<h3>Total Fine</h3>
<h2>₹{total_fine:.2f}</h2>
</div>

<h2>Detection Records</h2>

{table}

</body>

</html>
"""

    report_html.write_text(
        html,
        encoding="utf-8"
    )

    # =========================================================
    # PRINT FINAL REPORT
    # =========================================================

    print(
        "\n================================"
    )

    print(
        "       REPORT GENERATED"
    )

    print(
        "================================"
    )

    print(
        f"Total:        {total}"
    )

    print(
        f"Helmet:       {helmet_count}"
    )

    print(
        f"No Helmet:    {no_helmet_count}"
    )

    print(
        f"Compliance:   {compliance}%"
    )

    print(
        f"Total Fine:   Rs.{total_fine:.2f}"
    )

    print(
        "================================"
    )

    print(
        f"CSV:  {report_csv}"
    )

    print(
        f"HTML: {report_html}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not Path(
        MODEL_PATH
    ).exists():

        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    videos = sorted(
        VIDEO_DIR.glob(
            "*.mp4"
        )
    )[:10]

    if not videos:

        raise FileNotFoundError(
            "Put MP4 videos inside videos folder."
        )

    model = YOLO(
        MODEL_PATH
    )

    print(
        "Model classes:",
        model.names
    )

    for v in videos:

        print(
            f"\nProcessing: {v.name}"
        )

        result = process_video(
            v,
            model,
            show_window=True
        )

        if result:

            print(
                f"\nVideo completed: {v.name}"
            )

            print(
                "Detected video:",
                result["output_video"]
            )

            print(
                "Detection CSV:",
                result["detections_csv"]
            )

            print(
                "Confidence heatmap:",
                result["confidence_heatmap"]
            )

            print(
                "Challans:",
                result["challans"]
            )

    # =====================================================
    # FINAL REPORT
    # =====================================================

    generate_report()

    print(
        "\nALL VIDEOS COMPLETED"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()