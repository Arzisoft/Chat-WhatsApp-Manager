"""
Chat Detail — tabbed professional view with financial study.
"""

import json
import os
import streamlit as st
import pandas as pd
from core.database import (
    init_db, get_all_chats, get_analysis, get_messages,
    get_financial_mentions, mark_followup_done, update_area,
    get_contact, get_project, get_concrete_orders, get_action_items, complete_action_item,
)
from core.analyzer import AREA_TAXONOMY
from components.brand import apply_brand, page_header
from components.colors import LIGHT, DARK

_AUDIO_EXT = ('.opus', '.ogg', '.mp3', '.m4a', '.aac', '.wav')
_IMAGE_EXT  = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
_VIDEO_EXT  = ('.mp4', '.mov', '.avi', '.3gp', '.mkv')

_CSS = """
<style>
section[data-testid="stMain"] { font-size: 13px !important; }
[data-testid="stMetricLabel"] { font-size: 11px !important; }
[data-testid="stMetricValue"] { font-size: 17px !important; }
[data-testid="stExpander"] summary { font-size: 12px !important; }
[data-testid="stDataFrame"] { font-size: 12px !important; }
/* tab styling */
[data-testid="stTabs"] [role="tab"] { font-size: 12px !important; font-weight: 600; }
/* section headers */
.section-hdr {
    font-size: 11px; font-weight: 700; letter-spacing: .8px;
    text-transform: uppercase; color: #888; margin: 14px 0 6px 0;
    border-bottom: 1px solid #f0f0f0; padding-bottom: 3px;
}
/* info card */
.info-card {
    background: #f8fafd; border: 1px solid #dce8f5;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;
}
/* cost table row highlight */
.cost-total { font-weight: 700; background: #E8F1FB; }
</style>
"""

init_db()
st.set_page_config(page_title="Chat Detail | ChatChaos", page_icon=None, layout="wide")
apply_brand()
st.markdown(_CSS, unsafe_allow_html=True)
page_header("Chat Detail", "Project intelligence & message history")

# ── Chat selector ─────────────────────────────────────────────────────────────
all_chats = get_all_chats()
if not all_chats:
    st.info("No chats imported yet — go to **Import & Analyze** first.")
    st.stop()

chat_options = {f"{c['chat_name'] or c['filename']}  (ID {c['id']})": c['id'] for c in all_chats}
selected_label = st.selectbox("Select chat", list(chat_options.keys()),
                               label_visibility="collapsed", key="chat_sel")
chat_id  = chat_options[selected_label]
chat_row = next(c for c in all_chats if c['id'] == chat_id)

analysis       = get_analysis(chat_id)
messages       = get_messages(chat_id)
financials     = get_financial_mentions(chat_id)
contact_rec    = get_contact(chat_id)
project_rec    = get_project(chat_id)
concrete_orders = get_concrete_orders(chat_id)
action_items_rec = get_action_items(chat_id)

vn_total = sum(1 for m in messages if m['is_voice_note'])
vn_done  = sum(1 for m in messages if m['is_voice_note'] and m['transcription'])
days_silent = chat_row['days_silent'] or 0

# ── Header strip ──────────────────────────────────────────────────────────────
chat_name = chat_row['chat_name'] or chat_row['filename']

cat       = (analysis['category']         if analysis else None) or '—'
status    = (analysis['status']           if analysis else None) or '—'
urgency   = (analysis['urgency_level']    if analysis else None) or '—'
area      = (analysis['primary_area']     if analysis else None) or '—'
sentiment = (analysis['sentiment']        if analysis else None) or '—'
rel_stage = (analysis['relationship_stage'] if analysis else None) or '—'

s_clr = {'Active':'#27ae60','Waiting':'#e67e22','Follow-up Needed':'#2980b9',
          'Closed':'#95a5a6','Lost':'#e74c3c'}.get(status, '#95a5a6')
u_clr = {'Critical':'#e74c3c','High':'#e67e22','Medium':'#2980b9',
          'Low':'#27ae60'}.get(urgency, '#95a5a6')

badge = lambda label, val, col: (
    f"<span style='background:{col}18;border:1px solid {col}55;"
    f"border-radius:4px;padding:3px 10px;font-size:11px;"
    f"color:{col};font-weight:700;margin-right:6px;'>{label}: {val}</span>"
)

st.markdown(
    f"<div style='display:flex;align-items:center;gap:12px;margin:6px 0 4px 0;flex-wrap:wrap;'>"
    f"<span style='font-size:19px;font-weight:700;color:{LIGHT['text_primary']};'>{chat_name}</span>"
    f"</div>",
    unsafe_allow_html=True,
)
sent_clr  = {'Positive':'#27ae60','Neutral':'#2980b9',
             'Negative':'#e67e22','Frustrated':'#e74c3c'}.get(sentiment, '#95a5a6')
stage_clr = {'Hot':'#e74c3c','Negotiating':'#e67e22','Confirmed':'#27ae60',
             'Delivered':'#27ae60','Dispute':'#e74c3c','Warm':'#f39c12',
             'Cold':'#95a5a6'}.get(rel_stage, '#95a5a6')

st.markdown(
    badge("Category", cat, LIGHT['primary']) +
    badge("Status",   status, s_clr) +
    badge("Urgency",  urgency, u_clr) +
    badge("Stage",    rel_stage, stage_clr) +
    badge("Sentiment",sentiment, sent_clr) +
    badge("Area", area, '#555'),
    unsafe_allow_html=True,
)
st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_overview, tab_contact, tab_orders, tab_actions, tab_financials, tab_intel, tab_messages = st.tabs([
    "Overview", "Contact & Project",
    "Concrete Orders", "Action Items",
    "Financials", "Intelligence", "Messages"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab_overview:
    # KPI row
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Messages",    chat_row['message_count'])
    k2.metric("First Contact",(chat_row['date_first_msg'] or '—')[:10])
    k3.metric("Last Activity",(chat_row['date_last_msg']  or '—')[:10])
    k4.metric("Voice Notes",  f"{vn_done}/{vn_total}" if vn_total else "—")
    k5.metric("Days Silent",  days_silent)
    open_count = sum(1 for a in action_items_rec if not a['completed'])
    k6.metric("Open Actions", open_count if action_items_rec else "—")

    # Voice note transcription trigger (inline, no separate page needed)
    vn_pending = vn_total - vn_done
    if vn_pending > 0:
        api_key_local = st.session_state.get('api_key') or __import__('os').getenv('GEMINI_API_KEY', '').strip()
        if api_key_local:
            st.info(f"{vn_pending} voice note(s) not yet transcribed.")
            if st.button(f"Transcribe {vn_pending} Voice Note(s)", key="vn_transcribe_btn"):
                from core.transcriber import transcribe_audio
                from core.database import get_voice_notes, get_media_dir, save_transcription
                import os as _os
                media_dir_path = get_media_dir(chat_id)
                vn_rows = get_voice_notes(chat_id)
                untranscribed = [r for r in vn_rows if not r['transcription']]
                done_count = 0
                for row in untranscribed:
                    fname = _os.path.basename(row.get('media_path') or '')
                    audio_path = _os.path.join(media_dir_path, fname) if fname else ''
                    if not audio_path or not _os.path.exists(audio_path):
                        continue
                    with st.spinner(f"Transcribing {fname}..."):
                        try:
                            with open(audio_path, 'rb') as af:
                                res = transcribe_audio(af.read(), fname, api_key_local)
                            save_transcription(
                                row['id'],
                                res['transcription'],
                                res.get('translation'),
                                res.get('summary'),
                                res.get('location_detected'),
                            )
                            done_count += 1
                            info_parts = [f"({res.get('language','?').upper()})"]
                            if res.get('summary'):
                                info_parts.append(res['summary'])
                            if res.get('location_detected'):
                                info_parts.append(f"Location: {res['location_detected']}")
                            st.write(f"`{fname}` " + " | ".join(info_parts))
                        except Exception as exc:
                            st.warning(f"{fname}: {exc}")
                st.success(f"Transcribed {done_count}/{len(untranscribed)} voice notes.")
                st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2], gap="medium")

    with col_l:
        if analysis and analysis['executive_summary']:
            st.info(analysis['executive_summary'])

        # Project details table
        st.markdown("<div class='section-hdr'>Project Details</div>", unsafe_allow_html=True)
        sec_areas = json.loads(analysis['secondary_areas'] or '[]') if analysis else []
        details = {
            'Field': ['Contact', 'Area', 'Secondary Areas', 'Category', 'Status',
                      'Urgency', 'Last Activity', 'Analyzed'],
            'Value': [
                chat_name,
                area,
                ', '.join(sec_areas) if sec_areas else '—',
                cat,
                status,
                urgency,
                (chat_row['date_last_msg'] or '—')[:10],
                (analysis['analyzed_at'][:10] if analysis and analysis['analyzed_at'] else '—'),
            ],
        }
        st.dataframe(pd.DataFrame(details), use_container_width=True,
                     hide_index=True, height=318)

        # Manual area override — compact inline
        if analysis:
            st.markdown("<div class='section-hdr'>Set Area</div>", unsafe_allow_html=True)
            current_area = analysis['primary_area'] or ''
            area_options = [''] + sorted(AREA_TAXONOMY)
            current_idx  = area_options.index(current_area) if current_area in area_options else 0
            ac1, ac2 = st.columns([4, 1])
            chosen_area = ac1.selectbox(
                "Area override", area_options, index=current_idx,
                key="area_override_sel", label_visibility="collapsed",
            )
            if ac2.button("Save", key="area_save_btn", use_container_width=True):
                if chosen_area:
                    update_area(chat_id, chosen_area)
                    st.success(f"Area updated: **{chosen_area}**")
                    st.rerun()

    with col_r:
        # Follow-up box
        if analysis and analysis['followup_needed']:
            st.error("Follow-Up Required")
            if analysis['followup_reason']:
                st.markdown(
                    f"<div class='info-card'>"
                    f"<div style='font-size:11px;color:#888;font-weight:700;margin-bottom:4px;'>WHY</div>"
                    f"<div style='font-size:12px;line-height:1.5;'>{analysis['followup_reason']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            if analysis['followup_action']:
                st.markdown(
                    f"<div class='info-card' style='border-color:#FDA50D44;background:#FFFAF2;'>"
                    f"<div style='font-size:11px;color:{LIGHT['accent_alt']};font-weight:700;margin-bottom:4px;'>ACTION REQUIRED</div>"
                    f"<div style='font-size:12px;line-height:1.5;'>{analysis['followup_action']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            if st.button("Mark Follow-up Done", key="done_btn", use_container_width=True):
                mark_followup_done(chat_id)
                st.success("Done!")
                st.rerun()
        elif analysis:
            st.success("No follow-up needed")

        # Negotiation signals
        if analysis:
            sigs = json.loads(analysis['negotiation_signals'] or '[]')
            if sigs:
                st.markdown("<div class='section-hdr'>Negotiation Signals</div>",
                            unsafe_allow_html=True)
                for s in sigs:
                    st.markdown(
                        f"<div style='font-size:12px;padding:3px 0;border-bottom:1px solid #f5f5f5;'>"
                        f"• {s}</div>",
                        unsafe_allow_html=True,
                    )

        # Quick financial snapshot
        if financials:
            st.markdown("<div class='section-hdr'>Pipeline Snapshot</div>",
                        unsafe_allow_html=True)
            total = sum(f['amount'] for f in financials
                        if f['amount'] and f['currency'] == 'USD'
                        and f['mention_type'] in ('total_order','quote','price_per_m3','volume_m3'))
            if total:
                st.metric("Est. Pipeline (USD)", f"${total:,.0f}")
            st.caption(f"{len(financials)} financial mention(s) recorded")

        # Mini Lebanon location map
        if area and area != '—':
            try:
                from core.geo import get_coords
                import folium
                from streamlit_folium import st_folium
                coords = get_coords(area)
                if coords:
                    st.markdown("<div class='section-hdr'>Location</div>",
                                unsafe_allow_html=True)
                    mini_m = folium.Map(
                        location=coords, zoom_start=11,
                        tiles='CartoDB positron',
                    )
                    folium.Marker(
                        location=coords, tooltip=area,
                        icon=folium.Icon(color='blue', prefix='glyphicon'),
                    ).add_to(mini_m)
                    st_folium(mini_m, height=200, width=None, returned_objects=[])
                    st.caption(area)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — CONTACT & PROJECT
# ─────────────────────────────────────────────────────────────────────────────
with tab_contact:
    cp_l, cp_r = st.columns(2, gap="medium")

    with cp_l:
        st.markdown("<div class='section-hdr'>Contact</div>", unsafe_allow_html=True)
        if contact_rec:
            dm_badge = " <span style='background:#27ae6022;border:1px solid #27ae60;border-radius:3px;padding:1px 6px;font-size:10px;color:#27ae60;'>Decision Maker</span>" if contact_rec['is_decision_maker'] else ""
            st.markdown(
                f"<div class='info-card'>"
                f"<div style='font-size:15px;font-weight:700;margin-bottom:6px;'>"
                f"{contact_rec['name'] or '—'}{dm_badge}</div>"
                f"<div style='font-size:12px;line-height:2;'>"
                f"<b>Role:</b> {contact_rec['role'] or '—'}<br>"
                f"<b>Company:</b> {contact_rec['company'] or '—'}<br>"
                f"<b>Phone:</b> {contact_rec['phone'] or '—'}"
                f"</div></div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption("No contact data extracted. Re-analyze to populate.")

        # Payment info
        if analysis and (analysis['payment_terms'] or analysis['payment_method'] or analysis['payment_outstanding']):
            st.markdown("<div class='section-hdr'>Payment Info</div>", unsafe_allow_html=True)
            overdue_html = "<span style='color:#e74c3c;font-weight:700;'>[WARNING] OVERDUE</span>" if analysis['payment_overdue'] else "[DONE] Current"
            st.markdown(
                f"<div class='info-card' style='{'border-color:#e74c3c55;' if analysis['payment_overdue'] else ''}'>"
                f"<div style='font-size:12px;line-height:2;'>"
                f"<b>Terms:</b> {analysis['payment_terms'] or '—'}<br>"
                f"<b>Method:</b> {analysis['payment_method'] or '—'}<br>"
                f"<b>Outstanding:</b> {'$'+str(analysis['payment_outstanding']) if analysis['payment_outstanding'] else '—'}<br>"
                f"<b>Status:</b> {overdue_html}"
                f"</div></div>",
                unsafe_allow_html=True,
            )

        # Competitors
        if analysis:
            competitors = json.loads(analysis['competitors_mentioned'] or '[]')
            if competitors:
                st.markdown("<div class='section-hdr'>Competitors Mentioned</div>", unsafe_allow_html=True)
                for c in competitors:
                    st.markdown(f"<div style='font-size:12px;padding:2px 0;'>• {c}</div>", unsafe_allow_html=True)

        # Language mix
        if analysis:
            langs = json.loads(analysis['language_mix'] or '[]')
            if langs:
                st.markdown("<div class='section-hdr'>Language Mix</div>", unsafe_allow_html=True)
                st.caption(', '.join(langs))

    with cp_r:
        st.markdown("<div class='section-hdr'>Project</div>", unsafe_allow_html=True)
        if project_rec and any(project_rec[k] for k in ['name','type','location_detail','floors','area_m2','total_m3_estimate']):
            details = {
                'Field': ['Name', 'Type', 'Location Detail', 'Floors', 'Area (m²)', 'Total m³ Est.', 'Start Date', 'Completion'],
                'Value': [
                    project_rec['name']            or '—',
                    project_rec['type']            or '—',
                    project_rec['location_detail'] or '—',
                    str(project_rec['floors'])     if project_rec['floors'] else '—',
                    f"{project_rec['area_m2']:,.0f}"          if project_rec['area_m2'] else '—',
                    f"{project_rec['total_m3_estimate']:,.0f}" if project_rec['total_m3_estimate'] else '—',
                    project_rec['start_date']      or '—',
                    project_rec['completion_date'] or '—',
                ],
            }
            st.dataframe(pd.DataFrame(details), use_container_width=True,
                         hide_index=True, height=318)
        else:
            st.caption("No project details extracted. Re-analyze to populate.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — CONCRETE ORDERS
# ─────────────────────────────────────────────────────────────────────────────
with tab_orders:
    if not concrete_orders:
        st.info("No concrete orders extracted from this chat.")
    else:
        total_m3 = sum(o['volume_m3'] for o in concrete_orders if o['volume_m3'])
        st.metric("Total Volume", f"{total_m3:,.1f} m³",
                  help="Sum of all quoted/ordered volumes in this chat")

        order_rows = []
        for o in concrete_orders:
            order_rows.append({
                'Mix':      o['mix_grade'] or '—',
                'Slump':    o['slump']     or '—',
                'Pump':     '[DONE]' if o['pump_required'] else '—',
                'Volume m³':f"{o['volume_m3']:,.1f}"   if o['volume_m3']   else '—',
                'Price/m³': f"${o['price_per_m3']:,.2f}" if o['price_per_m3'] else '—',
                'Currency': o['currency'] or 'USD',
                'Delivery': (o['delivery_date'] or '—')[:10],
                'Status':   o['status']   or '—',
            })
        st.dataframe(pd.DataFrame(order_rows), use_container_width=True,
                     hide_index=True, height=min(38*len(order_rows)+40, 400))

        # Cost estimate for the biggest order
        biggest = max(concrete_orders, key=lambda x: x['volume_m3'] or 0, default=None)
        if biggest and biggest['volume_m3'] and biggest['price_per_m3']:
            st.markdown("<div class='section-hdr'>Quick Cost Estimate (largest order)</div>",
                        unsafe_allow_html=True)
            vol = biggest['volume_m3']
            ppm = biggest['price_per_m3']
            trucks = max(1, int(-(-(vol) // 7.5)))
            concrete_cost = vol * ppm
            transport = trucks * 150
            total_est = concrete_cost + transport
            e1, e2, e3, e4 = st.columns(4)
            e1.metric("Volume",   f"{vol:,.1f} m³")
            e2.metric("Concrete", f"${concrete_cost:,.0f}")
            e3.metric("Transport",f"${transport:,.0f} ({trucks} trucks)")
            e4.metric("Estimate", f"${total_est:,.0f}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — ACTION ITEMS
# ─────────────────────────────────────────────────────────────────────────────
with tab_actions:
    open_items = [a for a in action_items_rec if not a['completed']]
    done_items = [a for a in action_items_rec if a['completed']]

    if not action_items_rec:
        st.info("No action items extracted from this chat. Re-analyze to populate.")
    else:
        st.caption(f"{len(open_items)} open · {len(done_items)} completed")

        priority_color = {
            'Critical': '#e74c3c', 'High': '#e67e22',
            'Medium': '#2980b9', 'Low': '#27ae60',
        }

        if open_items:
            st.markdown("<div class='section-hdr'>Open Actions</div>", unsafe_allow_html=True)
            for item in open_items:
                col_action, col_btn = st.columns([5, 1])
                pclr = priority_color.get(item['priority'] or 'Medium', '#2980b9')
                due = f"  ·  Due: **{item['due_date']}**" if item['due_date'] else ''
                with col_action:
                    st.markdown(
                        f"<div style='border-left:3px solid {pclr};padding:6px 12px;"
                        f"background:{pclr}11;border-radius:0 6px 6px 0;margin-bottom:4px;'>"
                        f"<span style='font-size:10px;color:{pclr};font-weight:700;"
                        f"text-transform:uppercase;'>{item['priority'] or 'Medium'}</span>"
                        f"<div style='font-size:13px;margin-top:2px;'>{item['action']}</div>"
                        f"<div style='font-size:10px;color:#888;'>{due}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with col_btn:
                    if st.button("Done", key=f"action_done_{item['id']}",
                                 use_container_width=True):
                        complete_action_item(item['id'])
                        st.rerun()

        if done_items:
            with st.expander(f"Completed ({len(done_items)})"):
                for item in done_items:
                    st.markdown(
                        f"<div style='font-size:12px;color:#aaa;text-decoration:line-through;"
                        f"padding:3px 0;'>{item['action']}</div>",
                        unsafe_allow_html=True,
                    )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — FINANCIALS & COST STUDY
# ─────────────────────────────────────────────────────────────────────────────
with tab_financials:
    fc_l, fc_r = st.columns([3, 2], gap="medium")

    with fc_l:
        st.markdown("<div class='section-hdr'>Raw Financial Mentions</div>",
                    unsafe_allow_html=True)
        if financials:
            fin_rows = [{
                'Date':     (f['mention_date'] or '—')[:10],
                'Type':     (f['mention_type'] or '—').replace('_', ' ').title(),
                'Amount':   f"{f['amount']:,.2f}" if f['amount'] else '—',
                'Currency': f['currency'] or 'USD',
                'Quote':    (f['raw_text'] or '')[:60],
                'Note':     (f['context_note'] or '')[:60],
            } for f in financials]
            st.dataframe(pd.DataFrame(fin_rows), use_container_width=True,
                         hide_index=True, height=200)
        else:
            st.caption("No financial mentions recorded.")

        # ── Cost Study Calculator ──────────────────────────────────────────
        st.markdown("<div class='section-hdr'>Cost Study Calculator</div>",
                    unsafe_allow_html=True)

        # Try to pre-fill from financial data
        _unit_price_hint = next(
            (f['amount'] for f in financials
             if f['mention_type'] in ('price_per_m3', 'quote') and f['amount']),
            28.0
        )
        _area_hint = 0.0
        for f in financials:
            if f['mention_type'] == 'volume_m3' and f['amount']:
                _area_hint = f['amount']
                break

        ci1, ci2, ci3 = st.columns(3)
        surface_m2  = ci1.number_input("Surface Area (m²)", min_value=0.0,
                                        value=float(_area_hint) or 185.0,
                                        step=10.0, key="cs_area")
        depth_cm    = ci2.number_input("Concrete Depth (cm)", min_value=5.0,
                                        value=10.0, step=1.0, key="cs_depth")
        unit_price  = ci3.number_input("Unit Price ($/m²)", min_value=0.0,
                                        value=float(_unit_price_hint),
                                        step=1.0, key="cs_price")

        ci4, ci5, ci6 = st.columns(3)
        transport_per_trip = ci4.number_input("Transport / truck ($)", min_value=0.0,
                                               value=150.0, step=10.0, key="cs_transport")
        pump_cost   = ci5.number_input("Pump rental ($)", min_value=0.0,
                                        value=200.0, step=50.0, key="cs_pump")
        vat_pct     = ci6.number_input("VAT (%)", min_value=0.0,
                                        value=11.0, step=1.0, key="cs_vat")

        # Calculations
        volume_m3       = surface_m2 * (depth_cm / 100.0)
        truck_capacity  = 7.5   # m³ per truck
        num_trucks      = max(1, int(-(-volume_m3 // truck_capacity)))  # ceiling division
        transport_total = num_trucks * transport_per_trip
        concrete_total  = surface_m2 * unit_price
        subtotal        = concrete_total + transport_total + pump_cost
        vat_amount      = subtotal * (vat_pct / 100)
        grand_total     = subtotal + vat_amount

        cost_table = pd.DataFrame([
            {'Item': 'Decorative / Stamped Concrete',
             'Qty': f"{surface_m2:,.0f}", 'Unit': 'm²',
             'Unit Price': f"${unit_price:,.2f}", 'Total (USD)': f"${concrete_total:,.2f}"},
            {'Item': f'Transport ({num_trucks} truck{"s" if num_trucks>1 else ""})',
             'Qty': str(num_trucks), 'Unit': 'trip',
             'Unit Price': f"${transport_per_trip:,.0f}", 'Total (USD)': f"${transport_total:,.2f}"},
            {'Item': 'Concrete Pump Rental',
             'Qty': '1', 'Unit': 'day',
             'Unit Price': f"${pump_cost:,.0f}", 'Total (USD)': f"${pump_cost:,.2f}"},
            {'Item': '─── Subtotal', 'Qty': '', 'Unit': '',
             'Unit Price': '', 'Total (USD)': f"${subtotal:,.2f}"},
            {'Item': f'VAT ({vat_pct:.0f}%)', 'Qty': '', 'Unit': '',
             'Unit Price': '', 'Total (USD)': f"${vat_amount:,.2f}"},
            {'Item': '═══ GRAND TOTAL', 'Qty': '', 'Unit': '',
             'Unit Price': '', 'Total (USD)': f"${grand_total:,.2f}"},
        ])
        st.dataframe(cost_table, use_container_width=True, hide_index=True, height=248)

        # Key metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Volume",       f"{volume_m3:.1f} m³")
        m2.metric("Trucks Needed", num_trucks)
        m3.metric("Grand Total",  f"${grand_total:,.0f}")

    with fc_r:
        st.markdown("<div class='section-hdr'>Notes</div>", unsafe_allow_html=True)
        st.markdown(
            f"""<div class='info-card'>
            <div style='font-size:11px;color:#888;margin-bottom:8px;font-weight:700;'>CALCULATION BASIS</div>
            <div style='font-size:12px;line-height:1.8;'>
            • Volume = Surface × Depth<br>
            • Truck capacity: <b>7.5 m³</b> (standard Lebanon)<br>
            • Trucks = ⌈Volume ÷ 7.5⌉ (rounded up)<br>
            • Transport per truck: editable<br>
            • Pump rental: flat rate per day<br>
            • VAT: Lebanese standard ({vat_pct:.0f}%)<br><br>
            <span style='color:{LIGHT['accent_alt']};font-weight:700;'>Note: Labour / finishing cost
            not included — varies by pattern complexity.</span>
            </div></div>""",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='section-hdr'>Volume Breakdown</div>", unsafe_allow_html=True)
        vol_df = pd.DataFrame([
            {'Parameter': 'Surface area',    'Value': f"{surface_m2:,.0f} m²"},
            {'Parameter': 'Concrete depth',  'Value': f"{depth_cm:.0f} cm"},
            {'Parameter': 'Volume required', 'Value': f"{volume_m3:.2f} m³"},
            {'Parameter': 'Truck loads',     'Value': f"{num_trucks} × 7.5 m³"},
            {'Parameter': 'Unit price',      'Value': f"${unit_price:.2f}/m²"},
            {'Parameter': 'Price/m³ equiv',  'Value': f"${unit_price/(depth_cm/100):.2f}/m³"},
        ])
        st.dataframe(vol_df, use_container_width=True, hide_index=True, height=248)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — INTELLIGENCE
# ─────────────────────────────────────────────────────────────────────────────
with tab_intel:
    if not analysis:
        st.warning("Not analyzed yet — go to **Import & Analyze**.")
    else:
        ia_l, ia_r = st.columns([3, 2], gap="medium")

        with ia_l:
            # Timeline as dataframe
            timeline = json.loads(analysis['timeline_json'] or '[]')
            st.markdown(
                f"<div class='section-hdr'>Timeline ({len(timeline)} events)</div>",
                unsafe_allow_html=True,
            )
            if timeline:
                tl_df = pd.DataFrame([
                    {'Date': ev.get('date', '?'), 'Event': ev.get('event', '')}
                    for ev in timeline
                ])
                st.dataframe(tl_df, use_container_width=True, hide_index=True,
                             height=min(35 * len(timeline) + 38, 400))
            else:
                st.caption("No timeline events.")

            # Lifecycle
            transitions = json.loads(analysis['lifecycle_transitions'] or '[]')
            st.markdown("<div class='section-hdr'>Lifecycle Transitions</div>",
                        unsafe_allow_html=True)
            if transitions:
                for t in transitions:
                    st.markdown(
                        f"<div style='font-size:12px;padding:4px 0;"
                        f"border-bottom:1px solid #f0f0f0;'>{t}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No transitions recorded.")

        with ia_r:
            # Negotiation signals
            sigs = json.loads(analysis['negotiation_signals'] or '[]')
            st.markdown(
                f"<div class='section-hdr'>Negotiation Signals ({len(sigs)})</div>",
                unsafe_allow_html=True,
            )
            if sigs:
                for s in sigs:
                    st.markdown(
                        f"<div class='info-card' style='padding:8px 12px;margin-bottom:6px;'>"
                        f"<div style='font-size:12px;'>• {s}</div></div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No signals.")

            # Secondary areas
            sec = json.loads(analysis['secondary_areas'] or '[]')
            if sec:
                st.markdown("<div class='section-hdr'>Secondary Areas</div>",
                            unsafe_allow_html=True)
                for a in sec:
                    st.markdown(
                        f"<div style='font-size:12px;padding:2px 0;'>• {a}</div>",
                        unsafe_allow_html=True,
                    )

            # Analysis metadata
            st.markdown("<div class='section-hdr'>Analysis Metadata</div>",
                        unsafe_allow_html=True)
            meta_df = pd.DataFrame([
                {'Field': 'Model',         'Value': analysis['model_used'] or '—'},
                {'Field': 'Analyzed at',   'Value': (analysis['analyzed_at'] or '—')[:19]},
                {'Field': 'Last activity', 'Value': analysis['last_activity_date'] or '—'},
                {'Field': 'Days silent',   'Value': str(days_silent)},
            ])
            st.dataframe(meta_df, use_container_width=True, hide_index=True, height=178)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — MESSAGES
# ─────────────────────────────────────────────────────────────────────────────
with tab_messages:
    if not messages:
        st.caption("No messages.")
        st.stop()

    # Filter bar
    fc1, fc2, fc3, fc4 = st.columns([4, 1, 1, 1])
    search     = fc1.text_input("Search", placeholder="🔍 Search messages…",
                                 label_visibility="collapsed", key="search")
    show_media = fc2.checkbox("Media", value=True,  key="show_media")
    show_vn    = fc3.checkbox("Voice", value=True,  key="show_vn")
    limit      = fc4.number_input("Limit", 10, 500, 100, 10,
                                   key="limit", label_visibility="collapsed")

    display = list(messages)
    if not show_vn:
        display = [m for m in display if not m['is_voice_note']]
    if not show_media:
        display = [m for m in display if not m['is_media'] or m['is_voice_note']]
    if search:
        sq = search.lower()
        display = [m for m in display
                   if sq in (m['body'] or '').lower()
                   or sq in (m['transcription'] or '').lower()
                   or sq in (m['translation'] or '').lower()]
    display = display[-int(limit):]

    st.markdown(
        f"<div style='font-size:11px;color:#888;margin-bottom:8px;'>"
        f"Showing <b>{len(display)}</b> of <b>{len(messages)}</b> messages"
        f"</div>",
        unsafe_allow_html=True,
    )

    for msg in display:
        body       = msg['body']       or ''
        sender     = msg['sender']     or ''
        ts         = (msg['timestamp'] or '')[:16]
        is_vn      = bool(msg['is_voice_note'])
        transc     = msg['transcription']     if 'transcription'     in msg.keys() else None
        transl     = msg['translation']       if 'translation'       in msg.keys() else None
        vn_summary = msg['vn_summary']        if 'vn_summary'        in msg.keys() else None
        vn_location= msg['vn_location']       if 'vn_location'       in msg.keys() else None
        media_path = msg['media_path']        if 'media_path'        in msg.keys() else None
        attached   = msg['attached_filename'] if 'attached_filename' in msg.keys() else None

        is_outgoing = 'ChatChaos' in sender.lower()
        is_arabic   = any('\u0600' <= c <= '\u06ff' for c in body)
        rtl_style   = 'direction:rtl;text-align:right;' if is_arabic else ''

        # WhatsApp bubble styling
        if is_outgoing:
            align      = 'flex-end'
            bubble_bg  = '#E3F2FD'
            border_r   = '12px 2px 12px 12px'
            name_clr   = LIGHT['primary']
            border_clr = f'1px solid {LIGHT['primary']}33'
        else:
            align      = 'flex-start'
            bubble_bg  = '#FFFFFF'
            border_r   = '2px 12px 12px 12px'
            name_clr   = '#555'
            border_clr = '1px solid #E0E0E0'

        ts_short = ts[11:16] if len(ts) >= 16 else ts

        with st.container():
            if is_vn:
                has_file = bool(media_path and os.path.exists(media_path))
                if has_file:
                    if is_outgoing:
                        _, ac = st.columns([1, 2])
                    else:
                        ac, _ = st.columns([2, 1])
                    with open(media_path, 'rb') as af:
                        ac.audio(af.read(), format='audio/ogg')

                if transc:
                    ar    = any('\u0600' <= c <= '\u06ff' for c in transc)
                    rtl_t = 'direction:rtl;text-align:right;' if ar else ''
                    transl_html = (
                        f'<div style="color:{LIGHT['accent_alt']};font-size:11px;margin-top:4px;'
                        f'border-top:1px solid #eee;padding-top:4px;">[EN] {transl}</div>'
                        if transl else ''
                    )
                    summary_html = (
                        f'<div style="background:#f0f7ff;border-radius:4px;padding:5px 8px;'
                        f'margin-top:6px;font-size:11px;color:#2980b9;">'
                        f'<b>Summary:</b> {vn_summary}</div>'
                        if vn_summary else ''
                    )
                    location_html = (
                        f'<div style="display:inline-block;margin-top:5px;'
                        f'background:#27ae6018;border:1px solid #27ae6044;'
                        f'border-radius:4px;padding:2px 8px;font-size:10px;color:#27ae60;">'
                        f'Location: {vn_location}</div>'
                        if vn_location else ''
                    )
                    st.markdown(
                        f"<div style='display:flex;justify-content:{align};margin:3px 0 10px 0;'>"
                        f"<div style='max-width:75%;background:{bubble_bg};border:{border_clr};"
                        f"border-radius:{border_r};padding:8px 12px;"
                        f"box-shadow:0 1px 2px rgba(0,0,0,0.06);'>"
                        f"<div style='font-size:10px;color:{name_clr};font-weight:600;margin-bottom:3px;'>{sender}</div>"
                        f"<div style='font-size:9px;color:#888;text-transform:uppercase;"
                        f"letter-spacing:.5px;margin-bottom:4px;'>Voice note</div>"
                        f"<div style='{rtl_t}font-size:13px;line-height:1.55;'>{transc}</div>"
                        f"{transl_html}"
                        f"{summary_html}"
                        f"{location_html}"
                        f"<div style='font-size:10px;color:#aaa;text-align:right;margin-top:4px;'>{ts_short}</div>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )
                elif not has_file:
                    st.markdown(
                        f"<div style='display:flex;justify-content:{align};margin:3px 0 10px 0;'>"
                        f"<div style='max-width:75%;background:{bubble_bg};border:{border_clr};"
                        f"border-radius:{border_r};padding:8px 12px;'>"
                        f"<div style='font-size:10px;color:{name_clr};font-weight:600;margin-bottom:3px;'>{sender}</div>"
                        f"<div style='font-size:12px;color:#bbb;font-style:italic;'>Voice note — import folder with media to play</div>"
                        f"<div style='font-size:10px;color:#aaa;text-align:right;margin-top:4px;'>{ts_short}</div>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )

            elif media_path and os.path.exists(media_path):
                ext   = os.path.splitext(media_path)[1].lower()
                fname = attached or os.path.basename(media_path)
                st.markdown(
                    f"<div style='font-size:10px;color:{name_clr};font-weight:600;"
                    f"text-align:{'right' if is_outgoing else 'left'};margin-bottom:2px;'>"
                    f"{sender}  ·  {ts_short}</div>",
                    unsafe_allow_html=True,
                )
                if ext in _IMAGE_EXT:
                    if is_outgoing:
                        _, img_col = st.columns([1, 2])
                    else:
                        img_col, _ = st.columns([2, 1])
                    img_col.image(media_path, caption=fname, width='stretch')
                elif ext in _AUDIO_EXT:
                    with open(media_path, 'rb') as af:
                        st.audio(af.read())
                elif ext in _VIDEO_EXT:
                    with open(media_path, 'rb') as vf:
                        st.video(vf.read())
                else:
                    with open(media_path, 'rb') as df:
                        st.download_button(f"Download: {fname}", df.read(),
                                           file_name=fname, key=f"dl_{msg['id']}")

            elif attached:
                st.markdown(
                    f"<div style='display:flex;justify-content:{align};margin:3px 0 10px 0;'>"
                    f"<div style='max-width:75%;background:{bubble_bg};border:{border_clr};"
                    f"border-radius:{border_r};padding:8px 12px;'>"
                    f"<div style='font-size:10px;color:{name_clr};font-weight:600;margin-bottom:3px;'>{sender}</div>"
                    f"<div style='font-size:12px;color:#888;'>Attachment: {attached}</div>"
                    f"<div style='font-size:10px;color:#aaa;text-align:right;margin-top:4px;'>{ts_short}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

            else:
                # Regular text message bubble
                st.markdown(
                    f"<div style='display:flex;justify-content:{align};margin:3px 0 6px 0;'>"
                    f"<div style='max-width:75%;background:{bubble_bg};border:{border_clr};"
                    f"border-radius:{border_r};padding:8px 12px;"
                    f"box-shadow:0 1px 2px rgba(0,0,0,0.06);'>"
                    f"<div style='font-size:10px;color:{name_clr};font-weight:600;margin-bottom:3px;'>{sender}</div>"
                    f"<div style='{rtl_style}font-size:13px;line-height:1.6;'>{body}</div>"
                    f"<div style='font-size:10px;color:#aaa;text-align:right;margin-top:4px;'>{ts_short}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )




