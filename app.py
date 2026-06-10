import streamlit as st

st.set_page_config(
    page_title="InsightIQ",
    page_icon="📊",
    layout="wide"
)

# Sidebar
st.sidebar.title("📊 InsightIQ")
st.sidebar.markdown("AI-Powered Analytics for Olist E-Commerce")
st.sidebar.markdown("---")

# Main Page
st.title("📊 InsightIQ")

st.markdown("""
### Welcome 👋

InsightIQ lets you explore e-commerce data using natural language.

#### Features
- 💬 Chat with your data
- 📂 Upload and manage datasets
- 🔍 Automated Exploratory Data Analysis (EDA)
- 🤖 Machine Learning Insights
- 🕸️ Knowledge Graph Visualization

Use the sidebar to navigate between pages.
""")

st.info("⬅️ Open the Chat page from the sidebar to start asking questions.")

# Optional metrics section
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("LLM", "Groq")

with col2:
    st.metric("Database", "DuckDB")

with col3:
    st.metric("Dataset", "Olist")

st.markdown("---")

st.subheader("Project Architecture")

st.code("""
User Question
      ↓
   Streamlit
      ↓
     Groq
      ↓
 Natural Language → SQL
      ↓
    DuckDB
      ↓
   Olist Data
      ↓
  Results & Charts
""")