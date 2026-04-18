from __future__ import annotations

from typing import Any, Dict

from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god

_TEN_GODS = (
    "比肩",
    "劫财",
    "食神",
    "伤官",
    "正财",
    "偏财",
    "正官",
    "七杀",
    "正印",
    "偏印",
)

_BRANCHES = tuple("子丑寅卯辰巳午未申酉戌亥")


def infer_target_god_from_text(*texts: Any) -> str:
    for raw in texts:
        text = str(raw or "").strip()
        if not text:
            continue
        for god in _TEN_GODS:
            if god in text:
                return god
    return ""


def _day_master_from_physics(physics_tensor: Dict[str, Any] | None) -> str:
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    day_master = str(pt.get("day_master_stem") or "").strip()
    if day_master:
        return day_master
    four_pillars = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), dict) else {}
    day_gz = str(four_pillars.get("day", "")).strip()
    if len(day_gz) >= 2:
        return day_gz[0]
    return ""


def _infer_from_branch_mentions(*, text: str, physics_tensor: Dict[str, Any] | None) -> str:
    day_master = _day_master_from_physics(physics_tensor)
    if not day_master:
        return ""
    for ch in str(text or ""):
        if ch not in _BRANCHES:
            continue
        god = _branch_dominant_ten_god(ch, day_master)
        if god:
            return god
    return ""


def resolve_target_god(
    *,
    row_target: Any = "",
    impact: Dict[str, Any] | None = None,
    meta: Dict[str, Any] | None = None,
    title: Any = "",
    label: Any = "",
    plugin_id: Any = "",
    physics_tensor: Dict[str, Any] | None = None,
) -> str:
    impact = impact if isinstance(impact, dict) else {}
    meta = meta if isinstance(meta, dict) else {}
    explicit = str(
        row_target
        or impact.get("target_god")
        or meta.get("target_god")
        or ""
    ).strip()
    if explicit:
        return explicit

    text_hit = infer_target_god_from_text(title, label)
    if text_hit:
        return text_hit

    branch_hit = _infer_from_branch_mentions(
        text=" ".join(
            x for x in [str(plugin_id or ""), str(title or ""), str(label or ""), str(meta.get("fact") or "")]
            if x
        ),
        physics_tensor=physics_tensor,
    )
    if branch_hit:
        return branch_hit
    return ""
