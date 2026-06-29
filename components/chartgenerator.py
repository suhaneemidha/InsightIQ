import streamlit as st
import plotly.express as px
import pandas as pd
import uuid

def suggest_chart(df):
    """
    Suggest a default chart type based on the result.
    """

    if len(df.columns) < 2:
        return None

    x_col = df.columns[0]

    if "date" in x_col.lower():
        return "Line"

    if "month" in x_col.lower():
        return "Line"

    if df[x_col].nunique() <= 8:
        return "Pie"

    return "Bar"


def render_chart(df, key_suffix=""):
    """
    Renders an interactive chart for any query result.
    """

    if df is None or df.empty:
        return

    if len(df.columns) < 2:
        st.info("Not enough columns to generate a chart.")
        return

    x_col = df.columns[0]

    numeric_cols = [
        col
        for col in df.columns
        if pd.api.types.is_numeric_dtype(df[col])
    ]

    if not numeric_cols:
        st.info("No numeric columns available for visualization.")
        return

    y_col = numeric_cols[0]

    default_chart = suggest_chart(df)

    chart_type = st.selectbox(
        "📊 Visualization",
        ["Bar", "Line", "Pie", "Scatter"],
        key=f"chart_type_{key_suffix}",
        index=["Bar", "Line", "Pie", "Scatter"].index(default_chart)
    )

    try:

        if chart_type == "Bar":

            fig = px.bar(
                df,
                x=x_col,
                y=y_col,
                title=f"{y_col} by {x_col}"
            )

        elif chart_type == "Line":

            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=f"{y_col} Trend"
            )

        elif chart_type == "Pie":

            fig = px.pie(
                df,
                names=x_col,
                values=y_col,
                title=f"{y_col} Distribution"
            )

        elif chart_type == "Scatter":

            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                title=f"{x_col} vs {y_col}"
            )
        elif chart_type == "Pie" and len(df) > 10:
            st.warning("Pie charts work best with fewer than 10 categories.")
            
        fig.update_layout(
            height=500
        )

        st.plotly_chart(
            fig,
            width='stretch',
            key=f"chart_{uuid.uuid4()}"
        )

    except Exception as e:
        st.warning(f"Could not generate chart: {e}")