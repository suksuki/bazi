from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


PORTRAIT_SOURCE_POLICY = "feature_first_knowledge_supported"


@dataclass(frozen=True)
class PortraitKnowledgeLink:
    knowledge_id: str
    title: str
    domain: str
    boundary: str
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    reviewed: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = [
            "KNOWLEDGE_LINK_IS_SEMANTIC_SUPPORT",
            "KNOWLEDGE_LINK_DOES_NOT_CREATE_PORTRAIT_VERDICT",
        ]
        return payload


@dataclass(frozen=True)
class PortraitAxis:
    axis_id: str
    domain: str
    label: str
    measurement_stage: str
    feature_ids: tuple[str, ...]
    feature_count: int
    peak_confidence: float
    calibration_state: str
    knowledge_links: tuple[PortraitKnowledgeLink, ...]
    evidence_boundaries: tuple[str, ...]
    calibration_prompt: str
    alignment_status: str
    bazi_focus: str
    alignment_score: float
    source_policy: str = PORTRAIT_SOURCE_POLICY
    allowed_feedback_signals: tuple[str, ...] = (
        "confirm",
        "reject",
        "needs_review",
        "evidence_gap",
    )
    forbidden_usage: tuple[str, ...] = (
        "question_bias",
        "answer_conclusion_driver",
        "fortune_verdict",
        "rule_mutation",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "axis_id": self.axis_id,
            "domain": self.domain,
            "label": self.label,
            "measurement_stage": self.measurement_stage,
            "feature_ids": list(self.feature_ids),
            "feature_count": self.feature_count,
            "peak_confidence": self.peak_confidence,
            "calibration_state": self.calibration_state,
            "knowledge_ref_count": len(self.knowledge_links),
            "knowledge_links": [row.to_dict() for row in self.knowledge_links],
            "evidence_boundaries": list(self.evidence_boundaries),
            "calibration_prompt": self.calibration_prompt,
            "alignment_status": self.alignment_status,
            "bazi_focus": self.bazi_focus,
            "alignment_score": self.alignment_score,
            "source_policy": self.source_policy,
            "allowed_feedback_signals": list(self.allowed_feedback_signals),
            "forbidden_usage": list(self.forbidden_usage),
            "guardrails": [
                "PORTRAIT_AXIS_FROM_FEATURES",
                "REVIEWED_KNOWLEDGE_SUPPORTS_AXIS_LANGUAGE",
                "CALIBRATION_SIGNAL_ONLY",
            ],
        }


@dataclass(frozen=True)
class PortraitItem:
    feature_id: str
    title: str
    domain: str
    measurement_topic: str
    measurement_stage: str
    measurement_focus: str
    confidence: float
    calibration_state: str
    knowledge_links: tuple[PortraitKnowledgeLink, ...]
    alignment_status: str
    bazi_focus: str
    alignment_score: float
    source_policy: str = PORTRAIT_SOURCE_POLICY

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "title": self.title,
            "domain": self.domain,
            "measurement_topic": self.measurement_topic,
            "measurement_stage": self.measurement_stage,
            "measurement_focus": self.measurement_focus,
            "confidence": self.confidence,
            "calibration_state": self.calibration_state,
            "knowledge_ref_count": len(self.knowledge_links),
            "knowledge_links": [row.to_dict() for row in self.knowledge_links],
            "alignment_status": self.alignment_status,
            "bazi_focus": self.bazi_focus,
            "alignment_score": self.alignment_score,
            "source_policy": self.source_policy,
            "guardrails": [
                "PORTRAIT_ITEM_FROM_BAZI_FEATURE",
                "KNOWLEDGE_CONTEXT_IS_BOUNDARY_ONLY",
                "NO_DIRECT_PERSONALITY_LABEL",
            ],
        }


@dataclass(frozen=True)
class PortraitProjection:
    version: str
    status: str
    role: str
    measurement_role: str
    axes: tuple[PortraitAxis, ...]
    items: tuple[PortraitItem, ...]
    source_policy: str = PORTRAIT_SOURCE_POLICY
    guardrails: tuple[str, ...] = (
        "PORTRAIT_IS_FEATURE_PROJECTION",
        "KNOWLEDGE_SUPPORTS_LABELS_NOT_VERDICTS",
        "NO_QUESTION_BIAS_FROM_PORTRAIT",
        "NO_PORTRAIT_DRIVEN_FORTUNE_VERDICT",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "role": self.role,
            "measurement_role": self.measurement_role,
            "source_policy": self.source_policy,
            "axis_count": len(self.axes),
            "knowledge_ref_count": len(
                {link.knowledge_id for axis in self.axes for link in axis.knowledge_links}
            ),
            "axes": [row.to_dict() for row in self.axes],
            "items": [row.to_dict() for row in self.items],
            "guardrails": list(self.guardrails),
        }
