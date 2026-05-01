from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LLMRewriteCandidate:
    text: str
    locale: str = "en"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LLMIntentParse:
    intent_key: str
    normalized_question: str
    candidate_question_keys: tuple[str, ...]
    feature_domains: tuple[str, ...]
    confidence: float
    locale: str = "zh"
    contract_task: str = "intent_parse"
    guardrails: tuple[str, ...] = (
        "INTENT_IS_ROUTING_HINT_ONLY",
        "NO_CHART_FACT_CREATED",
        "NO_RULE_ACTIVATION",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LLMQuestionSuggestion:
    question_key: str
    reason: str
    source_feature_ids: tuple[str, ...]
    contract_task: str = "question_suggestion"
    status: str = "proposal_only"
    guardrails: tuple[str, ...] = (
        "QUESTION_RANKER_HAS_FINAL_SAY",
        "FEATURE_SPINE_SOURCES_REQUIRED",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LLMFeatureCandidate:
    domain: str
    rationale: str
    required_evidence: tuple[str, ...]
    contract_task: str = "feature_candidate_proposal"
    status: str = "proposal_only"
    guardrails: tuple[str, ...] = (
        "FEATURE_COMPILER_HAS_FINAL_SAY",
        "KNOWLEDGE_IS_CONTEXT_ONLY",
        "NO_RUNTIME_FEATURE_WRITE",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LLMRuleExtractionDraft:
    condition_atoms: tuple[dict[str, object], ...]
    emits_feature_hooks: tuple[str, ...]
    supports_question_hooks: tuple[str, ...]
    boundary: str
    risk_notes: tuple[str, ...]
    contract_task: str = "rule_extraction_draft"
    status: str = "draft_only"
    guardrails: tuple[str, ...] = (
        "KNOWLEDGE_BASE_REMAINS_RULE_AUTHORITY",
        "VALIDATOR_REQUIRED_BEFORE_SHADOW_USE",
        "NO_RUNTIME_RULE_ACTIVATION",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LLMSafetyReview:
    ok: bool
    failures: tuple[str, ...]
    risk_notes: tuple[str, ...]
    contract_task: str = "safety_review"
    guardrails: tuple[str, ...] = (
        "ADVISORY_REVIEW_ONLY",
        "DETERMINISTIC_VALIDATOR_FINAL",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LLMFeedbackSummary:
    summary: str
    candidate_domains: tuple[str, ...]
    calibration_notes: tuple[str, ...]
    contract_task: str = "feedback_summary"
    status: str = "analysis_only"
    guardrails: tuple[str, ...] = (
        "NO_AUTOMATIC_PROMOTION",
        "HUMAN_OR_VALIDATION_GATE_REQUIRED",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
