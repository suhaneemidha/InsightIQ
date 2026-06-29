import os
import streamlit as st

from ui.layout import (
    apply_global_styles,
    page_container,
    section_spacer,
)

from ui.components import (
    section_header,
    metric_row,
    sidebar_stat,
    render_flow_diagram,
    footer,
    feature_card,
)

from ui.hero import render_hero_section
from ui.sidebar import render_sidebar_brand


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="InsightIQ",
    page_icon="📊",
    layout="wide",
)

# Load complete design system
apply_global_styles()


# ==========================================================
# DATA LAYER (UNCHANGED)
# ==========================================================

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


# ==========================================================
# SIDEBAR
# ==========================================================

render_sidebar_brand(
    "InsightIQ",
    "AI-Powered Business Intelligence"
)

st.sidebar.markdown("---")

if stats:

    sidebar_stat("🛒", "Orders", f"{stats['orders']:,}")
    sidebar_stat("👥", "Customers", f"{stats['customers']:,}")
    sidebar_stat("🏪", "Sellers", f"{stats['sellers']:,}")
    sidebar_stat("📦", "Products", f"{stats['products']:,}")
    sidebar_stat("⭐", "Reviews", f"{stats['reviews']:,}")

    if stats["date_min"] and stats["date_max"]:
        st.sidebar.caption(
            f"📅 {stats['date_min']} → {stats['date_max']}"
        )

    with st.sidebar.expander("Dataset Schema"):

        st.markdown(
            """
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
"""
        )

else:

    st.sidebar.warning(
        "Database could not be loaded."
    )


# ==========================================================
# HOME PAGE
# ==========================================================

render_hero_section(
    badge_text="Business Intelligence Platform",
    title="InsightIQ",
    subtitle=(
        "Explore the Olist e-commerce dataset using natural language. "
        "Chat with your data, generate visualizations, and uncover "
        "business insights in seconds."
    ),
    cta_text="Explore Dashboard",
    height=480,
)

section_spacer(40)

# ==========================================================
# DATASET SNAPSHOT
# ==========================================================

if stats:

    section_header(
        "Dataset Snapshot",
        "A quick overview of the Olist e-commerce database."
    )

    metric_row([
        {
            "label": "Orders",
            "value": f"{stats['orders']:,}"
        },
        {
            "label": "Customers",
            "value": f"{stats['customers']:,}"
        },
        {
            "label": "Products",
            "value": f"{stats['products']:,}"
        },
        {
            "label": "Reviews",
            "value": f"{stats['reviews']:,}"
        },
    ])

    section_spacer(25)


# ==========================================================
# TECHNOLOGY STACK
# ==========================================================

section_header(
    "Technology Stack",
    "Built with a modern analytics and AI ecosystem."
)

metric_row([
    {
        "label": "LLM",
        "value": "Groq",
    },
    {
        "label": "Database",
        "value": "DuckDB",
    },
    {
        "label": "Framework",
        "value": "Streamlit",
    },
    {
        "label": "Dataset",
        "value": "Olist",
    },
])

section_spacer(35)

# ==========================================================
# PROJECT ARCHITECTURE
# ==========================================================

section_header(
    "Project Architecture",
    "How InsightIQ transforms natural language into actionable insights."
)

render_flow_diagram([
    "User Query",
    "Streamlit Interface",
    "Groq LLM",
    "Natural Language → SQL",
    "DuckDB Engine",
    "Olist Database",
    "Results & Visualizations",
])


# ==========================================================
# FOOTER
# ==========================================================

footer("InsightIQ • AI-Powered Business Intelligence • Built with Streamlit")