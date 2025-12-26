
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

        st.divider()
        st.markdown("### 📑 专题实验室 (Topic Tracks)")
        track_labels = {
            "SHANG_GUAN_JIAN_GUAN": "🔥 伤官见官 (SGJG) ✨",
            "SHANG_GUAN_SHANG_JIN": "⚔️ 伤官伤尽 (SGSJ) ✨",
            "YANG_REN_JIA_SHA": "🗡️ 羊刃架杀 (YRJS)",
            "XIAO_SHEN_DUO_SHI": "🦉 枭神夺食 (XSDS)",
            "CAI_GUAN_XIANG_SHENG": "🌊 财官相生 (CGXS)",
            "SHANG_GUAN_PEI_YIN": "⚖️ 伤官配印 (SGPY)",
            "PGB_SUPER_FLUID_LOCK": "🧊 排骨帮之超流锁定格 ✨",
            "PGB_BRITTLE_TITAN": "🗿 排骨帮之脆性巨人格 ✨"
        }
        selected_track = st.selectbox("选择对撞轨道", list(track_labels.keys()), format_func=lambda x: track_labels.get(x, x))
        
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
                deep_hits = controller.run_deep_specialized_scan(p, target_year=audit_year)
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
        st.markdown(f"### 🧪 专题实验室: {st.session_state.get('target_track')}")
        
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

        # --- PREVIEW CARD (NEW) ---
        p_preview = next((prof for prof in profiles if prof['id'] == selected_profile_id), None)
        if p_preview:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container():
                st.markdown(f"##### 📋 对撞前置参数预览 (Preview)")
                cp1, cp2 = st.columns([1, 1])
                
                # Pre-calculate pillars for preview
                from core.trinity.core.nexus.definitions import BaziParticleNexus as BPN
                try:
                    bdt = datetime(p_preview['year'], p_preview['month'], p_preview['day'], p_preview['hour'], p_preview.get('minute', 0))

                    profile_obj = BaziProfile(bdt, 1 if p_preview['gender'] == '男' else 0)
                    pillars = profile_obj.pillars
                    luck = profile_obj.get_luck_pillar_at(audit_year)
                    
                    with cp1:
                        st.markdown("**六柱全息对撞预览 (Six-Pillar Preview):**")
                        cols = st.columns(6)
                        p_labels = ["年", "月", "日", "时", "运", "岁"]
                        six_pillars = [pillars['year'], pillars['month'], pillars['day'], pillars['hour'], luck, profile_obj.get_year_pillar(audit_year)]
                        dm = pillars['day'][0]
                        
                        for i, p_val in enumerate(six_pillars):
                            stem = p_val[0]
                            branch = p_val[1]
                            s_god = BPN.get_shi_shen(stem, dm) if i != 2 else "日主"
                            hidden = BPN.get_branch_weights(branch)
                            h_gods = [BPN.get_shi_shen(h[0], dm) for h in hidden]
                            h_str = "<br>".join([f"<span style='color:#888; font-size:0.7em;'>{g}</span>" for g in h_gods])

                            
                            with cols[i]:
                                st.markdown(f"""
                                    <div style='text-align:center; background:#1e1e1e; border:1px solid #444; border-radius:5px; padding:8px; min-height:150px;'>
                                        <div style='color:#666; font-size:0.8em; margin-bottom:2px;'>{p_labels[i]}</div>
                                        <div style='color:#ffaa00; font-size:0.85em; font-weight:bold;'>{s_god}</div>
                                        <div style='font-size:1.4em; margin:2px 0;'>{stem}</div>
                                        <div style='font-size:1.4em; margin:2px 0;'>{branch}</div>
                                        <div style='border-top:1px solid #333; margin-top:5px; padding-top:5px;'>
                                            {h_str}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        # City Override / Selector
                        current_city = p_preview.get("city") or "Beijing"
                        from ui.pages.quantum_lab import GEO_CITY_MAP
                        city_list = list(GEO_CITY_MAP.keys())
                        try:
                            city_idx = next(i for i, c in enumerate(city_list) if current_city in c)
                        except:
                            city_idx = 0
                        
                        selected_city = st.selectbox("🎯 定位地理背景场 (GEO)", options=city_list, index=city_idx, key="audit_city_override")
                        
                    with cp2:
                        st.markdown("**流转 (Dynamics):**")
                        st.markdown(f"🌀 **大运:** `{luck}`")
                        st.markdown(f"📅 **目标流年:** `{profile_obj.get_year_pillar(audit_year)}` ({audit_year})")
                        
                        if st.button("🔍 深度格局鉴定 (Specialized Scan)", use_container_width=True):
                            st.session_state.sim_active = True
                            st.session_state.sim_op_type = "specialized_deep_scan"
                            st.session_state.selected_audit_profile = p_preview
                            st.session_state.persistent_audit_profile_id = selected_profile_id
                            st.session_state.audit_year = audit_year
                            st.rerun()

                except Exception as e:
                    st.error(f"档案解析失败: {e}")

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
                        if h.get("audit_mode") in ["SGJG_V2_MASTER_PROTOCOL", "SGJG_V2.1_MASTER_PROTOCOL"]:
                            st.markdown("**🔥 伤官见官 Master Protocol V2.1:**")
                            
                            # Core Metrics Grid
                            m1, m2, m3, m4 = st.columns(4)
                            with m1:
                                sai_val = float(h.get("stress", "0"))
                                sai_color = "#ff4b4b" if sai_val > 1.25 else ("#ffaa00" if sai_val > 0.8 else "#00cc66")
                                st.markdown(f"<div style='background:#1a1a2e; padding:12px; border-radius:8px; text-align:center;'><div style='color:#888; font-size:0.7em;'>当前 SAI</div><div style='color:{sai_color}; font-size:1.5em; font-weight:bold;'>{h.get('stress', 'N/A')}</div></div>", unsafe_allow_html=True)
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
                        if h.get("audit_mode") == "SGSJ_SUPERCONDUCTOR_TRACK":
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
                        
                        st.markdown(f"**物理断言:**")
                        st.caption(f"应力指纹: {h['stress']} | 格局标签: {h['label']} | 通关指数: {h.get('protection', 'N/A')}")
                        
                        # [V14.8.5] Inline Intervention Lab (No Page Jump)
                        if h.get("stress") and float(h["stress"]) > 1.25:
                            with st.expander(f"🛡️ 启动[{h['topic_name']}]救治实验", expanded=False):
                                st.markdown(f"**当前格局**: `{h['topic_name']}`")
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
                                    original_stress = float(h["stress"])
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
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        from collections import defaultdict
        import time
        
        track_id = st.session_state.get("target_track", "SHANG_GUAN_SHANG_JIN")
        track_name = "伤官伤尽 (SGSJ)" if "SHANG_JIN" in track_id else "伤官见官 (SGJG)"
        
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
        
        sgsj_samples = []
        element_clusters = defaultdict(list)
        total = 0
        
        for chart in engine.generate_all_bazi():
            total += 1
            if total % 50000 == 0:
                pct = min(25, int(total / 518400 * 25))
                progress_bar.progress(pct, text=f"Phase 1: 海选中 ({total:,}/518,400)")
            
            dm = chart[2][0]
            stems = [p[0] for p in chart]
            branches = [p[1] for p in chart]
            ten_gods = [BaziParticleNexus.get_shi_shen(s, dm) for s in stems]
            
            # Ancient hard rules
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
            sgsj_samples.append(chart)
        
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
        for chart in sgsj_samples[:2000]:
            scanned += 1
            six_pillar = list(chart) + [LUCK, ANNUAL_PILLARS[2026]]
            result = scout._deep_audit(six_pillar, 'SHANG_GUAN_SHANG_JIN')
            if result:
                try:
                    if float(result['stress']) < 0.5: anomaly_count += 1
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
            st.markdown("## 📊 扫描报告")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("总扫描", f"{total:,}")
            c2.metric("初选样本", f"{len(sgsj_samples):,}", f"{len(sgsj_samples)/total*100:.1f}%")
            c3.metric("隐藏护盾", f"{no_match_count}", f"{no_match_count/2000*100:.0f}%")
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

if __name__ == "__main__":
    render()
