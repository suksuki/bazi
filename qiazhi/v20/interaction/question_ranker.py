from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
from typing import Any

from v20.storage.local_jsonl import local_jsonl_store_from_env

SHADOW_POLICY_PATH_SUFFIX = "training/question_ranking/latest.json"


@dataclass(frozen=True)
class QuestionRankingPolicy:
    policy_id: str = "v20.question_ranking.default"
    domain_weights: dict[str, float] = field(default_factory=dict)
    stage_weights: dict[str, float] = field(default_factory=dict)
    status_weights: dict[str, float] = field(default_factory=dict)
    question_key_weights: dict[str, float] = field(default_factory=dict)
    rule_prefix_weights: dict[str, float] = field(default_factory=dict)
    feature_count_weight: float = 0.004
    max_feature_count: int = 8
    alignment_weight: float = 0.18
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


def question_ranking_policy_runtime() -> QuestionRankingPolicy:
    return load_shadow_question_ranking_policy()


def load_shadow_question_ranking_policy() -> QuestionRankingPolicy:
    latest = _shadow_policy_file_path()
    if not latest.exists():
        return default_question_ranking_policy()
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default_question_ranking_policy()
    if payload.get("status") not in {"ready", "ready_for_apply", "needs_review"}:
        return default_question_ranking_policy()
    policy_payload = payload.get("shadow_policy") or payload.get("policy")
    if not isinstance(policy_payload, dict):
        return default_question_ranking_policy()
    normalized: dict[str, Any] = {
        field_name: value
        for field_name, value in policy_payload.items()
        if field_name in QuestionRankingPolicy.__dataclass_fields__
    }
    try:
        return QuestionRankingPolicy(
            policy_id=normalized.get("policy_id", "v20.question_ranking.shadow_runtime"),
            domain_weights=normalized.get("domain_weights", {}),
            stage_weights=normalized.get("stage_weights", {}),
            status_weights=normalized.get("status_weights", {}),
            question_key_weights=normalized.get("question_key_weights", {}),
            rule_prefix_weights=normalized.get("rule_prefix_weights", {}),
            feature_count_weight=normalized.get("feature_count_weight", default_question_ranking_policy().feature_count_weight),
            max_feature_count=normalized.get("max_feature_count", default_question_ranking_policy().max_feature_count),
            alignment_weight=normalized.get("alignment_weight", default_question_ranking_policy().alignment_weight),
            max_adjustment=normalized.get("max_adjustment", default_question_ranking_policy().max_adjustment),
            source="shadow_learning",
            status=policy_payload.get("status", "active"),
            guardrails=tuple(policy_payload.get("guardrails", ())),
        )
    except TypeError:
        return default_question_ranking_policy()


def _shadow_policy_file_path() -> Path:
    return local_jsonl_store_from_env().runtime_dir / SHADOW_POLICY_PATH_SUFFIX


def rank_question_rows(rows: tuple[object, ...], policy: QuestionRankingPolicy | None = None) -> tuple[object, ...]:
    policy = policy or default_question_ranking_policy()
    scored = tuple((_adjusted_score(row, policy), row) for row in rows)
    return tuple(row for _score, row in sorted(scored, key=lambda item: (item[0], getattr(item[1], "question_key", "")), reverse=True))


def question_ranking_manifest() -> dict[str, object]:
    policy = question_ranking_policy_runtime()
    return {
        "version": "v20.question_ranking_manifest.v1",
        "default_policy": policy.to_dict(),
        "policy_path": str(_shadow_policy_file_path()),
        "policy_status": "shadow" if policy.source == "shadow_learning" else "deterministic_default",
        "allowed_learning_inputs": [
            "anonymized_feedback_summary",
            "synthetic_suite_result",
            "corpus_coverage_gap",
            "question_selection_outcome",
            "question_agent_state",
            "answered_question_suppression",
            "followup_depth_outcome",
            "decision_report_validation",
            "practitioner_control_feedback",
        ],
        "blocked_learning_outputs": [
            "new_question_key",
            "new_chart_fact",
            "rule_activation",
            "answer_conclusion",
            "answered_memory_mutation_without_user_action",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_RANKING_IS_REORDER_ONLY",
            "DYNAMIC_DECISION_CANDIDATES_ARE_AUTHORITATIVE",
            "LEARNED_POLICY_REQUIRES_PROMOTION_GATE",
            "SHADOW_POLICY_CAN_RUN_READ_ONLY",
            "QUESTION_AGENT_MEMORY_IS_SESSION_INPUT",
        ],
    }


def _adjusted_score(row: object, policy: QuestionRankingPolicy) -> float:
    base = _safe_float(row, "score")
    domain = str(getattr(row, "domain", ""))
    stage = str(getattr(row, "measurement_stage", ""))
    status = str(getattr(row, "source_decision_status", ""))
    question_key = str(getattr(row, "question_key", ""))
    rule_key = str(getattr(row, "source_rule_key", ""))
    feature_count = len(tuple(getattr(row, "source_feature_ids", ())))
    alignment = _safe_float(row, "alignment_score")
    adjustment = (
        policy.domain_weights.get(domain, 0.0)
        + policy.stage_weights.get(stage, 0.0)
        + policy.status_weights.get(status, 0.0)
        + policy.question_key_weights.get(question_key, 0.0)
        + _rule_prefix_weight(rule_key, policy)
        + min(policy.max_feature_count, feature_count) * policy.feature_count_weight
        + alignment * policy.alignment_weight
    )
    bounded = _apply_bounded_adjustment(policy, adjustment)
    return round(base + bounded, 3)


def _apply_bounded_adjustment(policy: QuestionRankingPolicy, adjustment: float) -> float:
    # Explicit runtime policies are expected to fully own their scale and may include larger
    # weights for controlled experiments. Learnable shadow policies keep hard bounds.
    if policy.source == "shadow_learning":
        return max(-policy.max_adjustment, min(policy.max_adjustment, adjustment))
    return adjustment


def _rule_prefix_weight(rule_key: str, policy: QuestionRankingPolicy) -> float:
    if not rule_key:
        return 0.0
    prefix = _rule_prefix(rule_key)
    return float(policy.rule_prefix_weights.get(prefix, 0.0))


def _rule_prefix(rule_key: str) -> str:
    parts = str(rule_key).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return str(rule_key)


def _safe_float(row: object, attr: str, default: float = 0.0) -> float:
    try:
        return float(getattr(row, attr))
    except (TypeError, ValueError, AttributeError):
        return default
