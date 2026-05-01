from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuleHit:
    rule_key: str
    label: str
    domain: str
    status: str
    score: float
    evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...] = ()
    feature_ids: tuple[str, ...] = ()
    source: str = "deterministic_chart_model"
    guardrails: tuple[str, ...] = (
        "RULE_HIT_IS_MATERIAL_ONLY",
        "NO_PORTRAIT_OR_VERDICT_FROM_HIT_ONLY",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PractitionerControl:
    control_key: str
    label: str
    options: tuple[str, ...]
    default: str
    source_decision_keys: tuple[str, ...]
    ui_surface: str = "analyst_admin_only"
    guardrails: tuple[str, ...] = (
        "BUTTON_OR_SELECT_ONLY",
        "NO_FREE_TEXT_FOR_CORE_DECISION",
        "PRACTITIONER_OVERRIDE_IS_TRAINING_SIGNAL",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuleDecision:
    decision_key: str
    rule_key: str
    label: str
    domain: str
    status: str
    role: str
    score: float
    support: tuple[str, ...]
    weakening: tuple[str, ...] = ()
    feature_ids: tuple[str, ...] = ()
    portrait_tags: tuple[str, ...] = ()
    question_seeds: tuple[str, ...] = ()
    practitioner_control_keys: tuple[str, ...] = ()
    learning_targets: tuple[str, ...] = (
        "decision_status",
        "decision_score",
        "mainline_role",
        "portrait_tag_mapping",
        "question_seed_ranking",
    )
    guardrails: tuple[str, ...] = (
        "DECISION_IS_EVIDENCE_BOUNDED",
        "PRACTITIONER_CAN_OVERRIDE_WITH_STRUCTURED_CHOICE",
        "LLM_MAY_EXPLAIN_NOT_DECIDE",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicPortraitTag:
    tag_key: str
    label: str
    domain: str
    summary: str
    score: float
    source_decision_keys: tuple[str, ...]
    question_seeds: tuple[str, ...] = ()
    status: str = "runtime_dynamic"
    guardrails: tuple[str, ...] = (
        "PORTRAIT_FROM_RULE_DECISION_ONLY",
        "NO_STATIC_518K_PORTRAIT_TRUTH",
        "NO_PERSONALITY_VERDICT",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicPortrait:
    version: str
    status: str
    tags: tuple[DynamicPortraitTag, ...]
    source: str = "runtime_rule_decisions"
    guardrails: tuple[str, ...] = (
        "DYNAMIC_PORTRAIT_FROM_CURRENT_CHART_DECISIONS",
        "TRAINING_CORPUS_IS_MATERIAL_ONLY",
        "PRACTITIONER_CALIBRATION_CAN_UPDATE_DECISION_PARAMS",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "tag_count": len(self.tags),
            "tags": [row.to_dict() for row in self.tags],
            "source": self.source,
            "guardrails": list(self.guardrails),
        }


@dataclass(frozen=True)
class DecisionReport:
    version: str
    status: str
    hits: tuple[RuleHit, ...]
    decisions: tuple[RuleDecision, ...]
    dynamic_portrait: DynamicPortrait
    practitioner_controls: tuple[PractitionerControl, ...] = field(default_factory=tuple)
    training_boundary: str = (
        "Knowledge, portrait, rule, and decision parameters are trained offline by scripts/admin review; "
        "runtime user measurement is driven by current-chart rule decisions."
    )
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "RULE_HITS_FEED_DECISIONS",
        "DECISIONS_FEED_DYNAMIC_PORTRAIT",
        "DYNAMIC_PORTRAIT_FEEDS_QUESTIONS_AND_LLM_CONTEXT",
        "518K_CORPUS_NEVER_OVERRIDES_RUNTIME_DECISION",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "hit_count": len(self.hits),
            "decision_count": len(self.decisions),
            "hits": [row.to_dict() for row in self.hits],
            "decisions": [row.to_dict() for row in self.decisions],
            "dynamic_portrait": self.dynamic_portrait.to_dict(),
            "practitioner_controls": [row.to_dict() for row in self.practitioner_controls],
            "training_boundary": self.training_boundary,
            "runtime_mutation": self.runtime_mutation,
            "guardrails": list(self.guardrails),
        }
