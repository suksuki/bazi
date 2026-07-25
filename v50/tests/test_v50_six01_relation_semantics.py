from __future__ import annotations

from scripts.v50_audit_six01_relation_semantics import (
    audit_six01_relation_semantics,
)


def test_six01_builds_complete_deterministic_relation_matrices() -> None:
    first = audit_six01_relation_semantics()
    second = audit_six01_relation_semantics()

    assert first["content_sha256"] == second["content_sha256"]
    assert first["counts"] == {
        "ordered_stem_pairs": 100,
        "unordered_branch_pairs_with_repeat": 78,
        "stem_branch_pairs": 120,
        "ordered_six_slot_pairs": 36,
        "formal_nary_relations": 6,
        "research_candidate_nary_relations": 4,
        "runtime_relation_types": 13,
        "positive_fixtures": 14,
        "negative_fixtures": 7,
        "boundary_fixtures": 5,
        "open_semantic_gaps": 9,
    }
    assert all(item["passed"] for item in first["fixture_results"])


def test_six01_keeps_research_candidates_out_of_runtime_authority() -> None:
    report = audit_six01_relation_semantics()
    stem_rows = report["matrices"]["stem_to_stem"]
    nary_rows = report["matrices"]["nary_relations"]

    jia_ji = next(
        item for item in stem_rows if item["source"] == "甲" and item["target"] == "己"
    )
    three_meetings = [
        item for item in nary_rows if item["relation_type"] == "three_meeting"
    ]

    assert jia_ji["stem_combination_candidate"] is not None
    assert jia_ji["stem_combination_runtime_status"] == "not_implemented"
    assert len(three_meetings) == 4
    assert all(
        item["runtime_status"] == "research_candidate_not_implemented"
        for item in three_meetings
    )
    assert report["conclusions"]["client_or_lab_may_promote_relation"] is False


def test_six01_exposes_unresolved_semantics_instead_of_claiming_completion() -> None:
    report = audit_six01_relation_semantics()
    gaps = {item["gap_id"]: item for item in report["open_semantic_gaps"]}

    assert report["status"] == "FOUNDATION_AUDIT_COMPLETE_WITH_OPEN_SEMANTICS"
    assert set(gaps) == {f"SIX-G{index:02d}" for index in range(1, 10)}
    assert gaps["SIX-G04"]["area"] == "transformation"
    assert gaps["SIX-G07"]["area"] == "temporal_activation"
    assert report["conclusions"]["structural_relation_is_activation"] is False
    assert report["conclusions"]["combination_is_transformation"] is False
    assert report["conclusions"]["formal_algorithm_changed"] is False
    assert report["formal_state_modified"] is False
    assert report["llm_used"] is False


def test_six01_preserves_slot_identity_and_multiple_branch_relations() -> None:
    report = audit_six01_relation_semantics()
    scope_rows = report["matrices"]["six_slot_identity_and_time"]
    branch_rows = report["matrices"]["branch_to_branch"]

    natal_to_year = next(
        item
        for item in scope_rows
        if item["source_slot"] == "natal_year" and item["target_slot"] == "annual"
    )
    yin_hai = next(
        item for item in branch_rows if item["participants"] == ["寅", "亥"]
    )

    assert natal_to_year["identity_distinct"] is True
    assert natal_to_year["temporal_role"] == "natal_context_for_temporal"
    assert yin_hai["multiple_structural_relations_preserved"] is True
    assert set(yin_hai["runtime_branch_relations"]) == {"break", "harmony"}
