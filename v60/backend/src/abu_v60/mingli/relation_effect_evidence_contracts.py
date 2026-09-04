from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.knowledge.relation_effect_contracts import (
    RELATION_EFFECT_RULE_DIMENSIONS,
    RelationEffectProposalDimensionStatus,
    RelationEffectRuleDimension,
)
from abu_v60.provenance import content_hash, stable_ref

RELATION_EFFECT_EVIDENCE_PACKET_VERSION = "v60.mingli-relation-effect-evidence-packet.001"
RELATION_EFFECT_EVIDENCE_DECISION_PATH = (
    "DETERMINISTIC_RELATION_FACT_AVAILABLE",
    "PROFESSIONAL_RULE_EVIDENCE_BLOCKED",
    "OWNER_PROFESSIONAL_REVIEW_NOT_INVOKED",
    "KNOWLEDGE_ADMISSION_NOT_ELIGIBLE",
    "READING_RULE_PROFILE_QUALIFICATION_NOT_AUTHORIZED",
    "EFFECT_DECISION_WITHHELD",
)
RELATION_EFFECT_REQUIRED_PROFESSIONAL_PATH = (
    "COMPLETE_PROFESSIONAL_EVIDENCE_PACKET",
    "OWNER_PROFESSIONAL_REVIEW_APPROVED",
    "KNOWLEDGE_IMMUTABLE_RULE_PROFILE_ADMITTED",
    "NEW_READING_BINDS_ADMITTED_RULE_PROFILE",
    "DETERMINISTIC_RULE_APPLICATION_OR_UNRESOLVED",
)

RelationEffectProfessionalArtifactKind = Literal[
    "PROFESSIONAL_APPLICABILITY_RULE",
    "PROFESSIONAL_EFFECT_DIRECTION_RULE",
    "PROFESSIONAL_COMPLETION_RULE",
    "PROFESSIONAL_BLOCKING_RULE",
    "PROFESSIONAL_COUNTER_EVIDENCE_PROTOCOL",
    "PROFESSIONAL_SOURCE_MANIFEST",
    "PROFESSIONAL_SOURCE_CITATION",
    "OWNER_PROFESSIONAL_REVIEW_RECEIPT",
]
RelationEffectEvidenceDecisionStep = Literal[
    "DETERMINISTIC_RELATION_FACT_AVAILABLE",
    "PROFESSIONAL_RULE_EVIDENCE_BLOCKED",
    "OWNER_PROFESSIONAL_REVIEW_NOT_INVOKED",
    "KNOWLEDGE_ADMISSION_NOT_ELIGIBLE",
    "READING_RULE_PROFILE_QUALIFICATION_NOT_AUTHORIZED",
    "EFFECT_DECISION_WITHHELD",
]
RelationEffectRequiredProfessionalStep = Literal[
    "COMPLETE_PROFESSIONAL_EVIDENCE_PACKET",
    "OWNER_PROFESSIONAL_REVIEW_APPROVED",
    "KNOWLEDGE_IMMUTABLE_RULE_PROFILE_ADMITTED",
    "NEW_READING_BINDS_ADMITTED_RULE_PROFILE",
    "DETERMINISTIC_RULE_APPLICATION_OR_UNRESOLVED",
]

RELATION_EFFECT_EVIDENCE_REQUIREMENTS = {
    "APPLICABILITY_CONTEXT": (
        "需要专业规则明确子午六冲成员关系在本命、严格同干与支藏来源坐标中何时可向作用命题传播。"
    ),
    "EFFECT_DIRECTION": (
        "需要专业规则在扰动、打开或暴露、损伤或移除等竞争解释间给出可复核的方向判据。"
    ),
    "COMPLETION_CONDITIONS": ("需要专业规则给出关系作用从成员事实到完成状态的必要与充分条件。"),
    "BLOCKING_CONDITIONS": ("需要专业规则给出合会、距离、时令及其他条件如何阻断或改变该作用原子。"),
    "COUNTER_EVIDENCE": ("需要专业反例协议定义逐项反证、撤销条件与适用边界。"),
    "PROFESSIONAL_PROVENANCE": ("需要命题级专业来源清单、可定位引文及 Owner 专业审阅回执。"),
}
RELATION_EFFECT_EVIDENCE_REQUESTED_ARTIFACTS: dict[
    RelationEffectRuleDimension,
    tuple[RelationEffectProfessionalArtifactKind, ...],
] = {
    "APPLICABILITY_CONTEXT": (
        "PROFESSIONAL_APPLICABILITY_RULE",
        "PROFESSIONAL_SOURCE_CITATION",
    ),
    "EFFECT_DIRECTION": (
        "PROFESSIONAL_EFFECT_DIRECTION_RULE",
        "PROFESSIONAL_SOURCE_CITATION",
    ),
    "COMPLETION_CONDITIONS": (
        "PROFESSIONAL_COMPLETION_RULE",
        "PROFESSIONAL_SOURCE_CITATION",
    ),
    "BLOCKING_CONDITIONS": (
        "PROFESSIONAL_BLOCKING_RULE",
        "PROFESSIONAL_SOURCE_CITATION",
    ),
    "COUNTER_EVIDENCE": (
        "PROFESSIONAL_COUNTER_EVIDENCE_PROTOCOL",
        "PROFESSIONAL_SOURCE_CITATION",
    ),
    "PROFESSIONAL_PROVENANCE": (
        "PROFESSIONAL_SOURCE_MANIFEST",
        "PROFESSIONAL_SOURCE_CITATION",
        "OWNER_PROFESSIONAL_REVIEW_RECEIPT",
    ),
}
RELATION_EFFECT_EVIDENCE_NEXT_ACTIONS = {
    "APPLICABILITY_CONTEXT": ("提交带版本与章节定位的适用范围规则，保持当前坐标事实只作上下文。"),
    "EFFECT_DIRECTION": ("提交能排除竞争解释的专业方向规则与对应引文。"),
    "COMPLETION_CONDITIONS": ("提交可执行且可反驳的作用完成条件。"),
    "BLOCKING_CONDITIONS": ("提交逐项阻断条件及其优先级、适用范围与引文。"),
    "COUNTER_EVIDENCE": ("提交反例类型、撤销条件与负向案例协议。"),
    "PROFESSIONAL_PROVENANCE": (
        "提交专业来源清单、命题级引文，并在材料完整后请求 Owner 专业审阅。"
    ),
}


class RelationEffectEvidenceDimensionSlot(BaseModel):
    """One canonical readiness slot; runtime context is not professional evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    slot_ref: str = Field(min_length=1)
    dimension_id: RelationEffectRuleDimension
    proposal_submission_status: RelationEffectProposalDimensionStatus
    current_basis_refs: tuple[str, ...]
    current_basis_status: Literal["RUNTIME_CONTEXT_ONLY_NOT_PROFESSIONAL_EVIDENCE"]
    requirement: str = Field(min_length=1)
    requested_artifact_kinds: tuple[
        RelationEffectProfessionalArtifactKind,
        ...,
    ] = Field(min_length=2, max_length=3)
    guidance_semantics: Literal["REQUEST_GUIDANCE_NOT_KNOWLEDGE_ADMISSION"]
    professional_evidence_refs: tuple[str, ...]
    professional_evidence_count: Literal[0]
    slot_status: Literal["BLOCKED_MISSING_PROFESSIONAL_EVIDENCE"]
    next_action: str = Field(min_length=1)
    ready: Literal[False]

    @model_validator(mode="after")
    def canonical_shape_and_identity_are_valid(
        self,
    ) -> RelationEffectEvidenceDimensionSlot:
        if len(self.current_basis_refs) != len(set(self.current_basis_refs)):
            raise ValueError("relation_effect_evidence_slot_basis_not_unique")
        if self.professional_evidence_refs:
            raise ValueError("relation_effect_evidence_slot_professional_evidence_not_admitted")
        if set(self.current_basis_refs) & set(self.professional_evidence_refs):
            raise ValueError("relation_effect_evidence_slot_basis_evidence_overlap")
        expected = (
            RELATION_EFFECT_EVIDENCE_REQUIREMENTS[self.dimension_id],
            RELATION_EFFECT_EVIDENCE_REQUESTED_ARTIFACTS[self.dimension_id],
            RELATION_EFFECT_EVIDENCE_NEXT_ACTIONS[self.dimension_id],
        )
        if (
            self.requirement,
            self.requested_artifact_kinds,
            self.next_action,
        ) != expected:
            raise ValueError("relation_effect_evidence_slot_canonical_guidance_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"slot_ref"},
        )
        if self.slot_ref != stable_ref(
            "v60-relation-effect-evidence-slot",
            identity,
        ):
            raise ValueError("relation_effect_evidence_slot_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        *,
        dimension_id: RelationEffectRuleDimension,
        proposal_submission_status: (RelationEffectProposalDimensionStatus),
        current_basis_refs: tuple[str, ...],
    ) -> RelationEffectEvidenceDimensionSlot:
        identity = {
            "dimension_id": dimension_id,
            "proposal_submission_status": (proposal_submission_status),
            "current_basis_refs": current_basis_refs,
            "current_basis_status": ("RUNTIME_CONTEXT_ONLY_NOT_PROFESSIONAL_EVIDENCE"),
            "requirement": RELATION_EFFECT_EVIDENCE_REQUIREMENTS[dimension_id],
            "requested_artifact_kinds": (
                RELATION_EFFECT_EVIDENCE_REQUESTED_ARTIFACTS[dimension_id]
            ),
            "guidance_semantics": ("REQUEST_GUIDANCE_NOT_KNOWLEDGE_ADMISSION"),
            "professional_evidence_refs": (),
            "professional_evidence_count": 0,
            "slot_status": ("BLOCKED_MISSING_PROFESSIONAL_EVIDENCE"),
            "next_action": RELATION_EFFECT_EVIDENCE_NEXT_ACTIONS[dimension_id],
            "ready": False,
        }
        return cls(
            slot_ref=stable_ref(
                "v60-relation-effect-evidence-slot",
                identity,
            ),
            **identity,
        )


class RelationEffectDemandEvidencePacket(BaseModel):
    """Six-slot professional evidence intake packet for one assessed demand."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    demand_packet_ref: str = Field(min_length=1)
    demand_packet_hash: str = Field(min_length=64, max_length=64)
    assessment_ref: str = Field(min_length=1)
    assessment_hash: str = Field(min_length=64, max_length=64)
    demand_ref: str = Field(min_length=1)
    source_review_ref: str = Field(min_length=1)
    source_evidence_ref: str = Field(min_length=1)
    intersection_ref: str = Field(min_length=1)
    relation_fact_ref: str = Field(min_length=1)
    carrier_ref: str = Field(min_length=1)
    visible_slot: Literal["year", "month", "day", "hour"]
    visible_stem: str = Field(min_length=1, max_length=1)
    source_slot: Literal["year", "month", "day", "hour"]
    source_branch: Literal["午"]
    peer_slot: Literal["year", "month", "day", "hour"]
    peer_branch: Literal["子"]
    relation_type: Literal["six_clash_membership"]
    source_match_kind: Literal["EXACT_IDENTITY"]
    policy_ref: str = Field(min_length=1)
    policy_hash: str = Field(min_length=64, max_length=64)
    proposal_ref: str = Field(min_length=1)
    proposal_hash: str = Field(min_length=64, max_length=64)
    dimension_slots: tuple[
        RelationEffectEvidenceDimensionSlot,
        ...,
    ] = Field(min_length=6, max_length=6)
    required_dimension_slot_count: Literal[6]
    ready_dimension_slot_count: Literal[0]
    professional_evidence_count: Literal[0]
    status: Literal["EVIDENCE_INTAKE_REQUIRED"]
    effect_status: Literal["UNRESOLVED"]
    usability_status: Literal["UNRESOLVED"]

    @model_validator(mode="after")
    def dimensions_counts_and_identity_are_valid(
        self,
    ) -> RelationEffectDemandEvidencePacket:
        if (
            tuple(item.dimension_id for item in self.dimension_slots)
            != RELATION_EFFECT_RULE_DIMENSIONS
        ):
            raise ValueError("relation_effect_evidence_packet_dimensions_invalid")
        if any(
            item.ready or item.professional_evidence_refs or item.professional_evidence_count
            for item in self.dimension_slots
        ):
            raise ValueError("relation_effect_evidence_packet_professional_evidence_invalid")
        identity = self.model_dump(
            mode="json",
            exclude={"demand_packet_ref", "demand_packet_hash"},
        )
        if self.demand_packet_hash != content_hash(identity):
            raise ValueError("relation_effect_evidence_demand_packet_hash_mismatch")
        if self.demand_packet_ref != stable_ref(
            "v60-relation-effect-demand-evidence-packet",
            identity,
        ):
            raise ValueError("relation_effect_evidence_demand_packet_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        **values: Any,
    ) -> RelationEffectDemandEvidencePacket:
        identity = {
            **values,
            "dimension_slots": tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in values["dimension_slots"]
            ),
            "required_dimension_slot_count": 6,
            "ready_dimension_slot_count": 0,
            "professional_evidence_count": 0,
            "status": "EVIDENCE_INTAKE_REQUIRED",
            "effect_status": "UNRESOLVED",
            "usability_status": "UNRESOLVED",
        }
        return cls(
            demand_packet_ref=stable_ref(
                "v60-relation-effect-demand-evidence-packet",
                identity,
            ),
            demand_packet_hash=content_hash(identity),
            **identity,
        )


class MingliRelationEffectEvidencePacketEnvelope(BaseModel):
    """Read-only professional evidence readiness, never an effect decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    packet_ref: str = Field(min_length=1)
    packet_hash: str = Field(min_length=64, max_length=64)
    packet_version: Literal["v60.mingli-relation-effect-evidence-packet.001"] = (
        RELATION_EFFECT_EVIDENCE_PACKET_VERSION
    )
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    frontier_ref: str = Field(min_length=1)
    frontier_hash: str = Field(min_length=64, max_length=64)
    admission_review_ref: str = Field(min_length=1)
    admission_review_hash: str = Field(min_length=64, max_length=64)
    policy_ref: str = Field(min_length=1)
    policy_hash: str = Field(min_length=64, max_length=64)
    proposal_ref: str = Field(min_length=1)
    proposal_hash: str = Field(min_length=64, max_length=64)
    demand_packets: tuple[RelationEffectDemandEvidencePacket, ...]
    demand_packet_count: int = Field(ge=0)
    required_dimension_slot_count: int = Field(ge=0)
    ready_dimension_slot_count: Literal[0]
    professional_evidence_count: Literal[0]
    status: Literal["EVIDENCE_INTAKE_REQUIRED", "NOT_TRIGGERED"]
    projection_semantics: Literal["PROFESSIONAL_EVIDENCE_READINESS_NOT_DECISION"]
    decision_path_semantics: Literal["READINESS_PATH_NOT_DECISION"]
    decision_path: tuple[RelationEffectEvidenceDecisionStep, ...]
    required_professional_path_semantics: Literal["FUTURE_AUTHORITY_PATH_NOT_EXECUTED"]
    required_professional_path: tuple[
        RelationEffectRequiredProfessionalStep,
        ...,
    ]
    effect_decision_status: Literal["WITHHELD", "NOT_TRIGGERED"]
    effect_status: Literal["UNRESOLVED"]
    usability_status: Literal["UNRESOLVED"]
    knowledge_admission_eligible: Literal[False]
    llm_allowed: Literal[False]
    provider_invoked: Literal[False]
    reasoner_invoked: Literal[False]
    decision_request_created: Literal[False]
    owner_professional_review_invoked: Literal[False]
    knowledge_promotion_request_created: Literal[False]
    gate_invoked: Literal[False]
    ledger_invoked: Literal[False]
    decision_created: Literal[False]
    selection_authority: Literal[False]
    professional_verdict_allowed: Literal[False]
    probability_claim_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def counts_path_boundaries_and_identity_are_valid(
        self,
    ) -> MingliRelationEffectEvidencePacketEnvelope:
        assessment_refs = tuple(item.assessment_ref for item in self.demand_packets)
        if assessment_refs != tuple(sorted(set(assessment_refs))):
            raise ValueError("relation_effect_evidence_packets_not_ordered_unique")
        if self.demand_packet_count != len(self.demand_packets):
            raise ValueError("relation_effect_evidence_packet_count_mismatch")
        if self.required_dimension_slot_count != (6 * len(self.demand_packets)):
            raise ValueError("relation_effect_evidence_slot_count_mismatch")
        triggered = bool(self.demand_packets)
        expected = (
            (
                "EVIDENCE_INTAKE_REQUIRED",
                RELATION_EFFECT_EVIDENCE_DECISION_PATH,
                "WITHHELD",
            )
            if triggered
            else ("NOT_TRIGGERED", (), "NOT_TRIGGERED")
        )
        if (
            self.status,
            self.decision_path,
            self.effect_decision_status,
        ) != expected:
            raise ValueError("relation_effect_evidence_readiness_path_mismatch")
        if self.required_professional_path != RELATION_EFFECT_REQUIRED_PROFESSIONAL_PATH:
            raise ValueError("relation_effect_evidence_professional_path_mismatch")
        if any(
            item.policy_ref != self.policy_ref
            or item.policy_hash != self.policy_hash
            or item.proposal_ref != self.proposal_ref
            or item.proposal_hash != self.proposal_hash
            for item in self.demand_packets
        ):
            raise ValueError("relation_effect_evidence_authority_binding_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"packet_ref", "packet_hash"},
        )
        if self.packet_hash != content_hash(identity):
            raise ValueError("relation_effect_evidence_packet_hash_mismatch")
        if self.packet_ref != stable_ref(
            "v60-relation-effect-evidence-packet",
            identity,
        ):
            raise ValueError("relation_effect_evidence_packet_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        **values: Any,
    ) -> MingliRelationEffectEvidencePacketEnvelope:
        demand_packets = tuple(
            sorted(
                values["demand_packets"],
                key=lambda item: item.assessment_ref,
            )
        )
        triggered = bool(demand_packets)
        identity = {
            "packet_version": (RELATION_EFFECT_EVIDENCE_PACKET_VERSION),
            **values,
            "demand_packets": tuple(item.model_dump(mode="json") for item in demand_packets),
            "demand_packet_count": len(demand_packets),
            "required_dimension_slot_count": (6 * len(demand_packets)),
            "ready_dimension_slot_count": 0,
            "professional_evidence_count": 0,
            "status": ("EVIDENCE_INTAKE_REQUIRED" if triggered else "NOT_TRIGGERED"),
            "projection_semantics": ("PROFESSIONAL_EVIDENCE_READINESS_NOT_DECISION"),
            "decision_path_semantics": ("READINESS_PATH_NOT_DECISION"),
            "decision_path": (RELATION_EFFECT_EVIDENCE_DECISION_PATH if triggered else ()),
            "required_professional_path_semantics": ("FUTURE_AUTHORITY_PATH_NOT_EXECUTED"),
            "required_professional_path": (RELATION_EFFECT_REQUIRED_PROFESSIONAL_PATH),
            "effect_decision_status": ("WITHHELD" if triggered else "NOT_TRIGGERED"),
            "effect_status": "UNRESOLVED",
            "usability_status": "UNRESOLVED",
            "knowledge_admission_eligible": False,
            "llm_allowed": False,
            "provider_invoked": False,
            "reasoner_invoked": False,
            "decision_request_created": False,
            "owner_professional_review_invoked": False,
            "knowledge_promotion_request_created": False,
            "gate_invoked": False,
            "ledger_invoked": False,
            "decision_created": False,
            "selection_authority": False,
            "professional_verdict_allowed": False,
            "probability_claim_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            packet_ref=stable_ref(
                "v60-relation-effect-evidence-packet",
                identity,
            ),
            packet_hash=content_hash(identity),
            **identity,
        )
