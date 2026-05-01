from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    artifact_type: str
    dataset_version: str
    code_version: str
    eval_report_id: str
    decision_record_id: str = ""
    production_eligible: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = ["ARTIFACT_REQUIRES_DECISION_RECORD", "NO_UNREVIEWED_RUNTIME_USE"]
        return payload
