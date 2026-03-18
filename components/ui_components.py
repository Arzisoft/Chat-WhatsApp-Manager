"""
Reusable Figma-inspired UI components for Chat Intelligence platform.
Bubble cards, KPI cards, action cards, color-coded alerts.
"""

import streamlit as st
from components.colors import LIGHT, DARK, PRODUCT_NAME
from components.theme import get_colors, get_theme_mode

def kpi_card(title, value, metric, icon=None, trend=None, color='primary'):
    """
    KPI card with icon, value, and optional trend indicator.
    
    Args:
        title: Card title
        value: Main KPI value
        metric: Metric label (e.g., "Active Chats")
        icon: Optional emoji or icon
        trend: Optional (direction, percentage) tuple
        color: Color variant (primary, success, warning, danger, info)
    """
    colors = get_colors()
    color_map = {
        'primary': colors['primary'],
        'success': colors['success'],
        'warning': colors['warning'],
        'danger': colors['danger'],
        'info': colors['info'],
    }
    accent_color = color_map.get(color, color_map['primary'])
    
    html = f"""
    <div style="
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border']};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        transition: all 0.2s ease;
        cursor: pointer;
    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 12px 32px rgba(0,0,0,0.18)';"
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 16px rgba(0,0,0,0.12)';">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
            <div style="flex: 1;">
                <div style="color: {colors['text_secondary']}; font-size: 13px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px;">
                    {metric}
                </div>
                <div style="color: {colors['text_primary']}; font-size: 13px; font-weight: 500;">
                    {title}
                </div>
            </div>
            {'<div style="font-size: 28px;">' + icon + '</div>' if icon else ''}
        </div>
        <div style="display: flex; align-items: baseline; gap: 12px;">
            <div style="color: {accent_color}; font-size: 32px; font-weight: 700;">
                {value}
            </div>
            {'<div style="color: ' + colors['success'] + '; font-size: 13px; font-weight: 600;">↑ ' + str(trend[1]) + '%</div>' if trend and trend[0] == 'up' else ''}
            {'<div style="color: ' + colors['danger'] + '; font-size: 13px; font-weight: 600;">↓ ' + str(trend[1]) + '%</div>' if trend and trend[0] == 'down' else ''}
        </div>
        <div style="border-top: 1px solid {colors['border']}; margin-top: 12px; padding-top: 12px;">
            <div style="color: {colors['text_light']}; font-size: 12px; text-align: right;">
                Last update: today
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def action_card(title, description, urgency='low', icon=None, callback=None):
    """
    Action card with color-coded urgency.
    
    Args:
        title: Card title
        description: Description text
        urgency: 'critical' (red), 'high' (orange), 'medium' (yellow), 'low' (blue)
        icon: Optional emoji
        callback: Optional callback function
    """
    colors = get_colors()
    urgency_colors = {
        'critical': colors['danger'],
        'high': colors['warning'],
        'medium': '#FFC107',
        'low': colors['info'],
    }
    accent_color = urgency_colors.get(urgency, colors['info'])
    
    html = f"""
    <div style="
        background-color: {colors['bg_card']};
        border-left: 4px solid {accent_color};
        border: 1px solid {colors['border']};
        border-left: 4px solid {accent_color};
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
        cursor: pointer;
    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 12px 32px rgba(0,0,0,0.18)';"
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0,0,0,0.08)';">
        <div style="display: flex; gap: 12px;">
            {'<div style="font-size: 24px; flex-shrink: 0;">' + icon + '</div>' if icon else ''}
            <div style="flex: 1;">
                <div style="color: {colors['text_primary']}; font-weight: 600; font-size: 14px; margin-bottom: 4px;">
                    {title}
                </div>
                <div style="color: {colors['text_secondary']}; font-size: 13px; line-height: 1.5;">
                    {description}
                </div>
                <div style="margin-top: 8px;">
                    <span style="display: inline-block; background-color: {accent_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase;">
                        {urgency.capitalize()}
                    </span>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def feature_card(title, description, icon=None):
    """
    Feature showcase card for landing page.
    
    Args:
        title: Feature title
        description: Feature description
        icon: Optional emoji/icon
    """
    colors = get_colors()
    
    html = f"""
    <div style="
        background-color: {colors['bg_card']};
        border: 1px solid {colors['border']};
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        transition: all 0.2s ease;
        height: 100%;
    " onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 12px 32px rgba(0,0,0,0.18)';"
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 16px rgba(0,0,0,0.12)';">
        {'<div style="font-size: 40px; margin-bottom: 16px;">' + icon + '</div>' if icon else ''}
        <div style="color: {colors['text_primary']}; font-weight: 700; font-size: 16px; margin-bottom: 8px;">
            {title}
        </div>
        <div style="color: {colors['text_secondary']}; font-size: 14px; line-height: 1.6;">
            {description}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def stat_bar(label, current, total, percentage, color='primary'):
    """
    Progress-style stat bar.
    
    Args:
        label: Stat label
        current: Current value
        total: Total value
        percentage: Percentage (0-100)
        color: Color variant
    """
    colors = get_colors()
    color_map = {
        'primary': colors['primary'],
        'success': colors['success'],
        'warning': colors['warning'],
        'danger': colors['danger'],
    }
    accent_color = color_map.get(color, color_map['primary'])
    
    html = f"""
    <div style="margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span style="color: {colors['text_primary']}; font-size: 13px; font-weight: 600;">
                {label}
            </span>
            <span style="color: {colors['text_secondary']}; font-size: 13px; font-weight: 600;">
                {current}/{total} ({percentage}%)
            </span>
        </div>
        <div style="
            background-color: {colors['border']};
            border-radius: 8px;
            height: 8px;
            overflow: hidden;
        ">
            <div style="
                background-color: {accent_color};
                height: 100%;
                width: {percentage}%;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def alert_box(message, alert_type='info', icon=None):
    """
    Alert/notification box.
    
    Args:
        message: Alert message
        alert_type: 'info', 'success', 'warning', 'danger'
        icon: Optional emoji
    """
    colors = get_colors()
    alert_colors = {
        'info': colors['info'],
        'success': colors['success'],
        'warning': colors['warning'],
        'danger': colors['danger'],
    }
    bg_color = alert_colors.get(alert_type, alert_colors['info'])
    
    html = f"""
    <div style="
        background-color: {colors['bg_card']};
        border-left: 4px solid {bg_color};
        border: 1px solid {colors['border']};
        border-left: 4px solid {bg_color};
        border-radius: 8px;
        padding: 12px 16px;
        display: flex;
        gap: 12px;
        align-items: flex-start;
    ">
        {'<div style="font-size: 20px;">' + icon + '</div>' if icon else ''}
        <div style="color: {colors['text_primary']}; font-size: 14px; line-height: 1.5;">
            {message}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def hero_banner(title, subtitle, cta_text=None, cta_callback=None, gradient=True):
    """
    Hero banner for page headers.
    
    Args:
        title: Main title
        subtitle: Subtitle text
        cta_text: Optional CTA button text
        cta_callback: Optional callback
        gradient: Use gradient background
    """
    colors = get_colors()
    
    gradient_bg = f"linear-gradient(135deg, {colors['primary']} 0%, {colors['accent']} 100%)" if gradient else colors['primary']
    
    html = f"""
    <div style="
        background: {gradient_bg};
        border-radius: 12px;
        padding: 40px;
        color: white;
        margin-bottom: 32px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    ">
        <div style="font-size: 32px; font-weight: 800; margin-bottom: 12px;">
            {title}
        </div>
        <div style="font-size: 16px; opacity: 0.9; margin-bottom: 20px; max-width: 600px;">
            {subtitle}
        </div>
        {'<button style="background-color: white; color: ' + colors['primary'] + '; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600; cursor: pointer; transition: all 0.2s ease;">' + cta_text + '</button>' if cta_text else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
