import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import logging
import os

from controllers.holographic_pattern_controller import HolographicPatternController
from core.bazi_profile import BaziProfile
from ui.components.holographic_manifold import render_5d_manifold, get_manifold_description
from ui.components.phase_timeline import render_phase_timeline
from ui.components.theme import COLORS, apply_custom_header
from core.narrator import generate_holographic_report, generate_timeline_insight, stream_holographic_report

# 配置日志
logger = logging.getLogger(__name__)

# --- V1.5.3 Demo Definition Matrix ---
# [V1.5.4 FIX] 修正四柱数据以确保匹配对应格局特征
# [V3.1 UPDATE] 基于全量51.8万样本扫描结果，更新为最佳匹配案例
# [V3.2 CLEANUP] 清理其他演示案例，仅保留A-03最佳匹配案例
DEMO_PROFILES = {
    'demo_a03_best_match': {
        # 基于全量51.8万样本扫描的最佳匹配案例
        # UID: 257531, Precision: 0.9040, Mahalanobis Distance: 0.5096
        # Tensor: E=0.6649, O=0.5656, M=0.4890, S=0.5413, R=0.4939
        # SAI: 0.5510, Pattern Status: MATCHED
        # 注意：此案例基于扫描结果，实际Precision为0.9040，但演示八字仅为占位，计算结果可能不同
        'name': '演示：羊刃架杀·最佳匹配案例', 'gender': '男', 'year': 2000,
        'year_pillar': '庚午', 'month_pillar': '壬午', 'day_pillar': '戊午', 'hour_pillar': '甲寅',
        'day_master': '戊', 'desc': '全量扫描最佳匹配 (UID: 257531) | 扫描结果: Precision=0.9040, M-Dist=0.5096 | 注意：演示八字为占位，计算结果可能不同'
    }
}

def render():
    # [V3.0] 清除可能缓存的旧演示案例数据
    PAGE_PREFIX = "holo_"
    # 如果检测到DEMO_PROFILES已更新，清除相关session state
    if f'{PAGE_PREFIX}demo_id' in st.session_state:
        current_demo_id = st.session_state.get(f'{PAGE_PREFIX}demo_id')
        # 验证当前选择的demo是否仍然存在且有效
        if current_demo_id not in DEMO_PROFILES:
            # 如果选择的demo不存在，重置为默认值
            st.session_state[f'{PAGE_PREFIX}demo_id'] = 'demo_a03_best_match'
    
    st.markdown("""
    <style>
    .stMetric {
        background: rgba(255, 255, 255, 0.03);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    .stMetric:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: #40e0d0;
        transform: translateY(-2px);
    }
    .collapse-warn { color: #ff4b4b; font-weight: bold; animation: collapse-blink 1s ease-in-out infinite; }
    @keyframes collapse-blink { 0%,100% { opacity: 1; } 50% { opacity: 0.6; } }
    .report-card {
        background: rgba(0, 0, 0, 0.2);
        border-left: 5px solid #40e0d0;
        padding: 20px;
        border-radius: 5px;
        margin: 10px 0;
    }
    /* Animated Gradient Background for Header */
    .css-10trblm {
        background: linear-gradient(-45deg, #000428, #004e92, #000000, #1c1c1c);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    apply_custom_header("全息格局观测站", "FDS-V4.0 Holographic Manifold Observatory")
    
    controller = HolographicPatternController()

    # --- 格局审计看板（FDS SOP V4.0）：已审计 / 在审计 格局一览 ---
    fds_patterns = controller.get_fds_sop_patterns()
    if fds_patterns:
        st.markdown("### 🏛️ 全息格局体系（FDS SOP V4.0）")
        st.caption("来自 registry/holographic_pattern/ 的已审计与在审计格局")
        cols = st.columns(min(len(fds_patterns), 4))
        for i, p in enumerate(fds_patterns):
            c = cols[i % len(cols)]
            with c:
                status_color = "#22c55e" if p["status"] == "已审计" else "#f59e0b"
                st.markdown(f"""
                <div style="background: rgba(64, 224, 208, 0.06); border: 1px solid rgba(64, 224, 208, 0.2); 
                    border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                    <div style="font-weight: 600; color: #e0e0e0;">{p['pattern_id']} · {p['name_cn']}</div>
                    <div style="font-size: 12px; color: #9ca3af;">版本 {p['version']}</div>
                    <span style="display: inline-block; margin-top: 6px; padding: 2px 8px; border-radius: 6px; 
                        font-size: 11px; background: {status_color}22; color: {status_color};">{p['status']}</span>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("---")
    
    # --- Sidebar: Profile & Pattern Selection ---
    # [MVC ISOLATION] This page manages its own sidebar completely independently
    from core.profile_manager import ProfileManager
    pm = ProfileManager()
    
    # Force sidebar to only show THIS page's content
    # Use unique keys with page prefix to avoid widget conflicts
    PAGE_PREFIX = "holo_"
    
    # [CRITICAL FIX] Clear any residual sidebar content from other pages
    # by overwriting with empty placeholders before rendering our content
    with st.sidebar:
        # This is the ONLY sidebar block for this page
        # All content must be within this block
        
        st.markdown("### 👤 观测中心")
        
        profiles = pm.get_all()
        real_profile_names = {p['name']: p['id'] for p in profiles}
        demo_profile_names = {v['name']: k for k, v in DEMO_PROFILES.items()}
        
        tab_real, tab_demo = st.tabs(["🏛️ 观测档案", "🎞️ 演示案例"])
        
        selected_profile_id = None
        profile_source = 'real'
        
        with tab_real:
            if not real_profile_names:
                st.caption("⚠️ 暂无档案")
            else:
                current_id = st.session_state.get(f'{PAGE_PREFIX}real_id')
                if not current_id or current_id not in real_profile_names.values():
                    current_id = list(real_profile_names.values())[0]
                
                sel_real = st.selectbox(
                    "选择本地档案",
                    options=list(real_profile_names.keys()),
                    index=list(real_profile_names.values()).index(current_id),
                    key=f"{PAGE_PREFIX}real_select"
                )
                st.session_state[f'{PAGE_PREFIX}real_id'] = real_profile_names[sel_real]
                # Default source is real if this tab is interacted with or session state says so
                if st.session_state.get(f'{PAGE_PREFIX}active_tab') == 'real' or not st.session_state.get(f'{PAGE_PREFIX}active_tab'):
                    selected_profile_id = real_profile_names[sel_real]
                    profile_source = 'real'

        with tab_demo:
            current_demo_id = st.session_state.get(f'{PAGE_PREFIX}demo_id')
            if not current_demo_id or current_demo_id not in demo_profile_names.values():
                current_demo_id = list(demo_profile_names.values())[0]
            
            sel_demo = st.selectbox(
                "选择演示案例",
                options=list(demo_profile_names.keys()),
                index=list(demo_profile_names.values()).index(current_demo_id),
                key=f"{PAGE_PREFIX}demo_select"
            )
            
            # [V3.2 FIX] 检测选择变化，强制更新session state并触发重新渲染
            new_demo_id = demo_profile_names[sel_demo]
            prev_demo_id = st.session_state.get(f'{PAGE_PREFIX}demo_id')
            
            # 立即更新demo_id
            st.session_state[f'{PAGE_PREFIX}demo_id'] = new_demo_id
            
            # 如果选择改变了，且当前在演示案例tab，立即更新并触发重新渲染
            if prev_demo_id != new_demo_id and st.session_state.get(f'{PAGE_PREFIX}active_tab') == 'demo':
                st.session_state['current_profile_id'] = new_demo_id
                st.session_state['current_profile_source'] = 'demo'
                st.rerun()  # 强制重新渲染
            st.caption(f"💡 {DEMO_PROFILES[new_demo_id]['desc']}")
            
            # Simple radio to switch active source
            prev_active_tab = st.session_state.get(f'{PAGE_PREFIX}active_tab', 'real')
            source_opt = st.radio("当前数据源", ["实测档案", "演示案例"], 
                                index=0 if prev_active_tab == 'real' else 1,
                                horizontal=True, key=f"{PAGE_PREFIX}source_toggle")
            
            # [V3.2 FIX] 检测数据源切换，强制更新
            new_active_tab = 'real' if source_opt == "实测档案" else 'demo'
            if prev_active_tab != new_active_tab:
                st.session_state[f'{PAGE_PREFIX}active_tab'] = new_active_tab
                # 立即更新选中的profile
                if new_active_tab == 'demo':
                    current_demo_id = st.session_state.get(f'{PAGE_PREFIX}demo_id', new_demo_id)
                    st.session_state['current_profile_id'] = current_demo_id
                    st.session_state['current_profile_source'] = 'demo'
                    st.rerun()  # 强制重新渲染
                elif new_active_tab == 'real' and real_profile_names:
                    real_id = st.session_state.get(f'{PAGE_PREFIX}real_id', list(real_profile_names.values())[0])
                    st.session_state['current_profile_id'] = real_id
                    st.session_state['current_profile_source'] = 'real'
                    st.rerun()  # 强制重新渲染
            
            if source_opt == "实测档案":
                st.session_state[f'{PAGE_PREFIX}active_tab'] = 'real'
                # fallback if real is empty
                if real_profile_names:
                    selected_profile_id = st.session_state.get(f'{PAGE_PREFIX}real_id')
                    profile_source = 'real'
                else:
                    st.error("无法切换：实测档案为空")
                    selected_profile_id = new_demo_id
                    profile_source = 'demo'
            else:
                st.session_state[f'{PAGE_PREFIX}active_tab'] = 'demo'
                selected_profile_id = new_demo_id
                profile_source = 'demo'

        if not selected_profile_id:
            # Final fallback
            if st.session_state.get(f'{PAGE_PREFIX}active_tab') == 'demo' or not real_profile_names:
                selected_profile_id = st.session_state.get(f'{PAGE_PREFIX}demo_id', 'demo_a03_best_match')
                profile_source = 'demo'
            else:
                selected_profile_id = st.session_state.get(f'{PAGE_PREFIX}real_id')
                profile_source = 'real'

        st.session_state['current_profile_id'] = selected_profile_id
        st.session_state['current_profile_source'] = profile_source
        
        # --- 加载档案数据用于显示 ---
        _profile_preview = None
        if profile_source == 'real':
            _profile_preview = next((p for p in profiles if p['id'] == selected_profile_id), None)
        else:
            _profile_preview = DEMO_PROFILES.get(selected_profile_id)

        # [V3.0 FIX] 仅当没有四柱数据时才从year计算，避免覆盖已有的正确四柱
        # Calculate pillars if not stored in profile (only for display purposes)
        if _profile_preview and not _profile_preview.get('year_pillar'):
            # 只有当确实没有year_pillar时，才尝试从year计算
            if _profile_preview.get('year') and _profile_preview.get('month') and _profile_preview.get('day'):
                try:
                    birth_date = datetime(
                        int(_profile_preview.get('year', 2000)),
                        int(_profile_preview.get('month', 1)),
                        int(_profile_preview.get('day', 1)),
                        int(_profile_preview.get('hour', 12))
                    )
                    gender_val = 1 if _profile_preview.get('gender') == '男' else 0
                    calc_profile = BaziProfile(birth_date, gender_val)
                    pillars = calc_profile.pillars
                    _profile_preview['year_pillar'] = pillars.get('year', '??')
                    _profile_preview['month_pillar'] = pillars.get('month', '??')
                    _profile_preview['day_pillar'] = pillars.get('day', '??')
                    _profile_preview['hour_pillar'] = pillars.get('hour', '??')
                    _profile_preview['day_master'] = calc_profile.day_master
                except Exception as e:
                    st.caption(f"⚠️ 四柱计算异常: {str(e)[:30]}")
        
        # --- 显示原局八字 (四柱) ---
        if _profile_preview:
            st.markdown("#### 📜 原局四柱")
            p_cols = st.columns(4)
            pillars_info = [
                ('年', _profile_preview.get('year_pillar', '??')),
                ('月', _profile_preview.get('month_pillar', '??')),
                ('日', _profile_preview.get('day_pillar', '??')),
                ('时', _profile_preview.get('hour_pillar', '??'))
            ]
            for i, (label, pillar) in enumerate(pillars_info):
                with p_cols[i]:
                    stem = pillar[0] if len(pillar) >= 1 else '?'
                    branch = pillar[1] if len(pillar) >= 2 else '?'
                    st.markdown(f"""<div style="text-align:center;padding:3px;background:rgba(255,255,255,0.05);border-radius:5px;">
                        <div style="font-size:9px;color:#888;">{label}柱</div>
                        <div style="font-size:16px;font-weight:bold;color:#FFD700;">{stem}</div>
                        <div style="font-size:16px;color:#87CEEB;">{branch}</div>
                    </div>""", unsafe_allow_html=True)
            
            dm = _profile_preview.get('day_master', _profile_preview.get('day_pillar', '??')[0])
            st.caption(f"**日主**: {dm} | **性别**: {_profile_preview.get('gender', '男')}")
            
            # --- 时空视窗 ---
            st.markdown("#### ⏱️ 时空视窗")
            current_year = datetime.now().year
            sidebar_year = st.select_slider("观测年份", options=list(range(1950, 2060)), value=current_year, key=f"{PAGE_PREFIX}year_slider")
            st.session_state[f'{PAGE_PREFIX}selected_year'] = sidebar_year
            
            # --- 地理场修正 (Geo Bias) ---
            from ui.pages.quantum_lab import GEO_CITY_MAP
            profile_city = _profile_preview.get('city', 'None') if _profile_preview else 'None'
            city_options = ["None"] + list(GEO_CITY_MAP.keys())
            city_idx = city_options.index(profile_city) if profile_city in city_options else 0
            selected_city = st.selectbox("🌍 地理场修正", options=city_options, index=city_idx, key=f"{PAGE_PREFIX}geo_select")
            st.session_state[f'{PAGE_PREFIX}selected_city'] = selected_city
            
            # --- 计算大运和流年 ---
            try:
                from lunar_python import Solar
                from core.bazi_profile import VirtualBaziProfile
                
                gender_val = 1 if _profile_preview.get('gender') == '男' else 0
                current_luck = '??'
                luck_start_age = 0
                birth_year = _profile_preview.get('year')
                profile_for_luck = None
                
                # 方案1: 如果有出生日期，使用 BaziProfile
                if birth_year and _profile_preview.get('month') and _profile_preview.get('day'):
                    try:
                        profile_for_luck = BaziProfile(
                            datetime(int(birth_year), int(_profile_preview.get('month', 1)), 
                                   int(_profile_preview.get('day', 1)), int(_profile_preview.get('hour', 12))),
                            gender_val
                        )
                    except:
                        pass
                
                # 方案2: 如果只有四柱，使用 VirtualBaziProfile 反推
                if not profile_for_luck and _profile_preview.get('year_pillar'):
                    try:
                        pillars = {
                            'year': _profile_preview.get('year_pillar', '??'),
                            'month': _profile_preview.get('month_pillar', '??'),
                            'day': _profile_preview.get('day_pillar', '??'),
                            'hour': _profile_preview.get('hour_pillar', '??')
                        }
                        profile_for_luck = VirtualBaziProfile(pillars, gender=gender_val)
                    except:
                        pass
                
                # 使用 profile 获取大运
                if profile_for_luck:
                    current_luck = profile_for_luck.get_luck_pillar_at(sidebar_year)
                    # 获取起运年龄
                    if hasattr(profile_for_luck, 'get_luck_cycles'):
                        cycles = profile_for_luck.get_luck_cycles()
                        for cycle in cycles:
                            if cycle.get('pillar') == current_luck:
                                luck_start_age = cycle.get('start_age', 0)
                                break
                
                # 流年干支
                solar = Solar.fromYmd(sidebar_year, 6, 15)
                annual_pillar = solar.getLunar().getYearInGanZhi()
                
                st.markdown("#### 🌊 动态二柱")
                lp_cols = st.columns(2)
                with lp_cols[0]:
                    st.markdown(f"""<div style="text-align:center;padding:6px;background:rgba(138,43,226,0.15);border-radius:6px;border:1px solid rgba(138,43,226,0.4);">
                        <div style="font-size:9px;color:#BA55D3;">大运 ({luck_start_age}岁起)</div>
                        <div style="font-size:18px;font-weight:bold;color:#DDA0DD;">{current_luck[0] if len(current_luck)>=1 else '?'}</div>
                        <div style="font-size:18px;color:#E6E6FA;">{current_luck[1] if len(current_luck)>=2 else '?'}</div>
                    </div>""", unsafe_allow_html=True)
                with lp_cols[1]:
                    st.markdown(f"""<div style="text-align:center;padding:6px;background:rgba(255,140,0,0.15);border-radius:6px;border:1px solid rgba(255,140,0,0.4);">
                        <div style="font-size:9px;color:#FFA500;">流年 ({sidebar_year})</div>
                        <div style="font-size:18px;font-weight:bold;color:#FFD700;">{annual_pillar[0] if len(annual_pillar)>=1 else '?'}</div>
                        <div style="font-size:18px;color:#FFDAB9;">{annual_pillar[1] if len(annual_pillar)>=2 else '?'}</div>
                    </div>""", unsafe_allow_html=True)
            except Exception as e:
                st.caption(f"⚠️ 动态柱异常: {str(e)[:50]}")

        st.markdown("---")
        st.markdown("### 🧬 格局方案")
        # 仅使用 FDS SOP 格局列表，按 pattern_id 排序，避免与 hierarchy 重复
        fds_patterns_sidebar = controller.get_fds_sop_patterns()
        pattern_options = {}
        seen_ids = set()
        if fds_patterns_sidebar:
            for p in sorted(fds_patterns_sidebar, key=lambda x: x["pattern_id"]):
                pid = p["pattern_id"]
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                label = f"📐 {p['name_cn']} ({pid})"
                pattern_options[label] = pid
        if not pattern_options:
            st.info("📋 待命状态")
            return
        selected_pattern_name = st.selectbox(
            "核心全息方案",
            options=list(pattern_options.keys()),
            key=f"{PAGE_PREFIX}pattern_select"
        )
        selected_pattern_id = pattern_options[selected_pattern_name]
        # 添加占位空间，确保下拉菜单有足够空间向下展开
        st.markdown("<br>", unsafe_allow_html=True)
        
        pattern_info = controller.get_pattern_by_id(selected_pattern_id)
        fds_match = next((x for x in (fds_patterns_sidebar or []) if x["pattern_id"] == selected_pattern_id), None)
        if pattern_info:
            st.markdown(f"""
            <div style="background: rgba(64, 224, 208, 0.05); border-left: 3px solid #40e0d0; padding: 10px; font-size: 13px;">
                <b>原型</b>: {pattern_info.get('meta_info', {}).get('physics_prototype', 'Standard Model')}<br>
                <b>版本</b>: {pattern_info.get('version', 'N/A')} | <b>状态</b>: 已校准
            </div>
            """, unsafe_allow_html=True)
        elif fds_match:
            st.markdown(f"""
            <div style="background: rgba(64, 224, 208, 0.05); border-left: 3px solid #40e0d0; padding: 10px; font-size: 13px;">
                <b>格局</b>: {fds_match['name_cn']} ({fds_match['pattern_id']})<br>
                <b>版本</b>: {fds_match['version']} | <b>状态</b>: {fds_match['status']}
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        st.caption("FDS-V4.0 Observatory Kernel")

    # --- Main Content Area ---
    # Load Profile Data
    # [V3.2 FIX] 确保从最新的session state读取，避免使用旧的缓存值
    profile_source = st.session_state.get('current_profile_source', 'real')
    selected_profile_id = st.session_state.get('current_profile_id')
    
    # 如果selected_profile_id为空，尝试从tab状态获取
    if not selected_profile_id:
        if st.session_state.get(f'{PAGE_PREFIX}active_tab') == 'demo':
            selected_profile_id = st.session_state.get(f'{PAGE_PREFIX}demo_id', 'demo_a03_best_match')
            profile_source = 'demo'
        else:
            if real_profile_names:
                selected_profile_id = st.session_state.get(f'{PAGE_PREFIX}real_id', list(real_profile_names.values())[0])
                profile_source = 'real'
    
    # 确保session state是最新的
    st.session_state['current_profile_id'] = selected_profile_id
    st.session_state['current_profile_source'] = profile_source
    
    profile_data = None
    if profile_source == 'real':
        profile_data = next((p for p in profiles if p['id'] == selected_profile_id), None)
    else:
        profile_data = DEMO_PROFILES.get(selected_profile_id)
        
    if not profile_data:
        st.error(f"❌ 档案读取失败: profile_id={selected_profile_id}, source={profile_source}")
        # 调试信息
        st.json({
            'available_demos': list(DEMO_PROFILES.keys()),
            'current_id': selected_profile_id,
            'session_state': {
                'current_profile_id': st.session_state.get('current_profile_id'),
                'current_profile_source': st.session_state.get('current_profile_source'),
                'demo_id': st.session_state.get(f'{PAGE_PREFIX}demo_id'),
                'active_tab': st.session_state.get(f'{PAGE_PREFIX}active_tab')
            }
        })
        return

    # --- 格局详情（FDS SOP）：已审计格局展示语义、子格局、强相关轴，并可调用 LLM 解读 ---
    pattern_detail = controller.get_fds_pattern_detail(selected_pattern_id)
    fds_status_for_selected = next((p["status"] for p in (fds_patterns or []) if p["pattern_id"] == selected_pattern_id), None)
    if pattern_detail:
        with st.expander("📜 格局详情（语义、子格局、强相关轴）", expanded=(fds_status_for_selected == "已审计")):
            meta = pattern_detail.get("meta_info") or {}
            rules = pattern_detail.get("classical_logic_rules") or {}
            subs = pattern_detail.get("sub_pattern_definitions") or []
            semantic = pattern_detail.get("semantic_core_dimensions") or {}
            strong = pattern_detail.get("strong_correlation") or []
            st.markdown(f"**{meta.get('chinese_name') or meta.get('display_name')}** · 版本 {pattern_detail.get('version', 'N/A')}")
            st.caption(meta.get("source_ref", ""))
            if rules.get("description"):
                st.markdown("#### 古典逻辑")
                st.markdown(rules["description"])
            if subs:
                st.markdown("#### 子格局")
                for s in subs:
                    st.markdown(f"- **{s.get('id', '')}** · {s.get('name', '')}")
            if semantic:
                st.markdown("#### 语义核心维度")
                for k, v in (semantic.items() if isinstance(semantic, dict) else []):
                    name = v.get("name", k) if isinstance(v, dict) else k
                    desc = v.get("classical_by_gemini") or v.get("definition") or str(v) if isinstance(v, dict) else str(v)
                    st.caption(f"**{name}**：{desc[:120]}{'…' if len(desc) > 120 else ''}")
            if strong:
                st.markdown("#### 强相关轴")
                st.markdown(", ".join([f"{x.get('ten_god')}→{x.get('dimension')}" for x in strong]))
            if fds_status_for_selected == "已审计":
                st.markdown("---")
                if st.button("🤖 用大模型生成格局解读", key=f"{PAGE_PREFIX}llm_overview_btn"):
                    from core.ai_engine import generate_pattern_overview, is_ai_engine_available
                    if is_ai_engine_available():
                        with st.spinner("大模型生成中…"):
                            res = generate_pattern_overview(selected_pattern_id, pattern_detail)
                        if res.get("success"):
                            st.session_state[f"{PAGE_PREFIX}llm_overview_text"] = res.get("text", "")
                            st.session_state[f"{PAGE_PREFIX}llm_overview_model"] = res.get("model", "")
                            st.rerun()
                        else:
                            st.error(res.get("error", "生成失败"))
                    else:
                        st.warning("未检测到 Ollama，无法生成解读")
                if st.session_state.get(f"{PAGE_PREFIX}llm_overview_text"):
                    st.markdown("**大模型格局解读**")
                    st.markdown(st.session_state[f"{PAGE_PREFIX}llm_overview_text"])
                    st.caption(f"由 {st.session_state.get(f'{PAGE_PREFIX}llm_overview_model', '')} 生成")
        st.markdown("---")

    # --- 双向匹配：档案↔格局（结合大运、流年、地域）---
    _year = st.session_state.get(f'{PAGE_PREFIX}selected_year', datetime.now().year)
    _city = st.session_state.get(f'{PAGE_PREFIX}selected_city', 'None')
    _city_param = _city if _city != "None" else None
    # 流年干支（仅依赖年份，供 dynamic_monitor 坍缩判定）
    try:
        from lunar_python import Solar
        _annual_pillar = Solar.fromYmd(int(_year), 6, 15).getLunar().getYearInGanZhi()
    except Exception:
        _annual_pillar = ""

    col_match1, col_match2 = st.columns(2)
    with col_match1:
        st.markdown("#### 📐 当前档案匹配的格局")
        st.caption("结合大运、流年、地域，按匹配度从高到低")
        patterns_for_profile = controller.get_patterns_for_profile(profile_data, year=_year, city=_city_param, top_k=20)
        if patterns_for_profile:
            from scripts.dynamic_monitor import run_dynamic_monitor
            for i, row in enumerate(patterns_for_profile[:15], 1):
                pid = row.get("pattern_id", "")
                md = row.get("match_degree", 0)
                collapse_alerts = run_dynamic_monitor(pid, _annual_pillar) if _annual_pillar else []
                collapse = next((a for a in collapse_alerts if a.get("alert") == "CRITICAL_STRUCTURE_COLLAPSE"), None)
                if i == 1 and collapse:
                    verdict = collapse.get("verdict", "刑伤突发，险境难支")
                    st.markdown(f"**{i}.** {row.get('chinese_name', '')} ({pid}) · 匹配度 <span class=\"collapse-warn\">**{md:.1f}%**</span> · D_M={row.get('D_M', 0):.4f}", unsafe_allow_html=True)
                    st.caption(f"🔴 **结构坍缩预警**: {verdict}")
                else:
                    st.markdown(f"**{i}.** {row.get('chinese_name', '')} ({pid}) · 匹配度 **{md:.1f}%** · D_M={row.get('D_M', 0):.4f}")
            if len(patterns_for_profile) > 15:
                st.caption(f"…共 {len(patterns_for_profile)} 个格局，仅展示前 15")
        else:
            st.caption("暂无匹配格局或档案无法解析四柱")
    with col_match2:
        st.markdown("#### 📂 当前格局集中的档案")
        st.caption("实测档案中归属该格局的命例，按匹配率从高到低")
        profiles_for_pattern = controller.get_profiles_for_pattern(selected_pattern_id, profiles, top_k_per_profile=60)
        if profiles_for_pattern:
            for i, row in enumerate(profiles_for_pattern[:15], 1):
                st.markdown(f"**{i}.** {row.get('name', '')} · 匹配率 **{row.get('match_rate', 0):.1f}%** · D_M={row.get('D_M', 0):.4f}")
            if len(profiles_for_pattern) > 15:
                st.caption(f"…共 {len(profiles_for_pattern)} 个档案，仅展示前 15")
        else:
            st.caption("暂无档案或档案库为空")
    st.markdown("---")

    # Initialize BaziProfile
    try:
        profile_obj = None
        gender = 1 if profile_data.get('gender') == '男' else 0
        
        # [V3.0 FIX] 优先使用四柱数据，避免用year字段重新计算导致错误
        # 1. Try Virtual Profile (Pillars Only) - 优先使用已提供的四柱
        if profile_data.get('year_pillar'):
            from core.bazi_profile import VirtualBaziProfile
            pillars = {
                'year': profile_data.get('year_pillar', '??'),
                'month': profile_data.get('month_pillar', '??'),
                'day': profile_data.get('day_pillar', '??'),
                'hour': profile_data.get('hour_pillar', '??')
            }
            profile_obj = VirtualBaziProfile(pillars, gender=gender)
        
        # 2. Fallback: Try Real Profile (Has Birth Date) - 仅当没有四柱数据时
        if not profile_obj and profile_data.get('year') and profile_data.get('month') and profile_data.get('day'):
            try:
                birth_date = datetime(int(profile_data['year']), int(profile_data['month']), int(profile_data['day']), int(profile_data.get('hour', 12)))
                profile_obj = BaziProfile(birth_date, gender)
            except Exception:
                pass
            
        if not profile_obj:
            raise ValueError("无法创建物理实体：缺少出生日期或四柱数据")
        
        # Derivce pillars from the calculated profile object
        p = profile_obj.pillars
        chart = [p['year'], p['month'], p['day'], p['hour']]
        day_master = profile_obj.day_master
    except Exception as e:
        st.error(f"❌ 物理实体初始化失败: {e}")
        return

    # --- Step 1: Spacetime Context ---
    # Year and GEO are now selected in sidebar, read from session state
    PAGE_PREFIX = "holo_"
    selected_year = st.session_state.get(f'{PAGE_PREFIX}selected_year', datetime.now().year)
    selected_city = st.session_state.get(f'{PAGE_PREFIX}selected_city', 'None')

    # Environment
    luck_pillar = profile_obj.get_luck_pillar_at(selected_year)
    year_pillar = profile_obj.get_year_pillar(selected_year)

    # --- Step 2: Core Calculation ---
    with st.spinner("量子演算中..."):
        result = controller.calculate_tensor_projection(
            pattern_id=selected_pattern_id,
            chart=chart,
            day_master=day_master,
            context={
                'luck_pillar': luck_pillar,
                'annual_pillar': year_pillar,
                'geo_city': selected_city if selected_city != "None" else None
            }
        )

    if 'error' in result:
        st.error(f"❌ 演算异常: {result['error']}")
        return

    projection = result['projection']
    recognition = result.get('recognition', {})
    sai = result.get('sai', 0.0)

    # --- Step 3: FDS 2.0 观测报告（static_atlas 流形追踪 + 识别态）---
    from core.manifold_trace import compute_dm_cloud
    trace = compute_dm_cloud(projection, top_k=3)
    overlay = trace.get("overlay") or []
    nearest = overlay[0] if overlay else {}
    d_m = nearest.get("D_M", 0)
    capture_id = nearest.get("pattern_id", "")
    capture_name = nearest.get("chinese_name", capture_id)
    # SOP V6.5：引力俘获模型 — 四级主权状态（PURE/VERIFIED/DRIFTING/BROKEN）
    capture_status = trace.get("capture_status") or nearest.get("status") or "BROKEN"
    capture_verdict = trace.get("capture_verdict") or nearest.get("verdict") or "格局坍缩，已脱离该质心引力井。"

    st.markdown("### 🌟 FDS 2.0 观测报告")
    st.caption("基于 60 格局静态图谱的流形距离 D_M 与叠加态（EDR_049 / SOP V6.5 引力俘获）")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("流形距离 D_M", f"{d_m:.4f}")
    m2.metric("捕获格局", f"{capture_id}" if capture_id else "—")
    m3.metric("系统对齐指数 SAI", f"{sai:.4f}")
    # 主权状态颜色：PURE/VERIFIED=绿，DRIFTING=黄，BROKEN=红
    _s = capture_status.upper()
    if _s in ("PURE", "VERIFIED"):
        _cap_color = "#22c55e"
    elif _s == "DRIFTING":
        _cap_color = "#f59e0b"
    else:
        _cap_color = "#ff4b4b"
    m4.markdown(f"""
    <div style="background: rgba(0,0,0,0.1); padding: 5px; border-radius: 5px; text-align: center; border-left: 3px solid {_cap_color};">
        <div style="font-size: 10px; color: #888;">主权状态</div>
        <div style="font-size: 14px; font-weight: bold; color: {_cap_color};">{capture_status}</div>
    </div>
    """, unsafe_allow_html=True)

    # SOP V6.5：BROKEN 时显示「格局坍缩、连接断开」红色区块
    if _s == "BROKEN":
        st.markdown(f"""
        <div class="collapse-warn" style="background: rgba(255,75,75,0.12); border: 1px solid #ff4b4b; border-radius: 8px; padding: 10px 12px; margin: 8px 0;">
            <div style="font-size: 12px; color: #ff6b6b;">⚠️ 格局坍缩 · 连接断开</div>
            <div style="font-size: 13px; color: #ff4b4b;">{capture_verdict}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.caption(f"**{capture_verdict}**")

    # SOP V6.4：Top1 格局卡片挂载 dynamic_monitor — 若触发 CRITICAL_STRUCTURE_COLLAPSE 则红色坍缩预警
    from scripts.dynamic_monitor import run_dynamic_monitor
    _alerts = run_dynamic_monitor((capture_id or "").strip(), year_pillar or "")
    _collapse = next((a for a in _alerts if a.get("alert") == "CRITICAL_STRUCTURE_COLLAPSE"), None)
    if _collapse:
        _verdict = _collapse.get("verdict", "刑伤突发，险境难支")
        _match_pct = round(100.0 / (1.0 + float(d_m)), 1) if d_m is not None else 0
        st.markdown(f"""
        <div class="collapse-warn" style="background: rgba(255,75,75,0.15); border: 1px solid #ff4b4b; border-radius: 8px; padding: 12px; margin: 10px 0;">
            <div style="font-size: 12px; color: #ff6b6b;">🔴 结构坍缩预警</div>
            <div style="font-size: 14px; font-weight: bold; color: #ff4b4b;">{_verdict}</div>
            <div style="font-size: 11px; color: #aaa;">当前捕获格局 {capture_id}（匹配度 <span class="collapse-warn">{_match_pct}%</span>）于流年 {year_pillar} 触刑，请关注应灾指引。</div>
        </div>
        """, unsafe_allow_html=True)

    # 叠加态（前 3 格局）+ SOP V6.5 每格主权状态
    if overlay:
        with st.expander("📊 流形叠加态（前 3 格局）", expanded=True):
            for i, o in enumerate(overlay):
                stt = (o.get("status") or "BROKEN").upper()
                st.markdown(f"**{i+1}.** {o.get('chinese_name', '')} ({o.get('pattern_id', '')}) · D_M={o.get('D_M', 0):.4f} · 权重 {o.get('probability', 0)*100:.1f}% · **{stt}**")

    sub_id = result.get('sub_id')
    if sub_id:
        st.caption(f"🛣️ **路由追踪**: {selected_pattern_id} ➔ `{sub_id}` (奇点激活)")
    st.info(f"🔮 **判言**: {recognition.get('description', '观测信号稳定')}")

    # --- Step 4: Observatory (3D Manifold) ---
    st.markdown("---")
    col_obs, col_dim = st.columns([2, 1])
    
    with col_obs:
        st.markdown("#### 🪐 全息命运晶体 (Fate Tensor Crystal)")
        _fa = (pattern_info or {}).get('feature_anchors') or {}
        _sm = _fa.get('standard_manifold') or {}
        ref_vector = _sm.get('mean_vector') if isinstance(_sm, dict) else None
        fig = render_5d_manifold(projection, ref_vector, p_type, result.get('pattern_name'), overlay=overlay)
        st.plotly_chart(fig, use_container_width=True, height=600)
        
    with col_dim:
        st.markdown("#### 维度洞察")
        desc = get_manifold_description(projection, p_type)
        st.markdown(f"🎭 **能量质量**: {desc['mass']}")
        st.markdown(f"🏰 **社会高度**: {desc['altitude']}")
        st.markdown(f"🔥 **核心温度**: {desc['temperature']}")
        st.markdown(f"🌀 **形态特征**: {desc['shape']}")
        st.markdown("---")
        st.markdown("#### 📜 格局解析")
        st.write(((pattern_info or {}).get('semantic_seed') or {}).get('description', '无扩展描述'))

    # --- Step 5: Dynamic Sensors ---
    st.markdown("---")
    st.markdown("### ⏱️ 动态演化传感器")
    from core.fate_simulator import simulate_trajectory
    timeline_data = simulate_trajectory(chart, day_master, selected_pattern_id, selected_year, 12, luck_pillar)
    
    # --- Fate Highlight Event Ribbon ---
    highlights = [d for d in timeline_data if d.get('pattern_state', {}).get('state') != 'STABLE']
    if highlights:
        h_cols = st.columns(len(highlights) if len(highlights) < 5 else 5)
        for i, h in enumerate(highlights[:5]):
            with h_cols[i]:
                state = h['pattern_state']['state']
                h_color = "#FFD700" if state == 'CRYSTALLIZED' else "#FF4B4B" if state == 'COLLAPSED' else "#F0F"
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); border-top: 3px solid {h_color}; padding: 10px; border-radius: 5px; text-align: center;">
                    <div style="font-size: 14px; font-weight: bold; color: {h_color};">{h['year']} {h['year_pillar']}</div>
                    <div style="font-size: 10px; color: #888;">{state}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.caption("✨ 未来12年结构场预测：结构保持稳定，无相变事件引发")

    t_tab1, t_tab2 = st.tabs(["🌊 能量流趋势", "🎙️ 轨迹报告"])
    with t_tab1:
        st.plotly_chart(render_phase_timeline(timeline_data), use_container_width=True)
    with t_tab2:
        current_data = next((d for d in timeline_data if d['year'] == selected_year), timeline_data[0])
        
        # [QGA V2.5.6] Dynamic Streaming LLM Report
        # Removed full-report cache to enable token-by-token streaming
        with st.status("🔮 正在实时解析全息轨迹...", expanded=True) as status:
            st.write("🌌 正在提取 5D 张量特征...")
            report_data = {
                'projection': current_data['projection'], 
                'alpha': current_data['alpha'], 
                'pattern_state': current_data['pattern_state']
            }
            
            # 从系统配置读取实时LLM模型名称
            from core.config_manager import ConfigManager
            config_manager = ConfigManager()
            current_model_name = config_manager.get("selected_model_name", "Qwen2.5")
            if not current_model_name:
                current_model_name = "Qwen2.5"  # 默认值
            
            st.write(f"🧠 正在联通星际语义引擎 ({current_model_name})...")
            
            # 使用自定义流式显示实现逐字逐句打字机效果
            report_container = st.empty()
            accumulated_text = ""
            
            # 使用生成器逐字符获取内容
            for char in stream_holographic_report(
                report_data,
                result.get('pattern_name'), 
                current_data['pattern_state'].get('state', 'STABLE')
            ):
                accumulated_text += char
                # 实时更新显示内容（支持Markdown格式）
                report_container.markdown(accumulated_text)
            
            status.update(label="✅ 轨迹报告解析完毕", state="complete", expanded=False)
        with st.expander("📝 物理公理矩阵 (Transfer Matrix V3.0)"):
            # Display the matrix that was actually used
            active_tm = result.get('transfer_matrix')
            if active_tm:
                rows = []
                for axis in ['E', 'O', 'M', 'S', 'R']:
                    row_data = active_tm.get(f'{axis}_row', {})
                    row_data['Axis'] = axis
                    rows.append(row_data)
                df_tm = pd.DataFrame(rows).set_index('Axis').fillna(0.0)
                st.dataframe(df_tm.style.format("{:.2f}"))
                st.caption("ℹ️ 该矩阵定义了十神能量向五维命运张量的转化率。正值代表促进，负值代表抑制。")
            else:
                st.warning("该格局尚未升级至 V3.0 矩阵协议")

        with st.expander("更多周期性判析"):
            st.write(generate_timeline_insight(timeline_data, result.get('pattern_name')))

if __name__ == "__main__":
    render()
