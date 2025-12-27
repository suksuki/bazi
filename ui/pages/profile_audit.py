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
