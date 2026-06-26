from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from v20.corpus.coverage import CorpusCoveragePlan, CorpusShard, build_corpus_coverage_plan
from v20.learning_orchestrator.job_schema import LearningJobProfile


@dataclass(frozen=True)
class LearningShardPlan:
    shard_count: int
    batch_size: int
    estimated_batch_count: int
    parallelism_hint: int
    first_shards: tuple[CorpusShard, ...]
    checkpoint_policy: str = "write_shard_artifact_then_merge"
    resume_policy: str = "skip_completed_shards_by_artifact_key"
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "SHARD_PLAN_ONLY",
        "CHECKPOINT_BEFORE_MERGE",
        "RESUMABLE_FULL_REPLAY",
        "NO_RUNTIME_POINTER_WRITE_IN_SHARD",
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "shard_count": self.shard_count,
            "batch_size": self.batch_size,
            "estimated_batch_count": self.estimated_batch_count,
            "parallelism_hint": self.parallelism_hint,
            "first_shards": [row.to_dict() for row in self.first_shards],
            "checkpoint_policy": self.checkpoint_policy,
            "resume_policy": self.resume_policy,
            "runtime_mutation": self.runtime_mutation,
            "guardrails": list(self.guardrails),
        }


def build_learning_shard_plan(
    profile: LearningJobProfile,
    *,
    corpus_plan: CorpusCoveragePlan | None = None,
) -> LearningShardPlan:
    plan = corpus_plan or build_corpus_coverage_plan(shard_count=profile.shard_count, batch_size=profile.batch_size)
    estimated_batch_count = sum(ceil(shard.case_count / profile.batch_size) for shard in plan.shards)
    return LearningShardPlan(
        shard_count=plan.shard_count,
        batch_size=profile.batch_size,
        estimated_batch_count=estimated_batch_count,
        parallelism_hint=_parallelism_hint(profile),
        first_shards=tuple(plan.shards[:3]),
    )


def _parallelism_hint(profile: LearningJobProfile) -> int:
    if profile.job_key == "fast":
        return 1
    if profile.job_key == "nightly":
        return 8
    if profile.job_key == "weekly":
        return 12
    return 16
