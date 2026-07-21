from __future__ import annotations

from scripts.v50_audit_next_framework_alignment import audit_framework_alignment


def test_next_framework_alignment_has_one_machine_readable_baseline() -> None:
    result = audit_framework_alignment()

    assert result["status"] == "READY_WITH_GAPS"
    assert result["counts"] == {
        "surfaces": 8,
        "canonical_or_canonical_consumer": 5,
        "transitional_or_design": 3,
        "invariants_passed": 8,
        "gaps": 3,
    }
    assert all(item["passed"] for item in result["invariants"])
    assert {item["gap_id"] for item in result["gaps"]} == {
        "FRAME-01",
        "LAB-01",
        "LAB-02",
    }
    assert result["formal_state_modified"] is False
    assert result["production_migration_performed"] is False


def test_next_framework_alignment_is_deterministic() -> None:
    assert audit_framework_alignment() == audit_framework_alignment()
