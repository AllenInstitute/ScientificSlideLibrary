import streamlit as st
import pandas as pd

# 5) BACKGROUND COLOR - Tag: BACKGROUND_STYLE
# Fixed the parameter here to 'unsafe_allow_html=True'
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f0f0f0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 4) HEADER TEXT - Tag: HEADER_SECTION
# Edit the text between the quotes to change your page header
st.title("Document Management Library")
st.markdown("""
    ### Resource Archive
    Use this page to access our shared slide decks and documents. 
    You can preview files in the browser or download them directly.
""")
# --- END HEADER SECTION ---

# 1) SWAP TABS - "Library" is now first (Default)
tab1, tab2 = st.tabs(["📚 View Library", "📤 Upload New File"])

with tab1:
    # This is placeholder data - replace 'df' with your actual Google Sheets dataframe
    data = {
        "File Name": ["Sample_Presentation.pptx", "Data_Analysis_v2.xlsx"],
        "Description": ["A short description of the file.", "A much longer description that will wrap within the cell to keep the table narrow."],
        "View Link": ["https://docs.google.com/spreadsheets/d/1", "https://docs.google.com/spreadsheets/d/2"],
        "Download Link": ["https://example.com/file1", "https://example.com/file2"]
    }
    df = pd.DataFrame(data)

    # 2) NARROWER TABLE & WORD WRAP 
    # 3) TWO LINK COLUMNS
    st.dataframe(
        df,
        column_config={
            "File Name": st.column_config.TextColumn("File Name", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "View Link": st.column_config.LinkColumn("View File", display_text="👁️ View"),
            "Download Link": st.column_config.LinkColumn("Download", display_text="📥 Download")
        },
        hide_index=True,
        use_container_width=True 
    )

with tab2:
    st.header("Upload Section")
    st.write("Upload functionality goes here.")