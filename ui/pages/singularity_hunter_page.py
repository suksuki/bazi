
"""
[SSEP] Singularity Hunter UI Page
View Layer for Singularity Hunter MVC.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ui.components.theme import GLASS_STYLE, apply_custom_header
from core.controllers.singularity_controller import SingularityController

def render():
    # Inject CSS Style Block
    st.markdown(f"""
        <style>
        .hunter-card {{
            {GLASS_STYLE}
            padding: 20px;
            margin-bottom: 20px;
        }}
        .stButton>button {{
            background: linear-gradient(90deg, #2d1b4e 0%, #1a0a2e 100%);
            border: 1px solid rgba(255, 215, 0, 0.5);
            color: #ffd700;
        }}
        </style>
    """, unsafe_allow_html=True)

    apply_custom_header("🌌 奇点狩猎者 (Singularity Hunter)", "QGA V17.1 实战协议 / [SSEP] 能量战地终端")
    
    # MVC Controller Initialization
    controller = SingularityController()
    
    # Layout Split: Central Panel vs Control Panel
    col_main, col_ctrl = st.columns([3, 1])
    
    with col_ctrl:
        st.markdown('<div class="hunter-card"><h3>📡 猎控台 (Hunter Console)</h3></div>', unsafe_allow_html=True)
        st.info("物理协议: [EVHZ] Event Horizon")
        
        if st.button("🛰️ 全息扫描 (Holographic Scan)", use_container_width=True):
            st.session_state.hunter_scan_res = controller.execute_global_scan()
            st.success("扫描完成: 锁定 3 处时空引力源")
        
        if st.button("🧬 演化扫描 (Evolutionary Scan)", use_container_width=True):
            with st.spinner("Injecting Virtual Luck Pillars..."):
                st.session_state.hunter_hidden_res = controller.execute_potential_scan()
                st.success("演化完成: 发现潜在超导者")
            
        # Prepare Options for Dropdown (Merge Real & Hidden)
        options = []
        id_map = {}
        
        if 'hunter_scan_res' in st.session_state and not st.session_state.hunter_scan_res.empty:
            df = st.session_state.hunter_scan_res
            options.extend(df['ID'].tolist())
            # create mapping ID -> Name
            for _, row in df.iterrows():
                # Try new key "姓名 (Name)", fallback to old "Name", then "ID"
                name_val = row.get('姓名 (Name)', row.get('Name', row['ID']))
                id_map[row['ID']] = name_val
                
        if 'hunter_hidden_res' in st.session_state and not st.session_state.hunter_hidden_res.empty:
            df_h = st.session_state.hunter_hidden_res
            # avoid duplicates
            new_ids = [i for i in df_h['ID'].tolist() if i not in id_map]
            options.extend(new_ids)
            for _, row in df_h.iterrows():
                name_val = row.get('姓名 (Name)', row.get('Name', row['ID']))
                id_map[row['ID']] = name_val

        selected_id = st.selectbox(
            "锁定目标 (Target Lock)", 
            options,
            format_func=lambda x: f"{id_map.get(x, x)}",
            index=0 if options else None
        )
        
        if selected_id:
            st.markdown("---")
            if st.button("🚀 视界穿透 (Penetrate Horizon)", type="primary", use_container_width=True):
                 with st.spinner("Injecting 10-Year Dynamic Stream..."):
                     res = controller.run_dynamic_injection(selected_id)
                     st.session_state.hunter_sim_res = res
                     st.success("穿透完成: 轨迹已捕捉")

    with col_main:
        # A. Radar / 3D Topology (Placeholder for Directive 1)
        st.markdown("### 🌌 奇点探测雷达 (Singularity Radar)")
        # Mock 3D visualization using Plotly
        # Here we visualize "Distance from Schwarzschild Radius"
        
        # If no data, show idle
        if 'hunter_sim_res' not in st.session_state:
             st.warning("⚠️ 探测器待命 (Standby). 等待全息扫描指令...")
             # Mock Idle Radar (Empty Polar)
             fig_radar = go.Figure(go.Scatterpolar(r=[0], theta=[0], mode='markers'))
             fig_radar.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
             st.plotly_chart(fig_radar, use_container_width=True)
        else:
             # B. Simulation Visualization
             sim_df = st.session_state.hunter_sim_res
             
             # Metric Lights (Directive 2)
             latest = sim_df.iloc[-1]
             m1, m2, m3 = st.columns(3)
             
             # Superconducting Light
             color_p = "blue" if latest['purity'] > 0.9 else "grey"
             m1.markdown(f"**超导纯度 (P)**: <span style='color:{color_p};font-size:1.2em'>●</span> {latest['purity']:.2f}", unsafe_allow_html=True)
             
             # Symmetry Light
             color_s = "green" if latest['symmetry'] > 0.9 else "grey"
             m2.markdown(f"**对 称 性 (S)**: <span style='color:{color_s};font-size:1.2em'>●</span> {latest['symmetry']:.2f}", unsafe_allow_html=True)
             
             # Turbulence Light (Red if near Horizon but not Stable)
             # Mass < 0.9 and > 0.7
             is_turbulent = 0.7 < latest['mass'] < 0.9
             color_t = "red" if is_turbulent else "grey"
             delta = "⚠️ TURBULENCE" if is_turbulent else "STABLE"
             m3.metric("视界状态", latest['state'], delta=delta, delta_color="inverse")

             # C. Real-time Parameters (Directive 3)
             st.markdown("#### 📈 动态流注入反馈 (Dynamic Injection Response)")
             fig_curve = px.line(sim_df, x="year", y=["mass", "purity"], markers=True, title="Mass(M) & Purity(P) Evolution")
             fig_curve.add_hline(y=0.9, line_dash="dash", line_color="red", annotation_text="Schwarzschild Radius")
             fig_curve.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
             st.plotly_chart(fig_curve, use_container_width=True)

        # D. Scan Grid
        # D. Scan Grid (Tabs)
        if 'hunter_scan_res' in st.session_state or 'hunter_hidden_res' in st.session_state:
            st.markdown("### 📋 猎物清单 (Prey Matrix)")
            tab1, tab2 = st.tabs(["🔴 显性奇点 (Singularities)", "🟡 隐性超导 (Hidden Potential)"])
            
            with tab1:
                if 'hunter_scan_res' in st.session_state:
                    st.dataframe(st.session_state.hunter_scan_res, use_container_width=True)
                else:
                    st.info("No Active Scan Data.")
            
            with tab2:
                if 'hunter_hidden_res' in st.session_state:
                    st.dataframe(st.session_state.hunter_hidden_res, use_container_width=True)
                    if not st.session_state.hunter_hidden_res.empty:
                        st.info("💡 提示: 这些样本在当前状态下平庸，但具备极高的觉醒潜力。")
                else:
                    st.info("Run Evolutionary Scan to find hidden gems.")

            # E. Documentation / Explanation
            st.markdown("""
            ---
            #### 📖 猎人战地手册 (Field Manual)
            
            **1. 物理状态 (Physics Status)**:
            *   **🔵 超导态 (Zero Resistance)**: 八字能量纯度极高 (Purity > 0.9)，无内耗，行事如入无人之境。
            *   **⚫ 奇点 (Singularity)**: 质量占比极大 (Mass > 0.9)，引力坍缩，能强行扭曲周围（人/事）服从其规则。
            *   **🔴 吸积盘 (Turbulence)**: 接近临界点，但杂质过多，处于高能湍流状态，易引发人生动荡。
            
            **2. 关键指标 (Metrics)**:
            *   **质量占比 (Mass Ratio)**: 命局中最强五行的能量占比。Mass > 0.9 为形成黑洞的阈值。
            *   **纯度 (Purity)**: [CEQS] 化气/顺势的完美程度。1.00 代表绝对的量子相干性。
            
            **3. 激活密钥 (Triggers)**:
            *   针对“隐性超导者”，这是开启其能量爆发的特定时间窗口（大运）。
            """)
