import pandas as pd
from pathlib import Path
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

CSV_PATH = Path(r"D:\\no_green_no_light\\evaluation\\ground_truth.csv")

print("=" * 60)
print("HELMET MODEL ACCURACY EVALUATION")
print("=" * 60)

if not CSV_PATH.exists():
    print(f"ERROR: Missing evaluation CSV file at {CSV_PATH}")
    exit()

# Load the tracking data, dropping rows where either column is empty
df = pd.read_csv(CSV_PATH)
df = df.dropna(subset=['actual', 'predicted'])

# Clean and normalize strings
df['actual'] = df['actual'].astype(str).str.strip().str.lower()
df['predicted'] = df['predicted'].astype(str).str.strip().str.lower()

# Exclude any rows labeled as 'no_detection' in either column for strict metric calculations
df = df[~df['actual'].isin(['no_detection', 'nan', ''])]
df = df[~df['predicted'].isin(['no_detection', 'nan', ''])]

if len(df) == 0:
    print("\nERROR: No valid matching rows found between actual and predicted columns.")
    print("Ensure you have manually annotated a few lines using your annotator script first!")
    exit()

# Map strings directly to metrics-safe binary numeric targets (0 for helmet, 1 for no_helmet)
label_map = {'helmet': 0, 'no_helmet': 1}

# Convert arrays
actual = df['actual'].map(label_map).tolist()
predicted = df['predicted'].map(label_map).tolist()

# Drop unmappable records safely if any strange values exist
valid_indices = [i for i, (a, p) in enumerate(zip(actual, predicted)) if pd.notna(a) and pd.notna(p)]
actual = [int(actual[i]) for i in valid_indices]
predicted = [int(predicted[i]) for i in valid_indices]

if len(actual) == 0:
    print("\nERROR: Could not convert text labels into evaluation matrices.")
    exit()

# Compute exact Scikit-Learn validation metrics
accuracy = accuracy_score(actual, predicted)
precision = precision_score(actual, predicted, zero_division=0)
recall = recall_score(actual, predicted, zero_division=0)
f1 = f1_score(actual, predicted, zero_division=0)

print()
print("=" * 60)
print("FINAL METRIC RESULTS")
print("=" * 60)
print(f"Samples Evaluated : {len(actual)}")
print(f"Accuracy          : {accuracy * 100:.2f}%")
print(f"Precision         : {precision * 100:.2f}%")
print(f"Recall            : {recall * 100:.2f}%")
print(f"F1 Score          : {f1 * 100:.2f}%")

print("\nConfusion Matrix:")
print(confusion_matrix(actual, predicted, labels=[0, 1]))

print("\nClassification Report:")
print(classification_report(
    actual, predicted, labels=[0, 1],
    target_names=["helmet", "no_helmet"], zero_division=0
))
