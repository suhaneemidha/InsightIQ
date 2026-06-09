import streamlit as st

st.set_page_config(
    page_title="InsightIQ",
    page_icon="📊",
    layout="wide"
)

st.sidebar.title("📊 InsightIQ")
st.sidebar.markdown("AI-powered analytics for Olist E-Commerce data")
st.sidebar.markdown("---")
st.sidebar.markdown("**Navigation**")

st.title("Welcome to InsightIQ 👋")
st.markdown("""
Ask questions about Olist e-commerce data in plain English.
Use the sidebar to navigate between pages.
""")