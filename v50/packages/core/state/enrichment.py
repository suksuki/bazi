from __future__ import annotations

from typing import Any

from core.contracts.base import Topic
from core.state.contracts import (
    DomainStateEnrichment,
    OpportunityField,
    RiskField,
    SemanticStateDeltaStatus,
    StateDimension,
    StateDirection,
    StatePolarity,
    TimingStateSummary,
    UncertaintyLevel,
    UncertaintyProfile,
)


SUPPORTED_ENRICHMENT_DOMAINS = {Topic.CAREER, Topic.WEALTH, Topic.GENERAL}

EXPECTED_DIMENSIONS: dict[Topic, set[str]] = {
    Topic.CAREER: {
        "career_direction",
        "output_drive",
        "pressure_handling",
        "authority_pressure",
        "stability",
        "mobility",
        "opportunity",
        "risk",
        "timing_activation",
    },
    Topic.WEALTH: {
        "wealth_path",
        "earning_capacity",
        "accumulation_capacity",
        "competition_or_leakage",
        "volatility",
        "opportunity",
        "risk",
        "timing_activation",
    },
    Topic.GENERAL: {
        "dominant_life_pattern",
        "core_tension",
        "support_field",
        "risk_field",
        "opportunity_field",
    },
}


def build_domain_state_enrichment(
    *,
    reading_id: str,
    domain: Topic,
    mechanism_ast: list[dict[str, Any]],
    evidence_refs: list[str],
    theory_refs: list[str] | None = None,
    timing_state: dict[str, Any] | None = None,
    uncertainty: dict[str, Any] | None = None,
) -> DomainStateEnrichment:
    """Extract semantic state dimensions from existing mechanism evidence.

    This is not a judgment layer. It gives research state analysis a richer
    vocabulary for evidence already present in Mechanism AST and timing metadata.
    """

    theory_refs = theory_refs or []
    if domain not in SUPPORTED_ENRICHMENT_DOMAINS:
        profile = _uncertainty_profile(
            reading_id=reading_id,
            evidence_refs=evidence_refs,
            missing_dimensions=[],
            reasons=[f"unsupported_domain:{domain.value}"],
        )
        return DomainStateEnrichment(
            enrichment_id=f"state_enrichment:{reading_id}:{domain.value}",
            reading_id=reading_id,
            domain=domain,
            domain_supported=False,
            domain_gap=True,
            uncertainty_profile=profile,
            unsupported_reason=f"domain_not_supported_by_unified_state_enrichment_v1:{domain.value}",
            evidence_refs=_unique(evidence_refs),
            theory_refs=theory_refs,
        )

    dimensions = _dimensions_from_ast(
        reading_id=reading_id,
        domain=domain,
        mechanism_ast=mechanism_ast,
        evidence_refs=evidence_refs,
        theory_refs=theory_refs,
        timing_state=timing_state or {},
    )
    observed = {dimension.name for dimension in dimensions}
    missing = sorted(EXPECTED_DIMENSIONS.get(domain, set()) - observed)
    profile = _uncertainty_profile(
        reading_id=reading_id,
        evidence_refs=evidence_refs,
        missing_dimensions=missing,
        reasons=_uncertainty_reasons(uncertainty or {}, missing),
    )
    risk_field = _risk_field(reading_id=reading_id, domain=domain, dimensions=dimensions)
    opportunity_field = _opportunity_field(reading_id=reading_id, domain=domain, dimensions=dimensions)
    timing_summary = _timing_summary(
        reading_id=reading_id,
        domain=domain,
        dimensions=dimensions,
        timing_state=timing_state or {},
    )
    return DomainStateEnrichment(
        enrichment_id=f"state_enrichment:{reading_id}:{domain.value}",
        reading_id=reading_id,
        domain=domain,
        domain_supported=True,
        domain_gap=False,
        state_dimensions=dimensions,
        risk_field=risk_field,
        opportunity_field=opportunity_field,
        timing_state_summary=timing_summary,
        uncertainty_profile=profile,
        missing_state_dimensions=missing,
        evidence_refs=_unique(evidence_refs),
        theory_refs=theory_refs,
    )


def _dimensions_from_ast(
    *,
    reading_id: str,
    domain: Topic,
    mechanism_ast: list[dict[str, Any]],
    evidence_refs: list[str],
    theory_refs: list[str],
    timing_state: dict[str, Any],
) -> list[StateDimension]:
    specs: dict[str, dict[str, Any]] = {}
    for ast in mechanism_ast:
        mechanism_code = str(ast.get("mechanism_code") or ast.get("mechanism_ref") or "unknown")
        representation_ref = str(ast.get("representation_id") or ast.get("mechanism_ref") or f"mechanism:{mechanism_code}")
        ast_evidence = _unique([*_as_list(ast.get("evidence_refs")), *evidence_refs])
        source_refs = [representation_ref]
        roles = _roles(ast)
        state_delta_status = _state_delta_status(ast)
        role_names = {str(component.get("role", "")) for component in roles}

        for dimension_name, polarity, direction in _mechanism_dimension_specs(domain, mechanism_code):
            _merge_spec(
                specs,
                name=dimension_name,
                polarity=polarity,
                direction=direction,
                score=_score(ast),
                source_refs=source_refs,
                evidence_refs=ast_evidence,
                state_delta_status=state_delta_status,
                reason=f"mechanism:{mechanism_code}",
            )
        for role in role_names:
            for dimension_name, polarity, direction in _role_dimension_specs(domain, role):
                _merge_spec(
                    specs,
                    name=dimension_name,
                    polarity=polarity,
                    direction=direction,
                    score=_score(ast),
                    source_refs=source_refs,
                    evidence_refs=ast_evidence,
                    state_delta_status=state_delta_status,
                    reason=f"role:{role}",
                )
        if state_delta_status != SemanticStateDeltaStatus.MISSING:
            _merge_spec(
                specs,
                name="timing_activation",
                polarity=StatePolarity.MIXED,
                direction=_direction_from_timing(timing_state),
                score=max(_score(ast), 0.55),
                source_refs=source_refs,
                evidence_refs=_unique([*_as_list(ast.get("state_delta_refs")), *ast_evidence]),
                state_delta_status=state_delta_status,
                reason=f"state_delta:{state_delta_status.value}",
            )

    return [
        StateDimension(
            dimension_id=f"state_dimension:{reading_id}:{domain.value}:{name}",
            reading_id=reading_id,
            domain=domain,
            name=name,
            score=round(min(1.0, spec["score"]), 3),
            polarity=spec["polarity"],
            direction=spec["direction"],
            source_mechanism_refs=sorted(spec["source_refs"]),
            evidence_refs=_unique(list(spec["evidence_refs"])),
            theory_refs=theory_refs,
            uncertainty=_uncertainty_profile(
                reading_id=reading_id,
                evidence_refs=_unique(list(spec["evidence_refs"])),
                missing_dimensions=[],
                reasons=sorted(spec["reasons"]),
            ),
            state_delta_status=spec["state_delta_status"],
        )
        for name, spec in sorted(specs.items())
    ]


def _mechanism_dimension_specs(domain: Topic, mechanism_code: str) -> list[tuple[str, StatePolarity, StateDirection]]:
    if domain == Topic.CAREER:
        mapping = {
            "output_to_wealth": [("output_drive", StatePolarity.POSITIVE, StateDirection.STABLE), ("career_direction", StatePolarity.POSITIVE, StateDirection.UNKNOWN), ("opportunity", StatePolarity.POSITIVE, StateDirection.UNKNOWN)],
            "output_controls_pressure": [("pressure_handling", StatePolarity.POSITIVE, StateDirection.STABLE), ("authority_pressure", StatePolarity.MIXED, StateDirection.UNKNOWN), ("risk", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "officer_pressure": [("authority_pressure", StatePolarity.NEGATIVE, StateDirection.UNKNOWN), ("risk", StatePolarity.NEGATIVE, StateDirection.UNKNOWN)],
            "resource_support": [("stability", StatePolarity.POSITIVE, StateDirection.STABLE), ("opportunity", StatePolarity.POSITIVE, StateDirection.UNKNOWN)],
            "branch_relation_movement": [("mobility", StatePolarity.MIXED, StateDirection.UNKNOWN), ("opportunity", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "peer_competes_for_wealth": [("risk", StatePolarity.MIXED, StateDirection.UNKNOWN)],
        }
        return mapping.get(mechanism_code, [("career_direction", StatePolarity.NEUTRAL, StateDirection.UNKNOWN)])
    if domain == Topic.WEALTH:
        mapping = {
            "output_to_wealth": [("wealth_path", StatePolarity.POSITIVE, StateDirection.STABLE), ("earning_capacity", StatePolarity.POSITIVE, StateDirection.UNKNOWN), ("opportunity", StatePolarity.POSITIVE, StateDirection.UNKNOWN)],
            "peer_competes_for_wealth": [("competition_or_leakage", StatePolarity.NEGATIVE, StateDirection.UNKNOWN), ("risk", StatePolarity.NEGATIVE, StateDirection.UNKNOWN), ("volatility", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "output_controls_pressure": [("earning_capacity", StatePolarity.MIXED, StateDirection.UNKNOWN), ("risk", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "officer_pressure": [("risk", StatePolarity.NEGATIVE, StateDirection.UNKNOWN), ("volatility", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "resource_support": [("accumulation_capacity", StatePolarity.POSITIVE, StateDirection.STABLE)],
            "branch_relation_movement": [("volatility", StatePolarity.MIXED, StateDirection.UNKNOWN), ("opportunity", StatePolarity.MIXED, StateDirection.UNKNOWN)],
        }
        return mapping.get(mechanism_code, [("wealth_path", StatePolarity.NEUTRAL, StateDirection.UNKNOWN)])
    if domain == Topic.GENERAL:
        mapping = {
            "output_to_wealth": [("dominant_life_pattern", StatePolarity.POSITIVE, StateDirection.UNKNOWN), ("opportunity_field", StatePolarity.POSITIVE, StateDirection.UNKNOWN)],
            "output_controls_pressure": [("core_tension", StatePolarity.MIXED, StateDirection.UNKNOWN), ("risk_field", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "resource_support": [("support_field", StatePolarity.POSITIVE, StateDirection.STABLE)],
            "officer_pressure": [("core_tension", StatePolarity.NEGATIVE, StateDirection.UNKNOWN), ("risk_field", StatePolarity.NEGATIVE, StateDirection.UNKNOWN)],
        }
        return mapping.get(mechanism_code, [("dominant_life_pattern", StatePolarity.NEUTRAL, StateDirection.UNKNOWN)])
    return []


def _role_dimension_specs(domain: Topic, role: str) -> list[tuple[str, StatePolarity, StateDirection]]:
    if domain == Topic.CAREER:
        mapping = {
            "converter": [("output_drive", StatePolarity.POSITIVE, StateDirection.UNKNOWN), ("pressure_handling", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "bridge": [("mobility", StatePolarity.MIXED, StateDirection.UNKNOWN), ("opportunity", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "anchor": [("stability", StatePolarity.POSITIVE, StateDirection.STABLE)],
            "counter_force": [("risk", StatePolarity.NEGATIVE, StateDirection.UNKNOWN), ("authority_pressure", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "state_delta": [("timing_activation", StatePolarity.MIXED, StateDirection.UNKNOWN)],
        }
        return mapping.get(role, [])
    if domain == Topic.WEALTH:
        mapping = {
            "converter": [("earning_capacity", StatePolarity.POSITIVE, StateDirection.UNKNOWN)],
            "bridge": [("volatility", StatePolarity.MIXED, StateDirection.UNKNOWN), ("opportunity", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "anchor": [("accumulation_capacity", StatePolarity.POSITIVE, StateDirection.STABLE)],
            "counter_force": [("competition_or_leakage", StatePolarity.NEGATIVE, StateDirection.UNKNOWN), ("risk", StatePolarity.NEGATIVE, StateDirection.UNKNOWN)],
            "state_delta": [("timing_activation", StatePolarity.MIXED, StateDirection.UNKNOWN)],
        }
        return mapping.get(role, [])
    if domain == Topic.GENERAL:
        mapping = {
            "converter": [("dominant_life_pattern", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "bridge": [("opportunity_field", StatePolarity.MIXED, StateDirection.UNKNOWN)],
            "anchor": [("support_field", StatePolarity.POSITIVE, StateDirection.STABLE)],
            "counter_force": [("risk_field", StatePolarity.NEGATIVE, StateDirection.UNKNOWN), ("core_tension", StatePolarity.MIXED, StateDirection.UNKNOWN)],
        }
        return mapping.get(role, [])
    return []


def _merge_spec(
    specs: dict[str, dict[str, Any]],
    *,
    name: str,
    polarity: StatePolarity,
    direction: StateDirection,
    score: float,
    source_refs: list[str],
    evidence_refs: list[str],
    state_delta_status: SemanticStateDeltaStatus,
    reason: str,
) -> None:
    spec = specs.setdefault(
        name,
        {
            "score": 0.0,
            "polarity": polarity,
            "direction": direction,
            "source_refs": set(),
            "evidence_refs": set(),
            "state_delta_status": SemanticStateDeltaStatus.MISSING,
            "reasons": set(),
        },
    )
    spec["score"] = max(spec["score"], score)
    if spec["polarity"] == StatePolarity.NEUTRAL:
        spec["polarity"] = polarity
    elif polarity != spec["polarity"]:
        spec["polarity"] = StatePolarity.MIXED
    if spec["direction"] == StateDirection.UNKNOWN:
        spec["direction"] = direction
    elif direction != StateDirection.UNKNOWN and direction != spec["direction"]:
        spec["direction"] = StateDirection.UNKNOWN
    spec["source_refs"].update(source_refs)
    spec["evidence_refs"].update(evidence_refs)
    spec["reasons"].add(reason)
    if state_delta_status == SemanticStateDeltaStatus.REAL:
        spec["state_delta_status"] = SemanticStateDeltaStatus.REAL
    elif spec["state_delta_status"] == SemanticStateDeltaStatus.MISSING and state_delta_status == SemanticStateDeltaStatus.INFERRED:
        spec["state_delta_status"] = SemanticStateDeltaStatus.INFERRED


def _risk_field(*, reading_id: str, domain: Topic, dimensions: list[StateDimension]) -> RiskField | None:
    risk_dimensions = [dimension for dimension in dimensions if dimension.name in {"risk", "authority_pressure", "competition_or_leakage", "volatility", "core_tension", "risk_field"}]
    if not risk_dimensions:
        return None
    return RiskField(
        field_id=f"risk_field:{reading_id}:{domain.value}",
        reading_id=reading_id,
        domain=domain,
        dimension_refs=[dimension.dimension_id for dimension in risk_dimensions],
        risk_codes=[dimension.name for dimension in risk_dimensions],
        score=max(dimension.score for dimension in risk_dimensions),
        evidence_refs=_unique([ref for dimension in risk_dimensions for ref in dimension.evidence_refs]),
    )


def _opportunity_field(*, reading_id: str, domain: Topic, dimensions: list[StateDimension]) -> OpportunityField | None:
    opportunity_dimensions = [dimension for dimension in dimensions if dimension.name in {"opportunity", "earning_capacity", "output_drive", "support_field", "opportunity_field"}]
    if not opportunity_dimensions:
        return None
    return OpportunityField(
        field_id=f"opportunity_field:{reading_id}:{domain.value}",
        reading_id=reading_id,
        domain=domain,
        dimension_refs=[dimension.dimension_id for dimension in opportunity_dimensions],
        opportunity_codes=[dimension.name for dimension in opportunity_dimensions],
        score=max(dimension.score for dimension in opportunity_dimensions),
        evidence_refs=_unique([ref for dimension in opportunity_dimensions for ref in dimension.evidence_refs]),
    )


def _timing_summary(
    *,
    reading_id: str,
    domain: Topic,
    dimensions: list[StateDimension],
    timing_state: dict[str, Any],
) -> TimingStateSummary | None:
    timing_dimensions = [dimension for dimension in dimensions if dimension.name == "timing_activation"]
    if not timing_dimensions:
        return None
    activated_by = _as_list(timing_state.get("activated_by")) or _as_list(timing_state.get("timing_refs"))
    if not activated_by:
        return None
    return TimingStateSummary(
        summary_id=f"timing_state_summary:{reading_id}:{domain.value}",
        reading_id=reading_id,
        domain=domain,
        activated_by=[str(value) for value in activated_by],
        state_delta_status=timing_dimensions[0].state_delta_status,
        direction=timing_dimensions[0].direction,
        evidence_refs=_unique([ref for dimension in timing_dimensions for ref in dimension.evidence_refs]),
    )


def _uncertainty_profile(
    *,
    reading_id: str,
    evidence_refs: list[str],
    missing_dimensions: list[str],
    reasons: list[str],
) -> UncertaintyProfile:
    level = UncertaintyLevel.HIGH if len(missing_dimensions) >= 4 else UncertaintyLevel.MEDIUM if missing_dimensions else UncertaintyLevel.LOW
    return UncertaintyProfile(
        level=level,
        reasons=reasons or ["state_enrichment_from_existing_evidence"],
        missing_dimensions=missing_dimensions,
        evidence_refs=_unique(evidence_refs),
    )


def _uncertainty_reasons(uncertainty: dict[str, Any], missing: list[str]) -> list[str]:
    reasons = []
    if uncertainty.get("reason"):
        reasons.append(str(uncertainty["reason"]))
    if uncertainty.get("conflict_summary"):
        reasons.append(str(uncertainty["conflict_summary"]))
    if missing:
        reasons.append("missing_state_dimensions")
    return reasons or ["no_additional_uncertainty_reported"]


def _roles(ast: dict[str, Any]) -> list[dict[str, Any]]:
    components = ast.get("components", [])
    if isinstance(components, list):
        return [component for component in components if isinstance(component, dict)]
    return []


def _score(ast: dict[str, Any]) -> float:
    value = ast.get("confidence", 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _state_delta_status(ast: dict[str, Any]) -> SemanticStateDeltaStatus:
    value = str(ast.get("state_delta_status") or "missing")
    if value == "real":
        return SemanticStateDeltaStatus.REAL
    if value == "inferred":
        return SemanticStateDeltaStatus.INFERRED
    return SemanticStateDeltaStatus.MISSING


def _direction_from_timing(timing_state: dict[str, Any]) -> StateDirection:
    trend = str(timing_state.get("trend") or "")
    if trend == "increasing":
        return StateDirection.INCREASING
    if trend == "decreasing":
        return StateDirection.DECREASING
    if trend == "stable":
        return StateDirection.STABLE
    return StateDirection.UNKNOWN


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _unique(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in seen:
            seen.add(text)
            output.append(text)
    return output
