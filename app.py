"""
Sales Intelligence Platform - Professional Demo
Main entry point: global dashboard with KPI cards and modern UI.
NO TopCrete branding - fully generic, client-ready design.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# ── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Sales Intelligence Dashboard",
    page_icon="[DASH]",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load env & init DB ───────────────────────────────────────────────────────
# Load environment from .env.txt (relative path in current directory)
load_dotenv(os.path.join(os.getcwd(), '.env.txt'))

# Fallback: Try loading from .env if .env.txt doesn't exist
if not os.getenv('GEMINI_API_KEY'):
    load_dotenv(os.path.join(os.getcwd(), '.env'))

from core.database import init_db, get_kpis, get_all_chats, get_pipeline_summary
from components.brand import apply_brand, page_header, product_name, product_tagline
from components.theme import theme_toggle_widget, get_colors
from components.colors import PRODUCT_NAME, PRODUCT_DESCRIPTION
from components.ui_components import (
    kpi_card, feature_card, action_card, hero_banner, 
    stat_bar, alert_box
)

init_db()
apply_brand()

# ── Sidebar: API key + Theme toggle ───────────────────────────────────────────
with st.sidebar:
    theme_toggle_widget()
    st.divider()
    
    # Get API key from environment (now properly loaded)
    env_key = os.getenv('GEMINI_API_KEY', '').strip() if os.getenv('GEMINI_API_KEY') else ''
    
    if env_key:
        st.success("API key loaded from .env.txt")
        st.session_state['api_key'] = env_key
    else:
        st.warning("No API key configured")
        manual_key = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIzaSy...",
            help="Add to .env.txt: GEMINI_API_KEY=...",
        )
        if manual_key:
            st.session_state['api_key'] = manual_key
            st.success("API key saved to session")

# ── Load data ─────────────────────────────────────────────────────────────────
chats    = get_all_chats()
kpis     = get_kpis()
pipeline = get_pipeline_summary()

# ══════════════════════════════════════════════════════════════════════════════
# LANDING PAGE — Professional onboarding (shown when no chats imported)
# ══════════════════════════════════════════════════════════════════════════════
if not chats:
    colors = get_colors()
    
    # Hero Banner
    hero_banner(
        title="Sales Intelligence Platform",
        subtitle="Professional AI-powered chat analytics and sales pipeline management",
        cta_text="Get Started →",
        gradient=True
    )
    
    # Feature Cards (4-column grid)
    st.markdown("### Key Features")
    f1, f2, f3, f4 = st.columns(4, gap="medium")
    
    with f1:
        feature_card(
            "Intelligent Analysis",
            "AI-powered extraction of leads, deal stages, customer contacts, and concrete orders from every conversation."
        )
    with f2:
        feature_card(
            "Live Dashboard",
            "Real-time KPI cards, pipeline totals by region and grade, urgency tracking, and sales metrics at a glance."
        )
    with f3:
        feature_card(
            "Risk Detection",
            "Automatically identifies stalled negotiations, silent leads, overdue payments, and deals requiring immediate attention."
        )
    with f4:
        feature_card(
            "Geographic Intelligence",
            "Interactive map showing deal locations across regions with deal summaries and regional performance analytics."
        )
    
    st.divider()
    
    # How to Get Started + Navigation
    st.markdown("### Getting Started")
    how_col, nav_col = st.columns([1.2, 1], gap="large")
    
    with how_col:
        st.markdown("**Step-by-Step Setup**")
        steps = [
            ("API Key", "Add your Gemini API key in the sidebar or .env.txt"),
            ("Export Chat", "Open WhatsApp → Menu → Export Chat → With Media"),
            ("Import", "Go to 'Import & Analyze' and upload the folder"),
            ("Analyze", "Platform automatically processes and generates insights"),
        ]
        for i, (step, desc) in enumerate(steps, 1):
            st.markdown(f"**{i}. {step}** — {desc}")
    
    with nav_col:
        st.markdown("**Available Pages**")
        pages = [
            ("Import & Analyze", "Upload WhatsApp exports or scan QR code to begin analysis"),
            ("Chat Detail", "Full conversation history with AI summaries and action items"),
            ("Area Overview", "Organize chats by Lebanese regions for regional intelligence"),
            ("Follow-Ups", "Priority-sorted action list with urgency indicators"),
            ("Risk Flags", "Automatic deal health warnings and risk indicators"),
            ("Map", "Interactive geographic view with deal locations and insights"),
        ]
        for icon_name, desc in pages:
            st.markdown(f"- **{icon_name}**: {desc}")
    
    st.divider()
    
    # CTA Section
    st.markdown("### Ready?")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Launch Dashboard", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Upload.py")
    
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD — Main interface when chats are present
# ══════════════════════════════════════════════════════════════════════════════
page_header(
    "Sales Intelligence Dashboard",
    "Real-time analytics, pipeline tracking, and deal management"
)

colors = get_colors()

# ── 8-Column KPI Grid ─────────────────────────────────────────────────────────
st.markdown("### Key Performance Indicators")
k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8, gap="small")

with k1:
    kpi_card(
        title="Total Active",
        value=str(kpis['total_chats']),
        metric="Conversations",
        color="primary"
    )
with k2:
    kpi_card(
        title="Engaged",
        value=str(kpis['active_clients']),
        metric="Client Count",
        color="success"
    )
with k3:
    kpi_card(
        title="Hot Leads",
        value=str(kpis['hot_leads']),
        metric="High Priority",
        color="warning"
    )
with k4:
    kpi_card(
        title="Follow-Ups",
        value=str(kpis['followups_due']),
        metric="Action Due",
        color="info"
    )
with k5:
    kpi_card(
        title="Open Tasks",
        value=str(kpis['open_actions']),
        metric="Pending Items",
        color="primary"
    )
with k6:
    kpi_card(
        title="At Risk",
        value=str(kpis['high_risk']),
        metric="Deal Health",
        color="danger"
    )
with k7:
    kpi_card(
        title="Pipeline",
        value=f"{kpis['pipeline_m3']:,.0f}",
        metric="Unit Volume",
        color="primary"
    )
with k8:
    kpi_card(
        title="Overdue",
        value=str(kpis['overdue_payments']),
        metric="Payments",
        color="warning"
    )

st.divider()

# ── Quick Action Strip ────────────────────────────────────────────────────────
st.markdown("### Quick Actions")
qa1, qa2, qa3, qa4 = st.columns(4, gap="small")

with qa1:
    if st.button("[IMPORT] Import New Chat", use_container_width=True):
        st.switch_page("pages/1_Upload.py")
with qa2:
    if st.button("[DONE] View Follow-Ups", use_container_width=True):
        st.switch_page("pages/4_Followups.py")
with qa3:
    if st.button("[ALERT] Risk Flags", use_container_width=True):
        st.switch_page("pages/5_Risk_Flags.py")
with qa4:
    if st.button("[LOCATION] Project Map", use_container_width=True):
        st.switch_page("pages/6_Map.py")

st.divider()

# ── Pipeline Summary ──────────────────────────────────────────────────────────
if pipeline.get('quoted_m3') or pipeline.get('ordered_m3') or pipeline.get('delivered_m3'):
    st.markdown("### Sales Pipeline Overview")
    
    pc1, pc2, pc3 = st.columns(3, gap="medium")
    
    with pc1:
        kpi_card(
            title="Quoted",
            value=f"{pipeline['quoted_m3']:,.0f}",
            metric="In Pipeline",
            color="info"
        )
    with pc2:
        kpi_card(
            title="Ordered",
            value=f"{pipeline['ordered_m3']:,.0f}",
            metric="Confirmed",
            color="success"
        )
    with pc3:
        kpi_card(
            title="Delivered",
            value=f"{pipeline['delivered_m3']:,.0f}",
            metric="Completed",
            color="primary"
        )
    
    # Pipeline by mix and area
    import pandas as pd
    pcol1, pcol2 = st.columns(2, gap="large")
    
    if pipeline.get('by_mix'):
        with pcol1:
            st.markdown("**By Product Mix**")
            df_mix = pd.DataFrame(pipeline['by_mix']).rename(columns={
                'mix_grade': 'Grade',
                'total_m3': 'Volume (m³)',
                'order_count': 'Orders'
            })
            st.dataframe(df_mix, hide_index=True, use_container_width=True)
    
    if pipeline.get('by_area'):
        with pcol2:
            st.markdown("**By Region**")
            df_area = pd.DataFrame(pipeline['by_area']).rename(columns={
                'primary_area': 'Area',
                'm3': 'Volume (m³)'
            })
            st.dataframe(df_area, hide_index=True, use_container_width=True)
    
    st.divider()

# ── All Chats Table with Filters ──────────────────────────────────────────────
st.markdown(f"### Chat Conversations ({len(chats)} Total)")

import pandas as pd

# Filter controls
fcol1, fcol2, fcol3 = st.columns([2, 2, 2], gap="medium")

with fcol1:
    urgency_filter = st.multiselect(
        "Filter by Urgency",
        ['Critical', 'High', 'Medium', 'Low'],
        default=['Critical', 'High', 'Medium', 'Low'],
        key="dashboard_urgency"
    )

with fcol2:
    stage_filter = st.multiselect(
        "Filter by Stage",
        ['Hot', 'Negotiating', 'Warm', 'Cold', 'Confirmed', 'Delivered', 'Dispute'],
        default=[],
        key="dashboard_stage"
    )

with fcol3:
    followup_only = st.checkbox("Show follow-ups needed only", value=False)

# Apply filters
filtered_chats = chats

if urgency_filter:
    filtered_chats = [c for c in filtered_chats
                      if (c.get('urgency_level') or 'Low') in urgency_filter]

if stage_filter:
    filtered_chats = [c for c in filtered_chats
                      if (c.get('relationship_stage') or '') in stage_filter]

if followup_only:
    filtered_chats = [c for c in filtered_chats if c.get('followup_needed')]

# Build table rows
rows = []
for c in filtered_chats:
    rows.append({
        'Chat Name': c.get('chat_name') or c.get('filename', 'Unknown'),
        'Contact': c.get('contact_name') or '—',
        'Area': c.get('primary_area') or '—',
        'Category': c.get('category') or '—',
        'Stage': c.get('relationship_stage') or '—',
        'Urgency': c.get('urgency_level') or '—',
        'Messages': c.get('message_count', 0),
        'Est. Volume': f"{c.get('total_m3_estimate', 0):,.0f}" if c.get('total_m3_estimate') else '—',
        'Last Activity': c.get('last_activity_date') or '—',
        'Silent (Days)': c.get('days_silent') if c.get('days_silent') is not None else '—',
        'Follow-Up': '[OK]' if c.get('followup_needed') else '',
    })

if rows:
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        height=400
    )
    st.caption(f"Showing {len(rows)} of {len(chats)} conversations")
else:
    alert_box("No conversations match the current filters.", alert_type="info")

# Footer
st.divider()
st.markdown(
    f"<div style='text-align: center; color: {colors['text_secondary']}; font-size: 12px;'>"
    f"<p>Sales Intelligence Platform | Last updated: Just now</p>"
    f"<p style='opacity: 0.7;'>Professional analytics for sales teams</p>"
    f"</div>",
    unsafe_allow_html=True
)


