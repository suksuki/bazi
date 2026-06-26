from __future__ import annotations

from dataclasses import dataclass

from v20.corpus.coverage import CorpusCoveragePlan, build_corpus_coverage_plan
from v20.learning_orchestrator.job_schema import LearningJobProfile


@dataclass(frozen=True)
class LearningDatasetPlan:
    dataset_key: str
    source_kind: str
    target_case_count: int
    deterministic_case_count: int
    synthetic_case_count: int
    interaction_signal_sources: tuple[str, ...]
    llm_eval_sample_limit: int
    full_corpus_enabled: bool
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "DATASET_PLAN_ONLY",
        "NO_USER_FREE_TEXT_AS_CORE_TRUTH",
        "FULL_518K_IS_DETERMINISTIC_REPLAY",
        "LLM_EVAL_IS_SAMPLED_ONLY",
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_key": self.dataset_key,
            "source_kind": self.source_kind,
            "target_case_count": self.target_case_count,
            "deterministic_case_count": self.deterministic_case_count,
            "synthetic_case_count": self.synthetic_case_count,
            "interaction_signal_sources": list(self.interaction_signal_sources),
            "llm_eval_sample_limit": self.llm_eval_sample_limit,
            "full_corpus_enabled": self.full_corpus_enabled,
            "runtime_mutation": self.runtime_mutation,
            "guardrails": list(self.guardrails),
        }


def build_learning_dataset_plan(
    profile: LearningJobProfile,
    *,
    corpus_plan: CorpusCoveragePlan | None = None,
) -> LearningDatasetPlan:
    plan = corpus_plan or build_corpus_coverage_plan(shard_count=profile.shard_count, batch_size=profile.batch_size)
    full_enabled = profile.target_case_count >= plan.target_case_count
    deterministic_count = plan.target_case_count if full_enabled else profile.target_case_count
    return LearningDatasetPlan(
        dataset_key=f"v20.learning_dataset.{profile.job_key}",
        source_kind=profile.dataset_mode,
        target_case_count=profile.target_case_count,
        deterministic_case_count=deterministic_count,
        synthetic_case_count=14,
        interaction_signal_sources=(
            "question_review_ledger",
            "role_question_click_ledger",
            "practitioner_calibration_ledger",
            "latent_event_calibration_ledger",
            "orchestrator_policy_observability_ledger",
        ),
        llm_eval_sample_limit=profile.llm_eval_sample_limit,
        full_corpus_enabled=full_enabled,
    )
