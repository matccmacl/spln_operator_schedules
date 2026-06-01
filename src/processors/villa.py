import camelot
import pandas as pd
import re
from src.processors.base import BaseScheduleProcessor

class VillaProcessor(BaseScheduleProcessor):
    """
    Processor strategy for Villa Air PDF schedules.
    Uses Camelot (lattice flavor) to extract flights.
    """
    
    def process(self, file, filename) -> tuple[pd.DataFrame | None, str | None]:
        try:
            # Filename format: "...DD-MM-YYYY.pdf"
            date_pattern = r"([0-9]{2}-[0-9]{2}-[0-9]{4})"
            match = re.search(date_pattern, filename)
            if not match:
                return None, "Could not extract date from Villa Air filename."

            date_object = pd.to_datetime(match.group(1), dayfirst=True)

            tables = camelot.read_pdf(file, pages='all', flavor='lattice')
            all_processed_tables = []

            for table in tables:
                df = table.df.copy()
                # Keep only genuine flight rows: TYPE column (col 1) == 'DHC6'
                df = df[df[1] == 'DHC6']
                if df.empty:
                    continue
                df = df.iloc[:, [2, 3, 4, 5, 6, 7]]
                df.columns = ["REG", "FLT NUMBER", "FROM", "TO", "STD", "STA"]
                df["DATE"] = date_object
                all_processed_tables.append(df)

            if not all_processed_tables:
                return None, "No valid Villa Air data found."

            combined_df = pd.concat(all_processed_tables, ignore_index=True)

            # Normalize times - format is "H:MM" or "HH:MM"
            for col in ["STD", "STA"]:
                combined_df[col] = pd.to_datetime(combined_df[col], format="%H:%M", errors="coerce").dt.strftime("%H:%M")

            # Split into Takeoffs and Landings
            takeoff_df = combined_df[combined_df["FROM"] == "VRMM"].copy()
            takeoff_df["DIRECTION"] = "TAKEOFF"
            takeoff_df.rename(columns={"STD": "TIME"}, inplace=True)

            landing_df = combined_df[combined_df["TO"] == "VRMM"].copy()
            landing_df["DIRECTION"] = "LANDING"
            landing_df.rename(columns={"STA": "TIME"}, inplace=True)

            final_df = pd.concat([takeoff_df, landing_df], ignore_index=True)
            if final_df.empty:
                return None, "No VRMM movements found in Villa Air file."

            final_df["DATE TIME LOCAL"] = pd.to_datetime(final_df["DATE"].dt.strftime("%Y-%m-%d") + " " + final_df["TIME"])
            final_df["DATE TIME UTC"] = final_df["DATE TIME LOCAL"] - pd.Timedelta(hours=5)
            final_df["AIRLINE"] = "VILLA AIR"

            cols = ['DATE TIME UTC', 'DATE TIME LOCAL', 'AIRLINE', 'FLT NUMBER', 'REG', 'FROM', 'TO', 'DIRECTION']
            return final_df[cols], None

        except Exception as e:
            return None, f"Villa Air PDF error: {e}"
