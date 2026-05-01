from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from typing import Any

from v20.corpus.coverage import build_corpus_coverage_plan
from v20.corpus.enumerator import FULL_CORPUS_CASE_COUNT, iter_canonical_cases
from v20.corpus.precompute_runner import precompute_case


@dataclass(frozen=True)
class PrecomputeCostEstimate:
    target_case_count: int
    per_case_ms: float
    writer_overhead_multiplier: float
    estimated_compute_seconds: float
    estimated_total_seconds: float
    estimated_total_minutes: float
    dgx_required_for_deterministic_labels: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_full_precompute_manifest(
    *,
    shard_count: int = 64,
    batch_size: int = 256,
    per_case_ms: float = 1.6,
    writer_overhead_multiplier: float = 3.0,
) -> dict[str, object]:
    plan = build_corpus_coverage_plan(shard_count=shard_count, batch_size=batch_size)
    estimate = estimate_precompute_cost(
        per_case_ms=per_case_ms,
        writer_overhead_multiplier=writer_overhead_multiplier,
    )
    return {
        "version": "v20.full_corpus_precompute_manifest.v1",
        "status": "ready_for_dry_run",
        "target_case_count": FULL_CORPUS_CASE_COUNT,
        "shard_count": plan.shard_count,
        "batch_size": plan.batch_size,
        "estimated_batch_count": sum(row.batch_count for row in plan.shards),
        "artifact_outputs": [
            "corpus_label_snapshot_jsonl",
            "corpus_feature_domain_coverage",
            "corpus_portrait_axis_coverage",
            "corpus_rule_proposal_support_index",
            "dataset_registry_record",
            "run_registry_record",
        ],
        "label_scope": [
            "chart_facts",
            "core_inference_capacity",
            "feature_ids_and_domains",
            "macro_feature_domains",
            "measurement_domains",
            "question_keys",
            "knowledge_ids",
            "portrait_domains",
            "relation_types",
            "ten_god_labels",
        ],
        "storage_targets": [
            "local_jsonl_dry_run",
            "postgres_v20_corpus_snapshots_after_explicit_apply",
            "parquet_or_object_storage_future",
        ],
        "cost_estimate": estimate.to_dict(),
        "runtime_mutation": False,
        "guardrails": [
            "FULL_PRECOMPUTE_MANIFEST_ONLY",
            "NO_DESTINY_TRUTH_LABEL",
            "NO_RULE_ACTIVATION_FROM_CORPUS",
            "POSTGRES_WRITE_REQUIRES_EXPLICIT_JOB",
            "DGX_RESERVED_FOR_MODEL_TRAINING_NOT_BASIC_LABELS",
        ],
    }


def preview_full_precompute_batch(start: int = 0, limit: int = 4) -> dict[str, object]:
    cases = iter_canonical_cases(start=start, limit=limit)
    snapshots = tuple(precompute_case(case) for case in cases)
    return {
        "version": "v20.full_corpus_precompute_preview.v1",
        "status": "ready" if snapshots else "empty",
        "start_index": start,
        "requested_limit": limit,
        "returned_count": len(snapshots),
        "snapshots": snapshots,
        "runtime_mutation": False,
        "guardrails": [
            "PREVIEW_ONLY",
            "NO_STORAGE_WRITE",
            "NO_DESTINY_TRUTH_LABEL",
        ],
    }


def estimate_precompute_cost(
    *,
    target_case_count: int = FULL_CORPUS_CASE_COUNT,
    per_case_ms: float = 1.6,
    writer_overhead_multiplier: float = 3.0,
) -> PrecomputeCostEstimate:
    compute_seconds = target_case_count * per_case_ms / 1000.0
    total_seconds = compute_seconds * writer_overhead_multiplier
    return PrecomputeCostEstimate(
        target_case_count=target_case_count,
        per_case_ms=per_case_ms,
        writer_overhead_multiplier=writer_overhead_multiplier,
        estimated_compute_seconds=round(compute_seconds, 3),
        estimated_total_seconds=round(total_seconds, 3),
        estimated_total_minutes=round(total_seconds / 60.0, 3),
    )


def shard_for_index(index: int, *, shard_count: int = 64) -> dict[str, object]:
    if index < 0 or index >= FULL_CORPUS_CASE_COUNT:
        raise IndexError(f"V20 full corpus index out of range: {index}")
    shard_size = ceil(FULL_CORPUS_CASE_COUNT / shard_count)
    shard_index = index // shard_size
    start = shard_index * shard_size
    end = min(FULL_CORPUS_CASE_COUNT, start + shard_size)
    return {
        "version": "v20.full_corpus_shard_lookup.v1",
        "index": index,
        "shard_id": f"v20.corpus.shard.{shard_index:03d}",
        "start_index": start,
        "end_index": end,
        "runtime_mutation": False,
    }
