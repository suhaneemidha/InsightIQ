"""
Reusable UI components: cards, badges, metrics, headings, buttons.
These are presentation-only — they never touch business logic.
"""
import streamlit as st


def glass_card(content_html: str, extra_class: str = "") -> None:
    """Render a glassmorphism card with arbitrary inner HTML."""
    st.markdown(
    f'<div class="glass-card hover-lift scale-in {extra_class}">{content_html}</div>',
    unsafe_allow_html=True,
    )


def badge(text: str) -> None:
    """Small glass pill badge, e.g. for status labels."""
    st.markdown(
        f'<span class="glass-badge"><span class="dot"></span>{text}</span>',
        unsafe_allow_html=True,
    )


def gradient_heading(text: str, level: int = 1) -> None:
    """Large heading with the brand gradient applied."""
    tag = f"h{level}"
    st.markdown(
        f'<{tag} class="gradient-heading slide-up">{text}</{tag}>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, col=None) -> None:
    """
    Styled metric card (alternative to st.metric with full design control).
    Pass a column object to render inside that column, otherwise renders inline.
    """
    html = f"""
    <div class="metric-card hover-lift scale-in">
        <div class="metric-label">
            {label}
        </div>
        <div class="metric-value">
            {value}
        </div>
    </div>
    """
    target = col if col is not None else st
    target.markdown(html, unsafe_allow_html=True)


def metric_row(metrics: list[dict]) -> None:
    """
    Render a row of metric cards.
    metrics = [{"label": "Total Rows", "value": "12,430"}, ...]
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        metric_card(m["label"], m["value"], col=col)


def section_header(title: str, subtitle: str = "") -> None:
    """Consistent section header used across all pages."""
    st.markdown(f'<h2 class="slide-up">{title}</h2>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            f'<p class="subheading slide-up slide-up-delay-1" style="margin-top:-8px;">{subtitle}</p>',
            unsafe_allow_html=True,
        )


def footer(text: str = "Built with Streamlit · © 2026") -> None:
    """Consistent footer across all pages."""
    st.markdown(f'<div class="app-footer">{text}</div>', unsafe_allow_html=True)

def sidebar_stat(icon: str, label: str, value: str) -> None:
    """Styled glass stat card for sidebar (replaces default st.metric look)."""
    st.sidebar.markdown(f"""
    <div class="glass-card hover-lift slide-up" style="padding:0.8rem 1rem; margin-bottom:10px;">
        <div style="font-family:'Cabin',sans-serif; font-size:.82rem; letter-spacing:.05em; text-transform:uppercase; color:var(--text-muted); display:flex; align-items:center; gap:6px;">
            <span>{icon}</span><span>{label}</span>
        </div>
        <div style="font-family:'Oswald',sans-serif; font-size:1.7rem; font-weight:500; color:var(--text-primary); margin-top:2px;">
            {value}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_flow_diagram(steps: list[str]) -> None:
    """
    Render a vertical animated flow diagram with glass nodes
    connected by gradient lines. Reusable for any pipeline (ETL, ML, etc).
    """
    nodes_html = ""
    for i, step in enumerate(steps):
        delay = f"slide-up-delay-{min(i + 1, 3)}" if i > 0 else ""
        nodes_html += f'<div class="flow-node glass-card hover-glow slide-up {delay}">{step}</div>'
        if i < len(steps) - 1:
            nodes_html += '<div class="flow-connector"></div>'

    st.markdown(f'<div class="flow-diagram">{nodes_html}</div>', unsafe_allow_html=True)

def feature_card(icon: str, title: str, description: str):

    glass_card(f"""
        <div style="font-size:2rem;margin-bottom:14px;">
            {icon}
        </div>

        <h3 style="margin-bottom:8px;">
            {title}
        </h3>

        <p class="subheading">
            {description}
        </p>
    """)