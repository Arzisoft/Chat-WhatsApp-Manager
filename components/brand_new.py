"""
Sales Intelligence platform - generic, professional brand system.
Replaces ChatChaos-specific branding.
No longer ChatChaos-specific - works for B2B SaaS clients.
"""

import streamlit as st
from components.theme import apply_theme_css, get_theme_colors, render_theme_toggle


# ── Generic product names (choose one) ────────────────────────────────────────
PRODUCT_NAME = "Sales Intelligence"
PRODUCT_TAGLINE = "Transform conversations into actionable insights"
PRODUCT_DESCRIPTION = "Analyze, track, and act on business conversations with AI-powered insights."


def apply_brand_new() -> None:
    """
    Apply professional brand theming (replaces ChatChaos-specific styling).
    Call once per page after st.set_page_config().
    """
    # Initialize theme
    colors = get_theme_colors()
    apply_theme_css(colors)
    
    # Render theme toggle in sidebar
    render_theme_toggle()


def page_header_new(
    title: str,
    subtitle: str = "",
    icon: str = None,
    show_breadcrumb: bool = True
) -> None:
    """
    Render a modern page header banner.
    
    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Optional emoji icon
        show_breadcrumb: Whether to show breadcrumb navigation
    """
    colors = get_theme_colors()
    icon_html = f"<span style='margin-right:12px;font-size:28px;'>{icon}</span>" if icon else ""
    
    header_html = f"""
    <div style="
        background: linear-gradient(135deg, {colors['accent_primary']} 0%, {colors['accent_tertiary']} 100%);
        border-bottom: 3px solid {colors['accent_secondary']};
        padding: 24px 32px;
        border-radius: 0 0 12px 12px;
        margin: -24px -24px 24px -24px;
    ">
        <div style="
            display: flex;
            align-items: center;
        ">
            {icon_html}
            <div>
                <div style="
                    color: {colors['text_inverse']};
                    font-size: 28px;
                    font-weight: 800;
                    line-height: 1.2;
                    letter-spacing: -0.5px;
                ">
                    {title}
                </div>
                {'<div style="color: ' + colors['accent_secondary'] + '; font-size: 14px; margin-top: 4px;">' + subtitle + '</div>' if subtitle else ''}
            </div>
        </div>
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)


def render_hero_section() -> None:
    """
    Render a professional hero section for landing pages.
    """
    colors = get_theme_colors()
    
    hero_html = f"""
    <div style="
        background: linear-gradient(135deg, {colors['accent_primary']} 0%, {colors['accent_tertiary']} 70%, rgba(16, 185, 129, 0.9) 100%);
        border-radius: 0 0 20px 20px;
        padding: 64px 40px 56px;
        margin: -24px -24px 32px -24px;
        text-align: center;
        color: white;
    ">
        <div style="
            font-size: 44px;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 16px;
            letter-spacing: -1px;
        ">
            {PRODUCT_NAME}
        </div>
        <div style="
            font-size: 18px;
            color: {colors['accent_secondary']};
            font-weight: 600;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 20px;
        ">
            {PRODUCT_TAGLINE}
        </div>
        <div style="
            font-size: 16px;
            color: rgba(255, 255, 255, 0.85);
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.6;
        ">
            {PRODUCT_DESCRIPTION}
        </div>
    </div>
    """
    
    st.markdown(hero_html, unsafe_allow_html=True)


def render_feature_section(
    features: list  # List of dicts: [{'icon': '...', 'title': '...', 'desc': '...'}]
) -> None:
    """
    Render a 4-column feature showcase section.
    
    Args:
        features: List of feature dicts with icon, title, desc
    """
    colors = get_theme_colors()
    
    feature_cards = ""
    for feature in features:
        feature_cards += f"""
        <div style="
            background-color: {colors['card_bg']};
            border: 1px solid {colors['card_border']};
            border-radius: 12px;
            padding: 28px 24px;
            text-align: center;
            box-shadow: 0 2px 8px {colors['card_shadow']};
            transition: all 0.3s ease;
        " onmouseover="this.style.transform='translateY(-6px)'; this.style.boxShadow='0 8px 20px {colors['card_shadow']}';"
          onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px {colors['card_shadow']}';">
            <div style="font-size: 48px; margin-bottom: 16px;">
                {feature['icon']}
            </div>
            <div style="
                font-size: 18px;
                font-weight: 700;
                color: {colors['text_primary']};
                margin-bottom: 10px;
            ">
                {feature['title']}
            </div>
            <div style="
                font-size: 14px;
                color: {colors['text_secondary']};
                line-height: 1.6;
            ">
                {feature['desc']}
            </div>
        </div>
        """
    
    section_html = f"""
    <div style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 20px;
        margin: 32px 0;
    ">
        {feature_cards}
    </div>
    """
    
    st.markdown(section_html, unsafe_allow_html=True)


def render_cta_section(
    heading: str,
    description: str,
    button_text: str,
    button_onclick: str = None
) -> None:
    """
    Render a call-to-action section.
    """
    colors = get_theme_colors()
    
    cta_html = f"""
    <div style="
        background: linear-gradient(135deg, {colors['accent_primary']} 0%, {colors['accent_tertiary']} 100%);
        border-radius: 16px;
        padding: 48px 40px;
        text-align: center;
        margin: 40px 0;
        color: white;
    ">
        <div style="
            font-size: 32px;
            font-weight: 800;
            margin-bottom: 16px;
        ">
            {heading}
        </div>
        <div style="
            font-size: 16px;
            margin-bottom: 28px;
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.6;
        ">
            {description}
        </div>
        <button style="
            background-color: {colors['accent_secondary']};
            color: #0F172A;
            border: none;
            border-radius: 8px;
            padding: 14px 36px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        " onmouseover="this.style.opacity='0.9'; this.style.transform='scale(1.05)';"
          onmouseout="this.style.opacity='1'; this.style.transform='scale(1)';">
            {button_text}
        </button>
    </div>
    """
    
    st.markdown(cta_html, unsafe_allow_html=True)


def render_step_guide(
    steps: list  # List of dicts: [{'number': 1, 'title': '...', 'desc': '...'}]
) -> None:
    """
    Render a numbered step-by-step guide section.
    """
    colors = get_theme_colors()
    
    steps_html = ""
    for step in steps:
        steps_html += f"""
        <div style="
            display: flex;
            margin-bottom: 24px;
            align-items: flex-start;
        ">
            <div style="
                background-color: {colors['accent_primary']};
                color: white;
                width: 44px;
                height: 44px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                font-size: 18px;
                margin-right: 20px;
                flex-shrink: 0;
            ">
                {step['number']}
            </div>
            <div>
                <div style="
                    font-size: 16px;
                    font-weight: 700;
                    color: {colors['text_primary']};
                    margin-bottom: 6px;
                ">
                    {step['title']}
                </div>
                <div style="
                    font-size: 14px;
                    color: {colors['text_secondary']};
                    line-height: 1.5;
                ">
                    {step['desc']}
                </div>
            </div>
        </div>
        """
    
    section_html = f"""
    <div style="max-width: 600px; margin: 32px 0;">
        {steps_html}
    </div>
    """
    
    st.markdown(section_html, unsafe_allow_html=True)

