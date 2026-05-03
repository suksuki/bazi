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
class BaziFeatureContext:
    context_id: str
    feature_id: str
    feature_type: str
    domain: str
    mechanism: str
    source_rule_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence_atoms: tuple[str, ...] = field(default_factory=tuple)
    counter_evidence_atoms: tuple[str, ...] = field(default_factory=tuple)
    strength_score: float = 0.0
    confidence_score: float = 0.0
    decision_state: str = "available"
    readiness: str = "available"
    blockers: tuple[str, ...] = field(default_factory=tuple)
    amplifiers: tuple[str, ...] = field(default_factory=tuple)
    affected_domains: tuple[str, ...] = field(default_factory=tuple)
    time_scope: str = "natal"
    activation_sources: tuple[str, ...] = field(default_factory=tuple)
    projection_hooks: tuple[str, ...] = field(default_factory=tuple)
    question_hooks: tuple[str, ...] = field(default_factory=tuple)
    answer_hooks: tuple[str, ...] = field(default_factory=tuple)
    boundary_flags: tuple[str, ...] = field(default_factory=tuple)
    trace_nodes: tuple[str, ...] = field(default_factory=tuple)
    guardrails: tuple[str, ...] = (
        "FEATURE_CONTEXT_IS_COMPUTATION_METADATA",
        "FEATURE_CONTEXT_IS_NOT_USER_COPY",
        "PORTRAIT_AND_QUESTION_USE_CONTEXT_NOT_RULE_TITLE",
    )

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
    context: BaziFeatureContext | None = None
    calibration_state: str = "system_suggested"
    guardrails: tuple[str, ...] = (
        "FEATURE_IS_METADATA_SIGNAL",
        "FEATURE_IS_NOT_VERDICT",
        "FEATURE_IS_NOT_USER_PORTRAIT_COPY",
        "NO_RULE_MUTATION",
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_refs"] = [row.to_dict() for row in self.evidence_refs]
        payload["context"] = self.context.to_dict() if self.context else {}
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
    feature_contexts: tuple[BaziFeatureContext, ...] = field(default_factory=tuple)
    macro_features: tuple[MacroFeature, ...] = field(default_factory=tuple)
    discovery_trace: dict[str, Any] = field(default_factory=dict)
    status: str = "ready"
    guardrails: tuple[str, ...] = (
        "BAZI_FEATURE_SPINE",
        "FEATURE_CONTEXTS_DRIVE_QUESTIONS_AND_EVIDENCE",
        "MACRO_FEATURES_DRIVE_DEFAULT_CONTEXT",
        "FEATURES_ARE_COMPUTATION_METADATA_NOT_USER_PORTRAIT",
        "NO_HARD_VERDICT",
    )

    def to_dict(self) -> dict[str, Any]:
        contexts = self.feature_contexts or tuple(
            row.context for row in self.features if row.context is not None
        )
        return {
            "version": self.version,
            "status": self.status,
            "feature_count": len(self.features),
            "feature_context_count": len(contexts),
            "macro_feature_count": len(self.macro_features),
            "macro_features": [row.to_dict() for row in self.macro_features],
            "feature_contexts": [row.to_dict() for row in contexts],
            "features": [row.to_dict() for row in self.features],
            "discovery_trace": self.discovery_trace,
            "guardrails": list(self.guardrails),
        }
