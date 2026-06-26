from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from pydantic import Field

from v30.contracts import ChartContext, FeatureEvidence, StructureState, V30Model


LATENT_BAZI_PROFILE_VERSION = "v30.latent_bazi_profile.v1"


class LatentBaziProfileDimension(V30Model):
    dimension_id: str
    state_tag: str
    status: str
    linked_domains: list[str] = Field(default_factory=list)
    linked_ten_god_families: list[str] = Field(default_factory=list)
    linked_dynamic_path_ids: list[str] = Field(default_factory=list)
    linked_claim_ids: list[str] = Field(default_factory=list)
    linked_evidence_ids: list[str] = Field(default_factory=list)
    years: list[int] = Field(default_factory=list)
    recurrence: str = ""
    intensity: str = ""
    confidence: str = ""
    signal_strength: float = 0.0
    source_feedback_ids: list[str] = Field(default_factory=list)
    source_question_ids: list[str] = Field(default_factory=list)
    boundary: str = "latent_profile_dimension_is_feedback_conditioned_bazi_attribute_not_chart_fact"


class LatentBaziProfile(V30Model):
    version: str = LATENT_BAZI_PROFILE_VERSION
    profile_id: str
    reading_id: str
    context_id: str
    chart_signature: dict[str, Any] = Field(default_factory=dict)
    source_state_id: str = ""
    status: str = "empty"
    dimensions: list[LatentBaziProfileDimension] = Field(default_factory=list)
    linked_evidence_ids: list[str] = Field(default_factory=list)
    linked_dynamic_path_ids: list[str] = Field(default_factory=list)
    linked_claim_ids: list[str] = Field(default_factory=list)
    chart_fact_mutation_allowed: bool = False
    calculation_use_policy: str = "available_as_calibration_signal_after_validation_only"
    training_routes: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    boundary: str = "latent_bazi_profile_binds_user_calibration_to_chart_context_without_mutating_facts"


STATE_TAG_BINDINGS: dict[str, dict[str, list[str]]] = {
    "career_pressure": {
        "domains": ["career", "useful_god"],
        "ten_god_families": ["authority", "resource"],
    },
    "role_change": {
        "domains": ["career", "timing"],
        "ten_god_families": ["authority", "resource"],
    },
    "wealth_fluctuation": {
        "domains": ["wealth", "timing"],
        "ten_god_families": ["wealth", "output"],
    },
    "partnership_distribution": {
        "domains": ["wealth", "relationship"],
        "ten_god_families": ["wealth", "authority"],
    },
    "relationship_repetition": {
        "domains": ["relationship", "timing"],
        "ten_god_families": ["wealth", "authority"],
    },
    "family_pressure": {
        "domains": ["relationship", "health"],
        "ten_god_families": ["resource", "authority"],
    },
    "health_rhythm": {
        "domains": ["health", "timing"],
        "ten_god_families": ["output", "authority"],
    },
    "credential_pressure": {
        "domains": ["career", "useful_god"],
        "ten_god_families": ["resource", "authority"],
    },
    "relocation_change": {
        "domains": ["career", "timing"],
        "ten_god_families": ["output", "wealth"],
    },
}


def build_latent_bazi_profile(
    *,
    context: ChartContext,
    structure: StructureState,
    feature_evidence: list[FeatureEvidence],
    hidden_factor_state: Mapping[str, Any] | None,
    real_bazi_diagnosis: Mapping[str, Any] | None = None,
    question_outcomes: list[Mapping[str, Any]] | None = None,
) -> LatentBaziProfile:
    state = dict(hidden_factor_state or {})
    repeated_states = [tag for tag in _str_list(state.get("repeated_states")) if tag in STATE_TAG_BINDINGS]
    diagnosis = dict(real_bazi_diagnosis or {})
    question_outcomes = question_outcomes or []
    dimensions = [
        _build_dimension(
            context=context,
            structure=structure,
            feature_evidence=feature_evidence,
            diagnosis=diagnosis,
            state=state,
            question_outcomes=question_outcomes,
            state_tag=state_tag,
        )
        for state_tag in repeated_states
    ]
    linked_evidence_ids = _dedupe([item for row in dimensions for item in row.linked_evidence_ids])
    linked_dynamic_path_ids = _dedupe([item for row in dimensions for item in row.linked_dynamic_path_ids])
    linked_claim_ids = _dedupe([item for row in dimensions for item in row.linked_claim_ids])
    status = _profile_status(str(state.get("status") or ""), dimensions)
    return LatentBaziProfile(
        profile_id=f"{context.reading_id}:latent_bazi_profile",
        reading_id=context.reading_id,
        context_id=context.context_id,
        chart_signature=_chart_signature(context),
        source_state_id=str(state.get("state_id") or ""),
        status=status,
        dimensions=dimensions,
        linked_evidence_ids=linked_evidence_ids,
        linked_dynamic_path_ids=linked_dynamic_path_ids,
        linked_claim_ids=linked_claim_ids,
        training_routes=_training_routes(dimensions),
    )


def summarize_latent_bazi_profile(profile: Mapping[str, Any] | LatentBaziProfile) -> dict[str, Any]:
    payload = profile.model_dump(mode="json") if isinstance(profile, LatentBaziProfile) else dict(profile or {})
    dimensions = payload.get("dimensions", [])
    dimensions = dimensions if isinstance(dimensions, list) else []
    return {
        "version": "v30.latent_bazi_profile.summary.v1",
        "profile_id": str(payload.get("profile_id") or ""),
        "reading_id": str(payload.get("reading_id") or ""),
        "context_id": str(payload.get("context_id") or ""),
        "status": str(payload.get("status") or ""),
        "dimension_count": len(dimensions),
        "active_state_tags": [
            str(row.get("state_tag"))
            for row in dimensions
            if isinstance(row, Mapping) and row.get("state_tag")
        ],
        "linked_dynamic_path_count": len(_str_list(payload.get("linked_dynamic_path_ids"))),
        "linked_claim_count": len(_str_list(payload.get("linked_claim_ids"))),
        "chart_fact_mutation_allowed": bool(payload.get("chart_fact_mutation_allowed")),
        "calculation_use_policy": str(payload.get("calculation_use_policy") or ""),
        "boundary": "latent_profile_summary_is_diagnostic_projection_not_chart_fact",
    }


def _build_dimension(
    *,
    context: ChartContext,
    structure: StructureState,
    feature_evidence: list[FeatureEvidence],
    diagnosis: Mapping[str, Any],
    state: Mapping[str, Any],
    question_outcomes: list[Mapping[str, Any]],
    state_tag: str,
) -> LatentBaziProfileDimension:
    bindings = STATE_TAG_BINDINGS.get(state_tag, {})
    domains = bindings.get("domains", ["structure"])
    families = bindings.get("ten_god_families", [])
    evidence_ids = _linked_evidence(feature_evidence, domains=domains, families=families)
    paths = _linked_paths(diagnosis, domains)
    claims = _linked_claims(diagnosis, domains, paths)
    if not evidence_ids:
        evidence_ids = _str_list(state.get("evidence_ids"))
    years = _int_list(state.get("special_event_years"))
    return LatentBaziProfileDimension(
        dimension_id=f"{context.reading_id}:latent:{state_tag}",
        state_tag=state_tag,
        status=_dimension_status(str(state.get("status") or ""), bool(paths or claims or evidence_ids)),
        linked_domains=_dedupe(domains),
        linked_ten_god_families=_dedupe(families),
        linked_dynamic_path_ids=_dedupe([*paths, *_structure_path_ids(structure, domains)]),
        linked_claim_ids=claims,
        linked_evidence_ids=evidence_ids,
        years=years,
        recurrence=_latest_structured_value(question_outcomes, "recurrence"),
        intensity=_latest_structured_value(question_outcomes, "intensity"),
        confidence=_latest_structured_value(question_outcomes, "confidence"),
        signal_strength=_signal_strength(state),
        source_feedback_ids=_str_list(state.get("feedback_ids")),
        source_question_ids=_source_question_ids(question_outcomes),
    )


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


def _linked_evidence(
    feature_evidence: list[FeatureEvidence],
    *,
    domains: list[str],
    families: list[str],
) -> list[str]:
    rows: list[str] = []
    domain_set = set(domains)
    family_set = set(families)
    for evidence in feature_evidence:
        evidence_family = str(evidence.kind or "")
        supports = {str(row) for row in evidence.supports}
        if evidence.domain in domain_set or evidence.domain == "ten_god" or supports & family_set:
            rows.append(evidence.evidence_id)
        elif any(family in evidence_family for family in family_set):
            rows.append(evidence.evidence_id)
    return _dedupe(rows)


def _linked_paths(diagnosis: Mapping[str, Any], domains: list[str]) -> list[str]:
    domain_set = set(domains)
    paths = diagnosis.get("paths", [])
    if not isinstance(paths, list):
        return []
    rows: list[str] = []
    for path in paths:
        if not isinstance(path, Mapping):
            continue
        targets = {str(row) for row in _list(path.get("domain_targets"))}
        if targets & domain_set:
            rows.append(str(path.get("path_id") or ""))
    return _dedupe(rows)


def _linked_claims(diagnosis: Mapping[str, Any], domains: list[str], path_ids: list[str]) -> list[str]:
    domain_set = set(domains)
    path_set = set(path_ids)
    claims = diagnosis.get("claims", [])
    if not isinstance(claims, list):
        return []
    rows: list[str] = []
    for claim in claims:
        if not isinstance(claim, Mapping):
            continue
        claim_paths = {str(row) for row in _list(claim.get("path_ids"))}
        if str(claim.get("domain") or "") in domain_set or claim_paths & path_set:
            rows.append(str(claim.get("claim_id") or ""))
    return _dedupe(rows)


def _structure_path_ids(structure: StructureState, domains: list[str]) -> list[str]:
    rows: list[str] = []
    domain_set = set(domains)
    for node in structure.graph_nodes:
        if not isinstance(node, Mapping):
            continue
        tags = {str(row) for row in _list(node.get("domain_tags"))}
        if tags and tags & domain_set:
            rows.append(str(node.get("node_id") or ""))
    return _dedupe(rows)


def _dimension_status(hidden_status: str, has_chart_links: bool) -> str:
    if hidden_status in {"conflicting", "user_denied", "expired"}:
        return hidden_status
    if hidden_status in {"amplifier_candidate", "feedback_calibrated"} and has_chart_links:
        return "chart_linked_candidate"
    if has_chart_links:
        return "chart_linked_signal"
    return "feedback_only_needs_chart_link"


def _profile_status(hidden_status: str, dimensions: list[LatentBaziProfileDimension]) -> str:
    if not dimensions:
        return "empty"
    if hidden_status in {"conflicting", "user_denied", "expired"}:
        return hidden_status
    if any(row.status == "chart_linked_candidate" for row in dimensions):
        return "chart_linked_candidate"
    return "chart_linked_signal"


def _training_routes(dimensions: list[LatentBaziProfileDimension]) -> list[str]:
    if not dimensions:
        return []
    return [
        "latent_bazi_profile_calibration",
        "question_strategy_calibration",
        "real_bazi_diagnosis_calibration",
    ]


def _latest_structured_value(question_outcomes: list[Mapping[str, Any]], key: str) -> str:
    for outcome in reversed(question_outcomes):
        signal = outcome.get("interaction_turn_signal")
        if not isinstance(signal, Mapping):
            continue
        structured = signal.get("structured_payload")
        if not isinstance(structured, Mapping):
            continue
        value = str(structured.get(key) or "")
        if value:
            return value
    return ""


def _source_question_ids(question_outcomes: list[Mapping[str, Any]]) -> list[str]:
    return _dedupe([str(row.get("question_id") or "") for row in question_outcomes if row.get("question_id")])


def _signal_strength(state: Mapping[str, Any]) -> float:
    try:
        return round(float(state.get("amplifier_strength") or 0.0), 3)
    except (TypeError, ValueError):
        return 0.0


def _int_list(value: Any) -> list[int]:
    rows: list[int] = []
    for raw in _list(value):
        try:
            rows.append(int(raw))
        except (TypeError, ValueError):
            continue
    return sorted(set(rows))


def _str_list(value: Any) -> list[str]:
    return _dedupe([str(row) for row in _list(value) if str(row or "").strip()])


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
