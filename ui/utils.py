import streamlit as st
import os

def load_css():
    """Injects custom CSS from assets/style.css"""
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets/style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Plotly Theme Setup - 延迟设置，避免循环导入
    # 不在启动时设置全局模板，而是在实际使用plotly时再设置
    pass

def init_session_state(keys_defaults):
    """
    Helper to initialize session state keys.
    keys_defaults: dict of {key: default_value}
    """
    for k, v in keys_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
