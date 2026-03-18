"""
Area Overview page — geographic intelligence grid.
"""

import re
import streamlit as st
import pandas as pd
from core.database import init_db, get_area_stats, get_contacts_by_area
from components.brand import apply_brand, page_header


def _looks_like_phone(s: str) -> bool:
    """Return True if the string is just a phone number, not a real name."""
    if not s:
        return False
    cleaned = re.sub(r'[\s\-\+\(\)\.x]', '', s)
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15


def _is_valid_phone(s: str) -> bool:
    """Return True only for real phone numbers (not raw WhatsApp internal IDs)."""
    if not s:
        return False
    d = re.sub(r'\D', '', s)
    # WhatsApp internal IDs tend to be >13 digits and don't start with a real CC
    if len(d) > 13:
        return False
    # Must start with a plausible country code or local format
    if s.strip().startswith('+'):
        return True
    if d.startswith('961'):   # Lebanon
        return 11 <= len(d) <= 12
    if len(d) == 8:           # local Lebanese (no CC)
        return True
    return 8 <= len(d) <= 13


def _format_lebanese(digits: str) -> str:
    """Best-effort pretty-print a Lebanese number from raw digits."""
    d = re.sub(r'\D', '', digits)
    if d.startswith('961') and len(d) >= 11:
        rest = d[3:]
        if len(rest) == 8:
            return f"+961 {rest[0]} {rest[1:4]} {rest[4:]}"
        return f"+961 {rest}"
    if len(d) == 8:
        return f"+961 {d[0]} {d[1:4]} {d[4:]}"
    return '+' + d if not digits.startswith('+') else digits


def _best_phone(ct_phone, chat_name) -> str:
    """Pick the most human-readable valid phone string."""
    candidates = [ct_phone, chat_name]
    # prefer formatted +xxx first
    for c in candidates:
        if c and c.strip().startswith('+') and _is_valid_phone(c):
            return c.strip()
    # then any valid numeric candidate
    for c in candidates:
        if c and _looks_like_phone(c) and _is_valid_phone(c):
            return _format_lebanese(c)
    return ""

init_db()

st.set_page_config(page_title="Area Overview | TopCrete", page_icon=None, layout="wide")
apply_brand()
page_header("Area Overview", "Geographic breakdown of TopCrete's project pipeline across Lebanon")

area_stats = get_area_stats()

if not area_stats:
    st.info("No analyzed chats yet. Upload and analyze chats to see geographic intelligence.")
    st.stop()

# Summary metrics
total_areas    = len(area_stats)
total_pipeline = sum(a['pipeline_usd'] or 0 for a in area_stats)
total_m3       = sum(a['pipeline_m3']  or 0 for a in area_stats)
total_hot      = sum(a['hot']          or 0 for a in area_stats)

m1, m2, m3_col, m4 = st.columns(4)
m1.metric("Active Markets",      total_areas)
m2.metric("Pipeline (USD)",      f"${total_pipeline:,.0f}")
m3_col.metric("Pipeline (m3)",   f"{total_m3:,.0f}")
m4.metric("Hot / Negotiating",   total_hot)

st.markdown("---")

# Sort options
sort_by = st.selectbox(
    "Sort by",
    ["Total Chats", "Pipeline Value", "Pipeline m3", "Hot Leads", "Active Deals"],
    index=0,
)

sort_key = {
    "Total Chats":    "total_chats",
    "Pipeline Value": "pipeline_usd",
    "Pipeline m3":    "pipeline_m3",
    "Hot Leads":      "hot",
    "Active Deals":   "active",
}[sort_by]

sorted_areas = sorted(area_stats, key=lambda x: x[sort_key] or 0, reverse=True)

# ── Colour helpers ────────────────────────────────────────────────────────────

URGENCY_COLORS = {
    'Critical': '#ff3333',
    'High':     '#ff9900',
    'Medium':   '#ffcc00',
    'Low':      '#44bb44',
}
STATUS_COLORS = {
    'Active':          '#00cc88',
    'Follow-up Needed':'#ff9900',
    'Waiting':         '#aaaaaa',
    'Closed':          '#888888',
    'Lost':            '#cc4444',
}
STAGE_COLORS = {
    'Hot':         '#ff4400',
    'Negotiating': '#ff9900',
    'Warm':        '#ffcc00',
    'Confirmed':   '#00cc88',
    'Cold':        '#888888',
    'Delivered':   '#4488ff',
    'Dispute':     '#cc3333',
}

def _badge(text, color):
    return (
        f"<span style='background:{color};color:#fff;"
        f"border-radius:4px;padding:2px 7px;font-size:11px;font-weight:600;'>{text}</span>"
    )

# ── 3-column grid ─────────────────────────────────────────────────────────────

cols_per_row = 3
for i in range(0, len(sorted_areas), cols_per_row):
    row_areas = sorted_areas[i:i + cols_per_row]
    cols = st.columns(cols_per_row)

    for col, area in zip(cols, row_areas):
        with col:
            pipeline  = area['pipeline_usd'] or 0
            pip_m3    = area['pipeline_m3']  or 0
            total     = area['total_chats']
            active    = area['active']
            hot       = area['hot']
            leads     = area['leads']
            projects  = area['projects']
            closed    = area['closed']
            area_name = area['primary_area']

            if active > 2 or pipeline > 500_000:
                border_color = "#00cc00"
            elif active > 0 or leads > 0:
                border_color = "#ff9900"
            else:
                border_color = "#888888"

            # Stats card (always visible)
            st.markdown(
                f"""
                <div style="
                    border: 2px solid {border_color};
                    border-radius: 10px 10px 0 0;
                    padding: 16px;
                    background: #1a1a2e;
                ">
                    <h3 style="margin:0; color:white;">{area_name}</h3>
                    <hr style="margin:8px 0; border-color:#444;">
                    <table style="width:100%; color:white; font-size:14px;">
                        <tr><td>Total Chats</td><td align="right"><b>{total}</b></td></tr>
                        <tr><td>Active</td><td align="right"><b>{active}</b></td></tr>
                        <tr><td>Hot / Negotiating</td><td align="right"><b>{hot}</b></td></tr>
                        <tr><td>Leads</td><td align="right"><b>{leads}</b></td></tr>
                        <tr><td>Projects</td><td align="right"><b>{projects}</b></td></tr>
                        <tr><td>Closed / Lost</td><td align="right"><b>{closed}</b></td></tr>
                    </table>
                    <hr style="margin:8px 0; border-color:#444;">
                    <div style="color:#00cc88; font-size:15px; font-weight:bold;">
                        Pipeline: ${pipeline:,.0f}
                    </div>
                    <div style="color:#88ccff; font-size:13px;">
                        Volume: {pip_m3:,.1f} m3
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Clickable expander for client list
            with st.expander(f"👥 View {total} client(s) in {area_name}"):
                contacts = get_contacts_by_area(area_name)

                if not contacts:
                    st.caption("No contact details available yet.")
                else:
                    scroll = st.container(height=360, border=False)
                    with scroll:
                        for ct in contacts:
                            raw_name  = ct['name'] or ""
                            chat_name = ct['chat_name'] or ""
                            raw_phone = ct['phone'] or ""

                            # Best phone: prefer raw_phone, fall back to raw_name/chat_name
                            best_ph = _best_phone(raw_phone, raw_name or chat_name)

                            # Best display name: a real name (not a phone number)
                            real_name = None
                            for candidate in (raw_name, chat_name):
                                if candidate and not _looks_like_phone(candidate):
                                    real_name = candidate
                                    break

                            if real_name:
                                name  = real_name
                                phone = best_ph          # show phone separately
                            else:
                                name  = best_ph or chat_name or "Unknown"
                                phone = ""               # phone IS the title — don't duplicate

                            status   = ct['status'] or ""
                            urgency  = ct['urgency_level'] or ""
                            stage    = ct['relationship_stage'] or ""
                            role     = ct['role'] or ""
                            company  = ct['company'] or ""

                            subtitle_parts = []
                            if role and role != 'Unknown': subtitle_parts.append(role)
                            if company: subtitle_parts.append(company)
                            subtitle = " · ".join(subtitle_parts)

                            # Render bubble using native Streamlit — avoids nested HTML issues
                            bubble = st.container(border=True)
                            with bubble:
                                st.markdown(f"**{name}**")
                                if phone:
                                    st.caption(f"[PHONE] {phone}")
                                if subtitle:
                                    st.caption(subtitle)
                                badges = " &nbsp; ".join(
                                    _badge(t, c) for t, c in [
                                        (status,  STATUS_COLORS.get(status,  '#555')),
                                        (urgency, URGENCY_COLORS.get(urgency,'#555')),
                                        (stage,   STAGE_COLORS.get(stage,   '#555')),
                                    ] if t
                                )
                                if badges:
                                    st.markdown(badges, unsafe_allow_html=True)

            # Bottom border continuation
            st.markdown(
                f"<div style='border: 2px solid {border_color}; border-top:none; border-radius:0 0 10px 10px; height:4px;'></div>",
                unsafe_allow_html=True,
            )

# Detailed table
st.markdown("---")
st.subheader("Detailed Area Table")

df = pd.DataFrame([{
    'Area':         a['primary_area'],
    'Total Chats':  a['total_chats'],
    'Active':       a['active'],
    'Hot':          a['hot'],
    'Leads':        a['leads'],
    'Projects':     a['projects'],
    'Closed/Lost':  a['closed'],
    'Pipeline (USD)': f"${a['pipeline_usd']:,.0f}" if a['pipeline_usd'] else '$0',
    'Pipeline (m3)':  f"{a['pipeline_m3']:,.1f}"   if a['pipeline_m3'] else '0',
} for a in sorted_areas])

st.dataframe(df, use_container_width=True, hide_index=True)


