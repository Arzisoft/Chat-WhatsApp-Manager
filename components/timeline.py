"""
Chronological event timeline renderer.
"""

import json
import streamlit as st
from typing import List, Dict, Any, Union


def render_timeline(events: Union[List[Dict[str, Any]], str], title: str = "Timeline"):
    """
    Render a chronological timeline of events.

    Args:
        events: list of {date, event} dicts, or a JSON string
        title: section header text
    """
    if isinstance(events, str):
        try:
            events = json.loads(events)
        except (json.JSONDecodeError, TypeError):
            events = []

    if not events:
        st.caption("No timeline events recorded.")
        return

    st.markdown(f"**{title}** ({len(events)} events)")

    for i, event in enumerate(events):
        date = event.get('date', '?')
        description = event.get('event', '')

        # Alternate connector style
        connector = "┣" if i < len(events) - 1 else "┗"

        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: flex-start;
                margin-bottom: 8px;
                padding: 8px;
                border-left: 2px solid #444;
                margin-left: 8px;
            ">
                <div style="
                    min-width: 100px;
                    color: #00cc88;
                    font-size: 12px;
                    font-weight: bold;
                    padding-right: 12px;
                ">
                    {date}
                </div>
                <div style="color: white; font-size: 14px;">
                    {description}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
