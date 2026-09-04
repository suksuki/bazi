from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.mingli.source_usability_contracts import (
    SOURCE_USABILITY_REQUIREMENT_ORDER,
    SourceUsabilityRequirementId,
)
from abu_v60.provenance import content_hash, stable_ref

SOURCE_DISCUSSION_RECEIPT_VERSION = "v60.mingli-source-discussion-abstention-receipt.001"
SOURCE_DISCUSSION_ABSTAINED_CLAIMS = (
    "RELATION_EFFECT",
    "SOURCE_USABILITY",
)

SourceDiscussionAbstainedClaim = Literal[
    "RELATION_EFFECT",
    "SOURCE_USABILITY",
]


class MingliSourceDiscussionAbstentionReceipt(BaseModel):
    """Immutable proof that source discussion stopped at facts and gaps."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    receipt_ref: str = Field(min_length=1)
    receipt_hash: str = Field(min_length=64, max_length=64)
    receipt_version: Literal["v60.mingli-source-discussion-abstention-receipt.001"] = (
        SOURCE_DISCUSSION_RECEIPT_VERSION
    )
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    source_review_vector_ref: str = Field(min_length=1)
    source_review_vector_hash: str = Field(min_length=64, max_length=64)
    prerequisite_ref: str = Field(min_length=1)
    prerequisite_hash: str = Field(min_length=64, max_length=64)
    carrier_refs: tuple[str, ...]
    carrier_count: int = Field(ge=0)
    ready_carrier_count: Literal[0]
    blocking_requirement_ids: tuple[SourceUsabilityRequirementId, ...]
    non_triggered_requirement_ids: tuple[
        SourceUsabilityRequirementId,
        ...,
    ]
    abstained_claims: tuple[SourceDiscussionAbstainedClaim, ...] = Field(
        min_length=2,
        max_length=2,
    )
    disposition: Literal["ABSTAIN"]
    reason: Literal["NO_ADMITTED_PROFESSIONAL_RULE_CHAIN"]
    output_mode: Literal["FACTS_AND_GAPS_ONLY"]
    provider_invoked: Literal[False]
    decision_created: Literal[False]
    discussion_allowed: Literal[False]
    professional_verdict_allowed: Literal[False]
    probability_claim_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_boundaries_are_valid(
        self,
    ) -> MingliSourceDiscussionAbstentionReceipt:
        if len(self.carrier_refs) != len(set(self.carrier_refs)) or self.carrier_count != len(
            self.carrier_refs
        ):
            raise ValueError("source_discussion_carrier_binding_invalid")
        for values in (
            self.blocking_requirement_ids,
            self.non_triggered_requirement_ids,
        ):
            expected = tuple(
                requirement_id
                for requirement_id in SOURCE_USABILITY_REQUIREMENT_ORDER
                if requirement_id in set(values)
            )
            if values != expected:
                raise ValueError("source_discussion_requirement_ids_not_ordered_unique")
        requirement_ids = set(self.blocking_requirement_ids) | set(
            self.non_triggered_requirement_ids
        )
        if self.carrier_count:
            if requirement_ids != set(SOURCE_USABILITY_REQUIREMENT_ORDER):
                raise ValueError("source_discussion_requirement_coverage_incomplete")
        elif requirement_ids:
            raise ValueError("source_discussion_empty_carrier_requirements_invalid")
        if self.abstained_claims != SOURCE_DISCUSSION_ABSTAINED_CLAIMS:
            raise ValueError("source_discussion_abstained_claims_invalid")
        identity = self.model_dump(
            mode="json",
            exclude={"receipt_ref", "receipt_hash"},
        )
        if self.receipt_hash != content_hash(identity):
            raise ValueError("source_discussion_receipt_hash_mismatch")
        if self.receipt_ref != stable_ref(
            "v60-source-discussion-abstention-receipt",
            identity,
        ):
            raise ValueError("source_discussion_receipt_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        **values: Any,
    ) -> MingliSourceDiscussionAbstentionReceipt:
        identity = {
            "receipt_version": SOURCE_DISCUSSION_RECEIPT_VERSION,
            **values,
            "abstained_claims": SOURCE_DISCUSSION_ABSTAINED_CLAIMS,
            "disposition": "ABSTAIN",
            "reason": "NO_ADMITTED_PROFESSIONAL_RULE_CHAIN",
            "output_mode": "FACTS_AND_GAPS_ONLY",
            "provider_invoked": False,
            "decision_created": False,
            "discussion_allowed": False,
            "professional_verdict_allowed": False,
            "probability_claim_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            receipt_ref=stable_ref(
                "v60-source-discussion-abstention-receipt",
                identity,
            ),
            receipt_hash=content_hash(identity),
            **identity,
        )
