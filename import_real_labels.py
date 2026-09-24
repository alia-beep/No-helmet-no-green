import os
import re
import pandas as pd
from pathlib import Path

# Setup clean absolute paths
CSV_PATH = Path(r"D:\\no_green_no_light\\evaluation\\ground_truth.csv")
LABELS_FOLDERS = [
    Path(r"D:\\no_green_no_light\dataset\\labels\\test"),
    Path(r"D:\\no_green_no_light\dataset\\labels\\val")
]

print("=" * 60)
print("COMPILING REAL DATASET GROUND-TRUTH LABELS")
print("=" * 60)

if not CSV_PATH.exists():
    print(f"ERROR: Cannot find your tracking CSV file at {CSV_PATH}")
    exit()

# Dictionary to hold file mapping keys -> human annotations
labels_lookup = {}

# Process every text file located in both annotation directories
for folder in LABELS_FOLDERS:
    if not folder.exists():
        print(f"Skipping directory path (not found): {folder.name}")
        continue
        
    txt_files = list(folder.glob("*.txt"))
    print(f"Scanning folder '{folder.name}': Found {len(txt_files)} label files.")
    
    for txt_path in txt_files:
        # Match names like video_1_frame_000011 -> extracts prefix and padded number
        match = re.match(r"(video_\d+_frame_)(\d+)", txt_path.stem)
        if match:
            prefix = match.group(1)
            frame_num = int(match.group(2)) # drops '000011' down to integer 11
            standard_key = f"{prefix}{frame_num}" # merges back to match CSV name structure
            
            # Read label values safely
            try:
                with open(txt_path, 'r') as f:
                    lines = [line.strip() for line in f if line.strip()]
                
                if not lines:
                    labels_lookup[standard_key] = 'no_detection'
                else:
                    first_item = lines[0].split()
                    if first_item:
                        class_id = int(first_item[0])
                        if class_id == 0:
                            labels_lookup[standard_key] = 'helmet'
                        elif class_id == 1:
                            labels_lookup[standard_key] = 'no_helmet'
                        else:
                            labels_lookup[standard_key] = 'no_detection'
            except Exception as e:
                pass

# Apply mapped true labels directly to data frame structure
df = pd.read_csv(CSV_PATH)
updated_rows = 0

for index, row in df.iterrows():
    if pd.isna(row['image']):
        continue
        
    csv_image_stem = Path(str(row['image'])).stem # extracts 'video_1_frame_11'
    
    if csv_image_stem in labels_lookup:
        df.at[index, 'actual'] = labels_lookup[csv_image_stem]
        updated_rows += 1
    else:
        df.at[index, 'actual'] = 'no_detection'

# Commit data back down to disk file storage 
df.to_csv(CSV_PATH, index=False)
print("-" * 60)
print(f"COMPLETED: Successfully imported {updated_rows} real labels into 'actual' column!")
print("Your ground_truth.csv is now completely ready.")
