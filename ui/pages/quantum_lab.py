import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
import numpy as np

from core.quantum_engine import QuantumEngine

def render():
    # Helper class moved to core.quantum_engine
    pass

    # --- Load Data ---
    @st.cache_data
    def load_cases():
        path = os.path.join(os.path.dirname(__file__), "../../data/calibration_cases.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return []

    cases = load_cases()

    # --- SIDEBAR ---
    st.sidebar.title("🎛️ 物理参数 (Physics)")
    w_e_val = st.sidebar.slider("We: 全局能量增益", 0.5, 2.0, 1.0, 0.1)
    f_yy_val = st.sidebar.slider("F(阴阳): 异性耦合效率", 0.8, 1.5, 1.1, 0.05)
    
    st.sidebar.subheader("W_事业 (Career)")
    w_career_officer = st.sidebar.slider("W_官杀 (Officer)", 0.0, 1.0, 0.8, 0.05)
    w_career_resource = st.sidebar.slider("W_印星 (Resource)", 0.0, 1.0, 0.1, 0.05)
    w_career_output = st.sidebar.slider("W_食伤 (Tech/Art)", 0.0, 1.0, 0.0, 0.05, help="食伤技艺对事业的直接贡献")
    k_control = st.sidebar.slider("K_制杀系数 (Control)", 0.0, 1.0, 0.55, help="食神制杀（Output controlling Officer）的转化效率")
    k_buffer = st.sidebar.slider("K_化杀系数 (Buffer)", 0.0, 1.0, 0.40, help="印星化杀（Resource buffering Officer）的转化效率")
    k_mutiny = st.sidebar.slider("K_叛变系数 (Mutiny)", 0.0, 3.0, 1.8, help="伤官见官（Weak Self Output attacking Officer）的惩罚系数")

    st.sidebar.markdown("---")
    st.sidebar.subheader("W_财富 (Wealth)")
    w_wealth_cai = st.sidebar.slider("W_财星 (Wealth)", 0.0, 1.0, 0.6, 0.05)
    w_wealth_output = st.sidebar.slider("W_食伤 (Source)", 0.0, 1.0, 0.4, 0.05)
    k_capture = st.sidebar.slider("K_担财系数 (Capture)", 0.0, 0.5, 0.0, 0.05, help="身旺担财：日主强旺对财富的正向贡献")
    k_leak = st.sidebar.slider("K_泄身系数 (Leak)", 0.0, 2.0, 0.87, 0.01, help="身弱泄气：食伤太旺导致贫困")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("W_感情 (Relationship)")
    w_rel_spouse = st.sidebar.slider("W_配偶星 (Spouse)", 0.1, 1.0, 0.35, 0.05)
    w_rel_self = st.sidebar.slider("W_日主 (Self)", -0.5, 0.5, 0.20, 0.05, help="负值代表身旺克妻/夫")
    w_rel_output = st.sidebar.slider("W_食伤 (Output)", 0.0, 1.0, 0.15, 0.05)
    k_clash = st.sidebar.slider("K_比劫克制 (Clash)", 0.0, 2.0, 0.0, 0.1, help="身旺财弱：比劫夺财")
    k_press = st.sidebar.slider("K_官杀攻身 (Press)", 0.0, 2.0, 0.0, 0.1, help="身弱杀重：压力摧毁感情")
    
    current_params = {
        "w_e_weight": w_e_val,
        "f_yy_correction": f_yy_val,
        
        "w_career_officer": w_career_officer,
        "w_career_resource": w_career_resource,
        "w_career_output": w_career_output,
        "k_control": k_control,
        "k_buffer": k_buffer,
        "k_mutiny": k_mutiny,
        
        "w_wealth_cai": w_wealth_cai,
        "w_wealth_output": w_wealth_output,
        "k_capture": k_capture,
        "k_leak": k_leak,

        "w_rel_spouse": w_rel_spouse,
        "w_rel_self": w_rel_self,
        "w_rel_output": w_rel_output,
        "k_clash": k_clash,
        "k_pressure": k_press
    }
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("💾 导出黄金参数 (Export)"):
        st.json(current_params)
        st.caption("贝叶斯迭代完成。请复制此 JSON 固化模型。")

    # --- MAIN UI LAYOUT ---
    st.title("🧪 量子八字 V2.1 验证工作台")
    st.markdown("Dynamic Space-Time Validation Module")

    # [Area 1] Setup & Charting
    st.subheader("1. 排盘与时空设定 (Charting & Context)")
    
    if not cases:
        st.error("Data missing.")
        return

    c_sel, c_ctx = st.columns([2, 3])
    with c_sel:
        case_idx = st.selectbox("📂 选择案例", range(len(cases)), format_func=lambda i: f"No.{cases[i]['id']} {cases[i]['day_master']}日主 ({cases[i]['gender']})")
        selected_case = cases[case_idx]
        
    with c_ctx:
        # Dynamic inputs
        presets = selected_case.get("dynamic_checks", [])
        
        c_y, c_l, c_w = st.columns(3)
        
        # Load default/preset values
        def_year = presets[0]['year'] if presets else "甲辰"
        def_luck = presets[0]['luck'] if presets else "癸卯"
        def_ws = selected_case.get("wang_shuai", "身中和")
        
        user_year = c_y.text_input("流年 (Year)", value=def_year)
        user_luck = c_l.text_input("大运 (Luck)", value=def_luck)
        user_wang = c_w.selectbox("旺衰 (Strength)", ["身旺", "身弱", "身中和", "从格", "极弱"], index=["身旺", "身弱", "身中和", "从格", "极弱"].index(def_ws) if def_ws in ["身旺", "身弱", "身中和", "从格", "极弱"] else 2)
        
        # Update case data with user overrides for calculation
        case_copy = selected_case.copy()
        case_copy['wang_shuai'] = user_wang 
    
    # --- CALCULATION (Moved Up) ---
    dynamic_ctx = {"year": user_year, "luck": user_luck}
    engine = QuantumEngine(current_params)
    pred_res = engine.calculate_energy(case_copy, dynamic_ctx)
    
    # Get Atomic Energies
    pe = pred_res.get('pillar_energies', [0]*8) # [Ys, Yb, Ms, Mb, Ds, Db, Hs, Hb]

    # Show Bazi Pillars
    bazi = selected_case['bazi'] # [Year, Month, Day, Hour]
    
    # Split Stem/Branch
    def split_sb(pillar):
        if not pillar or len(pillar) < 2: return "?", "?"
        return pillar[0], pillar[1]
    
    y_s, y_b = split_sb(bazi[0])
    m_s, m_b = split_sb(bazi[1])
    d_s, d_b = split_sb(bazi[2])
    h_s, h_b = split_sb(bazi[3])
    
    l_s, l_b = split_sb(user_luck)
    n_s, n_b = split_sb(user_year)

    # Standard Traditional Layout with Energy
    st.markdown(f"""
    <style>
        .bazi-box {{
            background-color: #1E1E1E;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-family: 'Courier New', Courier, monospace;
        }}
        .bazi-table {{
            width: 100%;
            table-layout: fixed;
            border-collapse: separate;
            border-spacing: 5px 0;
        }}
        .bazi-header {{
            font-size: 0.9em;
            color: #888;
            margin-bottom: 5px;
        }}
        .stem {{
            font-size: 1.8em;
            font-weight: bold;
            color: #FFF;
            line-height: 1.2;
        }}
        .branch {{
            font-size: 1.8em;
            font-weight: bold;
            color: #DDD;
            line-height: 1.2;
        }}
        .day-master {{
            color: #FF4500 !important;
        }}
        .dynamic {{
            color: #00BFFF !important;
        }}
        .dynamic-year {{
            color: #FF69B4 !important;
        }}
        .energy-val {{
            font-size: 0.5em;
            color: #4CAF50;
            font-family: sans-serif;
            margin-top: -5px;
            margin-bottom: 5px;
        }}
        .energy-val-low {{
             font-size: 0.5em;
             color: #555;
             font-family: sans-serif;
             margin-top: -5px;
             margin-bottom: 5px;
        }}
    </style>
    
    <div class="bazi-box">
        <table class="bazi-table">
            <tr>
                <td><div class="bazi-header">年柱</div></td>
                <td><div class="bazi-header">月柱</div></td>
                <td><div class="bazi-header">日柱</div></td>
                <td><div class="bazi-header">时柱</div></td>
                <td style="width: 20px;"></td> <!-- Spacer -->
                <td><div class="bazi-header">大运</div></td>
                <td><div class="bazi-header">流年</div></td>
            </tr>
            <tr>
                <!-- Stems -->
                <td class="stem">{y_s}<div class="{ 'energy-val' if pe[0]>2 else 'energy-val-low'}">{pe[0]}</div></td>
                <td class="stem">{m_s}<div class="{ 'energy-val' if pe[2]>2 else 'energy-val-low'}">{pe[2]}</div></td>
                <td class="stem day-master">{d_s}<div class="{ 'energy-val' if pe[4]>2 else 'energy-val-low'}">{pe[4]}</div></td>
                <td class="stem">{h_s}<div class="{ 'energy-val' if pe[6]>2 else 'energy-val-low'}">{pe[6]}</div></td>
                <td></td>
                <td class="stem dynamic">{l_s}</td>
                <td class="stem dynamic-year">{n_s}</td>
            </tr>
            <tr>
                <!-- Branches -->
                <td class="branch">{y_b}<div class="{ 'energy-val' if pe[1]>2 else 'energy-val-low'}">{pe[1]}</div></td>
                <td class="branch">{m_b}<div class="{ 'energy-val' if pe[3]>2 else 'energy-val-low'}">{pe[3]}</div></td>
                <td class="branch day-master">{d_b}<div class="{ 'energy-val' if pe[5]>2 else 'energy-val-low'}">{pe[5]}</div></td>
                <td class="branch">{h_b}<div class="{ 'energy-val' if pe[7]>2 else 'energy-val-low'}">{pe[7]}</div></td>
                <td></td>
                <td class="branch dynamic">{l_b}</td>
                <td class="branch dynamic-year">{n_b}</td>
            </tr>
        </table>
        <div style="margin-top: 10px; font-size: 0.9em; color: #AAA;">
            旺衰判定: <span style="color: #FFF; font-weight: bold;">{user_wang}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- CALCULATION (Done above) ---
    # Find V_Real (Dynamic or Static)
    target_v_real = selected_case["v_real"] # Default Static
    expert_note = "（无流年专家断语，使用原局参考）"
    
    # Check if user inputs match a preset dynamic check
    preset_match = next((p for p in presets if p['year'] == user_year), None)
    if preset_match:
        target_v_real = preset_match['v_real_dynamic']
        expert_note = f"【专家断语】: {preset_match['note']}"
    else:
        # If no dynamic preset, we might only have static V_Real.
        pass

    # engine calculation already done
    # pred_res already exists

    # [Area 1.5] Ten Gods Stats (Full 10)
    st.subheader("1.5. 十神能量分布 (Ten Gods Stats)")
    parts_10 = pred_res.get('ten_gods', {})
    
    # Grid Layout: 5 Columns x 2 Rows
    # Row 1: BiJian, ShiShen, PianCai, QiSha, PianYin
    r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
    # Row 2: JieCai, ShangGuan, ZhengCai, ZhengGuan, ZhengYin
    r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns(5)
    
    def style_metric(col, label, val):
        val = float(val)
        color = "#AAA"
        if val > 6: color = "#FF0000" # Strong -> Red
        elif val > 3: color = "#00FF00" # Med -> Green
        elif val > 0: color = "#FFFFFF" # Low -> White
        
        col.markdown(f"""
        <div style="text-align: center; border: 1px solid #333; padding: 5px; border-radius: 5px; margin-bottom: 5px;">
            <div style="font-size: 0.8em; color: #888;">{label}</div>
            <div style="font-size: 1.2em; font-weight: bold; color: {color};">{val}</div>
        </div>
        """, unsafe_allow_html=True)

    # Column 1: Self
    style_metric(r1c1, "比肩 (Bi Jian)", parts_10.get('bi_jian', 0))
    style_metric(r2c1, "劫财 (Jie Cai)", parts_10.get('jie_cai', 0))
    
    # Column 2: Output
    style_metric(r1c2, "食神 (Shi Shen)", parts_10.get('shi_shen', 0))
    style_metric(r2c2, "伤官 (Shang Guan)", parts_10.get('shang_guan', 0))
    
    # Column 3: Wealth
    style_metric(r1c3, "偏财 (Pian Cai)", parts_10.get('pian_cai', 0))
    style_metric(r2c3, "正财 (Zheng Cai)", parts_10.get('zheng_cai', 0))
    
    # Column 4: Officer
    style_metric(r1c4, "七杀 (Qi Sha)", parts_10.get('qi_sha', 0))
    style_metric(r2c4, "正官 (Zheng Guan)", parts_10.get('zheng_guan', 0))
    
    # Column 5: Resource
    style_metric(r1c5, "偏印 (Pian Yin)", parts_10.get('pian_yin', 0))
    style_metric(r2c5, "正印 (Zheng Yin)", parts_10.get('zheng_yin', 0))

    st.markdown("---")

    # [Area 2] Verdict & Comparison
    st.subheader("2. 断语验证 (Verdict Check)")
    
    c_ai, c_human = st.columns(2)
    
    with c_ai:
        st.markdown("🤖 **AI 量子断语 (Prediction)**")
        if pred_res['desc']:
            st.info(f"相位: {pred_res['desc']}")
            
        def get_verdict(score, dim):
            t = "平稳"
            if score > 6: t = "大吉/爆发"
            elif score > 2: t = "吉/上升"
            elif score < -6: t = "大凶/崩塌"
            elif score < -2: t = "凶/阻力"
            return f"**{score}** ({t})"
            
        st.write(f"💼 **事业**: {get_verdict(pred_res['career'], '事业')}")
        st.write(f"💰 **财富**: {get_verdict(pred_res['wealth'], '财富')}")
        st.write(f"❤️ **感情**: {get_verdict(pred_res['relationship'], '感情')}")

    with c_human:
        st.markdown("👨‍🏫 **专家/真实反馈 (Ground Truth)**")
        st.success(expert_note)
        st.write(f"💼 **事业 (真值)**: {target_v_real['career']}")
        st.write(f"💰 **财富 (真值)**: {target_v_real['wealth']}")
        st.write(f"❤️ **感情 (真值)**: {target_v_real['relationship']}")
    
    # [Area 3] Visualization (2D Line Chart)
    st.subheader("3. 能量波形对比 (Energy Waveform)")
    
    # Calculate MAE
    mae = (abs(pred_res['career']-target_v_real['career']) + 
           abs(pred_res['wealth']-target_v_real['wealth']) + 
           abs(pred_res['relationship']-target_v_real['relationship'])) / 3
    
    # Prepare Data
    categories = ["事业", "财富", "感情"]
    y_real = [target_v_real['career'], target_v_real['wealth'], target_v_real['relationship']]
    y_pred = [pred_res['career'], pred_res['wealth'], pred_res['relationship']]
    
    fig = go.Figure()
    
    # 1. Real Line
    fig.add_trace(go.Scatter(
        x=categories, y=y_real,
        mode='lines+markers',
        name='专家 (Real)',
        line=dict(color='#00FF00', width=3),
        marker=dict(size=10, symbol='circle')
    ))
    
    # 2. Pred Line
    fig.add_trace(go.Scatter(
        x=categories, y=y_pred,
        mode='lines+markers', # lines+markers
        name='预测 (AI)',
        line=dict(color='#00BFFF', width=3, dash='dash'), # Dashed for prediction
        marker=dict(size=10, symbol='diamond')
    ))
    
    fig.update_layout(
        title=f"模型拟合度 (MAE: {mae:.2f})",
        yaxis=dict(title="能量级 (Energy)", range=[-12, 12], zeroline=True, zerolinecolor='#555'),
        xaxis=dict(title="维度 (Dimension)"),
        legend=dict(x=0, y=1, bgcolor='rgba(0,0,0,0.5)'),
        margin=dict(l=40, r=40, t=40, b=40),
        height=350
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- Footer ---
    st.caption("Antigravity Quantum Workbench v2.1 | Powered by Streamlit & Plotly")

    
    # --- 4. DYNAMIC SIMULATION (Zeitgeist Cinema Integrated) ---
    st.markdown("---")
    st.header("4. 动态流年模拟 (Dynamic Timeline)")
    st.caption(f"基于当前滑块参数，模拟 {case_copy.get('day_master', '')}日主 未来12年的能量波动。")

    years = range(2024, 2036)
    sim_data = []
    
    # Re-instantiate engine with current live params ensures real-time feedback
    sim_engine = QuantumEngine(current_params)
    
    for y in years:
        # Simple Mock GanZhi (For demo purposes)
        gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"][(y - 2024) % 10]
        zhi = ["辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯"][(y - 2024) % 12]
        year_pillar = f"{gan}{zhi}"
        
        d_ctx = {"year": year_pillar, "luck": "Simulated"}
        res = sim_engine.calculate_energy(case_copy, d_ctx)
        
        sim_data.append({
            "year": y,
            "ganzhi": year_pillar,
            "career": res.get('career', 0),
            "wealth": res.get('wealth', 0),
            "relationship": res.get('relationship', 0),
            "desc": res.get('desc', '')
        })
        
    df_sim = pd.DataFrame(sim_data)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sim['year'], y=df_sim['career'], mode='lines+markers', name='事业 (Career)', hovertext=df_sim['desc'], line=dict(color='#00CED1', width=3))) 
    fig.add_trace(go.Scatter(x=df_sim['year'], y=df_sim['wealth'], mode='lines+markers', name='财富 (Wealth)', hovertext=df_sim['desc'], line=dict(color='#FFD700', width=3))) 
    fig.add_trace(go.Scatter(x=df_sim['year'], y=df_sim['relationship'], mode='lines+markers', name='感情 (Rel)', hovertext=df_sim['desc'], line=dict(color='#FF1493', width=3)))
    
    # Annotations
    for idx, row in df_sim.iterrows():
        if row['desc']:
            fig.add_annotation(
                x=row['year'], 
                y=max(row['career'], row['wealth'], row['relationship']) + 1,
                text=row['desc'].split(' ')[0], 
                showarrow=False
            )

    fig.update_layout(
        title=f"{case_copy.get('bazi', [''])[2]}日主 ({case_copy.get('desc', '')}) 12年运势",
        xaxis_title="流年",
        yaxis_title="能量级",
        hovermode="x unified",
        template="plotly_dark",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    render()
