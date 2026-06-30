import json
import os
import tempfile

import duckdb
import networkx as nx
import streamlit as st
from pyvis.network import Network

st.title("🕸️ Knowledge Graph")
st.caption(
    "Interactive Knowledge Graph showing relationships between customers, "
    "orders, products and reviews."
)
st.markdown(
    "This graph visualizes relationships among customers, orders, products, and "
    "reviews in the Olist dataset, enabling intuitive exploration of purchasing "
    "patterns and product associations."
)

# --------------------------------
# Color palette
# --------------------------------
NODE_COLORS = {
    "customer": "#4DABF7",
    "order": "#69DB7C",
    "product": "#FFA94D",
    "review": "#FF6B6B",  # fallback only, reviews are colored by score
}

EDGE_COLORS = {
    "placed": "#4DABF7",       # Customer -> Order
    "contains": "#FFA94D",     # Order -> Product
    "has_review": "#FA5252",   # Order -> Review
}

REVIEW_COLORS = {
    1: "#FA5252",  # red
    2: "#FF922B",  # orange
    3: "#FCC419",  # yellow
    4: "#94D82D",  # light green
    5: "#40C057",  # green
}

SEARCH_HIGHLIGHT_BORDER = "#FFD700"

# --------------------------------
# Database connection
# --------------------------------
conn = duckdb.connect("olist.db", read_only=True)

# --------------------------------
# Controls
# --------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    sample_size = st.slider(
        "Number of customers to visualize",
        min_value=5,
        max_value=50,
        value=15,
        step=5,
    )

with col2:
    layout = st.radio(
        "Graph layout",
        ["Barnes-Hut", "Force Atlas"],
        horizontal=True,
    )

with col3:
    enable_physics = st.checkbox("Enable physics", value=True)
    freeze_after_stabilize = st.checkbox(
        "Freeze layout once stable",
        value=False,
        help="Physics runs briefly to arrange the graph, then locks in place.",
    )

search_col, sample_col = st.columns([3, 1])

with search_col:
    search_term = st.text_input(
        "🔍 Search (customer ID, order ID, product category...)", ""
    )

with sample_col:
    st.write("")
    st.write("")
    if "graph_seed" not in st.session_state:
        st.session_state.graph_seed = 0
    if st.button("New random sample"):
        st.session_state.graph_seed += 1

st.divider()


# --------------------------------
# Load data
# --------------------------------
@st.cache_data
def load_graph_data(n, seed):
    """`seed` has no effect on the query itself -- it only busts the Streamlit
    cache so that pressing 'New random sample' triggers a fresh ORDER BY RANDOM()
    pull. IMPORTANT: it must NOT be prefixed with an underscore -- Streamlit
    excludes underscore-prefixed args from the cache key, which would make the
    button a no-op."""
    local_conn = duckdb.connect("olist.db", read_only=True)

    customers = local_conn.execute(f"""
        SELECT DISTINCT customer_id, customer_state
        FROM customers
        ORDER BY RANDOM()
        LIMIT {n}
    """).df()

    customer_ids = customers["customer_id"].tolist()
    if not customer_ids:
        local_conn.close()
        empty = local_conn.execute("SELECT NULL WHERE 1=0").df()
        return customers, empty, empty, empty

    customer_placeholders = ",".join(f"'{cid}'" for cid in customer_ids)

    orders = local_conn.execute(f"""
        SELECT o.order_id, o.customer_id
        FROM orders o
        WHERE o.customer_id IN ({customer_placeholders})
        LIMIT {n * 3}
    """).df()

    order_ids = orders["order_id"].tolist()
    if not order_ids:
        local_conn.close()
        empty = local_conn.execute("SELECT NULL WHERE 1=0").df()
        return customers, orders, empty, empty

    order_placeholders = ",".join(f"'{oid}'" for oid in order_ids)

    items = local_conn.execute(f"""
        SELECT oi.order_id, oi.product_id, p.product_category_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id IN ({order_placeholders})
        LIMIT {n * 3}
    """).df()

    reviews = local_conn.execute(f"""
        SELECT order_id, review_score
        FROM reviews
        WHERE order_id IN ({order_placeholders})
        LIMIT {n * 2}
    """).df()

    local_conn.close()
    return customers, orders, items, reviews


with st.spinner("Loading graph data..."):
    customers_df, orders_df, items_df, reviews_df = load_graph_data(
        sample_size, st.session_state.graph_seed
    )

# --------------------------------
# Pre-compute counts (used for node sizing)
# --------------------------------
customer_order_counts = (
    orders_df.groupby("customer_id").size().to_dict() if not orders_df.empty else {}
)
order_item_counts = (
    items_df.groupby("order_id").size().to_dict() if not items_df.empty else {}
)
product_order_counts = (
    items_df.groupby("product_id").size().to_dict() if not items_df.empty else {}
)

# --------------------------------
# Build graph
# --------------------------------
G = nx.DiGraph()

# --- Customer nodes ---
for _, row in customers_df.iterrows():
    cid = row["customer_id"]
    purchase_count = customer_order_counts.get(cid, 0)
    size = 15 + min(purchase_count * 3, 25)
    G.add_node(
        cid,
        label=f"C_{cid[:6]}",
        title=f"Customer\nState: {row['customer_state']}\nID: {cid}\nOrders placed: {purchase_count}",
        color=NODE_COLORS["customer"],
        shape="dot",
        size=size,
        group="customer",
    )

# --- Order nodes + customer -> order edges ---
for _, row in orders_df.iterrows():
    cid = row["customer_id"]
    oid = row["order_id"]
    item_count = order_item_counts.get(oid, 0)
    size = 12 + min(item_count * 3, 20)
    G.add_node(
        oid,
        label=f"O_{oid[:6]}",
        title=f"Order\nID: {oid}\nItems in order: {item_count}",
        color=NODE_COLORS["order"],
        shape="box",
        size=size,
        group="order",
    )
    if cid in G.nodes:
        G.add_edge(
            cid,
            oid,
            label="PLACED",
            title="PLACED",
            color=EDGE_COLORS["placed"],
        )

# --- Product nodes + order -> product edges ---
for _, row in items_df.iterrows():
    oid = row["order_id"]
    pid = row["product_id"]
    raw_cat = row["product_category_name"] or "unknown"
    cat_label = raw_cat.replace("_", " ").title()
    order_count = product_order_counts.get(pid, 0)
    size = 10 + min(order_count * 3, 20)
    G.add_node(
        pid,
        label=cat_label[:18],
        title=f"Product\nCategory: {cat_label}\nProduct ID: {pid}\nOrdered: {order_count}x",
        color=NODE_COLORS["product"],
        shape="diamond",
        size=size,
        group="product",
    )
    if oid in G.nodes:
        G.add_edge(
            oid,
            pid,
            label="CONTAINS",
            title="CONTAINS",
            color=EDGE_COLORS["contains"],
        )

# --- Review nodes + order -> review edges ---
for _, row in reviews_df.iterrows():
    oid = row["order_id"]
    score = int(row["review_score"])
    rid = f"R_{oid}"
    stars = "★" * score + "☆" * (5 - score)
    G.add_node(
        rid,
        label=stars,
        title=f"Review\nScore: {score}/5\nOrder: {oid}",
        color=REVIEW_COLORS.get(score, NODE_COLORS["review"]),
        shape="star",
        size=12,
        group="review",
    )
    if oid in G.nodes:
        G.add_edge(
            oid,
            rid,
            label="HAS REVIEW",
            title="HAS REVIEW",
            color=EDGE_COLORS["has_review"],
        )

# --------------------------------
# Search highlighting
# --------------------------------
search_lower = search_term.strip().lower()
matched_node_id = None

if search_lower:
    for node_id, attrs in G.nodes(data=True):
        haystack = f"{node_id} {attrs.get('label', '')} {attrs.get('title', '')}".lower()
        if search_lower in haystack:
            base_color = attrs.get("color", "#999999")
            if not isinstance(base_color, str):
                base_color = "#999999"
            G.nodes[node_id]["color"] = {
                "background": base_color,
                "border": SEARCH_HIGHLIGHT_BORDER,
                "highlight": {
                    "background": base_color,
                    "border": SEARCH_HIGHLIGHT_BORDER,
                },
            }
            G.nodes[node_id]["borderWidth"] = 4
            G.nodes[node_id]["borderWidthSelected"] = 6
            G.nodes[node_id]["size"] = attrs.get("size", 12) + 8
            if matched_node_id is None:
                matched_node_id = node_id

    if matched_node_id is None:
        st.warning("No nodes matched your search.")

# --------------------------------
# Entity counts
# --------------------------------
st.subheader("📊 Entity Counts")
c1, c2, c3, c4 = st.columns(4)
c1.metric("🔵 Customers", customers_df.shape[0])
c2.metric("🟢 Orders", orders_df.shape[0])
c3.metric("🟠 Products", items_df["product_id"].nunique() if not items_df.empty else 0)
c4.metric("🔴 Reviews", reviews_df.shape[0])

# --------------------------------
# Graph statistics
# --------------------------------
total_nodes = G.number_of_nodes()
total_edges = G.number_of_edges()
density = nx.density(G) if total_nodes > 1 else 0.0

st.subheader("🧮 Graph Statistics")
g1, g2, g3 = st.columns(3)
g1.metric("Total Nodes", total_nodes)
g2.metric("Total Edges", total_edges)
g3.metric("Density", f"{density:.4%}")

st.divider()

# --------------------------------
# Render with PyVis
# --------------------------------
net = Network(
    height="600px",
    width="100%",
    bgcolor="#0e1117",
    font_color="white",
    directed=True,
)

net.from_nx(G)

physics_flag = "true" if enable_physics else "false"
# NOTE: net.set_options() below replaces the *entire* options object, so
# calling net.barnes_hut()/net.force_atlas_2based() beforehand has no effect --
# the solver must be specified directly inside this JSON instead.
solver = "forceAtlas2Based" if layout == "Force Atlas" else "barnesHut"

net.set_options(f"""
{{
  "nodes": {{
    "font": {{ "size": 14, "color": "#ffffff" }}
  }},
  "edges": {{
    "arrows": {{ "to": {{ "enabled": true, "scaleFactor": 0.5 }} }},
    "font": {{ "size": 10, "color": "#cccccc", "strokeWidth": 0, "align": "middle" }},
    "smooth": {{ "type": "curvedCW", "roundness": 0.2 }}
  }},
  "physics": {{
    "enabled": {physics_flag},
    "solver": "{solver}",
    "stabilization": {{ "enabled": true, "iterations": 150 }}
  }},
  "interaction": {{
    "hover": true,
    "tooltipDelay": 100,
    "navigationButtons": true
  }}
}}
""")

with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
    path = tmp.name

net.save_graph(path)

with open(path, "r", encoding="utf-8") as f:
    html = f.read()

os.unlink(path)

# --------------------------------
# Inject extra behaviour: freeze-after-stabilize + search focus
# (pyvis's generated HTML exposes a top-level `network` variable)
# --------------------------------
extra_js_lines = []

if enable_physics and freeze_after_stabilize:
    extra_js_lines.append("""
network.once("stabilizationIterationsDone", function () {
    network.setOptions({ physics: false });
});
""")

if matched_node_id is not None:
    safe_node_id = json.dumps(matched_node_id)
    extra_js_lines.append(f"""
network.once("stabilizationIterationsDone", function () {{
    network.focus({safe_node_id}, {{ scale: 1.3, animation: {{ duration: 600 }} }});
    network.selectNodes([{safe_node_id}]);
}});
if (!{physics_flag}) {{
    // physics disabled, so stabilizationIterationsDone may not fire -- focus immediately
    network.focus({safe_node_id}, {{ scale: 1.3, animation: {{ duration: 600 }} }});
    network.selectNodes([{safe_node_id}]);
}}
""")

if extra_js_lines:
    custom_script = "<script>\n" + "\n".join(extra_js_lines) + "\n</script>"
    html = html.replace("</body>", custom_script + "\n</body>")

st.components.v1.html(html, height=620, scrolling=False)

st.divider()

# --------------------------------
# Legend
# --------------------------------
st.subheader("🗺️ Legend")
l1, l2, l3, l4 = st.columns(4)
l1.info("🔵 ⬤ Customer")
l2.success("🟢 ▭ Order")
l3.warning("🟠 ◆ Product")
l4.error("⭐ Review (color = score)")

st.caption(
    "Edges: 🔵 PLACED (customer → order) · 🟠 CONTAINS (order → product) · "
    "🔴 HAS REVIEW (order → review)  |  Node size reflects activity "
    "(more orders/items = bigger)  |  Gold border = search match"
)
st.caption("Hover over any node for details. Drag to rearrange. Scroll to zoom.")

conn.close()