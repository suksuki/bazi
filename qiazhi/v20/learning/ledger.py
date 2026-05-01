from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LedgerEntry:
    run_id: str
    source: str
    input_hash: str
    artifact_hash: str
    decision_status: str = "recorded_only"
    blocked_actions: tuple[str, ...] = ("core_truth_update", "production_rule_activation", "answer_conclusion_update")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = ["LEDGER_RECORD_ONLY", "NO_RUNTIME_MUTATION"]
        return payload
