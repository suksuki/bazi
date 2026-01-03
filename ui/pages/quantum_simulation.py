
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
import os
import json
from datetime import datetime

# Services & Core
from services.simulation_service import SimulationService
from core.bazi_profile import BaziProfile, VirtualBaziProfile
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.translation_util import T

# Data
# [Correction 3]: Fixing import path for GEO_CITY_MAP
from core.data.geo_cities import GEO_CITY_MAP

# UI Components
from ui.components.theme import COLORS, GLASS_STYLE, apply_custom_header, sidebar_header
# [Correction 1 & 2]: Importing the extracted report renderers
import ui.components.simulation_reports as reports

def render():
    # --- 样式注入 ---
    # Global styles from assets/style.css already handled background and basic geometry.
    st.markdown(f"""
    <style>
    .metric-card {{
        background: rgba(45, 27, 78, 0.3);
        border: 1px solid rgba(64, 224, 208, 0.2);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        transition: all 0.3s;
    }}
    .metric-card:hover {{
        border-color: #40e0d0;
        box-shadow: 0 0 15px rgba(64, 224, 208, 0.2);
    }}
    </style>
    """, unsafe_allow_html=True)

    # --- 标题 ---
    apply_custom_header("🔮 量子仿真中心 (ASE SIMULATION CENTER)", "Antigravity-ASE | 全样本命运普查系统")

    # --- 初始化控制器 ---
    if 'sim_controller' not in st.session_state or getattr(st.session_state.sim_controller, 'version', '0') != "15.6.0":
        # Clear legacy data on version bump
        if "scouted_charts" in st.session_state: del st.session_state.scouted_charts
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        st.session_state.sim_controller = SimulationService(project_root)
        # Ensure the version is set for the new service instance
        st.session_state.sim_controller.version = "15.6.0"
    
    controller = st.session_state.sim_controller

    # --- 初始化 View State ---
    if "sim_view" not in st.session_state:
        st.session_state.sim_view = "dashboard"

    # --- [QGA V16.0] 动态物理模型注册表 (Layer-Based Discovery) ---
    # 仅展示 L3: TOPIC 层的业务专题
    # [已删除知识库系统] 使用硬编码的主题列表
    TRACK_ICONS = {}
    TRACK_NAMES = {}
    TRACK_IDS = []

    # --- 侧边栏：核心控制 ---
    with st.sidebar:
        sidebar_header("🧬 系统导航", "🧬")
        if st.button("📊 核心看板", use_container_width=True):
            st.session_state.sim_view = "dashboard"
            st.rerun()
            
        if st.button("🏛️ 大一统对撞审计", use_container_width=True):
            st.session_state.sim_view = "grand_audit"
            st.rerun()
            
        if st.button("🛠️ 命运重塑实验", use_container_width=True):
            st.session_state.sim_view = "intervention"
            st.rerun()
 
        if st.button("⛩️ 真实档案实弹审计", use_container_width=True):
            st.session_state.sim_view = "real_world_audit"
            st.rerun()
 
        st.divider()
        sidebar_header("📑 物理模型仿真", "📑")
        
        def format_track(track_id: str) -> str:
            icon = TRACK_ICONS.get(track_id, "🧬")
            # [V16.0] 直接使用注册的中文名，Sparkle 已在 Manifest 中附带
            name = TRACK_NAMES.get(track_id, track_id)
            return f"{icon} {name}"
        
        selected_track = st.selectbox("选择对撞轨道", TRACK_IDS, format_func=format_track)
        
        # --- [QGA V4.3.5] 上下文相关的深度审计按钮 ---
        # Note: These buttons modify 'sim_op_type' and 'sim_active' which are handled inside components now, 
        # or triggered by buttons inside the reports.
        # However, the logic here was simply to *activate* the view.
        # But wait, the original code had buttons here that set state and reran.
        # The new component functions handle the "Start" buttons themselves if data is missing.
        # So we just need to route to the correct view.
        
        st.session_state.target_track = selected_track
        
        # Mapping track to view
        # We'll use a specific view for each special track, or a generic one.
        
        if st.button("🔬 进入专题实验室", use_container_width=True, type="primary"):
             st.session_state.sim_view = "topic_lab"
             st.rerun()
             
        st.divider()
        st.caption(f"Kernel: QGA-V16.4 | Engine: {controller.version}")

    # --- 主视图路由 ---
    view = st.session_state.sim_view
    
    # Check for active simulation tasks triggered from components
    if st.session_state.get("sim_active", False):
        op_type = st.session_state.sim_op_type
        
        with st.status(f"🚀 正在执行物理对撞任务: {op_type}...", expanded=True) as status:
            t_start = time.time()
            st.write("✨ 初始化量子场 (Quantum Field Init)...")
            time.sleep(0.5)
            
            # --- 任务分发 ---
            if op_type == "phase_8_grand":
                st.write("🌌 加载 518,400 样本全息矩阵...")
                res = controller.run_grand_unified_audit()
                st.session_state.grand_res = res
                st.write("✅ 审计完成，相图生成中...")
                
            elif op_type in ["v43_live_fire_audit", "v43_penetration_audit", "v435_yangren_audit", 
                             "v435_thermo_audit", "v435_inertia_audit", "v435_tunnel_audit",
                             "universal_topic_audit", "v44_resonance_audit", 
                             "v44_transition_audit", "v44_reversion_audit",
                             "v45_gxyg_audit", "v45_mbgs_audit", "v45_zhsg_audit"]:
                             
                # Generic pattern mapping to controller method
                method_global_map = {
                    "v43_live_fire_audit": "run_live_fire_whitepaper",
                    "v43_penetration_audit": "run_v43_defense_penetration",
                    "v435_yangren_audit": "run_v435_yangren_monopole",
                    "v435_thermo_audit": "run_v435_thermo_calibration",
                    "v435_inertia_audit": "run_v435_inertia_calibration",
                    "v435_tunnel_audit": "run_v435_tunnel_calibration",
                    "universal_topic_audit": "run_universal_topic_audit",
                    "v44_resonance_audit": "run_v44_resonance_calibration",
                    "v44_transition_audit": "run_v44_transition_calibration",
                    "v44_reversion_audit": "run_v44_reversion_calibration",
                    "v45_gxyg_audit": "run_v45_gxyg_audit",
                    "v45_mbgs_audit": "run_v45_mbgs_audit",
                    "v45_zhsg_audit": "run_v45_zhsg_audit"
                }
                
                method_name = method_global_map.get(op_type)
                if method_name:
                    st.write(f"📡 启动 {op_type} 核心算法...")
                    # Special handling for universal audit which needs an arg
                    if op_type == "universal_topic_audit":
                         res = getattr(controller, method_name)(st.session_state.get("target_track"))
                         st.session_state.universal_audit_res = res
                    else:
                         res = getattr(controller, method_name)()
                         # Mapping result to session state key
                         key_map = {
                             "v43_live_fire_audit": "live_fire_res",
                             "v43_penetration_audit": "v43_pen_res",
                             "v435_yangren_audit": "v435_yr_res",
                             "v435_thermo_audit": "v435_th_res",
                             "v435_inertia_audit": "v435_in_res",
                             "v435_tunnel_audit": "v435_tu_res",
                             "v44_resonance_audit": "v44_re_res",
                             "v44_transition_audit": "v44_tr_res",
                             "v44_reversion_audit": "v44_rv_res",
                             "v45_gxyg_audit": "v45_gp_res",
                             "v45_mbgs_audit": "v45_mb_res",
                             "v45_zhsg_audit": "v45_zh_res"
                         }
                         if key_map.get(op_type):
                             st.session_state[key_map[op_type]] = res

            elif op_type == "phase_9_intervention":
                st.write("💉 注入五行干预场...")
                params = st.session_state.inter_params
                res = controller.run_intervention_experiment(
                    st.session_state.inter_bazi,
                    st.session_state.inter_luck,
                    st.session_state.inter_annual,
                    params["geo_shift"],
                    params["damping_reduction"]
                )
                st.session_state.inter_res = res
                
            time.sleep(0.5)
            status.update(label="✅ 物理仿真完成!", state="complete", expanded=False)
            
        st.session_state.sim_active = False
        st.rerun()

    # --- View Rendering ---
    
    if view == "dashboard":
        # Dashboard Overview
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("### 🧬 核心控制台 (Main Console)")
            st.info("欢迎访问 QGA 量子仿真中心。请从左侧选择对撞轨道或专项审计功能。")
            
            # Show latest status if available
            latest = {"singularities": []} # Mock for now or retrieve from controller
            reports.render_phase_radar(latest)

        with col2:
            st.markdown("### 📜 实时日志")
            st.code("System Ready.\nEngine V15.6.0 Loaded.\nMatrix: 518,400 x 64", language="bash")

    elif view == "grand_audit":
        reports.render_grand_audit()
        st.divider()
        reports.render_live_fire_whitepaper()
        st.divider()
        reports.render_v43_penetration_report()

    elif view == "intervention":
        reports.render_intervention_lab()
        
    elif view == "real_world_audit":
        reports.render_real_world_audit(controller)
        
    elif view == "topic_lab":
        # Determine which report to show based on selected track
        track = st.session_state.get("target_track", "")
        
        # Universal header
        reports.render_crystal_notification(f"正在访问专题: {track}", "info")
        
        # Special logic for specific tracks to show their specialized reports
        if track == "MOD_121_YGZJ_MONOPOLE":
            reports.render_v435_yangren_report()
            
        elif track == "MOD_122_YHGS_THERMO":
             reports.render_v435_thermo_report()
             
        elif track == "MOD_123_LYKG_INERTIA":
             reports.render_v435_inertia_report()
             
        elif track == "MOD_124_JJGG_TUNNEL":
             reports.render_v435_tunnel_report()
        
        elif track == "MOD_125_TYKG_RESONANCE":
             reports.render_v44_resonance_report()
             
        elif track == "MOD_126_CWJS_TRANSITION":
            reports.render_v44_transition_report()
            
        elif track == "MOD_127_MHGG_REVERSION":
            reports.render_v44_reversion_report()
            
        elif track == "MOD_128_GXYG_GAP":
            reports.render_v45_gxyg_report()
            
        elif track == "MOD_129_MBGS_PENETRATION":
            reports.render_v45_mbgs_report()
            
        elif track == "MOD_130_ZHSG_EXCITATION":
            reports.render_v45_zhsg_report()
            
        else:
            # Default Universal Report for other tracks
             reports.render_universal_audit_report(track)
        
        # Also show the generic topic lab report at the bottom for any track
        st.divider()
        reports.render_topic_lab_report(controller)
        
        # And the full pipeline scan
        st.divider()
        if st.checkbox("Show Legacy Full Pipeline Scan Tool"):
            reports.render_full_pipeline_scan()

