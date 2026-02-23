import streamlit as st
import datetime
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
)
from core.case_retriever import get_default_retriever
from core.pathway_analyzer import analyze_repair_pathway
from core.config_manager import ConfigManager
from utils.notification_manager import get_notification_manager
from core.processors.physics import GENERATION, CONTROL
import numpy as np

# Configure Logger
logger = logging.getLogger(__name__)

# 5D 轴标签（双层雷达图）
AXIS_LABELS_5D = {"E": "能量 E", "O": "秩序 O", "M": "财富 M", "S": "压力 S", "R": "关系 R"}


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

    # --- NEW: A-01 Manifold Mapping & Knowledge Injection ---
    _physics = ConfigManager().get("physics") or {}
    _matrix_ver = _physics.get("matrix_version") if isinstance(_physics, dict) else None
    inference_engine = get_fds_inference_engine(_matrix_ver)
    should_infer = False
    logic_hit = None  # 避免 inference_engine 为 None 时后续 elif logic_hit is False 未定义
    if inference_engine is None:
        st.info("🧭 A-01 流形归位需配置 **registry** 与 **knowledge**。请将 `bazi_data_external` 中的 `registry/`、`knowledge/` 及 `config/patterns/` 拷到项目根目录下对应路径后刷新。")
    else:
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

    if inference_engine and should_infer:
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

        # --- A-01 古典语义立法（可折叠展示，来自 config/hkb/hkb_params.json）---
        try:
            import json
            from pathlib import Path
            _hkb_path = Path(__file__).resolve().parent.parent.parent / "config" / "hkb" / "hkb_params.json"
            if _hkb_path.exists():
                with open(_hkb_path, "r", encoding="utf-8") as f:
                    _hkb = json.load(f)
                _core = (_hkb.get("hkb") or {}).get("a01_semantic_core")
                if isinstance(_core, dict):
                    with st.expander("📜 A-01 古典语义立法（本页依据）", expanded=False):
                        for _key in ("dimension_a_order_rigidity", "dimension_b_energy_carrier", "dimension_c_wealth_coupling"):
                            _d = _core.get(_key)
                            if not isinstance(_d, dict):
                                continue
                            _name = _d.get("name", _key)
                            _axis = _d.get("axis") or ", ".join(_d.get("axes") or [])
                            _def = _d.get("definition", "")
                            _map = _d.get("physical_mapping", "")
                            st.markdown(f"**{_name}**（轴：{_axis}）")
                            st.caption(f"定义：{_def}")
                            st.caption(f"物理映射：{_map}")
                            st.markdown("")
        except Exception:
            pass

        # --- 动态演化：大运+流年+地理（先算好，供 AI 与雷达图使用）---
        luck_gan_zhi = (selected_yun.get("gan_zhi", "") if selected_yun else "") or ""
        year_gan_zhi = f"{gd[(sim_year - base_year) % 10]}{zhi[(sim_year - base_year) % 12]}"
        geo_direction = st.session_state.get("dynamic_geo_direction", "中")
        dynamic_state = None
        try:
            from core.dynamic_engine import get_time_delta, get_geo_factor, calculate_dynamic_state, build_dynamic_context_for_prompt
            time_delta = get_time_delta(luck_gan_zhi, year_gan_zhi)
            geo_factor = get_geo_factor(geo_direction)
            dynamic_state = calculate_dynamic_state(inference["point"], time_delta=time_delta, geo_factor=geo_factor)
        except Exception as e:
            logger.debug("dynamic_engine 跳过: %s", e)

        # --- 026: 5D 双层雷达图（原局 vs 推演）---
        if dynamic_state:
            st.markdown("#### 📐 5D 流形推演 (原局 vs 大运/流年/地理)")
            base_pt = dynamic_state.get("base_point") or inference["point"]
            dyn_pt = dynamic_state.get("dynamic_point") or base_pt
            dims = ["E", "O", "M", "S", "R"]
            r_base = [max(0, base_pt.get(k, 0)) for k in dims]
            r_dyn = [max(0, dyn_pt.get(k, 0)) for k in dims]
            fig_5d = go.Figure()
            fig_5d.add_trace(go.Scatterpolar(
                r=r_base,
                theta=[AXIS_LABELS_5D.get(k, k) for k in dims],
                fill='toself',
                name='原局',
                line=dict(color='#7F39FB', width=2),
                fillcolor='rgba(127, 57, 251, 0.25)',
            ))
            fig_5d.add_trace(go.Scatterpolar(
                r=r_dyn,
                theta=[AXIS_LABELS_5D.get(k, k) for k in dims],
                fill='toself',
                name='推演后',
                line=dict(color='#FF9800', width=1.5, dash='dash'),
                fillcolor='rgba(255, 152, 0, 0.15)',
            ))
            fig_5d.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                showlegend=True,
                height=320,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_5d, use_container_width=True)
            # 推演描述：调用大模型解释位移
            if is_ai_engine_available():
                if st.button("🔄 生成推演描述", key="btn_simulate_dynamic"):
                    with st.spinner("大模型推演中…"):
                        disp = dynamic_state.get("displacement") or {k: 0.0 for k in dims}
                        res = simulate_dynamic_impact(
                            base_point=base_pt,
                            delta_vector=disp,
                            context_type="liunian",
                        )
                    if res.get("success"):
                        st.success(res.get("text", ""))
                    else:
                        st.error(res.get("error", "推演失败"))

        # --- [AI 深度透视] 第一优先级：全息报告样式，置顶展示 ---
        st.markdown(f"""
            <div style="{GLASS_STYLE} padding: 12px; margin: 1rem 0; border-left: 4px solid {COLORS['rose_magenta']};">
                <h4 style="color: {COLORS['mystic_gold']}; margin: 0;">🔮 AI 深度透视 (Manifold-to-Text)</h4>
            </div>
        """, unsafe_allow_html=True)
        if is_ai_engine_available():
            from core.config_manager import ConfigManager
            _cm = ConfigManager()
            _ai_cfg = _cm.get("ai_engine")
            _current_chat_model = (_ai_cfg.get("chat_model") if isinstance(_ai_cfg, dict) else None) or _cm.get("selected_model_name") or "qwen2.5:32b"
            pt = inference["point"]
            # 缓存键含模型 + 大运/流年/方位，切换时间或地理即重新生成动态趋势判词
            _dyn_suffix = f"{luck_gan_zhi}_{year_gan_zhi}_{geo_direction}" if dynamic_state else "static"
            ai_cache_key = "ai_interpret_{}_{:.2f}_{:.2f}_{:.2f}_{:.2f}_{:.2f}_{}_{}".format(
                inference["best_subpattern"],
                pt.get("E", 0), pt.get("O", 0), pt.get("M", 0), pt.get("S", 0), pt.get("R", 0),
                _current_chat_model.replace(":", "_"),
                _dyn_suffix,
            )
            import html
            offset_str = inference_engine.format_offsets(inference["offset"])
            st.caption(f"当前判词模型：**{_current_chat_model}**（在系统配置页切换后可立即用新模型重新生成）")
            if ai_cache_key not in st.session_state:
                st.info(f"**推理依据**：基于偏移向量 {offset_str} 的物理微调。")
                ph = st.empty()
                accumulated = ""
                dynamic_context_str = None
                if dynamic_state:
                    dynamic_context_str = build_dynamic_context_for_prompt(
                        inference["point"],
                        dynamic_state["dynamic_point"],
                        dynamic_state["time_delta"],
                        dynamic_state["geo_factor"],
                        luck_gan_zhi=luck_gan_zhi,
                        year_gan_zhi=year_gan_zhi,
                        direction=geo_direction,
                    )
                try:
                    for chunk in stream_manifold_interpretation(
                        point=inference["point"],
                        offset=inference["offset"],
                        best_subpattern=inference["best_subpattern"],
                        matrix_version=inference.get("matrix_version", "4.0"),
                        ten_gods=ten_gods_vector,
                        dynamic_context=dynamic_context_str,
                        pattern_id=inference.get("pattern_id", "A-01"),
                    ):
                        accumulated += chunk
                        safe = html.escape(accumulated).replace("\n", "<br/>")
                        ph.markdown(f"""
                            <div style="background: linear-gradient(135deg, rgba(127,57,251,0.08) 0%, rgba(33,150,243,0.06) 100%); 
                                        border-radius: 12px; padding: 1rem 1.25rem; margin: 0.5rem 0; border: 1px solid rgba(127,57,251,0.25);">
                                <p style="color: var(--text-color, #e0e0e0); line-height: 1.6; margin: 0;">{safe}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    st.session_state[ai_cache_key] = {"success": True, "text": accumulated.strip(), "model": _current_chat_model}
                    st.caption(f"由 **{_current_chat_model}** 基于 5D 偏移向量生成 · 全息报告")
                except Exception as e:
                    st.session_state[ai_cache_key] = {"success": False, "text": "", "model": "", "error": str(e)}
                    ph.empty()
                    st.warning(f"AI 判词暂不可用：{e}")
            else:
                ai_result = st.session_state[ai_cache_key]
                if ai_result.get("success") and ai_result.get("text"):
                    st.info(f"**推理依据**：基于偏移向量 {offset_str} 的物理微调。")
                    safe_text = html.escape(ai_result["text"]).replace("\n", "<br/>")
                    st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(127,57,251,0.08) 0%, rgba(33,150,243,0.06) 100%); 
                                    border-radius: 12px; padding: 1rem 1.25rem; margin: 0.5rem 0; border: 1px solid rgba(127,57,251,0.25);">
                            <p style="color: var(--text-color, #e0e0e0); line-height: 1.6; margin: 0;">{safe_text}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    st.caption(f"由 **{ai_result.get('model', '')}** 基于 5D 偏移向量生成 · 全息报告")
                elif ai_result.get("error"):
                    st.warning(f"AI 判词暂不可用：{ai_result['error']}")
        else:
            st.info("未检测到本地 Ollama，请在天机设置中配置对话模型后使用 AI 深度透视。")

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
                name="原局 P",
                line_color="#7F39FB",
                fillcolor="rgba(127, 57, 251, 0.25)",
            )
        )
        if dynamic_state:
            dynamic_vals = [dynamic_state["dynamic_point"].get(d, 0.0) for d in dims]
            radar_fig.add_trace(
                go.Scatterpolar(
                    r=dynamic_vals,
                    theta=dims,
                    fill="toself",
                    name="动态点 (大运+流年+地理)",
                    line_color="#00E676",
                    fillcolor="rgba(0, 230, 118, 0.15)",
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
        st.plotly_chart(radar_fig, use_container_width=True)
        if dynamic_state:
            st.caption("原局 P：静态 5D；动态点：当前大运、流年、地理方位合成后的位移。")

        knowledge = inference.get("knowledge") or {}
        if knowledge:
            st.success(f"📜 全息判词 · {knowledge.get('name', inference['best_subpattern'])}")
            st.write(knowledge.get("description", ""))

        # --- 027: 全息相似案例（A-01 案例对撞机）---
        with st.expander("🔬 全息相似案例 (Holographic Similar Case)", expanded=False):
            st.caption("从全息案例库中匹配与当前 5D 坐标最近邻的典型案例，进行同类对比。")
            pt = inference.get("point", {})
            retriever = get_case_retriever()
            if retriever and pt:
                nearest = retriever.find_nearest_cases(pt, top_n=3)
                if nearest:
                    dims = list(AXIS_LABELS_5D.values())
                    cols = st.columns(3)
                    for i, case in enumerate(nearest):
                        with cols[i]:
                            vals = case.get("point") or []
                            if isinstance(vals, dict):
                                vals = [vals.get(k, 0) for k in ["E", "O", "M", "S", "R"]]
                            if len(vals) == 5:
                                fig = go.Figure()
                                fig.add_trace(
                                    go.Scatterpolar(
                                        r=vals + [vals[0]],
                                        theta=dims + [dims[0]],
                                        fill="toself",
                                        name=case.get("ref", ""),
                                        line_color="#2196F3",
                                        fillcolor="rgba(33, 150, 243, 0.2)",
                                    )
                                )
                                fig.update_layout(
                                    polar=dict(radialaxis=dict(visible=True)),
                                    height=180,
                                    margin=dict(l=20, r=20, t=20, b=20),
                                    showlegend=False,
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            st.caption(f"**{case.get('ref', '')}** · {case.get('subpattern', '')} · 相似度 {case.get('similarity_pct', 0)}%")
                            if case.get("is_singularity"):
                                st.caption("⭐ 奇点样板")
                    if is_ai_engine_available():
                        if st.button("🤖 生成同类项对比文案", key="btn_case_comparison"):
                            with st.spinner("大模型生成中…"):
                                blurb = generate_case_comparison_blurb(pt, nearest)
                            if blurb.get("success"):
                                st.success(blurb.get("text", ""))
                            else:
                                st.error(blurb.get("error", "生成失败"))
                    # 028: 全息侧写 — 选择案例查看详情与演化路径占位
                    chosen = st.radio("选择案例查看全息侧写", options=[c.get("ref", "") for c in nearest], key="case_sidewalk", horizontal=True)
                    if chosen:
                        sel = next((c for c in nearest if c.get("ref") == chosen), None)
                        if sel:
                            with st.expander("📐 全息侧写 (Holographic Profile)", expanded=True):
                                vals = sel.get("point") or []
                                if isinstance(vals, dict):
                                    vals = [vals.get(k, 0) for k in ["E", "O", "M", "S", "R"]]
                                if len(vals) == 5:
                                    fig_big = go.Figure()
                                    fig_big.add_trace(
                                        go.Scatterpolar(
                                            r=vals + [vals[0]],
                                            theta=list(AXIS_LABELS_5D.values()) + [list(AXIS_LABELS_5D.values())[0]],
                                            fill="toself",
                                            name=chosen,
                                            line_color="#9C27B0",
                                            fillcolor="rgba(156, 39, 176, 0.25)",
                                        )
                                    )
                                    fig_big.update_layout(polar=dict(radialaxis=dict(visible=True)), height=280, margin=dict(l=40, r=40, t=20, b=20))
                                    st.plotly_chart(fig_big, use_container_width=True)
                                st.caption(f"**{chosen}** · {sel.get('subpattern', '')} · 相似度 {sel.get('similarity_pct', 0)}%")
                                st.caption("_历史演化路径：若该案例有大运流年数据将在此展示（当前样本库暂无）。_")
                else:
                    st.caption("案例库暂无样本，请确认 registry/holographic_pattern/A-01.json 中 benchmarks 已配置。")
            else:
                st.json({k: round(pt.get(k, 0), 3) for k in ["E", "O", "M", "S", "R"]})
                if not retriever:
                    st.caption("_案例检索器未就绪；请确认 A-01.json 存在。_")
                else:
                    st.caption("_当前无 5D 坐标时无法检索相似案例。_")
            # 027/028: 奇点样板 + 英雄榜大模型剖析
            if retriever and retriever.case_count > 0:
                singularities = retriever.get_singularities(limit=10)
                if singularities:
                    hall = {}
                    try:
                        _hof = Path(__file__).resolve().parent.parent.parent / "registry" / "holographic_pattern" / "A-01_hall_of_fame.json"
                        if _hof.exists():
                            import json as _json
                            with open(_hof, "r", encoding="utf-8") as _f:
                                _d = _json.load(_f)
                            for _s in _d.get("singularities", []):
                                hall[_s.get("ref", "")] = _s.get("analysis", "")
                    except Exception:
                        pass
                    with st.expander("⭐ 奇点样板 (Golden / Extreme Cases)", expanded=False):
                        st.caption("案例库中预先标记的代表性命例；若已运行英雄榜脚本则展示大模型深度剖析。")
                        for s in singularities:
                            ref, sp = s.get("ref", ""), s.get("subpattern", "")
                            pt_s = s.get("point", [])
                            if isinstance(pt_s, dict):
                                pt_s = [pt_s.get(k, 0) for k in ["E", "O", "M", "S", "R"]]
                            st.caption(f"**{ref}** · {sp}" + (f" · 5D={[round(x, 2) for x in pt_s]}" if len(pt_s) == 5 else ""))
                            if ref and hall.get(ref):
                                st.write(hall[ref])

        # --- 029: 流形修复建议 (Manifold Repair) ---
        if retriever and pt and retriever.case_count > 0:
            pathway = analyze_repair_pathway(retriever, pt, top_repair=5)
            deficit_info = pathway.get("deficit_info")
            repair_vector = pathway.get("repair_vector")
            if deficit_info and deficit_info.get("deficit", 0) > 0:
                st.markdown(f"""
                    <div style="{GLASS_STYLE} padding: 12px; margin: 1rem 0; border-left: 4px solid {COLORS['mystic_gold']};">
                        <h4 style="color: {COLORS['mystic_gold']}; margin: 0;">🔧 流形修复建议 (Manifold Repair)</h4>
                    </div>
                """, unsafe_allow_html=True)
                axis_label = deficit_info.get("axis_label", deficit_info.get("axis", ""))
                st.caption(f"**你的物理瓶颈**：{deficit_info.get('axis', '')} 轴（{axis_label}）")
                st.caption(f"当前值：{deficit_info.get('current')} → 参考质心：{deficit_info.get('target_from_centroid')}（建议补齐：**+{deficit_info.get('deficit', 0):.2f}**）")
                if repair_vector:
                    delta = repair_vector.get("delta_vector") or {}
                    st.caption(f"**目标位移 ΔV**：{delta}")
                    if is_ai_engine_available():
                        if st.button("🧭 生成 AI 导航建议", key="btn_repair_strategy"):
                            with st.spinner("大模型生成修复路径…"):
                                blurb = generate_repair_strategy(
                                    deficit_info.get("axis", "O"),
                                    delta,
                                    user_point=pt,
                                )
                            if blurb.get("success"):
                                st.success(blurb.get("text", ""))
                            else:
                                st.error(blurb.get("error", "生成失败"))
                else:
                    st.caption("_样本库中暂无与您相似且在该轴成功修复的案例，可扩大检索或待全量索引后重试。_")
            elif deficit_info and deficit_info.get("deficit", 0) <= 0:
                st.caption("_当前流形相对质心无显著短板，无需修复建议。_")

        # --- [古籍印证] 模块：向量池检索 ---
        st.markdown(f"""
            <div style="{GLASS_STYLE} padding: 12px; margin: 1rem 0; border-left: 4px solid {COLORS['crystal_blue']};">
                <h4 style="color: {COLORS['mystic_gold']}; margin: 0;">📚 古籍印证 (Classical Match)</h4>
            </div>
        """, unsafe_allow_html=True)
        try:
            from data.vector_db import find_classical_match
            classical = find_classical_match(inference, n_results=1)
            if classical:
                st.markdown(f"**{classical.get('source', '古籍')}** · {classical.get('chapter', '')}")
                st.write(classical.get("text", ""))
                # 026: 逻辑溯源 - 点击后大模型解析「为什么古人这么说」
                if is_ai_engine_available():
                    if st.button("🕵️ 物理逻辑解析（为什么古人这么说）", key="btn_classical_logic"):
                        with st.spinner("大模型解析中…"):
                            _res = explain_classical_logic(
                                classical.get("text", ""),
                                source=classical.get("source", "古籍"),
                            )
                        if _res.get("success"):
                            st.success(_res.get("text", ""))
                        else:
                            st.error(_res.get("error", "解析失败"))
            else:
                st.caption("暂无匹配古籍条目，可向 data/vector_db/raw 添加文本并执行入库。")
        except Exception as e:
            logger.debug("古籍检索跳过: %s", e)
            st.caption("古籍向量库未就绪或未入库，请参考 data/vector_db/README.md 预热。")

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
