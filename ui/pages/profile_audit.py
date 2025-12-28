#!/usr/bin/env python3
"""
八字档案审计页面 (Profile Audit Page)
MVC View Layer - 只负责UI展示，所有业务逻辑通过Controller处理
基于QGA V23.0 "Causal Weaver" 逻辑
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# MVC: 只导入Controller，不直接操作Model或Engine
from controllers.profile_audit_controller import ProfileAuditController
from ui.components.theme import COLORS, GLASS_STYLE, apply_custom_header


def render():
    """渲染八字档案审计页面 (View Layer)"""
    st.set_page_config(
        page_title="八字档案审计", 
        page_icon="📋", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # --- 样式注入 ---
    st.markdown(f"""
    <style>
    .stApp {{
        background: radial-gradient(circle at 50% 50%, #0d0015 0%, #000000 100%);
        color: #e2e8f0;
    }}
    .audit-report-card {{
        background: rgba(45, 27, 78, 0.4);
        border: 1px solid rgba(255, 215, 0, 0.3);
        border-radius: 8px;
        padding: 12px;
        margin: 5px 0;
    }}
    .section-title {{
        color: {COLORS['mystic_gold']};
        font-size: 16px;
        font-weight: bold;
        margin-top: 8px;
        margin-bottom: 6px;
        border-bottom: 1px solid rgba(255, 215, 0, 0.3);
        padding-bottom: 3px;
    }}
    .compact-section {{
        margin: 3px 0;
        padding: 5px 0;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # --- 标题 ---
    apply_custom_header("📋 八字档案审计中心", "Profile Audit Center | 基于物理受力的深度命运分析")
    
    # MVC: 初始化Controller
    if 'audit_controller' not in st.session_state:
        st.session_state.audit_controller = ProfileAuditController()
    
    controller = st.session_state.audit_controller
    
    # --- 获取所有档案 ---
    all_profiles = controller.get_all_profiles()
    
    if not all_profiles:
        st.warning("📭 暂无档案数据，请先在智能排盘页面创建档案")
        return
    
    # --- 三栏布局：左侧档案选择、中间矢量图、右侧报告（紧凑版） ---
    col_left, col_mid, col_right = st.columns([1.0, 1.2, 1.5], gap="small")
    
    with col_left:
        render_profile_selector(controller, all_profiles)
    
    with col_mid:
        render_force_vector_diagram(controller)
    
    with col_right:
        render_audit_report(controller)


def render_profile_selector(controller: ProfileAuditController, all_profiles: list):
    """渲染左侧：档案与环境注入（紧凑版）"""
    st.markdown(f"""
    <div class="audit-report-card" style="padding: 10px;">
        <h3 style="color: {COLORS['mystic_gold']}; font-size: 16px; margin: 0 0 8px 0;">📂 档案与环境注入</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # [QGA V24.3] LLM合成开关
    # 注意：st.checkbox会自动管理session_state，不需要手动设置
    use_llm = st.checkbox(
        "🤖 启用LLM语义合成",
        value=st.session_state.get('use_llm_synthesis', False),
        key="use_llm_synthesis",
        help="使用LLM生成全息命运画像（需要安装ollama）"
    )
    
    # [QGA V24.3] 显示LLM配置信息和连接状态（始终显示，不管是否启用）
    from core.config_manager import ConfigManager
    from core.models.llm_semantic_synthesizer import LLMSemanticSynthesizer
    
    config_manager = ConfigManager()
    model_name = config_manager.get("selected_model_name", "未配置")
    ollama_host = config_manager.get("ollama_host", "http://localhost:11434")
    
    # 测试连接（只在需要时测试，避免每次都测试）
    if 'llm_connection_info' not in st.session_state or st.button("🔄 刷新LLM连接状态", key="refresh_llm_status"):
        with st.spinner("正在测试LLM连接..."):
            try:
                synthesizer = LLMSemanticSynthesizer(use_llm=True)
                connection_info = synthesizer.get_connection_info()
                st.session_state['llm_connection_info'] = connection_info
            except Exception as e:
                st.session_state['llm_connection_info'] = {
                    'model_name': model_name,
                    'ollama_host': ollama_host,
                    'connection_status': f"测试失败: {str(e)}",
                    'connection_error': str(e),
                    'use_llm': False
                }
    
    connection_info = st.session_state.get('llm_connection_info', {})
    
    # 显示LLM信息（始终显示）
    status_color = {
        "连接正常": "🟢",
        "连接失败": "🔴",
        "未安装ollama": "🟡",
        "未初始化": "⚪"
    }.get(connection_info.get('connection_status', ''), "⚪")
    
    # 如果还没有测试过，显示配置信息但不显示状态
    if not connection_info:
        st.markdown(f"""
        <div style="background: rgba(45, 27, 78, 0.3); padding: 8px; border-radius: 6px; margin: 5px 0; font-size: 12px;">
            <strong>🤖 LLM配置:</strong><br>
            • 模型: <code>{model_name}</code><br>
            • 服务器: <code>{ollama_host}</code><br>
            • 状态: 点击"刷新LLM连接状态"按钮测试连接
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: rgba(45, 27, 78, 0.3); padding: 8px; border-radius: 6px; margin: 5px 0; font-size: 12px;">
            <strong>🤖 LLM配置:</strong><br>
            • 模型: <code>{connection_info.get('model_name', model_name)}</code><br>
            • 服务器: <code>{connection_info.get('ollama_host', ollama_host)}</code><br>
            • 状态: {status_color} {connection_info.get('connection_status', '未知')}
            {f"<br>• 错误: <span style='color: {COLORS['rose_magenta']};'>{connection_info.get('connection_error', '')}</span>" if connection_info.get('connection_error') else ''}
        </div>
        """, unsafe_allow_html=True)
    
    # 如果连接失败，给出提示
    if connection_info.get('connection_status') and connection_info.get('connection_status') != "连接正常":
        st.warning("⚠️ LLM连接异常，将使用规则生成画像。请检查ollama服务是否运行，或前往系统配置页面检查LLM设置。")
    
    # 原来的if use_llm代码块已移除，因为现在始终显示
    if False:  # 保留原代码结构，但不再使用
        from core.config_manager import ConfigManager
        from core.models.llm_semantic_synthesizer import LLMSemanticSynthesizer
        
        config_manager = ConfigManager()
        model_name = config_manager.get("selected_model_name", "未配置")
        ollama_host = config_manager.get("ollama_host", "http://localhost:11434")
        
        # 测试连接（只在需要时测试，避免每次都测试）
        if 'llm_connection_info' not in st.session_state or st.button("🔄 刷新LLM连接状态", key="refresh_llm_status"):
            with st.spinner("正在测试LLM连接..."):
                try:
                    synthesizer = LLMSemanticSynthesizer(use_llm=True)
                    connection_info = synthesizer.get_connection_info()
                    st.session_state['llm_connection_info'] = connection_info
                except Exception as e:
                    st.session_state['llm_connection_info'] = {
                        'model_name': model_name,
                        'ollama_host': ollama_host,
                        'connection_status': f"测试失败: {str(e)}",
                        'connection_error': str(e),
                        'use_llm': False
                    }
        
        connection_info = st.session_state.get('llm_connection_info', {})
        
        # 显示LLM信息
        status_color = {
            "连接正常": "🟢",
            "连接失败": "🔴",
            "未安装ollama": "🟡",
            "未初始化": "⚪"
        }.get(connection_info.get('connection_status', ''), "⚪")
        
        st.markdown(f"""
        <div style="background: rgba(45, 27, 78, 0.3); padding: 8px; border-radius: 6px; margin: 5px 0; font-size: 12px;">
            <strong>🤖 LLM配置:</strong><br>
            • 模型: <code>{connection_info.get('model_name', model_name)}</code><br>
            • 服务器: <code>{connection_info.get('ollama_host', ollama_host)}</code><br>
            • 状态: {status_color} {connection_info.get('connection_status', '未知')}
            {f"<br>• 错误: <span style='color: {COLORS['rose_magenta']};'>{connection_info.get('connection_error', '')}</span>" if connection_info.get('connection_error') else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # 如果连接失败，给出提示
        if connection_info.get('connection_status') != "连接正常":
            st.warning("⚠️ LLM连接异常，将使用规则生成画像。请检查ollama服务是否运行，或前往系统配置页面检查LLM设置。")
    
    # 1. 档案选择
    st.markdown("#### 👤 档案", help="选择要审计的档案")
    profile_options = {p.get('id'): f"{p.get('name', '未知')} ({p.get('gender', '?')})" 
                      for p in all_profiles}
    
    selected_profile_id = st.selectbox(
        "档案列表",
        options=list(profile_options.keys()),
        format_func=lambda x: profile_options[x],
        key="audit_profile_select",
        label_visibility="collapsed"
    )
    
    if selected_profile_id:
        profile = controller.get_profile_by_id(selected_profile_id)
        if profile:
            st.caption(f"**{profile.get('name', '未知')}** ({profile.get('gender', '未知')}) | {profile.get('year', '?')}-{profile.get('month', '?')}-{profile.get('day', '?')} {profile.get('hour', '?')}时")
    
    # 2. 流年选择（显示对应大运）
    st.markdown("#### 📅 流年", help="选择要分析的流年")
    current_year = datetime.now().year
    selected_year = st.number_input(
        "选择流年",
        min_value=1900,
        max_value=2100,
        value=current_year,
        key="audit_year_select"
    )
    
    # 显示当前流年对应的大运
    if selected_profile_id:
        try:
            profile = controller.get_profile_by_id(selected_profile_id)
            if profile:
                from core.bazi_profile import BaziProfile
                from datetime import datetime as dt
                birth_date = dt(
                    profile['year'],
                    profile['month'],
                    profile['day'],
                    profile.get('hour', 12),
                    profile.get('minute', 0)
                )
                gender = 1 if profile.get('gender') == '男' else 0
                bazi_profile = BaziProfile(birth_date, gender)
                
                luck_pillar = bazi_profile.get_luck_pillar_at(selected_year)
                year_pillar = bazi_profile.get_year_pillar(selected_year)
                
                st.markdown(f"**流年**: {selected_year}年 {year_pillar}")
                st.markdown(f"**大运**: {luck_pillar}")
                
                # 显示大运周期信息
                luck_cycles = bazi_profile.get_luck_cycles()
                for cycle in luck_cycles:
                    if cycle['start_year'] <= selected_year <= cycle['end_year']:
                        st.caption(f"大运周期: {cycle['start_year']}-{cycle['end_year']}年 ({cycle['gan_zhi']})")
                        break
        except Exception as e:
            st.caption(f"无法计算大运: {str(e)}")
    
    st.divider()
    
    # 3. 地理环境
    st.markdown("#### 🌍 地理", help="选择城市和微环境")
    
    # 使用量子真言页面的城市列表
    GEO_CITY_MAP = {
        # === 中国直辖市/一线城市 (Tier-1 Cities) ===
        "北京 (Beijing)": (1.15, "Fire/Earth"),
        "上海 (Shanghai)": (1.08, "Water/Metal"),
        "深圳 (Shenzhen)": (1.12, "Fire/Water"),
        "广州 (Guangzhou)": (1.10, "Fire"),
        "天津 (Tianjin)": (1.05, "Water/Earth"),
        "重庆 (Chongqing)": (0.95, "Water/Fire"),
        
        # === 省会城市 (Provincial Capitals) ===
        "石家庄 (Shijiazhuang)": (1.02, "Earth"),
        "太原 (Taiyuan)": (0.98, "Metal/Earth"),
        "呼和浩特 (Hohhot)": (0.88, "Metal/Water"),
        "沈阳 (Shenyang)": (1.05, "Water/Metal"),
        "长春 (Changchun)": (1.00, "Water/Wood"),
        "哈尔滨 (Harbin)": (0.95, "Water"),
        "南京 (Nanjing)": (1.08, "Fire/Water"),
        "杭州 (Hangzhou)": (1.10, "Water/Wood"),
        "合肥 (Hefei)": (1.02, "Earth/Water"),
        "福州 (Fuzhou)": (1.05, "Water/Wood"),
        "南昌 (Nanchang)": (1.00, "Fire/Water"),
        "济南 (Jinan)": (1.03, "Water/Earth"),
        "郑州 (Zhengzhou)": (1.05, "Earth/Fire"),
        "武汉 (Wuhan)": (1.08, "Water/Fire"),
        "长沙 (Changsha)": (1.06, "Fire/Water"),
        "南宁 (Nanning)": (1.00, "Wood/Water"),
        "海口 (Haikou)": (0.92, "Water/Fire"),
        "成都 (Chengdu)": (0.95, "Earth/Wood"),
        "贵阳 (Guiyang)": (0.90, "Wood/Water"),
        "昆明 (Kunming)": (0.88, "Wood/Fire"),
        "拉萨 (Lhasa)": (0.75, "Metal/Earth"),
        "西安 (Xi'an)": (1.05, "Metal/Earth"),
        "兰州 (Lanzhou)": (0.92, "Metal/Water"),
        "西宁 (Xining)": (0.85, "Water/Metal"),
        "银川 (Yinchuan)": (0.88, "Metal/Earth"),
        "乌鲁木齐 (Urumqi)": (0.80, "Metal/Fire"),
        
        # === 其他重要城市 (Other Major Cities) ===
        "苏州 (Suzhou)": (1.10, "Water/Wood"),
        "无锡 (Wuxi)": (1.08, "Water/Metal"),
        "宁波 (Ningbo)": (1.06, "Water"),
        "青岛 (Qingdao)": (1.08, "Water/Wood"),
        "大连 (Dalian)": (1.05, "Water/Metal"),
        "厦门 (Xiamen)": (1.08, "Water/Fire"),
        "珠海 (Zhuhai)": (1.05, "Water/Fire"),
        "东莞 (Dongguan)": (1.08, "Fire/Metal"),
        "佛山 (Foshan)": (1.05, "Fire/Metal"),
        
        # === 港澳台 (HK/Macau/Taiwan) ===
        "香港 (Hong Kong)": (1.20, "Water/Metal"),
        "澳门 (Macau)": (1.10, "Water/Fire"),
        "台北 (Taipei)": (1.15, "Water/Wood"),
        "高雄 (Kaohsiung)": (1.08, "Fire/Water"),
        
        # === 亚洲城市 (Asian Cities) ===
        "东京 (Tokyo)": (1.20, "Water/Metal"),
        "大阪 (Osaka)": (1.12, "Water/Fire"),
        "首尔 (Seoul)": (1.15, "Metal/Water"),
        "新加坡 (Singapore)": (0.85, "Fire/Water"),
        "吉隆坡 (Kuala Lumpur)": (0.90, "Fire/Wood"),
        "曼谷 (Bangkok)": (0.88, "Fire/Water"),
        "马尼拉 (Manila)": (0.92, "Fire/Water"),
        "雅加达 (Jakarta)": (0.85, "Fire/Wood"),
        "河内 (Hanoi)": (0.95, "Water/Wood"),
        "胡志明市 (Ho Chi Minh)": (0.92, "Fire/Water"),
        "孟买 (Mumbai)": (0.95, "Fire/Water"),
        "新德里 (New Delhi)": (1.00, "Fire/Earth"),
        "迪拜 (Dubai)": (0.80, "Fire/Metal"),
        
        # === 欧洲城市 (European Cities) ===
        "伦敦 (London)": (1.15, "Water/Metal"),
        "巴黎 (Paris)": (1.12, "Metal/Water"),
        "柏林 (Berlin)": (1.08, "Metal/Earth"),
        "法兰克福 (Frankfurt)": (1.10, "Metal/Earth"),
        "阿姆斯特丹 (Amsterdam)": (1.05, "Water"),
        "苏黎世 (Zurich)": (1.08, "Metal/Water"),
        "米兰 (Milan)": (1.05, "Fire/Metal"),
        "莫斯科 (Moscow)": (1.00, "Water/Metal"),
        
        # === 北美城市 (North American Cities) ===
        "纽约 (New York)": (1.25, "Metal/Water"),
        "洛杉矶 (Los Angeles)": (1.15, "Fire/Metal"),
        "旧金山 (San Francisco)": (1.18, "Water/Metal"),
        "西雅图 (Seattle)": (1.12, "Water/Wood"),
        "芝加哥 (Chicago)": (1.10, "Metal/Water"),
        "多伦多 (Toronto)": (1.12, "Water/Metal"),
        "温哥华 (Vancouver)": (1.18, "Water/Wood"),
        
        # === 大洋洲城市 (Oceanian Cities) ===
        "悉尼 (Sydney)": (0.90, "Fire/Earth"),
        "墨尔本 (Melbourne)": (0.92, "Water/Earth"),
        "奥克兰 (Auckland)": (0.88, "Water/Wood"),
    }
    
    city_options = list(GEO_CITY_MAP.keys())
    selected_city = st.selectbox(
        "选择城市",
        options=city_options,
        key="audit_city_select"
    )
    
    # 显示城市的地理因子和五行属性
    if selected_city in GEO_CITY_MAP:
        geo_factor, geo_element = GEO_CITY_MAP[selected_city]
        st.caption(f"🌐 地理因子: **{geo_factor}** | 五行属性: **{geo_element}**")
    
    st.divider()
    
    # 4. 微环境
    st.markdown("#### 🏠 微环境")
    micro_env_options = ['近水', '近山', '高层', '低层']
    selected_micro_env = st.multiselect(
        "选择微环境（可多选）",
        options=micro_env_options,
        key="audit_micro_env_select"
    )
    
    st.divider()
    
    # 5. 执行审计按钮
    if st.button("🔍 执行深度审计", type="primary", use_container_width=True):
        with st.spinner("正在执行深度审计分析..."):
            try:
                # 提取城市名称（去掉英文部分）
                city_name = selected_city.split(' (')[0] if ' (' in selected_city else selected_city
                
                # [QGA V24.3] 传递LLM开关
                use_llm = st.session_state.get('use_llm_synthesis', False)
                audit_result = controller.perform_deep_audit(
                    selected_profile_id,
                    year=selected_year,
                    city=city_name,
                    micro_env=selected_micro_env if selected_micro_env else None,
                    use_llm=use_llm
                )
                st.session_state['current_audit_result'] = audit_result
                st.success("✅ 审计完成！")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 审计失败: {str(e)}")


def render_force_vector_diagram(controller: ProfileAuditController):
    """渲染中间：动态受力矢量图"""
    st.markdown(f"""
    <div class="audit-report-card">
        <h3 style="color: {COLORS['mystic_gold']};">⚡ 动态受力矢量图</h3>
    </div>
    """, unsafe_allow_html=True)
    
    audit_result = st.session_state.get('current_audit_result')
    
    if not audit_result or 'force_vectors' not in audit_result:
        st.info("👈 请先在左侧选择档案并执行审计")
        return
    
    force_vectors = audit_result['force_vectors'].copy()  # 复制，避免修改原数据
    pfa_data = audit_result.get('pfa', {})
    friction_index = pfa_data.get('friction_index', 0.0)
    
    # [QGA V24.3] 如果LLM推导出五行偏移，应用到矢量图
    # 注意：LLM校准信息存储在controller中，需要从审计结果获取
    if 'llm_calibration' in audit_result:
        llm_calibration = audit_result['llm_calibration']
        element_keys = ['metal', 'wood', 'water', 'fire', 'earth']
        for key in element_keys:
            if key in llm_calibration:
                offset = llm_calibration[key]
                force_vectors[key] = max(0.0, min(100.0, force_vectors.get(key, 20.0) + offset))
        
        # 重新归一化
        total = sum(force_vectors.values())
        if total > 0:
            for key in element_keys:
                force_vectors[key] = force_vectors[key] / total * 100.0
        
        st.caption("🤖 LLM已校准五行矢量")
    
    # 创建极坐标图显示五行受力
    elements = ['金', '木', '水', '火', '土']
    element_keys = ['metal', 'wood', 'water', 'fire', 'earth']
    values = [force_vectors.get(key, 20.0) for key in element_keys]
    
    # [优化1] 检测冲突维度（格局冲突>0.6时显示震荡）
    conflicting_axes = []
    if friction_index > 60 and pfa_data.get('conflicting_patterns'):
        # 检测对冲的五行（简化版：检测值差异大的相邻元素）
        for i in range(len(elements)):
            next_i = (i + 1) % len(elements)
            # 如果两个相邻元素值差异大，可能是冲突
            if abs(values[i] - values[next_i]) > 30:
                conflicting_axes.extend([i, next_i])
        conflicting_axes = list(set(conflicting_axes))
    
    # 创建雷达图
    fig = go.Figure()
    
    # 基础矢量
    base_trace = go.Scatterpolar(
        r=values,
        theta=elements,
        fill='toself',
        name='五行能量',
        line_color=COLORS['teal_mist'],
        fillcolor=f"rgba(64, 224, 208, 0.3)"
    )
    fig.add_trace(base_trace)
    
    # [优化1] 如果检测到冲突，添加震荡效果
    if conflicting_axes and friction_index > 60:
        # 创建震荡数据（高频波动）
        import numpy as np
        vibration_values = values.copy()
        for axis_idx in conflicting_axes:
            # 添加±5%的震荡
            vibration_values[axis_idx] = values[axis_idx] * (1.0 + 0.05 * np.sin(np.linspace(0, 4*np.pi, len(elements))))
        
        # 添加震荡轨迹（虚线）
        fig.add_trace(go.Scatterpolar(
            r=vibration_values,
            theta=elements,
            fill='none',
            name='系统震荡',
            line=dict(
                color=COLORS['rose_magenta'],
                width=2,
                dash='dash',
                shape='spline'
            ),
            mode='lines'
        ))
        
        # 显示警告
        st.warning(f"⚠️ 检测到系统不稳定（冲突指数{friction_index:.1f}），矢量场出现高频震荡")
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color='#e2e8f0', size=10),
                gridcolor='rgba(255, 255, 255, 0.2)'
            ),
            angularaxis=dict(
                tickfont=dict(color='#e2e8f0', size=11),
                linecolor='rgba(255, 255, 255, 0.3)'
            ),
            bgcolor='rgba(0, 0, 0, 0)'
        ),
        showlegend=False,
        height=320,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        font_color='#e2e8f0'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 显示数值（紧凑版）
    cols = st.columns(5)
    element_colors = {
        '金': '#FFD700', '木': '#10B981', '水': '#3B82F6',
        '火': '#EF4444', '土': '#F59E0B'
    }
    for i, (elem, val, key) in enumerate(zip(elements, values, element_keys)):
        with cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 6px; background: rgba(45, 27, 78, 0.3); border-radius: 6px; border: 1px solid {element_colors[elem]};">
                <div style="color: {element_colors[elem]}; font-size: 12px; font-weight: bold;">{elem}</div>
                <div style="color: {COLORS['teal_mist']}; font-size: 16px; font-weight: bold;">{val:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)


def render_audit_report(controller: ProfileAuditController):
    """渲染右侧：审计报告书（人话翻译，紧凑版）"""
    st.markdown(f"""
    <div class="audit-report-card" style="padding: 10px;">
        <h3 style="color: {COLORS['mystic_gold']}; font-size: 16px; margin: 0 0 8px 0;">📋 审计报告书</h3>
    </div>
    """, unsafe_allow_html=True)
    
    audit_result = st.session_state.get('current_audit_result')
    
    if not audit_result or 'semantic_report' not in audit_result:
        st.info("👈 请先在左侧选择档案并执行审计")
        return
    
    semantic_report = audit_result['semantic_report']
    
    # 1. 核心矛盾（紧凑版）
    st.markdown(f"""
    <div class="section-title" style="font-size: 15px; margin-top: 5px;">⚡ 核心矛盾</div>
    <div class="audit-report-card" style="padding: 10px; margin: 3px 0;">
        <p style="color: {COLORS['rose_magenta']}; font-size: 14px; line-height: 1.6; margin: 0;">
            {semantic_report.get('core_conflict', '暂无分析')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. 深度画像（紧凑版）
    st.markdown(f"""
    <div class="section-title" style="font-size: 15px; margin-top: 5px;">👤 深度画像</div>
    <div class="audit-report-card" style="padding: 10px; margin: 3px 0;">
        <p style="color: #e2e8f0; font-size: 13px; line-height: 1.6; text-align: justify; margin: 0;">
            {semantic_report.get('persona', '暂无分析')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. 财富相预测（紧凑版）
    st.markdown(f"""
    <div class="section-title" style="font-size: 15px; margin-top: 5px;">💰 财富相预测</div>
    <div class="audit-report-card" style="padding: 10px; margin: 3px 0;">
        <div style="color: {COLORS['mystic_gold']}; font-size: 13px; line-height: 1.6; margin: 0;">
            {semantic_report.get('wealth_prediction', '暂无分析')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 4. 干预药方（紧凑版）
    st.markdown(f"""
    <div class="section-title" style="font-size: 15px; margin-top: 5px;">💊 干预药方</div>
    <div class="audit-report-card" style="padding: 10px; margin: 3px 0;">
        <div style="color: {COLORS['teal_mist']}; font-size: 13px; line-height: 1.6; white-space: pre-line; margin: 0;">
            {semantic_report.get('prescription', '暂无分析')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # [QGA V24.4] LLM Debug Console（如果启用了LLM）
    # 注意：semantic_report已经在上面定义了（第573行），这里直接使用
    use_llm = st.session_state.get('use_llm_synthesis', False)
    debug_data = semantic_report.get('debug_data')
    debug_prompt = semantic_report.get('debug_prompt', '')
    debug_response = semantic_report.get('debug_response', '')
    
    # 如果启用了LLM，始终显示Debug Console区域（即使没有数据也显示提示）
    if use_llm:
        st.markdown("---")
        st.markdown(f"""
        <div class="section-title" style="font-size: 15px; margin-top: 5px; color: {COLORS['mystic_gold']};">
            🔬 LLM调试控制台 (Debug Console)
        </div>
        """, unsafe_allow_html=True)
        
        if debug_data:
            # 有debug数据，正常显示
            st.markdown(f"""
            <div style="background: rgba(45, 27, 78, 0.3); padding: 8px; border-radius: 6px; margin: 5px 0; font-size: 12px; color: {COLORS['teal_mist']};">
                💡 这里显示发送给LLM的原始数据、Prompt模板和LLM的原始响应，用于调试和验证LLM的逻辑推理过程
            </div>
            """, unsafe_allow_html=True)
            
            col_debug_left, col_debug_mid, col_debug_right = st.columns([1, 1, 1])
            
            with col_debug_left:
                st.markdown("**📥 发送给LLM的数据 (Input JSON)**")
                import json
                st.json(debug_data if debug_data else {})
                if debug_data:
                    st.caption(f"包含 {len(debug_data.get('ActivePatterns', []))} 个激活格局")
            
            with col_debug_mid:
                st.markdown("**📝 Prompt模板 (Prompt Template)**")
                # 显示完整Prompt，但限制显示长度
                prompt_display = debug_prompt if debug_prompt else "未生成"
                if len(prompt_display) > 2000:
                    prompt_display = prompt_display[:2000] + "\n\n... (已截断，完整内容请查看代码)"
                st.text_area(
                    "Prompt",
                    value=prompt_display,
                    height=250,
                    key="debug_prompt_display",
                    disabled=True,
                    label_visibility="collapsed"
                )
                st.caption("💡 提示：Prompt在代码中定义，如需修改请编辑 `core/models/llm_semantic_synthesizer.py`")
            
            with col_debug_right:
                st.markdown("**📤 LLM原始响应 (Raw Response)**")
                response_display = debug_response if debug_response else "无响应"
                if len(response_display) > 2000:
                    response_display = response_display[:2000] + "\n\n... (已截断)"
                st.text_area(
                    "Response",
                    value=response_display,
                    height=250,
                    key="debug_response_display",
                    label_visibility="collapsed"
                )
                if debug_response:
                    st.caption(f"响应长度: {len(debug_response)} 字符")
            
            # 显示解析结果
            st.markdown("---")
            st.markdown("**✅ 解析结果 (Parsed Results)**")
            col_result_left, col_result_right = st.columns([2, 1])
            
            with col_result_left:
                st.markdown("**生成的画像 (Persona):**")
                st.text_area(
                    "Persona",
                    value=semantic_report.get('persona', '')[:500],
                    height=100,
                    key="debug_persona_display",
                    disabled=True,
                    label_visibility="collapsed"
                )
            
            with col_result_right:
                st.markdown("**五行校准 (Element Calibration):**")
                calibration = audit_result.get('llm_calibration', {})
                if calibration:
                    st.json(calibration)
                else:
                    st.info("无五行校准数据")
            
            # [QGA V24.5] 完整审计报告（可复制）- 放在解析结果之后
            st.markdown("---")
            st.markdown(f"""
            <div class="section-title" style="font-size: 15px; margin-top: 10px; color: {COLORS['mystic_gold']};">
                📋 完整审计报告（供AI分析师）
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: rgba(45, 27, 78, 0.3); padding: 8px; border-radius: 6px; margin: 5px 0; font-size: 12px; color: {COLORS['teal_mist']};">
                💡 此报告包含完整的LLM交互信息，可直接复制发送给AI分析师进行深度审计
            </div>
            """, unsafe_allow_html=True)
            
            # 构建完整报告
            import json
            from datetime import datetime
            
            report_parts = []
            report_parts.append("=" * 80)
            report_parts.append("QGA 八字档案审计 - LLM交互完整报告")
            report_parts.append("=" * 80)
            report_parts.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_parts.append("")
            
            # 1. 基本信息
            report_parts.append("【1. 基本信息】")
            report_parts.append("-" * 80)
            if 'profile' in audit_result:
                profile = audit_result['profile']
                report_parts.append(f"档案名称: {profile.get('name', 'N/A')}")
                report_parts.append(f"出生日期: {profile.get('year', '')}年{profile.get('month', '')}月{profile.get('day', '')}日 {profile.get('hour', '')}时")
                report_parts.append(f"性别: {profile.get('gender', 'N/A')}")
            if 'bazi_profile' in audit_result:
                bazi = audit_result['bazi_profile']
                pillars = bazi.get('pillars', {})
                report_parts.append(f"八字: {pillars.get('year', '')} {pillars.get('month', '')} {pillars.get('day', '')} {pillars.get('hour', '')}")
                report_parts.append(f"日主: {bazi.get('day_master', 'N/A')}")
            report_parts.append("")
            
            # 2. 发送给LLM的数据
            report_parts.append("【2. 发送给LLM的输入数据 (Input JSON)】")
            report_parts.append("-" * 80)
            report_parts.append("数据格式: JSON")
            report_parts.append("")
            report_parts.append(json.dumps(debug_data, ensure_ascii=False, indent=2))
            report_parts.append("")
            
            # 3. Prompt模板
            report_parts.append("【3. LLM Prompt模板】")
            report_parts.append("-" * 80)
            report_parts.append(f"Prompt长度: {len(debug_prompt)} 字符")
            report_parts.append("")
            report_parts.append(debug_prompt if debug_prompt else "未生成")
            report_parts.append("")
            
            # 4. LLM原始响应
            report_parts.append("【4. LLM原始响应 (Raw Response)】")
            report_parts.append("-" * 80)
            report_parts.append(f"响应长度: {len(debug_response)} 字符")
            if debug_response:
                report_parts.append("")
                report_parts.append(debug_response)
            else:
                report_parts.append("(无响应)")
            report_parts.append("")
            
            # 5. APP处理逻辑
            report_parts.append("【5. APP处理逻辑】")
            report_parts.append("-" * 80)
            report_parts.append("5.1 解析步骤:")
            report_parts.append("  - 优先尝试解析纯JSON格式（包含'persona'和'corrected_elements'字段）")
            report_parts.append("  - 如果失败，回退到旧格式解析（查找'核心矛盾：'和'修正后：'标记）")
            report_parts.append("  - 应用非负约束（所有五行值 >= 0）")
            report_parts.append("  - 计算五行校准偏移量（corrected - original）")
            report_parts.append("")
            report_parts.append("5.2 解析结果:")
            
            # 解析结果详情
            parsed_persona = semantic_report.get('persona', '')
            calibration = audit_result.get('llm_calibration', {})
            report_parts.append(f"  生成的画像: {parsed_persona[:200]}..." if len(parsed_persona) > 200 else f"  生成的画像: {parsed_persona}")
            if calibration:
                report_parts.append("  五行校准偏移量:")
                for element, offset in calibration.items():
                    report_parts.append(f"    {element}: {offset:+.2f}")
            else:
                report_parts.append("  五行校准: 无数据")
            report_parts.append("")
            
            # 6. 错误信息（如果有）
            debug_error = semantic_report.get('debug_error')
            if debug_error:
                report_parts.append("【6. 错误信息】")
                report_parts.append("-" * 80)
                report_parts.append(debug_error)
                report_parts.append("")
            
            # 7. 系统信息
            report_parts.append("【7. 系统信息】")
            report_parts.append("-" * 80)
            if hasattr(st, 'session_state') and 'llm_connection_info' in st.session_state:
                conn_info = st.session_state.get('llm_connection_info', {})
                report_parts.append(f"LLM模型: {conn_info.get('model_name', 'N/A')}")
                report_parts.append(f"API地址: {conn_info.get('ollama_host', 'N/A')}")
                report_parts.append(f"连接状态: {conn_info.get('connection_status', 'N/A')}")
            report_parts.append("")
            
            report_parts.append("=" * 80)
            report_parts.append("报告结束")
            report_parts.append("=" * 80)
            
            # 合并报告
            full_report = "\n".join(report_parts)
            
            # 显示报告（可复制）
            st.text_area(
                "完整审计报告",
                value=full_report,
                height=600,
                key="full_audit_report",
                help="此报告包含完整的LLM交互信息，可直接复制发送给AI分析师",
                label_visibility="collapsed"
            )
            
            # 添加复制提示
            st.info("💡 **提示**: 点击文本框右上角的复制按钮，或使用 Ctrl+A 全选后 Ctrl+C 复制整个报告")
        else:
            # 没有debug数据，显示提示信息
            st.warning(f"""
            ⚠️ **Debug数据未找到**
            
            - LLM开关: ✅ 已启用
            - Debug数据: ❌ 未生成
            
            **可能原因：**
            1. LLM调用失败（请检查LLM连接状态）
            2. 使用了规则生成（LLM未实际调用）
            3. Debug数据未正确保存
            
            **调试步骤：**
            1. 检查左侧LLM连接状态是否显示"连接正常"
            2. 查看浏览器控制台是否有错误信息
            3. 重新执行审计
            """)
    
    # 5. 技术细节（可折叠）
    with st.expander("🔬 技术细节（物理计算）", expanded=False):
        if 'pfa' in audit_result:
            st.markdown("**格局冲突分析 (PFA):**")
            st.write(f"- 冲突指数: {audit_result['pfa']['friction_index']:.2f}")
            st.write(f"- 相干性等级: {audit_result['pfa']['coherence_level']}")
            if audit_result['pfa']['conflicting_patterns']:
                st.write(f"- 冲突格局: {', '.join(audit_result['pfa']['conflicting_patterns'])}")
        
        if 'soa' in audit_result:
            st.markdown("**系统优化分析 (SOA):**")
            st.write(f"- 稳定性分数: {audit_result['soa']['stability_score']:.3f}")
            st.write(f"- 熵值降低: {audit_result['soa']['entropy_reduction']:.3f}")
            if audit_result['soa']['optimal_elements']:
                st.write(f"- 最优元素: {audit_result['soa']['optimal_elements']}")
        
        if 'mca' in audit_result:
            st.markdown("**介质修正分析 (MCA):**")
            st.write(f"- 地理修正: {audit_result['mca']['geo_correction']}")
            st.write(f"- 微环境修正: {audit_result['mca']['micro_env_correction']}")
        
        if 'bazi_profile' in audit_result:
            st.markdown("**八字信息:**")
            pillars = audit_result['bazi_profile']['pillars']
            st.write(f"八字: {pillars.get('year', '')} {pillars.get('month', '')} {pillars.get('day', '')} {pillars.get('hour', '')}")
            st.write(f"日主: {audit_result['bazi_profile'].get('day_master', '')}")
    
    # [QGA V25.0 Phase 5] Neural Route Trace - 神经矩阵路由溯源面板
    if 'neural_router_metadata' in audit_result or 'logic_collapse' in audit_result:
        st.markdown("---")
        st.markdown(f"""
        <div class="section-title" style="font-size: 16px; margin-top: 10px; color: {COLORS['mystic_gold']};">
            🧠 神经矩阵路由溯源 (Neural Route Trace) [V25.0]
        </div>
        """, unsafe_allow_html=True)
        
        neural_metadata = audit_result.get('neural_router_metadata', {})
        feature_vector = neural_metadata.get('feature_vector', {})
        logic_collapse = audit_result.get('logic_collapse', {})
        energy_state = audit_result.get('energy_state_report', {})
        
        # 1. 特征向量指纹雷达图
        if feature_vector and 'elemental_fields_dict' in feature_vector:
            st.markdown("#### 🔬 特征向量指纹 (Phase 2)")
            elemental_fields = feature_vector.get('elemental_fields_dict', {})
            stress_tensor = feature_vector.get('stress_tensor', 0.0)
            phase_coherence = feature_vector.get('phase_coherence', 0.0)
            
            # 创建雷达图
            elements = ['金', '木', '水', '火', '土']
            element_keys = ['metal', 'wood', 'water', 'fire', 'earth']
            values = [elemental_fields.get(key, 0.0) * 100 for key in element_keys]  # 转换为百分比
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=elements,
                fill='toself',
                name='五行场强',
                line_color=COLORS['teal_mist'],
                fillcolor=f"rgba(64, 224, 208, 0.3)"
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickfont=dict(color='#e2e8f0', size=10),
                        gridcolor='rgba(255, 255, 255, 0.2)'
                    ),
                    angularaxis=dict(
                        tickfont=dict(color='#e2e8f0', size=11),
                        linecolor='rgba(255, 255, 255, 0.3)'
                    ),
                    bgcolor='rgba(0, 0, 0, 0)'
                ),
                showlegend=False,
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0, 0, 0, 0)',
                plot_bgcolor='rgba(0, 0, 0, 0)',
                font_color='#e2e8f0',
                title=dict(
                    text="特征向量指纹（五行场强分布）",
                    font=dict(size=14, color=COLORS['mystic_gold']),
                    x=0.5
                )
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # 显示数值和关键指标
            col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
            with col_metrics1:
                st.metric("应力张量", f"{stress_tensor:.3f}", 
                         help="系统内部冲突压力（0.0-1.0）")
            with col_metrics2:
                st.metric("相位一致性", f"{phase_coherence:.3f}",
                         help="相位关系协调度（0.0-1.0）")
            with col_metrics3:
                max_elem = max(elemental_fields.items(), key=lambda x: x[1])[0] if elemental_fields else "未知"
                elem_cn = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}.get(max_elem, '未知')
                st.metric("主导元素", elem_cn,
                         help="场强最高的五行元素")
        
        # 2. 权重坍缩热力图
        if logic_collapse:
            st.markdown("#### ⚖️ 逻辑权重坍缩 (Phase 4)")
            
            # 创建热力图数据
            pattern_names = []
            weights = []
            for pattern_id, weight in sorted(logic_collapse.items(), key=lambda x: -x[1]):
                # 尝试获取格局中文名称
                pattern_name = pattern_id
                # 可以从注册表获取，这里简化处理
                pattern_name_map = {
                    'SHANG_GUAN_JIAN_GUAN': '伤官见官',
                    'XIAO_SHEN_DUO_SHI': '枭神夺食',
                    'CONG_ER_GE': '从儿格',
                    'YANG_REN_JIA_SHA': '羊刃架杀',
                    'HUA_HUO_GE': '化火格',
                    'JIAN_LU_YUE_JIE': '建禄月劫',
                    'GUAN_YIN_XIANG_SHENG': '官印相生'
                }
                pattern_name = pattern_name_map.get(pattern_id, pattern_id)
                pattern_names.append(pattern_name)
                weights.append(weight * 100)  # 转换为百分比
            
            # 创建水平条形图（热力图风格）
            fig_heatmap = go.Figure()
            fig_heatmap.add_trace(go.Bar(
                x=weights,
                y=pattern_names,
                orientation='h',
                marker=dict(
                    color=weights,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="权重 (%)", titlefont=dict(color='#e2e8f0'), tickfont=dict(color='#e2e8f0'))
                ),
                text=[f"{w:.2f}%" for w in weights],
                textposition='outside',
                textfont=dict(color='#e2e8f0', size=11)
            ))
            
            fig_heatmap.update_layout(
                title=dict(
                    text="格局权重贡献分布（自动坍缩）",
                    font=dict(size=14, color=COLORS['mystic_gold']),
                    x=0.5
                ),
                xaxis=dict(
                    title="贡献百分比 (%)",
                    range=[0, 105],
                    tickfont=dict(color='#e2e8f0'),
                    gridcolor='rgba(255, 255, 255, 0.1)'
                ),
                yaxis=dict(
                    tickfont=dict(color='#e2e8f0'),
                    gridcolor='rgba(255, 255, 255, 0.1)'
                ),
                height=200 + len(pattern_names) * 40,
                margin=dict(l=100, r=20, t=50, b=20),
                paper_bgcolor='rgba(0, 0, 0, 0)',
                plot_bgcolor='rgba(0, 0, 0, 0)',
                font_color='#e2e8f0'
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # 显示权重总和验证
            total_weight = sum(logic_collapse.values()) * 100
            if 95 <= total_weight <= 105:
                st.success(f"✅ 权重归一化验证通过: {total_weight:.2f}%")
            else:
                st.warning(f"⚠️ 权重总和异常: {total_weight:.2f}% (应在95-105%范围内)")
        
        # 3. 能量状态报告（波形图）
        if energy_state:
            st.markdown("#### ⚡ 能量状态报告 (Phase 4)")
            
            system_stability = energy_state.get('system_stability', 0.0)
            critical_state = energy_state.get('critical_state', '未知')
            stress_tensor = energy_state.get('stress_tensor', 0.0)
            phase_coherence = energy_state.get('phase_coherence', 0.0)
            
            # 创建稳定性波形图
            import numpy as np
            time_points = np.linspace(0, 10, 100)
            
            # 根据稳定性生成波形
            if system_stability < 0.3:
                # 崩态：高频震荡
                waveform = 0.5 + 0.3 * np.sin(10 * time_points) * np.exp(-time_points * 0.1)
                wave_color = COLORS['rose_magenta']
                wave_label = "崩态波形（高频震荡）"
            elif system_stability < 0.5:
                # 临界态：中频波动
                waveform = 0.5 + 0.2 * np.sin(5 * time_points) * np.exp(-time_points * 0.05)
                wave_color = '#FFA500'  # 橙色
                wave_label = "临界态波形（中频波动）"
            elif phase_coherence > 0.7:
                # 稳态：平滑波形
                waveform = 0.5 + 0.1 * np.sin(2 * time_points) * np.exp(-time_points * 0.02)
                wave_color = COLORS['teal_mist']
                wave_label = "稳态波形（平滑传导）"
            else:
                # 波动态：低频波动
                waveform = 0.5 + 0.15 * np.sin(3 * time_points) * np.exp(-time_points * 0.03)
                wave_color = '#FFFF00'  # 黄色
                wave_label = "波动态波形（低频波动）"
            
            fig_wave = go.Figure()
            fig_wave.add_trace(go.Scatter(
                x=time_points,
                y=waveform,
                mode='lines',
                name=wave_label,
                line=dict(color=wave_color, width=2),
                fill='tozeroy',
                fillcolor=wave_color.replace('#', 'rgba(').replace('', '') + ', 0.2)' if wave_color.startswith('#') else f"rgba(64, 224, 208, 0.2)"
            ))
            
            # 添加稳定性阈值线
            fig_wave.add_hline(
                y=system_stability,
                line_dash="dash",
                line_color=COLORS['mystic_gold'],
                annotation_text=f"系统稳定性: {system_stability:.3f}",
                annotation_position="right"
            )
            
            fig_wave.update_layout(
                title=dict(
                    text=f"能量状态波形 - {critical_state}",
                    font=dict(size=14, color=COLORS['mystic_gold']),
                    x=0.5
                ),
                xaxis=dict(
                    title="时间（相对单位）",
                    tickfont=dict(color='#e2e8f0'),
                    gridcolor='rgba(255, 255, 255, 0.1)'
                ),
                yaxis=dict(
                    title="能量振幅",
                    range=[0, 1],
                    tickfont=dict(color='#e2e8f0'),
                    gridcolor='rgba(255, 255, 255, 0.1)'
                ),
                height=250,
                margin=dict(l=50, r=20, t=50, b=30),
                paper_bgcolor='rgba(0, 0, 0, 0)',
                plot_bgcolor='rgba(0, 0, 0, 0)',
                font_color='#e2e8f0',
                showlegend=True,
                legend=dict(
                    font=dict(color='#e2e8f0'),
                    bgcolor='rgba(0, 0, 0, 0)'
                )
            )
            
            st.plotly_chart(fig_wave, use_container_width=True)
            
            # 显示关键指标
            col_energy1, col_energy2, col_energy3 = st.columns(3)
            with col_energy1:
                stability_color = COLORS['rose_magenta'] if system_stability < 0.3 else (COLORS['teal_mist'] if system_stability > 0.7 else '#FFA500')
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: rgba(45, 27, 78, 0.3); border-radius: 6px; border-left: 3px solid {stability_color};">
                    <div style="font-size: 11px; color: {COLORS['teal_mist']};">系统稳定性</div>
                    <div style="font-size: 18px; font-weight: bold; color: {stability_color};">{system_stability:.3f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_energy2:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: rgba(45, 27, 78, 0.3); border-radius: 6px; border-left: 3px solid {COLORS['mystic_gold']};">
                    <div style="font-size: 11px; color: {COLORS['teal_mist']};">临界状态</div>
                    <div style="font-size: 14px; font-weight: bold; color: {COLORS['mystic_gold']};">{critical_state[:15]}...</div>
                </div>
                """, unsafe_allow_html=True)
            with col_energy3:
                energy_flow = energy_state.get('energy_flow_direction', '未知')
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: rgba(45, 27, 78, 0.3); border-radius: 6px; border-left: 3px solid {COLORS['teal_mist']};">
                    <div style="font-size: 11px; color: {COLORS['teal_mist']};">能量流向</div>
                    <div style="font-size: 12px; font-weight: bold; color: {COLORS['teal_mist']};">{energy_flow[:20]}...</div>
                </div>
                """, unsafe_allow_html=True)
        
        # 4. 处理元数据摘要
        if neural_metadata:
            with st.expander("🔧 处理元数据详情", expanded=False):
                st.markdown(f"""
                - **格局数**: {neural_metadata.get('pattern_count', 'N/A')}
                - **综合SAI**: {neural_metadata.get('aggregated_sai', 'N/A')}
                - **Prompt长度**: {neural_metadata.get('inline_prompt_length', 'N/A')} 字符
                - **场强阈值**: {neural_metadata.get('field_strength_threshold', 'N/A')}
                - **相干权重**: {neural_metadata.get('coherence_weight', 'N/A')}
                - **熵值阻尼**: {neural_metadata.get('entropy_damping', 'N/A')}
                """)
                if 'matrix_routing' in neural_metadata:
                    matrix_info = neural_metadata['matrix_routing']
                    st.markdown(f"""
                    - **权重数**: {matrix_info.get('collapse_weights_count', 'N/A')}
                    - **能量稳定性**: {matrix_info.get('energy_stability', 'N/A')}
                    """)
        
        st.caption("💡 [V25.0] 神经矩阵路由系统自动计算格局权重和能量状态，无需手动配置")
    
    # [QGA V24.7] 逻辑审计溯源面板：显示BaseVectorBias
    if 'pattern_audit' in audit_result:
        pattern_audit = audit_result['pattern_audit']
        
        # 显示BaseVectorBias（初始物理偏差）
        if 'base_vector_bias' in pattern_audit:
            st.markdown("---")
            st.markdown(f"""
            <div class="section-title" style="font-size: 14px; margin-top: 10px; color: {COLORS['mystic_gold']};">
                ⚖️ 初始物理偏差 (BaseVectorBias)
            </div>
            """, unsafe_allow_html=True)
            
            bias = pattern_audit['base_vector_bias']
            geo_context = pattern_audit.get('geo_context', '')
            
            # 显示地理环境
            if geo_context:
                st.caption(f"📍 地理环境: {geo_context}")
            
            # 显示偏差值（5列布局）
            col_bias1, col_bias2, col_bias3, col_bias4, col_bias5 = st.columns(5)
            element_map = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
            element_colors = {
                'metal': '#FFD700',  # 金色
                'wood': '#32CD32',   # 绿色
                'water': '#1E90FF',  # 蓝色
                'fire': '#FF4500',   # 红色
                'earth': '#8B4513'   # 棕色
            }
            
            cols = [col_bias1, col_bias2, col_bias3, col_bias4, col_bias5]
            for idx, (en_name, cn_name) in enumerate(element_map.items()):
                with cols[idx]:
                    val = bias.get(en_name, 0.0)
                    color = element_colors.get(en_name, '#FFFFFF')
                    sign = "+" if val >= 0 else ""
                    st.markdown(f"""
                    <div style="text-align: center; padding: 8px; background: rgba(45, 27, 78, 0.3); border-radius: 6px; border-left: 3px solid {color};">
                        <div style="font-size: 11px; color: {COLORS['teal_mist']};">{cn_name}</div>
                        <div style="font-size: 14px; font-weight: bold; color: {color if abs(val) > 0.1 else COLORS['teal_mist']};">{sign}{val:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.caption("💡 这是格局引擎根据激活格局计算出的初始物理偏差，LLM将在此基础上进行微调（±10%以内）")
    
    # [QGA V24.2] 实时激活格局清单（时空耦合格局审计，紧凑版）
    if 'pattern_audit' in audit_result:
        pattern_audit = audit_result['pattern_audit']
        state_changes = pattern_audit.get('state_changes', [])
        
        st.markdown("---")
        st.markdown(f"""
        <div class="section-title" style="font-size: 15px; margin-top: 5px;">🔬 实时激活格局清单</div>
        <div class="audit-report-card" style="padding: 8px; margin: 3px 0;">
            <p style="color: {COLORS['teal_mist']}; font-size: 12px; margin: 0;">
                <strong>流年:</strong> {pattern_audit.get('year', 'N/A')}年 {pattern_audit.get('year_pillar', '')} | 
                <strong>大运:</strong> {pattern_audit.get('luck_pillar', '')} | 
                <strong>激活:</strong> {pattern_audit.get('total_count', 0)}个格局
            </p>
            {f'<p style="color: {COLORS["rose_magenta"]}; font-size: 11px; margin: 3px 0 0 0;">⚠️ {len(state_changes)}个状态变化</p>' if state_changes else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # 显示格局状态变化（如果有，紧凑版）
        if state_changes:
            with st.expander(f"⚠️ 格局状态变化 ({len(state_changes)}个)", expanded=False):
                for change in state_changes:
                    st.warning(f"""
                    **{change.get('original', '')}** → **{change.get('current', '')}**
                    
                    {change.get('trigger', '')}
                    
                    {change.get('impact', '')}
                    """)
        
        patterns = pattern_audit.get('patterns', [])
        
        # [QGA V24.2] 优先显示状态变化的格局
        state_changed_patterns = [p for p in patterns if p.get('is_state_changed', False)]
        other_patterns = [p for p in patterns if not p.get('is_state_changed', False)]
        
        # 先显示状态变化的格局
        for i, pattern in enumerate(state_changed_patterns + other_patterns):
            pattern_type = pattern.get('type', 'normal')
            type_colors = {
                'primary': COLORS['mystic_gold'],
                'conflict': COLORS['rose_magenta'],
                'sub': '#FFA500',  # 橙色
                'normal': COLORS['teal_mist']
            }
            type_labels = {
                'primary': '主格局',
                'conflict': '冲突格局',
                'sub': '子格局',
                'normal': '普通格局'
            }
            
            # 状态变化的格局用特殊标记
            pattern_name = pattern.get('name', '未知格局')
            if pattern.get('is_state_changed', False):
                pattern_name = f"🔄 {pattern_name} (状态已变化)"
            
            with st.expander(f"【{pattern_name}】 ({type_labels.get(pattern_type, '未知')})", expanded=(i == 0 or pattern.get('is_state_changed', False))):
                # 击中逻辑（紧凑版）
                st.markdown(f"""
                <div style="background: rgba(45, 27, 78, 0.3); padding: 8px; border-radius: 4px; margin-bottom: 6px;">
                    <strong style="color: {type_colors.get(pattern_type, COLORS['teal_mist'])}; font-size: 12px;">🎯 击中逻辑:</strong>
                    <p style="color: #e2e8f0; font-size: 12px; margin: 3px 0 0 0; line-height: 1.4;">
                        {pattern.get('matching_logic', '暂无')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 格局特性（紧凑版）
                characteristics = pattern.get('characteristics', {})
                st.markdown(f"""
                <div style="background: rgba(45, 27, 78, 0.3); padding: 8px; border-radius: 4px; margin-bottom: 6px;">
                    <strong style="color: {COLORS['mystic_gold']}; font-size: 12px;">⚡ 格局特性:</strong>
                    <p style="color: #e2e8f0; font-size: 12px; margin: 3px 0 0 0; line-height: 1.4;">
                        <strong>物理:</strong> {characteristics.get('physical', '暂无')}<br>
                        <strong>宏观:</strong> {characteristics.get('destiny', '暂无')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 干预策略（紧凑版）
                intervention = pattern.get('intervention', {})
                st.markdown(f"""
                <div style="background: rgba(45, 27, 78, 0.3); padding: 8px; border-radius: 4px;">
                    <strong style="color: {COLORS['rose_magenta']}; font-size: 12px;">💊 干预策略:</strong>
                    <p style="color: #e2e8f0; font-size: 12px; margin: 3px 0 0 0; line-height: 1.4;">
                        <strong>用神:</strong> {intervention.get('yong_shen', '待定')} | 
                        <strong>空间:</strong> {intervention.get('spatial', '无')[:30]}...<br>
                        <strong>行为:</strong> {intervention.get('behavioral', '无')[:40]}...
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 技术指标（紧凑版）
                if pattern.get('sai', 0) > 0 or pattern.get('stress', 0) > 0:
                    st.caption(f"SAI: {pattern.get('sai', 0):.2f} | Stress: {pattern.get('stress', 0):.2f}")


if __name__ == "__main__":
    render()
