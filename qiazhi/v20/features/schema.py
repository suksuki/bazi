from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceRef:
    ref_id: str
    kind: str
    title: str
    source_layer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BaziFeature:
    feature_id: str
    title: str
    domain: str
    source_layers: tuple[str, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    confidence: float
    readiness: str
    boundary: str
    question_hooks: tuple[str, ...] = field(default_factory=tuple)
    answer_hooks: tuple[str, ...] = field(default_factory=tuple)
    calibration_state: str = "system_suggested"
    guardrails: tuple[str, ...] = (
        "FEATURE_IS_INTERMEDIATE_SIGNAL",
        "FEATURE_IS_NOT_VERDICT",
        "NO_RULE_MUTATION",
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_refs"] = [row.to_dict() for row in self.evidence_refs]
        return payload


@dataclass(frozen=True)
class MacroFeature:
    macro_id: str
    title: str
    domain: str
    feature_ids: tuple[str, ...]
    evidence_count: int
    peak_confidence: float
    summary: str
    default_consumer: str = "ui_and_llm_context"
    guardrails: tuple[str, ...] = (
        "MACRO_FEATURE_IS_AGGREGATE",
        "SUBFEATURES_REMAIN_SOURCE_OF_TRUTH",
        "NO_CONCLUSION_FROM_CLUSTER_ONLY",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FeatureLayer:
    version: str
    features: tuple[BaziFeature, ...]
    macro_features: tuple[MacroFeature, ...] = field(default_factory=tuple)
    discovery_trace: dict[str, Any] = field(default_factory=dict)
    status: str = "ready"
    guardrails: tuple[str, ...] = (
        "BAZI_FEATURE_SPINE",
        "FEATURES_DRIVE_QUESTIONS_AND_EVIDENCE",
        "MACRO_FEATURES_DRIVE_DEFAULT_CONTEXT",
        "NO_HARD_VERDICT",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "feature_count": len(self.features),
            "macro_feature_count": len(self.macro_features),
            "macro_features": [row.to_dict() for row in self.macro_features],
            "features": [row.to_dict() for row in self.features],
            "discovery_trace": self.discovery_trace,
            "guardrails": list(self.guardrails),
        }
