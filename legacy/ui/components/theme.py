"""
ui/components/theme.py
----------------------
Unified design system constants and styling utilities for the Gypsy theme.
"""

import streamlit as st

# Color Palette
COLORS = {
    "midnight": "#0d0015",
    "deep_violet": "#1a0a2e",
    "mystic_gold": "#ffd700",
    "rose_magenta": "#c21e56",
    "teal_mist": "#40e0d0",
    "moon_silver": "#e8e8f0",
    "velvet_purple": "#2d1b4e",
    "candle_glow": "#ff9f43",
    "crystal_blue": "#a855f7",
    "star_white": "#fffef0",
}

# Glassmorphism Box Style
GLASS_STYLE = f"""
    background: linear-gradient(145deg, 
        rgba(45, 27, 78, 0.45) 0%, 
        rgba(26, 10, 46, 0.6) 100%);
    border-radius: 20px;
    border: 1px solid rgba(255, 215, 0, 0.15);
    box-shadow: 
        0 8px 32px 0 rgba(0, 0, 0, 0.5),
        inset 0 1px 1px rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
"""

def apply_custom_header(title: str, subtitle: str = ""):
    """Renders a premium ornate header with shimmer effect."""
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 3rem; padding-top: 1rem;">
            <h1 class="shimmer-text" style="margin-bottom: 0.5rem; font-size: 3.5rem !important;">{title}</h1>
            <p style="color: {COLORS['teal_mist']}; font-style: italic; letter-spacing: 4px; font-size: 1.1rem; opacity: 0.9;">
                ✦ {subtitle} ✦
            </p>
        </div>
    """, unsafe_allow_html=True)

def card_container(content: str, title: str = "", card_type: str = "default"):
    """Wraps content in a styled card."""
    border_color = COLORS.get(card_type, COLORS['mystic_gold'])
    st.markdown(f"""
        <div style="{GLASS_STYLE} border-top: 3px solid {border_color}; padding: 20px; margin-bottom: 1rem;">
            {f'<h3 style="color: {COLORS["mystic_gold"]}; margin-top: 0;">{title}</h3>' if title else ''}
            <div>{content}</div>
        </div>
    """, unsafe_allow_html=True)

def sidebar_header(title: str, icon: str = ""):
    """Renders a premium header for the sidebar."""
    st.markdown(f'<div class="sidebar-title">{icon} {title}</div>', unsafe_allow_html=True)

def render_crystal_notification(message: str, type: str = "info"):
    """
    Renders a theme-compliant notification box.
    Types: info, success, warning, error
    """
    st.markdown(f"""
        <div class="crystal-alert crystal-{type}">
            {message}
        </div>
    """, unsafe_allow_html=True)
