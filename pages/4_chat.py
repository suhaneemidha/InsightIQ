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

# Initialize pending followup
if "pending_followup" not in st.session_state:
    st.session_state.pending_followup = None

if "followups" not in st.session_state:
    st.session_state.followups = []

# Display chat history
for idx, msg in enumerate(st.session_state.messages):
    
    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])

        if msg["role"] == "assistant":

            if msg.get("sql"):
                st.code(msg["sql"], language="sql")

            if msg.get("data") is not None:
                st.dataframe(
                    msg["data"],
                    use_container_width=True
                )

            if msg.get("confidence"):

                score = msg["confidence"]["score"]

                st.caption(
                    f"Confidence Score: {score}/100"
                )

            if msg.get("followups"):

                st.markdown("#### Related Questions")

                for j, q in enumerate(msg["followups"]):

                    if st.button(
                        q,
                        key=f"history_followup_{idx}_{j}"
                    ):
                        st.session_state.pending_followup = q
                        st.rerun()


# Normal chat input
prompt = st.chat_input(
    "Ask a question about the dataset..."
)

# Override prompt if followup button was clicked
if st.session_state.pending_followup:
    
    prompt = st.session_state.pending_followup

    st.session_state.pending_followup = None

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )
    
# Chat input
if prompt:

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

                        followups = generate_followup_questions(
                            prompt,
                            df_preview
                        )

                        st.session_state.followups = followups or []

                        if st.session_state.followups:

                            st.markdown("---")
                            st.markdown("### 🔁 Related Questions")

                            for i, q in enumerate(st.session_state.followups):

                                if st.button(
                                    q,
                                    key=f"followup_{i}"
                                ):
                                    st.session_state.pending_followup = q
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
        "content": response,
        "sql": sql,
        "data": execution["data"] if execution["success"] else None,
        "confidence": pipeline_result.get("confidence"),
        "followups": st.session_state.followups
    }
)