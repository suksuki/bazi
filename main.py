import streamlit as st
import logging
import os
from ui.utils import load_css
from ui.sidebar import render_sidebar
from core.config_manager import ConfigManager

# 1. Page Configuration
st.set_page_config(
    page_title="AI Bazi PRO", 
    layout="wide", 
    page_icon="☯️",
    initial_sidebar_state="expanded"
)

# 2. Global Styling & Title
load_css()
from ui.components.theme import apply_custom_header
apply_custom_header("🔮 吉普赛 · AI 命运占卜", "基于量子纠缠与子平古法的命运演算系统")

# 2.1 Top Navigation
from ui.utils import init_session_state
init_session_state({"nav_radio": "🔮 智能排盘 (Prediction)"})

app_mode = st.radio(
    "导航 (Navigation)", 
    ["🔮 智能排盘 (Prediction)", "💰 财运推演 (Wealth)", "🌀 量子仿真 (Simulation)", "🌙 自我进化 (Evolution)", "📜 古籍挖掘 (Mining)", "✨ 量子真言 (Quantum Lab)", "🌟 命运回响 (Cinema)", "🕯️ 悟性训练 (Training)", "📋 八字档案审计 (Audit)", "🌌 全息格局 (Holographic)", "⚙️ 天机设置 (Config)", "⚡ 架构师 (Architect)"], 
    horizontal=True,
    label_visibility="collapsed",
    key="nav_radio"
)
st.markdown("<br>", unsafe_allow_html=True)


# 3. Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 4. Sidebar Content (Profile Manager etc.)
render_sidebar(app_mode)

# 5. Page Routing
if app_mode == "⚡ 架构师 (Architect)":
    from ui.pages.architect_console import render_architect_console
    render_architect_console()

elif app_mode == "⚙️ 天机设置 (Config)":
    from ui.pages.system_config import render_system_config
    cm = ConfigManager()
    render_system_config(cm)

elif app_mode == "🕯️ 悟性训练 (Training)":
    from ui.pages.training_center import render_training_center
    render_training_center()
    
elif app_mode == "✨ 量子真言 (Quantum Lab)":
    import ui.pages.quantum_lab as qlab
    qlab.render()

elif app_mode == "🌟 命运回响 (Cinema)":
    import ui.pages.zeitgeist as cinema
    cinema.render()

elif app_mode == "🌀 量子仿真 (Simulation)":
    from ui.pages.quantum_simulation import render
    render()

elif app_mode == "🌙 自我进化 (Evolution)":
    from ui.pages.self_learning import render_self_learning
    render_self_learning()

elif app_mode == "📜 古籍挖掘 (Mining)":
    from ui.pages.mining_console import render as render_mining_console
    render_mining_console()

elif app_mode == "💰 财运推演 (Wealth)":
    from ui.pages.wealth_verification import render
    render()

elif app_mode == "📋 八字档案审计 (Audit)":
    from ui.pages.profile_audit import render
    render()

elif app_mode == "🌌 全息格局 (Holographic)":
    from ui.pages.holographic_pattern import render
    render()

elif app_mode == "🔮 智能排盘 (Prediction)":
    # --- Prediction Mode ---
    from ui.pages.prediction_dashboard import render_prediction_dashboard

    # Layout: Full Width Main Area
    # (Tools are now in Sidebar)

    # C. Prediction Dashboard
    if st.session_state.get('calc_active', False):
         render_prediction_dashboard()
    else:
         # Welcome / Placeholder
         st.info("👈 请在左侧侧边栏 (Sidebar) 选择档案或输入信息，点击 '开始排盘' 查看结果。")
         st.markdown("""
         ### 🌟 欢迎进入天机系统
         
         **核心功能 Quick Start:**
         1. **档案管理**: 建立并管理您的命理档案。
         2. **AI 排盘**: 融合古法子平与量子力学的深度演算。
         3. **时空熔炉**: 探索大运流年与原局的微妙化学反应。
         """)

# 6. Global Background Services
@st.cache_resource
def get_background_worker():
    """Starts the background task scheduler singleton."""
    # Stability Fix: Check if we should disable embedded worker (Process Separation)
    if os.environ.get("DISABLE_EMBEDDED_WORKER") == "true":
        logging.info("ℹ️  Embedded Worker DISABLED (Process Separation Mode)")
        return None

    from core.scheduler import BackgroundWorker
    worker = BackgroundWorker()
    worker.start()
    return worker

bg_worker = get_background_worker()
