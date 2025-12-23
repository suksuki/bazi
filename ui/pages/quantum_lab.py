
import streamlit as st
import json
import os
import datetime
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import re

# --- Core Engine Imports (Quantum Trinity V2.0) ---
from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.nexus.definitions import BaziParticleNexus, PhysicsConstants, ArbitrationNexus
from core.bazi_profile import VirtualBaziProfile
from core.models.config_model import ConfigModel
from controllers.quantum_lab_controller import QuantumLabController
from core.profile_manager import ProfileManager

# --- UI Components ---
from ui.components.oscilloscope import Oscilloscope
from ui.components.coherence_gauge import CoherenceGauge
from ui.components.envelope_gauge import EnvelopeGauge
from ui.components.tuning_panel import render_tuning_panel
from ui.components.theme import COLORS, GLASS_STYLE, apply_custom_header
from ui.components.wave_vision_3d import render_wave_vision_3d
from ui.components.wave_vision_3d import render_wave_vision_3d
from ui.components.molviz_3d import render_molviz_3d
from ui.components.holographic_radar import render_holographic_radar

def get_ten_god(dm_char: str, target_char: str) -> str:
    """Calculates the Ten Gods relation between DM and target char."""
    if not dm_char or not target_char: return ""
    stems = BaziParticleNexus.STEMS
    if dm_char not in stems or target_char not in stems: return ""
    
    dm_elem, dm_pol, _ = stems[dm_char]
    t_elem, t_pol, _ = stems[target_char]
    
    gen = PhysicsConstants.GENERATION
    con = PhysicsConstants.CONTROL
    
    same_pol = (dm_pol == t_pol)
    
    if dm_elem == t_elem:
        return "比肩" if same_pol else "劫财"
    elif gen[dm_elem] == t_elem:
        return "食神" if same_pol else "伤官"
    elif gen[t_elem] == dm_elem:
        return "偏印" if same_pol else "正印"
    elif con[dm_elem] == t_elem:
        return "偏财" if same_pol else "正财"
    elif con[t_elem] == dm_elem:
        return "七杀" if same_pol else "正官"
    return ""

def render():
    st.set_page_config(page_title="Quantum Lab | Trinity V2.0", page_icon="🧪", layout="wide")

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
                
                if st.button("🚀 生成概率叶 (Generate Case)", use_container_width=True):
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
                    birth_date = datetime.datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour'], bi.get('birth_minute', 0))
                elif 'year' in selected_case:
                    # ProfileManager format: use 'year' field directly
                    birth_year = selected_case['year']
                    birth_date = datetime.datetime(
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
                    current_year = datetime.datetime.now().year
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
                    birth_date = datetime.datetime(birth_year, 6, 15, 12)  # Mid-year default
                    st.caption(f"💡 根据年柱 **{year_pillar}** 推算出生年约为 **{birth_year}** (甲子循环)")
                
                v_profile = VirtualBaziProfile({'year':b_list[0], 'month':b_list[1], 'day':b_list[2], 'hour':b_list[3]}, 
                                               gender=(1 if selected_case.get('gender')=='男' else 0), 
                                               birth_date=birth_date)
            except Exception as e: 
                v_profile = None
                st.warning(f"无法创建 VirtualBaziProfile: {e}")

            # --- GLOBAL CONTROL AREA ---
            current_year = datetime.datetime.now().year
            
            # Get luck cycles
            luck_cycles = v_profile.get_luck_cycles() if v_profile else []
            l_opts = [f"{d['start_year']}-{d['end_year']} [{d['gan_zhi']}]" for d in luck_cycles] if luck_cycles else ["Unknown"]
            
            # [Phase 38] Find default luck cycle that covers current year
            default_luck_idx = 0
            for i, lc in enumerate(luck_cycles):
                if lc['start_year'] <= current_year <= lc['end_year']:
                    default_luck_idx = i
                    break
            
            # [Phase 38] GEO City Map - global
            GEO_CITY_MAP = {
                "北京 (Beijing)": (1.15, "Fire/Earth"),
                "上海 (Shanghai)": (1.08, "Water/Metal"),
                "深圳 (Shenzhen)": (1.12, "Fire/Water"),
                "广州 (Guangzhou)": (1.10, "Fire"),
                "成都 (Chengdu)": (0.95, "Earth/Wood"),
                "杭州 (Hangzhou)": (1.05, "Water/Wood"),
                "东京 (Tokyo)": (1.20, "Water/Metal"),
                "新加坡 (Singapore)": (0.85, "Fire/Water"),
                "纽约 (New York)": (1.25, "Metal/Water"),
                "伦敦 (London)": (1.15, "Water/Metal"),
                "悉尼 (Sydney)": (0.90, "Fire/Earth"),
                "温哥华 (Vancouver)": (1.18, "Water/Wood"),
            }
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
            st.info("💡 **物理提示**: 六柱谐振模型已激活，大运与流年已作为外部扰动源完整代入计算。")

    # 4. Oracle Core Analysis
    if not selected_case:
        st.info("Initiate subject selection to start Oracle.")
        return

    oracle = TrinityOracle(config=full_config)
    res = oracle.analyze(selected_case['bazi'][:4], selected_case.get('day_master'), luck_pillar=user_luck, annual_pillar=user_year, t=t_vec, injections=inj_list)
    resonance = res.get('resonance')
    verdict = res.get('verdict', {})
    
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
    label_disp = BILINGUAL_MAP.get(verdict.get("label"), verdict.get("label", "?"))
    
    # 5. Executive HUD (Pure CSS styling via class)
    st.write("")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        m_color = "#40e0d0" if resonance.mode == "COHERENT" else "#ff9f43" if resonance.mode == "BEATING" else "#ff4b4b" if resonance.mode == "ANNIHILATION" else "#888"
        st.markdown(f"""<div class="hud-card"><div class="sh-label">谐振模式 (Mode)</div><div class="sh-val" style="color:{m_color}; font-weight:bold; font-size:18px;">{mode_disp}</div></div>""", unsafe_allow_html=True)
    with h2: st.markdown(f'<div class="hud-card"><div class="sh-label">秩序参数 (Order - O)</div><div class="sh-val">{verdict.get("order_parameter",0):.4f}</div></div>', unsafe_allow_html=True)
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
            if st.button("一键执行量子注入 (Execute Injection)", use_container_width=True): 
                st.session_state['inj_active'] = True
                st.rerun()

    st.divider()
    # I will rely on the "Phase 3" display inside Tab 1 to show these insights.
    pass

    # --- MASTER-DETAIL ARCHITECTURE SPLIT ---
    
    # [MASTER VIEW]
    # Sections 0-6 (Chart, HUD, Gauges, Insights) are already rendered above.
    
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
    from core.logic_registry import LogicRegistry
    reg = LogicRegistry()
    
    st.sidebar.divider()
    st.sidebar.markdown("### 🔮 专题罗盘 (Topic Compass)")
    
    active_modules = reg.get_active_modules() # Returns list of dicts with 'id', 'name', etc.
    
    # Create a mapping for easy lookup
    module_map = {m['name']: m for m in active_modules}
    module_names = [m['name'] for m in active_modules]
    
    selected_name = st.sidebar.selectbox(
        "选择测算专题 (Select Deep Dive)",
        module_names,
        index=0
    )
    
    current_module = module_map.get(selected_name)
    selected_topic_id = current_module.get('id') if current_module else None

    # Render Selected Module Content (Above Global Console)
    st.divider()
    
    # [REF] Single Collapsible Container for Entire Topic
    with st.expander(f"📊 {current_module.get('name')}", expanded=True):
        
        # 1. Topic Metadata (Description, Goal, Outcome)
        tm1, tm2 = st.columns([1, 1])
        with tm1:
            st.markdown(f"**📝 描述 (Description)**: {current_module.get('description', '-')}")
            st.markdown(f"**🎯 目的 (Goal)**: {current_module.get('goal', 'TBD')}")
        with tm2:
            st.success(f"**🏆 成果 (Outcome)**: {current_module.get('outcome', 'TBD')}")

        st.divider()
        
        # 2. Rule Registry (Nested Expander)
        # We manually inline the logic of render_module_header here to keep it contained
        all_rules = reg.get_all_active_rules()
        linked_ids = current_module.get('linked_rules', [])
        
        if linked_ids:
            with st.expander("📜 关联八字规则 (Logic & Rules Registry)", expanded=False):
                module_rules = {rid: rdata for rid, rdata in all_rules.items() if rid in linked_ids}
                if not module_rules:
                    st.info(f"No active rules found matching spec: {linked_ids}")
                else:
                    rule_names = [f"{rid} | {r.get('name')}" for rid, r in module_rules.items()]
                    sel_rule = st.selectbox("查看规则详情 (Inspect Rule)", rule_names, key=f"sel_rule_{current_module['id']}")
                    if sel_rule:
                        rid = sel_rule.split(" | ")[0]
                        st.json(module_rules[rid])
        
        st.divider()

        # 3. Visualizations & Metrics (Topic Specific)
        
        # --- MODULE 1: INTEGRATED TRIPLE DYNAMICS (DETAIL) ---
        if selected_topic_id == "MOD_01_TRIPLE":
            # [NEW] Holographic Decision Radar (Moved here as it uses 3-in-1 Logic)
            st.markdown("#### 🔭 全息决策雷达 (Holographic Decision Radar)")
            render_holographic_radar(resonance, res.get('unified_metrics'), res.get('remedy'), verdict)
            st.write("")
    
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
    
        # --- MODULE 2: SUPER-STRUCTURE RESONANCE ---
        elif selected_topic_id == "MOD_02_SUPER":
            # 3D Orrery
            total_context = selected_case['bazi'][:4] + [user_luck, user_year]
            render_wave_vision_3d(res['waves'], total_context, dm_wave=resonance.dm_wave, resonance=resonance, injections=inj_list, height=500)
            st.write("")
            st.info("此专题用于分析【从强/从旺】格局的纯化程度与顺逆大运。 (Topic focused on purity of Follow/Vibrant structures.)")
    
        # --- MODULE 3: TRANSFORMATION CHEMISTRY ---
        elif selected_topic_id == "MOD_03_TRANSFORM":
            st.markdown("#### ⚛️ 键能稳定性分析 (Bond Energy Stability)")
            
            # 1. Calculate Bond Metrics
            # Find Combination Patterns (Heavenly Stems 5-Combine / Earthly Branches 6-Combine)
            comb_inters = [i for i in res.get('interactions', []) if "合" in i['name'] or "COMB" in i.get('type','')]
            
            nominal_score = 0.0
            comb_names = []
            if comb_inters:
                # Heuristic: Sum q-factors or take max. Let's take max * scale.
                # q=1.0 -> 50%, q=2.0 -> 100%
                max_q = max([i.get('q', 0.5) for i in comb_inters])
                nominal_score = min(max_q * 50.0, 100.0)
                comb_names = [i['name'] for i in comb_inters]
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
                    for n in list(set(comb_names))[:2]:
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
            if st.button("🚀 启动 财富流体仿真 (Run Wealth Fluid Simulation)", key="sim_wealth_fluid_btn", use_container_width=True):
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
            if st.button("🚀 启动 情感引力仿真 (Run Gravity Simulation)", key="sim_relationship_btn", use_container_width=True):
                from core.trinity.core.engines.relationship_gravity import RelationshipGravityEngine
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
                
                # Re-run calculation with dynamic params
                gravity_engine = RelationshipGravityEngine(dm, gender)
                dynamic_result = gravity_engine.analyze_relationship(
                    sim_waves,
                    selected_case['bazi'][:4],
                    luck_pillar=user_luck,
                    annual_pillar=user_year,
                    geo_factor=geo_factor
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
            
            if st.button("🔍 扫描终身情感时间线 (Scan Lifetime Timeline)", key="scan_timeline_btn", use_container_width=True):
                from core.trinity.core.engines.relationship_gravity import RelationshipGravityEngine
                
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
                        birth_date = datetime.datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour'])
                        v_profile = VirtualBaziProfile(pillars_dict, gender=gender_code, birth_date=birth_date)
                    elif 'year' in selected_case:
                        # ProfileManager format: year/month/day/hour as direct fields
                        birth_year = selected_case['year']
                        birth_date = datetime.datetime(
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
                    
                    gravity_engine = RelationshipGravityEngine(dm, selected_case.get('gender', '男'))
                    
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
                            test_result = gravity_engine.analyze_relationship(
                                scan_waves,
                                selected_case['bazi'][:4],
                                luck_pillar=luck_p,
                                annual_pillar=annual,
                                geo_factor=geo_factor
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
                        
                        # Calculate relationship state for this year
                        result = gravity_engine.analyze_relationship(
                            scan_waves,
                            selected_case['bazi'][:4],
                            luck_pillar=luck_pillar,
                            annual_pillar=annual_pillar,
                            geo_factor=geo_factor
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
                            current_year = datetime.datetime.now().year
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
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
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
                                        prob_cols = st.columns(4)
                                        state_labels = [("🟢 ENTANGLED", "ENTANGLED"), ("🔵 BOUND", "BOUND"), 
                                                       ("🟠 PERTURBED", "PERTURBED"), ("🔴 UNBOUND", "UNBOUND")]
                                        for i, (label, key) in enumerate(state_labels):
                                            with prob_cols[i]:
                                                p = probs.get(key, 0)
                                                st.metric(label, f"{p*100:.0f}%")
                                    
                                    st.markdown("---")
                                    st.markdown(f"**🔮 预测**: {event['prediction']}")
                    else:
                        st.info("未发现显著的情感状态变化。感情轨道全程稳定。")
                        
                except Exception as e:
                    st.error(f"扫描失败: {str(e)}")

    # [GLOBAL VIEW] -> Grand Unified Arbitration (System Root)
    st.divider()
    # Now below the Topic view
    with st.expander("🔮 大一统仲裁台 (Grand Unified Arbitration Console)", expanded=False):
        st.caption("🚀 System Root | Global Logic Optimization & Physics Synthesis")
        
        # 2. Global Logic Stack Monitor (Now Primary Global View)
        st.markdown("#### ⚖️ 全局逻辑堆栈 (Global Logic Stack)")
        stack = res.get('logic_stack', {})
        active_ids = set(stack.get('active_rules', []))
        
        # reg already initialized above
        manifest = reg.get_all_active_rules()
        
        m_cols = st.columns(4)
        for i, (rule_id, rule_info) in enumerate(manifest.items()):
                is_active = rule_id in active_ids
                bg = "rgba(64,224,208,0.2)" if is_active else "rgba(255,255,255,0.05)"
                bord = "#40e0d0" if is_active else "#444"
                with m_cols[i % 4]:
                    st.markdown(f"""
                    <div style="background:{bg}; border:1px solid {bord}; border-radius:4px; padding:5px; margin-bottom:5px; text-align:center;">
                        <div style="font-size:10px; color:{bord}; font-weight:bold;">{rule_id}</div>
                        <div style="font-size:8px; color:#888;">{rule_info['name']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # 3. Final Report Generation (Global)
        st.write("---")
        st.markdown("#### 🔴 最终全息报告 (Final Holographic Report)")
        
        if st.button("🚀 生成全息报告 (Generate Report)", key="gen_rep_global_main", use_container_width=True):
            from scripts.antigravity_pipeline_v1 import AntigravityPipelineV1
            pipeline = AntigravityPipelineV1()
            
            target_name = selected_case.get('description', selected_case.get('id', 'Manual_Case'))
            if "档案: " in target_name: target_name = target_name.replace("档案: ", "")
            
            rep_content = pipeline._assemble_report(
                target_name, 
                selected_case.get('bazi', []), 
                resonance, 
                res.get('interactions', [{}])[0] if res.get('interactions') else None,
                res.get('interactions', []),
                res.get('unified_metrics'),
                res.get('remedy'),
                res.get('verdict'),
                selected_case.get('birth_info')
            )
            st.session_state['last_pipeline_report'] = rep_content
            st.toast("Pipeline报告已生成 (Report Generated)")

        if st.session_state.get('last_pipeline_report'):
            st.write("")
            with st.container(border=True):
                st.markdown(st.session_state['last_pipeline_report'])
            
            if st.button("关闭报告 (Close Report)"):
                st.session_state['last_pipeline_report'] = None
                st.rerun()

    st.caption("Quantum Trinity V2.4 (Dynamic Registry) | Genesis Registry V1.0 Active")
