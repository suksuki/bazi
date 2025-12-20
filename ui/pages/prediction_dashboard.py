import streamlit as st
import datetime
import plotly.graph_objects as go
import logging
import pandas as pd

# Helpers
from ui.components.styles import (
    get_glassmorphism_css,
    get_animation_css, 
    get_bazi_table_css,
    get_theme
)
from ui.components.cards import DestinyCards

# MVC
from controllers.bazi_controller import BaziController
from core.engine_v88 import EngineV88 as QuantumEngine
from utils.notification_manager import get_notification_manager

# Configure Logger
logger = logging.getLogger(__name__)

def render_prediction_dashboard():
    """
    Renders the Clean Prediction Dashboard (Smart Prediction).
    Fully MVC compliant.
    """
    controller = BaziController()
    
    # 1. State Verification
    user_data = controller.get_user_data()
    if not user_data or not user_data.get('name'):
        st.info("👈 请在左侧边栏输入您的出生信息并点击 '开始排盘'。")
        return

    # Display Notifications
    get_notification_manager().display_all()

    # 2. Get Data from Controller
    chart = controller.get_chart()
    luck_cycles = controller.get_luck_cycles()
    
    # User Info
    name = user_data.get('name', '未命名')
    
    # 3. UI Header
    st.title(f"📜 {name} 的命理探究")
    st.caption(f"🔧 Engine Version: `{QuantumEngine.VERSION}`")
    
    # Apply CSS
    st.markdown(get_glassmorphism_css(), unsafe_allow_html=True)
    st.markdown(get_animation_css(), unsafe_allow_html=True)
    st.markdown(get_bazi_table_css(), unsafe_allow_html=True)

    # 4. Render Chart (Four Pillars)
    cols = st.columns(4)
    pillars = ['year', 'month', 'day', 'hour']
    labels = ["年柱 (Year)", "月柱 (Month)", "日柱 (Day)", "时柱 (Hour)"]
    
    for i, p_key in enumerate(pillars):
        p_data = chart.get(p_key, {})
        stem = p_data.get('stem', '?')
        branch = p_data.get('branch', '?')
        
        # Theme
        t_stem = get_theme(stem)
        t_branch = get_theme(branch)
        dm_class = "dm-glow" if (p_key == 'day') else ""
        
        # Hidden Stems Display
        hidden_list = p_data.get('hidden_stems', [])
        hidden_html = '<div class="hidden-container">'
        for h_char in hidden_list:
            h_theme = get_theme(h_char)
            hidden_html += f'<div class="hidden-token" style="background: {h_theme["grad"]};" title="{h_char}">{h_char}</div>'
        hidden_html += '</div>'
        
        with cols[i]:
            st.markdown(f"""<div class="pillar-card">
    <div class="pillar-title">{labels[i]}</div>
    <div class="quantum-token {dm_class}" style="background: {t_stem['grad']}; animation: {t_stem['anim']} 3s infinite alternate;">
        <div class="token-icon">{t_stem['icon']}</div>
        <div class="token-char">{stem}</div>
    </div>
    <div class="quantum-token" style="background: {t_branch['grad']}; animation: {t_branch['anim']} 4s infinite alternate; margin-top: 10px;">
         <div class="token-icon">{t_branch['icon']}</div>
        <div class="token-char">{branch}</div>
    </div>
    {hidden_html}
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # 5. Time Machine (Da Yun & Liu Nian)
    st.subheader("⏳ 流年推演 (Fate Simulation)")
    
    current_year = datetime.datetime.now().year
    c1, c2 = st.columns([2, 1])
    
    selected_yun = None
    current_gan_zhi = None 
    
    # Da Yun Selection
    if luck_cycles:
        with c1:
            yun_options = [f"{c['start_year']}~{c['end_year']} ({c['start_age']}岁): {c['gan_zhi']}" for c in luck_cycles]
            default_idx = 0
            for i, c in enumerate(luck_cycles):
                if c['start_year'] <= current_year <= c['end_year']:
                    default_idx = i
                    break
            selected_yun_str = st.selectbox("当前大运 (Da Yun)", yun_options, index=default_idx)
            selected_yun = luck_cycles[yun_options.index(selected_yun_str)]
            
    # Liu Nian Selection
    with c2:
        sim_year = st.number_input("模拟流年 (Year)", min_value=1900, max_value=2100, value=current_year)
        # Calculate Liu Nian
        base_year = 1924 # Jia Zi
        offset = sim_year - base_year
        gd = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
        zhi = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
        ln_gan = gd[offset % 10]
        ln_zhi = zhi[offset % 12]
        ln_gan_zhi = f"{ln_gan}{ln_zhi}"
        st.metric("流年", f"{sim_year} {ln_gan_zhi}")
        
    current_gan_zhi = ln_gan_zhi # Focus on Liu Nian for Physics

    # 6. Core Analysis (Flux Data)
    st.markdown("---")
    st.subheader("📊 八字核心分析 (Bazi Core Analysis)")
    
    # Get Flux Data via Controller
    flux_data = controller.get_flux_data(selected_yun, current_gan_zhi)
    
    if flux_data:
        # A. Wang/Shuai
        wang_shuai_str = controller.get_wang_shuai_str(flux_data)
        col_ws1, col_ws2 = st.columns([1, 2])
        with col_ws1:
            if "身旺" in wang_shuai_str:
                st.success(f"**日主强弱**: {wang_shuai_str}")
            elif "身弱" in wang_shuai_str:
                st.warning(f"**日主强弱**: {wang_shuai_str}")
            else:
                st.info(f"**日主强弱**: {wang_shuai_str}")
        
        with col_ws2:
             s_self = flux_data.get('BiJian', 0) + flux_data.get('JieCai', 0)
             st.caption(f"日主能量值: {(s_self * 0.08):.2f}")

        # B. Five Elements
        element_energies = controller.get_five_element_energies(flux_data)
        if element_energies:
            st.markdown("#### 🌈 五行能量分布")
            
            # Simple Bar Chart
            elements = list(element_energies.keys())
            energies = list(element_energies.values())
            colors = {'Wood': '#4CAF50', 'Fire': '#F44336', 'Earth': '#FF9800', 'Metal': '#2196F3', 'Water': '#00BCD4'}
            
            fig = go.Figure(data=[go.Bar(
                x=elements, y=energies,
                marker_color=[colors.get(e, '#aaa') for e in elements],
                text=[f"{e:.2f}" for e in energies],
                textposition='auto'
            )])
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=10, b=20), xaxis_title="五行 (Elements)", yaxis_title="能量值 (Energy)")
            st.plotly_chart(fig, use_container_width=True)

    # 7. Quantum Physics Diagnostics
    st.markdown("---")
    st.subheader("🧬 命运诊断 (Diagnostics)")
    
    # Use Controller to get full simulation results (replaces manual QuantumEngine usage)
    case_data = controller.get_case_data() # Uses internal state
    dynamic_context = {'year': current_gan_zhi, 'dayun': selected_yun['gan_zhi'] if selected_yun else ''}
    
    # Run Single Year Simulation
    results = controller.run_single_year_simulation(case_data, dynamic_context)
    
    d_col1, d_col2, d_col3 = st.columns(3)
    
    # Phase Change
    phase_info = results.get('phase_info', {})
    if phase_info.get('is_active'):
        d_col1.error(f"⚠️ {phase_info.get('description')}")
        d_col1.caption(f"效率修正: {phase_info.get('resource_efficiency', 1.0)*100:.0f}%")
    else:
        d_col1.success("✅ 气候适宜 (No Phase Change)")
        
    # Domain Logic
    domains = results.get('domain_details', {})
    wealth_info = domains.get('wealth', {})
    d_col2.info(f"💰 财运判定: {wealth_info.get('reason', 'Normal')}")
    
    career_info = domains.get('career', {})
    d_col3.info(f"⚔️ 事业判定: {career_info.get('reason', 'Normal')}")
    
    # Uncertainty / MCP Era
    st.markdown("---")
    
    # Era Info from Controller
    era_info = controller.get_current_era_info()
    if era_info:
        st.markdown("### 🌐 宏观场 (MCP: 时代上下文)")
        cols = st.columns(4)
        cols[0].metric("当前时代", era_info.get('desc', '未知'), f"周期 {era_info.get('period')}")
        cols[1].metric("红利元素", era_info.get('era_element', 'None'))
        cols[2].metric("红利加成", f"{era_info.get('era_bonus', 0)*100:.0f}%")
        cols[3].metric("时代折损", f"{era_info.get('era_penalty', 0)*100:.0f}%")

    # Layout Footer
    st.markdown("---")
    st.caption(f"天机·AI命理演算系统 {BaziController.VERSION if hasattr(BaziController, 'VERSION') else ''} | Powered by Gemini 2.0 Flash")
