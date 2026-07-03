from __future__ import annotations

from pydantic import Field, model_validator

from v40.contracts.base import V40Model
from v40.contracts.base import RoleKey
from v40.contracts.base import Topic
from v40.contracts.chart import BaziChartFacts, BirthInputCanonical, SyntheticCaseSeed, ZiweiChartFacts
from v40.contracts.context import ClientContext, EngineContext, LocaleContext, RoleContext
from v40.contracts.evaluation import (
    AcceptanceWindowResult,
    EvaluationBatchSummary,
    EvaluationCaseSpec,
    EvaluationRunResult,
    RealCaseRecord,
    ReleaseReadinessSummary,
    TrainingReplayBatchSummary,
    TrainingExampleReplayResult,
)
from v40.contracts.output import ExpressionTelemetry
from v40.contracts.probe import ProbeAnswerResult
from v40.contracts.review import ConsentGrant, PractitionerReviewDecision, PractitionerReviewRequest
from v40.contracts.runtime import RuntimeResult
from v40.contracts.user import BaziProfileRecord
from v40.contracts.training import (
    BatchTrainerV1Result,
    GlobalWeightVersion,
    LabelTargetType,
    LabelValue,
    TrainablePolicyRegistry,
    TrainingAttribution,
    TrainingExampleV2,
    TrainingLabelEvent,
    WeightActivationReview,
)
from v40.migration import MigratedMingliAsset, V30ExportEnvelope


class EvaluationRunFromRuntimeRequest(V40Model):
    version: str = "v40.evaluation_run_from_runtime_request.v1"
    run_id: str
    case_spec: EvaluationCaseSpec
    runtime: RuntimeResult
    candidate_version: str = "v40-alpha"
    build_release_gate: bool = True
    expression_telemetry: ExpressionTelemetry | None = None
    persist: bool = True
    boundary: str = "evaluation_run_request_evaluates_runtime_without_llm_judge"


class ShadowCompareBatchRequest(V40Model):
    version: str = "v40.shadow_compare_batch_request.v1"
    batch_id: str
    exports: list[V30ExportEnvelope]
    persist: bool = True
    boundary: str = "shadow_compare_batch_request_imports_plain_v30_json_without_touching_v30_runtime"

    @model_validator(mode="after")
    def _shadow_batch_boundary(self) -> "ShadowCompareBatchRequest":
        if not self.batch_id.strip():
            raise ValueError("Shadow compare batch request requires batch_id")
        if not self.exports:
            raise ValueError("Shadow compare batch request requires exports")
        return self


class MingliAssetMigrationGateRequest(V40Model):
    version: str = "v40.mingli_asset_migration_gate_request.v1"
    gate_id: str
    reading_id: str
    assets: list[MigratedMingliAsset]
    persist: bool = False
    boundary: str = "mingli_asset_migration_gate_request_accepts_plain_json_assets_without_v30_runtime_import"

    @model_validator(mode="after")
    def _asset_gate_boundary(self) -> "MingliAssetMigrationGateRequest":
        if not self.gate_id.strip():
            raise ValueError("Mingli asset migration gate request requires gate_id")
        if not self.reading_id.strip():
            raise ValueError("Mingli asset migration gate request requires reading_id")
        if not self.assets:
            raise ValueError("Mingli asset migration gate request requires assets")
        return self


class TrainingImpactFromEvaluationRequest(V40Model):
    version: str = "v40.training_impact_from_evaluation_request.v1"
    training_run_id: str
    base_version: str
    candidate_version: str
    evaluation_run: EvaluationRunResult
    persist: bool = True
    boundary: str = "training_impact_request_builds_candidate_diff_without_production_write"


class BatchTrainerV1Request(V40Model):
    version: str = "v40.batch_trainer_v1_request.v1"
    training_run_id: str
    base_registry: TrainablePolicyRegistry
    attributions: list[TrainingAttribution]
    label_events: list[TrainingLabelEvent] = Field(default_factory=list)
    candidate_policy_version: str
    persist_registry: bool = True
    persist_impact: bool = True
    boundary: str = "batch_trainer_v1_request_applies_validated_policy_immediately_with_rollback_without_approval_gate"

    @model_validator(mode="after")
    def _batch_trainer_boundary(self) -> "BatchTrainerV1Request":
        if not self.training_run_id.strip():
            raise ValueError("BatchTrainerV1 request requires training_run_id")
        if not self.candidate_policy_version.strip():
            raise ValueError("BatchTrainerV1 request requires candidate_policy_version")
        if not self.attributions:
            raise ValueError("BatchTrainerV1 request requires attributions")
        return self


class TrainingExampleFromReadingRequest(V40Model):
    version: str = "v40.training_example_from_reading_request.v1"
    example_id: str
    reading_id: str
    topic: Topic = Topic.UNKNOWN
    input_snapshot_ref: str = ""
    runtime_output_ref: str = ""
    persist: bool = True
    boundary: str = "training_example_from_reading_compiles_feedback_without_production_write"

    @model_validator(mode="after")
    def _example_boundary(self) -> "TrainingExampleFromReadingRequest":
        if not self.example_id.strip():
            raise ValueError("Training example request requires example_id")
        if not self.reading_id.strip():
            raise ValueError("Training example request requires reading_id")
        return self


class TrainingExampleReplayRequest(V40Model):
    version: str = "v40.training_example_replay_request.v1"
    replay_id: str
    training_example: TrainingExampleV2
    runtime: RuntimeResult
    candidate_version: str = "v40-alpha"
    persist: bool = True
    include_source_example: bool = True
    boundary: str = "training_example_replay_request_scores_feedback_without_production_write"

    @model_validator(mode="after")
    def _replay_boundary(self) -> "TrainingExampleReplayRequest":
        if not self.replay_id.strip():
            raise ValueError("Training example replay request requires replay_id")
        if self.training_example.reading_id != self.runtime.reading_id:
            raise ValueError("Training example replay requires matching reading_id")
        return self


class TrainingReplayBatchRequest(V40Model):
    version: str = "v40.training_replay_batch_request.v1"
    batch_id: str
    candidate_version: str = "v40-alpha"
    replays: list[TrainingExampleReplayResult]
    persist: bool = True
    boundary: str = "training_replay_batch_request_aggregates_replay_results_without_production_write"

    @model_validator(mode="after")
    def _replay_batch_boundary(self) -> "TrainingReplayBatchRequest":
        if not self.batch_id.strip():
            raise ValueError("Training replay batch request requires batch_id")
        if not self.replays:
            raise ValueError("Training replay batch request requires replays")
        return self


class EvaluationBatchFromRuntimeRequest(V40Model):
    version: str = "v40.evaluation_batch_from_runtime_request.v1"
    batch_id: str
    cases: list[EvaluationCaseSpec]
    runtime: RuntimeResult
    candidate_version: str = "v40-alpha"
    persist: bool = True
    boundary: str = "evaluation_batch_request_runs_many_cases_without_llm_judge"


class AcceptanceWindowFromRuntimeRequest(V40Model):
    version: str = "v40.acceptance_window_from_runtime_request.v1"
    window_id: str
    cases: list[RealCaseRecord]
    runtime: RuntimeResult
    candidate_version: str = "v40-alpha"
    expression_telemetry: ExpressionTelemetry | None = None
    persist: bool = True
    boundary: str = "acceptance_window_request_scores_real_cases_without_llm_judge_or_fact_mutation"

    @model_validator(mode="after")
    def _acceptance_window_boundary(self) -> "AcceptanceWindowFromRuntimeRequest":
        if not self.window_id.strip():
            raise ValueError("Acceptance window request requires window_id")
        if not self.cases:
            raise ValueError("Acceptance window request requires cases")
        return self


class RealCaseExpansionEvidenceRequest(V40Model):
    version: str = "v40.real_case_expansion_evidence_request.v1"
    cases: list[RealCaseRecord]
    acceptance_windows: list[AcceptanceWindowResult] = Field(default_factory=list)
    target_case_count: int = Field(default=100, ge=1)
    min_cases_per_topic: int = Field(default=8, ge=1)
    min_trainable_case_count: int = Field(default=20, ge=0)
    boundary: str = "real_case_expansion_request_reads_cases_and_windows_without_cutover"

    @model_validator(mode="after")
    def _real_case_expansion_boundary(self) -> "RealCaseExpansionEvidenceRequest":
        if not self.cases:
            raise ValueError("Real case expansion evidence request requires cases")
        return self


class DirectTrainingActivationEvidenceRequest(V40Model):
    version: str = "v40.direct_training_activation_evidence_request.v1"
    result: BatchTrainerV1Result
    boundary: str = "direct_training_activation_evidence_request_reads_batch_trainer_result_without_mutation"


class OnlineCutoverDecisionRequest(V40Model):
    version: str = "v40.online_cutover_decision_request.v1"
    project_status: dict[str, object]
    cutover_checklist: dict[str, object]
    real_case_evidence: dict[str, object]
    training_activation_evidence: dict[str, object]
    release_candidate_audit: dict[str, object] = Field(default_factory=dict)
    boundary: str = "online_cutover_decision_request_reads_evidence_without_switching_traffic"

    @model_validator(mode="after")
    def _online_cutover_decision_boundary(self) -> "OnlineCutoverDecisionRequest":
        required = {
            "project_status": self.project_status,
            "cutover_checklist": self.cutover_checklist,
            "real_case_evidence": self.real_case_evidence,
            "training_activation_evidence": self.training_activation_evidence,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Online cutover decision request requires {', '.join(missing)}")
        return self


class RealCaseAcceptancePackRequest(V40Model):
    version: str = "v40.real_case_acceptance_pack_request.v1"
    cases: list[RealCaseRecord]
    acceptance_window: AcceptanceWindowResult | None = None
    real_case_evidence: dict[str, object]
    online_cutover_decision: dict[str, object]
    min_owner_review_case_count: int = Field(default=1, ge=1)
    boundary: str = "real_case_acceptance_pack_request_reads_evidence_without_cutover"

    @model_validator(mode="after")
    def _real_case_acceptance_pack_boundary(self) -> "RealCaseAcceptancePackRequest":
        if not self.cases:
            raise ValueError("Real case acceptance pack request requires cases")
        if not self.real_case_evidence:
            raise ValueError("Real case acceptance pack request requires real_case_evidence")
        if not self.online_cutover_decision:
            raise ValueError("Real case acceptance pack request requires online_cutover_decision")
        return self


class CandidateWeightFromBatchRequest(V40Model):
    version: str = "v40.candidate_weight_from_batch_request.v1"
    weight_version_id: str
    source_training_run_id: str
    release_gate_id: str
    batch_summary: EvaluationBatchSummary
    persist: bool = True
    boundary: str = "candidate_weight_request_registers_candidate_without_activation"


class CandidateWeightFromReplayBatchRequest(V40Model):
    version: str = "v40.candidate_weight_from_replay_batch_request.v1"
    weight_version_id: str
    source_training_run_id: str
    release_gate_id: str
    replay_batch_summary: TrainingReplayBatchSummary
    persist: bool = True
    boundary: str = "candidate_weight_from_replay_batch_registers_candidate_without_activation"

    @model_validator(mode="after")
    def _replay_candidate_boundary(self) -> "CandidateWeightFromReplayBatchRequest":
        if not self.weight_version_id.strip():
            raise ValueError("Candidate replay weight request requires weight_version_id")
        if not self.source_training_run_id.strip():
            raise ValueError("Candidate replay weight request requires source_training_run_id")
        if not self.release_gate_id.strip():
            raise ValueError("Candidate replay weight request requires release_gate_id")
        return self


class ReleaseReadinessFromBatchesRequest(V40Model):
    version: str = "v40.release_readiness_from_batches_request.v1"
    readiness_id: str
    candidate_version: str
    batches: list[EvaluationBatchSummary]
    persist: bool = True
    boundary: str = "release_readiness_request_aggregates_batches_without_activation"


class ReleaseReadinessFromEvidenceBatchesRequest(V40Model):
    version: str = "v40.release_readiness_from_evidence_batches_request.v1"
    readiness_id: str
    candidate_version: str
    evaluation_batches: list[EvaluationBatchSummary] = Field(default_factory=list)
    replay_batches: list[TrainingReplayBatchSummary] = Field(default_factory=list)
    persist: bool = True
    boundary: str = "release_readiness_request_aggregates_evaluation_and_replay_batches_without_activation"

    @model_validator(mode="after")
    def _readiness_evidence_boundary(self) -> "ReleaseReadinessFromEvidenceBatchesRequest":
        if not self.readiness_id.strip():
            raise ValueError("Release readiness evidence request requires readiness_id")
        if not self.candidate_version.strip():
            raise ValueError("Release readiness evidence request requires candidate_version")
        return self


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
    ziwei_chart_facts: ZiweiChartFacts | None = None
    user_question: str = ""
    topic: Topic = Topic.OVERVIEW
    role_key: RoleKey = "user"
    locale_context: LocaleContext | None = None
    role_context: RoleContext | None = None
    client_context: ClientContext | None = None
    engine_context: EngineContext | None = None
    persist: bool = False
    boundary: str = "native_bazi_runtime_request_uses_v40_chart_facts_without_v30_runtime"


class NativeReadingReportRequest(V40Model):
    version: str = "v40.native_reading_report_request.v1"
    request_id: str
    reading_id: str
    chart_facts: BaziChartFacts
    ziwei_chart_facts: ZiweiChartFacts | None = None
    user_question: str = ""
    topic: Topic = Topic.OVERVIEW
    role_key: RoleKey = "user"
    locale_context: LocaleContext | None = None
    role_context: RoleContext | None = None
    client_context: ClientContext | None = None
    engine_context: EngineContext | None = None
    execution_mode: str = "ollama"
    provider_text: str = ""
    provider: str = "local_expression_adapter"
    model: str = "v40.expression.contract.v1"
    raw_thinking: str = ""
    persist: bool = False
    boundary: str = "native_reading_report_runs_runtime_and_expression_without_v30_state"

    @model_validator(mode="after")
    def _report_mode_boundary(self) -> "NativeReadingReportRequest":
        if self.execution_mode not in {"local", "provider_text", "ollama"}:
            raise ValueError("report execution_mode must be local, provider_text, or ollama")
        if self.execution_mode == "provider_text" and not self.provider_text.strip():
            raise ValueError("provider_text mode requires provider_text")
        return self


class ConversationTurnRequest(V40Model):
    version: str = "v40.conversation_turn_request.v1"
    turn_id: str
    runtime: RuntimeResult
    question: str
    seed_id: str = ""
    selected_option: str = ""
    role_key: RoleKey | None = None
    topic: Topic | None = None
    probe_answer_results: list[ProbeAnswerResult] = Field(default_factory=list)
    execution_mode: str = "ollama"
    provider_text: str = ""
    provider: str = "local_conversation_adapter"
    model: str = "v40.conversation.contract.v1"
    raw_thinking: str = ""
    persist: bool = False
    persist_training_label: bool = False
    boundary: str = "conversation_turn_request_answers_without_rerunning_reading_or_mutating_verdict"

    @model_validator(mode="after")
    def _conversation_turn_mode_boundary(self) -> "ConversationTurnRequest":
        if self.execution_mode not in {"local", "provider_text", "ollama"}:
            raise ValueError("conversation execution_mode must be local, provider_text, or ollama")
        if self.execution_mode == "provider_text" and not self.provider_text.strip():
            raise ValueError("provider_text mode requires provider_text")
        if not self.question.strip():
            raise ValueError("conversation turn requires question")
        return self


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


class PractitionerLensActionRequest(V40Model):
    version: str = "v40.practitioner_lens_action_request.v1"
    action_id: str
    runtime: RuntimeResult
    action_key: str
    target_type: LabelTargetType = LabelTargetType.SIGNAL
    target_ids: list[str] = Field(default_factory=list)
    note: str = ""
    created_by_role: RoleKey = "practitioner"
    persist: bool = False
    persist_overlay: bool = False
    boundary: str = "practitioner_lens_action_creates_local_feedback_without_verdict_or_weight_mutation"

    @model_validator(mode="after")
    def _lens_action_boundary(self) -> "PractitionerLensActionRequest":
        allowed_actions = {
            "more_like_this",
            "supporting_context",
            "do_not_use_now",
            "ask_to_confirm",
            "user_mismatch",
            "note",
        }
        if self.created_by_role not in {"practitioner", "admin"}:
            raise ValueError("Practitioner lens action requires practitioner or admin role")
        if self.runtime.request.role_key != "practitioner":
            raise ValueError("Practitioner lens action requires a practitioner runtime")
        if self.action_key not in allowed_actions:
            raise ValueError("Unknown practitioner lens action_key")
        if not self.action_id.strip():
            raise ValueError("Practitioner lens action requires action_id")
        if not self.target_ids:
            raise ValueError("Practitioner lens action requires target_ids")
        return self


class ConsentGrantRequest(V40Model):
    version: str = "v40.consent_grant_request.v1"
    grant_id: str
    reading_id: str
    granted_by_role: RoleKey = "user"
    allow_practitioner_review: bool = True
    allow_training_use: bool = True
    note: str = ""
    persist: bool = False
    boundary: str = "consent_grant_request_creates_user_app_consent_without_admin_control"


class PractitionerReviewCreateRequest(V40Model):
    version: str = "v40.practitioner_review_create_request.v1"
    review_request_id: str
    runtime: RuntimeResult
    consent_grant: ConsentGrant
    requested_topic: Topic | None = None
    requested_by_role: RoleKey = "user"
    note: str = ""
    persist: bool = False
    boundary: str = "practitioner_review_create_request_queues_anonymized_case_only"


class PractitionerReviewAssignRequest(V40Model):
    version: str = "v40.practitioner_review_assign_request.v1"
    queue_item_id: str
    practitioner_ref: str
    boundary: str = "practitioner_review_assign_request_updates_queue_metadata_only"

    @model_validator(mode="after")
    def _assign_boundary(self) -> "PractitionerReviewAssignRequest":
        if not self.queue_item_id.strip():
            raise ValueError("Review assignment requires queue_item_id")
        if not self.practitioner_ref.strip():
            raise ValueError("Review assignment requires practitioner_ref")
        return self


class PractitionerReviewResultRequest(V40Model):
    version: str = "v40.practitioner_review_result_request.v1"
    result_id: str
    review_request: PractitionerReviewRequest
    reviewer_role: RoleKey = "practitioner"
    decision: PractitionerReviewDecision = PractitionerReviewDecision.UNSURE
    selected_signal_ids: list[str] = Field(default_factory=list)
    selected_verdict_ids: list[str] = Field(default_factory=list)
    advice_notes: list[str] = Field(default_factory=list)
    probe_suggestions: list[str] = Field(default_factory=list)
    persist: bool = False
    boundary: str = "practitioner_review_result_request_creates_training_material_without_direct_runtime_mutation"


class ProbeAnswerRequest(V40Model):
    version: str = "v40.probe_answer_request.v1"
    answer_id: str
    runtime: RuntimeResult
    probe_id: str = ""
    answer_text: str = ""
    selected_option: str = ""
    mismatch_area: str = ""
    created_by_role: RoleKey = "user"
    persist: bool = False
    persist_overlay: bool = False
    boundary: str = "probe_answer_request_creates_current_reading_calibration_without_rerunning_chart"

    @model_validator(mode="after")
    def _probe_answer_boundary(self) -> "ProbeAnswerRequest":
        if not self.answer_id.strip():
            raise ValueError("Probe answer requires answer_id")
        if not (self.answer_text.strip() or self.selected_option.strip()):
            raise ValueError("Probe answer requires answer_text or selected_option")
        if self.created_by_role not in {"guest", "user", "practitioner"}:
            raise ValueError("Probe answer requires guest, user, or practitioner role")
        if self.probe_id and not any(probe.probe_id == self.probe_id for probe in self.runtime.probes):
            raise ValueError("Probe answer references unknown probe_id")
        return self


class UserRegisterRequest(V40Model):
    version: str = "v40.user_register_request.v1"
    email: str
    password: str
    display_name: str = ""
    role_key: RoleKey = "user"
    boundary: str = "user_register_request_creates_user_app_account_without_admin_role"

    @model_validator(mode="after")
    def _register_boundary(self) -> "UserRegisterRequest":
        if self.role_key not in {"user", "practitioner"}:
            raise ValueError("User app cannot register admin or lab roles")
        if "@" not in self.email:
            raise ValueError("Registration requires email")
        if len(self.password.strip()) < 6:
            raise ValueError("Password must be at least 6 characters")
        return self


class UserLoginRequest(V40Model):
    version: str = "v40.user_login_request.v1"
    email: str
    password: str
    boundary: str = "user_login_request_accepts_email_or_builtin_admin_username_without_admin_control"

    @model_validator(mode="after")
    def _login_boundary(self) -> "UserLoginRequest":
        if not self.email.strip():
            raise ValueError("Login requires account identifier")
        if not self.password.strip():
            raise ValueError("Login requires password")
        return self


class BaziProfileCreateRequest(V40Model):
    version: str = "v40.bazi_profile_create_request.v1"
    display_name: str
    gender: str = ""
    chart_facts: BaziChartFacts
    birth_input: BirthInputCanonical | None = None
    ziwei_chart_facts: ZiweiChartFacts | None = None
    is_default: bool = False
    tags: list[str] = Field(default_factory=list)
    boundary: str = "bazi_profile_create_request_saves_user_owned_profile_without_training_policy"

    @model_validator(mode="after")
    def _profile_create_boundary(self) -> "BaziProfileCreateRequest":
        if not self.display_name.strip():
            raise ValueError("Profile requires display_name")
        return self


class BaziProfileUpdateRequest(V40Model):
    version: str = "v40.bazi_profile_update_request.v1"
    profile: BaziProfileRecord
    boundary: str = "bazi_profile_update_request_replaces_user_owned_profile_without_chart_runtime_mutation"


class ExpressionFromRuntimeRequest(V40Model):
    version: str = "v40.expression_from_runtime_request.v1"
    task_id: str
    result_id: str
    acceptance_id: str
    runtime: RuntimeResult
    role_key: RoleKey | None = None
    topic: Topic | None = None
    execution_mode: str = "ollama"
    provider_text: str = ""
    provider: str = "local_expression_adapter"
    model: str = "v40.expression.contract.v1"
    raw_thinking: str = ""
    boundary: str = "expression_from_runtime_rewrites_language_without_verdict_or_chart_fact_mutation"

    @model_validator(mode="after")
    def _expression_mode_boundary(self) -> "ExpressionFromRuntimeRequest":
        if self.execution_mode not in {"local", "provider_text", "ollama"}:
            raise ValueError("expression execution_mode must be local, provider_text, or ollama")
        if self.execution_mode == "provider_text" and not self.provider_text.strip():
            raise ValueError("provider_text mode requires provider_text")
        return self
