import streamlit as st
import pandas as pd

# Set page configuration (optional but recommended for a library app)
st.set_page_config(page_title="Scientific Slide Library", layout="wide")

# 5) BACKGROUND COLOR - Tag: BACKGROUND_STYLE
# This changes the main app background to light grey
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f0f0f0;
    }
    /* Optional: Makes the dataframe container stand out slightly */
    .stDataFrame {
        background-color: white;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 4) HEADER TEXT - Tag: HEADER_SECTION
# You can edit the text inside the triple quotes below
st.title("Scientific Slide Library")
st.markdown("""
    Welcome to the central data repository. Use the table below to browse 
    scientific assets, preview documents, or download them directly.
""")
# --- END HEADER SECTION ---

# 1) SWAP TABS - "View Library" is defined first so it is the default tab
tab1, tab2 = st.tabs(["📚 View Library", "📤 Upload New File"])

with tab1:
    # DATA SECTION: 
    # Replace the 'data' dictionary below with your actual Google Sheets loading logic
    # e.g., df = conn.read(spreadsheet="URL_HERE")
    data = {
        "File Name": [
            "Molecular_Biology_v1.pptx", 
            "Chemical_Structures_Final.pdf", 
            "Lab_Safety_Protocols_2024.docx"
        ],
        "Description": [
            "A comprehensive overview of molecular biology foundations including CRISPR sequences.",
            "High-resolution renders of organic chemical structures for the Q3 presentation.",
            "Updated safety guidelines for all personnel working in the Grade 2 cleanroom environment."
        ],
        "View Link": [
            "https://docs.google.com/presentation/d/1", 
            "https://docs.google.com/viewer?url=example1", 
            "https://docs.google.com/viewer?url=example2"
        ],
        "Download Link": [
            "https://example.com/download/file1", 
            "https://example.com/download/file2", 
            "https://example.com/download/file3"
        ]
    }
    df = pd.DataFrame(data)

    # 2) NARROWER TABLE & WORD WRAP 
    # 3) TWO LINK COLUMNS
    # The 'width' parameter in column_config helps control the 'narrowness' of specific columns
    st.dataframe(
        df,
        column_config={
            "File Name": st.column_config.TextColumn("File Name", width="medium"),
            "Description": st.column_config.TextColumn(
                "Description", 
                width="large",
                help="Text wraps automatically when you click the cell"
            ),
            "View Link": st.column_config.LinkColumn(
                "View File", 
                display_text="👁️ Open in Sheets"
            ),
            "Download Link": st.column_config.LinkColumn(
                "Download", 
                display_text="📥 Download"
            )
        },
        hide_index=True,
        use_container_width=True # Ensures the table fills the center layout but respects column widths
    )

with tab2:
    st.header("Upload New Assets")
    st.info("Select a file below to add it to the library.")
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        st.success(f"File '{uploaded_file.name}' is ready for processing!")