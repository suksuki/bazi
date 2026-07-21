from __future__ import annotations

from scripts.v50_audit_mingli_lab_foundation import audit_mingli_lab_foundation


def test_mingli_lab_foundation_preserves_formal_authority_boundaries() -> None:
    result = audit_mingli_lab_foundation()

    assert result["status"] == "FOUNDATION_READY_WITH_GAPS"
    assert result["formal_authority"] == "LifeCase"
    assert result["scene_authority"] == "CanonicalSceneOwner"
    assert result["counts"] == {
        "implementations": 3,
        "runtime_implementations": 1,
        "formal_write_paths": 0,
        "invariants_passed": 8,
        "gaps": 4,
    }
    assert all(item["passed"] for item in result["invariants"])
    assert {item["gap_id"] for item in result["gaps"]} == {
        "LAB-F01",
        "LAB-F02",
        "LAB-F03",
        "LAB-F04",
    }
    assert result["production_lab_authorized"] is False


def test_mingli_lab_foundation_audit_is_deterministic() -> None:
    assert audit_mingli_lab_foundation() == audit_mingli_lab_foundation()
