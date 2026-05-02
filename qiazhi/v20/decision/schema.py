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
    dimension_key: str = ""
    dimension_layer: str = ""
    dimension_label: str = ""
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
class MainlineDecision:
    mainline_key: str
    title: str
    domain: str
    status: str
    score: float
    priority: int
    summary: str
    source_decision_keys: tuple[str, ...]
    support: tuple[str, ...]
    question_seed: str
    role: str = "primary_bazi_mainline"
    guardrails: tuple[str, ...] = (
        "MAINLINE_IS_AGGREGATED_FROM_RULE_DECISIONS",
        "NO_NEW_FACTS_FROM_MAINLINE",
        "MAINLINE_DRIVES_PORTRAIT_QUESTIONS_AND_ANSWER_ORDER",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionReport:
    version: str
    status: str
    hits: tuple[RuleHit, ...]
    decisions: tuple[RuleDecision, ...]
    mainlines: tuple[MainlineDecision, ...] = field(default_factory=tuple)
    practitioner_controls: tuple[PractitionerControl, ...] = field(default_factory=tuple)
    training_boundary: str = (
        "Knowledge, portrait, rule, and decision parameters are trained offline by scripts/admin review; "
        "runtime user measurement is driven by current-chart rule decisions."
    )
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "RULE_HITS_FEED_DECISIONS",
        "DECISIONS_FEED_MAINLINES",
        "DECISIONS_FEED_PORTRAIT_PROJECTION",
        "PORTRAIT_PROJECTION_FEEDS_QUESTIONS_AND_LLM_CONTEXT",
        "518K_CORPUS_NEVER_OVERRIDES_RUNTIME_DECISION",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "hit_count": len(self.hits),
            "decision_count": len(self.decisions),
            "mainline_count": len(self.mainlines),
            "hits": [row.to_dict() for row in self.hits],
            "decisions": [row.to_dict() for row in self.decisions],
            "mainlines": [row.to_dict() for row in self.mainlines],
            "practitioner_controls": [row.to_dict() for row in self.practitioner_controls],
            "training_boundary": self.training_boundary,
            "runtime_mutation": self.runtime_mutation,
            "guardrails": list(self.guardrails),
        }
