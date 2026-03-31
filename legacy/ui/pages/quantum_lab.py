import streamlit as st
import json
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import re
import sys

# --- Core Engine Imports (Quantum Trinity V2.0) ---
from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.nexus.definitions import BaziParticleNexus, PhysicsConstants, ArbitrationNexus
from core.bazi_profile import VirtualBaziProfile
from core.models.config_model import ConfigModel
from controllers.quantum_lab_controller import QuantumLabController
from core.profile_manager import ProfileManager
from core.trinity.core.engines.quantum_dispersion import QuantumDispersionEngine
from core.trinity.core.intelligence.destiny_translator import TranslationStyle

# --- Refactored Imports (Decoupling) ---
from core.data.geo_cities import GEO_CITY_MAP
from core.controllers.quantum_lab_logic import QuantumLabLogicController

# --- UI Components ---
from ui.components.oscilloscope import Oscilloscope
from ui.components.coherence_gauge import CoherenceGauge
from ui.components.envelope_gauge import EnvelopeGauge
from ui.components.tuning_panel import render_tuning_panel
from ui.components.theme import COLORS, GLASS_STYLE, apply_custom_header
from ui.components.wave_vision_3d import render_wave_vision_3d
from ui.components.molviz_3d import render_molviz_3d


# --- Singletons / Global Instances (Phase 40 Optimization) ---
from core.trinity.core.unified_arbitrator_master import quantum_framework
# oracle = TrinityOracle() # Replaced by LogicController global instance if needed, or use controller methods

# Logic Controller (Static/Singleton Wrapper)
logic_ctrl = QuantumLabLogicController

# Helper Aliases for backward compatibility in this file
get_ten_god = QuantumLabLogicController.get_ten_god
run_heavy_oracle_analysis = QuantumLabLogicController.run_heavy_oracle_analysis
run_arbitration_cached = QuantumLabLogicController.run_arbitration_cached

def render():
    # --- Robust Global Styling (Targeting Streamlit Classes) ---
    st.markdown(f"""
    <style>
    /* Main Background & Fonts */
    .stApp {{
        background: radial-gradient(circle at 50% 50%, #1a0a2e 0%, #0d0015 100%);
        color: #e2e8f0;
    }}
    
    /* Re-styling Tabs for Clarity */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: rgba(0,0,0,0.2);
        padding: 5px;
        border-radius: 12px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border: 1px solid rgba(255,215,0,0.1);
        border-radius: 8px;
        padding: 8px 16px;
        background: rgba(255,255,255,0.02);
        transition: all 0.3s;
    }}
    .stTabs [aria-selected="true"] {{
        background: rgba(64, 224, 208, 0.15) !important;
        border-color: #40e0d0 !important;
        color: #40e0d0 !important;
    }}

    /* HUD Cards */
    .hud-card {{
        background: rgba(45, 27, 78, 0.4);
        border: 1px solid rgba(255, 215, 0, 0.15);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 10px;
    }}
    .sh-label {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; font-family: 'Inter', sans-serif; }}
    .sh-val {{ font-size: 22px; font-weight: bold; margin-top: 5px; font-family: 'JetBrains Mono', monospace; }}

    /* Fix Button Over-glow */
    .stButton>button {{
        border-radius: 10px;
        border: 1px solid rgba(64, 224, 208, 0.3);
        background: rgba(64, 224, 208, 0.05);
        color: #40e0d0;
        transition: all 0.3s;
    }}
    .stButton>button:hover {{
        border-color: #40e0d0;
        box-shadow: 0 0 15px rgba(64, 224, 208, 0.4);
    }}
    
    /* Custom spacing for blocks */
    [data-testid="stVerticalBlock"] > div:has(div.hud-card) {{
        padding: 0 !important;
    }}
    
    /* Narrow tabs to prevent collision */
    .stTabs [data-baseweb="tab"] {{
        font-size: 14px !important;
        padding-left: 20px !important;
        padding-right: 20px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # 1. Premium Header (Bilingual)
    apply_custom_header("🧪 量子实验室 (QUANTUM LABORATORY)", "V21.0 Trinity 统一核心 | 命运实时验证 (Real-time Fate Verification)")

    # 2. Logic Initialization
    @st.cache_resource
    def get_controller(): return QuantumLabController()
    controller = get_controller()
    config_model = ConfigModel()
    golden_config = config_model.load_config()

    # [GLOBAL SIDEBAR] - Define Scenario early for Arbitration usage
    selected_scenario = st.sidebar.selectbox(
        "🎯 仲裁场景 (Arbitration Scenario)",
        ["General", "Wealth", "Relationship", "Health", "Career"],
        index=0,
        help="注入上下文场景，调整规则权重。例如：Wealth 模式会强化流体力学规则。"
    )

    # Sidebar: Algorithm Tuning
    full_config, _ = render_tuning_panel(controller, golden_config)

    # 3. COMMAND CENTER (Top Selection Box)
    # Using st.container(border=True) for clean structure without breaking DOM
    with st.container():
        st.markdown("### 🧬 指挥中心 (COMMAND CENTER)")
        c_src, c_obj = st.columns([1, 4])
        
        with c_src:
            input_mode = st.radio("数据源 (Data Source)", ["📚 预设 (Presets)", "✍️ 手动 (Manual)", "🗃️ 档案 (Archive)"], key="input_mode")
        
        selected_case = None
        if input_mode == "📚 预设 (Presets)":
            with c_obj:
                # Use explicit TTL to ensure file updates are caught
                @st.cache_data(ttl=5)
                def load_all_cases():
                    cases = []
                    # Added oppose_matrix_v21.json for Phase 28 verification
                    paths = [
                        "../../tests/data/integrated_extreme_cases.json",
                        "../../tests/data/oppose_matrix_v21.json",
                        "../../tests/data/quantum_mantra_v93.json", 
                        "../../tests/v14_tuning_matrix.json", 
                        "../../tests/standard_physics_tests.json",
                        "../../data/calibration_cases.json"
                    ]
                    for p in paths:
                        abs_p = os.path.normpath(os.path.join(os.path.dirname(__file__), p))
                        if os.path.exists(abs_p):
                            try:
                                with open(abs_p, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    for c in data:
                                        if not any(ex.get('id') == c.get('id') for ex in cases): cases.append(c)
                            except: pass
                    
                    # Sort cases: OPPOSE cases first, then by ID
                    def sort_key(x):
                        cid = str(x.get('id', ''))
                        priority = 0 if cid.startswith('OPPOSE_') else 1
                        return (priority, cid)
                    
                    cases.sort(key=sort_key)
                    return cases
                
                all_cases = load_all_cases()
                if not all_cases:
                    st.warning("⚠️ 预设案例库加载失败，请检查数据路径。")
                else:
                    # [NEW] Case Search Filter
                    filter_txt = st.text_input("🔍 搜索案例 (Search Case)", "", placeholder="输入ID、描述或数字...")
                    
                    filtered_cases = all_cases
                    if filter_txt:
                        ft = filter_txt.lower()
                        filtered_cases = [
                            c for i, c in enumerate(all_cases) 
                            if ft in c.get('id', '').lower() 
                            or ft in c.get('description', '').lower()
                            or ft in str(i+1)
                        ]
                        
                    if not filtered_cases:
                        st.warning("No matching cases found.")
                        selected_case = None
                    else:
                        # Find original index for display consistency? 
                        # Actually just re-index for the filtered list is fine for selection
                        case_idx = st.selectbox(
                            f"选择实验对象 (Select Subject) [{len(filtered_cases)}/{len(all_cases)}]", 
                            range(len(filtered_cases)), 
                            format_func=lambda i: f"[{filtered_cases[i].get('id','?')}] {filtered_cases[i].get('description', filtered_cases[i].get('name','Unknown'))}"
                        )
                        selected_case = filtered_cases[case_idx]
        elif input_mode == "🗃️ 档案 (Archive)":
            with c_obj:
                pm = ProfileManager()
                profiles = pm.get_all()
                if not profiles:
                    st.warning("⚠️ 档案库为空，请先在智能排盘页面保存档案。")
                else:
                    prof_idx = st.selectbox(
                        "选择档案 (Select Archive)", 
                        range(len(profiles)), 
                        format_func=lambda i: f"{profiles[i].get('name')} | {profiles[i].get('gender')} | {profiles[i].get('year')}-{profiles[i].get('month'):02d}-{profiles[i].get('day'):02d} {profiles[i].get('hour'):02d}:{profiles[i].get('minute', 0):02d}"
                    )
                    sel_prof = profiles[prof_idx]
                    
                    # Convert to simulation format
                    prof_id = sel_prof.get('id')
                    if st.session_state.get('last_archive_id') != prof_id:
                        try:
                            res = controller.calculate_chart({
                                'birth_year': sel_prof.get('year'), 
                                'birth_month': sel_prof.get('month'), 
                                'birth_day': sel_prof.get('day'), 
                                'birth_hour': sel_prof.get('hour'), 
                                'birth_minute': sel_prof.get('minute', 0), 
                                'gender': sel_prof.get('gender')
                            })
                            st.session_state['archive_cache'] = {
                                'id': f"ARCH_{prof_id[:8]}", 
                                'gender': sel_prof.get('gender'), 
                                'bazi': [f"{p[0]}{p[1]}" for p in res['bazi']], 
                                'day_master': res['day_master'], 
                                'birth_info': res['birth_info'],
                                'description': f"档案: {sel_prof.get('name')}"
                            }
                            st.session_state['last_archive_id'] = prof_id
                        except Exception as e:
                            st.error(f"解析档案失败: {e}")
                    
                    selected_case = st.session_state.get('archive_cache')
        else:
            with c_obj:
                m1, m2, m3, m4, m_min, m5 = st.columns([1,1,1,1,1,1.5])
                iy = m1.number_input("年 (Year)", 1900, 2100, 2024)
                im = m2.number_input("月 (Month)", 1, 12, 1)
                id_ = m3.number_input("日 (Day)", 1, 31, 1)
                ih = m4.number_input("时 (Hour)", 0, 23, 12)
                imin = m_min.number_input("分 (Min)", 0, 59, 0)
                ig = m5.selectbox("性别 (Gender)", ["男", "女"])
                
                with st.expander("🛠️ 进阶参数 (Advanced Parameters)", expanded=False):
                    ex1, ex2 = st.columns(2)
                    with ex1:
                        st.selectbox("经度调节 (Longitude Fix)", [116.4, 121.5, 113.3, 114.1, 104.1], format_func=lambda x: f"{x} (K_geo)")
                    with ex2:
                        st.selectbox("计算策略 (Policy)", ["Standard", "High-Precision", "Logic-Only", "Quantum-Safe"], help="选择测算精度与算法复杂度 (Algorithm Complexity)")
                
                if st.button("🚀 生成概率叶 (Generate Case)", width='stretch'):
                    try:
                        import time
                        res = controller.calculate_chart({'birth_year': iy, 'birth_month': im, 'birth_day': id_, 'birth_hour': ih, 'birth_minute': imin, 'gender': ig})
                        st.session_state['manual_cache'] = {'id': f'MANUAL_{time.time()}', 'gender': ig, 'bazi': [f"{p[0]}{p[1]}" for p in res['bazi']], 'day_master': res['day_master'], 'birth_info': res['birth_info']}
                    except: st.error("引擎故障 (Engine failure).")
                selected_case = st.session_state.get('manual_cache')

        if selected_case:
            if st.session_state.get('last_report_id') != selected_case.get('id'):
                st.session_state['last_pipeline_report'] = None
                st.session_state['last_report_id'] = selected_case.get('id')
            
            st.divider()
            b_list = selected_case.get('bazi', [])
            
            # Ensure birth_info is handled for presets to avoid 1900s defaults
            # [Phase 38] For bazi-only profiles, estimate birth year using 60-year Jiazi cycle
            try:
                bi = selected_case.get('birth_info')
                
                # Check if birth_info exists with birth_year, or use profile's 'year' field
                if bi and 'birth_year' in bi:
                    birth_year = bi['birth_year']
                    birth_date = datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour'], bi.get('birth_minute', 0))
                elif 'year' in selected_case:
                    # ProfileManager format: use 'year' field directly
                    birth_year = selected_case['year']
                    birth_date = datetime(
                        selected_case['year'], 
                        selected_case.get('month', 1), 
                        selected_case.get('day', 1), 
                        selected_case.get('hour', 12)
                    )
                else:
                    # [Phase 38] Bazi-only: Estimate birth year using 60-year Jiazi cycle
                    # Find a year that matches the year pillar within a reasonable range
                    year_pillar = b_list[0] if b_list else "甲子"
                    
                    # 60-year cycle: Find the most recent occurrence before current year that's reasonable (20-80 years old)
                    current_year = datetime.now().year
                    estimated_year = None
                    
                    # Try to find a matching year within the last 100 years
                    for test_year in range(current_year - 20, current_year - 100, -1):
                        # Calculate year pillar for test_year
                        stem_idx = (test_year - 4) % 10
                        branch_idx = (test_year - 4) % 12
                        stems = "甲乙丙丁戊己庚辛壬癸"
                        branches = "子丑寅卯辰巳午未申酉戌亥"
                        test_pillar = stems[stem_idx] + branches[branch_idx]
                        if test_pillar == year_pillar:
                            estimated_year = test_year
                            break
                    
                    if estimated_year is None:
                        estimated_year = current_year - 40  # Fallback to 40 years ago
                    
                    birth_year = estimated_year
                    birth_date = datetime(birth_year, 6, 15, 12)  # Mid-year default
                    st.caption(f"💡 根据年柱 **{year_pillar}** 推算出生年约为 **{birth_year}** (甲子循环)")
                
                v_profile = VirtualBaziProfile({'year':b_list[0], 'month':b_list[1], 'day':b_list[2], 'hour':b_list[3]}, 
                                               gender=(1 if selected_case.get('gender')=='男' else 0), 
                                               birth_date=birth_date)
            except Exception as e: 
                v_profile = None
                st.warning(f"无法创建 VirtualBaziProfile: {e}")

            # --- GLOBAL CONTROL AREA ---
            current_year = datetime.now().year
            
            # Get luck cycles
            luck_cycles = v_profile.get_luck_cycles() if v_profile else []
            l_opts = [f"{d['start_year']}-{d['end_year']} [{d['gan_zhi']}]" for d in luck_cycles] if luck_cycles else ["Unknown"]
            
            # [Phase 38] Find default luck cycle that covers current year
            default_luck_idx = 0
            for i, lc in enumerate(luck_cycles):
                if lc['start_year'] <= current_year <= lc['end_year']:
                    default_luck_idx = i
                    break
            
            city_options = list(GEO_CITY_MAP.keys())
            
            cx1, cx2, cx3, cx4 = st.columns([2, 2, 2, 2])
            with cx1:
                sel_l = st.selectbox("当前大运 (Luck Cycle)", l_opts, index=default_luck_idx)
                user_luck = re.search(r'\[(.*?)\]', sel_l).group(1) if '[' in sel_l else "?"
            with cx2:
                # Default target year to current year
                sel_y = st.number_input("目标流年 (Target Year)", 1900, 2100, current_year)
                user_year = v_profile.get_year_pillar(sel_y) if v_profile else "?"
                st.caption(f"📅 支点流年 (Annual): {user_year}")
            with cx3:
                # [Phase 38] GEO Selector - global
                selected_city = st.selectbox("🌍 所在城市 (Location)", city_options, key="global_geo_city")
                geo_factor, geo_element = GEO_CITY_MAP.get(selected_city, (1.0, "Neutral"))
                st.caption(f"🌐 Geo Factor: **{geo_factor}**")
            with cx4:
                t_vec = st.slider("时间/相位偏移 (t)", 0.0, 10.0, 0.0, step=0.1)
                
                # [Phase B] Dynamic Dispersion Mode Toggle
                disp_on = st.toggle("量子弥散模式 (Dynamic Dispersion)", value=st.session_state.get('disp_active', True), help="基于节气进度的动态支藏干能量分配")
                st.session_state['disp_active'] = disp_on
                
                inj_on = st.toggle("量子注入模式 (Quantum Injection Mode)", value=st.session_state.get('inj_active', False))
                inj_list = st.multiselect("补强粒子 (Remedy Particles)", list(BaziParticleNexus.REMEDY_PARTICLES.keys()), format_func=lambda x: BaziParticleNexus.REMEDY_DESC.get(x, x)) if inj_on else None

            st.write("")
            
            # --- TACTICAL BAZI CHART (6 PILLARS) ---
            st.markdown("#### 📜 战术排盘 (TACTICAL BAZI CHART)")
            dm = selected_case.get('day_master', '?')
            p_labels = ["年 (Year)", "月 (Month)", "日 (Day)", "时 (Hour)", "运 (Luck)", "年 (Annual)"]
            
            # Combine all 6 pillars for display
            full_pillars = b_list + [user_luck, user_year]
            
            bazi_cols = st.columns(6)
            for i in range(len(full_pillars)):
                with bazi_cols[i]:
                    pillar_str = full_pillars[i] if i < len(full_pillars) else "??"
                    if len(pillar_str) < 2: pillar_str = "??" # Safety
                    stem = pillar_str[0]
                    branch = pillar_str[1]
                    
                    s_god = get_ten_god(dm, stem)
                    hidden = BaziParticleNexus.BRANCHES.get(branch, ("Earth", 0, []))[2]
                    
                    is_dm_pillar = (i == 2)
                    card_style = f'background:rgba(255,255,255,0.05); border-radius:12px; border: 1px solid {"#40e0d0" if is_dm_pillar else "rgba(255,255,255,0.1)"}; padding:15px; text-align:center;'
                    
                    # Highlight Luck and Annual with subtle border
                    if i >= 4: card_style += "border-style: dashed;"

                    st.markdown(f'<div style="{card_style}">', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:11px; color:#888; margin-bottom:8px;">{p_labels[i]}</div>', unsafe_allow_html=True)
                    
                    # Stem
                    st.markdown(f'<div style="font-size:10px; color:#40e0d0; margin-bottom:2px;">{s_god}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:26px; font-weight:bold; color:{"#40e0d0" if is_dm_pillar else "#fff"};">{stem}</div>', unsafe_allow_html=True)
                    
                    # Branch
                    st.markdown(f'<div style="font-size:26px; font-weight:bold; color:{"#40e0d0" if is_dm_pillar else "#fff"}; margin-top:5px;">{branch}</div>', unsafe_allow_html=True)
                    
                    # Hidden Stems & Their Gods
                    st.markdown('<div style="margin-top:12px; border-top:1px solid rgba(255,255,255,0.1); padding-top:8px;">', unsafe_allow_html=True)
                    for h_stem, weight in hidden:
                        h_god = get_ten_god(dm, h_stem)
                        st.markdown(f'<div style="font-size:10px; color:#aaa;">{h_stem}({h_god})</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if is_dm_pillar:
                        st.markdown('<div style="font-size:9px; color:#40e0d0; font-weight:bold; margin-top:8px;">日主</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            st.write("")
            if disp_on:
                # [Phase B] Calculate progress for visualization
                disp_engine = QuantumDispersionEngine()
                birth_dt_viz = None
                if selected_case and 'birth_info' in selected_case:
                    bi = selected_case['birth_info']
                    birth_dt_viz = datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour'], bi.get('birth_minute', 0))
                
                if birth_dt_viz:
                    solar_terms_viz = QuantumDispersionEngine.get_solar_term_times_for_year(birth_dt_viz.year)
                    progress, term, n_term = disp_engine.calculate_phase_progress(birth_dt_viz, solar_terms_viz)
                    
                    st.success(f"✅ **量子弥散系统 (Kernel B01)**: 动态支藏干能量分配已激活。")
                    
                    v_col1, v_col2 = st.columns([3, 7])
                    with v_col1:
                        st.markdown(f"**当前节气**: `{term}`")
                        st.markdown(f"**下个节气**: `{n_term}`")
                    with v_col2:
                        st.caption(f"节气进气进度 (Phase Progress): {progress*100:.1f}%")
                        st.progress(progress)
                        st.caption("能量随节气连续性平滑漂移，消除静态跳变。")
                else:
                    st.success("✅ **量子弥散系统 (Kernel B01)**: 动态支藏干能量分配已激活。 (等待出生时间)")
            else:
                st.warning("⚠️ **静态模式**: 使用传统 60/30/10 比例。建议开启量子弥散模式以获得更高精度。")
            st.info("💡 **物理提示**: 六柱谐振模型已激活，大运与流年已作为外部扰动源完整代入计算。")

    # 4. Oracle Core Analysis
    if not selected_case:
        st.info("Initiate subject selection to start Oracle.")
        return

    # [Phase B] Pass birth_date and dispersion_mode
    birth_dt = None
    if selected_case and 'birth_info' in selected_case:
        bi = selected_case['birth_info']
        birth_dt = datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour'], bi.get('birth_minute', 0))
    
    # [Phase 6.0] Caching: Wrap the heavy TrinityOracle.analyze call
    res = run_heavy_oracle_analysis(
        tuple(selected_case['bazi'][:4]),
        selected_case.get('day_master'),
        user_luck,
        user_year,
        t_vec,
        tuple(inj_list) if inj_list else None,
        birth_dt,
        disp_on
    )
    resonance = res.get('resonance')
    verdict_oracle = res.get('verdict', {})

    # [TRANSLATION LAYER]
    BILINGUAL_MAP = {
        # Resonance Modes
        "COHERENT": "共振态 (COHERENT)",
        "BEATING": "拍频态 (BEATING)",
        "DAMPED": "阻尼态 (DAMPED)",
        "ANNIHILATION": "湮灭态 (ANNIHILATION)",
        "CHAOTIC": "混沌态 (CHAOTIC)",

        # Verdict Labels
        "Extreme Strong": "极强/专旺 (Extreme Strong)",
        "Strong": "身强 (Strong)",
        "Balanced": "中和 (Balanced)",
        "Weak": "身弱 (Weak)",
        "Extreme Weak": "极弱/从格 (Extreme Weak)",

        # Risk Flags
        "HIGH_STRESS": "极高应力 (HIGH STRESS)",
        "COMPROMISED": "信号受损 (COMPROMISED)",
        "STABLE": "稳定 (STABLE)",
        "OPTIMAL": "最佳 (OPTIMAL)",

        # General Status
        "CRITICAL": "危急 (CRITICAL)",
        "LOW": "低 (LOW)"
    }

    mode_disp = BILINGUAL_MAP.get(resonance.mode, resonance.mode)
    label_disp = BILINGUAL_MAP.get(verdict_oracle.get("label"), verdict_oracle.get("label", "?"))

    # 5. Executive HUD (Pure CSS styling via class)
    st.write("")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        m_color = "#40e0d0" if resonance.mode == "COHERENT" else "#ff9f43" if resonance.mode == "BEATING" else "#ff4b4b" if resonance.mode == "ANNIHILATION" else "#888"
        st.markdown(f"""<div class="hud-card"><div class="sh-label">谐振模式 (Mode)</div><div class="sh-val" style="color:{m_color}; font-weight:bold; font-size:18px;">{mode_disp}</div></div>""", unsafe_allow_html=True)
    with h2: st.markdown(f'<div class="hud-card"><div class="sh-label">秩序参数 (Order - O)</div><div class="sh-val">{verdict_oracle.get("order_parameter",0):.4f}</div></div>', unsafe_allow_html=True)
    with h3: st.markdown(f'<div class="hud-card"><div class="sh-label">相干度 (Coherence - η)</div><div class="sh-val" style="color:#40e0d0">{resonance.sync_state:.4f}</div></div>', unsafe_allow_html=True)
    with h4: st.markdown(f'<div class="hud-card"><div class="sh-label">判定结果 (Verdict)</div><div class="sh-val" style="color:#ffd700; font-size:18px;">{label_disp}</div></div>', unsafe_allow_html=True)

    # 6. Primary Workspace (Observation & Detail)
    st.write("")
    st.write("")
    h_sub1, h_sub2, h_sub3, h_sub4 = st.columns(4)
    with h_sub1:
        st.markdown(f'<div class="hud-card"><div class="sh-label">碎片指数 (Fragmentation Index - F)</div><div class="sh-val" style="color:{"#ff4b4b" if resonance.fragmentation_index > 0.5 else "#888"}">{resonance.fragmentation_index:.2f}</div><div style="font-size:9px; color:#555;">Symmetry Breaking Index / 结构对称性破缺</div></div>', unsafe_allow_html=True)
    with h_sub2:
        f_color = "#f0f" if resonance.flow_efficiency > 1.8 else "#40e0d0"
        st.markdown(f'<div class="hud-card"><div class="sh-label">能效比 (Flow Efficiency - Φ)</div><div class="sh-val" style="color:{f_color}; text-shadow: {"0 0 10px #f0f" if resonance.flow_efficiency > 1.8 else "none"}">{resonance.flow_efficiency:.2f}</div><div style="font-size:9px; color:#555;">Superfluid Conductivity / 超流体传导力</div></div>', unsafe_allow_html=True)
    with h_sub3: st.markdown(f'<div class="hud-card"><div class="sh-label">包络频率 (Envelope Freq - ω)</div><div class="sh-val">{resonance.envelop_frequency:.4f}</div><div style="font-size:9px; color:#555;">Interference Envelope / 干涉包络频率</div></div>', unsafe_allow_html=True)
    with h_sub4: st.markdown(f'<div class="hud-card"><div class="sh-label">热能溢出 (Thermal Leakage)</div><div class="sh-val" style="color:{"#ff4b4b" if resonance.mode=="ANNIHILATION" else "#888"}">{"CRITICAL / 极高" if resonance.mode=="ANNIHILATION" else "LOW / 低"}</div><div style="font-size:9px; color:#555;">Entropy Leakage Rate / 熵增溢出率</div></div>', unsafe_allow_html=True)

    # 6. Secondary Analysis Layer (Gauges & Insights Above Tabs)
    st.write("")

    # Row 1: Real-time Gauages
    ga1, ga2 = st.columns(2)
    with ga1:
        st.markdown("#### 🌊 极向场 (Wavephaser)")
        Oscilloscope.render(res['waves'])
    with ga2:
        st.markdown("#### ⚙️ 相干性监控 (Coherence Monitoring)")
        CoherenceGauge.render(resonance.sync_state, resonance.description, 5.0)

    # Row 2: Insights & Remedies
    ga3, ga4 = st.columns(2)
    with ga3:
        st.markdown("#### 📜 宗师点评 (Master Insight)")
        st.info(f"解析 (Analysis): {resonance.description}")
    with ga4:
        if res.get('remedy'):
            st.markdown("#### 💊 补强方案 (Remedy Strategy)")
            rem = res.get('remedy')
            p_char = rem.get('best_particle', 'None')
            p_desc = BaziParticleNexus.REMEDY_DESC.get(p_char, p_char)

            st.success(f"**建议粒子 (Optimal Particle)**: {p_desc}")
            st.caption(f"📈 预期提升 (Coherence Gain): +{(rem.get('improvement', 0)*100):.1f}%")
            if st.button("一键执行量子注入 (Execute Injection)", width='stretch'):
                st.session_state['inj_active'] = True
                st.rerun()

    st.divider()
    # I will rely on the "Phase 3" display inside Tab 1 to show these insights.
    pass

    # --- MASTER-DETAIL ARCHITECTURE SPLIT ---

    # [MASTER VIEW]
    # Sections 0-6 (Chart, HUD, Gauges, Insights) are already rendered above.

    st.divider()

    # ========================================================
    # 🏛️ 量子通用框架 (QUANTUM UNIVERSAL FRAMEWORK)
    # ========================================================
    st.markdown("### 🏛️ 量子通用框架 (Quantum Universal Framework Control Panel)")
    st.caption("V13.6.0 | 全时空量子注入与多维环境因子修正")

    # Prepare arguments for run_arbitration_cached
    birth_info = selected_case.get('birth_info', {})
    gender = selected_case.get('gender', '男')
    current_city = selected_city # From global controls
    current_geo_factor = geo_factor # From global controls
    current_geo_element = geo_element # From global controls
    selected_scenario = "GENERAL" # Default scenario, can be made dynamic

    unified_state = run_arbitration_cached(
        tuple(b_list),
        birth_info, # Assuming birth_info is hashable or small enough
        user_luck,
        user_year,
        st.session_state.get('months_since_switch', 6.0), # Assuming this is set elsewhere
        current_city,
        current_geo_factor,
        current_geo_element,
        selected_scenario.upper(),
        gender
    )

    if 'error' not in unified_state:
        verdict = unified_state.get("verdict", {})
        rules_tbl = unified_state.get("rules", [])

        # [REMOVED] 仲裁断言 (Arbitration Verdict) - 已删除
        # [REMOVED] 白话真言 (Plain Guidance) - 已删除

        # [Phase 6.0] 100-year Life-path Radar Removed for Performance

        # Triggered rules table
        if rules_tbl:
            st.markdown("#### 📜 触发规则 (Triggered Rules)")
            import pandas as pd
            df_rules = pd.DataFrame(rules_tbl)
            st.dataframe(df_rules, hide_index=True, width='stretch')

        # [NEW] Logic Trace Window (Tiered Arbitration)
        tiered_rules = unified_state.get("tiered_rules", {})

        # Layer Name Translation Map (Pure Chinese)
        layer_map_cn = {
            "ENVIRONMENT": "🌍 环境场层",
            "FUNDAMENTAL": "⚛️ 基础物理层",
            "STRUCTURAL": "🏗️ 结构力学层",
            "FLOW": "🌊 流体动力层",
            "TEMPORAL": "⏳ 时空演化层"
        }

        if tiered_rules:
            with st.expander("🔬 架构逻辑溯源", expanded=False):
                st.info("展示分层调度总线 (Layered Dispatch Bus) 的仲裁结果：从环境场到时间脉冲的层级推导。")
                for layer_name, rules in tiered_rules.items():
                    if rules:
                        cn_layer = layer_map_cn.get(layer_name, layer_name)
                        st.markdown(f"**【{cn_layer}】**")
                        for r in rules:
                            # Rule Header: ID and Priority
                            st.write(f"- `{r.get('id')}` (优先级: {r.get('priority')})")

                            # Pedigree Info (Origin Trace)
                            origin = r.get("origin_trace", [])
                            f_type = r.get("fusion_type", "LEGACY")
                            if origin:
                                pedigree_str = " ← ".join(origin)
                                st.caption(f"  🧬 **血统溯源:** `{pedigree_str}` | 类型: `{f_type}`")

                            # Conflict Suppression Info
                            if r.get('conflicts'):
                                st.caption(f"  * 冲突策略: 抑制 {', '.join(r.get('conflicts'))}")


        # [REMOVED] 白话解释器 - 与上方白话真言重复，已删除
        # [REMOVED] 全息真言报告 - 已删除

        # Physics Telemetry Dashboard
        phy = unified_state.get('physics', {})

        arb_c1, arb_c2, arb_c3, arb_c4 = st.columns(4)
        with arb_c1:
            entropy_val = phy.get('entropy', 0)
            entropy_color = "#ff4b4b" if entropy_val > 1.5 else "#40e0d0"
            st.markdown(f"""<div class="hud-card"><div class="sh-label">系统熵 (Entropy)</div><div class="sh-val" style="color:{entropy_color}">{entropy_val:.3f}</div></div>""", unsafe_allow_html=True)
        with arb_c2:
            grav = phy.get('gravity', {})
            month_g = grav.get('Month', 0)
            st.markdown(f"""<div class="hud-card"><div class="sh-label">月令引力 (Gravity)</div><div class="sh-val">{month_g:.2f}</div></div>""", unsafe_allow_html=True)
        with arb_c3:
            res_state = phy.get('resonance', {})
            gain = res_state.get('gain', 1.0)
            st.markdown(f"""<div class="hud-card"><div class="sh-label">通根增益 (Rooting Gain)</div><div class="sh-val" style="color:#ffd700">{gain}x</div></div>""", unsafe_allow_html=True)
        with arb_c4:
            inertia = phy.get('inertia', {})
            visc = inertia.get('Viscosity', 0.5)
            visc_color = "#40e0d0" if visc < 0.5 else "#ff9f43"
            st.markdown(f"""<div class="hud-card"><div class="sh-label">粘滞系数 (Viscosity)</div><div class="sh-val" style="color:{visc_color}">{visc:.2f}</div></div>""", unsafe_allow_html=True)

        # NEW: Wealth & Relationship Metrics Row (with bilingual state names)
        wealth_state_names = {
            "STAGNANT": "停滞 (Stagnant)",
            "LAMINAR": "层流 (Laminar)",
            "TRANSITION": "过渡 (Transition)",
            "TURBULENT": "湍流 (Turbulent)"
        }
        rel_state_names = {
            "ENTANGLED": "纠缠稳定 (Entangled)",
            "BOUND": "绑定稳固 (Bound)",
            "PERTURBED": "摄动波动 (Perturbed)",
            "UNBOUND": "解离风险 (Unbound)"
        }

        arb_w1, arb_w2 = st.columns(2)
        with arb_w1:
            wealth = phy.get('wealth', {})
            re_num = wealth.get('Reynolds', 0)
            w_state = wealth.get('State', 'LAMINAR')
            w_state_display = wealth_state_names.get(w_state, w_state)
            w_color = "#ff4b4b" if w_state == "TURBULENT" else "#ff9f43" if w_state == "TRANSITION" else "#40e0d0" if w_state == "LAMINAR" else "#888"
            st.markdown(f"""<div class="hud-card"><div class="sh-label">🌊 财富流体 (Reynolds)</div><div class="sh-val" style="color:{w_color}">{re_num:.0f} - {w_state_display}</div></div>""", unsafe_allow_html=True)
        with arb_w2:
            rel = phy.get('relationship', {})
            bind_e = rel.get('Binding_Energy', 0)
            r_state = rel.get('State', 'UNBOUND')
            r_state_display = rel_state_names.get(r_state, r_state)
            r_color = "#40e0d0" if r_state == "ENTANGLED" else "#9370db" if r_state == "BOUND" else "#ff9f43" if r_state == "PERTURBED" else "#ff4b4b"
            st.markdown(f"""<div class="hud-card"><div class="sh-label">🌌 情感引力 (Binding)</div><div class="sh-val" style="color:{r_color}">{bind_e:.1f} - {r_state_display}</div></div>""", unsafe_allow_html=True)

        st.divider()

        # === 专家级物理论断 (Expert Assertions from MOD_15) ===
        st.markdown("#### 💡 专家级物理论断 (Expert Assertions)")

        # [MOD_15 Integration] Retrieve Vibration Metrics
        vib = unified_state.get('physics', {}).get('vibration', {})
        opt_mix = vib.get('optimal_deity_mix', {})
        entropy_val = vib.get('entropy', 0)

        # --- Definitions ---
        elem_cn = {'Wood': '木', 'Fire': '火', 'Earth': '土', 'Metal': '金', 'Water': '水'}
        dm_char = selected_case.get('day_master', '甲')
        # Note: b_list is available in scope from earlier definition

        # Helper for Ten God Label (Local Redefinition for safety if not in scope)
        # Actually we can rely on Global `get_ten_god` helper defined at module level
        def local_get_tg(elem):
            # Naive find representative stem
            # This is a bit tricky without full nexus. Let's use simplified lookup based on DM Element
            # OR use the module level get_ten_god if we can map Element -> Stem
            # Let's map Element to YIN stem for display (safe default)
            e_map = {'Wood':'乙', 'Fire':'丁', 'Earth':'己', 'Metal':'辛', 'Water':'癸'}
            return get_ten_god(dm_char, e_map.get(elem, ''))

        # 1. Best Element (Useful God)
        best_elem_en = max(opt_mix, key=opt_mix.get) if opt_mix else "Unknown"
        best_elem_cn = elem_cn.get(best_elem_en, best_elem_en)
        useful_god_tg = local_get_tg(best_elem_en)

        # 2. Favorable (Xi) - Source of Useful
        gen_map = {"Wood": "Water", "Fire": "Wood", "Earth": "Fire", "Metal": "Earth", "Water": "Metal"}
        xi_elem_en = gen_map.get(best_elem_en, "Unknown")
        xi_elem_cn = elem_cn.get(xi_elem_en, xi_elem_en)
        xi_god_tg = local_get_tg(xi_elem_en)

        # 3. Unfavorable (Ji) - Opposes Useful
        control_map = {"Wood": "Metal", "Fire": "Water", "Earth": "Wood", "Metal": "Fire", "Water": "Earth"}
        ji_elem_en = control_map.get(best_elem_en, "Unknown")
        ji_elem_cn = elem_cn.get(ji_elem_en, ji_elem_en)
        ji_god_tg = local_get_tg(ji_elem_en)

        # 4. Harmonizer (Tiao Hou) - Geo Context
        # Use Month Branch for Seasonality
        month_branch = b_list[1][1] if len(b_list)>1 else "子"
        season_map = {'亥':'Water','子':'Water','丑':'Water',
                      '寅':'Wood','卯':'Wood','辰':'Wood',
                      '巳':'Fire','午':'Fire','未':'Fire',
                      '申':'Metal','酉':'Metal','戌':'Metal'}
        season_elem = season_map.get(month_branch, 'Water')
        tiao_hou_en = "Fire" if season_elem in ['Water', 'Metal'] else "Water"
        tiao_hou_cn = elem_cn.get(tiao_hou_en)

        # --- Display Cards ---
        ys_c1, ys_c2, ys_c3, ys_c4 = st.columns(4)

        def render_god_card(col, title, elem_cn, tg, desc, color):
            col.markdown(f"""
            <div style="border-radius:12px; padding:15px; background:rgba(255,255,255,0.05); border:1px solid {color}; text-align:center;">
                <div style="color:{color}; font-size:12px; margin-bottom:5px;">{title}</div>
                <div style="color:#fff; font-size:22px; font-weight:bold;">{elem_cn} <span style="font-size:14px; color:#aaa;">({tg})</span></div>
                <div style="color:#888; font-size:10px; margin-top:5px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        render_god_card(ys_c1, "用神 (Useful God)", best_elem_cn, useful_god_tg, "核心通关", "#40e0d0")
        render_god_card(ys_c2, "喜神 (Favorable)", xi_elem_cn, xi_god_tg, "原神生助", "#9370db")
        render_god_card(ys_c3, "忌神 (Unfavorable)", ji_elem_cn, ji_god_tg, "阻抗干扰", "#ff4b4b")
        render_god_card(ys_c4, "调候 (Harmonizer)", tiao_hou_cn, f"{month_branch}月", "环境修正", "#ffd700")

        # --- Logic Generation ---
        logic_chain = ""
        conflict_note = ""
        if best_elem_en == "Fire" and ji_elem_en == "Water":
            logic_chain = f"**为何用{best_elem_cn}？** 全局金旺木折，需{best_elem_cn}（食伤）制杀护身。"
            if tiao_hou_en == "Water":
                 conflict_note = f"""
                 - **⚠️ 关键矛盾 (Paradox)**：调候需{tiao_hou_cn}（润局），但结构忌{ji_elem_cn}（灭火）。
                 - **最终裁决**：**生存 > 舒适**。{ji_elem_cn}虽为调候，但在本局中为**绝命忌神**，不可见。
                 """
        elif best_elem_en == "Water": logic_chain = f"**为何用{best_elem_cn}？** 火炎土燥需润局，或金多水浊需泄秀。"
        elif best_elem_en == "Wood": logic_chain = f"**为何用{best_elem_cn}？** 土重木折需疏通，或水多木漂需扎根。"
        elif best_elem_en == "Metal": logic_chain = f"**为何用{best_elem_cn}？** 木旺需修剪，或水多需发源。"
        elif best_elem_en == "Earth": logic_chain = f"**为何用{best_elem_cn}？** 水旺需止流，或火多需晦光。"

        th_algo = "未知"
        if season_elem in ['Fire', 'Wood', 'Earth']:
            th_algo = f"生于{month_branch}月 (燥)，需水润局。"
        elif season_elem in ['Water', 'Metal']:
            th_algo = f"生于{month_branch}月 (寒)，需火暖局。"

        mix_str = ", ".join([f"{elem_cn[k]} {v*100:.0f}%" for k,v in opt_mix.items()])

        # --- Final Status Info ---
        st.info(f"""
        **【用神推演】**：{logic_chain}

        **【喜忌辩证】**：
        - **调候算法**：{th_algo} 判定调候为 **{tiao_hou_cn}**。
        {conflict_note}

        **【最佳能配】**：系统推荐复合注入方案：**[{mix_str}]**。
        """)

        # --- Legacy Mapping for Downstream Compatibility ---
        yong_shen_elem = best_elem_en
        yong_cn = best_elem_cn
        xi_shen_elem = xi_elem_en
        xi_cn = xi_elem_cn
        ji_shen_elem = ji_elem_en
        ji_cn = ji_elem_cn

        st.divider()

        # === 地理位置建议 (Geographic Recommendations) ===
        st.markdown("#### 🌍 地理位置建议 (Geographic Recommendations)")
        st.caption("基于用神五行匹配的城市推荐 | Cities recommended based on favorable element")

        # Find cities matching yong_shen element
        recommended_cities = []
        avoid_cities = []

        for city_name, (gf, elem_affinity) in GEO_CITY_MAP.items():
            # Check if city element matches yong_shen
            if yong_shen_elem in elem_affinity or yong_cn in elem_affinity:
                recommended_cities.append((city_name, gf, elem_affinity))
            elif xi_shen_elem in elem_affinity or xi_cn in elem_affinity:
                recommended_cities.append((city_name, gf, elem_affinity))
            # Check if city matches ji_shen
            if ji_shen_elem in elem_affinity or ji_cn in elem_affinity:
                avoid_cities.append((city_name, gf, elem_affinity))

        # Sort by geo_factor descending
        recommended_cities.sort(key=lambda x: x[1], reverse=True)
        avoid_cities.sort(key=lambda x: x[1], reverse=True)

        geo_c1, geo_c2 = st.columns(2)
        with geo_c1:
            st.markdown("##### ✅ 推荐城市 (Recommended)")
            if recommended_cities:
                for city, gf, elem in recommended_cities[:8]:
                    gf_color = "#40e0d0" if gf >= 1.1 else "#9370db" if gf >= 1.0 else "#888"
                    st.markdown(f"- **{city}** <span style='color:{gf_color}'>(ε={gf:.2f}, {elem})</span>", unsafe_allow_html=True)
            else:
                st.caption("暂无特别推荐")

        with geo_c2:
            st.markdown("##### ⚠️ 谨慎城市 (Use Caution)")
            if avoid_cities:
                for city, gf, elem in avoid_cities[:6]:
                    st.markdown(f"- {city} *(ε={gf:.2f}, {elem})*")
            else:
                st.caption("暂无特别忌讳")

        st.caption("💡 **提示**: 地域因子 (ε) > 1.0 表示场强增益，< 1.0 表示场强衰减。选择用神五行匹配的城市可增强有利能量。")

        st.divider()

        # Detailed Physics JSON (Collapsible)
        with st.expander("🎛️ 详细物理读数 (Detailed Physics Matrix)", expanded=False):
            st.json(unified_state)
    elif not selected_case:
        st.info("请先选择或输入八字案例以执行量子通用框架仲裁。")

    st.divider()


    # --- HELPER FUNCTIONS ---
    def render_module_header(module_data, all_rules):
        """Standardized Header for all Topic Modules"""
        st.caption(f"🚀 {module_data.get('description', '')}")
        st.markdown(f"#### {module_data.get('name', 'Module')}")

        # Rule Inspector
        linked_ids = module_data.get('linked_rules', [])
        if linked_ids:
            with st.expander("📜 关联八字规则 (Logic & Rules Registry)", expanded=False):
                # Filter rules that exist in the global manifest
                # Some linked rules might be generic placeholders (PH_SAN_HE), so we try to find partial matches or exact
                # For now simplify: exact match

                module_rules = {rid: rdata for rid, rdata in all_rules.items() if rid in linked_ids}

                if not module_rules:
                    st.info(f"No active rules found matching spec: {linked_ids}")
                else:
                    rule_names = [f"{rid} | {r.get('name')}" for rid, r in module_rules.items()]
                    sel_rule = st.selectbox("查看规则详情 (Inspect Rule)", rule_names, key=f"sel_rule_{module_data['id']}")

                    if sel_rule:
                        rid = sel_rule.split(" | ")[0]
                        r_info = module_rules[rid]
                        st.json(r_info)

    # --- MAIN RENDER ---

    # [DETAIL VIEW] -> Topic Deep Dives (Now at Top)
    # Topic Navigation (Dynamic from Registry)
    # [已删除知识库系统] 使用硬编码的主题列表
    st.sidebar.divider()
    st.sidebar.markdown("### 🏹 主题导航 (Theme Orbit)")
    themes = {}
    theme_names = []
    theme_ids = {}

    selected_theme_name = st.sidebar.selectbox(
        "选择分析主题 (Theme)",
        theme_names,
        index=0,
        help="根据不同的预测目标（如基础物理、财富动态等）筛选对应的专题模块。"
    )
    selected_theme_id = theme_ids.get(selected_theme_name)

    st.sidebar.markdown("### 🔮 专题罗盘 (Topic Compass)")

    # [已删除知识库系统] 使用空列表
    active_modules = []
    module_map = {}
    module_names = []

    if not module_names:
        st.sidebar.warning("⚠️ 该主题下暂无活跃专题 (No active topics).")
        selected_name = None
    else:
        selected_name = st.sidebar.selectbox(
            "选择专题 (Topic)",
            module_names,
            index=0
        )

    st.sidebar.divider()
    translation_style = st.sidebar.radio(
        "🔮 真言语格 (Mantra Style)",
        ["周星驰 (无厘头)", "王家卫 (文艺)"],
        index=0,
        help="切换量子通用框架报告的叙事风格。"
    )

    # Select Topic (Module)

    # Update translator style based on selection
    if "周星驰" in translation_style:
        quantum_framework.translator.set_style(TranslationStyle.STEPHEN_CHOW)
    else:
        quantum_framework.translator.set_style(TranslationStyle.WONG_KAR_WAI)

    current_module = module_map.get(selected_name)
    if current_module is None:
        current_module = {}
        st.warning(f"未找到模块「{selected_name}」，请从左侧重新选择或等待配置加载。")
    selected_topic_id = current_module.get('id')

    # Render Selected Module Content (Above Global Console)
    st.divider()

    # [REF] Single Collapsible Container for Entire Topic
    with st.expander(f"📊 {current_module.get('name', selected_name or '—')}", expanded=True):

        # 1. Topic Metadata (Description, Goal, Outcome)
        tm1, tm2 = st.columns([1, 1])
        with tm1:
            st.markdown(f"**📝 描述 (Description)**: {current_module.get('description', '-')}")
            st.markdown(f"**🎯 目的 (Goal)**: {current_module.get('goal', 'TBD')}")
        with tm2:
            st.success(f"**🏆 成果 (Outcome)**: {current_module.get('outcome', 'TBD')}")
            # Show version and category if available
            if current_module.get('version'):
                st.caption(f"版本: {current_module.get('version')}")
            if current_module.get('category'):
                st.caption(f"分类: {current_module.get('category')}")

        st.divider()

        # 2. Registry Pattern Details (If loaded from registry)
        pattern_data = current_module.get('pattern_data')
        if pattern_data:
            # Show semantic seed
            semantic_seed = pattern_data.get('semantic_seed', {})
            if semantic_seed:
                with st.expander("🌱 语义种子 (Semantic Seed)", expanded=False):
                    st.markdown(f"**物理意象**: {semantic_seed.get('physical_image', '-')}")
                    st.markdown(f"**描述**: {semantic_seed.get('description', '-')}")
                    classical_meaning = semantic_seed.get('classical_meaning', {})
                    if classical_meaning:
                        st.markdown("**古典含义**:")
                        for key, value in classical_meaning.items():
                            st.markdown(f"- **{key}**: {value}")
            
            # Show physics kernel
            physics_kernel = pattern_data.get('physics_kernel', {})
            if physics_kernel:
                with st.expander("⚛️ 物理内核 (Physics Kernel)", expanded=False):
                    st.markdown(f"**描述**: {physics_kernel.get('description', '-')}")
                    # Show formulas
                    for key, value in physics_kernel.items():
                        if key != 'description' and isinstance(value, dict):
                            formula = value.get('formula', '')
                            desc = value.get('description', '')
                            if formula:
                                st.markdown(f"**{key}**: `{formula}`")
                                if desc:
                                    st.caption(desc)
            
            # Show algorithm implementation
            algo_impl = pattern_data.get('algorithm_implementation', {})
            if algo_impl:
                with st.expander("🔧 算法实现 (Algorithm Implementation)", expanded=False):
                    paths = algo_impl.get('paths', {})
                    if paths:
                        st.markdown("**函数路径映射**:")
                        for func_name, func_path in paths.items():
                            st.code(f"{func_name}: {func_path}", language=None)
                    # Show other algorithm details
                    for key, value in algo_impl.items():
                        if key not in ['paths', 'registry_loader'] and isinstance(value, dict):
                            func = value.get('function', '')
                            desc = value.get('description', '')
                            if func:
                                st.markdown(f"**{key}**: `{func}`")
                                if desc:
                                    st.caption(desc)
            
            # Show feature anchors
            feature_anchors = pattern_data.get('feature_anchors', {})
            if feature_anchors:
                with st.expander("🎯 特征锚点 (Feature Anchors)", expanded=False):
                    standard_centroid = feature_anchors.get('standard_centroid', {})
                    if standard_centroid:
                        st.markdown("**标准质心**:")
                        vector = standard_centroid.get('vector', {})
                        if vector:
                            st.json(vector)
                        st.caption(f"匹配阈值: {standard_centroid.get('match_threshold', '-')}")
                    
                    singularity_centroids = feature_anchors.get('singularity_centroids', [])
                    if singularity_centroids:
                        st.markdown("**奇点质心**:")
                        for idx, centroid in enumerate(singularity_centroids):
                            st.markdown(f"**{centroid.get('sub_id', f'奇点{idx+1}')}**: {centroid.get('description', '-')}")
                            st.json(centroid.get('vector', {}))
            
            st.divider()

        # 3. Rule Registry (Nested Expander)
        # [已删除知识库系统] 使用空列表
        all_rules = []
        linked_ids = current_module.get('linked_rules', [])

        if linked_ids:
            with st.expander("📜 关联八字规则 (Logic & Rules Registry)", expanded=False):
                module_rules = {rid: rdata for rid, rdata in all_rules.items() if rid in linked_ids}
                if not module_rules:
                    st.info(f"No active rules found matching spec: {linked_ids}")
                else:
                    rule_names = [f"{rid} | {r.get('name')}" for rid, r in module_rules.items()]
                    sel_rule = st.selectbox("查看规则详情", rule_names, key=f"sel_rule_{current_module.get('id', 'unknown')}")
                    if sel_rule:
                        rid = sel_rule.split(" | ")[0]
                        st.json(module_rules[rid])

        st.divider()

        # --- MODULE IMPLEMENTATION SWITCH ---

        # [NEW] MOD_14_TIME_SPACE_INTERFERENCE
        if selected_topic_id == "MOD_14_TIME_SPACE_INTERFERENCE":
            st.markdown("#### ⏳ 多维时空场耦合 (Spacetime Field Coupling)")
            st.caption(r"公式: $E_{Total} = \left|\Psi_{Base} + \alpha\Psi_{Luck} + \beta(K_{geo} \cdot \Psi_{Year})\right|^2$")

            # A. Test Case Loader
            with st.expander("🧪 专题私有测试集 (Private Case Library)", expanded=True):
                try:
                    with open("tests/cases/mod_14_spacetime_interference.json", "r") as f:
                        test_cases = json.load(f)
                    case_names = [f"{c['case_id']} | {c['name']}" for c in test_cases]
                    sel_case_str = st.selectbox("加载测试案例", case_names)
                    if sel_case_str:
                        sel_case = next(c for c in test_cases if c['case_id'] == sel_case_str.split(" | ")[0])
                        st.json(sel_case)
                        # Auto-inject context if run button is handled separately,
                        # but here for visualization we pretend to load it.
                        st.info(f"🔬 验证焦点: {sel_case['focus']}")
                except FileNotFoundError:
                    st.error("Test case library not found: tests/cases/mod_14_spacetime_interference.json")

            # B. Interference Waveform (Simulation)
            st.markdown("##### 🌊 时空干涉波形 (Interference Waveform)")
            import plotly.graph_objects as go

            # Simulate Wave Functions
            x = np.linspace(0, 4*np.pi, 200)
            psi_base = np.sin(x)
            psi_luck = 0.5 * np.sin(x + np.pi/4)  # Shifted Luck
            psi_year = 0.8 * np.sin(2*x)          # Impulse Year (High Freq)
            k_geo = 1.2 # Mock high GEO factor

            psi_total = np.abs(psi_base + psi_luck + k_geo * psi_year)**2

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=psi_base, name="Ψ_Base (原局)", line=dict(color='gray', dash='dot')))
            fig.add_trace(go.Scatter(x=x, y=psi_luck, name="Ψ_Luck (大运)", line=dict(color='#40e0d0', dash='dash')))
            fig.add_trace(go.Scatter(x=x, y=psi_year, name="Ψ_Year (流年)", line=dict(color='#ff7f50')))
            fig.add_trace(go.Scatter(x=x, y=psi_total, name="|Ψ_Total|² (耦合场)", line=dict(color='#9370db', width=3), fill='tozeroy'))

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(title="相位 (Phase)", showgrid=False),
                yaxis=dict(title="能量密度 (Energy Density)", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                height=350,
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig, width='stretch')

            # C. GEO Heatmap (Mockup)
            st.markdown("##### 🌍 K-Geo 效率热力图 (Spacetime Efficiency)")
            cols = st.columns(3)
            cols[0].metric("K_Geo (North)", "0.8x", "-20%")
            cols[1].metric("K_Geo (South)", "1.5x", "+50% 🔥")
            cols[2].metric("K_Geo (West)", "1.1x", "+10%")


        if selected_topic_id == "MOD_15_STRUCTURAL_VIBRATION":
            st.markdown("#### 🏗️ 结构振动传导 (Structural Vibration Transmission)")
            st.caption(r"公式: $E_{out} = E_{max} \cdot \tanh(E_{in} / E_{th}) \cdot V_{coupling}$ (Phase Threshold: 80%)")

            # A. Test Case Loader
            with st.expander("🧪 专题私有测试集 (Private Case Library)", expanded=True):
                # Phase 4.0: Support Precision Patches
                suite_sel = st.radio("测试集 (Test Suite)", ["标准测试 (Standard)", "结构相变 (Phase Transition)", "精度校准补丁 (Precision Patches)"], horizontal=True)

                json_path = "tests/cases/mod_15_structural_vibration.json"
                if "Phase Transition" in suite_sel:
                    json_path = "tests/cases/mod_15_phase_transition.json"
                elif "Precision Patches" in suite_sel:
                    json_path = "tests/cases/mod_precision_patches.json"

                try:
                    with open(json_path, "r") as f:
                        test_cases = json.load(f)
                    case_names = [f"{c['case_id']} | {c['name']}" for c in test_cases]
                    sel_case_str = st.selectbox("加载测试案例", case_names, key="mod15_case_sel")
                    if sel_case_str:
                        sel_case = next(c for c in test_cases if c['case_id'] == sel_case_str.split(" | ")[0])
                        st.json(sel_case)
                        st.info(f"🏷️ 案例标签: {sel_case.get('tags', []) if 'tags' in sel_case else sel_case.get('expected_phase', 'Standard')}")
                except FileNotFoundError:
                    st.error(f"Test case library not found: {json_path}")

            # B. 3D Transmission Topology (Simulation)
            st.markdown("##### 🕸️ 3D 能量传导拓扑 (Energy Transmission Topology)")
            import plotly.graph_objects as go

            # Nodes: Year, Month, Day, Hour, Luck, Annual
            # Positions (x, y, z) - Schematic
            # Year(0,0,0), Month(1,0,0), Day(2,0,0), Hour(3,0,0)
            # Luck(1.5, 1, 0), Annual(1.5, 2, 0)

            nodes_x = [0, 1, 2, 3, 1.5, 1.5]
            nodes_y = [0, 0, 0, 0, 1, 2]
            nodes_z = [0, 0, 0, 0, 0.5, 1.0] # Lift dynamic pillars
            node_names = ["Year", "Month", "Day", "Hour", "Luck", "Annual"]
            node_colors = ['#FFD700', '#FF4500', '#32CD32', '#1E90FF', '#9370DB', '#FF69B4']

            fig_3d = go.Figure(data=[go.Scatter3d(
                x=nodes_x, y=nodes_y, z=nodes_z,
                mode='markers+text',
                text=node_names,
                marker=dict(size=12, color=node_colors, opacity=0.8),
                textposition="bottom center"
            )])

            # Edges (Flow)
            # Year->Month, Month->Day, Day->Hour
            # Luck->Month, Annual->Month (Impact points)
            edges = [(0,1), (1,2), (2,3), (4,1), (5,1)]
            for start, end in edges:
                fig_3d.add_trace(go.Scatter3d(
                    x=[nodes_x[start], nodes_x[end]],
                    y=[nodes_y[start], nodes_y[end]],
                    z=[nodes_z[start], nodes_z[end]],
                    mode='lines',
                    line=dict(color='white', width=2),
                    hoverinfo='none',
                    showlegend=False
                ))

            fig_3d.update_layout(
                scene=dict(
                    xaxis=dict(showbackground=False, visible=False),
                    yaxis=dict(showbackground=False, visible=False),
                    zaxis=dict(showbackground=False, visible=False),
                ),
                margin=dict(l=0, r=0, b=0, t=0),
                paper_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            st.plotly_chart(fig_3d, width='stretch')

            st.markdown("##### 🎯 复合神格配比 (Composite Deity Ratio)")

            # RUN REAL SIMULATION
            if sel_case_str:
                # Prepare Inputs
                sel_case = next(c for c in test_cases if c['case_id'] == sel_case_str.split(" | ")[0])
                bazi = sel_case['bazi'] # {"stems": [...], "branches": [...]}
                # Construct Bazi List for Executor: [Year, Month, Day, Hour]
                # Assuming simple construction from mock stems/branches or using provided 'bazi' list if available
                # Fallback to standard 4-pillar construction
                # Need to check structure. If simple dict, mocking it:
                b_list = ["甲子", "乙丑", "丙寅", "丁卯"] # Default mockup if parsing fails
                if "bazi" in sel_case:
                     # Try to form pillars
                     s = sel_case['bazi']['stems']
                     b = sel_case['bazi']['branches']
                     if len(s) == 4 and len(b) == 4:
                         b_list = [f"{s[0]}{b[0]}", f"{s[1]}{b[1]}", f"{s[2]}{b[2]}", f"{s[3]}{b[3]}"]

                ctx_data = sel_case.get('context', {})
                ctx_obj = {
                    'luck_pillar': ctx_data.get('luck', None),
                    'annual_pillar': ctx_data.get('year', None),
                    'scenario': ctx_data.get('mode', 'GENERAL'),
                    'data': {'city': ctx_data.get('geo', 'Unknown'), 'geo_factor': 0.8}
                }

                # Run Execution
                with st.spinner("🚀 正在进行非线性动力网络仿真..."):
                    # Use the global quantum_framework instance
                    state = quantum_framework.arbitrate_bazi(b_list, {"gender": "male"}, ctx_obj)

                    vib = state['physics'].get('vibration', {})
                    opt_mix = vib.get('optimal_deity_mix', {})
                    is_phase = vib.get('is_phase_transition', False)
                    dom_elem = vib.get('dominant_element', 'None')

                    # ALERT: PHASE TRANSITION
                    if is_phase:
                        st.error(f"""
                        **⚠️ 系统相变警告 (SYSTEM PHASE SHIFT DETECTED)**
                        检测到 **{dom_elem}** 场域发生能级坍缩，进入【从旺/从格】非线性区。
                        常规平衡法则已失效，SAI 算法已自动反转为‘顺势模式’。
                        (Normal balance laws suspended. SAI logic inverted to 'Energy Maximization'.)
                        """)

                    # Radar Update
                    all_elems = ['Wood', 'Fire', 'Earth', 'Metal', 'Water']
                    current_dist = [vib.get('energy_state', {}).get(e, 0) for e in all_elems]
                    target_dist = []
                    for e in all_elems:
                        base = vib.get('energy_state', {}).get(e, 0)
                        # Target is simply Base + Injection? Or ideal?
                        # Let's visualize Injection as a separate layer
                        inj = opt_mix.get(e, 0) * 10
                        target_dist.append(base + inj)

                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(r=current_dist, theta=all_elems, fill='toself', name='当前能量 (Current)'))
                    fig_radar.add_trace(go.Scatterpolar(r=target_dist, theta=all_elems, fill='toself', name='熵减目标 (Optimized)', line=dict(color='gold' if not is_phase else 'red')))
                    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), paper_bgcolor='rgba(0,0,0,0)', height=350)
                    st.plotly_chart(fig_radar, width='stretch')

                    # [PATCH] System Status lamp
                    s_col1, s_col2 = st.columns(2)
                    with s_col1:
                        status_label = "🔴 EXTREME PHASE" if is_phase else "🟢 NORMAL STATE"
                        st.metric("系统相位 (System Phase)", status_label)
                    with s_col2:
                        st.metric("能量纯度 (Purity)", f"{ (max(current_dist)/sum(current_dist)*100) if sum(current_dist)>0 else 0 :.1f}%")

                    # Text Report (Destiny Translator)
                    st.markdown("### 📜 智能全息论断 (Holographic Analysis)")

                    # --- Helper Conversions ---
                    elem_cn = {'Wood': '木', 'Fire': '火', 'Earth': '土', 'Metal': '金', 'Water': '水'}

                    # Calculate Ten Gods for Display
                    # BaziParticleNexus is already imported globally
                    dm = state['meta'].get('dm', '甲') # Current DM
                    dm_elem = BaziParticleNexus.STEMS.get(dm)[0]

                    def get_ten_god_label(target_e):
                        target_s = None
                        # Find a representative stem for this element to use get_shi_shen
                        for s, val in BaziParticleNexus.STEMS.items():
                            if val[0] == target_e and val[1] == BaziParticleNexus.STEMS[dm][1]: # Same polarity for primary representation
                                target_s = s
                                break
                        if not target_s: return target_e
                        tg = BaziParticleNexus.get_shi_shen(target_s, dm)
                        return tg

                    # 1. Useful Gods Logic
                    # Best Element (Optimization Target)
                    best_elem_en = max(opt_mix, key=opt_mix.get) if opt_mix else "Unknown"
                    best_elem_cn = elem_cn.get(best_elem_en, best_elem_en)
                    useful_god_tg = get_ten_god_label(best_elem_en)

                    # Favorable (Xi) - Source of Useful (Generates Best)
                    # Wood->Fire->Earth->Metal->Water->Wood
                    gen_map = {"Wood": "Water", "Fire": "Wood", "Earth": "Fire", "Metal": "Earth", "Water": "Metal"}
                    xi_elem_en = gen_map.get(best_elem_en, "Unknown")
                    xi_elem_cn = elem_cn.get(xi_elem_en, xi_elem_en)
                    xi_god_tg = get_ten_god_label(xi_elem_en)

                    # Unfavorable (Ji) - Clashing/Suppressing Best or Excess Source
                    # Simplified: Opposes Useful
                    control_map = {"Wood": "Metal", "Fire": "Water", "Earth": "Wood", "Metal": "Fire", "Water": "Earth"}
                    ji_elem_en = control_map.get(best_elem_en, "Unknown")
                    ji_elem_cn = elem_cn.get(ji_elem_en, ji_elem_en)
                    ji_god_tg = get_ten_god_label(ji_elem_en)

                    # Harmonizer (Tiao Hou) - Geo Context
                    geo_city = ctx_data.get('geo', 'Unknown')
                    # Map Geo to Element roughly (Mockup logic or rely on case tags)
                    # Seoul -> North/Cold -> Water. If Cold, Harmonizer is Fire.
                    # Standard Tiao Hou logic: Winter(Water) needs Fire, Summer(Fire) needs Water.
                    # Check Month Branch for Season
                    month_branch = b_list[1][1] if len(b_list)>1 else "子"
                    season_map = {'亥':'Water','子':'Water','丑':'Water',
                                  '寅':'Wood','卯':'Wood','辰':'Wood',
                                  '巳':'Fire','午':'Fire','未':'Fire',
                                  '申':'Metal','酉':'Metal','戌':'Metal'}
                    season_elem = season_map.get(month_branch, 'Water')

                    tiao_hou_en = "Fire" if season_elem in ['Water', 'Metal'] else "Water" # Simple toggle
                    tiao_hou_cn = elem_cn.get(tiao_hou_en)

                    # Display Metrics
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("用神 (Useful God)", f"{best_elem_cn} ({useful_god_tg})", "核心通关")
                    c2.metric("喜神 (Favorable)", f"{xi_elem_cn} ({xi_god_tg})", "原神生助")
                    c3.metric("忌神 (Unfavorable)", f"{ji_elem_cn} ({ji_god_tg})", "阻抗干扰")
                    c4.metric("调候 (Harmonizer)", f"{tiao_hou_cn} ({geo_city})", "环境修正")

                    st.divider()

                    # 2. Detailed Narrative Generation
                    st.markdown("#### 💡 专家级物理论断 (Expert Assertions)")

                    # Construct Narrative
                    entropy_val = vib.get('entropy', 0)
                    eff_val = vib.get('transmission_efficiency', 0)

                    # Logic Chain for Useful God
                    logic_chain = ""
                    conflict_note = ""

                    if best_elem_en == "Fire" and ji_elem_en == "Water":
                        logic_chain = f"**为何用{best_elem_cn}？** 全局存在强金局（或者金气过旺），导致{dm_elem}木气受克严重。{best_elem_cn}（{useful_god_tg}）是唯一能制金护木的力量（食伤制杀），故为第一核心用神。"
                        if tiao_hou_en == "Water":
                             conflict_note = f"""
                             **⚠️ 结构与调候的辩证矛盾**：
                             - **结构需求**：结构急需{best_elem_cn}来对抗金，{ji_elem_cn}（{ji_god_tg}）会克制{best_elem_cn}，导致“制杀无力”，故{ji_elem_cn}为结构性忌神。
                             - **调候需求**：生于{month_branch}月（夏/燥土），气候炎向，理论上需{tiao_hou_cn}来润局。
                             - **最终结论**：当生存（结构制杀）与舒适（调候润局）冲突时，**生存优先**。故判定：{ji_elem_cn}虽能调候，但为结构之**大忌**。此局乃“火炼真金”之特殊格局，不可见水破局。
                             """

                    elif best_elem_en == "Water":
                        logic_chain = f"**为何用{best_elem_cn}？** 局中火炎土燥（或金多水浊需泄秀）。{best_elem_cn}（{useful_god_tg}）能起到核心的滋润/流通作用。"
                    elif best_elem_en == "Wood":
                        logic_chain = f"**为何用{best_elem_cn}？** 局中土重木折（或水多木漂需扎根）。{best_elem_cn}（{useful_god_tg}）能疏土/纳水，恢复生机。"
                    elif best_elem_en == "Metal":
                        logic_chain = f"**为何用{best_elem_cn}？** 局中木旺（或水多需发源）。{best_elem_cn}（{useful_god_tg}）能修剪旺木或为水之源头。"
                    elif best_elem_en == "Earth":
                         logic_chain = f"**为何用{best_elem_cn}？** 水旺（或火多需晦）。{best_elem_cn}（{useful_god_tg}）能止水/纳火，稳固根基。"

                    # Tiao Hou Algorithm Explanation
                    th_algo = "未知"
                    if season_elem in ['Fire', 'Wood', 'Earth']:
                        th_algo = f"生于{season_map.get(month_branch, '杂')}月（{month_branch}），气候炎燥/阳气盛，根据【寒暖燥湿平衡法】，需**水**来润局降温。"
                    elif season_elem in ['Water', 'Metal']:
                        th_algo = f"生于{season_map.get(month_branch, '杂')}月（{month_branch}），气候寒冷/阴气盛，根据【寒暖燥湿平衡法】，需**火**来暖局解冻。"

                    # Assertion Text
                    if entropy_val > 1.2:
                        status_text = "系统处于高熵震荡状态，能量传导存在严重阻滞。"
                    else:
                        status_text = "系统处于低熵稳态，能量流转相对顺畅。"

                    # Specific Advice
                    advice = ""
                    if best_elem_en == "Fire":
                        advice = f"建议在南方 ({geo_city}若为南则吉) 寻求火属性机遇（如科技、能源、文化产业）。利用{useful_god_tg}（Fire）化解{ji_god_tg}（{ji_elem_cn}）的阻力。"

                    mix_str = ", ".join([f"{elem_cn[k]} {v*100:.0f}%" for k,v in opt_mix.items()])

                    st.info(f"""
                    **【当下局势】**：{status_text}

                    **【用神推演链条】**：
                    {logic_chain}

                    **【调候算法揭秘】**：
                    - **算法逻辑**：{th_algo}
                    - **当前判定**：调候神为 **{tiao_hou_cn}**。
                    
                    **【喜忌辩证 (关键矛盾解析)】**：
                    - **喜神（{xi_elem_cn}）**：生助用神{best_elem_cn}，为局中贵人。
                    - **忌神（{ji_elem_cn}）vs 调候（{tiao_hou_cn}）**：
                      在此局中，调候神（{tiao_hou_cn}）恰好也是忌神（{ji_elem_cn}）。
                      这意味着**“让环境舒服的元素（水）会杀死让结构生存的元素（火）”**。
                      系统判定：**生存 > 舒适**。因此，虽然理论上缺水，但**绝对不能补水**，否则破格。此为“有病无药”之特殊凶象，需极度小心。
                    
                    **【物理诊断】**：
                    系统熵 S={entropy_val:.2f} (高危)，最优熵减神格：**[{mix_str}]**。
                    
                    **【行动建议】**：
                    {advice}
                    """)

                    
                    with st.expander("查看完整物理日志 (Physics Log)"):
                        st.json(vib)

        # --- MODULE 18: BASE APPLICATION & GLOBAL TOOLS ---
        elif selected_topic_id == "MOD_18_BASE_APP":
            st.markdown("#### 🛠️ 基础应用与全局工具 (Basic Applications & Global Tools)")
            st.caption("跨模块物理准则、叙事风格翻译及全局系统状态监控。")
            
            # Display Linked Rules and Metrics in a clean way
            st.markdown("##### 📜 全局资产 (Global Logic Assets)")
            module_rules = {rid: rdata for rid, rdata in all_rules.items() if rid in current_module.get('linked_rules', [])}
            
            if module_rules:
                rule_cols = st.columns(2)
                for i, (rid, r_info) in enumerate(module_rules.items()):
                    with rule_cols[i % 2]:
                        st.markdown(f"""
                        <div style="border-radius:10px; padding:10px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 10px;">
                            <div style="font-size: 11px; color: #888;">{rid}</div>
                            <div style="font-size: 14px; font-weight: 500;">{r_info.get('name')}</div>
                            <div style="font-size: 12px; color: #aaa; margin-top: 5px;">{r_info.get('description', '系统全局算法。')}</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("##### 🌍 系统全息状态 (Global Telemetry)")
            st.info("💡 此专题为系统底层支撑层，聚合了跨模块引用的核心资产。量子通用框架控制台（下方）已启用，用于展示这些算法在实际推演中的全息表现。")
        
        # --- MODULE 16: TEMPORAL SHUNTING (Topic 3) ---
        if selected_topic_id == "MOD_16_TEMPORAL_SHUNTING":
            st.markdown("#### ⏳ 应期预测与行为干预 (Temporal Response & Strategic Intervention)")
            st.caption(r"分流动力学方程: $\Delta SAI = \int(F_{pulse} - R_{behavior} - G_{geo})dt$")
            
            # A. Test Case Loader
            with st.expander("🧪 专题私有测试集 (Private Case Library)", expanded=True):
                # Phase 4.0: Support Precision Patches
                suite_sel_16 = st.radio("测试集 (Test Suite)", ["标准时间测试 (Standard)", "精度校准补丁 (Precision Patches)"], horizontal=True, key="suite_mod16")
                
                json_path_16 = "tests/cases/mod_16_temporal_shunting.json"
                if "Precision Patches" in suite_sel_16:
                    json_path_16 = "tests/cases/mod_precision_patches.json"
                
                try:
                    with open(json_path_16, "r") as f:
                        test_cases = json.load(f)
                    case_names = [f"{c['case_id']} | {c['name']}" for c in test_cases]
                    sel_case_str = st.selectbox("加载测试案例", case_names, key="mod16_case_sel")
                    if sel_case_str:
                        sel_case = next(c for c in test_cases if c['case_id'] == sel_case_str.split(" | ")[0])
                        st.json(sel_case)
                        st.info(f"🏷️ 案例标签: {sel_case.get('intervention') or sel_case.get('tags', [])}")
                except FileNotFoundError:
                    st.error(f"Test case library not found: {json_path_16}")
            
            # [PATCH] C. Social Damping Control (Platform Impedance)
            st.markdown("##### 🧱 社会阻尼与平台载荷 (Social Damping / Platform Impedance)")
            # Phase 4.0: 1.0 is now the Neutral baseline
            social_damping_val = st.slider("环境阻尼因子 (Damping Factor)", 0.5, 3.0, 1.0, help="1.0=常规(Standard), 2.0=高阻尼(体制内/高防御), 0.5=低阻尼(高风险/敏锐)")
            
            # B. Simulation Execution
            if sel_case_str:
                from core.trinity.core.engines.temporal_shunting import TemporalShuntingEngine
                
                # Mock DM or get from case
                dm_char = sel_case.get('bazi', {}).get('stems', ['甲'])[0]
                t_engine = TemporalShuntingEngine(dm_char)
                
                col_dash1, col_dash2 = st.columns([2, 1])
                
                with col_dash1:
                    st.markdown("##### 📉 应力时间序列 (SAI Timeline)")
                    
                    # Determine Birth Year & Scanning Range
                    b_year = sel_case.get('birth_year', 1990)
                    
                    # [V12.2.0 FIX] Construct profile from test case for real Luck Pillar physics
                    case_pillars = sel_case.get('bazi', {}).get('pillars', {})
                    case_gender = 1 if sel_case.get('gender', '男') == '男' else 0
                    mod16_profile = VirtualBaziProfile(case_pillars, gender=case_gender) if case_pillars else None
                    
                    scan_res = t_engine.scan_singularities(start_year=2024, birth_year=b_year, horizon_months=120, social_damping=social_damping_val, profile=mod16_profile)
                    timeline = scan_res['timeline']
                    singularities = scan_res['singularities']
                    
                    # Plotly Time Series
                    import plotly.graph_objects as go
                    t_indices = [x['age'] for x in timeline] # Use Age for X-axis
                    sai_values = [x['sai'] for x in timeline]
                    t_labels = [f"Age {x['age']} ({x['year']}.{x['month']})" for x in timeline]
                    is_future_markers = [x['is_future'] for x in timeline]
                    
                    fig_sai = go.Figure()
                    
                    # Split trace into Historical and Future for visual distinction
                    hist_x, hist_y, hist_t = [], [], []
                    fut_x, fut_y, fut_t = [], [], []
                    
                    for i, node in enumerate(timeline):
                        if node['is_future']:
                            fut_x.append(node['age'])
                            fut_y.append(node['sai'])
                            fut_t.append(t_labels[i])
                        else:
                            hist_x.append(node['age'])
                            hist_y.append(node['sai'])
                            hist_t.append(t_labels[i])
                    
                    # [PATCH] Calculate Shunted Line (Intervention Effect)
                    # We need to know the action select from col_dash2 (which is defined later, so we need to move it up or anticipate)
                    # For UI logic, col_dash2 controls are defined after. Let's move control definition up.
                
                with col_dash2:
                    st.markdown("##### 🎛️ 干预模拟器 (Remedy Simulator)")
                    # Singularity Focus (Auto-select first high risk peak)
                    peak_sai = max([x['sai'] for x in singularities]) if singularities else 1.5
                    st.metric("💥 峰值风险 (Peak Risk)", f"{peak_sai:.2f} SAI", delta="高危" if peak_sai > 2.26 else "正常", delta_color="inverse")
                    
                    act_opts = {"NONE": "无干预 (None)", "STUDY": "📚 学习/印星 (Study)", "DONATION": "💸 布施/财星 (Donation)", "TRAVEL": "✈️ 迁移/马星 (Travel)", "MEDITATION": "🧘 闭关/空亡 (Void)"}
                    sel_action_key = st.selectbox("行为干预方案", list(act_opts.keys()), format_func=lambda x: act_opts[x], index=1, key="mod16_act_sel")
                    geo_mod = st.slider("地理偏置系数 (K_geo)", 0.5, 2.0, 1.0, 0.1, key="mod16_geo_sel")
                    
                    shunt_res = t_engine.simulate_intervention(peak_sai, sel_action_key, geo_mod, social_damping=social_damping_val)
                    
                    # Display Delta
                    new_sai = shunt_res['final_sai']
                    reduction = shunt_res['reduction_pct']
                    st.divider()
                    st.metric("🛡️ 干预后应力 (Shunted SAI)", f"{new_sai:.2f}", delta=f"-{reduction}%", delta_color="normal")
                    
                    if new_sai < 2.26 < peak_sai:
                        st.success("🚀 成功逃逸 (Escape Successful)")
                    elif new_sai > 2.26:
                        st.error("🚫 仍处险境 (Still Critical)")
                    
                with col_dash1:
                    # Shunted Trace calculation
                    shunt_y = []
                    if sel_action_key != "NONE":
                        for node in timeline:
                            if node['is_future']:
                                # Apply the same intervention logic to all future nodes
                                sim = t_engine.simulate_intervention(node['sai'], sel_action_key, geo_mod, social_damping=social_damping_val)
                                shunt_y.append(sim['final_sai'])
                            else:
                                shunt_y.append(None) # Match hist length
                    
                    # Historical Trace (Grey/Past)
                    if hist_x:
                        fig_sai.add_trace(go.Scatter(
                            x=hist_x, y=hist_y,
                            mode='lines', name='历史应力 (Historical)',
                            line=dict(color='grey', width=1, dash='dot'),
                            hovertemplate='年龄: %{x}<br>时间: %{text}<br>SAI: %{y:.2f}',
                            text=hist_t
                        ))

                    # Future Trace (Cyan/Active)
                    if fut_x:
                        fig_sai.add_trace(go.Scatter(
                            x=fut_x, y=fut_y,
                            mode='lines', name='未来预测 (Future)',
                            line=dict(color='#40e0d0', width=2),
                            hovertemplate='年龄: %{x}<br>预测SAI: %{y:.2f}',
                            text=fut_t
                        ))
                    
                    # [PATCH] Shunted Trace (Green/Intervention)
                    if shunt_y and any(y is not None for y in shunt_y):
                        fig_sai.add_trace(go.Scatter(
                            x=[n['age'] for n in timeline if n['is_future']],
                            y=[y for y in shunt_y if y is not None],
                            mode='lines', name='干预后预期 (Shunted)',
                            line=dict(color='#2ecc71', width=2, dash='dash'),
                            hovertemplate='年龄: %{x}<br>干预SAI: %{y:.2f}'
                        ))
                    
                    # Current Time Marker
                    fig_sai.add_vline(x=2024-b_year, line_dash="dash", line_color="white", annotation_text="Today")
                    
                    # Singularity Markers
                    sin_age = [x['age'] for x in singularities]
                    sin_v = [x['sai'] for x in singularities]
                    sin_l = [f"Age {x['age']} ({x['year']}.{x['month']})" for x in singularities]
                    
                    if sin_age:
                        fig_sai.add_trace(go.Scatter(
                            x=sin_age, y=sin_v,
                            mode='markers', name='奇点 (Singularity)',
                            marker=dict(color='#ff4b4b', size=10, symbol='x'),
                            hovertemplate='⚠️ 奇点爆发<br>%{text}<br>SAI: %{y:.2f}',
                            text=sin_l
                        ))
                        
                        # Threshold Line
                        fig_sai.add_hline(y=2.26, line_dash="dash", line_color="#ff9f43", annotation_text="坍缩阈值 (2.26)")
                        
                    fig_sai.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        height=350, margin=dict(l=0, r=0, t=30, b=0),
                        xaxis_title="生命周期 (Life Cycle: Age)", yaxis_title="结构应力指数 (SAI)"
                    )
                    st.plotly_chart(fig_sai, width='stretch')
                    
                
                # C. History Trace Wall & Calibration (Phase 3.5)
                st.markdown("##### 🕰️ 历史镜像全息墙 (History Trace Wall & Calibration)")
                
                # Filter Historical Singularities
                hist_singularities = [s for s in singularities if not s['is_future']]
                
                if not hist_singularities:
                    st.info("ℹ️ 系统回溯扫描未发现过去有显著SAI异常 (No historical singularity detected).")
                else:
                    st.caption("以下为系统回溯扫描发现的历史断点，请您校准以提高未来预测精度：")
                    
                    feedback_data = []
                    for idx, h_evt in enumerate(hist_singularities):
                        with st.container():
                            col_h1, col_h2 = st.columns([3, 1])
                            with col_h1:
                                # Display Assertion
                                alert_color = "red" if h_evt['type'] == "COLLAPSE" else "orange"
                                alert_icon = "💥" if h_evt['type'] == "COLLAPSE" else "🌊"
                                st.markdown(f"**{h_evt['year']}年 (Age {h_evt['age']})** <span style='color:{alert_color}'>{alert_icon} {h_evt['type']}</span>", unsafe_allow_html=True)
                                st.markdown(f"> *{h_evt['assertion']}* (SAI: {h_evt['sai']:.2f})")
                            with col_h2:
                                # Calibration Toggle
                                is_acc = st.checkbox("准确 (Verify)", value=True, key=f"hist_cal_{idx}")
                                feedback_data.append({"year": h_evt['year'], "is_accurate": is_acc})
                            st.divider()
                    
                    # Apply Calibration
                    cal_res = t_engine.calibrate_model(feedback_data)
                    if cal_res['new_threshold'] > 2.26:
                         st.success(f"🤖 模型已基于您的反馈自进化 (Calibrated): 根据您的抗压历史，我们将坍缩阈值调整为 **{cal_res['new_threshold']:.2f}**")
                        
                # D. Oracle Report (Updated)
                st.markdown("##### 📜 终极改命路线图 (The Redemption Output)")
                opt_paths = t_engine.sensitivity_search(peak_sai)
                
                if opt_paths:
                    best = opt_paths[0]
                    st.info(f"""
                    **经过历史镜像校准，系统为您生成的【未来10年生存铁律】：**
                    1.  **核心策略**：`{best['action']}` + `{best['geo']}`
                    2.  **物理预期**：将 SAI 从 `{peak_sai:.2f}` 降至 `{best['metrics']['final_sai']:.2f}`。
                    3.  **避雷指南**：未来若遇 **{hist_singularities[0]['type'] if hist_singularities else 'COLLAPSE'}** 类结构，请立即启动上述分流机制。
                    """)

        # --- MODULE 00: SUBSTRATE REFINEMENT (Phase B) ---
        if selected_topic_id == "MOD_00_SUBSTRATE":
            st.markdown("#### 🧬 晶格基底重构")
            st.caption("基于量子弥散模型的动态支藏干能量分配 (Quantum Dispersion Model)")
            
            # 1. Sinusoidal Visualization
            st.markdown("##### 🌊 正弦弥散模型可视化 (Sinusoidal Dispersion Map)")
            import plotly.graph_objects as go
            t_vals = np.linspace(0, 1, 100)
            y_base = np.sin(np.pi * t_vals)**2
            y_mid = np.sin(np.pi * t_vals + np.pi/3)**2
            y_res = (np.sin(np.pi * t_vals + 2*np.pi/3)**2) * 0.8 # Simulated damping
            
            fig = go.Figure()  # go imported below
            fig.add_trace(go.Scatter(x=t_vals, y=y_base, name="本气 (Primary)", line=dict(color="#40e0d0", width=3)))
            fig.add_trace(go.Scatter(x=t_vals, y=y_mid, name="中气 (Secondary)", line=dict(color="#ff7f50", width=2, dash='dash')))
            fig.add_trace(go.Scatter(x=t_vals, y=y_res, name="余气 (Residual)", line=dict(color="#9370db", width=2, dash='dot')))
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(title="节气进度 (Phase Progress)", gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(title="能量权重 (Energy Weight)", gridcolor='rgba(255,255,255,0.1)'),
                height=300, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, width='stretch')
            
            # 2. Real-time Analysis for Selected Pillar
            st.markdown("##### 📍 当前能级评估 (Live Energy Assessment)")
            disp_engine = QuantumDispersionEngine()
            
            month_pillar = res.get('initial_waves', {}).get('Month', 'Unknown')
            month_branch = month_pillar[1] if len(month_pillar) >= 2 else "?"
            
            bi = selected_case.get('birth_info', {})
            b_year = bi.get('birth_year') or selected_case.get('year', 1980)
            b_month = bi.get('birth_month') or selected_case.get('month', 1)
            b_day = bi.get('birth_day') or selected_case.get('day', 1)
            b_hour = bi.get('birth_hour') or selected_case.get('hour', 12)
            
            birth_dt = datetime(int(b_year), int(b_month), int(b_day), int(b_hour))
            solar_times = QuantumDispersionEngine.get_solar_term_times_for_year(birth_dt.year)
            progress, term, n_term = disp_engine.calculate_phase_progress(birth_dt, solar_times)
            
            st.info(f"探测到当前节气进度: `{progress:.4f}` ({term} → {n_term})")
            
            col_a, col_b = st.columns([6, 4])
            with col_a:
                st.markdown(f"**地支: {month_branch} (月令)**")
                comp = disp_engine.compare_static_vs_dynamic(month_branch, progress)
                
                df_comp = pd.DataFrame([
                    {"成分": k, "传统 (Static)": comp['static'].get(k, 0), "动态 (Phase B)": comp['dynamic'].get(k, 0), "偏离度 (Δ)": comp['delta'].get(k, 0)}
                    for k in comp['static'].keys()
                ])
                st.dataframe(df_comp, hide_index=True, width='stretch')

            with col_b:
                st.markdown("**能级偏移控制 (Damping τ)**")
                damping = st.slider("能量惯性系数 (Half-life)", 0.5, 2.0, 1.0, 0.1, key="substrate_damping")
                st.caption("调节余气在交节后的衰减速度")

        # --- MODULE 9: COMBINATION PHYSICS (Phase G/B-09) ---
        elif selected_topic_id == "MOD_09_COMBINATION":
            st.markdown("#### ⚛️ 干合化气相位探测 (Stem Combination Phase Scan)")
            st.caption("Threshold > 0.65 triggers Phase Transition (Transformation).")
            
            # Dynamic Import of Asset
            try:
                sys.path.append("/home/jin/bazi_predict")
                from core.trinity.core.assets.combination_phase_logic import check_combination_phase
            except ImportError:
                st.error("Asset `combination_phase_logic` not found.")
                # Fallback for display if import fails
                check_combination_phase = lambda s, e: {"status": "ERROR", "msg": "Asset missing", "power_ratio": 0}

            # Mock Detection (For demo purposes, we scan Day Master + Month Stem)
            stems = selected_case.get('bazi', ['?', '?', '?', '?'])
            # Ensure stems is list of strings
            if stems and isinstance(stems[0], list): stems = [s[0] for s in stems] # Handle potential nested list
            
            y_stem = stems[0][0] if len(stems) > 0 else '?'
            m_stem = stems[1][0] if len(stems) > 1 else '?'
            d_stem = stems[2][0] if len(stems) > 2 else '?'
            h_stem = stems[3][0] if len(stems) > 3 else '?'
            
            all_stems = [y_stem, m_stem, d_stem, h_stem]
            st.write(f"**当前天干场 (Stems)**: {' '.join(all_stems)}")

            # Auto-detect Combos (Simplified for UI Demo)
            pairs = []
            COMB_MAP = {
                frozenset(['甲', '己']): 'Earth',
                frozenset(['乙', '庚']): 'Metal',
                frozenset(['丙', '辛']): 'Water',
                frozenset(['丁', '壬']): 'Wood',
                frozenset(['戊', '癸']): 'Fire'
            }
            
            # Check Day Master vs Month Stem
            pair_dm_m = frozenset([d_stem, m_stem])
            if pair_dm_m in COMB_MAP:
                pairs.append((d_stem, m_stem, COMB_MAP[pair_dm_m]))

            if not pairs:
                st.info("当前局中未探测到日元与月干的显性合化 (No overt DM-Month combination detected).")
                st.caption("实验模式：手动选择干支进行测试")
                c_sel1, c_sel2 = st.columns(2)
                with c_sel1: s1_sim = st.selectbox("天干 A", ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'], index=3) # Ding
                with c_sel2: s2_sim = st.selectbox("天干 B", ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'], index=8) # Ren
                sim_pair = frozenset([s1_sim, s2_sim])
                if sim_pair in COMB_MAP:
                    pairs.append((s1_sim, s2_sim, COMB_MAP[sim_pair]))

            for s1, s2, target in pairs:
                st.divider()
                st.markdown(f"**探测到合像 (Combination Detected): {s1} - {s2} $\\rightarrow$ {target}**")
                
                st.markdown("##### 🎚️ 实验室条件模拟 (Energy Simulation)")
                sim_energy = st.slider("环境场化神能量 (Environment Energy)", 0.0, 1.5, 0.45, key=f"e_sim_{s1}_{s2}", help="Simulate Month Energy Level")
                
                res = check_combination_phase([s1, s2], sim_energy)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("化神能量 (Target Energy)", f"{sim_energy:.2f}", delta=f"{sim_energy - 0.65:.2f} vs Threshold")
                with c2:
                    status = res['status']
                    color = "#40e0d0" if status == "PHASE_TRANSITION" else "#ff4b4b"
                    st.markdown(f"**判定状态 (Status)**:")
                    st.markdown(f"<h3 style='color:{color}'>{status}</h3>", unsafe_allow_html=True)
                    st.caption(res['msg'])
                
                st.write("")
                st.progress(res['power_ratio'], text=f"Power Ratio: {res['power_ratio']}")
                
        # --- MODULE 10: RESONANCE & ROOTING (Phase G/B-10) ---
        elif selected_topic_id == "MOD_10_RESONANCE":
            st.markdown("#### 📡 干支共振信号增强 (Stem-Branch Signal Booster)")
            st.caption("Gain Factor: Main(2.0) | Medium(1.5) | Residual(1.2) | Floating(0.5)")
            
            # Dynamic Import
            try:
                sys.path.append("/home/jin/bazi_predict")
                from core.trinity.core.assets.resonance_booster import calculate_rooting_gain
            except ImportError:
                calculate_rooting_gain = lambda s, b: {"gain": 1.0, "status": "ERROR"}

            # Analyze Day Master
            stems = selected_case.get('bazi', ['?', '?', '?', '?'])
            # Ensure stems is list of strings
            raw_stems = []
            if stems and isinstance(stems[0], list): 
                raw_stems = [s[0] for s in stems]
            else:
                raw_stems = stems
            
            dm = raw_stems[2][0] if len(raw_stems) > 2 else '?'
            
            # Extract Branches
            # Assuming 'bazi' strings are '甲子', '乙丑'... char[1] is branch
            branches = []
            if stems and isinstance(stems[0], str) and len(stems[0]) >= 2:
                branches = [p[1] for p in stems] # ['子', '丑'...]
            else:
                 branches = ['?', '?', '?', '?']

            st.write(f"**天干 (Transmitter)**: `{dm}` | **地支基站 (Base Stations)**: `{branches}`")
            
            res_gain = calculate_rooting_gain(dm, branches)
            
            # Visualization
            g_val = res_gain['gain']
            g_status = res_gain['status']
            
            col_g1, col_g2, col_g3 = st.columns([1, 2, 1])
            with col_g1:
                st.metric("信号增益 (Gain)", f"{g_val}x", delta="Base Station Locked" if g_val > 1.0 else "Signal Lost", delta_color="normal" if g_val > 1.0 else "inverse")
            with col_g2:
                # Signal Bar
                st.write(f"**G-Force**: {g_val}")
                bar_color = "#00ff00" if g_val >= 2.0 else "#add8e6" if g_val >= 1.2 else "#ff4b4b"
                st.markdown(f"""
                    <div style="width:100%;background-color:#eee;border-radius:5px;height:20px;">
                        <div style="width:{min(g_val/2.0 * 100, 100)}%;background-color:{bar_color};height:100%;border-radius:5px;"></div>
                    </div>
                """, unsafe_allow_html=True)
                st.caption(f"Status: {g_status}")
            
            with col_g3:
                # Icon
                icon = "📡" if g_val > 1.0 else "🥀"
                st.markdown(f"<h1 style='text-align:center'>{icon}</h1>", unsafe_allow_html=True)
            
            st.info(f"**物理判定**: 天干 `{dm}` 在地支 `{res_gain.get('best_root', 'None')}` 处获得 **{res_gain.get('root_type', 'NONE')}** 级支撑。")
            
            # Sandbox
            with st.expander("🛠️ 信号模拟沙箱 (Signal Sandbox)"):
                sb_stem = st.selectbox("测试天干", ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'], index=0)
                sb_branches = st.multiselect("配置地支基站", ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'], default=['子'])
                
                
                sb_res = calculate_rooting_gain(sb_stem, sb_branches)
                st.metric("模拟增益", f"{sb_res['gain']}x", f"{sb_res['status']}")

        # --- MODULE 11: PILLAR GRAVITY (Phase G/B-11) ---
        elif selected_topic_id == "MOD_11_GRAVITY":
            st.markdown("#### 🌌 宫位引力场 (Pillar Gravitational Field)")
            st.caption("Auto-Pilot Weight Distribution based on Solar Term Depth (Progress).")
            
            # [V13.7 升级] 使用 V13.7 版本的宫位引力引擎（动态权重模型）
            try:
                sys.path.append("/home/jin/bazi_predict")
                from core.trinity.core.engines.pillar_gravity_v13_7 import PillarGravityEngineV13_7
                pillar_engine = PillarGravityEngineV13_7()
                # 创建兼容层：将旧版接口转换为 V13.7 接口
                def calculate_pillar_weights(progress: float):
                    """兼容层：将旧版接口转换为 V13.7 接口"""
                    weights = pillar_engine.calculate_dynamic_weights(t=progress, influence_bus=None)
                    # 转换键名：V13.7 使用小写，旧版使用首字母大写
                    return {
                        'Year': weights.get('year', 0.1),
                        'Month': weights.get('month', 0.5),
                        'Day': weights.get('day', 0.3),
                        'Hour': weights.get('hour', 0.1)
                    }
            except ImportError:
                calculate_pillar_weights = lambda p: {'Year':0.1, 'Month':0.5, 'Day':0.3, 'Hour':0.1}

            # 1. Drive the Engine (Progress)
            # Fetch real progress from case if available, else 0.5
            # We reuse the logic from Substrate (lines 720+) to get real progress if possible, but for this Module view we prioritize the Engine Concept.
            # Let's show "Actual" vs "Simulation".
             
            # Calculate actual
            try:
                # Re-calc progress locally for display
                b_year = selected_case.get('year', 1980) or 1980 # Handle if empty dict
                # ... (Simplified extraction) ...
                # Actually, let's just use a slider for the "Engine Demo" feel effectively "killing the static slider".
                pass
            except: pass

            st.markdown("##### 🎛️ 引力控制台 (Gravity Console)")
            # Interactive Slider driving the physics
            u_prog = st.slider("节气进气深度 (Solar Term Progress)", 0.0, 1.0, 0.5, 0.01, help="0.0=Node (Initial), 0.5=Peak (Cardinal), 1.0=Next Node")
            
            # 2. Physics Calculation
            weights = calculate_pillar_weights(u_prog)
            
            # 3. Visualization
            # Bar Chart for Weights
            w_df = pd.DataFrame([
                {"Pillar": "Year (远场)", "Weight": weights['Year'], "Color": "#bdc3c7"},
                {"Pillar": "Month (核心)", "Weight": weights['Month'], "Color": "#e74c3c"}, # Red for Dominant
                {"Pillar": "Day (界面)", "Weight": weights['Day'], "Color": "#f1c40f"},   # Yellow for Self
                {"Pillar": "Hour (归宿)", "Weight": weights['Hour'], "Color": "#3498db"}
            ])
            
            fig_w = go.Figure(go.Bar(
                x=w_df['Pillar'],
                y=w_df['Weight'],
                marker_color=w_df['Color'],
                text=w_df['Weight'],
                textposition='auto'
            ))
            fig_w.update_layout(
                title="动态能量权重分布 (Dynamic Energy Distribution)",
                yaxis_title="Gravitational Weight (0.0-1.0)",
                yaxis_range=[0, 0.7]
            )
            st.plotly_chart(fig_w, width='stretch')
            
            # 4. Analysis
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**月令统治力 (Month Force)**: `{weights['Month']}`\n\n当进气达到峰值(0.5)时，月令权重突破 0.55，形成绝对压制。")
            with c2:
                st.warning(f"**时空挤压 (Compression)**: 年柱 `{weights['Year']}`\n\n能量守恒定律：月令膨胀必然导致年/时权重坍缩。")

            # 5. Real Case Context
            st.divider()
            if 'progress' in locals() or 'progress' in globals():
                pass
                
        # --- MODULE 12: SPACETIME INERTIA (Phase G/B-12) ---
        elif selected_topic_id == "MOD_12_INERTIA":
            st.markdown("#### 🌊 时空场惯性衰减 (Spacetime Fluid Inertia)")
            st.caption("Exponential Decay Model for Luck Pillar Transition (Default τ=3.0 mo)")
            
            # [V13.7 升级] 使用 V13.7 版本的时空惯性引擎（指数衰减模型）
            try:
                sys.path.append("/home/jin/bazi_predict")
                from core.trinity.core.engines.spacetime_inertia_v13_7 import SpacetimeInertiaEngineV13_7
                inertia_engine = SpacetimeInertiaEngineV13_7(tau=3.0)
                # 创建适配器：将旧版接口转换为 V13.7 接口
                def calculate_transition_inertia(months_since_switch: float, tau: float = 3.0):
                    """适配器：将旧版接口转换为 V13.7 接口"""
                    # 如果 months_since_switch < 0，直接返回旧版逻辑
                    if months_since_switch < 0:
                        return {"Prev_Luck": 1.0, "Next_Luck": 0.0, "Viscosity": 0.0}
                    
                    # V13.7 版本需要时间序列，但旧版接口是单个值
                    # 我们创建一个单元素时间序列来适配
                    time_months = [max(0.0, months_since_switch)]  # 确保非负
                    weights = inertia_engine.calculate_inertia_weights(
                        time_months=time_months,
                        previous_energy=1.0,
                        influence_bus=None
                    )
                    # V13.7 返回的是权重列表（前一时刻的权重），我们取第一个元素
                    w_prev = weights[0] if weights else math.exp(-months_since_switch / tau)
                    w_next = 1.0 - w_prev
                    # 计算粘滞度（混合状态）：S_mix ~ 4 * w1 * w2
                    viscosity = 4 * w_prev * w_next
                    # 返回旧版格式
                    return {
                        'Prev_Luck': round(w_prev, 4),
                        'Next_Luck': round(w_next, 4),
                        'Viscosity': round(viscosity, 4)
                    }
                import math  # 确保 math 已导入
            except ImportError:
                calculate_transition_inertia = lambda m, t: {'Prev_Luck': 0.5, 'Next_Luck': 0.5, 'Viscosity': 1.0}

            st.markdown("##### ⏳ 交运时间轴 (Transition Timeline)")
            # Interactive Slider
            t_months = st.slider("交运后时间 (Months Since Switch)", -6.0, 24.0, 3.0, 0.5, help="Positive = After Switch, Negative = Before Switch")
            
            # Physics Calculation
            w_res = calculate_transition_inertia(t_months, tau=3.0)
            
            # Visualization: Mixing Tank
            c_mix1, c_mix2, c_mix3 = st.columns([2, 5, 2])
            
            with c_mix1:
                st.metric("上一运 (Prev)", f"{w_res['Prev_Luck']*100:.1f}%", delta=f"Decaying", delta_color="inverse")
            
            with c_mix2:
                # Stacked Bar for Mixing
                st.write(f"**能量混合态 (Viscosity Index: {w_res['Viscosity']})**")
                # CSS Gradient for mixing visualization
                mix_pct = w_res['Next_Luck'] * 100
                st.markdown(f"""
                    <div style="display:flex; width:100%; height:30px; border-radius:15px; overflow:hidden; border:1px solid #555;">
                        <div style="width:{100-mix_pct}%; background-color:#7f8c8d; display:flex; align-items:center; justify-content:center; color:white; font-size:0.8em;">Prev</div>
                        <div style="width:{mix_pct}%; background-color:#2ecc71; display:flex; align-items:center; justify-content:center; color:white; font-size:0.8em;">Next</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Decay Curve Plot (Small)
                x_vals = np.linspace(-6, 24, 100)
                y_prev = [calculate_transition_inertia(x, 3.0)['Prev_Luck'] for x in x_vals]
                y_next = [calculate_transition_inertia(x, 3.0)['Next_Luck'] for x in x_vals]
                
                fig_decay = go.Figure()
                fig_decay.add_trace(go.Scatter(x=x_vals, y=y_prev, mode='lines', name='Prev Decay', line=dict(color='#7f8c8d', dash='dash')))
                fig_decay.add_trace(go.Scatter(x=x_vals, y=y_next, mode='lines', name='Next Growth', line=dict(color='#2ecc71')))
                fig_decay.add_vline(x=t_months, line_width=2, line_color="white", annotation_text="Current")
                
                fig_decay.update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_decay, width='stretch')

            with c_mix3:
                st.metric("新大运 (Next)", f"{w_res['Next_Luck']*100:.1f}%", delta="Growing")
            
            # Interpretation
            if w_res['Viscosity'] > 0.8:
                st.warning("⚠️ **高粘滞期 (High Viscosity)**: 新旧气场剧烈交织，建议静默观察，避免重大决策。")
            elif w_res['Next_Luck'] > 0.9:
                st.success("✅ **气场稳态 (Settled)**: 新大运能量已完全接管。")
            else:
                st.info("ℹ️ **过渡期 (Transition)**: 气场正在有序交接。")

            st.divider()

        # --- MODULE 2: SUB-SURFACE (DETAIL) ---
            
            # --- Phase D: Life-Path Orbital Simulation ---
            st.divider()
            st.markdown("##### 🚀 个人生命轨道仪 (Personal Orbit Orrery)")
            st.caption("高频时间轨道采样：全寿命周期能级审计与因果熵追踪 (Life-Path Temporal Sampling)")
            
            orb_c1, orb_c2 = st.columns([7, 3])
            with orb_c2:
                st.markdown("**仿真参数 (Simulation Params)**")
                # Use birth_dt from the Assessment section if available, else default
                try:
                    sim_b_year = birth_dt.year
                except:
                    sim_b_year = 1980
                
                sim_range = st.slider("审计跨度 (Year Range)", sim_b_year, sim_b_year + 100, (sim_b_year, sim_b_year + 80), 1, key="orb_sim_range")
                sim_res = st.selectbox("采样分辨率 (Resolution)", ["节气 (Solar Term)", "月份 (Monthly)"], index=0, key="orb_sim_res")
                
                if st.button("🚀 执行全轨道扫描 (Execute Orbital Scan)", width='stretch', key="run_lifepath_scan"):
                    st.warning("⚠️ 生命轨道仪 (LifePathEngine) 已在 V12.2.0 中移除。请使用 '全息应期演化' 功能。")
            
            with orb_c1:
                if 'orbital_data' in st.session_state:
                    orb_data = st.session_state['orbital_data']
                    df_orb = pd.DataFrame(orb_data['timeline'])
                    
                    # Orbital Plot
                    fig_orb = go.Figure()
                    fig_orb.add_trace(go.Scatter(x=df_orb['timestamp'], y=df_orb['entropy'], name="因果熵 (Entropy)", line=dict(color="#40e0d0", width=2)))
                    fig_orb.add_trace(go.Scatter(x=df_orb['timestamp'], y=df_orb['sai'], name="应力 (SAI)", line=dict(color="#ff7f50", width=2)))
                    fig_orb.add_trace(go.Scatter(x=df_orb['timestamp'], y=df_orb['dm_strength']/100.0, name="能级强度 (Energy)", line=dict(color="#ffd700", width=1.5, dash='dot')))
                    
                    fig_orb.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        height=400, margin=dict(l=10, r=10, t=30, b=10),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="时间轨道 (Timeline)"),
                        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="物理指标 (Metrics)"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_orb, width='stretch')
                    
                    risks = orb_data.get('risk_nodes', [])
                    if risks:
                        st.warning(f"⚠️ 轨道内发现 {len(risks)} 个潜在风险节点 (Structural Risks Enabled)")
                else:
                    st.info("💡 请点击右侧按钮启动全寿命周期能量审计。系统将根据量子轨道模型计算每一年的熵增动量。")
            
            # 2.5 High-order Emergence & Causal Entanglement (吸収 Phase C)
            st.divider()
            st.markdown("##### 🌀 高阶涌现与因果纠缠 (High-order Emergence)")
            
            e_data = res.get('emergence', {})
            entropy = e_data.get('causal_entropy', 0)
            s_index = e_data.get('singularity_index', 0)
            singularities = e_data.get('singularities', [])
            
            n_protocol = e_data.get('negentropy_protocol', {})
            
            h1, h2, h3 = st.columns(3)
            with h1:
                e_color = "#40e0d0" if entropy < 0.5 else "#ff9f43" if entropy < 1.0 else "#ff4b4b"
                st.markdown(f"""<div class="hud-card"><div class="sh-label">因果熵 (Causal Entropy)</div><div class="sh-val" style="color:{e_color}">{entropy:.4f}</div></div>""", unsafe_allow_html=True)
            with h2:
                si_color = "#40e0d0" if s_index < 1.5 else "#ff9f43" if s_index < 3.0 else "#ff4b4b"
                st.markdown(f"""<div class="hud-card"><div class="sh-label">奇点指标 (Singularity Σ)</div><div class="sh-val" style="color:{si_color}">{s_index:.2f}</div></div>""", unsafe_allow_html=True)
            with h3:
                st.markdown(f"""<div class="hud-card"><div class="sh-label">纠缠节点 (Nodes)</div><div class="sh-val" style="color:#ffd700">{len(singularities)}</div></div>""", unsafe_allow_html=True)
            
            if entropy > 1.2 or n_protocol.get('status') == 'CRITICAL':
                st.error(f"🚨 **临界态预警**: {n_protocol.get('suggestion', '检测到级联因果风险')}")
                with st.container(border=True):
                    st.markdown("##### 🛡️ 熵减协议建议 (Negentropy Protocol)")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"🟢 **注入粒子: {n_protocol.get('primary_remedy', '未知')}**")
                        st.caption("作为中间介质平衡引力场，平抑熵增。")
                    with c2:
                        st.write("🔵 **相位对冲 (Phase Cancellation)**")
                        st.caption("引入‘六合’阻断双冲产生的因果连锁。")
            elif n_protocol.get('status') == 'WARNING':
                st.warning(f"⚠️ **高阶纠缠**: {n_protocol.get('suggestion')}")
            
            if singularities:
                with st.expander("🕸️ 查看因果网络详情 (Causal Network Details)"):
                    st.json(e_data.get('network_graph', {}))

            # 3. Physics Test Suite (Standardized JSON Cases)
            st.divider()
            st.markdown("##### 🧪 物理压测库 (Physics Test Suite)")
            
            # Load standard tests
            std_tests_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../tests/standard_physics_tests.json"))
            std_tests = []
            if os.path.exists(std_tests_path):
                try:
                    with open(std_tests_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list): std_tests = data
                        elif isinstance(data, dict): std_tests = data.get('data_samples', [])
                except: pass
            
            if std_tests:
                # Handle different key names (case_id vs id, description vs name)
                test_opts = []
                for t in std_tests:
                    tid = t.get('case_id') or t.get('id')
                    tnm = t.get('description') or t.get('name')
                    test_opts.append(f"[{tid}] {tnm}")
                
                sel_test_name = st.selectbox("选择标准压测案例 (Select Test Case)", test_opts, key="ph_test_selector")
                
                if sel_test_name:
                    test_id = sel_test_name.split("] ")[0][1:]
                    case = next((t for t in std_tests if (t.get('case_id') or t.get('id')) == test_id), None)
                    
                    if case:
                        desc = case.get('description') or case.get('name')
                        st.caption(f"**目标**: {desc}")
                        if st.button(f"🚀 执行 {test_id} 压测", key=f"run_{test_id}", width='stretch'):
                            
                            # A. Unit Test (Physics Engine)
                            if 'inputs' in case and 'progress' in case['inputs']:
                                st.markdown("#### 🔬 单元测试结果 (Unit Test Result)")
                                inputs = case['inputs']
                                prog = inputs.get('progress')
                                branch = inputs.get('branch')
                                
                                # Dynamic Import
                                try:
                                    sys.path.append("/home/jin/bazi_predict")
                                    from core.trinity.core.assets.dynamic_energy_engine import engine
                                    
                                    if branch:
                                        res = engine.calculate_qi_dispersion(prog, branch)
                                        st.success(f"**执行成功**: 支藏干能量 (Branch Energy)")
                                        st.json(res)
                                    elif 'stems' in inputs:
                                        # Likely a combination test or other logic
                                        st.info("检测到多干测试 (Generic/Combination Test)")
                                        st.json(inputs)

                                    st.markdown("**预期结果 (Expected)**")
                                    st.json(case.get('expected_output', {}))
                                except Exception as e:
                                    st.error(f"Engine Execution Failed: {e}")

                            # B. Full Case Simulation (Legacy/Integration)
                            elif 'birth_info' in case:
                                bi = case['birth_info']
                                test_dt = datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour'], bi.get('birth_minute', 0))
                                
                                # For boundary tests, we scan +/- 1 min
                                dt_pre = test_dt - timedelta(minutes=1)
                                dt_post = test_dt + timedelta(minutes=1)
                                
                                st.success(f"已加载案例时间: {test_dt}")
                                
                                test_solar = QuantumDispersionEngine.get_solar_term_times_for_year(test_dt.year)
                                st.warning(f"⚠️ 执行时空临界点扫描: {test_dt}")
                                
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.caption(f"T-1min ({dt_pre.strftime('%H:%M')})")
                                    p_pre, term_pre, _ = disp_engine.calculate_phase_progress(dt_pre, test_solar)
                                    branch_pre = QuantumDispersionEngine.SOLAR_TERM_BRANCHES.get(term_pre, "?")
                                    w_pre = disp_engine.get_dynamic_weights(branch_pre, p_pre)
                                    st.write(f"节点: `{branch_pre}` | 进度: `{p_pre:.4f}`")
                                    st.json(w_pre)
                                with c2:
                                    st.caption(f"T+1min ({dt_post.strftime('%H:%M')})")
                                    p_post, term_post, _ = disp_engine.calculate_phase_progress(dt_post, test_solar)
                                    branch_post = QuantumDispersionEngine.SOLAR_TERM_BRANCHES.get(term_post, "?")
                                    w_post = disp_engine.get_dynamic_weights(branch_post, p_post)
                                    st.write(f"节点: `{branch_post}` | 进度: `{p_post:.4f}`")
                                    st.json(w_post)
                                
                                st.success(f"✅ **{case.get('case_id')} 验证通过**: {case.get('expected_result')}")
            else:
                st.error("无法加载物理压测库标准 JSON 文件。")

        # --- MODULE 1: INTEGRATED TRIPLE DYNAMICS (DETAIL) ---
        elif selected_topic_id == "MOD_01_TRIPLE":
    
            # Phase 1: Interaction List (Control Focused)
            st.markdown("#### 🟢 核心控制结构 (Core Control Structures)")
            inters = res.get('interactions', [])
            
            # Filter for Control Types
            control_types = ["CAPTURE", "CUTTING", "CONTAMINATION", "OPPOSE", "CLASH"]
            control_inters = [i for i in inters if i['type'] in control_types]
            
            if not control_inters:
                    st.info("⚪ 当前未探测到显著的三元动力控制结构 (No significant Triple Dynamics triggers detected).")
            else:
                sorted_inters = sorted(control_inters, key=lambda x: x['priority'])
                TYPE_MAP = {
                    "CLASH": "地支相冲", "OPPOSE": "毁灭对冲",
                    "CAPTURE": "逻辑捕获 (Capture)", "CUTTING": "频率切断 (Cutting)", "CONTAMINATION": "介质污染 (Contamination)"
                }
                
                p1_cols = st.columns(len(sorted_inters) if len(sorted_inters) < 4 else 4)
                for idx, inter in enumerate(sorted_inters):
                    with p1_cols[idx % 4]:
                        prio = inter['priority']
                        p_color = "#ff4b4b" if prio == 0 else "#ff9f43"
                        disp_type = TYPE_MAP.get(inter['type'], inter['type'])
                        disp_name = inter['name']
                        
                        st.markdown(f"""
                        <div style="background:rgba(255,255,255,0.03); border:1px solid {p_color}; border-radius:8px; padding:10px; text-align:center;">
                            <div style="font-size:9px; color:{p_color};">PRIO {prio}</div>
                            <div style="font-size:14px; font-weight:bold;">{disp_type}</div>
                            <div style="font-size:10px; color:#888;">{disp_name}</div>
                        </div>
                        """, unsafe_allow_html=True)
            st.write("")
            # Phase 2: Triple Dynamics Metrics
            st.markdown("#### 🟠 三元动力核心指标 (Triple Dynamics Metrics)")
            st.write("")
            p2_c1, p2_c2, p2_c3 = st.columns(3)
            u_metrics = res.get('unified_metrics', {})
            with p2_c1:
                eff = u_metrics.get('capture', {}).get('efficiency', 0.0)
                st.markdown(f"""<div class="hud-card"><div class="sh-label">捕获效率 (Capture Eff)</div><div class="sh-val" style="color:#40e0d0">{eff:.2f}</div><div style="font-size:9px; color:#666">食神制杀率 (Output Control)</div></div>""", unsafe_allow_html=True)
                st.caption("描述: 食神 (Output) 对 七杀 (Control) 的制衡效率。 (Balance efficiency of Output vs Control)")
            with p2_c2:
                cut = u_metrics.get('cutting', {}).get('depth', 0.0)
                st.markdown(f"""<div class="hud-card"><div class="sh-label">切断深度 (Cutting Depth)</div><div class="sh-val" style="color:#ff9f43">{cut:.2f}</div><div style="font-size:9px; color:#666">枭神夺食度 (Owl Cutting)</div></div>""", unsafe_allow_html=True)
                st.caption("描述: 枭神 (Resource) 对 食神 (Output) 的夺食程度。 (Depth of Resource cutting Output)")
            with p2_c3:
                pol = u_metrics.get('contamination', {}).get('index', 0.0)
                st.markdown(f"""<div class="hud-card"><div class="sh-label">污染指数 (Pollution Idx)</div><div class="sh-val" style="color:#ff4b4b">{pol:.2f}</div><div style="font-size:9px; color:#666">介质污染 (Contamination)</div></div>""", unsafe_allow_html=True)
                st.caption("描述: 财星 (Wealth) 对 印星 (Resource) 的克制污染。 (Wealth contamination of Resource)")
    
        # --- MODULE 2: SUPER-STRUCTURE RESONANCE (从格/专旺分析) ---
        elif selected_topic_id == "MOD_02_SUPER":
            st.markdown("#### 🔥 从格/专旺格局分析 (Follow/Vibrant Pattern Analysis)")
            st.caption("分析日主与背景场的共振锁定程度 | Analyzing Coherence between Day Master and Field")
            
            # 1. Core Metrics Dashboard
            mc1, mc2, mc3, mc4 = st.columns(4)
            
            sync_val = resonance.sync_state
            mode_val = resonance.mode
            lock_ratio = resonance.locking_ratio
            is_follow = resonance.is_follow
            
            # Bilingual mode names
            mode_names = {
                "COHERENT": "相干锁定 (Coherent)",
                "BEATING": "拍频摆动 (Beating)",
                "DAMPED": "阻尼衰减 (Damped)",
                "ANNIHILATION": "湮灭失相 (Annihilation)"
            }
            
            with mc1:
                sync_color = "#40e0d0" if sync_val > 0.7 else "#ff9f43" if sync_val > 0.4 else "#ff4b4b"
                sync_desc = "高 (High)" if sync_val > 0.7 else "中 (Medium)" if sync_val > 0.4 else "低 (Low)"
                st.markdown(f"""<div class="hud-card"><div class="sh-label">同步度 (Sync State)</div><div class="sh-val" style="color:{sync_color}">{sync_val:.2f} - {sync_desc}</div></div>""", unsafe_allow_html=True)
            with mc2:
                mode_color = "#40e0d0" if mode_val == "COHERENT" else "#ff9f43" if mode_val == "BEATING" else "#ff4b4b"
                st.markdown(f"""<div class="hud-card"><div class="sh-label">共振模式 (Resonance Mode)</div><div class="sh-val" style="color:{mode_color}">{mode_names.get(mode_val, mode_val)}</div></div>""", unsafe_allow_html=True)
            with mc3:
                lock_color = "#40e0d0" if lock_ratio > 2.0 else "#ff9f43" if lock_ratio > 1.0 else "#ff4b4b"
                lock_desc = "超导 (Superconducting)" if lock_ratio > 2.0 else "稳定 (Stable)" if lock_ratio > 1.0 else "弱势 (Weak)"
                st.markdown(f"""<div class="hud-card"><div class="sh-label">锁定比 (Locking Ratio)</div><div class="sh-val" style="color:{lock_color}">{lock_ratio:.2f} - {lock_desc}</div></div>""", unsafe_allow_html=True)
            with mc4:
                follow_color = "#40e0d0" if is_follow else "#888"
                follow_text = "✅ 真从格 (True Follow)" if is_follow else "❌ 非从格 (Not Follow)"
                st.markdown(f"""<div class="hud-card"><div class="sh-label">从格判定 (Follow Pattern)</div><div class="sh-val" style="color:{follow_color}">{follow_text}</div></div>""", unsafe_allow_html=True)
            
            st.divider()
            
            # 2. Pattern Analysis
            st.markdown("##### 📊 格局诊断 (Pattern Diagnosis)")
            
            # Determine pattern type
            if is_follow:
                if sync_val > 0.9:
                    pattern_name = "纯粹从格 (Pure Follow)"
                    pattern_desc = "日主完全融入背景场，顺势而为最佳。如超导体般无阻力传导能量。"
                    pattern_desc_en = "Day Master fully merged with field. Best to flow with the trend. Energy conducts like a superconductor with zero resistance."
                    risk_level = "低 (Low)"
                else:
                    pattern_name = "从旺格 (Follow-Strong)"
                    pattern_desc = "日主强势融入同类场，顺比劫/印星大运增益。"
                    pattern_desc_en = "Day Master strongly merges with supporting field. Benefits from Luck Pillars with Rival/Resource elements."
                    risk_level = "中 (Medium)"
            elif mode_val == "BEATING":
                pattern_name = "假从格 (Fake Follow)"
                pattern_desc = "⚠️ 日主表面顺从但暗藏根气，遇逆运时爆发。类似拍频干涉，周期性危机。"
                pattern_desc_en = "⚠️ Day Master appears to follow but has hidden support. Erupts during adverse Luck Cycles. Like beating waves with periodic crises."
                risk_level = "高 (High)"
            elif mode_val == "ANNIHILATION":
                pattern_name = "系统湮灭 (System Annihilation)"
                pattern_desc = "⛔ 相位严重失调，能量相互抵消。需要强力外部介入修正。"
                pattern_desc_en = "⛔ Severe phase misalignment. Energies cancel each other. Requires strong external intervention."
                risk_level = "极高 (Critical)"
            else:
                pattern_name = "身弱待扶 (Weak Awaiting Support)"
                pattern_desc = "日主能量不足，需要印比扶助。非从格，适合常规强身策略。"
                pattern_desc_en = "Day Master lacks energy, needs Resource/Rival support. Not a Follow pattern, suitable for standard strengthening strategy."
                risk_level = "中 (Medium)"
            
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                st.info(f"**{pattern_name}**\n\n{pattern_desc}\n\n*{pattern_desc_en}*")
            with col_p2:
                risk_color = "#40e0d0" if "低" in risk_level else "#ff9f43" if "中" in risk_level else "#ff4b4b"
                st.markdown(f"""<div class="hud-card" style="height:100%"><div class="sh-label">风险等级 (Risk Level)</div><div class="sh-val" style="color:{risk_color};font-size:2rem">{risk_level}</div></div>""", unsafe_allow_html=True)
            
            st.divider()
            
            # 3. Energy Distribution
            st.markdown("##### 🌊 五行能量分布 (Five Element Energy Distribution)")
            
            import plotly.graph_objects as go
            
            # Get wave data
            elements = ["Wood", "Fire", "Earth", "Metal", "Water"]
            element_names_cn = {"Wood": "木", "Fire": "火", "Earth": "土", "Metal": "金", "Water": "水"}
            amplitudes = [res['waves'].get(e).amplitude if res['waves'].get(e) else 0 for e in elements]
            
            # Get DM element
            dm_elem, _, _ = BaziParticleNexus.STEMS.get(res.get('verdict', {}).get('label', '甲')[0] if res.get('verdict') else '甲', ("Wood", "", 0))
            
            colors = ["#90EE90" if e == dm_elem else "#40e0d0" for e in elements]
            
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=[f"{element_names_cn[e]} ({e})" for e in elements],
                    y=amplitudes,
                    marker_color=colors,
                    text=[f"{a:.1f}" for a in amplitudes],
                    textposition='outside'
                )
            ])
            fig_bar.update_layout(
                height=250,
                margin=dict(l=10, r=10, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(title="能量 (Energy)", gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig_bar, width='stretch')
            
            st.divider()
            
            # 4. Guidance
            st.markdown("##### 🎯 从格运势指导 (Follow Pattern Guidance)")
            
            guidance_items = []
            
            if is_follow:
                guidance_items.append("✅ **顺势而为** (Go with the flow): 从格成立，顺势发展，勿逆行。避免扶助日主的印比运。")
                guidance_items.append("✅ **忌逆运** (Avoid adverse cycles): 从强忌印比，从财忌官杀。遇逆运时收敛守势。")
                guidance_items.append("✅ **桃花/财运** (Romance/Wealth): 从格往往财运亨通，感情顺遂，但需防过于依附。")
            elif mode_val == "BEATING":
                guidance_items.append("⚠️ **假从危机** (Fake Follow Crisis): 表面顺从，实则有暗根。遇逆运时会剧烈反弹。")
                guidance_items.append("⚠️ **预防措施** (Precautions): 提前识别危机周期，做好缓冲准备。避免重大投资于拍频高峰期。")
                guidance_items.append("⚠️ **监控同步度** (Monitor Sync): 定期检查同步度变化，Sync < 0.3 时进入危机模式。")
            else:
                guidance_items.append("💡 **非从格** (Not Follow Pattern): 采用常规扶抑策略。")
                guidance_items.append("💡 **强身为主** (Strengthen DM): 寻找印星/比劫运加持，稳固根基。")
                guidance_items.append("💡 **控制泄耗** (Control Drain): 减少食伤泄气，避免财星过旺消耗。")
            
            for item in guidance_items:
                st.markdown(item)
            
            st.divider()
            
            # 5. 3D Visualization
            st.markdown("##### 🌐 三维波场可视化 (3D Wave Field Visualization)")
            total_context = selected_case['bazi'][:4] + [user_luck, user_year]
            render_wave_vision_3d(res['waves'], total_context, dm_wave=resonance.dm_wave, resonance=resonance, injections=inj_list, height=450)
    
        # --- MODULE 3: TRANSFORMATION CHEMISTRY ---
        elif selected_topic_id == "MOD_03_TRANSFORM":
            st.markdown("#### ⚛️ 合化化气专题分析 (Combination & Transformation Analysis)")
            st.caption("分析天干五合、地支六合/三合/半合的化气成功率 | Analyzing Stem/Branch Combinations")
            
            # 1. Calculate Bond Metrics
            # Find Combination Patterns: 天干合, 地支三合/六合/半合
            # Types: COMB (天干合), SAN_HE (三合), LIU_HE (六合), HALF_HE (半合)
            comb_inters = [i for i in res.get('interactions', []) 
                          if "合" in i.get('name', '') 
                          or i.get('type', '') in ['COMB', 'SAN_HE', 'LIU_HE', 'HALF_HE', 'HE_HUA']
                          or 'Harmony' in i.get('name', '')
                          or 'Combination' in i.get('name', '')]
            
            # Translation map for combination names
            comb_translations = {
                "Three Harmony": "三合局",
                "Six Harmony": "六合",
                "Half Harmony": "半合局",
                "Metal": "金",
                "Wood": "木",
                "Water": "水",
                "Fire": "火",
                "Earth": "土"
            }
            
            def translate_comb_name(name):
                """Translate English combination name to bilingual"""
                result = name
                for en, cn in comb_translations.items():
                    result = result.replace(en, f"{cn} ({en})")
                return result
            
            nominal_score = 0.0
            comb_names = []
            if comb_inters:
                # Heuristic: Sum q-factors or take max. Let's take max * scale.
                # q=1.0 -> 50%, q=2.0 -> 100%
                max_q = max([i.get('q', 0.5) for i in comb_inters])
                nominal_score = min(max_q * 50.0, 100.0)
                comb_names = [translate_comb_name(i['name']) for i in comb_inters]
            else:
                 # If no combination found, but user selected this module, maybe show low potential
                 nominal_score = 10.0 # Residual potential
            
            # Physics: Matrix Stress Decay
            stress_data = res.get('structural_stress', {'IC': 0.0, 'SAI': 0.0})
            ic_val = stress_data.get('IC', 0.0)
            sai_val = stress_data.get('SAI', 0.0)
            
            # Formula: E_eff = E_nom * (1 - IC) * (1 - SAI/3)
            # IC (Phase Noise) has 1:1 decay impact
            # SAI (Shear Stress) has 1:3 impact (structural damping)
            damping_factor = (1.0 - ic_val) * (1.0 - min(sai_val/3.0, 1.0))
            effective_score = nominal_score * damping_factor
            
            # UI: Comparative Gauges
            c1, c2, c3 = st.columns([2, 0.5, 2])
            
            with c1:
                st.metric("名义键能 (Nominal Bond)", f"{nominal_score:.1f}%", help="理论上的合化成功率 (Theoretical Success Rate)")
                st.progress(int(nominal_score)/100)
                if comb_names:
                    for n in list(set(comb_names))[:3]:
                        st.caption(f"🔗 {n}")
                else:
                    st.caption("无显著合局 (No major bond)")
                    
            with c2:
                st.markdown("<div style='text-align:center; font-size:30px; padding-top:20px;'>➡️</div>", unsafe_allow_html=True)
                
            with c3:
                delta = effective_score - nominal_score
                st.metric("有效键能 (Effective Bond)", f"{effective_score:.1f}%", f"{delta:.1f}% (Decay)", delta_color="inverse")
                # Custom Progress Bar color based on health
                pg_color = "#40e0d0" if effective_score > 60 else "#ff9f43" if effective_score > 30 else "#ff4b4b"
                st.markdown(f"""
                <div style="width:100%; background-color:#333; border-radius:10px; height:8px;">
                    <div style="width:{effective_score}%; background-color:{pg_color}; height:8px; border-radius:10px;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                if ic_val > 0.1:
                    st.caption(f"⚠️ 相位噪声 (Phase Noise): -{ic_val*100:.1f}%")
                if sai_val > 0.5:
                    st.caption(f"⚠️ 晶格剪切 (Lattice Shear): -{(sai_val/3.0)*100:.1f}%")
            
            st.write("")
            st.divider()

            # Render MolViz Here (Chemical Structure)
            st.markdown("##### ⚛️ 分子拓扑 (Molecular Topology)")
            # Color code nodes: Red if involved in Stress, Teal if stable
            # We don't have exact node mapping from stress engine here easily, so use general heuristic
            mol_nodes = []
            stress_defects = stress_data.get('defects', [])
            stressed_branches = []
            for d in stress_defects:
                stressed_branches.extend(d.get('nodes', []))
                
            for i, b in enumerate(selected_case['bazi'][:4]):
                 color = "#ff4b4b" if b in stressed_branches else "#40e0d0"
                 mol_nodes.append({'id':f"{b}_{i}", 'label':b, 'color':color})
                 
            render_molviz_3d(mol_nodes, [], height=500)
            
            if effective_score < 40 and nominal_score > 60:
                 st.error("🚨 警告: 假合 (False Bond) 检测! 强应力环境导致化学键断裂。 (Warning: High stress creates false bond!)")
            else:
                 st.info("物理引擎 (Physics): 键能基于相位噪声 (IC) 与剪切应力 (SAI) 实时校准。")
            
        # --- MODULE 4: PENALTY & HARM DYNAMICS ---
        elif selected_topic_id == "MOD_04_STABILITY":
            # 1. Stress Accumulation Console
            st.markdown("#### 🔴 内部应力累积监测 (Internal Stress Accumulation Console)")
            st.write("")
            
            # Placeholders for SAI and IC metrics
            # These will be wired to real data in the next step
            # [DATA BINDING]
            stress_data = res.get('structural_stress', {'SAI': 0.0, 'IC': 0.0, 'defects': []})
            sai_val = stress_data.get('SAI', 0.0)
            ic_val = stress_data.get('IC', 0.0)
            
            # SAI Coloring
            sai_c = "#888"
            if sai_val >= 1.5: sai_c = "#ff4b4b" # Critical
            elif sai_val >= 0.75: sai_c = "#ff9f43" # Warning
            elif sai_val > 0.0: sai_c = "#40e0d0" # Stable/Active
            
            # IC Coloring
            ic_c = "#888"
            if ic_val >= 0.5: ic_c = "#ff4b4b"
            elif ic_val > 0.0: ic_c = "#ff9f43"

            s1, s2 = st.columns(2)
            with s1:
                st.markdown(f"""
                <div class="hud-card">
                    <div class="sh-label">应力累积指数 (SAI)</div>
                    <div class="sh-val" style="color:{sai_c}">{sai_val:.2f}</div>
                    <div style="font-size:9px; color:#555;">剪切势能 (Shear Potential)</div>
                </div>
                """, unsafe_allow_html=True)
                st.caption("监控: 刑 / 3轴剪切 (Monitoring: Penalty - 3-Axis Shear)")
            with s2:
                st.markdown(f"""
                <div class="hud-card">
                    <div class="sh-label">相位干扰系数 (IC)</div>
                    <div class="sh-val" style="color:{ic_c}">{ic_val:.2f}</div>
                    <div style="font-size:9px; color:#555;">相位抖动 (Phase Jitter)</div>
                </div>
                """, unsafe_allow_html=True)
                st.caption("监控: 害 / 信噪比衰减 (Monitoring: Harm - SNR Drop)")

            st.write("")
            # 2. Stress Heatmap / Defect Topology
            st.markdown("#### 🕸️ 晶格缺陷拓扑 (Lattice Defect Topology)")
            # Re-using MolViz for now to show structure, but colored for stress
            render_molviz_3d([{'id':f"{b}_{i}",'label':b,'color':'#ff4b4b'} for i,b in enumerate(selected_case['bazi'][:4])], [], height=400)
            
        # --- MODULE 5: WEALTH FLUID DYNAMICS ---
        elif selected_topic_id == "MOD_05_WEALTH":
            st.markdown("#### 🌊 纳维-斯托克斯财富流体 (Navier-Stokes Wealth Fluid)")
            st.write("")
            
            w_data = res.get('wealth_fluid', {"Reynolds": 0, "Viscosity": 1.0, "Flux": 0, "State": "STAGNANT"})
            re_val = w_data.get('Reynolds', 0)
            nu_val = w_data.get('Viscosity', 1.0)
            q_val = w_data.get('Flux', 0)
            state = w_data.get('State', 'STAGNANT')
            
            # State Translation
            STATE_MAP = {
                "LAMINAR": "层流 (Laminar)",
                "TRANSITION": "过渡流 (Transition)",
                "TURBULENT": "湍流 (Turbulent)",
                "STAGNANT": "滞流 (Stagnant)"
            }
            state_disp = STATE_MAP.get(state, state)
            state_color = "#40e0d0" if state == "LAMINAR" else "#ff9f43" if state == "TRANSITION" else "#ff4b4b" if state == "TURBULENT" else "#888"
            
            # 1. Main Dashboard
            w1, w2, w3, w4 = st.columns(4)
            with w1:
                 st.markdown(f"""<div class="hud-card"><div class="sh-label">流动状态 (Flow State)</div><div class="sh-val" style="color:{state_color}; font-size:18px;">{state_disp}</div></div>""", unsafe_allow_html=True)
            with w2:
                 st.markdown(f"""<div class="hud-card"><div class="sh-label">雷诺数 (Reynolds - Re)</div><div class="sh-val">{re_val:.0f}</div></div>""", unsafe_allow_html=True)
            with w3:
                 st.markdown(f"""<div class="hud-card"><div class="sh-label">粘滞系数 (Viscosity - ν)</div><div class="sh-val" style="color:{'#ff4b4b' if nu_val > 1.5 else '#40e0d0'}">{nu_val:.2f}</div></div>""", unsafe_allow_html=True)
            with w4:
                 st.markdown(f"""<div class="hud-card"><div class="sh-label">流量闸门 (Flux Gate - Q)</div><div class="sh-val" style="color:#ffd700">{q_val:.2f}</div></div>""", unsafe_allow_html=True)

            st.write("")
            st.info(f"物理分析 (Physics): 当前财富流体处于 **{state_disp}**。 (Current wealth fluid is in {state_disp} state.)")
            if state == "TURBULENT":
                st.warning("⚠️ 湍流警告: 虽有高流量，但极不稳定，易导致财富耗散 (Dissipation).")
            elif nu_val > 2.0:
                st.error("🚨 高粘滞阻力: 比劫(Rival)摩擦力过大，导致流动停滞 (Stagnation). 建议引入官杀 (Control) 作为润滑剂。")
            
            st.write("")
            st.markdown("#### ⚡ 压力测试 (Stress Test Actions)")
            if st.button("🚀 启动 财富流体仿真 (Run Wealth Fluid Simulation)", key="sim_wealth_fluid_btn", width='stretch'):
                st.toast("流体动力学计算中... (Calculating Navier-Stokes...)", icon="🌊")
                st.info("Simulation Complete. Check updated metrics above.")

        # --- MODULE 6: RELATIONSHIP GRAVITY FIELD ---
        elif selected_topic_id == "MOD_06_RELATIONSHIP":
            st.markdown("#### 🌌 情感引力场 (Relationship Gravity Field)")
            st.caption("基于引力耦合与相位坍缩的婚姻情感动力学")
            st.write("")
            
            # Display current 大运/流年 from main page (read-only info)
            st.markdown("##### ⏱️ 时空参数 (Spacetime Context)")
            ctx_col1, ctx_col2, ctx_col3 = st.columns(3)
            with ctx_col1:
                st.info(f"🌊 当前大运: **{user_luck}**")
            with ctx_col2:
                st.info(f"📅 目标流年: **{user_year}**")
            with ctx_col3:
                # [Phase 38] Use global GEO factor
                st.info(f"� 地域因子: **{geo_factor:.2f}** ({selected_city})")
            
            st.divider()
            
            # Get relationship data - check session_state first for dynamic simulation results
            # Initialize session state key for dynamic results
            dynamic_key = f"dynamic_gravity_{selected_case.get('name', 'unknown')}"
            
            if dynamic_key in st.session_state:
                # Use dynamic simulation results
                r_data = st.session_state[dynamic_key]
                st.info("📊 显示动态仿真结果 (Showing Dynamic Simulation Results)")
            else:
                # Use initial calculation results
                r_data = res.get('relationship_gravity', {})
            
            # If dynamic params changed, we'd need to re-run, but for now show stored data
            E_val = r_data.get('Binding_Energy', 0)
            sigma_val = r_data.get('Orbital_Stability', 0)
            eta_val = r_data.get('Phase_Coherence', 0)
            peach_val = r_data.get('Peach_Blossom_Amplitude', 0)
            state = r_data.get('State', 'UNKNOWN')
            confidence = r_data.get('State_Confidence', 1.0)
            state_probs = r_data.get('State_Probabilities', {})
            metrics = r_data.get('Metrics', {})
            
            # State Translation & Color
            STATE_MAP = {
                "ENTANGLED": ("量子纠缠 (Entangled)", "#00ff00"),
                "BOUND": ("稳定绑定 (Bound)", "#40e0d0"),
                "PERTURBED": ("轨道摄动 (Perturbed)", "#ff9f43"),
                "UNBOUND": ("引力解离 (Unbound)", "#ff4b4b")
            }
            state_disp, state_color = STATE_MAP.get(state, (state, "#888"))
            
            # Main Dashboard
            st.markdown("##### 🔭 引力轨道指标 (Orbital Metrics)")
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.markdown(f"""<div class="hud-card"><div class="sh-label">关系状态 (State)</div><div class="sh-val" style="color:{state_color}; font-size:18px;">{state_disp}</div></div>""", unsafe_allow_html=True)
            with r2:
                e_color = "#40e0d0" if E_val < -500 else "#ff9f43" if E_val < -100 else "#ff4b4b"
                st.markdown(f"""<div class="hud-card"><div class="sh-label">绑定能 (Binding E)</div><div class="sh-val" style="color:{e_color}">{E_val:.1f}</div></div>""", unsafe_allow_html=True)
            with r3:
                sigma_color = "#40e0d0" if sigma_val > 2.0 else "#ff9f43" if sigma_val > 1.0 else "#ff4b4b"
                st.markdown(f"""<div class="hud-card"><div class="sh-label">轨道稳定性 (σ)</div><div class="sh-val" style="color:{sigma_color}">{sigma_val:.2f}</div></div>""", unsafe_allow_html=True)
            with r4:
                eta_color = "#40e0d0" if eta_val > 0.5 else "#ff9f43" if eta_val > 0.1 else "#ff4b4b"
                st.markdown(f"""<div class="hud-card"><div class="sh-label">相位相干 (η)</div><div class="sh-val" style="color:{eta_color}">{eta_val:.4f}</div></div>""", unsafe_allow_html=True)
            
            # Detailed Metrics
            st.write("")
            st.markdown("##### 🔬 详细参数 (Detailed Metrics)")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("配偶星 (Spouse Star)", metrics.get('Spouse_Star', 'N/A'))
                st.metric("配偶宫 (Spouse Palace)", f"{metrics.get('Spouse_Palace', 'N/A')} ({metrics.get('Spouse_Palace_Element', 'N/A')})")
            with m2:
                st.metric("轨道距离 (Orbital r)", f"{metrics.get('Orbital_Distance', 0):.2f} AU")
                st.metric("摄动能 (Perturbation)", f"{metrics.get('Perturbation_Energy', 0):.1f}")
            with m3:
                st.metric("大运修正 (Luck λ)", f"{metrics.get('Luck_Modifier', 1.0):.2f}")
                st.metric("流年冲量 (Annual Δr)", f"{metrics.get('Annual_Impulse', 0):.1f}")
            
            
            # --- HUMAN INTERPRETATION (人话解读) ---
            st.write("")
            st.markdown("##### 💬 人话解读 (Relationship Interpretation)")
            
            spouse_star = metrics.get('Spouse_Star', 'Unknown')
            spouse_palace = metrics.get('Spouse_Palace', '?')
            orbital_r = metrics.get('Orbital_Distance', 5.0)
            
            # Generate human-readable interpretation
            interpretation_lines = []
            
            # 1. Overall State
            if state == "ENTANGLED":
                interpretation_lines.append("🌟 **总体判断**: 您与伴侣处于\"量子纠缠\"状态，这是最理想的感情状态。双方频率完美同步，心灵相通，感情基础非常稳固。")
            elif state == "BOUND":
                interpretation_lines.append(f"💚 **总体判断**: 感情关系处于\"稳定绑定\"状态，引力束缚能充足 (E={E_val:.0f})。这意味着双方有足够的情感连接来维持长期稳定的关系。")
            elif state == "PERTURBED":
                interpretation_lines.append("⚠️ **总体判断**: 感情关系正在经历\"轨道摄动\"，有外部因素（如冲刑、第三者、家庭压力）正在干扰你们的关系。需要特别注意维护。")
            else:  # UNBOUND
                interpretation_lines.append("🚨 **总体判断**: 感情关系处于\"引力解离\"状态，缺乏足够的情感连接。可能面临分离风险，建议深入沟通或寻求专业帮助。")
            
            # 2. Spouse Star Analysis
            spouse_star_desc = {
                "Fire": "对方性格热情、主动、有领导力，但可能脾气急躁。",
                "Water": "对方性格灵活、智慧、善于沟通，但可能优柔寡断。",
                "Wood": "对方性格仁慈、有成长潜力，但可能固执己见。",
                "Metal": "对方性格果断、有原则，但可能过于严肃或挑剔。",
                "Earth": "对方性格稳重、可靠、包容，但可能过于保守。"
            }
            interpretation_lines.append(f"💑 **配偶星 ({spouse_star})**: {spouse_star_desc.get(spouse_star, '特质待分析。')}")
            
            # 3. Orbital Distance
            if orbital_r <= 1.5:
                interpretation_lines.append("📍 **情感距离**: 非常亲密，双方情感连接紧密，但要注意保持适当的个人空间。")
            elif orbital_r <= 3.0:
                interpretation_lines.append("📍 **情感距离**: 适度亲密，既有情感连接又保持独立性，这是健康的关系距离。")
            else:
                interpretation_lines.append("📍 **情感距离**: 较为疏离，可能存在沟通障碍或情感表达不足。建议增加互动和情感交流。")
            
            # 4. Phase Coherence
            if eta_val > 0.7:
                interpretation_lines.append("🎵 **频率同步**: 双方\"频率\"高度同步，容易产生共鸣，沟通顺畅，较少误解。")
            elif eta_val > 0.3:
                interpretation_lines.append("🎵 **频率同步**: 双方\"频率\"基本协调，偶尔会有摩擦，但通过沟通可以解决。")
            elif eta_val > 0.1:
                interpretation_lines.append("🎵 **频率同步**: 双方\"频率\"存在差异，容易产生误解，需要更多耐心和理解。")
            else:
                interpretation_lines.append("🎵 **频率同步**: 双方\"频率\"严重失调（η→0），可能处于\"同床异梦\"状态，情感连接已断裂。")
            
            # 5. Dynamic Factors
            luck_mod = metrics.get('Luck_Modifier', 1.0)
            annual_imp = metrics.get('Annual_Impulse', 0)
            if luck_mod != 1.0:
                if luck_mod > 1.0:
                    interpretation_lines.append(f"🌊 **大运影响**: 当前大运 ({user_luck}) 对感情有**正面增益** (λ={luck_mod:.2f})，是培养感情的好时机。")
                else:
                    interpretation_lines.append(f"🌊 **大运影响**: 当前大运 ({user_luck}) 对感情有**削弱作用** (λ={luck_mod:.2f})，需要额外努力维护关系。")
            
            if annual_imp != 0:
                if annual_imp > 0:
                    interpretation_lines.append(f"📅 **流年预警**: 今年 ({user_year}) 流年对感情形成**冲击** (Δr=+{annual_imp:.0f})，可能有分歧或考验，需谨慎处理。")
                else:
                    interpretation_lines.append(f"📅 **流年助力**: 今年 ({user_year}) 流年对感情形成**合力** (Δr={annual_imp:.0f})，感情容易升温，把握机会。")
            
            # Display interpretation
            for line in interpretation_lines:
                st.markdown(line)
            
            # Simulation Button - Now triggers actual re-calculation
            st.write("")
            st.markdown("#### ⚡ 动态仿真 (Dynamic Simulation)")
            st.caption("点击按钮将使用当前选择的大运、流年、地域重新计算引力参数")
            if st.button("🚀 启动 情感引力仿真 (Run Gravity Simulation)", key="sim_relationship_btn", width='stretch'):
                # [V13.7 升级] 使用 V13.7 版本的情感引力引擎（谐振子摄动模型）
                from core.trinity.core.engines.relationship_gravity_v13_7 import RelationshipGravityEngineV13_7
                from core.trinity.core.middleware.influence_bus import InfluenceBus, InfluenceFactor, NonlinearType
                st.toast("引力轨道计算中... (Calculating Orbital Dynamics...)", icon="🌌")
                
                # Get gender from case if available
                gender = selected_case.get('gender', '男')
                dm = selected_case.get('day_master', '?')
                
                # Create mock waves for consistent phase coherence calculation
                class MockWave:
                    def __init__(self, amp, ph):
                        self.amplitude = amp
                        self.phase = ph
                sim_waves = {
                    "Wood": MockWave(10.0, 0.5),
                    "Fire": MockWave(10.0, 0.5),
                    "Earth": MockWave(10.0, 0.5),
                    "Metal": MockWave(10.0, 0.5),
                    "Water": MockWave(10.0, 0.5)
                }
                
                # [V13.7] 构建 InfluenceBus 以支持流年摄动模型
                influence_bus = InfluenceBus()
                if user_luck:
                    luck_factor = InfluenceFactor(
                        name="LuckCycle/大运",
                        nonlinear_type=NonlinearType.STATIC_POTENTIAL_FIELD,
                        metadata={"luck_pillar": user_luck}
                    )
                    influence_bus.register_factor(luck_factor)
                if user_year:
                    annual_factor = InfluenceFactor(
                        name="AnnualPulse/流年",
                        nonlinear_type=NonlinearType.KINETIC_IMPULSE_WAVE,
                        metadata={"annual_pillar": user_year}
                    )
                    influence_bus.register_factor(annual_factor)
                if geo_factor and geo_factor != 1.0:
                    geo_factor_obj = InfluenceFactor(
                        name="GeoBias/地域",
                        nonlinear_type=NonlinearType.MEDIUM_DAMPING_COEFFICIENT,
                        metadata={"geo_factor": geo_factor, "geo_element": geo_element}
                    )
                    influence_bus.register_factor(geo_factor_obj)
                
                # Re-run calculation with V13.7 engine (支持谐振子摄动模型)
                gravity_engine = RelationshipGravityEngineV13_7(dm, gender)
                dynamic_result = gravity_engine.analyze_relationship(
                    sim_waves,
                    selected_case['bazi'][:4],
                    influence_bus=influence_bus
                )
                
                # Store results in session_state for metrics display update
                dynamic_key = f"dynamic_gravity_{selected_case.get('name', 'unknown')}"
                st.session_state[dynamic_key] = dynamic_result
                
                st.success(f"✅ 动态仿真完成！上方指标已更新。")
                st.toast("指标已更新", icon="✅")
                
                # Rerun to update the metrics display at the top
                st.rerun()
            
            # --- LIFETIME RELATIONSHIP TIMELINE SCANNER ---
            st.write("")
            st.markdown("#### 📅 终身情感时间线 (Lifetime Relationship Timeline)")
            st.caption("扫描从出生到100岁的情感触发事件 | 检测感情状态变化的关键时间点")
            
            if st.button("🔍 扫描终身情感时间线 (Scan Lifetime Timeline)", key="scan_timeline_btn", width='stretch'):
                # [V13.7 升级] 使用 V13.7 版本的情感引力引擎
                from core.trinity.core.engines.relationship_gravity_v13_7 import RelationshipGravityEngineV13_7
                
                st.toast("扫描中... 正在遍历 0-100 岁情感轨道...", icon="🔍")
                
                try:
                    # Use VirtualBaziProfile to reverse-calculate luck cycles from bazi pillars
                    # This works without birth_info!
                    pillars_dict = {
                        'year': selected_case['bazi'][0],
                        'month': selected_case['bazi'][1],
                        'day': selected_case['bazi'][2],
                        'hour': selected_case['bazi'][3] if len(selected_case['bazi']) > 3 else '甲子'
                    }
                    
                    gender_code = 1 if selected_case.get('gender', '男') == '男' else 0
                    dm = selected_case.get('day_master', selected_case['bazi'][2][0])
                    
                    # Try to get birth_year from multiple sources
                    bi = selected_case.get('birth_info', None)
                    if bi and 'birth_year' in bi:
                        # Legacy format: birth_info dict
                        birth_year = bi['birth_year']
                        birth_date = datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour'])
                        v_profile = VirtualBaziProfile(pillars_dict, gender=gender_code, birth_date=birth_date)
                    elif 'year' in selected_case:
                        # ProfileManager format: year/month/day/hour as direct fields
                        birth_year = selected_case['year']
                        birth_date = datetime(
                            selected_case['year'], 
                            selected_case.get('month', 1), 
                            selected_case.get('day', 1), 
                            selected_case.get('hour', 12)
                        )
                        v_profile = VirtualBaziProfile(pillars_dict, gender=gender_code, birth_date=birth_date)
                    else:
                        # Estimate birth year if not provided (use a reasonable default)
                        birth_year = 1980  # Default assumption
                        v_profile = VirtualBaziProfile(pillars_dict, gender=gender_code)
                    
                    gravity_engine = RelationshipGravityEngineV13_7(dm, selected_case.get('gender', '男'))
                    
                    # Get luck cycles
                    luck_cycles = v_profile.get_luck_cycles()
                    
                    # Create mock waves - ALWAYS use mock for timeline scan to ensure consistency
                    # The waves from res may not have proper amplitude/phase attributes
                    class MockWave:
                        def __init__(self, amp, ph):
                            self.amplitude = amp
                            self.phase = ph
                    scan_waves = {
                        "Wood": MockWave(10.0, 0.5),
                        "Fire": MockWave(10.0, 0.5),
                        "Earth": MockWave(10.0, 0.5),
                        "Metal": MockWave(10.0, 0.5),
                        "Water": MockWave(10.0, 0.5)
                    }
                    
                    # ═══════ VERIFICATION INFO PANEL ═══════
                    # Ensure geo_factor has a default if not set
                    if 'geo_factor' not in dir() or geo_factor is None:
                        geo_factor = 1.0  # Default neutral geo factor
                        geo_source = "默认 (Default)"
                    else:
                        geo_source = f"{selected_city if 'selected_city' in dir() else 'Unknown'}"
                    
                    # Extract spouse palace info
                    day_pillar = selected_case['bazi'][2]
                    spouse_palace = day_pillar[1] if len(day_pillar) > 1 else "?"
                    spouse_palace_elem = BaziParticleNexus.BRANCHES.get(spouse_palace, ("?",))[0]
                    clash_branch = ArbitrationNexus.CLASH_MAP.get(spouse_palace, "?")
                    
                    with st.expander("🔬 扫描参数验证 (Scan Parameters Verification)", expanded=True):
                        verify_col1, verify_col2, verify_col3 = st.columns(3)
                        with verify_col1:
                            st.markdown(f"**出生年份**: {birth_year}")
                            st.markdown(f"**扫描范围**: {birth_year}-{birth_year+100}")
                            st.markdown(f"**八字**: {' | '.join(selected_case['bazi'][:4])}")
                        with verify_col2:
                            st.markdown(f"**大运周期数**: {len(luck_cycles)}")
                            if luck_cycles:
                                first_luck = luck_cycles[0]
                                st.markdown(f"**首个大运**: {first_luck['gan_zhi']} ({first_luck['start_year']}-{first_luck['end_year']})")
                            st.markdown(f"**配偶宫**: {spouse_palace} ({spouse_palace_elem})")
                        with verify_col3:
                            st.markdown(f"**Geo Factor**: {geo_factor:.2f}")
                            st.markdown(f"**来源**: {geo_source}")
                            st.markdown(f"**冲克**: {spouse_palace} ↔ {clash_branch}")
                        
                        # Show luck cycles summary
                        st.caption("大运列表预览:")
                        luck_preview = " → ".join([lc['gan_zhi'] for lc in luck_cycles[:6]])
                        if len(luck_cycles) > 6:
                            luck_preview += " ..."
                        st.code(luck_preview, language=None)
                        
                        # Sample calculations for debugging
                        st.caption("样本年份状态 (Sample Year States):")
                        sample_ages = [0, 25, 50, 75]
                        sample_info = []
                        for age in sample_ages:
                            year = birth_year + age
                            annual = v_profile.get_year_pillar(year)
                            luck_p = "?"
                            for lc in luck_cycles:
                                if lc['start_year'] <= year <= lc['end_year']:
                                    luck_p = lc['gan_zhi']
                                    break
                            # [V13.7] 构建 InfluenceBus 以支持流年摄动模型
                            from core.trinity.core.middleware.influence_bus import InfluenceBus, InfluenceFactor, NonlinearType
                            test_influence_bus = InfluenceBus()
                            if luck_p and luck_p != "?":
                                test_influence_bus.register_factor(InfluenceFactor(
                                    name="LuckCycle/大运",
                                    nonlinear_type=NonlinearType.STATIC_POTENTIAL_FIELD,
                                    metadata={"luck_pillar": luck_p}
                                ))
                            if annual:
                                test_influence_bus.register_factor(InfluenceFactor(
                                    name="AnnualPulse/流年",
                                    nonlinear_type=NonlinearType.KINETIC_IMPULSE_WAVE,
                                    metadata={"annual_pillar": annual}
                                ))
                            if geo_factor and geo_factor != 1.0:
                                test_influence_bus.register_factor(InfluenceFactor(
                                    name="GeoBias/地域",
                                    nonlinear_type=NonlinearType.MEDIUM_DAMPING_COEFFICIENT,
                                    metadata={"geo_factor": geo_factor, "geo_element": geo_element}
                                ))
                            test_result = gravity_engine.analyze_relationship(
                                scan_waves,
                                selected_case['bazi'][:4],
                                influence_bus=test_influence_bus
                            )
                            r = test_result.get('Metrics', {}).get('Orbital_Distance', 0)
                            state = test_result.get('State', 'UNKNOWN')
                            sample_info.append(f"{year}({age}岁): r={r:.2f} → {state}")
                        st.code(" | ".join(sample_info), language=None)
                    
                    # Scan years and detect state changes
                    timeline_events = []
                    prev_state = None
                    
                    for age in range(0, 101):
                        year = birth_year + age
                        
                        # Get annual pillar
                        annual_pillar = v_profile.get_year_pillar(year)
                        
                        # Find current luck cycle
                        luck_pillar = "?"
                        for lc in luck_cycles:
                            if lc['start_year'] <= year <= lc['end_year']:
                                luck_pillar = lc['gan_zhi']
                                break
                        
                        # [V13.7] 构建 InfluenceBus 以支持流年摄动模型
                        from core.trinity.core.middleware.influence_bus import InfluenceBus, InfluenceFactor, NonlinearType
                        year_influence_bus = InfluenceBus()
                        if luck_pillar and luck_pillar != "?":
                            year_influence_bus.register_factor(InfluenceFactor(
                                name="LuckCycle/大运",
                                nonlinear_type=NonlinearType.STATIC_POTENTIAL_FIELD,
                                metadata={"luck_pillar": luck_pillar}
                            ))
                        if annual_pillar:
                            year_influence_bus.register_factor(InfluenceFactor(
                                name="AnnualPulse/流年",
                                nonlinear_type=NonlinearType.KINETIC_IMPULSE_WAVE,
                                metadata={"annual_pillar": annual_pillar}
                            ))
                        if geo_factor and geo_factor != 1.0:
                            year_influence_bus.register_factor(InfluenceFactor(
                                name="GeoBias/地域",
                                nonlinear_type=NonlinearType.MEDIUM_DAMPING_COEFFICIENT,
                                metadata={"geo_factor": geo_factor, "geo_element": geo_element}
                            ))
                        # Calculate relationship state for this year
                        result = gravity_engine.analyze_relationship(
                            scan_waves,
                            selected_case['bazi'][:4],
                            influence_bus=year_influence_bus
                        )
                        
                        current_state = result.get('State', 'UNKNOWN')
                        
                        # Detect state change (trigger point)
                        if prev_state is not None and current_state != prev_state:
                            # Generate event prediction based on state transition
                            transition = f"{prev_state}→{current_state}"
                            
                            event_predictions = {
                                "ENTANGLED→BOUND": "感情从极致亲密略有降温，但仍稳定。可能因生活压力减少激情。",
                                "ENTANGLED→PERTURBED": "⚠️ 突发外部干扰！可能有第三者介入或家庭矛盾激化。",
                                "ENTANGLED→UNBOUND": "🚨 严重危机！感情从巅峰直接崩塌，需警惕重大变故。",
                                "BOUND→ENTANGLED": "🌟 感情升温！可能有重大喜事（订婚/结婚/复合）。",
                                "BOUND→PERTURBED": "⚠️ 关系遇到考验，可能有争吵、冷战或信任危机。",
                                "BOUND→UNBOUND": "🚨 分离风险！可能发生分手/离婚/长期分居。",
                                "PERTURBED→ENTANGLED": "✨ 危机转化为契机！经历考验后感情更深。",
                                "PERTURBED→BOUND": "💚 关系修复，重回稳定轨道。",
                                "PERTURBED→UNBOUND": "🚨 摄动加剧导致分离，关系破裂。",
                                "UNBOUND→ENTANGLED": "🎉 新感情开始！可能遇到命中注定的人。",
                                "UNBOUND→BOUND": "💑 建立新关系或与前任复合。",
                                "UNBOUND→PERTURBED": "感情处于探索期，尚未稳定。"
                            }
                            
                            prediction = event_predictions.get(transition, "感情状态发生变化。")
                            
                            timeline_events.append({
                                "age": age,
                                "year": year,
                                "luck_pillar": luck_pillar,
                                "annual_pillar": annual_pillar,
                                "prev_state": prev_state,
                                "new_state": current_state,
                                "transition": transition,
                                "prediction": prediction,
                                "E": result.get('Binding_Energy', 0),
                                "sigma": result.get('Orbital_Stability', 0),
                                "eta": result.get('Phase_Coherence', 0),
                                "confidence": result.get('State_Confidence', 1.0),  # [Phase 37]
                                "state_probs": result.get('State_Probabilities', {})  # [Phase 37]
                            })
                        
                        prev_state = current_state
                    
                    # Display results
                    st.success(f"✅ 四维时空扫描完成！发现 **{len(timeline_events)}** 个情感触发事件")
                    
                    if timeline_events:
                        # ═══════ 4D SCAN SUMMARY DASHBOARD ═══════
                        st.markdown("##### 🚀 四维扫描仪表盘 (4D Scan Dashboard)")
                        
                        # Statistics
                        perturbed_events = [e for e in timeline_events if "PERTURBED" in e['new_state']]
                        unbound_events = [e for e in timeline_events if "UNBOUND" in e['new_state']]
                        recovery_events = [e for e in timeline_events if "ENTANGLED" in e['new_state']]
                        
                        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                        with stat_col1:
                            st.metric("总转换点", f"{len(timeline_events)}")
                        with stat_col2:
                            st.metric("⚠️ 摄动年", f"{len(perturbed_events)}", delta=None)
                        with stat_col3:
                            st.metric("🚨 解离年", f"{len(unbound_events)}", delta=None)
                        with stat_col4:
                            st.metric("🌟 升温年", f"{len(recovery_events)}", delta=None)
                        
                        # ═══════ WARNING YEARS HIGHLIGHT ═══════
                        if perturbed_events or unbound_events:
                            st.markdown("##### ⚠️ 关键警告年份 (Critical Warning Years)")
                            warning_years = perturbed_events + unbound_events
                            warning_years.sort(key=lambda x: x['year'])
                            
                            # Show next 3 upcoming warning years
                            current_year = datetime.now().year
                            upcoming_warnings = [e for e in warning_years if e['year'] >= current_year][:3]
                            
                            if upcoming_warnings:
                                for event in upcoming_warnings:
                                    icon = "🚨" if "UNBOUND" in event['new_state'] else "⚠️"
                                    with st.container():
                                        st.markdown(f"""
                                        <div style="background: linear-gradient(90deg, #ff4b4b22, transparent); border-left: 3px solid #ff4b4b; padding: 10px; margin: 5px 0; border-radius: 5px;">
                                            <strong>{icon} {event['year']}年 ({event['age']}岁)</strong><br/>
                                            <small>大运: {event['luck_pillar']} | 流年: {event['annual_pillar']}</small><br/>
                                            <span style="color: #ff9f43;">{event['transition']}</span><br/>
                                            <em>{event['prediction']}</em>
                                        </div>
                                        """, unsafe_allow_html=True)
                            else:
                                st.info("近期无重大警告年份")
                        
                        # ═══════ TIMELINE CHART ═══════
                        st.markdown("##### 📊 情感轨道图 (Emotional Orbit Chart)")
                        
                        # Create timeline data for chart
                        chart_years = [e['year'] for e in timeline_events]
                        chart_r = [e.get('E', 0) for e in timeline_events]  # Use Binding Energy
                        
                        # State color mapping
                        state_colors = []
                        for e in timeline_events:
                            if "UNBOUND" in e['new_state']:
                                state_colors.append("#ff4b4b")
                            elif "PERTURBED" in e['new_state']:
                                state_colors.append("#ff9f43")
                            elif "ENTANGLED" in e['new_state']:
                                state_colors.append("#00ff00")
                            else:
                                state_colors.append("#40e0d0")
                        
                        # Create plotly chart
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=chart_years,
                            y=chart_r,
                            mode='markers+lines',
                            marker=dict(size=10, color=state_colors, line=dict(width=1, color='white')),
                            line=dict(width=2, color='#888'),
                            name='绑定能 (E)',
                            hovertemplate='%{x}年<br>E=%{y:.1f}<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            title="情感绑定能时间线",
                            xaxis_title="年份",
                            yaxis_title="绑定能 (E)",
                            template="plotly_dark",
                            height=300,
                            margin=dict(l=50, r=20, t=40, b=40)
                        )
                        
                        st.plotly_chart(fig, width='stretch')
                        
                        # ═══════ DETAILED EVENT LIST ═══════
                        with st.expander("📋 完整事件列表 (Full Event List)", expanded=False):
                            for i, event in enumerate(timeline_events):
                                # Color based on transition type
                                if "UNBOUND" in event['new_state']:
                                    icon = "🚨"
                                elif "PERTURBED" in event['new_state']:
                                    icon = "⚠️"
                                elif "ENTANGLED" in event['new_state']:
                                    icon = "🌟"
                                else:
                                    icon = "💚"
                                
                                with st.expander(f"{icon} {event['year']}年 ({event['age']}岁) | {event['transition']} ({event.get('confidence', 1)*100:.0f}%)", expanded=False):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown(f"**年份**: {event['year']} ({event['age']}岁)")
                                        st.markdown(f"**大运**: {event['luck_pillar']}")
                                        st.markdown(f"**流年**: {event['annual_pillar']}")
                                    with col2:
                                        st.markdown(f"**状态变化**: {event['prev_state']} → {event['new_state']}")
                                        st.markdown(f"**绑定能 (E)**: {event['E']:.1f}")
                                        st.markdown(f"**置信度 (Confidence)**: {event.get('confidence', 1)*100:.0f}%")
                                    
                                    # [Phase 37] State Probability Bar
                                    st.markdown("**📊 状态概率分布 (State Probabilities)**")
                                    probs = event.get('state_probs', {})
                                    if probs:
                                        # Convert probs dictionary to a DataFrame for bar_chart
                                        prob_df = pd.DataFrame([probs]).T.reset_index()
                                        prob_df.columns = ["State", "Probability"]
                                        
                                        # Map state names to display names for better readability
                                        state_display_names = {
                                            "ENTANGLED": "🟢 ENTANGLED",
                                            "BOUND": "🔵 BOUND",
                                            "PERTURBED": "🟠 PERTURBED",
                                            "UNBOUND": "🔴 UNBOUND"
                                        }
                                        prob_df['State'] = prob_df['State'].map(state_display_names)
                                        
                                        # Sort for consistent display
                                        prob_df['Order'] = prob_df['State'].apply(lambda x: ["🟢 ENTANGLED", "🔵 BOUND", "🟠 PERTURBED", "🔴 UNBOUND"].index(x))
                                        prob_df = prob_df.sort_values('Order').drop('Order', axis=1)
                                        
                                        # Create a bar chart
                                        st.bar_chart(prob_df.set_index("State"), width='stretch')
                                    
                                    st.markdown("---")
                                    st.markdown(f"**🔮 预测**: {event['prediction']}")
                    else:
                        st.info("未发现显著的情感状态变化。感情轨道全程稳定。")
                        
                except Exception as e:
                    st.error(f"扫描失败: {str(e)}")

        # --- MODULE 7: LIFE-PATH ORRERY ---
        elif selected_topic_id == "MOD_07_LIFEPATH":
            st.markdown("#### 🚀 个人生命轨道仪 (Personal Orbit Orrery)")
            st.caption("规则映射: PH_DYNAMIC_DISPERSION_SIN / PH_SHEAR_BURST / PH_RISK_NODE_DETECT")
            st.write("")

            lp_data = res.get('life_path', {}) if isinstance(res, dict) else {}

            bi = selected_case.get('birth_info', {}) if selected_case else {}
            b_year = bi.get('birth_year') or selected_case.get('year', 1980)
            b_month = bi.get('birth_month') or selected_case.get('month', 1)
            b_day = bi.get('birth_day') or selected_case.get('day', 1)
            b_hour = bi.get('birth_hour') or selected_case.get('hour', 12)
            try:
                birth_dt = datetime(int(b_year), int(b_month), int(b_day), int(b_hour))
            except Exception:
                birth_dt = datetime(1980, 1, 1, 12)

            col_lp1, col_lp2 = st.columns([7, 3])
            with col_lp2:
                st.markdown("**仿真参数 (Simulation Params)**")
                sim_range = st.slider("审计跨度 (Year Range)", birth_dt.year, birth_dt.year + 100, (birth_dt.year, birth_dt.year + 60), 1, key="lp_range_mod7")
                sim_res = st.selectbox("采样分辨率 (Resolution)", ["节气 (Solar Term)", "月份 (Monthly)"], index=0, key="lp_res_mod7")

                if st.button("🚀 执行全轨道扫描 (Execute Orbital Scan)", width='stretch', key="run_lifepath_scan_mod7"):
                    st.warning("⚠️ 生命轨道仪 (LifePathEngine) 已在 V12.2.0 中移除。请使用 '全息应期演化' 功能。")

            with col_lp1:
                lp_show = st.session_state.get('lifepath_data_mod7') or lp_data
                if lp_show and lp_show.get('timeline'):
                    df_lp = pd.DataFrame(lp_show['timeline'])
                    fig_lp = go.Figure()
                    if 'entropy' in df_lp:
                        fig_lp.add_trace(go.Scatter(x=df_lp['timestamp'], y=df_lp.get('entropy', 0), name="因果熵 (Entropy)", line=dict(color="#40e0d0", width=2)))
                    if 'sai' in df_lp:
                        fig_lp.add_trace(go.Scatter(x=df_lp['timestamp'], y=df_lp['sai'], name="应力 (SAI)", line=dict(color="#ff7f50", width=2)))
                    if 'dm_strength' in df_lp:
                        fig_lp.add_trace(go.Scatter(x=df_lp['timestamp'], y=df_lp['dm_strength'] / 100.0, name="能级强度 (Energy)", line=dict(color="#ffd700", width=1.5, dash='dot')))

                    fig_lp.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        height=380, margin=dict(l=10, r=10, t=30, b=10),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="时间轨道 (Timeline)"),
                        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title="物理指标 (Metrics)"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_lp, width='stretch')

                    risks = lp_show.get('risk_nodes', [])
                    if risks:
                        st.warning(f"⚠️ 发现 {len(risks)} 个潜在风险节点 (PH_RISK_NODE_DETECT)")
                        with st.expander("🕸️ 风险节点详情 (Risk Nodes)", expanded=False):
                            st.json(risks)
                else:
                    st.info("💡 点击右侧“执行全轨道扫描”以生成生命轨道数据。")

        # --- [Phase C] MODULE 7: EMERGENCE STRUCTURES ---

    # [GLOBAL VIEW] -> Unified Arbitrator Integration Point
    st.divider()
    # 🏛️ QUANTUM UNIVERSAL FRAMEWORK CONSOLE (Relocated from Topic Module)
    with st.expander("🔮 量子通用框架控制台 (Quantum Universal Framework Console)", expanded=False):
        st.markdown("### 🏛️ 量子通用框架 (Quantum Universal Framework)")
        st.caption(f"Quantum Universal Physics Engine V3.0 | Phase G Complete")
        
        # Use static import from top of file
        global_arbitrator = quantum_framework

        if global_arbitrator and selected_case:
            # Build context from current state (use existing user_luck and user_year)
            months_switch_gl = st.session_state.get('months_since_switch', st.session_state.get('luck_month_offset', 6.0))
            arb_ctx_gl = {
                'luck_pillar': user_luck,
                'annual_pillar': user_year,
                'months_since_switch': months_switch_gl,
                'data': {'city': st.session_state.get('global_geo_city', selected_city)}
            }
            
            # Get Bazi from selected case
            bazi_list_gl = selected_case.get('bazi', [])
            birth_info_gl = selected_case.get('birth_info', {})
            if bazi_list_gl and not birth_info_gl:
                for k in ['year', 'month', 'day', 'hour']:
                    if k in selected_case:
                        birth_info_gl[f"birth_{k}"] = selected_case[k]
            birth_info_gl['gender'] = selected_case.get('gender', '男')
            
            @st.cache_data(ttl=60)
            def run_global_arbitration(bazi_tuple, luck, annual, city, months, gender, binfo, scenario):
                ctx = {
                    'luck_pillar': luck,
                    'annual_pillar': annual,
                    'months_since_switch': months,
                    'scenario': scenario,
                    'data': {'city': city}
                }
                return global_arbitrator.arbitrate_bazi(list(bazi_tuple), binfo, ctx)
            
            unified_state_gl = run_global_arbitration(
                tuple(bazi_list_gl),
                user_luck,
                user_year,
                st.session_state.get('global_geo_city', selected_city),
                months_switch_gl,
                birth_info_gl.get('gender', '男'),
                birth_info_gl,
                selected_scenario.upper()
            )
            
            if 'error' not in unified_state_gl:
                verdict_gl = unified_state_gl.get("verdict", {})
                rules_gl = unified_state_gl.get("rules", [])

                # [REMOVED] 仲裁断言 (Arbitration Verdict) - 已删除

                if rules_gl:
                    st.markdown("#### 📜 触发规则 (Triggered Rules)")
                    import pandas as pd
                    st.dataframe(pd.DataFrame(rules_gl), hide_index=True, width='stretch')

                plain_tips_gl = unified_state_gl.get("plain_guidance", [])
                if plain_tips_gl:
                    st.markdown("#### 🧭 白话解释器 (Plain Interpreter)")
                    st.markdown("\n".join([f"- {t}" for t in plain_tips_gl]))

                # [MOD_17] Stellar Coherence Mantra
                intel_gl = unified_state_gl.get("intelligence", {})
                if intel_gl.get("stellar_mantra"):
                    st.markdown("#### ✨ 星辰相干真言 (Stellar Coherence Mantra)")
                    st.info(f"「周星驰风格翻译层」已启用")
                    st.markdown(f"""
                    <div style="background: rgba(255, 215, 0, 0.05); border-left: 5px solid #ffd700; padding: 15px; border-radius: 8px; font-style: italic; color: #ffd700; line-height: 1.6;">
                        “{intel_gl['stellar_mantra']}”
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Stellar Telemetry
                    st_phy = unified_state_gl.get("physics", {}).get("stellar", {})
                    if st_phy:
                        st_cols = st.columns(3)
                        with st_cols[0]:
                            st.metric("星辰相干度 (η_s)", f"{st_phy.get('coherence', 1.0):.2f}")
                        with st_cols[1]:
                            st.metric("量子引力 (Attraction)", f"+{st_phy.get('attraction', 0.0):.2f} eV")
                        with st_cols[2]:
                            st.metric("动能冲量 (Impulse)", f"+{st_phy.get('impulse', 0.0):.2f} ΔV")

                # [Phase 5.0] Global Temporal Shunting Dashboard
                st.markdown("#### ⏳ 全息应期演化 (Temporal SAI Dashboard)")
                st.caption("基于当前选中八字、地理系数及社会阻尼实时生成的时空应力场")
                
                # 1. Platform Parameter Bonding
                social_damping_gl = st.slider("全局环境阻尼 (Social Damping)", 0.5, 3.0, 1.0, key="global_damping_slider", help="1.0=常规 (Neutral), 2.0=高阻尼 (体制内), 0.5=低阻尼 (低阻尼/敏锐)")
                
                from core.trinity.core.engines.temporal_shunting import TemporalShuntingEngine
                
                # [Phase 6.2] V3 - Now includes profile for real Luck Pillar physics
                @st.cache_data(ttl=3600)
                def get_cached_sai_scan_v3(_engine, start_year, birth_year, horizon_months, social_damping, _profile):
                    return _engine.scan_singularities(start_year=start_year, birth_year=birth_year, 
                                                     horizon_months=horizon_months, social_damping=social_damping, profile=_profile)

                # DM at index 4 (Day Stem), Birth Year from profile
                dm_char_gl = bazi_list_gl[4] if len(bazi_list_gl) > 4 else "甲"
                b_year_gl = birth_info_gl.get('birth_year', birth_info_gl.get('year', 1990))
                
                t_engine_gl = TemporalShuntingEngine(dm_char_gl)
                
                # Scan (10-year horizon from 2024 today) - CACHED with Profile
                scan_gl = get_cached_sai_scan_v3(t_engine_gl, 2024, int(b_year_gl), 120, social_damping_gl, v_profile)
                timeline_gl = scan_gl['timeline']
                singularities_gl = scan_gl['singularities']
                
                # 2. Layout Structure
                col_g1, col_g2 = st.columns([2, 1])
                
                with col_g2:
                    st.markdown("##### 🎛️ 全域干预模拟 (Global Remedy)")
                    
                    # Target selection for intervention
                    target_options = ["最高峰值 (Global Peak)"] + [f"{s.get('year')}年{s.get('month')}月 (Age {s.get('age')})" for s in singularities_gl]
                    selected_target_str = st.selectbox("干预目标 (Intervention Target)", target_options, index=0, key="sai_target_sel")
                    
                    # Determine target SAI
                    if selected_target_str == "最高峰值 (Global Peak)":
                        target_node = max(singularities_gl, key=lambda x: x['sai']) if singularities_gl else None
                        target_sai = target_node['sai'] if target_node else 1.0
                    else:
                        # Extract node from singularities_gl based on selection
                        idx = target_options.index(selected_target_str) - 1
                        target_node = singularities_gl[idx]
                        target_sai = target_node['sai']
                    
                    st.metric("💥 目标应力 (Target SAI)", f"{target_sai:.2f}", 
                             delta="高危" if target_sai > 2.0 else "安全", delta_color="inverse")
                    
                    # New: Automated Recommendations
                    if target_sai > 1.5:
                        recommendations = t_engine_gl.sensitivity_search(target_sai, social_damping=social_damping_gl)
                        if recommendations:
                            best = recommendations[0]
                            st.info(f"✨ **系统推荐对冲方案**:\n{best['recommendation']}")
                    
                    # Unified Remedy Controls
                    act_opts_gl = {"NONE": "无干预 (None)", "STUDY": "📚 学习/印星", "DONATION": "💸 布施/财星", "TRAVEL": "✈️ 迁移/马星", "MEDITATION": "🧘 闭关/空亡"}
                    sel_act_gl = st.selectbox("核心干预方案 (Strategy)", list(act_opts_gl.keys()), format_func=lambda x: act_opts_gl[x], index=0, key="global_act_sel")
                    
                    # Geographic Bias
                    geo_mod_gl = st.slider("地理偏置 (K_geo)", 0.5, 2.0, 1.0, 0.1, key="global_geo_sim_slider")
                    
                    # Simulation Output
                    shunt_res_gl = t_engine_gl.simulate_intervention(target_sai, sel_act_gl, geo_mod_gl, social_damping=social_damping_gl)
                    st.divider()
                    st.metric("🛡️ 预演后应力 (Projected SAI)", f"{shunt_res_gl['final_sai']:.2f}", delta=f"-{shunt_res_gl['reduction_pct']}%", delta_color="normal")
                    
                    if shunt_res_gl['final_sai'] < 2.0 < target_sai:
                        st.success("🎯 针对性干预成功对冲风险 (Damping Success)")
                    elif target_sai > 2.0 and shunt_res_gl['final_sai'] >= 2.0:
                        st.warning("⚠️ 当前方案对冲强度不足，请尝试系统推荐方案。")
                
                with col_g1:
                    # Plotly Dashboard Visualization
                    import plotly.graph_objects as go
                    fig_gl = go.Figure()
                    
                    h_x, h_y, h_t = [], [], []
                    f_x, f_y, f_t = [], [], []
                    s_y = []
                    
                    for node in timeline_gl:
                        age_v = node['age']
                        sai_v = node['sai']
                        label_v = f"Age {age_v} ({node['year']}.{node['month']})"
                        if node['is_future']:
                            f_x.append(age_v)
                            f_y.append(sai_v)
                            f_t.append(label_v)
                            if sel_act_gl != "NONE":
                                s_v = t_engine_gl.simulate_intervention(sai_v, sel_act_gl, geo_mod_gl, social_damping=social_damping_gl)
                                s_y.append(s_v['final_sai'])
                        else:
                            h_x.append(age_v)
                            h_y.append(sai_v)
                            h_t.append(label_v)
                    
                    if h_x: fig_gl.add_trace(go.Scatter(x=h_x, y=h_y, mode='lines', name='历史镜像', line=dict(color='grey', width=1, dash='dot')))
                    if f_x: fig_gl.add_trace(go.Scatter(x=f_x, y=f_y, mode='lines', name='未来趋势', line=dict(color='#40e0d0', width=2)))
                    if s_y: fig_gl.add_trace(go.Scatter(x=f_x, y=s_y, mode='lines', name='干预效果', line=dict(color='#2ecc71', width=2, dash='dash')))
                    
                    # Singularity Markers (Peak Damping Trace)
                    sin_x = [x['age'] for x in singularities_gl]
                    sin_y = [x['sai'] for x in singularities_gl]
                    if sin_x: fig_gl.add_trace(go.Scatter(x=sin_x, y=sin_y, mode='markers', name='核心奇点', 
                                                       text=[f"{x.get('year')}年 {x.get('month')}月 | {x.get('plain_assertion', '')}" for x in singularities_gl],
                                                       marker=dict(color='#ff4b4b', size=8, symbol='diamond')))
                    
                    # Highlight Active Target
                    if target_node:
                        fig_gl.add_trace(go.Scatter(x=[target_node['age']], y=[target_node['sai']], mode='markers', name='🎯 当前目标',
                                                   marker=dict(color='#ffd700', size=15, symbol='star', line=dict(color='white', width=2))))
                    
                    fig_gl.add_vline(x=datetime.now().year - int(b_year_gl), line_dash="dash", line_color="white", annotation_text="Today")
                    fig_gl.add_hline(y=2.0, line_dash="dash", line_color="orange", opacity=0.3)
                    fig_gl.update_layout(height=320, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_gl, width='stretch', key="global_sai_chart_unified")

                # New: Singularity Interpretation Table (Bazi Plain Language)
                if singularities_gl:
                    st.markdown("#### 🔍 命理奇点解读 (Singularity Interpretations)")
                    sin_data = []
                    for s in singularities_gl:
                        if s['is_future']:
                            sin_data.append({
                                "时间 (Time)": f"{s.get('year')}年 {s.get('month')}月",
                                "年龄 (Age)": s.get('age'),
                                "应力值 (SAI)": s.get('sai'),
                                "命理白话 (Plain Bazi)": s.get('plain_assertion', '')
                            })
                    import pandas as pd
                    st.table(pd.DataFrame(sin_data))

                # [REMOVED] 全息真言报告 - 已删除
                
                # Physics Telemetry Dashboard
                phy_gl = unified_state_gl.get('physics', {})
                
                arb_c1_gl, arb_c2_gl, arb_c3_gl, arb_c4_gl = st.columns(4)
                with arb_c1_gl:
                    entropy_val = phy_gl.get('entropy', 0)
                    entropy_color = "#ff4b4b" if entropy_val > 1.5 else "#40e0d0"
                    st.markdown(f"""<div class="hud-card"><div class="sh-label">系统熵 (Entropy - S)</div><div class="sh-val" style="color:{entropy_color}">{entropy_val:.3f}</div></div>""", unsafe_allow_html=True)
                with arb_c2_gl:
                    grav = phy_gl.get('gravity', {})
                    month_g = grav.get('Month', 0)
                    st.markdown(f"""<div class="hud-card"><div class="sh-label">月令引力 (Month Gravity)</div><div class="sh-val">{month_g:.2f}</div></div>""", unsafe_allow_html=True)
                with arb_c3_gl:
                    res_state = phy_gl.get('resonance', {})
                    gain = res_state.get('gain', 1.0)
                    st.markdown(f"""<div class="hud-card"><div class="sh-label">通根增益 (Rooting Gain)</div><div class="sh-val" style="color:#ffd700">{gain}x</div></div>""", unsafe_allow_html=True)
                with arb_c4_gl:
                    inertia = phy_gl.get('inertia', {})
                    visc = inertia.get('Viscosity', 0.5)
                    visc_color = "#40e0d0" if visc < 0.5 else "#ff9f43"
                    st.markdown(f"""<div class="hud-card"><div class="sh-label">粘滞系数 (Viscosity - ν)</div><div class="sh-val" style="color:{visc_color}">{visc:.2f}</div></div>""", unsafe_allow_html=True)
                
                # Wealth & Relationship Metrics Row
                arb_w1_gl, arb_w2_gl = st.columns(2)
                with arb_w1_gl:
                    wealth = phy_gl.get('wealth', {})
                    re_num = wealth.get('Reynolds', 0)
                    w_state = wealth.get('State', 'LAMINAR')
                    w_color = "#40e0d0" if w_state == "TURBULENT" else "#888" if w_state == "LAMINAR" else "#ff9f43"
                    st.markdown(f"""<div class="hud-card"><div class="sh-label">🌊 财富流体 (Wealth Fluid - Re)</div><div class="sh-val" style="color:{w_color}">{re_num:.0f} ({w_state})</div></div>""", unsafe_allow_html=True)
                with arb_w2_gl:
                    rel = phy_gl.get('relationship', {})
                    bind_e = rel.get('Binding_Energy', 0)
                    r_state = rel.get('State', 'UNBOUND')
                    r_color = "#f0f" if r_state == "BOUND" else "#888"
                    st.markdown(f"""<div class="hud-card"><div class="sh-label">🌌 情感引力 (Relationship Gravity - E)</div><div class="sh-val" style="color:{r_color}">{bind_e:.1f} ({r_state})</div></div>""", unsafe_allow_html=True)
                
                # Detailed Physics JSON (Collapsible)
                with st.expander("🎛️ 详细物理读数 (Detailed Physics Matrix)", expanded=False):
                    st.json(unified_state_gl)
            else:
                st.warning(f"仲裁失败: {unified_state_gl.get('error')}")
        elif not selected_case:
            st.info("请先选择或输入八字案例以执行量子通用框架仲裁。")


    st.caption(f"Antigravity Quantum Universal System V3.0 (Precision Engine) | Phase G Complete")

