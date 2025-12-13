import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from core.quantum_engine import QuantumEngine

def render():
    st.set_page_config(page_title="Quantum Lab", page_icon="🧪", layout="wide")

    # --- CSS: Quantum Glassmorphism & Animations ---
    st.markdown("""
    <style>
    /* Narrative Card Styles */
    .narrative-card {
        position: relative;
        padding: 24px;
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        transition: all 0.3s ease;
        margin-bottom: 10px;
    }
    .narrative-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* Card Types */
    .card-mountain {
        background: linear-gradient(135deg, rgba(120, 53, 15, 0.15) 0%, rgba(251, 191, 36, 0.1) 100%);
        border-top: 2px solid rgba(251, 191, 36, 0.4);
    }
    .icon-mountain {
        font-size: 28px;
        background: linear-gradient(to bottom, #fbbf24, #b45309);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.5));
    }
    
    .card-shield {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.2) 0%, rgba(56, 189, 248, 0.1) 100%);
        border-top: 2px solid rgba(56, 189, 248, 0.4);
    }
    .icon-shield {
        font-size: 28px;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.8);
    }
    
    .card-flow {
        background: linear-gradient(135deg, rgba(6, 78, 59, 0.2) 0%, rgba(52, 211, 153, 0.1) 100%);
        border-top: 2px solid rgba(52, 211, 153, 0.4);
    }
    .icon-flow {
        font-size: 28px;
        color: #34d399;
        filter: drop-shadow(0 0 5px rgba(52, 211, 153, 0.6));
    }

    .card-danger {
        background: linear-gradient(135deg, rgba(127, 29, 29, 0.2) 0%, rgba(248, 113, 113, 0.1) 100%);
        border-top: 2px solid rgba(248, 113, 113, 0.4);
    }

    /* Typography */
    .card-title { font-weight: 700; font-size: 1.0rem; margin-bottom: 2px; color: #f1f5f9; }
    .card-subtitle { font-size: 0.85rem; color: #94a3b8; margin-bottom: 8px; }
    .card-impact { font-family: 'monospace'; font-size: 0.8rem; padding: 2px 6px; border-radius: 4px; background: rgba(0,0,0,0.3); display: inline-block; }
    </style>
    """, unsafe_allow_html=True)
    
    def render_narrative_card(event):
        """Renders a single narrative card based on the event payload."""
        ctype = event.get('card_type', 'default')
        
        config = {
            "mountain_alliance": {"css": "card-mountain", "icon": "⛰️", "icon_css": "icon-mountain"},
            "penalty_cap": {"css": "card-shield", "icon": "🛡️", "icon_css": "icon-shield"},
            "mediation": {"css": "card-flow", "icon": "🌊", "icon_css": "icon-flow"},
            "pressure": {"css": "card-danger", "icon": "⚠️", "icon_css": ""},
            "control": {"css": "card-shield", "icon": "⚡", "icon_css": "icon-shield"}, 
            "default": {"css": "", "icon": "📜", "icon_css": ""}
        }
        
        cfg = config.get(ctype, config['default'])
        
        html = f"""
        <div class="narrative-card {cfg['css']}">
            <div style="display: flex; align-items: start; gap: 12px;">
                <div class="{cfg['icon_css']}">{cfg['icon']}</div>
                <div style="flex-grow: 1;">
                    <div class="card-title">{event.get('title', 'Unknown Event')}</div>
                    <div class="card-subtitle">{event.get('desc', '')}</div>
                    <div class="card-impact">{event.get('score_delta', '')}</div>
                </div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    # --- Load Data ---
    @st.cache_data
    def load_cases():
        path = os.path.join(os.path.dirname(__file__), "../../data/calibration_cases.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return []

    # --- Load Params Helper ---
    def load_params_from_disk():
        path = os.path.join(os.path.dirname(__file__), "../../data/golden_parameters.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}
        
    def save_params_to_disk(new_params):
        path = os.path.join(os.path.dirname(__file__), "../../data/golden_parameters.json")
        original = load_params_from_disk()
        
        # Update global
        original['global_physics']['w_e_weight'] = new_params.get('w_e_weight', 1.0)
        original['global_physics']['f_yy_correction'] = new_params.get('f_yy_correction', 1.1)
        
        # Update K Factors
        k = original['conflict_and_conversion_k_factors']
        k['K_Control_Conversion'] = new_params.get('k_control', 0.55)
        k['K_Buffer_Defense'] = new_params.get('k_buffer', 0.40)
        k['K_Clash_Robbery'] = new_params.get('k_clash', 1.2)
        k['K_Mutiny_Betrayal'] = new_params.get('k_mutiny', 1.8)
        k['K_Leak_Drain'] = new_params.get('k_leak', 0.87)
        k['K_Pressure_Attack'] = new_params.get('k_pressure', 1.0)
        k['K_Burden_Wealth'] = new_params.get('k_burden', 1.0)
        k['K_Broken_Collapse'] = new_params.get('k_broken', 1.5)
        
        # Update Weights
        mw = original['macro_weights_w']
        mw['W_Career_Officer'] = new_params.get('w_career_officer', 0.8)
        mw['W_Career_Resource'] = new_params.get('w_career_resource', 0.1)
        mw['W_Career_Output'] = new_params.get('w_career_output', 0.0)
        mw['W_Wealth_Cai'] = new_params.get('w_wealth_cai', 0.6)
        mw['W_Wealth_Output'] = new_params.get('w_wealth_output', 0.4)
        
        rw = original['relationship_weights']
        rw['W_Rel_Spouse'] = new_params.get('w_rel_spouse', 0.35)
        rw['W_Rel_Self'] = new_params.get('w_rel_self', 0.20)
        rw['W_Rel_Output'] = new_params.get('w_rel_output', 0.15)
        
        # flags
        original['logic_flags']['enable_mediation_exemption'] = new_params.get('enable_mediation_exemption', True)
        original['logic_flags']['enable_structural_clash'] = new_params.get('enable_structural_clash', True)

        with open(path, "w") as f:
            json.dump(original, f, indent=4, ensure_ascii=False)
        st.toast("✅ Parameters Saved to Disk!")

    cases = load_cases()
    defaults = load_params_from_disk()
    
    # Flatten defaults for sliders
    fd = {}
    if defaults:
        gp = defaults.get('global_physics', {})
        fd['w_e'] = gp.get('w_e_weight', 1.0)
        fd['f_yy'] = gp.get('f_yy_correction', 1.1)
        
        mw = defaults.get('macro_weights_w', {})
        fd['w_off'] = mw.get('W_Career_Officer', 0.8)
        fd['w_res'] = mw.get('W_Career_Resource', 0.1)
        fd['w_out_c'] = mw.get('W_Career_Output', 0.0)
        fd['w_cai'] = mw.get('W_Wealth_Cai', 0.6)
        fd['w_out_w'] = mw.get('W_Wealth_Output', 0.4)
        
        rw = defaults.get('relationship_weights', {})
        fd['w_spouse'] = rw.get('W_Rel_Spouse', 0.35)
        fd['w_self'] = rw.get('W_Rel_Self', 0.20)
        fd['w_out_r'] = rw.get('W_Rel_Output', 0.15)
        
        k = defaults.get('conflict_and_conversion_k_factors', {})
        fd['k_ctl'] = k.get('K_Control_Conversion', 0.55)
        fd['k_buf'] = k.get('K_Buffer_Defense', 0.40)
        fd['k_mut'] = k.get('K_Mutiny_Betrayal', 1.8)
        fd['k_cap'] = k.get('K_Capture_Wealth', 0.0)
        fd['k_leak'] = k.get('K_Leak_Drain', 0.87)
        fd['k_clash'] = k.get('K_Clash_Robbery', 1.2)
        fd['k_press'] = k.get('K_Pressure_Attack', 1.0)
        fd['k_brk'] = k.get('K_Broken_Collapse', 1.5)
        fd['k_bur'] = k.get('K_Burden_Wealth', 1.0)
        
        fl = defaults.get('logic_flags', {})
        fd['en_med'] = fl.get('enable_mediation_exemption', True)
        fd['en_str'] = fl.get('enable_structural_clash', True)


    # --- SIDEBAR CONTROLS ---
    st.sidebar.title("🎛️ 物理参数 (Physics)")
    
    # Global
    w_e_val = st.sidebar.slider("We: 全局能量增益", 0.5, 2.0, fd.get('w_e', 1.0), 0.1)
    f_yy_val = st.sidebar.slider("F(阴阳): 异性耦合效率", 0.8, 1.5, fd.get('f_yy', 1.1), 0.05)
    
    # Career
    st.sidebar.subheader("W_事业 (Career)")
    w_career_officer = st.sidebar.slider("W_官杀 (Officer)", 0.0, 1.0, fd.get('w_off', 0.8), 0.05)
    w_career_resource = st.sidebar.slider("W_印星 (Resource)", 0.0, 1.0, fd.get('w_res', 0.1), 0.05)
    w_career_output = st.sidebar.slider("W_食伤 (Tech)", 0.0, 1.0, fd.get('w_out_c', 0.0), 0.05)
    k_control = st.sidebar.slider("K_制杀 (Control)", 0.0, 1.0, fd.get('k_ctl', 0.55))
    k_buffer = st.sidebar.slider("K_化杀 (Buffer)", 0.0, 1.0, fd.get('k_buf', 0.40))
    k_mutiny = st.sidebar.slider("K_伤官见官 (Mutiny)", 0.0, 3.0, fd.get('k_mut', 1.8))
    k_pressure = st.sidebar.slider("K_官杀攻身 (Pressure)", 0.0, 2.0, fd.get('k_press', 1.0))
    st.sidebar.caption("Pressure controls Career stress & Relationship stress")

    # Wealth
    st.sidebar.markdown("---")
    st.sidebar.subheader("W_财富 (Wealth)")
    w_wealth_cai = st.sidebar.slider("W_财星 (Wealth)", 0.0, 1.0, fd.get('w_cai', 0.6), 0.05)
    w_wealth_output = st.sidebar.slider("W_食伤 (Source)", 0.0, 1.0, fd.get('w_out_w', 0.4), 0.05)
    k_capture = st.sidebar.slider("K_身旺担财 (Capture)", 0.0, 0.5, fd.get('k_cap', 0.0), 0.05)
    k_leak = st.sidebar.slider("K_身弱泄气 (Leak)", 0.0, 2.0, fd.get('k_leak', 0.87), 0.01)
    k_burden = st.sidebar.slider("K_财多身弱 (Burden)", 0.5, 2.0, fd.get('k_bur', 1.0), 0.1)

    # Relationship
    st.sidebar.markdown("---")
    st.sidebar.subheader("W_感情 (Relationship)")
    w_rel_spouse = st.sidebar.slider("W_配偶星 (Spouse)", 0.1, 1.0, fd.get('w_spouse', 0.35), 0.05)
    w_rel_self = st.sidebar.slider("W_日主 (Self)", -0.5, 0.5, fd.get('w_self', 0.20), 0.05)
    w_rel_output = st.sidebar.slider("W_食伤 (Output)", 0.0, 1.0, fd.get('w_out_r', 0.15), 0.05)
    k_clash = st.sidebar.slider("K_比劫夺财 (Clash)", 0.0, 2.0, fd.get('k_clash', 1.2), 0.1)

    # Advanced Logic
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚩 逻辑开关 (Advanced Flags)")
    k_broken = st.sidebar.slider("K_假从崩塌 (Broken)", 1.0, 3.0, fd.get('k_brk', 1.5), 0.1)
    enable_mediation = st.sidebar.checkbox("通关豁免 (Mediation)", fd.get('en_med', True))
    enable_structural = st.sidebar.checkbox("地支互斥 (Structural)", fd.get('en_str', True))
    
    current_params = {
        "w_e_weight": w_e_val,
        "f_yy_correction": f_yy_val,
        
        "w_career_officer": w_career_officer,
        "w_career_resource": w_career_resource,
        "w_career_output": w_career_output,
        "k_control": k_control,
        "k_buffer": k_buffer,
        "k_mutiny": k_mutiny,
        "k_pressure": k_pressure,
        
        "w_wealth_cai": w_wealth_cai,
        "w_wealth_output": w_wealth_output,
        "k_capture": k_capture,
        "k_leak": k_leak,
        "k_burden": k_burden,

        "w_rel_spouse": w_rel_spouse,
        "w_rel_self": w_rel_self,
        "w_rel_output": w_rel_output,
        "k_clash": k_clash,
        
        "k_broken": k_broken,
        "enable_mediation_exemption": enable_mediation,
        "enable_structural_clash": enable_structural
    }
    
    st.sidebar.markdown("---")
    if st.sidebar.button("💾 保存现有配置 (Save)", type="primary"):
        save_params_to_disk(current_params)

    # --- MAIN ENGINE SETUP ---
    engine = QuantumEngine(current_params)

    # --- UI HEADER ---
    st.title("🧪 量子八字 V2.6 验证工作台")
    st.markdown("Dynamic Space-Time Validation Module")

    # --- TABS ---
    tab_global, tab_single  = st.tabs(["🔭 全局校准 (Global Telescope)", "🔬 单点分析 (Single Microscope)"])

    # ==========================
    # TAB 1: GLOBAL TELESCOPE
    # ==========================
    with tab_global:
        st.subheader("全局调校控制台 (Global Calibration Console)")
        st.caption("通过左侧滑块调整物理参数，目标是消除热力图中的红色区域 (RMSE > 5.0)。")
        
        if not cases:
            st.error("No cases loaded.")
        else:
            # 1. Batch Calculation
            results = []
            total_sq_error = 0
            count = 0
            
            for c in cases:
                d_ctx = {"year": "2024", "luck": "default"}
                presets = c.get("dynamic_checks", [])
                target_v = c.get("v_real", {})
                
                if presets:
                    p = presets[0]
                    d_ctx = {"year": p['year'], "luck": p['luck']}
                    if 'v_real_dynamic' in p:
                        target_v = p['v_real_dynamic']
                
                # Calc logic
                calc = engine.calculate_energy(c, d_ctx)
                
                err_c = calc['career'] - target_v.get('career', 0)
                err_w = calc['wealth'] - target_v.get('wealth', 0)
                err_r = calc['relationship'] - target_v.get('relationship', 0)
                
                sq_err = (err_c**2 + err_w**2 + err_r**2) / 3
                rmse_c = np.sqrt(sq_err)
                
                total_sq_error += sq_err
                count += 1
                
                results.append({
                    "Case": f"C{c['id']}",
                    "ID": c['id'],
                    "Desc": c['desc'],
                    "Career_Real": target_v.get('career', 0),
                    "Career_Pred": calc['career'],
                    "Career_Delta": err_c,
                    "Wealth_Real": target_v.get('wealth', 0),
                    "Wealth_Pred": calc['wealth'],
                    "Wealth_Delta": err_w,
                    "Rel_Real": target_v.get('relationship', 0),
                    "Rel_Pred": calc['relationship'],
                    "Rel_Delta": err_r,
                    "RMSE": rmse_c,
                    "Verdict": calc['desc']
                })
            
            global_rmse = np.sqrt(total_sq_error / count) if count > 0 else 0
            df_res = pd.DataFrame(results)

            # 2. Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Global RMSE", f"{global_rmse:.4f}", delta_color="inverse")
            worst_case = df_res.loc[df_res['RMSE'].idxmax()]
            c2.metric("Worst Case", f"{worst_case['Case']}", f"RMSE: {worst_case['RMSE']:.2f}")
            c3.metric("Cases", count)
            c4.metric("Status", "Balanced" if global_rmse < 5.0 else "Tuning Needed")

            # 3. Heatmap
            st.divider()
            st.markdown("#### 🔥 只关注红色区域 (Heatmap)")
            
            # Melt data for heatmap
            heat_rows = []
            for r in results:
                heat_rows.append({"Case": r['Case'], "Aspect": "Career", "Delta": abs(r['Career_Delta']), "Val": r['Career_Delta']})
                heat_rows.append({"Case": r['Case'], "Aspect": "Wealth", "Delta": abs(r['Wealth_Delta']), "Val": r['Wealth_Delta']})
                heat_rows.append({"Case": r['Case'], "Aspect": "Rel", "Delta": abs(r['Rel_Delta']), "Val": r['Rel_Delta']})
            
            df_heat = pd.DataFrame(heat_rows)
            
            fig_heat = px.density_heatmap(
                df_heat, 
                x="Aspect", 
                y="Case", 
                z="Delta", 
                color_continuous_scale=["#00CC96", "#FECB52", "#EF553B"], # Green -> Yellow -> Red
                range_color=[0, 8],
                title="Absolute Error Magnitude (Green < 2, Red > 5)",
                text_auto=True 
            )
            fig_heat.update_layout(height=600)
            st.plotly_chart(fig_heat, use_container_width=True)

            # 4. Scatter (Bias Check)
            st.markdown("#### 📐 偏差偏向性 (Bias Check)")
            scatter_data = []
            for r in results:
                scatter_data.append({"Val": r["Career_Real"], "Pred": r["Career_Pred"], "Type": "Career", "Case": r["Case"]})
                scatter_data.append({"Val": r["Wealth_Real"], "Pred": r["Wealth_Pred"], "Type": "Wealth", "Case": r["Case"]})
                scatter_data.append({"Val": r["Rel_Real"], "Pred": r["Rel_Pred"], "Type": "Rel", "Case": r["Case"]})
            
            df_scatter = pd.DataFrame(scatter_data)
            fig_scatter = px.scatter(
                df_scatter, x="Val", y="Pred", color="Type", hover_data=["Case"],
                title="V_real (X) vs E_pred (Y) - 都在线下则模型偏保守",
                range_x=[-11, 11], range_y=[-11, 11]
            )
            fig_scatter.add_shape(type="line", x0=-10, y0=-10, x1=10, y1=10, line=dict(color="Gray", dash="dash"))
            st.plotly_chart(fig_scatter, use_container_width=True)

    # ==========================
    # TAB 2: SINGLE MICROSCOPE
    # ==========================
    with tab_single:
        st.subheader("单点显微镜 (Detailed Analysis)")
        
        if not cases:
            st.error("No data.")
        else:
            c_sel, c_ctx = st.columns([2, 3])
            with c_sel:
                case_idx = st.selectbox("📂 选择案例", range(len(cases)), format_func=lambda i: f"No.{cases[i]['id']} {cases[i]['day_master']}日主 ({cases[i]['gender']})")
                selected_case = cases[case_idx]
                
            with c_ctx:
                # Dynamic inputs
                presets = selected_case.get("dynamic_checks", [])
                
                c_y, c_l, c_w = st.columns(3)
                def_year = presets[0]['year'] if presets else "甲辰"
                def_luck = presets[0]['luck'] if presets else "癸卯"
                def_ws = selected_case.get("wang_shuai", "身中和")
                
                user_year = c_y.text_input("流年 (Year)", value=def_year)
                user_luck = c_l.text_input("大运 (Luck)", value=def_luck)
                user_wang = c_w.selectbox("旺衰", ["身旺", "身弱", "身中和", "从格", "极弱", "从儿格", "假从"], index=["身旺", "身弱", "身中和", "从格", "极弱", "从儿格", "假从"].index(def_ws) if def_ws in ["身旺", "身弱", "身中和", "从格", "极弱", "从儿格", "假从"] else 2)
                
                case_copy = selected_case.copy()
                case_copy['wang_shuai'] = user_wang 
        
            # Single Calc
            dynamic_ctx = {"year": user_year, "luck": user_luck}
            pred_res = engine.calculate_energy(case_copy, dynamic_ctx)
            
            # --- Rendering Bazi Chart ---
            pe = pred_res.get('pillar_energies', [0]*8)
            bazi = selected_case['bazi'] # [Year, Month, Day, Hour]
            def split_sb(pillar): return (pillar[0], pillar[1]) if pillar and len(pillar)>1 else ("?","?")
            
            y_s, y_b = split_sb(bazi[0])
            m_s, m_b = split_sb(bazi[1])
            d_s, d_b = split_sb(bazi[2])
            h_s, h_b = split_sb(bazi[3])
            l_s, l_b = split_sb(user_luck)
            n_s, n_b = split_sb(user_year)

            st.markdown(f"""
            <style>
                .bazi-box {{ background-color: #1E1E1E; padding: 15px; border-radius: 8px; text-align: center; font-family: 'Courier New'; }}
                .stem {{ font-size: 1.8em; font-weight: bold; color: #FFF; }}
                .branch {{ font-size: 1.8em; font-weight: bold; color: #DDD; }}
                .day-master {{ color: #FF4500 !important; }}
                .dynamic {{ color: #00BFFF !important; }}
                .dynamic-year {{ color: #FF69B4 !important; }}
                .energy-val {{ font-size: 0.5em; color: #4CAF50; }}
            </style>
            <div class="bazi-box">
                <table style="width:100%; text-align:center;">
                    <tr style="color:#888;"><td>年</td><td>月</td><td>日</td><td>时</td><td width="20"></td><td>运</td><td>岁</td></tr>
                    <tr>
                        <td class="stem">{y_s}<div class="energy-val">{pe[0]}</div></td>
                        <td class="stem">{m_s}<div class="energy-val">{pe[2]}</div></td>
                        <td class="stem day-master">{d_s}<div class="energy-val">{pe[4]}</div></td>
                        <td class="stem">{h_s}<div class="energy-val">{pe[6]}</div></td>
                        <td></td>
                        <td class="stem dynamic">{l_s}</td>
                        <td class="stem dynamic-year">{n_s}</td>
                    </tr>
                    <tr>
                        <td class="branch">{y_b}<div class="energy-val">{pe[1]}</div></td>
                        <td class="branch">{m_b}<div class="energy-val">{pe[3]}</div></td>
                        <td class="branch day-master">{d_b}<div class="energy-val">{pe[5]}</div></td>
                        <td class="branch">{h_b}<div class="energy-val">{pe[7]}</div></td>
                        <td></td>
                        <td class="branch dynamic">{l_b}</td>
                        <td class="branch dynamic-year">{n_b}</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            # --- Results ---
            st.markdown("#### 结果分析")
            c_res, c_real, c_chart = st.columns([1, 1, 2])
            
            with c_res:
                st.info(f"AI 判词: {pred_res['desc']}")
                st.write(f"💼 事业: **{pred_res['career']:.1f}**")
                st.write(f"💰 财富: **{pred_res['wealth']:.1f}**")
                st.write(f"❤️ 感情: **{pred_res['relationship']:.1f}**")

            target_v_real = selected_case.get("v_real", {})
            expert_note = ""
            preset_match = next((p for p in presets if p['year'] == user_year), None)
            if preset_match:
                target_v_real = preset_match['v_real_dynamic']
                expert_note = preset_match.get('note', '')

            with c_real:
                st.success("专家真值" + (f" ({expert_note})" if expert_note else ""))
                st.write(f"Career: {target_v_real.get('career', '?')}")
                st.write(f"Wealth: {target_v_real.get('wealth', '?')}")
                st.write(f"Rel: {target_v_real.get('relationship', '?')}")

            with c_chart:
                cats = ["事业", "财富", "感情"]
                try:
                    y_r = [float(target_v_real.get('career', 0)), float(target_v_real.get('wealth', 0)), float(target_v_real.get('relationship', 0))]
                except: y_r = [0,0,0]
                y_p = [pred_res['career'], pred_res['wealth'], pred_res['relationship']]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=cats, y=y_r, name='Real', line=dict(color='#00FF00', width=3)))
                fig.add_trace(go.Scatter(x=cats, y=y_p, name='AI', line=dict(color='#00BFFF', dash='dash', width=3)))
                fig.update_layout(height=250, margin=dict(t=10,b=10))
                st.plotly_chart(fig, use_container_width=True)

            # Narrative Cards (New in V2.9)
            narrative_events = pred_res.get('narrative_events', [])
            if narrative_events:
                st.markdown("#### 📜 核心叙事 (Narrative Events)")
                nc1, nc2 = st.columns(2)
                for i, event in enumerate(narrative_events):
                    with nc1 if i % 2 == 0 else nc2:
                        render_narrative_card(event)

            # Timeline
            st.divider()
            with st.expander("⏳ 12年运势模拟 (Timeline Simulation)"):
                years = range(2024, 2036)
                sim_data = []
                # Use fresh engine instance with same params
                sim_engine = QuantumEngine(current_params)
                for y in years:
                    gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"][(y - 2024) % 10]
                    zhi = ["辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯"][(y - 2024) % 12]
                    d_c = {"year": f"{gan}{zhi}", "luck": user_luck}
                    r = sim_engine.calculate_energy(selected_case, d_c)
                    sim_data.append({"year": y, "career": r['career'], "wealth": r['wealth'], "rel": r['relationship'], "desc": r['desc']})
                
                sdf = pd.DataFrame(sim_data)
                fig_t = go.Figure()
                fig_t.add_trace(go.Scatter(x=sdf['year'], y=sdf['career'], name='Career'))
                fig_t.add_trace(go.Scatter(x=sdf['year'], y=sdf['wealth'], name='Wealth'))
                fig_t.add_trace(go.Scatter(x=sdf['year'], y=sdf['rel'], name='Rel'))
                fig_t.update_layout(height=300, title="未来趋势")
                st.plotly_chart(fig_t, use_container_width=True)

if __name__ == "__main__":
    render()
