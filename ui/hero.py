"""
Animated particle hero section — rendered via components.v1.html
because it needs a real canvas animation loop.
"""

from pathlib import Path
import streamlit.components.v1 as components


TEMPLATE_PATH = (
    Path(__file__).parent.parent
    / "static"
    / "particles_template.html"
)


def render_hero_section(
    badge_text: str = "Business Intelligence Platform",
    title: str = "InsightIQ",
    subtitle: str = (
        "Transform raw business data into meaningful insights "
        "through conversational analytics and AI."
    ),
    cta_text: str = "Explore Dashboard",
    height: int = 480,
) -> None:
    """
    Render the animated hero section.

    Parameters
    ----------
    badge_text
        Small badge displayed above the title.

    title
        Main heading.

    subtitle
        Supporting description.

    cta_text
        Call-to-action button text.

    height
        Height of the hero (pixels).
    """

    html = TEMPLATE_PATH.read_text(encoding="utf-8")

    replacements = {
        "__HEIGHT__": str(height),
        "__BADGE_TEXT__": badge_text,
        "__TITLE__": title,
        "__SUBTITLE__": subtitle,
        "__CTA_TEXT__": cta_text,
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    components.html(
        html,
        height=height,
        scrolling=False,
    )
    