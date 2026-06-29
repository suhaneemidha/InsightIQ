import streamlit as st

from ui.layout import apply_global_styles, section_spacer
from ui.sidebar import render_sidebar_brand
from ui.components import (
    section_header,
    footer,
)
apply_global_styles()

render_sidebar_brand(
    "InsightIQ",
    "AI-powered analytics"
)

section_header(
    "📂 Upload Dataset",
    "Upload a CSV dataset to begin AI-powered analysis." 
)
st.caption("Currently configured for the Olist E-Commerce Dataset.")

uploaded_file = st.file_uploader(
    "Choose a CSV File",
    type=["csv"],
    help="Supported format: CSV"
)

if uploaded_file:
    st.success(f"✅ {uploaded_file.name} uploaded successfully.")
    st.caption(
    "Dataset processing and automatic profiling will be completed in the following pages."
)
else:
    st.info("Please upload a CSV file.")


footer("InsightIQ • Dataset Upload")