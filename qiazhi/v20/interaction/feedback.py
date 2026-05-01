from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class FeatureCalibrationSignal:
    feature_id: str
    profile_id: str
    signal: str
    source_role: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = ["CALIBRATION_SIGNAL_ONLY", "NO_RULE_MUTATION"]
        return payload
