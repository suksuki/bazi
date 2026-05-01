from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class KnowledgeSource:
    source_ref: str
    title: str
    source_type: str
    path: str
    review_status: str = "reviewed"
    release_scope: str = "v20_reference"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = [
            "SOURCE_REF_IS_TRACEABILITY_HANDLE",
            "SOURCE_DOES_NOT_ACTIVATE_RULES",
            "REVIEW_STATUS_REQUIRED_FOR_RELEASE",
        ]
        return payload


@dataclass(frozen=True)
class KnowledgeRuleAtom:
    atom_id: str
    atom_type: str
    operator: str
    value: str
    evidence_role: str
    confidence: float = 0.5
    boundary: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = [
            "RULE_ATOM_FROM_REVIEWED_KNOWLEDGE",
            "ATOM_IS_CANDIDATE_CONDITION_NOT_RUNTIME_TRUTH",
        ]
        return payload


@dataclass(frozen=True)
class KnowledgePortraitMapping:
    portrait_key: str
    label: str
    domain: str
    description: str
    temperature: str = "warm"
    from_rule_atoms: tuple[str, ...] = field(default_factory=tuple)
    question_seeds: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = [
            "PORTRAIT_MAPPING_IS_USER_FACING_PROJECTION",
            "NO_FIXED_FORTUNE_VERDICT",
        ]
        return payload


@dataclass(frozen=True)
class KnowledgeQuestionMapping:
    question_key: str
    title: str
    domain: str
    trigger_rule_atoms: tuple[str, ...] = field(default_factory=tuple)
    role: str = "recommended_question"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = [
            "QUESTION_MAPPING_MUST_BE_HUMAN_READABLE",
            "QUESTION_GUIDES_MEASUREMENT_NOT_VERDICT",
        ]
        return payload


@dataclass(frozen=True)
class KnowledgeAnswerGuidance:
    guidance_key: str
    domain: str
    reading_focus: str
    allowed_phrases: tuple[str, ...] = field(default_factory=tuple)
    forbidden_phrases: tuple[str, ...] = field(default_factory=tuple)
    boundary: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = [
            "ANSWER_GUIDANCE_IS_STYLE_AND_BOUNDARY_ONLY",
            "LLM_MUST_NOT_CREATE_NEW_CHART_FACTS",
        ]
        return payload


@dataclass(frozen=True)
class KnowledgeCounterexample:
    counterexample_key: str
    description: str
    blocks_rule_atoms: tuple[str, ...] = field(default_factory=tuple)
    required_evidence: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = [
            "COUNTEREXAMPLE_REQUIRES_EVIDENCE",
            "USED_FOR_VALIDATION_AND_ARBITRATION",
        ]
        return payload


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
    rule_atoms: tuple[KnowledgeRuleAtom, ...] = field(default_factory=tuple)
    portrait_mappings: tuple[KnowledgePortraitMapping, ...] = field(default_factory=tuple)
    question_mappings: tuple[KnowledgeQuestionMapping, ...] = field(default_factory=tuple)
    answer_guidance: tuple[KnowledgeAnswerGuidance, ...] = field(default_factory=tuple)
    counterexamples: tuple[KnowledgeCounterexample, ...] = field(default_factory=tuple)
    allowed_usage: tuple[str, ...] = ("evidence_context", "feature_support", "question_support")
    forbidden_usage: tuple[str, ...] = ("direct_rule_truth", "fortune_verdict", "domain_event_prediction")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rule_atoms"] = [row.to_dict() for row in self.rule_atoms]
        payload["portrait_mappings"] = [row.to_dict() for row in self.portrait_mappings]
        payload["question_mappings"] = [row.to_dict() for row in self.question_mappings]
        payload["answer_guidance"] = [row.to_dict() for row in self.answer_guidance]
        payload["counterexamples"] = [row.to_dict() for row in self.counterexamples]
        payload["guardrails"] = [
            "KNOWLEDGE_IS_EVIDENCE_NOT_RULE",
            "REVIEWED_BEFORE_RUNTIME_USE",
            "NO_DIRECT_CONCLUSION",
            "STRUCTURED_MAPPINGS_REQUIRE_RULE_VALIDATION",
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
