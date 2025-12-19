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
        
        # V13.0: 已删除引擎模式选择和概率分布开关
        # - Legacy 引擎已完全移除，只使用 Graph 网络引擎
        # - 概率分布已全程启用，无需开关
            
        # Global Background Task Monitor (Removed per request)
        # render_mini_task_monitor() 
            
# def render_mini_task_monitor():

