import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))

st.set_page_config(
    page_title="InsightIQ",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_stats():
    try:
        import duckdb
        #conn = duckdb.connect("olist.db", read_only=True)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(BASE_DIR, "olist.db")
        conn = duckdb.connect(DB_PATH, read_only=True)
        
        stats = {
            "orders":    conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
            "customers": conn.execute("SELECT COUNT(DISTINCT customer_id) FROM customers").fetchone()[0],
            "sellers":   conn.execute("SELECT COUNT(DISTINCT seller_id) FROM sellers").fetchone()[0],
            "date_min":  conn.execute("SELECT MIN(order_purchase_timestamp) FROM orders").fetchone()[0],
            "date_max":  conn.execute("SELECT MAX(order_purchase_timestamp) FROM orders").fetchone()[0],
        }
        conn.close()
        return stats
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

stats = load_stats()

st.sidebar.title("📊 InsightIQ")
st.sidebar.markdown("AI-powered analytics — Olist E-Commerce")
st.sidebar.markdown("---")

if stats:
    st.sidebar.metric("Total Orders", f"{stats['orders']:,}")
    st.sidebar.metric("Customers", f"{stats['customers']:,}")
    st.sidebar.metric("Sellers", f"{stats['sellers']:,}")
    date_min = str(stats['date_min'])[:10]
    date_max = str(stats['date_max'])[:10]
    st.sidebar.caption(f"📅 {date_min} → {date_max}")
else:
    st.sidebar.warning("DB not loaded yet. Run `python core/data_store.py` first.")

st.title("Welcome to InsightIQ 👋")
st.markdown("Ask questions about Olist e-commerce data in plain English. Use the sidebar to navigate.")
st.info("⬅️ Navigate using the sidebar.")