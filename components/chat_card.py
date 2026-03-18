"""
Reusable chat summary card widget.
"""

import streamlit as st
import json


def render_chat_card(chat_row, analysis_row=None):
    """
    Render a compact summary card for a chat.

    Args:
        chat_row: sqlite3.Row from chats table (may include joined analysis fields)
        analysis_row: optional sqlite3.Row from analyses table
    """
    chat_name = chat_row['chat_name'] or chat_row['filename']

    # Get analysis data from either source
    if analysis_row:
        category = analysis_row['category'] or '—'
        status = analysis_row['status'] or '—'
        urgency = analysis_row['urgency_level'] or '—'
        area = analysis_row['primary_area'] or '—'
        summary = analysis_row.get('executive_summary') or ''
        followup = bool(analysis_row['followup_needed'])
    elif 'category' in chat_row.keys():
        category = chat_row['category'] or '—'
        status = chat_row['status'] or '—'
        urgency = chat_row['urgency_level'] or '—'
        area = chat_row['primary_area'] or '—'
        summary = chat_row.get('executive_summary') or ''
        followup = bool(chat_row.get('followup_needed', False))
    else:
        category = status = urgency = area = '—'
        summary = ''
        followup = False

    status_icon = {
        'Active': '🟢', 'Waiting': '🟡', 'Follow-up Needed': '🔵',
        'Closed': '⚫', 'Lost': '🔴',
    }.get(status, '⚪')

    urgency_icon = {
        'Critical': '🚨', 'High': '⚠️', 'Medium': '📋', 'Low': '✅',
    }.get(urgency, '')

    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{chat_name}**")
            st.caption(
                f"{status_icon} {status}  |  {urgency_icon} {urgency}  |  "
                f"📍 {area}  |  🏷️ {category}"
            )
            if summary:
                st.caption(summary[:120] + ('...' if len(summary) > 120 else ''))
        with col2:
            if followup:
                st.error("🔔 Follow-up")
            else:
                st.success("✅ OK")
