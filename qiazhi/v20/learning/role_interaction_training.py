from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from v20.interaction.question_dag import role_default_dag_path, visibility_for_role
from v20.interaction.question_review import QUESTION_REVIEW_ACTIONS, QUESTION_REVIEW_REASONS
from v20.validation.synthetic_schema import SyntheticBaziCase, minimal_synthetic_bazi_cases


ROLE_INTERACTION_TARGETS: tuple[str, ...] = ("guest", "user", "analyst", "admin")


def build_role_interaction_training_report(
    cases: tuple[SyntheticBaziCase, ...] | None = None,
) -> dict[str, Any]:
    rows = tuple(cases or minimal_synthetic_bazi_cases())
    role_policies = tuple(_role_policy(role, rows) for role in ROLE_INTERACTION_TARGETS)
    return {
        "version": "v20.role_interaction_training_report.v1",
        "status": "ready" if rows else "empty",
        "case_count": len(rows),
        "training_targets": [
            "guest_entry_policy",
            "user_guided_policy",
            "analyst_review_policy",
            "admin_observe_policy",
        ],
        "candidate_policy": {
            "version": "v20.role_interaction_candidate_policy.v1",
            "policy_key": "role_interaction_policy",
            "role_policies": role_policies,
            "question_review_actions": QUESTION_REVIEW_ACTIONS,
            "question_review_reasons": QUESTION_REVIEW_REASONS,
            "runtime_mutation": False,
            "guardrails": [
                "ROLE_INTERACTION_POLICY_IS_CANDIDATE_ONLY",
                "NO_RUNTIME_POINTER_MUTATION",
                "NO_CORE_FACT_MUTATION",
                "NO_RULE_TRUTH_MUTATION",
            ],
        },
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_INTERACTION_TRAINING_IS_OFFLINE",
            "CANDIDATE_POLICY_ONLY",
            "USER_INTERACTION_DOES_NOT_MUTATE_CORE_MODEL",
        ],
    }


def _role_policy(role_key: str, cases: tuple[SyntheticBaziCase, ...]) -> dict[str, Any]:
    stage_counts = _role_stage_counts(role_key, cases)
    forbidden_counts = _role_forbidden_counts(role_key, cases)
    return {
        "role_key": role_key,
        "default_path": role_default_dag_path(role_key),
        "visibility": visibility_for_role(role_key),
        "interaction_mode": _interaction_mode(role_key),
        "answer_mode": _answer_mode(role_key),
        "learning_signal": _learning_signal(role_key),
        "stage_priority": _stage_priority(stage_counts),
        "forbidden_stage_policy": tuple(
            {
                "stage": stage,
                "support_count": count,
                "effect": "suppress_for_role",
            }
            for stage, count in sorted(forbidden_counts.items())
        ),
        "runtime_mutation": False,
    }


def _role_stage_counts(role_key: str, cases: tuple[SyntheticBaziCase, ...]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for case in cases:
        for expectation in case.role_expectations:
            if expectation.role_key == role_key:
                counts.update(expectation.required_stages)
    if not counts:
        counts.update(role_default_dag_path(role_key))
    return counts


def _role_forbidden_counts(role_key: str, cases: tuple[SyntheticBaziCase, ...]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for case in cases:
        for expectation in case.role_expectations:
            if expectation.role_key == role_key:
                counts.update(expectation.forbidden_stages)
        counts.update(case.negative.forbidden_role_stages.get(role_key, ()))
    return counts


def _stage_priority(counts: Counter[str]) -> tuple[dict[str, Any], ...]:
    total = max(1, sum(counts.values()))
    grouped: dict[str, int] = defaultdict(int)
    for stage, count in counts.items():
        grouped[stage] += count
    return tuple(
        {
            "stage": stage,
            "support_count": count,
            "priority": round(count / total, 3),
        }
        for stage, count in sorted(grouped.items())
    )


def _interaction_mode(role_key: str) -> str:
    return {
        "guest": "entry_choice",
        "user": "guided_choice",
        "analyst": "structured_review",
        "admin": "system_observe",
    }[role_key]


def _answer_mode(role_key: str) -> str:
    return "llm" if role_key in {"guest", "user"} else "hybrid"


def _learning_signal(role_key: str) -> str:
    return {
        "guest": "interaction_signal",
        "user": "preference_signal",
        "analyst": "calibration_signal",
        "admin": "validation_signal",
    }[role_key]
