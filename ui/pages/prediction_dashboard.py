import streamlit as st
import datetime
import plotly.graph_objects as go
import logging
import pandas as pd

# Helpers
from ui.components.styles import (
    get_glassmorphism_css,
    get_animation_css, 
    get_bazi_table_css,
    get_theme
)
from ui.components.cards import DestinyCards

# MVC
from controllers.bazi_controller import BaziController
from core.unified_engine import UnifiedEngine as QuantumEngine
from core.fds_inference_engine import FDSInferenceEngine, ENGINE_NOTE_FALLBACK
from utils.notification_manager import get_notification_manager
from core.processors.physics import GENERATION, CONTROL
import numpy as np

# Configure Logger
logger = logging.getLogger(__name__)


@st.cache_resource
def get_fds_inference_engine() -> FDSInferenceEngine:
    """Cache inference engine to avoid re-loading files every rerun."""
    return FDSInferenceEngine()


def build_ten_gods_from_flux(flux_data: dict) -> dict:
    """
    Extract Ten-Gods vector from flux/graph outputs and map to standard codes.
    Accepts flat numeric values or {mean: x}.
    """
    if not flux_data:
        return {}
    mapping = {
        "ZhengGuan": "ZG",
        "QiSha": "PG",
        "ZhengCai": "ZR",
        "PianCai": "PR",
        "ShiShen": "ZS",
        "ShangGuan": "PS",
        "ZhengYin": "ZC",
        "PianYin": "PC",
        "BiJian": "ZB",
        "JieCai": "PB",
    }
    normalized = {}
    for src, code in mapping.items():
        if src in flux_data:
            val = flux_data[src]
            if isinstance(val, dict):
                val = val.get("mean", val.get("strength", val.get("value", 0)))
            try:
                normalized[code] = float(val)
            except Exception:
                normalized[code] = 0.0
    return normalized

def render_prediction_dashboard():
    """
    Renders the Clean Prediction Dashboard (Smart Prediction).
    Fully MVC compliant.
    """
    controller = BaziController()
    selected_yun = None  # Initialize to prevent UnboundLocalError
    
    # 1. State Verification & Hydration
    # [Fix] Hydrate Controller from Session State (Form Data)
    if st.session_state.get('calc_active', False):
        try:
            name = st.session_state.get('input_name', 'Unknown')
            gender = st.session_state.get('input_gender', '男')
            date_obj = st.session_state.get('input_date')
            time_val = st.session_state.get('input_time', 12)
            minute_val = st.session_state.get('input_minute', 0)
            city = st.session_state.get('unified_geo_city', 'Unknown')
            longitude = st.session_state.get('input_longitude', 116.46)
            enable_solar = st.session_state.get('input_enable_solar_time', True)
            
            if date_obj:
                controller.set_user_input(
                    name=name, gender=gender, date_obj=date_obj, 
                    time_int=time_val, minute_int=minute_val, city=city, 
                    longitude=longitude, enable_solar=enable_solar
                )
        except Exception as e:
            logger.error(f"Failed to hydrate controller: {e}")
            from ui.components.theme import render_crystal_notification
            render_crystal_notification("数据加载失败，请重新输入", "error")
            return

    user_data = controller.get_user_data()
    if not user_data or not user_data.get('name'):
        from ui.components.theme import render_crystal_notification
        render_crystal_notification("👈 请在左侧边栏输入您的出生信息并点击 '启卦排盘'。", "info")
        return

    # Display Notifications
    get_notification_manager().display_all()

    # 2. Get Data from Controller
    chart = controller.get_chart()
    luck_cycles = controller.get_luck_cycles()
    
    # User Info
    name = user_data.get('name', '未命名')
    
    # 3. UI Header
    from ui.components.theme import COLORS, GLASS_STYLE, card_container
    
    st.markdown(get_bazi_table_css(), unsafe_allow_html=True)
    st.markdown(get_animation_css(), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Calculate Liu Nian for energy context (Default to current)
    sim_year = st.session_state.get('sim_year', datetime.datetime.now().year)
    base_year = 1924 
    offset = sim_year - base_year
    gd = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    zhi = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    ln_gz = f"{gd[offset % 10]}{zhi[offset % 12]}"

    # Map flux particles to pe_list [y_s, y_b, m_s, m_b, d_s, d_b, h_s, h_b]
    # Get current flux data for energy bars
    current_flux = controller.get_flux_data(selected_yun=selected_yun, current_gan_zhi=ln_gz)
    
    pe_list = [0.0] * 8
    if current_flux and 'particles' in current_flux:
        particles = current_flux['particles']
        for i in range(min(len(particles), 8)):
            pe_list[i] = particles[i].get('strength', 0)

    wang_shuai_str = controller.get_wang_shuai_str(current_flux)
    
    # 4. Render Primary Chart (Four Pillars)
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1rem;">
            <h2 style="color: {COLORS['mystic_gold']}; font-family: 'Cinzel Decorative', cursive;">✨ 命盘真境 (Destiny Chart)</h2>
        </div>
    """, unsafe_allow_html=True)
    
    DestinyCards.render_bazi_table_with_engine(
        chart=chart,
        selected_yun=selected_yun,
        current_gan_zhi=ln_gz,
        pe_list=pe_list,
        wang_shuai_str=wang_shuai_str
    )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 5. Time Machine (Da Yun & Liu Nian)
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 2rem; border-right: 4px solid {COLORS['mystic_gold']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">⏳ 运势推演 (Fate Simulation)</h3>
        </div>
    """, unsafe_allow_html=True)
    
    current_year = datetime.datetime.now().year
    c1, c2 = st.columns([2, 1])
    
    # Da Yun Selection
    if luck_cycles:
        with c1:
            yun_options = [f"{c['start_year']}~{c['end_year']} ({c['start_age']}岁): {c['gan_zhi']}" for c in luck_cycles]
            default_idx = 0
            for i, c in enumerate(luck_cycles):
                if c['start_year'] <= current_year <= c['end_year']:
                    default_idx = i
                    break
            selected_yun_str = st.selectbox("选择大运 (Da Yun)", yun_options, index=default_idx)
            selected_yun = luck_cycles[yun_options.index(selected_yun_str)]
            
    # Liu Nian Selection
    with c2:
        sim_year = st.number_input("设置流年 (Year)", min_value=1900, max_value=2100, value=current_year, key="sim_year_input")
        # Reuse ln_gz calculation for metric display
        offset = sim_year - base_year
        ln_gan = gd[offset % 10]
        ln_zhi = zhi[offset % 12]
        ln_gan_zhi = f"{ln_gan}{ln_zhi}"
        st.metric("演算流年", f"{sim_year} {ln_gan_zhi}")
        
    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Core Analysis (Flux Data)
    from ui.components.theme import COLORS, GLASS_STYLE
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 1rem; border-left: 4px solid {COLORS['rose_magenta']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">📊 核心能量解析 (Core Energy)</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Use already computed current_flux
    flux_data = current_flux
    
    if flux_data:
        # A. Wang/Shuai
        wang_shuai_str = controller.get_wang_shuai_str(flux_data)
        col_ws1, col_ws2 = st.columns([1, 2])
        with col_ws1:
            if "身旺" in wang_shuai_str:
                st.success(f"**日主判定**: {wang_shuai_str}")
            elif "身弱" in wang_shuai_str:
                st.warning(f"**日主判定**: {wang_shuai_str}")
            else:
                st.info(f"**日主判定**: {wang_shuai_str}")
        
        with col_ws2:
             s_self = flux_data.get('BiJian', 0) + flux_data.get('JieCai', 0)
             st.metric("日主能量", f"{(s_self * 0.08):.2f}", help="日主原局能量强度")

        # B. Five Elements
        element_energies = controller.get_five_element_energies(flux_data)
        if element_energies:
            st.markdown("#### 🌈 五行能量分布")
            
            # Simple Bar Chart
            elements = list(element_energies.keys())
            energies = list(element_energies.values())
            colors = {'Wood': '#4CAF50', 'Fire': '#F44336', 'Earth': '#FF9800', 'Metal': '#2196F3', 'Water': '#00BCD4'}
            
            fig = go.Figure(data=[go.Bar(
                x=elements, y=energies,
                marker_color=[colors.get(e, '#aaa') for e in elements],
                text=[f"{e:.2f}" for e in energies],
                textposition='auto'
            )])
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=10, b=20), xaxis_title="五行 (Elements)", yaxis_title="能量值 (Energy)")
            st.plotly_chart(fig, width='stretch')

    # --- NEW: A-01 Manifold Mapping & Knowledge Injection ---
    inference_engine = get_fds_inference_engine()
    ten_gods_vector = build_ten_gods_from_flux(flux_data) if flux_data else {}
    self_energy_ctx = flux_data.get("self_energy", {}) if flux_data else {}
    logic_hit = (
        inference_engine.matches_classical_logic(ten_gods_vector, self_energy_ctx)
        if ten_gods_vector
        else None
    )
    should_infer = bool(
        ten_gods_vector
        and (
            logic_hit is True
            or (logic_hit is None and ten_gods_vector.get("ZG", 0) >= 2)
        )
    )

    if should_infer:
        inference = inference_engine.infer(
            ten_gods_vector, extra_context={"self_energy": self_energy_ctx}
        )
        if not FDSInferenceEngine.strict_logic_available():
            st.caption(f"⚠️ {ENGINE_NOTE_FALLBACK}")
        st.markdown(f"""
            <div style="{GLASS_STYLE} padding: 12px; margin: 1rem 0; border-left: 4px solid {COLORS['crystal_blue']};">
                <h4 style="color: {COLORS['mystic_gold']}; margin: 0;">🧭 A-01 流形归位 · 正官格</h4>
            </div>
        """, unsafe_allow_html=True)
        mv = inference.get("matrix_version", "3.0")
        st.caption(f"基于 **{mv}** 物理校准矩阵运算")

        d_min = min(inference["distances"].values()) if inference.get("distances") else 0.0
        if d_min > 3.0:
            st.warning(
                "**奇点预警 (Singularity Alert)** — 该命例展现出极高的物理独特性，"
                "不完全符合现有 S1/S2 标准分布，建议手动分析其 5D 偏移向量。"
            )
        c_infer1, c_infer2, c_infer3 = st.columns([1, 1, 1])
        with c_infer1:
            st.metric("最优子格局", inference["best_subpattern"], help="基于5D欧氏距离的最近质心")
            st.metric("相似度", f"{inference['similarity_percent']:.2f}%", help="距离占比换算的接近度")
        with c_infer2:
            st.metric("距 S1", f"{inference['distances'].get('A-01-S1', 0):.3f}")
            st.metric("距 S2", f"{inference['distances'].get('A-01-S2', 0):.3f}")
        with c_infer3:
            st.metric("混合度", "Yes" if inference["is_hybrid"] else "No", help="两质心距离接近时标记混合态")
            st.caption(f"偏移向量 | {inference_engine.format_offsets(inference['offset'])}")

        dims = FDSInferenceEngine.DIM_KEYS
        point_vals = [inference["point"].get(d, 0.0) for d in dims]
        centroid_s1 = inference_engine.centroids.get("A-01-S1")
        centroid_s2 = inference_engine.centroids.get("A-01-S2")
        centroid_vals_s1 = [float(v) for v in centroid_s1] if centroid_s1 is not None else [0.0] * 5
        centroid_vals_s2 = [float(v) for v in centroid_s2] if centroid_s2 is not None else [0.0] * 5

        radar_fig = go.Figure()
        radar_fig.add_trace(
            go.Scatterpolar(
                r=point_vals,
                theta=dims,
                fill="toself",
                name="命例坐标 P",
                line_color="#7F39FB",
                fillcolor="rgba(127, 57, 251, 0.25)",
            )
        )
        radar_fig.add_trace(
            go.Scatterpolar(
                r=centroid_vals_s1,
                theta=dims,
                fill="toself",
                name="A-01-S1 质心 (Order)",
                line_color="#2196F3",
                fillcolor="rgba(33, 150, 243, 0.12)",
            )
        )
        radar_fig.add_trace(
            go.Scatterpolar(
                r=centroid_vals_s2,
                theta=dims,
                fill="toself",
                name="A-01-S2 质心 (Wealth)",
                line_color="#FFD700",
                fillcolor="rgba(255, 215, 0, 0.12)",
            )
        )
        radar_fig.update_layout(
            height=320,
            margin=dict(l=20, r=20, t=10, b=10),
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=True,
        )
        st.plotly_chart(radar_fig, width="stretch")

        knowledge = inference.get("knowledge") or {}
        if knowledge:
            st.success(f"📜 全息判词 · {knowledge.get('name', inference['best_subpattern'])}")
            st.write(knowledge.get("description", ""))
    elif logic_hit is False:
        st.info("正官格逻辑未触发，未执行流形归位。")

    # --- NEW: 触发规则分析 (Triggered Rules Analysis) ---
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 1rem; border-left: 4px solid {COLORS['mystic_gold']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">📜 触发神煞规则 (Activated Rules)</h3>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        from core.rule_matcher import RuleMatcher, MatchedRule
        
        # Build bazi list from chart
        bazi_list = [
            f"{chart.get('year', {}).get('stem', '')}{chart.get('year', {}).get('branch', '')}",
            f"{chart.get('month', {}).get('stem', '')}{chart.get('month', {}).get('branch', '')}",
            f"{chart.get('day', {}).get('stem', '')}{chart.get('day', {}).get('branch', '')}",
            f"{chart.get('hour', {}).get('stem', '')}{chart.get('hour', {}).get('branch', '')}"
        ]
        dm = chart.get('day', {}).get('stem', '')
        
        # Match rules
        matcher = RuleMatcher()
        matched_rules = matcher.match(bazi_list, dm)
        summary = matcher.get_rule_summary(matched_rules)
        
        # Display summary metrics
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        with col_r1:
            st.metric("总规则数", summary['total'], help="触发的八字规则总数")
        with col_r2:
            st.metric("交互规则", summary['by_category'].get('B', 0), help="天干五合、六冲、三刑等")
        with col_r3:
            st.metric("墓库规则", summary['by_category'].get('D', 0), help="墓库开闭状态")
        with col_r4:
            active_count = len(summary['active_effects'])
            st.metric("动态激活", active_count, help="非始终应用的规则")
        
        # Display active effects (dynamic rules)
        if summary['active_effects']:
            st.markdown("#### ⚡ 激活的动态规则")
            for effect in summary['active_effects']:
                st.info(f"🔹 {effect}")
        
        # Expandable rule details
        with st.expander("📋 查看所有规则详情", expanded=False):
            # Group by category
            categories = {'A': '基础物理', 'B': '几何交互', 'C': '能量流转', 'D': '墓库规则', 'E': '判定阈值'}
            
            for cat, cat_name in categories.items():
                cat_rules = [r for r in matched_rules if r.category == cat]
                if cat_rules:
                    st.markdown(f"**{cat}. {cat_name}** ({len(cat_rules)}条)")
                    for rule in cat_rules:
                        participants_str = f" | 参与: {', '.join(rule.participants)}" if rule.participants else ""
                        effect_str = rule.effect if rule.effect != "始终应用" else "📌 基础规则"
                        st.caption(f"• **{rule.rule_id} {rule.name_cn}**: {effect_str}{participants_str}")
                    st.markdown("")
                    
    except Exception as e:
        logger.error(f"Rule matching failed: {e}")
        from ui.components.theme import render_crystal_notification
        render_crystal_notification("规则匹配暂时不可用", "warning")

    # 7. Quantum Physics Diagnostics (Advanced Smart Chart)
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 15px; margin-bottom: 1.5rem; border-left: 4px solid {COLORS['crystal_blue']};">
            <h3 style="color: {COLORS['mystic_gold']}; margin: 0;">🧬 深度命运诊断 (Pro Diagnostics)</h3>
        </div>
    """, unsafe_allow_html=True)

    # Run Advanced Simulation (Graph Engine)
    dynamic_context = {'year': current_gan_zhi, 'dayun': selected_yun['gan_zhi'] if selected_yun else '', 'luck_pillar': selected_yun['gan_zhi'] if selected_yun else ''}
    adv_result = controller.run_advanced_simulation(dynamic_context)
    
    if adv_result:
        # --- Section B: Ten Gods Radar ---
        st.markdown("#### 📡 十神势力雷达 (Ten Gods Radar)")
        c_radar, c_monitor = st.columns([1, 1])
        
        # Use proper Ten Gods data from controller
        ten_gods = adv_result.get('ten_gods', {})
        
        if ten_gods:
            tg_labels = list(ten_gods.keys())
            tg_means = [v['mean'] for v in ten_gods.values()]
            tg_stds = [v['std'] for v in ten_gods.values()]
            
            with c_radar:
                # Radar Chart with error bars representation
                fig_radar = go.Figure()
                
                # Main trace
                fig_radar.add_trace(go.Scatterpolar(
                    r=tg_means,
                    theta=tg_labels,
                    fill='toself',
                    name='μ (均值)',
                    line_color='#7F39FB',
                    fillcolor='rgba(127, 57, 251, 0.3)'
                ))
                
                # Upper bound (mean + std)
                fig_radar.add_trace(go.Scatterpolar(
                    r=[m + s for m, s in zip(tg_means, tg_stds)],
                    theta=tg_labels,
                    mode='lines',
                    name='μ + σ',
                    line=dict(color='rgba(127, 57, 251, 0.5)', dash='dash')
                ))
                
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True)),
                    showlegend=True,
                    height=350,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_radar, width='stretch')
                
                # Show detailed values with uncertainty
                st.caption("**十神详情 (ProbValue μ ± σ)**")
                for label, vals in ten_gods.items():
                    st.text(f"{label}: {vals['mean']:.2f} ± {vals['std']:.2f}")
        else:
            st.warning("十神数据未计算")
        
        # --- NEW: Node Energy Probability Table ---
        nodes_data = adv_result.get('nodes', [])
        if nodes_data:
            with st.expander("🔬 节点能量概率值 (Node Energy ProbValue)", expanded=False):
                st.caption("每个干支节点的能量值，以概率波函数表示 (μ ± σ)")
                
                # Build table data
                table_data = []
                for node in nodes_data:
                    char = node.get('char', '?')
                    elem = node.get('element', '?')
                    mean = node.get('energy_mean', 0)
                    std = node.get('energy_std', 0)
                    ntype = node.get('type', '?')
                    ten_god = node.get('ten_god', 'N/A')
                    
                    # Format energy as ProbValue string
                    energy_str = f"{mean:.2f} ± {std:.2f}"
                    
                    table_data.append({
                        '字符': char,
                        '五行': elem,
                        '类型': '天干' if ntype == 'stem' else '地支',
                        '十神': ten_god,
                        '能量 (μ ± σ)': energy_str,
                        '均值': mean
                    })
                
                # Sort by element for grouping
                df_nodes = pd.DataFrame(table_data)
                df_nodes = df_nodes.sort_values(by='均值', ascending=False)
                
                # Display with color coding by element
                st.dataframe(
                    df_nodes[['字符', '五行', '类型', '十神', '能量 (μ ± σ)']],
                    width='stretch',
                    hide_index=True
                )
                
                # Summary stats
                total_mean = sum(n.get('energy_mean', 0) for n in nodes_data)
                st.metric("总能量", f"{total_mean:.2f}", help="所有节点能量均值之和")
            
            
        with c_monitor:
            st.markdown("#### 🛡️ 控制论反馈 (Cybernetics)")
            feedback_stats = adv_result.get('feedback_stats', [])
            
            # Stats Aggregation
            inv_control_count = sum(1 for f in feedback_stats if f.get('is_inverse'))
            total_recoil = sum(f.get('recoil', 0) for f in feedback_stats)
            avg_shield = np.mean([f.get('shield_efficiency', 0) for f in feedback_stats]) if feedback_stats else 0
            
            m1, m2, m3 = st.columns(3)
            m1.metric("反克触发", f"{inv_control_count}次", delta_color="inverse")
            m2.metric("反噬伤害", f"{total_recoil:.1f}", delta_color="inverse")
            m3.metric("环境屏蔽", f"{avg_shield*100:.0f}%")
            
            if inv_control_count > 0:
                st.error(f"⚠️ 警告: 即使攻击者也受到 {total_recoil:.1f} 点反噬伤害 (Impedance Mismatch)!")
            if avg_shield > 0.3:
                st.success("🛡️ 护盾激活: 环境气场屏蔽了部分克制伤害")
                
        # --- Section D: Quantum Assertions ---
        st.markdown("#### 🔮 量子断言 (Quantum Assertions)")
        assertions = []
        if inv_control_count > 0:
            assertions.append(f"⛔ **反克现象**: 弱木克土? 或者是弱金克木? 局中出现了以弱击强的【反克】现象 {inv_control_count} 次。")
        if total_recoil > 10.0:
            assertions.append(f"💥 **强烈反噬**: 攻击者受到严重反震，名为克制实为自损。建议以守为攻。")
        if avg_shield > 0.5:
            assertions.append(f"🔒 **得地得势**: 环境能量形成了天然护盾，外界压力难以穿透。")
        
        if not assertions:
            assertions.append("✅ **系统平稳**: 能量流动符合经典物理模型，未检测到异常湍流。")
            
        for a in assertions:
            st.info(a)
            
    else:
        from ui.components.theme import render_crystal_notification
        render_crystal_notification("Computing Advanced Physics...", "info")
    
    st.caption("注：雷达图展示了该年运下的十神能量相对强弱；控制论面板显示了深层物理交互状态。")
    
    # Uncertainty / MCP Era
    st.markdown("---")
    
    # Era Info from Controller
    era_info = controller.get_current_era_info()
    if era_info:
        st.markdown("### 🌐 宏观场 (MCP: 时代上下文)")
        cols = st.columns(4)
        cols[0].metric("当前时代", era_info.get('desc', '未知'), f"周期 {era_info.get('period')}")
        cols[1].metric("红利元素", era_info.get('era_element', 'None'))
        cols[2].metric("红利加成", f"{era_info.get('era_bonus', 0)*100:.0f}%")
        cols[3].metric("时代折损", f"{era_info.get('era_penalty', 0)*100:.0f}%")

    # Layout Footer
    st.markdown("---")
    st.caption(f"天机·AI命理演算系统 {BaziController.VERSION if hasattr(BaziController, 'VERSION') else ''} | Powered by Gemini 2.0 Flash")
