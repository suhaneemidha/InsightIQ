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

# Handle follow-up chip clicks
if "pending_followup" in st.session_state and st.session_state.pending_followup:
    followup_q = st.session_state.pending_followup
    st.session_state.pending_followup = None   # clear it

    # Treat it exactly like a user typed it
    st.session_state.messages.append({"role": "user", "content": followup_q})
    # Rerun will now show it in chat and the user can submit
    # (We can't auto-run it without a second rerun cycle, so we just pre-fill the last message)
    
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

                    # After the confidence badge expander block, add:
                    # -------------------------------------------------------
                    # Follow-up question chips
                    # -------------------------------------------------------
                    from core.insight_generator import generate_followup_questions

                    if execution["success"] and execution["data"] is not None:
                        df_preview = execution["data"].head(5).to_string(index=False)

                        followups = generate_followup_questions(prompt, df_preview)

                        if followups:
                            st.markdown("**You might also want to ask:**")
                            col1, col2 = st.columns(2)

                            with col1:
                                if st.button(f"💬 {followups[0]}", key="followup_0"):
                                    # Pre-fill the chat with this question
                                    # Streamlit doesn't allow programmatic chat_input fill,
                                    # so we store it in session state and show it as a new message
                                    st.session_state.pending_followup = followups[0]
                                    st.rerun()

                            with col2:
                                if len(followups) > 1:
                                    if st.button(f"💬 {followups[1]}", key="followup_1"):
                                        st.session_state.pending_followup = followups[1]
                                        st.rerun()
                    
                    
                    if insights:
                        response = "\n".join(insights)
                    else:
                        response = f"Query executed successfully. Returned {execution['row_count']} rows."
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