import streamlit as st
import pandas as pd

# 5) BACKGROUND COLOR - Tag: BACKGROUND_STYLE
# This injects custom CSS to change the main app background to light grey
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f0f0f0;
    }
    </style>
    """,
    unsafe_content_as_allowed=True
)

# 4) HEADER TEXT - Tag: HEADER_SECTION
# Edit the strings below to customize your page introduction
st.title("Document Management Library")
st.markdown("""
    Welcome to the Digital Library. Here you can browse all stored files, 
    view them directly in Google Sheets, or download them to your local device.
""")
# --- END HEADER SECTION ---

# 1) SWAP TABS - "Library" is now the first index (Default)
tab1, tab2 = st.tabs(["📚 View Library", "📤 Upload New File"])

with tab1:
    # Sample Data - Replace this with your actual Google Sheet / Dataframe logic
    data = {
        "File Name": ["Project_Alpha_Specs.pdf", "Budget_2024.xlsx", "Team_Contact_List.csv"],
        "Description": [
            "Full technical specifications for the Alpha project initiative including timeline.",
            "Complete budget breakdown for the upcoming fiscal year 2024.",
            "Internal contact directory for all department heads and primary stakeholders."
        ],
        "View Link": ["https://docs.google.com/spreadsheets/d/1", "https://docs.google.com/spreadsheets/d/2", "https://docs.google.com/spreadsheets/d/3"],
        "Download Link": ["https://example.com/download1", "https://example.com/download2", "https://example.com/download3"]
    }
    df = pd.DataFrame(data)

    # 2) NARROWER TABLE & WORD WRAP 
    # 3) TWO LINK COLUMNS
    # We use st.column_config to turn URLs into clickable buttons/links
    st.dataframe(
        df,
        column_config={
            "File Name": st.column_config.TextColumn("File Name", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "View Link": st.column_config.LinkColumn("View File", display_text="Open in Sheets"),
            "Download Link": st.column_config.LinkColumn("Download", display_text="Direct Download")
        },
        hide_index=True,
        use_container_width=True # This ensures it fits the "narrower" container feel
    )

with tab2:
    st.header("Upload Section")
    st.file_uploader("Select a file to upload to the library")