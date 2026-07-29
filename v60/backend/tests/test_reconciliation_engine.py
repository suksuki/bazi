import pytest
from abu_v60.decision import EvidenceReconciliationEngine, ReconciliationResult


def test_reconciliation_is_atom_level_and_gives_no_baseline_credit() -> None:
    decision = EvidenceReconciliationEngine().reconcile(
        predicted_atoms={"flow": "INTERMITTENT", "root": "LIMITED_SUPPORT"},
        actual_atoms={"flow": "INTERMITTENT", "root": "NO_SUPPORT"},
        compare_atoms=("flow", "root"),
    )
    assert decision.result is ReconciliationResult.PARTIAL
    assert decision.baseline_credit is False
    assert decision.atom_reconciliation["flow"]["matched"] is True
    assert decision.atom_reconciliation["root"]["matched"] is False


def test_reconciliation_fails_closed_when_an_atom_is_missing() -> None:
    with pytest.raises(ValueError, match="reconciliation_atom_missing:root"):
        EvidenceReconciliationEngine().reconcile(
            predicted_atoms={"flow": "INTERMITTENT"},
            actual_atoms={"flow": "INTERMITTENT"},
            compare_atoms=("flow", "root"),
        )
