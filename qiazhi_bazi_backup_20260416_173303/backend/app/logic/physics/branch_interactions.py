"""由 ``metadata.conflict_matrix`` 生成 ``physics_tensor.branch_interactions`` 供冲突法典消费。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping

_BRANCH_CHARS = "子丑寅卯辰巳午未申酉戌亥"
# 典型「子午冲」「寅申冲」等：两支 + 冲
_RE_TWO_BRANCH_CLASH = re.compile(rf"^([{_BRANCH_CHARS}])([{_BRANCH_CHARS}])冲")


def build_branch_interactions(metadata: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """扫描冲突矩阵，输出标准化互动行（pair 可为空，如法典未识别的文案）。"""
    out: List[Dict[str, Any]] = []
    cm = metadata.get("conflict_matrix")
    if not isinstance(cm, dict):
        return out
    pts = cm.get("points")
    if not isinstance(pts, list):
        return out
    for p in pts:
        if not isinstance(p, dict):
            continue
        kind = str(p.get("kind") or "clash").strip().upper() or "CLASH"
        detail = str(p.get("detail") or "").strip()
        pair: List[str] = []
        m = _RE_TWO_BRANCH_CLASH.match(detail)
        if m:
            pair = [m.group(1), m.group(2)]
        out.append(
            {
                "type": kind,
                "pair": pair,
                "detail": detail,
                "positions": p.get("positions"),
            }
        )
    return out
