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
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }}
    .section-title {{
        color: {COLORS['mystic_gold']};
        font-size: 18px;
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 10px;
        border-bottom: 2px solid rgba(255, 215, 0, 0.3);
        padding-bottom: 5px;
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
    
    # --- 三栏布局：左侧档案选择、中间矢量图、右侧报告 ---
    col_left, col_mid, col_right = st.columns([1.2, 1.5, 1.8])
    
    with col_left:
        render_profile_selector(controller, all_profiles)
    
    with col_mid:
        render_force_vector_diagram(controller)
    
    with col_right:
        render_audit_report(controller)


def render_profile_selector(controller: ProfileAuditController, all_profiles: list):
    """渲染左侧：档案与环境注入"""
    st.markdown(f"""
    <div class="audit-report-card">
        <h3 style="color: {COLORS['mystic_gold']};">📂 档案与环境注入</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. 档案选择
    st.markdown("#### 👤 选择档案")
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
            st.markdown(f"**姓名**: {profile.get('name', '未知')}")
            st.markdown(f"**性别**: {profile.get('gender', '未知')}")
            st.markdown(f"**出生**: {profile.get('year', '?')}年{profile.get('month', '?')}月{profile.get('day', '?')}日 {profile.get('hour', '?')}时")
    
    st.divider()
    
    # 2. 流年选择（显示对应大运）
    st.markdown("#### 📅 流年选择")
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
    st.markdown("#### 🌍 地理环境")
    
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
                
                audit_result = controller.perform_deep_audit(
                    selected_profile_id,
                    year=selected_year,
                    city=city_name,
                    micro_env=selected_micro_env if selected_micro_env else None
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
    
    force_vectors = audit_result['force_vectors']
    
    # 创建极坐标图显示五行受力
    elements = ['金', '木', '水', '火', '土']
    element_keys = ['metal', 'wood', 'water', 'fire', 'earth']
    values = [force_vectors.get(key, 20.0) for key in element_keys]
    
    # 创建雷达图
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=elements,
        fill='toself',
        name='五行能量',
        line_color=COLORS['teal_mist'],
        fillcolor=f"rgba(64, 224, 208, 0.3)"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color='#e2e8f0'),
                gridcolor='rgba(255, 255, 255, 0.2)'
            ),
            angularaxis=dict(
                tickfont=dict(color='#e2e8f0'),
                linecolor='rgba(255, 255, 255, 0.3)'
            ),
            bgcolor='rgba(0, 0, 0, 0)'
        ),
        showlegend=False,
        height=400,
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        font_color='#e2e8f0'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 显示数值
    st.markdown("**五行能量分布:**")
    cols = st.columns(5)
    element_colors = {
        '金': '#FFD700', '木': '#10B981', '水': '#3B82F6',
        '火': '#EF4444', '土': '#F59E0B'
    }
    for i, (elem, val, key) in enumerate(zip(elements, values, element_keys)):
        with cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: rgba(45, 27, 78, 0.3); border-radius: 8px; border: 1px solid {element_colors[elem]};">
                <div style="color: {element_colors[elem]}; font-size: 14px; font-weight: bold;">{elem}</div>
                <div style="color: {COLORS['teal_mist']}; font-size: 20px; font-weight: bold;">{val:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)


def render_audit_report(controller: ProfileAuditController):
    """渲染右侧：审计报告书（人话翻译）"""
    st.markdown(f"""
    <div class="audit-report-card">
        <h3 style="color: {COLORS['mystic_gold']};">📋 审计报告书</h3>
    </div>
    """, unsafe_allow_html=True)
    
    audit_result = st.session_state.get('current_audit_result')
    
    if not audit_result or 'semantic_report' not in audit_result:
        st.info("👈 请先在左侧选择档案并执行审计")
        return
    
    semantic_report = audit_result['semantic_report']
    
    # 1. 核心矛盾
    st.markdown(f"""
    <div class="section-title">⚡ 核心矛盾</div>
    <div class="audit-report-card">
        <p style="color: {COLORS['rose_magenta']}; font-size: 16px; line-height: 1.8;">
            {semantic_report.get('core_conflict', '暂无分析')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. 深度画像
    st.markdown(f"""
    <div class="section-title">👤 深度画像</div>
    <div class="audit-report-card">
        <p style="color: #e2e8f0; font-size: 14px; line-height: 1.8; text-align: justify;">
            {semantic_report.get('persona', '暂无分析')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. 财富相预测
    st.markdown(f"""
    <div class="section-title">💰 财富相预测</div>
    <div class="audit-report-card">
        <div style="color: {COLORS['mystic_gold']}; font-size: 14px; line-height: 1.8;">
            {semantic_report.get('wealth_prediction', '暂无分析')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 4. 干预药方
    st.markdown(f"""
    <div class="section-title">💊 干预药方</div>
    <div class="audit-report-card">
        <div style="color: {COLORS['teal_mist']}; font-size: 14px; line-height: 1.8; white-space: pre-line;">
            {semantic_report.get('prescription', '暂无分析')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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


if __name__ == "__main__":
    render()
