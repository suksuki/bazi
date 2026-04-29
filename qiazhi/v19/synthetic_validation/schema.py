from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping


SYNTHETIC_CASE_SCHEMA_VERSION = "v19.synthetic_case.v1"


@dataclass(frozen=True)
class SyntheticCase:
    case_id: str
    chart: Dict[str, Any]
    expected_inference_signals: Dict[str, Any] = field(default_factory=dict)
    expected_domain_adapter_outputs: Dict[str, Any] = field(default_factory=dict)
    forbidden_outputs: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    schema_version: str = SYNTHETIC_CASE_SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SyntheticCase":
        return cls(
            case_id=str(payload.get("case_id") or ""),
            chart=dict(payload.get("chart") or {}),
            expected_inference_signals=dict(payload.get("expected_inference_signals") or {}),
            expected_domain_adapter_outputs=dict(payload.get("expected_domain_adapter_outputs") or {}),
            forbidden_outputs=[str(item) for item in payload.get("forbidden_outputs", [])],
            tags=[str(item) for item in payload.get("tags", [])],
            schema_version=str(payload.get("schema_version") or SYNTHETIC_CASE_SCHEMA_VERSION),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "chart": dict(self.chart),
            "expected_inference_signals": dict(self.expected_inference_signals),
            "expected_domain_adapter_outputs": dict(self.expected_domain_adapter_outputs),
            "forbidden_outputs": list(self.forbidden_outputs),
            "tags": list(self.tags),
        }
