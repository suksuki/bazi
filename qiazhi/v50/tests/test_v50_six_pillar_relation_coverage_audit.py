from __future__ import annotations

from scripts.v50_audit_six_pillar_relation_coverage import (
    audit_six_pillar_relation_coverage,
)


def test_six_pillar_relation_audit_exposes_current_coverage_without_fixing_it() -> None:
    result = audit_six_pillar_relation_coverage()

    assert result["status"] == "AUDIT_COMPLETE_RA1_REQUIRED"
    assert result["counts"] == {
        "declared_relation_types": 12,
        "builder_emitted_relation_types": 6,
        "declared_but_unemitted": 6,
        "canvas_advertised_relation_types": 11,
        "canvas_only_relation_types": 3,
        "configured_triple_combinations": 1,
        "six_clash_pairs_in_knowledge": 6,
        "six_harmony_pairs_in_knowledge": 6,
        "temporal_relation_builders": 0,
        "findings": 8,
    }
    assert result["declared_but_unemitted"] == [
        "activates",
        "bridges",
        "clashes",
        "forms_half_combination",
        "harmonizes",
        "roots",
    ]
    assert result["canvas_only_relation_types"] == ["breaks", "harms", "punishes"]
    assert all(item["passed"] for item in result["checks"])
    assert result["relation_semantics_modified"] is False
    assert result["formal_state_modified"] is False


def test_six_pillar_relation_audit_is_deterministic() -> None:
    assert audit_six_pillar_relation_coverage() == audit_six_pillar_relation_coverage()
