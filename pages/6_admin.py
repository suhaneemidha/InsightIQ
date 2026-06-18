# pages/6_admin.py
# Admin panel — password protected.
# Shows recent queries, lets admin correct SQL, saves to feedback store.

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.feedback import FeedbackStore
from core.query_history import get_recent_queries, init_history_db

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("Admin SQL Editor")

# -------------------------------------------------------
# Password gate
# -------------------------------------------------------
# Simple hardcoded password for demo purposes.
# In a real app you'd use proper auth.

PASSWORD = "insightiq2024"

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    pwd = st.text_input("Enter admin password", type="password")
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

st.success("Logged in as admin.")

if st.button("Logout"):
    st.session_state.admin_authenticated = False
    st.rerun()

st.divider()

# Initialize DB (creates table if not exists)
init_history_db()

# Load last 10 queries
recent = get_recent_queries(limit=10)

if not recent:
    st.info("No queries logged yet. Run some queries in the Chat page first.")
    st.stop()

# Initialize feedback store
feedback_store = FeedbackStore()

st.subheader(f"Last {len(recent)} Queries")

# -------------------------------------------------------
# Show each query as an editable row
# -------------------------------------------------------

for i, row in enumerate(recent):
    with st.expander(f"Query {i+1}: {row['nl_query'][:80]}..."):

        # Show original question
        st.markdown(f"**Question:** {row['nl_query']}")
        st.markdown(f"**Confidence:** {row['confidence_score']}/100")
        st.markdown(f"**Timestamp:** {row['timestamp']}")

        # Show generated SQL (read only, for reference)
        st.markdown("**Generated SQL:**")
        st.code(row["sql"], language="sql")

        # Editable text area for correction
        corrected = st.text_area(
            label="Corrected SQL (edit if wrong):",
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