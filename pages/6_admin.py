# pages/6_admin.py
# Admin panel — password protected.
# Shows recent queries, lets admin correct SQL, saves to feedback store.

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime
from ui.layout import apply_global_styles, section_spacer
from ui.sidebar import render_sidebar_brand
from ui.hero import render_page_banner
from ui.components import (
    section_header,
    glass_card,
    sidebar_stat,
    footer,
)

from core.feedback import FeedbackStore
from core.query_history import (
    get_recent_queries,
    init_history_db,
)

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="InsightIQ Admin",
    page_icon="💻",
    layout="wide"
)

apply_global_styles()
render_sidebar_brand(
    "InsightIQ",
    "AI-Powered Analytics"
)
render_page_banner(
    icon="💻",
    title="Admin Panel",
    subtitle="Review generated SQL and improve future responses",
    height=180,
)
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

# -------------------------------------------------------
# Password gate
# -------------------------------------------------------
# Simple hardcoded password for demo purposes.
# In a real app you'd use proper auth.

PASSWORD = "insightiq2024"

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    pwd = st.text_input(
    "Administrator Password",
    type="password",
    placeholder="Enter password..."
    )
    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.admin_authenticated = True
            st.rerun()   # refresh the page to show admin content
        else:
            st.error("Wrong password.")
    st.stop()   # don't render anything else until logged in

# -------------------------------------------------------
# Admin content (only shown after login)
# -------------------------------------------------------

st.success("Administrator authenticated successfully")

if st.button(
    "Logout"
):
    st.session_state.admin_authenticated = False
    st.rerun()

st.divider()

# Initialize DB (creates table if not exists)
init_history_db()

# Load last 10 queries
recent = get_recent_queries(limit=100)

if not recent:
    st.info("No queries logged yet. Run some queries in the Chat page first.")
    st.stop()

# Initialize feedback store
feedback_store = FeedbackStore()

section_header(
    "Recent SQL Queries",
    f"{len(recent)} recent queries available for review."
)

section_spacer(5)

# -------------------------------------------------------
# Show each query as an editable row
# -------------------------------------------------------

for i, row in enumerate(recent):
    StatusIcon = "❌" if not row["success"] else "✅"
    with st.expander(f"{StatusIcon} Query {i+1}: {row['nl_query'][:80]}...", expanded=False):

        # Show original question
        st.markdown(f"**Question**\n\n{row['nl_query']}")
        st.markdown(f"**Confidence:** {row['confidence_score']}/100")
        st.markdown(f"**Timestamp:** {row['timestamp']}")
        
        if not row["success"]:
            st.error(f"❌ Failed: {row['error_message']}")

        # Show generated SQL (read only, for reference)
        st.markdown("**Generated SQL:**")
        glass_card(f"""
        <pre style="margin:0;
        white-space:pre-wrap;
        font-size:.9rem;">
        {row["sql"]}
        </pre>
        """)
        section_spacer(3)
        # Editable text area for correction
        corrected = st.text_area(
            label="**Corrected SQL (edit if wrong):**",
            value=row["sql"],               # pre-filled with generated SQL
            height=150,
            key=f"correction_{i}"           # unique key per row
        )

        # Save button
        if st.button(f"Save Correction", key=f"save_{i}"):
            if corrected.strip() == row["sql"].strip():
                st.warning("SQL is unchanged. Edit it before saving.")
            else:
                feedback_store.save_correction(
                    original_query=row["nl_query"],
                    generated_sql=row["sql"],
                    corrected_sql=corrected.strip(),
                    admin_id="admin"
                )
                st.success("Correction saved! The pipeline will use this in future queries.")
footer("InsightIQ • Admin Panel")