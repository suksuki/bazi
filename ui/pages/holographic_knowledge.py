#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全息知识中心页面 (HKB Center)
View Layer - 仅负责UI展示，所有业务逻辑通过Controller处理
"""

import streamlit as st
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from controllers.holographic_knowledge_controller import HolographicKnowledgeController
from ui.components.theme import apply_custom_header


def render_axis_metrics(axis_scores: dict):
    st.subheader("🧭 5D 物理图谱")
    if not axis_scores:
        st.info("暂无5D轴数据。")
        return
    cols = st.columns(len(axis_scores))
    for col, (axis, value) in zip(cols, axis_scores.items()):
        col.metric(axis, f"{value:.3f}")
    st.bar_chart(axis_scores)


def render_dominant_axes(dominant_axes: list):
    st.subheader("✨ 主导维度解析")
    if not dominant_axes:
        st.info("暂无主导维度信息。")
        return
    for item in dominant_axes:
        axis = item.get("axis")
        score = item.get("score")
        semantics = item.get("semantics", [])
        st.markdown(f"**{axis}** · {score:.3f}")
        if semantics:
            st.caption("、".join(semantics))


def render_classical_alignment(classical_alignment: dict):
    st.subheader("📜 古典对齐判词")
    description = classical_alignment.get("description")
    base_abundance = classical_alignment.get("base_abundance")
    if description:
        st.write(description)
    if base_abundance is not None:
        st.caption(f"基准丰度: {base_abundance:.4f}%")


def render_risk_notes(singularity_risk: dict):
    st.subheader("⚠️ 奇点风险提示")
    notes = singularity_risk.get("risk_notes", [])
    if not notes:
        st.info("暂无风险提示。")
        return
    for note in notes:
        st.warning(note)


def render_knowledge_entries(entries: list):
    st.subheader("🧬 子格局知识词条")
    if not entries:
        st.info("暂无可用词条，可能缺少子格局质心数据。")
        return
    
    for entry in entries:
        pattern_id = entry.get("pattern_id", "UNKNOWN")
        name = entry.get("name", pattern_id)
        description = entry.get("description", "")
        message = entry.get("message", "")
        axis_scores = entry.get("axis_scores", {})
        centroid_vector = entry.get("centroid_vector", [])
        
        with st.expander(f"**{pattern_id}** · {name}", expanded=True):
            # 优先显示description（基于模板生成的详细描述）
            if description:
                st.markdown(f"**物理特征描述：**")
                st.write(description)
            elif message:
                # 降级：显示message（基于rules的简单消息）
                st.markdown(f"**物理特征：**")
                st.write(message)
            
            # 显示轴评分
            if axis_scores:
                st.markdown("**5D轴评分：**")
                cols = st.columns(5)
                axes = ["E", "O", "M", "S", "R"]
                axis_names = ["能量", "秩序", "财富", "压力", "关系"]
                for i, (axis, axis_name) in enumerate(zip(axes, axis_names)):
                    with cols[i]:
                        score = axis_scores.get(axis, 0)
                        st.metric(axis_name, f"{score:.2f}")
            
            # 显示质心向量（技术细节）
            if centroid_vector:
                st.caption(f"质心向量: {[round(x, 4) for x in centroid_vector]}")


def render_system_message(message: str):
    st.subheader("🕯️ 系统寄语")
    if not message:
        st.info("暂无系统寄语。")
        return
    st.success(message)


def _load_matrix_evolution_result():
    """读取 Step 8 矩阵进化结果（若存在）。"""
    path = project_root / "sop_output" / "matrix_evolution_result.json"
    if not path.exists():
        return None
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def render():
    apply_custom_header(
        "🧠 全息知识中心",
        "物理发现到语义知识的自动转化中枢"
    )

    evolution = _load_matrix_evolution_result()
    if evolution:
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**［矩阵版本］** 当前参考：**{evolution.get('matrix_version', 'N/A')}** 真理校准矩阵")
        with c2:
            pct = evolution.get("improvement_pct")
            if pct is not None:
                st.success(f"**［解释力提升］** 系统精准度提升 **{pct}%**（相对 Step 8 审计基线）")
            else:
                st.caption("［解释力提升］ 暂无二次验证数据")

    controller = HolographicKnowledgeController()
    patterns = controller.list_available_patterns()

    if not patterns:
        st.warning("⚠️ 未找到任何知识库文件。")
        st.info("请先运行 `python3 fds_kb_generator.py --target A-01` 生成知识库。")
        return

    options = {
        p["pattern_id"]: f"{p['pattern_id']} · {p.get('chinese_name') or p.get('display_name') or ''}"
        for p in patterns
        if p.get("pattern_id")
    }
    selected_id = st.selectbox("选择格局", list(options.keys()), format_func=lambda k: options.get(k, k))

    knowledge = controller.load_knowledge(selected_id)
    if not knowledge:
        st.error("知识库读取失败，请检查文件是否存在或格式是否正确。")
        return

    render_axis_metrics(knowledge.get("physical_summary", {}).get("axis_scores", {}))
    render_dominant_axes(knowledge.get("physical_summary", {}).get("dominant_axes", []))
    render_classical_alignment(knowledge.get("classical_alignment", {}))
    render_risk_notes(knowledge.get("singularity_risk", {}))
    render_knowledge_entries(knowledge.get("knowledge_entries", []))
    render_system_message(knowledge.get("system_message", ""))
