import streamlit as st
import tempfile
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# App Title
st.title("Scientific Slide Library Uploader")

# Load configuration from Streamlit Secrets (for security)
# In Streamlit Cloud, you'll paste your JSON content into the "Secrets" setting
if "gcp_service_account" in st.secrets:
    info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(info)
else:
    # For local testing, looks for your file
    creds = service_account.Credentials.from_service_account_file("service-account.json")

SHEET_ID = st.secrets.get("SHEET_ID", "YOUR_SHEET_ID")
FOLDER_ID = st.secrets.get("FOLDER_ID", "YOUR_FOLDER_ID")

# Initialize Services
sheets_service = build("sheets", "v4", credentials=creds)
drive_service = build("drive", "v3", credentials=creds)

# Simple Form UI
with st.form("upload_form", clear_on_submit=True):
    name = st.text_input("Name")
    description = st.text_area("Description")
    keywords = st.text_input("Keywords")
    uploaded_file = st.file_ Breaker("Choose a file")
    
    submit_button = st.form_submit_button("Submit")

if submit_button:
    if not name or not description:
        st.error("Please provide both a name and a description.")
    else:
        with st.spinner("Uploading..."):
            file_link = ""
            
            # Handle File Upload to Google Drive
            if uploaded_file is not None:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                try:
                    file_metadata = {"name": uploaded_file.name, "parents": [FOLDER_ID]}
                    media = MediaFileUpload(tmp_path, resumable=True)
                    drive_file = drive_service.files().create(
                        body=file_metadata, media_body=media, fields="webViewLink"
                    ).execute()
                    file_link = drive_file.get("webViewLink")
                finally:
                    os.remove(tmp_path)

            # Update Google Sheet
            row = [[name, description, keywords, file_link]]
            sheets_service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID,
                range="Sheet1!A:D",
                valueInputOption="USER_ENTERED",
                body={"values": row}
            ).execute()
            
            st.success(f"Success! Data added to sheet. File link: {file_link}")