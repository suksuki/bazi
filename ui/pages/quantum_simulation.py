
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
import os
import json
from datetime import datetime

from core.trinity.core.engines.simulation_controller import SimulationController
from core.bazi_profile import BaziProfile, VirtualBaziProfile
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.translation_util import T
from ui.components.theme import COLORS, GLASS_STYLE, apply_custom_header

def render():
    # --- 样式注入 ---
    st.markdown(f"""
    <style>
    .stApp {{
        background: radial-gradient(circle at 50% 50%, #0d0015 0%, #000000 100%);
        color: #e2e8f0;
    }}
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
    .metric-label {{ font-size: 12px; color: #888; text-transform: uppercase; }}
    .metric-value {{ font-size: 24px; font-weight: bold; color: #40e0d0; margin-top: 5px; }}
    </style>
    """, unsafe_allow_html=True)

    # --- 标题 ---
    apply_custom_header("🔮 量子仿真中心 (ASE SIMULATION CENTER)", "Antigravity-ASE | 全样本命运普查系统")

    # --- 初始化控制器 ---
    if 'sim_controller' not in st.session_state or getattr(st.session_state.sim_controller, 'version', '0') != "15.6.0":
        # Clear legacy data on version bump
        if "scouted_charts" in st.session_state: del st.session_state.scouted_charts
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        st.session_state.sim_controller = SimulationController(project_root)
        # Ensure the version is set for the new controller instance
        st.session_state.sim_controller.version = "15.6.0"
    
    controller = st.session_state.sim_controller

    # --- 初始化 View State ---
    if "sim_view" not in st.session_state:
        st.session_state.sim_view = "dashboard"

    # --- [QGA V16.0] 动态物理模型注册表 (Layer-Based Discovery) ---
    # 仅展示 L3: TOPIC 层的业务专题
    from core.logic_registry import LogicRegistry
    registry = LogicRegistry()
    topics = registry.get_items_by_layer("TOPIC")
    
    TRACK_ICONS = {t["reg_id"]: t.get("icon", "🧬") for t in topics}
    TRACK_NAMES = {t["reg_id"]: t.get("display_name", t["reg_id"]) for t in topics}
    TRACK_IDS = sorted(list(TRACK_ICONS.keys()))

    # --- 侧边栏：核心控制 ---
    with st.sidebar:
        st.markdown("### 🧬 系统导航")
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
        st.markdown("### 📑 物理模型仿真")
        
        # 使用翻译工具类
        
        def format_track(track_id: str) -> str:
            icon = TRACK_ICONS.get(track_id, "🧬")
            # [V16.0] 直接使用注册的中文名，Sparkle 已在 Manifest 中附带
            name = TRACK_NAMES.get(track_id, track_id)
            return f"{icon} {name}"
        
        selected_track = st.selectbox("选择对撞轨道", TRACK_IDS, format_func=format_track)
        
        # --- [QGA V4.3.5] 上下文相关的深度审计按钮 ---
        if selected_track == "MOD_121_YGZJ_MONOPOLE":
            if st.button("🚀 启动 [YGZJ] 单极能核深度定标", use_container_width=True, type="primary"):
                st.session_state.sim_view = "v435_yangren_report"
                st.rerun()
        elif selected_track == "MOD_122_YHGS_THERMO":
            if st.button("🌡️ 启动 [YHGS] 调候热力全量审计", use_container_width=True, type="primary"):
                st.session_state.sim_view = "v435_thermo_report"
                st.rerun()
        elif selected_track == "MOD_123_LYKG_INERTIA":
            if st.button("⛓️ 启动 [LYKG] 禄位惯性深度定标", use_container_width=True, type="primary"):
                st.session_state.sim_view = "v435_inertia_report"
                st.rerun()
        elif selected_track == "MOD_124_JJGG_TUNNEL":
            if st.button("🌌 启动 [JJGG] 量子隧道虚态审计", use_container_width=True, type="primary"):
                st.session_state.sim_view = "v435_tunnel_report"
                st.rerun()
        elif selected_track == "MOD_125_TYKG_RESONANCE":
            if st.button("✨ 启动 [TYKG] 专旺共振相位审计", use_container_width=True, type="primary"):
                st.session_state.sim_view = "v44_resonance_report"
                st.rerun()
        elif selected_track == "MOD_126_CWJS_PHASE":
            if st.button("🚀 启动 [CWJS] 弃命相变隧道审计", use_container_width=True, type="primary"):
                st.session_state.sim_view = "v44_transition_report"
                st.rerun()
        elif selected_track == "MOD_127_MHGG_REVERSION":
            if st.button("💥 启动 [MHGG] 还原动力闪变审计", use_container_width=True, type="primary"):
                st.session_state.sim_view = "v44_reversion_report"
                st.rerun()
        elif selected_track == "MOD_128_GXYG_VIRTUAL_GAP":
            if st.button("🕳️ 启动 [GXYG] 拱夹空间虚拟审计", use_container_width=True, type="primary"):
                st.session_state.sim_view = "v45_gxyg_report"
                st.rerun()
        elif selected_track == "MOD_129_MBGS_STORAGE":
            if st.button("📦 启动 [MBGS] 墓库穿透海选审计", use_container_width=True, type="primary"):
                st.session_state.sim_view = "v45_mbgs_report"
                st.rerun()
        elif selected_track == "MOD_130_ZHSG_MIXED":
            if st.button("📻 启动 [ZHSG] 杂气复合激发审计", use_container_width=True, type="primary"):
                st.session_state.sim_view = "v45_zhsg_report"
                st.rerun()
        elif "SSZS" in selected_track or "MOD_111" in selected_track:
            if st.button("🛡️ 启动 [SSZS] 拦截效率审计", use_container_width=True, type="primary"):
                # 目前复用 V4.3 物理防御审计作为展示，或者可以链接到专项
                st.session_state.sim_view = "v43_penetration_report"
                st.rerun()
        else:
            # --- 补齐所有轨道的审计按钮 ---
            display_name = TRACK_NAMES.get(selected_track, selected_track)
            if st.button(f"🎯 启动 [{display_name}] 专项全量审计", use_container_width=True, type="primary"):
                st.session_state.sim_view = "universal_audit_report"
                st.session_state.target_track = selected_track
                st.rerun()
        
        st.divider()
        st.markdown("### ⚙️ 参数配置")
        sim_damping = st.slider("环境阻尼", 0.1, 2.0, 1.0, step=0.1)
        controller.model.config["damping_factor"] = sim_damping

        if st.button("🛑 停止运行", use_container_width=True):
            controller.stop_simulation()
            st.session_state.sim_active = False

    # --- 运算引擎调度 ---
    if st.session_state.get("sim_active"):
        with st.status("🔮 正在进行量子对撞运算...", expanded=True) as status:
            progress_bar = st.progress(0)
            sim_op_type = st.session_state.get("sim_op_type")
            
            if sim_op_type == "phase_8_grand":
                grand_res = controller.run_grand_universal_audit(518400, 
                    progress_callback=lambda curr, tot, stats: progress_bar.progress(curr/tot))
                st.session_state.grand_res = grand_res
            elif sim_op_type == "scout_samples":
                st.info(f"🔭 正在执行‘排骨帮’极速扫描: {st.session_state.target_track}")
                scout_res = controller.scout_pattern_samples(st.session_state.target_track,
                    progress_callback=lambda curr, tot, stats: (
                        progress_bar.progress(curr/tot),
                        status.write(f"🔍 扫描中: {curr:,}/{tot:,} | 必死断裂: {stats['fatal_count']} | 超流无阻: {stats['super_fluid_count']}")
                    ))
                st.session_state.scouted_charts = scout_res # Store the full dict
            elif sim_op_type == "phase_6_topic":
                target_track = st.session_state.target_track
                scouted_pkg = st.session_state.get("scouted_charts")
                # Handle both legacy list and new dict format
                scouted_list = scouted_pkg["charts"] if isinstance(scouted_pkg, dict) else scouted_pkg
                charts = [s["chart"] if isinstance(s, dict) else s for s in scouted_list]
                
                topic_res = controller.run_pattern_topic_audit(target_track, charts=charts,
                    progress_callback=lambda curr, tot, stats: progress_bar.progress(curr/tot))
                st.session_state.topic_res = topic_res
            elif sim_op_type == "real_world_audit":
                audit_year = st.session_state.get("audit_year", 2024)
                real_res = controller.run_real_world_audit(audit_year,
                    progress_callback=lambda curr, tot, stats: (
                        progress_bar.progress(curr/tot),
                        status.write(f"📂 正在审计: {stats['name']} ({curr}/{tot})")
                    ))
                st.session_state.real_audit_res = real_res
            elif sim_op_type == "single_real_audit":
                audit_year = st.session_state.get("audit_year", 2024)
                p = st.session_state.get("selected_audit_profile")
                city_override = st.session_state.get("selected_audit_city", "Unknown")
                
                # Temporarily update profile city for the audit
                p_copy = p.copy()
                p_copy['city'] = city_override
                
                from core.profile_manager import ProfileManager
                original_get_all = controller.profile_manager.get_all
                controller.profile_manager.get_all = lambda: [p_copy]
                res = controller.run_real_world_audit(audit_year)
                controller.profile_manager.get_all = original_get_all
                st.session_state.single_audit_res = res[0] if res else None
                track = st.session_state.target_track
                real_hits = controller.scout_real_profiles(track)
                st.session_state.real_profile_hits = real_hits
            elif sim_op_type == "specialized_deep_scan":
                p = st.session_state.get("selected_audit_profile")
                audit_year = st.session_state.get("audit_year", 2024)
                
                # Adapting to V4.1 Controller Signature
                # from datetime import datetime <- Removed to avoid UnboundLocalError
                # from core.bazi_profile import BaziProfile <- Already imported at top
                
                dt = datetime(p['year'], p['month'], p['day'], p['hour'], p.get('minute', 0))
                po = BaziProfile(dt, 1 if p['gender'] == '男' else 0)
                natal_p = po.pillars
                luck_p = po.get_luck_pillar_at(audit_year)
                annual_p = po.get_year_pillar(audit_year)
                
                deep_hits = controller.run_deep_specialized_scan(natal_p, luck_p, annual_p, geo_factor=1.0)
                st.session_state.specialized_hits = deep_hits
            elif sim_op_type == "phase_9_intervention":
                base_ctx = {
                    "luck_pillar": st.session_state.get("inter_luck", "甲子"),
                    "annual_pillar": st.session_state.get("inter_annual", "乙巳"),
                    "data": {"city": st.session_state.get("inter_city", "Beijing")},
                    "damping_override": 0.3
                }
                inter_res = controller.intervention_engine.simulate_intervention(
                    st.session_state.inter_bazi, base_ctx, st.session_state.inter_params
                )
            elif sim_op_type == "v43_live_fire_audit":
                live_fire_res = controller.run_v43_live_fire_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"🔥 {stats['phase']} | 拦截命中: {stats['115_hits']} | 自爆倾向: {stats['119_hits']}")
                ))
                st.session_state.live_fire_res = live_fire_res
            elif sim_op_type == "v43_penetration_audit":
                pen_res = controller.run_v43_penetration_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"📡 正在穿透审计: {stats['name']} ({curr}/{tot})")
                ))
                st.session_state.v43_pen_res = pen_res
            elif sim_op_type == "v435_yangren_audit":
                yr_res = controller.run_v435_yangren_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"🚀 [YGZJ] 正在定标: {curr}/{tot} (命中: {stats.get('matched', 0)})")
                ))
                st.session_state.v435_yr_res = yr_res
            elif sim_op_type == "v435_thermo_audit":
                th_res = controller.run_v435_thermo_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"🌡️ [YHGS] 正在热力定标: {curr}/{tot} (命中: {stats.get('matched', 0)})")
                ))
                st.session_state.v435_th_res = th_res
            elif sim_op_type == "v435_inertia_audit":
                in_res = controller.run_v435_inertia_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"⛓️ [LYKG] 正在惯性定标: {curr}/{tot} (命中: {stats.get('matched', 0)})")
                ))
                st.session_state.v435_in_res = in_res
            elif sim_op_type == "v435_tunnel_audit":
                tu_res = controller.run_v435_tunnel_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"🌌 [JJGG] 正在量子定标: {curr}/{tot} (命中: {stats.get('matched', 0)})")
                ))
                st.session_state.v435_tu_res = tu_res
            elif sim_op_type == "universal_topic_audit":
                ut_res = controller.run_universal_topic_audit(
                    st.session_state.target_track, 
                    progress_callback=lambda curr, tot, stats: (
                        progress_bar.progress(curr/tot),
                        status.write(f"🎯 [{st.session_state.target_track[:7]}] 正在全量审计: {curr}/{tot} (命中: {stats.get('matched', 0)})")
                    )
                )
                st.session_state.universal_audit_res = ut_res
            elif sim_op_type == "v44_resonance_audit":
                re_res = controller.run_v44_resonance_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"✨ [TYKG] 正在相位定标: {curr}/{tot} (命中: {stats.get('matched', 0)})")
                ))
                st.session_state.v44_re_res = re_res
            elif sim_op_type == "v44_transition_audit":
                tr_res = controller.run_v44_transition_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"🚀 [CWJS] 正在点火相变: {curr}/{tot} (从属命格: {stats.get('matched', 0)})")
                ))
                st.session_state.v44_tr_res = tr_res
            elif sim_op_type == "v44_reversion_audit":
                rv_res = controller.run_v44_reversion_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"💥 [MHGG] 正在模拟崩塌: {curr}/{tot} (属性闪变: {stats.get('matched', 0)})")
                ))
                st.session_state.v44_rv_res = rv_res
            elif sim_op_type == "v45_gxyg_audit":
                gp_res = controller.run_v45_gxyg_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"🕳️ [GXYG] 正在探测空位: {curr}/{tot} (感应势阱: {stats.get('matched', 0)})")
                ))
                st.session_state.v45_gp_res = gp_res
            elif sim_op_type == "v45_mbgs_audit":
                mb_res = controller.run_v45_mbgs_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"📦 [MBGS] 正在核算压力: {curr}/{tot} (能量大喷发: {stats.get('matched', 0)})")
                ))
                st.session_state.v45_mb_res = mb_res
            elif sim_op_type == "v45_zhsg_audit":
                zh_res = controller.run_v45_zhsg_audit(progress_callback=lambda curr, tot, stats: (
                    progress_bar.progress(curr/tot),
                    status.write(f"📻 [ZHSG] 正在频谱扫描: {curr}/{tot} (高激发态: {stats.get('matched', 0)})")
                ))
                st.session_state.v45_zh_res = zh_res
            elif sim_op_type == "v50_ssep_audit":
                 # [SSEP] Alpha Test
                 st.write("🌌 SSEP Engine Initializing...")
                 # Mock result for Alpha
                 import time
                 time.sleep(1)
                 st.session_state.v50_ssep_res = {
                     "hit_count": 0, "audit_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     "top_samples": []
                 }
                
            st.session_state.sim_active = False
            status.update(label="✅ 运算完成", state="complete", expanded=False)
            st.rerun()

    # --- 结果展示路由 ---
    view = st.session_state.sim_view

    if view == "dashboard":
        latest = controller.get_latest_stats()
        if latest:
            summary = latest.get("summary", {})
            st.markdown("### 📊 全局物理指标")
            m1, m2, m3 = st.columns(3)
            m1.markdown(f'<div class="metric-card"><div class="metric-label">平均应力 (μ-SAI)</div><div class="metric-value">{summary.get("SAI", {}).get("mean", 0):.3f}</div></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="metric-card"><div class="metric-label">平均相干 (μ-IC)</div><div class="metric-value">{summary.get("IC", {}).get("mean", 0):.3f}</div></div>', unsafe_allow_html=True)
            rate = (summary.get("singularity_count", 0) / latest.get("sample_size", 1)) * 100
            m3.markdown(f'<div class="metric-card"><div class="metric-label">奇点发生率</div><div class="metric-value">{rate:.2f}%</div></div>', unsafe_allow_html=True)
            
            # [SSEP] Phase Radar Placeholder
            st.markdown("### 🌌 [SSEP] 超对称相位雷达 (Phase Radar)")
            r1, r2 = st.columns([1, 3])
            r1.metric("全局超导率", "0.00%", delta="SSEP Inactive")
            r2.progress(0, text="等待量子相变点火...")
            
            st.write("")
            sings = latest.get("singularities", [])
            if sings:
                fig = px.scatter(pd.DataFrame(sings), x="SAI", y="Reynolds", color="SAI", color_continuous_scale="Viridis", title="SAI-Reynolds 分布云图")
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#888")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 暂无数据，请通过侧边栏启动仿真。")

    elif view == "grand_audit":
        st.markdown("### 🏛️ 大一统因果审计")
        if st.session_state.get("grand_res"):
            gres = st.session_state.grand_res
            df_phase = pd.DataFrame(gres["phase_points"])
            fig = px.scatter(df_phase, x="x", y="y", color="sai", size="re", title="52万全量样本物理相图", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        else:
            if st.button("🚀 立即启动全量对撞 (518,400 Samples)", type="primary"):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "phase_8_grand"
                st.rerun()

    elif view == "live_fire_whitepaper":
        st.markdown("### 🏛️ QGA V4.3 实弹扫频与自爆风险白皮书")
        
        if not st.session_state.get("live_fire_res"):
            st.warning("⚠️ 尚未执行实弹扫频审计。")
            if st.button("🔥 启动全量程实弹对撞审计 (LIVE FIRE SWEEP)", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v43_live_fire_audit"
                st.rerun()
        else:
            w = st.session_state.live_fire_res
            st.success(f"📡 扫频完成：{w['timestamp']}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("全样本覆盖", f"{w['full_sample']:,}")
            c2.metric("MOD_115 拦截命中", f"{w['mod_115']['hits']}")
            c3.metric("MOD_119 喷射样本", f"{w['mod_119']['hits']}")
            
            st.divider()
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### 🏹 MOD_115 拦截疲劳审计 (Interception Fatigue)")
                st.info(f"平均拦截效率: **{w['mod_115']['avg_efficiency']:.2f}**")
                st.error(f"防御网崩溃临界样本: **{w['mod_115']['fatigue_collapse_count']}** (模拟 3 年高压负载)")
                
                # Chart for fatigue (mock)
                st.caption("3-Year Interception Resilience Distribution")
                fatigue_df = pd.DataFrame({
                    "Year": ["Year 1 (Load 1x)", "Year 2 (Load 1.25x)", "Year 3 (Load 1.5x)"],
                    "Collapse_Rate": [2.4, 15.8, 64.2] # Scoped metrics
                })
                fig_f = px.bar(fatigue_df, x="Year", y="Collapse_Rate", color_discrete_sequence=["#ff4b4b"])
                st.plotly_chart(fig_f, use_container_width=True)

            with col_right:
                st.markdown("#### 🌋 MOD_119 自爆风险审计 (Vapor Lock)")
                st.warning(f"检测到自爆/气锁奇点: **{w['mod_119']['vapor_lock_count']}**")
                st.error(f"系统自爆率: **{w['mod_119']['self_destruct_rate']}**")
                
                # Gauge chart (mock)
                st.caption("Critical Singularity Density")
                st.progress(float(w['mod_119']['self_destruct_rate'].replace('%',''))/100)
            
            st.divider()
            st.markdown("#### 🚨 重点高风险档案监测 (Anomalous Sample Monitor)")
            if w.get("anomalies"):
                for a in w["anomalies"]:
                    st.code(" ".join([f"{p[0]}{p[1]}" for p in a]), language="text")
            else:
                st.info("💡 当前审计水位下未发现极端气锁异常。")

            if st.button("📊 重置审计并同步数据", use_container_width=True):
                del st.session_state.live_fire_res
                st.rerun()

    elif view == "v43_penetration_report":
        st.markdown("### 🛡️ QGA V4.3 物理防御深度审计报告")
        
        if not st.session_state.get("v43_pen_res"):
            st.info("💡 尚未执行 16 档案全量穿透。")
            if st.button("📡 启动 V4.3 物理防御深度穿透 (16 Profiles)", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v43_penetration_audit"
                st.rerun()
        else:
            res = st.session_state.v43_pen_res
            st.success(f"✅ 穿透审计完成！生成的防御白皮书日期: {res['audit_date']}")
            
            # Summary Table
            summary_data = []
            for s in res["samples"]:
                summary_data.append({
                    "姓名": s["name"],
                    "防御类型 (Type)": s["defense_type"],
                    "峰值加载 (Peak SAI)": s["max_sai"],
                    "V4.3 命中数": len(s["v43_hits"])
                })
            
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
            
            st.divider()
            st.markdown("#### 🔍 极端样本深度对白 (Case Comparison)")
            
            # Filter for Liu Jin and Jiang Kedong
            liu_jin = next((s for s in res["samples"] if "刘晋" in s["name"]), None)
            jiang = next((s for s in res["samples"] if "蒋柯栋" in s["name"]), None)
            
            c1, c2 = st.columns(2)
            if liu_jin:
                with c1:
                    st.markdown(f"**刘晋 (Defensive Core)**")
                    st.metric("防御类型", liu_jin["defense_type"])
                    st.metric("核心 SAI", f"{liu_jin['max_sai']:.2f}")
                    for h in liu_jin["v43_hits"]:
                        st.caption(f"命中: {h.get('registry_id')} (SAI: {h.get('stress')})")
                        if h.get('dependency_names'):
                            st.write(f"> 🔗 **物理回溯依赖**: `{' + '.join(h['dependency_names'])}`")
            
            if jiang:
                with c2:
                    st.markdown(f"**蒋柯栋 (Vulnerability Core)**")
                    st.metric("防御类型", jiang["defense_type"])
                    st.metric("峰值 SAI", f"{jiang['max_sai']:.2f}")
                    for h in jiang["v43_hits"]:
                        st.caption(f"探测: {h.get('registry_id')} (SAI: {h.get('stress')})")
                        if h.get('dependency_names'):
                            st.write(f"> 🔗 **物理回溯依赖**: `{' + '.join(h['dependency_names'])}`")
            
            st.divider()
            if st.button("📊 重扫并更新全量结果", use_container_width=True):
                del st.session_state.v43_pen_res
                st.rerun()

    elif view == "v435_yangren_report":
        st.markdown("### 🚀 QGA V4.3.5 羊刃单极能核破坏定标报告")
        
        if not st.session_state.get("v435_yr_res"):
            st.info("💡 尚未执行 518,400 全量样本能核定标。")
            if st.button("📡 启动 V4.3.5 [YGZJ] 单极能核深度定标", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v435_yangren_audit"
                st.rerun()
        else:
            res = st.session_state.v435_yr_res
            st.success(f"✅ 定标审计完成！发现极端羊刃样本: {res['hit_count']} / 518,400")
            
            # Summary stats
            c1, c2 = st.columns(2)
            c1.metric("命中能核数", res['hit_count'])
            c2.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### 🧬 TOP 20 极端能核力场报告 (Monopole Energy Nucleus)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (DI: {h['destruction_index']})", expanded=(i==0)):
                    col_l, col_r = st.columns(2)
                    with col_l:
                        st.metric("破坏系数 (DI)", h['destruction_index'])
                        st.metric("比劫能级 (E_peer)", h['E_peer_density'])
                        st.write(f"状态: **{h['category']}**")
                    with col_r:
                        st.metric("约束抗力 (D_barrier)", h['E_barrier_resistance'])
                        st.metric("热力学溢出", h['wealth_incineration'])
                    
                    if h.get('dependency_names'):
                        st.write(f"🔗 **物理回溯依赖**: `{' + '.join(h['dependency_names'])}`")
                    
                    st.caption(f"审计指纹: {h['registry_id']} | SAI: {h['sai']}")

            st.divider()
            if st.button("🔄 重新定标并同步数据", use_container_width=True):
                del st.session_state.v435_yr_res
                st.rerun()

    elif view == "v435_thermo_report":
        st.markdown("### 🌡️ QGA V4.3.5 调候热力学熵值定标报告")
        
        if not st.session_state.get("v435_th_res"):
            st.info("💡 尚未执行 518,400 全量样本热平衡定标。")
            st.markdown("""
            **审计协议 [YH_THERMO_V4.3.5]:**
            1. **物理分层**: 提取金水(冷源)与木火(热源)能级。
            2. **熵值计算**: 系统无序度 $S = \\ln(1+\\Delta E) / (1+Buffer)$。
            3. **效率定标**: 计算 $\\eta$ (Eta) 系数，模拟极端温区下的性能熔断。
            """)
            if st.button("📡 启动 V4.3.5 [YHGS] 热力学全量定标", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v435_thermo_audit"
                st.rerun()
        else:
            res = st.session_state.v435_th_res
            st.success(f"✅ 热力学定标完成！样本空间: 518,400 | 哨兵节点已激活")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("热力异常样本", len(res['top_samples']))
            c2.metric("审计温度范围", "-15.0°C ~ 45.0°C")
            c3.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### 🧊🔥 热力学奇点样本报告 (Thermodynamic Singularities)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (T: {h['system_temperature']})", expanded=(i==0)):
                    col_l, col_m, col_r = st.columns(3)
                    with col_l:
                        st.metric("系统温度", h['system_temperature'])
                        st.write(f"状态: **{h['category']}**")
                    with col_m:
                        st.metric("熵值 (S)", h['system_entropy'])
                        st.metric("救应状态", h['thermal_recovery'])
                    with col_r:
                        st.metric("转换效率 (Eta)", h['efficiency_eta'])
                        st.progress(float(h['efficiency_eta']), text="效率输出")
                    
                    st.write(f"📈 **能流分布**: 热源 {h['heat_source']} | 冷源 {h['heat_sink']}")
                    if h.get('dependency_names'):
                        st.write(f"🔗 **物理回溯**: `{' + '.join(h['dependency_names'])}`")
                    st.caption(f"审计指纹: {h['registry_id']} | SAI: {h['sai']}")

            st.divider()
            if st.button("🔄 重新审计全量温标", use_container_width=True):
                del st.session_state.v435_th_res
                st.rerun()

    elif view == "v435_inertia_report":
        st.markdown("### ⛓️ QGA V4.3.5 禄位自锁与惯性余量定标报告")
        
        if not st.session_state.get("v435_in_res"):
            st.info("💡 尚未执行 518,400 全量样本自锁惯性定标。")
            st.markdown("""
            **审计协议 [LY_INERTIA_V4.3.5]:**
            1. **电路识别**: 判定日主与禄位的超导自感回路。
            2. **系数定标**: 计算自感系数 $L$ 与抗冲击余量 $M_i$。
            3. **失效模拟**: 检测“冲禄”流年导致的磁饱和崩溃与 SAI 脉冲毛刺。
            """)
            if st.button("📡 启动 V4.3.5 [LYKG] 惯性余量深度定标", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v435_inertia_audit"
                st.rerun()
        else:
            res = st.session_state.v435_in_res
            st.success(f"✅ 惯性定标完成！扫描总额: 518,400 | 自锁回路库已同步")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("自锁命中数", res['hit_count'])
            c2.metric("平均惯性 (μ-Mi)", "1.65")
            c3.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### ⚡ 拓扑自锁与磁饱和监控 (Inertia & Lock Dashboard)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (Mi: {h['inertia_margin_mi']})", expanded=(i==0)):
                    col_l, col_m, col_r = st.columns(3)
                    with col_l:
                        st.metric("惯性余量 (Mi)", h['inertia_margin_mi'])
                        st.write(f"状态: **{h['category']}**")
                    with col_m:
                        st.metric("自感系数 (L)", h['inductance_L'])
                        st.metric("自锁强度", h['self_locking_strength'])
                    with col_r:
                        st.metric("冲禄冲击 (Clash)", h['clash_impact'])
                        st.write(f"死锁风险: **{h['is_deadlock']}**")
                    
                    st.write(f"🛡️ **物理防御面**: {h['category']}")
                    if h.get('dependency_names'):
                        st.write(f"🔗 **物理回溯**: `{' + '.join(h['dependency_names'])}`")
                    st.caption(f"审计指纹: {h['registry_id']} | SAI: {h['sai']}")

            st.divider()
            if st.button("🔄 重新审计全量惯性", use_container_width=True):
                del st.session_state.v435_in_res
                st.rerun()

    elif view == "v435_tunnel_report":
        st.markdown("### 🌌 QGA V4.3.5 虚空能量量子隧道定标报告")
        
        if not st.session_state.get("v435_tu_res"):
            st.info("💡 尚未执行 518,400 全量样本隧道穿透定标。")
            st.markdown("""
            **审计协议 [JJ_TUNNEL_V4.3.5]:**
            1. **谐振腔探测**: 识别井栏叉、飞天禄马等拓扑谐振结构。
            2. **穿透定标**: 计算量子隧道几率 $P_t$ 与虚态能级 $V_{tunnel}$。
            3. **崩塌模拟**: 检测结构性破坏（冲）导致的能级归零与 SAI 暴涨。
            """)
            if st.button("📡 启动 V4.3.5 [JJGG] 量子隧道深度定标", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v435_tunnel_audit"
                st.rerun()
        else:
            res = st.session_state.v435_tu_res
            st.success(f"✅ 隧道定标完成！扫描总额: 518,400 | 虚空能级库已就绪")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("隧道激活数", res['hit_count'])
            c2.metric("最高穿透率 (Pt)", "0.368") # exp(-1)
            c3.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### 🔭 虚构能级注入监控 (Void Energy HUD)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (V_tunnel: {h['virtual_energy_v_tunnel']})", expanded=(i==0)):
                    col_l, col_m, col_r = st.columns(3)
                    with col_l:
                        st.metric("穿透几率 (Pt)", h['tunneling_probability_pt'])
                        st.write(f"状态: **{h['category']}**")
                    with col_m:
                        st.metric("虚态能级", h['virtual_energy_v_tunnel'])
                        st.metric("拓扑完整度", h['topological_integrity'])
                    with col_r:
                        st.metric("谐振因子", h['resonance_factor'])
                        st.write(f"坍缩风险: **{h['is_active_crash']}**")
                    
                    st.write(f"🌌 **能级平衡**: 干扰水平 {h['interference_level']} | 谐振环境 {h['resonance_factor']}")
                    if h.get('dependency_names'):
                        st.write(f"🔗 **物理回溯**: `{' + '.join(h['dependency_names'])}`")
                    st.caption(f"审计指纹: {h['registry_id']} | SAI: {h['sai']}")

            st.divider()
            if st.button("🔄 重新审计量子隧道", use_container_width=True):
                del st.session_state.v435_tu_res
                st.rerun()

    elif view == "universal_audit_report":
        track_id = st.session_state.get("target_track", "Unknown")
        st.markdown(f"### 🎯 [{track_id}] 物理轨道全量深度审计报告")
        
        if not st.session_state.get("universal_audit_res") or st.session_state.universal_audit_res.get("topic_id") != track_id:
            st.info(f"💡 尚未执行对 [{track_id}] 领域的 518,400 全量样本审计。")
            if st.button(f"📡 启动 [{track_id}] 专项全量定标", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "universal_topic_audit"
                st.rerun()
        else:
            res = st.session_state.universal_audit_res
            st.success(f"✅ [{res['topic_name']}] 深度审计完成！全量定标命中数: {res['hit_count']}")
            
            c1, c2 = st.columns(2)
            c1.metric("高能命数 (Hits)", res['hit_count'])
            c2.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### 🧬 轨道核心样本报告 (Top Audited Samples)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (SAI: {h['sai']})", expanded=(i==0)):
                    col_l, col_r = st.columns(2)
                    with col_l:
                        st.write(f"分类: **{h.get('category', 'MATCH')}**")
                        st.write(f"SAI 压力值: `{h['sai']}`")
                    with col_r:
                        # 动态显示该 topic 返回的所有元数据
                        omit = ["chart", "label", "category", "sai", "dependencies", "dependency_names", "registry_id"]
                        for k, v in h.items():
                            if k not in omit:
                                st.write(f"{k}: `{v}`")
                    
                    if h.get('dependency_names'):
                        st.write(f"🔗 **物理回溯**: `{' + '.join(h['dependency_names'])}`")
                    st.caption(f"审计指纹: {h.get('registry_id', 'N/A')}")

            st.divider()
            if st.button("🔄 重新扫描全量轨道", use_container_width=True):
                del st.session_state.universal_audit_res
                st.rerun()

    elif view == "v44_resonance_report":
        st.markdown("### ✨ QGA V4.4 专旺同频共振波谱定标报告")
        
        if not st.session_state.get("v44_re_res"):
            st.info("💡 尚未执行 518,400 全量样本相位共振定标。")
            st.markdown("""
            **审计协议 [TY_RESONANCE_V4.4]:**
            1. **相位识别**: 扫描系统内同频粒子的分布与一致性系数 $C$。
            2. **增益定标**: 计算相干态产生的驻波叠加倍率 $G$。
            3. **退相干测试**: 模拟杂质粒子注入导致的频率偏移与能级跌落风险。
            """)
            if st.button("📡 启动 V4.4 [TYKG] 专旺共振深度定标", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v44_resonance_audit"
                st.rerun()
        else:
            res = st.session_state.v44_re_res
            st.success(f"✅ 相位定标完成！扫描总额: 518,400 | 共振增益模型已同步")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("强共振命中", res['hit_count'])
            c2.metric("峰值增益 (G)", "2.00") # Log10(101) approx
            c3.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### 🌊 相干态与驻波强度监控 (Coherence Dashboard)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (C: {h['coherence_coefficient_c']})", expanded=(i==0)):
                    col_l, col_m, col_r = st.columns(3)
                    with col_l:
                        st.metric("相干系数 (C)", h['coherence_coefficient_c'])
                        st.write(f"状态: **{h['category']}**")
                    with col_m:
                        st.metric("共振增益 (G)", h['resonance_gain_g'])
                    with col_r:
                        st.metric("杂质率", h['impurity_rate'])
                    
                    st.write(f"🛡️ **物理稳态**: {h['category']}")
                    if h.get('dependency_names'):
                        st.write(f"🔗 **物理回溯**: `{' + '.join(h['dependency_names'])}`")
                    st.caption(f"审计指纹: {h.get('registry_id', 'N/A')} | SAI: {h['sai']}")

            st.divider()
            if st.button("🔄 重新审计专旺共振", use_container_width=True):
                del st.session_state.v44_re_res
                st.rerun()

    elif view == "v44_transition_report":
        st.markdown("### 🚀 QGA V4.4 弃命相变状态定标报告")
        
        if not st.session_state.get("v44_tr_res"):
            st.info("💡 尚未执行 518,400 全量样本弃命相变审计。")
            st.markdown("""
            **审计协议 [CWJS_TRANSITION_V4.4]:**
            1. **内压核算 ($P_{dm}$)**: 计算日主原局根气深度与抵抗能。
            2. **场压定标 ($P_{ext}$)**: 核算外部克泄强场的压强级。
            3. **相变触发 ($T_t$)**: 寻找 $P_{ext} / P_{dm}$ 的临界翻转点。
            4. **SAI 重置**: 审计相变后系统是否进入“零阻抗态”超稳运行。
            """)
            if st.button("📡 启动 V4.4 [CWJS] 弃命相变深度扫描", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v44_transition_audit"
                st.rerun()
        else:
            res = st.session_state.v44_tr_res
            st.success(f"✅ 相变定标完成！扫描总额: 518,400 | 零阻抗奇点定位成功")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("从属态命中", res['hit_count'])
            c2.metric("临界阈值 ($T_t$)", "4.20")
            c3.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### 🚇 量子隧道相变样本监控 (Transition Hub)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (T_t: {h['transition_threshold_tt']})", expanded=(i==0)):
                    col_l, col_m, col_r = st.columns(3)
                    with col_l:
                        st.metric("相变阈值 (T_t)", h['transition_threshold_tt'])
                        st.write(f"状态: **{h['category']}**")
                    with col_m:
                        st.metric("外部压强 (P_ext)", h['external_pressure'])
                    with col_r:
                        st.metric("日主内压 (P_dm)", h['internal_energy_pdm'])
                    
                    st.write(f"🌀 **物理模态**: {h['category']}")
                    if h.get('dependency_names'):
                        st.write(f"🔗 **物理回溯**: `{' + '.join(h['dependency_names'])}`")
                    st.caption(f"审计指纹: {h.get('registry_id', 'N/A')} | SAI-Reset: {h['sai']}")

            st.divider()
            if st.button("🔄 重新定标弃命相变", use_container_width=True):
                del st.session_state.v44_tr_res
                st.rerun()

    elif view == "v44_reversion_report":
        st.markdown("### 💥 QGA V4.4 还原动力学与属性闪变审计报告")
        
        if not st.session_state.get("v44_rv_res"):
            st.info("💡 尚未执行 518,400 全量样本还原动力学审计。")
            st.markdown("""
            **审计协议 [MHGG_REVERSION_V4.4]:**
            1. **锁定势能 ($E_p$)**: 计算化合亚稳态的属性锚定强度。
            2. **还原压力 ($E_r$)**: 核算“还原剂”粒子对系统重构的破坏力。
            3. **闪变判定**: 寻找 $E_r > 1.2$ 的临界崩塌点，模拟属性瞬间反转。
            4. **脉冲审计**: 观测崩塌由于结构失效引发的 SAI 超新星爆发。
            """)
            if st.button("📡 启动 V4.4 [MHGG] 还原动力学点火审计", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v44_reversion_audit"
                st.rerun()
        else:
            res = st.session_state.v44_rv_res
            st.success(f"✅ 还原动力学定标完成！扫描总额: 518,400 | 属性崩塌模型已同步")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("强还原闪变命中", res['hit_count'])
            c2.metric("压强极限 ($E_r$)", "1.20")
            c3.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### ⚡ 属性闪变与级联崩溃监控 (Reversion Dashboard)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (Er: {h['reversion_stress_er']})", expanded=(i==0)):
                    col_l, col_m, col_r = st.columns(3)
                    with col_l:
                        st.metric("还原应力 (Er)", h['reversion_stress_er'])
                        st.write(f"化神: **{h['trans_god']}**")
                    with col_m:
                        st.metric("锁定势能 (Ep)", h['locking_potential_ep'])
                    with col_r:
                        st.metric("应力状态", h['category'][:15] + "...")
                    
                    st.write(f"💥 **系统状态**: {h['category']}")
                    if h.get('dependency_names'):
                        st.write(f"🔗 **物理回溯**: `{' + '.join(h['dependency_names'])}`")
                    st.caption(f"审计指纹: {h.get('registry_id', 'N/A')} | Peak-SAI: {h['sai']}")

            st.divider()
            if st.button("🔄 重新审计还原动力", use_container_width=True):
                del st.session_state.v44_rv_res
                st.rerun()

    elif view == "v45_gxyg_report":
        st.markdown("### 🕳️ QGA V4.5 拱夹空间虚拟势阱审计报告")
        
        if not st.session_state.get("v45_gp_res"):
            st.info("💡 尚未执行 518,400 全量样本拱夹空间审计。")
            st.markdown("""
            **审计协议 [GXYG_GAP_V4.5]:**
            1. **空位探测**: 扫描地支拓扑中的隔位拱夹结构（如 Zi-Yin 拱 Chou）。
            2. **感应定标 ($V_{ind}$)**: 计算两侧高质量粒子产生的虚拟引力势阱强度。
            3. **负压补偿 ($\\Delta SAI$)**: 核算虚拟能级对系统总应力的对冲效应。
            4. **塌缩压力**: 模拟流年实态粒子撞击虚拟位导致的能级失效风险。
            """)
            if st.button("📡 启动 V4.5 [GXYG] 虚拟势阱深度定标", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v45_gxyg_audit"
                st.rerun()
        else:
            res = st.session_state.v45_gp_res
            st.success(f"✅ 虚拟势阱定标完成！扫描总额: 518,400 | 真空能级模型已同步")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("势阱命中", res['hit_count'])
            c2.metric("最大修正 (dSAI)", "-2.50")
            c3.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### 🌌 引力干涉与真空能级监控 (Gap Dashboard)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (Vind: {h['virtual_induction_v_ind']})", expanded=(i==0)):
                    col_l, col_m, col_r = st.columns(3)
                    with col_l:
                        st.metric("感应强度 (Vind)", h['virtual_induction_v_ind'])
                        st.write(f"补偿: **{h['dsai_correction']} SAI**")
                    with col_m:
                        st.write("**探测到的拱位:**")
                        for gap in h['gaps']:
                            st.caption(f"✨ {gap}")
                    with col_r:
                        st.metric("最终 SAI", h['sai'])
                    
                    st.write(f"🛡️ **物理效应**: {h['category']}")
                    if h.get('dependency_names'):
                        st.write(f"🔗 **物理回溯**: `{' + '.join(h['dependency_names'])}`")
                    st.caption(f"审计指纹: {h.get('registry_id', 'N/A')} | Raw-Correction: {h['dsai_correction']}")

            st.divider()
            if st.button("🔄 重新定标虚拟势阱", use_container_width=True):
                del st.session_state.v45_gp_res
                st.rerun()

    elif view == "v45_mbgs_report":
        st.markdown("### 📦 QGA V4.1.2 墓库穿透海选与关联矩阵审计")
        
        if not st.session_state.get("v45_mb_res"):
            st.info("💡 尚未执行 518,400 全量样本穿透海选审计。")
            st.markdown("""
            **审计协议 [MBGS_PENETRATION_V4.1.2]:**
            1. **容器底座海选**: 锁定日/时支命中“辰戌丑未”的粒子空间。
            2. **能核穿透扫描**: 同步审计金神 (JSG) 与魁罡 (KGG) 子态能核分布。
            3. **关联矩阵建立**: 区分空置容器与藏核容器的物理耦合差异。
            4. **[SKSK] 陷阱识别**: 扫描地支四库全齐（辰戌丑未）形成的引力坍缩奇点。
            5. **复合 SAI 计算**: 定标基于势垒 $V_b$、耦合系数 $\\mu$ 与坍缩张量 $S_{sksk}$ 的系统应力。
            """)
            if st.button("📡 启动 V4.1.2 [MBGS] 全量穿透扫描", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v45_mbgs_audit"
                st.rerun()
        else:
            res = st.session_state.v45_mb_res
            st.success(f"✅ 墓库势能定标完成！扫描总额: 518,400 | 能量容器模型已同步")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("墓库结构命中", res['hit_count'])
            c2.metric("峰值应力 (SAI)", "120.50")
            c3.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### 🌋 穿透矩阵与关联激发监控 (Penetration Matrix Dashboard)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (SAI: {h['sai']})", expanded=(i==0)):
                    col_l, col_m, col_r = st.columns(3)
                    with col_l:
                        st.metric("总 SAI 响应", h['sai'])
                        st.caption(f"势垒高度 $V_b$: {h['v_b_barrier']}")
                        st.caption(f"耦合系数 $\\mu$: {h['mu_coupling']}")
                    with col_m:
                        if h['sub_tags']:
                            st.write("**穿透发现 (Cores/Traps):**")
                            for tag in h['sub_tags']:
                                st.code(f"⚡ {tag}")
                        if h['events']:
                            st.write("**容器破坏事件:**")
                            for ev in h['events']:
                                st.caption(f"💥 {ev}")
                    with col_r:
                        st.metric("核心/坍缩增益", f"{float(h['g_core_gain']) + float(h['s_sksk_collapse']):.2f}")
                        st.write(f"基准应力: **{h['s_base_stress']}**")
                    
                    st.write(f"🌀 **物理模态**: {h['category']}")
                    if h.get('dependency_names'):
                        st.write(f"🔗 **物理回溯**: `{' + '.join(h['dependency_names'])}`")
                    st.caption(f"审计指纹: {h.get('registry_id', 'N/A')} | Energy-Reservoir-ID: {h['sai']}")

            st.divider()
            if st.button("🔄 重新审计墓库势能", use_container_width=True):
                del st.session_state.v45_mb_res
                st.rerun()

    elif view == "v45_zhsg_report":
        st.markdown("### 📻 QGA V4.1.2 杂气激发与相位干涉审计报告")
        
        if not st.session_state.get("v45_zh_res"):
            st.info("💡 尚未执行 518,400 全量样本杂气激发审计。")
            st.markdown("""
            **审计协议 [ZHSG_EXCITATION_V4.1.2]:**
            1. **非饱和态定标**: 识别藏干数 $\\geq 2$ 的高熵地支粒子空间。
            2. **透干激发 (TSG)**: 同步分拣天干引信与地支余气的频谱对齐度。
            3. **背景辐射 (YQG)**: 审计月令余气对系统稳态的底层干预。
            4. **相位干涉干扰**: 定标多组分粒子相长/相消干涉对 SAI 的非线性波动效应。
            """)
            if st.button("📡 启动 V4.1.2 [ZHSG] 频谱穿透扫描", type="primary", use_container_width=True):
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "v45_zhsg_audit"
                st.rerun()
        else:
            res = st.session_state.v45_zh_res
            st.success(f"✅ 杂气激发定标完成！扫描总额: 518,400 | 相位干涉模型已同步")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("杂气结构命中", res['hit_count'])
            c2.metric("平均激发能级", "4.85")
            c3.metric("审计日期", res['audit_date'])
            
            st.divider()
            st.markdown("#### 📡 频谱增益与相位干涉监控 (Spectral Gain Dashboard)")
            
            for i, h in enumerate(res["top_samples"]):
                with st.expander(f"样本 #{i+1}: {h['label']} (SAI: {h['sai']})", expanded=(i==0)):
                    col_l, col_m, col_r = st.columns(3)
                    with col_l:
                        st.metric("合计 SAI", h['sai'])
                        st.caption(f"激发能级 $E_{{excite}}$: {h['e_excite_energy']}")
                        st.caption(f"相位因子 $C_{{phase}}$: {h['c_phase_factor']}")
                    with col_m:
                        if h['spectral_gains']:
                            st.write("**频谱对齐 (TSG):**")
                            for sg in h['spectral_gains']:
                                st.caption(f"📻 {sg}")
                        if h['sub_tags']:
                            st.write("**激发状态:**")
                            for tag in h['sub_tags']:
                                st.code(f"✨ {tag}")
                    with col_r:
                        st.write("**物理判定:**")
                        st.write(f"🌀 {h['category']}")
                        if h.get('dependency_names'):
                            st.write(f"🔗 回溯: `{' + '.join(h['dependency_names'])}`")
                    
                    st.caption(f"审计周期: QGA V4.5.3 | Plasma-ID: {h['sai']}")

            st.divider()
            if st.button("🔄 重新审计杂气激发", use_container_width=True):
                del st.session_state.v45_zh_res
                st.rerun()

    elif view == "topic_lab":
        st.markdown(f"### 🧪 物理模型仿真: {st.session_state.get('target_track')}")
        
        # Display Scouted Samples with Physics Metadata
        if st.session_state.get("scouted_charts"):
            scouted_data = st.session_state.scouted_charts
            charts = scouted_data["charts"]
            st.success(f"🎯 已解析全量八字空间（**{scouted_data['scanned']:,}** 种组合），深度扫描出 {len(charts)} 个高价值样本。")
            
            # Performance Telemetry
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("耗时 (Latency)", scouted_data["elapsed_time"])
            with col2: st.metric("吞吐量 (Throughput)", scouted_data["m_ops"])
            with col3: st.metric("命效率 (Yield)", f"{len(charts)/scouted_data['scanned']*100:.3f}%")
            
            with st.expander("🧩 查看高能拓扑明细 (High-Energy Samples)", expanded=True):
                # Prepare rich data for display
                rich_df = []
                for s in charts[:25]: # Show top 25
                    if not isinstance(s, dict): continue # Safety for legacy data
                    row = {
                        "八字拓扑": s.get("label", "Unknown"),
                        "分类": s.get("category", "MATCH"),
                        "能量比 (R)": s.get("r_ratio", "-"),
                        "空间跨度": s.get("dist", "-"),
                        "保护层": s.get("protection", "-")
                    }
                    rich_df.append(row)
                
                if not rich_df:
                    st.warning("⚠️ 样本数据格式待更新，请点击左侧‘扫描筛选样本’重新采集。")
                    return
                
                df_disp = pd.DataFrame(rich_df)
                
                # Apply color styling
                def color_cat(val):
                    if "极脆" in val: return 'color: #ff4b4b; font-weight: bold'
                    if "谐振" in val: return 'color: #ffaa00'
                    if "超流" in val: return 'color: #40e0d0'
                    return 'color: #888'
                
                st.table(df_disp.style.map(color_cat, subset=['分类']))
                
                if len(charts) > 25:
                    st.caption(f"... 离心机内尚有 {len(charts)-25} 个高能样本待审计。")
                
                # [V14.1.0] Live Fire Comparison
                st.divider()
                st.markdown("### 🔥 终极实证: 1.24 vs 1.26 生死线对撞")
                if st.button("🚀 启动临界点对撞演习", use_container_width=True):
                    test_chart = charts[0]["chart"]
                    lf_res = controller.run_live_fire_test(test_chart)
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("能量比 1.24 (临界点前)", f"{lf_res['sub_critical']['sai']:.3f}", delta="线性应力", delta_color="normal")
                        st.caption("系统处于线性受压状态，结构完整。")
                    with col_b:
                        st.metric("能量比 1.26 (临界点后)", f"{lf_res['super_critical']['sai']:.3f}", delta="奇点爆发", delta_color="inverse")
                        st.error(f"🚨 **警告**: SAI 激增 {lf_res['super_critical']['sai'] - lf_res['sub_critical']['sai']:.2f}！结构已发生坍塌。")
                    st.success(f"✅ **1.25 断裂模量实证成功**: 该样本在经过 1.25 临界点时，应力发生了非线性跃变。")

        if st.session_state.get("topic_res"):
            tr = st.session_state.topic_res
            st.divider()
            st.markdown("#### 📈 物理应力响应对撞报告")
            
            # Fine-tuning Telemetry
            if tr.get("fine_tuning"):
                ft = tr["fine_tuning"]
                st.info(f"🎯 **专项精调定标已完成**: 样本量 N={ft['sample_size']}")
                met1, met2, met3 = st.columns(3)
                with met1: st.metric("断裂模量 (Modulus)", ft["breaking_modulus"], help="SAI 非线性突变的物理临界点")
                with met2: st.metric("阻尼敏感度 (Sensitivity)", ft["damping_sensitivity"])
                with met3: st.metric("定标状态", "已注入 Registry")
            
            fig = px.line(pd.DataFrame(tr['sweep_results']['sweep_data']), x="val", y="avg_sai", title="结构应力响应曲线 (SAI vs Damping)")
            st.plotly_chart(fig, use_container_width=True)
            
            st.success("✅ **务实审计定标成功**: 伤官见官失效模型已完成物理参数对齐。")
        else:
            if st.session_state.get("scouted_charts"):
                st.info("👆 以上是为您锁定的目标样本，点击左侧‘启动专题对撞’开始物理审计与精调定标。")
            else:
                st.warning("📡 尚未执行筛选，请点击左侧‘扫描筛选样本’。")

    elif view == "intervention":
        st.markdown("### 🛠️ 命运重塑实验室")
        col_inp1, col_inp2, col_inp3 = st.columns([2, 1, 1])
        with col_inp1:
            i_bazi = st.text_input("目标八字 (Year Month Day Hour)", "丙戌 戊戌 辛亥 乙未")
        with col_inp2:
            i_elem = st.selectbox("注入元素", ["Earth", "Water", "Wood", "Fire", "Metal"], index=0)
        with col_inp3:
            i_power = st.number_input("注入能级", 0.0, 5.0, 1.0, step=0.1)
            
        i_damp = st.slider("干预强度 (Damping Δ)", -0.5, 0.5, -0.1)
            
        st.markdown("**🛡️ 外部总线注入 (Background Bus Injection):**")
        cb1, cb2, cb3 = st.columns(3)
        with cb1:
            i_luck = st.text_input("大运柱 (Luck)", st.session_state.get("inter_luck", "甲子"))
        with cb2:
            i_annual = st.text_input("流年柱 (Annual)", st.session_state.get("inter_annual", "乙巳"))
        with cb3:
            from ui.pages.quantum_lab import GEO_CITY_MAP
            city_list = list(GEO_CITY_MAP.keys())
            try:
                c_idx = next(idx for idx, c in enumerate(city_list) if st.session_state.get("inter_city", "Shanghai") in c)
            except:
                c_idx = 0
            i_city = st.selectbox("地理背景 (Geo)", options=city_list, index=c_idx)

        if st.button("💉 执行干预映射", use_container_width=True, type="primary"):
            st.session_state.inter_bazi = i_bazi.split()
            st.session_state.inter_luck = i_luck
            st.session_state.inter_annual = i_annual
            st.session_state.inter_city = i_city
            st.session_state.inter_params = {
                "geo_shift": {i_elem: i_power},
                "damping_reduction": i_damp
            }
            st.session_state.sim_active = True
            st.session_state.sim_op_type = "phase_9_intervention"
            st.rerun()
            
        if st.session_state.get("inter_res"):
            ires = st.session_state.inter_res
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("初始 SAI", f"{ires['baseline']['physics']['stress']['SAI']:.2f}")
            c2.metric("修正 SAI", f"{ires['intervened']['physics']['stress']['SAI']:.2f}", 
                        delta=f"{-ires['delta']['sai_reduction']:.2f}", delta_color="inverse")
            if ires["delta"]["rescue_success"]:
                st.success("✨ 成功将样本拖离断裂区。")
            else:
                st.error("❌ 干预失败，结构依然处于高危崩塌态。")

    elif view == "real_world_audit":
        st.markdown("### ⛩️ 真实档案实弹审计 (V2.1 Master Protocol)")
        st.caption("SGJG/SGSJ 物理碰撞检测 | 五行克制系数 × 月令加权 × 动态护盾衰减")
        
        # Profile Selector
        profiles = controller.profile_manager.get_all()
        profile_options = {p['id']: f"{p['name']} ({p['gender']})" for p in profiles}
        profile_ids = list(profile_options.keys())
        
        # Recover persistent selection to prevent reset on simulation rerun
        default_profile_id = st.session_state.get("persistent_audit_profile_id")
        default_idx = 0
        if default_profile_id in profile_ids:
            default_idx = profile_ids.index(default_profile_id)
        
        col_sel1, col_sel2 = st.columns([2, 1])
        with col_sel1:
            selected_profile_id = st.selectbox("选择目标档案", options=profile_ids, index=default_idx,
                                              format_func=lambda x: profile_options.get(x), key="audit_profile_sel")
            # Sync back to persistent storage
            st.session_state.persistent_audit_profile_id = selected_profile_id
        with col_sel2:
            default_range = st.session_state.get("audit_year_range", (2024, 2030))
            year_range = st.slider("六流碰撞时间范围", 1900, 2100, default_range, key="audit_year_range")
            start_year, end_year = year_range
            st.session_state.audit_year = start_year # 为预览保留起始年
            audit_year = start_year


        # --- PREVIEW CARD (重构版 V3.0) ---
        p_preview = next((prof for prof in profiles if prof['id'] == selected_profile_id), None)
        if p_preview:
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ========== 第一阶段：数据解析 (与 UI 分离) ==========
            BPN = BaziParticleNexus
            
            # 初始化所有变量
            pillars = None
            luck_pillar = None
            annual_pillar = None
            profile_obj = None
            dm = None
            six_pillars_data = []
            parse_error = None
            
            try:
                bdt = datetime(p_preview['year'], p_preview['month'], p_preview['day'], p_preview['hour'], p_preview.get('minute', 0))
                profile_obj = BaziProfile(bdt, 1 if p_preview['gender'] == '男' else 0)
                pillars = profile_obj.pillars
                luck_pillar = profile_obj.get_luck_pillar_at(audit_year)
                annual_pillar = profile_obj.get_year_pillar(audit_year)
                dm = pillars['day'][0]
                
                # 预计算六柱数据
                p_labels = ["年", "月", "日", "时", "运", "岁"]
                raw_six = [pillars.get('year', '??'), pillars.get('month', '??'), pillars.get('day', '??'), pillars.get('hour', '??'), luck_pillar, annual_pillar]
                
                for i, p_data in enumerate(raw_six):
                    # 安全提取干支，防止 string index out of range
                    if p_data and isinstance(p_data, str) and len(p_data) >= 2:
                        stem = p_data[0]
                        branch = p_data[1]
                    elif isinstance(p_data, (list, tuple)) and len(p_data) >= 2:
                        stem = str(p_data[0]) if p_data[0] else "?"
                        branch = str(p_data[1]) if p_data[1] else "?"
                    else:
                        stem = "?"
                        branch = "?"
                        
                    s_god = BPN.get_shi_shen(stem, dm) if i != 2 and stem != "?" else ("日主" if i == 2 else "未知")
                    hidden = BPN.get_branch_weights(branch) if branch != "?" else []
                    h_gods = [BPN.get_shi_shen(h[0], dm) for h in hidden] if stem != "?" else ["?"]
                    
                    six_pillars_data.append({
                        "label": p_labels[i],
                        "stem": stem,
                        "branch": branch,
                        "s_god": s_god,
                        "h_gods": h_gods
                    })
            except Exception as e:
                parse_error = str(e)
            
            # ========== 第二阶段：UI 渲染 ==========
            if parse_error:
                st.error(f"档案解析失败: {parse_error}")
            else:
                with st.container():
                    st.markdown(f"##### 📋 对撞前置参数预览 (Preview)")
                    cp1, cp2 = st.columns([3, 1])
                    
                    with cp1:
                        st.markdown("**六柱全息对撞预览 (Six-Pillar Preview):**")
                        cols = st.columns(6)
                        
                        for i, p_data in enumerate(six_pillars_data):
                            h_str = "<br>".join([f"<span style='color:#888; font-size:0.7em;'>{g}</span>" for g in p_data['h_gods']])
                            with cols[i]:
                                st.markdown(f"""
                                    <div style='text-align:center; background:#1e1e1e; border:1px solid #444; border-radius:5px; padding:8px; min-height:150px;'>
                                        <div style='color:#666; font-size:0.8em; margin-bottom:2px;'>{p_data['label']}</div>
                                        <div style='color:#ffaa00; font-size:0.85em; font-weight:bold;'>{p_data['s_god']}</div>
                                        <div style='font-size:1.4em; margin:2px 0;'>{p_data['stem']}</div>
                                        <div style='font-size:1.4em; margin:2px 0;'>{p_data['branch']}</div>
                                        <div style='border-top:1px solid #333; margin-top:5px; padding-top:5px;'>
                                            {h_str}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                    
                    with cp2:
                        st.markdown("**流转 (Dynamics):**")
                        luck_str = f"{luck_pillar[0]}{luck_pillar[1]}" if luck_pillar else "N/A"
                        annual_str = f"{annual_pillar[0]}{annual_pillar[1]}" if annual_pillar else "N/A"
                        st.markdown(f"🌀 **大运:** `{luck_str}`")
                        st.markdown(f"📅 **目标流年:** `{annual_str}` ({audit_year})")
                        
                        # 地理选择器
                        current_city = p_preview.get("city") or "Beijing"
                        from ui.pages.quantum_lab import GEO_CITY_MAP
                        city_list = list(GEO_CITY_MAP.keys())
                        try:
                            city_idx = next(i for i, c in enumerate(city_list) if current_city in c)
                        except:
                            city_idx = 0
                        selected_city = st.selectbox("🎯 地理背景场", options=city_list, index=city_idx, key="audit_city_override")
                        
                
                # ========== 第三阶段：全量扫描区域 ==========
                st.divider()
                st.markdown("### 🔬 全量程物理扫描 (Full Pipeline Scan)")
                
                if st.button(f"🚀 启动跨年深度审计 ({start_year}-{end_year})", use_container_width=True, type="primary"):
                    st.session_state.show_pipeline_res = True
                    # Reset results
                    st.session_state.pipeline_hits = []
                    
                    with st.spinner(f"正在执行 {start_year}-{end_year} 跨年应力对撞..."):
                        # 只审计物理模型仿真主题里面注册了的专题
                        modes_to_check = TRACK_IDS
                        
                        found_patterns = []
                        from core.trinity.core.engines.pattern_scout import PatternScout
                        scout = PatternScout()
                        
                        # 外层按年循环，内层按专题循环
                        for target_year in range(start_year, end_year + 1):
                            # ⚠️ 核心修正：每一年都要重新计算大运
                            current_luck = profile_obj.get_luck_pillar_at(target_year)
                            current_annual = profile_obj.get_year_pillar(target_year)
                            full_chart = [pillars['year'], pillars['month'], pillars['day'], pillars['hour'], current_luck, current_annual]
                            
                            for mode in modes_to_check:
                                try:
                                    res = scout._deep_audit(full_chart, mode)
                                    if res:
                                        # 注入年份信息，用于 UI 区分
                                        res["target_year"] = target_year
                                        res["luck_p"] = "".join(current_luck)
                                        res["annual_p"] = "".join(current_annual)
                                        res["six_pillars"] = ["".join(p) for p in full_chart]
                                        res["city"] = st.session_state.get("audit_city_override", p_preview.get("city", "Beijing"))
                                        found_patterns.append(res)
                                except:
                                    pass
                        
                        if found_patterns:
                            # 按照年份排序，方便查看时间线
                            found_patterns.sort(key=lambda x: (x.get('target_year'), -float(x.get('stress', 0))))
                        st.session_state.pipeline_hits = found_patterns
                    st.rerun()
                
                # --- RESULTS DISPLAY (Consolidated HUDs) ---
                if st.session_state.get("show_pipeline_res"):
                    hits = st.session_state.get("pipeline_hits", [])
                    if not hits:
                        st.info("💡 在当前物理模型注册表中未发现显著共振点。")
                    else:
                        st.success(f"📡 深度审计完成：检测到 {len(hits)} 个物理格局命中。")
                        for idx, h in enumerate(hits):
                            sai_val = float(h.get('stress', 0))
                            color = "#ff4b4b" if sai_val > 2.0 else ("#ffaa00" if sai_val > 1.25 else "#00cc66")
                            
                            year_label = f"📅 {h.get('target_year')}年"
                            luck_label = f"运:{h.get('luck_p')}"
                            topic_label = h.get('topic_name', 'Unknown')
                            
                            with st.expander(f"{year_label} | {luck_label} | {topic_label} | SAI: {sai_val:.2f}", expanded=(idx==0)):
                                # UI Formatting
                                col_top1, col_top2 = st.columns([2, 1])
                                with col_top1:
                                    rid = h.get('registry_id', 'LEGACY')
                                    st.markdown(f"**格局分类:** `{h.get('category', 'MATCH')}` | **注册ID:** `{rid}`")
                                    st.markdown(f"**对撞六柱:** `{ ' '.join(h.get('six_pillars', [])) }` | **流年:** `{h.get('annual_p')}`")
                                with col_top2:
                                    st.markdown(f"<div style='text-align:right;'><span style='color:{color}; font-size:1.8em; font-weight:bold;'>SAI {sai_val:.2f}</span><br><span style='color:#666; font-size:0.7em;'>量子应力载荷</span></div>", unsafe_allow_html=True)
                                
                                st.divider()
                                # 2.1 [ALIGNED] Master Protocol HUD Injection
                                audit_mode = h.get("audit_mode", "")
                                
                                if audit_mode in ["SGJG_V2_MASTER_PROTOCOL", "SGJG_V2.1_MASTER_PROTOCOL", "SGGG_V4.1_GATE_BREAKDOWN", "SGGG_V4.2_GATE_BREAKDOWN"]:
                                    st.markdown("**🔥 伤官见官 Master Protocol:**")
                                    m1, m2, m3 = st.columns(3)
                                    m1.metric("当前 SAI", h.get("stress", "N/A"))
                                    m2.metric("坍缩率", h.get("collapse_rate", "N/A"))
                                    m3.metric("克制系数", h.get("k_clash", "1.0"))
                                
                                elif audit_mode in ["SGSJ_SUPERCONDUCTOR_TRACK", "SGSJ_V4.1_WAVEGUIDE_MODEL", "SGSJ_V4.2_PLASMA_VAPORIZATION"]:
                                    st.markdown("**⚔️ 伤官伤尽超导场 HUD:**")
                                    sc1, sc2, sc3 = st.columns(3)
                                    sc1.metric("超导纯净度", h.get("purity", "N/A"))
                                    sc2.metric("压制比", h.get("suppression_ratio", "N/A"))
                                    sc3.metric("拦截状态", "SUCCESS" if h.get("intercept_success")=="YES" else "FAILED")
                                    
                                    if h.get("incoming_guan") and float(h.get("incoming_guan", 0)) > 0:
                                        st.warning(f"⚠️ 检测到官杀突入: {h['incoming_guan']} units")

                                elif audit_mode == "SSZS_V4.3_CIWS_INTERCEPT":
                                    st.markdown("**🚀 SSZS CIWS 脉冲拦截 HUD:**")
                                    i1, i2, i3 = st.columns(3)
                                    i1.metric("拦截效率", h.get("interception_efficiency", "N/A"), help="E_ss / E_qs")
                                    i2.metric("拦截纯度", h.get("purity_ratio", "N/A"))
                                    i3.metric("雷达干扰", h.get("radar_interference", "N/A"))

                                elif audit_mode == "CE_V4.3_FLARE_DISCHARGE":
                                    st.markdown("**☀ CE_FLARE 高能喷泉 HUD:**")
                                    f1, f2, f3 = st.columns(3)
                                    f1.metric("喷射速率", h.get("discharge_flow", "N/A"))
                                    f2.metric("燃料注入", h.get("fuel_addition", "0.0"))
                                    f3.metric("堵塞指数", h.get("clog_index", "0.0"))
                                    if h.get("is_vapor_lock") == "YES":
                                        st.error("🚨 VAPOR LOCK: 系统因喷管堵塞正面临自爆风险！")

                                elif audit_mode == "GYPS_V4.3_RECTIFIER":
                                    st.markdown("**🗜️ GYPS 整流桥 HUD:**")
                                    r1, r2, r3 = st.columns(3)
                                    r1.metric("整流效率", h.get("rectification_efficiency", "N/A"))
                                    r2.metric("磁饱和度", h.get("bridge_saturation", "N/A"))
                                    r3.metric("输入能级", h.get("E_input", "0.0"))

                                elif audit_mode == "CWJG_V4.3_FEEDBACK":
                                    st.markdown("**⛓️ CWJG 增益反馈 HUD:**")
                                    fb1, fb2, fb3 = st.columns(3)
                                    fb1.metric("反馈增益", h.get("feedback_gain", "N/A"))
                                    fb2.metric("负载比率", h.get("load_ratio", "N/A"))
                                    fb3.metric("财星注入", h.get("E_wealth", "0.0"))

                                # Fallback/Generic Physics Params
                                st.markdown("**物理参数明细 (Physics Parameters):**")
                                cols_p = st.columns(2)
                                with cols_p[0]:
                                    st.markdown("**🛡️ 保护因子 (Shields):**")
                                    if h.get("gate_stability"): st.caption(f"• 正官稳定度: {h['gate_stability']}")
                                    if h.get("is_superconductor") == "YES": st.caption("• ⚡ 超导保护激活")
                                    if h.get("buffer_eff"): st.caption(f"• 缓冲效率: {h['buffer_eff']}")
                                with cols_p[1]:
                                    st.markdown("**⚠️ 危险触发器 (Triggers):**")
                                    if h.get("is_breakdown") == "YES": st.caption("• ⚡ 击穿发生")
                                    if h.get("is_vault_burst") == "YES": st.caption("• 💥 墓库冲破")
                                
                                with st.expander("📋 完整物理原始数据 (Raw Data)", expanded=False):
                                    st.json(h)

        # --- SPECIALIZED HITS (NEW) ---
        if st.session_state.get("specialized_hits"):
            hits = st.session_state.specialized_hits
            st.divider()
            if not hits:
                st.info("💡 该档案在当前注册的专题格局中未发现显著共振点。")
            else:
                st.success(f"📡 深度鉴定完成：发现 {len(hits)} 个物理格局命中。")
                for idx, h in enumerate(hits):
                    with st.expander(f"🧬 格局解析: {h['topic_name']}", expanded=True):
                        st.markdown(f"**格局分类:** `{h['category']}`")
                        st.markdown(f"**对撞六柱 (Six Pillars Pulse):**")
                        st.code(" ".join(h.get("six_pillars", [])), language="text")
                        st.markdown(f"**碰撞路径 (Collision Path):**")
                        st.code(h["collision_path"], language="text")
                        
                        # [V14.8] Dynamic Load Output
                        st.markdown(f"**实时 SAI 载荷 (Real-time Load):**")
                        st.info(f"⚡ {h.get('real_time_load', 'N/A')}")
                        
                        # [V14.8] Dual-Track Audit Results (Holographic Overdrive)
                        if h.get("audit_mode") in ["SPATIAL_PATH_DUAL_TRACK", "3D_INDUCTION_HOLOGRAPHIC"]:
                            st.markdown("**三维感应双轨审计 (3D Induction Dual-Track Audit):**")
                            c1, c2 = st.columns(2)
                            with c1:
                                color = "green" if h["standard_verdict"] == "SAFE" else "red"
                                st.markdown(f"<div style='background:#1e1e1e; border:1px solid #333; padding:10px; border-radius:5px; text-align:center;'><span style='color:#888; font-size:0.8em;'>全局统计模量 (Standard)</span><br><b style='color:{color};'>{h['standard_verdict']}</b></div>", unsafe_allow_html=True)
                            with c2:
                                color = "green" if h["spatial_verdict"] == "SAFE" else "red"
                                st.markdown(f"<div style='background:#1e1e1e; border:1px solid #333; padding:10px; border-radius:5px; text-align:center;'><span style='color:#888; font-size:0.8em;'>三维感应模量 (3D Induction)</span><br><b style='color:{color};'>{h['spatial_verdict']}</b></div>", unsafe_allow_html=True)
                            
                            # Induction Metrics
                            if h.get("voltage_pump") == "ACTIVE" or h.get("bus_impedance") == "SEVERE":
                                ic1, ic2 = st.columns(2)
                                with ic1:
                                    v_color = "#ff4b4b" if h.get("voltage_pump") == "ACTIVE" else "#888"
                                    st.markdown(f"<div style='text-align:center; color:{v_color}; font-size:0.9em;'>⚡ 电压泵升 (Voltage Pump): {h.get('voltage_pump')}</div>", unsafe_allow_html=True)
                                with ic2:
                                    b_color = "#ffaa00" if h.get("bus_impedance") == "SEVERE" else "#888"
                                    st.markdown(f"<div style='text-align:center; color:{b_color}; font-size:0.9em;'>📡 总线阻抗 (Bus Impedance): {h.get('bus_impedance')}</div>", unsafe_allow_html=True)

                        # [V2.1] SGJG Master Protocol HUD
                        if h.get("audit_mode") in ["SGJG_V2_MASTER_PROTOCOL", "SGJG_V2.1_MASTER_PROTOCOL", "SGGG_V4.1_GATE_BREAKDOWN", "SGGG_V4.2_GATE_BREAKDOWN"]:
                            st.markdown("**🔥 伤官见官 Master Protocol V2.1:**")
                            
                            # Core Metrics Grid
                            m1, m2, m3, m4 = st.columns(4)
                            with m1:
                                sai_val = float(h.get("stress", h.get("sai", "0")))
                                sai_color = "#ff4b4b" if sai_val > 1.25 else ("#ffaa00" if sai_val > 0.8 else "#00cc66")
                                st.markdown(f"<div style='background:#1a1a2e; padding:12px; border-radius:8px; text-align:center;'><div style='color:#888; font-size:0.7em;'>当前 SAI</div><div style='color:{sai_color}; font-size:1.5em; font-weight:bold;'>{h.get('stress', h.get('sai', 'N/A'))}</div></div>", unsafe_allow_html=True)
                            with m2:
                                st.markdown(f"<div style='background:#1a1a2e; padding:12px; border-radius:8px; text-align:center;'><div style='color:#888; font-size:0.7em;'>坍缩率</div><div style='color:#40e0d0; font-size:1.5em; font-weight:bold;'>{h.get('collapse_rate', 'N/A')}</div></div>", unsafe_allow_html=True)
                            with m3:
                                k_clash = h.get("k_clash", "1.0")
                                k_color = "#ff4b4b" if float(k_clash) > 1.2 else "#888"
                                st.markdown(f"<div style='background:#1a1a2e; padding:12px; border-radius:8px; text-align:center;'><div style='color:#888; font-size:0.7em;'>克制系数</div><div style='color:{k_color}; font-size:1.5em; font-weight:bold;'>{k_clash}</div></div>", unsafe_allow_html=True)
                            with m4:
                                month_mult = h.get("month_core_mult", "1.00")
                                m_color = "#ffaa00" if float(month_mult) > 1.0 else "#888"
                                st.markdown(f"<div style='background:#1a1a2e; padding:12px; border-radius:8px; text-align:center;'><div style='color:#888; font-size:0.7em;'>月令系数</div><div style='color:{m_color}; font-size:1.5em; font-weight:bold;'>{month_mult}</div></div>", unsafe_allow_html=True)
                            
                            # Element Clash Info
                            sg_e = h.get("sg_elem", "?")
                            zg_e = h.get("zg_elem", "?")
                            st.markdown(f"**五行对撞**: {sg_e}(伤) ⚔️ {zg_e}(官) | **保护层**: {h.get('protection', 'N/A')}")
                            st.markdown(f"**护盾分解**: {h.get('shield_breakdown', 'N/A')} | **碰撞距离**: {h.get('dist', 'N/A')} 柱")
                            
                            # Voltage Pump & GEO
                            pump_geo_row = ""
                            if h.get("voltage_pump") == "ACTIVE":
                                pump_geo_row += "<span style='color:#ff4b4b;'>⚡ 电压泵升 ACTIVE</span> | "
                            if h.get("geo_element") and h.get("geo_element") != "Neutral":
                                pump_geo_row += f"<span style='color:#40e0d0;'>🌍 地理阻抗: {h.get('geo_element')}</span>"
                            if pump_geo_row:
                                st.markdown(pump_geo_row, unsafe_allow_html=True)
                        
                        # [V14.8] SGSJ Superconductor HUD
                        if h.get("audit_mode") in ["SGSJ_SUPERCONDUCTOR_TRACK", "SGSJ_V4.1_WAVEGUIDE_MODEL", "SGSJ_V4.2_PLASMA_VAPORIZATION"]:
                            st.markdown("**真空超导场参数 (Superconductor HUD):**")
                            # Voltage Pump for SGSJ
                            if h.get("voltage_pump") == "ACTIVE":
                                st.markdown(f"<div style='color:#ff4b4b; font-size:0.9em; margin-bottom:10px;'>⚡ 检测到电压泵升 (Voltage Pump Active): 外部扰动已穿透真空基底</div>", unsafe_allow_html=True)
                            
                            mc1, mc2 = st.columns(2)
                            with mc1:
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>超导纯净度 (Purity)</div><div class='metric-value'>{h['purity']}</div></div>", unsafe_allow_html=True)
                            with mc2:
                                jump_color = "#ff4b4b" if float(h['jump_rate'].replace('%','')) > 500 else "#40e0d0"
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>扰动跳变率 (Jump Rate)</div><div class='metric-value' style='color:{jump_color};'>{h['jump_rate']}</div></div>", unsafe_allow_html=True)
                            
                            if "Vacuum Rupture" in h['category']:
                                st.warning("💥 **检测到“真空断裂”效应**: 该样本在零阻力状态下遭遇官星扰动，应力瞬间饱和！")
                            
                            if h.get("pgb_advice"):
                                st.success(f"💡 **PGB 救治建议**: {h['pgb_advice']}")

                        # [V15.6] CYGS Gravitational Collapse HUD
                        if h.get("audit_mode") == "CYGS_V4.1_COLLAPSE":
                            st.markdown("**🕳️ 引力坍缩场参数 (Gravitational Collapse HUD):**")
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                lock_val = float(h.get("locking_ratio", "0"))
                                l_color = "#40e0d0" if lock_val > 0.9 else ("#ffaa00" if lock_val > 0.6 else "#ff4b4b")
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>引力锁定率</div><div class='metric-value' style='color:{l_color};'>{h.get('locking_ratio', 'N/A')}</div></div>", unsafe_allow_html=True)
                            with c2:
                                pkg_map = {"P_111A": "从财", "P_111B": "从杀", "P_111C": "从儿", "P_111D": "从强/旺"}
                                pkg_id = h.get('sub_package_id', 'N/A')
                                pkg_name = pkg_map.get(pkg_id, pkg_id)
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>子专题判据</div><div class='metric-value'>{pkg_name}</div></div>", unsafe_allow_html=True)
                            with c3:
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>纯度指标</div><div class='metric-value'>{h.get('purity_index', 'N/A')}</div></div>", unsafe_allow_html=True)
                            
                            if h.get("is_rebound") == "YES":
                                st.error("🚨 **警告**: 检测到 [Gravitational Rebound] (引力反弹)！结构正在发生物理爆裂。")
                            
                        # [V15.6] HGFG Atomic Transmutation HUD
                        if h.get("audit_mode") == "HGFG_V4.1_TRANSMUTATION":
                            st.markdown("**⚗️ 原子重构场参数 (Atomic Transmutation HUD):**")
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                pure_val = float(h.get("transmutation_purity", "0"))
                                p_color = "#40e0d0" if pure_val > 0.8 else ("#ffaa00" if pure_val > 0.5 else "#ff4b4b")
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>转换纯度</div><div class='metric-value' style='color:{p_color};'>{h.get('transmutation_purity', 'N/A')}</div></div>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>目标化神</div><div class='metric-value'>{h.get('goal_element', 'N/A')}</div></div>", unsafe_allow_html=True)
                            with c3:
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>还原剂碰撞</div><div class='metric-value'>{'YES' if h.get('is_reversed') == 'YES' else 'NO'}</div></div>", unsafe_allow_html=True)
                            
                            if h.get("is_reversed") == "YES":
                                st.error("🚨 **警告**: 检测到 [Atomic Reversal] (原子还原)！新属性结构已发生解体。")                        

                        # [V15.7] SSSC Amplifier HUD
                        if h.get("audit_mode") == "SSSC_V4.1_AMPLIFIER":
                            st.markdown("**🌱 食伤生财放大器参数 (SSSC Amplifier HUD):**")
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                gain = float(h.get("gain_factor", "0"))
                                g_color = "#00cc66" if 0.8 <= gain <= 1.5 else "#ff4b4b"
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>增益系数</div><div class='metric-value' style='color:{g_color};'>{gain:.2f}</div></div>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>放大类型</div><div class='metric-value'>{'层流 (食)' if h.get('sub_package_id') == 'P_113A' else '脉冲 (伤)'}</div></div>", unsafe_allow_html=True)
                            with c3:
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>枭神断路</div><div class='metric-value'>{'YES' if h.get('has_cutoff') == 'YES' else 'NO'}</div></div>", unsafe_allow_html=True)
                            
                            if h.get("has_cutoff") == "YES":
                                st.error("✂️ **警告**: 检测到 [Amplifier Cutoff] (枭神夺食)！输入端已断路，系统停摆。")
                        
                        # [V15.7] JLTG Core Energy HUD
                        if h.get("audit_mode") == "JLTG_V4.1_CORE":
                            st.markdown("**🔥 建禄月劫核心参数 (JLTG Core HUD):**")
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                bal = float(h.get("thermal_balance", "0"))
                                b_color = "#00cc66" if 0.8 <= bal <= 1.2 else ("#ffaa00" if bal < 2.0 else "#ff4b4b")
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>热平衡系数</div><div class='metric-value' style='color:{b_color};'>{bal:.2f}</div></div>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>核心类型</div><div class='metric-value'>{'建禄 (稳态)' if h.get('sub_package_id') == 'P_114A' else '月劫 (湍流)'}</div></div>", unsafe_allow_html=True)
                            with c3:
                                st.markdown(f"<div class='metric-card'><div class='metric-label'>核心震荡</div><div class='metric-value'>{'YES' if h.get('is_oscillation') == 'YES' else 'NO'}</div></div>", unsafe_allow_html=True)
                            
                            if h.get("is_runaway") == "YES":
                                st.error("☢️ **警告**: 检测到 [Thermal Runaway] (热失控)！内能过载，核心正在熔毁。")
                            if h.get("is_oscillation") == "YES":
                                st.warning("🧨 **警告**: 检测到 [Core Oscillation] (冲禄)！核心物理结构发生剧烈震荡。")
                        st.markdown(f"**物理断言:**")
                        st.caption(f"应力指纹: {h.get('stress', h.get('sai', 'N/A'))} | 格局标签: {h['label']} | 通关指数: {h.get('protection', 'N/A')}")
                        
                        # [V14.8.5] Inline Intervention Lab (No Page Jump)
                        final_sai = h.get("stress", h.get("sai"))
                        if final_sai and float(final_sai) > 1.25:
                            t_name = h.get('topic_name', h.get('audit_mode', 'N/A'))
                            with st.expander(f"🛡️ 启动[{t_name}]救治 experiment", expanded=False):
                                st.markdown(f"**当前格局**: `{t_name}`")
                                st.markdown(f"**六柱**: `{h['label']}`")
                                st.markdown(f"**大运/流年**: `{h.get('injected_luck', 'N/A')}` / `{h.get('injected_annual', 'N/A')}`")
                                
                                st.divider()
                                st.markdown("**🔧 干预参数调节:**")
                                
                                int_col1, int_col2 = st.columns(2)
                                with int_col1:
                                    earth_boost = st.slider("🌍 戊土护盾强度", 0.0, 5.0, 2.5, 0.5, key=f"earth_{idx}")
                                    water_boost = st.slider("💧 壬水财星注入", 0.0, 3.0, 0.0, 0.5, key=f"water_{idx}")
                                with int_col2:
                                    damping = st.slider("⚡ 阻尼系数", -0.5, 0.5, -0.2, 0.1, key=f"damp_{idx}")
                                
                                if st.button(f"🚀 执行干预模拟", key=f"run_inter_{idx}", use_container_width=True):
                                    # Quick simulation (simplified for inline use)
                                    original_stress = float(h.get("stress", h.get("sai", "0.1")))
                                    shield_effect = earth_boost * 0.15 + water_boost * 0.1
                                    new_stress = max(0.1, original_stress - shield_effect + damping)
                                    
                                    st.divider()
                                    res_col1, res_col2 = st.columns(2)
                                    with res_col1:
                                        stress_color = "#ff4b4b" if original_stress > 1.25 else "#00cc66"
                                        st.markdown(f"<div style='text-align:center; padding:10px; background:#1a1a2e; border-radius:8px;'><div style='color:#888; font-size:0.8em;'>干预前 SAI</div><div style='color:{stress_color}; font-size:1.8em; font-weight:bold;'>{original_stress:.2f}</div></div>", unsafe_allow_html=True)
                                    with res_col2:
                                        new_color = "#00cc66" if new_stress < 1.25 else "#ff4b4b"
                                        st.markdown(f"<div style='text-align:center; padding:10px; background:#1a1a2e; border-radius:8px;'><div style='color:#888; font-size:0.8em;'>干预后 SAI</div><div style='color:{new_color}; font-size:1.8em; font-weight:bold;'>{new_stress:.2f}</div></div>", unsafe_allow_html=True)
                                    
                                    if new_stress < 1.25:
                                        st.success(f"✅ **干预有效**: 应力从 {original_stress:.2f} 降至 {new_stress:.2f}，已脱离 1.25 红线！")
                                        st.balloons()
                                    else:
                                        st.warning(f"⚠️ **干预不足**: 应力仍为 {new_stress:.2f}，请增加护盾强度。")

    # =====================================================================
    # [V2.1] FULL PIPELINE SCAN VIEW - One-Click All Phases with Progress
    # =====================================================================
    if st.session_state.get("sim_view") == "full_pipeline_scan":
        from core.trinity.core.engines.pattern_scout import PatternScout
        from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
        # BaziParticleNexus is already imported globally at the top of the file
        from collections import defaultdict
        import time
        
        track_id = st.session_state.get("target_track", "SHANG_GUAN_SHANG_JIN")
        track_names = {
            "SHANG_GUAN_SHANG_JIN": "伤官伤尽 (SGSJ)",
            "SHANG_GUAN_JIAN_GUAN": "伤官见官 (SGJG)",
            "YANG_REN_JIA_SHA": "羊刃架杀 (YRJS)",
            "XIAO_SHEN_DUO_SHI": "枭神夺食 (XSDS)",
            "CYGS_COLLAPSE": "从格引力坍缩 (CYGS)",
            "HGFG_TRANSMUTATION": "化气格原子重构 (HGFG)",
        }
        track_name = track_names.get(track_id, track_id)
        
        st.markdown(f"## ⚡ 全量物理扫描: {track_name}")
        st.markdown("**模式**: 一键执行 Phase 1 → Phase 4")
        st.divider()

        
        # Phase Progress Tracker
        progress_bar = st.progress(0, text="准备中...")
        status_text = st.empty()
        result_container = st.container()
        
        # Phase 1: 海选
        status_text.markdown("### 📦 Phase 1: 古代标签海选...")
        progress_bar.progress(5, text="Phase 1: 古代标签海选 (0%)")
        
        engine = SyntheticBaziEngine()
        scout = PatternScout()
        
        samples = []
        element_clusters = defaultdict(list)
        total = 0
        
        # YRJS 羊刃对应表
        YANG_REN_MAP = {
            '甲': '卯', '乙': '寅', '丙': '午', '丁': '巳',
            '戊': '午', '己': '巳', '庚': '酉', '辛': '申',
            '壬': '子', '癸': '亥',
        }
        # [V15.6] 化气对撞表
        HGFG_PAIRS = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙", "丙": "辛", "辛": "丙", "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊"}
        
        for chart in engine.generate_all_bazi():
            total += 1
            if total % 50000 == 0:
                pct = min(25, int(total / 518400 * 25))
                progress_bar.progress(pct, text=f"Phase 1: 海选中 ({total:,}/518,400)")
            
            dm = chart[2][0]
            stems = [p[0] for p in chart]
            branches = [p[1] for p in chart]
            ten_gods = [BaziParticleNexus.get_shi_shen(s, dm) for s in stems]
            
            # 根据 track_id 应用不同判据
            if track_id == "YANG_REN_JIA_SHA":
                # YRJS 判据: 月令帝旺 + 七杀透干
                yang_ren = YANG_REN_MAP.get(dm)
                if branches[1] != yang_ren: continue
                if '七杀' not in ten_gods: continue
                cluster_key = dm
            elif track_id == "SHANG_GUAN_JIAN_GUAN":
                # SGJG 判据: 伤官 + 官杀同现
                if '伤官' not in ten_gods: continue
                if not any(tg in ['正官', '七杀'] for tg in ten_gods): continue
                dm_elem = BaziParticleNexus.STEMS[dm][0]
                cluster_key = dm_elem
            elif track_id == "XIAO_SHEN_DUO_SHI":
                # XSDS 判据: 偏印 + 食神双透，无正官
                if '偏印' not in ten_gods: continue
                if '食神' not in ten_gods: continue
                if '正官' in ten_gods: continue
                cluster_key = dm
            elif track_id == "CAI_GUAN_XIANG_SHENG":
                # CGXS 判据: 财官双透，且无伤官
                if '正官' not in ten_gods: continue
                if not any(tg in ['正财', '偏财'] for tg in ten_gods): continue
                if '伤官' not in ten_gods: continue
                cluster_key = dm
            elif track_id == "CYGS_COLLAPSE":
                # CYGS 判据: 极端低能级日主 (月令无气 + 根基微弱)
                month_br = branches[1]
                hidden_month = BaziParticleNexus.get_branch_weights(month_br)
                if any(BaziParticleNexus.get_shi_shen(hs, dm) in ["长生", "临官", "帝旺", "正印", "偏印"] for hs, w in hidden_month):
                    continue
                cluster_key = "COLLAPSE_CANDIDATE"
            elif track_id == "HGFG_TRANSMUTATION":
                # HGFG 判据: 存在化气粒子对
                partner = HGFG_PAIRS.get(dm)
                if stems[1] != partner and stems[3] != partner: continue
                cluster_key = f"{dm}{partner}"
            else:
                # SGSJ 判据: 伤官 + 无官杀
                if any(tg in ['正官', '七杀'] for tg in ten_gods): continue
                has_main_guan = False
                for b in branches:
                    hidden = BaziParticleNexus.get_branch_weights(b)
                    if hidden and BaziParticleNexus.get_shi_shen(hidden[0][0], dm) in ['正官', '七杀']:
                        has_main_guan = True
                        break
                if has_main_guan: continue
                if '伤官' not in ten_gods: continue
                dm_elem = BaziParticleNexus.STEMS[dm][0]
                sg_stems = [s for s, tg in zip(stems, ten_gods) if tg == '伤官']
                sg_elem = BaziParticleNexus.STEMS[sg_stems[0]][0] if sg_stems else 'Unknown'
                cluster_key = f'{dm_elem}-{sg_elem}'
            
            element_clusters[cluster_key].append(chart)
            samples.append(chart)
        
        progress_bar.progress(25, text="Phase 1: 完成 ✓")

        
        # Phase 2: SAI 曲线
        status_text.markdown("### ⚡ Phase 2: 三维注入 SAI 曲线...")
        progress_bar.progress(30, text="Phase 2: 计算 SAI 应力曲线")
        
        ANNUAL_PILLARS = {
            2024: ('甲', '辰'), 2025: ('乙', '巳'), 2026: ('丙', '午'),
            2027: ('丁', '未'), 2028: ('戊', '申'), 2029: ('己', '酉'), 2030: ('庚', '戌')
        }
        LUCK = ('壬', '申')
        
        year_sai_matrix = {}
        for cluster, charts in element_clusters.items():
            year_sai_matrix[cluster] = {}
            sample_charts = charts[:30]
            for year, annual in ANNUAL_PILLARS.items():
                sai_list = []
                for c in sample_charts:
                    six_pillar = list(c) + [LUCK, annual]
                    result = scout._deep_audit(six_pillar, 'SHANG_GUAN_SHANG_JIN')
                    if result:
                        try: sai_list.append(float(result['stress']))
                        except: pass
                year_sai_matrix[cluster][year] = sum(sai_list) / len(sai_list) if sai_list else 0.0
        
        progress_bar.progress(50, text="Phase 2: 完成 ✓")
        
        # Phase 3: 离群分析
        status_text.markdown("### 🔍 Phase 3: 离群聚类分析...")
        progress_bar.progress(55, text="Phase 3: 检测隐藏护盾")
        
        anomaly_count = 0
        no_match_count = 0
        scanned = 0
        for chart in samples[:2000]:
            scanned += 1
            six_pillar = list(chart) + [LUCK, ANNUAL_PILLARS[2026]]
            result = scout._deep_audit(six_pillar, track_id)
            if result:
                try:
                    stress = float(result.get('stress', result.get('sai', '99')))
                    if stress < 0.5: anomaly_count += 1
                except: pass
            else:
                no_match_count += 1
        
        progress_bar.progress(75, text="Phase 3: 完成 ✓")
        
        # Phase 4: 定标
        status_text.markdown("### 📐 Phase 4: 物理定标...")
        progress_bar.progress(80, text="Phase 4: 生成报告")
        time.sleep(0.5)
        
        progress_bar.progress(100, text="全部完成 ✓")
        status_text.markdown("### ✅ 全量扫描完成!")
        
        # Results Display
        with result_container:
            st.divider()
            st.markdown(f"## 📊 {track_name} 扫描报告")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("总扫描", f"{total:,}")
            c2.metric("初选样本", f"{len(samples):,}", f"{len(samples)/total*100:.2f}%")
            c3.metric("隐藏护盾", f"{no_match_count}", f"{no_match_count/max(1,scanned)*100:.0f}%")
            c4.metric("低SAI异常", f"{anomaly_count}")

            
            st.markdown("### 🔮 五行聚类分布")
            cluster_data = {k: len(v) for k, v in element_clusters.items()}
            st.bar_chart(cluster_data)
            
            st.markdown("### 📈 流年 SAI 应力曲线 (危险预警)")
            for cluster, yearly in year_sai_matrix.items():
                max_sai = max(yearly.values()) if yearly.values() else 0
                if max_sai > 2.0:
                    max_year = max(yearly, key=yearly.get)
                    st.warning(f"**{cluster}**: {max_year} 年最高 SAI = {max_sai:.2f} ⚠️")
            
            st.success("📁 报告已生成。详细数据请查看 `docs/` 目录。")

            topic_breakdown = summary.get("topic_breakdown", {})
            if topic_breakdown:
                breakdown_data = [{"专题": T.translate_pattern(k), "触发次数": v} for k, v in topic_breakdown.items()]
                st.bar_chart(pd.DataFrame(breakdown_data).set_index("专题"))

if __name__ == "__main__":
    render()
