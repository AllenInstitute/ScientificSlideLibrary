import streamlit as st
import pandas as pd
import tempfile
import os
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# =========================
# CONFIG & AUTH
# =========================

# Combined Scopes for both Sheets and Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]

SHEET_ID = st.secrets["SHEET_ID"]
FOLDER_ID = st.secrets["FOLDER_ID"]

def get_google_service(service_name, version):
    """
    Authenticate using Service Account secrets stored in Streamlit Cloud.
    No local JSON files needed!
    """
    # Load credentials from Streamlit Secrets
    creds_info = st.secrets["service_account"]
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES
    )
    return build(service_name, version, credentials=creds)

# --- Initialize Services ---
sheets_service = get_google_service("sheets", "v4")
drive_service = get_google_service("drive", "v3")

# =========================
# APP INTERFACE CONFIG
# =========================
st.set_page_config(
    page_title="Scientific Slide Library",
    layout="wide",
    page_icon="🔬"
)

st.markdown(
    """
    <style>
    .stApp { background-color: #e6e6e6; }
    div[data-testid="stDataFrame"] { background-color: white; border-radius: 8px; padding: 6px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔬 Scientific Slide Library")
tab1, tab2 = st.tabs(["📚 Browse Library", "📤 Upload New Slides"])

# =========================
# 📚 TAB 1: BROWSE LIBRARY
# =========================
with tab1:
    st.header("Library Database")
    search_query = st.text_input("🔍 Search", placeholder="Search topics...")

    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range="Sheet1!A:Z"
        ).execute()
        values = result.get("values", [])

        if not values:
            st.info("The library is currently empty.")
        else:
            df = pd.DataFrame(values[1:], columns=values[0])

            if search_query:
                df = df[df.apply(lambda r: r.astype(str).str.contains(search_query, case=False).any(), axis=1)]

            st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Could not load database: {e}")

# =========================
# 📤 TAB 2: UPLOAD NEW FILE
# =========================
with tab2:
    st.header("Contribute to the Library")
    
    with st.form("upload_form", clear_on_submit=True):
        person = st.text_input("Your Name")
        title = st.text_input("Presentation Title")
        description = st.text_area("Topic / Description")
        keywords = st.text_input("Keywords")
        uploaded_file = st.file_uploader("Choose File")
        submit_button = st.form_submit_button("Submit Entry")

    if submit_button:
        if not title or not uploaded_file:
            st.warning("Please provide a title and a file.")
        else:
            with st.spinner("Uploading to Google Drive..."):
                try:
                    # 1. Save uploaded file to a temporary location
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    # 2. Upload to Drive (Specifically into the FOLDER_ID)
                    file_metadata = {
                        "name": uploaded_file.name,
                        "parents": [FOLDER_ID] 
                    }
                    media = MediaFileUpload(tmp_path, resumable=True)
                    drive_file = drive_service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields="id, webViewLink"
                    ).execute()
                    
                    file_link = drive_file.get("webViewLink")

                    # 3. Append to Google Sheets
                    row_data = [[title, description, keywords, file_link, person]]
                    sheets_service.spreadsheets().values().append(
                        spreadsheetId=SHEET_ID,
                        range="Sheet1!A1",
                        valueInputOption="USER_ENTERED",
                        body={"values": row_data}
                    ).execute()

                    st.success("✅ Success! File uploaded and Sheet updated.")
                    st.balloons()
                    
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

                except Exception as e:
                    st.error(f"Error: {e}")