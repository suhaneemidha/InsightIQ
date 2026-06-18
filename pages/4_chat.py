import streamlit as st
from core.pipeline import run_pipeline



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

                pipeline_result = run_pipeline(prompt)

                sql = pipeline_result["sql_result"]["sql"]
                execution = pipeline_result["execution_result"]
                insights = pipeline_result["insights"]

                st.code(sql, language="sql")

                if execution["success"]:

                    st.dataframe(
                        execution["data"],
                        use_container_width=True
                    )

                    if insights:

                        st.subheader("💡 Insights")

                        for insight in insights:
                            st.markdown(f"- {insight}")

                    
                    if "confidence" in pipeline_result:

                        score = pipeline_result["confidence"]["score"]
                        signals = pipeline_result["confidence"]["signals"]

                        if score >= 80:
                            color = "green"
                            label = "High Confidence"

                        elif score >= 55:
                            color = "orange"
                            label = "Medium Confidence"

                        else:
                            color = "red"
                            label = "Low Confidence"

                        st.markdown(
                            f"""
                            <div style="
                                display:inline-block;
                                background-color:{color};
                                color:white;
                                padding:6px 16px;
                                border-radius:20px;
                                font-weight:bold;
                                font-size:14px;
                            ">
                                {label}: {score}/100
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        with st.expander("See confidence breakdown"):

                            st.write(
                                f"**Retrieval quality:** {signals['retrieval']}/30"
                            )

                            st.write(
                                f"**SQL validity:** {signals['sql_validity']}/30"
                            )

                            st.write(
                                f"**LLM confidence:** {signals['llm_confidence']}/20"
                            )

                            st.write(
                                f"**Feedback match:** {signals['feedback_match']}/20"
                            )


                    response = (
                        f"✅ Query executed successfully.\n\n"
                        f"Rows returned: {execution['row_count']}"
                    )

                else:

                    response = (
                        f"❌ SQL execution failed:\n\n"
                        f"{execution['error']}"
                    )

                    st.error(response)

            except Exception as e:

                response = f"❌ Error:\n\n{str(e)}"

                st.error(response)

        st.markdown(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )