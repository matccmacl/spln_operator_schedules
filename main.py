import streamlit as st
import pandas as pd
import time
import src.database as database
from src.ui import (
    load_master_data,
    inspect_database_dialog,
    render_tab_today,
    render_tab_history,
    render_view_ingestion
)

# --- STREAMLIT PAGE CONFIGURATION ---
st.set_page_config(page_title="Seaplane Ops Dashboard", layout="wide", page_icon=":material/flight:")

# --- DATABASE INITIALIZATION ---
if 'db_init' not in st.session_state:
    database.init_db()
    st.session_state['db_init'] = True

# --- SESSION STATE FOR NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state['page'] = "Operational Analytics"

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("### :material/flight: Air Traffic Services")
    st.divider()
    
    st.write("Navigation")
    if st.button(":material/analytics: Operational Analytics", use_container_width=True, type="secondary" if st.session_state['page'] == "File Ingestion" else "primary"):
        st.session_state['page'] = "Operational Analytics"
        st.rerun()
        
    if st.button(":material/upload_file: File Ingestion", use_container_width=True, type="secondary" if st.session_state['page'] == "Operational Analytics" else "primary"):
        st.session_state['page'] = "File Ingestion"
        st.rerun()
        
    st.divider()
    with st.expander(":material/build: Developer Tools"):
        # Display DB Size
        db_size = database.get_db_size()
        st.write(f":material/database: **DB Size:** `{db_size}`")
        
        if st.button("Clear Local SQLite DB", use_container_width=True):
            database.clear_data()
            load_master_data.clear()
            st.success("Local database wiped.")
            time.sleep(1)
            st.rerun()
            
        st.divider()
        st.write("Inspect Database")
        
        if st.button(":material/database: Inspect Database", use_container_width=True):
            inspect_database_dialog()
            
    st.info("Seaplane Ops v1.2 (SQLite-only)")

# --- MAIN PAGE ROUTING ---
st.title(":material/flight: Seaplane Operator Schedule Dashboard")

if st.session_state['page'] == "File Ingestion":
    render_view_ingestion()
else:
    st.header("Fleet Operational Insights")
    master_data = load_master_data()
    if not master_data.empty:
        # Renders the high-performance tabbed view
        tab_today, tab_history = st.tabs([":material/today: Today's Operations", ":material/history: Historical Analysis"])
        with tab_today:
            render_tab_today(master_data)
        with tab_history:
            render_tab_history(master_data)
    else:
        st.info("No operational data available in the local database. Please ingest schedules in the Ingestion page.")