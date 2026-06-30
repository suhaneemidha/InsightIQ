"""
Sidebar UI helpers.

These components are purely presentational and work alongside
your existing Streamlit navigation without changing routing.
"""

import streamlit as st


def render_sidebar_brand(
    name: str = "InsightIQ",
    subtitle: str | None = None,
) -> None:
    """
    Render the application branding at the top of the sidebar.
    """

    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand">
            {name}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if subtitle:
        st.sidebar.markdown(
            f"""
            <div class="subheading"
                 style="font-size:.85rem;
                        margin-top:-6px;
                        margin-bottom:1rem;
                        opacity:.85;">
                {subtitle}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_nav_item(
    label: str,
    active: bool = False,
    icon: str = "",
) -> None:
    """
    Render a styled navigation item.

    Parameters
    ----------
    label
        Navigation label.

    active
        Highlight the item.

    icon
        Optional emoji/icon.
    """

    active_class = "active" if active else ""

    icon_html = (
        f'<span style="margin-right:10px;">{icon}</span>'
        if icon
        else ""
    )

    st.sidebar.markdown(
        f"""
        <div class="nav-item {active_class}">
            {icon_html}
            <span>{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )