import streamlit as st
from core.config_manager import ConfigManager
from ui.utils import init_session_state
from ui.modules.profile_section import render_profile_section
from ui.modules.input_form import render_input_form

def render_sidebar(app_mode):
    """
    Renders the sidebar content: System Monitor & Config Status.
    Navigation has moved to top level in main.py.
    """
    with st.sidebar:
        # 1. System Monitor & Config Status
        # Shared Config Initialization (Invisible but necessary)
        cm = ConfigManager()
        saved_host = cm.get("ollama_host", "http://115.93.10.51:11434")
        init_session_state({'ollama_host': saved_host})
        
        saved_model = cm.get("selected_model_name")
        if saved_model:
            init_session_state({'selected_model_name': saved_model})
            
        if app_mode == "🔮 智能排盘 (Prediction)":
             st.markdown("### 🔧 档案与输入")
             render_profile_section()
             st.divider()
             submit = render_input_form()
             if submit:
                 st.session_state['calc_active'] = True
             st.divider()
        
        # Engine Switcher (for all modes that use engine)
        if app_mode in ["🔮 智能排盘 (Prediction)", "🧪 量子验证 (Quantum Lab)", "🎬 命运影院 (Cinema)"]:
            st.markdown("---")
            st.markdown("### ⚙️ 计算引擎 (Engine)")
            init_session_state({'engine_mode': 'Legacy'})
            
            engine_mode = st.radio(
                "引擎模式",
                ["Legacy (线性)", "Graph (图网络)"],
                index=0 if st.session_state.get('engine_mode', 'Legacy') == 'Legacy' else 1,
                key='engine_mode_radio',
                help="选择计算引擎：Legacy=传统线性算法，Graph=图网络矩阵算法"
            )
            st.session_state['engine_mode'] = 'Legacy' if engine_mode == 'Legacy (线性)' else 'Graph'
            
            if engine_mode == 'Graph (图网络)':
                st.caption("🌐 图网络引擎：基于矩阵传播的动态能量计算")
            else:
                st.caption("📊 传统引擎：基于规则的能量累加计算")
            
        # Global Background Task Monitor (Removed per request)
        # render_mini_task_monitor() 
            
# def render_mini_task_monitor():

