from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class QuestionRankingPolicy:
    policy_id: str = "v20.question_ranking.default"
    domain_weights: dict[str, float] = field(default_factory=dict)
    stage_weights: dict[str, float] = field(default_factory=dict)
    max_adjustment: float = 0.12
    source: str = "deterministic_default"
    status: str = "active"
    guardrails: tuple[str, ...] = (
        "RANKING_POLICY_REORDERS_ONLY",
        "NO_NEW_QUESTION_GENERATION",
        "FEATURE_BACKED_CANDIDATES_REQUIRED",
        "VALIDATION_AND_DECISION_REQUIRED_FOR_LEARNED_POLICY",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_question_ranking_policy() -> QuestionRankingPolicy:
    return QuestionRankingPolicy()


def rank_question_rows(rows: tuple[object, ...], policy: QuestionRankingPolicy | None = None) -> tuple[object, ...]:
    policy = policy or default_question_ranking_policy()
    scored = tuple((_adjusted_score(row, policy), row) for row in rows)
    return tuple(row for _score, row in sorted(scored, key=lambda item: (item[0], getattr(item[1], "question_key", "")), reverse=True))


def question_ranking_manifest() -> dict[str, object]:
    policy = default_question_ranking_policy()
    return {
        "version": "v20.question_ranking_manifest.v1",
        "default_policy": policy.to_dict(),
        "allowed_learning_inputs": [
            "anonymized_feedback_summary",
            "synthetic_suite_result",
            "corpus_coverage_gap",
            "question_selection_outcome",
        ],
        "blocked_learning_outputs": [
            "new_question_key",
            "new_chart_fact",
            "rule_activation",
            "answer_conclusion",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_RANKING_IS_REORDER_ONLY",
            "FEATURE_SPINE_CANDIDATES_ARE_AUTHORITATIVE",
            "LEARNED_POLICY_REQUIRES_PROMOTION_GATE",
        ],
    }


def _adjusted_score(row: object, policy: QuestionRankingPolicy) -> float:
    base = float(getattr(row, "score", 0.0))
    domain = str(getattr(row, "domain", ""))
    stage = str(getattr(row, "measurement_stage", ""))
    adjustment = policy.domain_weights.get(domain, 0.0) + policy.stage_weights.get(stage, 0.0)
    bounded = max(-policy.max_adjustment, min(policy.max_adjustment, adjustment))
    return round(base + bounded, 3)
