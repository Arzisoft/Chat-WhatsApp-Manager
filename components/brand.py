"""
Professional brand theme for Sales Intelligence platform.
Removed all ChatChaos branding - now generic, client-ready.
Call apply_brand() at the top of every page (after set_page_config).
"""

import streamlit as st
from components.colors import LIGHT, DARK, PRODUCT_NAME, PRODUCT_TAGLINE
from components.theme import inject_theme_css, get_colors

# Professional color aliases (for backward compatibility)
PRIMARY_BLUE = LIGHT['primary']
ACCENT_GOLD = LIGHT['accent_alt']
DARK_BG = DARK['secondary']
LIGHT_BG = LIGHT['bg_card']

CSS = """
<style>
/* ── Global Typography ─────────────────────────────────────────── */
* {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif !important;
}

html, body {
    background-color: var(--secondary-color);
    color: var(--text-primary);
    transition: background-color 0.3s ease, color 0.3s ease;
}

/* ── Sidebar ────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--primary-color) !important;
    border-right: 3px solid var(--accent-alt) !important;
}

[data-testid="stSidebar"] *,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown span,
[data-testid="stSidebar"] small {
    color: #ffffff !important;
}

[data-testid="stSidebarNavItems"] a {
    color: #ffffff !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    transition: all 0.2s ease;
}

[data-testid="stSidebarNavItems"] a:hover {
    background: rgba(255,255,255,0.15) !important;
    color: var(--accent-alt) !important;
}

/* Active nav item */
[data-testid="stSidebarNavItems"] li[aria-current="page"] a {
    background: rgba(255,255,255,0.25) !important;
    border-left: 3px solid var(--accent-alt) !important;
    font-weight: 600;
    color: var(--accent-alt) !important;
}

/* ── Top Header ─────────────────────────────────────────────── */
[data-testid="stHeader"] {
    background: transparent !important;
}

/* ── Main Content ────────────────────────────────────────────── */
[data-testid="stMainBlockContainer"] {
    background: var(--secondary-color);
    padding: 20px 40px;
}

/* ── Metric Cards ────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    transition: all 0.2s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.18);
}

[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px !important;
}

[data-testid="stMetricValue"] {
    color: var(--primary-color) !important;
    font-weight: 700 !important;
    font-size: 28px !important;
}

[data-testid="stMetricDelta"] {
    color: var(--success) !important;
    font-weight: 600 !important;
}

/* ── Buttons ─────────────────────────────────────────────────── */
.stButton > button {
    background-color: var(--primary-color) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.15) !important;
}

/* Secondary button variant */
.stButton > button[data-testid="stButton"] {
    background-color: var(--bg-hover) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
}

/* ── Input Fields ────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    transition: all 0.2s ease;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(0,87,173,0.1) !important;
}

/* ── Tabs ────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 2px solid var(--border-color);
    gap: 20px;
}

[data-testid="stTabs"] [role="tab"] {
    color: var(--text-secondary) !important;
    font-weight: 600;
    padding: 10px 0;
    border-bottom: 2px solid transparent;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--primary-color) !important;
    border-bottom-color: var(--primary-color) !important;
}

/* ── Expander ────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
}

[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
    font-weight: 600;
}

/* ── Divider ─────────────────────────────────────────────────── */
hr {
    border-color: var(--border-color) !important;
}

/* ── Dataframe & Tables ──────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    overflow: hidden;
}

[data-testid="stDataFrame"] thead {
    background-color: var(--bg-hover) !important;
}

[data-testid="stDataFrame"] thead th {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    border-color: var(--border-color) !important;
}

[data-testid="stDataFrame"] tbody tr {
    border-color: var(--border-color) !important;
}

[data-testid="stDataFrame"] tbody tr:hover {
    background-color: var(--bg-hover) !important;
}

/* ── Code Block ──────────────────────────────────────────────── */
code {
    background-color: var(--bg-hover) !important;
    color: var(--text-primary) !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
}

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--secondary-color);
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-light);
}

/* ── Success/Error/Warning Alerts ─────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border-left: 4px solid !important;
}

[data-testid="stAlert"] [role="status"] {
    font-size: 14px;
}

/* Animations */
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

[data-testid="stMetric"] {
    animation: slideIn 0.3s ease;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    html, body {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
}
</style>
"""

def apply_brand():
    """Apply professional brand styling to entire app."""
    st.markdown(CSS, unsafe_allow_html=True)
    inject_theme_css()

def page_header(title, subtitle="", icon=""):
    """
    Render a professional page header with title and subtitle.
    
    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Optional emoji icon
    """
    colors = get_colors()
    
    header_html = f"""
    <div style="
        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['accent']} 100%);
        border-radius: 12px;
        padding: 32px;
        margin: -24px -24px 24px -24px;
        color: white;
    ">
        <div style="display: flex; align-items: center; gap: 16px;">
            {'<div style="font-size: 40px;">' + icon + '</div>' if icon else ''}
            <div>
                <h1 style="margin: 0 0 8px 0; font-size: 32px; font-weight: 800;">
                    {title}
                </h1>
                {'<p style="margin: 0; opacity: 0.9; font-size: 16px;">' + subtitle + '</p>' if subtitle else ''}
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

def logo_html(size='small'):
    """
    Get HTML for brand logo.
    Default: generic placeholder since ChatChaos logo removed.
    
    Args:
        size: 'small', 'medium', or 'large'
    """
    colors = get_colors()
    sizes = {
        'small': ('60px', '16px', '2px'),
        'medium': ('80px', '20px', '4px'),
        'large': ('120px', '28px', '6px'),
    }
    height, font_size, radius = sizes.get(size, sizes['medium'])
    
    return f"""
    <div style="
        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['accent']} 100%);
        width: {height};
        height: {height};
        border-radius: {radius};
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 800;
        font-size: {font_size};
        text-align: center;
        box-shadow: {colors['border']};
    ">
        SI
    </div>
    """

def product_name():
    """Get the product name (no ChatChaos!)."""
    return PRODUCT_NAME

def product_tagline():
    """Get the product tagline."""
    return PRODUCT_TAGLINE

