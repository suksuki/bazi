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
from core.engine_v88 import EngineV88 as QuantumEngine
from utils.notification_manager import get_notification_manager
from core.processors.physics import GENERATION, CONTROL
import numpy as np

# Configure Logger
logger = logging.getLogger(__name__)

def render_prediction_dashboard():
    """
    Renders the Clean Prediction Dashboard (Smart Prediction).
    Fully MVC compliant.
    """
    controller = BaziController()
    
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
            st.error("数据加载失败，请重新输入")
            return

    user_data = controller.get_user_data()
    if not user_data or not user_data.get('name'):
        st.info("👈 请在左侧边栏输入您的出生信息并点击 '开始排盘'。")
        return

    # Display Notifications
    get_notification_manager().display_all()

    # 2. Get Data from Controller
    chart = controller.get_chart()
    luck_cycles = controller.get_luck_cycles()
    
    # User Info
    name = user_data.get('name', '未命名')
    
    # 3. UI Header
    st.title(f"📜 {name} 的命理探究")
    st.caption(f"🔧 Engine Version: `{QuantumEngine.VERSION}`")
    
    # Apply CSS
    st.markdown(get_glassmorphism_css(), unsafe_allow_html=True)
    st.markdown(get_animation_css(), unsafe_allow_html=True)
    st.markdown(get_bazi_table_css(), unsafe_allow_html=True)

    # 4. Render Chart (Four Pillars)
    cols = st.columns(4)
    pillars = ['year', 'month', 'day', 'hour']
    labels = ["年柱 (Year)", "月柱 (Month)", "日柱 (Day)", "时柱 (Hour)"]
    
    for i, p_key in enumerate(pillars):
        p_data = chart.get(p_key, {})
        stem = p_data.get('stem', '?')
        branch = p_data.get('branch', '?')
        
        # Theme
        t_stem = get_theme(stem)
        t_branch = get_theme(branch)
        dm_class = "dm-glow" if (p_key == 'day') else ""
        
        # Hidden Stems Display
        hidden_list = p_data.get('hidden_stems', [])
        hidden_html = '<div class="hidden-container">'
        for h_char in hidden_list:
            h_theme = get_theme(h_char)
            hidden_html += f'<div class="hidden-token" style="background: {h_theme["grad"]};" title="{h_char}">{h_char}</div>'
        hidden_html += '</div>'
        
        with cols[i]:
            st.markdown(f"""<div class="pillar-card">
    <div class="pillar-title">{labels[i]}</div>
    <div class="quantum-token {dm_class}" style="background: {t_stem['grad']}; animation: {t_stem['anim']} 3s infinite alternate;">
        <div class="token-icon">{t_stem['icon']}</div>
        <div class="token-char">{stem}</div>
    </div>
    <div class="quantum-token" style="background: {t_branch['grad']}; animation: {t_branch['anim']} 4s infinite alternate; margin-top: 10px;">
         <div class="token-icon">{t_branch['icon']}</div>
        <div class="token-char">{branch}</div>
    </div>
    {hidden_html}
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # 5. Time Machine (Da Yun & Liu Nian)
    st.subheader("⏳ 流年推演 (Fate Simulation)")
    
    current_year = datetime.datetime.now().year
    c1, c2 = st.columns([2, 1])
    
    selected_yun = None
    current_gan_zhi = None 
    
    # Da Yun Selection
    if luck_cycles:
        with c1:
            yun_options = [f"{c['start_year']}~{c['end_year']} ({c['start_age']}岁): {c['gan_zhi']}" for c in luck_cycles]
            default_idx = 0
            for i, c in enumerate(luck_cycles):
                if c['start_year'] <= current_year <= c['end_year']:
                    default_idx = i
                    break
            selected_yun_str = st.selectbox("当前大运 (Da Yun)", yun_options, index=default_idx)
            selected_yun = luck_cycles[yun_options.index(selected_yun_str)]
            
    # Liu Nian Selection
    with c2:
        sim_year = st.number_input("模拟流年 (Year)", min_value=1900, max_value=2100, value=current_year)
        # Calculate Liu Nian
        base_year = 1924 # Jia Zi
        offset = sim_year - base_year
        gd = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
        zhi = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
        ln_gan = gd[offset % 10]
        ln_zhi = zhi[offset % 12]
        ln_gan_zhi = f"{ln_gan}{ln_zhi}"
        st.metric("流年", f"{sim_year} {ln_gan_zhi}")
        
    current_gan_zhi = ln_gan_zhi # Focus on Liu Nian for Physics

    # 6. Core Analysis (Flux Data)
    st.markdown("---")
    st.subheader("📊 八字核心分析 (Bazi Core Analysis)")
    
    # Get Flux Data via Controller
    flux_data = controller.get_flux_data(selected_yun, current_gan_zhi)
    
    if flux_data:
        # A. Wang/Shuai
        wang_shuai_str = controller.get_wang_shuai_str(flux_data)
        col_ws1, col_ws2 = st.columns([1, 2])
        with col_ws1:
            if "身旺" in wang_shuai_str:
                st.success(f"**日主强弱**: {wang_shuai_str}")
            elif "身弱" in wang_shuai_str:
                st.warning(f"**日主强弱**: {wang_shuai_str}")
            else:
                st.info(f"**日主强弱**: {wang_shuai_str}")
        
        with col_ws2:
             s_self = flux_data.get('BiJian', 0) + flux_data.get('JieCai', 0)
             st.caption(f"日主能量值: {(s_self * 0.08):.2f}")

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
            st.plotly_chart(fig, use_container_width=True)

    # --- NEW: 触发规则分析 (Triggered Rules Analysis) ---
    st.markdown("---")
    st.subheader("📜 触发规则分析 (Activated Rules)")
    
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
        st.warning("规则匹配暂时不可用")

    # 7. Quantum Physics Diagnostics (Advanced Smart Chart)
    st.markdown("---")
    st.subheader("🧬 命运诊断 (Pro Diagnostics)")

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
                st.plotly_chart(fig_radar, use_container_width=True)
                
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
                    use_container_width=True,
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
        st.info("Computing Advanced Physics...")
    
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
