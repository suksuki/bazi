from __future__ import annotations

from scripts.v50_audit_six_pillar_relation_coverage import (
    audit_six_pillar_relation_coverage,
)


def test_six_pillar_relation_audit_tracks_ra1_progress_without_overstating_it() -> None:
    result = audit_six_pillar_relation_coverage()

    assert result["status"] == "RA1_IN_PROGRESS"
    assert result["counts"] == {
        "declared_relation_types": 13,
        "builder_emitted_relation_types": 13,
        "declared_but_unemitted": 0,
        "canvas_advertised_relation_types": 11,
        "canvas_only_relation_types": 0,
        "configured_triple_combinations": 4,
        "configured_half_triple_combinations": 8,
        "six_clash_pairs_in_knowledge": 6,
        "six_harmony_pairs_in_knowledge": 6,
        "six_harm_pairs_in_knowledge": 6,
        "six_break_pairs_in_knowledge": 6,
        "pair_punishment_definitions": 1,
        "self_punishment_definitions": 4,
        "triple_punishment_definitions": 2,
        "temporal_relation_builders": 1,
        "findings": 2,
    }
    assert result["declared_but_unemitted"] == []
    assert result["canvas_only_relation_types"] == []
    assert all(item["passed"] for item in result["checks"])
    assert [item["finding_id"] for item in result["resolved_findings"]] == [
        "REL-A01",
        "REL-A02",
        "REL-A03",
        "REL-A04",
        "REL-A05",
        "REL-A06",
    ]
    assert result["relation_semantics_modified"] is False
    assert result["relation_projection_modified"] is True
    assert result["formal_state_modified"] is False


def test_six_pillar_relation_audit_is_deterministic() -> None:
    assert audit_six_pillar_relation_coverage() == audit_six_pillar_relation_coverage()
