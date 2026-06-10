import streamlit as st
from core.llm import ask_llm

st.set_page_config(
    page_title="InsightIQ Chat",
    page_icon="💬",
    layout="wide"
)

st.title("💬 InsightIQ Chat")
st.markdown("Ask anything about the Olist e-commerce dataset.")

# Sidebar stats
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Dataset Stats")
st.sidebar.metric("Total Orders", "~99,441")
st.sidebar.metric("Customers", "~99,441")
st.sidebar.metric("Sellers", "~3,095")
st.sidebar.caption("📅 Sep 2016 – Oct 2018")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Hi! I'm InsightIQ.\n\n"
                "Ask me anything about the Olist dataset.\n\n"
                "**Examples:**\n"
                "- Which state has the most delayed deliveries?\n"
                "- Top 5 sellers by revenue\n"
                "- How many orders were delivered?\n"
                "- Which product category has the highest sales?"
            )
        }
    ]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask a question about the dataset..."):

    # User message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = ask_llm(prompt)
            except Exception as e:
                response = f"❌ Error: {str(e)}"

        st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )