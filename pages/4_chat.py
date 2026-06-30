import streamlit as st
from core.pipeline import run_pipeline
from components.chartgenerator import render_chart
from core.insight_generator import generate_followup_questions
from ui.layout import apply_global_styles, section_spacer
from ui.sidebar import render_sidebar_brand
from ui.components import (
    section_header,
    sidebar_stat,
    footer,
)

st.set_page_config(
    page_title="InsightIQ Chat",
    page_icon="💬",
    layout="wide"
)
apply_global_styles()

render_sidebar_brand(
    "InsightIQ",
    "AI-powered analytics"
)

section_header(
    "💬 InsightIQ Chat",
    "Ask natural language questions about the Olist e-commerce dataset."
)


# Sidebar stats
st.sidebar.markdown("---")
st.sidebar.markdown("**Dataset Stats**")
sidebar_stat("1.", "Orders", "~99,441")
sidebar_stat("2.", "Customers", "~99,441")
sidebar_stat("3.", "Sellers", "~3,095")

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

if "ConversationHistory" not in st.session_state:
    st.session_state.ConversationHistory = []   # list of {question, sql, result}
    
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
                    width='stretch'
                )
                render_chart(
                    msg["data"],
                    key_suffix=f"history_{idx}"
                    )

            if msg.get("confidence")and isinstance(msg["confidence"], dict):

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

        with st.spinner("Analyzing your question..."):
            sql        = None
            execution  = {"success": False, "data": None, "error": "Pipeline did not run."}
            insights   = []
            confidence = None
            followups  = []
            response   = ""

            try:

                pipeline_result = run_pipeline(prompt, ConversationHistory=st.session_state.ConversationHistory,)
                
                # Show cached badge if result came from semantic cache
                if pipeline_result.get("from_cache"):
                    st.info(
                        f"⚡ Cached result — similar to: "
                        f"*\"{pipeline_result.get('cache_hit_query', '')}\"*  "
                        f"(answered instantly)"
                    )
                    
                sql = pipeline_result["sql_result"]["sql"]
                execution = pipeline_result["execution_result"]
                insights = pipeline_result["insights"]
                confidence = pipeline_result.get("confidence")

                st.code(sql, language="sql")

                if execution["success"]:
                    display_df = execution["data"]
                    
                        
                    if len(display_df) > 1000:
                        st.info(
                            f"Showing first 1000 of {len(display_df)} rows"
                        )
                    st.dataframe(
                        display_df,
                        width='stretch',
                        height=700
                    )
                    st.caption(
                        f"Rows Returned: {execution['row_count']}"
)                   
                    csv = execution["data"].to_csv(index=False)
                    st.download_button(
                        label="⬇ Download Full Results",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv"
)
                    section_header("Visualization")

                    display_df = display_df.head(1000)
                    st.dataframe(
                        display_df,
                        width='stretch'
                    )
                    
                    st.caption(
                        f"Rows Returned: {execution['row_count']}"
)                   
                    csv = execution["data"].to_csv(index=False)
                    st.download_button(
                        label="⬇ Download Full Results",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv"
)
                    section_header("Visualization")

                    render_chart(
                        execution["data"],
                        key_suffix=f"current_{len(st.session_state.messages)}"
                    )
                    
                    if insights:

                        section_header("Insights")

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
                                color:#0B0909;
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

                        with st.expander("See confidence breakdown", expanded=False):

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

                    # -------------------------------------------------------
                    # Follow-up question chips
                    # -------------------------------------------------------
                    

                    if execution["success"] and execution["data"] is not None:

                        df_preview = execution["data"].head(5).to_string(index=False)

                        followups = generate_followup_questions(
                            prompt,
                            df_preview,
                            conversation_history=""
                        )

                        st.session_state.followups = followups or []

                        if st.session_state.followups:

                            st.markdown("---")
                            section_header("Suggested Follow-up Questions")

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
                        response = "\n".join(f"- {i}" for i in insights) if insights else "Query executed successfully."
                    
                    # ── Update conversation history for next turn ──────────
                    
                    st.session_state.ConversationHistory.append({
                        "question": prompt,
                        "sql":      sql,
                        "result":   execution["data"].head(5).to_string(index=False)
                                    if execution["data"] is not None else "(empty)",
                    })
                    response = "\n".join(insights) if insights else f"Query executed successfully."
                else:

                    response = (
                        f"❌ SQL execution failed:\n\n"
                        f"{execution['error']}"
                    )

                    st.error(response)

            except Exception as e:

                response = f"❌ Error:\n\n{str(e)}"

                st.error(response)

        

    st.session_state.messages.append(
    {
        "role": "assistant",
        "content": response,
        "sql": sql,
        "data": execution["data"] if execution["success"] else None,
        "confidence":confidence,
        "followups": followups
    }
)
