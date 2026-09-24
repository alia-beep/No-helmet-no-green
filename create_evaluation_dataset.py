import cv2
import csv
from pathlib import Path

VIDEO_DIR = Path("videos")
EVAL_DIR = Path("evaluation/frames")

FRAMES_PER_VIDEO = 20

EVAL_DIR.mkdir(parents=True, exist_ok=True)

csv_file = open(
    "evaluation/ground_truth.csv",
    "w",
    newline="",
    encoding="utf-8"
)

writer = csv.writer(csv_file)

writer.writerow([
    "video",
    "frame",
    "image",
    "actual",
    "predicted"
])

videos = list(VIDEO_DIR.glob("*.mp4"))[:10]

if not videos:
    print("No MP4 videos found!")
    exit()

for video_path in videos:

    print(f"\nProcessing: {video_path.name}")

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print("Cannot open:", video_path)
        continue

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames == 0:
        cap.release()
        continue

    step = max(1, total_frames // FRAMES_PER_VIDEO)

    for i in range(FRAMES_PER_VIDEO):

        frame_number = min(i * step, total_frames - 1)

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        success, frame = cap.read()

        if not success:
            continue

        image_name = (
            f"{video_path.stem}_frame_{frame_number}.jpg"
        )

        image_path = EVAL_DIR / image_name

        cv2.imwrite(str(image_path), frame)

        writer.writerow([
            video_path.name,
            frame_number,
            str(image_path),
            "",
            ""
        ])

    cap.release()

csv_file.close()

print("\n================================")
print("Evaluation dataset created!")
print("================================")
print(f"Videos processed: {len(videos)}")
print(f"Frames per video: {FRAMES_PER_VIDEO}")
print(f"Total possible samples: {len(videos) * FRAMES_PER_VIDEO}")

print("\nImages:")
print("evaluation/frames/")

print("\nCSV:")
print("evaluation/ground_truth.csv")