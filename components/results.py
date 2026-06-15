# components/results_display.py

import streamlit as st
import plotly.express as px
import pandas as pd

def render_results(df: pd.DataFrame, question: str = ""):
    if df is None or df.empty:
        st.warning("No results returned.")
        return
    
    st.subheader("📊 Results")
    
    # Always show the table
    st.dataframe(df, use_container_width=True)
    
    fig = auto_chart(df, question)

    if fig:
        st.plotly_chart(fig, use_container_width=True)
    

def auto_chart(df: pd.DataFrame, question: str = ""):
    if df is None or df.empty:
        return None

    cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    non_numeric_cols = [c for c in cols if c not in numeric_cols]

    # Better date detection
    date_cols = df.select_dtypes(include=['datetime', 'object']).columns.tolist()
    date_cols = [c for c in date_cols if 'date' in c.lower() or 'time' in c.lower() or 'created' in c.lower()]

    # Rule 1: time series
    if date_cols and numeric_cols:
        return px.line(df, x=date_cols[0], y=numeric_cols[0], title=question)

    # Rule 2: category + metric
    if len(numeric_cols) == 1 and len(non_numeric_cols) >= 1:
        return px.bar(df, x=non_numeric_cols[0], y=numeric_cols[0], title=question)

    # Rule 3: multiple metrics
    if len(numeric_cols) >= 2:
        return px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title=question)

    return None

