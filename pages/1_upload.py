import streamlit as st
from datetime import datetime
from ui.hero import render_page_banner
from ui.layout import apply_global_styles, section_spacer
from ui.sidebar import render_sidebar_brand
from ui.components import (
    section_header,
    sidebar_stat,
    footer,
)

st.set_page_config(
    page_title="InsightIQ Upload Dataset",
    page_icon="📂",
    layout="wide"
)

apply_global_styles()
render_sidebar_brand(
    "InsightIQ",
    "AI-Powered Analytics"
)
render_page_banner(
    icon="📂",
    title="Upload Dataset",
    subtitle="Upload a CSV dataset to begin AI-powered analysis",
    height=180,
)
st.caption("Currently configured for the Olist E-Commerce Dataset.")
st.caption(
    f"Updated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
)

# Sidebar stats
st.sidebar.markdown("---")
st.sidebar.markdown("**Dataset Stats**")
sidebar_stat("1.", "Orders", "~99,441")
sidebar_stat("2.", "Customers", "~99,441")
sidebar_stat("3.", "Sellers", "~3,095")
st.sidebar.caption("📅 September 2016 – October 2018")

# File Upload Logic
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