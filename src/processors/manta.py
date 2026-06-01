import pandas as pd
import re
from src.processors.base import BaseScheduleProcessor

class MantaProcessor(BaseScheduleProcessor):
    """
    Processor strategy for MANTA Air Excel flight schedules.
    Expected sheet: 'flights'
    """
    
    def process(self, file, filename) -> tuple[pd.DataFrame | None, str | None]:
        try:
            # --- Date from filename: _MANTA_YYYY-MM-DD_ ---
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
            if date_match:
                schedule_date = pd.to_datetime(date_match.group(1)).date()
            else:
                schedule_date = pd.Timestamp.today().date()

            df = pd.read_excel(file, sheet_name="flights", header=None)
            # Row 0 is the header; data starts at row 1
            df = df.iloc[1:].copy()
            df.columns = ["DATE", "FLT NUMBER", "REG",
                          "ADEP_NAME", "FROM", "STD",
                          "ADES_NAME", "TO", "STA"]

            def _strip_vr(code):
                """'VRNOQ' -> 'NOQ', 'MLE' -> 'MLE'"""
                code_str = str(code).strip()
                return code_str[2:] if code_str.upper().startswith("VR") else code_str

            def _time_to_str(t):
                """datetime.time -> 'HH:MM'"""
                try:
                    return f"{t.hour:02d}:{t.minute:02d}"
                except AttributeError:
                    try:
                        parsed = pd.to_datetime(str(t))
                        return parsed.strftime("%H:%M")
                    except Exception:
                        return "00:00"

            # --- TAKEOFFS: FROM == 'MLE' ---
            dep = df[df["FROM"] == "MLE"].copy()
            dep["DIRECTION"] = "TAKEOFF"
            dep["TIME_UTC"] = dep["STD"].apply(_time_to_str)
            dep["TO"] = dep["TO"].apply(_strip_vr)

            # --- LANDINGS: TO == 'MLE' ---
            arr = df[df["TO"] == "MLE"].copy()
            arr["DIRECTION"] = "LANDING"
            arr["TIME_UTC"] = arr["STA"].apply(_time_to_str)
            arr["FROM"] = arr["FROM"].apply(_strip_vr)

            combined = pd.concat([dep, arr], ignore_index=True)
            if combined.empty:
                return None, "No MLE movements found in MANTA file."

            combined["AIRLINE"] = "MANTA AIR"
            date_str = str(schedule_date)
            combined["DATE TIME UTC"] = pd.to_datetime(date_str + " " + combined["TIME_UTC"])
            combined["DATE TIME LOCAL"] = combined["DATE TIME UTC"] + pd.Timedelta(hours=5)

            cols = ["DATE TIME UTC", "DATE TIME LOCAL", "AIRLINE", "FLT NUMBER", "REG", "FROM", "TO", "DIRECTION"]
            return combined[cols], None

        except Exception as e:
            return None, f"MANTA Air Excel error: {e}"
