from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

LearningJobKey = Literal["fast", "nightly", "weekly", "full"]


@dataclass(frozen=True)
class LearningJobProfile:
    job_key: LearningJobKey
    label: str
    cadence: str
    dataset_mode: str
    target_case_count: int
    shard_count: int
    batch_size: int
    llm_eval_sample_limit: int
    evaluator_tracks: tuple[str, ...]
    optimizer_tracks: tuple[str, ...]
    artifact_outputs: tuple[str, ...]
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "LEARNING_JOB_PROFILE_ONLY",
        "NO_DIRECT_RUNTIME_MUTATION",
        "NO_LLM_FACT_GENERATION",
        "RUNTIME_USES_POINTER_AFTER_REPLAY",
    )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evaluator_tracks"] = list(self.evaluator_tracks)
        payload["optimizer_tracks"] = list(self.optimizer_tracks)
        payload["artifact_outputs"] = list(self.artifact_outputs)
        payload["guardrails"] = list(self.guardrails)
        return payload


def build_learning_job_profiles() -> tuple[LearningJobProfile, ...]:
    return (
        LearningJobProfile(
            job_key="fast",
            label="Fast Learning Smoke",
            cadence="on_demand_or_commit",
            dataset_mode="synthetic_smoke_and_recent_ledgers",
            target_case_count=14,
            shard_count=1,
            batch_size=64,
            llm_eval_sample_limit=0,
            evaluator_tracks=("synthetic", "question_dag", "role_view", "answer_safety"),
            optimizer_tracks=("question_ranking_light", "role_view_light"),
            artifact_outputs=("coverage_report", "failure_report", "candidate_report"),
        ),
        LearningJobProfile(
            job_key="nightly",
            label="Nightly Full Deterministic Replay",
            cadence="nightly_low_traffic_window",
            dataset_mode="full_518k_deterministic_replay",
            target_case_count=518_400,
            shard_count=128,
            batch_size=512,
            llm_eval_sample_limit=0,
            evaluator_tracks=("core_feature", "rule", "portrait", "question", "question_dag", "role_view"),
            optimizer_tracks=("threshold_grid_search", "rule_weight_search", "portrait_weight_search", "question_ranker_bandit"),
            artifact_outputs=("full_replay_manifest", "evaluator_summary", "candidate_policy", "replay_comparison"),
        ),
        LearningJobProfile(
            job_key="weekly",
            label="Weekly Deep Policy Search",
            cadence="weekly_deep_window",
            dataset_mode="full_518k_plus_boundary_samples",
            target_case_count=518_400,
            shard_count=128,
            batch_size=512,
            llm_eval_sample_limit=512,
            evaluator_tracks=("core_feature", "rule", "portrait", "question", "question_dag", "role_view", "llm_answer_sample"),
            optimizer_tracks=("bayesian_parameter_search", "contextual_bandit", "dag_policy_search"),
            artifact_outputs=("deep_search_manifest", "candidate_policy", "sampled_llm_eval", "promotion_preflight"),
        ),
        LearningJobProfile(
            job_key="full",
            label="Monthly Full Baseline Rebuild",
            cadence="monthly_or_manual",
            dataset_mode="full_518k_baseline_rebuild",
            target_case_count=518_400,
            shard_count=256,
            batch_size=512,
            llm_eval_sample_limit=1024,
            evaluator_tracks=("core_feature", "rule", "portrait", "question", "question_dag", "role_view", "llm_answer_sample"),
            optimizer_tracks=("baseline_rebuild", "parameter_sweep", "policy_comparison"),
            artifact_outputs=("baseline_manifest", "full_evaluator_report", "policy_version_candidate", "runtime_pointer_preflight"),
        ),
    )


def get_learning_job_profile(job_key: str = "nightly") -> LearningJobProfile:
    profiles = {profile.job_key: profile for profile in build_learning_job_profiles()}
    return profiles.get(job_key, profiles["nightly"])
