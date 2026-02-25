import streamlit as st
import datetime
import html
import plotly.graph_objects as go
import logging
import pandas as pd
from typing import Optional

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
from core.ai_engine import (
    generate_manifold_interpretation,
    stream_manifold_interpretation,
    is_ai_engine_available,
    simulate_dynamic_impact,
    explain_classical_logic,
    generate_case_comparison_blurb,
    generate_repair_strategy,
    generate_combined_pattern_verdict,
    stream_combined_pattern_verdict,
)
from core.case_retriever import get_default_retriever
from controllers.holographic_pattern_controller import HolographicPatternController
from core.pathway_analyzer import analyze_repair_pathway
from core.config_manager import ConfigManager

def _get_radar_extreme_threshold() -> float:
    """从 config/physics/algorithm_params.json 读取雷达图极值阈值。"""
    params = ConfigManager.get_algorithm_params() or {}
    return float((params.get("ui_radar") or {}).get("extreme_threshold", 1.2))
from core.dynamic_engine import (
    calculate_temporal_displacement,
    get_geo_factor,
    get_time_delta,
)
from core.manifold_visual_utils import get_manifold_band_for_pattern, get_axis_hover_text
from utils.notification_manager import get_notification_manager
from core.processors.physics import GENERATION, CONTROL
import numpy as np

# Configure Logger
logger = logging.getLogger(__name__)

# 5D 轴标签（双层雷达图）
AXIS_LABELS_5D = {"E": "能量 E", "O": "秩序 O", "M": "财富 M", "S": "压力 S", "R": "关系 R"}

# 地域键名映射：侧栏/主区选择 -> geographic_factors.regions
GEO_DIRECTION_TO_REGION = {
    "中": "中原", "东": "东方", "南": "南方", "西": "西方", "北": "北方",
    "东南": "东南", "东北": "东北", "西南": "西南", "西北": "西北",
}


def _get_region_offset_5d(direction: str) -> dict:
    """从 config/physics/geographic_factors.json 读取地域 5D 修正；缺失则用 dynamic_engine.get_geo_factor。"""
    from pathlib import Path
    import json
    path = Path(__file__).resolve().parent.parent.parent / "config" / "physics" / "geographic_factors.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            regions = cfg.get("regions") or {}
            key = GEO_DIRECTION_TO_REGION.get(direction, "中原")
            d = regions.get(key) or regions.get("中原") or {}
            if isinstance(d, dict):
                return {k: float(d.get(k, 0)) for k in ["E", "O", "M", "S", "R"]}
        except Exception:
            pass
    return get_geo_factor(direction)


@st.cache_resource
def get_fds_inference_engine(matrix_version: Optional[str] = None) -> Optional[FDSInferenceEngine]:
    """Cache inference engine 按矩阵版本隔离；若缺少 registry/knowledge 等文件则返回 None。"""
    try:
        return FDSInferenceEngine(preferred_matrix_version=matrix_version)
    except FileNotFoundError as e:
        logger.warning("FDS inference engine 未加载（缺少配置文件）: %s", e)
        return None


@st.cache_resource
def get_case_retriever():
    """A-01 案例对撞机：从 registry 与可选扩展样本构建最近邻检索器。"""
    try:
        return get_default_retriever()
    except Exception as e:
        logger.warning("Case retriever 未加载: %s", e)
        return None


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
    
    # 大运：用 session_state 持久化选择，保证表格与选择器一致（避免表里显示 ? 或与下拉不一致）
    current_year = datetime.datetime.now().year
    if luck_cycles:
        yun_options = [f"{c['start_year']}~{c['end_year']} ({c['start_age']}岁): {c['gan_zhi']}" for c in luck_cycles]
        default_idx = 0
        for i, c in enumerate(luck_cycles):
            if c['start_year'] <= current_year <= c['end_year']:
                default_idx = i
                break
        default_str = yun_options[default_idx]
        if "bazi_da_yun_choice" not in st.session_state:
            st.session_state["bazi_da_yun_choice"] = default_str
        selected_yun_str = st.session_state["bazi_da_yun_choice"]
        if selected_yun_str not in yun_options:
            selected_yun_str = default_str
            st.session_state["bazi_da_yun_choice"] = default_str
        selected_yun = luck_cycles[yun_options.index(selected_yun_str)]
    else:
        selected_yun = None
        yun_options = []
        default_idx = 0
    
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
    c1, c2, c3 = st.columns([2, 1, 1])

    # Da Yun Selection（与上方表格用同一 session_state，保证大运列与选择器一致）
    if luck_cycles:
        with c1:
            st.selectbox("选择大运 (Da Yun)", yun_options, key="bazi_da_yun_choice")

    # Liu Nian Selection
    with c2:
        sim_year = st.number_input("设置流年 (Year)", min_value=1900, max_value=2100, value=current_year, key="sim_year_input")
        offset = sim_year - base_year
        ln_gan = gd[offset % 10]
        ln_zhi = zhi[offset % 12]
        ln_gan_zhi = f"{ln_gan}{ln_zhi}"
        st.metric("演算流年", f"{sim_year} {ln_gan_zhi}")

    # 地理方位（动态演化·空间耦合）- 八方
    with c3:
        geo_direction = st.selectbox(
            "地理方位",
            ["中", "东", "南", "西", "北", "东南", "东北", "西南", "西北"],
            index=0,
            key="dynamic_geo_direction",
            help="用于 5D 动态修正：南火、西金、东方木等",
        )

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
            st.plotly_chart(fig, use_container_width=True)

    # --- 全息格局对撞（多格局通用，非 A-01 专属）---
    st.markdown(f"""
        <div style="{GLASS_STYLE} padding: 12px; margin: 1rem 0; border-left: 4px solid {COLORS['crystal_blue']};">
            <h4 style="color: {COLORS['mystic_gold']}; margin: 0;">🔀 全息格局对撞 · 流形可视化与混合判词</h4>
        </div>
    """, unsafe_allow_html=True)
    st.caption("对 QGA 注册格局（A-01 / A-02 / A-03）做多矩阵投影与置信度评分，生成混合 5D 雷达图与 32B 综合判词。")
    # 第 041 号：移动端雷达图限高，避免遮挡判词
    st.markdown("""
        <style>
        @media (max-width: 768px) {
            div[data-testid="stHorizontalBlock"] .stPlotlyChart { max-height: 260px !important; }
            div[data-testid="column"] .stPlotlyChart { min-height: 200px !important; }
        }
        </style>
    """, unsafe_allow_html=True)
    try:
        c = controller.get_chart()
        bazi_list = [
            f"{c.get('year', {}).get('stem', '')}{c.get('year', {}).get('branch', '')}",
            f"{c.get('month', {}).get('stem', '')}{c.get('month', {}).get('branch', '')}",
            f"{c.get('day', {}).get('stem', '')}{c.get('day', {}).get('branch', '')}",
            f"{c.get('hour', {}).get('stem', '')}{c.get('hour', {}).get('branch', '')}",
        ]
        day_master = (c.get("day") or {}).get("stem", "")
        if not day_master or not all(bazi_list):
            st.caption("_排盘数据不完整，无法进行格局对撞。_")
        else:
            holo = HolographicPatternController()
            ctx = holo.get_mixed_pattern_context(bazi_list, day_master)
            patterns = ctx.get("probabilistic_patterns") or []
            point_5d = ctx.get("point_5d") or {}
            geo_direction = st.session_state.get("dynamic_geo_direction", "中")
            region_offset = _get_region_offset_5d(geo_direction)
            point_5d_with_geo = {k: point_5d.get(k, 0) + region_offset.get(k, 0) for k in ["E", "O", "M", "S", "R"]}
            luck_gan_zhi = (selected_yun.get("gan_zhi", "") if selected_yun else "") or ""
            try:
                _off = sim_year - base_year
                year_gan_zhi = f"{gd[_off % 10]}{zhi[_off % 12]}"
            except Exception:
                year_gan_zhi = ""
            temporal = calculate_temporal_displacement(point_5d_with_geo, luck_gan_zhi, year_gan_zhi) if point_5d_with_geo else {}
            displaced_point = temporal.get("displaced_point") or point_5d_with_geo
            dims = ["E", "O", "M", "S", "R"]
            theta_labels = [f"{d} · {AXIS_LABELS_5D.get(d, d)}" for d in dims]
            extreme_threshold = _get_radar_extreme_threshold()
            is_extreme = any(abs(displaced_point.get(d, 0)) >= extreme_threshold for d in dims)
            retriever = get_case_retriever()
            col_radar, col_verdict = st.columns([1, 1])
            with col_radar:
                fig_collider = go.Figure()
                dominant_id = patterns[0].get("pattern_id") if patterns else None
                band = get_manifold_band_for_pattern(dominant_id or "A-01") if dominant_id else None
                if band:
                    mu, std = band.get("mean"), band.get("std")
                    if mu and std:
                        r_lo = [max(0, mu.get(d, 0) - std.get(d, 0.5)) for d in dims]
                        r_hi = [mu.get(d, 0) + std.get(d, 0.5) for d in dims]
                        r_lo.append(r_lo[0])
                        r_hi.append(r_hi[0])
                        fig_collider.add_trace(go.Scatterpolar(
                            r=r_hi, theta=theta_labels + [theta_labels[0]],
                            fill="toself", name=f"{dominant_id or '格局'} μ+σ",
                            line=dict(color="rgba(33,150,243,0.3)", width=1),
                            fillcolor="rgba(33,150,243,0.12)",
                        ))
                        fig_collider.add_trace(go.Scatterpolar(
                            r=r_lo, theta=theta_labels + [theta_labels[0]],
                            fill="toself", name=f"{dominant_id or '格局'} μ−σ",
                            line=dict(color="rgba(33,150,243,0.25)", width=1),
                            fillcolor="rgba(33,150,243,0.06)",
                        ))
                r_base = [max(0, point_5d_with_geo.get(d, 0)) for d in dims]
                r_base.append(r_base[0])
                fig_collider.add_trace(go.Scatterpolar(
                    r=r_base, theta=theta_labels + [theta_labels[0]],
                    fill="toself", name="命主（含地域）",
                    line=dict(color="#7F39FB", width=2), fillcolor="rgba(127,57,251,0.25)",
                    hovertemplate="%{theta}<br>值=%{r:.2f}<extra></extra>",
                ))
                r_dyn = [max(0, displaced_point.get(d, 0)) for d in dims]
                r_dyn.append(r_dyn[0])
                fig_collider.add_trace(go.Scatterpolar(
                    r=r_dyn, theta=theta_labels + [theta_labels[0]],
                    fill="toself", name="流年/大运后" + (" ⚠ 极值区" if is_extreme else ""),
                    line=dict(color="#FF9800" if is_extreme else "#00E676", width=1.5, dash="dash"),
                    fillcolor="rgba(255,152,0,0.15)" if is_extreme else "rgba(0,230,118,0.15)",
                    hovertemplate="%{theta}<br>值=%{r:.2f}<extra></extra>",
                ))
                fig_collider.update_layout(
                    polar=dict(radialaxis=dict(visible=True)),
                    showlegend=True, height=360, margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_collider, use_container_width=True)
                st.caption("基准层：命主混合 5D+地域修正；背景：主格局 μ±σ；虚线：流年/大运位移，橙为极值区预警。")
            with col_verdict:
                if patterns:
                    ratio_str = " · ".join([f"{p.get('pattern_id', '')} {p.get('confidence_pct', 0):.0f}%" for p in patterns[:5]])
                    st.caption(f"**命中格局**：{ratio_str}")
                    academic_mode = st.checkbox("学术模式（显示 5D 坐标与流形修复）", value=False, key="verdict_academic_mode")
                    repair_vector = None
                    if retriever and retriever.case_count > 0:
                        pathway = analyze_repair_pathway(retriever, point_5d_with_geo, top_repair=5)
                        repair_vector = pathway.get("repair_vector")
                        if academic_mode and pathway.get("deficit_info") and pathway["deficit_info"].get("deficit", 0) > 0:
                            st.caption(f"**流形修复**：{pathway['deficit_info'].get('axis_label', pathway['deficit_info'].get('axis', ''))} 轴建议补齐")
                    if academic_mode:
                        st.caption(f"**混合 5D（+地域）**：E={point_5d_with_geo.get('E', 0):.2f} O={point_5d_with_geo.get('O', 0):.2f} M={point_5d_with_geo.get('M', 0):.2f} S={point_5d_with_geo.get('S', 0):.2f} R={point_5d_with_geo.get('R', 0):.2f}")
                    if is_ai_engine_available():
                        verdict_key = "combined_verdict_text"
                        verdict_style = (
                            'background: linear-gradient(135deg, rgba(127,57,251,0.12) 0%, rgba(33,150,243,0.08) 100%); '
                            'border-radius: 12px; padding: 1rem 1.25rem; margin: 0.5rem 0; '
                            'border: 1px solid rgba(127,57,251,0.35); '
                            'font-family: "Noto Serif SC", serif; line-height: 1.7;'
                        )
                        # 喜忌神看板（第 040/041 号）：带「量子模拟中…」Loading，雷达图移动端不遮挡判词
                        try:
                            from core.balance_engine import run_balance_audit
                            dominant_id = patterns[0].get("pattern_id") if patterns else None
                            ten_gods = holo._chart_to_ten_gods(bazi_list, day_master) if dominant_id else None
                            with st.spinner("量子模拟中…"):
                                balance_audit = run_balance_audit(point_5d_with_geo, ten_gods or {}, dominant_id or "") if ten_gods and dominant_id else {}
                            if balance_audit and (balance_audit.get("useful_god") or balance_audit.get("harmful_god")):
                                st.markdown("**喜忌看板**")
                                row_xi = st.columns(3)
                                with row_xi[0]:
                                    st.caption("🌟 **用神**：" + (balance_audit.get("useful_god") or "—"))
                                with row_xi[1]:
                                    st.caption("🚫 **忌神**：" + (balance_audit.get("harmful_god") or "—"))
                                with row_xi[2]:
                                    st.caption("🌉 **通关神**：" + (balance_audit.get("bridge_god") or "—"))
                        except Exception as _e:
                            logger.debug("喜忌看板未展示: %s", _e)
                        if verdict_key in st.session_state and st.session_state[verdict_key]:
                            safe = html.escape(st.session_state[verdict_key]).replace("\n", "<br/>")
                            st.markdown(
                                f'<div style="{verdict_style}">'
                                f'<p style="color: var(--text-color, #e8e4e0); margin: 0;">{safe}</p></div>',
                                unsafe_allow_html=True,
                            )
                            st.caption("由 **全息对撞** 生成 · 上一段判词")
                        if st.button("📜 生成混合格局判词", key="btn_combined_verdict"):
                            ph_verdict = st.empty()
                            accumulated = ""
                            ph_verdict.markdown(
                                f'<div style="{verdict_style}">'
                                '<p style="color: #b0a090; margin: 0;">▌ 正在生成判词…</p></div>',
                                unsafe_allow_html=True,
                            )
                            try:
                                ten_gods_for_verdict = holo._chart_to_ten_gods(bazi_list, day_master)
                                dominant_for_verdict = patterns[0].get("pattern_id") if patterns else None
                                for chunk in stream_combined_pattern_verdict(
                                    probabilistic_patterns=patterns,
                                    point_5d=point_5d_with_geo,
                                    repair_vector=repair_vector,
                                    ten_gods=ten_gods_for_verdict,
                                    dominant_pattern_id=dominant_for_verdict,
                                ):
                                    accumulated += chunk
                                    safe = html.escape(accumulated).replace("\n", "<br/>")
                                    ph_verdict.markdown(
                                        f'<div style="{verdict_style}">'
                                        f'<p style="color: var(--text-color, #e8e4e0); margin: 0;">{safe}<span style="opacity:0.8;">▌</span></p></div>',
                                        unsafe_allow_html=True,
                                    )
                                if accumulated.strip():
                                    st.session_state[verdict_key] = accumulated.strip()
                                    safe = html.escape(accumulated.strip()).replace("\n", "<br/>")
                                    ph_verdict.markdown(
                                        f'<div style="{verdict_style}">'
                                        f'<p style="color: var(--text-color, #e8e4e0); margin: 0;">{safe}</p></div>',
                                        unsafe_allow_html=True,
                                    )
                                    st.caption("由 **全息对撞** 生成 · 打字机展示")
                                else:
                                    res = generate_combined_pattern_verdict(
                                        probabilistic_patterns=patterns,
                                        point_5d=point_5d_with_geo,
                                        repair_vector=repair_vector,
                                        ten_gods=ten_gods_for_verdict,
                                        dominant_pattern_id=dominant_for_verdict,
                                    )
                                    if res.get("success") and res.get("text"):
                                        text = res["text"].strip()
                                        st.session_state[verdict_key] = text
                                        safe = html.escape(text).replace("\n", "<br/>")
                                        ph_verdict.markdown(
                                            f'<div style="{verdict_style}">'
                                            f'<p style="color: var(--text-color, #e8e4e0); margin: 0;">{safe}</p></div>',
                                            unsafe_allow_html=True,
                                        )
                                        st.caption("由 **全息对撞** 生成（非流式回退）")
                                    else:
                                        ph_verdict.markdown(
                                            f'<div style="{verdict_style}">'
                                            f'<p style="color: #c08080;">{html.escape(res.get("error", "模型未返回内容"))}</p></div>',
                                            unsafe_allow_html=True,
                                        )
                            except Exception as e:
                                logger.exception("混合格局判词流式调用失败")
                                err_msg = str(e)
                                ph_verdict.markdown(
                                    f'<div style="{verdict_style}">'
                                    f'<p style="color: #c08080;">生成失败：{html.escape(err_msg)}</p></div>',
                                    unsafe_allow_html=True,
                                )
                                st.error(err_msg)
                    else:
                        st.info("未检测到本地 Ollama，请在天机设置中配置对话模型后使用混合判词。")
                else:
                    st.caption("_未命中已注册格局，请确认 registry/qga_manifest.json 与格局数据已配置。_")
    except Exception as e:
        logger.exception("全息格局对撞失败")
        st.caption(f"_对撞或判词失败：{e}_")


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
    dynamic_context = {'year': ln_gz, 'dayun': selected_yun['gan_zhi'] if selected_yun else '', 'luck_pillar': selected_yun['gan_zhi'] if selected_yun else ''}
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
