from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from v30.contracts import BirthInput
from v30.core.chart_context import build_chart_context_from_birth_input
from v30.hidden_factor import HiddenFactorCalibration, build_hidden_factor_state, hidden_factor_feedback_from_payload
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_runtime_from_context
from v30.validation.synthetic_case import SyntheticValidationResult, SyntheticValidationSuiteResult


LATENT_BAZI_DIVERGENCE_VERSION = "v30.synthetic.latent_bazi_divergence.v1"

BASE_BIRTH_INPUT: dict[str, Any] = {
    "input_id": "latent-divergence-same-bazi",
    "calendar_type": "solar",
    "birth_date": "1990-02-04",
    "birth_time": "23:30",
    "timezone": "Asia/Shanghai",
    "gender": "male",
}

LATENT_DIVERGENCE_CASES: tuple[dict[str, Any], ...] = (
    {
        "case_id": "v30.synthetic.latent_bazi_divergence.career_vs_wealth_001",
        "left": {
            "label": "career_pressure",
            "state_tag": "career_pressure",
            "selected_option": "domain:career",
            "years": [2021, 2024],
            "expected_active_domain": "career_bias",
            "expected_active_global": "resource_index",
            "expected_active_family": "authority",
        },
        "right": {
            "label": "wealth_fluctuation",
            "state_tag": "wealth_fluctuation",
            "selected_option": "domain:wealth",
            "years": [2020, 2023],
            "expected_active_domain": "wealth_bias",
            "expected_active_global": "risk_index",
            "expected_active_family": "wealth",
        },
    },
    {
        "case_id": "v30.synthetic.latent_bazi_divergence.career_vs_relationship_001",
        "left": {
            "label": "career_pressure",
            "state_tag": "career_pressure",
            "selected_option": "domain:career",
            "years": [2021, 2024],
            "expected_active_domain": "career_bias",
            "expected_active_global": "resource_index",
            "expected_active_family": "resource",
        },
        "right": {
            "label": "relationship_repetition",
            "state_tag": "relationship_repetition",
            "selected_option": "domain:relationship",
            "years": [2019, 2022],
            "expected_active_domain": "relationship_bias",
            "expected_active_global": "risk_index",
            "expected_active_family": "authority",
        },
    },
)


def run_latent_bazi_divergence_synthetic_suite() -> SyntheticValidationSuiteResult:
    results = [run_latent_bazi_divergence_case(row) for row in LATENT_DIVERGENCE_CASES]
    passed_count = sum(1 for row in results if row.passed)
    failed_count = len(results) - passed_count
    return SyntheticValidationSuiteResult(
        suite_id="v30.synthetic.latent_bazi_divergence",
        passed=failed_count == 0,
        case_count=len(results),
        passed_count=passed_count,
        failed_count=failed_count,
        results=results,
    )


def run_latent_bazi_divergence_case(case: Mapping[str, Any]) -> SyntheticValidationResult:
    base_runtime, chart_build = _base_runtime(str(case.get("case_id") or "latent-divergence"))
    base_chart_fingerprint = _chart_fact_fingerprint(base_runtime, chart_build)
    base_model_fingerprint = _base_model_fingerprint(base_runtime)
    left = _runtime_with_latent_state(base_runtime, _mapping(case.get("left")))
    right = _runtime_with_latent_state(base_runtime, _mapping(case.get("right")))
    left_observed = _variant_observation(left, _mapping(case.get("left")))
    right_observed = _variant_observation(right, _mapping(case.get("right")))

    failures: list[str] = []
    for side, runtime in (("left", left), ("right", right)):
        if _chart_fact_fingerprint(runtime, chart_build) != base_chart_fingerprint:
            failures.append(f"{side}_chart_fact_changed")
        if _base_model_fingerprint(runtime) != base_model_fingerprint:
            failures.append(f"{side}_base_model_changed")
        attrs = _mapping(runtime.question_plan.policy_effect.get("latent_bazi_attributes"))
        projection = _mapping(runtime.question_plan.policy_effect.get("latent_bazi_individualized_projection"))
        if attrs.get("status") != "inferred":
            failures.append(f"{side}_latent_attributes_not_inferred")
        if projection.get("individualization_ready") is not True:
            failures.append(f"{side}_projection_not_ready")
        if projection.get("chart_fact_mutation_allowed") is not False:
            failures.append(f"{side}_projection_allows_chart_fact_mutation")
        if projection.get("base_ten_god_energy_mutation_allowed") is not False:
            failures.append(f"{side}_projection_allows_base_energy_mutation")
        if projection.get("ranked_decision_mutation_allowed") is not False:
            failures.append(f"{side}_projection_allows_ranked_decision_mutation")

    if left_observed["latent_attribute_fingerprint"] == right_observed["latent_attribute_fingerprint"]:
        failures.append("latent_attribute_fingerprints_not_divergent")
    if left_observed["projection_fingerprint"] == right_observed["projection_fingerprint"]:
        failures.append("individualized_projection_fingerprints_not_divergent")
    if not left_observed["expected_domain_active"]:
        failures.append("left_expected_domain_not_active")
    if not right_observed["expected_domain_active"]:
        failures.append("right_expected_domain_not_active")
    if not left_observed["expected_family_active"]:
        failures.append("left_expected_family_not_active")
    if not right_observed["expected_family_active"]:
        failures.append("right_expected_family_not_active")

    return SyntheticValidationResult(
        case_id=str(case.get("case_id") or ""),
        passed=not failures,
        failures=failures,
        observed={
            "version": LATENT_BAZI_DIVERGENCE_VERSION,
            "chart_facts_stable": _chart_fact_fingerprint(left, chart_build) == base_chart_fingerprint
            and _chart_fact_fingerprint(right, chart_build) == base_chart_fingerprint,
            "base_model_stable": _base_model_fingerprint(left) == base_model_fingerprint
            and _base_model_fingerprint(right) == base_model_fingerprint,
            "latent_attributes_diverged": left_observed["latent_attribute_fingerprint"] != right_observed["latent_attribute_fingerprint"],
            "individualized_projection_diverged": left_observed["projection_fingerprint"] != right_observed["projection_fingerprint"],
            "base_chart_fingerprint": base_chart_fingerprint,
            "base_model_fingerprint": base_model_fingerprint,
            "left": left_observed,
            "right": right_observed,
            "training_routes": ["latent_attribute_inference", "question_strategy", "individualized_projection"],
            "blocked_training_routes": ["chart_facts", "calendar_conversion", "luck_cycle", "flow_timing"],
            "boundary": "same_bazi_latent_divergence_validates_personalization_without_chart_fact_mutation",
        },
    )


def _base_runtime(reading_id: str):
    build = build_chart_context_from_birth_input(
        reading_id=reading_id,
        birth_input=BirthInput.model_validate(BASE_BIRTH_INPUT),
    )
    if build.chart_context is None:
        raise RuntimeError(f"latent divergence base chart build failed: {build.four_pillar_result.status}")
    runtime = create_runtime_from_context(build.chart_context, trace_suffix="latent-divergence")
    return runtime, build.four_pillar_result.model_dump(mode="json")


def _runtime_with_latent_state(base_runtime, spec: Mapping[str, Any]):
    state_tag = str(spec.get("state_tag") or "")
    years = [int(row) for row in spec.get("years", []) if isinstance(row, int)]
    answered = attach_question_outcome(
        base_runtime,
        "q_v30_hidden_factor_boundary_discovery",
        {
            "answer": f"{state_tag} repeated in {', '.join(str(row) for row in years)}.",
            "selected_option": str(spec.get("selected_option") or ""),
            "structured_payload": {
                "years": years,
                "state_tags": [state_tag],
                "intensity": "strong",
                "recurrence": "repeated",
                "confidence": "certain",
            },
            "feedback_tags": ["structured_hidden_factor", state_tag],
            "confidence": 0.86,
        },
    )
    feedback = hidden_factor_feedback_from_payload(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        payload={
            "feedback_id": f"{answered.reading_id}:latent-divergence:{state_tag}",
            "special_event_years": years,
            "repeated_states": [state_tag],
            "feedback_status": "confirmed",
        },
    )
    state = build_hidden_factor_state(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        calibration=HiddenFactorCalibration.model_validate(
            answered.question_plan.policy_effect["hidden_factor_calibration"]
        ),
        feedback=[feedback],
    )
    return attach_hidden_factor_state(answered, state.model_dump(mode="json"))


def _variant_observation(runtime, spec: Mapping[str, Any]) -> dict[str, Any]:
    attrs = _mapping(runtime.question_plan.policy_effect.get("latent_bazi_attributes"))
    summary = _mapping(runtime.question_plan.policy_effect.get("latent_bazi_attributes_summary"))
    projection = _mapping(runtime.question_plan.policy_effect.get("latent_bazi_individualized_projection"))
    projection_summary = _mapping(runtime.question_plan.policy_effect.get("latent_bazi_individualized_projection_summary"))
    active_domains = set(str(row) for row in summary.get("active_domain_biases", []) if isinstance(row, str))
    active_globals = set(str(row) for row in summary.get("active_global_attributes", []) if isinstance(row, str))
    active_families = set(str(row) for row in summary.get("active_ten_god_modifiers", []) if isinstance(row, str))
    return {
        "label": str(spec.get("label") or ""),
        "state_tag": str(spec.get("state_tag") or ""),
        "status": str(attrs.get("status") or ""),
        "active_global_attributes": sorted(active_globals),
        "active_ten_god_modifiers": sorted(active_families),
        "active_domain_biases": sorted(active_domains),
        "adjusted_families": list(projection_summary.get("adjusted_families", [])),
        "adjusted_domains": list(projection_summary.get("adjusted_domains", [])),
        "expected_domain_active": str(spec.get("expected_active_domain") or "") in active_domains,
        "expected_global_active": str(spec.get("expected_active_global") or "") in active_globals,
        "expected_family_active": str(spec.get("expected_active_family") or "") in active_families,
        "latent_attribute_fingerprint": _latent_attribute_fingerprint(attrs),
        "projection_fingerprint": _projection_fingerprint(projection),
        "chart_fact_mutation_allowed": bool(attrs.get("chart_fact_mutation_allowed")),
        "individualization_ready": bool(projection.get("individualization_ready")),
    }


def _chart_fact_fingerprint(runtime, chart_build: Mapping[str, Any]) -> dict[str, Any]:
    chart = runtime.chart_context
    source = _mapping(chart.input_pillars.get("chart_build_source"))
    six = _mapping(chart.time_layers.get("six_pillar_context"))
    return {
        "day_master": chart.day_master,
        "day_master_element": chart.day_master_element,
        "input_pillars": deepcopy(chart.input_pillars),
        "natal_pillars": deepcopy(chart.natal_pillars),
        "chart_build_status": source.get("status"),
        "chart_build_source_type": source.get("source_type"),
        "chart_build_pillars": deepcopy(_mapping(chart_build.get("pillars"))),
        "six_pillar_status": six.get("status"),
        "six_pillars": deepcopy(six.get("pillars")),
    }


def _base_model_fingerprint(runtime) -> dict[str, Any]:
    policy = runtime.question_plan.policy_effect
    return {
        "ten_god_energy_model": deepcopy(policy.get("ten_god_energy_model")),
        "ten_god_energy_summary": deepcopy(policy.get("ten_god_energy_summary")),
        "ranked_decisions": deepcopy(policy.get("ranked_decisions")),
        "real_bazi_diagnosis_summary": deepcopy(_mapping(policy.get("real_bazi_diagnosis")).get("summaries")),
    }


def _latent_attribute_fingerprint(attrs: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "global_attributes": _score_map(_mapping(attrs.get("global_attributes")), "value"),
        "ten_god_modifiers": _score_map(_mapping(attrs.get("ten_god_modifiers")), "multiplier"),
        "domain_biases": _score_map(_mapping(attrs.get("domain_biases")), "value"),
        "stability_thresholds": _score_map(_mapping(attrs.get("stability_thresholds")), "value"),
    }


def _projection_fingerprint(projection: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "family_energy_projection": [
            {
                "family": str(row.get("family") or ""),
                "latent_multiplier": _round(row.get("latent_multiplier"), default=1.0),
                "adjusted_energy": _round(row.get("adjusted_energy"), default=0.0),
            }
            for row in _list(projection.get("family_energy_projection"))
        ],
        "domain_path_projection": [
            {
                "domain": str(row.get("domain") or ""),
                "latent_multiplier": _round(row.get("latent_multiplier"), default=1.0),
                "adjusted_path_score": _round(row.get("adjusted_path_score"), default=0.0),
            }
            for row in _list(projection.get("domain_path_projection"))
        ],
        "ranked_decision_projection": deepcopy(_list(projection.get("ranked_decision_projection"))),
    }


def _score_map(rows: Mapping[str, Any], score_key: str) -> dict[str, float]:
    return {
        str(key): _round(_mapping(value).get(score_key), default=1.0 if score_key == "multiplier" else 0.5)
        for key, value in sorted(rows.items(), key=lambda item: str(item[0]))
    }


def _round(value: Any, *, default: float) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []
