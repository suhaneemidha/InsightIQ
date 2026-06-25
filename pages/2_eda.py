import streamlit as st
import duckdb
import plotly.express as px

st.title("🔍 Exploratory Data Analysis")

st.caption(
    "Interactive business insights from the Olist e-commerce dataset"
)

# --------------------------------
# Database connection
# --------------------------------

conn = duckdb.connect(
    "olist.db",
    read_only=True
)

# --------------------------------
# Dataset overview metrics
# --------------------------------

orders = conn.execute(
    "SELECT COUNT(*) FROM orders"
).fetchone()[0]

customers = conn.execute(
    "SELECT COUNT(*) FROM customers"
).fetchone()[0]

sellers = conn.execute(
    "SELECT COUNT(*) FROM sellers"
).fetchone()[0]

products = conn.execute(
    "SELECT COUNT(*) FROM products"
).fetchone()[0]

st.subheader("📊 Dataset Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "🛒 Orders",
    f"{orders:,}"
)

col2.metric(
    "👥 Customers",
    f"{customers:,}"
)

col3.metric(
    "🏪 Sellers",
    f"{sellers:,}"
)

col4.metric(
    "📦 Products",
    f"{products:,}"
)

st.divider()
st.info(
    "📅 Dataset duration: September 2016 - October 2018"
)

# --------------------------------
# Orders per month
# --------------------------------
st.subheader("📈 Orders Trend")
monthly_orders = conn.execute(
"""
SELECT

DATE_TRUNC(
'month',

STRPTIME(
order_purchase_timestamp,
'%d-%m-%Y %H:%M'
)

) AS month,

COUNT(*) AS orders

FROM orders

GROUP BY month

ORDER BY month
"""
).df()

fig1 = px.line(
    monthly_orders,

    x="month",

    y="orders",

    title="Orders Per Month"
)

fig1.update_traces(
    line=dict(
        color="#00CC96",
        width=4
    )
)

fig1.update_layout(
    hovermode="x unified"
)

st.plotly_chart(
    fig1,
    width='stretch'
)

peak_month = monthly_orders.loc[
    monthly_orders["orders"].idxmax(),
    "month"
]

peak_orders = monthly_orders["orders"].max()

st.info(
    f"📌 Peak order volume occurred in {peak_month.strftime('%b %Y')} with {peak_orders:,} orders."
)

# --------------------------------
# Top customer states
# --------------------------------
st.subheader("🌎 Customer Distribution")
states = conn.execute(
"""
SELECT

customer_state,

COUNT(*) AS customers

FROM customers

GROUP BY customer_state

ORDER BY customers DESC

LIMIT 10
"""
).df()

fig2 = px.bar(
    states,

    x="customer_state",

    y="customers",

    title="Top 10 States By Customers",

    color="customers",

    color_continuous_scale="Viridis"
)

fig2.update_layout(
    coloraxis_showscale=False
)

st.plotly_chart(
    fig2,
    width='stretch'
)

top_state = states.iloc[0]["customer_state"]

st.info(
    f"📌 {top_state} has the highest number of customers."
)

# --------------------------------
# Review score distribution
# --------------------------------
st.subheader("⭐ Customer Satisfaction")
reviews = conn.execute(
"""
SELECT

review_score,

COUNT(*) AS count

FROM reviews

GROUP BY review_score

ORDER BY review_score
"""
).df()

fig3 = px.bar(
    reviews,

    x="review_score",

    y="count",

    title="Review Score Distribution",

    color="review_score",

    color_continuous_scale="RdYlGn"
)

fig3.update_layout(
    coloraxis_showscale=False
)

st.plotly_chart(
    fig3,
    width='stretch'
)

top_review = reviews.loc[
    reviews["count"].idxmax(),
    "review_score"
]

st.info(
    f"📌 Most customers gave a {top_review}-star rating."
)

# --------------------------------
# Payment Methods
# --------------------------------
st.subheader("💳 Payment Methods")

payments = conn.execute(
"""
SELECT

payment_type,

COUNT(*) AS total

FROM payments

GROUP BY payment_type

ORDER BY total DESC
"""
).df()

fig4 = px.pie(
    payments,

    names="payment_type",

    values="total",

    title="Payment Type Distribution"
)

fig4.update_traces(
    textposition="inside",

    textinfo="percent+label"
)

st.plotly_chart(
    fig4,
    width='stretch'
)

top_payment = payments.iloc[0]["payment_type"]

st.info(
    f"📌 {top_payment.title()} is the preferred payment method."
)

conn.close()