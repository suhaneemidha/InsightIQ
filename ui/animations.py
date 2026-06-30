"""
Small helpers for staggered fade/slide entrance animations.
"""
import streamlit as st


def fade_in_wrapper(content_fn, delay_class: str = "") -> None:
    """Wrap any render function's output in a fade/slide-up animation."""
    st.markdown(f'<div class="slide-up {delay_class}">', unsafe_allow_html=True)
    content_fn()
    st.markdown("</div>", unsafe_allow_html=True)


def shimmer_placeholder(height_px: int = 80) -> None:
    """Loading shimmer block — use while data/model results are loading."""
    st.markdown(
        f'<div class="shimmer-loading" style="height:{height_px}px; border-radius:18px;"></div>',
        unsafe_allow_html=True,
    )