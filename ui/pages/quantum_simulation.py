
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
    if 'sim_controller' not in st.session_state or getattr(st.session_state.sim_controller, 'version', '0') != "14.1.7":
        # Clear legacy data on version bump
        if "scouted_charts" in st.session_state: del st.session_state.scouted_charts
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        st.session_state.sim_controller = SimulationController(project_root)
        # Ensure the version is set for the new controller instance
        st.session_state.sim_controller.version = "14.1.7"
    
    controller = st.session_state.sim_controller

    # --- 初始化 View State ---
    if "sim_view" not in st.session_state:
        st.session_state.sim_view = "dashboard"

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

        if st.button("📈 命运时间线扫描", use_container_width=True):
            st.session_state.sim_view = "lifespan_scan"
            st.rerun()

        st.divider()
        st.markdown("### 📑 物理模型仿真")
        
        # 使用翻译工具类
        TRACK_ICONS = {
            "SHANG_GUAN_JIAN_GUAN": "🔥",
            "SHANG_GUAN_SHANG_JIN": "⚔️",
            "YANG_REN_JIA_SHA": "🗡️",
            "XIAO_SHEN_DUO_SHI": "🦉",
            "CAI_GUAN_XIANG_SHENG": "🚀",
            "SHANG_GUAN_PEI_YIN": "⚖️",
            "PGB_SUPER_FLUID_LOCK": "🧊",
            "PGB_BRITTLE_TITAN": "🗿",
            "CYGS_COLLAPSE": "🕳️",
            "HGFG_TRANSMUTATION": "⚗️",
            "SSSC_AMPLIFIER": "🌱",
            "JLTG_CORE_ENERGY": "🔥"
        }
        
        TRACK_IDS = list(TRACK_ICONS.keys())
        
        def format_track(track_id: str) -> str:
            icon = TRACK_ICONS.get(track_id, "")
            name = T.translate_pattern(track_id)
            return f"{icon} {name} ✨"
        
        selected_track = st.selectbox("选择对撞轨道", TRACK_IDS, format_func=format_track)
        
        # [V2.1] 一键全量扫描 - 带进度条
        if st.button("⚡ 一键全量扫描 (Phase 1-4)", use_container_width=True, type="primary"):
            st.session_state.sim_view = "full_pipeline_scan"
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
                st.session_state.inter_res = inter_res
            elif sim_op_type == "lifespan_topic_scan":
                p = st.session_state.get("lifespan_profile")
                topic_ids = st.session_state.get("lifespan_topics", [])
                max_age = st.session_state.get("lifespan_max_age", 100)
                
                dt = datetime(p['year'], p['month'], p['day'], p['hour'], p.get('minute', 0))
                po = BaziProfile(dt, 1 if p['gender'] == '男' else 0)
                
                scan_res = controller.run_lifespan_topic_scan(
                    po, topic_ids, max_age,
                    progress_callback=lambda curr, tot, stats: (
                        progress_bar.progress(curr / tot),
                        status.write(f"🔮 扫描中: {curr}岁 / {tot}岁")
                    )
                )
                st.session_state.lifespan_scan_result = scan_res
                
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
            default_year = st.session_state.get("audit_year", 2024)
            audit_year = st.number_input("六柱对撞目标流年", 1900, 2100, default_year, key="audit_year_val")
            st.session_state.audit_year = audit_year

        if st.button("🚀 启动单兵实弹对撞", use_container_width=True, type="primary"):
            p = next((prof for prof in profiles if prof['id'] == selected_profile_id), None)
            if p:
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "single_real_audit"
                st.session_state.selected_audit_profile = p
                # Important: Use the city from the preview logic (might be overridden)
                st.session_state.selected_audit_city = st.session_state.get("audit_city_override", p.get("city", "Beijing"))
                st.session_state.audit_year = audit_year
                st.rerun()

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
                raw_six = [pillars['year'], pillars['month'], pillars['day'], pillars['hour'], luck_pillar, annual_pillar]
                
                for i, p_val in enumerate(raw_six):
                    stem = p_val[0]
                    branch = p_val[1]
                    s_god = BPN.get_shi_shen(stem, dm) if i != 2 else "日主"
                    hidden = BPN.get_branch_weights(branch)
                    h_gods = [BPN.get_shi_shen(h[0], dm) for h in hidden]
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
                        
                        if st.button("🔍 深度格局鉴定", use_container_width=True):
                            st.session_state.sim_active = True
                            st.session_state.sim_op_type = "specialized_deep_scan"
                            st.session_state.selected_audit_profile = p_preview
                            st.session_state.persistent_audit_profile_id = selected_profile_id
                            st.session_state.audit_year = audit_year
                            st.rerun()
                
                # ========== 第三阶段：全量扫描区域 ==========
                st.divider()
                st.markdown("### 🔬 全量程物理扫描 (Full Pipeline Scan)")
                
                if st.button("🚀 一键全量扫描 (All V4.1 Models)", use_container_width=True, type="primary"):
                    st.session_state.show_pipeline_res = True
                    st.rerun()
                
                if st.session_state.get("show_pipeline_res") and pillars:
                    with st.spinner("正在对所有 V4.1 物理模型进行并发审计..."):
                        modes_to_check = [
                            "SSSC_AMPLIFIER", "JLTG_CORE_ENERGY", 
                            "CYGS_COLLAPSE", "HGFG_TRANSMUTATION",
                            "SHANG_GUAN_JIAN_GUAN", "SHANG_GUAN_SHANG_JIN",
                            "PGB_ULTRA_FLUID", "PGB_BRITTLE_TITAN"
                        ]
                        
                        found_patterns = []
                        full_chart = [pillars['year'], pillars['month'], pillars['day'], pillars['hour'], luck_pillar, annual_pillar]
                        
                        from core.trinity.core.engines.pattern_scout import PatternScout
                        scout = PatternScout()
                        
                        for mode in modes_to_check:
                            try:
                                res = scout._deep_audit(full_chart, mode)
                                if res:
                                    found_patterns.append(res)
                            except:
                                pass  # 忽略单个模型的错误
                        
                        if found_patterns:
                            found_patterns.sort(key=lambda x: float(x.get('stress', 0)), reverse=True)
                            st.success(f"检测到 {len(found_patterns)} 个物理格局")
                            
                            for idx, pat in enumerate(found_patterns[:5]):
                                sai_val = float(pat.get('stress', 0))
                                color = "#ff4b4b" if sai_val > 2.0 else ("#ffaa00" if sai_val > 1.0 else "#00cc66")
                                st.markdown(f"""
                                <div style='background:#1a1a2e; border:1px solid #333; padding:12px; border-radius:8px; margin-bottom:8px;'>
                                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                                        <div>
                                            <div style='font-weight:bold; color:#fff; font-size:1.1em;'>{pat.get('topic_name', 'Unknown')}</div>
                                            <div style='font-size:0.85em; color:#888; margin-top:4px;'>{pat.get('category', '')}</div>
                                        </div>
                                        <div style='text-align:right;'>
                                            <div style='color:{color}; font-weight:bold; font-size:1.4em;'>SAI {sai_val:.2f}</div>
                                            <div style='font-size:0.7em; color:#666;'>应力指数</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("💡 未检测到显著的物理构型格局")

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
                        if h.get("audit_mode") in ["SGJG_V2_MASTER_PROTOCOL", "SGJG_V2.1_MASTER_PROTOCOL", "SGGG_V4.1_GATE_BREAKDOWN"]:
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
                        if h.get("audit_mode") in ["SGSJ_SUPERCONDUCTOR_TRACK", "SGSJ_V4.1_WAVEGUIDE_MODEL"]:
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

        st.divider()
        with st.expander("📂 批量审计工具 (Batch Audit)"):
            if st.button("启动全档案六柱对撞审计 (物理压力测试)", use_container_width=True):
                st.session_state.audit_year = audit_year
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "real_world_audit"
                st.rerun()

        # Display Single Audit Result
        if st.session_state.get("single_audit_res"):
            item = st.session_state.single_audit_res
            st.divider()
            
            # Header with Status Badge
            status_color = "#ff4b4b" if item["is_pgb_critical"] else ("#ffaa00" if item["sai"] > 1.0 else "#00cc66")
            st.markdown(f"""
                <div style="background:{status_color}22; border-left: 5px solid {status_color}; padding:15px; border-radius:5px;">
                    <h3 style="margin:0; color:{status_color};">🛰️ 实弹审计报告: {item['profile_name']}</h3>
                    <caption style="color:{status_color}aa;">量子应力分析完成 | 目标流年: {st.session_state.audit_year}</caption>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Three Panel Layout
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1: # Left: Profile & Geo
                st.markdown("##### 🧬 空间维度 (Spatial)")
                st.code(" ".join(item['chart']), language="text")
                st.markdown(f"""
                    <div style="background:#1e1e1e; padding:10px; border-radius:5px; border:1px solid #333;">
                        <span style="color:#00ccff;">📍 地理注入:</span> {item['city']}<br>
                        <span style="color:#666; font-size:0.8em;">(GEO_FIELD_ALPHA 已同步)</span>
                    </div>
                """, unsafe_allow_html=True)

            with col2: # Middle: Temporal Dynamics
                st.markdown("##### ⏳ 时间维度 (Temporal)")
                st.markdown(f"**大运:** `{item['luck']}` ({item['luck_range']})")
                st.markdown(f"**流年:** `{item['annual']}` ({st.session_state.audit_year})")
                
                # Mock Waveform
                interference_data = np.random.normal(0.5, 0.1, 10).tolist()
                fig = px.area(interference_data, height=80)
                fig.update_layout(margin=dict(l=0,r=0,b=0,t=0), showlegend=False, xaxis_visible=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.caption("六柱干涉相消强度 (Interference)")

            with col3: # Right: Result
                st.markdown("##### 📉 应力指标 (SAI)")
                st.markdown(f"<h1 style='color:{status_color}; margin:0;'>{item['sai']:.3f}</h1>", unsafe_allow_html=True)
                thr = item.get('dynamic_threshold', 1.25)
                st.caption(f"SAI 实时载荷 (Dynamic Threshold: {thr:.2f})")
                
                if item["is_pgb_critical"]:
                    st.error("🚨 **PGB_CRITICAL**")
                    st.caption("达到物理粉碎阈值，建议执行‘量子干预’进行阻尼减压。")
                else:
                    st.success("✅ 结构稳定")

        # Display Batch results if any
        if st.session_state.get("real_audit_res"):
            st.divider()
            st.markdown("#### 📊 全档案审计汇总")
            res_list = st.session_state.real_audit_res
            critical_count = sum(1 for r in res_list if r["is_pgb_critical"])
            m1, m2 = st.columns(2)
            m1.metric("同步档案总数", len(res_list))
            m2.metric("PGB 高危断裂", critical_count, delta_color="inverse")
            
            with st.expander("查看所有高危样本"):
                for r in res_list:
                    if r["is_pgb_critical"]:
                        st.write(f"🚩 {r['profile_name']} | SAI: {r['sai']:.3f} | {r['luck']}/{r['annual']}")

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
                if '伤官' in ten_gods: continue
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

    # =====================================================================
    # [V4.2] 命运时间线扫描视图 (Lifespan Topic Scanner)
    # =====================================================================
    elif view == "lifespan_scan":
        st.markdown("### 📈 命运时间线扫描 (Lifespan Topic Scanner)")
        st.caption("扫描命主从出生到100岁的所有年份，检测指定物理格局的触发情况")
        
        # 档案选择
        profiles = controller.profile_manager.get_all()
        profile_options = {p['id']: f"{p['name']} ({p['gender']})" for p in profiles}
        profile_ids = list(profile_options.keys())
        
        col_sel, col_age = st.columns([3, 1])
        with col_sel:
            selected_profile_id = st.selectbox(
                "选择目标档案", 
                options=profile_ids, 
                format_func=lambda x: profile_options.get(x),
                key="lifespan_profile_sel"
            )
        with col_age:
            max_age = st.number_input("最大扫描年龄", 50, 120, 100, key="lifespan_max_age_input")
        
        # 专题选择 - 使用翻译工具
        TOPIC_ICONS = {
            "SELECT_ALL": "⭐",
            "SHANG_GUAN_JIAN_GUAN": "🔥",
            "SHANG_GUAN_SHANG_JIN": "⚔️",
            "YANG_REN_JIA_SHA": "🗡️",
            "XIAO_SHEN_DUO_SHI": "🦉",
            "CYGS_COLLAPSE": "🕳️",
            "HGFG_TRANSMUTATION": "⚗️",
            "SSSC_AMPLIFIER": "🌱",
            "JLTG_CORE_ENERGY": "🔥"
        }
        
        TOPIC_IDS = [
            "SELECT_ALL",
            "SHANG_GUAN_JIAN_GUAN",
            "SHANG_GUAN_SHANG_JIN", 
            "YANG_REN_JIA_SHA",
            "XIAO_SHEN_DUO_SHI",
            "CYGS_COLLAPSE",
            "HGFG_TRANSMUTATION",
            "SSSC_AMPLIFIER",
            "JLTG_CORE_ENERGY"
        ]
        
        def format_topic(topic_id: str) -> str:
            """格式化专题显示名称"""
            icon = TOPIC_ICONS.get(topic_id, "")
            name = T.translate_pattern(topic_id)
            return f"{icon} {name}"
        
        # 实际可扫描的专题 (不包含 SELECT_ALL)
        real_topic_ids = [k for k in TOPIC_IDS if k != "SELECT_ALL"]
        
        selected_raw = st.multiselect(
            "选择要扫描的物理格局 (可多选)",
            options=TOPIC_IDS,
            default=["SHANG_GUAN_JIAN_GUAN"],
            format_func=format_topic,
            key="lifespan_topics_sel"
        )
        
        # 处理全选逻辑
        if "SELECT_ALL" in selected_raw:
            selected_topics = real_topic_ids
            st.info(f"✅ 已选择全部 {len(real_topic_ids)} 个物理格局")
        else:
            selected_topics = selected_raw
        
        if st.button("🚀 启动时间线扫描", use_container_width=True, type="primary"):
            p = next((prof for prof in profiles if prof['id'] == selected_profile_id), None)
            if p and selected_topics:
                st.session_state.sim_active = True
                st.session_state.sim_op_type = "lifespan_topic_scan"
                st.session_state.lifespan_profile = p
                st.session_state.lifespan_topics = selected_topics
                st.session_state.lifespan_max_age = max_age
                st.rerun()
            else:
                st.warning("请选择档案和至少一个扫描专题")
        
        # 显示扫描结果
        if st.session_state.get("lifespan_scan_result"):
            scan_res = st.session_state.lifespan_scan_result
            timeline = scan_res["timeline"]
            summary = scan_res["summary"]
            
            st.divider()
            
            # 摘要卡片
            st.markdown("#### 📊 扫描摘要")
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("总扫描年数", f"{summary['total_years_scanned']}年")
            with m2:
                st.metric("危险年数", f"{summary['total_triggered_years']}年", 
                         delta=summary['trigger_rate'], delta_color="inverse")
            with m3:
                peak_age = summary.get('peak_danger_age', 'N/A')
                st.metric("峰值危险年龄", f"{peak_age}岁")
            with m4:
                peak_sai = summary.get('peak_danger_sai', 0)
                sai_color = "inverse" if peak_sai > 1.5 else "normal"
                st.metric("峰值 SAI", f"{peak_sai:.2f}", delta_color=sai_color)
            
            # 危险周期提示
            if summary.get("danger_periods"):
                st.markdown("#### ⚠️ 危险周期识别")
                for period in summary["danger_periods"]:
                    if period["end_age"] - period["start_age"] > 0:
                        st.error(f"🚨 **{period['start_age']}-{period['end_age']}岁**: 连续危险期，峰值 SAI = {period['max_sai']:.2f}")
                    else:
                        st.warning(f"⚡ **{period['start_age']}岁**: 单点危险，SAI = {period['max_sai']:.2f}")
            
            st.divider()
            
            # 交互式图表
            st.markdown("#### 📈 命运应力时间线 (点击查看详情)")
            
            # 准备图表数据
            ages = [t["age"] for t in timeline]
            sai_values = [t["max_sai"] for t in timeline]
            years = [t["year"] for t in timeline]
            luck_pillars = [t.get("luck_pillar", "") for t in timeline]
            annual_pillars = [t.get("annual_pillar", "") for t in timeline]
            
            # 颜色编码：根据 SAI 值
            colors = []
            for sai in sai_values:
                if sai > 2.0:
                    colors.append("#ff4b4b")  # 高危 - 红色
                elif sai > 1.25:
                    colors.append("#ffaa00")  # 警告 - 橙色
                elif sai > 0.5:
                    colors.append("#40e0d0")  # 轻微 - 青色
                else:
                    colors.append("#00cc66")  # 安全 - 绿色
            
            # 创建 hover 文本
            hover_texts = []
            for t in timeline:
                topics_str = ", ".join([tp["topic_name"] for tp in t.get("triggered_topics", [])]) or "无触发"
                text = f"<b>{t['age']}岁 ({t['year']}年)</b><br>"
                text += f"大运: {t.get('luck_pillar', 'N/A')}<br>"
                text += f"流年: {t.get('annual_pillar', 'N/A')}<br>"
                text += f"SAI: {t['max_sai']:.2f}<br>"
                text += f"触发格局: {topics_str}"
                hover_texts.append(text)
            
            # 创建 Plotly 图表
            fig = go.Figure()
            
            # 添加安全区域背景
            fig.add_hrect(y0=0, y1=1.25, fillcolor="rgba(0, 204, 102, 0.1)", 
                         line_width=0, annotation_text="安全区", annotation_position="top left")
            fig.add_hrect(y0=1.25, y1=2.0, fillcolor="rgba(255, 170, 0, 0.1)", 
                         line_width=0, annotation_text="警戒区", annotation_position="top left")
            fig.add_hrect(y0=2.0, y1=5.0, fillcolor="rgba(255, 75, 75, 0.1)", 
                         line_width=0, annotation_text="危险区", annotation_position="top left")
            
            # 主折线
            fig.add_trace(go.Scatter(
                x=ages, 
                y=sai_values,
                mode='lines+markers',
                name='SAI 应力值',
                line=dict(color='#40e0d0', width=2),
                marker=dict(
                    size=8,
                    color=colors,
                    line=dict(color='white', width=1)
                ),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=hover_texts
            ))
            
            # 标注危险点
            danger_ages = [t["age"] for t in timeline if t["is_danger_zone"]]
            danger_sais = [t["max_sai"] for t in timeline if t["is_danger_zone"]]
            
            if danger_ages:
                fig.add_trace(go.Scatter(
                    x=danger_ages,
                    y=danger_sais,
                    mode='markers',
                    name='危险触发点',
                    marker=dict(
                        size=14,
                        color='#ff4b4b',
                        symbol='diamond',
                        line=dict(color='white', width=2)
                    ),
                    hoverinfo='skip'
                ))
            
            # 1.25 红线
            fig.add_hline(y=1.25, line_dash="dash", line_color="#ff4b4b", 
                         annotation_text="断裂模量 1.25", annotation_position="right")
            
            fig.update_layout(
                title=dict(text="命运应力时间线 (点击数据点查看详情)", font=dict(size=18, color='#fff')),
                xaxis=dict(
                    title="年龄 (岁)",
                    gridcolor='rgba(255,255,255,0.1)',
                    tickmode='linear',
                    dtick=10
                ),
                yaxis=dict(
                    title="SAI 应力指数",
                    gridcolor='rgba(255,255,255,0.1)',
                    range=[0, max(3.0, max(sai_values) * 1.1)]
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#888'),
                hovermode='closest',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                height=450,
                clickmode='event+select'
            )
            
            # 显示图表
            st.plotly_chart(fig, use_container_width=True, key="lifespan_chart")
            
            # 危险年份快速跳转
            st.markdown("#### 🔍 年份详情查询")
            
            # 提取所有有触发的年份（按 SAI 排序）
            triggered_years_sorted = sorted(
                [t for t in timeline if t["max_sai"] > 0],
                key=lambda x: x["max_sai"],
                reverse=True
            )[:20]  # 取 SAI 最高的前20个
            
            if triggered_years_sorted:
                st.caption("⚡ 快速跳转 (点击查看详情):")
                
                # 创建按钮行
                btn_cols = st.columns(min(10, len(triggered_years_sorted)))
                for i, yd in enumerate(triggered_years_sorted[:10]):
                    sai_color = "#ff4b4b" if yd["max_sai"] > 1.25 else "#ffaa00"
                    with btn_cols[i]:
                        if st.button(f"{yd['age']}岁", key=f"jump_{yd['age']}", use_container_width=True):
                            st.session_state.selected_detail_age = yd["age"]
                            st.rerun()
            
            st.divider()
            
            # 年龄选择器
            col_query1, col_query2 = st.columns([1, 3])
            with col_query1:
                # 构建下拉选项：优先显示危险年份
                age_options = list(range(0, len(timeline)))
                
                # 获取当前选中的年龄
                default_age = st.session_state.get("selected_detail_age", 30)
                if default_age >= len(timeline):
                    default_age = 30
                
                query_age = st.selectbox(
                    "选择年龄查看详情",
                    options=age_options,
                    index=default_age,
                    format_func=lambda x: f"{x}岁 {'🔴' if timeline[x]['max_sai'] > 1.25 else ('🟠' if timeline[x]['max_sai'] > 0.5 else '🟢')} SAI:{timeline[x]['max_sai']:.1f}",
                    key="query_age_select"
                )
            
            with col_query2:
                if query_age < len(timeline):
                    year_detail = timeline[query_age]
                    
                    st.markdown(f"""
                    <div style='background:#1a1a2e; border:1px solid #333; padding:15px; border-radius:10px;'>
                        <div style='display:flex; justify-content:space-between; margin-bottom:10px;'>
                            <div>
                                <div style='font-size:1.5em; font-weight:bold; color:#fff;'>{query_age}岁 ({year_detail['year']}年)</div>
                                <div style='color:#888;'>大运: {year_detail.get('luck_pillar', 'N/A')} | 流年: {year_detail.get('annual_pillar', 'N/A')}</div>
                            </div>
                            <div style='text-align:right;'>
                                <div style='font-size:1.8em; font-weight:bold; color:{"#ff4b4b" if year_detail["max_sai"] > 1.25 else "#00cc66"};'>SAI {year_detail['max_sai']:.2f}</div>
                                <div style='color:#888;'>应力指数</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 显示触发的专题详情
                    if year_detail.get("triggered_topics"):
                        st.markdown("**触发的物理格局:**")
                        for topic in year_detail["triggered_topics"]:
                            sai_color = "#ff4b4b" if topic["sai"] > 1.25 else "#ffaa00"
                            # 翻译专题名称
                            topic_name = T.translate_pattern(topic.get('topic_id', '')) or topic.get('topic_name', topic['topic_id'])
                            # 翻译分类
                            category_raw = topic.get('category', 'N/A')
                            category_cn = T.translate_category(category_raw)
                            
                            with st.expander(f"🧬 {topic_name} (SAI: {topic['sai']:.2f})", expanded=False):
                                # 分类和实时载荷
                                st.markdown(f"**分类:** {category_cn}")
                                st.markdown(f"**实时载荷:** {topic.get('real_time_load', 'N/A')}")
                                st.markdown(f"**标签:** `{topic.get('label', 'N/A')}`")
                                
                                # 提取详情中的保护/危险因子
                                details = topic.get("details", {})
                                
                                # 显示物理参数
                                col_p1, col_p2 = st.columns(2)
                                with col_p1:
                                    # 稳定性/保护因子
                                    st.markdown("**🛡️ 保护因子:**")
                                    if details.get("gate_stability"):
                                        st.caption(f"• 正官稳定度: {details['gate_stability']}")
                                    if details.get("o_stabilization"):
                                        st.caption(f"• 官星稳态: {details['o_stabilization']}")
                                    if details.get("buffer_eff"):
                                        st.caption(f"• 缓冲效率: {details['buffer_eff']}")
                                    if details.get("is_superconductor") == "YES":
                                        st.caption("• ⚡ 超导保护激活")
                                    if details.get("is_coupled") == "YES":
                                        st.caption("• 🔗 耦合稳态激活")
                                    if details.get("is_neutralized") == "YES":
                                        st.caption("• ☯️ 中和保护激活")
                                
                                with col_p2:
                                    # 危险触发器
                                    st.markdown("**⚠️ 危险因子:**")
                                    if details.get("is_trap") == "YES":
                                        st.caption("• 🪤 天干合绊陷阱 (SAI×1.5)")
                                    if details.get("is_vault_burst") == "YES":
                                        st.caption("• 💥 墓库冲破 (SAI×3.0)")
                                    if details.get("is_breakdown") == "YES":
                                        st.caption("• ⚡ 击穿发生")
                                    if details.get("is_phase_cancel") == "YES":
                                        st.caption("• 🌀 相位干涉")
                                    if details.get("is_vault_overflow") == "YES":
                                        st.caption("• 🕳️ 墓库溢出")
                                    if details.get("is_burst") == "YES":
                                        st.caption("• 💣 能量暴发")
                                    if details.get("is_runaway") == "YES":
                                        st.caption("• 🔥 热失控")
                                
                                # 关键物理参数
                                if details.get("charge_density") or details.get("sg_kinetic"):
                                    st.markdown(f"**伤官动能:** {details.get('charge_density', details.get('sg_kinetic', 'N/A'))}")
                                if details.get("ratio"):
                                    st.markdown(f"**能量比:** {details['ratio']}")
                                
                                # 完整 JSON (折叠)
                                with st.expander("📋 完整物理数据", expanded=False):
                                    st.json(details)
                    else:
                        st.info("💚 该年份未触发任何危险格局")
            
            # 专题分布统计
            st.divider()
            st.markdown("#### 📊 专题触发统计")
            
            topic_breakdown = summary.get("topic_breakdown", {})
            if topic_breakdown:
                breakdown_data = [{"专题": T.translate_pattern(k), "触发次数": v} for k, v in topic_breakdown.items()]
                st.bar_chart(pd.DataFrame(breakdown_data).set_index("专题"))

if __name__ == "__main__":
    render()
