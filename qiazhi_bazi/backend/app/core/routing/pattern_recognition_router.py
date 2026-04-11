"""格局识别：从格/化格（简化能量集中度）→ meta.pattern_profile，供路由/UI/断言关键词。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping

from app.skills.physics_rules import STEM_TO_ELEMENT, deity_element_map

_ELEMENT_ZH = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}


def _dominant_element(norm: Mapping[str, Any]) -> tuple[str, float]:
    best = "earth"
    best_v = 0.0
    total = 0.0
    for k in ("wood", "fire", "earth", "metal", "water"):
        try:
            v = float(norm.get(k, 0.0) or 0.0)
        except (TypeError, ValueError):
            v = 0.0
        total += v
        if v > best_v:
            best_v = v
            best = k
    ratio = (best_v / total) if total > 1e-9 else 0.0
    return best, ratio


def _cong_favorable_deities(self_el: str, dom_el: str) -> List[str]:
    """从格顺势：dominant 元素与日主十神管道对齐的轴视为喜用反转候选。"""
    if self_el == dom_el:
        return []
    m = deity_element_map(self_el)
    out: List[str] = []
    if m.get("食伤") == dom_el:
        out.extend(["食神", "伤官"])
    if m.get("财星") == dom_el:
        out.extend(["正财", "偏财"])
    if m.get("官杀") == dom_el:
        out.extend(["正官", "七杀"])
    if m.get("印星") == dom_el:
        out.extend(["正印", "偏印"])
    if not out:
        out = ["食神", "伤官", "正财", "偏财", "正官", "七杀"]
    return sorted(set(out))


def evaluate_pattern_profile(
    *,
    physics_tensor: MutableMapping[str, Any],
    metadata: Mapping[str, Any],
    settings: Mapping[str, float],
) -> Dict[str, Any]:
    """写入 meta.pattern_profile；从格阈值来自 PATTERN_CONG_DOMINANCE。"""
    meta = physics_tensor.setdefault("meta", {})
    if not isinstance(meta, dict):
        return {"pattern_kind": "none"}

    norm = physics_tensor.get("normalized")
    if not isinstance(norm, dict):
        profile: Dict[str, Any] = {"pattern_kind": "none", "pattern_name_zh": "平常局", "sovereignty_priority": False}
        meta["pattern_profile"] = profile
        return profile

    thr = max(0.35, min(0.92, float(settings.get("PATTERN_CONG_DOMINANCE", 0.52))))
    dom_el, ratio = _dominant_element(norm)
    pillars = metadata.get("pillars") if isinstance(metadata, dict) else None
    day_stem = ""
    if isinstance(pillars, dict):
        day = pillars.get("day")
        if isinstance(day, dict) and day.get("stem"):
            day_stem = str(day["stem"])
    self_el = STEM_TO_ELEMENT.get(day_stem, "earth")

    interaction_v2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    hua_hint = bool(interaction_v2.get("attribute_collapse")) and ratio >= (thr - 0.06)

    profile: Dict[str, Any] = {
        "pattern_kind": "none",
        "pattern_name_zh": "平常局",
        "dominant_element": dom_el,
        "dominance_ratio": round(ratio, 4),
        "sovereignty_priority": False,
        "suppress_l1_interaction_ids": [],
        "xi_ji_reversal_lines": [],
        "assertion_keywords": [],
    }

    if ratio >= thr and self_el != dom_el:
        zh = _ELEMENT_ZH.get(dom_el, dom_el)
        profile["pattern_kind"] = f"cong_{dom_el}"
        profile["pattern_name_zh"] = f"从{zh}格（能量集中度）"
        profile["sovereignty_priority"] = True
        profile["suppress_l1_interaction_ids"] = ["SHANG_GUAN_JIAN_GUAN", "XIAO_SHEN_DUO_SHI"]
        profile["eta_flip_gain"] = max(1.0, min(2.0, float(settings.get("PATTERN_ETA_FLIP_GAIN", 1.12))))
        fav = _cong_favorable_deities(self_el, dom_el)
        profile["favorable_deities"] = fav
        profile["xi_ji_reversal_lines"] = [
            f"格局主权：局中「{zh}」气占 {round(ratio * 100, 1)}%，从势而论，财官食伤之克泄在此上下文中可转为顺势增益（非身旺抗克逻辑）。",
            "喜忌反转：忌强行扶印比抗局；喜顺从 dominant 管道。",
        ]
        profile["assertion_keywords"] = ["格局主权", "从格顺势", "喜忌反转"]
    elif hua_hint:
        profile["pattern_kind"] = "hua_candidate"
        profile["pattern_name_zh"] = "化格候选（合局坍缩 + 能量集中）"
        profile["assertion_keywords"] = ["合化倾向", "格局主权"]

    meta["pattern_profile"] = profile
    return profile
