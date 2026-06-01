import pandas as pd
from src.processors.base import BaseScheduleProcessor

class TmaProcessor(BaseScheduleProcessor):
    """
    Processor strategy for TMA Excel schedules.
    Expected outbound/inbound side-by-side layout.
    """
    
    def process(self, file, filename) -> tuple[pd.DataFrame | None, str | None]:
        try:
            raw = pd.read_excel(file, header=None)

            def _extract_section(df_cols, direction, time_col_label):
                """Slice one side of the sheet, clean, and tag direction."""
                section = df_cols.iloc[2:].copy()  # skip two header rows
                section.columns = ["DATE", "TAIL", "FLT NUMBER", "FROM", "TO", time_col_label]

                # Drop rows where both DATE and TAIL are missing
                section = section.dropna(subset=["DATE", "TAIL"])
                section = section[section["TAIL"].astype(str).str.strip() != ""]

                # REG: prepend '8Q-' to the 3-char tail suffix
                section["REG"] = "8Q-" + section["TAIL"].astype(str).str.strip()

                # DATE: Excel reads it as a datetime; extract just the date part
                section["DATE"] = pd.to_datetime(section["DATE"]).dt.normalize()

                # TIME: cells come in as timedelta (HH:MM:SS) or datetime; normalise to HH:MM string
                def _to_hhmm(val):
                    if pd.isna(val):
                        return "00:00"
                    if isinstance(val, pd.Timedelta):
                        total_seconds = int(val.total_seconds())
                    elif hasattr(val, 'hour'):  # datetime.time or datetime
                        total_seconds = val.hour * 3600 + val.minute * 60
                    else:
                        try:
                            t = pd.to_datetime(str(val))
                            total_seconds = t.hour * 3600 + t.minute * 60
                        except Exception:
                            return "00:00"
                    h, m = divmod(total_seconds // 60, 60)
                    return f"{h:02d}:{m:02d}"

                section["TIME"] = section[time_col_label].apply(_to_hhmm)
                section["DIRECTION"] = direction

                return section[["DATE", "REG", "FLT NUMBER", "FROM", "TO", "TIME", "DIRECTION"]]

            dep = _extract_section(raw.iloc[:, 0:6],  "TAKEOFF", "STD")
            arr = _extract_section(raw.iloc[:, 7:13], "LANDING", "STA")

            combined = pd.concat([dep, arr], ignore_index=True)
            if combined.empty:
                return None, "No data rows found in TMA file."

            combined["AIRLINE"] = "TMA"
            combined["DATE TIME LOCAL"] = pd.to_datetime(
                combined["DATE"].dt.strftime("%Y-%m-%d") + " " + combined["TIME"]
            )
            combined["DATE TIME UTC"] = combined["DATE TIME LOCAL"] - pd.Timedelta(hours=5)

            cols = ["DATE TIME UTC", "DATE TIME LOCAL", "AIRLINE", "FLT NUMBER", "REG", "FROM", "TO", "DIRECTION"]
            return combined[cols], None

        except Exception as e:
            return None, f"TMA Excel error: {e}"
