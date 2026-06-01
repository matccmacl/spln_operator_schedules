import camelot
import pandas as pd
import numpy as np
import re
from src.processors.base import BaseScheduleProcessor

class MaldivianProcessor(BaseScheduleProcessor):
    """
    Processor strategy for Maldivian (Q2) flight schedules.
    Supports both PDF (via Camelot) and Excel/CSV formats.
    """
    
    def process(self, file, filename) -> tuple[pd.DataFrame | None, str | None]:
        filename_upper = filename.upper()
        if filename_upper.endswith(".PDF"):
            return self._process_pdf(file, filename)
        elif filename_upper.endswith((".XLSX", ".XLS", ".CSV")):
            return self._process_excel(file, filename)
        else:
            return None, f"Unsupported format for Maldivian: {filename}"

    def _process_pdf(self, file, filename) -> tuple[pd.DataFrame | None, str | None]:
        try:
            # Extract date from filename: e.g., "Aircraft Allocation for 25TH Jan 2026 ISSUE 2"
            date_pattern = r"(?i)(\d{1,2})[a-z]{2}\s([a-z]+)\s(\d{4})"
            match = re.search(date_pattern, filename)
            if not match:
                return None, "Could not extract date from Maldivian filename."
            
            clean_date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"
            date_object = pd.to_datetime(clean_date_str)

            # Read tables
            tables = camelot.read_pdf(file, pages="all", flavor="hybrid")
            if not tables:
                return None, "No tables found in PDF."

            combined_df = pd.concat([table.df for table in tables], ignore_index=True)
            
            # Initial cleaning (skip headers/junk)
            combined_df.drop(index=[0, 1, 2, 3], inplace=True)
            combined_df = combined_df.drop(combined_df.columns[0], axis=1) # Remove empty index col
            
            if combined_df.shape[1] < 6:
                return None, "Table structure unexpected."

            # Rename and slice
            df = combined_df.iloc[:, :6].copy()
            df.columns = ["FLT NUMBER", "REG", "FROM", "TO", "STD", "STA"]
            df["DATE"] = date_object

            # Normalize times
            for col in ["STD", "STA"]:
                df[col] = df[col].astype(str).str.replace(r"\.0$", "", regex=True)
                df[col] = pd.to_datetime(df[col].str.zfill(4), format="%H%M", errors="coerce").dt.strftime("%H:%M")

            # Split into Takeoffs and Landings
            takeoff_df = df[df["FROM"] == "MLE"].copy()
            takeoff_df["DIRECTION"] = "TAKEOFF"
            takeoff_df.rename(columns={"STD": "TIME"}, inplace=True)

            landing_df = df[df["TO"] == "MLE"].copy()
            landing_df["DIRECTION"] = "LANDING"
            landing_df.rename(columns={"STA": "TIME"}, inplace=True)

            final_df = pd.concat([takeoff_df, landing_df], ignore_index=True)
            final_df["FLT NUMBER"] = final_df["FLT NUMBER"].str.replace("0:00\n", "", regex=False)
            
            # Timestamps
            final_df["DATE TIME LOCAL"] = pd.to_datetime(final_df["DATE"].dt.strftime("%Y-%m-%d") + " " + final_df["TIME"])
            final_df["DATE TIME UTC"] = final_df["DATE TIME LOCAL"] - pd.Timedelta(hours=5)
            final_df["AIRLINE"] = "MALDIVIAN"
            
            # Standardize Columns
            cols = ['DATE TIME UTC', 'DATE TIME LOCAL', 'AIRLINE', 'FLT NUMBER', 'REG', 'FROM', 'TO', 'DIRECTION']
            return final_df[cols], None

        except Exception as e:
            return None, f"Maldivian PDF error: {e}"

    def _process_excel(self, file, filename) -> tuple[pd.DataFrame | None, str | None]:
        try:
            # 1. Initial load to find the header grid
            if filename.upper().endswith(".CSV"):
                raw_df = pd.read_csv(file, header=None)
            else:
                raw_df = pd.read_excel(file, header=None)
                
            # Find the row and column where 'FLT NUMBER' or 'REG' starts
            mask = raw_df.apply(lambda x: x.astype(str).str.contains('FLT NUMBER', case=False, na=False))
            if not mask.any().any():
                mask = raw_df.apply(lambda x: x.astype(str).str.contains('REG', case=False, na=False))
                
            if not mask.any().any():
                return None, "Could not find expected headers (FLT NUMBER or REG) in Maldivian file."

            # Get coordinates of the header
            row_indices, col_indices = np.where(mask)
            header_row = row_indices[0]
            start_col = col_indices[0]

            # 2. Slice data starting from the identified header row
            df = raw_df.iloc[header_row + 1 :].copy()
            
            # 3. Slice the correct data columns (6 columns starting from start_col)
            df = df.iloc[:, start_col : start_col + 6]
            df.columns = ["FLT NUMBER", "REG", "FROM", "TO", "STD", "STA"]
            
            # 4. Basic Cleaning
            df = df.dropna(subset=["FLT NUMBER"])
            df = df[df["FLT NUMBER"].astype(str).str.contains(r'\d', na=False)]
            df = df[~df["FROM"].astype(str).str.contains("COMPWASH", case=False, na=False)]
            df = df[~df["FLT NUMBER"].astype(str).str.contains("COMPWASH", case=False, na=False)]
            
            # Date extraction from filename
            date_pattern = r"(?i)(\d{1,2})[a-z]{2}\s([a-z]+)\s(\d{4})"
            match = re.search(date_pattern, filename)
            if match:
                clean_date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                date_object = pd.to_datetime(clean_date_str)
            else:
                date_object = pd.to_datetime("today")
            
            # 5. Standardize Times
            def format_time(val):
                if pd.isna(val) or val == "": return None
                t_str = str(val).split('.')[0].strip().zfill(4)
                if len(t_str) == 4:
                    return f"{t_str[:2]}:{t_str[2:]}"
                return None

            df["STD"] = df["STD"].apply(format_time)
            df["STA"] = df["STA"].apply(format_time)

            # 6. Transform to Movement Logic (Takeoff/Landing)
            takeoffs = df[df["FROM"].astype(str).str.contains("MLE", na=False)].copy()
            takeoffs["DIRECTION"] = "TAKEOFF"
            takeoffs["TIME"] = takeoffs["STD"]

            landings = df[df["TO"].astype(str).str.contains("MLE", na=False)].copy()
            landings["DIRECTION"] = "LANDING"
            landings["TIME"] = landings["STA"]

            # 7. Final Combined DataFrame
            combined = pd.concat([takeoffs, landings], ignore_index=True)
            if combined.empty:
                return None, "No MLE movements found in Maldivian file."
                
            combined["AIRLINE"] = "MALDIVIAN"
            combined["DATE"] = date_object
            
            # Create UTC/Local Timestamps
            combined["TIME"] = combined["TIME"].fillna("00:00")
            combined["DATE TIME LOCAL"] = pd.to_datetime(
                combined["DATE"].dt.strftime('%Y-%m-%d') + ' ' + combined["TIME"]
            )
            combined["DATE TIME UTC"] = combined["DATE TIME LOCAL"] - pd.Timedelta(hours=5)

            # Clean up flight numbers (remove noise like '0:00 ')
            combined["FLT NUMBER"] = combined["FLT NUMBER"].astype(str).str.replace(r'^0:00\s+', '', regex=True)

            # Standardize Columns
            cols = ['DATE TIME UTC', 'DATE TIME LOCAL', 'AIRLINE', 'FLT NUMBER', 'REG', 'FROM', 'TO', 'DIRECTION']
            return combined[cols], None

        except Exception as e:
            return None, f"Maldivian Excel error: {e}"
