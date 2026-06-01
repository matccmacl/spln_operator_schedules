import streamlit as st
import pandas as pd
import io
import time
from datetime import datetime
import src.database as database
from src.processors import process_file
from src.ui.components import load_master_data

def check_duplicate(filename: str) -> bool:
    """Checks the local SQLite database for previously processed files."""
    return database.check_file_processed_local(filename)

def render_view_ingestion():
    """
    Renders the multi-file Ingestion Wizard.
    Runs extraction, schedule date confirmation, and database transactions.
    """
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
                        st.session_state['bypass_duplicate'] = False
                        st.rerun()
                st.stop() # Wait for user action

            with st.status(f"Processing `{filename}`...", expanded=True) as status:
                # Data Extraction
                st.write("Running extraction engine...")
                df_processed, error = process_file(io.BytesIO(current_file.getvalue()), filename)
                
                if error:
                    status.update(label="Extraction Failed", state="error")
                    st.error(f":material/cancel: **Error Details:** {error}")
                    if st.button("Skip this file"):
                        st.session_state['ingestion_queue'].pop(0)
                        st.session_state['bypass_duplicate'] = False
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

            # Extraction summary
            airline_name = df_processed['AIRLINE'].iloc[0] if not df_processed.empty else "Unknown"
            row_count = len(df_processed)
            c_a, c_r = st.columns(2)
            c_a.metric(":material/airlines: Airline Detected", airline_name)
            c_r.metric(":material/table_rows: Movements Processed", row_count)

            # Date Verification
            st.markdown("### :material/calendar_month: Step 2: Verify Schedule Date")
            current_date = df_processed['DATE TIME LOCAL'].iloc[0].date() if not df_processed.empty else datetime.now().date()
            selected_date = st.date_input("The system detected the following date. Please correct if necessary:", value=current_date, key="verify_date_picker")
            
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
                    st.session_state['bypass_duplicate'] = False
                    st.rerun()
            with c2:
                if st.button(":material/check_circle: Confirm & Save to Database", type="primary", use_container_width=True):
                    with st.status("Finalizing Ingestion...", expanded=True) as status:
                        # SAVE TO LOCAL SQLITE
                        st.write("Saving to Local Database...")
                        # Add filename tag for cascading deletes
                        df_processed['FILENAME'] = filename
                        
                        # Normalize REG to 8Q- format
                        if 'REG' in df_processed.columns:
                            df_processed['REG'] = df_processed['REG'].astype(str).str.replace('8Q', '8Q-', regex=False).str.replace('8Q--', '8Q-', regex=False)

                        database.save_movements(df_processed)
                        database.log_file_local(filename)
                        
                        # Evict the cached master data loader so the analytics page displays fresh data
                        load_master_data.clear()
                        
                        # CLEANUP & NEXT IN QUEUE
                        st.session_state['ingestion_queue'].pop(0)
                        st.session_state['df_extracted'] = None
                        st.session_state['extracted_filename'] = None
                        st.session_state['bypass_duplicate'] = False
                        
                        status.update(label="Ingestion Successful!", state="complete")
                        st.success(f"Successfully processed `{filename}`.")
                        if not st.session_state['ingestion_queue']:
                            st.balloons()
                        time.sleep(1)
                        st.rerun()
