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
    
    # Try to auto-pick a chart type
    cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    
    if len(numeric_cols) >= 1 and len(cols) >= 2:
        st.subheader("📈 Chart")
        x_col = cols[0]   # first column as x-axis (usually label/category)
        y_col = numeric_cols[0]   # first numeric as y-axis
        
        fig = px.bar(df, x=x_col, y=y_col, title=question)
        st.plotly_chart(fig, use_container_width=True)  