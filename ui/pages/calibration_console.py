import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
import numpy as np

# Set page config
st.set_page_config(page_title="Quantum Calibration Console", page_icon="🎛️", layout="wide")

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from core.unified_engine import UnifiedEngine as QuantumEngine  # V9.1 Unified Engine

# --- CONSTANTS ---
CASES_PATH = os.path.join(os.path.dirname(__file__), "../../data/calibration_cases.json")
PARAMS_PATH = os.path.join(os.path.dirname(__file__), "../../data/golden_parameters.json")

# --- DATA LOADING ---
@st.cache_data
def load_cases():
    if os.path.exists(CASES_PATH):
        with open(CASES_PATH, "r") as f:
            return json.load(f)
    return []

def load_params():
    if os.path.exists(PARAMS_PATH):
        with open(PARAMS_PATH, "r") as f:
            return json.load(f)
    return {}

def save_params(new_params):
    # We need to preserve the original structure
    original = load_params()
    
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
    
    # flags
    original['logic_flags']['enable_mediation_exemption'] = new_params.get('enable_mediation_exemption', True)
    original['logic_flags']['enable_structural_clash'] = new_params.get('enable_structural_clash', True)

    with open(PARAMS_PATH, "w") as f:
        json.dump(original, f, indent=4, ensure_ascii=False)
    st.success("✅ Parameters Saved to Disk!")

# --- UI ---
st.title("🎛️ Quantum Calibration Console")
st.markdown("### V9.1 Physics Engine Tuning (Hot-Reload)")

from core.config_manager import ConfigManager

# Load Active Config
config = ConfigManager.load_config()

# 1. PHYSICS CONTROLS
st.sidebar.header("🛠️ Physics Layers")

st.sidebar.subheader("Layer 1: Base Physics")
p_cfg = config.get('physics', {})
new_stem = st.sidebar.slider("Stem Score (Base Unit)", 5.0, 20.0, float(p_cfg.get('stem_score', 10.0)), 0.5)
new_branch_main = st.sidebar.slider("Branch Main Qi", 5.0, 20.0, float(p_cfg.get('branch_main_qi', 10.0)), 0.5)
new_branch_sub = st.sidebar.slider("Branch Sub Qi", 1.0, 10.0, float(p_cfg.get('branch_sub_qi', 7.0)), 0.5)

st.sidebar.subheader("Layer 2: Seasonal")
s_cfg = config.get('seasonal', {})
new_cmd_bonus = st.sidebar.slider("Command Bonus (Multiplier)", 0.0, 5.0, float(s_cfg.get('monthly_command_bonus', 1.5)), 0.1)
new_gen_bonus = st.sidebar.slider("Generation Bonus (Multiplier)", 0.0, 5.0, float(s_cfg.get('generation_bonus', 1.2)), 0.1)

# Construct Params Object for Save
new_config = {
    "physics": {
        "stem_score": new_stem,
        "branch_main_qi": new_branch_main,
        "branch_sub_qi": new_branch_sub
    },
    "seasonal": {
        "monthly_command_bonus": new_cmd_bonus,
        "generation_bonus": new_gen_bonus
    }
}

# Save Button
if st.sidebar.button("💾 Apply & Save Config"):
    ConfigManager.save_config(new_config)
    st.sidebar.success("Config saved! Engine will reload.")
    st.rerun()

# 2. CALCULATION ENGINE
# Initialize Engine (it will auto-load config via ConfigManager in processors)
engine = QuantumEngine() # No need to pass params, processors read ConfigManager directly
cases = load_cases()

results = []
total_sq_err = 0
count = 0

for c in cases:
    # Handle Dynamic Context
    d_ctx = {"year": "2024", "luck": "default"}
    target_v = c.get("v_real", {})
    if c.get("dynamic_checks"):
        p = c["dynamic_checks"][0]
        d_ctx = {"year": p['year'], "luck": p['luck']}
        if 'v_real_dynamic' in p:
            target_v = p['v_real_dynamic']

    # Calc
    res = engine.calculate_energy(c, d_ctx)
    
    # Deltas
    dc = res['career'] - target_v.get('career', 0)
    dw = res['wealth'] - target_v.get('wealth', 0)
    dr = res['relationship'] - target_v.get('relationship', 0)
    
    sq_err = (dc**2 + dw**2 + dr**2) / 3
    rmse = np.sqrt(sq_err)
    
    total_sq_err += sq_err
    count += 1
    
    results.append({
        "Case": f"C{c['id']}",
        "ID": c['id'],
        "Desc": c['desc'],
        "Career_Real": target_v.get('career', 0),
        "Career_Pred": res['career'],
        "Career_Delta": dc,
        "Wealth_Real": target_v.get('wealth', 0),
        "Wealth_Pred": res['wealth'],
        "Wealth_Delta": dw,
        "Rel_Real": target_v.get('relationship', 0),
        "Rel_Pred": res['relationship'],
        "Rel_Delta": dr,
        "RMSE": rmse,
        "Verdict": res['desc']
    })

df = pd.DataFrame(results)
global_rmse = np.sqrt(total_sq_err / count) if count > 0 else 0

# 3. DASHBOARD METRICS
col1, col2, col3, col4 = st.columns(4)
col1.metric("Global RMSE", f"{global_rmse:.4f}", delta_color="inverse")
col2.metric("Worst Case", f"{df.iloc[df['RMSE'].argmax()]['Case']}", f"RMSE: {df['RMSE'].max():.2f}")
col3.metric("Cases Loaded", len(cases))
col4.metric("Engine Version", "V2.6.1")

# 4. HEATMAP (The Grid)
st.subheader("🌡️ Global Error Heatmap")

# Transform for Heatmap
heat_data = []
for r in results:
    heat_data.append({"Case": r["Case"], "Aspect": "Career", "Delta": r["Career_Delta"], "AbsDelta": abs(r["Career_Delta"])})
    heat_data.append({"Case": r["Case"], "Aspect": "Wealth", "Delta": r["Wealth_Delta"], "AbsDelta": abs(r["Wealth_Delta"])})
    heat_data.append({"Case": r["Case"], "Aspect": "Rel", "Delta": r["Rel_Delta"], "AbsDelta": abs(r["Rel_Delta"])})

df_heat = pd.DataFrame(heat_data)

# Visual with Plotly
fig_heat = px.density_heatmap(
    df_heat, 
    x="Aspect", 
    y="Case", 
    z="AbsDelta", 
    color_continuous_scale=["#00CC96", "#FECB52", "#EF553B"], # Green, Yellow, Red
    range_color=[0, 8],
    title="Absolute Error Magnitude (Green < 2, Red > 5)"
)
fig_heat.update_layout(height=600)
st.plotly_chart(fig_heat, width='stretch')

# 5. SCATTER PLOT (Correlation)
st.subheader("📈 Prediction vs Reality Correlation")

scatter_data = []
for r in results:
    scatter_data.append({"Val": r["Career_Real"], "Pred": r["Career_Pred"], "Type": "Career", "Case": r["Case"]})
    scatter_data.append({"Val": r["Wealth_Real"], "Pred": r["Wealth_Pred"], "Type": "Wealth", "Case": r["Case"]})
    scatter_data.append({"Val": r["Rel_Real"], "Pred": r["Rel_Pred"], "Type": "Rel", "Case": r["Case"]})

df_scatter = pd.DataFrame(scatter_data)

fig_scatter = px.scatter(
    df_scatter, 
    x="Val", 
    y="Pred", 
    color="Type", 
    hover_data=["Case"],
    title="V_real (X) vs E_pred (Y)",
    range_x=[-11, 11],
    range_y=[-11, 11]
)
# Add y=x line
fig_scatter.add_shape(type="line", x0=-10, y0=-10, x1=10, y1=10, line=dict(color="Gray", dash="dash"))

st.plotly_chart(fig_scatter, width='stretch')

# 6. DETAILED DATA
with st.expander("查看详细数据表 (Detailed Data)"):
    st.dataframe(df.style.background_gradient(subset=['RMSE'], cmap="RdYlGn_r"))
