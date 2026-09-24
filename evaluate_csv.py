
from ultralytics import YOLO
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(r"D:\no_green_no_light")

MODEL_PATH = BASE_DIR / "AdvHelmet.pt"

CSV_PATH = BASE_DIR / "evaluation" / "ground_truth.csv"

# Folder containing the images referenced in ground_truth.csv
# CHANGE THIS ONLY IF YOUR IMAGES ARE STORED SOMEWHERE ELSE.
IMAGE_DIRS = [
    BASE_DIR / "evaluation" / "frames",
    BASE_DIR / "evaluation",
    BASE_DIR / "frames",
    BASE_DIR / "dataset" / "images" / "val",
]

# Detection settings
IMAGE_SIZE = 640
CONFIDENCE = 0.25
IOU = 0.45

# Your project only evaluates these two classes
TARGET_CLASSES = {
    0: "helmet",
    1: "no_helmet",
}


# ============================================================
# FIND IMAGE
# ============================================================

def find_image(image_name):
    """
    Search for an image in the configured directories.
    """

    image_name = Path(str(image_name).strip()).name

    for directory in IMAGE_DIRS:

        if not directory.exists():
            continue

        image_path = directory / image_name

        if image_path.exists():
            return image_path

    # Recursive search
    for directory in IMAGE_DIRS:

        if not directory.exists():
            continue

        matches = list(directory.rglob(image_name))

        if matches:
            return matches[0]

    return None


# ============================================================
# CONVERT YOLO PREDICTION TO PROJECT CLASS
# ============================================================

def get_prediction(result):
    """
    Convert YOLO detections into one final class:

        helmet
        no_helmet

    The model also contains class 2 = Only Helmet.

    For this evaluation:
        class 0 -> helmet
        class 1 -> no_helmet
        class 2 -> ignored

    If multiple detections exist, the highest-confidence
    helmet/no_helmet detection is used.
    """

    if result.boxes is None or len(result.boxes) == 0:
        return None, 0.0

    best_class = None
    best_conf = 0.0

    for cls, conf in zip(
        result.boxes.cls.cpu().numpy(),
        result.boxes.conf.cpu().numpy()
    ):

        cls = int(cls)
        conf = float(conf)

        # Ignore "Only Helmet"
        if cls not in TARGET_CLASSES:
            continue

        if conf > best_conf:
            best_conf = conf
            best_class = TARGET_CLASSES[cls]

    return best_class, best_conf


# ============================================================
# NORMALIZE GROUND TRUTH
# ============================================================

def normalize_label(label):
    """
    Convert different possible spellings into:

        helmet
        no_helmet
    """

    label = str(label).strip().lower()

    label = label.replace(" ", "_")
    label = label.replace("-", "_")

    if label in [
        "helmet",
        "with_helmet",
        "wearing_helmet",
    ]:
        return "helmet"

    if label in [
        "no_helmet",
        "nohelmet",
        "without_helmet",
        "not_wearing_helmet",
    ]:
        return "no_helmet"

    return None


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("        ADVHELMET CSV-BASED EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    if not MODEL_PATH.exists():
        print("\nERROR: Model not found:")
        print(MODEL_PATH)
        return

    if not CSV_PATH.exists():
        print("\nERROR: CSV not found:")
        print(CSV_PATH)
        return

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print("\nLoading model...")
    print(MODEL_PATH)

    model = YOLO(str(MODEL_PATH))

    print("\nModel classes:")
    for class_id, class_name in model.names.items():
        print(f"  {class_id}: {class_name}")

    # --------------------------------------------------------
    # Load CSV
    # --------------------------------------------------------

    print("\nLoading ground-truth CSV...")
    print(CSV_PATH)

    df = pd.read_csv(CSV_PATH)

    print("\nCSV columns:")
    print(list(df.columns))

    print(f"\nTotal CSV rows: {len(df)}")

    # --------------------------------------------------------
    # Detect CSV columns
    # --------------------------------------------------------

    image_column = None
    label_column = None

    possible_image_columns = [
        "image",
        "image_name",
        "filename",
        "file",
        "frame",
        "image_path",
    ]

    possible_label_columns = [
        "ground_truth",
        "label",
        "class",
        "actual",
        "groundtruth",
    ]

    for column in possible_image_columns:

        if column in df.columns:
            image_column = column
            break

    for column in possible_label_columns:

        if column in df.columns:
            label_column = column
            break

    if image_column is None:

        print("\nERROR: Could not find image column.")

        print("Expected one of:")
        print(possible_image_columns)

        print("\nYour CSV columns are:")
        print(list(df.columns))

        return

    if label_column is None:

        print("\nERROR: Could not find ground-truth label column.")

        print("Expected one of:")
        print(possible_label_columns)

        print("\nYour CSV columns are:")
        print(list(df.columns))

        return

    print(f"\nImage column     : {image_column}")
    print(f"Ground truth     : {label_column}")

    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    results = []

    total = len(df)

    print("\n")
    print("=" * 70)
    print("                    RUNNING EVALUATION")
    print("=" * 70)

    for index, row in df.iterrows():

        image_name = row[image_column]
        ground_truth_raw = row[label_column]

        ground_truth = normalize_label(ground_truth_raw)

        image_path = find_image(image_name)

        # ----------------------------------------------------
        # Invalid ground truth
        # ----------------------------------------------------

        if ground_truth is None:

            results.append({
                "image": image_name,
                "ground_truth": ground_truth_raw,
                "prediction": "",
                "confidence": 0,
                "correct": False,
                "status": "invalid_ground_truth"
            })

            continue

        # ----------------------------------------------------
        # Missing image
        # ----------------------------------------------------

        if image_path is None:

            print(
                f"[{index + 1}/{total}] "
                f"{image_name} -> IMAGE NOT FOUND"
            )

            results.append({
                "image": image_name,
                "ground_truth": ground_truth,
                "prediction": "",
                "confidence": 0,
                "correct": False,
                "status": "image_not_found"
            })

            continue

        # ----------------------------------------------------
        # Run YOLO
        # ----------------------------------------------------

        try:

            prediction_results = model.predict(
                source=str(image_path),
                imgsz=IMAGE_SIZE,
                conf=CONFIDENCE,
                iou=IOU,
                verbose=False
            )

            prediction, confidence = get_prediction(
                prediction_results[0]
            )

        except Exception as e:

            print(
                f"[{index + 1}/{total}] "
                f"{image_name} -> ERROR: {e}"
            )

            results.append({
                "image": image_name,
                "ground_truth": ground_truth,
                "prediction": "",
                "confidence": 0,
                "correct": False,
                "status": "prediction_error"
            })

            continue

        # ----------------------------------------------------
        # Handle no detection
        # ----------------------------------------------------

        if prediction is None:

            print(
                f"[{index + 1}/{total}] "
                f"{image_name} -> "
                f"GT: {ground_truth} | "
                f"Prediction: NO DETECTION"
            )

            results.append({
                "image": image_name,
                "ground_truth": ground_truth,
                "prediction": "no_detection",
                "confidence": 0,
                "correct": False,
                "status": "no_detection"
            })

            continue

        # ----------------------------------------------------
        # Compare
        # ----------------------------------------------------

        correct = prediction == ground_truth

        print(
            f"[{index + 1}/{total}] "
            f"{image_name} -> "
            f"GT: {ground_truth} | "
            f"Pred: {prediction} | "
            f"Conf: {confidence:.3f} | "
            f"{'CORRECT' if correct else 'WRONG'}"
        )

        results.append({
            "image": image_name,
            "ground_truth": ground_truth,
            "prediction": prediction,
            "confidence": confidence,
            "correct": correct,
            "status": "evaluated"
        })

    # --------------------------------------------------------
    # Convert results to DataFrame
    # --------------------------------------------------------

    results_df = pd.DataFrame(results)

    # Save detailed results
    output_csv = BASE_DIR / "evaluation" / "evaluation_results.csv"

    results_df.to_csv(
        output_csv,
        index=False
    )

    # --------------------------------------------------------
    # Keep only successfully evaluated images
    # --------------------------------------------------------

    evaluated = results_df[
        results_df["status"] == "evaluated"
    ].copy()

    if len(evaluated) == 0:

        print("\nERROR: No images were successfully evaluated.")
        print("Check your image directory configuration.")

        return

    y_true = evaluated["ground_truth"]
    y_pred = evaluated["prediction"]

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision = precision_score(
        y_true,
        y_pred,
        labels=["helmet", "no_helmet"],
        average="weighted",
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        labels=["helmet", "no_helmet"],
        average="weighted",
        zero_division=0
    )

    f1 = f1_score(
        y_true,
        y_pred,
        labels=["helmet", "no_helmet"],
        average="weighted",
        zero_division=0
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=["helmet", "no_helmet"]
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    correct_count = int(
        (y_true == y_pred).sum()
    )

    wrong_count = len(evaluated) - correct_count

    no_detection_count = int(
        (results_df["status"] == "no_detection").sum()
    )

    missing_count = int(
        (results_df["status"] == "image_not_found").sum()
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print("\n\n")
    print("=" * 70)
    print("                    FINAL RESULTS")
    print("=" * 70)

    print(f"\nTotal CSV samples       : {total}")
    print(f"Successfully evaluated  : {len(evaluated)}")
    print(f"Correct predictions     : {correct_count}")
    print(f"Wrong predictions       : {wrong_count}")
    print(f"No detection            : {no_detection_count}")
    print(f"Missing images          : {missing_count}")

    print("\n" + "-" * 70)

    print(
        f"Accuracy                : "
        f"{accuracy:.4f} ({accuracy * 100:.2f}%)"
    )

    print(
        f"Precision               : "
        f"{precision:.4f} ({precision * 100:.2f}%)"
    )

    print(
        f"Recall                  : "
        f"{recall:.4f} ({recall * 100:.2f}%)"
    )

    print(
        f"F1 Score                : "
        f"{f1:.4f} ({f1 * 100:.2f}%)"
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("                    CONFUSION MATRIX")
    print("=" * 70)

    print("\n                 Predicted")
    print("              Helmet  No Helmet")
    print(
        f"Actual Helmet    {cm[0][0]:4d}      {cm[0][1]:4d}"
    )
    print(
        f"Actual NoHelmet  {cm[1][0]:4d}      {cm[1][1]:4d}"
    )

    # --------------------------------------------------------
    # Per-class report
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("                    CLASSIFICATION REPORT")
    print("=" * 70)

    report = classification_report(
        y_true,
        y_pred,
        labels=["helmet", "no_helmet"],
        target_names=["Helmet", "No Helmet"],
        zero_division=0
    )

    print("\n" + report)

    # --------------------------------------------------------
    # Save confusion matrix
    # --------------------------------------------------------

    cm_df = pd.DataFrame(
        cm,
        index=["Actual Helmet", "Actual No Helmet"],
        columns=["Predicted Helmet", "Predicted No Helmet"]
    )

    cm_path = BASE_DIR / "evaluation" / "confusion_matrix.csv"

    cm_df.to_csv(cm_path)

    # --------------------------------------------------------
    # Save summary
    # --------------------------------------------------------

    summary = pd.DataFrame({
        "Metric": [
            "Total Samples",
            "Successfully Evaluated",
            "Correct Predictions",
            "Wrong Predictions",
            "No Detection",
            "Missing Images",
            "Accuracy",
            "Precision",
            "Recall",
            "F1 Score"
        ],
        "Value": [
            total,
            len(evaluated),
            correct_count,
            wrong_count,
            no_detection_count,
            missing_count,
            accuracy,
            precision,
            recall,
            f1
        ]
    })

    summary_path = BASE_DIR / "evaluation" / "evaluation_summary.csv"

    summary.to_csv(
        summary_path,
        index=False
    )

    # --------------------------------------------------------
    # Finished
    # --------------------------------------------------------

    print("=" * 70)
    print("                    EVALUATION COMPLETE")
    print("=" * 70)

    print("\nFiles generated:")

    print(f"\nDetailed results:")
    print(output_csv)

    print(f"\nConfusion matrix:")
    print(cm_path)

    print(f"\nSummary:")
    print(summary_path)

    print("\n")


# ============================================================
# WINDOWS ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()

