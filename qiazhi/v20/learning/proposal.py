from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LearningProposal:
    proposal_id: str
    proposal_type: str
    summary: str
    risk: str = "low"
    status: str = "draft"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = ["PROPOSAL_ONLY", "VALIDATION_REQUIRED", "NO_AUTO_PROMOTION"]
        return payload
