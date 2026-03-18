"""
Risk Flags — Modern deal risk management interface.
Identifies stalled deals, silent leads, and payment issues.
"""

import streamlit as st
from core.database import (
    init_db,
    get_silent_high_value_leads,
    get_stalled_negotiations,
    get_lifecycle_stuck,
    get_overdue_payments,
)
from components.brand import apply_brand, page_header
from components.theme import get_colors
from components.ui_components import alert_box, kpi_card, action_card

init_db()

st.set_page_config(page_title="Risk Flags | Sales Intelligence", page_icon="[ALERT]", layout="wide")
apply_brand()

page_header("Deal Risk Management", "Proactive monitoring of deal health and warning signs")

colors = get_colors()

# ── Load risk data ────────────────────────────────────────────────────────────
silent_leads = get_silent_high_value_leads()
stalled      = get_stalled_negotiations()
stuck        = get_lifecycle_stuck()
overdue      = get_overdue_payments()

total_risks = len(silent_leads) + len(stalled) + len(stuck) + len(overdue)

# ── Risk Summary Cards ────────────────────────────────────────────────────────
st.markdown("### Risk Overview")

k1, k2, k3, k4 = st.columns(4, gap="small")

with k1:
    kpi_card(
        title="Silent Leads",
        value=str(len(silent_leads)),
        metric="No Contact >14d",
        color="danger"
    )

with k2:
    kpi_card(
        title="Stalled Deals",
        value=str(len(stalled)),
        metric="Negotiation Stuck",
        color="warning"
    )

with k3:
    kpi_card(
        title="Lifecycle Issues",
        value=str(len(stuck)),
        metric="Stage Unclear",
        color="warning"
    )

with k4:
    kpi_card(
        title="Overdue Payments",
        value=str(len(overdue)),
        metric="Payment Due",
        color="danger"
    )

st.divider()

if total_risks == 0:
    alert_box(
        "No risk flags detected. All deals appear to be progressing normally.",
        alert_type="success"
    )
    st.stop()

# ── Tabs for each risk category ───────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    f"🤐 Silent Leads ({len(silent_leads)})",
    f"⏸️ Stalled ({len(stalled)})",
    f"[REFRESH] Stuck ({len(stuck)})",
    f"💰 Overdue ({len(overdue)})"
])

# ── TAB 1: Silent High-Value Leads ────────────────────────────────────────────
with tab1:
    if not silent_leads:
        alert_box("No silent high-value leads.", alert_type="success")
    else:
        st.markdown(
            "#### Potential leads with financial data that have gone silent for >14 days"
        )
        
        for lead in silent_leads:
            days = lead.get('days_silent') or 0
            value = lead.get('total_value', 0)
            m3_val = lead.get('total_m3', 0)
            urgency = lead.get('urgency_level') or 'low'
            
            action_card(
                title=f"{lead['chat_name']} • {lead.get('contact_name', 'Unknown')}",
                description=f"Silent for {days} days | Value: ${value:,.0f} | Volume: {m3_val}m³",
                urgency=urgency,
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("[PHONE] Call", key=f"silent_call_{lead['chat_id']}", use_container_width=True):
                    st.info("Reminder: Follow up with this lead by phone")
            with col2:
                if st.button("[CHAT] Message", key=f"silent_msg_{lead['chat_id']}", use_container_width=True):
                    st.info("Send a follow-up message to re-engage")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ── TAB 2: Stalled Negotiations ───────────────────────────────────────────────
with tab2:
    if not stalled:
        alert_box("No stalled negotiations.", alert_type="success")
    else:
        st.markdown("#### Deals stuck in negotiation phase for extended periods")
        
        for deal in stalled:
            days = deal.get('days_in_stage') or 0
            stage = deal.get('relationship_stage', 'Negotiating')
            last_msg = deal.get('last_activity_date', 'Unknown')
            
            action_card(
                title=f"{deal['chat_name']} • {deal.get('contact_name', 'Unknown')}",
                description=f"Stuck in '{stage}' for {days} days | Last message: {last_msg}",
                urgency='high',
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("↗️ Move Forward", key=f"stalled_move_{deal['chat_id']}", use_container_width=True):
                    st.info("Consider advancing this deal to next stage")
            with col2:
                if st.button("💭 Discuss", key=f"stalled_discuss_{deal['chat_id']}", use_container_width=True):
                    st.info("Schedule discussion about next steps")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ── TAB 3: Lifecycle Stuck ────────────────────────────────────────────────────
with tab3:
    if not stuck:
        alert_box("No lifecycle issues detected.", alert_type="success")
    else:
        st.markdown("#### Deals with unclear stage or missing lifecycle information")
        
        for deal in stuck:
            reason = deal.get('issue', 'Incomplete deal information')
            
            action_card(
                title=f"{deal['chat_name']} • {deal.get('contact_name', 'Unknown')}",
                description=f"{reason}",
                urgency='medium',
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("📝 Update", key=f"stuck_update_{deal['chat_id']}", use_container_width=True):
                    st.info("Update deal information and status")
            with col2:
                if st.button("📖 Review", key=f"stuck_review_{deal['chat_id']}", use_container_width=True):
                    st.switch_page("pages/2_Chat_Detail.py")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ── TAB 4: Overdue Payments ───────────────────────────────────────────────────
with tab4:
    if not overdue:
        alert_box("All payments are current.", alert_type="success")
    else:
        st.markdown("#### Invoices and payments past due date")
        
        for payment in overdue:
            days_overdue = payment.get('days_overdue', 0)
            amount = payment.get('amount', 0)
            invoice_date = payment.get('invoice_date', 'Unknown')
            due_date = payment.get('due_date', 'Unknown')
            
            action_card(
                title=f"{payment['chat_name']} • {payment.get('contact_name', 'Unknown')}",
                description=f"${amount:,.0f} overdue by {days_overdue} days | Invoice: {invoice_date} | Due: {due_date}",
                urgency='critical',
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("💳 Follow Up", key=f"pay_follow_{payment['chat_id']}", use_container_width=True):
                    st.info("Send payment reminder")
            with col2:
                if st.button("[PHONE] Call", key=f"pay_call_{payment['chat_id']}", use_container_width=True):
                    st.info("Follow up by phone")
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ── Summary Statistics ────────────────────────────────────────────────────────
st.divider()
st.markdown("### Action Summary")

summary_cols = st.columns(4, gap="medium")

with summary_cols[0]:
    st.metric(
        "Total At-Risk Deals",
        total_risks,
        delta=f"{total_risks} require attention"
    )

with summary_cols[1]:
    critical_count = len([x for x in silent_leads + overdue if (x.get('urgency_level') or 'low').lower() == 'critical'])
    st.metric("🔴 Critical", critical_count)

with summary_cols[2]:
    total_at_risk_value = sum(
        [x.get('total_value', 0) for x in silent_leads] +
        [x.get('amount', 0) for x in overdue]
    )
    st.metric("💵 At-Risk Value", f"${total_at_risk_value:,.0f}")

with summary_cols[3]:
    avg_days_silent = sum([x.get('days_silent', 0) for x in silent_leads]) / max(len(silent_leads), 1)
    st.metric("[TIME] Avg Days Silent", f"{avg_days_silent:.0f}")

st.markdown(
    f"<div style='text-align: center; margin-top: 24px; padding: 16px; "
    f"background-color: {colors['bg_hover']}; border-radius: 8px;'>"
    f"<p style='color: {colors['text_secondary']}; margin: 0;'>"
    f"Review and action these flags weekly to maintain pipeline health.</p>"
    f"</div>",
    unsafe_allow_html=True
)


