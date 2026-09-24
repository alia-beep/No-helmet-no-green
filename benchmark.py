from ultralytics import YOLO
from pathlib import Path
import time
import csv
import torch


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(r"D:\no_green_no_light")

MODEL_PATH = BASE_DIR / "AdvHelmet.pt"

IMAGE_DIRS = [
    BASE_DIR / "evaluation" / "frames",
    BASE_DIR / "evaluation",
    BASE_DIR / "frames",
    BASE_DIR / "dataset" / "images" / "val",
]

IMG_SIZE = 640

WARMUP_RUNS = 5
BENCHMARK_RUNS = 30

BATCH_SIZES = [1, 2, 4, 8]


# ============================================================
# FIND TEST IMAGES
# ============================================================

def find_test_images():

    extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"
    }

    images = []

    for directory in IMAGE_DIRS:

        if not directory.exists():
            continue

        for file in directory.rglob("*"):

            if file.is_file() and file.suffix.lower() in extensions:
                images.append(file)

    # Remove duplicates
    images = list(dict.fromkeys(images))

    return images


# ============================================================
# BENCHMARK FUNCTION
# ============================================================

def benchmark_device(model, image_paths, device, batch_size):

    selected_images = []

    for i in range(batch_size):
        selected_images.append(
            str(image_paths[i % len(image_paths)])
        )

    # --------------------------------------------------------
    # Warm-up
    # --------------------------------------------------------

    for _ in range(WARMUP_RUNS):

        model.predict(
            source=selected_images,
            imgsz=IMG_SIZE,
            batch=batch_size,
            device=device,
            verbose=False
        )

    # --------------------------------------------------------
    # Benchmark
    # --------------------------------------------------------

    if device != "cpu" and torch.cuda.is_available():

        torch.cuda.synchronize()

    start_time = time.perf_counter()

    for _ in range(BENCHMARK_RUNS):

        model.predict(
            source=selected_images,
            imgsz=IMG_SIZE,
            batch=batch_size,
            device=device,
            verbose=False
        )

    if device != "cpu" and torch.cuda.is_available():

        torch.cuda.synchronize()

    elapsed_time = time.perf_counter() - start_time

    total_images = BENCHMARK_RUNS * batch_size

    # Images processed per second
    fps = total_images / elapsed_time

    # Time for one batch
    latency_batch_ms = (
        elapsed_time / BENCHMARK_RUNS
    ) * 1000

    # Approximate time per image
    latency_image_ms = (
        latency_batch_ms / batch_size
    )

    return {
        "device": str(device),
        "batch_size": batch_size,
        "latency_per_image_ms": latency_image_ms,
        "latency_per_batch_ms": latency_batch_ms,
        "fps": fps
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("             ADVHELMET.PT BENCHMARK")
    print("=" * 70)

    # --------------------------------------------------------
    # Check model
    # --------------------------------------------------------

    if not MODEL_PATH.exists():

        print("\nERROR: AdvHelmet.pt not found.")

        print(MODEL_PATH)

        return

    # --------------------------------------------------------
    # Find images
    # --------------------------------------------------------

    images = find_test_images()

    if not images:

        print("\nERROR: No images found.")

        print("\nPut some JPG/PNG images in one of:")

        for directory in IMAGE_DIRS:
            print(directory)

        return

    print("\nModel:")
    print(MODEL_PATH)

    print("\nImages found:")
    print(len(images))

    print("\nImage size:")
    print(IMG_SIZE)

    print("\nWarm-up runs:")
    print(WARMUP_RUNS)

    print("\nBenchmark runs:")
    print(BENCHMARK_RUNS)

    print("\nExample image:")
    print(images[0])

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print("\nLoading AdvHelmet.pt...")

    model = YOLO(str(MODEL_PATH))

    print("Model loaded successfully.")

    # --------------------------------------------------------
    # Detect devices
    # --------------------------------------------------------

    devices = ["cpu"]

    if torch.cuda.is_available():

        devices.append("0")

        print("\nCUDA GPU detected:")
        print(torch.cuda.get_device_name(0))

    else:

        print("\nNo CUDA GPU detected.")
        print("Only CPU benchmark will be performed.")

    # --------------------------------------------------------
    # Run benchmark
    # --------------------------------------------------------

    results = []

    for device in devices:

        print("\n")
        print("=" * 70)
        print(f"DEVICE: {device}")
        print("=" * 70)

        for batch_size in BATCH_SIZES:

            print(
                f"\nTesting batch size: {batch_size}"
            )

            try:

                result = benchmark_device(
                    model=model,
                    image_paths=images,
                    device=device,
                    batch_size=batch_size
                )

                results.append(result)

                print(
                    f"Latency/image : "
                    f"{result['latency_per_image_ms']:.2f} ms"
                )

                print(
                    f"Latency/batch : "
                    f"{result['latency_per_batch_ms']:.2f} ms"
                )

                print(
                    f"Throughput    : "
                    f"{result['fps']:.2f} FPS"
                )

            except Exception as e:

                print(
                    f"Batch size {batch_size} failed."
                )

                print(
                    f"Reason: {e}"
                )

    # --------------------------------------------------------
    # Final table
    # --------------------------------------------------------

    print("\n\n")

    print("=" * 70)
    print("                  FINAL RESULTS")
    print("=" * 70)

    print(
        f"\n{'Device':<10}"
        f"{'Batch':<10}"
        f"{'Latency/img':<18}"
        f"{'Latency/batch':<18}"
        f"{'FPS':<10}"
    )

    print("-" * 70)

    for result in results:

        print(
            f"{result['device']:<10}"
            f"{result['batch_size']:<10}"
            f"{result['latency_per_image_ms']:<18.2f}"
            f"{result['latency_per_batch_ms']:<18.2f}"
            f"{result['fps']:<10.2f}"
        )

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    output_dir = BASE_DIR / "evaluation"

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = output_dir / "benchmark_results.csv"

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "device",
                "batch_size",
                "latency_per_image_ms",
                "latency_per_batch_ms",
                "fps"
            ]
        )

        writer.writeheader()

        writer.writerows(results)

    # --------------------------------------------------------
    # CPU Batch 1
    # --------------------------------------------------------

    cpu_batch1 = None

    for result in results:

        if (
            result["device"] == "cpu"
            and result["batch_size"] == 1
        ):

            cpu_batch1 = result

            break

    print("\n")
    print("=" * 70)
    print("              REAL-TIME ASSESSMENT")
    print("=" * 70)

    if cpu_batch1:

        fps = cpu_batch1["fps"]

        latency = cpu_batch1[
            "latency_per_image_ms"
        ]

        print(
            f"\nCPU Batch 1:"
        )

        print(
            f"Latency : {latency:.2f} ms/frame"
        )

        print(
            f"FPS     : {fps:.2f}"
        )

        if fps >= 25:

            print(
                "\nExcellent for real-time video."
            )

        elif fps >= 15:

            print(
                "\nGood for real-time monitoring."
            )

        elif fps >= 10:

            print(
                "\nUsable for near-real-time monitoring."
            )

        elif fps >= 5:

            print(
                "\nUsable for prototype/monitoring."
            )

        else:

            print(
                "\nToo slow for practical real-time video."
            )

    # --------------------------------------------------------
    # Finish
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)

    print("Benchmark completed successfully.")

    print("=" * 70)

    print("\nResults saved to:")

    print(output_file)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()