from pathlib import Path
import cv2


VIDEOS_DIR = Path("videos")
DATASET_DIR = Path("dataset")

# Save every 10th frame
FRAME_INTERVAL = 10


def create_folders():

    folders = [
        DATASET_DIR / "images" / "train",
        DATASET_DIR / "images" / "val",
        DATASET_DIR / "images" / "test",

        DATASET_DIR / "labels" / "train",
        DATASET_DIR / "labels" / "val",
        DATASET_DIR / "labels" / "test",
    ]

    for folder in folders:
        folder.mkdir(
            parents=True,
            exist_ok=True
        )


def find_videos():

    extensions = [
        "*.mp4",
        "*.avi",
        "*.mov",
        "*.mkv",
        "*.MP4",
        "*.AVI",
        "*.MOV",
        "*.MKV"
    ]

    videos = []

    for extension in extensions:
        videos.extend(
            VIDEOS_DIR.glob(extension)
        )

    return sorted(videos)


def extract_video(video_path, split):

    output_dir = (
        DATASET_DIR
        / "images"
        / split
    )

    video_name = video_path.stem

    cap = cv2.VideoCapture(
        str(video_path)
    )

    if not cap.isOpened():

        print(
            f"ERROR: Cannot open "
            f"{video_path.name}"
        )

        return 0

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    print()
    print("-" * 60)
    print(f"Video       : {video_path.name}")
    print(f"Split       : {split}")
    print(f"Total frames: {total_frames}")
    print(f"FPS         : {fps:.2f}")
    print("-" * 60)

    frame_number = 0
    saved_frames = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        if frame_number % FRAME_INTERVAL == 0:

            filename = (
                f"{video_name}_"
                f"frame_{frame_number:06d}.jpg"
            )

            output_path = (
                output_dir / filename
            )

            cv2.imwrite(
                str(output_path),
                frame
            )

            saved_frames += 1

        frame_number += 1

        if frame_number % 500 == 0:

            print(
                f"Processed "
                f"{frame_number}/"
                f"{total_frames}"
            )

    cap.release()

    print(
        f"Saved {saved_frames} frames"
    )

    return saved_frames


def create_yaml():

    yaml_content = """path: ./dataset

train: images/train
val: images/val
test: images/test

names:
  0: helmet
  1: no_helmet
"""

    Path("data.yaml").write_text(
        yaml_content,
        encoding="utf-8"
    )


def main():

    print("=" * 60)
    print("NO HELMET - AUTOMATIC DATASET PREPARATION")
    print("=" * 60)

    if not VIDEOS_DIR.exists():

        print()
        print(
            "ERROR: videos folder not found:"
        )

        print(
            VIDEOS_DIR.resolve()
        )

        return

    create_folders()

    videos = find_videos()

    print()
    print(
        f"Found {len(videos)} video(s)"
    )

    if len(videos) == 0:

        print()
        print(
            "No videos found."
        )

        print(
            "Put your .mp4/.avi/.mov/.mkv "
            "files inside:"
        )

        print(
            VIDEOS_DIR.resolve()
        )

        return

    if len(videos) < 3:

        print()
        print(
            "ERROR: At least 3 videos "
            "are recommended."
        )

        return

    # --------------------------------------------------------
    # AUTOMATIC VIDEO SPLIT
    # --------------------------------------------------------

    total = len(videos)

    train_count = round(
        total * 0.70
    )

    val_count = round(
        total * 0.10
    )

    # Make sure at least one test video exists
    if train_count + val_count >= total:
        val_count = 1

    train_videos = videos[
        :train_count
    ]

    val_videos = videos[
        train_count:
        train_count + val_count
    ]

    test_videos = videos[
        train_count + val_count:
    ]

    print()
    print("=" * 60)
    print("VIDEO SPLIT")
    print("=" * 60)

    print()
    print("TRAIN:")

    for video in train_videos:
        print(
            f"  {video.name}"
        )

    print()
    print("VALIDATION:")

    for video in val_videos:
        print(
            f"  {video.name}"
        )

    print()
    print("TEST:")

    for video in test_videos:
        print(
            f"  {video.name}"
        )

    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    train_frames = 0
    val_frames = 0
    test_frames = 0

    print()
    print("=" * 60)
    print("EXTRACTING TRAIN FRAMES")
    print("=" * 60)

    for video in train_videos:

        train_frames += extract_video(
            video,
            "train"
        )

    print()
    print("=" * 60)
    print("EXTRACTING VALIDATION FRAMES")
    print("=" * 60)

    for video in val_videos:

        val_frames += extract_video(
            video,
            "val"
        )

    print()
    print("=" * 60)
    print("EXTRACTING TEST FRAMES")
    print("=" * 60)

    for video in test_videos:

        test_frames += extract_video(
            video,
            "test"
        )

    create_yaml()

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("DATASET PREPARATION COMPLETED")
    print("=" * 60)

    print(
        f"Training frames   : {train_frames}"
    )

    print(
        f"Validation frames : {val_frames}"
    )

    print(
        f"Testing frames    : {test_frames}"
    )

    print(
        f"Total frames      : "
        f"{train_frames + val_frames + test_frames}"
    )

    print()
    print("Created:")

    print(
        "dataset/images/train/"
    )

    print(
        "dataset/images/val/"
    )

    print(
        "dataset/images/test/"
    )

    print()
    print(
        "Next step:"
    )

    print(
        "Annotate the extracted images "
        "with helmet/no_helmet bounding boxes."
    )


if __name__ == "__main__":
    main()