#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量子通用架构注册信息页面 (Quantum Framework Registry Page)
—— 显示量子通用架构下所有主体和专题的注册信息 ——

**版本**: V1.0
**状态**: ACTIVE
**MVC**: View Layer - 仅负责UI展示，所有业务逻辑通过Controller处理
"""

import streamlit as st
from pathlib import Path
import sys
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# MVC: 只导入Controller，不直接操作Model
from controllers.quantum_framework_registry_controller import QuantumFrameworkRegistryController
from ui.components.theme import apply_custom_header, COLORS

# 注册表规范版本（与 FDS-SOP / QGA-HR 一致，统一为 3.0）
REGISTRY_SCHEMA_VERSION = "3.0"


def _subject_display_name(name: str, subjects: list) -> str:
    """下拉框显示名：全息格局用中文，其余用原名 + 专题数"""
    subject = next((s for s in subjects if s.get('name') == name), None)
    count = subject.get('topics_count', 0) if subject else 0
    if name == 'holographic_pattern':
        return f"全息格局（正官格等）({count} 个专题)"
    return f"{name} ({count} 个专题)"


def render_subject_card(subject: dict):
    """渲染单个主体信息卡片"""
    subject_name = subject.get('name', 'UNKNOWN')
    metadata = subject.get('metadata', {})
    topics_count = subject.get('topics_count', 0)
    has_registry = subject.get('has_registry', False)
    
    # 获取主体描述
    description = metadata.get('description', '无描述')
    name_cn = metadata.get('name', subject_name)
    name_en = metadata.get('name_en', '')
    
    # 状态颜色
    status_color = COLORS.get('teal_mist', '#40e0d0') if has_registry else COLORS.get('rose_magenta', '#c21e56')
    status_text = "✅ 已注册" if has_registry else "⚠️ 未注册"
    
    with st.container():
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {COLORS.get('glass_bg', 'rgba(30,30,60,0.95)')} 0%, rgba(20,20,40,0.98) 100%);
            border: 1px solid {COLORS.get('border', 'rgba(255,255,255,0.1)')};
            border-left: 4px solid {status_color};
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        ">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                <div style="flex: 1;">
                    <h3 style="margin: 0; color: {COLORS.get('primary', '#40e0d0')};">
                        📁 {subject_name}
                    </h3>
                    <p style="margin: 0.3rem 0 0 0; color: {COLORS.get('mystic_gold', '#ffd700')}; font-size: 1.1rem; font-weight: bold;">
                        {name_cn}
                    </p>
                    {f'<p style="margin: 0.2rem 0 0 0; color: {COLORS.get("text_secondary", "#a0a0a0")}; font-size: 0.9rem; font-style: italic;">{name_en}</p>' if name_en else ''}
                </div>
                <div style="text-align: right;">
                    <div style="color: {status_color}; font-weight: bold; font-size: 1.0rem; margin-bottom: 0.5rem;">
                        {status_text}
                    </div>
                    <div style="color: {COLORS.get('accent', '#ffd700')}; font-weight: bold; font-size: 1.2rem;">
                        {topics_count}
                    </div>
                    <div style="color: {COLORS.get('text_secondary', '#a0a0a0')}; font-size: 0.9rem;">
                        专题数量
                    </div>
                </div>
            </div>
            
            <div style="
                color: {COLORS.get('text', '#e2e8f0')};
                font-size: 0.95rem;
                line-height: 1.6;
                margin-top: 1rem;
                padding-top: 1rem;
                border-top: 1px solid {COLORS.get('border', 'rgba(255,255,255,0.1)')};
            ">
                {description}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_topic_item(topic_id: str, topic_data: dict, index: int):
    """渲染单个专题项"""
    name_cn = topic_data.get('name_cn') or topic_data.get('name', topic_id)
    description = topic_data.get('description', '')
    
    # 获取专题类型或分类
    topic_type = topic_data.get('type', '')
    category = topic_data.get('category', '')
    
    with st.expander(f"**{index}. {topic_id}** - {name_cn}", expanded=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if description:
                st.write(f"**描述**: {description}")
            if category:
                st.write(f"**分类**: {category}")
            if topic_type:
                st.write(f"**类型**: {topic_type}")
        
        with col2:
            # 显示专题的关键字段（如果有）
            if 'version' in topic_data:
                st.caption(f"版本: {topic_data.get('version')}")
            if 'created_at' in topic_data:
                st.caption(f"创建: {topic_data.get('created_at')}")


def render_subject_details(subject: dict):
    """渲染主体详细信息"""
    subject_name = subject.get('name', 'UNKNOWN')
    metadata = subject.get('metadata', {})
    topics = subject.get('topics', {})
    
    st.subheader(f"📋 主体详细信息: {subject_name}")
    
    # 元信息
    with st.expander("📊 主体元信息 (Metadata)", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**主体名称**: `{subject_name}`")
            st.write(f"**中文名称**: {metadata.get('name', 'N/A')}")
            st.write(f"**英文名称**: {metadata.get('name_en', 'N/A')}")
            if metadata.get('id'):
                st.write(f"**注册ID**: `{metadata.get('id')}`")
        with col2:
            st.write(f"**版本**: {metadata.get('version', 'N/A')}")
            if metadata.get('created_at'):
                st.write(f"**创建时间**: {metadata.get('created_at')}")
            if metadata.get('updated_at'):
                st.write(f"**更新时间**: {metadata.get('updated_at')}")
            if metadata.get('total_patterns') is not None:
                st.write(f"**专题总数**: {metadata.get('total_patterns')}")
    
    if metadata.get('description'):
        st.info(f"**描述**: {metadata.get('description')}")
    
    # 规格信息
    if metadata.get('specification'):
        with st.expander("📐 规格信息 (Specification)", expanded=False):
            spec = metadata.get('specification', {})
            st.json(spec)
    
    # 专题列表
    st.markdown("---")
    st.subheader(f"📚 专题列表 ({len(topics)} 个)")
    
    if topics:
        for index, (topic_id, topic_data) in enumerate(sorted(topics.items()), 1):
            render_topic_item(topic_id, topic_data, index)
    else:
        st.info("该主体下暂无专题")


def render():
    """渲染量子通用架构注册信息页面 (View Layer)"""
    apply_custom_header(
        "🏛️ 量子通用架构注册信息 (Quantum Framework Registry)",
        "显示量子通用架构下所有主体（Subjects）和专题（Topics）的注册信息"
    )
    
    # MVC: 初始化Controller
    if 'framework_registry_controller' not in st.session_state:
        st.session_state.framework_registry_controller = QuantumFrameworkRegistryController()
    
    controller = st.session_state.framework_registry_controller
    
    # 刷新按钮 + 版本信息
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.markdown("### 所有主体（Subjects）")
        st.caption(f"📌 **注册表规范版本**: {REGISTRY_SCHEMA_VERSION} (QGA-HR)")
    with col_header2:
        if st.button("🔄 刷新", help="重新加载主体和专题信息"):
            controller.clear_cache()
            st.rerun()
    
    st.caption("💡 正官格 (A-01) 等全息格局的注册信息在主体 **「全息格局」** 下，数据来自 `registry/holographic_pattern/`。")
    
    # 获取所有主体
    subjects = controller.get_all_subjects()
    
    if not subjects:
        st.warning("⚠️ 未找到任何主体。")
        st.info("💡 提示：主体目录应位于 `./core/subjects/`，每个主体目录下应包含 `registry.json` 文件。")
        return
    
    # 显示统计信息
    stats = controller.get_framework_statistics()
    st.success(f"✅ 找到 {stats['total_subjects']} 个主体，共 {stats['total_topics']} 个专题")
    
    # 统计卡片
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("总主体数", stats['total_subjects'])
    with col_stat2:
        st.metric("总专题数", stats['total_topics'])
    with col_stat3:
        st.metric("有专题的主体", stats['subjects_with_topics'])
    with col_stat4:
        avg_topics = stats['total_topics'] / stats['total_subjects'] if stats['total_subjects'] > 0 else 0
        st.metric("平均专题数", f"{avg_topics:.1f}")
    
    st.divider()
    
    # 选择器：按主体名称选择（优先显示“全息格局”）
    subject_names = [s.get('name', 'UNKNOWN') for s in subjects]
    # 将 holographic_pattern 排到第一位，便于找到正官格注册信息
    if 'holographic_pattern' in subject_names:
        subject_names = ['holographic_pattern'] + [n for n in subject_names if n != 'holographic_pattern']
    selected_subject_name = st.selectbox(
        "选择主体查看详细信息",
        options=subject_names,
        format_func=lambda x: _subject_display_name(x, subjects),
        key="selected_subject_name"
    )
    
    selected_subject = controller.get_subject_by_name(selected_subject_name)
    
    if selected_subject:
        # 显示详细卡片
        render_subject_card(selected_subject)
        
        # 显示详细信息
        render_subject_details(selected_subject)
    
    # 所有主体列表
    st.markdown("---")
    st.subheader("📚 所有主体列表")
    
    for subject in subjects:
        render_subject_card(subject)


if __name__ == "__main__":
    render()

