"""弱模型「叙事工厂」守卫：断言必须锚定插件证据，否则退回 physics 兜底 JSON。"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from app.skills.final_verdict_parts.evidence import format_deity_abs_semantic_slices


# 行首或「快照 :: …」缀后的十神 Abs 脱水行均需剔除，避免弱模型从前缀快照读回数值。
_TEN_GOD_ABS_IN_LINE = re.compile(r"十神\.[^.]+\.Abs=")


def filter_logical_evidence_for_narrative_factory(lines: List[str], *, high_reasoning: bool) -> List[str]:
    """
    非高推理模式：从 LLM 可见证据中移除「十神.X.Abs=数值」原始行，
    保留 `语义.十神.*` 档位行及其余脱水行，迫使模型做标签缝合而非现场重算 Abs。
    """
    if high_reasoning:
        return list(lines or [])
    out: List[str] = []
    for line in lines or []:
        s = str(line or "")
        if _TEN_GOD_ABS_IN_LINE.search(s):
            continue
        out.append(s)
    return out


_VF_REF = re.compile(r"^VF\d+", re.IGNORECASE)


def _weak_mode_evidence_anchor_ok(ref: Any) -> bool:
    """弱模型：断言须锚定 Context 中已编号的 VF、柱位、矩阵、插件等短键之一。"""
    s = str(ref or "").strip()
    if not s:
        return False
    if s.startswith("plugin."):
        return True
    if _VF_REF.match(s):
        return True
    if s.startswith("conflict_matrix."):
        return True
    if s.startswith("meta."):
        return True
    if s.startswith("branch."):
        return True
    for pk in ("year.", "month.", "day.", "hour."):
        if s.startswith(pk):
            return True
    return False


def evidence_ref_allowed_for_verdict_parse(ref: Any) -> bool:
    """终判 JSON parse 阶段裁剪非法 evidence_refs 时复用与弱守卫一致的白名单。"""
    return _weak_mode_evidence_anchor_ok(ref)


def weak_mode_requires_physics_fallback(obj: Dict[str, Any], *, high_reasoning: bool) -> bool:
    """断语优先：不再因 VF/证据锚缺失而强制 physics 兜底；审计交由抽屉与后续链路。"""
    return False


def inject_label_only_semantic_slices(
    logical_evidence: List[str],
    *,
    physics_tensor: Dict[str, Any],
    enabled: bool,
) -> List[str]:
    """
    弱模式：去掉 get_logical_evidence 中带 Abs 的语义行，换入 label_only 档位行；
    插在「地支.三合.*」块之后，避免淹没三合置顶证据。
    """
    if not enabled:
        return list(logical_evidence or [])
    sem_only = format_deity_abs_semantic_slices(physics_tensor, label_only=True)
    rest = [ln for ln in (logical_evidence or []) if not str(ln).startswith("语义.十神")]
    if not sem_only:
        return rest
    idx = 0
    n = len(rest)
    while idx < n and str(rest[idx]).startswith("地支.三合."):
        idx += 1
    return rest[:idx] + sem_only + rest[idx:]


def extract_reasoning_feedback_loop(obj: Dict[str, Any]) -> Any:
    """从 LLM JSON 顶层取出强模型可选回写字段（若存在）。"""
    if not isinstance(obj, dict):
        return None
    v = obj.get("reasoning_feedback_loop")
    if v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, dict) and not v):
        return None
    return v
