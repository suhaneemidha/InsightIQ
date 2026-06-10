import streamlit as st

st.title("📂 Upload Dataset")

st.markdown("""
Upload your dataset to begin analysis.

Currently configured for the Olist E-Commerce Dataset.
""")

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"]
)

if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")
    st.info("Dataset processing will be implemented in Phase 3.")
else:
    st.info("Please upload a CSV file.")