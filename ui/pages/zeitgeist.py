import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import sys

# Append root path to sys.path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.quantum_engine import QuantumEngine

# Load Golden Parameters
GOLDEN_PARAMS_PATH = os.path.join(os.path.dirname(__file__), '../../data/golden_parameters.json')
CALIBRATION_CASES_PATH = os.path.join(os.path.dirname(__file__), '../../data/calibration_cases.json')

try:
    with open(GOLDEN_PARAMS_PATH, 'r') as f:
        GOLDEN_CONFIG = json.load(f)
        GOLDEN_WEIGHTS = GOLDEN_CONFIG.get('weights', {})
        # Flatten structure for Engine consumption
        FLATTENED_PARAMS = {
            "w_e_weight": GOLDEN_WEIGHTS.get("w_e_weight", 1.0),
            "f_yy_correction": GOLDEN_WEIGHTS.get("f_yy_correction", 1.1),
            
            # Career
            "w_career_officer": GOLDEN_WEIGHTS.get("career", {}).get("w_officer", 0.8),
            "w_career_resource": GOLDEN_WEIGHTS.get("career", {}).get("w_resource", 0.1),
            "w_career_output": GOLDEN_WEIGHTS.get("career", {}).get("w_output", 0.0),
            "k_control": GOLDEN_WEIGHTS.get("career", {}).get("k_control", 0.55),
            "k_buffer": GOLDEN_WEIGHTS.get("career", {}).get("k_buffer", 0.40),

            # Wealth
            "w_wealth_cai": GOLDEN_WEIGHTS.get("wealth", {}).get("w_wealth", 0.6),
            "w_wealth_output": GOLDEN_WEIGHTS.get("wealth", {}).get("w_output", 0.4),
            "k_capture": GOLDEN_WEIGHTS.get("wealth", {}).get("k_capture", 0.40),
            "k_leak": GOLDEN_WEIGHTS.get("wealth", {}).get("k_leak", 0.87),

            # Relationship
            "w_rel_spouse": GOLDEN_WEIGHTS.get("relationship", {}).get("w_spouse", 0.35),
            "w_rel_self": GOLDEN_WEIGHTS.get("relationship", {}).get("w_self", 0.0),
            "w_rel_output": GOLDEN_WEIGHTS.get("relationship", {}).get("w_output", 0.15),
            "k_clash": GOLDEN_WEIGHTS.get("relationship", {}).get("k_clash", 0.10),
            "k_pressure": GOLDEN_WEIGHTS.get("relationship", {}).get("k_pressure", 1.0)
        }
except Exception as e:
    # Default fallback
    FLATTENED_PARAMS = {}

def load_cases():
    try:
        with open(CALIBRATION_CASES_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load cases: {e}")
        return []

def render():
    st.set_page_config(page_title="Zeitgeist Cinema", page_icon="🎬", layout="wide")
    
    st.title("🎬 命运波函数影院 (Zeitgeist Cinema)")
    st.caption("Powered by Quantum Engine V2.2 | Golden Parameters Enabled")
    
    # Sidebar: Case Selector
    cases = load_cases()
    case_options = {f"No.{c['id']} {c['bazi'][2]}日主 ({c['desc']})": c for c in cases}
    selected_label = st.sidebar.selectbox("选择主演 (Subject)", list(case_options.keys()))
    selected_case = case_options[selected_label]
    
    # ---------------------------
    # 1. 12-Year Simulation
    # ---------------------------
    st.subheader(f"1. 命运心电图 (Destiny ECG): 2024-2035")
    
    years = range(2024, 2036)
    
    # Simulation Data
    sim_data = []
    
    engine = QuantumEngine(FLATTENED_PARAMS)
    
    for y in years:
        # Mock GanZhi generation for demo (In real app, use Calendar Utils)
        # 2024=甲辰, 2025=乙巳, 2026=丙午...
        gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"][(y - 2024) % 10]
        zhi = ["辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯"][(y - 2024) % 12]
        year_pillar = f"{gan}{zhi}"
        
        # Inject "Jia Zi" logic for demo if user wants to see the crash
        # Let's map 2032 (Ren Zi) -> Jia Zi for demo? Or just let the engine generic logic work.
        # Since we implemented generic logic: "Jia Zi" in year + Strong Output triggers crash.
        # Let's artificially force 2024 to be "甲子" for Case 1 to verify? No, let's keep it real.
        # Real 2024 is Jia Chen (Wood/Earth). High prob of Owl Steals Food if generic logic is loose.
        
        d_ctx = {"year": year_pillar, "luck": "测试大运"}
        res = engine.calculate_energy(selected_case, d_ctx)
        
        sim_data.append({
            "year": y,
            "ganzhi": year_pillar,
            "career": res.get('career', 0),
            "wealth": res.get('wealth', 0),
            "relationship": res.get('relationship', 0),
            "desc": res.get('desc', ''),
            "particles": res.get('particles', {}),
            "ten_gods": res.get('ten_gods', {}),  # If available
            "raw_res": res # Keep full result for drill down
        })
        
    df_sim = pd.DataFrame(sim_data)
    
    # Plotly Chart
    fig = go.Figure()
    
    # Traces
    fig.add_trace(go.Scatter(x=df_sim['year'], y=df_sim['career'], mode='lines+markers', name='事业 (Career)', hovertext=df_sim['desc'], line=dict(color='#00CED1', width=3)))
    fig.add_trace(go.Scatter(x=df_sim['year'], y=df_sim['wealth'], mode='lines+markers', name='财富 (Wealth)', hovertext=df_sim['desc'], line=dict(color='#FFD700', width=3)))
    fig.add_trace(go.Scatter(x=df_sim['year'], y=df_sim['relationship'], mode='lines+markers', name='感情 (Rel)', hovertext=df_sim['desc'], line=dict(color='#FF1493', width=3)))
    
    # Annotations for "Events"
    for idx, row in df_sim.iterrows():
        if row['desc']:
            fig.add_annotation(
                x=row['year'], 
                y=max(row['career'], row['wealth'], row['relationship']) + 1,
                text=row['desc'].split(' ')[0], # Show icon only
                showarrow=False,
                font=dict(size=14)
            )

    fig.update_layout(
        title=f"12年运势波幅 ({selected_case['bazi'][2]}日主)",
        xaxis_title="流年 (Year)",
        yaxis_title="能量级别 (Energy Level)",
        hovermode="x unified",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ---------------------------
    # 2. Time Shuttle & Particle Chamber
    # ---------------------------
    st.markdown("---")
    st.subheader("2. 粒子碰撞室 (Particle Chamber)")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        selected_year = st.select_slider("拖动时间轴以观测粒子状态", options=years, value=2024)
        
        # Get data for selected year
        current_data = next(item for item in sim_data if item["year"] == selected_year)
        st.markdown(f"### {current_data['year']} {current_data['ganzhi']}")
        st.info(f"事件: {current_data['desc']}" if current_data['desc'] else "状态: 平稳")
        
    with c2:
        # Particle Visualization
        # Display the 5 Particles as Progress Bars or Metrics
        parts = current_data['particles']
        
        cols = st.columns(5)
        p_names = {
            "self": "比劫 (Self)",
            "output": "食伤 (Output)",
            "wealth": "财星 (Wealth)",
            "officer": "官杀 (Officer)",
            "resource": "印星 (Resource)"
        }
        
        for i, (key, label) in enumerate(p_names.items()):
            val = parts.get(key, 0)
            with cols[i]:
                st.metric(label.split(' ')[0], f"{val:.1f}")
                # Visual Bar
                norm_val = min(1.0, max(0.0, (val + 5) / 15)) # Normalize -5 to 10 -> 0 to 1
                color = "red" if val > 6 else "green" if val > 3 else "blue"
                st.progress(norm_val)

    # ---------------------------
    # 3. Penalty Drill Down
    # ---------------------------
    if current_data['desc']:
        st.markdown("### ⚠️ 物理效应分析")
        st.warning(f"检测到物理干涉: **{current_data['desc']}**")
        
        # Explain Why
        full_res = current_data['raw_res']
        # This part requires engine to return 'debug_info' or similar. 
        # For now we infer from values.
        st.write("当流年引发物理干涉时，原本的能量平衡被打破。例如‘枭印夺食’导致食伤能量骤降，从而破坏了财富的源头（泄身惩罚失效）或事业的制杀能力（格局破败）。")
        
if __name__ == "__main__":
    render()
