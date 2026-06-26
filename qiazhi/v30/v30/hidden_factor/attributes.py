from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from pydantic import Field

from v30.contracts import ChartContext, V30Model
from v30.hidden_factor.latent_profile import LATENT_BAZI_PROFILE_VERSION


LATENT_BAZI_ATTRIBUTES_VERSION = "v30.latent_bazi_attributes.v1"
INDIVIDUALIZED_MODEL_PROJECTION_VERSION = "v30.latent_bazi_individualized_model_projection.v1"


class LatentAttributeScore(V30Model):
    key: str
    value: float = 0.5
    default_value: float = 0.5
    confidence: float = 0.1
    evidence_count: int = 0
    source_dimension_ids: list[str] = Field(default_factory=list)
    source_years: list[int] = Field(default_factory=list)
    linked_bazi_parts: list[str] = Field(default_factory=list)
    inference_notes: list[str] = Field(default_factory=list)
    boundary: str = "latent_attribute_score_is_inferred_modifier_not_chart_fact"


class LatentModifierScore(V30Model):
    key: str
    multiplier: float = 1.0
    default_multiplier: float = 1.0
    confidence: float = 0.1
    evidence_count: int = 0
    source_dimension_ids: list[str] = Field(default_factory=list)
    source_years: list[int] = Field(default_factory=list)
    linked_bazi_parts: list[str] = Field(default_factory=list)
    inference_notes: list[str] = Field(default_factory=list)
    boundary: str = "latent_modifier_score_is_inferred_multiplier_not_chart_fact"


class LatentBaziAttributes(V30Model):
    version: str = LATENT_BAZI_ATTRIBUTES_VERSION
    attributes_id: str
    reading_id: str
    context_id: str
    chart_signature: dict[str, Any] = Field(default_factory=dict)
    source_profile_version: str = LATENT_BAZI_PROFILE_VERSION
    source_profile_id: str = ""
    status: str = "default"
    global_attributes: dict[str, LatentAttributeScore] = Field(default_factory=dict)
    ten_god_modifiers: dict[str, LatentModifierScore] = Field(default_factory=dict)
    domain_biases: dict[str, LatentAttributeScore] = Field(default_factory=dict)
    stability_thresholds: dict[str, LatentAttributeScore] = Field(default_factory=dict)
    calculation_modifiers: dict[str, Any] = Field(default_factory=dict)
    inference_trace: list[dict[str, Any]] = Field(default_factory=list)
    chart_fact_mutation_allowed: bool = False
    calculation_use_policy: str = "may_modify_energy_stability_and_path_scores_after_validation_not_chart_facts"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    boundary: str = "latent_bazi_attributes_personalize_model_calculation_without_mutating_chart_facts"


GLOBAL_ATTRIBUTE_KEYS = (
    "luck_index",
    "stability_index",
    "execution_index",
    "resource_index",
    "risk_index",
    "recovery_index",
    "choice_quality_index",
)

TEN_GOD_MODIFIER_KEYS = (
    "day_master",
    "wealth",
    "authority",
    "resource",
    "output",
    "peer",
)

DOMAIN_BIAS_KEYS = (
    "career_bias",
    "wealth_bias",
    "relationship_bias",
    "health_bias",
    "migration_bias",
    "learning_bias",
    "family_drag",
    "partnership_drag",
)

STABILITY_THRESHOLD_KEYS = (
    "pressure_tolerance",
    "event_trigger_sensitivity",
    "volatility_tolerance",
)

STATE_TAG_ATTRIBUTE_EFFECTS: dict[str, dict[str, list[str]]] = {
    "career_pressure": {
        "global_up": ["resource_index", "risk_index"],
        "ten_god_up": ["authority", "resource"],
        "domain_up": ["career_bias"],
        "threshold_up": ["event_trigger_sensitivity"],
    },
    "role_change": {
        "global_up": ["execution_index", "risk_index"],
        "ten_god_up": ["authority"],
        "domain_up": ["career_bias"],
        "threshold_up": ["event_trigger_sensitivity"],
    },
    "wealth_fluctuation": {
        "global_up": ["risk_index"],
        "global_down": ["stability_index"],
        "ten_god_up": ["wealth", "output"],
        "domain_up": ["wealth_bias"],
        "threshold_down": ["volatility_tolerance"],
    },
    "partnership_distribution": {
        "global_up": ["risk_index"],
        "ten_god_up": ["wealth", "authority"],
        "domain_up": ["wealth_bias", "partnership_drag"],
        "threshold_up": ["event_trigger_sensitivity"],
    },
    "relationship_repetition": {
        "global_up": ["risk_index"],
        "global_down": ["stability_index"],
        "ten_god_up": ["wealth", "authority"],
        "domain_up": ["relationship_bias"],
        "threshold_up": ["event_trigger_sensitivity"],
    },
    "family_pressure": {
        "global_up": ["risk_index"],
        "global_down": ["stability_index"],
        "ten_god_up": ["resource", "authority"],
        "domain_up": ["family_drag", "relationship_bias"],
        "threshold_down": ["pressure_tolerance"],
    },
    "health_rhythm": {
        "global_up": ["risk_index"],
        "global_down": ["stability_index", "recovery_index"],
        "ten_god_up": ["output", "authority"],
        "domain_up": ["health_bias"],
        "threshold_down": ["pressure_tolerance", "volatility_tolerance"],
    },
    "credential_pressure": {
        "global_up": ["resource_index", "choice_quality_index"],
        "ten_god_up": ["resource", "authority"],
        "domain_up": ["career_bias", "learning_bias"],
        "threshold_up": ["pressure_tolerance"],
    },
    "relocation_change": {
        "global_up": ["luck_index", "execution_index", "risk_index"],
        "ten_god_up": ["output", "wealth"],
        "domain_up": ["migration_bias", "career_bias"],
        "threshold_up": ["event_trigger_sensitivity"],
    },
}


def build_latent_bazi_attributes(
    *,
    context: ChartContext,
    latent_profile: Mapping[str, Any] | None = None,
) -> LatentBaziAttributes:
    profile = dict(latent_profile or {})
    global_attributes = {key: _attribute_score(key) for key in GLOBAL_ATTRIBUTE_KEYS}
    ten_god_modifiers = {key: _modifier_score(key) for key in TEN_GOD_MODIFIER_KEYS}
    domain_biases = {key: _attribute_score(key) for key in DOMAIN_BIAS_KEYS}
    stability_thresholds = {key: _attribute_score(key) for key in STABILITY_THRESHOLD_KEYS}
    inference_trace: list[dict[str, Any]] = []
    dimensions = profile.get("dimensions", [])
    if not isinstance(dimensions, list):
        dimensions = []
    for dimension in dimensions:
        if not isinstance(dimension, Mapping):
            continue
        state_tag = str(dimension.get("state_tag") or "")
        effects = STATE_TAG_ATTRIBUTE_EFFECTS.get(state_tag)
        if not effects:
            continue
        delta = _dimension_delta(dimension)
        confidence_delta = _dimension_confidence_delta(dimension)
        source = _source_payload(dimension, state_tag=state_tag, delta=delta)
        _apply_attribute_effects(
            global_attributes,
            keys=effects.get("global_up", []),
            delta=delta,
            confidence_delta=confidence_delta,
            source=source,
        )
        _apply_attribute_effects(
            global_attributes,
            keys=effects.get("global_down", []),
            delta=-delta,
            confidence_delta=confidence_delta,
            source=source,
        )
        _apply_modifier_effects(
            ten_god_modifiers,
            keys=effects.get("ten_god_up", []),
            delta=delta,
            confidence_delta=confidence_delta,
            source=source,
        )
        _apply_attribute_effects(
            domain_biases,
            keys=effects.get("domain_up", []),
            delta=delta,
            confidence_delta=confidence_delta,
            source=source,
        )
        _apply_attribute_effects(
            stability_thresholds,
            keys=effects.get("threshold_up", []),
            delta=delta,
            confidence_delta=confidence_delta,
            source=source,
        )
        _apply_attribute_effects(
            stability_thresholds,
            keys=effects.get("threshold_down", []),
            delta=-delta,
            confidence_delta=confidence_delta,
            source=source,
        )
        inference_trace.append(source)
    status = "inferred" if inference_trace else "default"
    attrs = LatentBaziAttributes(
        attributes_id=f"{context.reading_id}:latent_bazi_attributes",
        reading_id=context.reading_id,
        context_id=context.context_id,
        chart_signature=_chart_signature(context),
        source_profile_id=str(profile.get("profile_id") or ""),
        status=status,
        global_attributes=global_attributes,
        ten_god_modifiers=ten_god_modifiers,
        domain_biases=domain_biases,
        stability_thresholds=stability_thresholds,
        calculation_modifiers=_calculation_modifiers(
            global_attributes=global_attributes,
            ten_god_modifiers=ten_god_modifiers,
            domain_biases=domain_biases,
            stability_thresholds=stability_thresholds,
            status=status,
        ),
        inference_trace=inference_trace,
    )
    return attrs


def summarize_latent_bazi_attributes(attributes: Mapping[str, Any] | LatentBaziAttributes) -> dict[str, Any]:
    payload = attributes.model_dump(mode="json") if isinstance(attributes, LatentBaziAttributes) else dict(attributes or {})
    global_attributes = _dict(payload.get("global_attributes"))
    ten_god_modifiers = _dict(payload.get("ten_god_modifiers"))
    domain_biases = _dict(payload.get("domain_biases"))
    return {
        "version": "v30.latent_bazi_attributes.summary.v1",
        "attributes_id": str(payload.get("attributes_id") or ""),
        "reading_id": str(payload.get("reading_id") or ""),
        "context_id": str(payload.get("context_id") or ""),
        "status": str(payload.get("status") or ""),
        "active_global_attributes": _active_score_keys(global_attributes, score_key="value", default=0.5),
        "active_ten_god_modifiers": _active_score_keys(ten_god_modifiers, score_key="multiplier", default=1.0),
        "active_domain_biases": _active_score_keys(domain_biases, score_key="value", default=0.5),
        "inference_trace_count": len(payload.get("inference_trace", [])) if isinstance(payload.get("inference_trace"), list) else 0,
        "chart_fact_mutation_allowed": bool(payload.get("chart_fact_mutation_allowed")),
        "calculation_use_policy": str(payload.get("calculation_use_policy") or ""),
        "boundary": "latent_bazi_attributes_summary_is_diagnostic_projection_not_chart_fact",
    }


def build_individualized_model_projection(
    *,
    context: ChartContext,
    ten_god_energy_model: Mapping[str, Any] | None = None,
    ten_god_energy_summary: Mapping[str, Any] | None = None,
    ranked_decisions: Mapping[str, Any] | None = None,
    latent_attributes: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    attrs = _dict(latent_attributes)
    modifiers = _dict(attrs.get("calculation_modifiers"))
    family_multipliers = _float_mapping(modifiers.get("family_energy_multipliers"), default=1.0)
    domain_multipliers = _float_mapping(modifiers.get("domain_path_multipliers"), default=1.0)
    global_context = _float_mapping(modifiers.get("global_energy_context"), default=0.5)
    thresholds = _float_mapping(modifiers.get("stability_thresholds"), default=0.5)
    model = _dict(ten_god_energy_model)
    summary = _dict(ten_god_energy_summary)
    ranked = _dict(ranked_decisions)
    individualization_ready = bool(modifiers.get("individualization_ready"))
    family_rows = _family_energy_projection(
        model_scores=_dict(model.get("scores")),
        top_energy=_list(summary.get("top_energy")),
        family_multipliers=family_multipliers,
    )
    domain_rows = _domain_path_projection(domain_multipliers)
    ranked_rows = _ranked_decision_projection(ranked, global_context=global_context, thresholds=thresholds)
    return {
        "version": INDIVIDUALIZED_MODEL_PROJECTION_VERSION,
        "projection_id": f"{context.reading_id}:latent-bazi-individualized-projection",
        "reading_id": context.reading_id,
        "context_id": context.context_id,
        "status": "inferred" if individualization_ready else "default",
        "individualization_ready": individualization_ready,
        "source_attributes_id": str(attrs.get("attributes_id") or ""),
        "base_model_refs": {
            "ten_god_energy_version": str(model.get("version") or "v30.ten_god_energy_model.v1"),
            "ten_god_energy_status": str(model.get("status") or summary.get("status") or ""),
            "ranked_decision_domains": sorted(str(key) for key in ranked.keys()),
        },
        "family_energy_projection": family_rows,
        "domain_path_projection": domain_rows,
        "ranked_decision_projection": ranked_rows,
        "global_energy_context": global_context,
        "stability_thresholds": thresholds,
        "chart_fact_mutation_allowed": False,
        "base_ten_god_energy_mutation_allowed": False,
        "ranked_decision_mutation_allowed": False,
        "boundary": "individualized_projection_is_diagnostic_candidate_model_not_base_energy_or_ranked_decision_mutation",
    }


def summarize_individualized_model_projection(projection: Mapping[str, Any]) -> dict[str, Any]:
    payload = _dict(projection)
    family_rows = _list(payload.get("family_energy_projection"))
    domain_rows = _list(payload.get("domain_path_projection"))
    ranked_rows = _list(payload.get("ranked_decision_projection"))
    adjusted_family = [
        str(row.get("family"))
        for row in family_rows
        if isinstance(row, Mapping) and _changed(row, "base_energy", "adjusted_energy")
    ]
    adjusted_domains = [
        str(row.get("domain"))
        for row in domain_rows
        if isinstance(row, Mapping) and _changed(row, "base_path_score", "adjusted_path_score")
    ]
    return {
        "version": "v30.latent_bazi_individualized_model_projection.summary.v1",
        "projection_id": str(payload.get("projection_id") or ""),
        "reading_id": str(payload.get("reading_id") or ""),
        "context_id": str(payload.get("context_id") or ""),
        "status": str(payload.get("status") or ""),
        "individualization_ready": bool(payload.get("individualization_ready")),
        "adjusted_family_count": len(adjusted_family),
        "adjusted_families": adjusted_family,
        "adjusted_domain_count": len(adjusted_domains),
        "adjusted_domains": adjusted_domains,
        "ranked_projection_count": len(ranked_rows),
        "chart_fact_mutation_allowed": bool(payload.get("chart_fact_mutation_allowed")),
        "base_ten_god_energy_mutation_allowed": bool(payload.get("base_ten_god_energy_mutation_allowed")),
        "ranked_decision_mutation_allowed": bool(payload.get("ranked_decision_mutation_allowed")),
        "boundary": "individualized_projection_summary_is_diagnostic_not_base_model_mutation",
    }


def _attribute_score(key: str) -> LatentAttributeScore:
    return LatentAttributeScore(key=key)


def _modifier_score(key: str) -> LatentModifierScore:
    return LatentModifierScore(key=key)


def _family_energy_projection(
    *,
    model_scores: Mapping[str, Any],
    top_energy: list[Any],
    family_multipliers: Mapping[str, float],
) -> list[dict[str, Any]]:
    by_family: dict[str, dict[str, Any]] = {}
    for label, raw in model_scores.items():
        row = _dict(raw)
        family = str(row.get("family") or "")
        if not family:
            continue
        energy = _float(row.get("energy"))
        stability = _float(row.get("stability"))
        volatility = _float(row.get("volatility"))
        current = by_family.get(family)
        if current is None or energy > _float(current.get("base_energy")):
            by_family[family] = {
                "label": str(label),
                "family": family,
                "base_energy": energy,
                "base_stability": stability,
                "base_volatility": volatility,
            }
    if not by_family:
        for raw in top_energy:
            row = _dict(raw)
            family = str(row.get("family") or "")
            if family:
                by_family[family] = {
                    "label": str(row.get("label") or family),
                    "family": family,
                    "base_energy": _float(row.get("energy")),
                    "base_stability": _float(row.get("stability")),
                    "base_volatility": _float(row.get("volatility")),
                }
    for family in TEN_GOD_MODIFIER_KEYS:
        by_family.setdefault(
            family,
            {
                "label": family,
                "family": family,
                "base_energy": 0.0,
                "base_stability": 0.0,
                "base_volatility": 0.0,
            },
        )
    rows: list[dict[str, Any]] = []
    for family, row in by_family.items():
        multiplier = _float(family_multipliers.get(family, 1.0), default=1.0)
        base_energy = _float(row.get("base_energy"))
        rows.append(
            {
                **row,
                "latent_multiplier": multiplier,
                "adjusted_energy": round(base_energy * multiplier, 3),
                "calculation_boundary": "base_energy_times_latent_family_multiplier_diagnostic_only",
            }
        )
    rows.sort(key=lambda row: (-_float(row.get("adjusted_energy")), str(row.get("family"))))
    return rows


def _domain_path_projection(domain_multipliers: Mapping[str, float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for domain in ("career", "wealth", "relationship", "health", "migration"):
        multiplier = _float(domain_multipliers.get(domain, 1.0), default=1.0)
        rows.append(
            {
                "domain": domain,
                "base_path_score": 1.0,
                "latent_multiplier": multiplier,
                "adjusted_path_score": round(multiplier, 3),
                "calculation_boundary": "neutral_domain_path_score_times_latent_domain_multiplier_diagnostic_only",
            }
        )
    return rows


def _ranked_decision_projection(
    ranked: Mapping[str, Any],
    *,
    global_context: Mapping[str, float],
    thresholds: Mapping[str, float],
) -> list[dict[str, Any]]:
    risk = _float(global_context.get("risk_index", 0.5), default=0.5)
    stability = _float(global_context.get("stability_index", 0.5), default=0.5)
    sensitivity = _float(thresholds.get("event_trigger_sensitivity", 0.5), default=0.5)
    context_multiplier = round(_bounded(1.0 + (stability - 0.5) * 0.25 - (risk - 0.5) * 0.18 + (sensitivity - 0.5) * 0.12, lower=0.7, upper=1.3), 3)
    rows: list[dict[str, Any]] = []
    for domain, raw in ranked.items():
        decision = _dict(raw)
        scores = _dict(decision.get("candidate_scores"))
        primary = str(decision.get("primary_candidate") or "")
        base_score = _float(scores.get(primary), default=max((_float(value) for value in scores.values()), default=0.0))
        rows.append(
            {
                "decision_domain": str(domain),
                "primary_candidate": primary,
                "base_candidate_score": base_score,
                "latent_context_multiplier": context_multiplier,
                "adjusted_candidate_score": round(base_score * context_multiplier, 3),
                "source_decision_id": str(decision.get("decision_id") or ""),
                "calculation_boundary": "ranked_decision_score_projection_diagnostic_only_original_decision_unchanged",
            }
        )
    return rows


def _apply_attribute_effects(
    scores: dict[str, LatentAttributeScore],
    *,
    keys: list[str],
    delta: float,
    confidence_delta: float,
    source: dict[str, Any],
) -> None:
    for key in keys:
        current = scores.get(key, _attribute_score(key))
        scores[key] = current.model_copy(
            update={
                "value": _bounded(current.value + delta),
                "confidence": _bounded(current.confidence + confidence_delta, lower=0.0, upper=1.0),
                "evidence_count": current.evidence_count + 1,
                "source_dimension_ids": _dedupe([*current.source_dimension_ids, str(source.get("dimension_id") or "")]),
                "source_years": _dedupe_int([*current.source_years, *_int_list(source.get("years"))]),
                "linked_bazi_parts": _dedupe([*current.linked_bazi_parts, *_str_list(source.get("linked_bazi_parts"))]),
                "inference_notes": _dedupe([*current.inference_notes, str(source.get("note") or "")]),
            }
        )


def _apply_modifier_effects(
    scores: dict[str, LatentModifierScore],
    *,
    keys: list[str],
    delta: float,
    confidence_delta: float,
    source: dict[str, Any],
) -> None:
    multiplier_delta = round(delta * 0.5, 3)
    for key in keys:
        current = scores.get(key, _modifier_score(key))
        scores[key] = current.model_copy(
            update={
                "multiplier": _bounded(current.multiplier + multiplier_delta, lower=0.7, upper=1.3),
                "confidence": _bounded(current.confidence + confidence_delta, lower=0.0, upper=1.0),
                "evidence_count": current.evidence_count + 1,
                "source_dimension_ids": _dedupe([*current.source_dimension_ids, str(source.get("dimension_id") or "")]),
                "source_years": _dedupe_int([*current.source_years, *_int_list(source.get("years"))]),
                "linked_bazi_parts": _dedupe([*current.linked_bazi_parts, *_str_list(source.get("linked_bazi_parts"))]),
                "inference_notes": _dedupe([*current.inference_notes, str(source.get("note") or "")]),
            }
        )


def _dimension_delta(dimension: Mapping[str, Any]) -> float:
    intensity = str(dimension.get("intensity") or "")
    recurrence = str(dimension.get("recurrence") or "")
    try:
        signal_strength = float(dimension.get("signal_strength") or 0.0)
    except (TypeError, ValueError):
        signal_strength = 0.0
    base = {"light": 0.035, "medium": 0.055, "strong": 0.08}.get(intensity, 0.045)
    base += {"single": 0.0, "repeated": 0.025, "continuous": 0.04}.get(recurrence, 0.0)
    if signal_strength > 0.5:
        base += min(0.035, (signal_strength - 0.5) * 0.08)
    return round(min(base, 0.14), 3)


def _dimension_confidence_delta(dimension: Mapping[str, Any]) -> float:
    confidence = str(dimension.get("confidence") or "")
    evidence_count = len(_str_list(dimension.get("linked_evidence_ids")))
    value = {"certain": 0.22, "approximate": 0.14, "uncertain": 0.08}.get(confidence, 0.08)
    value += min(0.08, evidence_count * 0.01)
    return round(value, 3)


def _source_payload(dimension: Mapping[str, Any], *, state_tag: str, delta: float) -> dict[str, Any]:
    linked_parts = [
        *[f"domain:{row}" for row in _str_list(dimension.get("linked_domains"))],
        *[f"ten_god:{row}" for row in _str_list(dimension.get("linked_ten_god_families"))],
        *[f"path:{row}" for row in _str_list(dimension.get("linked_dynamic_path_ids"))],
        *[f"claim:{row}" for row in _str_list(dimension.get("linked_claim_ids"))],
    ]
    return {
        "state_tag": state_tag,
        "dimension_id": str(dimension.get("dimension_id") or ""),
        "years": _int_list(dimension.get("years")),
        "delta": delta,
        "linked_bazi_parts": linked_parts,
        "note": f"{state_tag}_structured_feedback_updates_latent_attributes",
        "boundary": "reverse_inference_updates_latent_attributes_not_chart_facts",
    }


def _calculation_modifiers(
    *,
    global_attributes: dict[str, LatentAttributeScore],
    ten_god_modifiers: dict[str, LatentModifierScore],
    domain_biases: dict[str, LatentAttributeScore],
    stability_thresholds: dict[str, LatentAttributeScore],
    status: str,
) -> dict[str, Any]:
    return {
        "version": "v30.latent_bazi_calculation_modifiers.v1",
        "individualization_ready": status == "inferred",
        "family_energy_multipliers": {
            key: score.multiplier for key, score in ten_god_modifiers.items()
        },
        "domain_path_multipliers": {
            "career": _domain_multiplier(domain_biases["career_bias"]),
            "wealth": _domain_multiplier(domain_biases["wealth_bias"]),
            "relationship": _domain_multiplier(domain_biases["relationship_bias"]),
            "health": _domain_multiplier(domain_biases["health_bias"]),
            "migration": _domain_multiplier(domain_biases["migration_bias"]),
        },
        "global_energy_context": {
            key: score.value for key, score in global_attributes.items()
        },
        "stability_thresholds": {
            key: score.value for key, score in stability_thresholds.items()
        },
        "formula_boundary": "base_bazi_energy_times_latent_modifiers_is_candidate_model_signal_not_fact",
    }


def _domain_multiplier(score: LatentAttributeScore) -> float:
    return round(_bounded(1.0 + (score.value - 0.5) * 0.6, lower=0.7, upper=1.3), 3)


def _chart_signature(context: ChartContext) -> dict[str, Any]:
    return {
        "day_master": context.day_master,
        "day_master_element": context.day_master_element,
        "natal_pillars": context.natal_pillars,
        "time_layers": {
            key: value
            for key, value in context.time_layers.items()
            if key in {"status", "luck_pillar", "flow_year_pillar", "flow_month_pillar"}
        },
    }


def _active_score_keys(rows: Mapping[str, Any], *, score_key: str, default: float) -> list[str]:
    active: list[str] = []
    for key, raw in rows.items():
        row = _dict(raw)
        try:
            value = float(row.get(score_key, default))
        except (TypeError, ValueError):
            continue
        if abs(value - default) >= 0.001:
            active.append(str(key))
    return active


def _float_mapping(value: Any, *, default: float) -> dict[str, float]:
    payload = _dict(value)
    return {str(key): _float(raw, default=default) for key, raw in payload.items()}


def _changed(row: Mapping[str, Any], base_key: str, adjusted_key: str) -> bool:
    return abs(_float(row.get(base_key)) - _float(row.get(adjusted_key))) >= 0.001


def _float(value: Any, *, default: float = 0.0) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default


def _bounded(value: float, *, lower: float = 0.0, upper: float = 1.0) -> float:
    return round(max(lower, min(upper, value)), 3)


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _str_list(value: Any) -> list[str]:
    return _dedupe([str(row) for row in _list(value) if str(row or "").strip()])


def _int_list(value: Any) -> list[int]:
    rows: list[int] = []
    for raw in _list(value):
        try:
            rows.append(int(raw))
        except (TypeError, ValueError):
            continue
    return _dedupe_int(rows)


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
    return out


def _dedupe_int(values: list[int]) -> list[int]:
    return sorted(set(values))
