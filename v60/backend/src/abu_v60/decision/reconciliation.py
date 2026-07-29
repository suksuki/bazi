from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class ReconciliationResult(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    NOT_SUPPORTED = "NOT_SUPPORTED"


class ReconciliationDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    result: ReconciliationResult
    baseline_credit: bool = False
    atom_reconciliation: dict[str, dict[str, Any]]


class EvidenceReconciliationEngine:
    """Compare a sealed proposition only with post-cutoff committed evidence."""

    def reconcile(
        self,
        *,
        predicted_atoms: Mapping[str, Any],
        actual_atoms: Mapping[str, Any],
        compare_atoms: Sequence[str],
    ) -> ReconciliationDecision:
        if not compare_atoms:
            raise ValueError("reconciliation_atoms_required")
        atom_results: dict[str, dict[str, Any]] = {}
        for atom in compare_atoms:
            if atom not in predicted_atoms or atom not in actual_atoms:
                raise ValueError(f"reconciliation_atom_missing:{atom}")
            predicted = predicted_atoms[atom]
            actual = actual_atoms[atom]
            atom_results[atom] = {
                "predicted": predicted,
                "actual": actual,
                "matched": predicted == actual,
            }
        match_count = sum(bool(item["matched"]) for item in atom_results.values())
        result = (
            ReconciliationResult.SUPPORTED
            if match_count == len(atom_results)
            else ReconciliationResult.PARTIAL
            if match_count > 0
            else ReconciliationResult.NOT_SUPPORTED
        )
        return ReconciliationDecision(
            result=result,
            baseline_credit=False,
            atom_reconciliation=atom_results,
        )
