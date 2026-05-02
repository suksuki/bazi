from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuleCondition:
    condition_id: str
    evidence_type: str
    operator: str
    value: str
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuleCounterEvidence:
    counter_id: str
    title: str
    condition_refs: tuple[str, ...]
    effect: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuleProjection:
    projection_id: str
    topic_domain: str
    output_focus: tuple[str, ...]
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BaziRuleSpec:
    rule_id: str
    title: str
    directory_node: str
    domain: str
    layer: str
    runtime_status: str
    decision_state: str
    conditions: tuple[RuleCondition, ...]
    counter_evidence: tuple[RuleCounterEvidence, ...] = field(default_factory=tuple)
    projections: tuple[RuleProjection, ...] = field(default_factory=tuple)
    bridges_to_runtime_rules: tuple[str, ...] = field(default_factory=tuple)
    source: str = "v20_full_bazi_knowledge_content"
    runtime_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["conditions"] = [row.to_dict() for row in self.conditions]
        payload["counter_evidence"] = [row.to_dict() for row in self.counter_evidence]
        payload["projections"] = [row.to_dict() for row in self.projections]
        payload["guardrails"] = [
            "BAZI_RULE_SPEC_IS_STRUCTURAL_RULE",
            "RUNTIME_ALLOWED_ONLY_AFTER_REVIEW",
            "NO_DIRECT_FORTUNE_VERDICT",
        ]
        return payload
