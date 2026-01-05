import streamlit as st
import pandas as pd
import tempfile
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 1. SETTINGS & AUTHENTICATION ---
SPREADSHEET_ID = st.secrets["SHEET_ID"]
FOLDER_ID = st.secrets["FOLDER_ID"]
SHEET_ID = SPREADSHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_gdrive_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["service_account"],
        scopes=SCOPES
    )

    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)

    return drive_service, sheets_service


# Initialize the services
try:
    drive_service, sheets_service = get_gdrive_service()
except Exception as e:
    st.error(f"Authentication Failed: {e}")
    st.stop()


# --- 2. APP INTERFACE CONFIG ---
st.set_page_config(
    page_title="Scientific Slide Library",
    layout="wide",
    page_icon="🔬"
)

# --- 3. GLOBAL STYLES ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #e6e6e6;
    }

    div[data-testid="stDataFrame"] {
        background-color: white;
        border-radius: 8px;
        padding: 6px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }

    div[data-testid="stDataFrame"] td {
        white-space: normal !important;
        word-wrap: break-word;
    }

    div[data-testid="stDataFrame"] tr:hover {
        background-color: #f5f7fa;
    }

    h1, h2, h3 {
        color: #2c2c2c;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 4. HEADER ---
st.title("🔬 Scientific Slide Library")
st.markdown(
    """
    Welcome to the central resource repository.  
    Browse curated scientific presentations, search for specific topics,
    and access downloadable files directly.
    """
)

# --- 5. TABS ---
tab1, tab2 = st.tabs(["📚 Browse Library", "📤 Upload New Slides"])


# =========================
# 📚 TAB 1: BROWSE LIBRARY
# =========================
with tab1:
    st.header("Library Database")

    st.subheader("🔍 Search Library")
    search_query = st.text_input(
        "",
        placeholder="Search by title, description, keyword, or contact…"
    )

    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="Sheet1!A:Z"
        ).execute()

        values = result.get("values", [])

        if not values:
            st.info("The library is currently empty. Start by uploading a file!")
        else:
            df = pd.DataFrame(values[1:], columns=values[0])

            # --- CREATE DOWNLOAD LINK ---
            def make_download_url(view_url):
                try:
                    if "drive.google.com" in view_url:
                        file_id = view_url.split("/d/")[1].split("/")[0]
                        return f"https://drive.google.com/uc?export=download&id={file_id}"
                    return view_url
                except Exception:
                    return view_url

            if "Link" in df.columns:
                df["Download"] = df["Link"].apply(make_download_url)

            # --- SEARCH FILTER ---
            if search_query:
                df = df[df.apply(
                    lambda row: row.astype(str).str.contains(search_query, case=False).any(),
                    axis=1
                )]

            # --- COLUMN ORDERING ---
            desired_order = [
                "Presentation Title",
                "Description",
                "Keywords",
                "Person",      # Contact
                "Link",        # View
                "Download"     # Download
            ]
            df = df[[c for c in desired_order if c in df.columns]]

            # --- DISPLAY TABLE ---
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                height=600,
                column_config={
                    "Presentation Title": st.column_config.TextColumn(
                        "Title", width="medium"
                    ),
                    "Description": st.column_config.TextColumn(
                        "Description", width="large"
                    ),
                    "Keywords": st.column_config.TextColumn(
                        "Keywords", width="small"
                    ),
                    "Person": st.column_config.TextColumn(
                        "Contact", width="small"
                    ),
                    "Link": st.column_config.LinkColumn(
                        "View", display_text="👁️ Open"
                    ),
                    "Download": st.column_config.LinkColumn(
                        "Download", display_text="📥 Download"
                    )
                }
            )

            if st.button("🔄 Refresh Database"):
                st.rerun()

    except Exception as e:
        st.error(f"Could not load the database: {e}")


# =========================
# 📤 TAB 2: UPLOAD NEW FILE
# =========================
with tab2:
    st.header("Contribute to the Library")
    st.write("Upload your slides and provide the associated metadata.")

    with st.form("upload_form", clear_on_submit=True):
        person = st.text_input("Your Name")
        name = st.text_input("Presentation Title")
        description = st.text_area("Topic / Description")
        keywords = st.text_input("Keywords (comma separated)")
        uploaded_file = st.file_uploader(
            "Choose Presentation File (PDF, PPTX, etc.)"
        )

        submit_button = st.form_submit_button("Submit Entry")

    if submit_button:
        if not name or not description:
            st.warning("Please provide at least a title and a description.")
        else:
            with st.spinner("Processing upload..."):
                file_link = "No file uploaded"
                st.write("Drive service auth:", drive_service._http.credentials.__class__)


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
                            fields="id, webViewLink",
                            supportsAllDrives=True
                        ).execute()

                        file_link = uploaded_drive_file.get("webViewLink")

                    except Exception as e:
                        st.error(f"Drive Error: {e}")
                        st.error("Drive upload failed")
                        st.exception(e)
                        st.stop()

                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

                try:
                    row_data = [[
                        name,
                        description,
                        keywords,
                        file_link,
                        person
                    ]]

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
