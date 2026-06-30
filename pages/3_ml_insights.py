import streamlit as st
import duckdb
import plotly.express as px
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
from ui.layout import apply_global_styles, section_spacer
from ui.sidebar import render_sidebar_brand
from ui.components import (
    section_header,
    sidebar_stat,
    footer,
)

apply_global_styles()

render_sidebar_brand(
    "InsightIQ",
    "AI-Powered Business Intelligence"
)

section_header(
    "ML Insights",
    "AI-powered forecasting, business intelligence and decision support."
)
st.sidebar.markdown("---")

sidebar_stat("🛒", "Orders", "~99,441")
sidebar_stat("👥", "Customers", "~99,441")
sidebar_stat("🏪", "Sellers", "~3,095")

st.sidebar.caption("📅 Sep 2016 – Oct 2018")


# -------------------------------
# AI Dashboard Time
# -------------------------------
from datetime import datetime
st.caption(
f"🕒 Dashboard generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
)


# -------------------------------
# Database connection
# -------------------------------
conn = duckdb.connect(
    "olist.db",
    read_only=True
)

revenue = conn.execute(
"""
SELECT
ROUND(
SUM(price),
0
)
FROM order_items
"""
).fetchone()[0]

@st.cache_data
def load_monthly_orders():
    conn = duckdb.connect("olist.db", read_only=True)
    df = conn.execute("""
        SELECT
            DATE_TRUNC(
                'month',
                STRPTIME(
                    order_purchase_timestamp,
                    '%d-%m-%Y %H:%M'
                )
            ) AS ds,
            COUNT(*) AS y
        FROM orders
        GROUP BY ds
        ORDER BY ds
    """).df()
    conn.close()

    df["ds"] = pd.to_datetime(df["ds"])

    # Remove incomplete final month (September 2018)
    df = df.iloc[:-1].reset_index(drop=True)
    return df


# -------------------------------
# helper functions
# -------------------------------
@st.cache_data
def load_monthly_revenue():
    conn = duckdb.connect("olist.db", read_only=True)
    df = conn.execute("""
        SELECT
            DATE_TRUNC(
                'month',
                STRPTIME(
                    o.order_purchase_timestamp,
                    '%d-%m-%Y %H:%M'
                )
            ) AS ds,
            SUM(oi.price) AS y
        FROM orders o
        JOIN order_items oi
        ON o.order_id = oi.order_id
        GROUP BY ds
        ORDER BY ds
    """).df()
    conn.close()
    df["ds"] = pd.to_datetime(df["ds"])

    # Remove incomplete final month (September 2018)
    df = df.iloc[:-1].reset_index(drop=True)
    return df


# -------------------------------
# KPI cards
# -------------------------------
avg_rating = conn.execute(
"""
SELECT
ROUND(
AVG(review_score),
1
)
FROM reviews
"""
).fetchone()[0]

on_time = conn.execute(
"""
SELECT
ROUND(
100.0 *
SUM(
CASE
WHEN STRPTIME(
order_delivered_customer_date,
'%d-%m-%Y %H:%M'
)
<=
STRPTIME(
order_estimated_delivery_date,
'%d-%m-%Y %H:%M'
)
THEN 1
ELSE 0
END
)
/
COUNT(*),
1
)
FROM orders
WHERE order_delivered_customer_date IS NOT NULL
"""
).fetchone()[0]
st.divider()


# -------------------------------
# Key Predictions
# -------------------------------
section_header("Key Predictions")
col1, col2, col3 = st.columns(3)
delay_risk = round(
    100-on_time, 3
)

col1.metric(
    "Delivery Delay Risk",
    f"{delay_risk}%"
)
col2.metric(
    "Avg Customer Rating",
    f"{avg_rating}"
)
col3.metric(
    "Total Revenue",
    f"R$ {revenue:,.0f}"
)
st.divider()


# -------------------------------
# Customer Segmentation
# -------------------------------
section_header("Customer Segmentation")

segments = conn.execute(
"""
SELECT
customer_state,
COUNT(*) AS total_customers
FROM customers
GROUP BY customer_state
ORDER BY total_customers DESC
LIMIT 5
"""
).df()

cols = st.columns(5)
for i, row in segments.iterrows():
    state = row["customer_state"]
    total = row["total_customers"]

    if total > 10000:
        label = "High Value"
    elif total > 5000:
        label = "Growth"
    else:
        label = "Emerging"
    
    cols[i].info(
        f"""
        {state}
        {label}\n
        {total:,} customers
        """
    )
st.divider()


# -------------------------------
# Delivery Risk Predictor
# -------------------------------
section_header("Delivery Risk Analysis")

risk = conn.execute(
"""
SELECT
c.customer_state,
AVG(
CASE
WHEN
DATEDIFF(
'day',
STRPTIME(
o.order_estimated_delivery_date,
'%d-%m-%Y %H:%M'
),
STRPTIME(
o.order_delivered_customer_date,
'%d-%m-%Y %H:%M'
)
) > 0
THEN
DATEDIFF(
'day',
STRPTIME(
o.order_estimated_delivery_date,
'%d-%m-%Y %H:%M'
),
STRPTIME(
o.order_delivered_customer_date,
'%d-%m-%Y %H:%M'
)
)
ELSE NULL
END
) AS delay
FROM orders o
JOIN customers c
ON o.customer_id=c.customer_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY delay DESC
LIMIT 5
"""
).df()
risk = risk.dropna()

chart_type = st.radio(
    "Select visualization",
    ["Bar Chart", "Pie Chart"],
    horizontal=True
)

if chart_type == "Pie Chart":
    fig = px.pie(
        risk,
        names="customer_state",
        values="delay",
        hole=0.6,
        color_discrete_sequence=[
            "#FF6B6B",
            "#FFA94D",
            "#FFD43B",
            "#69DB7C",
            "#4DABF7"
        ]
    )
else:
    fig = px.bar(
        risk,
        x="delay",
        y="customer_state",
        orientation="h",
        color="delay",
        color_continuous_scale="Reds"
    )
    fig.update_layout(
        coloraxis_showscale=False
    )

fig.update_layout(
    title="High Risk States",
    showlegend=True
)

st.plotly_chart(
    fig,
    width='stretch',
    config={"displayModeBar": False}
)
st.divider()


# -------------------------------
# AI Business Opportunities
# -------------------------------
section_header("AI Business Opportunities")

top_state = segments.iloc[0]["customer_state"]
delay_state = risk.iloc[0]["customer_state"]

top_category = conn.execute(
"""
SELECT
t.product_category_name_english,
COUNT(*) AS sales
FROM order_items oi
JOIN products p
ON oi.product_id = p.product_id
JOIN category_translation t
ON p.product_category_name =
t.product_category_name
GROUP BY 1
ORDER BY sales DESC
LIMIT 1
"""
).fetchone()[0]

top_review_state = conn.execute(
"""
SELECT
c.customer_state,
ROUND(
AVG(r.review_score),
2
) AS rating
FROM reviews r
JOIN orders o
ON r.order_id=o.order_id
JOIN customers c
ON o.customer_id=c.customer_id
GROUP BY c.customer_state
ORDER BY rating DESC
LIMIT 1
"""
).fetchone()[0]

opportunities = [
f"Expand marketing campaigns in {top_state}",
f"Improve logistics in {delay_state}",
f"Increase inventory for {top_category}",
f"Reward customers in {top_review_state}"
]

col1, col2 = st.columns(2)
col1.info(
    opportunities[0]
)
col1.info(
    opportunities[1]
)
col2.info(
    opportunities[2]
)
col2.info(
    opportunities[3]
)
st.divider()


# -------------------------------
# Seller Leaderboard
# -------------------------------
section_header("Seller Leaderboard")

sellers = conn.execute(
"""
SELECT
seller_id,
SUM(price) AS revenue
FROM order_items
GROUP BY seller_id
ORDER BY revenue DESC
LIMIT 5
"""
).df()

cols = st.columns(5)
position = ["a.","b.","c.","d.","e."]
for i,row in sellers.iterrows():
    cols[i].metric(
    f"Seller {i+1}",
    f"R$ {row['revenue']:,.0f}"
)
st.divider()


# -------------------------------
# Risk Meter
# -------------------------------
section_header("Business Risk")

if on_time > 90:
    st.success(
        "Low Risk Business"
    )
elif on_time > 80:
    st.warning(
        "Moderate Risk Business"
    )
else:
    st.error(
        "High Risk Business"
    )
st.divider()


# -------------------------------
# Business Health Score
# -------------------------------
score = 0
# Customer rating (40 points)
score += (avg_rating / 5) * 40
# On-time delivery (40 points)
score += (on_time / 100) * 40
# Delivery risk (20 points)
score += max(0, 20 - delay_risk)
score = round(score)


# -------------------------------
# ML Forecasting
# -------------------------------
section_header("Machine Learning Forecast")

metric = st.selectbox(
    "Forecast Metric",
    [
        "Monthly Revenue",
        "Monthly Orders"
    ]
)
forecast_months = st.slider(
    "Forecast Months",
    1,
    6,
    3
)

if st.button("Run Forecast"):
    with st.spinner("Training ML model..."):

        if metric == "Monthly Revenue":
            df = load_monthly_revenue()
            ylabel = "Revenue (BRL)"
        else:
            df = load_monthly_orders()
            ylabel = "Orders"
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode="multiplicative"
        )
        model.fit(df)
        future = model.make_future_dataframe(
            periods=forecast_months,
            freq="MS"
        )
        forecast = model.predict(future)
        future_df = forecast[
            forecast["ds"] > df["ds"].max()
        ]

    st.success("Forecast generated successfully.")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["ds"],
            y=df["y"],
            mode="lines+markers",
            name="Historical",
            line=dict(
                color="#4DABF7",
                width=3
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=future_df["ds"],
            y=future_df["yhat"],
            mode="lines+markers",
            name="Forecast",
            line=dict(
                color="#FF6B6B",
                width=3,
                dash="dash"
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=pd.concat(
                [
                    future_df["ds"],
                    future_df["ds"][::-1]
                ]
            ),
            y=pd.concat(
                [
                    future_df["yhat_upper"],
                    future_df["yhat_lower"][::-1]
                ]
            ),
            fill="toself",
            fillcolor="rgba(255,99,71,0.2)",
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=False
        )
    )

    fig.update_layout(
        title=f"{metric} Forecast",
        xaxis_title="Month",
        yaxis_title=ylabel,
        hovermode="x unified"
    )

    st.plotly_chart(
    fig,
    width='stretch',
    config={"displayModeBar": False}
    )

    section_header("Forecast Results")
    table = future_df[
        [
            "ds",
            "yhat",
            "yhat_lower",
            "yhat_upper"
        ]
    ].copy()
    table.columns = [
        "Month",
        "Forecast",
        "Lower",
        "Upper"
    ]
    table["Month"] = table["Month"].dt.strftime("%b %Y")

    st.dataframe(
        table,
        width='stretch',
        hide_index=True
    )

    section_header("AI Prediction Interpretation")

    # Compare the average of the last 3 historical months
    # with the average of the forecast period
    historical_avg = df["y"].tail(3).mean()
    forecast_avg = future_df["yhat"].mean()

    st.metric(
        "Average Forecast",
        f"{forecast_avg:,.0f}"
    )

    if forecast_avg > historical_avg * 1.10:
        st.success(
            "The forecast indicates an upward business trend over the coming months. Consider increasing inventory and marketing investment."
        )
    elif forecast_avg < historical_avg * 0.90:
        st.warning(
            "The forecast indicates a downward trend. Consider reviewing pricing, logistics and promotional strategies."
        )
    else:
        st.info(
            "The forecast indicates relatively stable business performance over the forecast period."
        )  


# -------------------------------
# AI Executive Summary
# -------------------------------
if score >= 85:
    status = "Excellent"
elif score >= 70:
    status = "Good"
else:
    status = "Needs Improvement"
# -------------------------------
if delay_risk > 15:
    action = "Improve delivery logistics"
elif avg_rating < 4:
    action = "Improve customer satisfaction"
else:
    action = "Expand marketing to high-value markets"
# -------------------------------
forecast_value = "Not generated"
if "future_df" in locals():
    forecast_value = f"{future_df['yhat'].mean():,.0f}"
# -------------------------------

with st.container(border=True):
    st.markdown(f"""
### Executive Summary

- **Overall Business Status:** {status}
- **Average Rating:** {avg_rating}
- **Total Revenue:** R$ {revenue:,.0f}
- **Delivery Delay Risk:** {delay_risk:.1f}%
- **{forecast_months}-month ML Forecast:** {forecast_value}
- **Largest Customer State Market:** {top_state}
- **Biggest Challenge:** Delivery delays in {delay_state}
- **Recommended Action:** {action}
""")

conn.close()

footer("InsightIQ • ML Insights")