from pathlib import Path
from ultralytics import YOLO
import cv2


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "AdvHelmet.pt"

DATASET_DIR = Path("dataset")

# Minimum confidence
CONFIDENCE = 0.70

# Your AdvHelmet.pt classes
MODEL_CLASSES = {
    0: "Helmet",
    1: "No Helmet",
    2: "Only Helmet"
}

# Classes that we want to keep
# Final dataset:
# 0 = helmet
# 1 = no_helmet

CLASS_MAPPING = {
    0: 0,   # Helmet -> helmet
    1: 1    # No Helmet -> no_helmet
}


# ============================================================
# FIND IMAGES
# ============================================================

def get_images(image_dir):

    images = []

    for extension in [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.JPG",
        "*.JPEG",
        "*.PNG"
    ]:

        images.extend(
            image_dir.glob(extension)
        )

    return sorted(images)


# ============================================================
# PROCESS SPLIT
# ============================================================

def process_split(model, split):

    image_dir = (
        DATASET_DIR
        / "images"
        / split
    )

    label_dir = (
        DATASET_DIR
        / "labels"
        / split
    )

    label_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    images = get_images(
        image_dir
    )

    print()
    print("=" * 60)
    print(f"PROCESSING {split.upper()}")
    print("=" * 60)

    print(
        f"Images found: {len(images)}"
    )

    total_images = len(images)

    labeled_images = 0
    no_detection = 0
    ignored_only_helmet = 0
    total_boxes = 0

    for index, image_path in enumerate(
        images,
        start=1
    ):

        print(
            f"[{index}/{total_images}] "
            f"{image_path.name}"
        )

        image = cv2.imread(
            str(image_path)
        )

        if image is None:

            print(
                "WARNING: Cannot read image"
            )

            continue

        height, width = image.shape[:2]

        # ----------------------------------------------------
        # YOLO PREDICTION
        # ----------------------------------------------------

        results = model.predict(
            source=str(image_path),
            conf=CONFIDENCE,
            verbose=False
        )

        result = results[0]

        if result.boxes is None:

            no_detection += 1
            continue

        lines = []

        # ----------------------------------------------------
        # PROCESS DETECTIONS
        # ----------------------------------------------------

        for box in result.boxes:

            model_class = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )

            # ------------------------------------------------
            # IGNORE CLASS 2
            # ------------------------------------------------

            if model_class == 2:

                ignored_only_helmet += 1

                continue

            # ------------------------------------------------
            # IGNORE UNKNOWN CLASS
            # ------------------------------------------------

            if model_class not in CLASS_MAPPING:

                continue

            final_class = CLASS_MAPPING[
                model_class
            ]

            # ------------------------------------------------
            # BOUNDING BOX
            # ------------------------------------------------

            x1, y1, x2, y2 = (
                box.xyxy[0].tolist()
            )

            # ------------------------------------------------
            # CONVERT TO YOLO FORMAT
            # ------------------------------------------------

            center_x = (
                (x1 + x2) / 2
            ) / width

            center_y = (
                (y1 + y2) / 2
            ) / height

            box_width = (
                x2 - x1
            ) / width

            box_height = (
                y2 - y1
            ) / height

            # ------------------------------------------------
            # SAVE LINE
            # ------------------------------------------------

            line = (
                f"{final_class} "
                f"{center_x:.6f} "
                f"{center_y:.6f} "
                f"{box_width:.6f} "
                f"{box_height:.6f}"
            )

            lines.append(line)

            total_boxes += 1

        # ----------------------------------------------------
        # NO VALID DETECTION
        # ----------------------------------------------------

        if len(lines) == 0:

            no_detection += 1

            continue

        # ----------------------------------------------------
        # SAVE YOLO TXT
        # ----------------------------------------------------

        label_path = (
            label_dir
            / f"{image_path.stem}.txt"
        )

        label_path.write_text(
            "\n".join(lines),
            encoding="utf-8"
        )

        labeled_images += 1

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("-" * 60)
    print(f"{split.upper()} SUMMARY")
    print("-" * 60)

    print(
        f"Total images          : {total_images}"
    )

    print(
        f"Labeled images        : {labeled_images}"
    )

    print(
        f"No valid detection    : {no_detection}"
    )

    print(
        f"Ignored 'Only Helmet' : {ignored_only_helmet}"
    )

    print(
        f"Total boxes           : {total_boxes}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("AUTOMATIC HELMET YOLO LABELING")
    print("=" * 60)

    print()
    print(
        f"Loading model: {MODEL_PATH}"
    )

    model = YOLO(
        MODEL_PATH
    )

    print()
    print(
        "MODEL CLASSES:"
    )

    print(
        model.names
    )

    print()
    print(
        "Using:"
    )

    print(
        "0 = Helmet"
    )

    print(
        "1 = No Helmet"
    )

    print(
        "2 = Only Helmet → IGNORED"
    )

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    process_split(
        model,
        "train"
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    process_split(
        model,
        "val"
    )

    # --------------------------------------------------------
    # TEST
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("TEST SET")
    print("=" * 60)

    print(
        "Test images are NOT automatically "
        "labeled because their labels should "
        "be independent ground truth."
    )

    print()
    print("=" * 60)
    print("COMPLETED")
    print("=" * 60)

    print()
    print(
        "Generated labels:"
    )

    print(
        "dataset/labels/train/"
    )

    print(
        "dataset/labels/val/"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Review the automatically generated "
        "labels before training."
    )


if __name__ == "__main__":
    main()