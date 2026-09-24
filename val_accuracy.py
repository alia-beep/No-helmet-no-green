
from ultralytics import YOLO
import os


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = r"D:\no_green_no_light\AdvHelmet.pt"

# IMPORTANT:
# Change this to your dataset YAML file.
#
# Example:
# D:\no_green_no_light\dataset\data.yaml
#
DATA_YAML = r"D:\no_green_no_light\dataset\data.yaml"

IMAGE_SIZE = 640
BATCH_SIZE = 8
CONFIDENCE = 0.001
IOU = 0.6


# ============================================================
# VALIDATION
# ============================================================

def main():

    print("=" * 60)
    print("       ADVHELMET MODEL VALIDATION")
    print("=" * 60)

    # Check model
    if not os.path.exists(MODEL_PATH):
        print(f"\nERROR: Model not found:")
        print(MODEL_PATH)
        return

    # Check dataset YAML
    if not os.path.exists(DATA_YAML):
        print(f"\nERROR: Dataset YAML not found:")
        print(DATA_YAML)
        print("\nPlease change DATA_YAML at the top of this file.")
        return

    print(f"\nModel  : {MODEL_PATH}")
    print(f"Dataset: {DATA_YAML}")

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print("\nLoading AdvHelmet.pt...")

    model = YOLO(MODEL_PATH)

    print("Model loaded successfully.")

    # Show classes
    print("\nModel Classes:")
    for class_id, class_name in model.names.items():
        print(f"  {class_id}: {class_name}")

    # --------------------------------------------------------
    # Run validation
    # --------------------------------------------------------

    print("\nStarting validation...")
    print("-" * 60)

    metrics = model.val(
        data=DATA_YAML,
        imgsz=IMAGE_SIZE,
        batch=BATCH_SIZE,
        conf=CONFIDENCE,
        iou=IOU,
        plots=True,
        verbose=True
    )

    # --------------------------------------------------------
    # Extract metrics
    # --------------------------------------------------------

    precision = metrics.box.mp
    recall = metrics.box.mr
    map50 = metrics.box.map50
    map50_95 = metrics.box.map

    # F1 = 2 * Precision * Recall / (Precision + Recall)
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("             FINAL MODEL RESULTS")
    print("=" * 60)

    print(f"\nPrecision       : {precision:.4f}  ({precision * 100:.2f}%)")
    print(f"Recall          : {recall:.4f}  ({recall * 100:.2f}%)")
    print(f"mAP@50          : {map50:.4f}  ({map50 * 100:.2f}%)")
    print(f"mAP@50-95       : {map50_95:.4f}  ({map50_95 * 100:.2f}%)")
    print(f"F1 Score        : {f1:.4f}  ({f1 * 100:.2f}%)")

    print("\n" + "=" * 60)
    print("             PER-CLASS RESULTS")
    print("=" * 60)

    # Per-class metrics
    class_names = model.names

    for i, class_id in enumerate(metrics.box.ap_class_index):

        class_name = class_names[int(class_id)]

        class_precision = metrics.box.p[i]
        class_recall = metrics.box.r[i]
        class_f1 = metrics.box.f1[i]
        class_map50 = metrics.box.ap50[i]
        class_map50_95 = metrics.box.ap[i]

        print(f"\nClass: {class_name}")
        print(f"  Precision    : {class_precision:.4f} ({class_precision * 100:.2f}%)")
        print(f"  Recall       : {class_recall:.4f} ({class_recall * 100:.2f}%)")
        print(f"  F1 Score     : {class_f1:.4f} ({class_f1 * 100:.2f}%)")
        print(f"  mAP50        : {class_map50:.4f} ({class_map50 * 100:.2f}%)")
        print(f"  mAP50-95     : {class_map50_95:.4f} ({class_map50_95 * 100:.2f}%)")

    # --------------------------------------------------------
    # Speed
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("             INFERENCE SPEED")
    print("=" * 60)

    if hasattr(metrics, "speed"):
        for key, value in metrics.speed.items():
            print(f"{key.capitalize():15}: {value:.2f} ms/image")

    print("\n" + "=" * 60)
    print("Validation completed successfully.")
    print("=" * 60)

    print("\nGenerated validation files are usually saved inside:")
    print("runs/detect/val*")


# ============================================================
# WINDOWS ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
