import streamlit as st

st.title("💬 Ask a Question")
st.markdown("Type a question about the data below.")

user_query = st.text_input("Your question", placeholder="e.g. What are the top 5 sellers by revenue?")

if user_query:
    with st.spinner("Thinking..."):
        # Stub — no real backend yet
        st.info(f"You asked: **{user_query}**")
        st.warning("Backend not connected yet — coming in Phase 2!")