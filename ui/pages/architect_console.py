
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from core.flux import FluxEngine

def render_architect_console():
    st.set_page_config(page_title="Architect Console (God Mode)", page_icon="⚡", layout="wide")
    
    st.title("⚡ Architect Console (V5.3 God Mode)")
    st.caption("Quantum Bazi Core Engine Debugger & Tuner")

    # --- 0. Session Context Init ---
    if 'quantum_context' not in st.session_state:
        st.session_state.quantum_context = {
            "params": {
                "resonance_factor": 1.5,
                "entropy_penalty": 0.5,
                "enable_phase_locking": True,
                "enable_rooting": True,
                "apply_classic_rules": True
            },
            "sandbox_pillar": None
        }
    
    # Use a default chart for debugging if none selected in main session
    if 'current_chart' not in st.session_state:
        st.warning("No chart loaded from Dashboard. Using Test Case: [Ding Si / Yi Si / Yi Chou / Yi You]")
        st.session_state.current_chart = {
            "year": {"stem": "丁", "branch": "巳"},
            "month": {"stem": "乙", "branch": "巳"},
            "day": {"stem": "乙", "branch": "丑"},
            "hour": {"stem": "乙", "branch": "酉"}
        }
    
    chart = st.session_state.current_chart

    # ==========================================
    # PANEL 2: THE QUANTUM TUNER (Left Sidebar)
    # ==========================================
    with st.sidebar:
        st.header("🎛️ Quantum Tuner")
        st.markdown("---")
        
        ctx = st.session_state.quantum_context['params']
        
        # Sliders
        ctx['resonance_factor'] = st.slider("共振系数 (Resonance)", 1.0, 3.0, 1.5, 0.1, help="三合局能量放大倍数")
        ctx['entropy_penalty'] = st.slider("熵增惩罚 (Entropy Penalty)", 0.0, 1.0, 0.5, 0.1, help="冲战造成的能量损耗率")
        
        st.markdown("---")
        
        # Switches
        ctx['enable_phase_locking'] = st.toggle("启用相位锁定 (Phase Locking)", value=True)
        ctx['enable_rooting'] = st.toggle("启用通根矢量 (Vector Rooting)", value=True)
        ctx['apply_classic_rules'] = st.toggle("应用古籍修正 (L2 Heuristics)", value=True)
        
        st.success("Kernel Parameters Updated")

    # ==========================================
    # ENGINE PROCESSSING
    # ==========================================
    
    # Init Engine
    engine = FluxEngine(chart)
    
    # Inject Sandbox Pillar (Panel 3 Logic)
    sandbox_p = st.session_state.quantum_context['sandbox_pillar']
    if sandbox_p:
        # Hack: Inject into chart or engine dynamics
        # Since FluxEngine handles DaYun/LiuNian as extra particles, we can manually add them
        # engine.set_environment(...) 
        # For this demo, let's treat it as a LiuNian injection
        s = sandbox_p[0]
        b = sandbox_p[1]
        engine.set_environment(liu_nian={'stem':s, 'branch':b})

    # Inject Parameters
    engine.set_hyperparameters(ctx)
    
    # Run Compute
    result = engine.compute_energy_state()
    trace = result['trace']
    
    # ==========================================
    # PANEL 1: LAYERED LOGIC VISUALIZER (Main)
    # ==========================================
    
    col_viz, col_logs = st.columns([2, 1])
    
    with col_viz:
        st.subheader("🧬 逻辑分层透视 (Layered Logic Path)")
        st.caption("可视化能量从物理层 (L1) 到修正层 (L2) 的演化过程")
        
        # Sankey Diagram Data Prep
        # Nodes: Elements_L1 -> Elements_L2
        elements = ["Wood", "Fire", "Earth", "Metal", "Water"]
        
        # L1 Values
        l1_vals = [trace['l1_spectrum'][e] for e in elements]
        # L2 Values
        l2_vals = [trace['l2_spectrum'][e] for e in elements]
        
        # Colors (Standard Wuxing Colors)
        color_lookup = {
            "Wood": "#4CAF50", "Fire": "#F44336", "Earth": "#FFC107", 
            "Metal": "#9E9E9E", "Water": "#2196F3"
        }
        node_colors = [color_lookup[e] for e in elements] * 2
        
        # Build Link Data
        sources = []
        targets = []
        values = []
        link_colors = []
        
        for i, el in enumerate(elements):
            # Direct Flow (Same Element)
            sources.append(i)         # L1 Node
            targets.append(i + 5)     # L2 Node
            values.append(l1_vals[i]) # Flow Strength
            
            # Dynamic Link Color (Fade effect)
            opacity = 0.4 if l1_vals[i] > 0 else 0.1
            link_colors.append(color_lookup[el].replace(")", f", {opacity})").replace("rgb", "rgba"))

        fig = go.Figure(data=[go.Sankey(
            node = dict(
              pad = 15,
              thickness = 20,
              line = dict(color = "black", width = 0.5),
              label = [f"L1 {e}" for e in elements] + [f"L2 {e}" for e in elements],
              color = node_colors
            ),
            link = dict(
              source = sources,
              target = targets,
              value = values,
              color = link_colors
          ))])
        
        fig.update_layout(
            title_text=None, 
            font_size=12, 
            height=350,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, width="stretch")
        
    with col_logs:
        st.subheader("📜 仲裁日志 (Arbiter Logs)")
        st.caption("核心引擎的实时决策记录")
        with st.container(height=350, border=True):
            if not result['log']:
                st.info("System Normal. No special events.")
            
            for log in result['log']:
                if "THRESHOLD" in log:
                    st.error(log, icon="⚠️")
                elif "Learned" in log:
                    st.success(log, icon="📚")
                elif "ACTIVATED" in log:
                    st.warning(log, icon="⚡")
                elif "Suffocated" in log or "Buried" in log:
                    st.error(log, icon="☠️")
                else:
                    st.markdown(f"`{log}`")

    # ==========================================
    # PANEL 3: SIMULATION SANDBOX (Bottom)
    # ==========================================
    st.divider()
    st.subheader("🧪 沙盘推演 (Simulation Sandbox)")
    
    col_control, col_display = st.columns([1, 4])
    
    with col_control:
        st.markdown("##### 干扰变量投放")
        st.info("在此投放外部变量（如流年），观察系统在极端压力下的表现。")
        
        # Sim Options
        sim_options = {
            "None": None,
            "🔥 丙午 (烈火燎原)": ["丙", "午"],
            "🌊 壬子 (洪水滔天)": ["壬", "子"],
            "⚔️ 庚申 (刚金肃杀)": ["庚", "申"],
            "🌲 甲寅 (纯木仁寿)": ["甲", "寅"]
        }
        
        selected_key = st.selectbox("选择流年干支", list(sim_options.keys()))
        selected_val = sim_options[selected_key]
        
        if selected_val:
            st.session_state.quantum_context['sandbox_pillar'] = selected_val
            st.warning(f"⚠️ 模拟激活: {selected_val[0]}{selected_val[1]}")
        else:
            st.session_state.quantum_context['sandbox_pillar'] = None
            
    with col_display:
        st.markdown(f"##### 最终能量场状态 (Resonance: {ctx['resonance_factor']}x)")
        
        # Custom CSS for Progress Bars
        st.markdown("""
        <style>
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #4CAF50, #FFEB3B, #F44336);
        }
        </style>
        """, unsafe_allow_html=True)
        
        final_spec = result['spectrum']
        # Compute Delta if Sandbox is active
        # (Need base to compare? For now just show absolute)
        
        cols = st.columns(5)
        for i, el in enumerate(elements):
            with cols[i]:
                val = final_spec[el]
                is_crit = val > 150
                is_dead = val < 5
                
                # Dynamic Label
                label = f"{el}"
                if is_crit: label += " 🔥"
                if is_dead: label += " 💀"
                
                st.metric(label, f"{val:.1f}", delta=None) # TODO: Delta from Base
                
                # Color-coded progress
                bar_color = color_lookup[el]
                st.progress(min(val / 300, 1.0))
                
                if is_crit:
                     st.caption(":red[**CRITICAL**]")
                elif is_dead:
                     st.caption(":grey[*Suppressed*]")

if __name__ == "__main__":
    render_architect_console()
