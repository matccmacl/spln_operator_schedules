import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import io

st.set_page_config(page_title="Seaplane File Ingestion", layout="wide")
st.title("Seaplane Schedule Ingestion")

# Constants
MALDIVIAN_FOLDER_ID = "1yL63EAYl7HLh0rgsIvJfNzWkBWUH0OT9"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1yJLPasQSRxUC9Ad1-e0k62aSY0ibVzwbwz8e14fDrBY/"
LOG_WORKSHEET = "uploaded_files"

def get_drive_service():
    """Returns a Google Drive service object using service account secrets."""
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
    """
    Uploads file to Drive and returns the webViewLink.
    """
    service = get_drive_service()
    if not service:
        return None, None

    file_metadata = {'name': file_name, 'parents': [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(file_content),
                              mimetype='application/pdf',
                              resumable=True)

    try:
        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id, webViewLink').execute()
        return file.get('id'), file.get('webViewLink')
    except Exception as e:
        st.error(f"Drive upload failed: {e}")
        return None, None

def check_duplicate(filename):
    """
    Checks if the filename already exists in the 'uploaded_files' sheet.
    Uses ttl=0 to ensure we always get the latest data from the sheet.
    """
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # ttl=0 ensures we don't use cached data for duplicate checks
        log_df = conn.read(spreadsheet=SHEET_URL, worksheet=LOG_WORKSHEET, ttl=0)

        if not log_df.empty and 'Filename' in log_df.columns:
            # Strip whitespace to ensure match works correctly
            existing_files = log_df['Filename'].astype(str).str.strip().tolist()
            return filename.strip() in existing_files
    except Exception as e:
        st.warning(f"Note: Could not verify duplicates (Log sheet might be empty or inaccessible). Error: {e}")
        return False
    return False

# UI Section
uploaded_file = st.file_uploader("Choose a schedule file to upload", type=["pdf", "xlsx", "xls"])

if uploaded_file is not None:
    filename = uploaded_file.name

    st.info(f"Checking for existing record of `{filename}`...")
    is_duplicate = check_duplicate(filename)

    if is_duplicate:
        st.error(f"🚫 **Duplicate Found:** The file `{filename}` has already been uploaded to the system. Upload blocked.")
        if st.button("I understand, but process this local file anyway"):
            st.session_state['ready_to_process'] = True
            st.session_state['current_filename'] = filename
    else:
        st.success(f"✅ `{filename}` is a new file.")
        if st.button("🚀 Upload and Log File"):
            with st.status("Initializing Ingestion...", expanded=True) as status:
                # 1. Upload to Drive
                st.write("Uploading to Google Drive...")
                file_id, file_url = upload_to_drive(filename, uploaded_file.getvalue(), MALDIVIAN_FOLDER_ID)

                if file_id and file_url:
                    # 2. Log to GSheets
                    st.write("Logging metadata to Google Sheets...")
                    conn = st.connection("gsheets", type=GSheetsConnection)

                    # Fetch current log without cache to avoid overwriting
                    current_log = conn.read(spreadsheet=SHEET_URL, worksheet=LOG_WORKSHEET, ttl=0)

                    # Prepare new entry
                    new_entry = pd.DataFrame([{
                        "Filename": filename,
                        "File URL": file_url,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])

                    # Ensure columns match even if sheet was empty/differently structured
                    if current_log.empty:
                        updated_log = new_entry
                    else:
                        updated_log = pd.concat([current_log, new_entry], ignore_index=True)

                    # Update the sheet with the full combined dataframe
                    conn.update(spreadsheet=SHEET_URL, worksheet=LOG_WORKSHEET, data=updated_log)

                    status.update(label="File Ingested Successfully!", state="complete")
                    st.success(f"File logged and saved. [View File]({file_url})")

                    # 3. Set state to prompt for processing
                    st.session_state['ready_to_process'] = True
                    st.session_state['current_filename'] = filename
                else:
                    status.update(label="Upload Failed", state="error")

# Processing Prompt (appears after successful upload or duplicate bypass)
if st.session_state.get('ready_to_process'):
    st.divider()
    st.subheader("Ready for Processing")
    st.write(f"The file `{st.session_state['current_filename']}` is staged. Would you like to proceed with data extraction?")

    if st.button("⚙️ Start Data Extraction"):
        st.info("Processing logic will go here in the next step.")