"""
Core layout helpers: CSS loading and page-level wrappers.
"""
import streamlit as st
from pathlib import Path

CSS_DIR = Path(__file__).parent.parent / "assets" / "css"


def load_css(files: list[str]) -> None:
    """
    Load and inject one or more CSS files (in order) into the app.
    Order matters: theme.css should load before components.css, etc.
    """
    css = []
    for filename in files:
        path = CSS_DIR / filename
        if path.exists():
            css.append(path.read_text(encoding="utf-8"))
        else:
            st.warning(f"CSS file not found: {filename}")

    st.markdown(
        f"<style>{''.join(css)}</style>",
        unsafe_allow_html=True,
    )

def apply_global_styles() -> None:
    """Convenience wrapper — call once at the top of app.py."""
    load_css([
        "theme.css",
        "base.css",
        "animations.css",
        "components.css",
        "hero.css",
        "sidebar.css",
    ])


def page_container(content_fn) -> None:
    """
    Wrap a page's rendering function in a fade-in container.
    Usage:
        def render():
            st.write("page content")
        page_container(render)
    """
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    content_fn()
    st.markdown('</div>', unsafe_allow_html=True)


def section_spacer(height_px: int = 24) -> None:
    """Add consistent vertical whitespace between sections."""
    st.markdown(f"<div style='height:{height_px}px'></div>", unsafe_allow_html=True)

def divider(
    margin_top: int = 16,
    margin_bottom: int = 16,
) -> None:
    """
    Render a subtle divider that matches the theme.
    """

    st.markdown(
        f"""
        <hr style="
            border:none;
            border-top:1px solid var(--border-color);
            margin:{margin_top}px 0 {margin_bottom}px;
        ">
        """,
        unsafe_allow_html=True,
    )