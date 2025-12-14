import streamlit as st
import datetime
import json
import time
import numpy as np
import pandas as pd
from ui.components.charts import DestinyCharts
from ui.components.styles import (
    get_glassmorphism_css,
    get_animation_css, 
    get_bazi_table_css,
    get_theme,
    get_nature_color
)

# Core Imports
from core.calculator import BaziCalculator
from core.flux import FluxEngine
from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Pure Modular
from learning.db import LearningDB
from core.interactions import get_stem_interaction, get_branch_interaction
from core.bazi_profile import BaziProfile
from ui.components.cards import DestinyCards




def render_prediction_dashboard():
    """
    Renders the V2.4 Pure Prediction Dashboard.
    Focuses solely on Quantum Physics Logic.
    """
    # 0. Inputs (Session State)
    name = st.session_state.get('input_name', '某人')
    gender = st.session_state.get('input_gender', '男')
    d = st.session_state.get('input_date', datetime.date(1990, 1, 1))
    t = st.session_state.get('input_time', 12)
    
    # 1. Basic Calculation (The Chart)
    enable_solar = st.session_state.get('input_enable_solar_time', True)
    longitude = st.session_state.get('input_longitude', 116.46) if enable_solar else 120.0
    
    calc = BaziCalculator(d.year, d.month, d.day, t, 0, longitude=longitude)
    chart = calc.get_chart()
    details = calc.get_details()
    
    # Luck Cycles
    gender_idx = 1 if "男" in gender else 0
    luck_cycles = calc.get_luck_cycles(gender_idx)
    
    # 2. UI: Header & Chart
    st.title(f"🔮 {name} 的量子命盘 (V5.3 Skull)")
    st.caption(f"🔧 Engine Version: `{QuantumEngine.VERSION}` (Modular)")
    
    # --- V2.9 Glassmorphism CSS (Dark Mode) ---
    st.markdown(get_glassmorphism_css(), unsafe_allow_html=True)

    
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
    
    # 4. Engine Execution (Flux -> Quantum V2.4)
    
    # A. FluxEngine (Sensor Layer)
    flux_engine = FluxEngine(chart)
    
    # Prepare Environment
    dy_dict = None
    if selected_yun:
        gz = selected_yun['gan_zhi']
        if len(gz) >= 2: dy_dict = {'stem': gz[0], 'branch': gz[1]}
        
    ln_dict = None
    if current_gan_zhi and len(current_gan_zhi) >= 2:
        ln_dict = {'stem': current_gan_zhi[0], 'branch': current_gan_zhi[1]}
        
    flux_engine.set_environment(dy_dict, ln_dict)
    
    # Run Calculation
    flux_data = flux_engine.compute_energy_state()
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
    
    # 1. Load Parameters (Golden Master V2.9)
    try:
        import os
        params_path = os.path.join(os.path.dirname(__file__), '../../data/golden_parameters.json')
        with open(params_path, 'r') as f:
            gp = json.load(f)
        
        # Pass the full configuration directly to QuantumEngine.
        # The engine's _flatten_params method will handle the nested structure 
        # (k_factors, logic_switches, weights, etc.) automatically.
        params = gp
        
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
    pe_list = []
    p_order = ["year_stem", "year_branch", "month_stem", "month_branch", "day_stem", "day_branch", "hour_stem", "hour_branch"]
    for pid in p_order:
        val = 0.0
        for p in flux_engine.particles:
            if p.id == pid:
                val = p.wave.amplitude * scale # Apply Scaling to match Physics/TenGods magnitude
                break
        pe_list.append(round(val, 1))

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
        }
    }
    
    # 3. Execute Quantum Engine
    engine = QuantumEngine(params)
    dynamic_context = {'year': current_gan_zhi, 'dayun': selected_yun['gan_zhi'] if selected_yun else ''}
    results = engine.calculate_energy(case_data, dynamic_context)
    
    # 4. Render Interface (Quantum Lab Style)
    st.markdown("### 🏛️ 四柱能量 (Four Pillars Energy - Interaction Matrix)")
    
    DestinyCards.render_bazi_table_with_engine(
        chart, selected_yun, current_gan_zhi, flux_engine, scale, wang_shuai_str
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
        
        # 2. Call QuantumEngine V6.0 Interface
        ctx = engine.calculate_year_context(profile, y)
        
        # Extract data from DestinyContext (clean and simple!)
        final_career = ctx.career
        final_wealth = ctx.wealth
        final_rel = ctx.relationship
        full_desc = ctx.description
        
        # Trinity data for visualization
        is_treasury_open = ctx.is_treasury_open
        treasury_icon_type = ctx.icon
        treasury_risk = ctx.risk_level
        treasury_tags = ctx.tags
        
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
                
                timeline = engine.get_luck_timeline(
                    birth_year, birth_month, birth_day, birth_hour, gender, num_steps=10
                )
                
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
                        luck = engine.get_dynamic_luck_pillar(
                            birth_year, birth_month, birth_day, birth_hour, gender, y
                        )
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
        audit_data = []
        for p in flux_engine.particles:
            if "dy_" in p.id or "ln_" in p.id: continue
            raw = p.wave.amplitude
            scaled = raw * scale
            audit_data.append({
                "Particle": f"{p.char} ({p.id})",
                "Raw Flux (E_f)": f"{raw:.1f}",
                "Scale Factor": f"{scale}",
                "Quantum Input (E_q)": f"{scaled:.1f}"
            })
        st.dataframe(pd.DataFrame(audit_data))
        
        st.markdown("### 3. 被激活的黄金参数 (Active Golden Params)")
        st.caption("以下参数来自 `golden_parameters.json`，确保了与量子验证实验室的一致性。")
        st.json(params)

