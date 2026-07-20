from __future__ import annotations

from typing import Any

from core.contracts.base import Topic
from core.state.contracts import (
    ConfidenceDriver,
    ConfidenceLimiter,
    ConfidenceProbeGain,
    DecisionConfidenceBand,
    DecisionConfidenceComponent,
    DecisionConfidenceProfile,
    DecisionConfidenceScore,
    DecisionStrategySource,
    DomainStateEnrichment,
    TimingStateEvolution,
    UnifiedThemeBundle,
    UncertaintyLevel,
    UncertaintyProfile,
)


SUPPORTED_DECISION_CONFIDENCE_DOMAINS = {Topic.CAREER, Topic.WEALTH, Topic.GENERAL}


def build_decision_confidence_profile_v1(
    *,
    reading_id: str,
    domain: Topic,
    theme_bundle: UnifiedThemeBundle,
    timing_evolution: TimingStateEvolution,
    domain_state: DomainStateEnrichment,
    mechanism_ast: list[dict[str, Any]],
    evidence_refs: list[str],
    theory_refs: list[str],
    probe_candidates: list[dict[str, Any]],
    must_not_say: list[str],
) -> DecisionConfidenceProfile:
    """Build auditable decision support confidence from existing semantics."""

    if domain not in SUPPORTED_DECISION_CONFIDENCE_DOMAINS:
        profile_refs = _unique(evidence_refs)
        return DecisionConfidenceProfile(
            profile_id=f"decision_confidence:{reading_id}:{domain.value}",
            reading_id=reading_id,
            domain=domain,
            domain_supported=False,
            domain_gap=True,
            decision_context={"strategy_bias": "unknown", "strategy_source": DecisionStrategySource.UNKNOWN.value},
            score=DecisionConfidenceScore(value=0.0, band=DecisionConfidenceBand.NOT_AVAILABLE, calibrated=False),
            confidence_limiters=[
                ConfidenceLimiter(reason="unsupported_domain", missing_input=domain.value, uncertainty_ref=f"uncertainty:{reading_id}:{domain.value}")
            ],
            must_not_say=must_not_say,
            evidence_refs=profile_refs,
            theory_refs=theory_refs,
            uncertainty=_uncertainty_profile(profile_refs, ["unsupported_domain"]),
        )

    components = {
        "self_understanding": _self_understanding_component(theme_bundle=theme_bundle, domain_state=domain_state),
        "timing_understanding": _timing_understanding_component(timing_evolution=timing_evolution),
        "evidence_trust": _evidence_trust_component(
            theme_bundle=theme_bundle,
            timing_evolution=timing_evolution,
            domain_state=domain_state,
            mechanism_ast=mechanism_ast,
            evidence_refs=evidence_refs,
        ),
        "action_clarity": _action_clarity_component(theme_bundle=theme_bundle, timing_evolution=timing_evolution, evidence_refs=evidence_refs),
    }
    uncertainty_drag = _uncertainty_drag(theme_bundle=theme_bundle, timing_evolution=timing_evolution, domain_state=domain_state)
    conflict_penalty = _conflict_penalty(theme_bundle=theme_bundle, mechanism_ast=mechanism_ast, timing_evolution=timing_evolution)
    raw_score = (
        0.25 * components["self_understanding"].score
        + 0.25 * components["timing_understanding"].score
        + 0.25 * components["evidence_trust"].score
        + 0.25 * components["action_clarity"].score
        - uncertainty_drag
        - conflict_penalty
    )
    value = round(max(0.0, min(1.0, raw_score)), 3)
    profile_refs = _unique(
        [
            *evidence_refs,
            *theme_bundle.evidence_refs,
            *timing_evolution.evidence_refs,
            *domain_state.evidence_refs,
        ]
    )
    limiters = _limiters(
        reading_id=reading_id,
        theme_bundle=theme_bundle,
        timing_evolution=timing_evolution,
        domain_state=domain_state,
        uncertainty_drag=uncertainty_drag,
        conflict_penalty=conflict_penalty,
    )
    drivers = _drivers(components)
    probes = _probe_gains(probe_candidates=probe_candidates, evidence_refs=profile_refs, limiters=limiters)
    return DecisionConfidenceProfile(
        profile_id=f"decision_confidence:{reading_id}:{domain.value}",
        reading_id=reading_id,
        domain=domain,
        decision_context={
            "strategy_bias": timing_evolution.strategy_bias.value.value,
            "strategy_source": _strategy_source(theme_bundle=theme_bundle, timing_evolution=timing_evolution, domain_state=domain_state),
        },
        score=DecisionConfidenceScore(value=value, band=_band(value), calibrated=False),
        components=components,
        confidence_drivers=drivers,
        confidence_limiters=limiters,
        what_would_increase_confidence=probes,
        must_not_say=must_not_say,
        evidence_refs=profile_refs,
        theory_refs=theory_refs,
        uncertainty=_uncertainty_profile(profile_refs, [limiter.reason for limiter in limiters]),
    )


def _self_understanding_component(*, theme_bundle: UnifiedThemeBundle, domain_state: DomainStateEnrichment) -> DecisionConfidenceComponent:
    theme_score = theme_bundle.primary_theme.strength
    completeness_bonus = {"complete": 0.18, "partial": 0.1, "weak": 0.02, "unknown": 0.0}.get(theme_bundle.primary_theme.completeness.value, 0.0)
    coverage = min(0.24, len(domain_state.state_dimensions) / 32)
    uncertainty_penalty = min(0.18, len(theme_bundle.missing_theme_inputs) * 0.04 + len(domain_state.missing_state_dimensions) * 0.01)
    score = _clamp(theme_score * 0.58 + completeness_bonus + coverage - uncertainty_penalty)
    return DecisionConfidenceComponent(
        component_id="self_understanding",
        score=score,
        reasons=["theme_strength", "theme_completeness", "state_dimension_coverage"],
        source_theme_refs=[theme_bundle.primary_theme.theme_id],
        source_state_refs=[dimension.dimension_id for dimension in domain_state.state_dimensions],
        evidence_refs=_unique([*theme_bundle.primary_theme.evidence_refs, *domain_state.evidence_refs]),
    )


def _timing_understanding_component(*, timing_evolution: TimingStateEvolution) -> DecisionConfidenceComponent:
    layers = sum(1 for value in [timing_evolution.luck, timing_evolution.year, timing_evolution.month] if value is not None)
    layer_score = layers / 3
    strategy_score = 0.0 if timing_evolution.strategy_bias.value.value == "unknown" else 0.26
    window_score = min(0.22, 0.08 * (len(timing_evolution.risk_windows) + len(timing_evolution.opportunity_windows)))
    missing_penalty = min(0.24, 0.08 * len(timing_evolution.missing_inputs))
    score = _clamp(0.42 * layer_score + strategy_score + window_score - missing_penalty)
    return DecisionConfidenceComponent(
        component_id="timing_understanding",
        score=score,
        reasons=["timing_layer_coverage", "strategy_bias_clarity", "risk_opportunity_window_coverage"],
        source_timing_refs=[timing_evolution.evolution_id],
        evidence_refs=timing_evolution.evidence_refs,
    )


def _evidence_trust_component(
    *,
    theme_bundle: UnifiedThemeBundle,
    timing_evolution: TimingStateEvolution,
    domain_state: DomainStateEnrichment,
    mechanism_ast: list[dict[str, Any]],
    evidence_refs: list[str],
) -> DecisionConfidenceComponent:
    density = min(0.38, len(set(evidence_refs)) / 80)
    traceability = 0.22 if theme_bundle.primary_theme.evidence_refs and timing_evolution.evidence_refs and domain_state.evidence_refs else 0.0
    mechanism_quality = 0.18 if all(str(item.get("completeness", "")) != "reference_only" for item in mechanism_ast) else 0.04
    state_quality = min(0.22, len(domain_state.state_dimensions) / 36)
    score = _clamp(density + traceability + mechanism_quality + state_quality)
    return DecisionConfidenceComponent(
        component_id="evidence_trust",
        score=score,
        reasons=["evidence_density", "evidence_traceability", "mechanism_ast_completeness"],
        source_theme_refs=[theme_bundle.primary_theme.theme_id],
        source_state_refs=[dimension.dimension_id for dimension in domain_state.state_dimensions],
        source_timing_refs=[timing_evolution.evolution_id],
        evidence_refs=_unique([*evidence_refs, *theme_bundle.evidence_refs, *timing_evolution.evidence_refs, *domain_state.evidence_refs]),
    )


def _action_clarity_component(
    *,
    theme_bundle: UnifiedThemeBundle,
    timing_evolution: TimingStateEvolution,
    evidence_refs: list[str],
) -> DecisionConfidenceComponent:
    strategy = timing_evolution.strategy_bias.value.value
    strategy_score = 0.0 if strategy == "unknown" else 0.36
    action_specificity = 0.22 if timing_evolution.risk_windows or timing_evolution.opportunity_windows else 0.08
    theme_alignment = 0.16 if theme_bundle.primary_theme.strategy_link == strategy or theme_bundle.primary_theme.active_now else 0.06
    missing_penalty = min(0.16, len(timing_evolution.missing_inputs) * 0.04)
    score = _clamp(strategy_score + action_specificity + theme_alignment - missing_penalty)
    return DecisionConfidenceComponent(
        component_id="action_clarity",
        score=score,
        reasons=[f"strategy_bias:{strategy}", "risk_opportunity_specificity", "theme_strategy_alignment"],
        source_theme_refs=[theme_bundle.primary_theme.theme_id],
        source_timing_refs=[timing_evolution.evolution_id],
        evidence_refs=_unique([*evidence_refs, *theme_bundle.evidence_refs, *timing_evolution.evidence_refs]),
    )


def _uncertainty_drag(*, theme_bundle: UnifiedThemeBundle, timing_evolution: TimingStateEvolution, domain_state: DomainStateEnrichment) -> float:
    return round(
        min(
            0.32,
            0.04 * len(theme_bundle.missing_theme_inputs)
            + 0.05 * len(timing_evolution.missing_inputs)
            + 0.015 * len(domain_state.missing_state_dimensions),
        ),
        3,
    )


def _conflict_penalty(*, theme_bundle: UnifiedThemeBundle, mechanism_ast: list[dict[str, Any]], timing_evolution: TimingStateEvolution) -> float:
    penalty = 0.04 * len(theme_bundle.theme_conflicts)
    if len({str(item.get("mechanism_code", "")) for item in mechanism_ast}) > 2:
        penalty += 0.04
    if timing_evolution.risk_windows and timing_evolution.opportunity_windows:
        penalty += 0.04
    return round(min(0.18, penalty), 3)


def _limiters(
    *,
    reading_id: str,
    theme_bundle: UnifiedThemeBundle,
    timing_evolution: TimingStateEvolution,
    domain_state: DomainStateEnrichment,
    uncertainty_drag: float,
    conflict_penalty: float,
) -> list[ConfidenceLimiter]:
    limiters: list[ConfidenceLimiter] = []
    for missing in timing_evolution.missing_inputs:
        limiters.append(ConfidenceLimiter(reason="missing_timing", missing_input=missing, uncertainty_ref=f"uncertainty:{reading_id}:timing"))
    if theme_bundle.missing_theme_inputs:
        limiters.append(ConfidenceLimiter(reason="weak_or_incomplete_theme", missing_input=",".join(theme_bundle.missing_theme_inputs), uncertainty_ref=f"uncertainty:{reading_id}:theme"))
    if domain_state.missing_state_dimensions:
        limiters.append(ConfidenceLimiter(reason="thin_state", missing_input=",".join(domain_state.missing_state_dimensions[:4]), uncertainty_ref=f"uncertainty:{reading_id}:state"))
    if conflict_penalty > 0:
        limiters.append(ConfidenceLimiter(reason="conflict_penalty", missing_input="theme_or_timing_conflict", uncertainty_ref=f"uncertainty:{reading_id}:conflict"))
    if uncertainty_drag > 0 and not limiters:
        limiters.append(ConfidenceLimiter(reason="uncertainty_drag", missing_input="uncertainty", uncertainty_ref=f"uncertainty:{reading_id}:general"))
    return limiters or [ConfidenceLimiter(reason="residual_uncertainty", missing_input="user_context", uncertainty_ref=f"uncertainty:{reading_id}:context")]


def _drivers(components: dict[str, DecisionConfidenceComponent]) -> list[ConfidenceDriver]:
    drivers: list[ConfidenceDriver] = []
    for component in components.values():
        if component.score >= 0.45:
            drivers.append(ConfidenceDriver(reason=f"{component.component_id}:{component.reasons[0]}", evidence_refs=component.evidence_refs[:6]))
    return drivers or [ConfidenceDriver(reason="baseline_traceable_evidence", evidence_refs=next(iter(components.values())).evidence_refs[:3])]


def _probe_gains(*, probe_candidates: list[dict[str, Any]], evidence_refs: list[str], limiters: list[ConfidenceLimiter]) -> list[ConfidenceProbeGain]:
    gains: list[ConfidenceProbeGain] = []
    if probe_candidates:
        for probe in probe_candidates[:3]:
            gains.append(
                ConfidenceProbeGain(
                    probe_question=str(probe.get("question_code") or probe.get("probe_id") or "probe.reality_calibration"),
                    reason=str(probe.get("reason") or "reduce_decision_uncertainty"),
                    expected_information_gain=float(probe.get("expected_information_gain", 0.42)),
                    evidence_refs=_unique([*_as_list(probe.get("evidence_refs")), *evidence_refs[:1]]),
                )
            )
    if not gains:
        for limiter in limiters[:2]:
            gains.append(
                ConfidenceProbeGain(
                    probe_question=f"probe.{limiter.reason}",
                    reason=f"resolve_{limiter.reason}",
                    expected_information_gain=0.48,
                    evidence_refs=evidence_refs[:1],
                )
            )
    return gains


def _strategy_source(*, theme_bundle: UnifiedThemeBundle, timing_evolution: TimingStateEvolution, domain_state: DomainStateEnrichment) -> str:
    sources = []
    if theme_bundle.primary_theme.theme_type.value != "unknown":
        sources.append(DecisionStrategySource.THEME.value)
    if timing_evolution.strategy_bias.value.value != "unknown":
        sources.append(DecisionStrategySource.TIMING.value)
    if domain_state.state_dimensions:
        sources.append(DecisionStrategySource.STATE.value)
    if len(sources) >= 2:
        return DecisionStrategySource.MIXED.value
    return sources[0] if sources else DecisionStrategySource.UNKNOWN.value


def _band(value: float) -> DecisionConfidenceBand:
    if value >= 0.72:
        return DecisionConfidenceBand.HIGH
    if value >= 0.45:
        return DecisionConfidenceBand.MEDIUM
    return DecisionConfidenceBand.LOW


def _uncertainty_profile(evidence_refs: list[str], reasons: list[str]) -> UncertaintyProfile:
    level = UncertaintyLevel.HIGH if any(reason in {"unsupported_domain", "missing_timing"} for reason in reasons) else UncertaintyLevel.MEDIUM
    return UncertaintyProfile(level=level, reasons=reasons or ["decision_confidence_directional"], evidence_refs=_unique(evidence_refs))


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


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
