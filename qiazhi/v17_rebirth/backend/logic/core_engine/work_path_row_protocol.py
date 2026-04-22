from __future__ import annotations

from typing import Any, Dict, Iterable, List

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import STEM_ELEMENT, ten_god_from_stems
from v17_rebirth.backend.logic.core_engine.work_evidence_protocol import WORK_EVIDENCE_KEY


RELATION_FAMILY_ALIASES: Dict[str, str] = {
    "san_hui": "sanhui",
    "sanhui": "sanhui",
    "san_he": "sanhe",
    "sanxing": "sanxing",
    "liu_he": "liuhe",
    "liu_po": "liu_po",
    "liupo": "liu_po",
    "liu_hai": "liu_hai",
    "liuhai": "liu_hai",
    "liu_chong": "liu_chong",
    "ban_he": "banhe",
    "banhe": "banhe",
    "banhe_shengwang": "banhe",
    "banhe_muwang": "banhe",
    "gong_he": "gonghe",
    "gonghe": "gonghe",
    "risk_blade_clash": "blade_clash",
    "risk_owl_food": "owl_food",
    "risk_officer_hurt_contest": "officer_hurt",
    "risk_officer_crush": "officer_hurt",
    "status_machine": "status_machine",
    "officer_hurt": "officer_hurt",
}

RELATION_DEFAULT_FAMILY = "dynamic_work"


def clamp_value(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return float(fallback)


def sign_from_effect(effect_type: str, impact_ratio: float) -> int:
    normalized = str(effect_type or "").strip().lower()
    if impact_ratio > 0:
        return 1
    if impact_ratio < 0:
        return -1
    if normalized in {"benefit", "release", "transform", "support", "bind"}:
        return 1
    if normalized in {"harm", "storage", "stuck", "disrupt", "clash"}:
        return -1
    return 0


def normalize_relation_family(raw_relation: str) -> str:
    normalized = str(raw_relation or "").strip().lower().replace("-", "_")
    normalized = normalized.replace("  ", " ").replace(" ", "_")
    if not normalized:
        return RELATION_DEFAULT_FAMILY
    if normalized in RELATION_FAMILY_ALIASES:
        return RELATION_FAMILY_ALIASES[normalized]
    if normalized.startswith("risk_"):
        stripped = normalized[5:]
        if stripped in RELATION_FAMILY_ALIASES:
            return RELATION_FAMILY_ALIASES[stripped]
    return normalized


def _legacy_members(impact: Dict[str, Any]) -> List[str]:
    work = impact.get(WORK_EVIDENCE_KEY) if isinstance(impact.get(WORK_EVIDENCE_KEY), dict) else {}
    members = work.get("members") if isinstance(work, dict) else None
    if isinstance(members, list):
        cleaned = [str(item).strip() for item in members if str(item).strip()]
        if cleaned:
            return cleaned
    pair = impact.get("clash_pair")
    if isinstance(pair, list):
        cleaned = [str(item).strip() for item in pair if str(item).strip()]
        if cleaned:
            return cleaned
    return []


def normalize_work_path_row(row: Dict[str, Any]) -> Dict[str, Any]:
    impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
    work = impact.get(WORK_EVIDENCE_KEY) if isinstance(impact.get(WORK_EVIDENCE_KEY), dict) else {}
    target = str(row.get("target_god") or impact.get("target_god") or work.get("target_god") or "").strip()
    relation_family_raw = str(
        work.get("relation_family")
        or impact.get("relation_family")
        or row.get("source")
        or row.get("plugin_id")
        or "unknown"
    ).strip()
    relation_family = normalize_relation_family(relation_family_raw)
    impact_ratio = safe_float(work.get("impact_ratio", impact.get("impact_ratio", 0.0)))
    match_ratio = clamp_value(safe_float(work.get("match_ratio", impact.get("match_ratio", 0.0))), 0.0, 1.0)
    condition_state = str(work.get("condition_state") or impact.get("condition_state") or "").strip()
    layer = str(work.get("layer") or impact.get("interaction_layer") or "unknown").strip()
    origin_scope = str(work.get("origin_scope") or impact.get("origin_type") or "natal").strip()
    effect_type = str(work.get("effect_type") or "").strip()
    significance = safe_float(impact.get("significance_weight", 1.0), 1.0)
    decision_id = str(row.get("id") or "").strip()
    plugin_id = str(row.get("plugin_id") or row.get("source") or relation_family).strip()
    source_label = str(
        row.get("source_label")
        or row.get("display_name")
        or row.get("definition_text")
        or row.get("title")
        or row.get("label")
        or plugin_id
        or relation_family
    ).strip()
    decision_label = str(
        row.get("label")
        or row.get("title")
        or row.get("summary")
        or row.get("reason")
        or source_label
    ).strip()
    path_strength = safe_float(
        work.get("path_strength"),
        abs(impact_ratio) * max(0.45, match_ratio) * max(0.75, significance),
    )
    return {
        "row_id": decision_id,
        "decision_id": decision_id,
        "plugin_id": plugin_id,
        "source_label": source_label,
        "decision_label": decision_label,
        "target_god": target,
        "relation_family_raw": relation_family_raw,
        "relation_family": relation_family,
        "effect_type": effect_type,
        "members": _legacy_members(impact),
        "actor_members": [
            str(item).strip()
            for item in (
                work.get("actor_members")
                if isinstance(work.get("actor_members"), list)
                else impact.get("actor_members")
                if isinstance(impact.get("actor_members"), list)
                else row.get("actor_members")
                if isinstance(row.get("actor_members"), list)
                else []
            )
            if str(item).strip()
        ],
        "receiver_members": [
            str(item).strip()
            for item in (
                work.get("receiver_members")
                if isinstance(work.get("receiver_members"), list)
                else impact.get("receiver_members")
                if isinstance(impact.get("receiver_members"), list)
                else row.get("receiver_members")
                if isinstance(row.get("receiver_members"), list)
                else []
            )
            if str(item).strip()
        ],
        "origin_scope": origin_scope,
        "layer": layer,
        "condition_state": condition_state,
        "impact_ratio": impact_ratio,
        "match_ratio": match_ratio,
        "path_strength": max(0.0, path_strength),
        "significance_weight": significance,
        "actor_gods": [
            str(item).strip()
            for item in (
                work.get("actor_gods")
                if isinstance(work.get("actor_gods"), list)
                else impact.get("actor_gods")
                if isinstance(impact.get("actor_gods"), list)
                else row.get("actor_gods")
                if isinstance(row.get("actor_gods"), list)
                else []
            )
            if str(item).strip()
        ],
        "receiver_gods": [
            str(item).strip()
            for item in (
                work.get("receiver_gods")
                if isinstance(work.get("receiver_gods"), list)
                else impact.get("receiver_gods")
                if isinstance(impact.get("receiver_gods"), list)
                else row.get("receiver_gods")
                if isinstance(row.get("receiver_gods"), list)
                else []
            )
            if str(item).strip()
        ],
        "source": str(row.get("source") or row.get("plugin_id") or relation_family).strip(),
        "work": dict(work) if isinstance(work, dict) else {},
        "impact": dict(impact) if isinstance(impact, dict) else {},
    }


def extract_counterpart_gods(
    *,
    row: Dict[str, Any],
    work: Dict[str, Any],
    impact: Dict[str, Any],
    relation_family: str,
    target_god: str,
    day_master: str,
) -> List[str]:
    candidates: list[str] = []
    raw_sources = [
        row.get("counterpart_gods"),
        row.get("interaction_gods"),
        row.get("interaction_pair"),
        work.get("counterpart_gods"),
        work.get("interaction_gods"),
        work.get("interaction_pair"),
        work.get("interplay"),
        impact.get("counterpart_gods"),
        impact.get("interaction_gods"),
    ]
    for raw in raw_sources:
        if isinstance(raw, list):
            candidates.extend([str(item).strip() for item in raw if str(item).strip()])
        elif isinstance(raw, str):
            candidates.append(raw.strip())

    members = row.get("members") if isinstance(row.get("members"), list) else work.get("members")
    if isinstance(members, list):
        for member in members:
            name = str(member).strip()
            if len(name) == 1 and STEM_ELEMENT.get(name):
                try:
                    candidates.append(ten_god_from_stems(day_master, name))
                except Exception:
                    continue

    normalized_family = str(relation_family or "").lower().strip()
    if normalized_family.startswith("risk_officer") and target_god in {"正官", "七杀"}:
        candidates.append("伤官")
    if normalized_family.startswith("risk_officer") and target_god == "伤官":
        candidates.append("正官")

    out: list[str] = []
    for candidate in candidates:
        name = str(candidate or "").strip()
        if not name or name == target_god:
            continue
        if name not in out:
            out.append(name)
    return out


def collect_effect_maps(decision_rows: Iterable[Dict[str, object]]) -> tuple[Dict[str, float], Dict[str, float]]:
    positive: Dict[str, float] = {}
    negative: Dict[str, float] = {}
    for row in decision_rows:
        normalized = normalize_work_path_row(dict(row))
        god = str(normalized.get("target_god") or "").strip()
        if not god:
            continue
        ratio = safe_float(normalized.get("impact_ratio"), 0.0)
        path_strength = safe_float(normalized.get("path_strength"), abs(ratio))
        sign = sign_from_effect(str(normalized.get("effect_type") or ""), ratio)
        if sign > 0:
            positive[god] = positive.get(god, 0.0) + max(path_strength, ratio, 0.0)
        elif sign < 0:
            negative[god] = negative.get(god, 0.0) + max(path_strength, abs(ratio))
    return positive, negative


__all__ = [
    "RELATION_DEFAULT_FAMILY",
    "clamp_value",
    "collect_effect_maps",
    "extract_counterpart_gods",
    "normalize_relation_family",
    "normalize_work_path_row",
    "safe_float",
    "sign_from_effect",
]
