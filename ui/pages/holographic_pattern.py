"""
全息格局页面 (Holographic Pattern Page)
MVC View Layer - 只负责UI展示和用户交互

严格遵循MVC架构原则：
- 不包含业务逻辑
- 所有业务逻辑通过Controller API调用
- 只负责UI渲染和用户交互

注意：这是全新的"张量全息格局"系统，基于FDS-V1.1规范
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from ui.components.holographic_manifold import render_5d_manifold, get_manifold_description
from ui.components.phase_timeline import render_phase_timeline
from core.narrator import generate_holographic_report, generate_timeline_insight
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from controllers.holographic_pattern_controller import HolographicPatternController
from ui.components.theme import apply_custom_header, COLORS, GLASS_STYLE
from core.bazi_profile import BaziProfile
from core.profile_manager import ProfileManager

logger = logging.getLogger(__name__)


def render():
    """
    渲染全息格局页面
    
    严格遵循MVC：只负责UI渲染，业务逻辑由Controller处理
    """
    # --- 样式注入 ---
    st.markdown(f"""
    <style>
    .stApp {{
        background: radial-gradient(circle at 50% 50%, #0d0015 0%, #000000 100%);
        color: #e2e8f0;
    }}
    .pattern-card {{
        background: rgba(45, 27, 78, 0.3);
        border: 1px solid rgba(64, 224, 208, 0.2);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        transition: all 0.3s;
    }}
    .pattern-card:hover {{
        border-color: #40e0d0;
        box-shadow: 0 0 15px rgba(64, 224, 208, 0.2);
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # --- 标题 ---
    apply_custom_header("🌌 全息格局 (Holographic Pattern)", "张量全息格局系统 | 基于FDS-V1.1的五维张量投影")
    
    # --- 初始化Controller ---
    # 检查并重新创建controller（处理Streamlit缓存问题）
    if 'holographic_controller' not in st.session_state:
        st.session_state.holographic_controller = HolographicPatternController()
    
    controller = st.session_state.holographic_controller
    
    # 检查方法是否存在，如果不存在则重新创建（处理代码更新后的缓存问题）
    if not hasattr(controller, 'get_pattern_hierarchy') or not hasattr(controller, 'calculate_evolution'):
        logger.warning("Controller缺少必要方法，重新创建controller")
        st.session_state.holographic_controller = HolographicPatternController()
        controller = st.session_state.holographic_controller
    
    # 初始化ProfileManager（在侧边栏和主内容区都需要使用）
    profile_manager = ProfileManager()
    
    # --- 侧边栏：档案选择与格局选择 ---
    with st.sidebar:
        # === 档案选择区域 ===
        st.markdown("### 📂 档案选择")
        all_profiles = profile_manager.get_all()
        
        # 构建档案选项
        profile_options = {"new": "(新建档案)"}
        for p in all_profiles:
            pid = p.get('id', '')
            pname = p.get('name', 'Unknown')
            pgender = p.get('gender', '?')
            profile_options[pid] = f"{pname} ({pgender})"
        
        # 处理待选择的档案
        if '_pending_profile_select' in st.session_state:
            pending_id = st.session_state.pop('_pending_profile_select')
            if pending_id in profile_options:
                st.session_state['profile_select_id'] = pending_id
        
        # 获取当前选中的档案ID
        current_profile_id = st.session_state.get('profile_select_id', st.session_state.get('current_profile_id', 'new'))
        if current_profile_id not in profile_options:
            current_profile_id = 'new'
        
        # 档案选择下拉框
        option_list = list(profile_options.keys())
        try:
            current_idx = option_list.index(current_profile_id)
        except ValueError:
            current_idx = 0
        
        if 'profile_select_id' not in st.session_state:
            st.session_state['profile_select_id'] = current_profile_id
        
        selected_profile_id = st.selectbox(
            "选择档案",
            options=option_list,
            format_func=lambda x: profile_options.get(x, x),
            key="profile_select_id",
            index=current_idx
        )
        
        # 更新session state
        if selected_profile_id != current_profile_id:
            st.session_state['profile_select_id'] = selected_profile_id
            if selected_profile_id != 'new':
                st.session_state['current_profile_id'] = selected_profile_id
            st.rerun()
        
        st.markdown("---")
        
        # === 格局选择区域 ===
        st.markdown("### 🧬 格局选择")
        
        # 获取格局层级结构
        hierarchy = controller.get_pattern_hierarchy()
        
        if not hierarchy:
            st.info("📋 注册表为空，等待添加格局")
            st.markdown("---")
            st.markdown("### 📝 说明")
            st.markdown("""
            这是全新的**张量全息格局**系统。
            
            格局将通过FDS-V1.1规范注册：
            - Step 1: AI分析师定义物理意象和权重
            - Step 2-5: 完成拟合和注册流程
            
            当前注册表：`core/subjects/holographic_pattern/registry.json`
            """)
            return
        
        # 构建层级显示的格局选项
        pattern_options = {}
        for parent_id, hierarchy_data in sorted(hierarchy.items()):
            main_pattern = hierarchy_data['main']
            sub_patterns = hierarchy_data['subs']
            
            # 主格局
            main_display = f"{main_pattern['icon']} {main_pattern['name_cn'] or main_pattern['name']} ({parent_id})"
            pattern_options[main_display] = parent_id
            
            # 子格局（缩进显示）
            for sub_pattern in sub_patterns:
                sub_display = f"  └─ {sub_pattern['icon']} {sub_pattern['name_cn'] or sub_pattern['name']} ({sub_pattern['id']})"
                pattern_options[sub_display] = sub_pattern['id']
        
        # 格局选择器
        selected_pattern_name = st.selectbox(
            "选择格局",
            options=list(pattern_options.keys()),
            key="selected_pattern"
        )
        selected_pattern_id = pattern_options[selected_pattern_name]
        
        # 显示格局信息
        pattern_info = controller.get_pattern_by_id(selected_pattern_id)
        if pattern_info:
            st.markdown("---")
            st.markdown(f"**格局ID**: `{selected_pattern_id}`")
            st.markdown(f"**版本**: {pattern_info.get('version', 'N/A')}")
            st.markdown(f"**状态**: {'✅ 激活' if pattern_info.get('active', False) else '⏸️ 未激活'}")
            
            # 显示语义意象
            semantic_seed = pattern_info.get('semantic_seed', {})
            if semantic_seed:
                st.markdown("---")
                st.markdown("### 🌟 语义意象")
                st.markdown(semantic_seed.get('description', 'N/A'))
        
        # === 地理信息区域（仅显示，选择在主内容区）===
        st.markdown("---")
        st.markdown("### 🌍 地理信息")
        
        # 导入城市地图
        from ui.pages.quantum_lab import GEO_CITY_MAP
        
        # 获取当前选中的城市（从session_state）
        current_city = st.session_state.get('holographic_geo_city', 'None')
        
        # 显示当前城市信息
        if current_city != "None" and current_city in GEO_CITY_MAP:
            geo_factor, geo_element = GEO_CITY_MAP[current_city]
            st.markdown(f"**当前城市**: {current_city}")
            st.markdown(f"**地理修正系数**: {geo_factor:.2f}")
            st.markdown(f"**五行偏向**: {geo_element}")
            
        else:
            st.info("👈 请在主内容区选择城市")
    
    # --- 主内容区 ---
    st.markdown("## 📊 全息格局分析")
    
    # 获取当前档案ID
    current_profile_id = st.session_state.get('profile_select_id') or st.session_state.get('current_profile_id')
    
    if not current_profile_id or current_profile_id == 'new':
        st.info("👈 请在左侧边栏选择或创建档案")
        return
    
    # 从ProfileManager获取档案数据
    all_profiles = profile_manager.get_all()
    profile_data = next((p for p in all_profiles if p.get('id') == current_profile_id), None)
    
    if not profile_data:
        st.info("👈 档案不存在，请重新选择")
        return
    
    # 创建BaziProfile对象
    try:
        birth_date = datetime(
            profile_data['year'],
            profile_data['month'],
            profile_data['day'],
            profile_data.get('hour', 12),
            profile_data.get('minute', 0)
        )
        gender = 1 if profile_data.get('gender') == '男' else 0
        current_profile = BaziProfile(birth_date, gender)
        
        # 获取八字信息
        pillars = current_profile.pillars
        chart = [pillars['year'], pillars['month'], pillars['day'], pillars['hour']]
        day_master = current_profile.day_master
        
        # === 排盘信息显示 ===
        st.markdown("### 📋 八字排盘")
        
        # 档案基本信息
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.markdown(f"**姓名**: {profile_data.get('name', 'N/A')}")
        with col_info2:
            st.markdown(f"**性别**: {profile_data.get('gender', 'N/A')}")
        with col_info3:
            st.markdown(f"**出生**: {profile_data['year']}-{profile_data['month']}-{profile_data['day']} {profile_data.get('hour', 12)}:00")
        
        st.markdown("---")
        
        # === 流年选择与城市选择 ===
        col_year, col_city = st.columns([1, 1])
        
        with col_year:
            # 流年选择（用于六柱显示）
            current_year = datetime.now().year
            selected_year = st.number_input(
                "选择流年",
                min_value=1900,
                max_value=2100,
                value=current_year,
                key="selected_year_holographic"
            )
        
        with col_city:
            # 导入城市地图
            from ui.pages.quantum_lab import GEO_CITY_MAP
            
            # 获取档案中的城市信息
            profile_city = profile_data.get('city')
            city_options = ["None"] + list(GEO_CITY_MAP.keys())
            
            # 确定当前选中的城市
            if profile_city and profile_city != "None":
                # 尝试匹配城市名称
                current_city = None
                for city_name in city_options:
                    if profile_city in city_name or city_name in profile_city:
                        current_city = city_name
                        break
                if not current_city:
                    current_city = profile_city
            else:
                current_city = st.session_state.get('holographic_geo_city', 'None')
            
            # 城市选择器
            city_idx = city_options.index(current_city) if current_city in city_options else 0
            selected_city = st.selectbox(
                "选择城市",
                options=city_options,
                index=city_idx,
                key="holographic_geo_city"
            )
            
            # 显示地理修正信息（在城市选择器下方）
            if selected_city != "None" and selected_city in GEO_CITY_MAP:
                geo_factor, geo_element = GEO_CITY_MAP[selected_city]
                st.markdown(f"**地理修正系数**: `{geo_factor:.2f}`")
                st.markdown(f"**五行偏向**: `{geo_element}`")
                geo_factor = geo_factor
                geo_element = geo_element
            else:
                geo_factor = 1.0
                geo_element = "Neutral"
        
        # 获取大运和流年（用于六柱显示）
        luck_pillar = current_profile.get_luck_pillar_at(selected_year)
        year_pillar = current_profile.get_year_pillar(selected_year)
        
        st.markdown("---")
        
        # === 六柱横向排列显示（四柱+大运+流年）===
        st.markdown("#### 六柱排盘")
        
        # 导入十神和藏干计算模块
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        
        # 构建六柱数据
        six_pillars = [
            {'name': '年柱', 'stem': chart[0][0], 'branch': chart[0][1], 'type': '原局'},
            {'name': '月柱', 'stem': chart[1][0], 'branch': chart[1][1], 'type': '原局'},
            {'name': '日柱', 'stem': chart[2][0], 'branch': chart[2][1], 'type': '原局'},
            {'name': '时柱', 'stem': chart[3][0], 'branch': chart[3][1], 'type': '原局'},
            {'name': '大运', 'stem': luck_pillar[0], 'branch': luck_pillar[1], 'type': '大运'},
            {'name': '流年', 'stem': year_pillar[0], 'branch': year_pillar[1], 'type': '流年'},
        ]
        
        # 计算每个柱的详细信息
        pillar_details = []
        for pillar in six_pillars:
            stem = pillar['stem']
            branch = pillar['branch']
            
            # 天干十神
            stem_shi_shen = BaziParticleNexus.get_shi_shen(stem, day_master) if stem != day_master else '日主'
            
            # 地支藏干
            hidden_stems = BaziParticleNexus.get_branch_weights(branch)
            hidden_stems_info = []
            for h_stem, h_weight in hidden_stems:
                h_shi_shen = BaziParticleNexus.get_shi_shen(h_stem, day_master)
                hidden_stems_info.append({
                    'stem': h_stem,
                    'weight': h_weight,
                    'shi_shen': h_shi_shen
                })
            
            pillar_details.append({
                **pillar,
                'stem_shi_shen': stem_shi_shen,
                'hidden_stems': hidden_stems_info
            })
        
        # 导入主题颜色函数
        from ui.components.styles import get_theme
        
        # 辅助函数：将十六进制颜色转换为RGB
        def hex_to_rgb(hex_color):
            """将#RRGGBB转换为RGB元组"""
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return (226, 232, 240)  # 默认灰色
        
        # 创建六列布局
        cols = st.columns(6)
        
        for idx, detail in enumerate(pillar_details):
            with cols[idx]:
                # 获取天干和地支的主题颜色
                stem_theme = get_theme(detail['stem'])
                branch_theme = get_theme(detail['branch'])
                
                stem_color = stem_theme.get('color', '#e2e8f0')
                branch_color = branch_theme.get('color', '#e2e8f0')
                
                # 日主特殊处理（金色高亮）
                if detail['stem_shi_shen'] == '日主':
                    stem_color = "#ffd700"
                
                # 转换颜色为RGB用于背景
                stem_rgb = hex_to_rgb(stem_color)
                branch_rgb = hex_to_rgb(branch_color)
                
                # 柱名和类型（无边框，使用文字颜色）
                type_color = "#40e0d0" if detail['type'] == '原局' else "#ffd700" if detail['type'] == '大运' else "#ff6b6b"
                st.markdown(f"""
                <div style="text-align: center; padding: 8px; margin-bottom: 8px;">
                    <div style="color: {type_color}; font-size: 12px; margin-bottom: 3px; font-weight: bold;">{detail['name']}</div>
                    <div style="color: #888; font-size: 10px;">{detail['type']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 天干（无边框，使用五行颜色背景）
                st.markdown(f"""
                <div style="text-align: center; padding: 12px; margin: 5px 0; border-radius: 8px; background: rgba({stem_rgb[0]}, {stem_rgb[1]}, {stem_rgb[2]}, 0.2);">
                    <div style="color: {stem_color}; font-size: 36px; font-weight: bold; text-shadow: 0 0 15px {stem_color}60;">{detail['stem']}</div>
                    <div style="color: #a0a0a0; font-size: 11px; margin-top: 5px;">{detail['stem_shi_shen']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 地支（无边框，使用五行颜色背景）
                st.markdown(f"""
                <div style="text-align: center; padding: 12px; margin: 5px 0; border-radius: 8px; background: rgba({branch_rgb[0]}, {branch_rgb[1]}, {branch_rgb[2]}, 0.2);">
                    <div style="color: {branch_color}; font-size: 36px; font-weight: bold; text-shadow: 0 0 15px {branch_color}60;">{detail['branch']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 藏干（小字显示，使用藏干的五行颜色）
                if detail['hidden_stems']:
                    hidden_items = []
                    for h in detail['hidden_stems']:
                        h_theme = get_theme(h['stem'])
                        h_color = h_theme.get('color', '#888')
                        hidden_items.append(
                            f"<span style='color: {h_color}; font-size: 10px; font-weight: 500;'>{h['stem']}</span>"
                            f"<span style='color: #666; font-size: 9px;'>({h['shi_shen']})</span>"
                        )
                    hidden_text = " | ".join(hidden_items)
                    st.markdown(f"""
                    <div style="text-align: center; padding: 5px; margin-top: 5px; font-size: 10px; color: #a0a0a0; line-height: 1.4;">
                        {hidden_text}
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 计算五维张量投影
        with st.spinner("正在计算五维张量投影..."):
            result = controller.calculate_tensor_projection(
                pattern_id=selected_pattern_id,
                chart=chart,
                day_master=day_master
            )
        
        if 'error' in result:
            st.error(f"❌ {result['error']}")
            return
        
        # 显示结果
        st.markdown("---")
        st.markdown("### 🌟 五维张量投影结果")
        
        # SAI总模长
        col1, col2 = st.columns([1, 2])
        with col1:
            sai_value = result.get('sai', 0.0)
            sai_display = f"{sai_value:.4f}"
            
            # 根据SAI值显示不同的说明
            if sai_value == 0.0:
                st.metric("SAI (系统对齐指数)", sai_display, delta="⚠️ 计算异常", delta_color="off")
                
                # 显示警告信息（如果有）
                sai_warning = result.get('sai_warning')
                if sai_warning:
                    st.warning(f"⚠️ {sai_warning}")
                
                # 提供诊断信息
                with st.expander("🔍 诊断信息", expanded=False):
                    st.warning("**可能的原因：**")
                    st.markdown("""
                    1. **格局不匹配**：当前八字可能不符合该格局的特征
                    2. **计算框架未初始化**：物理引擎可能未正确加载
                    3. **数据异常**：八字数据可能存在问题
                    4. **版本兼容性**：该格局可能使用了新的V2.1矩阵系统，需要检查计算路径
                    
                    **建议：**
                    - 检查八字输入是否正确
                    - 尝试切换到其他格局进行分析
                    - 查看控制台日志获取详细错误信息
                    - 如果使用A-03格局，确保已正确配置transfer_matrix
                    """)
                    # 显示原始结果用于调试
                    if st.checkbox("显示调试信息"):
                        st.json(result)
            elif sai_value < 0.5:
                st.metric("SAI (系统对齐指数)", sai_display, delta="低应力", delta_color="normal")
            elif sai_value < 1.2:
                st.metric("SAI (系统对齐指数)", sai_display, delta="正常范围", delta_color="normal")
            elif sai_value < 2.0:
                st.metric("SAI (系统对齐指数)", sai_display, delta="高应力", delta_color="inverse")
            else:
                st.metric("SAI (系统对齐指数)", sai_display, delta="⚠️ 临界应力", delta_color="inverse")
                st.warning("⚠️ SAI超过2.0，系统处于高应力状态，可能存在结构风险")
        
        # 五维投影可视化
        projection = result['projection']
        weights = result['weights']
        
        # 创建雷达图
        fig = go.Figure()
        
        categories = ['能级轴 (E)', '秩序轴 (O)', '物质轴 (M)', '应力轴 (S)', '关联轴 (R)']
        values = [
            projection.get('E', 0),
            projection.get('O', 0),
            projection.get('M', 0),
            projection.get('S', 0),
            projection.get('R', 0)
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='五维投影',
            line_color='#40e0d0'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) * 1.2 if values else 1]
                )),
            showlegend=True,
            title="五维命运张量投影",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # === 全息投影可视化 (Holographic Visualization) ===
        st.markdown("---")
        st.markdown("### 🌌 全息投影可视化 (Holographic Visualization)")
        st.caption("基于FDS-V1.4：实时演算命运轨迹 | 命运风洞实验室")
        
        # 实时演算命运轨迹
        from core.fate_simulator import simulate_trajectory
        
        # 获取大运（如果有）
        luck_pillar = ""
        try:
            # 尝试从当前档案获取大运
            current_year = datetime.now().year
            luck_pillar = current_profile.get_luck_pillar_at(current_year) if hasattr(current_profile, 'get_luck_pillar_at') else ""
        except:
            pass
        
        # 实时演算（带进度显示）
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            import time
            start_time = time.time()
            
            # 显示初始状态
            status_text.text("正在演算量子命运轨迹... (0秒)")
            logger.info("=" * 70)
            logger.info("🚀 开始演算量子命运轨迹")
            logger.info(f"   格局: {selected_pattern_id}")
            logger.info(f"   起始年份: {selected_year}")
            logger.info(f"   八字: {chart}, 日主: {day_master}")
            logger.info("=" * 70)
            
            # 直接运行（不使用线程，避免Streamlit兼容性问题）
            timeline_results = simulate_trajectory(
                chart=chart,
                day_master=day_master,
                pattern_id=selected_pattern_id,
                start_year=selected_year,
                duration=12,
                luck_pillar=luck_pillar
            )
            
            # 完成
            total_elapsed = time.time() - start_time
            progress_bar.progress(1.0)
            status_text.text(f"✅ 演算完成！耗时 {total_elapsed:.2f}秒")
            
            if total_elapsed > 10.0:
                logger.warning(f"⚠️ 演算耗时较长: {total_elapsed:.2f}秒")
            else:
                logger.info(f"✅ 演算完成，耗时: {total_elapsed:.2f}秒")
            
            # 短暂显示完成状态后清除
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            # 检查结果
            if not timeline_results:
                st.error("❌ 演算失败：未返回任何结果")
                st.info("💡 提示：请检查控制台日志获取详细错误信息")
                return
            
            if timeline_results:
                # === 动态状态判定 (Dynamic Status Check) ===
                # 获取当前年份的状态（而不是静态的原局匹配）
                current_year_data = None
                for r in timeline_results:
                    if r.get('year') == selected_year:
                        current_year_data = r
                        break
                
                # 如果没有找到当前年份，使用第一年
                if not current_year_data:
                    current_year_data = timeline_results[0] if timeline_results else None
                
                # === 动态状态判定 (Dynamic Status Check with Injection Factors) ===
                # 获取当前年份的状态（注入因子后的混合状态）
                current_pattern_state = None
                current_alpha = None
                if current_year_data:
                    pattern_state_obj = current_year_data.get('pattern_state', {})
                    current_pattern_state = pattern_state_obj.get('state', 'STABLE')
                    current_alpha = current_year_data.get('alpha', 1.0)
                
                # 检查原局匹配（静态，出厂设置）
                recognition = result.get('recognition', {})
                is_pattern_matched = recognition.get('matched', False)
                
                # 动态判定：基于当前年份的状态显示提示（优先级逻辑）
                if selected_pattern_id == 'A-03':
                    # Case 1: 动态成功（注入因子生效！流年能量注入成功）
                    if current_pattern_state in ['CRYSTALLIZED', 'FORMED_A03']:
                        alpha_display = f"{current_alpha:.2f}" if current_alpha is not None else "N/A"
                        st.success(
                            f"✨ **运至成格 (Phase Crystallized)** | "
                            f"流年能量注入成功，已激活 A-03 专属高维矩阵 "
                            f"(Alpha: {alpha_display})"
                        )
                    
                    # Case 2: 静态成功（原局入格，天生就是A-03）
                    elif is_pattern_matched and current_pattern_state != 'COLLAPSED':
                        status_display = current_pattern_state if current_pattern_state else 'STABLE'
                        st.info(f"🛡️ **标准格局 (Standard A-03)** | 状态: {status_display}")
                    
                    # Case 3: 动态失败（格局崩塌）
                    elif current_pattern_state == 'COLLAPSED':
                        alpha_display = f"{current_alpha:.2f}" if current_alpha is not None else "N/A"
                        st.error(
                            f"⚡ **格局崩塌 (Phase Collapse)** | "
                            f"结构完整性受损 (Alpha: {alpha_display})，已降级为通用矩阵"
                        )
                    
                    # Case 4: 完全失败（既不是原局入格，也没有动态成格）
                    else:
                        st.warning(
                            "⚠️ **非标格局 (Standard Pattern)** | "
                            "当前八字未入 A-03 正格，且流年未达成格条件。以下为'强制拟合'视角的投影。"
                        )
                
                # === 五维超流形可视化 (5D Hyper-Manifold) ===
                st.markdown("#### 🪐 全息命运流形 (The Fate Manifold)")
                st.caption("3D+2D视觉模型：将五维张量映射为悬浮在宇宙中的'发光天体'")
                
                # 获取当前投影和标准质心
                current_projection = result.get('projection', {})
                pattern_info = controller.get_pattern_by_id(selected_pattern_id)
                reference_centroid = None
                if pattern_info:
                    feature_anchors = pattern_info.get('feature_anchors', {})
                    standard_centroid = feature_anchors.get('standard_centroid', {})
                    reference_centroid = standard_centroid.get('vector', {})
                
                # 获取格局状态
                pattern_state = result.get('pattern_state', {}).get('state', 'STABLE')
                if 'recognition' in result:
                    recognition = result['recognition']
                    if recognition.get('matched'):
                        pattern_state = recognition.get('pattern_type', 'STABLE')
                
                # 渲染3D超流形
                manifold_fig = render_5d_manifold(
                    current_tensor=current_projection,
                    reference_tensor=reference_centroid,
                    pattern_state=pattern_state,
                    pattern_name=result.get('pattern_name', selected_pattern_id)
                )
                st.plotly_chart(manifold_fig, use_container_width=True)
                
                # 显示流形描述
                description = get_manifold_description(current_projection, pattern_state)
                col_desc1, col_desc2, col_desc3, col_desc4 = st.columns(4)
                
                with col_desc1:
                    st.metric("能级质量 (Mass)", description['mass'], description['energy'])
                with col_desc2:
                    st.metric("社会高度 (Altitude)", description['altitude'], description['order'])
                with col_desc3:
                    st.metric("核心温度 (Temp)", description['temperature'], description['stress'])
                with col_desc4:
                    st.metric("形态特征 (Shape)", description['shape'], "")
                
                # === 动态时间轴 ===
                st.markdown("#### ⏱️ 动态时间轴 (2024-2035)")
                st.caption("秩序轴 (O) vs 应力轴 (S) 演化趋势 | 相变事件标记")
                
                # 渲染时间轴
                timeline_fig = render_phase_timeline(
                    timeline_data=timeline_results,
                    show_alpha=True,
                    show_projection=True
                )
                st.plotly_chart(timeline_fig, use_container_width=True)
                
                # 显示关键事件摘要
                with st.expander("📋 关键事件摘要", expanded=False):
                    critical_years = []
                    for r in timeline_results:
                        state = r.get('pattern_state', {}).get('state', 'STABLE')
                        if state in ['COLLAPSED', 'CRYSTALLIZED', 'MUTATED']:
                            critical_years.append({
                                'year': r['year'],
                                'year_pillar': r.get('year_pillar', ''),
                                'state': state,
                                'alpha': r.get('alpha', 0.0),
                                'trigger': r.get('pattern_state', {}).get('trigger', 'N/A')
                            })
                    
                    if critical_years:
                        for event in critical_years:
                            state_icons = {
                                'COLLAPSED': '⚡',
                                'CRYSTALLIZED': '💎',
                                'MUTATED': '🔮'
                            }
                            state_names = {
                                'COLLAPSED': '破格',
                                'CRYSTALLIZED': '成格',
                                'MUTATED': '变异'
                            }
                            icon = state_icons.get(event['state'], '⚪')
                            name = state_names.get(event['state'], event['state'])
                            
                            st.markdown(f"**{icon} {event['year']}年 ({event['year_pillar']})**: {name}")
                            st.markdown(f"  - Alpha: {event['alpha']:.4f}")
                            st.markdown(f"  - 触发: {event['trigger']}")
                            st.markdown("---")
                    else:
                        st.info("无关键事件")
                
                # === 命运叙事层 (Narrative Layer) ===
                st.markdown("---")
                st.markdown("#### 🔮 解码命运流形 (Decode Manifold)")
                st.caption("基于5维张量的物理解读 | AI叙事生成")
                
                # 获取当前年份的数据（用于生成报告）
                current_year_data_for_report = None
                for r in timeline_results:
                    if r.get('year') == selected_year:
                        current_year_data_for_report = r
                        break
                
                if not current_year_data_for_report:
                    # 如果没有找到当前年份，使用第一年
                    current_year_data_for_report = timeline_results[0] if timeline_results else None
                
                if current_year_data_for_report:
                    # 生成当前年份的报告
                    report_data = {
                        'projection': current_year_data_for_report.get('projection', {}),
                        'alpha': current_year_data_for_report.get('alpha', 1.0),
                        'pattern_state': current_year_data_for_report.get('pattern_state', {})
                    }
                    
                    narrative = generate_holographic_report(
                        tensor_data=report_data,
                        pattern_name=result.get('pattern_name', selected_pattern_id),
                        pattern_state=pattern_state
                    )
                    
                    # 使用st.markdown显示，确保Markdown格式（包括换行）被正确渲染
                    # 使用unsafe_allow_html=False确保安全，但允许Markdown格式
                    st.markdown(narrative, unsafe_allow_html=False)
                    
                    # 生成时间轴洞察
                    timeline_insight = generate_timeline_insight(
                        timeline_data=timeline_results,
                        pattern_name=result.get('pattern_name', selected_pattern_id)
                    )
                    
                    with st.expander("📊 12年轨迹洞察", expanded=False):
                        st.markdown(timeline_insight)
            else:
                st.warning("⚠️ 演算结果为空")
        except Exception as e:
            logging.error(f"实时演算失败: {e}", exc_info=True)
            st.error(f"❌ 演算失败: {e}")
            import traceback
            st.code(traceback.format_exc(), language='python')
        
        # 显示详细数据
        with st.expander("📋 详细数据", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 投影值")
                df_projection = pd.DataFrame([
                    {'维度': '能级轴 (E)', '投影值': f"{projection.get('E', 0):.4f}", '权重': f"{weights.get('E', 0):.4f}"},
                    {'维度': '秩序轴 (O)', '投影值': f"{projection.get('O', 0):.4f}", '权重': f"{weights.get('O', 0):.4f}"},
                    {'维度': '物质轴 (M)', '投影值': f"{projection.get('M', 0):.4f}", '权重': f"{weights.get('M', 0):.4f}"},
                    {'维度': '应力轴 (S)', '投影值': f"{projection.get('S', 0):.4f}", '权重': f"{weights.get('S', 0):.4f}"},
                    {'维度': '关联轴 (R)', '投影值': f"{projection.get('R', 0):.4f}", '权重': f"{weights.get('R', 0):.4f}"},
                ])
                st.dataframe(df_projection, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("#### 格局信息")
                st.json({
                    'pattern_id': result['pattern_id'],
                    'pattern_name': result['pattern_name'],
                    'sai': result['sai']
                })
        
        # === 动态演化视窗 (Dynamic Evolution View) ===
        st.markdown("---")
        st.markdown("### 🌌 动态演化视窗 (Dynamic Evolution View)")
        st.caption("基于FDS-V1.1 Step 6：从静态全息到动态流形 | 命运风洞实验室")
        
        # 演化控制面板
        col_control1, col_control2, col_control3 = st.columns(3)
        
        with col_control1:
            st.markdown("#### 🎛️ 时间轴控制")
            # 时间轴滑块（用于动态演化）
            evolution_year = st.slider(
                "选择演化年份",
                min_value=1900,
                max_value=2100,
                value=selected_year,
                key="evolution_year",
                help="拖动滑块查看不同年份的演化状态"
            )
        
        with col_control2:
            st.markdown("#### 🌍 地理环境")
            # 地理环境已在上方选择，这里显示当前状态
            if selected_city != "None" and selected_city in GEO_CITY_MAP:
                geo_factor, geo_element = GEO_CITY_MAP[selected_city]
                st.info(f"**当前环境**: {selected_city}\n**修正系数**: {geo_factor:.2f}\n**五行偏向**: {geo_element}")
            else:
                st.warning("⚠️ 未选择地理环境")
        
        # 计算演化结果（在所有地方都能访问）
        evolution_result = None
        try:
            evolution_result = controller.calculate_evolution(
                pattern_id=selected_pattern_id,
                chart=chart,
                day_master=day_master,
                year=evolution_year,
                geo_city=selected_city if selected_city != "None" else None
            )
        except Exception as e:
            logging.error(f"计算动态演化失败: {e}", exc_info=True)
            evolution_result = {'error': str(e)}
        
        with col_control3:
            st.markdown("#### 📊 演化状态")
            # 显示演化状态
            if evolution_result and 'error' in evolution_result:
                st.warning(f"⚠️ 演化计算错误: {evolution_result['error']}")
            elif evolution_result and 'status' in evolution_result:
                status = evolution_result['status']
                status_colors = {
                    'STABLE': '🟢',
                    'CRITICAL': '🟡',
                    'FRACTURED': '🔴',
                    'MUTATED': '🟣'
                }
                status_names = {
                    'STABLE': '稳定态',
                    'CRITICAL': '临界态',
                    'FRACTURED': '断裂态',
                    'MUTATED': '变异态'
                }
                status_icon = status_colors.get(status, '⚪')
                status_name = status_names.get(status, status)
                
                st.markdown(f"**当前状态**: {status_icon} {status_name}")
                
                if status == 'CRITICAL':
                    st.warning("⚠️ 系统接近临界点，建议谨慎决策")
                elif status == 'FRACTURED':
                    st.error("❌ 系统结构崩解，高风险状态")
                elif status == 'MUTATED':
                    st.info("ℹ️ 系统发生相变，格局变异")
            else:
                st.info("👈 选择年份查看演化状态")
        
        # 三态演化可视化
        st.markdown("---")
        st.markdown("#### 🔬 三态演化模型")
        
        col_state1, col_state2, col_state3 = st.columns(3)
        
        with col_state1:
            st.markdown("##### 第一态：原局基态")
            st.caption("命主的'出厂设置'，真空环境下的潜力")
            # 显示原局张量
            base_tensor = result.get('projection', {})
            st.json({
                'E': f"{base_tensor.get('E', 0):.4f}",
                'O': f"{base_tensor.get('O', 0):.4f}",
                'M': f"{base_tensor.get('M', 0):.4f}",
                'S': f"{base_tensor.get('S', 0):.4f}",
                'R': f"{base_tensor.get('R', 0):.4f}"
            })
        
        with col_state2:
            st.markdown("##### 第二态：环境场加载")
            st.caption("注入大运、流年、地理后的状态")
            # 显示演化后的张量（如果有）
            try:
                if evolution_result and 'final_tensor' in evolution_result:
                    final_tensor = evolution_result['final_tensor']
                    st.json({
                        'E': f"{final_tensor.get('E', 0):.4f}",
                        'O': f"{final_tensor.get('O', 0):.4f}",
                        'M': f"{final_tensor.get('M', 0):.4f}",
                        'S': f"{final_tensor.get('S', 0):.4f}",
                        'R': f"{final_tensor.get('R', 0):.4f}"
                    })
                    
                    # 显示变化量
                    delta_s = final_tensor.get('S', 0) - base_tensor.get('S', 0)
                    if delta_s > 0:
                        st.metric("应力变化", f"+{delta_s:.4f}", delta="增加", delta_color="inverse")
                    elif delta_s < 0:
                        st.metric("应力变化", f"{delta_s:.4f}", delta="减少", delta_color="normal")
                    else:
                        st.metric("应力变化", "0.0000", delta="无变化")
                else:
                    st.info("👈 选择年份查看演化状态")
            except Exception as e:
                st.warning(f"演化数据暂不可用")
        
        with col_state3:
            st.markdown("##### 第三态：演化结果")
            st.caption("形变类型：弹性/塑性/断裂")
            # 显示演化结果类型
            try:
                if evolution_result and not evolution_result.get('error'):
                    deformation_type = evolution_result.get('deformation_type', 'UNKNOWN')
                    deformation_names = {
                        'ELASTIC': '弹性形变（可恢复）',
                        'PLASTIC': '塑性形变（永久改变）',
                        'FRACTURE': '结构断裂（崩解）'
                    }
                    deformation_desc = deformation_names.get(deformation_type, f'未知类型 ({deformation_type})')
                    st.info(f"**形变类型**: {deformation_desc}")
                    
                    # 显示演化说明
                    if evolution_result.get('description'):
                        st.caption(evolution_result['description'])
                elif evolution_result and evolution_result.get('error'):
                    st.warning(f"⚠️ {evolution_result['error']}")
                else:
                    st.info("👈 选择年份查看演化结果")
            except Exception as e:
                st.warning(f"演化结果暂不可用: {e}")
        
        # 动态演化对比图
        st.markdown("---")
        st.markdown("#### 📈 动态演化对比（五维张量雷达图）")
        
        try:
            if evolution_result and 'final_tensor' in evolution_result and not evolution_result.get('error'):
                # 创建对比雷达图
                fig_evolution = go.Figure()
                
                categories = ['能级轴 (E)', '秩序轴 (O)', '物质轴 (M)', '应力轴 (S)', '关联轴 (R)']
                
                # 原局基态
                base_values = [
                    base_tensor.get('E', 0),
                    base_tensor.get('O', 0),
                    base_tensor.get('M', 0),
                    base_tensor.get('S', 0),
                    base_tensor.get('R', 0)
                ]
                
                # 演化后状态
                final_tensor = evolution_result['final_tensor']
                final_values = [
                    final_tensor.get('E', 0),
                    final_tensor.get('O', 0),
                    final_tensor.get('M', 0),
                    final_tensor.get('S', 0),
                    final_tensor.get('R', 0)
                ]
                
                fig_evolution.add_trace(go.Scatterpolar(
                    r=base_values,
                    theta=categories,
                    fill='toself',
                    name='原局基态',
                    line_color='#40e0d0'
                ))
                
                fig_evolution.add_trace(go.Scatterpolar(
                    r=final_values,
                    theta=categories,
                    fill='toself',
                    name=f'演化后 ({evolution_year}年)',
                    line_color='#ff6b6b'
                ))
                
                fig_evolution.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, max(max(base_values), max(final_values)) * 1.2 if base_values or final_values else 1]
                        )),
                    showlegend=True,
                    title=f"动态演化对比 ({evolution_year}年)",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#e2e8f0')
                )
                
                st.plotly_chart(fig_evolution, use_container_width=True)
            else:
                # 提供更详细的提示信息
                if not evolution_result:
                    st.info("👈 请先选择格局和档案，然后拖动时间轴滑块查看演化状态")
                elif evolution_result.get('error'):
                    st.warning(f"⚠️ 演化计算失败: {evolution_result['error']}")
                elif 'final_tensor' not in evolution_result:
                    st.warning("⚠️ 演化结果缺少final_tensor数据")
                else:
                    st.info("👈 选择年份并确保已选择地理环境，查看动态演化对比")
        except Exception as e:
            st.warning(f"演化对比图暂不可用: {e}")
            import traceback
            st.code(traceback.format_exc(), language='python')
        
    except Exception as e:
        st.error(f"❌ 计算失败: {e}")
        # 使用模块级logger，避免作用域冲突
        logging.error(f"全息格局计算失败: {e}", exc_info=True)

