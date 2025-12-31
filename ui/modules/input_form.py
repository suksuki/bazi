import streamlit as st
from datetime import datetime as dt
from ui.utils import init_session_state

def render_input_form():
    """
    Renders the Input Form with real-time session state sync.
    Returns:
        submitted (bool): True if 'Calculate' button clicked.
    """
    # Ensure session state keys exist with defaults
    init_session_state({
        'input_name': "某人",
        'input_gender': "男",
        'input_date': dt(1990, 1, 1),
        'input_time': 12,
        'input_minute': 0,
        'input_longitude': 116.46,
        'unified_geo_city': "None",
        'input_enable_solar_time': True
    })

    # Use container instead of form for real-time updates
    from ui.components.theme import COLORS, GLASS_STYLE, sidebar_header
    sidebar_header("👤 命主信息", "👤")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("姓名 (Name)", key="input_name")
    with col2:
        st.radio("性别 (Gender)", ["女", "男"], horizontal=True, key="input_gender")
        
    st.date_input(
        "出生日期 (Date)", 
        min_value=dt(1900, 1, 1), 
        max_value=dt(2100, 12, 31), 
        key="input_date"
    )
    
    # Time input: Hour and Minute
    st.markdown("**出生时间 (Birth Time)**")
    c3, c4, c5 = st.columns([1, 1, 1.5])
    with c3:
        st.number_input("时 (Hour)", 0, 23, key="input_time", help="0-23小时制")
    with c4:
        st.number_input("分 (Minute)", 0, 59, key="input_minute", help="0-59分钟")
    with c5:
        st.number_input("经度 (Longitude)", -180.0, 180.0, step=0.1, key="input_longitude", help="用于真太阳时校准")
    
    st.caption("💡 **时辰边界提示**: 时辰边界为奇数小时(1,3,5...23)。例如17:00已是酉时(17-19时)。")
    
    # True Solar Time Toggle
    st.checkbox(
        "启用真太阳时 (True Solar Time)", 
        key="input_enable_solar_time", 
        help="选中：使用经度校准真太阳时；不选：使用北京时间(120°E)"
    )
    
    # GEO City Selection
    from utils.constants_manager import get_constants
    import json
    import os
    
    consts = get_constants()
    
    # Load GEO cities
    def _load_geo_cities():
        geo_path = os.path.join(os.path.dirname(__file__), "../../data/geo_coefficients.json")
        try:
            with open(geo_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return list(data.get("cities", {}).keys())
        except:
            return []
    
    cities = ["None"] + consts.DEFAULT_GEO_CITIES
    
    st.markdown("**🌍 地脉修正 (Geomancy Context)**")
    
    # Get current city from session state for correct index
    current_city = st.session_state.get("unified_geo_city", "None")
    city_idx = cities.index(current_city) if current_city in cities else 0
    
    st.selectbox(
        "选择城市", 
        cities, 
        index=city_idx,
        key="unified_geo_city",
        help="选择出生城市以应用地理修正系数"
    )
    
    if st.session_state.get('unified_geo_city') == "None":
        st.warning("⚠️ 未选择城市，地域修正模块将无法激活。")

    st.divider()
    
    # Main Submit Button
    submitted = st.button("🔮 启卦排盘 (Divination)", type="primary", width='stretch')
    
    return submitted