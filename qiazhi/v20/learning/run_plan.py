from __future__ import annotations

from v20.corpus.coverage import CorpusCoveragePlan, build_corpus_coverage_plan
from v20.learning.evolution import build_evolution_dry_run_plan


def build_learning_run_plan(*, corpus_plan: CorpusCoveragePlan | None = None) -> dict[str, object]:
    plan = corpus_plan or build_corpus_coverage_plan()
    evolution = build_evolution_dry_run_plan(corpus_plan=plan)
    stages = (
        _stage(
            "structural_precompute",
            "Precompute ChartFacts, CoreInference, BaziFeature, questions, knowledge refs, and answer-plan metadata.",
            "corpus_snapshot",
        ),
        _stage(
            "coverage_gap_clustering",
            "Cluster sparse domains, boundary misses, and synthetic-case coverage gaps.",
            "coverage_gap_report",
        ),
        _stage(
            "active_policy_learning",
            "Produce draft ranking, retrieval, or calibration policies in active iteration mode.",
            "policy_proposal_artifact",
        ),
        _stage(
            "validation_and_decision_gate",
            "Run synthetic validation and require runtime replay before continuous tuning.",
            "decision_record",
        ),
    )
    return {
        "version": "v20.learning_run_plan.v1",
        "status": evolution["status"],
        "target_case_count": plan.target_case_count,
        "shard_count": plan.shard_count,
        "batch_size": plan.batch_size,
        "estimated_batch_count": sum(shard.batch_count for shard in plan.shards),
        "first_shards": [shard.to_dict() for shard in plan.shards[:3]],
        "allowed_algorithm_tracks": evolution["allowed_algorithm_tracks"],
        "deferred_algorithm_tracks": evolution["deferred_algorithm_tracks"],
        "stages": stages,
        "artifact_outputs": (
            "corpus_snapshot_manifest",
            "coverage_gap_report",
            "active_policy_artifact",
            "synthetic_validation_report",
            "decision_record",
        ),
        "blocked_outputs": evolution["blocked_actions"],
        "runtime_mutation": False,
        "guardrails": [
            "LEARNING_RUN_PLAN_ONLY",
            "FULL_CORPUS_PRECOMPUTE_IS_STRUCTURAL",
            "NO_DESTINY_TRUTH_LABELS",
            "POLICY_ACTIVATES_WITH_CONTINUOUS_ITERATION",
        ],
    }


def _stage(stage_key: str, purpose: str, output_artifact: str) -> dict[str, object]:
    return {
        "stage_key": stage_key,
        "purpose": purpose,
        "output_artifact": output_artifact,
        "runtime_mutation": False,
        "requires_validation": True,
    }
