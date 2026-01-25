import pdfplumber
import pandas as pd
import os
import io

pdf_path = "airline_schedules/Aircraft Allocation for 25TH Jan 2026  ISSUE 2.pdf"
filename = os.path.basename(pdf_path).replace(".pdf", "")

# Improved parsing for the date string
date_str = filename.split("Aircraft Allocation for ")[-1].split("ISSUE")[0].strip()
date_object = pd.to_datetime(date_str)

all_tables = []

try:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                # Convert to DataFrame immediately to make cleaning easier
                df_page = pd.DataFrame(table)
                all_tables.append(df_page)
except Exception as e:
    print(f"Error opening PDF: {e}")

def clean_tables(df):
    df = pd.DataFrame(df)



    # FIX 1: Only process tables that have at least 6 columns
    if df.shape[1] < 6:
        return None

    # Slice to exactly 6 columns
    df = df.iloc[:, :6].copy()

    # FIX 2: Skip the header row if it contains the word "FLT" or "Flight"
    first_cell = str(df.iloc[0, 0]).upper()
    if "FLT" in first_cell or "FLIGHT" in first_cell or "NUMBER" in first_cell:
        df = df.iloc[1:].copy()

    # Assign column names
    df.columns = ['FLT NUMBER', 'REG', 'FROM', 'TO', 'STD', 'STA']

    # FIX 3: Drop rows where FLT NUMBER is empty
    df = df.dropna(subset=['FLT NUMBER'])
    df = df[df['FLT NUMBER'].astype(str).str.strip() != ""]

    df['DATE'] = date_object

    # Time processing (unchanged but now safer because headers are gone)
    for col in ['STA', 'STD']:
        df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True)
        df[col] = pd.to_datetime(df[col].str.zfill(4), format='%H%M', errors='coerce').dt.strftime('%H:%M')

    # Filter out any rows that failed the time conversion
    df = df.dropna(subset=['STD', 'STA'])

    # Directional Logic
    takeoff_df = df[df['FROM'] == "MLE"].copy()
    takeoff_df['DIRECTION'] = "TAKEOFF"
    takeoff_df['TIME'] = takeoff_df['STD']

    landing_df = df[df['TO'] == "MLE"].copy()
    landing_df['DIRECTION'] = "LANDING"
    landing_df['TIME'] = landing_df['STA']

    combined_df = pd.concat([
        takeoff_df[['DATE', 'FLT NUMBER', 'REG', 'FROM', 'TO', 'TIME', 'DIRECTION']],
        landing_df[['DATE', 'FLT NUMBER', 'REG', 'FROM', 'TO', 'TIME', 'DIRECTION']]
    ], ignore_index=True)

    combined_df['DATE TIME'] = pd.to_datetime(
        combined_df['DATE'].dt.strftime('%Y-%m-%d') + ' ' + combined_df['TIME']
    )

    return combined_df

all_cleaned_dfs = []

print(f"Total tables found by pdfplumber: {len(all_tables)}")

for i, table_df in enumerate(all_tables):
    try:
        processed = clean_tables(table_df)
        if processed is not None:
            all_cleaned_dfs.append(processed)
            print(f"Table {i}: Successfully cleaned.") # Checkpoint 2
        else:
            print(f"Table {i}: Skipped (Failed shape/guard check).") # Checkpoint 3
    except Exception as e:
        print(f"Table {i}: Error during cleaning -> {e}") # Checkpoint 4

# Check if we have anything before trying to concat
if not all_cleaned_dfs:
    print("!!! ERROR: No tables were successfully cleaned. final_master_df was never created.")
else:
    final_master_df = pd.concat(all_cleaned_dfs, ignore_index=True)
    print("--- FINAL DATASET ---")
    print(final_master_df)