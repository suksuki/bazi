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
        
        # [V56.3] GEO 修正城市选择（放在"启用真太阳时"之后）
        from utils.constants_manager import get_constants
        import json
        import os
        
        consts = get_constants()
        
        # 加载 GEO 城市列表
        def _load_geo_cities():
            geo_path = os.path.join(os.path.dirname(__file__), "../../data/geo_coefficients.json")
            try:
                with open(geo_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return list(data.get("cities", {}).keys())
            except:
                return []
        
        raw_cities = _load_geo_cities()
        if "Beijing" in raw_cities:
            raw_cities.remove("Beijing")
        cities = ["None"] + consts.DEFAULT_GEO_CITIES
        
        # 从 session_state 获取默认城市
        default_city = st.session_state.get("unified_geo_city", "None")
        default_idx = cities.index(default_city) if default_city in cities else 0
        
        # [V9.3 MCP] 强制地理输入提示
        st.markdown("**🌍 GEO 修正城市** (必需)")
        st.caption("⚠️ 为激活地域修正模块，请选择出生城市或输入经纬度")
        
        selected_city = st.selectbox(
            "选择城市", 
            cities, 
            index=default_idx, 
            key="unified_geo_city",
            help="选择出生城市以应用地理修正系数（寒暖燥湿、地域加持）"
        )
        
        # [V9.3 MCP] 如果选择 "None"，显示警告
        if selected_city == "None":
            st.warning("⚠️ **MCP 警告**: 未选择地理城市，地域修正模块将无法激活。预测结果可能不准确。")
            st.info("💡 **建议**: 请选择出生城市，或在下方的经纬度输入中提供坐标。")

        # Main Submit Button
        submitted = st.form_submit_button("🚀 开始排盘 (Calculate)")
        
        # [V9.3 MCP] 验证地理输入（可选：可以阻止提交）
        # 如果需要强制，可以取消下面的注释
        # if submitted and selected_city == "None":
        #     st.error("❌ 请先选择地理城市或输入经纬度，才能开始排盘。")
        #     submitted = False
        
        return submitted