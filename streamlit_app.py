import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os

# --- 1. SETTINGS & AUTHENTICATION ---

# Replace these with your actual IDs
SPREADSHEET_ID = st.secrets["SHEET_ID"]
FOLDER_ID = st.secrets["FOLDER_ID"]

def get_gdrive_service():
    """Authenticates using the OAuth Refresh Token from st.secrets"""
    creds_info = st.secrets["google_oauth"]
    
    # Create credentials object using your specific Refresh Token
    creds = Credentials(
        token=None,  # Access token starts empty
        refresh_token=creds_info["refresh_token"],
        client_id=creds_info["client_id"],
        client_secret=creds_info["client_secret"],
        token_uri="https://oauth2.googleapis.com/token"
    )

    # Refresh the access token automatically if it's expired
    if not creds.valid:
        creds.refresh(Request())
    
    # Build the services
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    return drive_service, sheets_service

# Initialize the services
try:
    drive_service, sheets_service = get_gdrive_service()
except Exception as e:
    st.error(f"Authentication Failed: {e}")
    st.stop()

# --- APP INTERFACE START ---
st.title("Scientific Slide Library")
st.write("Upload your slides and details below.")

# 2. THE UPLOAD FORM
with st.form("upload_form", clear_on_submit=True):
    person = st.text_input("Your name")
    name = st.text_input("Name of Presentation")
    description = st.text_area("Topic/Description")
    keywords = st.text_input("Keywords (comma separated)")
    
    # Corrected function name: st.file_uploader
    uploaded_file = st.file_uploader("Choose Presentation File (PDF, PPTX, etc.)")
    
    submit_button = st.form_submit_button("Submit Entry")

# 3. PROCESSING
if submit_button:
    if not name or not description:
        st.warning("Please provide at least a name and a description.")
    else:
        with st.spinner("Processing upload... please wait."):
            file_link = "No file uploaded"
            
            # --- STEP A: UPLOAD TO GOOGLE DRIVE ---
            if uploaded_file is not None:
                # Write memory file to a temp file on disk for the Google API to read
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                try:
                    file_metadata = {
                        "name": uploaded_file.name,
                        "parents": [FOLDER_ID]
                    }
                    media = MediaFileUpload(tmp_path, resumable=True)
                    
                    # Create the file in Drive
                    uploaded_drive_file = drive_service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields="webViewLink"
                    ).execute()
                    
                    # Optional: Add this right after the .execute() line if it still fails
                    drive_service.permissions().create(
                        fileId=uploaded_drive_file.get("id"),
                        body={'type': 'anyone', 'role': 'reader'}
                    ).execute()
                    
                    file_link = uploaded_drive_file.get("webViewLink")
                except Exception as e:
                    st.error(f"Drive Error: {e}")
                finally:
                    # Cleanup the temporary file from the server
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

            # --- STEP B: UPDATE GOOGLE SHEET ---
            try:
                # Prepare row data
                row_data = [[name, description, keywords, file_link, person]]
                
                sheets_service.spreadsheets().values().append(
                    spreadsheetId=SHEET_ID,
                    range="Sheet1!A1",
                    valueInputOption="USER_ENTERED",
                    body={"values": row_data}
                ).execute()
                
                st.success("✅ Entry recorded successfully!")
                st.balloons()
            except Exception as e:
                st.error(f"Sheets Error: {e}")