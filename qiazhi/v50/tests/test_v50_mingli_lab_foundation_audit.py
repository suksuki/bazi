from __future__ import annotations

from scripts.v50_audit_mingli_lab_foundation import audit_mingli_lab_foundation


def test_mingli_lab_foundation_preserves_formal_authority_boundaries() -> None:
    result = audit_mingli_lab_foundation()

    assert result["status"] == "CLOSED_PASS"
    assert result["formal_authority"] == "LifeCase"
    assert result["scene_authority"] == "CanonicalSceneOwner"
    assert result["counts"] == {
        "implementations": 4,
        "runtime_implementations": 1,
        "formal_write_paths": 0,
        "invariants_passed": 10,
        "gaps": 0,
    }
    assert all(item["passed"] for item in result["invariants"])
    assert result["gaps"] == []
    assert result["production_lab_authorized"] is False


def test_mingli_lab_foundation_audit_is_deterministic() -> None:
    assert audit_mingli_lab_foundation() == audit_mingli_lab_foundation()
