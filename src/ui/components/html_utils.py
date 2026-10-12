"""
SPARC-PM: HTML Sanitizer & Rendering Utilities
==============================================
Sanitizes raw HTML to prevent CommonMark / Markdown from treating
indented HTML as indented code blocks (<pre><code>).
"""

from __future__ import annotations

import streamlit as st


def clean_html(html: str) -> str:
    """Strips all leading and trailing whitespace from every line, joining with a single space.
    
    Guarantees CommonMark or HTML parsers will never treat indented lines as code blocks.
    """
    return " ".join(line.strip() for line in html.splitlines() if line.strip())


def render_html(html: str) -> None:
    """Safely renders HTML directly into the DOM.
    
    Uses native st.html() in Streamlit (bypassing CommonMark markdown parsing completely).
    Falls back to st.markdown with sanitized single-line HTML if st.html is unavailable.
    """
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(clean_html(html), unsafe_allow_html=True)
