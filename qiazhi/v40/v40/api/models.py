from __future__ import annotations

from pydantic import Field, model_validator

from v40.contracts.base import V40Model
from v40.contracts.base import RoleKey
from v40.contracts.base import Topic
from v40.contracts.chart import BaziChartFacts, SyntheticCaseSeed
from v40.contracts.evaluation import EvaluationBatchSummary, EvaluationCaseSpec, EvaluationRunResult, ReleaseReadinessSummary
from v40.contracts.runtime import RuntimeResult
from v40.contracts.training import GlobalWeightVersion, LabelTargetType, LabelValue, WeightActivationReview


class EvaluationRunFromRuntimeRequest(V40Model):
    version: str = "v40.evaluation_run_from_runtime_request.v1"
    run_id: str
    case_spec: EvaluationCaseSpec
    runtime: RuntimeResult
    candidate_version: str = "v40-alpha"
    build_release_gate: bool = True
    persist: bool = True
    boundary: str = "evaluation_run_request_evaluates_runtime_without_llm_judge"


class TrainingImpactFromEvaluationRequest(V40Model):
    version: str = "v40.training_impact_from_evaluation_request.v1"
    training_run_id: str
    base_version: str
    candidate_version: str
    evaluation_run: EvaluationRunResult
    persist: bool = True
    boundary: str = "training_impact_request_builds_candidate_diff_without_production_write"


class EvaluationBatchFromRuntimeRequest(V40Model):
    version: str = "v40.evaluation_batch_from_runtime_request.v1"
    batch_id: str
    cases: list[EvaluationCaseSpec]
    runtime: RuntimeResult
    candidate_version: str = "v40-alpha"
    persist: bool = True
    boundary: str = "evaluation_batch_request_runs_many_cases_without_llm_judge"


class CandidateWeightFromBatchRequest(V40Model):
    version: str = "v40.candidate_weight_from_batch_request.v1"
    weight_version_id: str
    source_training_run_id: str
    release_gate_id: str
    batch_summary: EvaluationBatchSummary
    persist: bool = True
    boundary: str = "candidate_weight_request_registers_candidate_without_activation"


class ReleaseReadinessFromBatchesRequest(V40Model):
    version: str = "v40.release_readiness_from_batches_request.v1"
    readiness_id: str
    candidate_version: str
    batches: list[EvaluationBatchSummary]
    persist: bool = True
    boundary: str = "release_readiness_request_aggregates_batches_without_activation"


class WeightActivationReviewRequest(V40Model):
    version: str = "v40.weight_activation_review_request.v1"
    review_id: str
    weight_version: GlobalWeightVersion
    release_readiness: ReleaseReadinessSummary
    reviewed_by_role: RoleKey = "admin"
    persist: bool = True
    boundary: str = "weight_activation_review_request_records_review_without_activation"


class WeightActivationExecutionRequest(V40Model):
    version: str = "v40.weight_activation_execution_request.v1"
    execution_id: str
    review: WeightActivationReview
    weight_version: GlobalWeightVersion
    rollback_version_id: str
    confirm_phrase: str
    boundary: str = "weight_activation_execution_request_requires_explicit_confirmation"


class NativeBaziRuntimeRequest(V40Model):
    version: str = "v40.native_bazi_runtime_request.v1"
    request_id: str
    reading_id: str
    chart_facts: BaziChartFacts
    user_question: str = ""
    topic: Topic = Topic.OVERVIEW
    role_key: RoleKey = "user"
    persist: bool = False
    boundary: str = "native_bazi_runtime_request_uses_v40_chart_facts_without_v30_runtime"


class SyntheticCasesFromSeedsRequest(V40Model):
    version: str = "v40.synthetic_cases_from_seeds_request.v1"
    seeds: list[SyntheticCaseSeed]
    persist: bool = False
    boundary: str = "synthetic_cases_request_builds_evaluation_cases_without_real_world_truth_claim"


class NativeBatchFromSeedsRequest(V40Model):
    version: str = "v40.native_batch_from_seeds_request.v1"
    batch_id: str
    candidate_version: str = "v40-native"
    seeds: list[SyntheticCaseSeed]
    role_key: RoleKey = "user"
    persist: bool = False
    boundary: str = "native_batch_from_seeds_runs_v40_native_runtime_without_v30_state"


class PractitionerCalibrationRequest(V40Model):
    version: str = "v40.practitioner_calibration_request.v1"
    event_id: str
    reading_id: str
    target_type: LabelTargetType = LabelTargetType.BRANCH
    target_ids: list[str] = Field(default_factory=list)
    label: LabelValue = LabelValue.SUPPORTS
    strength: float = Field(default=0.7, ge=0.0, le=1.0)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    reason: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    created_by_role: RoleKey = "practitioner"
    persist: bool = True
    boundary: str = "practitioner_calibration_becomes_training_label_without_chart_fact_mutation"

    @model_validator(mode="after")
    def _calibration_boundary(self) -> "PractitionerCalibrationRequest":
        if self.created_by_role not in {"practitioner", "admin"}:
            raise ValueError("Practitioner calibration requires practitioner or admin role")
        if not self.target_ids:
            raise ValueError("Practitioner calibration requires target_ids")
        return self
