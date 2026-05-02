from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from v20.knowledge.schema import KnowledgeUnit


@dataclass(frozen=True)
class KnowledgeRetrievalPolicy:
    policy_id: str = "v20.knowledge_retrieval.default"
    domain_weights: dict[str, float] = field(default_factory=dict)
    tag_weights: dict[str, float] = field(default_factory=dict)
    max_adjustment: float = 0.15
    source: str = "deterministic_default"
    status: str = "active"
    guardrails: tuple[str, ...] = (
        "RETRIEVAL_POLICY_REORDERS_REVIEWED_UNITS_ONLY",
        "NO_RULE_ACTIVATION_FROM_KNOWLEDGE",
        "REVIEWED_STATUS_REQUIRED",
        "LEARNED_POLICY_REQUIRES_PROMOTION_GATE",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_knowledge_retrieval_policy() -> KnowledgeRetrievalPolicy:
    return KnowledgeRetrievalPolicy()


def rank_knowledge_units(
    units: tuple[KnowledgeUnit, ...] | list[KnowledgeUnit],
    policy: KnowledgeRetrievalPolicy | None = None,
) -> tuple[KnowledgeUnit, ...]:
    policy = policy or default_knowledge_retrieval_policy()
    scored = tuple((_score_unit(unit, policy), unit.knowledge_id, unit) for unit in units)
    return tuple(unit for _score, _knowledge_id, unit in sorted(scored, reverse=True))


def knowledge_retrieval_manifest() -> dict[str, object]:
    policy = default_knowledge_retrieval_policy()
    return {
        "version": "v20.knowledge_retrieval_policy_manifest.v1",
        "default_policy": policy.to_dict(),
        "allowed_learning_inputs": [
            "reviewed_knowledge_click_or_use_stats",
            "synthetic_validation_missing_domain",
            "embedding_recall_active_replay_report",
            "anonymized_feedback_domain_summary",
        ],
        "blocked_learning_outputs": [
            "direct_rule_truth",
            "unreviewed_knowledge_activation",
            "answer_conclusion",
            "chart_fact",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_RETRIEVAL_IS_CONTEXT_ONLY",
            "POLICY_REORDERS_REVIEWED_UNITS_ONLY",
            "EMBEDDING_RECALL_MUST_PASS_REVIEW_FILTER",
        ],
    }


def _score_unit(unit: KnowledgeUnit, policy: KnowledgeRetrievalPolicy) -> float:
    base = 1.0 if unit.status == "reviewed" else -1.0
    adjustment = policy.domain_weights.get(unit.domain, 0.0)
    adjustment += sum(policy.tag_weights.get(tag, 0.0) for tag in unit.retrieval_tags)
    bounded = max(-policy.max_adjustment, min(policy.max_adjustment, adjustment))
    return round(base + bounded, 3)
