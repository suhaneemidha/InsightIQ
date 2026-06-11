import streamlit as st
import os

st.set_page_config(
    page_title="InsightIQ",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_stats():
    try:
        import duckdb

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(BASE_DIR, "olist.db")

        conn = duckdb.connect(DB_PATH, read_only=True)

        stats = {
            "orders": conn.execute(
                "SELECT COUNT(*) FROM orders"
            ).fetchone()[0],

            "customers": conn.execute(
                "SELECT COUNT(DISTINCT customer_id) FROM customers"
            ).fetchone()[0],

            "sellers": conn.execute(
                "SELECT COUNT(DISTINCT seller_id) FROM sellers"
            ).fetchone()[0],

            "products": conn.execute(
                "SELECT COUNT(*) FROM products"
            ).fetchone()[0],

            "reviews": conn.execute(
                "SELECT COUNT(*) FROM reviews"
            ).fetchone()[0],

            "payments": conn.execute(
                "SELECT COUNT(*) FROM payments"
            ).fetchone()[0],

            "date_min": conn.execute(
                "SELECT MIN(order_purchase_timestamp) FROM orders"
            ).fetchone()[0],

            "date_max": conn.execute(
                "SELECT MAX(order_purchase_timestamp) FROM orders"
            ).fetchone()[0],
        }

        conn.close()
        return stats

    except Exception as e:
        st.error(f"Database error: {e}")
        return None


stats = load_stats()

# ---------------- SIDEBAR ---------------- #

st.sidebar.title("📊 InsightIQ")
st.sidebar.markdown("AI-powered analytics — Olist E-Commerce")
st.sidebar.markdown("---")

if stats:

    st.sidebar.metric("🛒 Orders", f"{stats['orders']:,}")
    st.sidebar.metric("👥 Customers", f"{stats['customers']:,}")
    st.sidebar.metric("🏪 Sellers", f"{stats['sellers']:,}")
    st.sidebar.metric("📦 Products", f"{stats['products']:,}")
    st.sidebar.metric("⭐ Reviews", f"{stats['reviews']:,}")

    if stats["date_min"] and stats["date_max"]:
        st.sidebar.caption(
            f"📅 {stats['date_min']} → {stats['date_max']}"
        )

    with st.sidebar.expander("🗄️ Dataset Schema"):
        st.markdown("""
        **Available Tables**

        - customers
        - orders
        - order_items
        - products
        - sellers
        - payments
        - reviews
        - geolocation
        - category_translation
        """)

else:
    st.sidebar.warning("Database could not be loaded.")

# ---------------- MAIN PAGE ---------------- #

st.title("📊 InsightIQ")

st.markdown("""
### Welcome 👋

InsightIQ lets you explore e-commerce data using natural language.

#### Features

- Chat with your data
- Upload and manage datasets
- Automated Exploratory Data Analysis (EDA)
- Machine Learning Insights
- Knowledge Graph Visualization

Use the sidebar to navigate between pages.
""")

st.info("⬅️ Open the Chat page from the sidebar to start asking questions.")

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