from __future__ import annotations

from core.contracts import Topic
from core.state import build_domain_state_enrichment, build_timing_state_evolution_v1


def _ast(*, representation_id: str, mechanism_code: str, roles: list[str]) -> dict[str, object]:
    return {
        "representation_id": representation_id,
        "reading_id": "reading.timing_state_evolution.test",
        "mechanism_code": mechanism_code,
        "components": [
            {
                "component_id": f"{representation_id}:{role}",
                "reading_id": "reading.timing_state_evolution.test",
                "role": role,
                "ref": f"node.{role}",
                "evidence_refs": [f"evidence.{role}"],
                "confidence": 0.72,
            }
            for role in roles
        ],
        "path_refs": [f"path.{representation_id}"],
        "state_delta_refs": [f"state_delta.{representation_id}"],
        "evidence_refs": [f"evidence.{representation_id}"],
        "completeness": "complete",
        "ast_shape": "+".join(sorted(roles)),
        "state_delta_status": "real",
        "confidence": 0.72,
    }


def _dimensions(topic: Topic, ast: dict[str, object]):
    enrichment = build_domain_state_enrichment(
        reading_id=f"reading.timing_state_evolution.{topic.value}",
        domain=topic,
        mechanism_ast=[ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
        timing_state={"activated_by": ["year.丙午"], "trend": "increasing"},
    )
    return enrichment.state_dimensions


def test_same_natal_different_timing_changes_state_evolution() -> None:
    ast = _ast(representation_id="m1", mechanism_code="output_to_wealth", roles=["source", "path", "converter", "anchor", "target", "state_delta"])
    dimensions = _dimensions(Topic.WEALTH, ast)
    luck_only = build_timing_state_evolution_v1(
        reading_id="reading.timing.luck_only",
        domain=Topic.WEALTH,
        state_dimensions=dimensions,
        mechanism_ast=[ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T001"],
        timing_overlays={"luck": {"model_id": "timing.luck.long_term_field.v1", "evidence_refs": ["timing.luck"], "confidence": 0.62}},
    )
    year_month = build_timing_state_evolution_v1(
        reading_id="reading.timing.year_month",
        domain=Topic.WEALTH,
        state_dimensions=dimensions,
        mechanism_ast=[ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T001"],
        timing_overlays={
            "year": {"model_id": "timing.year.activation_event.v1", "evidence_refs": ["timing.year"], "confidence": 0.66},
            "month": {"model_id": "timing.month.event_window.v1", "evidence_refs": ["timing.month"], "confidence": 0.61},
        },
    )

    assert luck_only.strategy_bias.value != year_month.strategy_bias.value or luck_only.missing_inputs != year_month.missing_inputs
    assert luck_only.luck is not None
    assert year_month.year is not None
    assert year_month.month is not None


def test_same_timing_different_natal_changes_effect() -> None:
    wealth_ast = _ast(representation_id="m2", mechanism_code="output_to_wealth", roles=["source", "path", "converter", "anchor", "target", "state_delta"])
    pressure_ast = _ast(representation_id="m3", mechanism_code="officer_pressure", roles=["source", "path", "counter_force", "target", "state_delta"])
    timing = {"year": {"model_id": "timing.year.activation_event.v1", "evidence_refs": ["timing.year"], "confidence": 0.66}}
    wealth = build_timing_state_evolution_v1(
        reading_id="reading.timing.same_timing.wealth",
        domain=Topic.WEALTH,
        state_dimensions=_dimensions(Topic.WEALTH, wealth_ast),
        mechanism_ast=[wealth_ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T001"],
        timing_overlays=timing,
    )
    career = build_timing_state_evolution_v1(
        reading_id="reading.timing.same_timing.career",
        domain=Topic.CAREER,
        state_dimensions=_dimensions(Topic.CAREER, pressure_ast),
        mechanism_ast=[pressure_ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T001"],
        timing_overlays=timing,
    )

    wealth_names = {item.dimension_name for item in wealth.activated_state_dimensions}
    career_names = {item.dimension_name for item in career.activated_state_dimensions}
    assert wealth_names != career_names


def test_timing_evolution_allows_missing_inputs_without_hard_fill() -> None:
    ast = _ast(representation_id="m4", mechanism_code="resource_support", roles=["source", "path", "anchor", "target"])
    evolution = build_timing_state_evolution_v1(
        reading_id="reading.timing.missing",
        domain=Topic.CAREER,
        state_dimensions=_dimensions(Topic.CAREER, ast),
        mechanism_ast=[ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T001"],
        timing_overlays={},
    )

    assert set(evolution.missing_inputs) == {"no_luck", "no_year", "no_month"}
    assert evolution.strategy_bias.value == "unknown"
    assert not evolution.risk_windows
    assert not evolution.opportunity_windows


def test_timing_layers_are_separate() -> None:
    ast = _ast(representation_id="m5", mechanism_code="output_controls_pressure", roles=["source", "path", "converter", "bridge", "target", "state_delta"])
    evolution = build_timing_state_evolution_v1(
        reading_id="reading.timing.layers",
        domain=Topic.CAREER,
        state_dimensions=_dimensions(Topic.CAREER, ast),
        mechanism_ast=[ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T001"],
        timing_overlays={
            "luck": {"model_id": "timing.luck.perturbation_source.v1", "evidence_refs": ["timing.luck"]},
            "year": {"model_id": "timing.year.activation_event.v1", "evidence_refs": ["timing.year"]},
            "month": {"model_id": "timing.month.event_window.v1", "evidence_refs": ["timing.month"]},
        },
    )

    assert evolution.luck is not None
    assert evolution.year is not None
    assert evolution.month is not None
    assert evolution.luck.model_candidate_ref.startswith("timing.luck.")
    assert evolution.year.model_candidate_ref.startswith("timing.year.")
    assert evolution.month.model_candidate_ref.startswith("timing.month.")


def test_unsupported_domain_does_not_create_fake_timing() -> None:
    ast = _ast(representation_id="m6", mechanism_code="output_controls_pressure", roles=["source", "path", "target"])
    evolution = build_timing_state_evolution_v1(
        reading_id="reading.timing.relationship",
        domain=Topic.RELATIONSHIP,
        state_dimensions=[],
        mechanism_ast=[ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T001"],
        timing_overlays={"year": {"model_id": "timing.year.activation_event.v1", "evidence_refs": ["timing.year"]}},
    )

    assert evolution.domain_supported is False
    assert evolution.domain_gap is True
    assert not evolution.activated_state_dimensions
    assert not evolution.risk_windows


def test_timing_state_evolution_has_evidence_refs() -> None:
    ast = _ast(representation_id="m7", mechanism_code="peer_competes_for_wealth", roles=["source", "path", "bridge", "counter_force", "target", "state_delta"])
    evolution = build_timing_state_evolution_v1(
        reading_id="reading.timing.evidence",
        domain=Topic.WEALTH,
        state_dimensions=_dimensions(Topic.WEALTH, ast),
        mechanism_ast=[ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T001"],
        timing_overlays={"year": {"model_id": "timing.year.activation_event.v1", "evidence_refs": ["timing.year"], "confidence": 0.66}},
    )

    assert evolution.evidence_refs
    assert evolution.activated_state_dimensions
    for item in [*evolution.activated_state_dimensions, *evolution.weakened_state_dimensions]:
        assert item.evidence_refs
        assert item.uncertainty.evidence_refs
    for window in [*evolution.risk_windows, *evolution.opportunity_windows]:
        assert window.evidence_refs
        assert window.uncertainty.evidence_refs
