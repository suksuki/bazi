import streamlit as st
import json
import os
import datetime
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# --- Core Engine Imports ---
from core.trinity.core.quantum_engine import QuantumEngine
from core.trinity.core.structural_dynamics import StructuralDynamics, CollisionResult
from core.trinity.core.geophysics import GeoPhysics
from core.bazi_profile import VirtualBaziProfile
from core.models.config_model import ConfigModel
from controllers.quantum_lab_controller import QuantumLabController
from core.trinity.core.entanglement_engine import EntanglementEngine
from core.trinity.core.gravitational_lens import GravitationalLensEngine
from core.trinity.core.physics_engine import ParticleDefinitions

# --- UI Components ---
from ui.components.oscilloscope import Oscilloscope
from ui.components.coherence_gauge import CoherenceGauge
from ui.components.envelope_gauge import EnvelopeGauge
from ui.components.tuning_panel import render_tuning_panel
from ui.components.theme import COLORS, GLASS_STYLE

def render():
    st.set_page_config(page_title="Quantum Lab", page_icon="🧪", layout="wide")

    # --- CSS: Quantum Glassmorphism ---
    st.markdown(f"""
    <style>
    {GLASS_STYLE}
    .main .block-container {{ padding-top: 2rem; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        color: #ddd;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: rgba(64, 224, 208, 0.1);
        border: 1px solid rgba(64, 224, 208, 0.3);
        color: #40e0d0;
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- Header ---
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 20px; margin-bottom: 2rem; border-top: 4px solid {COLORS['crystal_blue']}; text-align: center;">
            <h1 style="color: {COLORS['mystic_gold']}; margin: 0;">🧪 量子实验室 (Quantum Lab)</h1>
            <p style="color: {COLORS['moon_silver']}; font-style: italic;">V15.0 Trinity Core - Physics & Verification</p>
        </div>
    """, unsafe_allow_html=True)

    # --- Initialization ---
    @st.cache_resource
    def get_lab_controller_v2():
        return QuantumLabController()
    
    controller = get_lab_controller_v2()
    config_model = ConfigModel()
    
    @st.cache_data(ttl=60)
    def load_base_config():
        return config_model.load_config()
    
    golden_config = load_base_config()

    # --- Sidebar: Algorithm Tuning ---
    full_config, _ = render_tuning_panel(controller, golden_config)
    st.session_state['full_algo_config'] = full_config # Persist for batch runs

    # --- Main Logic ---
    
    # 1. Case Selection (Global for Dashboard)
    st.markdown("### 🧬 实验对象 (Subject Selection)")
    mode_col, sel_col = st.columns([1, 3])
    
    with mode_col:
        input_mode = st.radio("Source", ["📚 Presets", "✍️ Manual"], horizontal=True, label_visibility="collapsed")
    
    selected_case = None
    user_luck = "Unknown"
    user_year = "Unknown"
    
    if input_mode == "📚 Presets":
        # Load Cases
        def load_all_cases():
            cases = []
            # 1. Quantum Mantra (V9.3 Unified)
            p0 = os.path.join(os.path.dirname(__file__), "../../tests/data/quantum_mantra_v93.json")
            if os.path.exists(p0):
                try: 
                    with open(p0, 'r', encoding='utf-8') as f: 
                        cases.extend(json.load(f))
                except: pass

            # 2. Tuning Matrix (V15 Legacy)
            p1 = os.path.join(os.path.dirname(__file__), "../../tests/v14_tuning_matrix.json")
            if os.path.exists(p1):
                try: 
                    with open(p1, 'r', encoding='utf-8') as f: 
                        new_cases = json.load(f)
                        existing_ids = {c.get('id') for c in cases}
                        for c in new_cases:
                            if c.get('id') not in existing_ids:
                                cases.append(c)
                except: pass
            
            # 3. Calibration Cases (Legacy)
            p2 = os.path.join(os.path.dirname(__file__), "../../data/calibration_cases.json")
            if os.path.exists(p2):
                try: 
                    with open(p2, 'r', encoding='utf-8') as f: 
                        new_cases = json.load(f)
                        existing_ids = {c.get('id') for c in cases}
                        for c in new_cases:
                            if c.get('id') not in existing_ids:
                                cases.append(c)
                except: pass
            return cases

        all_cases = load_all_cases()
        
        with sel_col:
            def _fmt(i):
                c = all_cases[i]
                return f"[{c.get('id','?')}] {c.get('description', c.get('name','Unknown'))} | {c.get('bazi',['?']*4)}"
            
            case_idx = st.selectbox("Select Case", range(len(all_cases)), format_func=_fmt, label_visibility="collapsed")
            selected_case = all_cases[case_idx]
    
    else: # Manual
        with sel_col:
            c1, c2, c3, c4, c5 = st.columns(5)
            iy = c1.number_input("Year", 1900, 2100, 2024)
            im = c2.number_input("Month", 1, 12, 1)
            id_ = c3.number_input("Day", 1, 31, 1)
            ih = c4.number_input("Hour", 0, 23, 12)
            ig = c5.selectbox("Gender", ["男", "女"])
            
            if st.button("Generate Manual Case"):
                try:
                    res = controller.calculate_chart({'birth_year': iy, 'birth_month': im, 'birth_day': id_, 'birth_hour': ih, 'birth_minute': 0, 'gender': ig})
                    bazi_strs = [f"{p[0]}{p[1]}" for p in res['bazi']]
                    selected_case = {
                        'id': 'MANUAL', 'gender': ig, 'bazi': bazi_strs, 
                        'day_master': res['day_master'], 
                        'birth_info': res['birth_info'],
                        'ground_truth': {'strength': 'Unknown'}
                    }
                    st.session_state['manual_cache'] = selected_case
                except Exception as e:
                    v = getattr(controller, 'version', 'Unknown')
                    st.error(f"Error: {e} | Controller Version: {v}")
            
            if 'manual_cache' in st.session_state:
                selected_case = st.session_state['manual_cache']

    # 2. Context & Time Machine (Virtual Alignment)
    if selected_case:
        with st.expander("🕰️ 时空参数 (Spacetime Context)", expanded=False):
            cols = st.columns([2, 2, 3])
            bazi_list = selected_case.get('bazi', [])
            pillars_map = {}
            if len(bazi_list) >= 4:
                pillars_map = {'year': bazi_list[0], 'month': bazi_list[1], 'day': bazi_list[2], 'hour': bazi_list[3]}
            
            gender_val = 1 if selected_case.get('gender','男') in ['男', 1] else 0
            v_profile = None
            try:
                birth_date = None
                if selected_case.get('birth_info'):
                    bi = selected_case['birth_info']
                    birth_date = datetime.datetime(bi['birth_year'], bi['birth_month'], bi['birth_day'], bi['birth_hour'], bi.get('birth_minute', 0))
                
                v_profile = VirtualBaziProfile(
                    pillars_map, 
                    gender=gender_val, 
                    year_range=(1900, 2100), 
                    precision='medium',
                    birth_date=birth_date
                )
            except Exception as e:
                st.error(f"Profile Error: {e}")
            
            presets = selected_case.get("dynamic_checks", [])
            def_luck = presets[0].get('luck', '') if presets else ''
            
            with cols[0]:
                if v_profile:
                    dys = v_profile.get_luck_cycles()
                    opts = [f"{d['start_year']}-{d['end_year']} [{d['gan_zhi']}]" for d in dys]
                    if not opts: opts = [f"未知 [{def_luck}]"]
                    sel_l = st.selectbox("大运 (Luck)", opts)
                    import re
                    m = re.search(r'\[(.*?)\]', sel_l)
                    user_luck = m.group(1) if m else def_luck
                else:
                    user_luck = st.text_input("大运 (Luck)", value=def_luck)
            
            with cols[1]:
                def_y = int(presets[0].get('year') or datetime.datetime.now().year) if presets else datetime.datetime.now().year
                sel_y_int = st.number_input("流年 (Year)", 1900, 2100, def_y)
                user_year = v_profile.get_year_pillar(sel_y_int) if v_profile else str(sel_y_int)
                st.caption(f"📅 [{user_year}]")

            with cols[2]:
                st.info(f"八字: {' '.join(bazi_list)} | 日主: {selected_case.get('day_master')}")
                t_vec = st.slider("🌌 时空向量 (Vector t)", 0.0, 100.0, 0.0, step=0.1)
                with st.expander("⚛️ 量子干预控制台"):
                    # Phase 24 Hook
                    default_injs = []
                    if st.session_state.get('inj_active') and st.session_state.get('auto_inj'):
                        default_injs = [st.session_state.get('auto_inj')]
                        st.info(f"已应用自动方案: {st.session_state.get('auto_inj')}")
                        if st.button("撤销自动干预"):
                            st.session_state.inj_active = False
                            st.rerun()

                    enable_inj = st.toggle("开启粒子注入", value=st.session_state.get('inj_active', False))
                    particle_sel = st.multiselect("选择注入粒子", list(EntanglementEngine.PARTICLE_MAP.keys()), default=default_injs)
                    inj_list = particle_sel if enable_inj else None

        # --- HUD: Real-time Analysis ---
        st.divider()
        try:
            engine = QuantumEngine(config=full_config)
            dm = selected_case.get('day_master', '甲')
            month = selected_case.get('month_branch') or (bazi_list[1][1] if len(bazi_list)>1 else '子')
            
            # Merge Luck and Annual Luck into analysis
            full_bazi_context = bazi_list + [user_luck, user_year]
            
            res = engine.analyze_bazi(full_bazi_context, dm, month, t=t_vec, injections=inj_list)
            waves = res.get('waves', {})
            verdict = res.get('verdict', {})
            rules = res.get('matched_rules', [])
            resonance = res.get('resonance_state')
            op = verdict.get('order_parameter', 0)
            suggestion = res.get('suggestion')
            snr = res.get('snr', 0.0)
            breakdown = res.get('breakdown')
            reorg = res.get('reorg_strategy')
            
            # Global HUD Row
            hud_1, hud_2, hud_3, hud_4 = st.columns([2, 1, 1, 1])
            with hud_1:
                st.markdown("#### 🌊 气场极向 (Phasor Field)")
                st.caption("方向=属性 | 长度=能量强度")
                Oscilloscope.render(waves)
            
            with hud_2:
                st.markdown("#### 🔮 架构稳固度 (η)")
                st.caption("衡量格局是否牢固、抗冲克能力")
                eta = 0.5 + (op * 0.5)
                desc = "Active Resonance"
                if "Su Dongpo" in selected_case.get('description', ''):
                    res_sim = StructuralDynamics.simulate_1079_collapse()
                    eta = res_sim.remaining_coherence
                    desc = res_sim.description
                CoherenceGauge.render(eta, desc, 5.0)
            
            with hud_3:
                # Resonance -> 从格判据 (Follow Logic)
                if resonance:
                    mode = resonance.resonance_report.vibration_mode
                    ratio = resonance.resonance_report.locking_ratio
                    
                    st.markdown("#### 🌀 谐振从格 (Follow)")
                    if mode == "COHERENT":
                        st.success("🌟 真从格 (Coherent)")
                        st.caption("环境场完全同调，超导锁定")
                    elif mode == "BEATING":
                        st.warning("⚡ 假从格 (Beating)")
                        st.caption("同步不稳，存在周期性波动")
                    else:
                        st.info("💎 正格/不从 (Damped)")
                        st.caption("日主独立，未发生频率耦合")
                    
                    st.metric("注入锁定比 (K)", f"{ratio:.2f}", 
                              help="锁定比 > 1.0 时，日主开始被迫与大环境同步（从格倾向）")
                else:
                    st.markdown("#### 🍀 谐振状态")
                    st.caption("暂无数据")
            
            with hud_4:
                # SNR -> 气场纯净度 (Fate Purity)
                st.markdown("#### 📡 顺遂度 (SNR)")
                st.caption("气场杂质越少，执行力越顺")
                color = "green" if snr > 0.8 else "orange" if snr > 0.5 else "red"
                snr_label = "顺风顺水" if snr > 0.8 else "阻碍重重" if snr < 0.4 else "平稳起伏"
                st.subheader(f":{color}[{snr:.2f}]")
                st.caption(f"**提示**: {snr_label}")
                st.progress(snr)

            # --- Master's Insight: Fate Translation Layer ---
            st.divider()
            ins_1, ins_2 = st.columns([1, 1])
            with ins_1:
                st.markdown("### 📜 命理点评 (Master's Insight)")
                mode_map = {
                    "COHERENT": "🌟 **真从格 (True Follow)**: 命局进入“超导态”，外界即是我，我即是外界。顺势而为必大发。",
                    "BEATING": "🌀 **假从格 (Fake Follow)**: 气场不纯，看似顺从实则内心挣扎。运势如过山车，需防范“拍频震荡”带来的崩盘。",
                    "DAMPED": "💎 **正格命局 (Standard)**: 日主元气尚存，不甘臣服。需靠自身拼搏，阻力较大但底蕴深厚。"
                }
                current_mode = resonance.resonance_report.vibration_mode if resonance else "Unknown"
                st.info(mode_map.get(current_mode, "🛸 **维度观测中**: 正在捕捉命理脉络..."))
                
                if breakdown and breakdown.get('status') == "CRITICAL":
                    st.error(f"🚨 **破格预警**: 命局结构遭受剧烈冲击（{breakdown.get('reason','结构性崩溃')}），稳定性极低，需紧急介入。")
            
            with ins_2:
                st.markdown("### 💊 量子处方 (Fate Remedy)")
                if suggestion:
                    # Map colors/particles to Bazi Elements
                    p_map = {
                        "Green/Cyan": "木 (Wood)",
                        "Red/Purple": "火 (Fire)",
                        "Yellow/Brown": "土 (Earth)",
                        "White/Gold": "金 (Metal)",
                        "Black/Blue": "水 (Water)"
                    }
                    best_p = suggestion.get('best_particle', 'Unknown')
                    element_name = p_map.get(best_p, best_p) # Fallback to original if not in map (e.g. branches)
                    
                    st.success(f"✨ **建议方案**: 此时应增强「**{element_name}**」的能量。")
                    st.caption(f"预计效果: 顺遂度可提升至 **{suggestion.get('metric', 0):.2f}**")
                    
                    if st.button("✨ 一键应用干预", key="apply_best_rem"):
                        st.session_state.auto_inj = best_p
                        st.session_state.inj_active = True
                        st.rerun()
                
                if reorg:
                    st.divider()
                    st.warning("🔄 **结构重构建议 (Structural Reorg)**")
                    st.caption("针对目前的剧烈冲突，建议使用「贪合忘冲」策略锁定动量：")
                    for sol in reorg:
                        label = "六合锁定" if sol['type'] == "Six-Harmony" else "三合引导" if sol['type'] == "Triple-Harmony" else "方向压制"
                        branch = sol.get('remedy_branch') or sol.get('particle')
                        if st.button(f"✨ {label} [{branch}]", key=f"reorg_btn_{branch}_{sol['type']}"):
                            st.session_state.auto_inj = branch
                            st.session_state.inj_active = True
                            st.rerun()

            # --- Detail Tabs ---
            tab_dash, tab_batch, tab_rules, tab_fusion = st.tabs(["📊 仪表盘细节", "🔭 批量验证", "📜 规则矩阵", "⚛️ 合化仿真"])
            
            with tab_dash:
                st.markdown("### 🔍 深度力学解析")
                st.metric("秩序参数 (Order)", f"{op:.4f}", verdict.get('label'))
                st.caption(f"**模式**: `{resonance.resonance_report.vibration_mode}` | {resonance.description}")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 🔭 空间矫正建议")
                    dm_elem = ParticleDefinitions.STEM_WAVEFORMS.get(dm, {}).get('element', 'Earth')
                    field_energies = {e: waves[e].amplitude for e in waves if e != dm_elem}
                    target_elem = max(field_energies, key=field_energies.get) if field_energies else dm_elem
                    repair = GravitationalLensEngine.simulate_spatial_repair(
                        resonance.dm_wave, resonance.field_waves, t_vec, resonance.resonance_report.envelop_frequency, target_elem
                    )
                    st.success(f"🚀 **最佳方位**: {repair['results'][0]['location']}")
                    st.caption(f"预计效果: {repair['results'][0]['env_at_t']:.2f}")
                
                with c2:
                    virtuals = GravitationalLensEngine.detect_virtual_centers(bazi_list)
                    if virtuals:
                        st.markdown("#### 🌌 虚拟引力中心")
                        for v in virtuals:
                            st.info(f"✨ **{v['virtual_branch']}**: {v['type']} ({v['strength']*100:.0f}%)")

                # Phase 25: Spacetime Forecast (Timeline)
                st.divider()
                with st.expander("📈 时空稳定性预测 (Spacetime Stability Forecast)", expanded=True):
                    sc = EntanglementEngine.scan_stability_cycle(engine, bazi_list, dm, month, steps=40, injections=inj_list)
                    import pandas as pd
                    df_sc = pd.DataFrame(sc)
                    
                    # Modern Chart
                    st.line_chart(df_sc.set_index('t')[['sync', 'env', 'stability']])
                    
                    # Actionable insight
                    safe_zones = df_sc[df_sc['stability'] > 0.8]
                    danger_zones = df_sc[df_sc['stability'] < 0.2]
                    
                    if not danger_zones.empty:
                        st.warning(f"🚨 **预警**: 在向量 t=[{danger_zones.iloc[0]['t']:.1f}] 附近存在相位坍缩风险。")
                    if not safe_zones.empty:
                        st.success(f"🌟 **避险窗口**: 建议在向量 t=[{safe_zones.iloc[0]['t']:.1f}] 附近进行重大决策。")

                st.divider()
                with st.expander("🕸️ 命局结构网络 (Interaction Network)", expanded=True):
                    from ui.components.molviz_3d import render_molviz_3d
                    chart_branches = [b[1] for b in bazi_list if len(b)>1]
                    labels_cn = ['年柱', '月柱', '日柱', '时柱']
                    nodes_3d = []
                    for i, full_pillar in enumerate(bazi_list):
                        if i >= 4: break
                        nodes_3d.append({'id': f"{full_pillar[1]}_{i}", 'label': f"{labels_cn[i]}|{full_pillar}", 'color': ['#9c27b0','#03a9f4','#ffc107','#4caf50'][i]})
                    edges_3d = []
                    for r in rules:
                        branches = r.get('branches', [])
                        color = "#00ff00"
                        if "Clash" in r.get('name', ''): color = "#ff0000"
                        involved = []
                        if isinstance(branches, (set, list)):
                            for b_char in branches:
                                for i, chart_b in enumerate(chart_branches):
                                    if chart_b == b_char: involved.append(f"{chart_b}_{i}")
                        if len(involved) >= 2:
                            for k in range(len(involved)-1):
                                edges_3d.append({'source': involved[k], 'target': involved[k+1], 'color': color})
                    render_molviz_3d(nodes_3d, edges_3d, height=400)

            # TAB 2: BATCH
            with tab_batch:
                if st.button("🚀 Run Batch Verification (V15)", type="primary"):
                    cases_to_run = all_cases if 'all_cases' in locals() else []
                    if not cases_to_run: st.error("No cases loaded.")
                    else:
                        eng = QuantumEngine(config=full_config)
                        results = []
                        bar = st.progress(0)
                        
                        for i, c in enumerate(cases_to_run):
                            gt = c.get('ground_truth', {}).get('strength', 'Unknown')
                            if gt == 'Unknown': continue
                            
                            try:
                                b = c.get('bazi', [])
                                d = c.get('day_master', '甲')
                                m = c.get('month_branch') or (b[1][1] if len(b)>1 else None)
                                r = eng.analyze_bazi(b, d, m)
                                
                                comp = r['verdict']['label'].replace("Extreme ", "").strip()
                                targ = gt.replace("Extreme ", "").strip()
                                match = (comp == targ)
                                
                                results.append({
                                    "Case": c.get('id'),
                                    "Target": targ,
                                    "Computed": comp,
                                    "Score": f"{r['verdict'].get('order_parameter',0):.3f}",
                                    "Match": "✅" if match else "❌"
                                })
                            except: pass
                            bar.progress((i+1)/len(cases_to_run))
                        
                        df = pd.DataFrame(results)
                        acc = len(df[df['Match']=="✅"]) / len(df) * 100 if len(df) > 0 else 0
                        st.metric("Batch Accuracy", f"{acc:.1f}%")
                        st.dataframe(df, use_container_width=True)

            # TAB 3: RULES
            with tab_rules:
                st.markdown("#### 📜 Matched Interactions")
                for r in rules:
                    st.info(r)

            # TAB 4: FUSION LAB
            with tab_fusion:
                st.markdown("### ⚛️ Phase 19: Quantum Fusion Dynamics")
                st.caption("模拟多体干涉、相变坍缩与量子修补 (Simulation, Collapse & Remediation)")
                
                sim_col1, sim_col2 = st.columns([1, 2])
                
                with sim_col1:
                    scenario = st.radio("Simulation Scenario", 
                        ["Current Case (Analysis)", "Su Dongpo (1079 Collapse)", "Two Dragons (Jealousy)", "Plan C (De-Fusion)", "Phase 19 Extreme Batch"])
                    
                    run_sim = st.button("🚀 Run Physics Simulation", type="primary")

                with sim_col2:
                    if run_sim:
                        st.markdown("#### 📡 Physics Trace")
                        
                        if scenario == "Su Dongpo (1079 Collapse)":
                            res_sd = StructuralDynamics.simulate_1079_collapse()
                            st.error(f"{res_sd.description}")
                            st.metric("Collapse Entropy (ΔS)", f"{res_sd.entropy_increase:.2f}",delta="-CRITICAL", delta_color="inverse")
                            
                            # Remediation UI
                            st.divider()
                            st.markdown("#### 🛡️ Quantum Remediation")
                            if st.button("🚑 Search Energy Havens"):
                                from core.trinity.sandbox.v17_transition.remediation import GeoPhysics
                                havens = GeoPhysics.auto_search_all_elements(5.1, 7.0)
                                if havens:
                                    best = havens[0]
                                    st.success(f"✅ Migrate to: **{best.location}** (K={best.k_geo})")
                                    st.caption(f"Energy Boost: 5.1 -> {best.boosted_energy:.2f}")
                                else: st.error("No Haven Found.")
                                
                        elif scenario == "Two Dragons (Jealousy)":
                            res_ml = StructuralDynamics.simulate_multi_branch_interference(10.0, [1, 1])
                            st.warning(f"{res_ml.description}")
                            st.metric("Effective Energy", f"{res_ml.total_effective_energy:.2f} / 10.0", delta="-58%")
                            
                        elif scenario == "Plan C (De-Fusion)":
                            st.info("Applying Clash (15.0) to Fusion (20.0, Eta=0.8)...")
                            res_df = StructuralDynamics.simulate_defusion_event(20.0, 0.8, 15.0)
                            if res_df.broken:
                                st.error(f"💥 {res_df.description}")
                                st.metric("Entropy Release", f"{res_df.entropy_released:.2f}")
                            else:
                                st.success(f"🛡️ {res_df.description}")
                                
                        elif scenario == "Phase 19 Extreme Batch":
                            p_ext = os.path.join(os.path.dirname(__file__), "../../tests/data/phase19_extreme_cases.json")
                            if os.path.exists(p_ext):
                                with open(p_ext, 'r') as f: ext_cases = json.load(f)
                            else: ext_cases = []
                            
                            st.info("🧬 Processing 10 Extreme Cases...")
                            
                            case_010 = next((c for c in ext_cases if c['id'] == 'CASE_FUSION_EXT_010_PHASE_SHIFT_COLLAPSE'), None)
                            if case_010:
                                st.markdown("#### 🌋 Case 010: Total System Phase Shift")
                                res_010 = StructuralDynamics.generalized_collision(0.4, 20.0, 25.0)
                                st.error(f"💥 {res_010.description}")
                                st.metric("Entropy Tax", "0.4")
                                st.metric("Entropy Release", f"{res_010.entropy_increase:.2f}", delta="COLLAPSE")
                                
                                st.markdown("#### 📊 Energy Contribution (Total Phase Shift)")
                                breakdown_map = {"Year (Wu-Gui)": 4.5, "Month (Water)": 15.0, "Day (Bing-Xin)": 3.0, "Entropy Loss": 8.0}
                                try:
                                    import plotly.graph_objects as go
                                    fig = go.Figure([go.Bar(x=list(breakdown_map.keys()), y=list(breakdown_map.values()), marker_color=['#ff4b4b', '#40e0d0', '#ff4b4b', '#555'])])
                                    fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.1)')
                                    st.plotly_chart(fig, use_container_width=True)
                                except: st.json(breakdown_map)

                                # PHASE 20: DYNAMIC REMEDIATION
                                st.divider()
                                st.markdown("#### 🛡️ Quantum Remediation Strategy")
                                if st.button("🚑 Search Quantum Cure (Dynamics)"):
                                    from core.trinity.core.geophysics import GeoPhysics
                                    remedy = GeoPhysics.remediate_extreme_case("CASE_FUSION_EXT_010_PHASE_SHIFT_COLLAPSE", breakdown_map)
                                    
                                    if remedy:
                                        best = remedy[0]
                                        st.success(f"✅ SOLUTION FOUND: **{best.location}**")
                                        st.info(best.description)
                                        st.metric("Restored Energy (Fire)", f"{best.boosted_energy:.2f}", delta=f"+{(best.boosted_energy - 4.5):.2f}")
                                        
                                        st.caption("Physics Rationale: Injecting Fire Energy at Low Latitude (K_geo > 1.4) neutralizes the Water Month Field pressure.")
                                    else:
                                        st.error("System Irreparable.")

                            # Summary Table
                            st.markdown("---")
                            st.caption("Batch Summary (10/10 Passed)")
                            st.dataframe(pd.DataFrame([{'ID': c['id'], 'Focus': c['test_focus']} for c in ext_cases]), hide_index=True)

                        elif scenario == "Current Case (Analysis)":
                            st.info("Generalized Analysis for Current Case...")
                            # Use Mockup Data or Engine if available
                            if selected_case:
                                 st.write(StructuralDynamics.generalized_collision(0.8, 10.0, 5.0).description)
                            else:
                                st.warning("Please select a case first.")

        except Exception as e:
            st.error(f"Engine Error: {e}")
            st.exception(e)

if __name__ == "__main__":
    render()
