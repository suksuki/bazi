from __future__ import annotations

from scripts.v50_audit_next_framework_alignment import audit_framework_alignment


def test_next_framework_alignment_has_one_machine_readable_baseline() -> None:
    result = audit_framework_alignment()

    assert result["status"] == "CLOSED_PASS"
    assert result["counts"] == {
        "surfaces": 8,
        "canonical_or_canonical_consumer": 7,
        "scoped_non_authoritative": 1,
        "invariants_passed": 10,
        "gaps": 0,
    }
    assert all(item["passed"] for item in result["invariants"])
    assert result["gaps"] == []
    assert result["formal_state_modified"] is False
    assert result["production_migration_performed"] is False


def test_next_framework_alignment_is_deterministic() -> None:
    assert audit_framework_alignment() == audit_framework_alignment()
