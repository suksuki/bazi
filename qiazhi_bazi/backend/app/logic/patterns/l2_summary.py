"""L2 法典行摘要：与 pattern_detector_v2 / 终判结构口径共用。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def sanitize_pattern_headline_zh(raw: Optional[str]) -> str:
    """V9.1：禁止「平常局」口径；空命中与禁用文案统一为「常规格」。"""
    t = str(raw or "").strip()
    if not t:
        return "常规格"
    if t == "平常局" or t.startswith("平常局"):
        return "常规格"
    return t


def affinity_for_pattern_row(r: Dict[str, Any]) -> float:
    a = r.get("affinity_score")
    if isinstance(a, (int, float)) and not isinstance(a, bool):
        return float(a)
    p = r.get("progress")
    if isinstance(p, (int, float)) and not isinstance(p, bool):
        return float(p)
    return 0.0


def pattern_display_name_zh(name: str, pattern_id: str) -> str:
    """法典 ``display_name`` 已为「正官格」等；无则补「格」后缀。"""
    n = (name or "").strip()
    if n:
        if n.endswith("格"):
            return n
        return f"{n}格"
    p = (pattern_id or "").strip()
    return p if p else "常规格"


def l2_result_summary_zh(rows: List[Dict[str, Any]]) -> str:
    """顶栏 / 终判对齐：「正官格 (亲和度 100.0%)」。"""
    if not rows:
        return ""
    top = max(rows, key=affinity_for_pattern_row)
    name_raw = str(top.get("name") or "").strip()
    pid = str(top.get("pattern_id") or "").strip()
    display = pattern_display_name_zh(name_raw, pid)
    raw = affinity_for_pattern_row(top)
    pct = raw * 100.0 if raw <= 1.501 else raw
    pct_r = round(float(pct) * 10) / 10.0
    return sanitize_pattern_headline_zh(f"{display} (亲和度 {pct_r:.1f}%)")
