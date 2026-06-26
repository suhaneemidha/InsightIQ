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
    "a. Orders",
    f"{orders:,}"
)
col2.metric(
    "b. Customers",
    f"{customers:,}"
)
col3.metric(
    "c. Sellers",
    f"{sellers:,}"
)
col4.metric(
    "d. Products",
    f"{products:,}"
)

st.info(
    "📅 Dataset duration: September 2016 - October 2018"
)
st.divider()


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

chart = st.radio(
    "Select Visualization",
    [
    "Area Chart",
    "Line Chart",
    "Smooth Line",
    "Bar Chart",
    "Scatter Plot"
    ],
    horizontal=True,
    key="orders"
)

if chart == "Line Chart":
    fig = px.line(
        monthly_orders,
        x="month",
        y="orders",
        markers=True,
        title="Orders Per Month"
    )
elif chart == "Bar Chart":
    fig = px.bar(
        monthly_orders,
        x="month",
        y="orders",
        title="Orders Per Month",
        color="orders",
        color_continuous_scale="Blues"
    )
    fig.update_layout(coloraxis_showscale=False)
elif chart == "Smooth Line":
    fig = px.line(
        monthly_orders,
        x="month",
        y="orders"
    )
    fig.update_traces(
        line=dict(
            shape="spline",
            smoothing=1.2,
            width=4
        )
    )
elif chart == "Scatter Plot":
    fig = px.scatter(
        monthly_orders,
        x="month",
        y="orders",
        size="orders",
        color="orders",
        color_continuous_scale="Turbo"
    )
    fig.update_layout(coloraxis_showscale=False)
else:
    fig = px.area(
        monthly_orders,
        x="month",
        y="orders",
        title="Orders Per Month"
    )

st.plotly_chart(

    fig,
    use_container_width=True,
    config={"displayModeBar": False}

)

peak_month = monthly_orders.loc[
    monthly_orders["orders"].idxmax(),
    "month"
]
peak_orders = monthly_orders["orders"].max()

st.info(
    f"Peak order volume occurred in {peak_month.strftime('%b %Y')} with {peak_orders:,} orders."
)
st.divider()


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

chart = st.radio(
    "Select Visualization",
    [
    "Bar Chart",
    "Horizontal Bar",
    "Pie Chart",
    "Treemap"
    ],
    horizontal=True,
    key="customers"
)

if chart == "Bar Chart":
    fig = px.bar(
        states,
        x="customer_state",
        y="customers",
        color="customers",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(coloraxis_showscale=False)
elif chart == "Horizontal Bar":
    fig = px.bar(
        states,
        x="customers",
        y="customer_state",
        orientation="h",
        color="customers",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(coloraxis_showscale=False)
elif chart == "Pie Chart":
    fig = px.pie(
        states,
        names="customer_state",
        values="customers",
        hole=0.5
    )
else:
    fig = px.treemap(
        states,
        path=["customer_state"],
        values="customers"
    )

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)

top_state = states.iloc[0]["customer_state"]

st.info(
    f"{top_state} has the highest number of customers."
)
st.divider()


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

chart = st.radio(
    "Select Visualization",
    [
    "Bar Chart",
    "Line Chart",
    "Pie Chart",
    "Donut Chart",
    "Scatter Plot"
    ],
    horizontal=True,
    key="reviews"
)

if chart == "Bar Chart":
    fig = px.bar(
        reviews,
        x="review_score",
        y="count",
        color="review_score",
        color_continuous_scale="RdYlGn"
    )
elif chart == "Line Chart":
    fig = px.line(
        reviews,
        x="review_score",
        y="count",
        markers=True
    )
elif chart == "Pie Chart":
    fig = px.pie(
        reviews,
        names="review_score",
        values="count"
    )
elif chart == "Scatter Plot":
    fig = px.scatter(
        reviews,
        x="review_score",
        y="count",
        size="count",
        color="count"
    )
else:
    fig = px.pie(
        reviews,
        names="review_score",
        values="count",
        hole=0.6
    )

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
    
)

top_review = reviews.loc[
    reviews["count"].idxmax(),
    "review_score"
]

st.info(
    f"Most customers gave a {top_review}-star rating."
)
st.divider()


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

chart = st.radio(
    "Select Visualization",
    [
    "Pie Chart",
    "Donut Chart",
    "Horizontal Bar",
    "Treemap",
    "Bar Chart"
    ],
    horizontal=True,
    key="payments"
)

if chart == "Pie Chart":
    fig = px.pie(
        payments,
        names="payment_type",
        values="total"
    )
elif chart == "Donut Chart":
    fig = px.pie(
        payments,
        names="payment_type",
        values="total",
        hole=0.6
    )
elif chart == "Horizontal Bar":
    fig = px.bar(
        payments,
        x="total",
        y="payment_type",
        orientation="h",
        color="total",
        color_continuous_scale="Teal"
    )
    fig.update_layout(coloraxis_showscale=False)
elif chart == "Treemap":
    fig = px.treemap(
        payments,
        path=["payment_type"],
        values="total"
    )
else:
    fig = px.bar(
        payments,
        x="payment_type",
        y="total",
        color="total",
        color_continuous_scale="Teal"
    )
    fig.update_layout(coloraxis_showscale=False)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
    
)

top_payment = payments.iloc[0]["payment_type"]

st.info(
    f"{top_payment.title()} is the preferred payment method."
)
st.divider()


# --------------------------------
# Top Product Categories
# --------------------------------
st.subheader("🛍 Top Product Categories")

categories = conn.execute("""
SELECT
t.product_category_name_english AS category,
COUNT(*) AS sales
FROM order_items oi
JOIN products p
ON oi.product_id=p.product_id
JOIN category_translation t
ON p.product_category_name=t.product_category_name
GROUP BY category
ORDER BY sales DESC
LIMIT 10
""").df()

chart = st.radio(
    "Select Visualization",
    [
    "Horizontal Bar",
    "Bar Chart",
    "Pie Chart",
    "Donut Chart",
    "Treemap"
    ],
    horizontal=True,
    key="category"
)

if chart == "Horizontal Bar":
    fig = px.bar(
        categories,
        x="sales",
        y="category",
        orientation="h",
        color="sales",
        color_continuous_scale="Oranges"
    )
    fig.update_layout(coloraxis_showscale=False)
elif chart == "Bar Chart":
    fig = px.bar(
        categories,
        x="category",
        y="sales",
        color="sales",
        color_continuous_scale="Oranges"
    )
    fig.update_layout(coloraxis_showscale=False)
elif chart == "Pie Chart":
    fig = px.pie(
        categories,
        names="category",
        values="sales"
    )
elif chart == "Donut Chart":
    fig = px.pie(
        categories,
        names="category",
        values="sales",
        hole=0.6
    )
else:
    fig = px.treemap(
        categories,
        path=["category"],
        values="sales"
    )

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)

st.info(
    f"{categories.iloc[0]['category']} is the best-selling category."
)
st.divider()


# --------------------------------
# Product Price Distribution
# --------------------------------
st.subheader("📦 Product Price Distribution")

prices = conn.execute("""
SELECT
    price
FROM order_items
""").df()

chart = st.radio(
    "Select Visualization",
    [
        "Histogram",
        "Box Plot",
        "Violin Plot"
    ],
    horizontal=True,
    key="price"
)

if chart == "Histogram":
    fig = px.histogram(
        prices,
        x="price",
        nbins=40,
        title="Product Price Distribution",
        color_discrete_sequence=["#636EFA"]
    )
elif chart == "Box Plot":
    fig = px.box(
        prices,
        y="price",
        title="Product Price Distribution",
        color_discrete_sequence=["#EF553B"]
    )
else:
    fig = px.violin(
        prices,
        y="price",
        box=True,
        title="Product Price Distribution",
        color_discrete_sequence=["#00CC96"]
    )

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)

st.info(
    f"Product prices range from R$ {prices['price'].min():.2f} to R$ {prices['price'].max():.2f}."
)
st.divider()


# --------------------------------
# Freight Cost Analysis
# --------------------------------
st.subheader("🚚 Freight Cost Analysis")

freight = conn.execute("""
SELECT
price,
freight_value
FROM order_items
""").df()

chart = st.radio(
    "Select Visualization",
    ["Histogram","Box Plot","Scatter Plot"],
    horizontal=True,
    key="freight"
)

if chart=="Histogram":
    fig=px.histogram(
        freight,
        x="freight_value",
        nbins=40,
        color_discrete_sequence=["#AB63FA"]
    )
elif chart=="Box Plot":
    fig=px.box(
        freight,
        y="freight_value",
        color_discrete_sequence=["#FFA15A"]
    )
else:
    fig=px.scatter(
        freight,
        x="price",
        y="freight_value",
        opacity=0.5,
        color="freight_value",
        color_continuous_scale="Turbo"
    )

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)
st.divider()


# --------------------------------
# Payment Value Distribution
# --------------------------------
st.subheader("💰 Payment Value Distribution")

payment_values = conn.execute("""
SELECT
    payment_value
FROM payments
""").df()

chart = st.radio(
    "Select Visualization",
    [
        "Histogram",
        "Box Plot",
        "Violin Plot"
    ],
    horizontal=True,
    key="paymentvalue"
)

if chart == "Histogram":
    fig = px.histogram(
        payment_values,
        x="payment_value",
        nbins=40,
        title="Payment Value Distribution",
        color_discrete_sequence=["#19D3F3"]
    )
elif chart == "Box Plot":
    fig = px.box(
        payment_values,
        y="payment_value",
        title="Payment Value Distribution",
        color_discrete_sequence=["#FF6692"]
    )
else:
    fig = px.violin(
        payment_values,
        y="payment_value",
        box=True,
        title="Payment Value Distribution",
        color_discrete_sequence=["#B6E880"]
    )

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)

st.info(
    f"Payment values range from R$ {payment_values['payment_value'].min():.2f} to R$ {payment_values['payment_value'].max():.2f}."
)
st.divider()


# --------------------------------
# Orders by Hour
# --------------------------------
st.subheader("🕒 Orders by Hour")

hours = conn.execute("""
SELECT
EXTRACT(
    HOUR FROM STRPTIME(
        order_purchase_timestamp,
        '%d-%m-%Y %H:%M'
    )
) AS hour,
COUNT(*) AS orders
FROM orders
GROUP BY hour
ORDER BY hour
""").df()

chart = st.radio(
    "Select Visualization",
    [
        "Area Chart",
        "Line Chart",
        "Bar Chart",
        "Scatter Plot"
    ],
    horizontal=True,
    key="hour"
)

if chart == "Area Chart":
    fig = px.area(
        hours,
        x="hour",
        y="orders",
        title="Orders by Hour",
        color_discrete_sequence=["#00CC96"]
    )
elif chart == "Line Chart":
    fig = px.line(
        hours,
        x="hour",
        y="orders",
        markers=True,
        title="Orders by Hour"
    )
    fig.update_traces(
    line=dict(
        width=4,
        color="#EF553B"
        )
    )
elif chart == "Bar Chart":
    fig = px.bar(
        hours,
        x="hour",
        y="orders",
        color="orders",
        color_continuous_scale="Viridis",
        title="Orders by Hour"
    )
    fig.update_layout(
        coloraxis_showscale=False
    )
else:
    fig = px.scatter(
        hours,
        x="hour",
        y="orders",
        size="orders",
        color="orders",
        color_continuous_scale="Plasma",
        title="Orders by Hour"
    )
    fig.update_layout(
        coloraxis_showscale=False
    )

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)

peak_hour = hours.loc[
    hours["orders"].idxmax(),
    "hour"
]

st.info(
    f"Peak shopping activity occurs around {int(peak_hour):02d}:00 hours."
)

#----------------------------------------------
st.divider()
st.subheader("📥 Download Data")
csv = monthly_orders.to_csv(index=False)
st.download_button(
    "Download EDA Data",
    csv,
    "eda_data.csv",
    "text/csv"
)
conn.close()