import os
import pandas as pd
from pathlib import Path

CSV_PATH = Path(r"D:\\no_green_no_light\\evaluation\\ground_truth.csv")
PROJECT_DIR = Path(r"D:\no_green_no_light")

if not CSV_PATH.exists():
    print(f"ERROR: Cannot find CSV file at {CSV_PATH}")
    exit()

df = pd.read_csv(CSV_PATH)

print("=" * 60)
print("TERMINAL GROUND-TRUTH ANNOTATOR")
print("=" * 60)
print("Keys: [h] = helmet | [n] = no_helmet | [d] = no_detection | [q] = quit")
print("-" * 60)

changes_made = False

for index, row in df.iterrows():
    img_relative_path = row['image']
    img_full_path = PROJECT_DIR / img_relative_path
    img_name = Path(img_relative_path).name

    # Check if the file exists on your system
    status = "EXISTS" if img_full_path.exists() else "MISSING"

    # Print out interactive prompt inside terminal line
    print(f"\n[Row {index}] Frame: {row['frame']} | File: {img_name} ({status})")
    print(f"Current predicted class is: {row['predicted']}")
    
    while True:
        choice = input("Enter true label (h/n/d) or 'q' to quit: ").strip().lower()
        
        if choice == 'h':
            df.at[index, 'actual'] = 'helmet'
            changes_made = True
            break
        elif choice == 'n':
            df.at[index, 'actual'] = 'no_helmet'
            changes_made = True
            break
        elif choice == 'd':
            df.at[index, 'actual'] = 'no_detection'
            changes_made = True
            break
        elif choice == 'q':
            print("Exiting and saving progress...")
            break
        else:
            print("Invalid input! Type h, n, d, or q.")
            
    if choice == 'q':
        break

if changes_made:
    df.to_csv(CSV_PATH, index=False)
    print(f"\nSuccess! Saved label updates to: {CSV_PATH}")
else:
    print("\nNo updates were recorded.")
