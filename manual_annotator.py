import os
import pandas as pd
from pathlib import Path

# Set explicit paths
CSV_PATH = Path(r"D:\no_green_no_light\evaluation\ground_truth.csv")
PROJECT_DIR = Path(r"D:\no_green_no_light")

def main():
    print("=" * 60)
    print("   QUICK INTERACTIVE TERMINAL ANNOTATOR")
    print("=" * 60)
    print("Instructions:")
    print("  [h] -> Set True Label as 'helmet'")
    print("  [n] -> Set True Label as 'no_helmet'")
    print("  [d] -> Set True Label as 'no_detection'")
    print("  [s] -> Skip this frame (leave blank)")
    print("  [q] -> Save current progress and Quit")
    print("-" * 60)

    if not CSV_PATH.exists():
        print(f"ERROR: Cannot find your tracking CSV file at: {CSV_PATH}")
        return

    # FIX: Force 'actual' column to be loaded as string/text data type
    df = pd.read_csv(CSV_PATH, dtype={'actual': str})
    
    # Secondary protection to stop float64 crashes
    df['actual'] = df['actual'].astype(object)
    
    total_rows = len(df)
    
    # Calculate initial progress statistics
    initially_labeled = df['actual'].notna().sum()
    print(f"Total Rows: {total_rows} | Already Annotated: {initially_labeled}")
    print("-" * 60)

    changes_made = False

    for index, row in df.iterrows():
        # Check if row is already filled out (allows resuming progress seamlessly)
        if pd.notna(row['actual']) and str(row['actual']).strip() != "":
            continue

        img_relative_path = row['image']
        img_full_path = PROJECT_DIR / img_relative_path
        img_name = Path(str(img_relative_path)).name

        # Verify image exists physically on your disk drive
        status_flag = "OK" if img_full_path.exists() else "MISSING IMAGE FILE"

        # Interactive Command Prompt Header
        print(f"\n[Progress: {index + 1}/{total_rows}] File: {img_name} ({status_flag})")
        print(f"Model Predicted Value: {row['predicted']}")
        
        while True:
            choice = input("Enter True Ground-Truth Label (h / n / d / s / q): ").strip().lower()
            
            if choice == 'h':
                df.at[index, 'actual'] = 'helmet'
                changes_made = True
                print("-> Saved as: helmet")
                break
            elif choice == 'n':
                df.at[index, 'actual'] = 'no_helmet'
                changes_made = True
                print("-> Saved as: no_helmet")
                break
            elif choice == 'd':
                df.at[index, 'actual'] = 'no_detection'
                changes_made = True
                print("-> Saved as: no_detection")
                break
            elif choice == 's':
                print("-> Skipped frame.")
                break
            elif choice == 'q':
                print("\nSaving progress to disk and exiting script gracefully...")
                break
            else:
                print("Invalid Entry! Please choose among (h, n, d, s, q).")

        if choice == 'q':
            break

    # Save tracking dataframe modification back down onto disk storage safely
    if changes_made:
        df.to_csv(CSV_PATH, index=False)
        labeled_now = df['actual'].notna().sum()
        print(f"\nSuccess! File updated. Total progress status: {labeled_now}/{total_rows} completed.")
    else:
        print("\nExited. No new annotations were added.")

if __name__ == "__main__":
    main()
