# pages/7_dashboard.py
# Static KPI dashboard — 6 pre-computed metrics from DuckDB.
# Refreshed on every page load.

import streamlit as st
import duckdb
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("📊 KPI Dashboard")
st.caption("Pre-computed business metrics from the Olist dataset. Refreshes on page load.")

from datetime import datetime
st.caption(
    f"Updated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
)
# -------------------------------------------------------
# Load all KPIs from DuckDB
# -------------------------------------------------------
@st.cache_data(ttl=600)   # cache for 10 minutes, then refresh
def load_kpis():
    conn = duckdb.connect("olist.db", read_only=True)

    total_revenue = conn.execute("""
        SELECT ROUND(SUM(payment_value), 2)
        FROM payments
    """).fetchone()[0]

    total_orders = conn.execute("""
        SELECT COUNT(*) FROM orders
    """).fetchone()[0]

    avg_review = conn.execute("""
        SELECT ROUND(AVG(review_score), 2) FROM reviews
    """).fetchone()[0]

    top_seller = conn.execute("""
        SELECT seller_id, ROUND(SUM(price + freight_value), 2) AS revenue
        FROM order_items
        GROUP BY seller_id
        ORDER BY revenue DESC
        LIMIT 1
    """).fetchone()

    most_delayed_state = conn.execute("""
    SELECT c.customer_state,
        ROUND(AVG(
                CASE
                    WHEN DATEDIFF('day', 
                            STRPTIME(o.order_estimated_delivery_date, '%d-%m-%Y %H:%M'),
                            STRPTIME(o.order_delivered_customer_date, '%d-%m-%Y %H:%M')
                    ) > 0

                    THEN DATEDIFF('day', 
                            STRPTIME(o.order_estimated_delivery_date, '%d-%m-%Y %H:%M'),
                            STRPTIME(o.order_delivered_customer_date, '%d-%m-%Y %H:%M')
                    )
                    ELSE NULL
                END
            ),
            1
        ) AS avg_delay
    FROM orders o
    JOIN customers c
    ON o.customer_id = c.customer_id
    WHERE o.order_delivered_customer_date IS NOT NULL
    GROUP BY c.customer_state
    ORDER BY avg_delay DESC
    LIMIT 1
    """).fetchone()

    mom_growth = conn.execute("""
    WITH monthly AS (
        SELECT
            DATE_TRUNC(
                'month',
                STRPTIME(order_purchase_timestamp, '%d-%m-%Y %H:%M')
            ) AS month,

            COUNT(*) AS orders

        FROM orders

        WHERE
            order_purchase_timestamp IS NOT NULL
            AND STRPTIME(order_purchase_timestamp, '%d-%m-%Y %H:%M') < DATE '2018-09-01'

        GROUP BY month

        ORDER BY month
    ),

    lagged AS (
        SELECT
            month,
            orders,
            LAG(orders) OVER (ORDER BY month) AS prev_orders
        FROM monthly
    )

    SELECT
        month,

        ROUND(
            (orders - prev_orders) * 100.0 /
            NULLIF(prev_orders, 0),
            1
        ) AS growth_pct

    FROM lagged

    WHERE prev_orders IS NOT NULL

    ORDER BY month DESC

    LIMIT 1;

    """).fetchone()

    # Monthly revenue for chart
    monthly_revenue = conn.execute("""
        SELECT
            DATE_TRUNC('month', STRPTIME(o.order_purchase_timestamp, '%d-%m-%Y %H:%M')) AS month,
            ROUND(SUM(p.payment_value), 2) AS revenue
        FROM orders o
        JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_purchase_timestamp IS NOT NULL
        GROUP BY month
        ORDER BY month
    """).df()
    # Remove incomplete final month (September 2018)
    monthly_revenue = monthly_revenue.iloc[:-1].reset_index(drop=True)

    conn.close()

    return {
        "total_revenue":      total_revenue,
        "total_orders":       total_orders,
        "avg_review":         avg_review,
        "top_seller_id":      top_seller[0] if top_seller else "N/A",
        "top_seller_revenue": top_seller[1] if top_seller else 0,
        "most_delayed_state": most_delayed_state[0] if most_delayed_state else "N/A",
        "most_delayed_days":  most_delayed_state[1] if most_delayed_state else 0,
        "mom_growth_pct":     mom_growth[1] if mom_growth else 0,
        "monthly_revenue":    monthly_revenue
    }

# -------------------------------------------------------
# Display KPI cards (6 metrics in 3x2 grid)
# -------------------------------------------------------

with st.spinner("Loading KPIs from database..."):
    kpis = load_kpis()

st.subheader("Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric(
    label="Total Revenue",
    value=f"R$ {kpis['total_revenue']:,.2f}"
)

col2.metric(
    label="Total Orders",
    value=f"{kpis['total_orders']:,}"
)

col3.metric(
    label="Avg Review Score",
    value=f"{kpis['avg_review']} / 5.0"
)

col4, col5, col6 = st.columns(3)

col4.metric(
    label="Top Seller Revenue",
    value=f"R$ {kpis['top_seller_revenue']:,.2f}",
    help=f"Seller ID: {kpis['top_seller_id']}"
)

col5.metric(
    label="Most Delayed State",
    value=kpis["most_delayed_state"],
    delta=f"{kpis['most_delayed_days']} avg days to deliver",
    delta_color="inverse"
)

col6.metric(
    label="Latest MoM Growth",
    value=f"{kpis['mom_growth_pct']}%",
    delta="vs previous month"
)

st.divider()

# -------------------------------------------------------
# Monthly revenue chart
# -------------------------------------------------------
st.subheader("📈 Monthly Revenue Trend")

chart_type = st.radio(
    "Select Visualization",
    [
        "Area Chart",
        "Line Chart",
        "Smooth Line",
        "Bar Chart",
        "Scatter Plot"
    ],
    horizontal=True
)

if chart_type == "Area Chart":

    fig = px.area(
        kpis["monthly_revenue"],
        x="month",
        y="revenue",
        color_discrete_sequence=["#636EFA"]
    )

elif chart_type == "Line Chart":
    fig = px.line(
        kpis["monthly_revenue"],
        x="month",
        y="revenue"
    )
    fig.update_traces(
        line=dict(
            width=4,
            color="#00CC96"
        )
    )

elif chart_type == "Smooth Line":
    fig = px.line(
        kpis["monthly_revenue"],
        x="month",
        y="revenue"
    )
    fig.update_traces(
        line=dict(
            width=4,
            color="#AB63FA",
            shape="spline",
            smoothing=1.2
        )
    )

elif chart_type == "Bar Chart":
    fig = px.bar(
        kpis["monthly_revenue"],
        x="month",
        y="revenue",
        color="revenue",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        coloraxis_showscale=False
    )

else:
    fig = px.scatter(
        kpis["monthly_revenue"],
        x="month",
        y="revenue",
        size="revenue",
        color="revenue",
        color_continuous_scale="Turbo"
    )
    fig.update_layout(
        coloraxis_showscale=False
    )

fig.update_layout(
    title=f"Monthly Revenue ({chart_type})",
    hovermode="x unified",
    template="plotly_white",
    xaxis_title="Month",
    yaxis_title="Revenue (R$)"
)
st.plotly_chart(
    fig,
    width='stretch',
    config={"displayModeBar": False}
)

st.divider()

st.subheader("📥 Download Data")
csv = kpis["monthly_revenue"].to_csv(index=False)
st.download_button(
    label="Download Monthly Revenue CSV",
    data=csv,
    file_name="monthly_revenue.csv",
    mime="text/csv"
)

st.caption(
    "Metrics are computed dynamically from the Olist Brazilian E-Commerce dataset."
)