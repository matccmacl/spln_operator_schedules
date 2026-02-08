import streamlit as st
import requests
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseUpload
from processors import combine_tables, clean_tables_maldivian
import os
import io
import time

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

    filename = uploaded_file.name
    #combined_df, date_object = combine_tables(uploaded_file, filename)
    #cleaned_df = clean_tables_maldivian(combined_df, date_object)
    #t.dataframe(cleaned_df)

    # 1. Add a start button
    if st.button("Start Processing Schedule"):

        # 2. Initialize a progress bar and status text
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Stage 1: Extraction
            status_text.text("Extracting tables from PDF (this may take a moment)...")
            progress_bar.progress(25)
            combined_df, date_object = combine_tables(uploaded_file, filename)

            # Stage 2: Cleaning
            status_text.text("Cleaning and standardizing data...")
            progress_bar.progress(60)
            cleaned_df = clean_tables_maldivian(combined_df, date_object)

            # Stage 3: Completion
            progress_bar.progress(100)
            status_text.text("Processing complete!")
            time.sleep(1) # Brief pause so the user sees 100%

            # Clear progress indicators
            status_text.empty()
            progress_bar.empty()

            # 3. Display results
            st.success(f"Successfully processed {len(cleaned_df)} movements for {date_object.strftime('%d %b %Y')}")
            st.dataframe(cleaned_df)

            # Store cleaned_df in session state so it persists for the graph
            st.session_state['cleaned_df'] = cleaned_df

        except Exception as e:
            st.error(f"An error occurred: {e}")
            progress_bar.empty()
            status_text.empty()

        if 'cleaned_df' in st.session_state:
            df = st.session_state['cleaned_df']

            st.subheader("Flight Movements Over Time")

            # Simple grouping for the bar chart
            chart_data = df.groupby(pd.Grouper(key='DATE TIME UTC', freq='h'))['REG'].count().reset_index()
            chart_data.columns = ['Time', 'Flight Count']

            st.bar_chart(data=chart_data, x='Time', y='Flight Count')