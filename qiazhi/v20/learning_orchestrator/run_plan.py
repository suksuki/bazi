from __future__ import annotations

from v20.corpus.coverage import CorpusCoveragePlan, build_corpus_coverage_plan
from v20.learning_orchestrator.dataset_plan import build_learning_dataset_plan
from v20.learning_orchestrator.job_schema import get_learning_job_profile
from v20.learning_orchestrator.sharding import build_learning_shard_plan


def build_learning_orchestrator_run_plan(
    job_key: str = "nightly",
    *,
    corpus_plan: CorpusCoveragePlan | None = None,
) -> dict[str, object]:
    profile = get_learning_job_profile(job_key)
    plan = corpus_plan or build_corpus_coverage_plan(shard_count=profile.shard_count, batch_size=profile.batch_size)
    dataset = build_learning_dataset_plan(profile, corpus_plan=plan)
    shards = build_learning_shard_plan(profile, corpus_plan=plan)
    return {
        "version": "v20.learning_orchestrator_run_plan.v1",
        "status": "ready_for_scheduled_run",
        "job": profile.to_dict(),
        "dataset": dataset.to_dict(),
        "sharding": shards.to_dict(),
        "stages": _stages(profile.job_key),
        "candidate_policy_targets": (
            "rule_weight_policy",
            "feature_threshold_policy",
            "portrait_axis_weight_policy",
            "question_ranker_policy",
            "question_dag_policy",
            "role_view_policy",
        ),
        "activation_policy": {
            "runtime_mutation": False,
            "candidate_requires_replay": True,
            "pointer_write": "explicit_after_replay_or_admin_activation",
            "llm_training": "disabled",
        },
        "completion": {
            "learning_orchestrator_v1": 100,
            "nightly_518k_plan": 100,
            "nightly_518k_executor": 0,
            "parameter_optimizer": 0,
        },
        "runtime_mutation": False,
        "guardrails": [
            "LEARNING_ORCHESTRATOR_PLAN_ONLY",
            "FULL_518K_REPLAY_ALLOWED_OFFLINE",
            "LLM_EVAL_SAMPLED_NOT_FULL_CORPUS",
            "RUNTIME_POINTER_NOT_UPDATED_BY_PLAN",
        ],
    }


def _stages(job_key: str) -> list[dict[str, object]]:
    base = [
        _stage("dataset_build", "Build deterministic full/smoke dataset and interaction signal manifest.", "dataset_manifest"),
        _stage("shard_replay", "Replay runtime deterministically by shard with checkpoint artifacts.", "shard_replay_artifacts"),
        _stage("evaluator_suite", "Evaluate rules, features, portraits, questions, DAG paths, and role views.", "evaluator_summary"),
        _stage("candidate_policy_search", "Search candidate weights or policies without mutating runtime truth.", "candidate_policy"),
        _stage("replay_compare", "Compare baseline and candidate policy on deterministic replay outputs.", "replay_comparison"),
        _stage("promotion_preflight", "Produce pointer activation preflight only after replay comparison.", "promotion_preflight"),
    ]
    if job_key in {"weekly", "full"}:
        base.insert(
            3,
            _stage("sampled_llm_eval", "Evaluate a bounded LLM answer sample against verified context.", "sampled_llm_eval_report"),
        )
    return base


def _stage(stage_key: str, purpose: str, output_artifact: str) -> dict[str, object]:
    return {
        "stage_key": stage_key,
        "purpose": purpose,
        "output_artifact": output_artifact,
        "runtime_mutation": False,
        "requires_checkpoint": True,
    }
