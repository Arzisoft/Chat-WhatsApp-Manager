"""
Lebanon Map — project locations as interactive markers.
"""

import json
import streamlit as st
import folium
from streamlit_folium import st_folium

from core.database import init_db, get_all_chats, get_analysis, get_financial_mentions
from core.geo import AREA_COORDS, LEBANON_CENTER, LEBANON_BOUNDS, get_coords
from components.brand import apply_brand, page_header
from components.colors import LIGHT, DARK
init_db()

st.set_page_config(page_title="Map | ChatChaos", page_icon=None, layout="wide")
apply_brand()
page_header("Project Map", "Lebanon — delivery sites & project locations")

# ── Load all chats that have an analysis with a known area ───────────────────
all_chats = get_all_chats()

# Build project list: one entry per chat with area + coordinates
projects = []
for c in all_chats:
    area = c['primary_area']
    if not area:
        continue
    coords = get_coords(area)
    if not coords:
        continue
    projects.append({
        'chat_id':   c['id'],
        'chat_name': c['chat_name'] or c['filename'],
        'area':      area,
        'coords':    coords,
        'status':    c['status']       or '—',
        'urgency':   c['urgency_level'] or 'Low',
        'category':  c['category']     or '—',
        'summary':   c['executive_summary'] or '',
        'followup':  bool(c['followup_needed']),
        'days_silent': c['days_silent'] or 0,
    })

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style='color:{LIGHT['accent_alt']};font-size:11px;font-weight:700;letter-spacing:1px;"
        f"text-transform:uppercase;margin-bottom:6px;'>Map Filters</div>",
        unsafe_allow_html=True,
    )
    all_areas = sorted(set(p['area'] for p in projects))
    sel_areas = st.multiselect("Areas", all_areas, default=all_areas, key="map_areas")

    all_statuses = sorted(set(p['status'] for p in projects if p['status'] != '—'))
    sel_statuses = st.multiselect("Status", all_statuses, default=all_statuses, key="map_status")

    urgencies = ['Critical', 'High', 'Medium', 'Low']
    sel_urgencies = st.multiselect("Urgency", urgencies, default=urgencies, key="map_urgency")

    show_followup_only = st.checkbox("Follow-ups only", key="map_followup")

# Apply filters
filtered = [p for p in projects
            if p['area'] in sel_areas
            and p['status'] in sel_statuses
            and p['urgency'] in sel_urgencies
            and (not show_followup_only or p['followup'])]

# ── Layout: map left, detail panel right ─────────────────────────────────────
map_col, detail_col = st.columns([3, 2], gap="medium")

# ── Urgency → marker color ────────────────────────────────────────────────────
_URGENCY_COLOR = {
    'Critical': 'red',
    'High':     'orange',
    'Medium':   'blue',
    'Low':      'green',
}
_STATUS_ICON = {
    'Active':           'play',
    'Waiting':          'pause',
    'Closed':           'ok-sign',
    'Lost':             'remove-sign',
    'Follow-up Needed': 'bell',
}

with map_col:
    if not filtered:
        st.info("No projects match the current filters.")
    else:
        # Build folium map — ESRI tiles (free, no API key)
        m = folium.Map(
            location=LEBANON_CENTER,
            zoom_start=9,
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri &mdash; Sources: Esri, HERE, DeLorme, USGS',
            name='Streets',
            max_zoom=19,
            prefer_canvas=True,
        )
        # Satellite layer toggle
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri &mdash; Source: Esri, Maxar, GeoEye',
            name='Satellite',
            max_zoom=19,
        ).add_to(m)
        # Light minimal layer
        folium.TileLayer(
            tiles='CartoDB positron',
            name='Light',
        ).add_to(m)
        folium.LayerControl(position='topright').add_to(m)

        # Restrict map to Lebanon bounds
        m.fit_bounds(LEBANON_BOUNDS)

        # Group projects by area so we can offset overlapping markers
        from collections import defaultdict
        area_projects: dict = defaultdict(list)
        for p in filtered:
            area_projects[p['area']].append(p)

        for area, area_ps in area_projects.items():
            base_lat, base_lng = area_ps[0]['coords']
            n = len(area_ps)
            for i, p in enumerate(area_ps):
                # Slight offset for multiple projects in same area
                offset_lat = (i - (n - 1) / 2) * 0.008
                offset_lng = (i - (n - 1) / 2) * 0.008
                lat = base_lat + offset_lat
                lng = base_lng + offset_lng

                color  = _URGENCY_COLOR.get(p['urgency'], 'gray')
                icon   = _STATUS_ICON.get(p['status'], 'info-sign')

                # Popup HTML
                followup_badge = (
                    "<span style='background:#e74c3c;color:white;border-radius:3px;"
                    "padding:1px 5px;font-size:10px;'>Follow-up</span>"
                    if p['followup'] else ""
                )
                popup_html = f"""
                <div style='font-family:Segoe UI,Arial,sans-serif;min-width:200px;'>
                    <div style='font-weight:700;font-size:13px;margin-bottom:4px;'>
                        {p['chat_name']} {followup_badge}
                    </div>
                    <div style='font-size:11px;color:#555;margin-bottom:6px;'>
                        {p['area']} &nbsp;|&nbsp; {p['category']}
                    </div>
                    <div style='font-size:11px;margin-bottom:4px;'>
                        <b>Status:</b> {p['status']} &nbsp;
                        <b>Urgency:</b> <span style='color:{"#e74c3c" if p["urgency"]=="Critical" else "#e67e22" if p["urgency"]=="High" else "#2980b9" if p["urgency"]=="Medium" else "#27ae60"}'>{p['urgency']}</span>
                    </div>
                    <div style='font-size:11px;color:#777;margin-top:4px;line-height:1.4;'>
                        {p['summary'][:160] + '…' if len(p['summary']) > 160 else p['summary']}
                    </div>
                    <div style='font-size:10px;color:#aaa;margin-top:6px;'>
                        Silent: {p['days_silent']} day(s)
                    </div>
                </div>
                """

                folium.Marker(
                    location=[lat, lng],
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=f"{p['chat_name']} — {p['area']}",
                    icon=folium.Icon(color=color, icon=icon, prefix='glyphicon'),
                ).add_to(m)

        # Render map and capture click
        map_data = st_folium(m, width='100%', height=560, returned_objects=["last_object_clicked_tooltip"])

        # Legend
        st.markdown(
            "<div style='font-size:11px;color:#888;margin-top:4px;display:flex;gap:16px;align-items:center;'>"
            "<span><span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:#e74c3c;margin-right:4px;'></span>Critical</span>"
            "<span><span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:#e67e22;margin-right:4px;'></span>High</span>"
            "<span><span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:#2980b9;margin-right:4px;'></span>Medium</span>"
            "<span><span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:#27ae60;margin-right:4px;'></span>Low</span>"
            "</div>",
            unsafe_allow_html=True,
        )

# ── Detail panel ──────────────────────────────────────────────────────────────
with detail_col:
    # Try to pick selected project from map click
    clicked_tooltip = None
    try:
        clicked_tooltip = map_data.get('last_object_clicked_tooltip') if map_data else None
    except Exception:
        pass

    # Match tooltip to project
    selected_project = None
    if clicked_tooltip:
        # Tooltip format: "ChatName — Area"
        for p in filtered:
            if clicked_tooltip.startswith(p['chat_name']):
                selected_project = p
                break

    if selected_project:
        p = selected_project
        _s_clr = {'Active': '#27ae60', 'Waiting': '#e67e22',
                  'Follow-up Needed': '#2980b9', 'Closed': '#95a5a6',
                  'Lost': '#e74c3c'}.get(p['status'], '#95a5a6')
        _u_clr = {'Critical': '#e74c3c', 'High': '#e67e22',
                  'Medium': '#2980b9', 'Low': '#27ae60'}.get(p['urgency'], '#95a5a6')

        st.markdown(
            f"<h3 style='margin:4px 0 2px 0;font-size:17px;'>{p['chat_name']}</h3>",
            unsafe_allow_html=True,
        )
        badge = lambda label, val, col: (
            f"<span style='background:{col}18;border:1px solid {col}44;"
            f"border-radius:4px;padding:2px 8px;font-size:11px;"
            f"color:{col};font-weight:600;margin-right:4px;'>{label}: {val}</span>"
        )
        st.markdown(
            badge("Area",     p['area'],     LIGHT['primary']) +
            badge("Status",   p['status'],   _s_clr) +
            badge("Urgency",  p['urgency'],  _u_clr),
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if p['summary']:
            st.info(p['summary'])

        # Pull full analysis for this chat
        analysis = get_analysis(p['chat_id'])
        if analysis:
            if analysis['followup_needed']:
                st.error(f"**Follow-Up:** {analysis['followup_action'] or analysis['followup_reason'] or 'Required'}")

            timeline = json.loads(analysis['timeline_json'] or '[]')
            if timeline:
                with st.expander(f"Timeline ({len(timeline)} events)"):
                    for ev in timeline:
                        st.markdown(
                            f"<div style='font-size:12px;padding:2px 0'>"
                            f"<b>{ev.get('date','?')}</b> — {ev.get('event','')}</div>",
                            unsafe_allow_html=True,
                        )

            sigs = json.loads(analysis['negotiation_signals'] or '[]')
            if sigs:
                st.markdown(
                    "<div style='font-size:12px;font-weight:600;margin-top:8px'>Signals</div>",
                    unsafe_allow_html=True,
                )
                for s in sigs:
                    st.markdown(f"<div style='font-size:12px'>• {s}</div>", unsafe_allow_html=True)

        # Financial snapshot
        financials = get_financial_mentions(p['chat_id'])
        if financials:
            total = sum(f['amount'] for f in financials
                        if f['amount'] and f['currency'] == 'USD'
                        and f['mention_type'] in ('total_order', 'quote', 'price_per_m3'))
            if total:
                st.metric("Pipeline (USD)", f"${total:,.0f}")

        if st.button("Full Chat Detail", key="map_goto_detail", use_container_width=True):
            st.session_state['chat_sel'] = f"{p['chat_name']}  (ID {p['chat_id']})"
            st.switch_page("pages/2_Chat_Detail.py")

    else:
        st.markdown(
            f"<div style='color:#999;font-size:13px;margin-top:24px;text-align:center;'>"
            f"Click a marker on the map<br>to view project details.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin:16px 0'>", unsafe_allow_html=True)

    # ── Project list ──────────────────────────────────────────────────────────
    st.markdown(
        f"<div style='font-size:12px;font-weight:700;color:{LIGHT['primary']};margin-bottom:6px;'>"
        f"ALL PROJECTS ({len(filtered)})</div>",
        unsafe_allow_html=True,
    )
    if not filtered:
        st.caption("No projects to display.")
    else:
        urgency_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        for p in sorted(filtered, key=lambda x: (urgency_order.get(x['urgency'], 9), x['area'])):
            dot_color = _URGENCY_COLOR.get(p['urgency'], 'gray')
            _dot_hex = {'red': '#e74c3c', 'orange': '#e67e22',
                        'blue': '#2980b9', 'green': '#27ae60'}.get(dot_color, '#95a5a6')
            followup_mark = "  <span style='font-size:9px;background:#e74c3c22;color:#e74c3c;border:1px solid #e74c3c44;border-radius:3px;padding:1px 5px;'>Follow-up</span>" if p['followup'] else ""
            st.markdown(
                f"<div style='display:flex;align-items:flex-start;gap:8px;"
                f"padding:5px 0;border-bottom:1px solid #f0f0f0;'>"
                f"<div style='width:8px;height:8px;border-radius:50%;background:{_dot_hex};"
                f"margin-top:4px;flex-shrink:0;'></div>"
                f"<div>"
                f"<div style='font-size:12px;font-weight:600;'>{p['chat_name']}{followup_mark}</div>"
                f"<div style='font-size:11px;color:#888;'>{p['area']} · {p['status']} · "
                f"{p['days_silent']}d silent</div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )




