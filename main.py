import streamlit as st
import pandas as pd
from datetime import datetime
import io
import time

# Internal Imports
import database
from processors import process_file
from insights_module import load_master_data, generate_performance_visuals

# --- CONFIGURATION ---
st.set_page_config(page_title="Seaplane Ops Dashboard", layout="wide", page_icon=":material/flight:")

# --- UTILS ---
# --- DATABASE INIT ---
if 'db_init' not in st.session_state:
    database.init_db()
    st.session_state['db_init'] = True

def check_duplicate(filename):
    """Checks the local SQLite database for previously processed files."""
    return database.check_file_processed_local(filename)

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
            st.success("Local database wiped.")
            time.sleep(1)
            st.rerun()
            
        st.divider()
        st.write("Inspect Database")
        
        @st.dialog("Inspect Database", width="large")
        def inspect_database():
            tab_mvmt, tab_reg, tab_files = st.tabs([
                ":material/flight: Movements",
                ":material/directions_boat: Registrations",
                ":material/folder: Processed Files",
            ])

            with tab_mvmt:
                df = database.get_all_movements()
                if df.empty:
                    st.info("Table is empty.")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)

            with tab_reg:
                df = database.get_all_registrations()
                if df.empty:
                    st.info("Table is empty.")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)

            with tab_files:
                files_df = database.get_all_filenames()
                if files_df.empty:
                    st.info("No processed files found.")
                else:
                    search = st.text_input(":material/search: Search Files", placeholder="Enter filename...")
                    if search:
                        files_df = files_df[files_df['filename'].str.contains(search, case=False)]

                    if 'Select' not in files_df.columns:
                        files_df.insert(0, "Select", False)

                    edited_df = st.data_editor(
                        files_df,
                        hide_index=True,
                        column_config={
                            "Select": st.column_config.CheckboxColumn(default=False),
                            "filename": st.column_config.TextColumn("Filename", width="large"),
                            "timestamp": st.column_config.TextColumn("Processed At", width="medium"),
                            "id": None,
                        },
                        disabled=["filename", "timestamp"],
                        use_container_width=True,
                        key="file_editor"
                    )

                    selected_files = edited_df[edited_df["Select"] == True]["filename"].tolist()
                    if selected_files:
                        st.divider()
                        st.warning(f":material/warning: **Bulk Delete:** {len(selected_files)} file(s) selected.")
                        if st.button(f"Confirm Delete ({len(selected_files)})", type="primary", use_container_width=True):
                            for fname in selected_files:
                                database.delete_file(fname)
                            st.success("Selected files deleted successfully.")
                            time.sleep(1)
                            st.rerun()

        if st.button(":material/database: Inspect Database", use_container_width=True):
            inspect_database()
            


    st.info("Seaplane Ops v1.2 (SQLite-only)")

st.title(":material/flight: Seaplane Operator Schedule Dashboard")

if st.session_state['page'] == "File Ingestion":
    st.header("Upload & Process Schedules")
    
    # --- QUEUE INITIALIZATION ---
    if 'ingestion_queue' not in st.session_state:
        st.session_state['ingestion_queue'] = []
    if 'uploader_key' not in st.session_state:
        st.session_state['uploader_key'] = 0
    if 'df_extracted' not in st.session_state:
        st.session_state['df_extracted'] = None
    if 'extracted_filename' not in st.session_state:
        st.session_state['extracted_filename'] = None

    # --- UPLOADER ---
    # Only show uploader if we're not currently processing a file preview
    # This keeps the UI focused
    if not st.session_state['ingestion_queue']:
        st.markdown("### :material/upload_file: Step 1: Upload Schedules")
        uploaded_files = st.file_uploader(
            "Choose one or more schedule files (PDF/Excel)", 
            type=["pdf", "xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_{st.session_state['uploader_key']}"
        )
        
        if uploaded_files:
            # Move files to queue and reset uploader
            st.session_state['ingestion_queue'].extend(uploaded_files)
            st.session_state['uploader_key'] += 1
            st.rerun()
    
    # --- QUEUE PROCESSING ---
    if st.session_state['ingestion_queue']:
        queue = st.session_state['ingestion_queue']
        current_file = queue[0]
        filename = current_file.name
        
        st.info(f":material/list: **Ingestion Queue:** {len(queue)} file(s) pending. Currently reviewing: `{filename}`")
        
        # --- STEP 1: EXTRACTION (Auto-run for current file) ---
        if st.session_state['df_extracted'] is None:
            # CHECK FOR DUPLICATE
            if check_duplicate(filename) and not st.session_state.get('bypass_duplicate'):
                st.error(f":material/block: **Duplicate Found:** `{filename}` has already been uploaded.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Ignore and process anyway"):
                        st.session_state['bypass_duplicate'] = True
                        st.rerun()
                with c2:
                    if st.button("Skip this file"):
                        st.session_state['ingestion_queue'].pop(0)
                        st.rerun()
                st.stop() # Wait for user action

            with st.status(f"Processing `{filename}`...", expanded=True) as status:
                # 1. Data Extraction
                st.write("Running extraction engine...")
                df_processed, error = process_file(io.BytesIO(current_file.getvalue()), filename)
                
                if error:
                    status.update(label="Extraction Failed", state="error")
                    st.error(f":material/cancel: **Error Details:** {error}")
                    if st.button("Skip this file"):
                        st.session_state['ingestion_queue'].pop(0)
                        st.rerun()
                else:
                    # Save to session state for the next step
                    st.session_state['df_extracted'] = df_processed
                    st.session_state['extracted_filename'] = filename
                    status.update(label="Extraction Complete!", state="complete")
                    st.rerun()

        # --- STEP 2: PREVIEW & CONFIRMATION ---
        else:
            df_processed = st.session_state['df_extracted']

            # 0. Extraction summary
            airline_name = df_processed['AIRLINE'].iloc[0] if not df_processed.empty else "Unknown"
            row_count = len(df_processed)
            c_a, c_r = st.columns(2)
            c_a.metric(":material/airlines: Airline Detected", airline_name)
            c_r.metric(":material/table_rows: Movements Processed", row_count)

            # 1. Date Verification
            st.markdown("### :material/calendar_month: Step 2: Verify Schedule Date")
            current_date = df_processed['DATE TIME LOCAL'].iloc[0].date() if not df_processed.empty else datetime.now().date()
            selected_date = st.date_input("The system detected the following date. Please correct if necessary:", value=current_date)
            
            if selected_date != current_date:
                # Recalculate timestamps
                st.write("Updating timestamps...")
                df_processed['DATE TIME LOCAL'] = df_processed['DATE TIME LOCAL'].apply(
                    lambda dt: dt.replace(year=selected_date.year, month=selected_date.month, day=selected_date.day)
                )
                df_processed['DATE TIME UTC'] = df_processed['DATE TIME LOCAL'] - pd.Timedelta(hours=5)
                st.session_state['df_extracted'] = df_processed
                st.rerun()

            with st.expander(":material/analytics: Preview Extracted Data", expanded=True):
                st.dataframe(df_processed, use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns([1, 4])
            with c1:
                if st.button(":material/cancel: Cancel/Skip", use_container_width=True):
                    st.session_state['ingestion_queue'].pop(0)
                    st.session_state['df_extracted'] = None
                    st.session_state['extracted_filename'] = None
                    st.rerun()
            with c2:
                if st.button(":material/check_circle: Confirm & Save to Database", type="primary", use_container_width=True):
                    with st.status("Finalizing Ingestion...", expanded=True) as status:
                        # 1. SAVE TO LOCAL SQLITE
                        st.write("Saving to Local Database...")
                        # Add filename tag for cascading deletes
                        df_processed['FILENAME'] = filename
                        
                        # Normalize REG to 8Q- format
                        if 'REG' in df_processed.columns:
                            df_processed['REG'] = df_processed['REG'].astype(str).str.replace('8Q', '8Q-', regex=False).str.replace('8Q--', '8Q-', regex=False)

                        database.save_movements(df_processed)
                        database.log_file_local(filename)
                        
                        # D. CLEANUP & NEXT IN QUEUE
                        st.session_state['ingestion_queue'].pop(0)
                        st.session_state['df_extracted'] = None
                        st.session_state['extracted_filename'] = None
                        status.update(label="Ingestion Successful!", state="complete")
                        st.success(f"Successfully processed `{filename}`.")
                        if not st.session_state['ingestion_queue']:
                            st.balloons()
                        time.sleep(1)
                        st.rerun()



else: # Operational Analytics
    st.header("Fleet Operational Insights")
    # Load using the modular insights engine
    master_data = load_master_data()
    if not master_data.empty:
        generate_performance_visuals(master_data)
    else:
        st.info("No operational data available in the local database. Please ingest schedules in the Ingestion page.")