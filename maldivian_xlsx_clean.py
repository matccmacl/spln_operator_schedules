import pandas as pd
import numpy as np
import re

def extract_date_from_filename(filename):
    """
    Extracts date from Maldivian schedule filenames.
    Example: 'Aircraft Allocation for 25TH Mar 2026' -> 2026-03-25
    """
    pattern = r"(\d{1,2})[A-Z]{2}\s([A-Za-z]+)\s(\d{4})"
    match = re.search(pattern, filename)
    if match:
        clean_date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"
        return pd.to_datetime(clean_date_str)
    return pd.to_datetime("today")

def clean_tables_maldivian_excel(file_path, filename):
    """
    Processes the raw Maldivian Excel/CSV allocation into a standardized format.
    Automatically detects data boundaries to avoid empty padding columns.
    """
    # 1. Initial load to find the header
    raw_df = pd.read_csv(file_path, header=None)
    
    # Find the row and column where 'FLT NUMBER' starts
    # We search the whole grid for the string 'FLT NUMBER'
    mask = raw_df.apply(lambda x: x.astype(str).str.contains('FLT NUMBER', case=False, na=False))
    if not mask.any().any():
        # Fallback if specific header not found
        mask = raw_df.apply(lambda x: x.astype(str).str.contains('REG', case=False, na=False))
        
    # Get coordinates of the header
    row_indices, col_indices = np.where(mask)
    header_row = row_indices[0]
    start_col = col_indices[0]

    # 2. Re-load data starting from the identified header row
    df = pd.read_csv(file_path, skiprows=header_row + 1, header=None)
    
    # 3. Slice the correct data columns (6 columns starting from start_col)
    # This skips the leading empty columns (usually 3 columns)
    df = df.iloc[:, start_col : start_col + 6]
    df.columns = ["FLT NUMBER", "REG", "FROM", "TO", "STD", "STA"]
    
    # 4. Basic Cleaning
    # Drop rows where FLT NUMBER is truly empty
    df = df.dropna(subset=["FLT NUMBER"])
    # Ensure it's a valid flight (contains at least one digit)
    df = df[df["FLT NUMBER"].astype(str).str.contains(r'\d', na=False)]
    # Filter out "COMPWASH" or other non-flight rows
    df = df[~df["FROM"].astype(str).str.contains("COMPWASH", case=False, na=False)]
    
    date_object = extract_date_from_filename(filename)
    
    # 5. Standardize Times
    def format_time(val):
        if pd.isna(val) or val == "": return None
        # Handle Excel decimal issues (e.g. 900.0)
        t_str = str(val).split('.')[0].strip().zfill(4)
        if len(t_str) == 4:
            return f"{t_str[:2]}:{t_str[2:]}"
        return None

    df["STD"] = df["STD"].apply(format_time)
    df["STA"] = df["STA"].apply(format_time)

    # 6. Transform to Movement Logic (Takeoff/Landing)
    # Takeoffs: From Male (MLE)
    takeoffs = df[df["FROM"].astype(str).str.contains("MLE", na=False)].copy()
    takeoffs["DIRECTION"] = "TAKEOFF"
    takeoffs["TIME"] = takeoffs["STD"]

    # Landings: To Male (MLE)
    landings = df[df["TO"].astype(str).str.contains("MLE", na=False)].copy()
    landings["DIRECTION"] = "LANDING"
    landings["TIME"] = landings["STA"]

    # 7. Final Combined DataFrame
    combined = pd.concat([takeoffs, landings], ignore_index=True)
    combined["AIRLINE"] = "MALDIVIAN"
    combined["DATE"] = date_object
    
    # Create UTC Timestamps
    combined["TIME"] = combined["TIME"].fillna("00:00")
    combined["DATE TIME LOCAL"] = pd.to_datetime(
        combined["DATE"].dt.strftime('%Y-%m-%d') + ' ' + combined["TIME"]
    )
    combined["DATE TIME UTC"] = combined["DATE TIME LOCAL"] - pd.Timedelta(hours=5)

    # Clean up flight numbers (remove noise like '0:00 ')
    combined["FLT NUMBER"] = combined["FLT NUMBER"].astype(str).str.replace(r'^0:00\s+', '', regex=True)

    return combined[["DATE TIME UTC", "AIRLINE", "FLT NUMBER", "REG", "FROM", "TO", "DIRECTION"]]