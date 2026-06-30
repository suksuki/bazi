from __future__ import annotations

from v40.contracts.base import ReleaseRecommendation
from v40.contracts.evaluation import EvaluationBatchSummary, TrainingReplayBatchSummary
from v40.contracts.training import GlobalWeightVersion


def build_candidate_weight_version_from_batch(
    *,
    summary: EvaluationBatchSummary,
    weight_version_id: str,
    source_training_run_id: str,
    release_gate_id: str,
) -> GlobalWeightVersion:
    if summary.recommendation != ReleaseRecommendation.APPROVE:
        raise ValueError("candidate weight version requires approved batch summary")
    if not release_gate_id.strip():
        raise ValueError("candidate weight version requires release_gate_id")
    return GlobalWeightVersion(
        weight_version_id=weight_version_id,
        source_training_run_id=source_training_run_id,
        release_gate_id=release_gate_id,
        active=False,
    )


def build_candidate_weight_version_from_replay_batch(
    *,
    summary: TrainingReplayBatchSummary,
    weight_version_id: str,
    source_training_run_id: str,
    release_gate_id: str,
) -> GlobalWeightVersion:
    if summary.recommendation != ReleaseRecommendation.APPROVE:
        raise ValueError("candidate weight version requires approved replay batch summary")
    if summary.production_write_allowed:
        raise ValueError("replay batch summary must not allow production write")
    if summary.replay_count <= 0:
        raise ValueError("candidate weight version requires replay evidence")
    if not release_gate_id.strip():
        raise ValueError("candidate weight version requires release_gate_id")
    return GlobalWeightVersion(
        weight_version_id=weight_version_id,
        source_training_run_id=source_training_run_id,
        release_gate_id=release_gate_id,
        active=False,
    )
