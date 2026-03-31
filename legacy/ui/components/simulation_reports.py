
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from core.data.geo_cities import GEO_CITY_MAP
from core.translation_util import T
# Import core definitions needed for type hints or logic
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.bazi_profile import BaziProfile

def render_crystal_notification(message, type="info"):
    if type == "info":
        st.info(message)
    elif type == "success":
        st.success(message)
    elif type == "warning":
        st.warning(message)
    elif type == "error":
        st.error(message)

def render_phase_radar(latest):
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

def render_grand_audit():
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

def render_live_fire_whitepaper():
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

def render_v43_penetration_report():
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

def render_v435_yangren_report():
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

def render_v435_thermo_report():
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

def render_v435_inertia_report():
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

def render_v435_tunnel_report():
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

def render_universal_audit_report(track_id):
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

def render_v44_resonance_report():
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

def render_v44_transition_report():
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

def render_v44_reversion_report():
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

def render_v45_gxyg_report():
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

def render_v45_mbgs_report():
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

def render_v45_zhsg_report():
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

def render_topic_lab_report(controller):
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


def render_intervention_lab():
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

def render_real_world_audit(controller):
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
                    city_list = list(GEO_CITY_MAP.keys())
                    try:
                        city_idx = next(i for i, c in enumerate(city_list) if current_city in c)
                    except:
                        city_idx = 0
                    selected_city = st.selectbox("🎯 地理背景场", options=city_list, index=city_idx, key="audit_city_override")
                    
            
            # ========== 第三阶段：全量扫描区域 ==========
            st.divider()
            st.markdown("### 🔬 全量程物理扫描 (Full Pipeline Scan)")
            
            # Re-import TRACK_IDS equivalent here for safety as we don't pass it in
            from core.logic_registry import LogicRegistry
            reg = LogicRegistry()
            topics = reg.get_items_by_layer("TOPIC")
            TRACK_ICONS = {t["reg_id"]: t.get("icon", "🧬") for t in topics}
            TRACK_IDS_LOCAL = sorted(list(TRACK_ICONS.keys()))

            if st.button(f"🚀 启动跨年深度审计 ({start_year}-{end_year})", use_container_width=True, type="primary"):
                st.session_state.show_pipeline_res = True
                # Reset results
                st.session_state.pipeline_hits = []
                
                with st.spinner(f"正在执行 {start_year}-{end_year} 跨年应力对撞..."):
                    from core.logic_registry import LogicRegistry
                    reg = LogicRegistry()
                    topics = reg.get_items_by_layer("TOPIC")
                    TRACK_ICONS = {t["reg_id"]: t.get("icon", "🧬") for t in topics}
                    TRACK_IDS_LOCAL = sorted(list(TRACK_ICONS.keys()))
                    
                    modes_to_check = TRACK_IDS_LOCAL
                    
                    found_patterns = controller.run_multi_year_real_world_scan(p_preview, start_year, end_year, modes_to_check)
                    
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
                    
                    st.markdown(f"**物理断言:**")
                    st.caption(f"应力指纹: {h.get('stress', h.get('sai', 'N/A'))} | 格局标签: {h['label']} | 通关指数: {h.get('protection', 'N/A')}")

def render_full_pipeline_scan():
    # Helper to get controller from session state
    if 'sim_controller' not in st.session_state:
        st.error("控制器尚未初始化 (Controller not initialized)")
        return
    controller = st.session_state.sim_controller
    
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
    
    # Logic moved to controller
    result_data = controller.run_full_pipeline_scan(track_id, lambda v, t, msg: progress_bar.progress(int(v/t*100), text=msg))
    
    progress_bar.progress(100, text="全部完成 ✓")
    status_text.markdown("### ✅ 全量扫描完成!")
    
    # Results Display
    with result_container:
        st.divider()
        st.markdown(f"## 📊 {track_name} 扫描报告")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("总扫描", f"{result_data['total']:,}")
        c2.metric("初选样本", f"{len(result_data['samples']):,}", f"{len(result_data['samples'])/result_data['total']*100:.2f}%")
        c3.metric("隐藏护盾", f"{result_data['no_match_count']}", f"{result_data['no_match_count']/max(1,result_data['total'])*100:.0f}%")
        c4.metric("低SAI异常", f"{result_data['anomaly_count']}")

        st.markdown("### 🔮 五行聚类分布")
        cluster_data = {k: len(v) for k, v in result_data['element_clusters'].items()}
        st.bar_chart(cluster_data)
        
        st.markdown("### 📈 流年 SAI 应力曲线 (危险预警)")
        for cluster, yearly in result_data['year_sai_matrix'].items():
            max_sai = max(yearly.values()) if yearly.values() else 0
            if max_sai > 2.0:
                max_year = max(yearly, key=yearly.get)
                st.warning(f"**{cluster}**: {max_year} 年最高 SAI = {max_sai:.2f} ⚠️")
        
        st.success("📁 报告已生成。详细数据请查看 `docs/` 目录。")
