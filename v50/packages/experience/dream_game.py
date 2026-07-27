from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import Field, model_validator

from experience.contracts import ExperienceModel


DREAM_GAME_SCHEMA_VERSION = "deepbazi.dream_problem_flower.v1"
DREAM_GAME_SIMULATED_NAMESPACE = "dream-game:simulated-fixture:v1"
DREAM_GAME_BANNER = "模拟验证场｜非真实案例｜不计入正式果实"
DREAM_GAME_V50_NAMESPACE = "dream-game:v50-canonical:v1"
DREAM_GAME_V50_BANNER = "V50结构验证场｜正式命盘快照｜不计入真人果实"
DREAM_GAME_PROJECTION_POLICY_VERSION = "pre-outcome-knowledge-cutoff.v1"
DREAM_GAME_EVALUATION_POLICY_VERSION = "blind-option-calibration.v1"
DREAM_GAME_REVEAL_POLICY_VERSION = "independent-dual-seal.v1"
DREAM_QUESTION_SET_VERSION = "dream-question-story-engine.v1"
DREAM_FLOWER_PROTOCOL_VERSION = "multi-answer-shared-fruit.v1"

EvidenceClass = Literal[
    "SIMULATED",
    "V50_CANONICAL",
    "VERIFIED_REAL",
    "HISTORICAL_VERIFIED",
    "UNVERIFIED",
]
ContentState = Literal["DRAFT", "VALIDATED", "SEALED", "PUBLISHABLE", "REVOKED"]
OutcomeOptionId = Literal["yes", "no", "partial_or_unclear"]
ConfidenceBucket = Literal["low", "medium", "high"]
CutoffVerificationStatus = Literal[
    "VERIFIED_AS_OF_SOURCE_VERSION",
    "LEGACY_CUTOFF_UNVERIFIABLE",
]
DreamLearningQuestionKind = Literal[
    "LEAF_BASIC_01",
    "LEAF_BASIC_02",
    "TRUNK_BACKBONE_01",
]
DreamQuestionOrganRole = Literal[
    "OBSERVATION_LEAF",
    "RULE_LEAF",
    "TRUNK_FRAMEWORK",
]
DreamQuestionDomain = Literal["BAZI"]
DreamQuestionContentState = Literal[
    "DRAFT",
    "VALIDATED",
    "GOLDEN",
    "ACTIVE",
    "RETIRED",
]
DreamQuestionStoryScript = Literal[
    "RECOGNIZE_THIS_TREE",
    "FIND_MAIN_TRUNK",
    "SEASONAL_VARIATION",
]
DreamFlowerRevealPolicy = Literal[
    "ASSERTION_REVEAL",
    "REALITY_REVEAL",
]
DreamQuestionDifficulty = Literal["FOUNDATION", "INTERMEDIATE", "ADVANCED"]
DreamLearningQuestionStatus = Literal[
    "NOT_STARTED",
    "RETRY_REQUIRED",
    "COMPLETED",
]
AnswerAssistanceMode = Literal["INDEPENDENT", "ASSISTED"]
FlowerCloseReason = Literal[
    "NATURAL_WITHER",
    "OWNER_CLOSED",
    "OUTCOME_CUTOFF",
]
FlowerLifecycleState = Literal[
    "OPEN",
    "CLOSED_NO_RESPONSE",
    "SHARED_FRUIT_FORMED",
]


class DreamGameState(str, Enum):
    ROUND_ELIGIBILITY_CHECK = "ROUND_ELIGIBILITY_CHECK"
    PROJECTION_ISSUING = "PROJECTION_ISSUING"
    ROUND_OBSERVING = "ROUND_OBSERVING"
    QUESTION_FLOWER_OPEN = "QUESTION_FLOWER_OPEN"
    OPTIONAL_DIVINATION = "OPTIONAL_DIVINATION"
    JUDGMENT_DRAFTING = "JUDGMENT_DRAFTING"
    USER_JUDGMENT_SEALED = "USER_JUDGMENT_SEALED"
    BOTH_JUDGMENTS_SEALED = "BOTH_JUDGMENTS_SEALED"
    OUTCOME_REVEALABLE = "OUTCOME_REVEALABLE"
    OUTCOME_REVEALED = "OUTCOME_REVEALED"
    EVALUATED = "EVALUATED"
    KNOWLEDGE_SEED_ISSUED = "KNOWLEDGE_SEED_ISSUED"
    ROUND_COMPLETE = "ROUND_COMPLETE"
    CONTENT_GATE_BLOCKED = "CONTENT_GATE_BLOCKED"
    AUTHORIZATION_REVOKED = "AUTHORIZATION_REVOKED"
    PROJECTION_INVALID = "PROJECTION_INVALID"
    SEAL_CONFLICT = "SEAL_CONFLICT"
    EVIDENCE_INSUFFICIENT = "EVIDENCE_INSUFFICIENT"
    FAIL_CLOSED = "FAIL_CLOSED"


class ProblemQuestionRecord(ExperienceModel):
    schema_version: Literal["deepbazi.problem_question.v1"] = "deepbazi.problem_question.v1"
    question_id: str = Field(min_length=1, max_length=180)
    question_version: str = Field(min_length=1, max_length=80)
    subject_label: str = Field(min_length=1, max_length=120)
    neutral_question_text: str = Field(min_length=1, max_length=800)
    known_context: list[str] = Field(default_factory=list, max_length=12)
    knowledge_cutoff: datetime
    clock_domain: str = Field(min_length=1, max_length=120)
    outcome_window_start: datetime
    outcome_window_end: datetime
    outcome_options: dict[OutcomeOptionId, str]
    resolution_criteria: list[str] = Field(min_length=1, max_length=12)
    disconfirmation_definition: str = Field(min_length=1, max_length=800)
    liuyao_permitted: bool = True

    @model_validator(mode="after")
    def validate_window(self) -> "ProblemQuestionRecord":
        if self.outcome_window_end <= self.outcome_window_start:
            raise ValueError("dream_game_outcome_window_invalid")
        if set(self.outcome_options) != {"yes", "no", "partial_or_unclear"}:
            raise ValueError("dream_game_outcome_options_invalid")
        return self


class HypothesisNodeOption(ExperienceModel):
    node_ref: str = Field(min_length=1, max_length=260)
    label: str = Field(min_length=1, max_length=100)
    pillar_label: str = Field(default="", max_length=40)
    layer: Literal["stem", "branch", "hidden_stem", "timing", "unknown"] = "unknown"


class HypothesisRelationOption(ExperienceModel):
    relation_ref: str = Field(min_length=1, max_length=260)
    label: str = Field(min_length=1, max_length=100)
    source_node_ref: str = Field(min_length=1, max_length=260)
    target_node_ref: str = Field(min_length=1, max_length=260)
    formal: bool
    evidence_class: Literal["formal_pre_cutoff", "simulated_candidate"]

    @model_validator(mode="after")
    def validate_formal_boundary(self) -> "HypothesisRelationOption":
        if self.formal != (self.evidence_class == "formal_pre_cutoff"):
            raise ValueError("dream_game_relation_formal_boundary_invalid")
        return self


class ImmutableDreamSourceSnapshot(ExperienceModel):
    schema_version: Literal["deepbazi.dream_source_snapshot.v1"] = (
        "deepbazi.dream_source_snapshot.v1"
    )
    source_snapshot_id: str = Field(min_length=16, max_length=180)
    cutoff_at: datetime
    cutoff_verification_status: CutoffVerificationStatus
    source_scene_ref: str = Field(min_length=16, max_length=180)
    source_scene_version: str = Field(min_length=1, max_length=180)
    source_hash: str = Field(min_length=64, max_length=64)
    source_life_case_version: str = Field(min_length=1, max_length=180)
    source_updated_at: datetime
    authorization_version: str = Field(min_length=1, max_length=120)
    captured_at: datetime
    snapshot_payload: dict[str, Any]
    snapshot_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_cutoff_proof(self) -> "ImmutableDreamSourceSnapshot":
        if self.cutoff_verification_status == "VERIFIED_AS_OF_SOURCE_VERSION":
            if self.source_updated_at > self.cutoff_at or self.cutoff_at > self.captured_at:
                raise ValueError("dream_game_cutoff_proof_invalid")
        return self


class DreamLearningQuestionOption(ExperienceModel):
    option_id: str = Field(min_length=1, max_length=180)
    label: str = Field(min_length=1, max_length=180)
    answer_ref_kind: Literal["node", "relation", "path", "none"] = "none"
    answer_ref: str = Field(default="", max_length=260)


class DreamLearningQuestion(ExperienceModel):
    question_id: str = Field(min_length=1, max_length=180)
    kind: DreamLearningQuestionKind
    title: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=1, max_length=600)
    target_lens: Literal[
        "overview",
        "five_element",
        "combination_conflict",
        "roots_reveal",
        "timing",
        "work_path",
    ]
    answer_type: Literal["single_choice"] = "single_choice"
    options: list[DreamLearningQuestionOption] = Field(min_length=2, max_length=4)
    correct_option_id: str = Field(min_length=1, max_length=180)
    answer_commitment_hash: str = Field(min_length=64, max_length=64)
    evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    organ_role: DreamQuestionOrganRole | None = None
    depends_on: list[str] = Field(default_factory=list, max_length=3)
    truth_ref: str = Field(default="", max_length=260)
    knowledge_atom_refs: list[str] = Field(default_factory=list, max_length=8)
    question_pattern_ref: str = Field(default="", max_length=180)
    explanation: str = Field(default="", max_length=600)
    difficulty: DreamQuestionDifficulty = "FOUNDATION"
    reveal_policy: DreamFlowerRevealPolicy = "ASSERTION_REVEAL"
    success_message: str = Field(min_length=1, max_length=600)
    retry_message: str = Field(min_length=1, max_length=600)
    immutable_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_answer_identity(self) -> "DreamLearningQuestion":
        option_ids = [item.option_id for item in self.options]
        if len(set(option_ids)) != len(option_ids):
            raise ValueError("dream_game_question_option_duplicate")
        if self.correct_option_id not in option_ids:
            raise ValueError("dream_game_question_answer_missing")
        if len(set(self.depends_on)) != len(self.depends_on):
            raise ValueError("dream_game_question_dependency_duplicate")
        if self.question_id in self.depends_on:
            raise ValueError("dream_game_question_self_dependency")
        return self


class DreamQuestionDependencyEdge(ExperienceModel):
    source_question_id: str = Field(min_length=1, max_length=180)
    target_question_id: str = Field(min_length=1, max_length=180)
    dependency_kind: Literal[
        "EVIDENCE_REQUIRED",
        "FRAMEWORK_REQUIRED",
    ]


class DreamQuestionSet(ExperienceModel):
    schema_version: Literal["deepbazi.dream_question_set.v1"] = (
        "deepbazi.dream_question_set.v1"
    )
    question_set_id: str = Field(min_length=16, max_length=180)
    round_id: str = Field(min_length=1, max_length=180)
    source_snapshot_id: str = Field(min_length=16, max_length=180)
    cutoff_at: datetime
    source_version: str = Field(min_length=1, max_length=180)
    source_hash: str = Field(min_length=64, max_length=64)
    question_set_version: str = DREAM_QUESTION_SET_VERSION
    questions: list[DreamLearningQuestion] = Field(min_length=3, max_length=3)
    domain: DreamQuestionDomain = "BAZI"
    content_status: DreamQuestionContentState = "RETIRED"
    story_script_ref: DreamQuestionStoryScript | None = None
    target_lens: Literal[
        "overview",
        "five_element",
        "combination_conflict",
        "roots_reveal",
        "timing",
        "work_path",
    ] | None = None
    flower_question_id: str = Field(default="", max_length=180)
    flower_target_ref: str = Field(default="", max_length=260)
    reveal_policy: DreamFlowerRevealPolicy = "ASSERTION_REVEAL"
    evidence_requirements: list[str] = Field(default_factory=list, max_length=16)
    truth_refs: list[str] = Field(default_factory=list, max_length=24)
    dependency_edges: list[DreamQuestionDependencyEdge] = Field(
        default_factory=list,
        max_length=8,
    )
    story_script_version: str = Field(default="", max_length=80)
    bundle_validator_version: str = Field(default="", max_length=80)
    immutable_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_required_questions(self) -> "DreamQuestionSet":
        kinds = [item.kind for item in self.questions]
        if kinds != ["LEAF_BASIC_01", "LEAF_BASIC_02", "TRUNK_BACKBONE_01"]:
            raise ValueError("dream_game_question_set_shape_invalid")
        if len({item.question_id for item in self.questions}) != 3:
            raise ValueError("dream_game_question_set_duplicate")
        if self.content_status in {"GOLDEN", "ACTIVE"}:
            if (
                self.story_script_ref is None
                or self.target_lens is None
                or not self.flower_question_id
                or not self.flower_target_ref
                or not self.truth_refs
                or not self.evidence_requirements
                or not self.story_script_version
                or not self.bundle_validator_version
            ):
                raise ValueError("dream_game_question_bundle_metadata_incomplete")
            expected_roles: list[DreamQuestionOrganRole] = [
                "OBSERVATION_LEAF",
                "RULE_LEAF",
                "TRUNK_FRAMEWORK",
            ]
            if [item.organ_role for item in self.questions] != expected_roles:
                raise ValueError("dream_game_question_bundle_organ_roles_invalid")
            if any(item.target_lens != self.target_lens for item in self.questions):
                raise ValueError("dream_game_question_bundle_lens_mismatch")
            if any(item.reveal_policy != self.reveal_policy for item in self.questions):
                raise ValueError("dream_game_question_bundle_reveal_policy_mismatch")
            first, second, trunk = self.questions
            if first.depends_on or second.depends_on:
                raise ValueError("dream_game_question_leaf_cannot_depend_on_prerequisite")
            if set(trunk.depends_on) != {first.question_id, second.question_id}:
                raise ValueError("dream_game_question_trunk_dependencies_incomplete")
            if not first.evidence_refs or not second.evidence_refs:
                raise ValueError("dream_game_question_leaf_evidence_missing")
            if set(first.evidence_refs) & set(second.evidence_refs):
                raise ValueError("dream_game_question_leaf_evidence_not_distinct")
            leaf_evidence = {*first.evidence_refs, *second.evidence_refs}
            if not leaf_evidence.issubset(set(trunk.evidence_refs)):
                raise ValueError("dream_game_question_trunk_evidence_incomplete")
            required_edges = {
                (first.question_id, trunk.question_id, "EVIDENCE_REQUIRED"),
                (second.question_id, trunk.question_id, "EVIDENCE_REQUIRED"),
                (trunk.question_id, self.flower_question_id, "FRAMEWORK_REQUIRED"),
            }
            actual_edges = {
                (
                    item.source_question_id,
                    item.target_question_id,
                    item.dependency_kind,
                )
                for item in self.dependency_edges
            }
            if not required_edges.issubset(actual_edges):
                raise ValueError("dream_game_question_bundle_dependency_graph_incomplete")
        return self


class DreamLearningQuestionPublic(ExperienceModel):
    question_id: str
    kind: DreamLearningQuestionKind
    title: str
    prompt: str
    target_lens: Literal[
        "overview",
        "five_element",
        "combination_conflict",
        "roots_reveal",
        "timing",
        "work_path",
    ]
    answer_type: Literal["single_choice"] = "single_choice"
    options: list[dict[str, str]]
    available: bool
    organ_role: DreamQuestionOrganRole | None = None
    depends_on: list[str] = Field(default_factory=list)
    difficulty: DreamQuestionDifficulty = "FOUNDATION"


class DreamQuestionSetProjection(ExperienceModel):
    schema_version: Literal["deepbazi.dream_question_set_projection.v1"] = (
        "deepbazi.dream_question_set_projection.v1"
    )
    question_set_id: str
    question_set_version: str
    source_snapshot_id: str
    cutoff_at: datetime
    questions: list[DreamLearningQuestionPublic] = Field(min_length=3, max_length=3)
    domain: DreamQuestionDomain = "BAZI"
    content_status: DreamQuestionContentState = "RETIRED"
    story_script_ref: DreamQuestionStoryScript | None = None
    target_lens: Literal[
        "overview",
        "five_element",
        "combination_conflict",
        "roots_reveal",
        "timing",
        "work_path",
    ] | None = None
    reveal_policy: DreamFlowerRevealPolicy = "ASSERTION_REVEAL"


class DreamQuestionProgressItem(ExperienceModel):
    question_id: str
    kind: DreamLearningQuestionKind
    status: DreamLearningQuestionStatus = "NOT_STARTED"
    attempts: int = Field(default=0, ge=0)
    last_selected_option_id: str = Field(default="", max_length=180)
    feedback: str = Field(default="", max_length=600)
    resolved_answer_ref_kind: Literal["node", "relation", "path", "none"] = "none"
    resolved_answer_ref: str = Field(default="", max_length=260)
    resolved_evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    completed_at: datetime | None = None


class DreamQuestionAttemptProgress(ExperienceModel):
    schema_version: Literal["deepbazi.dream_question_attempt_progress.v1"] = (
        "deepbazi.dream_question_attempt_progress.v1"
    )
    question_set_id: str = Field(min_length=16, max_length=180)
    items: list[DreamQuestionProgressItem] = Field(min_length=3, max_length=3)
    flower_unlocked: bool = False
    updated_at: datetime

    @model_validator(mode="after")
    def validate_unlock(self) -> "DreamQuestionAttemptProgress":
        if self.flower_unlocked and any(item.status != "COMPLETED" for item in self.items):
            raise ValueError("dream_game_flower_unlock_without_prerequisites")
        return self


class DreamLearningAnswerRecord(ExperienceModel):
    schema_version: Literal["deepbazi.dream_learning_answer.v1"] = (
        "deepbazi.dream_learning_answer.v1"
    )
    answer_id: str
    attempt_id: str
    round_id: str
    viewer_id: str
    question_set_id: str
    question_id: str
    selected_option_id: str
    correct: bool
    resolved_evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    idempotency_key_hash: str = Field(min_length=64, max_length=64)
    answered_at: datetime
    immutable_hash: str = Field(min_length=64, max_length=64)


class MaturedFruitSlot(ExperienceModel):
    slot_id: str = Field(min_length=1, max_length=120)
    event_family: Literal[
        "JOB_CHANGE",
        "CONTRACT_SIGNING",
        "RELOCATION_OR_TRAVEL",
        "V50_STRUCTURE_PATH",
        "V50_QUESTION_STORY",
    ]
    question: ProblemQuestionRecord
    simulated_outcome_option_id: OutcomeOptionId | None = None
    simulated_outcome_summary: str = Field(default="", max_length=1000)
    simulated_evidence_items: list[str] = Field(default_factory=list, max_length=8)
    system_outcome_option_id: OutcomeOptionId
    system_confidence_basis_points: int = Field(ge=0, le=10000)
    system_reasoning_summary: str = Field(min_length=1, max_length=1200)
    system_strongest_alternative: str = Field(min_length=1, max_length=800)
    system_disconfirmation_condition: str = Field(min_length=1, max_length=800)


class MaturedFruitContentPack(ExperienceModel):
    schema_version: Literal["deepbazi.matured_fruit_content_pack.v1"] = (
        "deepbazi.matured_fruit_content_pack.v1"
    )
    pack_id: str = Field(min_length=1, max_length=180)
    pack_version: str = Field(min_length=1, max_length=80)
    namespace: str = Field(min_length=1, max_length=180)
    evidence_class: EvidenceClass
    content_state: ContentState
    development_only: bool
    release_eligible: bool
    verified_real_gate_contribution: int = Field(ge=0, le=1)
    explicit_authorization_ref: str = Field(default="", max_length=240)
    deidentification_policy_version: str = Field(min_length=1, max_length=120)
    original_timestamp_manifest_hash: str = Field(min_length=64, max_length=64)
    cutoff_material_manifest_hash: str = Field(min_length=64, max_length=64)
    chain_of_custody_manifest_hash: str = Field(min_length=64, max_length=64)
    withdrawal_policy_version: str = Field(min_length=1, max_length=120)
    slots: list[MaturedFruitSlot] = Field(min_length=1, max_length=3)
    immutable_hash: str = Field(min_length=64, max_length=64)
    created_at: datetime
    revoked_at: datetime | None = None

    @model_validator(mode="after")
    def validate_evidence_boundary(self) -> "MaturedFruitContentPack":
        if len({item.slot_id for item in self.slots}) != len(self.slots):
            raise ValueError("dream_game_duplicate_content_slot")
        if self.evidence_class == "SIMULATED":
            if (
                not self.development_only
                or self.release_eligible
                or self.verified_real_gate_contribution != 0
                or self.namespace != DREAM_GAME_SIMULATED_NAMESPACE
            ):
                raise ValueError("dream_game_simulated_pack_boundary_invalid")
            if any(item.simulated_outcome_option_id is None for item in self.slots):
                raise ValueError("dream_game_simulated_outcome_required")
        elif self.evidence_class == "V50_CANONICAL":
            if (
                self.development_only
                or self.release_eligible
                or self.verified_real_gate_contribution != 0
                or self.namespace != DREAM_GAME_V50_NAMESPACE
            ):
                raise ValueError("dream_game_v50_canonical_pack_boundary_invalid")
        elif self.evidence_class in {"VERIFIED_REAL", "HISTORICAL_VERIFIED"}:
            if (
                self.development_only
                or not self.release_eligible
                or self.verified_real_gate_contribution != 1
                or not self.explicit_authorization_ref
            ):
                raise ValueError("dream_game_verified_pack_boundary_invalid")
        else:
            if self.release_eligible or self.verified_real_gate_contribution:
                raise ValueError("dream_game_unverified_pack_cannot_release")
        if self.content_state == "REVOKED" and self.revoked_at is None:
            raise ValueError("dream_game_revoked_pack_timestamp_required")
        return self


class ContentPackAudit(ExperienceModel):
    schema_version: Literal["deepbazi.matured_fruit_pack_audit.v1"] = (
        "deepbazi.matured_fruit_pack_audit.v1"
    )
    pack_id: str
    evidence_class: EvidenceClass
    resulting_state: ContentState
    passed: bool
    issue_codes: list[str] = Field(default_factory=list)
    projection_manifest_hash: str = Field(min_length=64, max_length=64)
    verified_real_gate_contribution: int = Field(ge=0, le=1)
    audited_at: datetime


class FrozenProjectionManifest(ExperienceModel):
    schema_version: Literal["deepbazi.frozen_round_projection.v1"] = (
        "deepbazi.frozen_round_projection.v1"
    )
    knowledge_cutoff: datetime
    clock_domain: str = Field(min_length=1, max_length=120)
    source_scene_ref: str = Field(min_length=16, max_length=180)
    source_scene_version: str = Field(min_length=1, max_length=180)
    source_scene_hash: str = Field(min_length=64, max_length=64)
    source_life_case_version: str = Field(min_length=1, max_length=180)
    source_snapshot_id: str = Field(default="", max_length=180)
    cutoff_verification_status: CutoffVerificationStatus = (
        "LEGACY_CUTOFF_UNVERIFIABLE"
    )
    coordinate_version: Literal["canonical-six-pillar-twelve-node.v1"] = (
        "canonical-six-pillar-twelve-node.v1"
    )
    canvas_snapshot: dict[str, Any]
    allowed_nodes: list[HypothesisNodeOption] = Field(default_factory=list)
    allowed_relations: list[HypothesisRelationOption] = Field(default_factory=list)
    input_manifest: dict[str, Any]
    input_manifest_hash: str = Field(min_length=64, max_length=64)
    projection_hash: str = Field(min_length=64, max_length=64)


class BlindRoundDefinition(ExperienceModel):
    schema_version: Literal["deepbazi.blind_round_definition.v1"] = (
        "deepbazi.blind_round_definition.v1"
    )
    round_id: str = Field(min_length=1, max_length=180)
    round_version: str = Field(min_length=1, max_length=80)
    pack_id: str = Field(min_length=1, max_length=180)
    pack_version: str = Field(min_length=1, max_length=80)
    slot_id: str = Field(min_length=1, max_length=120)
    namespace: str = Field(min_length=1, max_length=180)
    resident_scene_ref: str = Field(min_length=16, max_length=180)
    resident_label: str = Field(min_length=1, max_length=120)
    event_family: str = Field(min_length=1, max_length=100)
    evidence_class: EvidenceClass
    development_only: bool
    release_eligible: bool
    verified_real_gate_contribution: int = Field(ge=0, le=1)
    content_state: ContentState
    question: ProblemQuestionRecord
    frozen_projection: FrozenProjectionManifest
    source_snapshot: ImmutableDreamSourceSnapshot | None = None
    question_set: DreamQuestionSet | None = None
    system_judgment_seal_ref: str = Field(min_length=1, max_length=180)
    system_judgment_commitment_hash: str = Field(min_length=64, max_length=64)
    flower_protocol_version: Literal[
        "single-answer-immediate-fruit.v1",
        "multi-answer-shared-fruit.v1",
    ] = "single-answer-immediate-fruit.v1"
    flower_owner_ref: str = Field(default="", max_length=180)
    answer_close_at: datetime | None = None
    outcome_due_at: datetime | None = None
    projection_policy_version: str = DREAM_GAME_PROJECTION_POLICY_VERSION
    evaluation_policy_version: str = DREAM_GAME_EVALUATION_POLICY_VERSION
    reveal_policy_version: str = DREAM_GAME_REVEAL_POLICY_VERSION
    sealed_at: datetime
    published_at: datetime
    immutable_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_publication(self) -> "BlindRoundDefinition":
        if self.sealed_at >= self.published_at:
            raise ValueError("dream_game_system_seal_must_precede_publication")
        if self.evidence_class == "SIMULATED" and (
            not self.development_only
            or self.release_eligible
            or self.verified_real_gate_contribution != 0
        ):
            raise ValueError("dream_game_simulated_round_boundary_invalid")
        if self.evidence_class == "V50_CANONICAL":
            if (
                self.development_only
                or self.release_eligible
                or self.verified_real_gate_contribution != 0
                or self.source_snapshot is None
                or self.question_set is None
                or self.frozen_projection.cutoff_verification_status
                != "VERIFIED_AS_OF_SOURCE_VERSION"
                or self.frozen_projection.source_snapshot_id
                != self.source_snapshot.source_snapshot_id
                or self.question_set.source_snapshot_id
                != self.source_snapshot.source_snapshot_id
                or self.question_set.round_id != self.round_id
            ):
                raise ValueError("dream_game_v50_canonical_round_boundary_invalid")
        if self.flower_protocol_version == DREAM_FLOWER_PROTOCOL_VERSION:
            if (
                not self.flower_owner_ref
                or self.answer_close_at is None
                or self.outcome_due_at is None
                or self.answer_close_at > self.outcome_due_at
            ):
                raise ValueError("dream_game_multi_answer_window_invalid")
        return self


class BlindRoundCard(ExperienceModel):
    round_id: str
    resident_scene_ref: str
    resident_label: str
    anonymous_label: str
    event_family: str
    question_preview: str
    selection_whisper: str = Field(min_length=1, max_length=42)
    evidence_class: EvidenceClass
    development_only: bool
    banner: str = Field(default=DREAM_GAME_BANNER, min_length=1, max_length=160)
    content_state: ContentState
    knowledge_cutoff: datetime
    tree_available: bool = True
    tree_visual_profile: dict[str, Any] = Field(default_factory=dict)


class PreOutcomeDreamProjection(ExperienceModel):
    schema_version: Literal["deepbazi.pre_outcome_dream_projection.v1"] = (
        "deepbazi.pre_outcome_dream_projection.v1"
    )
    projection_ref: str = Field(min_length=32, max_length=180)
    round_id: str
    attempt_id: str
    viewer_id: str
    visit_id: str
    case_namespace: str
    resident_scene_ref: str
    resident_label: str
    authorization_version: str
    knowledge_cutoff: datetime
    clock_domain: str
    source_snapshot_id: str = Field(default="", max_length=180)
    cutoff_verification_status: CutoffVerificationStatus = (
        "LEGACY_CUTOFF_UNVERIFIABLE"
    )
    expires_at: datetime
    frozen_projection_hash: str = Field(min_length=64, max_length=64)
    viewer_projection_hash: str = Field(min_length=64, max_length=64)
    question: ProblemQuestionRecord
    canvas: dict[str, Any]
    allowed_nodes: list[HypothesisNodeOption]
    allowed_relations: list[HypothesisRelationOption]
    available_lenses: list[
        Literal[
            "overview",
            "five_element",
            "combination_conflict",
            "roots_reveal",
            "timing",
            "work_path",
        ]
    ] = Field(min_length=6, max_length=6)
    evidence_class: EvidenceClass
    development_only: bool
    banner: str = Field(default=DREAM_GAME_BANNER, min_length=1, max_length=160)


class PreOutcomeDreamProjectionView(ExperienceModel):
    """Public pre-outcome view; the locked flower question is intentionally absent."""

    schema_version: Literal["deepbazi.pre_outcome_dream_projection_view.v1"] = (
        "deepbazi.pre_outcome_dream_projection_view.v1"
    )
    projection_ref: str = Field(min_length=32, max_length=180)
    round_id: str
    attempt_id: str
    resident_scene_ref: str
    resident_label: str
    authorization_version: str
    knowledge_cutoff: datetime
    clock_domain: str
    source_snapshot_id: str = Field(min_length=16, max_length=180)
    cutoff_verification_status: CutoffVerificationStatus
    expires_at: datetime
    frozen_projection_hash: str = Field(min_length=64, max_length=64)
    viewer_projection_hash: str = Field(min_length=64, max_length=64)
    canvas: dict[str, Any]
    allowed_nodes: list[HypothesisNodeOption]
    allowed_relations: list[HypothesisRelationOption]
    available_lenses: list[
        Literal[
            "overview",
            "five_element",
            "combination_conflict",
            "roots_reveal",
            "timing",
            "work_path",
        ]
    ] = Field(min_length=6, max_length=6)
    evidence_class: EvidenceClass
    development_only: bool
    banner: str = Field(min_length=1, max_length=160)


class DivinationRecord(ExperienceModel):
    schema_version: Literal["deepbazi.divination_record.v1"] = (
        "deepbazi.divination_record.v1"
    )
    divination_id: str
    attempt_id: str
    round_id: str
    viewer_id: str
    explicit_user_intent: Literal[True] = True
    question_id: str
    exact_question: str
    subject_ref: str
    server_timestamp: datetime
    divination_temporality: Literal["RETROSPECTIVE_BLIND", "PROSPECTIVE"]
    casting_method: Literal["server_three_coin_six_line.v1"] = "server_three_coin_six_line.v1"
    line_values_bottom_up: list[int] = Field(min_length=6, max_length=6)
    moving_line_indexes: list[int] = Field(default_factory=list)
    interpretation_status: Literal["not_generated"] = "not_generated"
    authorization_ref: str
    idempotency_key_hash: str = Field(min_length=64, max_length=64)
    immutable_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_lines(self) -> "DivinationRecord":
        if any(item not in {6, 7, 8, 9} for item in self.line_values_bottom_up):
            raise ValueError("dream_game_divination_lines_invalid")
        expected = [
            index + 1 for index, value in enumerate(self.line_values_bottom_up)
            if value in {6, 9}
        ]
        if self.moving_line_indexes != expected:
            raise ValueError("dream_game_divination_moving_lines_invalid")
        return self


class UserPathHypothesis(ExperienceModel):
    hypothesis_id: str
    node_refs: list[str] = Field(default_factory=list, max_length=8)
    relation_refs: list[str] = Field(default_factory=list, max_length=8)
    interpretation: str = Field(default="", max_length=1200)
    formal_status: Literal["USER_HYPOTHESIS_ONLY"] = "USER_HYPOTHESIS_ONLY"


class JudgmentSubmission(ExperienceModel):
    schema_version: Literal["deepbazi.judgment_submission.v1"] = (
        "deepbazi.judgment_submission.v1"
    )
    submission_id: str
    attempt_id: str
    round_id: str
    viewer_id: str
    projection_hash: str = Field(min_length=64, max_length=64)
    selected_outcome_option_id: OutcomeOptionId
    confidence_basis_points: int = Field(ge=0, le=10000)
    user_path_hypothesis: UserPathHypothesis
    evidence_refs: list[str] = Field(default_factory=list, max_length=24)
    strongest_alternative: str = Field(min_length=1, max_length=1000)
    disconfirmation_condition: str = Field(min_length=1, max_length=1000)
    assistance_mode: AnswerAssistanceMode = "INDEPENDENT"
    divination_ref: str = Field(default="", max_length=180)
    created_at: datetime
    immutable_hash: str = Field(min_length=64, max_length=64)


class UserJudgmentSeal(ExperienceModel):
    schema_version: Literal["deepbazi.user_judgment_seal.v1"] = (
        "deepbazi.user_judgment_seal.v1"
    )
    seal_id: str
    round_id: str
    attempt_id: str
    viewer_id: str
    submission_ref: str
    projection_hash: str = Field(min_length=64, max_length=64)
    submission_hash: str = Field(min_length=64, max_length=64)
    sealed_at: datetime
    immutable_hash: str = Field(min_length=64, max_length=64)


class SystemJudgmentSeal(ExperienceModel):
    schema_version: Literal["deepbazi.system_judgment_seal.v1"] = (
        "deepbazi.system_judgment_seal.v1"
    )
    seal_id: str
    round_id: str
    projection_hash: str = Field(min_length=64, max_length=64)
    selected_outcome_option_id: OutcomeOptionId
    confidence_basis_points: int = Field(ge=0, le=10000)
    formal_path_assertion_refs: list[str] = Field(default_factory=list)
    candidate_path_refs: list[str] = Field(default_factory=list)
    reasoning_summary: str = Field(min_length=1, max_length=1600)
    strongest_alternative: str = Field(min_length=1, max_length=1000)
    disconfirmation_condition: str = Field(min_length=1, max_length=1000)
    model_version: str
    prompt_version: str
    reasoner_version: str
    knowledge_versions: list[str]
    input_manifest: dict[str, Any]
    input_manifest_hash: str = Field(min_length=64, max_length=64)
    generated_at: datetime
    sealed_at: datetime
    immutable_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def reject_player_inputs(self) -> "SystemJudgmentSeal":
        forbidden = {
            "player",
            "viewer",
            "submission",
            "confidence",
            "user_path_hypothesis",
            "player_text",
            "player_choice",
        }
        keys = {str(key).lower() for key in self.input_manifest}
        if keys & forbidden:
            raise ValueError("dream_game_system_seal_player_input_forbidden")
        return self


class FlowerLifecycle(ExperienceModel):
    schema_version: Literal["deepbazi.flower_lifecycle.v1"] = (
        "deepbazi.flower_lifecycle.v1"
    )
    flower_id: str = Field(min_length=16, max_length=180)
    round_id: str = Field(min_length=1, max_length=180)
    protocol_version: Literal["multi-answer-shared-fruit.v1"] = (
        DREAM_FLOWER_PROTOCOL_VERSION
    )
    owner_ref: str = Field(min_length=1, max_length=180)
    question_seal_ref: str = Field(min_length=1, max_length=180)
    answer_close_at: datetime
    outcome_due_at: datetime
    state: FlowerLifecycleState = "OPEN"
    answer_count: int = Field(default=0, ge=0)
    closure_ref: str = Field(default="", max_length=180)
    shared_fruit_ref: str = Field(default="", max_length=180)
    created_at: datetime
    updated_at: datetime
    row_version: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "FlowerLifecycle":
        if self.answer_close_at > self.outcome_due_at:
            raise ValueError("dream_game_multi_answer_window_invalid")
        if self.state == "OPEN" and (self.closure_ref or self.shared_fruit_ref):
            raise ValueError("dream_game_open_flower_has_closure")
        if self.state == "CLOSED_NO_RESPONSE" and (
            self.answer_count != 0 or not self.closure_ref or self.shared_fruit_ref
        ):
            raise ValueError("dream_game_empty_flower_closure_invalid")
        if self.state == "SHARED_FRUIT_FORMED" and (
            self.answer_count < 1 or not self.closure_ref or not self.shared_fruit_ref
        ):
            raise ValueError("dream_game_shared_fruit_state_invalid")
        return self


class FlowerClosureRecord(ExperienceModel):
    schema_version: Literal["deepbazi.flower_closure_record.v1"] = (
        "deepbazi.flower_closure_record.v1"
    )
    closure_id: str = Field(min_length=16, max_length=180)
    flower_id: str = Field(min_length=16, max_length=180)
    round_id: str = Field(min_length=1, max_length=180)
    question_seal_ref: str = Field(min_length=1, max_length=180)
    closed_at: datetime
    close_reason: FlowerCloseReason
    answer_seal_refs: list[str]
    answer_count: int = Field(ge=0)
    answer_set_hash: str = Field(min_length=64, max_length=64)
    trigger_kind: Literal["OWNER", "SYSTEM"]
    trigger_ref: str = Field(min_length=1, max_length=180)
    idempotency_key_hash: str = Field(min_length=64, max_length=64)
    immutable_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_answer_set(self) -> "FlowerClosureRecord":
        if self.answer_count != len(self.answer_seal_refs):
            raise ValueError("dream_game_flower_answer_count_mismatch")
        if self.answer_seal_refs != sorted(set(self.answer_seal_refs)):
            raise ValueError("dream_game_flower_answer_set_not_canonical")
        return self


class SharedFruit(ExperienceModel):
    schema_version: Literal["deepbazi.shared_fruit.v1"] = "deepbazi.shared_fruit.v1"
    fruit_id: str = Field(min_length=16, max_length=180)
    flower_id: str = Field(min_length=16, max_length=180)
    round_id: str = Field(min_length=1, max_length=180)
    question_seal_ref: str = Field(min_length=1, max_length=180)
    closure_ref: str = Field(min_length=16, max_length=180)
    answer_set_hash: str = Field(min_length=64, max_length=64)
    answer_count: int = Field(ge=1)
    visual_state: Literal["MIST_WHITE"] = "MIST_WHITE"
    formed_at: datetime
    outcome_due_at: datetime
    immutable_hash: str = Field(min_length=64, max_length=64)


class FlowerLifecycleView(ExperienceModel):
    schema_version: Literal["deepbazi.flower_lifecycle_view.v1"] = (
        "deepbazi.flower_lifecycle_view.v1"
    )
    flower_id: str
    state: FlowerLifecycleState
    answer_close_at: datetime
    outcome_due_at: datetime
    own_answer_sealed: bool
    answer_count_visible: bool
    answer_count: int | None = Field(default=None, ge=0)
    close_reason: FlowerCloseReason | None = None
    shared_fruit_visible: bool
    revealable: bool
    neutral_message: str = Field(min_length=1, max_length=240)


class OutcomeEvidence(ExperienceModel):
    schema_version: Literal["deepbazi.outcome_evidence.v1"] = (
        "deepbazi.outcome_evidence.v1"
    )
    evidence_id: str
    round_id: str
    evidence_class: EvidenceClass
    verification_status: Literal["VERIFIED", "UNVERIFIED", "DISPUTED", "WITHDRAWN"]
    resolved_option_id: OutcomeOptionId
    outcome_summary: str = Field(min_length=1, max_length=1600)
    evidence_items: list[str] = Field(min_length=1, max_length=12)
    chain_of_custody_manifest_hash: str = Field(min_length=64, max_length=64)
    occurred_at: datetime
    verified_at: datetime
    immutable_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_simulated_boundary(self) -> "OutcomeEvidence":
        if self.evidence_class in {"SIMULATED", "V50_CANONICAL"} and (
            self.verification_status != "VERIFIED"
        ):
            raise ValueError("dream_game_simulated_fixture_must_be_internally_verified")
        return self


class OutcomeRevealRecord(ExperienceModel):
    schema_version: Literal["deepbazi.outcome_reveal_record.v1"] = (
        "deepbazi.outcome_reveal_record.v1"
    )
    reveal_id: str
    attempt_id: str
    round_id: str
    viewer_id: str
    user_seal_ref: str
    system_seal_ref: str
    evidence_ref: str
    revealed_at: datetime
    idempotency_key_hash: str = Field(min_length=64, max_length=64)
    immutable_hash: str = Field(min_length=64, max_length=64)


class JudgmentEvaluation(ExperienceModel):
    option_match: bool
    confidence_bucket: ConfidenceBucket
    formal_evidence_support: Literal["NOT_REVIEWED"] = "NOT_REVIEWED"
    decisive_node_omissions: list[str] = Field(default_factory=list)
    disconfirmation_condition_quality: Literal["VALID", "INVALID"]


class EvaluationRecord(ExperienceModel):
    schema_version: Literal["deepbazi.evaluation_record.v1"] = (
        "deepbazi.evaluation_record.v1"
    )
    evaluation_id: str
    attempt_id: str
    round_id: str
    user_seal_ref: str
    system_seal_ref: str
    reveal_ref: str
    evaluation_policy_version: str
    user_result: JudgmentEvaluation
    system_result: JudgmentEvaluation
    outcome_choice_differs: bool
    confidence_gap_basis_points: int = Field(ge=0, le=10000)
    path_reference_overlap: Literal["NOT_REVIEWED"] = "NOT_REVIEWED"
    limitations: list[str]
    evaluated_at: datetime
    immutable_hash: str = Field(min_length=64, max_length=64)


class KnowledgeSeed(ExperienceModel):
    schema_version: Literal["deepbazi.knowledge_seed.v1"] = "deepbazi.knowledge_seed.v1"
    seed_id: str
    attempt_id: str
    round_id: str
    viewer_id: str
    evaluation_ref: str
    issued_calibration_summary: str = Field(min_length=1, max_length=1600)
    observation_kept: list[str] = Field(default_factory=list)
    missed_or_overweighted: list[str] = Field(default_factory=list)
    applicable_boundary: str = Field(min_length=1, max_length=1200)
    formal_status: Literal["PRIVATE_LEARNING_RECORD"] = "PRIVATE_LEARNING_RECORD"
    issued_at: datetime
    immutable_hash: str = Field(min_length=64, max_length=64)


class DreamGameRecordEnvelope(ExperienceModel):
    record_id: str
    record_kind: Literal[
        "divination",
        "learning_answer",
        "judgment_submission",
        "user_judgment_seal",
        "flower_closure",
        "shared_fruit",
        "outcome_reveal",
        "evaluation",
        "knowledge_seed",
        "content_revocation",
    ]
    round_id: str
    viewer_id: str = ""
    immutable_hash: str = Field(min_length=64, max_length=64)
    payload: dict[str, Any]
    created_at: datetime


class DreamGameAttempt(ExperienceModel):
    schema_version: Literal["deepbazi.dream_game_attempt.v1"] = (
        "deepbazi.dream_game_attempt.v1"
    )
    attempt_id: str
    round_id: str
    viewer_id: str
    visit_id: str
    case_namespace: str
    resident_scene_ref: str
    state: DreamGameState
    projection: PreOutcomeDreamProjection
    question_set_ref: str = Field(default="", max_length=180)
    question_progress: DreamQuestionAttemptProgress | None = None
    observed_lenses: list[str] = Field(default_factory=list)
    divination_ref: str = ""
    submission_ref: str = ""
    user_seal_ref: str = ""
    answer_source_attempt_id: str = ""
    reveal_ref: str = ""
    evaluation_ref: str = ""
    knowledge_seed_ref: str = ""
    created_at: datetime
    updated_at: datetime
    row_version: int = Field(default=1, ge=1)
    state_history: list[DreamGameState] = Field(default_factory=list, max_length=64)

    @model_validator(mode="after")
    def validate_projection_binding(self) -> "DreamGameAttempt":
        if (
            self.projection.attempt_id != self.attempt_id
            or self.projection.round_id != self.round_id
            or self.projection.viewer_id != self.viewer_id
            or self.projection.visit_id != self.visit_id
            or self.projection.case_namespace != self.case_namespace
        ):
            raise ValueError("dream_game_attempt_projection_binding_invalid")
        if self.question_progress is not None and (
            self.question_progress.question_set_id != self.question_set_ref
        ):
            raise ValueError("dream_game_attempt_question_set_binding_invalid")
        return self


class DreamGameAttemptView(ExperienceModel):
    attempt_id: str
    round_id: str
    state: DreamGameState
    projection: PreOutcomeDreamProjectionView
    question_set: DreamQuestionSetProjection
    question_progress: DreamQuestionAttemptProgress
    flower_question: ProblemQuestionRecord | None = None
    observed_lenses: list[str]
    divination: DivinationRecord | None = None
    flower: FlowerLifecycleView | None = None
    sealed: bool
    revealable: bool
    completed: bool
    updated_at: datetime


class DreamGameResultProjection(ExperienceModel):
    schema_version: Literal["deepbazi.dream_game_result_projection.v1"] = (
        "deepbazi.dream_game_result_projection.v1"
    )
    banner: str = Field(default=DREAM_GAME_BANNER, min_length=1, max_length=160)
    evidence_class: EvidenceClass
    development_only: bool
    submission: JudgmentSubmission
    user_seal: UserJudgmentSeal
    shared_fruit: SharedFruit | None = None
    system_seal: SystemJudgmentSeal
    outcome_evidence: OutcomeEvidence
    reveal_record: OutcomeRevealRecord
    evaluation: EvaluationRecord
    knowledge_seed: KnowledgeSeed


__all__ = [
    "BlindRoundCard",
    "BlindRoundDefinition",
    "ContentPackAudit",
    "ContentState",
    "DREAM_GAME_BANNER",
    "DREAM_GAME_EVALUATION_POLICY_VERSION",
    "DREAM_GAME_PROJECTION_POLICY_VERSION",
    "DREAM_GAME_REVEAL_POLICY_VERSION",
    "DREAM_GAME_SCHEMA_VERSION",
    "DREAM_GAME_SIMULATED_NAMESPACE",
    "DREAM_GAME_V50_BANNER",
    "DREAM_GAME_V50_NAMESPACE",
    "DREAM_QUESTION_SET_VERSION",
    "DREAM_FLOWER_PROTOCOL_VERSION",
    "DivinationRecord",
    "DreamLearningAnswerRecord",
    "DreamLearningQuestion",
    "DreamLearningQuestionKind",
    "DreamLearningQuestionOption",
    "DreamLearningQuestionPublic",
    "DreamFlowerRevealPolicy",
    "DreamGameAttempt",
    "DreamGameAttemptView",
    "DreamGameRecordEnvelope",
    "DreamGameResultProjection",
    "DreamGameState",
    "DreamQuestionAttemptProgress",
    "DreamQuestionContentState",
    "DreamQuestionDependencyEdge",
    "DreamQuestionDomain",
    "DreamQuestionOrganRole",
    "DreamQuestionProgressItem",
    "DreamQuestionSet",
    "DreamQuestionSetProjection",
    "DreamQuestionStoryScript",
    "EvaluationRecord",
    "EvidenceClass",
    "FrozenProjectionManifest",
    "FlowerClosureRecord",
    "FlowerLifecycle",
    "FlowerLifecycleView",
    "HypothesisNodeOption",
    "HypothesisRelationOption",
    "ImmutableDreamSourceSnapshot",
    "JudgmentEvaluation",
    "JudgmentSubmission",
    "KnowledgeSeed",
    "MaturedFruitContentPack",
    "MaturedFruitSlot",
    "OutcomeEvidence",
    "OutcomeOptionId",
    "OutcomeRevealRecord",
    "PreOutcomeDreamProjection",
    "PreOutcomeDreamProjectionView",
    "ProblemQuestionRecord",
    "SystemJudgmentSeal",
    "SharedFruit",
    "UserJudgmentSeal",
    "UserPathHypothesis",
]
