"""
Modern UI Component Library - ChatChaos Dashboard
Glassmorphism, floating animations, soft UI evolution pattern.
Based on UI/UX Pro Max design system.
"""

import streamlit as st
from typing import Optional, Tuple

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM COLORS & TOKENS
# ══════════════════════════════════════════════════════════════════════════════

COLORS = {
    'primary': '#2563EB',
    'secondary': '#3B82F6',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'info': '#06B6D4',
    'bg_white': '#FFFFFF',
    'bg_light': '#F8FAFC',
    'bg_lighter': '#F1F5F9',
    'bg_lightest': '#F0F9FF',
    'text_primary': '#1E293B',
    'text_secondary': '#64748B',
    'text_muted': '#94A3B8',
    'border': '#E2E8F0',
}

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM CSS (Inject once at app startup)
# ══════════════════════════════════════════════════════════════════════════════

DESIGN_SYSTEM_CSS = """
<style>
:root {
    --primary: #2563EB;
    --secondary: #3B82F6;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --info: #06B6D4;
    --bg-white: #FFFFFF;
    --bg-light: #F8FAFC;
    --bg-lighter: #F1F5F9;
    --bg-lightest: #F0F9FF;
    --text-primary: #1E293B;
    --text-secondary: #64748B;
    --text-muted: #94A3B8;
    --border: #E2E8F0;
    --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

html {
    background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
    scroll-behavior: smooth;
}

body {
    background: transparent;
    font-family: 'Fira Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Animations */
@keyframes floating {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-12px); }
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

@keyframes pulse-subtle {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* KPI Bubble Card */
.kpi-bubble {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.9) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 14px;
    padding: 24px;
    box-shadow: var(--shadow-md), inset 0 1px 0 rgba(255, 255, 255, 0.5);
    animation: floating 3.5s ease-in-out infinite;
    transition: all var(--transition-normal);
    cursor: pointer;
    position: relative;
    overflow: hidden;
    min-height: 200px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.kpi-bubble:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: var(--shadow-xl), inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 0 40px rgba(37, 99, 235, 0.15);
    border-color: rgba(37, 99, 235, 0.4);
}

.kpi-bubble::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.15) 50%, transparent 70%);
    transform: translateX(-100%);
}

.kpi-bubble:hover::before {
    animation: shimmer 0.6s ease-in-out;
}

.kpi-label {
    color: var(--text-secondary);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.kpi-icon {
    font-size: 28px;
    opacity: 0.85;
    transition: transform var(--transition-normal);
}

.kpi-bubble:hover .kpi-icon {
    transform: scale(1.15);
}

.kpi-value {
    font-family: 'Fira Code', monospace;
    font-size: 40px;
    font-weight: 700;
    line-height: 1;
    margin: 8px 0 16px 0;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.kpi-value.success {
    background: linear-gradient(135deg, var(--success), #34D399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.kpi-value.warning {
    background: linear-gradient(135deg, var(--warning), #FBBF24);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.kpi-value.danger {
    background: linear-gradient(135deg, var(--danger), #F87171);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.kpi-value.info {
    background: linear-gradient(135deg, var(--info), #22D3EE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.kpi-metric {
    color: var(--text-muted);
    font-size: 12px;
    margin-top: auto;
    padding-top: 16px;
    border-top: 1px solid rgba(226, 232, 240, 0.6);
}

/* Hero Banner */
.hero-banner {
    background: linear-gradient(135deg, #2563EB 0%, #1E40AF 50%, #06B6D4 100%);
    border-radius: 18px;
    padding: 48px;
    color: white;
    margin-bottom: 40px;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-lg), 0 0 50px rgba(37, 99, 235, 0.2);
}

.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 500px;
    height: 500px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    animation: pulse-subtle 8s ease-in-out infinite;
}

.hero-banner::after {
    content: '';
    position: absolute;
    bottom: -30%;
    left: -5%;
    width: 300px;
    height: 300px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 50%;
    animation: pulse-subtle 6s ease-in-out infinite reverse;
}

.hero-title {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 12px;
    position: relative;
    z-index: 1;
    letter-spacing: -0.5px;
}

.hero-subtitle {
    font-size: 16px;
    opacity: 0.95;
    position: relative;
    z-index: 1;
    line-height: 1.5;
}

/* Section Header */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 40px 0 24px 0;
    padding-bottom: 16px;
    border-bottom: 2px solid var(--border);
}

.section-header::before {
    content: '';
    width: 4px;
    height: 32px;
    background: linear-gradient(180deg, var(--primary), var(--secondary));
    border-radius: 2px;
    flex-shrink: 0;
}

.section-header h2 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.5px;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.badge-success { background: rgba(16, 185, 129, 0.1); color: var(--success); }
.badge-warning { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
.badge-danger { background: rgba(239, 68, 68, 0.1); color: var(--danger); }
.badge-info { background: rgba(6, 182, 212, 0.1); color: var(--info); }

/* Data Table */
.dataframe {
    background-color: var(--bg-white);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
}

.dataframe thead {
    background: linear-gradient(180deg, var(--bg-lighter), var(--bg-light));
    border-bottom: 2px solid var(--border);
}

.dataframe th {
    padding: 14px;
    font-weight: 700;
    color: var(--text-primary);
    font-family: 'Fira Code', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    text-align: left;
}

.dataframe td {
    padding: 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text-secondary);
    font-size: 13px;
}

.dataframe tr:hover {
    background-color: var(--bg-lightest);
    transition: background-color var(--transition-fast);
}

.dataframe tr:last-child td {
    border-bottom: none;
}
</style>
"""

def inject_design_system():
    """Inject design system CSS (call once at app startup)"""
    st.markdown(DESIGN_SYSTEM_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MODERN UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def kpi_bubble(
    label: str,
    value: str,
    metric: str,
    icon: str = "📊",
    color: str = "primary",
    trend: Optional[Tuple[str, int]] = None,
):
    """
    Render a modern floating KPI bubble card.
    
    Args:
        label: Card label (e.g., "Total Active")
        value: Main KPI value (e.g., "248")
        metric: Metric description (e.g., "Conversations")
        icon: Emoji icon
        color: "primary", "success", "warning", "danger", "info"
        trend: Optional (direction, percentage) tuple, e.g., ("up", 12)
    """
    
    trend_html = ""
    if trend:
        direction, pct = trend
        if direction == "up":
            trend_html = f'<div style="color: var(--success); font-size: 12px; margin-top: 8px;">↑ {pct}% from last period</div>'
        else:
            trend_html = f'<div style="color: var(--danger); font-size: 12px; margin-top: 8px;">↓ {pct}% from last period</div>'
    
    html = f"""
    <div class="kpi-bubble">
        <div>
            <div class="kpi-label">{icon} {label}</div>
            <div class="kpi-value {color}">{value}</div>
            {trend_html}
        </div>
        <div class="kpi-metric">{metric}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def hero_section(title: str, subtitle: str):
    """
    Render a modern hero banner section.
    
    Args:
        title: Main heading
        subtitle: Subheading
    """
    html = f"""
    <div class="hero-banner">
        <h1 class="hero-title">{title}</h1>
        <p class="hero-subtitle">{subtitle}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def section_header(title: str):
    """Render a section header with modern styling."""
    st.markdown(f"### {title}", unsafe_allow_html=True)