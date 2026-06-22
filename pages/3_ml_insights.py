import streamlit as st
import duckdb
import plotly.express as px

st.title("🤖 AI Business Intelligence")

st.caption("AI-powered business intelligence and decision support using the Olist dataset.")
st.info("🧠 This dashboard simulates AI-driven business decision making using historical Olist e-commerce data.")

# -------------------------------
# AI Dashboard Time
# -------------------------------
from datetime import datetime
st.caption("Generated using historical Olist transaction patterns.")
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

# -------------------------------
# Key Predictions
# -------------------------------
st.subheader("📊 Key Predictions")
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
    f"{avg_rating} ⭐"
)
col3.metric(
"Total Revenue",
f"₹{revenue*15:,.0f}"
)

st.divider()

# -------------------------------
# Customer Segmentation
# -------------------------------
st.subheader("👥 Customer Segmentation")

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

        {label}

        {total:,} customers 👥 
        """
    )


# -------------------------------
# Delivery Risk Predictor
# -------------------------------
st.subheader("🚚 Delivery Risk Analysis")

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
st.write(risk)
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
    use_container_width=True,
    config={
        "displayModeBar": False
    }
)


# -------------------------------
# AI Business Opportunities
# -------------------------------
st.subheader("💡 AI Opportunities")

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


# -------------------------------
# Seller Leaderboard
# -------------------------------
st.subheader("🏆 Seller Intelligence")

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
        f"{position[i]} Seller {i+1}",
        f"₹{row['revenue']*15:,.0f}"
    )
    cols[i].caption(
        f"{row['revenue']:,.0f} BRL"
    ) 

# -------------------------------
# Risk Meter
# -------------------------------
st.subheader("⚠️ AI Risk Meter")

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


# -------------------------------
# Prediction Simulator
# -------------------------------
st.subheader("🎯 AI Prediction Simulator")
rating_factor = avg_rating/5
delivery_factor = on_time/100

marketing = st.slider(
    "Marketing Budget Increase (%)",
    0,
    50,
    10
)

predicted_revenue = round(
revenue *
(
1 +
marketing/100 * 0.15
),
0
)

st.metric(
"Projected Revenue",
f"₹{predicted_revenue*15:,.0f}"
)

if marketing < 15:
    st.info(
        "📌 Conservative strategy"
    )

elif marketing < 30:
    st.warning(
        "📌 Balanced growth strategy"
    )

else:
    st.success(
        "📌 Aggressive expansion strategy"
    )


# -------------------------------
# Business Health Score
# -------------------------------
st.subheader("❤️ Business Health Score")

score = round(
(
avg_rating*20 + on_time
) 
/2
)

st.progress(
    score
)

st.metric(
    "Overall Health",
    f"{score}/100"
)

if score >= 85:
    st.success(
        "Excellent Business Health"
    )

elif score >= 70:
    st.warning(
        "Good Business Health"
    )

else:
    st.error(
        "Needs Improvement"
    )

if score >= 85:
    st.info(
        "📌 Excellent performance. Focus on scaling operations."
    )

elif score >= 70:
    st.info(
        "📌 Stable business with room for optimization."
    )

else:
    st.info(
        "📌 Immediate attention required in logistics and customer experience."
    )


# -------------------------------
# AI Executive Summary
# -------------------------------
st.subheader("🧠 AI Executive Summary")

if score >= 85:
    status = "Excellent"

elif score >= 70:
    status = "Good"

else:
    status = "Needs Improvement"

summary = f"""
1. Overall Status: {status}
2. Average Rating: {avg_rating}
3. Revenue Growth: {revenue}%
4. Biggest Challenge: Delivery delays in {delay_state}
5. Suggested Action: Prioritize logistics optimization
"""

st.info(summary)

conn.close()