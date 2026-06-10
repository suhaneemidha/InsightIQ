import streamlit as st

st.title("🕸️ Knowledge Graph")

st.markdown("""
Explore relationships within the Olist dataset.
""")

st.info("Knowledge Graph visualization coming in Phase 4.")

with st.expander("Planned Features"):
    st.markdown("""
    - Customer → Orders
    - Orders → Products
    - Products → Sellers
    - Customer → Reviews
    - Interactive Network Visualization
    """)