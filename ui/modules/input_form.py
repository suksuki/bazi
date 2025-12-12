import streamlit as st
from datetime import datetime as dt
from ui.utils import init_session_state

def render_input_form():
    """
    Renders the Input Form which pulls default values from session_state.
    Returns:
        submitted (bool): True if 'Calculate' button clicked.
    """
    # Defaults & Session State Sync
    # Ensure keys exist
    init_session_state({
        'input_name': "某人",
        'input_gender': "男",
        'input_date': dt(1990, 1, 1),
        'input_time': 12,
        'input_longitude': 116.46 # Default Beijing
    })

    with st.form("bazi_input_form"):
        st.subheader("👤 命主信息")
        
        col1, col2 = st.columns(2)
        with col1:
             # IMPORTANT: Do not set 'value' if using 'key' in session state
             st.text_input("姓名 (Name)", key="input_name")
        with col2:
             st.radio("性别 (Gender)", ["女", "男"], horizontal=True, key="input_gender")
            
        st.date_input("出生日期 (Date)", min_value=dt(1900, 1, 1), max_value=dt(2100, 12, 31), key="input_date")
        
        c3, c4 = st.columns(2)
        with c3:
            st.number_input("出生时辰 (0-23)", 0, 23, key="input_time")
        with c4:
            st.number_input("出生经度 (Longitude)", -180.0, 180.0, step=0.1, key="input_longitude", help="用于真太阳时校准 (True Solar Time)")
        
        # True Solar Time Toggle
        st.checkbox("启用真太阳时 (True Solar Time)", value=True, key="input_enable_solar_time", help="选中：使用经度校准真太阳时；不选：使用北京时间(120°E)")
        
        st.caption("ℹ️ V4.0 内核已支持真太阳时校准。不选中则默认按标准北京时间计算。")

        # Main Submit Button
        submitted = st.form_submit_button("🚀 开始排盘 (Calculate)")
        
        return submitted
