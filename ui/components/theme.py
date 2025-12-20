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
        rgba(45, 27, 78, 0.8) 0%, 
        rgba(26, 10, 46, 0.85) 100%);
    border-radius: 16px;
    border: 1px solid rgba(255, 215, 0, 0.2);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
"""

def apply_custom_header(title: str, subtitle: str = ""):
    """Renders a premium ornate header."""
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="margin-bottom: 0;">{title}</h1>
            <p style="color: {COLORS['teal_mist']}; font-style: italic; letter-spacing: 2px;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)

def card_container(content: str, title: str = "", card_type: str = "default"):
    """Wraps content in a styled card."""
    border_color = COLORS.get(card_type, COLORS['mystic_gold'])
    st.markdown(f"""
        <div style="{GLASS_STYLE} border-top: 3px solid {border_color}; padding: 20px; margin-bottom: 1rem;">
            {f'<h3 style="color: {COLORS["mystic_gold"]}; margin-top: 0;">{title}</h3>' if title else ''}
            {content}
        </div>
    """, unsafe_allow_html=True)
