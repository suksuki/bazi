from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.knowledge.relation_effect_contracts import (
    RELATION_EFFECT_RULE_DIMENSIONS,
    RelationEffectRuleDimension,
)
from abu_v60.mingli.relation_effect_evidence_contracts import (
    RELATION_EFFECT_EVIDENCE_NEXT_ACTIONS,
    RELATION_EFFECT_EVIDENCE_REQUESTED_ARTIFACTS,
    RELATION_EFFECT_EVIDENCE_REQUIREMENTS,
    RelationEffectProfessionalArtifactKind,
)
from abu_v60.provenance import content_hash, stable_ref

RELATION_EFFECT_EVIDENCE_REQUEST_VERSION = (
    "v60.mingli-relation-effect-evidence-request.001"
)
RELATION_EFFECT_EVIDENCE_REQUEST_RECEIPT_VERSION = (
    "v60.mingli-relation-effect-evidence-request-receipt.001"
)


class RelationEffectEvidencePreparationRequest(BaseModel):
    """Replay-safe request to prepare the current server-owned evidence gaps."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_version: Literal[
        "v60.mingli-relation-effect-evidence-request.001"
    ]
    expected_packet_ref: str = Field(min_length=1)
    expected_packet_hash: str = Field(min_length=64, max_length=64)
    idempotency_key: str = Field(min_length=1, max_length=180)


class RelationEffectEvidenceRequestedSlot(BaseModel):
    """Server-derived request for one existing readiness slot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    slot_ref: str = Field(min_length=1)
    dimension_id: RelationEffectRuleDimension
    requirement: str = Field(min_length=1)
    requested_artifact_kinds: tuple[
        RelationEffectProfessionalArtifactKind,
        ...,
    ] = Field(min_length=2, max_length=3)
    next_action: str = Field(min_length=1)
    status: Literal["REQUESTED_NOT_EVIDENCE"]
    professional_material_count: Literal[0]
    professional_evidence_count: Literal[0]
    ready: Literal[False]

    @model_validator(mode="after")
    def canonical_guidance_is_valid(
        self,
    ) -> RelationEffectEvidenceRequestedSlot:
        expected = (
            RELATION_EFFECT_EVIDENCE_REQUIREMENTS[self.dimension_id],
            RELATION_EFFECT_EVIDENCE_REQUESTED_ARTIFACTS[
                self.dimension_id
            ],
            RELATION_EFFECT_EVIDENCE_NEXT_ACTIONS[self.dimension_id],
        )
        if (
            self.requirement,
            self.requested_artifact_kinds,
            self.next_action,
        ) != expected:
            raise ValueError(
                "relation_effect_evidence_request_slot_"
                "canonical_guidance_mismatch"
            )
        return self

    @classmethod
    def issue(
        cls,
        *,
        slot_ref: str,
        dimension_id: RelationEffectRuleDimension,
        requirement: str,
        requested_artifact_kinds: tuple[
            RelationEffectProfessionalArtifactKind,
            ...,
        ],
        next_action: str,
    ) -> RelationEffectEvidenceRequestedSlot:
        return cls(
            slot_ref=slot_ref,
            dimension_id=dimension_id,
            requirement=requirement,
            requested_artifact_kinds=requested_artifact_kinds,
            next_action=next_action,
            status="REQUESTED_NOT_EVIDENCE",
            professional_material_count=0,
            professional_evidence_count=0,
            ready=False,
        )


class RelationEffectEvidenceRequestItem(BaseModel):
    """One exact demand and its six server-derived preparation slots."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_item_ref: str = Field(min_length=1)
    demand_packet_ref: str = Field(min_length=1)
    demand_packet_hash: str = Field(min_length=64, max_length=64)
    assessment_ref: str = Field(min_length=1)
    assessment_hash: str = Field(min_length=64, max_length=64)
    demand_ref: str = Field(min_length=1)
    dimension_slots: tuple[
        RelationEffectEvidenceRequestedSlot,
        ...,
    ] = Field(min_length=6, max_length=6)
    requested_dimension_slot_count: Literal[6]

    @model_validator(mode="after")
    def dimensions_and_identity_are_valid(
        self,
    ) -> RelationEffectEvidenceRequestItem:
        if tuple(
            item.dimension_id for item in self.dimension_slots
        ) != RELATION_EFFECT_RULE_DIMENSIONS:
            raise ValueError(
                "relation_effect_evidence_request_dimensions_invalid"
            )
        if len(
            {item.slot_ref for item in self.dimension_slots}
        ) != len(self.dimension_slots):
            raise ValueError(
                "relation_effect_evidence_request_slots_not_unique"
            )
        identity = self.model_dump(
            mode="json",
            exclude={"request_item_ref"},
        )
        if self.request_item_ref != stable_ref(
            "v60-relation-effect-evidence-request-item",
            identity,
        ):
            raise ValueError(
                "relation_effect_evidence_request_item_ref_mismatch"
            )
        return self

    @classmethod
    def issue(
        cls,
        **values: Any,
    ) -> RelationEffectEvidenceRequestItem:
        identity = {
            **values,
            "dimension_slots": tuple(
                item.model_dump(mode="json")
                if isinstance(item, BaseModel)
                else item
                for item in values["dimension_slots"]
            ),
            "requested_dimension_slot_count": 6,
        }
        return cls(
            request_item_ref=stable_ref(
                "v60-relation-effect-evidence-request-item",
                identity,
            ),
            **identity,
        )


class RelationEffectEvidenceRequestReceipt(BaseModel):
    """Append-only proof of a preparation request, never evidence itself."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    receipt_ref: str = Field(min_length=1)
    receipt_hash: str = Field(min_length=64, max_length=64)
    receipt_version: Literal[
        "v60.mingli-relation-effect-evidence-request-receipt.001"
    ] = RELATION_EFFECT_EVIDENCE_REQUEST_RECEIPT_VERSION
    request_version: Literal[
        "v60.mingli-relation-effect-evidence-request.001"
    ] = RELATION_EFFECT_EVIDENCE_REQUEST_VERSION
    requester_account_ref: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=180)
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
    packet_ref: str = Field(min_length=1)
    packet_hash: str = Field(min_length=64, max_length=64)
    request_items: tuple[RelationEffectEvidenceRequestItem, ...] = Field(
        min_length=1
    )
    request_item_count: int = Field(ge=1)
    requested_dimension_slot_count: int = Field(ge=6)
    ready_dimension_slot_count: Literal[0]
    professional_material_count: Literal[0]
    professional_evidence_count: Literal[0]
    status: Literal["REQUEST_RECORDED_NOT_EVIDENCE"]
    semantics: Literal[
        "PREPARATION_REQUEST_NOT_PROFESSIONAL_EVIDENCE"
    ]
    evidence_role: Literal["NOT_EVIDENCE"]
    effect_decision_status: Literal["WITHHELD"]
    effect_status: Literal["UNRESOLVED"]
    usability_status: Literal["UNRESOLVED"]
    llm_allowed: Literal[False]
    provider_invoked: Literal[False]
    reasoner_invoked: Literal[False]
    owner_professional_review_invoked: Literal[False]
    knowledge_admission_eligible: Literal[False]
    knowledge_write_allowed: Literal[False]
    gate_invoked: Literal[False]
    decision_request_created: Literal[False]
    decision_created: Literal[False]
    professional_verdict_allowed: Literal[False]
    probability_claim_allowed: Literal[False]
    effect_or_usability_write_allowed: Literal[False]
    private_to_requester_account: Literal[True]
    append_only: Literal[True]
    material_intake_open: Literal[False]
    file_upload_allowed: Literal[False]
    url_submission_allowed: Literal[False]
    free_text_submission_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def counts_order_boundaries_and_identity_are_valid(
        self,
    ) -> RelationEffectEvidenceRequestReceipt:
        item_refs = tuple(
            item.demand_packet_ref for item in self.request_items
        )
        if item_refs != tuple(sorted(set(item_refs))):
            raise ValueError(
                "relation_effect_evidence_request_items_not_ordered_unique"
            )
        if self.request_item_count != len(self.request_items):
            raise ValueError(
                "relation_effect_evidence_request_item_count_mismatch"
            )
        if self.requested_dimension_slot_count != (
            6 * len(self.request_items)
        ):
            raise ValueError(
                "relation_effect_evidence_request_slot_count_mismatch"
            )
        identity = self.model_dump(
            mode="json",
            exclude={"receipt_ref", "receipt_hash"},
        )
        if self.receipt_hash != content_hash(identity):
            raise ValueError(
                "relation_effect_evidence_request_receipt_hash_mismatch"
            )
        if self.receipt_ref != stable_ref(
            "v60-relation-effect-evidence-request-receipt",
            identity,
        ):
            raise ValueError(
                "relation_effect_evidence_request_receipt_ref_mismatch"
            )
        return self

    @classmethod
    def issue(
        cls,
        **values: Any,
    ) -> RelationEffectEvidenceRequestReceipt:
        request_items = tuple(
            sorted(
                values["request_items"],
                key=lambda item: item.demand_packet_ref,
            )
        )
        identity = {
            "receipt_version": (
                RELATION_EFFECT_EVIDENCE_REQUEST_RECEIPT_VERSION
            ),
            "request_version": RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
            **values,
            "request_items": tuple(
                item.model_dump(mode="json")
                for item in request_items
            ),
            "request_item_count": len(request_items),
            "requested_dimension_slot_count": (
                6 * len(request_items)
            ),
            "ready_dimension_slot_count": 0,
            "professional_material_count": 0,
            "professional_evidence_count": 0,
            "status": "REQUEST_RECORDED_NOT_EVIDENCE",
            "semantics": (
                "PREPARATION_REQUEST_NOT_PROFESSIONAL_EVIDENCE"
            ),
            "evidence_role": "NOT_EVIDENCE",
            "effect_decision_status": "WITHHELD",
            "effect_status": "UNRESOLVED",
            "usability_status": "UNRESOLVED",
            "llm_allowed": False,
            "provider_invoked": False,
            "reasoner_invoked": False,
            "owner_professional_review_invoked": False,
            "knowledge_admission_eligible": False,
            "knowledge_write_allowed": False,
            "gate_invoked": False,
            "decision_request_created": False,
            "decision_created": False,
            "professional_verdict_allowed": False,
            "probability_claim_allowed": False,
            "effect_or_usability_write_allowed": False,
            "private_to_requester_account": True,
            "append_only": True,
            "material_intake_open": False,
            "file_upload_allowed": False,
            "url_submission_allowed": False,
            "free_text_submission_allowed": False,
            "read_only": True,
        }
        return cls(
            receipt_ref=stable_ref(
                "v60-relation-effect-evidence-request-receipt",
                identity,
            ),
            receipt_hash=content_hash(identity),
            **identity,
        )
