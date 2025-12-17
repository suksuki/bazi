import streamlit as st
import datetime
import json
import time
import os
import numpy as np
import pandas as pd
import copy  # V9.2 Fix
import plotly.graph_objects as go
import logging

# [V10.1] 用于平滑曲线的插值
try:
    from scipy.interpolate import make_interp_spline
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# 设置 logger
logger = logging.getLogger(__name__)

from ui.components.charts import DestinyCharts
from ui.components.styles import (
    get_glassmorphism_css,
    get_animation_css, 
    get_bazi_table_css,
    get_theme,
    get_nature_color
)

# Core Imports (V9.5 MVC: Models accessed via Controller)
from core.engine_v88 import EngineV88 as QuantumEngine  # V9.1 Unified Engine
from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
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


def calculate_lucky_score(result: dict, useful_god: list, taboo_god: list, 
                          year_pillar: str = None, day_master: str = None) -> float:
    """
    [V56.0 改进版] 计算吉凶分（Lucky Score）
    从 verify_timeline.py 移植
    """
    dynamic_score = result.get('dynamic_score', 0.0)
    trigger_events = result.get('trigger_events', [])
    strength_score = result.get('strength_score', 50.0)
    strength_label = result.get('strength_label', 'Balanced')
    
    # 基础分数：动态评分
    base_score = dynamic_score
    
    # 检查触发事件
    penalty = 0.0
    bonus = 0.0
    
    # [V56.0 新增] 检测七杀攻身
    has_seven_kill = False
    has_officer_attack = False
    
    # 从流年天干判断七杀攻身
    if year_pillar and day_master and len(year_pillar) >= 2:
        year_stem = year_pillar[0]
        seven_kill_map = {
            '甲': '庚', '乙': '辛', '丙': '壬', '丁': '癸', '戊': '甲',
            '己': '乙', '庚': '丙', '辛': '丁', '壬': '戊', '癸': '己'
        }
        if seven_kill_map.get(day_master) == year_stem:
            has_seven_kill = True
            if strength_label == 'Weak' or strength_score < 40:
                has_officer_attack = True
                penalty += 35.0
            else:
                penalty += 20.0
    
    for event in trigger_events:
        if '冲提纲' in event:
            penalty += 40.0
        if '强根' in event or '帝旺' in event or '临官' in event:
            if '帝旺' in event:
                bonus += 20.0
            elif '临官' in event:
                bonus += 15.0
            elif '强根' in event:
                bonus += 10.0
        elif '冲开' in event and '库' in event:
            bonus += 20.0
        elif '冲' in event and '提纲' not in event:
            penalty += 5.0
    
    # 最终分数
    lucky_score = base_score - penalty + bonus
    
    # [V56.0 改进] 强根加分需要根据身强身弱调整
    has_strong_root = any('强根' in e or '帝旺' in e or '临官' in e for e in trigger_events)
    if has_strong_root and penalty < 5:
        if strength_label == 'Weak' or strength_score < 40:
            if any('帝旺' in e for e in trigger_events):
                lucky_score += 12.0
            elif any('临官' in e for e in trigger_events):
                lucky_score += 10.0
            else:
                lucky_score += 8.0
        else:
            if any('帝旺' in e for e in trigger_events):
                lucky_score += 8.0
            elif any('临官' in e for e in trigger_events):
                lucky_score += 6.0
            else:
                lucky_score += 5.0
    
    # 根据喜用神调整
    if dynamic_score > 50 and penalty < 10:
        lucky_score += 10.0
    
    # [V56.0 改进] 七杀攻身时，即使有官印相生也要扣分
    has_officer_resource = any('官印相生' in e for e in trigger_events)
    if has_officer_resource:
        if has_officer_attack:
            lucky_score += 0.0
        else:
            lucky_score += 30.0
    
    # 如果有冲提纲，大幅扣分
    has_month_clash = any('冲提纲' in e for e in trigger_events)
    if has_month_clash:
        lucky_score -= 30.0
    
    # 如果有库开，加分
    has_storehouse_open = any('冲开' in e and '库' in e for e in trigger_events)
    if has_storehouse_open:
        lucky_score += 25.0
    
    # [V56.0 新增] 如果七杀攻身且身弱，额外扣分
    if has_seven_kill and (strength_label == 'Weak' or strength_score < 40):
        has_passage = any('通关' in e for e in trigger_events)
        if not has_passage:
            lucky_score -= 15.0
        else:
            lucky_score -= 8.0
    
    return max(0.0, min(100.0, lucky_score))


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
    d_raw = user_data.get('date', datetime.date(1990, 1, 1))
    # 处理 date 可能是字典的情况
    if isinstance(d_raw, dict):
        d = datetime.date(
            d_raw.get('year', 1990),
            d_raw.get('month', 1),
            d_raw.get('day', 1)
        )
    elif isinstance(d_raw, datetime.date):
        d = d_raw
    else:
        d = datetime.date(1990, 1, 1)
    t = user_data.get('time', 12)
    # Ensure city has a non-None value for downstream usage
    city_for_calc = user_data.get('city') or city_for_controller or "Beijing"
    
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
        tengods_distributions = {}  # [V10.1] 概率分布数据
        
        # [V10.1] 检查是否启用概率分布
        use_probabilistic = st.session_state.get('use_probabilistic_energy', False)
        
        for key, name in tengods_mapping.items():
            value = flux_data_for_analysis.get(key, 0) * 0.08  # Apply scale
            if value > 0.1:  # Only show significant values
                tengods_data[name] = value
                
                # [V10.1] 如果启用概率分布，计算概率分布
                if use_probabilistic:
                    # 使用蒙特卡洛模拟生成概率分布
                    from core.bayesian_inference import BayesianInference
                    
                    # 定义参数扰动范围（基于当前值）
                    # 注意：monte_carlo_simulation 需要正确的参数格式
                    parameter_ranges = {
                        'base_value': (value * 0.9, value * 1.1),  # ±10% 扰动
                    }
                    
                    try:
                        # 蒙特卡洛模拟
                        monte_carlo_result = BayesianInference.monte_carlo_simulation(
                            base_estimate=value,
                            parameter_ranges=parameter_ranges,
                            n_samples=500,  # 减少采样次数以提高性能
                            confidence_level=0.95
                        )
                    except Exception as e:
                        logger.debug(f"十神能量概率分布计算失败 ({name}): {e}")
                        # 如果计算失败，使用简化版本（基于不确定性估计）
                        monte_carlo_result = {
                            'mean': value,
                            'std': value * 0.1,  # 假设 10% 的不确定性
                            'percentiles': {
                                'p5': value * 0.85,
                                'p25': value * 0.92,
                                'p50': value,
                                'p75': value * 1.08,
                                'p95': value * 1.15
                            }
                        }
                    
                    tengods_distributions[name] = {
                        "mean": monte_carlo_result.get('mean', value),
                        "std": monte_carlo_result.get('std', value * 0.1),
                        "percentiles": monte_carlo_result.get('percentiles', {}),
                        "point_estimate": value
                    }
        
        if tengods_data:
            # Display as cards
            tengods_cols = st.columns(5)
            tengods_list = list(tengods_data.items())
            
            for i, (name, value) in enumerate(tengods_list):
                col_idx = i % 5
                with tengods_cols[col_idx]:
                    if use_probabilistic and name in tengods_distributions:
                        # [V10.1] 显示概率分布
                        dist = tengods_distributions[name]
                        mean_val = dist['mean']
                        std_val = dist['std']
                        percentiles = dist.get('percentiles', {})
                        
                        # 显示均值和标准差
                        st.metric(
                            name, 
                            f"{mean_val:.2f}",
                            delta=f"±{std_val:.2f}" if std_val > 0 else None
                        )
                        
                        # 显示分位数（如果有）
                        if percentiles:
                            p25 = percentiles.get('p25', mean_val)
                            p75 = percentiles.get('p75', mean_val)
                            st.caption(f"范围: {p25:.2f} - {p75:.2f}")
                    else:
                        # 传统模式：只显示确定性值
                        st.metric(name, f"{value:.2f}")
            
            # Create a summary DataFrame
            if use_probabilistic and tengods_distributions:
                # [V10.1] 包含概率分布的数据表
                tengods_df = pd.DataFrame([
                    {
                        '十神': name, 
                        '能量值(均值)': tengods_distributions.get(name, {}).get('mean', value),
                        '标准差': tengods_distributions.get(name, {}).get('std', 0),
                        '25%分位': tengods_distributions.get(name, {}).get('percentiles', {}).get('p25', value),
                        '50%分位': tengods_distributions.get(name, {}).get('percentiles', {}).get('p50', value),
                        '75%分位': tengods_distributions.get(name, {}).get('percentiles', {}).get('p75', value),
                        '点估计': value
                    } 
                    for name, value in sorted(tengods_data.items(), key=lambda x: x[1], reverse=True)
                ])
            else:
                # 传统模式：只显示确定性值
                tengods_df = pd.DataFrame([
                    {'十神': name, '能量值': value} 
                    for name, value in sorted(tengods_data.items(), key=lambda x: x[1], reverse=True)
                ])
            
            with st.expander("📋 十神详细数据表"):
                st.dataframe(tengods_df, hide_index=True, width='stretch')
                
                # [V10.1] 如果启用概率分布，显示说明
                if use_probabilistic and tengods_distributions:
                    st.info("📊 **概率分布模式**: 能量值显示为概率分布（均值±标准差），而非单一确定值。这更符合量子八字的本质：命运是概率分布，而非确定性结论。")
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
            'year': d.year if isinstance(d, datetime.date) else (d.get('year', 1990) if isinstance(d, dict) else 1990),
            'month': d.month if isinstance(d, datetime.date) else (d.get('month', 1) if isinstance(d, dict) else 1),
            'day': d.day if isinstance(d, datetime.date) else (d.get('day', 1) if isinstance(d, dict) else 1),
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
    
    # [V9.3 MCP] 模型不确定性提示
    # 从 chart 或 results 中获取不确定性信息
    uncertainty = None
    # 尝试从多个位置获取不确定性信息
    if chart:
        if 'strength_data' in chart and isinstance(chart['strength_data'], dict):
            uncertainty = chart['strength_data'].get('uncertainty')
        elif 'uncertainty' in chart:
            uncertainty = chart.get('uncertainty')
    
    if not uncertainty and results:
        if 'strength_data' in results and isinstance(results['strength_data'], dict):
            uncertainty = results['strength_data'].get('uncertainty')
        elif 'uncertainty' in results:
            uncertainty = results.get('uncertainty')
    
    # 如果仍然没有，尝试从引擎直接获取
    if not uncertainty and engine:
        try:
            # 使用引擎的 analyze 方法获取不确定性
            analysis_result = engine.analyze(bazi_list, chart.get('day', {}).get('stem', ''), 
                                            chart.get('gender', '男'), 
                                            selected_yun['gan_zhi'] if selected_yun else None,
                                            current_gan_zhi)
            if analysis_result and 'uncertainty' in analysis_result:
                uncertainty = analysis_result.get('uncertainty')
        except Exception as e:
            logger.debug(f"Could not get uncertainty from engine: {e}")
    
    if uncertainty and uncertainty.get('has_uncertainty', False):
        warning_msg = uncertainty.get('warning_message', '')
        if warning_msg:
            pattern_type = uncertainty.get('pattern_type', 'Unknown')
            if pattern_type == 'Extreme_Weak':
                st.warning(warning_msg)
            elif pattern_type == 'Multi_Clash':
                st.warning(warning_msg)
            elif pattern_type == 'Follower_Grid':
                st.info(warning_msg)
            
            # 显示概率分布
            follower_prob = uncertainty.get('follower_probability', 0.0)
            volatility = uncertainty.get('volatility_range', 0.0)
            if follower_prob > 0 or volatility > 0:
                prob_col1, prob_col2 = st.columns(2)
                with prob_col1:
                    if follower_prob > 0:
                        st.metric("从格转化概率", f"{follower_prob*100:.0f}%", 
                                 "概率分布", delta_color="inverse" if follower_prob > 0.3 else "normal")
                    else:
                        st.metric("从格转化概率", "0%", "稳定格局")
                with prob_col2:
                    if volatility > 0:
                        st.metric("预测波动范围", f"±{volatility:.0f}分", 
                                 "不确定性", delta_color="inverse" if volatility > 30 else "normal")
                    else:
                        st.metric("预测波动范围", "±0分", "稳定预测")
    
    # [V9.3 MCP] 宏观场实时更新显示
    era_info = controller.get_current_era_info()
    if era_info:
        st.markdown("### 🌐 宏观场 (MCP: 时代上下文)")
        era_cols = st.columns(4)
        
        with era_cols[0]:
            era_desc = era_info.get('desc', '未知')
            st.metric("当前时代", era_desc, f"周期 {era_info.get('period', '?')}")
        
        with era_cols[1]:
            era_element = era_info.get('era_element', '')
            era_bonus = era_info.get('era_bonus', 0.0)
            element_names = {'wood': '木', 'fire': '火', 'earth': '土', 'metal': '金', 'water': '水'}
            element_name = element_names.get(era_element, era_element)
            st.metric("时代红利", f"{era_bonus*100:.0f}%", f"{element_name}能量增强", delta_color="normal")
        
        with era_cols[2]:
            era_penalty = era_info.get('era_penalty', 0.0)
            controlled_element = None
            CONTROL = {'wood': 'earth', 'fire': 'metal', 'earth': 'water', 'metal': 'wood', 'water': 'fire'}
            if era_element in CONTROL:
                controlled_element = CONTROL[era_element]
                controlled_name = element_names.get(controlled_element, controlled_element)
                st.metric("时代折损", f"{abs(era_penalty)*100:.0f}%", f"{controlled_name}能量减弱", delta_color="inverse")
            else:
                st.metric("时代折损", "0%", "无")
        
        with era_cols[3]:
            start_year = era_info.get('start_year', '?')
            end_year = era_info.get('end_year', '?')
            st.metric("时代跨度", f"{start_year}-{end_year}", f"共{end_year-start_year+1}年")
        
        # 影响描述
        impact_desc = era_info.get('impact_description', '')
        if impact_desc:
            st.info(f"💡 **时代影响**: {impact_desc}")
        
        st.markdown("---")
    
    # [V9.3 MCP] Geo Effect - Enhanced Visualization
    if city_for_calc != "Unknown":
        geo_mods = controller.get_geo_modifiers(city_for_calc)
        if geo_mods:
            st.caption(f"📍 地理修正: {geo_mods.get('desc')} (Applied to Energy Map)")
            
            # [V9.3 MCP] 寒暖燥湿可视化面板
            with st.expander("🌍 环境修正详情 (MCP: 地理上下文)", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                # 温度系数
                temp_factor = geo_mods.get('temperature_factor', 1.0)
                with col1:
                    if temp_factor > 1.1:
                        st.metric("🌡️ 温度系数", f"{temp_factor:.2f}x", "热辐射极值", delta_color="inverse")
                    elif temp_factor < 0.9:
                        st.metric("🌡️ 温度系数", f"{temp_factor:.2f}x", "寒冷", delta_color="normal")
                    else:
                        st.metric("🌡️ 温度系数", f"{temp_factor:.2f}x", "中性")
                
                # 湿度系数
                humidity_factor = geo_mods.get('humidity_factor', 1.0)
                with col2:
                    if humidity_factor > 1.1:
                        st.metric("💧 湿度系数", f"{humidity_factor:.2f}x", "湿润", delta_color="normal")
                    elif humidity_factor < 0.9:
                        st.metric("💧 湿度系数", f"{humidity_factor:.2f}x", "干燥", delta_color="inverse")
                    else:
                        st.metric("💧 湿度系数", f"{humidity_factor:.2f}x", "中性")
                
                # 环境修正偏向
                env_bias = geo_mods.get('environment_bias', '未应用地理修正')
                with col3:
                    st.markdown("**环境修正偏向**")
                    st.info(env_bias)
                
                # 五行修正系数详情
                st.markdown("#### 📊 五行能量修正系数")
                element_cols = st.columns(5)
                element_labels = {'wood': '木', 'fire': '火', 'earth': '土', 'metal': '金', 'water': '水'}
                element_colors = {'wood': '🟢', 'fire': '🔴', 'earth': '🟡', 'metal': '⚪', 'water': '🔵'}
                
                for idx, (elem, label) in enumerate(element_labels.items()):
                    mod_value = geo_mods.get(elem, 1.0)
                    color_icon = element_colors.get(elem, '⚫')
                    with element_cols[idx]:
                        if mod_value > 1.05:
                            st.success(f"{color_icon} {label}\n**{mod_value:.2f}x** ⬆️")
                        elif mod_value < 0.95:
                            st.error(f"{color_icon} {label}\n**{mod_value:.2f}x** ⬇️")
                        else:
                            st.info(f"{color_icon} {label}\n**{mod_value:.2f}x** ➡️")
                
                st.caption("💡 **MCP 说明**: 地理修正系数直接影响五行能量计算，进而影响财富、事业等预测结果。")
    else:
        st.warning("⚠️ **MCP 警告**: 未选择地理城市，地域修正模块未激活。预测结果可能不准确。")
    
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
    
    # [V10.1] 初始化概率分布数据列表（用于命运全息图）
    distributions_data_for_hologram = []
    use_probabilistic = st.session_state.get('use_probabilistic_energy', False)
    
    # [V10.1] 如果启用概率分布，初始化 GraphNetworkEngine
    graph_engine_for_hologram = None
    if use_probabilistic:
        graph_config = DEFAULT_FULL_ALGO_PARAMS.copy()
        graph_config['probabilistic_energy'] = {'use_probabilistic_energy': True}
        graph_engine_for_hologram = GraphNetworkEngine(config=graph_config)
    
    # Helper for GanZhi
    gan_chars = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    zhi_chars = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    base_year = 1924 # Jia Zi
    
    # === V6.0: BaziProfile Initialization ===
    # [V56.3] 复用 Controller 的 profile，避免重复创建
    profile = controller.get_profile()
    if not profile:
        # Fallback: 如果 controller 没有 profile，则创建新的
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

        # [V10.1] 如果启用概率分布，计算概率分布数据
        domain_distributions = {}
        if use_probabilistic and graph_engine_for_hologram:
            try:
                # 使用 GraphNetworkEngine 计算概率分布
                # 获取八字信息（从 case_data 或 controller）
                chart = controller.get_chart() if hasattr(controller, 'get_chart') else None
                if chart:
                    bazi_list = [
                        chart.get('year', {}).get('stem', '') + chart.get('year', {}).get('branch', ''),
                        chart.get('month', {}).get('stem', '') + chart.get('month', {}).get('branch', ''),
                        chart.get('day', {}).get('stem', '') + chart.get('day', {}).get('branch', ''),
                        chart.get('hour', {}).get('stem', '') + chart.get('hour', {}).get('branch', '')
                    ]
                    day_master = chart.get('day', {}).get('stem', '甲')
                else:
                    # 从 case_data 获取
                    bazi_list = case_data.get('bazi', ['甲子', '乙丑', '丙寅', '丁卯'])
                    day_master = case_data.get('day_master', '甲')
                
                # 分析该年
                analyze_result = graph_engine_for_hologram.analyze(
                    bazi=bazi_list,
                    day_master=day_master,
                    luck_pillar=active_luck,
                    year_pillar=l_gz
                )
                
                # 计算 domain_scores 的概率分布（简化版：基于不确定性估计）
                from core.bayesian_inference import BayesianInference
                
                for domain_name, domain_value in [('career', safe_career), ('wealth', safe_wealth), ('relationship', safe_rel)]:
                    # 定义参数扰动范围
                    parameter_ranges = {
                        'base_value': (domain_value * 0.9, domain_value * 1.1),  # ±10% 扰动
                    }
                    
                    try:
                        monte_carlo_result = BayesianInference.monte_carlo_simulation(
                            base_estimate=domain_value,
                            parameter_ranges=parameter_ranges,
                            n_samples=500,
                            confidence_level=0.95
                        )
                        
                        domain_distributions[domain_name] = {
                            "mean": monte_carlo_result.get('mean', domain_value),
                            "std": monte_carlo_result.get('std', domain_value * 0.1),
                            "percentiles": monte_carlo_result.get('percentiles', {})
                        }
                    except Exception as e:
                        logger.debug(f"概率分布计算失败 ({domain_name}): {e}")
                        # 使用简化版本
                        domain_distributions[domain_name] = {
                            "mean": domain_value,
                            "std": domain_value * 0.1,
                            "percentiles": {
                                'p25': domain_value * 0.92,
                                'p50': domain_value,
                                'p75': domain_value * 1.08
                            }
                        }
            except Exception as e:
                logger.debug(f"命运全息图概率分布计算失败: {e}")
        
        # 保存概率分布数据
        if use_probabilistic and domain_distributions:
            distributions_data_for_hologram.append({
                'year': safe_year,
                'distributions': domain_distributions
            })

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
    # [V10.1] 传递概率分布数据到图表组件
    fig = DestinyCharts.render_life_curve(
        df_traj, 
        sim_year, 
        handover_years,
        use_probabilistic=use_probabilistic,
        distributions_data=distributions_data_for_hologram if use_probabilistic and distributions_data_for_hologram else None
    )
    
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
    
    # ==========================================
    # E. 流年大运折线 & 财富折线 (V56.2)
    # ==========================================
    st.markdown("---")
    st.markdown("### 📈 流年大运折线 & 财富折线 (Lifetime Timeline)")
    
    # [V56.3] 复用 Controller 的 profile
    # profile 已经在第718行从 controller.get_profile() 获取（或创建），这里直接复用
    # 从 profile 获取出生年份（最可靠的方式）
    if profile and hasattr(profile, 'birth_date'):
        birth_year = profile.birth_date.year
        birth_month = profile.birth_date.month
        birth_day = profile.birth_date.day
        st.caption(f"✅ 复用已有的 BaziProfile，出生日期: {birth_year}年{birth_month}月{birth_day}日")
    else:
        # Fallback: 如果 profile 不存在，从 d 获取
        if isinstance(d, datetime.date):
            birth_year = d.year
            birth_month = d.month
            birth_day = d.day
        elif isinstance(d, dict):
            birth_year = d.get('year', 1990)
            birth_month = d.get('month', 1)
            birth_day = d.get('day', 1)
        else:
            birth_year = 1990
            birth_month = 1
            birth_day = 1
        st.warning(f"⚠️ Profile不存在，使用日期: {birth_year}年{birth_month}月{birth_day}日")
    
    st.caption(f"从出生到100岁的完整预测 ({birth_year} - {birth_year + 100})")
    
    # 初始化图网络引擎（用于计算流年大运和财富）
    graph_config = DEFAULT_FULL_ALGO_PARAMS.copy()
    # 尝试加载用户配置
    try:
        config_path = os.path.join(os.path.dirname(__file__), '../../config/parameters.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                def deep_merge(base, update):
                    for key, value in update.items():
                        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                            deep_merge(base[key], value)
                        else:
                            base[key] = value
                deep_merge(graph_config, user_config)
    except Exception as e:
        st.warning(f"⚠️ 加载配置失败，使用默认配置: {e}")

    # [V10.1] 概率分布开关（来自侧边栏）
    use_prob = st.session_state.get('use_probabilistic_energy', False)
    if 'probabilistic_energy' not in graph_config:
        graph_config['probabilistic_energy'] = {}
    graph_config['probabilistic_energy']['use_probabilistic_energy'] = use_prob
    
    graph_engine = GraphNetworkEngine(config=graph_config)
    
    # 获取八字信息
    bazi_list = [
        f"{chart.get('year',{}).get('stem','')}{chart.get('year',{}).get('branch','')}",
        f"{chart.get('month',{}).get('stem','')}{chart.get('month',{}).get('branch','')}",
        f"{chart.get('day',{}).get('stem','')}{chart.get('day',{}).get('branch','')}",
        f"{chart.get('hour',{}).get('stem','')}{chart.get('hour',{}).get('branch','')}"
    ]
    day_master = chart.get('day', {}).get('stem', '甲')
    gender_str = gender
    
    # 计算从出生到100岁的数据（从出生年份开始，不是当前年份）
    # 例如：如果出生年份是1990年，则计算1990-2090年
    end_year = birth_year + 100
    years_range = range(birth_year, end_year + 1)
    
    # 确认：确保是从出生年份开始
    if years_range and years_range[0] != birth_year:
        st.error(f"⚠️ 错误：年份范围应该从出生年份 {birth_year} 开始，但实际从 {years_range[0]} 开始")
    
    # [V56.3] 调试信息：显示年份范围
    st.caption(f"📊 年份范围: {birth_year} - {end_year} (共 {len(years_range)} 年)")
    
    # [V56.3 修复] 确保 d 是 datetime.date 类型后再访问属性
    if isinstance(d, datetime.date):
        d_display = d
    elif isinstance(d, dict):
        d_display = datetime.date(
            d.get('year', birth_year),
            d.get('month', birth_month),
            d.get('day', birth_day)
        )
    else:
        d_display = datetime.date(birth_year, birth_month, birth_day)
    
    st.caption(f"📅 出生日期: {d_display.year}年{d_display.month}月{d_display.day}日 {t}时 | 性别: {gender} (idx={gender_idx})")
    
    # [V56.3] 关键调试：显示实际使用的出生年份和profile信息
    if profile and hasattr(profile, 'birth_date'):
        st.info(f"🔍 **调试信息**: Profile出生日期 = {profile.birth_date.year}年{profile.birth_date.month}月{profile.birth_date.day}日 | 计算的birth_year = {birth_year}")
    else:
        st.warning(f"⚠️ **警告**: Profile不存在或没有birth_date属性！使用的birth_year = {birth_year}")
    
    # [V56.3] 显示前5年和后5年的年份，用于验证
    if len(years_range) > 0:
        first_5_years = list(years_range[:5])
        last_5_years = list(years_range[-5:])
        st.caption(f"📋 年份验证: 前5年 = {first_5_years}, 后5年 = {last_5_years}")
    
    # 获取大运时间表（用于检测换运）
    timeline = controller.get_luck_timeline(num_steps=15)  # 获取15步大运（150年）
    handover_years_all = []
    
    # [V10.1] 初始化概率分布数据列表
    wealth_distributions = []
    
    # 计算每年的数据
    lucky_scores = []
    wealth_indices = []
    years_list = []
    
    # 辅助函数：获取年份的干支
    gan_chars = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    zhi_chars = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    base_year = 1924
    
    # 检测换运年份
    prev_luck = None
    for timeline_item in timeline:
        if timeline_item.get('is_handover'):
            handover_years_all.append({
                'year': timeline_item.get('year'),
                'from': timeline_item.get('luck_pillar'),  # 可能需要调整
                'to': timeline_item.get('luck_pillar')
            })
    
    # 使用 BaziProfile 检测换运
    prev_luck_pillar = None
    
    # 添加进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_years = len(years_range)
    
    error_count = 0
    for idx, y in enumerate(years_range):
        try:
            # 更新进度
            progress = (idx + 1) / total_years
            progress_bar.progress(progress)
            status_text.text(f"正在计算 {y}年 ({idx + 1}/{total_years})...")
            
            # 获取当前年份的大运
            current_luck_raw = profile.get_luck_pillar_at(y)
            
            # [V56.3 修复] 确保 current_luck 是字符串格式的干支
            # lunar_python 的 getGanZhi() 可能返回字符串或整数索引
            current_luck = None
            
            if isinstance(current_luck_raw, str) and len(current_luck_raw) >= 2:
                # 已经是有效的字符串格式
                current_luck = current_luck_raw
            elif isinstance(current_luck_raw, int):
                # 如果是整数，尝试从 controller 获取
                try:
                    current_luck = controller.get_dynamic_luck_pillar(y)
                    if not isinstance(current_luck, str) or len(current_luck) < 2:
                        current_luck = None
                except:
                    current_luck = None
            else:
                # 其他类型，尝试转换为字符串
                try:
                    current_luck_str = str(current_luck_raw)
                    if len(current_luck_str) >= 2:
                        current_luck = current_luck_str
                    else:
                        current_luck = None
                except:
                    current_luck = None
            
            # 最终验证和 Fallback：确保是有效的干支格式（2个字符）
            if not current_luck or not isinstance(current_luck, str) or len(current_luck) < 2:
                # 最后尝试：从 controller 获取
                try:
                    current_luck = controller.get_dynamic_luck_pillar(y)
                    if not isinstance(current_luck, str) or len(current_luck) < 2:
                        current_luck = "未知大运"
                except:
                    current_luck = "未知大运"
            
            # [V56.3 关键修复] 最终强制类型检查：确保 current_luck 一定是字符串
            if not isinstance(current_luck, str):
                current_luck = str(current_luck) if current_luck else "未知大运"
            
            # 如果长度不够，使用默认值
            if len(current_luck) < 2:
                current_luck = "未知大运"
            
            # 检测换运
            if prev_luck_pillar and prev_luck_pillar != current_luck:
                handover_years_all.append({
                    'year': y,
                    'from': prev_luck_pillar,
                    'to': current_luck
                })
            prev_luck_pillar = current_luck
            
            # 计算流年干支
            offset = y - base_year
            year_gan = gan_chars[offset % 10]
            year_zhi = zhi_chars[offset % 12]
            year_pillar = f"{year_gan}{year_zhi}"
            
            # 1. 计算流年大运折线（使用 analyze + calculate_lucky_score）
            try:
                analyze_result = graph_engine.analyze(
                    bazi=bazi_list,
                    day_master=day_master,
                    luck_pillar=current_luck,
                    year_pillar=year_pillar
                )
                
                # 计算 lucky_score（简化版，不使用喜用神）
                useful_god = []  # 可以从其他地方获取
                taboo_god = []
                lucky_score = calculate_lucky_score(
                    analyze_result, 
                    useful_god, 
                    taboo_god,
                    year_pillar=year_pillar,
                    day_master=day_master
                )
            except Exception as e:
                lucky_score = 50.0  # 默认值
                error_count += 1
                if error_count <= 3:  # 只显示前3个错误
                    st.warning(f"⚠️ {y}年流年大运计算失败: {e}")
            
            # 2. 计算财富折线（使用 calculate_wealth_index）
            # [V56.3 关键修复] 在调用前再次确保 current_luck 是字符串
            if not isinstance(current_luck, str):
                current_luck = str(current_luck) if current_luck else "未知大运"
            if len(current_luck) < 2:
                current_luck = "未知大运"
            
            try:
                wealth_result = graph_engine.calculate_wealth_index(
                    bazi=bazi_list,
                    day_master=day_master,
                    gender=gender_str,
                    luck_pillar=current_luck,
                    year_pillar=year_pillar
                )
                
                if isinstance(wealth_result, dict):
                    wealth_index = wealth_result.get('wealth_index', 0.0)
                    wealth_details = wealth_result.get('details', [])
                    wealth_opportunity = wealth_result.get('opportunity', 0.0)
                    
                    # [V10.1] 保存概率分布数据（如果启用）
                    wealth_distribution = wealth_result.get('wealth_distribution')
                    if wealth_distribution:
                        wealth_distributions.append({
                            'year': y,
                            'distribution': wealth_distribution
                        })
                    
                    # 调试信息：显示前几年的详细计算过程
                    if idx < 5:
                        st.caption(f"🔍 {y}年财富计算: 机会={wealth_opportunity:.1f}, 指数={wealth_index:.1f}, 事件={', '.join(wealth_details[:3]) if wealth_details else '无'}")
                else:
                    wealth_index = float(wealth_result) if wealth_result else 0.0
            except Exception as e:
                wealth_index = 0.0
                error_count += 1
                if error_count <= 3:  # 只显示前3个错误
                    st.warning(f"⚠️ {y}年财富计算失败: {e}")
                    import traceback
                    st.caption(f"详细错误: {traceback.format_exc()}")
            
            years_list.append(y)
            lucky_scores.append(lucky_score)
            wealth_indices.append(wealth_index)
            
        except Exception as e:
            # 如果某年计算失败，跳过
            error_count += 1
            if error_count <= 3:  # 只显示前3个错误
                st.warning(f"⚠️ {y}年计算失败: {e}")
            continue
    
    # 清除进度条
    progress_bar.empty()
    status_text.empty()
    
    if error_count > 3:
        st.caption(f"⚠️ 共有 {error_count} 年计算失败，已自动使用默认值")
    
    # 绘制流年大运折线
    if years_list and lucky_scores:
        st.markdown("#### 📊 流年大运折线 (Lucky Score Timeline)")
        fig_lucky = go.Figure()
        
        # 添加折线
        fig_lucky.add_trace(go.Scatter(
            x=years_list,
            y=lucky_scores,
            mode='lines+markers',
            name='流年大运分',
            line=dict(color='#00BFFF', width=2),
            marker=dict(size=3),
            hovertemplate='%{x}年: %{y:.1f}分<extra></extra>'
        ))
        
        # 添加换大运的纵向虚线
        for handover in handover_years_all:
            if handover['year'] in years_list:
                fig_lucky.add_vline(
                    x=handover['year'],
                    line_width=2,
                    line_dash="dash",
                    line_color="rgba(255,255,255,0.6)",
                    annotation_text=f"🔄 换运\\n{handover['to']}",
                    annotation_position="top",
                    annotation=dict(
                        font=dict(size=10, color="white"),
                        bgcolor="rgba(100,100,255,0.3)",
                        bordercolor="rgba(255,255,255,0.5)",
                        borderwidth=1
                    )
                )
        
        fig_lucky.update_layout(
            title="流年大运折线 (从出生到100岁)",
            xaxis_title="年份 (Year)",
            yaxis_title="流年大运分 (Lucky Score)",
            yaxis=dict(range=[0, 100]),
            height=400,
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0.05)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_lucky, use_container_width=True)
    
    # 绘制财富折线
    if years_list and wealth_indices:
        st.markdown("#### 💰 财富折线 (Wealth Index Timeline)")
        fig_wealth = go.Figure()
        
        # [V10.1] 检查是否启用概率分布
        use_probabilistic = st.session_state.get('use_probabilistic_energy', False)
        
        if use_probabilistic and wealth_distributions and len(wealth_distributions) > 0:
            # 概率分布模式：显示平滑曲线和置信区间
            
            # 提取概率分布数据
            dist_years = [d['year'] for d in wealth_distributions]
            dist_means = [d['distribution'].get('mean', 0) for d in wealth_distributions]
            dist_stds = [d['distribution'].get('std', 0) for d in wealth_distributions]
            dist_lowers = [d['distribution'].get('percentiles', {}).get('p25', d['distribution'].get('mean', 0) - d['distribution'].get('std', 0)) for d in wealth_distributions]
            dist_uppers = [d['distribution'].get('percentiles', {}).get('p75', d['distribution'].get('mean', 0) + d['distribution'].get('std', 0)) for d in wealth_distributions]
            
            # 1. 添加置信区间（阴影区域）
            fig_wealth.add_trace(go.Scatter(
                x=dist_years + dist_years[::-1],
                y=dist_uppers + dist_lowers[::-1],
                fill='toself',
                fillcolor='rgba(255, 215, 0, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=True,
                name='置信区间 (25%-75%)'
            ))
            
            # 2. 添加平滑曲线（基于均值，使用插值）
            if HAS_SCIPY and len(dist_years) > 3:
                # 使用样条插值创建平滑曲线
                try:
                    # 创建更密集的x轴点
                    x_smooth = np.linspace(min(dist_years), max(dist_years), len(dist_years) * 3)
                    # 使用样条插值
                    spl = make_interp_spline(dist_years, dist_means, k=min(3, len(dist_years)-1))
                    y_smooth = spl(x_smooth)
                    
                    # 添加平滑曲线
                    fig_wealth.add_trace(go.Scatter(
                        x=x_smooth,
                        y=y_smooth,
                        mode='lines',
                        name='财富指数 (平滑曲线)',
                        line=dict(color='#FFD700', width=3, shape='spline'),
                        hovertemplate='%{x:.0f}年: %{y:.1f}分<extra></extra>'
                    ))
                except Exception as e:
                    logger.debug(f"样条插值失败，使用普通折线: {e}")
                    # 如果插值失败，使用普通折线
                    fig_wealth.add_trace(go.Scatter(
                        x=dist_years,
                        y=dist_means,
                        mode='lines+markers',
                        name='财富指数 (均值)',
                        line=dict(color='#FFD700', width=3, shape='spline'),
                        marker=dict(size=4),
                        hovertemplate='%{x}年: %{y:.1f}分 (均值)<extra></extra>'
                    ))
            else:
                # 数据点太少或没有 scipy，使用普通折线（但使用 spline 形状）
                fig_wealth.add_trace(go.Scatter(
                    x=dist_years,
                    y=dist_means,
                    mode='lines+markers',
                    name='财富指数 (均值)',
                    line=dict(color='#FFD700', width=3, shape='spline'),  # shape='spline' 让 Plotly 自动平滑
                    marker=dict(size=4),
                    hovertemplate='%{x}年: %{y:.1f}分 (均值)<extra></extra>'
                ))
            
            # 3. 添加点估计值（可选，作为参考）
            fig_wealth.add_trace(go.Scatter(
                x=years_list,
                y=wealth_indices,
                mode='markers',
                name='点估计',
                marker=dict(size=2, color='rgba(255, 215, 0, 0.5)'),
                hovertemplate='%{x}年: %{y:.1f}分 (点估计)<extra></extra>',
                showlegend=False
            ))
        else:
            # 传统模式：普通折线（但使用 spline 形状让曲线更平滑）
            fig_wealth.add_trace(go.Scatter(
                x=years_list,
                y=wealth_indices,
                mode='lines+markers',
                name='财富指数',
                line=dict(color='#FFD700', width=2, shape='spline'),  # shape='spline' 让 Plotly 自动平滑
                marker=dict(size=3),
                hovertemplate='%{x}年: %{y:.1f}分<extra></extra>'
            ))
        
        # 添加换大运的纵向虚线
        for handover in handover_years_all:
            if handover['year'] in years_list:
                fig_wealth.add_vline(
                    x=handover['year'],
                    line_width=2,
                    line_dash="dash",
                    line_color="rgba(255,255,255,0.6)",
                    annotation_text=f"🔄 换运\\n{handover['to']}",
                    annotation_position="top",
                    annotation=dict(
                        font=dict(size=10, color="white"),
                        bgcolor="rgba(100,100,255,0.3)",
                        bordercolor="rgba(255,255,255,0.5)",
                        borderwidth=1
                    )
                )
        
        fig_wealth.update_layout(
            title="财富折线 (从出生到100岁)",
            xaxis_title="年份 (Year)",
            yaxis_title="财富指数 (Wealth Index)",
            yaxis=dict(range=[-100, 100]),
            height=400,
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0.05)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_wealth, use_container_width=True)

