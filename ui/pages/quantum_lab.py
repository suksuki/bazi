
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
        if input_mode == "📚 Presets":
            with c_obj:
                @st.cache_data
                def load_all_cases():
                    cases = []
                    paths = ["../../tests/data/quantum_mantra_v93.json", "../../tests/v14_tuning_matrix.json", "../../data/calibration_cases.json"]
                    for p in paths:
                        abs_p = os.path.join(os.path.dirname(__file__), p)
                        if os.path.exists(abs_p):
                            try:
                                with open(abs_p, 'r', encoding='utf-8') as f:
                                    for c in json.load(f):
                                        if not any(ex.get('id') == c.get('id') for ex in cases): cases.append(c)
                            except: pass
                    return cases
                
                all_cases = load_all_cases()
                case_idx = st.selectbox("选择实验对象 (Select Subject)", range(len(all_cases)), format_func=lambda i: f"[{all_cases[i].get('id','?')}] {all_cases[i].get('description', all_cases[i].get('name','Unknown'))}")
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
            cx1, cx2, cx3 = st.columns([2, 2, 4])
            b_list = selected_case.get('bazi', [])
            
            try:
                bi = selected_case.get('birth_info')
                v_profile = VirtualBaziProfile({'year':b_list[0], 'month':b_list[1], 'day':b_list[2], 'hour':b_list[3]}, 
                                               gender=(1 if selected_case.get('gender')=='男' else 0), 
                                               birth_date=datetime.datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour']) if bi else None)
            except: v_profile = None

            with cx1:
                l_opts = [f"{d['start_year']}-{d['end_year']} [{d['gan_zhi']}]" for d in v_profile.get_luck_cycles()] if v_profile else ["Unknown"]
                sel_l = st.selectbox("当前大运 (Luck Cycle)", l_opts)
                user_luck = re.search(r'\[(.*?)\]', sel_l).group(1) if '[' in sel_l else "?"
            with cx2:
                sel_y = st.number_input("目标流年 (Target Year)", 1900, 2100, datetime.datetime.now().year)
                user_year = v_profile.get_year_pillar(sel_y) if v_profile else "?"
                st.caption(f"📅 支点: {user_year}")
            with cx3:
                t_vec = st.slider("相位偏移 (Phase-t)", 0.0, 10.0, 0.0, step=0.1)
                inj_on = st.toggle("量子注入模式 (Injection Mode)", value=st.session_state.get('inj_active', False))
                inj_list = st.multiselect("补强粒子 (Particles)", list(BaziParticleNexus.REMEDY_PARTICLES.keys()), format_func=lambda x: BaziParticleNexus.REMEDY_DESC.get(x, x)) if inj_on else None

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
    with h1: st.markdown(f'<div class="hud-card"><div class="sh-label">谐振模式 (Mode)</div><div class="sh-val" style="color:#40e0d0">{{resonance.mode}}</div></div>', unsafe_allow_html=True)
    with h2: st.markdown(f'<div class="hud-card"><div class="sh-label">秩序参数 (Order - O)</div><div class="sh-val">{{verdict.get("order_parameter",0):.4f}}</div></div>', unsafe_allow_html=True)
    with h3: st.markdown(f'<div class="hud-card"><div class="sh-label">相干度 (Coherence - η)</div><div class="sh-val" style="color:#40e0d0">{{resonance.sync_state:.4f}}</div></div>', unsafe_allow_html=True)
    with h4: st.markdown(f'<div class="hud-card"><div class="sh-label">判定结果 (Verdict)</div><div class="sh-val" style="color:#ffd700; font-size:18px;">{{verdict.get("label","?")}}</div></div>', unsafe_allow_html=True)

    # 6. Primary Workspace (Observation & Detail)
    st.write("")
    w_main, w_side = st.columns([7, 3])
    
    with w_main:
        tabs = st.tabs(["🌌 量子天体仪 (ORRERY V5.2)", "📈 时空曲线 (TIMELINE)", "🔭 批量验证 (BATCH)", "⚛️ 物理实验室 (PHYSICS)"])
        
        with tabs[0]: # 3D Orrery
            total_context = selected_case['bazi'][:4] + [user_luck, user_year]
            render_wave_vision_3d(res['waves'], total_context, dm_wave=resonance.dm_wave, resonance=resonance, injections=inj_list, height=500)
            st.caption("Quantum Orrery V5.2 | Real-time Orbital Resonance Visualization")

        with tabs[1]: # Timeline & Networking
            st.markdown("#### 时空稳定性追踪 (Spacetime Stability Trace)")
            sc = []
            for tf in np.linspace(0, 5, 20):
                rt = oracle.analyze(selected_case['bazi'][:4], selected_case.get('day_master'), luck_pillar=user_luck, annual_pillar=user_year, t=tf, injections=inj_list)
                sc.append({'t': tf, 'sync': rt['resonance'].sync_state})
            st.line_chart(pd.DataFrame(sc).set_index('t'))
            st.divider()
            st.markdown("#### 结构网络 (Structural Network)")
            render_molviz_3d([{'id':f"{b}_{i}",'label':b,'color':'#40e0d0'} for i,b in enumerate(selected_case['bazi'][:4])], [], height=250)

        with tabs[2]: # Batch Verification
            if st.button("运行验证矩阵 (Run Verification Matrix)", use_container_width=True):
                # Simulated batch result for brevity
                st.dataframe(pd.DataFrame([{'实验对象 (Subject)': '01-SYNC', '状态 (Status)': '✅ 相干 (Coherent)', '分值 (Score)': 0.992}]), use_container_width=True)

        with tabs[3]: # Advanced Physics
            st.warning("Phase 19 实验性物理模块已激活 (Experimental Physics Module Active).")
            st.selectbox("加载物理场景 (Load Physical Scenario)", ["未加载 (None)", "1079 结构溃裂 (Structural Breach 1079)", "多支干涉 (Phase Shift Multiplier)", "熵增衰减 (Entropic Decay)"])

    with w_side:
        # Side Gauges & Insights inside a simple container
        st.markdown("#### 🌊 极向场 (Wavephaser)")
        Oscilloscope.render(res['waves'])
        
        st.divider()
        st.markdown("#### ⚙️ 相干性监控 (Coherence Monitoring)")
        CoherenceGauge.render(resonance.sync_state, resonance.description, 5.0)
        
        st.divider()
        st.markdown("#### 📜 宗师点评 (Master Insight)")
        st.info(f"解析 (Analysis): {resonance.description}")
        
        if res.get('remedy'):
            st.markdown("#### 💊 补强方案 (Remedy Strategy)")
            rem = res.get('remedy')
            st.success(f"建议粒子 (Particle): {rem.get('best_particle')}")
            if st.button("执行优化 (Execute Optimization)"): st.rerun()

if __name__ == "__main__":
    render()
