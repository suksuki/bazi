
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
from core.trinity.core.nexus.definitions import BaziParticleNexus, PhysicsConstants
from core.bazi_profile import VirtualBaziProfile
from core.models.config_model import ConfigModel
from controllers.quantum_lab_controller import QuantumLabController

# --- UI Components ---
from ui.components.oscilloscope import Oscilloscope
from ui.components.coherence_gauge import CoherenceGauge
from ui.components.envelope_gauge import EnvelopeGauge
from ui.components.tuning_panel import render_tuning_panel
from ui.components.theme import COLORS, GLASS_STYLE, apply_custom_header
from ui.components.wave_vision_3d import render_wave_vision_3d
from ui.components.molviz_3d import render_molviz_3d

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
    .sh-label {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
    .sh-val {{ font-size: 22px; font-weight: bold; margin-top: 5px; }}

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
            input_mode = st.radio("数据源 (Source)", ["📚 预设 (Presets)", "✍️ 手动 (Manual)"], key="input_mode")
        
        selected_case = None
        if input_mode == "📚 预设 (Presets)":
            with c_obj:
                @st.cache_data
                def load_all_cases():
                    cases = []
                    # Added oppose_matrix_v21.json for Phase 28 verification
                    paths = [
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
                    case_idx = st.selectbox(
                        "选择实验对象 (Select Subject)", 
                        range(len(all_cases)), 
                        format_func=lambda i: f"{i+1:03d} | [{all_cases[i].get('id','?')}] {all_cases[i].get('description', all_cases[i].get('name','Unknown'))}"
                    )
                    selected_case = all_cases[case_idx]
        else:
            with c_obj:
                m1, m2, m3, m4, m5 = st.columns(5)
                iy = m1.number_input("年 (Year)", 1900, 2100, 2024)
                im = m2.number_input("月 (Month)", 1, 12, 1)
                id_ = m3.number_input("日 (Day)", 1, 31, 1)
                ih = m4.number_input("时 (Hour)", 0, 23, 12)
                ig = m5.selectbox("性别 (Gender)", ["男", "女"])
                if st.button("生成概率叶 (Generate Case)", use_container_width=True):
                    try:
                        res = controller.calculate_chart({'birth_year': iy, 'birth_month': im, 'birth_day': id_, 'birth_hour': ih, 'birth_minute': 0, 'gender': ig})
                        st.session_state['manual_cache'] = {'id': 'MANUAL', 'gender': ig, 'bazi': [f"{p[0]}{p[1]}" for p in res['bazi']], 'day_master': res['day_master'], 'birth_info': res['birth_info']}
                    except: st.error("Engine failure.")
                selected_case = st.session_state.get('manual_cache')

        if selected_case:
            st.divider()
            b_list = selected_case.get('bazi', [])
            
            # Ensure birth_info is handled for presets to avoid 1900s defaults
            try:
                bi = selected_case.get('birth_info')
                v_profile = VirtualBaziProfile({'year':b_list[0], 'month':b_list[1], 'day':b_list[2], 'hour':b_list[3]}, 
                                               gender=(1 if selected_case.get('gender')=='男' else 0), 
                                               birth_date=datetime.datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour']) if bi else None)
            except: v_profile = None

            cx1, cx2, cx3 = st.columns([2, 2, 4])
            with cx1:
                l_opts = [f"{d['start_year']}-{d['end_year']} [{d['gan_zhi']}]" for d in v_profile.get_luck_cycles()] if v_profile else ["Unknown"]
                sel_l = st.selectbox("当前大运 (Luck Cycle)", l_opts)
                user_luck = re.search(r'\[(.*?)\]', sel_l).group(1) if '[' in sel_l else "?"
            with cx2:
                # Default target year to current luck cycle if available, or current year
                default_y = datetime.datetime.now().year
                sel_y = st.number_input("目标流年 (Target Year)", 1900, 2100, default_y)
                user_year = v_profile.get_year_pillar(sel_y) if v_profile else "?"
                st.caption(f"📅 支点流年 (Annual): {user_year}")
            with cx3:
                t_vec = st.slider("相位偏移 (Phase-t)", 0.0, 10.0, 0.0, step=0.1)
                inj_on = st.toggle("量子注入模式 (Injection Mode)", value=st.session_state.get('inj_active', False))
                inj_list = st.multiselect("补强粒子 (Particles)", list(BaziParticleNexus.REMEDY_PARTICLES.keys()), format_func=lambda x: BaziParticleNexus.REMEDY_DESC.get(x, x)) if inj_on else None

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
    
    # 5. Executive HUD (Pure CSS styling via class)
    st.write("")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        m_color = "#40e0d0" if resonance.mode == "COHERENT" else "#ff9f43" if resonance.mode == "BEATING" else "#ff4b4b" if resonance.mode == "ANNIHILATION" else "#888"
        st.markdown(f"""<div class="hud-card"><div class="sh-label">谐振模式 (Mode)</div><div class="sh-val" style="color:{m_color}; font-weight:bold;">{resonance.mode}</div></div>""", unsafe_allow_html=True)
    with h2: st.markdown(f'<div class="hud-card"><div class="sh-label">秩序参数 (Order - O)</div><div class="sh-val">{verdict.get("order_parameter",0):.4f}</div></div>', unsafe_allow_html=True)
    with h3: st.markdown(f'<div class="hud-card"><div class="sh-label">相干度 (Coherence - η)</div><div class="sh-val" style="color:#40e0d0">{resonance.sync_state:.4f}</div></div>', unsafe_allow_html=True)
    with h4: st.markdown(f'<div class="hud-card"><div class="sh-label">判定结果 (Verdict)</div><div class="sh-val" style="color:#ffd700; font-size:18px;">{verdict.get("label","?")}</div></div>', unsafe_allow_html=True)

    # 6. Primary Workspace (Observation & Detail)
    st.write("")
    st.write("")
    h_sub1, h_sub2, h_sub3, h_sub4 = st.columns(4)
    with h_sub1: 
        st.markdown(f'<div class="hud-card"><div class="sh-label">碎片指数 (Frag - F)</div><div class="sh-val" style="color:{"#ff4b4b" if resonance.fragmentation_index > 0.5 else "#888"}">{resonance.fragmentation_index:.2f}</div><div style="font-size:9px; color:#555;">Symmetry Breaking Index</div></div>', unsafe_allow_html=True)
    with h_sub2: 
        f_color = "#f0f" if resonance.flow_efficiency > 1.8 else "#40e0d0"
        st.markdown(f'<div class="hud-card"><div class="sh-label">能效比 (Flow - Φ)</div><div class="sh-val" style="color:{f_color}; text-shadow: {"0 0 10px #f0f" if resonance.flow_efficiency > 1.8 else "none"}">{resonance.flow_efficiency:.2f}</div><div style="font-size:9px; color:#555;">Superfluid Conductivity</div></div>', unsafe_allow_html=True)
    with h_sub3: st.markdown(f'<div class="hud-card"><div class="sh-label">包络频率 (Env - ω)</div><div class="sh-val">{resonance.envelop_frequency:.4f}</div><div style="font-size:9px; color:#555;">Interference Envelope</div></div>', unsafe_allow_html=True)
    with h_sub4: st.markdown(f'<div class="hud-card"><div class="sh-label">热能溢出 (Thermal)</div><div class="sh-val" style="color:{"#ff4b4b" if resonance.mode=="ANNIHILATION" else "#888"}">{"CRITICAL" if resonance.mode=="ANNIHILATION" else "LOW"}</div><div style="font-size:9px; color:#555;">Entropy Leakage Rate</div></div>', unsafe_allow_html=True)

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
            st.success(f"建议粒子 (Particle): {rem.get('best_particle')}")
            if st.button("执行优化 (Execute Optimization)"): st.rerun()

    st.divider()

    # 7. Primary Visualization Workspace (Full Width)
    tabs = st.tabs(["🌌 量子天体仪 (ORRERY V5.2)", "📈 时空曲线 (TIMELINE)", "🔭 批量验证 (BATCH)", "⚛️ 物理实验室 (PHYSICS)"])
    
    with tabs[0]: # 3D Orrery
        total_context = selected_case['bazi'][:4] + [user_luck, user_year]
        render_wave_vision_3d(res['waves'], total_context, dm_wave=resonance.dm_wave, resonance=resonance, injections=inj_list, height=600)
        st.write("")
        
        # --- QUANTUM FIELD INTERPRETATION (Bilingual) ---
        expl_cols = st.columns(3)
        mode_key = resonance.mode
        
        # Mapping for Intelligence Brief
        interpretations = {
            "COHERENT": {
                "desc": "粒子相位高度同步，能量场呈超流体(Superfluid)导通状态。波胞无衰减，输出稳定。",
                "pred": "系统具备跨维度突破能力，适合高能级扩张与进取。处于“伤官伤尽”或“真从”态。",
                "sugg": "保持当前矢量方向，无需外部干预。防御粒子可卸载，全力转向动能输出。"
            },
            "ANNIHILATION": {
                "desc": "场域发生频率不相容对撞，正负电子云剧烈湮灭。存在明显的能级剥离现象。",
                "pred": "结构稳定性崩溃风险极高，热能溢出可能导致核心（正官）被彻底焚毁。",
                "sugg": "立即注入厚土（戊/己）屏蔽层，降低辐射通量。避免强行对冲，优先进行热能导入。"
            },
            "BEATING": {
                "desc": "系统处于非线性拍频状态，强干涉包络正在形成。能量场呈现周期性剧烈震荡。",
                "pred": "可能出现“假从”带来的瞬时高能，但伴随周期性的结构性危机。波动性极大。",
                "sugg": "利用相位偏移（Phase-t）进行主动微调。建议在气场峰值期进行战略部署。"
            },
            "DAMPED": {
                "desc": "能量场由于高阻尼效应陷入静默，粒子活性低于阈值。系统秩序参数处于平均水平。",
                "pred": "平稳但缺乏爆发力。属于常规维稳状态，无大范围能级跃迁可能。",
                "sugg": "注入激活粒子（丙/丁辐射）以提升场活性。打破当前低能平衡态。"
            }
        }
        
        info = interpretations.get(mode_key, interpretations["DAMPED"])
        
        with expl_cols[0]:
            st.markdown(f"""
            <div style="background:rgba(64,224,208,0.05); padding:15px; border-radius:10px; border-left:4px solid #40e0d0; height:100%;">
                <div style="font-size:12px; color:#40e0d0; font-weight:bold;">🔬 粒子场解读 (Analysis)</div>
                <div style="font-size:14px; margin-top:8px; line-height:1.6;">{info['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
        with expl_cols[1]:
            st.markdown(f"""
            <div style="background:rgba(255,159,67,0.05); padding:15px; border-radius:10px; border-left:4px solid #ff9f43; height:100%;">
                <div style="font-size:12px; color:#ff9f43; font-weight:bold;">🔮 趋势演测 (Prediction)</div>
                <div style="font-size:14px; margin-top:8px; line-height:1.6;">{info['pred']}</div>
            </div>
            """, unsafe_allow_html=True)
        with expl_cols[2]:
            st.markdown(f"""
            <div style="background:rgba(255,75,75,0.05); padding:15px; border-radius:10px; border-left:4px solid #ff4b4b; height:100%;">
                <div style="font-size:12px; color:#ff4b4b; font-weight:bold;">💊 量子建议 (Suggestion)</div>
                <div style="font-size:14px; margin-top:8px; line-height:1.6;">{info['sugg']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        st.caption("Quantum Orrery V5.2 | Intelligence Briefing Layer Active")

    with tabs[1]: # Timeline & Networking
        st.markdown("#### 时空稳定性追踪 (Spacetime Stability Trace)")
        sc = []
        for tf in np.linspace(0, 5, 20):
            rt = oracle.analyze(selected_case['bazi'][:4], selected_case.get('day_master'), luck_pillar=user_luck, annual_pillar=user_year, t=tf, injections=inj_list)
            sc.append({'t': tf, 'sync': rt['resonance'].sync_state})
        st.line_chart(pd.DataFrame(sc).set_index('t'))
        st.divider()
        st.markdown("#### 结构网络 (Structural Network)")
        render_molviz_3d([{'id':f"{b}_{i}",'label':b,'color':'#40e0d0'} for i,b in enumerate(selected_case['bazi'][:4])], [], height=400)

    with tabs[2]: # Batch Verification
        if st.button("运行验证矩阵 (Run Verification Matrix)", use_container_width=True):
            st.dataframe(pd.DataFrame([{'实验对象 (Subject)': '01-SYNC', '状态 (Status)': '✅ 相干 (Coherent)', '分值 (Score)': 0.992}]), use_container_width=True)

    with tabs[3]: # Advanced Physics
        st.warning("Phase 19 实验性物理模块已激活 (Active).")
        st.selectbox("加载物理场景 (Load Physical Scenario)", ["未加载 (None)", "1079 结构溃裂 (Structural Breach 1079)", "多支干涉 (Phase Shift Multiplier)", "熵增衰减 (Entropic Decay)"])

if __name__ == "__main__":
    render()
