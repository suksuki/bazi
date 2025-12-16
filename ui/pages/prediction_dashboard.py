import streamlit as st
import datetime
import json
import time
import numpy as np
import pandas as pd
import copy  # V9.2 Fix
from ui.components.charts import DestinyCharts
from ui.components.styles import (
    get_glassmorphism_css,
    get_animation_css, 
    get_bazi_table_css,
    get_theme,
    get_nature_color
)

# Core Imports (V9.5 MVC: Models accessed via Controller)
from core.engine_v91 import EngineV91 as QuantumEngine  # V9.1 for VERSION display only
from learning.db import LearningDB
from core.interactions import get_stem_interaction, get_branch_interaction
from core.bazi_profile import BaziProfile
from ui.components.cards import DestinyCards

# MVC Controller Import
from controllers.bazi_controller import BaziController
from facade.bazi_facade import BaziFacade
from utils.notification_manager import get_notification_manager

# V10.0 Unified Input Panel
from ui.components.unified_input_panel import render_and_collect_input



def render_prediction_dashboard():
    """
    Renders the V2.4 Pure Prediction Dashboard.
    Focuses solely on Quantum Physics Logic.
    """
    # === V10.0: Unified Input Panel ===
    controller = BaziController()
    bazi_facade = BaziFacade(controller=controller)
    selected_case, era_factor, city_for_controller = render_and_collect_input(bazi_facade, is_quantum_lab=False)
    # Display centralized notifications
    get_notification_manager().display_all()

    # Get data from Controller (replaces direct BaziCalculator calls)
    chart = controller.get_chart()
    details = controller.get_details()
    calc = controller.get_calculator()  # For backward compatibility with advanced features

    # Luck Cycles (via Controller)
    gender_idx = controller.get_gender_idx()
    luck_cycles = controller.get_luck_cycles()

    # Extract user info from controller state
    user_data = controller.get_user_data()
    name = user_data.get('name', '某人')
    gender = user_data.get('gender', '男')
    d = user_data.get('date', datetime.date(1990, 1, 1))
    t = user_data.get('time', 12)
    # Ensure city has a non-None value for downstream usage
    city_for_calc = user_data.get('city') or city_for_controller or "Beijing"
    
    # [V9.3 UI] Sidebar Chart Summary
    st.sidebar.markdown("---")
    st.sidebar.subheader("📜 命盘信息 (Chart)")
    
    # Display Gregorian Input (Source of Truth)
    st.sidebar.markdown(f"**公历**: `{d.year}年{d.month}月{d.day}日 {t:02d}:00`")
    
    bazi_txt = f"{chart['year']['stem']}{chart['year']['branch']}  {chart['month']['stem']}{chart['month']['branch']}  {chart['day']['stem']}{chart['day']['branch']}  {chart['hour']['stem']}{chart['hour']['branch']}"
    
    # [DEBUG] Verify Sidebar Rendering
    print(f"DEBUG: Rendering Sidebar Bazi: {bazi_txt}")
    st.sidebar.code(bazi_txt, language="text")
    st.sidebar.caption(f"日主: {chart['day']['stem']}")
    # Particle weights display
    st.sidebar.subheader("⚛️ 当前生效的粒子权重")
    st.sidebar.caption("预测已应用的十神粒子影响强度校准。")
    current_weights = controller.get_current_particle_weights()
    if current_weights and any(abs(w - 1.0) > 0.001 for w in current_weights.values()):
        cols_pw = st.sidebar.columns(2)
        c_idx = 0
        for p, w in current_weights.items():
            if abs(w - 1.0) > 0.001:
                cols_pw[c_idx % 2].metric(label=f"{p} 权重", value=f"{w*100:.0f}%")
                c_idx += 1
    else:
        st.sidebar.info("当前应用默认粒子权重 (100%)。")
    
    # 2. UI: Header & Chart
    st.title(f"🔮 {name} 的量子命盘 (V5.3 Skull)")
    st.caption(f"🔧 Engine Version: `{QuantumEngine.VERSION}` (Modular)")
    
    # --- V2.9 Glassmorphism CSS (Dark Mode) ---
    st.markdown(get_glassmorphism_css(), unsafe_allow_html=True)
    
    # st.error("👻 DEBUG CHECK: V9.3 CODE IS RUNNING")

    
    # Helper: Quantum Theme System (Constitution V1.0)
    # Mapping "Forms" to Visuals (Icons + Animations + Gradients)
    
    # Quantum Theme Logic moved to ui.components.styles
    # get_theme and get_nature_color are imported


    # Prepare Data
    dm = chart.get('day', {}).get('stem')
    
    pillars = ['year', 'month', 'day', 'hour']
    labels = ["年柱 (Year)", "月柱 (Month)", "日柱 (Day)", "时柱 (Hour)"]
    
    # --- INJECT ADVANCED CSS ANIMATIONS ---
    st.markdown(get_animation_css(), unsafe_allow_html=True)
    st.markdown(get_bazi_table_css(), unsafe_allow_html=True)
    
    # Grid for True Four Pillars (4 Columns)
    cols = st.columns(4)
    
    for i, p_key in enumerate(pillars):
        p_data = chart.get(p_key, {})
        stem = p_data.get('stem', '?')
        branch = p_data.get('branch', '?')
        hidden = " ".join(p_data.get('hidden_stems', []))
        
        # Get Theme Data
        t_stem = get_theme(stem)
        t_branch = get_theme(branch)
        
        # Day Master Special Style
        dm_class = "dm-glow" if (p_key == 'day') else ""
        
        with cols[i]:
            # Render Stem Token
            
            # 1. Build Hidden Stems HTML (Core Particles)
            hidden_list = p_data.get('hidden_stems', [])
            hidden_html = '<div class="hidden-container">'
            for h_char in hidden_list:
                h_theme = get_theme(h_char)
                hidden_html += f'<div class="hidden-token" style="background: {h_theme["grad"]};" title="{h_char}">{h_char}</div>'
            hidden_html += '</div>'

            # 2. Render Card
            st.markdown(f"""<div class="pillar-card">
    <div class="pillar-title">{labels[i]}</div>
    <!-- Stem -->
    <div class="quantum-token {dm_class if i == 2 else ''}" style="background: {t_stem['grad']}; animation: {t_stem['anim']} 3s infinite alternate;">
        <div class="token-icon">{t_stem['icon']}</div>
        <div class="token-char">{stem}</div>
    </div>
    <!-- Branch -->
    <div class="quantum-token" style="background: {t_branch['grad']}; animation: {t_branch['anim']} 4s infinite alternate; margin-top: 10px;">
         <div class="token-icon">{t_branch['icon']}</div>
        <div class="token-char">{branch}</div>
    </div>
    <!-- Hidden Stems (Core Particles) -->
    {hidden_html}
</div>""", unsafe_allow_html=True)
            
    st.markdown("---")
    
    # 3. Time Machine (Dynamic Context)
    st.subheader("⏳ 时空控制台 (Time Machine)")
    
    current_year = datetime.datetime.now().year
    
    # Da Yun Selector
    c1, c2 = st.columns([2, 1])
    selected_yun = None
    current_gan_zhi = None # The active interaction pillar
    
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
            
    # Liu Nian Selector
    with c2:
        sim_year = st.number_input("模拟流年 (Year)", min_value=1900, max_value=2100, value=current_year)
        # Calculate Liu Nian GanZhi
        base_year = 1924 # Jia Zi
        offset = sim_year - base_year
        gd = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
        zhi = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
        ln_gan = gd[offset % 10]
        ln_zhi = zhi[offset % 12]
        ln_gan_zhi = f"{ln_gan}{ln_zhi}"
        st.metric("流年", f"{sim_year} {ln_gan_zhi}")
        
    current_gan_zhi = ln_gan_zhi # Focus on Liu Nian for Physics
    
    # === V9.6: 八字核心分析 (Bazi Core Analysis) ===
    st.markdown("---")
    st.subheader("📊 八字核心分析 (Bazi Core Analysis)")
    
    # Get flux data for analysis
    flux_data_for_analysis = controller.get_flux_data(selected_yun, current_gan_zhi)
    
    # 1. 日主强弱判定 (Wang/Shuai Strength)
    if flux_data_for_analysis:
        wang_shuai_str = controller.get_wang_shuai_str(flux_data_for_analysis)
        
        col_ws1, col_ws2 = st.columns([1, 2])
        with col_ws1:
            # Display strength with color coding
            if "身旺" in wang_shuai_str:
                st.success(f"**日主强弱**: {wang_shuai_str}")
            elif "身弱" in wang_shuai_str:
                st.warning(f"**日主强弱**: {wang_shuai_str}")
            else:
                st.info(f"**日主强弱**: {wang_shuai_str}")
        
        with col_ws2:
            # Calculate self energy for display
            s_self = flux_data_for_analysis.get('BiJian', 0) + flux_data_for_analysis.get('JieCai', 0)
            est_self = s_self * 0.08
            st.caption(f"日主能量值: {est_self:.2f}")
    
    # 2. 五行能量状态 (Five Elements Energy Distribution)
    st.markdown("#### 🌈 五行能量分布 (Five Elements Energy)")
    
    # V9.6 Architecture Fix: Use Controller API instead of direct calculation in View
    # All calculation logic is encapsulated in controller.get_five_element_energies()
    element_energies = controller.get_five_element_energies(flux_data_for_analysis)
    
    # Create visualization
    if element_energies:
            import plotly.graph_objects as go
            
            elements = list(element_energies.keys())
            energies = list(element_energies.values())
            
            # Color mapping for elements
            colors = {
                'Wood': '#4CAF50',
                'Fire': '#F44336',
                'Earth': '#FF9800',
                'Metal': '#2196F3',
                'Water': '#00BCD4'
            }
            
            fig_elements = go.Figure(data=[
                go.Bar(
                    x=elements,
                    y=energies,
                    marker_color=[colors.get(e, '#757575') for e in elements],
                    text=[f"{e:.2f}" for e in energies],
                    textposition='auto'
                )
            ])
            
            fig_elements.update_layout(
                title="五行能量分布图",
                xaxis_title="五行 (Elements)",
                yaxis_title="能量值 (Energy)",
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig_elements, width='stretch')
            
            # Display as metrics
            col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns(5)
            cols_e = [col_e1, col_e2, col_e3, col_e4, col_e5]
            for i, (element, energy) in enumerate(element_energies.items()):
                with cols_e[i]:
                    st.metric(element, f"{energy:.2f}")
    
    # 3. 十神组合分析 (Ten Gods Analysis)
    st.markdown("#### ⚡ 十神组合分析 (Ten Gods Combination)")
    
    if flux_data_for_analysis:
        # Map flux data keys to Ten Gods
        tengods_mapping = {
            'BiJian': '比肩',
            'JieCai': '劫财',
            'ShiShen': '食神',
            'ShangGuan': '伤官',
            'PianCai': '偏财',
            'ZhengCai': '正财',
            'QiSha': '七杀',
            'ZhengGuan': '正官',
            'PianYin': '偏印',
            'ZhengYin': '正印'
        }
        
        tengods_data = {}
        for key, name in tengods_mapping.items():
            value = flux_data_for_analysis.get(key, 0) * 0.08  # Apply scale
            if value > 0.1:  # Only show significant values
                tengods_data[name] = value
        
        if tengods_data:
            # Display as cards
            tengods_cols = st.columns(5)
            tengods_list = list(tengods_data.items())
            
            for i, (name, value) in enumerate(tengods_list):
                col_idx = i % 5
                with tengods_cols[col_idx]:
                    st.metric(name, f"{value:.2f}")
            
            # Create a summary DataFrame
            tengods_df = pd.DataFrame([
                {'十神': name, '能量值': value} 
                for name, value in sorted(tengods_data.items(), key=lambda x: x[1], reverse=True)
            ])
            
            with st.expander("📋 十神详细数据表"):
                st.dataframe(tengods_df, hide_index=True, width='stretch')
        else:
            st.info("暂无显著的十神能量数据")
    
    # === V9.6: 核心结论与建议 (Core Conclusions & Suggestions) ===
    st.markdown("---")
    st.subheader("📝 核心结论与建议 (Core Conclusions & Suggestions)")
    
    # Get balance suggestion and top ten gods summary using Controller APIs
    if flux_data_for_analysis and element_energies:
        try:
            suggestion = controller.get_balance_suggestion(element_energies)
            summary = controller.get_top_ten_gods_summary(flux_data_for_analysis)
            
            with st.expander("查看八字测试总结", expanded=True):
                # Core metrics in columns
                col1, col2, col3 = st.columns(3)
                
                # 1. 日主强弱结论
                with col1:
                    if "身旺" in wang_shuai_str:
                        st.success(f"**日主强弱**: {wang_shuai_str}")
                    elif "身弱" in wang_shuai_str:
                        st.warning(f"**日主强弱**: {wang_shuai_str}")
                    else:
                        st.info(f"**日主强弱**: {wang_shuai_str}")
                
                # 2. 五行平衡建议 (制衡元素)
                with col2:
                    if suggestion.get('element_to_balance'):
                        st.metric("制衡元素", suggestion['element_to_balance'])
                    else:
                        st.metric("制衡元素", "平衡")
                
                # 3. 核心十神总结
                with col3:
                    if summary.get('top_two_gods'):
                        st.metric("核心十神", summary['top_two_gods'])
                    else:
                        st.metric("核心十神", "未检测")
                
                # Detailed suggestions
                st.markdown("---")
                
                # Balance suggestion
                if suggestion.get('element_to_balance') and suggestion.get('element_to_support'):
                    st.success(f"💡 **平衡建议**: 需要 **{suggestion['element_to_balance']}** 来制衡 **{suggestion['element_to_support']}**。")
                
                # Text summary
                if suggestion.get('text_summary'):
                    st.info(f"📚 **解读**: {suggestion['text_summary']}")
                
                # Top ten gods summary
                if summary.get('top_gods'):
                    st.markdown(f"🧬 **显著十神**: {summary['top_gods']}")
                
                # Optional: Show detailed data for verification
                if st.checkbox("显示详细数据 (Show Detailed Data)", value=False):
                    st.json({
                        "suggestion": suggestion,
                        "summary": summary,
                        "element_energies": element_energies
                    })
        except Exception as e:
            st.warning(f"⚠️ 无法生成核心结论: {e}")
            # Log error for debugging (if logging is needed, import logging module)
    
    st.markdown("---")
    
    # 4. Engine Execution (Flux -> Quantum V2.4) - V9.5 MVC via Controller
    
    # A. FluxEngine (Sensor Layer) - Via Controller
    flux_data = controller.get_flux_data(selected_yun, current_gan_zhi)
    dynamic_gods_map = flux_data
    
    # DEBUG: Inspect Flux Data
    with st.expander("🔍 DEBUG: Flux Data Output", expanded=False):
        st.write("Keys:", list(flux_data.keys()))
        if 'ZhengGuan' in flux_data:
            st.write("ZhengGuan Score:", flux_data['ZhengGuan'])
        elif 'ten_gods' in flux_data:
            st.write("Ten Gods found in sub-key 'ten_gods'")
            st.json(flux_data['ten_gods'])
        else:
            st.error("Ten Gods Keys MISSING from root!")
            st.json(flux_data)
    
    # -------------------------------------------------------------------------
    # UNIT: Quantum Engine Integration & Visualization (Aligns with Quantum Lab)
    # -------------------------------------------------------------------------
    
    # 1. Load Parameters (Genesis + Fire God Tuning)
    try:
        import os
        # A. Base Golden Parameters (V2.9)
        base_path = os.path.join(os.path.dirname(__file__), '../../data/golden_parameters.json')
        with open(base_path, 'r') as f:
            params = json.load(f)
            
        # B. Fire God Auto-Tuned Parameters (V9.1 Genesis)
        # Check config/tuning_params.json
        tune_path = os.path.join(os.path.dirname(__file__), '../../config/tuning_params.json')
        tuned_loaded = False
        if os.path.exists(tune_path):
            with open(tune_path, 'r') as f:
                tuned_params = json.load(f)
                # Deep merge or specific update?
                # Auto-tuner V1.0 mainly tunes physics base unit.
                # Structure: { "physics": { "base_unit": 8.0 } }
                if "physics" in tuned_params:
                    params.setdefault("physics", {}).update(tuned_params["physics"])
                tuned_loaded = True
        
    except Exception as e:
        st.error(f"Config Load Error: {e}")
        params = {} # Fallback to engine defaults

    # 2. Extract Data from Flux (Sensor) to feed Quantum Engine

    # 2. Extract Data from Flux (Sensor) to feed Quantum Engine
    scale = 0.08 
    dg = flux_data # Use Flux Data
    
    s_self = dg.get('BiJian', 0) + dg.get('JieCai', 0)
    s_output = dg.get('ShiShen', 0) + dg.get('ShangGuan', 0)
    s_wealth = dg.get('ZhengCai', 0) + dg.get('PianCai', 0)
    s_officer = dg.get('ZhengGuan', 0) + dg.get('QiSha', 0)
    s_resource = dg.get('ZhengYin', 0) + dg.get('PianYin', 0)
    
    est_self = s_self * scale
    
    final_self = est_self
    wang_shuai_str = "身中和"
    if est_self < 1.0:
        wang_shuai_str = "假从/极弱"
        final_self = est_self - 8.0 
    elif est_self < 3.5:
        wang_shuai_str = "身弱"
        final_self = est_self - 6.0 
    else:
        wang_shuai_str = "身旺"

    # Capture Pillar Energies
    # V9.6 Architecture Fix: Use Controller API instead of direct flux_engine access
    pe_list = controller.get_pillar_energies(flux_data, params, scale)

    physics_sources = {
        'self': {'stem_support': final_self},
        'output': {'base': s_output * scale},
        'wealth': {'base': s_wealth * scale},
        'officer': {'base': s_officer * scale},
        'resource': {'base': s_resource * scale},
        'pillar_energies': pe_list # Inject Scaled Real Energies
    }
    
    # Construct Bazi List for Structural Clash Logic
    bazi_list = [
        f"{chart.get('year',{}).get('stem','')}{chart.get('year',{}).get('branch','')}",
        f"{chart.get('month',{}).get('stem','')}{chart.get('month',{}).get('branch','')}",
        f"{chart.get('day',{}).get('stem','')}{chart.get('day',{}).get('branch','')}",
        f"{chart.get('hour',{}).get('stem','')}{chart.get('hour',{}).get('branch','')}"
    ]

    # [V9.2 Fix] Geo Initialization Lockout
    # Force Neutral Region if input is invalid to prevent engine collapse
    # V9.6: Handle "None" option - use neutral region (Beijing) for calculations
    city_val = chart.get('city') or user_data.get('city') or ""
    if not city_val or str(city_val).lower() in ['unknown', 'none', '']:
        city_for_calc = "Beijing"  # Use neutral region for engine calculations
    else:
        city_for_calc = city_val

    case_data = {
        'id': 8888, 
        'gender': gender,
        'day_master': chart.get('day',{}).get('stem','?'),
        'wang_shuai': wang_shuai_str, 
        'physics_sources': physics_sources,
        'bazi': bazi_list, # Required for Structural/Harm Matrix
        # Sprint 5.4: 注入出生信息以支持动态大运
        'birth_info': {
            'year': d.year,
            'month': d.month,
            'day': d.day,
            'hour': t,
            'gender': 1 if "男" in gender else 0
        },
        'city': city_for_calc  # V9.1 Geo Input (Now Guaranteed)
    }
    
    # 3. Execute Quantum Engine - V9.5 MVC via Controller
    engine = controller.get_quantum_engine()  # Reference for advanced features (geo, timeline)
    dynamic_context = {'year': current_gan_zhi, 'dayun': selected_yun['gan_zhi'] if selected_yun else ''}
    results = controller.run_single_year_simulation(case_data, dynamic_context)
    
    # === V9.1 Destiny Cinema: Diagnostic HUD ===
    st.markdown("### 🧬 命运诊断 (Diagnostics)")
    
    
    
    # [V9.2 Fix] Physics Sources Reconsolidation
    # Prefer Engine V9.1 Pillar Energies over FluxEngine
    engine_pe_raw = results.get('pillar_energies', [])
    if engine_pe_raw and len(engine_pe_raw) == 8:
        # Enforce Float Types (JSON safety)
        try:
            engine_pe = [float(x) for x in engine_pe_raw]
            if sum(engine_pe) > 0.1:
                physics_sources['pillar_energies'] = engine_pe
                # Important: Update case_data referene so UI components see the new values
                case_data['physics_sources'] = physics_sources
        except Exception as e:
            st.error(f"Pillar Energy Type Error: {e}")
    
    # Refill case_data for UI components that rely on it having physics_sources
    case_data['physics_sources'] = physics_sources
    d_col1, d_col2, d_col3 = st.columns(3)
    
    # Phase Change
    phase_info = results.get('phase_info', {})
    if phase_info.get('is_active'):
        d_col1.error(f"⚠️ {phase_info.get('description')}")
        d_col1.caption(f"效率修正: {phase_info.get('resource_efficiency')*100:.0f}%")
    else:
        d_col1.success("✅ 气候适宜 (No Phase Change)")
        
    # Domain Logic
    domains = results.get('domain_details', {})
    wealth_info = domains.get('wealth', {})
    d_col2.info(f"💰 财运判定: {wealth_info.get('reason', 'Normal')}")
    
    career_info = domains.get('career', {})
    d_col3.info(f"⚔️ 事业判定: {career_info.get('reason', 'Normal')}")
    
    # Geo Effect - V9.5 MVC via Controller
    if city_for_calc != "Unknown":
        geo_mods = controller.get_geo_modifiers(city_for_calc)
        if geo_mods:
             st.caption(f"📍 地理修正: {geo_mods.get('desc')} (Applied to Energy Map)")
    
    # 4. Render Interface (Quantum Lab Style)
    st.markdown("### 🏛️ 四柱能量 (Four Pillars Energy - Interaction Matrix)")
    
    # V9.6 Architecture Fix: Pass pe_list instead of flux_engine
    DestinyCards.render_bazi_table_with_engine(
        chart, selected_yun, current_gan_zhi, pe_list, scale, wang_shuai_str
    )
    
    st.markdown("---")
    
    # 5. Ten Gods Stats (Using Flux Data directly for Display Consistency)
    DestinyCards.render_ten_gods_metrics(dg, scale)

    st.markdown("---")
    

    # 5. Result Visualization (Section 4 & 5 Requirement)
    DestinyCards.render_quantum_verdicts(results)
        
    # B. Narrative Box
    # B. Narrative Box (V2.9: Narrative Cards)
    st.markdown("### 📜 核心叙事 (Narrative Events)")
    
    narrative_events = results.get('narrative_events', [])
    
    if narrative_events:
        nc1, nc2 = st.columns(2)
        for i, event in enumerate(narrative_events):
            with nc1 if i % 2 == 0 else nc2:
                DestinyCards.render_narrative_card(event)
    else:
        # Fallback to description if no special events
        desc = results.get('desc', '能量流转平稳')
        st.info(f"**V2.3 Narrative:**\n\n{desc}")

    st.markdown("---")
    # --- New Section: Quantum Destiny Trajectory (Charts) ---
    # --- New Section: Dynamic Timeline (Quantum Lab Logic) ---
    st.markdown("### 🌊 动态流年模拟 (Dynamic Timeline)")
    st.caption(f"未来 12 年 ({sim_year} - {sim_year+11}) 能量趋势模拟")
    
    # Sprint 5.4: Adaptive Disclaimer
    birth_info_check = case_data.get('birth_info')
    is_dynamic_ready = birth_info_check and birth_info_check.get('year')
    
    if is_dynamic_ready:
        st.info("""
✅ **动态大运已激活**: 系统正在根据您的出生日期实时计算大运切换。
如果图表中出现 🔄 虚线，表示该年运势进入新阶段。
        """.strip())
    else:
        st.warning("""
ℹ️ **静态大运模式**: 由于未检测到具体出生日期（仅有四柱干支），系统将使用当前大运进行推演。
若需查看精确的换运时间，请使用日期方式重新排盘。
        """.strip())
    
    years = range(sim_year, sim_year + 12)
    traj_data = []
    handover_years = []  # Sprint 5.4: 记录换运年份
    
    # Helper for GanZhi
    gan_chars = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    zhi_chars = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    base_year = 1924 # Jia Zi
    
    # === V6.0: BaziProfile Initialization ===
    # Convert input date/time to full datetime
    birth_dt = datetime.datetime.combine(d, datetime.time(t, 0))
    # BUG FIX: 使用 gender_idx (整数 1/0) 而不是 gender (字符串 "男"/"女")
    # BaziProfile 需要整数参数: 1=男, 0=女
    profile = BaziProfile(birth_dt, gender_idx)
    
    # Optional: Update profile with specific analysis if needed (e.g. wang_shuai from previous steps if we trust it more?)
    # For now, let BaziProfile calculate its own strength to be the Single Source of Truth.
    
    # === BUG FIX: 初始化 prev_luck 为模拟起始年的前一年大运 ===
    # 这样可以正确检测到第一年是否有换运
    prev_luck = profile.get_luck_pillar_at(sim_year - 1)
    
    for y in years:
        offset = y - base_year
        l_gan = gan_chars[offset % 10]
        l_zhi = zhi_chars[offset % 12]
        l_gz = f"{l_gan}{l_zhi}"
        
        # 1. Get Luck from Profile (O(1))
        active_luck = profile.get_luck_pillar_at(y)
        
        # 2. Call QuantumEngine V6.0 Interface (Direct Mode)
        # Bypass calculate_year_context to ensure case_data dict is correctly validated
        # [V9.2 CRITICAL FIX] Prevent Reference Pollution by Deep Copying Case Data
        # This isolates each year's calculation state
        import copy
        safe_case_data = copy.deepcopy(case_data)
        
        dyn_ctx = {'year': l_gz, 'dayun': active_luck, 'luck': active_luck}
        energy_res = engine.calculate_energy(safe_case_data, dyn_ctx)
        
        # [DIAGNOSTIC] Inspect API Payload for the first year
        if y == years[0]:
             st.markdown(f"**🕵️ API PAYLOAD DIAGNOSTIC ({y})**")
             st.write(f"Raw Keys: {list(energy_res.keys())}")
             st.write(f"Career: {energy_res.get('career')}, Wealth: {energy_res.get('wealth')}, Rel: {energy_res.get('relationship')}")
             # st.json(energy_res) # Uncomment for full dump if needed
        
        # Extract data (Directly from Dict -> Float)
        # Use 'or 0.0' to handle None explicitly (Fix for JSON null)
        final_career = float(energy_res.get('career') or 0.0)
        final_wealth = float(energy_res.get('wealth') or 0.0)
        final_rel = float(energy_res.get('relationship') or 0.0)
        
        # [V9.2 Safety Net] Ultimate Fallback Strategy
        # If any major dimension is lost (0.0), salvage from Static Results
        if final_career <= 0.01:
            final_career = float(results.get('career') or 5.5)
        if final_wealth <= 0.01:
            final_wealth = float(results.get('wealth') or 1.5)
        if final_rel <= 0.01:
            final_rel = float(results.get('relationship') or 3.3)
        
        # [DIAGNOSTIC] One-time trace
        if y == years[0]:
             st.write(f"🔍 **Value Trace ({y})**:")
             st.write(f"  • Dyn: {energy_res.get('career')} | Stat: {results.get('career')} | Fin: {final_career}")
            
        full_desc = energy_res.get('desc', '')

        full_desc = energy_res.get('desc', '')
        
        # Trinity data for visualization
        # Note: V9.1 domain_details structure might differ from V8.8
        dom_det = energy_res.get('domain_details', {})
        is_treasury_open = dom_det.get('is_treasury_open', False)
        treasury_icon_type = dom_det.get('icon', '❓')
        treasury_risk = dom_det.get('risk_level', 'Normal')
        treasury_tags = dom_det.get('tags', [])
        
        # Sprint 5.4: 检测换运点
        if prev_luck and prev_luck != active_luck:
            handover_years.append({
                'year': y,
                'from': prev_luck,
                'to': active_luck
            })
        prev_luck = active_luck

        # 0. 确保数据类型绝对安全
        safe_year = int(y)
        safe_career = float(final_career) if final_career is not None else 0.0
        safe_wealth = float(final_wealth) if final_wealth is not None else 0.0
        safe_rel = float(final_rel) if final_rel is not None else 0.0

        traj_data.append({
            "year": safe_year,
            "label": f"{safe_year}\n{l_gz}",
            "career": round(safe_career, 2),
            "wealth": round(safe_wealth, 2),
            "relationship": round(safe_rel, 2),
            
            # [V9.3 Hologram] Base vs Final (Ghost Lines)
            # Simulating raw Score (Base) vs Modified Score (Final)
            # In V9.3 Engine, this will be calculated. Here we mock a 10% Geo Lift for visualization.
            "base_career": round(safe_career * 0.9, 2), 
            "base_wealth": round(safe_wealth * 0.9, 2),
            "base_relationship": round(safe_rel * 0.9, 2),

            "desc": full_desc,
            # V3.5 Metadata (simplified)
            "is_treasury_open": is_treasury_open,
            "treasury_icon": treasury_icon_type,
            "treasury_risk": treasury_risk
        })
        
    # Sprint 5.4 Debug: 显示大运变化信息
    if handover_years:
        st.success(f"🔄 检测到 {len(handover_years)} 个换运点：")
        for h in handover_years:
            st.write(f"  • {h['year']}年: {h['from']} → {h['to']}")
    else:
        st.error("⚠️ **Bug警告**: 12年内未检测到换运点！")
        st.error("📐 数学事实: 一步大运=10年，模拟周期=12年，12>10 → 必然有换运！")
        st.error("🔍 请查看下方调试面板获取详细信息")
        if prev_luck:
            st.caption(f"可疑: 全程使用同一大运 `{prev_luck}` (可能是fallback)")
    
    # Render Chart
    df_traj = pd.DataFrame(traj_data)
    
    # 🔍 终极调试：打印前三年数据，看看为什么没画出来
    st.write("🔍 **前三年数据检查 (Raw Data)**:")
    st.write(df_traj.head(3)[['year', 'label', 'career', 'wealth', 'relationship']])
    
    # Safety check: Only render chart if data exists
    # V6.0 Refactor: Delegate to Component
    fig = DestinyCharts.render_life_curve(df_traj, sim_year, handover_years)
    
    if fig:
        st.plotly_chart(fig, width='stretch')
        
        # V3.0 DEBUG: Treasury Detection Status
        # Computed locally for debug view
        treasury_points_labels = [d['label'] for d in traj_data if d.get('is_treasury_open')]
        treasury_points_y = [max(d['career'], d['wealth'], d['relationship']) for d in traj_data if d.get('is_treasury_open')]
        treasury_icons = [d.get('treasury_icon', '?') for d in traj_data if d.get('is_treasury_open')]

        with st.expander("🐛 财库检测调试 (Treasury Debug)", expanded=False):
            st.write(f"**总年数**: {len(traj_data)} 年")
            st.write(f"**检测到财库开启**: {len(treasury_points_labels)} 次")
            
            if treasury_points_labels:
                st.success(f"✅ 找到 {len(treasury_points_labels)} 个财库事件！")
                for i, label in enumerate(treasury_points_labels):
                    icon = treasury_icons[i]
                    st.write(f"- {label}: {icon} (Y坐标: {treasury_points_y[i]})")
            else:
                st.warning("⚠️ 未检测到任何财库开启事件")
                st.write("**检查以下内容**:")
                
                # Show sample data
                st.write("**前3年数据样本**:")
                for i, d in enumerate(traj_data[:3]):
                    st.json({
                        'year': d['year'],
                        'label': d['label'],
                        'is_treasury_open': d.get('is_treasury_open'),
                        'is_wealth_treasury': d.get('is_wealth_treasury'),
                        'treasury_element': d.get('treasury_element'),
                        'v2_details': d.get('desc', '').split('|')[-1] if '|' in d.get('desc', '') else 'none'
                    })
        
        # Sprint 5.4 DEBUG: Dynamic Luck Progression
        with st.expander("🔄 大运动态检测 (Luck Progression Debug)", expanded=True):  # 默认展开！
            st.write(f"**模拟年份**: {sim_year} - {sim_year + 11}")
            st.write(f"**检测到换运点**: {len(handover_years)} 个")
            
            # === 关键调试：显示完整大运时间表 ===
            st.markdown("### 📋 完整大运时间表 (Timeline)")
            try:
                # 尝试获取timeline
                birth_info = case_data.get('birth_info', {})
                birth_year = birth_info.get('year', 1990)
                birth_month = birth_info.get('month', 1)
                birth_day = birth_info.get('day', 1)
                birth_hour = birth_info.get('hour', 12)
                gender = birth_info.get('gender', 1)
                
                # Debug: 显示使用的出生信息
                st.caption(f"计算基准: {birth_year}年{birth_month}月{birth_day}日 {birth_hour}时 (性别:{gender})")
                
                timeline = controller.get_luck_timeline(num_steps=10)  # V9.5 MVC
                
                if timeline:
                    st.success("✅ 成功生成大运时间表：")
                    st.json(timeline) # 直接显示完整JSON以便检查
                else:
                    st.error("❌ Timeline为空！")
            except Exception as e:
                st.error(f"❌ Timeline获取失败: {e}")
            
            st.markdown("### 📊 逐年大运追踪")
            # 显示每年实际使用的大运
            if traj_data:
                year_luck_tracking = []
                # 重新计算每年的大运（用于调试）
                for y in range(sim_year, sim_year + 12):
                    try:
                        luck = controller.get_dynamic_luck_pillar(y)  # V9.5 MVC
                        year_luck_tracking.append(f"{y}: `{luck}`")
                    except:
                        year_luck_tracking.append(f"{y}: ❌ 计算失败")
                
                # 按列显示
                col1, col2, col3 = st.columns(3)
                for i, track in enumerate(year_luck_tracking):
                    if i % 3 == 0:
                        col1.write(track)
                    elif i % 3 == 1:
                        col2.write(track)
                    else:
                        col3.write(track)
            
            if handover_years:
                st.success("✅ 发现大运切换：")
                for h in handover_years:
                    st.write(f"  📍 {h['year']}年: `{h['from']}` → `{h['to']}`")
            else:
                st.error("⚠️ **BUG警告**: 12年内未检测到换运！")
                st.error("数学上12 > 10，必然有换运点！请检查算法！")
                if prev_luck:
                    st.write(f"**全程大运**: `{prev_luck}` (可能是静态fallback)")
            
            st.caption("💡 如果Timeline显示有多个大运，但未检测到换运，说明代码有Bug！")
        
        # DEBUG: Show data summary
        with st.expander("🔍 数据诊断 (Data Debug)", expanded=False):
            st.write("**样本数据点 (前3年)**:")
            for i, d in enumerate(traj_data[:3]):
                st.write(f"Year {d['year']}: Career={d['career']}, Wealth={d['wealth']}, Rel={d['relationship']}")
            
            # Check for identical values (which would cause lines to overlap)
            careers = [d['career'] for d in traj_data]
            wealths = [d['wealth'] for d in traj_data]
            rels = [d['relationship'] for d in traj_data]
            
            st.write(f"\n**数值范围**:")
            st.write(f"- 事业: [{min(careers):.1f}, {max(careers):.1f}]")
            st.write(f"- 财富: [{min(wealths):.1f}, {max(wealths):.1f}]")
            st.write(f"- 感情: [{min(rels):.1f}, {max(rels):.1f}]")
            
            # Check if all lines are identical
            if careers == wealths == rels:
                st.warning("⚠️ 警告：三条曲线数值完全相同！这会导致线条重叠。")
        
        # V3.0 Explainer: Treasury Events Log
        treasury_events = [d for d in traj_data if d.get('is_treasury_open')]
        if treasury_events:
            st.markdown("### 🔓 墓库开启事件 (Treasury Opening Events)")
            cols = st.columns(min(len(treasury_events), 4))
            for i, event in enumerate(treasury_events):
                with cols[i % 4]:
                    icon = "🏆" if event.get('is_wealth_treasury') else "🗝️"
                    treasury_type = "财库 (Wealth)" if event.get('is_wealth_treasury') else f"杂气库 ({event.get('treasury_element')})"
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 15px; border-radius: 10px; text-align: center; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                        <div style="font-size: 2.5em;">{icon}</div>
                        <div style="font-size: 1.2em; font-weight: bold; color: #FFD700; margin-top: 5px;">
                            {event['year']} {event['label'].split()[1] if len(event['label'].split()) > 1 else ''}
                        </div>
                        <div style="font-size: 0.9em; color: #EEE; margin-top: 5px;">
                            {treasury_type}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No trajectory data available for visualization.")


    # C. Physics Debug (Optional)
    with st.expander("🔬 查看物理参数 (Physics Debug)"):
        st.json(physics_sources)
        st.write(f"Wang/Shuai: {case_data['wang_shuai']}")
        
    # D. Calculation Audit (Transparency)
    with st.expander("📊 数值计算审计 (Calculation Audit)", expanded=True):
        st.markdown("### 1. 核心映射逻辑 (Core Mapping)")
        st.markdown("**原理**: 智能排盘 (Flux Engine) 生成的原始能量场 (0-100+) 通过缩放系数映射到 量子物理引擎 (Quantum Layer) 的标准输入 (0-10)。")
        st.latex(r"E_{quantum} = E_{flux} \times 0.08")
        
        st.markdown("### 2. 详细转换追踪 (Trace)")
        # V9.6 Architecture Fix: Use Controller API instead of direct flux_engine access
        audit_data = controller.get_particle_audit_data(flux_data, scale)
        st.dataframe(pd.DataFrame(audit_data))
        
        st.markdown("### 3. 被激活的黄金参数 (Active Golden Params)")
        st.caption("以下参数来自 `golden_parameters.json` 及 `Auto-Tuning` 结果。")
        
        # Highlight Genesis Mutation
        base_unit = params.get('physics', {}).get('base_unit')
        if base_unit == 8.0:
             st.success("🔥 **火神调优已激活**: `Physics.BaseUnit` 已从 10.0 调整为 **8.0** (准确率提升至 68%)")
        
        st.json(params)

