import pandas as pd
import os

# --- CONFIGURATION ---
INPUT_FILE = "stop_times.txt"  # Make sure this file is in the same folder or update path
OUTPUT_FILE = "stop_times_visualized.xlsx"

def convert_txt_to_excel():
    print(f"Reading {INPUT_FILE}...")
    
    # GTFS files are CSVs, usually comma-separated
    try:
        # Read the CSV (GTFS standard uses commas)
        # We treat trip_id and stop_id as strings to preserve IDs like "001"
        df = pd.read_csv(INPUT_FILE, dtype={'trip_id': str, 'stop_id': str})
        
        print(f"Successfully loaded {len(df)} rows.")
        print("First 5 rows preview:")
        print(df.head())

        print(f"Saving to {OUTPUT_FILE}...")
        
        # Save to Excel
        df.to_excel(OUTPUT_FILE, index=False)
        
        print("✅ Done! You can now open the Excel file.")
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find '{INPUT_FILE}'. Check the path.")
    except Exception as e:
        print(f"❌ Error during conversion: {e}")

if __name__ == "__main__":
    convert_txt_to_excel()