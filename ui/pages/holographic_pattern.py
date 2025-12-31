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
from core.narrator import generate_holographic_report, generate_timeline_insight

# 配置日志
logger = logging.getLogger(__name__)

def render():
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
    
    apply_custom_header("全息格局观测站", "FDS-V1.5 Holographic Manifold Observatory")
    
    controller = HolographicPatternController()
    
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
        
        st.markdown("### 👤 观测档案")
        profiles = pm.get_all()
        profile_names = {p['name']: p['id'] for p in profiles}
        profile_names['演示：羊刃架杀·经典案例'] = 'demo'
        profile_names['演示：将星本部 (Standard)'] = 'demo_standard'
        profile_names['演示：库刃爆发 (Vault)'] = 'demo_vault'
        profile_names['演示：D-01 正财格 (Standard)'] = 'demo_d01_std'
        profile_names['演示：D-01 从财格 (Surrender)'] = 'demo_d01_surrender'
        profile_names['演示：D-01 墓库格 (Vault)'] = 'demo_d01_vault'
        profile_names['演示：D-02 偏财格 (Standard Tycoon)'] = 'demo_d02_std'
        profile_names['演示：D-02 资本大鳄 (The Syndicate)'] = 'demo_d02_syndicate'
        profile_names['演示：D-02 乱世枭雄 (The Collider)'] = 'demo_d02_collider'
        
        current_profile_id = st.session_state.get('current_profile_id', list(profile_names.values())[0] if profile_names else 'demo')
        # Ensure current_profile_id is valid
        if current_profile_id not in profile_names.values():
            current_profile_id = 'demo'
            
        selected_profile_name = st.selectbox(
            "选择档案", 
            options=list(profile_names.keys()), 
            index=list(profile_names.values()).index(current_profile_id),
            key=f"{PAGE_PREFIX}profile_select"  # Page-specific key
        )
        selected_profile_id = profile_names[selected_profile_name]
        st.session_state['current_profile_id'] = selected_profile_id
        
        # --- 加载档案数据用于显示 ---
        _profile_preview = None
        if selected_profile_id == 'demo':
            _profile_preview = {
                'name': '羊刃架杀·经典案例', 'gender': '男', 
                'year': 2000,
                'year_pillar': '庚辰', 'month_pillar': '乙酉', 
                'day_pillar': '庚子', 'hour_pillar': '丙戌',
                'day_master': '庚'
            }
        elif selected_profile_id == 'demo_standard':
            _profile_preview = {
                'name': '将星本部 (Standard)', 'gender': '男', 
                'year_pillar': '庚辰', 'month_pillar': '乙酉', 
                'day_pillar': '庚子', 'hour_pillar': '丙戌',
                'day_master': '庚'
            }
        elif selected_profile_id == 'demo_vault':
            _profile_preview = {
                'name': '库刃爆发 (Vault)', 'gender': '男', 
                'year_pillar': '壬辰', 'month_pillar': '庚戌', 
                'day_pillar': '庚寅', 'hour_pillar': '丙戌',
                'day_master': '庚'
            }
        elif selected_profile_id == 'demo_d01_std':
            _profile_preview = {
                'name': 'D-01 正财标准', 'gender': '男', 
                'year_pillar': '庚辰', 'month_pillar': '乙酉', 
                'day_pillar': '丁丑', 'hour_pillar': '庚子',
                'day_master': '丁'
            }
        elif selected_profile_id == 'demo_d01_surrender':
            _profile_preview = {
                'name': 'D-01 弃命从财', 'gender': '男', 
                'year_pillar': '庚申', 'month_pillar': '辛酉', 
                'day_pillar': '丙申', 'hour_pillar': '戊子',
                'day_master': '丙'
            }
        elif selected_profile_id == 'demo_d01_vault':
            _profile_preview = {
                'name': 'D-01 顶级墓库', 'gender': '男', 
                'year_pillar': '戊戌', 'month_pillar': '乙未', 
                'day_pillar': '甲辰', 'hour_pillar': '庚午',
                'day_master': '甲'
            }
        elif selected_profile_id == 'demo_d02_std':
            _profile_preview = {
                'name': 'D-02 偏财大亨', 'gender': '男',
                'year_pillar': '甲子', 'month_pillar': '壬申',
                'day_pillar': '丙寅', 'hour_pillar': '己丑',
                'day_master': '丙'
            }
        elif selected_profile_id == 'demo_d02_syndicate':
            _profile_preview = {
                'name': 'D-02 资本大鳄', 'gender': '男',
                'year_pillar': '丙午', 'month_pillar': '丙申',
                'day_pillar': '丙午', 'hour_pillar': '庚寅',
                'day_master': '丙'
            }
        elif selected_profile_id == 'demo_d02_collider':
            _profile_preview = {
                'name': 'D-02 乱世枭雄', 'gender': '男',
                'year_pillar': '庚申', 'month_pillar': '甲申',
                'day_pillar': '甲寅', 'hour_pillar': '庚午',
                'day_master': '甲'
            }
        else:
            _profile_preview = next((p for p in profiles if p['id'] == selected_profile_id), None)
            # Calculate pillars if not stored in profile
            if _profile_preview and not _profile_preview.get('year_pillar'):
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
        hierarchy = controller.get_pattern_hierarchy()
        if not hierarchy:
            st.info("📋 待命状态")
            return
            
        pattern_options = {}
        for p_id, data in sorted(hierarchy.items()):
            main = data['main']
            pattern_options[f"{main['icon']} {main['name_cn']}"] = p_id
            for sub in data['subs']:
                pattern_options[f"  └ {sub['icon']} {sub['name_cn']}"] = sub['id']
                
        selected_pattern_name = st.selectbox(
            "核心全息方案", 
            options=list(pattern_options.keys()),
            key=f"{PAGE_PREFIX}pattern_select"  # Page-specific key
        )
        selected_pattern_id = pattern_options[selected_pattern_name]
        
        pattern_info = controller.get_pattern_by_id(selected_pattern_id)
        if pattern_info:
            st.markdown(f"""
            <div style="background: rgba(64, 224, 208, 0.05); border-left: 3px solid #40e0d0; padding: 10px; font-size: 13px;">
                <b>原型</b>: {pattern_info.get('meta_info', {}).get('physics_prototype', 'Standard Model')}<br>
                <b>版本</b>: {pattern_info.get('version', 'N/A')} | <b>状态</b>: 已校准
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        st.caption("FDS-V1.5.2 Observatory Kernel")

    # --- Main Content Area ---
    # Load Profile Data
    profile_data = None
    if selected_profile_id == 'demo':
        # [V1.5.1 Verified] 真正的"羊刃架杀"经典案例
        # 庚日主的羊刃在酉(月支) + 七杀丙火透干(时干)
        # 庚辰年 乙酉月 庚子日 丙戌时 - 刃杀俱全，结构完整
        profile_data = {
            'name': '羊刃架杀·经典案例', 'gender': '男', 'year': 2000,
            'year_pillar': '庚辰', 'month_pillar': '乙酉', 'day_pillar': '庚子', 'hour_pillar': '丙戌',
            'day_master': '庚'
        }
    elif selected_profile_id == 'demo_standard':
        profile_data = {
            'name': '将星本部 (Standard)', 'gender': '男',
            'year_pillar': '庚辰', 'month_pillar': '乙酉', 'day_pillar': '庚子', 'hour_pillar': '丙戌',
            'day_master': '庚'
        }
    elif selected_profile_id == 'demo_vault':
        profile_data = {
            'name': '库刃爆发 (Vault)', 'gender': '男',
            'year_pillar': '壬辰', 'month_pillar': '庚戌', 'day_pillar': '庚寅', 'hour_pillar': '丙戌',
            'day_master': '庚'
        }
    elif selected_profile_id == 'demo_d01_std':
        profile_data = {'name': 'D-01 正财标准', 'gender': '男', 'year_pillar': '庚辰', 'month_pillar': '乙酉', 'day_pillar': '丁丑', 'hour_pillar': '庚子', 'day_master': '丁'}
    elif selected_profile_id == 'demo_d01_surrender':
        profile_data = {'name': 'D-01 弃命从财', 'gender': '男', 'year_pillar': '庚申', 'month_pillar': '辛酉', 'day_pillar': '丙申', 'hour_pillar': '戊子', 'day_master': '丙'}
    elif selected_profile_id == 'demo_d01_vault':
        profile_data = {'name': 'D-01 顶级墓库', 'gender': '男', 'year_pillar': '戊戌', 'month_pillar': '乙未', 'day_pillar': '甲辰', 'hour_pillar': '庚午', 'day_master': '甲'}
    elif selected_profile_id == 'demo_d02_std':
        profile_data = {'name': 'D-02 偏财大亨', 'gender': '男', 'year_pillar': '甲子', 'month_pillar': '壬申', 'day_pillar': '丙寅', 'hour_pillar': '己丑', 'day_master': '丙'}
    elif selected_profile_id == 'demo_d02_syndicate':
        profile_data = {'name': 'D-02 资本大鳄', 'gender': '男', 'year_pillar': '丙午', 'month_pillar': '丙申', 'day_pillar': '丙午', 'hour_pillar': '庚寅', 'day_master': '丙'}
    elif selected_profile_id == 'demo_d02_collider':
        profile_data = {'name': 'D-02 乱世枭雄', 'gender': '男', 'year_pillar': '庚申', 'month_pillar': '甲申', 'day_pillar': '甲寅', 'hour_pillar': '庚午', 'day_master': '甲'}
    else:
        profile_data = next((p for p in profiles if p['id'] == selected_profile_id), None)
        
    if not profile_data:
        st.error("❌ 档案读取失败")
        return

    # Initialize BaziProfile
    try:
        profile_obj = None
        gender = 1 if profile_data.get('gender') == '男' else 0
        
        # 1. Try Real Profile (Has Birth Date)
        if profile_data.get('year') and profile_data.get('month') and profile_data.get('day'):
            try:
                birth_date = datetime(int(profile_data['year']), int(profile_data['month']), int(profile_data['day']), int(profile_data.get('hour', 12)))
                profile_obj = BaziProfile(birth_date, gender)
            except Exception:
                pass
        
        # 2. Try Virtual Profile (Pillars Only)
        if not profile_obj and profile_data.get('year_pillar'):
            from core.bazi_profile import VirtualBaziProfile
            pillars = {
                'year': profile_data.get('year_pillar', '??'),
                'month': profile_data.get('month_pillar', '??'),
                'day': profile_data.get('day_pillar', '??'),
                'hour': profile_data.get('hour_pillar', '??')
            }
            profile_obj = VirtualBaziProfile(pillars, gender=gender)
            
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

    # --- Step 3: High-Precision Dashboard ---
    st.markdown("### 🌟 FDS-V1.5 观测报告")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("SAI (总对齐力)", f"{sai:.4f}")
    m2.metric("M-Dist (马氏距离)", f"{recognition.get('mahalanobis_dist', 0):.4f}")
    m3.metric("Precision (精密评分)", f"{recognition.get('precision_score', 0):.4f}")
    
    # [V2.5] Routing Trace
    sub_id = result.get('sub_id')
    if sub_id:
        st.caption(f"🛣️ **路由追踪**: {selected_pattern_id} ➔ `{sub_id}` (奇点激活)")
    
    p_type = recognition.get('pattern_type', 'UNKNOWN')
    status_color = "#40e0d0" if "STANDARD" in p_type or "ACTIVATED" in p_type else "#ff6b6b"
    m4.markdown(f"""
    <div style="background: rgba(0,0,0,0.1); padding: 5px; border-radius: 5px; text-align: center; border-left: 3px solid {status_color};">
        <div style="font-size: 10px; color: #888;">识别态</div>
        <div style="font-size: 14px; font-weight: bold; color: {status_color};">{p_type}</div>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"🔮 **AI 判言**: {recognition.get('description', '观测信号稳定')}")

    # --- Step 4: Observatory (3D Manifold) ---
    st.markdown("---")
    col_obs, col_dim = st.columns([2, 1])
    
    with col_obs:
        st.markdown("#### 🪐 全息命运晶体 (Fate Tensor Crystal)")
        ref_vector = pattern_info.get('feature_anchors', {}).get('standard_manifold', {}).get('mean_vector')
        fig = render_5d_manifold(projection, ref_vector, p_type, result.get('pattern_name'))
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
        st.write(pattern_info.get('semantic_seed', {}).get('description', '无扩展描述'))

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
        
        # [QGA V2.5.5] Use cache to avoid 60s wait for remote LLM
        @st.cache_data(ttl=3600, show_spinner=False)
        def get_cached_report(data, pattern_name, state):
            return generate_holographic_report(data, pattern_name, state)

        with st.status("🔮 正在解析全息轨迹...", expanded=True) as status:
            st.write("🌌 正在提取 5D 张量特征...")
            report_data = {
                'projection': current_data['projection'], 
                'alpha': current_data['alpha'], 
                'pattern_state': current_data['pattern_state']
            }
            
            st.write("🧠 正在请求远程星际语义引擎 (Qwen2.5:3b)...")
            st.info("💡 首次生成需 30-60s，请稍候...")
            
            report = get_cached_report(
                report_data,
                result.get('pattern_name'), 
                current_data['pattern_state'].get('state', 'STABLE')
            )
            status.update(label="✅ 轨迹报告联通完毕", state="complete", expanded=False)
            
        st.markdown(report)
        with st.expander("📝 物理公理矩阵 (Transfer Matrix V2.5)"):
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
                st.warning("该格局尚未升级至 V2.5 矩阵协议")

        with st.expander("更多周期性判析"):
            st.write(generate_timeline_insight(timeline_data, result.get('pattern_name')))

if __name__ == "__main__":
    render()
