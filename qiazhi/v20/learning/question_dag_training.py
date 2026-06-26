from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from v20.interaction.question_dag import QUESTION_DAG_STAGES, role_default_dag_path
from v20.interaction.question_review import QUESTION_REVIEW_ACTIONS, QUESTION_REVIEW_REASONS
from v20.learning.question_review_training import build_question_review_training_report
from v20.storage.local_jsonl import LocalJsonlStore
from v20.validation.question_dag_coherence import build_question_dag_coherence_report
from v20.validation.synthetic_schema import SyntheticBaziCase, minimal_synthetic_bazi_cases


def build_question_dag_training_report(
    cases: tuple[SyntheticBaziCase, ...] | None = None,
    question_review_training_report: dict[str, object] | None = None,
    store: LocalJsonlStore | None = None,
) -> dict[str, Any]:
    rows = tuple(cases or minimal_synthetic_bazi_cases())
    review_training = question_review_training_report or build_question_review_training_report(store=store)
    transition_counts = _transition_counts(rows)
    role_policy = _role_default_policy()
    synthetic_policy = _synthetic_transition_policy(transition_counts)
    review_policy = _review_policy(review_training)
    stage_coverage = _stage_coverage(rows)
    coherence_report = build_question_dag_coherence_report(rows)
    candidate_policy = {
        "version": "v20.question_dag_candidate_policy.v1",
        "policy_key": "next_question_policy",
        "role_default_policy": role_policy,
        "synthetic_transition_policy": synthetic_policy,
        "question_review_policy": review_policy,
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_DAG_POLICY_IS_CANDIDATE_ONLY",
            "NO_RUNTIME_POINTER_MUTATION",
            "NO_CORE_FACT_MUTATION",
            "NO_RULE_TRUTH_MUTATION",
        ],
    }
    return {
        "version": "v20.question_dag_training_report.v1",
        "status": "ready" if rows and coherence_report["status"] == "pass" else "needs_review" if rows else "empty",
        "case_count": len(rows),
        "training_targets": [
            "question_stage_transition",
            "role_default_dag_path",
            "question_review_policy",
        ],
        "stage_coverage": stage_coverage,
        "coherence_report": coherence_report,
        "question_review_training_status": review_training.get("status", ""),
        "transition_count": sum(transition_counts.values()),
        "candidate_policy": candidate_policy,
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_DAG_TRAINING_IS_OFFLINE",
            "CANDIDATE_POLICY_ONLY",
            "SYNTHETIC_CASES_VALIDATE_BEFORE_RUNTIME",
        ],
    }


def _transition_counts(cases: tuple[SyntheticBaziCase, ...]) -> Counter[tuple[str, str]]:
    counts: Counter[tuple[str, str]] = Counter()
    for case in cases:
        stages = tuple(stage for stage in case.expected.dag_stages if stage in QUESTION_DAG_STAGES)
        for left, right in zip(stages, stages[1:]):
            counts[(left, right)] += 1
    return counts


def _synthetic_transition_policy(counts: Counter[tuple[str, str]]) -> tuple[dict[str, Any], ...]:
    total_by_stage: dict[str, int] = defaultdict(int)
    for (from_stage, _to_stage), count in counts.items():
        total_by_stage[from_stage] += count
    rows = []
    for (from_stage, to_stage), count in sorted(counts.items()):
        total = max(1, total_by_stage[from_stage])
        rows.append(
            {
                "from_stage": from_stage,
                "to_stage": to_stage,
                "support_count": count,
                "priority": round(count / total, 3),
                "training_source": "synthetic_bazi_case_expected_dag_path",
            }
        )
    return tuple(rows)


def _role_default_policy() -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "role_key": role_key,
            "default_path": role_default_dag_path(role_key),
            "training_source": "role_aware_brain_design",
        }
        for role_key in ("guest", "user", "analyst", "admin")
    )


def _review_policy(question_review_training_report: dict[str, object]) -> dict[str, Any]:
    recommendations = _review_recommendations(question_review_training_report)
    return {
        "actions": QUESTION_REVIEW_ACTIONS,
        "reasons": QUESTION_REVIEW_REASONS,
        "source_report_version": question_review_training_report.get("version", ""),
        "source_review_count": question_review_training_report.get("review_count", 0),
        "recommendation_count": len(recommendations),
        "training_recommendations": recommendations,
        "candidate_effects": {
            "approve": "keep_or_promote",
            "rewrite": "template_rewrite_candidate",
            "downrank": "ranking_penalty_candidate",
            "merge": "dedupe_candidate",
            "delete": "suppression_candidate",
            "suppress_question_candidate": "ranking_penalty_candidate",
            "rewrite_question_candidate": "template_rewrite_candidate",
            "suppress_role_stage_question_candidate": "role_stage_penalty_candidate",
        },
        "runtime_mutation": False,
    }


def _review_recommendations(question_review_training_report: dict[str, object]) -> tuple[dict[str, Any], ...]:
    rows = []
    for recommendation in question_review_training_report.get("recommendations", ()):
        if not isinstance(recommendation, dict):
            continue
        rows.append({
            "recommendation_key": str(recommendation.get("recommendation_key", "")),
            "recommendation_type": str(recommendation.get("recommendation_type", "")),
            "question_key": str(recommendation.get("question_key", "")),
            "role_target": str(recommendation.get("role_target", "")),
            "stage": str(recommendation.get("stage", "")),
            "domain": str(recommendation.get("domain", "")),
            "basis": str(recommendation.get("basis", "")),
            "training_source": "question_review_training",
            "runtime_allowed": False,
        })
    return tuple(rows)


def _stage_coverage(cases: tuple[SyntheticBaziCase, ...]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    for case in cases:
        counts.update(stage for stage in case.expected.dag_stages if stage in QUESTION_DAG_STAGES)
    covered = tuple(stage for stage in QUESTION_DAG_STAGES if counts[stage] > 0)
    missing = tuple(stage for stage in QUESTION_DAG_STAGES if counts[stage] == 0)
    return {
        "covered_stages": covered,
        "missing_stages": missing,
        "stage_counts": {stage: counts[stage] for stage in QUESTION_DAG_STAGES},
        "coverage_ratio": round(len(covered) / max(1, len(QUESTION_DAG_STAGES)), 3),
    }
