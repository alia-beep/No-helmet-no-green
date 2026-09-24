from pathlib import Path
import csv
from ultralytics import YOLO

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = Path("AdvHelmet.pt")

CSV_PATH = Path("evaluation/ground_truth.csv")

FRAMES_DIR = Path("evaluation/frames")

CONFIDENCE_THRESHOLD = 0.25


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_class_name(name):
    """
    Converts the model class name into one of our two
    standard labels:

        helmet
        no_helmet
    """

    name = str(name).lower().strip()

    # Remove spaces, hyphens and underscores
    normalized = (
        name
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )

    # Possible names for NO HELMET
    if normalized in [
        "nohelmet",
        "withouthelmet",
        "helmetless",
        "notwearinghelmet"
    ]:
        return "no_helmet"

    # Possible names for HELMET
    if normalized in [
        "helmet",
        "withhelmet"
    ]:
        return "helmet"

    return None


def predict_image(model, image_path):
    """
    Runs YOLO prediction on one image.

    Returns:
        helmet
        no_helmet
        None
    """

    results = model.predict(
        source=str(image_path),
        conf=CONFIDENCE_THRESHOLD,
        verbose=False
    )

    if not results:
        return None

    result = results[0]

    if result.boxes is None or len(result.boxes) == 0:
        return None

    predictions = []

    for box in result.boxes:

        confidence = float(box.conf[0].cpu().numpy())

        class_id = int(box.cls[0].cpu().numpy())

        class_name = model.names[class_id]

        normalized = normalize_class_name(class_name)

        if normalized is not None:
            predictions.append(
                (confidence, normalized)
            )

    if not predictions:
        return None

    # Select the detection having the highest confidence
    predictions.sort(
        key=lambda x: x[0],
        reverse=True
    )

    best_confidence, best_prediction = predictions[0]

    return best_prediction


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("=" * 60)
    print("YOLO EVALUATION PREDICTION")
    print("=" * 60)

    # --------------------------------------------------------
    # Check model
    # --------------------------------------------------------

    if not MODEL_PATH.exists():

        print()
        print("ERROR: AdvHelmet.pt was not found.")
        print()
        print("Expected location:")
        print(MODEL_PATH.resolve())

        return

    # --------------------------------------------------------
    # Check CSV
    # --------------------------------------------------------

    if not CSV_PATH.exists():

        print()
        print("ERROR: ground_truth.csv was not found.")
        print()
        print("Expected location:")
        print(CSV_PATH.resolve())

        return

    # --------------------------------------------------------
    # Check frames folder
    # --------------------------------------------------------

    if not FRAMES_DIR.exists():

        print()
        print("ERROR: evaluation/frames folder was not found.")
        print()
        print(FRAMES_DIR.resolve())

        return

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print()
    print("Loading YOLO model...")

    model = YOLO(str(MODEL_PATH))

    print("Model loaded successfully.")

    print()
    print("Model classes:")

    for class_id, class_name in model.names.items():
        print(f"  {class_id}: {class_name}")

    # --------------------------------------------------------
    # Read CSV
    # --------------------------------------------------------

    print()
    print("Reading ground_truth.csv...")

    with open(
        CSV_PATH,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        rows = list(reader)

        fieldnames = reader.fieldnames

    if not fieldnames:

        print("ERROR: CSV has no columns.")
        return

    required_columns = [
        "video",
        "frame",
        "image",
        "actual",
        "predicted"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in fieldnames
    ]

    if missing_columns:

        print()
        print("ERROR: Missing CSV columns:")
        print(missing_columns)

        print()
        print("Your CSV should contain:")
        print(required_columns)

        return

    # --------------------------------------------------------
    # Prediction counters
    # --------------------------------------------------------

    total = len(rows)

    processed = 0

    successful_predictions = 0

    no_detection = 0

    unknown_predictions = 0

    # --------------------------------------------------------
    # Process every image
    # --------------------------------------------------------

    print()
    print(f"Total evaluation samples: {total}")
    print()
    print("Starting prediction...")
    print("-" * 60)

    for index, row in enumerate(rows, start=1):

        image_path = Path(row["image"])

        # ----------------------------------------------------
        # Handle different image paths
        # ----------------------------------------------------

        if not image_path.exists():

            # Try only the filename inside evaluation/frames
            alternative_path = (
                FRAMES_DIR / image_path.name
            )

            if alternative_path.exists():

                image_path = alternative_path

            else:

                print(
                    f"[{index}/{total}] "
                    f"IMAGE NOT FOUND: {row['image']}"
                )

                row["predicted"] = "unknown"

                unknown_predictions += 1

                continue

        processed += 1

        # ----------------------------------------------------
        # Run prediction
        # ----------------------------------------------------

        prediction = predict_image(
            model,
            image_path
        )

        if prediction is None:

            row["predicted"] = "no_detection"

            no_detection += 1

            print(
                f"[{index}/{total}] "
                f"{image_path.name} "
                f"-> NO DETECTION"
            )

        else:

            row["predicted"] = prediction

            successful_predictions += 1

            print(
                f"[{index}/{total}] "
                f"{image_path.name} "
                f"-> {prediction}"
            )

    # --------------------------------------------------------
    # Save updated CSV
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("Saving predictions...")

    with open(
        CSV_PATH,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(rows)

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PREDICTION COMPLETED")
    print("=" * 60)

    print(f"Total samples          : {total}")
    print(f"Images processed       : {processed}")
    print(f"Successful predictions : {successful_predictions}")
    print(f"No detection           : {no_detection}")
    print(f"Unknown/missing images : {unknown_predictions}")

    print()
    print("Updated CSV:")
    print(CSV_PATH.resolve())

    


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()