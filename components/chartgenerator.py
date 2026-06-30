import streamlit as st
import plotly.express as px
import pandas as pd
import uuid


def suggest_chart(df):

    if len(df.columns) < 2:
        return None

    first_col = df.columns[0].lower()

    if any(
        word in first_col
        for word in ["date", "month", "year", "timestamp"]
    ):
        return "Line"

    if df[df.columns[0]].nunique() <= 8:
        return "Pie"

    return "Bar"


def render_chart(df, key_suffix=""):

    if df is None or df.empty:
        return

    if len(df.columns) < 2:
        st.info("Not enough columns to generate a chart.")
        return

    columns = list(df.columns)

    # --------------------------------------------------
    # Detect dimensions and measures
    # --------------------------------------------------

    dimensions = [
        col
        for col in columns
        if not pd.api.types.is_numeric_dtype(df[col])
    ]

    measures = [
        col
        for col in columns
        if pd.api.types.is_numeric_dtype(df[col])
    ]

    num_dims = len(dimensions)
    num_measures = len(measures)

    if not measures:
        st.info("No numeric columns available for visualization.")
        return

    # --------------------------------------------------
    # Choose x-axis
    # --------------------------------------------------

    time_cols = [
        col
        for col in columns
        if any(
            keyword in col.lower()
            for keyword in [
                "date",
                "month",
                "year",
                "timestamp"
            ]
        )
    ]

    if time_cols:
        x_col = time_cols[0]

    elif dimensions:
        x_col = dimensions[0]

    else:
        x_col = columns[0]

    default_chart = suggest_chart(df)

    chart_type = st.selectbox(
        "📊 Visualization",
        [
            "Bar",
            "Line",
            "Pie",
            "Scatter",
            "Heatmap"
        ],
        key=f"chart_type_{key_suffix}",
        index=[
            "Bar",
            "Line",
            "Pie",
            "Scatter",
            "Heatmap"
        ].index(default_chart)
        if default_chart in [
            "Bar",
            "Line",
            "Pie",
            "Scatter",
            "Heatmap"
        ]
        else 0
    )

    try:

        # ==================================================
        # BAR
        # ==================================================

        if chart_type == "Bar":

            if num_dims >= 2 and num_measures == 1:

                fig = px.bar(
                    df,
                    x=dimensions[0],
                    y=measures[0],
                    color=dimensions[1],
                    barmode="group",
                    title=f"{measures[0]} by {dimensions[0]}"
                )

            elif num_dims >= 2 and num_measures > 1:

                selected_measure = st.selectbox(
                    "Metric",
                    measures,
                    key=f"metric_bar_{key_suffix}"
                )

                fig = px.bar(
                    df,
                    x=dimensions[0],
                    y=selected_measure,
                    color=dimensions[1],
                    barmode="group",
                    title=f"{selected_measure} by {dimensions[0]}"
                )

            else:

                fig = px.bar(
                    df,
                    x=x_col,
                    y=measures,
                    barmode="group",
                    title=f"{', '.join(measures)} by {x_col}"
                )

        # ==================================================
        # LINE
        # ==================================================

        elif chart_type == "Line":

            # month | category | sales

            if num_dims >= 2 and num_measures == 1:

                fig = px.line(
                    df,
                    x=dimensions[0],
                    y=measures[0],
                    color=dimensions[1],
                    markers=True,
                    title=f"{measures[0]} by {dimensions[0]} and {dimensions[1]}"
                )

            # month | category | sales | orders

            elif num_dims >= 2 and num_measures > 1:

                selected_measure = st.selectbox(
                    "Metric",
                    measures,
                    key=f"metric_line_{key_suffix}"
                )

                fig = px.line(
                    df,
                    x=dimensions[0],
                    y=selected_measure,
                    color=dimensions[1],
                    markers=True,
                    title=f"{selected_measure} by {dimensions[0]} and {dimensions[1]}"
                )

            else:

                fig = px.line(
                    df,
                    x=x_col,
                    y=measures,
                    markers=True,
                    title=f"{', '.join(measures)} over {x_col}"
                )

        # ==================================================
        # PIE
        # ==================================================

        elif chart_type == "Pie":

            selected_measure = st.selectbox(
                "Metric",
                measures,
                key=f"metric_pie_{key_suffix}"
            )

            fig = px.pie(
                df,
                names=x_col,
                values=selected_measure,
                title=f"{selected_measure} Distribution"
            )

        # ==================================================
        # SCATTER
        # ==================================================

        elif chart_type == "Scatter":

            if len(measures) >= 2:

                x_metric = st.selectbox(
                    "X Metric",
                    measures,
                    key=f"x_scatter_{key_suffix}"
                )

                y_metric = st.selectbox(
                    "Y Metric",
                    measures,
                    index=min(1, len(measures)-1),
                    key=f"y_scatter_{key_suffix}"
                )

                fig = px.scatter(
                    df,
                    x=x_metric,
                    y=y_metric,
                    color=dimensions[0] if dimensions else None,
                    title=f"{x_metric} vs {y_metric}"
                )

            else:

                st.info(
                    "Scatter chart requires at least two numeric columns."
                )
                return

        # ==================================================
        # HEATMAP
        # ==================================================

        elif chart_type == "Heatmap":

            if num_dims >= 2 and num_measures >= 1:

                selected_measure = st.selectbox(
                    "Metric",
                    measures,
                    key=f"metric_heatmap_{key_suffix}"
                )

                pivot_df = df.pivot_table(
                    index=dimensions[1],
                    columns=dimensions[0],
                    values=selected_measure,
                    aggfunc="sum"
                )

                fig = px.imshow(
                    pivot_df,
                    aspect="auto",
                    title=f"{selected_measure} Heatmap"
                )

            else:

                st.info(
                    "Heatmap requires at least 2 dimensions and 1 measure."
                )
                return

        # ==================================================
        # FINAL DISPLAY
        # ==================================================

        fig.update_layout(
            height=600,
            legend_title_text="Metrics"
        )

        st.plotly_chart(
            fig,
            width='stretch',
            key=f"chart_{uuid.uuid4()}"
        )

    except Exception as e:

        st.warning(
            f"Could not generate chart: {e}"
        )