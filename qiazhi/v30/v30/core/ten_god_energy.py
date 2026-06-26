from __future__ import annotations

from typing import Any

from v30.contracts import ChartContext, TenGodEnergyModel, TenGodEnergyScore
from v30.core.constants import HIDDEN_STEMS
from v30.core.pillars import parse_pillar
from v30.core.ten_gods import ten_god


TEN_GOD_ENERGY_MODEL_VERSION = "v30.ten_god_energy_model.v1"
TEN_GOD_FAMILY = {
    "比肩": "self",
    "劫财": "self",
    "食神": "output",
    "伤官": "output",
    "正财": "wealth",
    "偏财": "wealth",
    "正官": "authority",
    "七杀": "authority",
    "正印": "resource",
    "偏印": "resource",
}
NATAL_STEM_WEIGHTS = {"year": 0.75, "month": 1.25, "day": 0.0, "hour": 0.82}
NATAL_BRANCH_WEIGHTS = {"year": 0.55, "month": 1.45, "day": 1.0, "hour": 0.72}
TIME_STEM_WEIGHTS = {"luck": 0.92, "flow_year": 0.74, "flow_month": 0.42}
TIME_BRANCH_WEIGHTS = {"luck": 0.74, "flow_year": 0.58, "flow_month": 0.3}
TIME_VOLATILITY = {"luck": 0.14, "flow_year": 0.24, "flow_month": 0.32}
BRANCH_CONFLICT_RELATIONS = {"clash", "harm", "break", "punishment"}
BRANCH_ALIGNMENT_RELATIONS = {"harmony", "three_harmony", "three_meeting"}


def build_ten_god_energy_model(context: ChartContext) -> TenGodEnergyModel:
    contributions: dict[str, list[dict[str, Any]]] = {}
    _collect_natal_contributions(context, contributions)
    _collect_time_layer_contributions(context, contributions)
    relation_modifiers = _relation_modifiers(context)
    max_weight = max((sum(float(row["weight"]) for row in rows) for rows in contributions.values()), default=0.0)
    scores: dict[str, TenGodEnergyScore] = {}
    for label, rows in sorted(contributions.items()):
        if not label:
            continue
        raw_weight = round(sum(float(row["weight"]) for row in rows), 3)
        source_keys = [str(row["source"]) for row in rows]
        source_set = set(source_keys)
        energy = _bounded(raw_weight / max(max_weight, 1.0))
        stability = _stability(source_set, relation_modifiers)
        volatility = _volatility(source_set, relation_modifiers)
        confidence = _confidence(source_set, raw_weight, relation_modifiers)
        scores[label] = TenGodEnergyScore(
            label=label,
            family=TEN_GOD_FAMILY.get(label, "unknown"),
            energy=energy,
            stability=stability,
            volatility=volatility,
            confidence=confidence,
            raw_weight=raw_weight,
            sources=sorted(source_set),
            modifiers=relation_modifiers,
            evidence_ids=[f"{context.context_id}:ten_god_energy:{label}"],
        )
    dominant = [label for label, score in scores.items() if score.energy >= 0.64]
    high_volatility = [label for label, score in scores.items() if score.volatility >= 0.62]
    low_stability = [label for label, score in scores.items() if score.stability <= 0.38]
    return TenGodEnergyModel(
        status="ready" if scores else "pending",
        context_id=context.context_id,
        target_year=_target_year(context),
        day_master=context.day_master,
        day_master_element=context.day_master_element,
        scores=scores,
        dominant_ten_gods=sorted(dominant),
        high_volatility_ten_gods=sorted(high_volatility),
        low_stability_ten_gods=sorted(low_stability),
        interaction_matrix=_interaction_matrix(scores),
        trace={
            "version": TEN_GOD_ENERGY_MODEL_VERSION,
            "natal_source_count": sum(len(rows) for rows in contributions.values()),
            "relation_modifiers": relation_modifiers,
            "boundary": "energy_trace_explains_model_signal_not_chart_fact",
        },
    )


def _collect_natal_contributions(context: ChartContext, contributions: dict[str, list[dict[str, Any]]]) -> None:
    pillars = context.natal_pillars.get("pillars", {})
    if not isinstance(pillars, dict):
        return
    for position, payload in pillars.items():
        if not isinstance(payload, dict):
            continue
        stem = str(payload.get("stem") or "")
        branch = str(payload.get("branch") or "")
        if position != "day" and stem:
            _add(
                context,
                contributions,
                stem=stem,
                weight=NATAL_STEM_WEIGHTS.get(str(position), 0.65),
                source=f"natal_{position}_stem",
            )
        for hidden_stem, hidden_weight in HIDDEN_STEMS.get(branch, ()):
            _add(
                context,
                contributions,
                stem=hidden_stem,
                weight=NATAL_BRANCH_WEIGHTS.get(str(position), 0.55) * float(hidden_weight),
                source=f"natal_{position}_hidden",
            )


def _collect_time_layer_contributions(context: ChartContext, contributions: dict[str, list[dict[str, Any]]]) -> None:
    layers = context.time_layers.get("layers", [])
    if not isinstance(layers, list):
        return
    for row in layers:
        if not isinstance(row, dict):
            continue
        layer_key = str(row.get("layer_key") or "")
        pillar_payload = row.get("pillar")
        try:
            if isinstance(pillar_payload, dict):
                display = f"{pillar_payload.get('stem', '')}{pillar_payload.get('branch', '')}"
            else:
                display = str(pillar_payload or "")
            pillar = parse_pillar(display, layer_key)
        except ValueError:
            continue
        _add(
            context,
            contributions,
            stem=pillar.stem,
            weight=TIME_STEM_WEIGHTS.get(layer_key, 0.3),
            source=f"{layer_key}_stem",
        )
        for hidden_stem, hidden_weight in HIDDEN_STEMS.get(pillar.branch, ()):
            _add(
                context,
                contributions,
                stem=hidden_stem,
                weight=TIME_BRANCH_WEIGHTS.get(layer_key, 0.25) * float(hidden_weight),
                source=f"{layer_key}_hidden",
            )


def _add(
    context: ChartContext,
    contributions: dict[str, list[dict[str, Any]]],
    *,
    stem: str,
    weight: float,
    source: str,
) -> None:
    label = ten_god(context.day_master, stem)
    if not label:
        return
    contributions.setdefault(label, []).append({"stem": stem, "weight": round(weight, 4), "source": source})


def _relation_modifiers(context: ChartContext) -> list[str]:
    relations = context.natal_pillars.get("relation_hits", [])
    if not isinstance(relations, list):
        return []
    relation_types = {str(row.get("relation_type") or "") for row in relations if isinstance(row, dict)}
    modifiers: list[str] = []
    if relation_types & BRANCH_CONFLICT_RELATIONS:
        modifiers.append("branch_conflict_reduces_stability")
    if relation_types & BRANCH_ALIGNMENT_RELATIONS:
        modifiers.append("branch_alignment_increases_stability")
    return sorted(modifiers)


def _stability(sources: set[str], modifiers: list[str]) -> float:
    score = 0.24
    if any(source.startswith("natal_month") for source in sources):
        score += 0.18
    if any(source.startswith("natal_day_hidden") for source in sources):
        score += 0.14
    if len({source.split("_", 2)[0] + "_" + source.split("_", 2)[1] for source in sources if "_" in source}) >= 3:
        score += 0.18
    if any(source.startswith("luck") for source in sources):
        score += 0.08
    if any(source.startswith("flow_year") for source in sources):
        score -= 0.08
    if "branch_conflict_reduces_stability" in modifiers:
        score -= 0.12
    if "branch_alignment_increases_stability" in modifiers:
        score += 0.08
    return _bounded(score)


def _volatility(sources: set[str], modifiers: list[str]) -> float:
    score = 0.24
    for prefix, value in TIME_VOLATILITY.items():
        if any(source.startswith(prefix) for source in sources):
            score += value
    if "branch_conflict_reduces_stability" in modifiers:
        score += 0.16
    if "branch_alignment_increases_stability" in modifiers:
        score -= 0.06
    if not any(source.startswith("natal") for source in sources):
        score += 0.12
    return _bounded(score)


def _confidence(sources: set[str], raw_weight: float, modifiers: list[str]) -> float:
    score = 0.36 + min(0.26, raw_weight * 0.08) + min(0.24, len(sources) * 0.04)
    if any(source.startswith("natal") for source in sources) and any(source.startswith("luck") for source in sources):
        score += 0.06
    if modifiers:
        score += 0.04
    return _bounded(score)


def _interaction_matrix(scores: dict[str, TenGodEnergyScore]) -> dict[str, dict[str, float]]:
    matrix: dict[str, dict[str, float]] = {}
    for left, left_score in scores.items():
        matrix[left] = {}
        for right, right_score in scores.items():
            if left == right:
                continue
            matrix[left][right] = _bounded((left_score.energy + right_score.volatility) / 2)
    return matrix


def _target_year(context: ChartContext) -> int | None:
    flow = context.time_layers.get("flow_context", {})
    if isinstance(flow, dict):
        target_date = str(flow.get("target_date") or "")
        if len(target_date) >= 4:
            try:
                return int(target_date[:4])
            except ValueError:
                return None
    return None


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)
