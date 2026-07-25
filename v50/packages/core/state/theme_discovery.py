from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from core.contracts.base import Topic
from core.state.contracts import (
    ActiveTheme,
    BaseTheme,
    FlowState,
    PalaceStateSpace,
    RealityState,
    StateDimension,
    StateEvolution,
    TemporalState,
    ThemeCandidate,
    ThemeActivationSource,
    ThemeCompleteness,
    ThemeSensitivity,
    ThemeStability,
    ThemeTransition,
    ThemeTransitionType,
    ThemeType,
    TimingStateEvolution,
    UnifiedTheme,
    UnifiedThemeBundle,
    UncertaintyLevel,
    UncertaintyProfile,
)

SUPPORTED_THEME_DOMAINS = {Topic.CAREER, Topic.WEALTH, Topic.GENERAL}


def discover_unified_theme_bundle(
    *,
    reading_id: str,
    domain: Topic,
    mechanism_ast: list[dict[str, Any]],
    state_dimensions: list[StateDimension],
    timing_evolution: TimingStateEvolution | None,
    evidence_refs: list[str],
    theory_refs: list[str] | None = None,
) -> UnifiedThemeBundle:
    """Discover structural life themes from mechanism, state, and timing evidence."""

    theory_refs = theory_refs or []
    if domain not in SUPPORTED_THEME_DOMAINS:
        profile = _uncertainty_profile(evidence_refs, [f"unsupported_domain:{domain.value}"])
        unknown = ThemeCandidate(
            theme_id=f"theme_candidate:{reading_id}:{domain.value}:unknown",
            reading_id=reading_id,
            domain=domain,
            theme_name="unknown",
            theme_type=ThemeType.UNKNOWN,
            strength=0.0,
            stability=ThemeStability.UNKNOWN,
            timing_sensitivity=ThemeSensitivity.HIGH,
            active_now=None,
            evidence_refs=_unique(evidence_refs),
            theory_refs=theory_refs,
            uncertainty=profile,
            completeness=ThemeCompleteness.UNKNOWN,
        )
        base_theme = _base_theme_from_candidate(unknown)
        active_theme = _unknown_active_theme(reading_id=reading_id, domain=domain, evidence_refs=evidence_refs, reasons=["unsupported_domain"])
        transition = _theme_transition(reading_id=reading_id, domain=domain, base_theme=base_theme, active_theme=active_theme, evidence_refs=evidence_refs)
        return UnifiedThemeBundle(
            bundle_id=f"unified_theme_bundle:{reading_id}:{domain.value}",
            reading_id=reading_id,
            domain=domain,
            domain_supported=False,
            domain_gap=True,
            base_theme=base_theme,
            active_theme=active_theme,
            theme_transition=transition,
            primary_theme=unknown,
            evidence_refs=_unique(evidence_refs),
            theory_refs=theory_refs,
            uncertainty=profile,
            missing_theme_inputs=["unsupported_domain"],
        )

    base_signals = _collect_theme_signals(
        domain=domain,
        mechanism_ast=mechanism_ast,
        state_dimensions=state_dimensions,
        timing_evolution=None,
    )
    base_candidates = _build_candidates(
        reading_id=reading_id,
        domain=domain,
        signals=base_signals,
        mechanism_ast=mechanism_ast,
        state_dimensions=state_dimensions,
        timing_evolution=None,
        evidence_refs=evidence_refs,
        theory_refs=theory_refs,
    )
    legacy_signals = _collect_theme_signals(
        domain=domain,
        mechanism_ast=mechanism_ast,
        state_dimensions=state_dimensions,
        timing_evolution=timing_evolution,
    )
    candidates = _build_candidates(
        reading_id=reading_id,
        domain=domain,
        signals=legacy_signals,
        mechanism_ast=mechanism_ast,
        state_dimensions=state_dimensions,
        timing_evolution=timing_evolution,
        evidence_refs=evidence_refs,
        theory_refs=theory_refs,
    )
    missing_inputs = _missing_theme_inputs(mechanism_ast=mechanism_ast, state_dimensions=state_dimensions, timing_evolution=timing_evolution)
    profile = _uncertainty_profile(evidence_refs, missing_inputs or ["theme_discovery_directional"])
    unknown_candidate = ThemeCandidate(
        theme_id=f"theme_candidate:{reading_id}:{domain.value}:unknown",
        reading_id=reading_id,
        domain=domain,
        theme_name="unknown",
        theme_type=ThemeType.UNKNOWN,
        strength=0.0,
        stability=ThemeStability.UNKNOWN,
        timing_sensitivity=ThemeSensitivity.HIGH,
        active_now=None,
        evidence_refs=_unique(evidence_refs),
        theory_refs=theory_refs,
        uncertainty=profile,
        completeness=ThemeCompleteness.WEAK,
    )
    if not base_candidates:
        base_candidates = [unknown_candidate]
    if not candidates:
        candidates = [unknown_candidate]
    primary = candidates[0]
    secondary = candidates[1:4]
    counter = [candidate for candidate in candidates[1:] if _is_counter_theme(primary.theme_type, candidate.theme_type)][:2]
    conflicts = [f"{primary.theme_type.value}_vs_{candidate.theme_type.value}" for candidate in counter]
    base_theme = _base_theme_from_candidate(base_candidates[0])
    active_theme = _build_active_theme(
        reading_id=reading_id,
        domain=domain,
        timing_evolution=timing_evolution,
        state_dimensions=state_dimensions,
        evidence_refs=evidence_refs,
        theory_refs=theory_refs,
    )
    transition = _theme_transition(
        reading_id=reading_id,
        domain=domain,
        base_theme=base_theme,
        active_theme=active_theme,
        evidence_refs=_unique([*evidence_refs, *base_theme.evidence_refs, *active_theme.evidence_refs]),
    )
    return UnifiedThemeBundle(
        bundle_id=f"unified_theme_bundle:{reading_id}:{domain.value}",
        reading_id=reading_id,
        domain=domain,
        base_theme=base_theme,
        active_theme=active_theme,
        theme_transition=transition,
        primary_theme=primary,
        secondary_themes=secondary,
        counter_themes=counter,
        theme_conflicts=conflicts,
        evidence_refs=_unique([*evidence_refs, *[ref for candidate in candidates for ref in candidate.evidence_refs]]),
        theory_refs=theory_refs,
        uncertainty=profile,
        missing_theme_inputs=missing_inputs,
    )


def _base_theme_from_candidate(candidate: ThemeCandidate) -> BaseTheme:
    return BaseTheme(
        theme_id=f"base_theme:{candidate.reading_id}:{candidate.domain.value}:{candidate.theme_type.value}",
        reading_id=candidate.reading_id,
        domain=candidate.domain,
        theme_type=candidate.theme_type,
        strength=candidate.strength,
        stability=candidate.stability,
        source_mechanism_refs=list(candidate.source_mechanism_refs),
        source_state_refs=list(candidate.source_state_dimension_refs),
        evidence_refs=list(candidate.evidence_refs),
        uncertainty=candidate.uncertainty,
    )


def _build_active_theme(
    *,
    reading_id: str,
    domain: Topic,
    timing_evolution: TimingStateEvolution | None,
    state_dimensions: list[StateDimension],
    evidence_refs: list[str],
    theory_refs: list[str],
) -> ActiveTheme:
    if timing_evolution is None or not timing_evolution.domain_supported:
        return _unknown_active_theme(
            reading_id=reading_id,
            domain=domain,
            evidence_refs=evidence_refs,
            reasons=["missing_or_unsupported_timing_evolution"],
        )
    signals = _timing_theme_signals(
        strategy=timing_evolution.strategy_bias.value.value,
        timing_evolution=timing_evolution,
    )
    scores: dict[ThemeType, float] = defaultdict(float)
    for theme_type, weight, _reason in signals:
        scores[theme_type] += weight
    if not scores:
        return _unknown_active_theme(
            reading_id=reading_id,
            domain=domain,
            evidence_refs=timing_evolution.evidence_refs,
            reasons=["timing_has_no_theme_activation_signal"],
        )
    theme_type, strength = sorted(scores.items(), key=lambda item: (-item[1], item[0].value))[0]
    if strength < 0.14:
        return _unknown_active_theme(
            reading_id=reading_id,
            domain=domain,
            evidence_refs=timing_evolution.evidence_refs,
            reasons=["timing_theme_activation_below_existing_signal_floor"],
        )
    refs = _unique([*timing_evolution.evidence_refs, *[ref for item in timing_evolution.activated_state_dimensions for ref in item.evidence_refs], *[ref for item in timing_evolution.weakened_state_dimensions for ref in item.evidence_refs]])
    activation_source = _activation_source(timing_evolution)
    uncertainty = _uncertainty_profile(refs, timing_evolution.missing_inputs or ["active_theme_is_timing_directional"])
    return ActiveTheme(
        theme_id=f"active_theme:{reading_id}:{domain.value}:{theme_type.value}",
        reading_id=reading_id,
        domain=domain,
        theme_type=theme_type,
        activation_source=activation_source,
        activation_strength=round(min(1.0, strength), 3),
        active_now=True,
        opportunity_link=_dimension_ids(state_dimensions, {"opportunity", "earning_capacity", "output_drive", "wealth_path", "career_direction"}),
        risk_link=_dimension_ids(state_dimensions, {"risk", "authority_pressure", "competition_or_leakage", "volatility"}),
        strategy_link=timing_evolution.strategy_bias.value.value,
        source_timing_refs=[timing_evolution.evolution_id, *refs],
        evidence_refs=refs,
        uncertainty=uncertainty,
    )


def _unknown_active_theme(*, reading_id: str, domain: Topic, evidence_refs: list[str], reasons: list[str]) -> ActiveTheme:
    refs = _unique(evidence_refs)
    return ActiveTheme(
        theme_id=f"active_theme:{reading_id}:{domain.value}:unknown",
        reading_id=reading_id,
        domain=domain,
        theme_type=ThemeType.UNKNOWN,
        activation_source=ThemeActivationSource.UNKNOWN,
        activation_strength=0.0,
        active_now=False,
        source_timing_refs=[],
        evidence_refs=refs,
        uncertainty=_uncertainty_profile(refs, reasons),
    )


def _activation_source(timing_evolution: TimingStateEvolution) -> ThemeActivationSource:
    if timing_evolution.month is not None:
        return ThemeActivationSource.MONTH
    if timing_evolution.year is not None:
        return ThemeActivationSource.YEAR
    if timing_evolution.luck is not None:
        return ThemeActivationSource.LUCK
    if timing_evolution.activated_state_dimensions or timing_evolution.weakened_state_dimensions:
        return ThemeActivationSource.STATE_DELTA
    return ThemeActivationSource.TIMING_STATE


def _theme_transition(
    *,
    reading_id: str,
    domain: Topic,
    base_theme: BaseTheme,
    active_theme: ActiveTheme,
    evidence_refs: list[str],
) -> ThemeTransition:
    if active_theme.theme_type == ThemeType.UNKNOWN:
        transition_type = ThemeTransitionType.UNKNOWN
        reason = "active_theme_unknown_or_timing_evidence_insufficient"
    elif active_theme.theme_type == base_theme.theme_type:
        transition_type = ThemeTransitionType.STABLE
        reason = "timing_reinforces_base_theme"
    elif active_theme.theme_type == ThemeType.RISK_CONTROL:
        transition_type = ThemeTransitionType.RISK_SHIFT
        reason = "timing_activates_risk_control"
    elif active_theme.theme_type in {ThemeType.CREATION, ThemeType.ACCUMULATION}:
        transition_type = ThemeTransitionType.OPPORTUNITY_SHIFT
        reason = "timing_activates_opportunity_or_accumulation"
    elif active_theme.theme_type in {ThemeType.COMPETITION, ThemeType.PRESSURE_TRANSFORMATION}:
        transition_type = ThemeTransitionType.CONFLICT_SHIFT
        reason = "timing_activates_conflict_or_pressure"
    else:
        transition_type = ThemeTransitionType.TIMING_ACTIVATED
        reason = "timing_activates_non_base_theme"
    return ThemeTransition(
        transition_id=f"theme_transition:{reading_id}:{domain.value}",
        reading_id=reading_id,
        domain=domain,
        base_theme=base_theme,
        active_theme=active_theme,
        transition_type=transition_type,
        reason=reason,
        evidence_refs=_unique(evidence_refs),
    )


def discover_unified_theme(
    *,
    reading_id: str,
    domain: Topic,
    flow_state: FlowState | None = None,
    palace_state_space: PalaceStateSpace | None = None,
    reality_state: RealityState | None = None,
    temporal_state: TemporalState | None = None,
    state_evolution: StateEvolution | None = None,
) -> UnifiedTheme:
    """Discover a cross-producer theme without creating a judgment."""

    states = [flow_state, palace_state_space, reality_state, temporal_state, state_evolution]
    if not any(states):
        raise ValueError("Unified Theme Discovery requires at least one state producer")
    for state in states:
        if state is None:
            continue
        if state.reading_id != reading_id:
            raise ValueError("Unified Theme Discovery cannot mix readings")
        state_domain = getattr(state, "domain", domain)
        if state_domain != domain:
            raise ValueError("Unified Theme Discovery cannot mix domains")

    theme_code = _theme_code(
        domain=domain,
        flow_state=flow_state,
        palace_state_space=palace_state_space,
        reality_state=reality_state,
        temporal_state=temporal_state,
        state_evolution=state_evolution,
    )
    state_refs = _state_refs(states)
    evidence_refs = _evidence_refs(states)
    producer_refs = _producer_refs(
        flow_state=flow_state,
        palace_state_space=palace_state_space,
        reality_state=reality_state,
        temporal_state=temporal_state,
        state_evolution=state_evolution,
    )
    strength = _theme_strength(
        flow_state=flow_state,
        palace_state_space=palace_state_space,
        reality_state=reality_state,
        temporal_state=temporal_state,
        state_evolution=state_evolution,
    )

    return UnifiedTheme(
        theme_id=f"unified_theme:{reading_id}:{domain.value}:{theme_code}",
        reading_id=reading_id,
        domain=domain,
        theme_code=theme_code,
        strength=strength,
        producer_refs=producer_refs,
        state_refs=state_refs,
        evidence_refs=evidence_refs,
        confidence=strength,
    )


def _collect_theme_signals(
    *,
    domain: Topic,
    mechanism_ast: list[dict[str, Any]],
    state_dimensions: list[StateDimension],
    timing_evolution: TimingStateEvolution | None,
) -> dict[ThemeType, dict[str, Any]]:
    signals: dict[ThemeType, dict[str, Any]] = defaultdict(lambda: {"score": 0.0, "reasons": set(), "state_refs": set(), "mechanism_refs": set(), "timing_refs": set(), "evidence_refs": set()})
    for ast in mechanism_ast:
        mechanism_ref = str(ast.get("representation_id") or ast.get("mechanism_code") or "mechanism.unknown")
        ast_evidence = set(str(ref) for ref in _as_list(ast.get("evidence_refs")))
        roles = {str(component.get("role", "")) for component in _as_list(ast.get("components")) if isinstance(component, dict)}
        mechanism_code = str(ast.get("mechanism_code", ""))
        for theme_type, weight, reason in _mechanism_theme_signals(mechanism_code=mechanism_code, roles=roles):
            _add_signal(signals, theme_type, weight, reason, mechanism_ref, "", "", ast_evidence)
    for dimension in state_dimensions:
        for theme_type, weight, reason in _state_dimension_theme_signals(dimension):
            _add_signal(signals, theme_type, weight, reason, "", dimension.dimension_id, "", set(dimension.evidence_refs))
    if timing_evolution is not None and timing_evolution.domain_supported:
        strategy = timing_evolution.strategy_bias.value.value
        timing_ref = timing_evolution.evolution_id
        timing_evidence = set(timing_evolution.evidence_refs)
        for theme_type, weight, reason in _timing_theme_signals(strategy=strategy, timing_evolution=timing_evolution):
            _add_signal(signals, theme_type, weight, reason, "", "", timing_ref, timing_evidence)
    return signals


def _build_candidates(
    *,
    reading_id: str,
    domain: Topic,
    signals: dict[ThemeType, dict[str, Any]],
    mechanism_ast: list[dict[str, Any]],
    state_dimensions: list[StateDimension],
    timing_evolution: TimingStateEvolution | None,
    evidence_refs: list[str],
    theory_refs: list[str],
) -> list[ThemeCandidate]:
    candidates: list[ThemeCandidate] = []
    evidence_density = min(0.14, len(set(evidence_refs)) / 100)
    conflict_penalty = 0.06 if len(signals) >= 5 else 0.0
    all_mechanism_refs = _unique([str(ast.get("representation_id") or ast.get("mechanism_code") or "") for ast in mechanism_ast])
    all_state_refs = [dimension.dimension_id for dimension in state_dimensions]
    for theme_type, signal in signals.items():
        if theme_type == ThemeType.UNKNOWN:
            continue
        score = min(1.0, max(0.0, signal["score"] + _theme_domain_bonus(domain, theme_type) + evidence_density - conflict_penalty))
        if score < 0.18:
            continue
        source_mechanism_refs = sorted(signal["mechanism_refs"]) or all_mechanism_refs
        source_state_refs = sorted(signal["state_refs"]) or all_state_refs
        timing_refs = sorted(signal["timing_refs"])
        theme_evidence = _unique([*evidence_refs, *signal["evidence_refs"]])
        missing = []
        if not source_mechanism_refs:
            missing.append("missing_mechanism_signal")
        if not source_state_refs:
            missing.append("missing_state_signal")
        if timing_evolution is None or not timing_refs:
            missing.append("weak_timing")
        completeness = _completeness(missing)
        candidates.append(
            ThemeCandidate(
                theme_id=f"theme_candidate:{reading_id}:{domain.value}:{theme_type.value}",
                reading_id=reading_id,
                domain=domain,
                theme_name=theme_type.value,
                theme_type=theme_type,
                strength=round(score, 3),
                stability=_stability(theme_type=theme_type, timing_evolution=timing_evolution),
                timing_sensitivity=_timing_sensitivity(timing_refs=timing_refs, timing_evolution=timing_evolution),
                active_now=bool(timing_refs) if timing_evolution is not None else None,
                opportunity_link=_dimension_ids(state_dimensions, {"opportunity", "earning_capacity", "output_drive", "wealth_path", "career_direction"}),
                risk_link=_dimension_ids(state_dimensions, {"risk", "authority_pressure", "competition_or_leakage", "volatility"}),
                strategy_link=timing_evolution.strategy_bias.value.value if timing_evolution is not None else "unknown",
                source_mechanism_refs=source_mechanism_refs,
                source_state_dimension_refs=source_state_refs,
                source_timing_refs=timing_refs,
                evidence_refs=theme_evidence,
                theory_refs=theory_refs,
                counter_theme="",
                uncertainty=_uncertainty_profile(theme_evidence, missing or ["theme_discovery_directional"]),
                completeness=completeness,
            )
        )
    return sorted(candidates, key=lambda candidate: candidate.strength, reverse=True)


def _mechanism_theme_signals(*, mechanism_code: str, roles: set[str]) -> list[tuple[ThemeType, float, str]]:
    signals: list[tuple[ThemeType, float, str]] = []
    if "converter" in roles:
        signals.append((ThemeType.CREATION, 0.22, "converter_signal"))
    if "bridge" in roles:
        signals.append((ThemeType.MOBILITY, 0.18, "bridge_signal"))
    if "anchor" in roles:
        signals.append((ThemeType.STABILITY, 0.18, "anchor_signal"))
    if "counter_force" in roles:
        signals.append((ThemeType.PRESSURE_TRANSFORMATION, 0.2, "counter_force_signal"))
    if mechanism_code == "output_to_wealth":
        signals.extend([(ThemeType.CREATION, 0.18, "output_to_wealth"), (ThemeType.ACCUMULATION, 0.16, "output_to_wealth")])
    elif mechanism_code == "output_controls_pressure":
        signals.extend([(ThemeType.PRESSURE_TRANSFORMATION, 0.22, "output_controls_pressure"), (ThemeType.RISK_CONTROL, 0.12, "output_controls_pressure")])
    elif mechanism_code == "peer_competes_for_wealth":
        signals.extend([(ThemeType.COMPETITION, 0.24, "peer_competes_for_wealth"), (ThemeType.RISK_CONTROL, 0.12, "peer_competes_for_wealth")])
    elif mechanism_code == "officer_pressure":
        signals.extend([(ThemeType.MANAGEMENT, 0.2, "officer_pressure"), (ThemeType.PRESSURE_TRANSFORMATION, 0.18, "officer_pressure")])
    elif mechanism_code == "resource_support":
        signals.append((ThemeType.RESOURCE_SUPPORT, 0.22, "resource_support"))
    elif mechanism_code == "branch_relation_movement":
        signals.append((ThemeType.MOBILITY, 0.24, "branch_relation_movement"))
    return signals


def _theme_domain_bonus(domain: Topic, theme_type: ThemeType) -> float:
    if domain == Topic.WEALTH and theme_type == ThemeType.ACCUMULATION:
        return 0.12
    if domain == Topic.CAREER and theme_type == ThemeType.MANAGEMENT:
        return 0.08
    if theme_type == ThemeType.RESOURCE_SUPPORT:
        return 0.06
    if theme_type == ThemeType.MOBILITY:
        return 0.04
    return 0.0


def _state_dimension_theme_signals(dimension: StateDimension) -> list[tuple[ThemeType, float, str]]:
    name = dimension.name
    score = max(0.06, dimension.score * 0.2)
    mapping = {
        "output_drive": ThemeType.CREATION,
        "career_direction": ThemeType.MANAGEMENT,
        "earning_capacity": ThemeType.CREATION,
        "wealth_path": ThemeType.ACCUMULATION,
        "accumulation_capacity": ThemeType.ACCUMULATION,
        "authority_pressure": ThemeType.PRESSURE_TRANSFORMATION,
        "pressure_handling": ThemeType.PRESSURE_TRANSFORMATION,
        "risk": ThemeType.RISK_CONTROL,
        "competition_or_leakage": ThemeType.COMPETITION,
        "volatility": ThemeType.RISK_CONTROL,
        "mobility": ThemeType.MOBILITY,
        "stability": ThemeType.STABILITY,
        "opportunity": ThemeType.CREATION,
    }
    theme_type = mapping.get(name)
    return [(theme_type, score, f"state_dimension:{name}")] if theme_type is not None else []


def _timing_theme_signals(*, strategy: str, timing_evolution: TimingStateEvolution) -> list[tuple[ThemeType, float, str]]:
    signals: list[tuple[ThemeType, float, str]] = []
    if strategy == "advance":
        signals.append((ThemeType.CREATION, 0.16, "strategy:advance"))
    elif strategy == "accumulate":
        signals.append((ThemeType.ACCUMULATION, 0.18, "strategy:accumulate"))
    elif strategy == "reduce_risk":
        signals.append((ThemeType.RISK_CONTROL, 0.2, "strategy:reduce_risk"))
    elif strategy == "hold":
        signals.append((ThemeType.STABILITY, 0.14, "strategy:hold"))
    if timing_evolution.risk_windows:
        month_bonus = 0.08 if timing_evolution.month is not None else 0.0
        signals.append((ThemeType.RISK_CONTROL, 0.14 + month_bonus, "timing:risk_window"))
    if timing_evolution.opportunity_windows:
        month_bonus = 0.06 if timing_evolution.month is not None else 0.0
        signals.append((ThemeType.CREATION, 0.14 + month_bonus, "timing:opportunity_window"))
    if timing_evolution.weakened_state_dimensions:
        signals.append((ThemeType.PRESSURE_TRANSFORMATION, 0.1, "timing:weakened_dimension"))
    return signals


def _add_signal(
    signals: dict[ThemeType, dict[str, Any]],
    theme_type: ThemeType,
    weight: float,
    reason: str,
    mechanism_ref: str,
    state_ref: str,
    timing_ref: str,
    evidence_refs: set[str],
) -> None:
    item = signals[theme_type]
    item["score"] += weight
    item["reasons"].add(reason)
    if mechanism_ref:
        item["mechanism_refs"].add(mechanism_ref)
    if state_ref:
        item["state_refs"].add(state_ref)
    if timing_ref:
        item["timing_refs"].add(timing_ref)
    item["evidence_refs"].update(evidence_refs)


def _stability(*, theme_type: ThemeType, timing_evolution: TimingStateEvolution | None) -> ThemeStability:
    if timing_evolution is None:
        return ThemeStability.UNKNOWN
    if theme_type in {ThemeType.RISK_CONTROL, ThemeType.MOBILITY, ThemeType.PRESSURE_TRANSFORMATION}:
        return ThemeStability.TIMING_SENSITIVE
    if timing_evolution.strategy_bias.value.value in {"wait", "reduce_risk"}:
        return ThemeStability.TIMING_SENSITIVE
    return ThemeStability.STABLE


def _timing_sensitivity(*, timing_refs: list[str], timing_evolution: TimingStateEvolution | None) -> ThemeSensitivity:
    if timing_evolution is None:
        return ThemeSensitivity.HIGH
    if timing_refs and timing_evolution.risk_windows:
        return ThemeSensitivity.HIGH
    if timing_refs:
        return ThemeSensitivity.MEDIUM
    return ThemeSensitivity.LOW


def _completeness(missing: list[str]) -> ThemeCompleteness:
    if not missing:
        return ThemeCompleteness.COMPLETE
    if len(missing) == 1:
        return ThemeCompleteness.PARTIAL
    return ThemeCompleteness.WEAK


def _missing_theme_inputs(*, mechanism_ast: list[dict[str, Any]], state_dimensions: list[StateDimension], timing_evolution: TimingStateEvolution | None) -> list[str]:
    missing = []
    if not mechanism_ast:
        missing.append("missing_mechanism_ast")
    if not state_dimensions:
        missing.append("missing_state_dimensions")
    if timing_evolution is None:
        missing.append("missing_timing_evolution")
    elif timing_evolution.missing_inputs:
        missing.extend(timing_evolution.missing_inputs)
    return _unique(missing)


def _is_counter_theme(primary: ThemeType, candidate: ThemeType) -> bool:
    pairs = {
        (ThemeType.CREATION, ThemeType.RISK_CONTROL),
        (ThemeType.ACCUMULATION, ThemeType.COMPETITION),
        (ThemeType.STABILITY, ThemeType.MOBILITY),
        (ThemeType.PRESSURE_TRANSFORMATION, ThemeType.RESOURCE_SUPPORT),
    }
    return (primary, candidate) in pairs or (candidate, primary) in pairs


def _dimension_ids(dimensions: list[StateDimension], names: set[str]) -> list[str]:
    return [dimension.dimension_id for dimension in dimensions if dimension.name in names]


def _uncertainty_profile(evidence_refs: list[str], reasons: list[str]) -> UncertaintyProfile:
    level = UncertaintyLevel.MEDIUM if reasons else UncertaintyLevel.LOW
    if any(reason.startswith("missing") or reason.startswith("no_") for reason in reasons):
        level = UncertaintyLevel.HIGH if len(reasons) >= 2 else UncertaintyLevel.MEDIUM
    return UncertaintyProfile(level=level, reasons=reasons or ["theme_discovery_directional"], evidence_refs=_unique(evidence_refs))


def _theme_code(
    *,
    domain: Topic,
    flow_state: FlowState | None,
    palace_state_space: PalaceStateSpace | None,
    reality_state: RealityState | None,
    temporal_state: TemporalState | None,
    state_evolution: StateEvolution | None,
) -> str:
    mechanism = flow_state.mechanism if flow_state else ""
    dimensions = palace_state_space.dimensions if palace_state_space else {}
    has_timing_pressure = bool(
        temporal_state
        and (temporal_state.weakened_nodes or temporal_state.rerouted_flows)
    ) or bool(state_evolution and state_evolution.suppressed_by)
    living_abroad = bool(reality_state and reality_state.geography.get("living_abroad"))

    if domain == Topic.CAREER and mechanism == "output_controls_pressure":
        if dimensions.get("pressure", 0.0) >= 0.65 or has_timing_pressure:
            return "career_output_under_structural_pressure"
        return "career_output_control_theme"
    if domain == Topic.WEALTH and mechanism == "output_to_wealth":
        if living_abroad:
            return "wealth_from_output_with_cross_border_context"
        return "wealth_from_output_conversion"
    if domain == Topic.WEALTH and mechanism == "peer_competes_for_wealth":
        return "wealth_competition_and_resource_division"
    if living_abroad and domain in {Topic.CAREER, Topic.MIGRATION}:
        return "cross_border_mobility_theme"
    if has_timing_pressure:
        return f"{domain.value}_timing_pressure_theme"
    return f"{domain.value}_mixed_or_unclear_theme"


def _theme_strength(
    *,
    flow_state: FlowState | None,
    palace_state_space: PalaceStateSpace | None,
    reality_state: RealityState | None,
    temporal_state: TemporalState | None,
    state_evolution: StateEvolution | None,
) -> float:
    values: list[float] = []
    if flow_state is not None:
        values.extend([flow_state.output_strength, flow_state.path_score, flow_state.confidence])
    if palace_state_space is not None:
        values.extend(palace_state_space.dimensions.values())
        values.append(palace_state_space.confidence)
    if reality_state is not None:
        values.append(reality_state.confidence)
    if temporal_state is not None:
        values.append(temporal_state.confidence)
    if state_evolution is not None:
        values.extend(abs(value) for value in state_evolution.delta_by_dimension.values())
        values.append(state_evolution.confidence)
    if not values:
        return 0.0
    return round(max(0.0, min(1.0, mean(values))), 3)


def _producer_refs(
    *,
    flow_state: FlowState | None,
    palace_state_space: PalaceStateSpace | None,
    reality_state: RealityState | None,
    temporal_state: TemporalState | None,
    state_evolution: StateEvolution | None,
) -> list[str]:
    refs: list[str] = []
    if flow_state is not None:
        refs.append("producer.bazi_flow")
    if palace_state_space is not None:
        refs.append("producer.ziwei_palace")
    if reality_state is not None:
        refs.append("producer.context_reality")
    if temporal_state is not None:
        refs.append("producer.timing_temporal")
    if state_evolution is not None:
        refs.append("producer.state_evolution")
    return refs


def _state_refs(states: list[object | None]) -> list[str]:
    refs = [getattr(state, "state_id", getattr(state, "evolution_id", "")) for state in states if state is not None]
    return _unique(refs)


def _evidence_refs(states: list[object | None]) -> list[str]:
    refs: list[str] = []
    for state in states:
        if state is not None:
            refs.extend(getattr(state, "evidence_refs", []))
    return _unique(refs)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _unique(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result
