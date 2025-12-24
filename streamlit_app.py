import streamlit as st
import tempfile
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Set page title
st.set_page_config(page_title="Scientific Slide Library", page_icon="🔬")
st.title("🔬 Scientific Slide Library Uploader")
st.markdown("Use the form below to upload your slides and update the tracking sheet.")

# 1. AUTHENTICATION (Using Streamlit Secrets)
try:
    # Get IDs and JSON contents from Secrets
    SHEET_ID = st.secrets["SHEET_ID"]
    FOLDER_ID = st.secrets["FOLDER_ID"]
    
    # Map the service account keys from the [gcp_service_account] section in Secrets
    credentials_info = st.secrets["gcp_service_account"]
    
    creds = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file"
        ]
    )
    
    # Build the API services
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
except Exception as e:
    st.error("⚠️ Authentication Error: Please check your Streamlit 'Secrets' configuration.")
    st.stop()

# 2. THE UPLOAD FORM
with st.form("upload_form", clear_on_submit=True):
    name = st.text_input("Presenter Name")
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
                row_data = [[name, description, keywords, file_link]]
                
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