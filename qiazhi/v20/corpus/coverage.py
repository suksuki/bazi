from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from typing import Any

from v20.corpus.enumerator import FULL_CORPUS_CASE_COUNT, sample_corpus_cases

FULL_CORPUS_TARGET_COUNT = FULL_CORPUS_CASE_COUNT


@dataclass(frozen=True)
class CorpusShard:
    shard_id: str
    start_index: int
    end_index: int
    case_count: int
    batch_size: int
    batch_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CorpusCoveragePlan:
    version: str
    target_case_count: int
    shard_count: int
    batch_size: int
    shards: tuple[CorpusShard, ...]
    sample_case_ids: tuple[str, ...]
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "CORPUS_PLAN_ONLY",
        "NO_DESTINY_TRUTH_LABEL",
        "PRECOMPUTE_STRUCTURAL_FEATURES_ONLY",
        "LEARNING_OUTPUT_REQUIRES_VALIDATION_AND_DECISION",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "target_case_count": self.target_case_count,
            "shard_count": self.shard_count,
            "batch_size": self.batch_size,
            "shards": [row.to_dict() for row in self.shards],
            "sample_case_ids": list(self.sample_case_ids),
            "runtime_mutation": self.runtime_mutation,
            "guardrails": list(self.guardrails),
        }


def build_corpus_coverage_plan(*, shard_count: int = 64, batch_size: int = 256) -> CorpusCoveragePlan:
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    shard_size = ceil(FULL_CORPUS_TARGET_COUNT / shard_count)
    shards: list[CorpusShard] = []
    for index in range(shard_count):
        start = index * shard_size
        end = min(FULL_CORPUS_TARGET_COUNT, start + shard_size)
        if start >= end:
            break
        case_count = end - start
        shards.append(
            CorpusShard(
                shard_id=f"v20.corpus.shard.{index:03d}",
                start_index=start,
                end_index=end,
                case_count=case_count,
                batch_size=batch_size,
                batch_count=ceil(case_count / batch_size),
            )
        )
    return CorpusCoveragePlan(
        version="v20.corpus_coverage_plan.v1",
        target_case_count=FULL_CORPUS_TARGET_COUNT,
        shard_count=len(shards),
        batch_size=batch_size,
        shards=tuple(shards),
        sample_case_ids=tuple(case.case_id for case in sample_corpus_cases(limit=12)),
    )
