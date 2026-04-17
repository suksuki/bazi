"""
V6.3：因果推荐理由的人性化合成（非纯模板），基于格局 Progress / Stability 对比。
"""
from __future__ import annotations

from typing import Any, Mapping


def _pct_from_component(comp: Any, weight: float) -> str:
    try:
        c = float(comp)
        w = float(weight)
    except (TypeError, ValueError):
        return ""
    if w <= 1e-9:
        return ""
    # components 为 [0,1] 归一化子项，粗映射为「等效百分点」便于 UI 加粗
    approx = max(0.0, min(99.0, c * w * 100.0))
    if approx < 0.5:
        return ""
    return f"{approx:.0f}%"


class CausalReasoningSynthesizer:
    """将因果子分与业务短语合成为一条可读推荐句。"""

    @staticmethod
    def synthesize(
        *,
        action_phrase: str,
        score_detail: Mapping[str, Any],
        pattern_label_before: str = "",
        pattern_label_after: str = "",
    ) -> str:
        raw = score_detail.get("raw") if isinstance(score_detail.get("raw"), dict) else {}
        nb = str(pattern_label_before or raw.get("follower_name_before") or "").strip() or "常规格"
        na = str(pattern_label_after or raw.get("follower_name_after") or "").strip() or nb
        comps = score_detail.get("components") if isinstance(score_detail.get("components"), dict) else {}
        weights = score_detail.get("weights") if isinstance(score_detail.get("weights"), dict) else {}
        pb = comps.get("pattern_boost")
        sg = comps.get("stability_gain")
        wp = weights.get("pattern", 0.4)
        ws = weights.get("stability", 0.3)
        p_pct = _pct_from_component(pb, wp)
        s_pct = _pct_from_component(sg, ws)
        tail_parts: list[str] = []
        if p_pct:
            tail_parts.append(f"格局达成度等效提升约 {p_pct}")
        if s_pct:
            tail_parts.append(f"稳定性等效增益约 {s_pct}")
        tail = "；".join(tail_parts) if tail_parts else "格局张力与稳定性出现可感知位移。"
        phrase = str(action_phrase or "此项意志").strip()
        return (
            f"裁决者，{phrase}可将格局从「{nb}」推向「{na}」临界；{tail}"
        ).strip()


def synthesize_recommendation_reason(
    *,
    action_phrase: str,
    score_detail: Mapping[str, Any],
    tensor_before: Mapping[str, Any],
    tensor_after: Mapping[str, Any],
) -> str:
    """便捷函数：优先用因果子分中的从格主名，其次用 meta.pattern_profile。"""
    def _pn_zh(t: Mapping[str, Any]) -> str:
        meta = t.get("meta") if isinstance(t.get("meta"), dict) else {}
        pp = meta.get("pattern_profile") if isinstance(meta.get("pattern_profile"), dict) else {}
        return str(pp.get("pattern_name_zh") or "").strip()

    raw = score_detail.get("raw") if isinstance(score_detail.get("raw"), dict) else {}
    nb = str(raw.get("follower_name_before") or "").strip() or _pn_zh(tensor_before) or "常规格"
    na = str(raw.get("follower_name_after") or "").strip() or _pn_zh(tensor_after) or nb
    return CausalReasoningSynthesizer.synthesize(
        action_phrase=action_phrase,
        score_detail=score_detail,
        pattern_label_before=nb,
        pattern_label_after=na,
    )
