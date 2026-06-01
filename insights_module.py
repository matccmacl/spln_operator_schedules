# --- LEGACY SUPPORT FOR ROOT LEVEL IMPORTS ---
import streamlit as st
import pandas as pd
from src.ui.components import load_master_data
from src.ui.tab_today import render_tab_today
from src.ui.tab_history import render_tab_history

def generate_performance_visuals(df: pd.DataFrame):
    """
    Legacy visualization wrapper for backwards compatibility.
    Replicates original feature engineering and routes rendering to new UI tabs.
    """
    if df is None or df.empty:
        st.warning("The database appears to be empty.")
        return

    # Critical Column Check
    if 'DATE TIME UTC' not in df.columns:
        st.error("Missing critical column: 'DATE-TIME' (mapped to 'DATE TIME UTC')")
        return

    df = df.dropna(subset=['DATE TIME UTC'])

    # Replicate original feature engineering
    df['Month'] = df['DATE TIME UTC'].dt.strftime('%b %Y')
    df['MonthName'] = df['DATE TIME UTC'].dt.strftime('%B')
    df['Year'] = df['DATE TIME UTC'].dt.year
    df['Day'] = df['DATE TIME UTC'].dt.date
    df['Hour'] = df['DATE TIME UTC'].dt.hour
    df['Minute'] = df['DATE TIME UTC'].dt.minute
    df['Minute_Bin'] = df['DATE TIME UTC'].dt.floor('15min').dt.strftime('%H:%M')

    # Renders original tabs
    tab_today, tab_history = st.tabs([":material/today: Today's Operations", ":material/history: Historical Analysis"])
    with tab_today:
        render_tab_today(df)
    with tab_history:
        render_tab_history(df)