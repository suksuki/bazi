from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class KnowledgeUnit:
    knowledge_id: str
    title: str
    domain: str
    summary: str
    evidence_template: str
    boundary: str
    version: str = "v20.knowledge_unit.v1"
    status: str = "reviewed"
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    feature_hooks: tuple[str, ...] = field(default_factory=tuple)
    question_hooks: tuple[str, ...] = field(default_factory=tuple)
    retrieval_tags: tuple[str, ...] = field(default_factory=tuple)
    allowed_usage: tuple[str, ...] = ("evidence_context", "feature_support", "question_support")
    forbidden_usage: tuple[str, ...] = ("direct_rule_truth", "fortune_verdict", "domain_event_prediction")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = [
            "KNOWLEDGE_IS_EVIDENCE_NOT_RULE",
            "REVIEWED_BEFORE_RUNTIME_USE",
            "NO_DIRECT_CONCLUSION",
        ]
        return payload


@dataclass(frozen=True)
class KnowledgeRef:
    knowledge_id: str
    title: str
    domain: str
    evidence_template: str
    boundary: str
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    reviewed: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = ["REVIEWED_KNOWLEDGE_REF_ONLY"]
        return payload


@dataclass(frozen=True)
class KnowledgeRetrievalReport:
    version: str
    refs: tuple[KnowledgeRef, ...]
    mode: str = "feature_spine_reviewed_knowledge_retrieval"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "mode": self.mode,
            "count": len(self.refs),
            "refs": [row.to_dict() for row in self.refs],
            "guardrails": [
                "KNOWLEDGE_RETRIEVAL_CONTEXT_ONLY",
                "EMBEDDING_RECALL_MUST_PASS_REVIEW_STATUS",
                "NO_RULE_ACTIVATION_FROM_KNOWLEDGE",
            ],
        }
