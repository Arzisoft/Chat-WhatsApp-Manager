"""
Follow-Up Tracker — Modern action management interface.
Priority-sorted action items and chat follow-ups.
"""

import streamlit as st
import pandas as pd
from collections import Counter

from core.database import (
    init_db, get_followups, get_distinct_areas, get_distinct_categories,
    mark_followup_done, get_open_action_items,
)
from components.brand import apply_brand, page_header
from components.theme import get_colors
from components.ui_components import action_card, alert_box

init_db()

st.set_page_config(page_title="Follow-Ups | Sales Intelligence", page_icon="[DONE]", layout="wide")
apply_brand()

page_header("Follow-Up Management", "Track action items and follow-up requirements by urgency")

colors = get_colors()

# ── Filters ───────────────────────────────────────────────────────────────────
st.markdown("### Filter Actions")
filter_cols = st.columns([2, 2, 2], gap="medium")

with filter_cols[0]:
    areas = get_distinct_areas()
    area_filter = st.selectbox("Area", ["All"] + areas, index=0)
    selected_area = area_filter if area_filter != "All" else None

with filter_cols[1]:
    categories = get_distinct_categories()
    cat_filter = st.multiselect("Category", categories, default=[])

with filter_cols[2]:
    urgency_filter = st.multiselect(
        "Urgency",
        ['Critical', 'High', 'Medium', 'Low'],
        default=['Critical', 'High', 'Medium', 'Low']
    )

st.divider()

# ── Tabs: Follow-ups vs Action Items ──────────────────────────────────────────
tab_followups, tab_actions = st.tabs(["📌 Chat Follow-Ups", "[TARGET] Action Items"])

# ── TAB 1: Chat Follow-Ups ────────────────────────────────────────────────────
with tab_followups:
    followups = get_followups(
        area=selected_area,
        categories=cat_filter if cat_filter else None,
    )
    
    if not followups:
        alert_box(
            "No follow-ups required. Great job staying on top of your leads!",
            alert_type="success"
        )
        st.stop()
    
    # Group by urgency
    urgency_map = {
        'critical': ('🔴 Critical', 'critical'),
        'high': ('🟠 High', 'high'),
        'medium': ('🟡 Medium', 'medium'),
        'low': ('🔵 Low', 'low'),
    }
    
    for urgency_level in ['critical', 'high', 'medium', 'low']:
        if urgency_level not in urgency_filter:
            continue
        
        filtered = [f for f in followups if (f.get('urgency_level') or 'low').lower() == urgency_level]
        if not filtered:
            continue
        
        display_name, color = urgency_map[urgency_level]
        st.markdown(f"### {display_name}")
        
        cols = st.columns(1)
        with cols[0]:
            for fu in filtered:
                action_card(
                    title=f"{fu['chat_name']} • {fu['contact_name'] or 'Unknown'}",
                    description=fu.get('reason', 'Follow-up required'),
                    urgency=urgency_level,
                    icon=urgency_map[urgency_level][0],
                )
                
                # Quick action buttons
                fcol1, fcol2, fcol3 = st.columns([1, 1, 2])
                with fcol1:
                    if st.button("[OK] Mark Done", key=f"fu_done_{fu['id']}", use_container_width=True):
                        mark_followup_done(fu['id'])
                        st.success("Marked complete!")
                        st.rerun()
                with fcol2:
                    if st.button("[CHAT] View Chat", key=f"fu_chat_{fu['id']}", use_container_width=True):
                        st.switch_page("pages/2_Chat_Detail.py")
                with fcol3:
                    pass
                
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ── TAB 2: Action Items ───────────────────────────────────────────────────────
with tab_actions:
    actions = get_open_action_items(
        area=selected_area,
        categories=cat_filter if cat_filter else None,
    )
    
    if not actions:
        alert_box(
            "No open action items. Your pipeline is organized!",
            alert_type="success"
        )
        st.stop()
    
    # Sort by urgency and date
    urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    actions_sorted = sorted(
        actions,
        key=lambda x: (
            urgency_order.get((x.get('urgency_level') or 'low').lower(), 99),
            x.get('due_date') or '9999-12-31'
        )
    )
    
    # Group by urgency
    for urgency_level in ['critical', 'high', 'medium', 'low']:
        if urgency_level not in urgency_filter:
            continue
        
        filtered = [a for a in actions_sorted 
                   if (a.get('urgency_level') or 'low').lower() == urgency_level]
        if not filtered:
            continue
        
        display_name, color = urgency_map[urgency_level]
        st.markdown(f"### {display_name}")
        
        for action in filtered:
            action_card(
                title=action.get('title', 'Untitled action'),
                description=f"{action.get('description', '')} | Due: {action.get('due_date', 'No date')}",
                urgency=urgency_level,
                icon=urgency_map[urgency_level][0],
            )
            
            # Quick action buttons
            acol1, acol2, acol3 = st.columns([1, 1, 2])
            with acol1:
                if st.button("[OK] Complete", key=f"action_done_{action['id']}", use_container_width=True):
                    # TODO: Implement action completion
                    st.success("Action marked complete!")
                    st.rerun()
            with acol2:
                if st.button("→ Defer", key=f"action_defer_{action['id']}", use_container_width=True):
                    # TODO: Implement deferring
                    st.info("Action deferred.")
                    st.rerun()
            with acol3:
                pass
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ── Statistics ────────────────────────────────────────────────────────────────
st.divider()
st.markdown("### Statistics")

stat_cols = st.columns(4, gap="small")
with stat_cols[0]:
    st.metric("Total Follow-Ups", len(followups))
with stat_cols[1]:
    critical_count = len([f for f in followups if (f.get('urgency_level') or 'low').lower() == 'critical'])
    st.metric("🔴 Critical", critical_count)
with stat_cols[2]:
    high_count = len([f for f in followups if (f.get('urgency_level') or 'low').lower() == 'high'])
    st.metric("🟠 High", high_count)
with stat_cols[3]:
    by_area = pd.DataFrame([{'area': f.get('primary_area', 'Unknown')} for f in followups])
    if len(by_area) > 0:
        st.metric("[LOCATION] Regions", by_area['area'].nunique())
    else:
        st.metric("[LOCATION] Regions", 0)


