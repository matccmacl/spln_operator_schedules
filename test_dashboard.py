import streamlit as st
from insights_module import load_master_data, generate_performance_visuals

try:
    from config import SCHEDULES_SHEET_URL, SCHEDULES_WS
except ImportError:
    st.error("⚠️ config.py not found or incomplete.")
    SCHEDULES_SHEET_URL = None
    SCHEDULES_WS = None

def main():
    st.set_page_config(page_title="Analytics Test Environment", layout="wide")
    st.title("📊 Master Schedule Analytics Test")

    if not SCHEDULES_SHEET_URL or not SCHEDULES_WS:
        st.warning("Check config.py for SCHEDULES_SHEET_URL and SCHEDULES_WS")
        return

    # Load using the correct worksheet from config
    master_df = load_master_data(SCHEDULES_SHEET_URL, SCHEDULES_WS)

    if not master_df.empty:
        generate_performance_visuals(master_df)
    else:
        st.error(f"Worksheet '{SCHEDULES_WS}' is empty or could not be loaded.")

if __name__ == "__main__":
    main()