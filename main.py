import streamlit as st
import requests
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseUpload
import os
import io 

st.title("Seaplane Movements")

MALDIVIAN_FOLDER_ID = "1yL63EAYl7HLh0rgsIvJfNzWkBWUH0OT9"  # Replace with your actual folder ID

def upload_to_drive(file_name, file_content, folder_id):
    """
    Uploads a file to Google Drive using a Service Account.
    file_content should be the bytes from streamlit's st.file_uploader
    """
    # Load credentials from Streamlit Secrets
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["connections"],
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    # Wrap bytes in a buffer for the upload
    media = MediaIoBaseUpload(io.BytesIO(file_content), 
                              mimetype='application/octet-stream', 
                              resumable=True)
    
    file = service.files().create(body=file_metadata, 
                                  media_body=media, 
                                  fields='id').execute()
    return file.get('id')


uploaded_file = st.file_uploader("Choose a file")

if uploaded_file is not None:
    binary_data = uploaded_file.read()
    file_id = upload_to_drive(uploaded_file.name, binary_data, MALDIVIAN_FOLDER_ID)
    st.success(f"File uploaded successfully with ID: {file_id}")
