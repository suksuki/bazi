from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from abu_v60.provenance import content_hash, stable_ref

RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION = (
    "v60.mingli-relation-effect-evidence-material-request.001"
)
RELATION_EFFECT_EVIDENCE_MATERIAL_VERSION = (
    "v60.mingli-relation-effect-evidence-material.001"
)


class RelationEffectEvidenceBibliographyMetadata(BaseModel):
    """Unverified bibliography coordinates without source or quotation content."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(min_length=1, max_length=240)
    responsible_party: str = Field(min_length=1, max_length=180)
    edition_or_publication_identity: str = Field(
        min_length=1,
        max_length=180,
    )
    locator: str = Field(min_length=1, max_length=180)

    @field_validator(
        "title",
        "responsible_party",
        "edition_or_publication_identity",
        "locator",
    )
    @classmethod
    def metadata_is_bounded_and_not_a_url(cls, value: str) -> str:
        if value != value.strip() or any(
            ord(character) < 32 or ord(character) == 127
            for character in value
        ):
            raise ValueError(
                "relation_effect_evidence_material_metadata_not_canonical"
            )
        lowered = value.casefold()
        if (
            "://" in lowered
            or lowered.startswith(
                ("http:", "https:", "ftp:", "file:", "data:", "www.")
            )
        ):
            raise ValueError(
                "relation_effect_evidence_material_url_not_allowed"
            )
        return value


class RelationEffectEvidenceMaterialRequest(BaseModel):
    """Replay-safe registration of one bibliography-only candidate material."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    material_request_version: Literal[
        "v60.mingli-relation-effect-evidence-material-request.001"
    ]
    expected_receipt_ref: str = Field(min_length=1)
    expected_receipt_hash: str = Field(min_length=64, max_length=64)
    expected_packet_ref: str = Field(min_length=1)
    expected_packet_hash: str = Field(min_length=64, max_length=64)
    expected_request_item_ref: str = Field(min_length=1)
    expected_demand_packet_ref: str = Field(min_length=1)
    expected_demand_packet_hash: str = Field(
        min_length=64,
        max_length=64,
    )
    expected_slot_ref: str = Field(min_length=1)
    candidate_kind: Literal["BIBLIOGRAPHIC_COORDINATE_CANDIDATE"]
    target_artifact_kind: Literal["PROFESSIONAL_SOURCE_MANIFEST"]
    bibliography: RelationEffectEvidenceBibliographyMetadata
    idempotency_key: str = Field(min_length=1, max_length=180)


class RelationEffectEvidenceMaterialRecord(BaseModel):
    """Append-only candidate material that grants no professional evidence credit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    material_ref: str = Field(min_length=1)
    material_hash: str = Field(min_length=64, max_length=64)
    material_version: Literal[
        "v60.mingli-relation-effect-evidence-material.001"
    ] = RELATION_EFFECT_EVIDENCE_MATERIAL_VERSION
    material_request_version: Literal[
        "v60.mingli-relation-effect-evidence-material-request.001"
    ] = RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION
    requester_account_ref: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=180)
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    request_receipt_ref: str = Field(min_length=1)
    request_receipt_hash: str = Field(min_length=64, max_length=64)
    packet_ref: str = Field(min_length=1)
    packet_hash: str = Field(min_length=64, max_length=64)
    request_item_ref: str = Field(min_length=1)
    demand_packet_ref: str = Field(min_length=1)
    demand_packet_hash: str = Field(min_length=64, max_length=64)
    slot_ref: str = Field(min_length=1)
    dimension_id: Literal["PROFESSIONAL_PROVENANCE"]
    candidate_kind: Literal["BIBLIOGRAPHIC_COORDINATE_CANDIDATE"]
    target_artifact_kind: Literal["PROFESSIONAL_SOURCE_MANIFEST"]
    bibliography: RelationEffectEvidenceBibliographyMetadata
    bibliography_hash: str = Field(min_length=64, max_length=64)
    status: Literal[
        "CANDIDATE_METADATA_RECORDED_NOT_REQUESTED_ARTIFACT"
    ]
    semantics: Literal["UNVERIFIED_BIBLIOGRAPHY_METADATA_ONLY"]
    evidence_role: Literal["NOT_EVIDENCE"]
    requested_artifact_satisfied: Literal[False]
    candidate_material_count: Literal[1]
    professional_material_count: Literal[0]
    professional_evidence_count: Literal[0]
    ready_dimension_slot_count: Literal[0]
    effect_decision_status: Literal["WITHHELD"]
    effect_status: Literal["UNRESOLVED"]
    usability_status: Literal["UNRESOLVED"]
    material_truth_verified: Literal[False]
    source_authenticity_verified: Literal[False]
    artifact_content_present: Literal[False]
    citation_body_present: Literal[False]
    structured_bibliography_metadata_only: Literal[True]
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
    structured_bibliography_metadata_allowed: Literal[True]
    file_upload_allowed: Literal[False]
    url_submission_allowed: Literal[False]
    quotation_body_submission_allowed: Literal[False]
    conclusion_submission_allowed: Literal[False]
    unstructured_notes_submission_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def boundary_and_identity_are_valid(
        self,
    ) -> RelationEffectEvidenceMaterialRecord:
        if self.bibliography_hash != content_hash(
            self.bibliography.model_dump(mode="json")
        ):
            raise ValueError(
                "relation_effect_evidence_material_bibliography_hash_mismatch"
            )
        identity = self.model_dump(
            mode="json",
            exclude={"material_ref", "material_hash"},
        )
        if self.material_hash != content_hash(identity):
            raise ValueError(
                "relation_effect_evidence_material_hash_mismatch"
            )
        if self.material_ref != stable_ref(
            "v60-relation-effect-evidence-material",
            identity,
        ):
            raise ValueError(
                "relation_effect_evidence_material_ref_mismatch"
            )
        return self

    @classmethod
    def issue(
        cls,
        **values: Any,
    ) -> RelationEffectEvidenceMaterialRecord:
        bibliography = RelationEffectEvidenceBibliographyMetadata.model_validate(
            values["bibliography"]
        )
        identity = {
            "material_version": RELATION_EFFECT_EVIDENCE_MATERIAL_VERSION,
            "material_request_version": (
                RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION
            ),
            **values,
            "bibliography": (
                bibliography.model_dump(mode="json")
                if isinstance(bibliography, BaseModel)
                else bibliography
            ),
            "bibliography_hash": content_hash(
                bibliography.model_dump(mode="json")
            ),
            "status": (
                "CANDIDATE_METADATA_RECORDED_NOT_REQUESTED_ARTIFACT"
            ),
            "semantics": "UNVERIFIED_BIBLIOGRAPHY_METADATA_ONLY",
            "evidence_role": "NOT_EVIDENCE",
            "requested_artifact_satisfied": False,
            "candidate_material_count": 1,
            "professional_material_count": 0,
            "professional_evidence_count": 0,
            "ready_dimension_slot_count": 0,
            "effect_decision_status": "WITHHELD",
            "effect_status": "UNRESOLVED",
            "usability_status": "UNRESOLVED",
            "material_truth_verified": False,
            "source_authenticity_verified": False,
            "artifact_content_present": False,
            "citation_body_present": False,
            "structured_bibliography_metadata_only": True,
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
            "structured_bibliography_metadata_allowed": True,
            "file_upload_allowed": False,
            "url_submission_allowed": False,
            "quotation_body_submission_allowed": False,
            "conclusion_submission_allowed": False,
            "unstructured_notes_submission_allowed": False,
            "read_only": True,
        }
        return cls(
            material_ref=stable_ref(
                "v60-relation-effect-evidence-material",
                identity,
            ),
            material_hash=content_hash(identity),
            **identity,
        )
