import json
from datetime import datetime
import os

# --- Configuration ---
# This is the master file you just created
INPUT_FILE = 'CLEAN_EXPLOSIONS.json' 
# This file will be OVERWRITTEN with 2010-2022 data
TRAINING_SET_FILE = 'CLEAN_EXPLOSIONS.json'
# This new file will be CREATED with 2023-2024 data
DISCARD_SET_FILE = 'DISCARD_EXPLOSIONS.json' 
# ---------------------

def split_data():
    """
    Splits the main data file into a training set (pre-2023) and a
    discard/test set (2023-2024).
    
    - Overwrites INPUT_FILE with the training data.
    - Creates DISCARD_SET_FILE with the test data.
    """
    
    keep_discoveries = []   # Data for training (<= 2022)
    discard_discoveries = [] # Data for holdout (>= 2023)

    # --- 1. Load the master file ---
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERROR: Input file not found: {INPUT_FILE}")
        print("Please make sure the file is in the same directory.")
        return

    print(f"Loading data from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r') as f:
        try:
            data = json.load(f)
            discoveries = data['discoveries']
            print(f"Loaded {len(discoveries)} total discoveries.")
        except json.JSONDecodeError as e:
            print(f"❌ ERROR: Could not read {INPUT_FILE}. File might be corrupted.")
            print(f"Details: {e}")
            return
        except KeyError:
            print(f"❌ ERROR: Input file has an unexpected format. 'discoveries' key is missing.")
            return

    # --- 2. Split the data by year ---
    print("Splitting discoveries by catalyst_date (2023/2024)...")
    skipped_count = 0
    for discovery in discoveries:
        try:
            # Get the catalyst year as an integer
            catalyst_date_str = discovery['catalyst_date']
            catalyst_year = datetime.strptime(catalyst_date_str, '%Y-%m-%d').year
            
            # The main split logic
            if catalyst_year >= 2023:
                discard_discoveries.append(discovery)
            else:
                keep_discoveries.append(discovery)
                
        except KeyError:
            print(f"⚠️ Warning: Skipping a discovery (Ticker: {discovery.get('ticker')}) due to missing 'catalyst_date'.")
            skipped_count += 1
        except Exception as e:
            print(f"⚠️ Warning: Skipping a discovery (Ticker: {discovery.get('ticker')}). Error: {e}")
            skipped_count += 1

    # --- 3. Save the DISCARD/TEST set (2023-2024) ---
    discard_output = {
        'description': 'Discard/Holdout (Test) Set. Contains all explosions from 2023-2024.',
        'generated_at': datetime.now().isoformat(),
        'total_discoveries': len(discard_discoveries),
        'discoveries': discard_discoveries
    }
    with open(DISCARD_SET_FILE, 'w') as f:
        json.dump(discard_output, f, indent=2)
    print(f"\n✅ Created {DISCARD_SET_FILE} with {len(discard_discoveries)} discoveries (2023-2024).")

    # --- 4. Overwrite the main file with the TRAINING set (pre-2023) ---
    # We re-use the original file's metadata, just replacing the discoveries
    data['description'] = 'Cleaned Training Set (pre-2023). 2023-2024 data has been removed and saved to DISCARD_EXPLOSIONS.json.'
    data['total_explosions'] = len(keep_discoveries)
    data['discoveries'] = keep_discoveries
    
    with open(TRAINING_SET_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Overwritten {TRAINING_SET_FILE} with {len(keep_discoveries)} discoveries (pre-2023).")
    
    print("\n" + "="*50)
    print("Split complete.")
    print(f"  Total analyzed: {len(discoveries)}")
    print(f"  Total kept (training): {len(keep_discoveries)}")
    print(f"  Total discarded (test): {len(discard_discoveries)}")
    print(f"  Total skipped (errors): {skipped_count}")
    print("="*50)

if __name__ == "__main__":
    split_data()
