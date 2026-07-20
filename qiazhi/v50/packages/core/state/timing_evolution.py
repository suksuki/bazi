from __future__ import annotations

from typing import Any

from core.contracts.base import Topic
from core.state.contracts import (
    StateDimension,
    TimingActivatedPath,
    TimingLayerEffect,
    TimingStateDimensionDelta,
    TimingStateEvolution,
    TimingStrategyBias,
    TimingStrategyBiasValue,
    TimingWindow,
    UncertaintyLevel,
    UncertaintyProfile,
)
from core.timing import TimingLayer, TimingModelCandidate, build_timing_model_candidates_v1


SUPPORTED_TIMING_DOMAINS = {Topic.CAREER, Topic.WEALTH, Topic.GENERAL}


def build_timing_state_evolution_v1(
    *,
    reading_id: str,
    domain: Topic,
    state_dimensions: list[StateDimension],
    mechanism_ast: list[dict[str, Any]],
    evidence_refs: list[str],
    theory_refs: list[str] | None = None,
    timing_overlays: dict[str, dict[str, Any]] | None = None,
    timing_model_candidates: list[TimingModelCandidate] | None = None,
) -> TimingStateEvolution:
    """Build auditable timing state evolution from existing state evidence.

    v1 uses TimingModelCandidate as policy candidates and explicit overlays as
    context. It does not promote a timing theory to runtime truth.
    """

    theory_refs = theory_refs or []
    timing_overlays = timing_overlays or {}
    candidates = timing_model_candidates or build_timing_model_candidates_v1()

    if domain not in SUPPORTED_TIMING_DOMAINS:
        profile = _uncertainty_profile(evidence_refs, ["unsupported_timing_domain"])
        return TimingStateEvolution(
            evolution_id=f"timing_state_evolution:{reading_id}:{domain.value}",
            reading_id=reading_id,
            domain=domain,
            domain_supported=False,
            domain_gap=True,
            strategy_bias=TimingStrategyBias(value=TimingStrategyBiasValue.UNKNOWN, reason="unsupported_domain", confidence=0.0),
            unsupported_domains=[domain.value],
            missing_inputs=[],
            evidence_refs=_unique(evidence_refs),
            theory_refs=theory_refs,
        )

    layer_effects = {
        layer.value: _layer_effect(
            reading_id=reading_id,
            layer=layer,
            overlay=timing_overlays.get(layer.value),
            candidates=candidates,
            fallback_evidence_refs=evidence_refs,
        )
        for layer in (TimingLayer.LUCK, TimingLayer.YEAR, TimingLayer.MONTH)
    }
    present_effects = {key: value for key, value in layer_effects.items() if value is not None}
    missing_inputs = [f"no_{layer}" for layer, value in layer_effects.items() if value is None]

    activated_dimensions: list[TimingStateDimensionDelta] = []
    weakened_dimensions: list[TimingStateDimensionDelta] = []
    for dimension in state_dimensions:
        delta, activated_by, weakened_by = _dimension_delta(dimension=dimension, effects=present_effects)
        if abs(delta) < 0.035:
            continue
        after_score = round(max(0.0, min(1.0, dimension.score + delta)), 3)
        refs = _unique([*dimension.evidence_refs, *[ref for effect in present_effects.values() for ref in effect.evidence_refs]])
        item = TimingStateDimensionDelta(
            delta_id=f"timing_delta:{reading_id}:{domain.value}:{dimension.name}",
            reading_id=reading_id,
            domain=domain,
            dimension_id=dimension.dimension_id,
            dimension_name=dimension.name,
            before_score=dimension.score,
            after_score=after_score,
            delta=round(delta, 3),
            activated_by=activated_by,
            weakened_by=weakened_by,
            evidence_refs=refs,
            uncertainty=_uncertainty_profile(refs, _uncertainty_reasons(missing_inputs)),
        )
        if delta > 0:
            activated_dimensions.append(item)
        else:
            weakened_dimensions.append(item)

    activated_paths = _activated_paths(mechanism_ast=mechanism_ast, effects=present_effects)
    risk_windows = _windows(
        reading_id=reading_id,
        domain=domain,
        dimensions=[*activated_dimensions, *weakened_dimensions],
        effects=present_effects,
        window_kind="risk",
        evidence_refs=evidence_refs,
    )
    opportunity_windows = _windows(
        reading_id=reading_id,
        domain=domain,
        dimensions=[*activated_dimensions, *weakened_dimensions],
        effects=present_effects,
        window_kind="opportunity",
        evidence_refs=evidence_refs,
    )
    strategy = _strategy_bias(
        activated_dimensions=activated_dimensions,
        weakened_dimensions=weakened_dimensions,
        risk_windows=risk_windows,
        opportunity_windows=opportunity_windows,
        missing_inputs=missing_inputs,
        effects=present_effects,
    )
    return TimingStateEvolution(
        evolution_id=f"timing_state_evolution:{reading_id}:{domain.value}",
        reading_id=reading_id,
        domain=domain,
        luck=present_effects.get("luck"),
        year=present_effects.get("year"),
        month=present_effects.get("month"),
        activated_state_dimensions=activated_dimensions,
        weakened_state_dimensions=weakened_dimensions,
        activated_paths=activated_paths,
        risk_windows=risk_windows,
        opportunity_windows=opportunity_windows,
        strategy_bias=strategy,
        unsupported_domains=["relationship", "health", "family", "education"],
        missing_inputs=missing_inputs,
        evidence_refs=_unique([*evidence_refs, *[ref for effect in present_effects.values() for ref in effect.evidence_refs]]),
        theory_refs=theory_refs,
    )


def _layer_effect(
    *,
    reading_id: str,
    layer: TimingLayer,
    overlay: dict[str, Any] | None,
    candidates: list[TimingModelCandidate],
    fallback_evidence_refs: list[str],
) -> TimingLayerEffect | None:
    if overlay is None:
        return None
    candidate = _candidate_for_layer(layer=layer, candidates=candidates, model_id=str(overlay.get("model_id", "")))
    if candidate is None:
        return None
    evidence_refs = _unique([candidate.model_id, *candidate.source_refs, *_as_list(overlay.get("evidence_refs")), *fallback_evidence_refs[:1]])
    return TimingLayerEffect(
        layer=layer.value,
        stem=str(overlay.get("stem", "")),
        branch=str(overlay.get("branch", "")),
        model_candidate_ref=candidate.model_id,
        effect_summary=_effect_summary(candidate),
        confidence=float(overlay.get("confidence", candidate.current_confidence)),
        evidence_refs=evidence_refs,
    )


def _candidate_for_layer(*, layer: TimingLayer, candidates: list[TimingModelCandidate], model_id: str) -> TimingModelCandidate | None:
    layer_candidates = [candidate for candidate in candidates if candidate.timing_layer == layer]
    if model_id:
        for candidate in layer_candidates:
            if candidate.model_id == model_id:
                return candidate
    return sorted(layer_candidates, key=lambda candidate: candidate.current_confidence, reverse=True)[0] if layer_candidates else None


def _effect_summary(candidate: TimingModelCandidate) -> str:
    outputs = ",".join(output.value for output in candidate.simulator_outputs[:3])
    return f"{candidate.timing_layer.value}:{candidate.model_family.value}:{outputs}"


def _dimension_delta(*, dimension: StateDimension, effects: dict[str, TimingLayerEffect]) -> tuple[float, list[str], list[str]]:
    delta = 0.0
    activated_by: list[str] = []
    weakened_by: list[str] = []
    for layer_name, effect in effects.items():
        layer_delta = _layer_dimension_delta(layer_name=layer_name, effect=effect, dimension_name=dimension.name)
        delta += layer_delta
        if layer_delta > 0:
            activated_by.append(layer_name)
        elif layer_delta < 0:
            weakened_by.append(layer_name)
    return round(max(-0.38, min(0.38, delta)), 3), activated_by, weakened_by


def _layer_dimension_delta(*, layer_name: str, effect: TimingLayerEffect, dimension_name: str) -> float:
    confidence = effect.confidence
    model = effect.model_candidate_ref
    if layer_name == "luck":
        base = 0.12 * confidence
        if any(token in dimension_name for token in ("stability", "accumulation", "career_direction", "wealth_path")):
            return base
        if any(token in dimension_name for token in ("mobility", "volatility", "risk")) and "perturbation" in model:
            return base * 0.75
        if any(token in dimension_name for token in ("output", "earning", "opportunity")):
            return base * 0.65
    if layer_name == "year":
        base = 0.10 * confidence
        if any(token in dimension_name for token in ("timing", "opportunity", "mobility", "earning")):
            return base
        if any(token in dimension_name for token in ("risk", "pressure", "volatility", "competition")):
            return base * 0.8
    if layer_name == "month":
        base = 0.06 * confidence
        if any(token in dimension_name for token in ("opportunity", "risk", "volatility", "timing")):
            return base
        if dimension_name in {"stability", "accumulation_capacity"}:
            return -base * 0.5
    return 0.0


def _activated_paths(*, mechanism_ast: list[dict[str, Any]], effects: dict[str, TimingLayerEffect]) -> list[TimingActivatedPath]:
    if not effects:
        return []
    items: list[TimingActivatedPath] = []
    for ast in mechanism_ast:
        path_refs = _as_list(ast.get("path_refs"))
        evidence_refs = _unique([*_as_list(ast.get("evidence_refs")), *[ref for effect in effects.values() for ref in effect.evidence_refs]])
        for index, path_ref in enumerate(path_refs[:2]):
            layer = "year" if "year" in effects else "luck" if "luck" in effects else "month"
            items.append(
                TimingActivatedPath(
                    path_ref=str(path_ref),
                    activation_reason=f"{layer}.path_activation_candidate",
                    timing_layer=layer,
                    evidence_refs=evidence_refs,
                )
            )
            if index >= 1:
                break
    return items


def _windows(
    *,
    reading_id: str,
    domain: Topic,
    dimensions: list[TimingStateDimensionDelta],
    effects: dict[str, TimingLayerEffect],
    window_kind: str,
    evidence_refs: list[str],
) -> list[TimingWindow]:
    if not effects:
        return []
    if window_kind == "risk":
        names = {"risk", "authority_pressure", "competition_or_leakage", "volatility"}
    else:
        names = {"opportunity", "earning_capacity", "output_drive", "wealth_path", "career_direction"}
    matching = [dimension for dimension in dimensions if dimension.dimension_name in names and dimension.delta > 0]
    if not matching:
        return []
    layer = "month" if "month" in effects else "year" if "year" in effects else "luck"
    refs = _unique([*evidence_refs, *[ref for dimension in matching for ref in dimension.evidence_refs], *effects[layer].evidence_refs])
    return [
        TimingWindow(
            window_id=f"timing_window:{reading_id}:{domain.value}:{window_kind}:{layer}",
            reading_id=reading_id,
            domain=domain,
            timing_label=layer,
            window_type=window_kind,
            score=max(dimension.after_score for dimension in matching),
            evidence_refs=refs,
            uncertainty=_uncertainty_profile(refs, [f"{window_kind}_window_is_directional_not_exact_event"]),
        )
    ]


def _strategy_bias(
    *,
    activated_dimensions: list[TimingStateDimensionDelta],
    weakened_dimensions: list[TimingStateDimensionDelta],
    risk_windows: list[TimingWindow],
    opportunity_windows: list[TimingWindow],
    missing_inputs: list[str],
    effects: dict[str, TimingLayerEffect],
) -> TimingStrategyBias:
    if not effects:
        return TimingStrategyBias(value=TimingStrategyBiasValue.UNKNOWN, reason="missing_timing_inputs", confidence=0.0)
    opportunity_score = max((window.score for window in opportunity_windows), default=0.0)
    risk_score = max((window.score for window in risk_windows), default=0.0)
    refs = _unique([ref for effect in effects.values() for ref in effect.evidence_refs])
    confidence = round(sum(effect.confidence for effect in effects.values()) / max(1, len(effects)), 3)
    if risk_score >= opportunity_score + 0.12:
        value = TimingStrategyBiasValue.REDUCE_RISK
        reason = "risk_window_stronger_than_opportunity_window"
    elif opportunity_score >= risk_score + 0.12:
        value = TimingStrategyBiasValue.ADVANCE
        reason = "opportunity_window_stronger_than_risk_window"
    elif "luck" in effects and "no_year" in missing_inputs:
        value = TimingStrategyBiasValue.ACCUMULATE
        reason = "long_term_field_present_without_near_trigger"
    elif weakened_dimensions:
        value = TimingStrategyBiasValue.HOLD
        reason = "state_weakening_requires_holding_boundary"
    else:
        value = TimingStrategyBiasValue.WAIT if missing_inputs else TimingStrategyBiasValue.HOLD
        reason = "mixed_timing_signals"
    return TimingStrategyBias(value=value, reason=reason, confidence=confidence, evidence_refs=refs)


def _uncertainty_profile(evidence_refs: list[str], reasons: list[str]) -> UncertaintyProfile:
    level = UncertaintyLevel.MEDIUM if reasons else UncertaintyLevel.LOW
    return UncertaintyProfile(level=level, reasons=reasons or ["timing_state_evolution_directional"], evidence_refs=_unique(evidence_refs))


def _uncertainty_reasons(missing_inputs: list[str]) -> list[str]:
    return missing_inputs or ["timing_direction_not_exact_event"]


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
