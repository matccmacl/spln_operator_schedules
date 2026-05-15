import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io
import time

# Internal Imports
from config import MALDIVIAN_FOLDER_ID, TEST_SHEET_URL, LOG_WORKSHEET, TEST_UPLOAD_SHEET
from processors import process_file
from insights_module import load_master_data, generate_performance_visuals

# --- CONFIGURATION ---
st.set_page_config(page_title="Seaplane Ops Dashboard", layout="wide", page_icon=":material/flight:")

# --- UTILS ---
def get_drive_service():
    try:
        service_account_info = st.secrets["connections"]["gsheets"]
        creds = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Failed to initialize Drive service: {e}")
        return None

def upload_to_drive(file_name, file_content, folder_id):
    service = get_drive_service()
    if not service: return None, None
    file_metadata = {'name': file_name, 'parents': [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype='application/pdf', resumable=True)
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('id'), file.get('webViewLink')
    except Exception as e:
        st.error(f"Drive upload failed: {e}")
        return None, None

def check_duplicate(filename):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        log_df = conn.read(spreadsheet=TEST_SHEET_URL, worksheet=LOG_WORKSHEET, ttl=0)
        if not log_df.empty and 'Filename' in log_df.columns:
            existing_files = log_df['Filename'].astype(str).str.strip().tolist()
            return filename.strip() in existing_files
    except:
        return False
    return False

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
    st.info("Seaplane Ops v1.0")

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
                # 1. Drive Upload
                st.write("Uploading to Google Drive...")
                file_id, file_url = upload_to_drive(filename, current_file.getvalue(), MALDIVIAN_FOLDER_ID)
                
                if file_id:
                    # 2. Metadata Logging
                    st.write("Logging metadata...")
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    current_log = conn.read(spreadsheet=TEST_SHEET_URL, worksheet=LOG_WORKSHEET, ttl=0)
                    new_log_entry = pd.DataFrame([{"Filename": filename, "File URL": file_url, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                    updated_log = pd.concat([current_log, new_log_entry], ignore_index=True)
                    conn.update(spreadsheet=TEST_SHEET_URL, worksheet=LOG_WORKSHEET, data=updated_log)
                    
                    # 3. Data Extraction
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
                else:
                    status.update(label="Drive Upload Failed", state="error")
                    if st.button("Retry"):
                        st.rerun()
                    if st.button("Skip this file"):
                        st.session_state['ingestion_queue'].pop(0)
                        st.rerun()

        # --- STEP 2: PREVIEW & CONFIRMATION ---
        else:
            df_processed = st.session_state['df_extracted']
            
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
                if st.button(":material/check_circle: Confirm & Append to Master Log", type="primary", use_container_width=True):
                    with st.status("Finalizing Ingestion...", expanded=True) as status:
                        st.write("Connecting to Master Log...")
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        master_df = conn.read(spreadsheet=TEST_SHEET_URL, worksheet=TEST_UPLOAD_SHEET, ttl=0)
                        
                        # A. COLUMN ALIGNMENT
                        st.write("Aligning column structures...")
                        if not master_df.empty:
                            target_columns = master_df.columns.tolist()
                            for col in df_processed.columns:
                                if col not in target_columns:
                                    target_columns.append(col)
                            for col in target_columns:
                                if col not in df_processed.columns:
                                    df_processed[col] = None
                            df_processed = df_processed[target_columns]

                        # B. TYPE STANDARDIZATION
                        for col in ['FLT NUMBER', 'REG', 'FROM', 'TO']:
                            if col in df_processed.columns:
                                df_processed[col] = df_processed[col].astype(str)
                            if not master_df.empty and col in master_df.columns:
                                master_df[col] = master_df[col].astype(str)
                        
                        # C. UPDATE
                        st.write("Pushing to Google Sheets...")
                        updated_master = pd.concat([master_df, df_processed], ignore_index=True)
                        conn.update(spreadsheet=TEST_SHEET_URL, worksheet=TEST_UPLOAD_SHEET, data=updated_master)
                        
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
    # Load using the modular insights engine - USE TEST_UPLOAD_SHEET for consistency during testing
    master_data = load_master_data(TEST_SHEET_URL, TEST_UPLOAD_SHEET)
    if not master_data.empty:
        generate_performance_visuals(master_data)
    else:
        st.info("No operational data available in the test sheet. Please ingest schedules in the Ingestion page.")