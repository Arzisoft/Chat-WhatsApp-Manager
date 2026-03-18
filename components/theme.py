"""
Theme management for Chat Intelligence platform.
Handles light/dark/system mode switching with CSS variables.
"""

import streamlit as st
from components.colors import LIGHT, DARK, RADIUS_LARGE, SHADOW_MEDIUM, TRANSITION_NORMAL

def get_theme_mode():
    """Get current theme mode (light/dark/system)."""
    if 'theme_mode' not in st.session_state:
        st.session_state.theme_mode = 'system'
    return st.session_state.theme_mode

def get_colors(mode=None):
    """Get color palette for given mode (light/dark/system)."""
    if mode is None:
        mode = get_theme_mode()
    
    if mode == 'light':
        return LIGHT
    elif mode == 'dark':
        return DARK
    else:  # system (default to light for now)
        return LIGHT

def set_theme_mode(mode):
    """Set theme mode and save to session."""
    if mode in ['light', 'dark', 'system']:
        st.session_state.theme_mode = mode

def theme_toggle_widget():
    """Sidebar widget for theme selection."""
    with st.sidebar:
        st.divider()
        current_mode = get_theme_mode()
        new_mode = st.radio(
            "Theme",
            ['Light', 'Dark', 'System'],
            index=['light', 'dark', 'system'].index(current_mode),
            horizontal=False,
            key='theme_selector'
        )
        set_theme_mode(['light', 'dark', 'system'][['Light', 'Dark', 'System'].index(new_mode)])

def inject_theme_css():
    """Inject CSS for current theme with smooth transitions."""
    colors = get_colors()
    mode = get_theme_mode()
    
    css = f"""
    <style>
    :root {{
        --primary-color: {colors['primary']};
        --secondary-color: {colors['secondary']};
        --accent-color: {colors['accent']};
        --accent-alt: {colors['accent_alt']};
        --text-primary: {colors['text_primary']};
        --text-secondary: {colors['text_secondary']};
        --text-light: {colors['text_light']};
        --border-color: {colors['border']};
        --bg-card: {colors['bg_card']};
        --bg-hover: {colors['bg_hover']};
        --danger: {colors['danger']};
        --warning: {colors['warning']};
        --success: {colors['success']};
        --info: {colors['info']};
        --radius: {RADIUS_LARGE};
        --shadow-md: {SHADOW_MEDIUM};
        --transition: {TRANSITION_NORMAL};
    }}
    
    * {{
        transition: background-color {TRANSITION_NORMAL}, color {TRANSITION_NORMAL}, border-color {TRANSITION_NORMAL};
    }}
    
    body {{
        background-color: var(--bg-card);
        color: var(--text-primary);
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def create_card_style(color='card', hover=True, shadow='medium'):
    """Generate CSS for a bubble card component."""
    colors = get_colors()
    
    shadow_map = {
        'small': '0 2px 8px rgba(0,0,0,0.08)',
        'medium': '0 4px 16px rgba(0,0,0,0.12)',
        'large': '0 8px 24px rgba(0,0,0,0.15)',
    }
    
    bg_color = colors.get(color, colors['bg_card'])
    
    style = f"""
        background-color: {bg_color};
        border: 1px solid {colors['border']};
        border-radius: {RADIUS_LARGE};
        padding: 20px;
        box-shadow: {shadow_map.get(shadow, shadow_map['medium'])};
        transition: all {TRANSITION_NORMAL};
    """
    
    if hover:
        style += f"""
        &:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(0,0,0,0.18);
        }}
        """
    
    return style

def create_button_style(variant='primary'):
    """Generate CSS for button variants."""
    colors = get_colors()
    
    variants = {
        'primary': f"""
            background-color: {colors['primary']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            cursor: pointer;
            transition: all {TRANSITION_NORMAL};
        """,
        'secondary': f"""
            background-color: {colors['bg_hover']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            cursor: pointer;
            transition: all {TRANSITION_NORMAL};
        """,
        'ghost': f"""
            background-color: transparent;
            color: {colors['primary']};
            border: 1px solid {colors['primary']};
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            cursor: pointer;
            transition: all {TRANSITION_NORMAL};
        """,
        'danger': f"""
            background-color: {colors['danger']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            cursor: pointer;
            transition: all {TRANSITION_NORMAL};
        """,
    }
    
    return variants.get(variant, variants['primary'])

def apply_global_theme():
    """Apply global theme CSS to entire app."""
    inject_theme_css()
