from __future__ import annotations

from core.contracts import Topic
from core.state import build_domain_state_enrichment


def _ast(*, representation_id: str, mechanism_code: str, roles: list[str], state_delta_status: str = "missing") -> dict[str, object]:
    return {
        "representation_id": representation_id,
        "reading_id": "reading.state_enrichment.test",
        "mechanism_code": mechanism_code,
        "components": [
            {
                "component_id": f"{representation_id}:{role}",
                "reading_id": "reading.state_enrichment.test",
                "role": role,
                "ref": f"node.{role}",
                "evidence_refs": [f"evidence.{role}"],
                "confidence": 0.72,
            }
            for role in roles
        ],
        "path_refs": [f"path.{representation_id}"],
        "state_delta_refs": [f"state_delta.{representation_id}"] if state_delta_status != "missing" else [],
        "evidence_refs": [f"evidence.{representation_id}"],
        "completeness": "partial",
        "missing_fields": [],
        "uncertainty": {"reasons": ["fixture"]},
        "ast_shape": "+".join(sorted(roles)),
        "state_delta_status": state_delta_status,
        "confidence": 0.72,
    }


def test_mechanism_ast_to_state_dimensions_distinguishes_same_label_variants() -> None:
    converter_variant = build_domain_state_enrichment(
        reading_id="reading.state_enrichment.converter",
        domain=Topic.CAREER,
        mechanism_ast=[_ast(representation_id="m1", mechanism_code="output_controls_pressure", roles=["source", "path", "converter", "target"])],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )
    bridge_variant = build_domain_state_enrichment(
        reading_id="reading.state_enrichment.bridge",
        domain=Topic.CAREER,
        mechanism_ast=[_ast(representation_id="m2", mechanism_code="output_controls_pressure", roles=["source", "path", "bridge", "target"])],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )

    converter_dimensions = {dimension.name for dimension in converter_variant.state_dimensions}
    bridge_dimensions = {dimension.name for dimension in bridge_variant.state_dimensions}

    assert "output_drive" in converter_dimensions
    assert "mobility" in bridge_dimensions
    assert converter_dimensions != bridge_dimensions
    assert "risk" in converter_dimensions & bridge_dimensions


def test_state_dimensions_have_evidence_refs() -> None:
    enrichment = build_domain_state_enrichment(
        reading_id="reading.state_enrichment.evidence",
        domain=Topic.WEALTH,
        mechanism_ast=[
            _ast(
                representation_id="m3",
                mechanism_code="peer_competes_for_wealth",
                roles=["source", "path", "bridge", "counter_force", "target"],
                state_delta_status="real",
            )
        ],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
        timing_state={"activated_by": ["year.丙午"], "trend": "increasing"},
    )

    assert enrichment.state_dimensions
    for dimension in enrichment.state_dimensions:
        assert dimension.evidence_refs
        assert dimension.source_mechanism_refs
        assert set(dimension.theory_refs) == {"theory.T011"}
    assert enrichment.risk_field is not None
    assert enrichment.risk_field.evidence_refs


def test_unified_state_allows_missing_dimensions_without_hard_fill() -> None:
    no_timing = build_domain_state_enrichment(
        reading_id="reading.state_enrichment.no_timing",
        domain=Topic.CAREER,
        mechanism_ast=[_ast(representation_id="m4", mechanism_code="resource_support", roles=["source", "path", "anchor", "target"])],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )
    no_wealth_evidence = build_domain_state_enrichment(
        reading_id="reading.state_enrichment.no_wealth",
        domain=Topic.WEALTH,
        mechanism_ast=[],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )

    assert "timing_activation" not in {dimension.name for dimension in no_timing.state_dimensions}
    assert no_timing.timing_state_summary is None
    assert "timing_activation" in no_timing.missing_state_dimensions
    assert not no_wealth_evidence.state_dimensions
    assert "wealth_path" in no_wealth_evidence.missing_state_dimensions


def test_unsupported_domain_does_not_create_fake_state() -> None:
    enrichment = build_domain_state_enrichment(
        reading_id="reading.state_enrichment.relationship",
        domain=Topic.RELATIONSHIP,
        mechanism_ast=[_ast(representation_id="m5", mechanism_code="output_controls_pressure", roles=["source", "path", "target"])],
        evidence_refs=["evidence.root"],
        theory_refs=["theory.T011"],
    )

    assert enrichment.domain_supported is False
    assert enrichment.domain_gap is True
    assert enrichment.state_dimensions == []
    assert "relationship" in enrichment.unsupported_reason
