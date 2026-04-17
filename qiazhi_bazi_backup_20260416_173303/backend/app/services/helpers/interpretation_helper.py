"""展示层语义辅助：神煞等标签仅在断言/LLM 前注入 metadata，不参与物理张量计算。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping

# 与 legacy symbolic_stars 表一致；仅产出标签，不写入能量修正。
_TIAN_YI_MAP: Dict[str, List[str]] = {
    "甲": ["丑", "未"],
    "戊": ["丑", "未"],
    "庚": ["丑", "未"],
    "乙": ["子", "申"],
    "己": ["子", "申"],
    "丙": ["亥", "酉"],
    "丁": ["亥", "酉"],
    "壬": ["卯", "巳"],
    "癸": ["卯", "巳"],
    "辛": ["午", "寅"],
}

_WEN_CHANG_MAP: Dict[str, str] = {
    "甲": "巳",
    "乙": "午",
    "丙": "申",
    "丁": "酉",
    "戊": "申",
    "己": "酉",
    "庚": "亥",
    "辛": "子",
    "壬": "寅",
    "癸": "卯",
}

_PEACH_BLOSSOM_MAP: Dict[str, str] = {
    "寅": "卯",
    "午": "卯",
    "戌": "卯",
    "申": "酉",
    "子": "酉",
    "辰": "酉",
    "巳": "午",
    "酉": "午",
    "丑": "午",
    "亥": "子",
    "卯": "子",
    "未": "子",
}

_POST_HORSE_MAP: Dict[str, str] = {
    "寅": "申",
    "午": "申",
    "戌": "申",
    "申": "寅",
    "子": "寅",
    "辰": "寅",
    "巳": "亥",
    "酉": "亥",
    "丑": "亥",
    "亥": "巳",
    "卯": "巳",
    "未": "巳",
}


def _pillars_branches(pillars: Mapping[str, Any]) -> List[str]:
    out: List[str] = []
    for key in ("year", "month", "day", "hour"):
        col = pillars.get(key)
        if isinstance(col, dict) and col.get("branch"):
            out.append(str(col["branch"]))
    return out


def build_shensha_tag_metadata(metadata: Mapping[str, Any] | None) -> Dict[str, Any]:
    """
    从四柱提取常见神煞命中（标签级），供 LLM 断言上下文使用。
    不在 physics_engine / interaction_pipeline 中修改能量。
    """
    if not isinstance(metadata, dict):
        return {"active_tags": [], "tags_by_pillar": {}}
    pillars = metadata.get("pillars")
    if not isinstance(pillars, dict):
        return {"active_tags": [], "tags_by_pillar": {}}
    day = pillars.get("day")
    if not isinstance(day, dict):
        return {"active_tags": [], "tags_by_pillar": {}}
    day_stem = str(day.get("stem") or "")
    branches = _pillars_branches(pillars)
    year_branch = str((pillars.get("year") or {}).get("branch") or "") if isinstance(pillars.get("year"), dict) else ""
    day_branch = str(day.get("branch") or "")
    tags: List[Dict[str, Any]] = []

    for b in branches:
        if b in (_TIAN_YI_MAP.get(day_stem) or []):
            tags.append({"name": "天乙贵人", "kind": "shensha", "branch": b})
        if b == _WEN_CHANG_MAP.get(day_stem):
            tags.append({"name": "文昌贵人", "kind": "shensha", "branch": b})
        pb = _PEACH_BLOSSOM_MAP.get(year_branch) or _PEACH_BLOSSOM_MAP.get(day_branch)
        if pb and b == pb:
            tags.append({"name": "桃花", "kind": "shensha", "branch": b})
        ph = _POST_HORSE_MAP.get(year_branch) or _POST_HORSE_MAP.get(day_branch)
        if ph and b == ph:
            tags.append({"name": "驿马", "kind": "shensha", "branch": b})

    dedup: Dict[str, Dict[str, Any]] = {}
    for t in tags:
        key = f"{t.get('name')}|{t.get('branch')}"
        dedup[key] = t
    active = list(dedup.values())
    return {
        "version": "shensha_tags.v1",
        "day_stem": day_stem,
        "active_tags": active,
        "note": "标签仅供叙事与 LLM 参考，未参与物理能量计算。",
    }


def merge_interpretation_metadata_for_llm(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """在终判/审计前合并展示层 metadata（浅拷贝根对象）。"""
    out = dict(metadata)
    shen = build_shensha_tag_metadata(out)
    interp = dict(out.get("interpretation") or {}) if isinstance(out.get("interpretation"), dict) else {}
    interp["shensha"] = shen
    out["interpretation"] = interp
    return out
