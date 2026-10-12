# src/ui/components/navigation_rail.py
"""Compact vertical navigation rail used across the SPARC-PM UI.
Provides grouped sections: OPERATIONS, MISSION, RESPONSE, SYSTEM.
Each entry is a button; the selected value is stored in
st.session_state["selected_page"].
"""

import streamlit as st

# -------------------------------------------------------------------------
# Navigation structure
# -------------------------------------------------------------------------
_SECTIONS = {
    "OPERATIONS": [
        "🧭 Mission Control",
        "📊 Overview",
        "🛰️ Orbital Monitor",
        "📈 Space Weather",
    ],
    "MISSION": [
        "👨‍🚀 Crew Dosimetry",
        "🔧 Fleet Health",
        "⚙️ Predictive Maintenance",
    ],
    "RESPONSE": [
        "📡 Command Center",
        "⚠️ Hazard Analysis",
    ],
    "SYSTEM": [
        "📋 Telemetry Feeds",
        "🗃️ Data Sources",
    ],
}


def render_navigation() -> None:
    """Render the navigation rail in the sidebar.
    The selected page is stored in ``st.session_state['selected_page']``.
    """
    st.markdown(
        "<div style='font-family: \"JetBrains Mono\", monospace; "
        "font-size: 0.62rem; color: #475569; font-weight: 700; "
        "letter-spacing: 1px;'>NAVIGATION</div>",
        unsafe_allow_html=True,
    )

    # Initialise default selection and migrate legacy icon if present
    if "selected_page" not in st.session_state or st.session_state.get("selected_page") == "🌐 Mission Control":
        st.session_state["selected_page"] = "🧭 Mission Control"

    for section, pages in _SECTIONS.items():
        st.markdown(
            f"<div style='font-family: \"Inter\", sans-serif; "
            f"font-size:0.68rem; color:#94a3b8; margin-top:8px;'>{section}</div>",
            unsafe_allow_html=True,
        )
        for p in pages:
            # Highlight the active selection
            style = (
                "background:#1e293b; color:#f8fafc;" if st.session_state["selected_page"] == p
                else "background:#0f172a; color:#94a3b8;"
            )
            if st.button(p, key=f"nav_{p.replace(' ', '_')}"):
                st.session_state["selected_page"] = p
                st.rerun()
        st.markdown("---", unsafe_allow_html=True)
