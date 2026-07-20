from __future__ import annotations

from core.contracts import Topic
from core.state import build_domain_state_enrichment, build_timing_state_evolution_v1, discover_unified_theme_bundle


def _ast(*, representation_id: str, mechanism_code: str, roles: list[str]) -> dict[str, object]:
    return {
        "representation_id": representation_id,
        "reading_id": "reading.theme_bundle.test",
        "mechanism_code": mechanism_code,
        "components": [
            {
                "component_id": f"{representation_id}:{role}",
                "reading_id": "reading.theme_bundle.test",
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


def _state_and_timing(*, reading_id: str, domain: Topic, ast: dict[str, object], overlays: dict[str, dict[str, object]]):
    enrichment = build_domain_state_enrichment(
        reading_id=reading_id,
        domain=domain,
        mechanism_ast=[ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
        timing_state={"activated_by": ["year.丙午"], "trend": "increasing"},
    )
    timing = build_timing_state_evolution_v1(
        reading_id=reading_id,
        domain=domain,
        state_dimensions=enrichment.state_dimensions,
        mechanism_ast=[ast],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T001"],
        timing_overlays=overlays,
    )
    return enrichment, timing


def test_theme_is_not_mechanism_label() -> None:
    ast = _ast(representation_id="m1", mechanism_code="output_controls_pressure", roles=["source", "path", "converter", "target", "state_delta"])
    enrichment, timing = _state_and_timing(
        reading_id="reading.theme_bundle.not_label",
        domain=Topic.CAREER,
        ast=ast,
        overlays={"year": {"model_id": "timing.year.activation_event.v1", "evidence_refs": ["timing.year"]}},
    )
    bundle = discover_unified_theme_bundle(
        reading_id="reading.theme_bundle.not_label",
        domain=Topic.CAREER,
        mechanism_ast=[ast],
        state_dimensions=enrichment.state_dimensions,
        timing_evolution=timing,
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )

    assert bundle.primary_theme.theme_name != "output_controls_pressure"
    assert bundle.primary_theme.theme_type.value in {"creation", "pressure_transformation", "risk_control", "management"}


def test_same_natal_different_timing_changes_active_theme() -> None:
    ast = _ast(representation_id="m2", mechanism_code="output_controls_pressure", roles=["source", "path", "converter", "counter_force", "target", "state_delta"])
    advance_state, advance_timing = _state_and_timing(
        reading_id="reading.theme_bundle.advance",
        domain=Topic.CAREER,
        ast=ast,
        overlays={"year": {"model_id": "timing.year.activation_event.v1", "evidence_refs": ["timing.year"], "confidence": 0.66}},
    )
    risk_state, risk_timing = _state_and_timing(
        reading_id="reading.theme_bundle.risk",
        domain=Topic.CAREER,
        ast=ast,
        overlays={
            "year": {"model_id": "timing.year.activation_event.v1", "evidence_refs": ["timing.year"], "confidence": 0.66},
            "month": {"model_id": "timing.month.event_window.v1", "evidence_refs": ["timing.month"], "confidence": 0.61},
        },
    )
    advance = discover_unified_theme_bundle(
        reading_id="reading.theme_bundle.advance",
        domain=Topic.CAREER,
        mechanism_ast=[ast],
        state_dimensions=advance_state.state_dimensions,
        timing_evolution=advance_timing,
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )
    risk = discover_unified_theme_bundle(
        reading_id="reading.theme_bundle.risk",
        domain=Topic.CAREER,
        mechanism_ast=[ast],
        state_dimensions=risk_state.state_dimensions,
        timing_evolution=risk_timing,
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )

    assert advance.base_theme.theme_type == risk.base_theme.theme_type
    assert advance.base_theme.strength == risk.base_theme.strength
    assert advance.active_theme.model_dump(mode="json") != risk.active_theme.model_dump(mode="json")
    assert advance.theme_transition.timing_changed_base_theme is False
    assert risk.theme_transition.timing_changed_base_theme is False


def test_same_mechanism_different_state_changes_theme() -> None:
    converter_ast = _ast(representation_id="m3", mechanism_code="output_controls_pressure", roles=["source", "path", "converter", "target", "state_delta"])
    bridge_ast = _ast(representation_id="m4", mechanism_code="output_controls_pressure", roles=["source", "path", "bridge", "anchor", "target", "state_delta"])
    converter_state, converter_timing = _state_and_timing(
        reading_id="reading.theme_bundle.converter",
        domain=Topic.CAREER,
        ast=converter_ast,
        overlays={"year": {"model_id": "timing.year.activation_event.v1", "evidence_refs": ["timing.year"]}},
    )
    bridge_state, bridge_timing = _state_and_timing(
        reading_id="reading.theme_bundle.bridge",
        domain=Topic.CAREER,
        ast=bridge_ast,
        overlays={"luck": {"model_id": "timing.luck.long_term_field.v1", "evidence_refs": ["timing.luck"]}},
    )
    converter = discover_unified_theme_bundle(
        reading_id="reading.theme_bundle.converter",
        domain=Topic.CAREER,
        mechanism_ast=[converter_ast],
        state_dimensions=converter_state.state_dimensions,
        timing_evolution=converter_timing,
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )
    bridge = discover_unified_theme_bundle(
        reading_id="reading.theme_bundle.bridge",
        domain=Topic.CAREER,
        mechanism_ast=[bridge_ast],
        state_dimensions=bridge_state.state_dimensions,
        timing_evolution=bridge_timing,
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )

    assert converter.primary_theme.theme_type != bridge.primary_theme.theme_type or converter.secondary_themes != bridge.secondary_themes


def test_theme_candidates_have_evidence_refs() -> None:
    ast = _ast(representation_id="m5", mechanism_code="peer_competes_for_wealth", roles=["source", "path", "bridge", "counter_force", "target", "state_delta"])
    enrichment, timing = _state_and_timing(
        reading_id="reading.theme_bundle.evidence",
        domain=Topic.WEALTH,
        ast=ast,
        overlays={"year": {"model_id": "timing.year.activation_event.v1", "evidence_refs": ["timing.year"]}},
    )
    bundle = discover_unified_theme_bundle(
        reading_id="reading.theme_bundle.evidence",
        domain=Topic.WEALTH,
        mechanism_ast=[ast],
        state_dimensions=enrichment.state_dimensions,
        timing_evolution=timing,
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )

    for theme in [bundle.primary_theme, *bundle.secondary_themes]:
        assert theme.evidence_refs
        assert theme.source_mechanism_refs
        assert theme.source_state_dimension_refs


def test_theme_discovery_allows_unknown() -> None:
    bundle = discover_unified_theme_bundle(
        reading_id="reading.theme_bundle.unknown",
        domain=Topic.CAREER,
        mechanism_ast=[],
        state_dimensions=[],
        timing_evolution=None,
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )

    assert bundle.primary_theme.theme_type.value == "unknown"
    assert bundle.primary_theme.completeness.value == "weak"


def test_unsupported_domain_does_not_create_fake_theme() -> None:
    ast = _ast(representation_id="m6", mechanism_code="output_controls_pressure", roles=["source", "path", "target"])
    bundle = discover_unified_theme_bundle(
        reading_id="reading.theme_bundle.relationship",
        domain=Topic.RELATIONSHIP,
        mechanism_ast=[ast],
        state_dimensions=[],
        timing_evolution=None,
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )

    assert bundle.domain_supported is False
    assert bundle.domain_gap is True
    assert bundle.primary_theme.theme_type.value == "unknown"
