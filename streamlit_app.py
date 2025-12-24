import streamlit as st
import pandas as pd
import tempfile 
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- 1. SETTINGS & AUTHENTICATION ---
SPREADSHEET_ID = st.secrets["SHEET_ID"]
FOLDER_ID = st.secrets["FOLDER_ID"]
SHEET_ID = SPREADSHEET_ID

def get_gdrive_service():
    """Authenticates using the OAuth Refresh Token from st.secrets"""
    creds_info = st.secrets["google_oauth"]
    creds = Credentials(
        token=None, 
        refresh_token=creds_info["refresh_token"],
        client_id=creds_info["client_id"],
        client_secret=creds_info["client_secret"],
        token_uri="https://oauth2.googleapis.com/token"
    )
    if not creds.valid:
        creds.refresh(Request())
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    return drive_service, sheets_service

# Initialize the services
try:
    drive_service, sheets_service = get_gdrive_service()
except Exception as e:
    st.error(f"Authentication Failed: {e}")
    st.stop()

# --- 2. APP INTERFACE CONFIG ---
st.set_page_config(page_title="Scientific Slide Library", layout="wide", page_icon="🔬")

# 5) BACKGROUND COLOR - Tag: BACKGROUND_STYLE
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f0f0f0;
    }
    .stDataFrame {
        background-color: white;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 4) HEADER TEXT - Tag: HEADER_SECTION
# Feel free to edit the text inside these quotes
st.title("🔬 Scientific Slide Library")
st.markdown("""
    Welcome to the central resource repository. Use this dashboard to browse through 
    curated scientific presentations, search for specific topics, and access files directly.
""")
# --- END HEADER SECTION ---

# 1) SWAP TABS - Browse Library is now first (Default)
tab1, tab2 = st.tabs(["📚 Browse Library", "📤 Upload New Slides"])

with tab1:
    st.header("Library Database")
    st.write("Search, filter, and access all stored presentations.")
    
    try:
        # Fetch all data from the Google Sheet
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID, range="Sheet1!A:Z"
        ).execute()
        
        values = result.get('values', [])

        if not values:
            st.info("The library is currently empty. Start by uploading a file!")
        else:
            # Create a DataFrame (assumes headers: Name, Description, Keywords, Link, Person)
            df = pd.DataFrame(values[1:], columns=values[0])
            
            # --- 3) TWO LINK COLUMNS LOGIC ---
            # We create a "Download" link by modifying the Google Drive "View" link
            # Converting 'file/d/ID/view' to 'uc?export=download&id=ID'
            def make_download_url(view_url):
                try:
                    if "drive.google.com" in view_url:
                        file_id = view_url.split("/d/")[1].split("/")[0]
                        return f"https://drive.google.com/uc?export=download&id={file_id}"
                    return view_url
                except:
                    return view_url

            if "Link" in df.columns:
                df["Download"] = df["Link"].apply(make_download_url)

            # Interactive Search
            search_query = st.text_input("Quick Filter", placeholder="Search by name, topic, or keyword...")
            if search_query:
                df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

            # 2) NARROWER TABLE & WORD WRAP 
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Presentation Title": st.column_config.TextColumn("Title", width="medium"),
                    "Description": st.column_config.TextColumn("Topic/Description", width="large"),
                    "Keywords": st.column_config.TextColumn("Keywords", width="small"),
                    "Link": st.column_config.LinkColumn("View File", display_text="👁️ Open Sheets"),
                    "Download": st.column_config.LinkColumn("Download", display_text="📥 Download")
                }
            )
            
            if st.button("Refresh Database"):
                st.rerun()

    except Exception as e:
        st.error(f"Could not load the database: {e}")

with tab2:
    st.header("Contribute to the Library")
    st.write("Upload your slides and fill out the details below.")
    
    with st.form("upload_form", clear_on_submit=True):
        person = st.text_input("Your Name")
        name = st.text_input("Presentation Title")
        description = st.text_area("Topic/Description")
        keywords = st.text_input("Keywords (comma separated)")
        uploaded_file = st.file_uploader("Choose Presentation File (PDF, PPTX, etc.)")
        
        submit_button = st.form_submit_button("Submit Entry")

    if submit_button:
        if not name or not description:
            st.warning("Please provide at least a title and a description.")
        else:
            with st.spinner("Processing upload... please wait."):
                file_link = "No file uploaded"
                
                if uploaded_file is not None:
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    try:
                        file_metadata = {
                            "name": uploaded_file.name,
                            "parents": [FOLDER_ID]
                        }
                        media = MediaFileUpload(tmp_path, resumable=True)
                        
                        uploaded_drive_file = drive_service.files().create(
                            body=file_metadata,
                            media_body=media,
                            fields="id, webViewLink"
                        ).execute()
                        
                        file_link = uploaded_drive_file.get("webViewLink")
                    except Exception as e:
                        st.error(f"Drive Error: {e}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

                try:
                    # Prepare row data (ensure this matches the order of your sheet columns)
                    row_data = [[name, description, keywords, file_link, person]]
                    
                    sheets_service.spreadsheets().values().append(
                        spreadsheetId=SHEET_ID,
                        range="Sheet1!A1",
                        valueInputOption="USER_ENTERED",
                        body={"values": row_data}
                    ).execute()
                    
                    st.success("✅ Entry recorded successfully!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Sheets Error: {e}")