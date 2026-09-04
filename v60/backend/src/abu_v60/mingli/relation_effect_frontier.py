from __future__ import annotations

from collections.abc import Iterable

from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.mingli.reading_versions import MINGLI_READING_VERSION
from abu_v60.mingli.relation_effect_frontier_contracts import (
    MingliRelationEffectResearchFrontierEnvelope,
    RelationEffectRuleDemand,
)
from abu_v60.mingli.source_discussion_contracts import (
    SOURCE_DISCUSSION_RECEIPT_VERSION,
    MingliSourceDiscussionAbstentionReceipt,
)
from abu_v60.mingli.source_review_contracts import (
    SOURCE_REVIEW_VECTOR_VERSION,
    MingliSourceCoordinateReviewVector,
    SourceCoordinateReviewEvidence,
)
from abu_v60.mingli.source_usability_contracts import (
    SOURCE_USABILITY_PREREQUISITE_VERSION,
    MingliSourceUsabilityPrerequisiteEnvelope,
    SourceCarrierUsabilityPrerequisite,
)

SOURCE_REVIEW_RUNTIME_SCOPE = "SOURCE_COORDINATE_RELATION_REVIEW"
REQUIRED_READING_UNRESOLVED_DIMENSIONS = frozenset({"relation_effect", "usability"})


class MingliRelationEffectResearchFrontierProjector:
    """Classify relation-rule research dependencies without inferring effect."""

    def project(
        self,
        *,
        reading: MingliReadingEnvelope,
        source_review_vector: MingliSourceCoordinateReviewVector,
        prerequisite: MingliSourceUsabilityPrerequisiteEnvelope,
        refusal: MingliSourceDiscussionAbstentionReceipt,
    ) -> MingliRelationEffectResearchFrontierEnvelope:
        reading, source_review_vector, prerequisite, refusal = self._validated_inputs(
            reading=reading,
            source_review_vector=source_review_vector,
            prerequisite=prerequisite,
            refusal=refusal,
        )
        self._validate_lineage(
            reading=reading,
            source_review_vector=source_review_vector,
            prerequisite=prerequisite,
            refusal=refusal,
        )
        carriers_by_review = self._validate_scope_bindings(
            source_review_vector=source_review_vector,
            prerequisite=prerequisite,
        )
        demands = tuple(
            sorted(
                self._demands(
                    source_review_vector=source_review_vector,
                    carriers_by_review=carriers_by_review,
                ),
                key=lambda item: (
                    ("year", "month", "day", "hour").index(item.visible_slot),
                    item.visible_stem,
                    ("year", "month", "day", "hour").index(item.source_slot),
                    item.source_branch,
                    ("year", "month", "day", "hour").index(item.peer_slot),
                    item.peer_branch,
                    item.relation_type,
                    item.intersection_ref,
                ),
            )
        )
        return MingliRelationEffectResearchFrontierEnvelope.issue(
            case_ref=reading.case_ref,
            chart_version_ref=reading.chart_version_ref,
            reading_ref=reading.reading_ref,
            reading_hash=reading.reading_hash,
            source_review_vector_ref=source_review_vector.vector_ref,
            source_review_vector_hash=source_review_vector.vector_hash,
            prerequisite_ref=prerequisite.prerequisite_ref,
            prerequisite_hash=prerequisite.prerequisite_hash,
            refusal_receipt_ref=refusal.receipt_ref,
            refusal_receipt_hash=refusal.receipt_hash,
            demands=demands,
            demand_count=len(demands),
            scope_invariant_rule_demand_count=sum(
                item.dependency_status == "SCOPE_INVARIANT_RULE_DEMAND" for item in demands
            ),
            match_scope_rule_first_count=sum(
                item.dependency_status == "MATCH_SCOPE_RULE_FIRST" for item in demands
            ),
            admitted_effect_rule_count=0,
        )

    @staticmethod
    def _validated_inputs(
        *,
        reading: MingliReadingEnvelope,
        source_review_vector: MingliSourceCoordinateReviewVector,
        prerequisite: MingliSourceUsabilityPrerequisiteEnvelope,
        refusal: MingliSourceDiscussionAbstentionReceipt,
    ) -> tuple[
        MingliReadingEnvelope,
        MingliSourceCoordinateReviewVector,
        MingliSourceUsabilityPrerequisiteEnvelope,
        MingliSourceDiscussionAbstentionReceipt,
    ]:
        validated = (
            MingliReadingEnvelope.model_validate(reading.model_dump(mode="python")),
            MingliSourceCoordinateReviewVector.model_validate(
                source_review_vector.model_dump(mode="python")
            ),
            MingliSourceUsabilityPrerequisiteEnvelope.model_validate(
                prerequisite.model_dump(mode="python")
            ),
            MingliSourceDiscussionAbstentionReceipt.model_validate(
                refusal.model_dump(mode="python")
            ),
        )
        current_reading, current_review, current_prerequisite, current_refusal = validated
        if current_reading.reading_version != MINGLI_READING_VERSION:
            raise ValueError("relation_effect_frontier_reading_version_not_supported")
        if current_review.vector_version != SOURCE_REVIEW_VECTOR_VERSION:
            raise ValueError("relation_effect_frontier_source_review_version_not_supported")
        if current_prerequisite.prerequisite_version != SOURCE_USABILITY_PREREQUISITE_VERSION:
            raise ValueError("relation_effect_frontier_prerequisite_version_not_supported")
        if current_refusal.receipt_version != SOURCE_DISCUSSION_RECEIPT_VERSION:
            raise ValueError("relation_effect_frontier_refusal_version_not_supported")
        source_review_profile = current_reading.source_review_profile
        if source_review_profile is None:
            raise ValueError("relation_effect_frontier_source_review_profile_missing")
        if source_review_profile.runtime_scope != SOURCE_REVIEW_RUNTIME_SCOPE:
            raise ValueError("relation_effect_frontier_source_review_runtime_scope_mismatch")
        if source_review_profile.professionally_reviewed:
            raise ValueError(
                "relation_effect_frontier_professionally_reviewed_profile_not_supported"
            )
        if not REQUIRED_READING_UNRESOLVED_DIMENSIONS <= set(current_reading.unresolved_dimensions):
            raise ValueError("relation_effect_frontier_reading_unresolved_dimensions_missing")
        if (
            current_refusal.disposition != "ABSTAIN"
            or current_refusal.discussion_allowed
            or current_refusal.provider_invoked
            or current_refusal.decision_created
        ):
            raise ValueError("relation_effect_frontier_refusal_boundary_invalid")
        return validated

    @staticmethod
    def _validate_lineage(
        *,
        reading: MingliReadingEnvelope,
        source_review_vector: MingliSourceCoordinateReviewVector,
        prerequisite: MingliSourceUsabilityPrerequisiteEnvelope,
        refusal: MingliSourceDiscussionAbstentionReceipt,
    ) -> None:
        case_chart_pairs = {
            (reading.case_ref, reading.chart_version_ref),
            (
                source_review_vector.case_ref,
                source_review_vector.chart_version_ref,
            ),
            (prerequisite.case_ref, prerequisite.chart_version_ref),
            (refusal.case_ref, refusal.chart_version_ref),
        }
        if len(case_chart_pairs) != 1:
            raise ValueError("relation_effect_frontier_case_chart_lineage_mismatch")
        if (
            reading.source_review_vector_ref != source_review_vector.vector_ref
            or reading.source_review_vector_hash != source_review_vector.vector_hash
            or prerequisite.source_review_vector_ref != source_review_vector.vector_ref
            or prerequisite.source_review_vector_hash != source_review_vector.vector_hash
            or refusal.source_review_vector_ref != source_review_vector.vector_ref
            or refusal.source_review_vector_hash != source_review_vector.vector_hash
        ):
            raise ValueError("relation_effect_frontier_source_review_lineage_mismatch")
        if (
            prerequisite.quant_vector_ref != source_review_vector.quant_vector_ref
            or prerequisite.quant_vector_hash != source_review_vector.quant_vector_hash
            or reading.quant_vector_ref != source_review_vector.quant_vector_ref
            or reading.quant_vector_hash != source_review_vector.quant_vector_hash
        ):
            raise ValueError("relation_effect_frontier_quant_lineage_mismatch")
        if (
            refusal.reading_ref != reading.reading_ref
            or refusal.reading_hash != reading.reading_hash
        ):
            raise ValueError("relation_effect_frontier_reading_lineage_mismatch")
        if (
            refusal.prerequisite_ref != prerequisite.prerequisite_ref
            or refusal.prerequisite_hash != prerequisite.prerequisite_hash
        ):
            raise ValueError("relation_effect_frontier_prerequisite_lineage_mismatch")
        carrier_refs = tuple(item.carrier_ref for item in prerequisite.carriers)
        if (
            refusal.carrier_refs != carrier_refs
            or refusal.carrier_count != prerequisite.carrier_count
            or refusal.ready_carrier_count != prerequisite.ready_carrier_count
        ):
            raise ValueError("relation_effect_frontier_carrier_lineage_mismatch")

    @classmethod
    def _validate_scope_bindings(
        cls,
        *,
        source_review_vector: MingliSourceCoordinateReviewVector,
        prerequisite: MingliSourceUsabilityPrerequisiteEnvelope,
    ) -> dict[str, SourceCarrierUsabilityPrerequisite]:
        reviews = {item.review_ref: item for item in source_review_vector.reviews}
        if len(reviews) != len(source_review_vector.reviews):
            raise ValueError("relation_effect_frontier_review_identity_not_unique")
        carriers_by_review: dict[str, SourceCarrierUsabilityPrerequisite] = {}
        for carrier in prerequisite.carriers:
            strict, inclusive = carrier.scopes
            expected_inclusive_intersections: list[str] = []
            expected_strict_intersections: list[str] = []
            for review_ref in inclusive.source_review_refs:
                review = reviews.get(review_ref)
                if review is None or review_ref in carriers_by_review:
                    raise ValueError("relation_effect_frontier_review_carrier_bijection_invalid")
                cls._validate_review_carrier(review=review, carrier=carrier)
                carriers_by_review[review_ref] = carrier
                intersections = [item.intersection_ref for item in review.relation_intersections]
                expected_inclusive_intersections.extend(intersections)
                if review_ref in strict.source_review_refs:
                    if review.source_match_kind != "EXACT_IDENTITY":
                        raise ValueError("relation_effect_frontier_strict_scope_match_invalid")
                    expected_strict_intersections.extend(intersections)
                elif review.source_match_kind != "SAME_ELEMENT_DIFFERENT_IDENTITY":
                    raise ValueError("relation_effect_frontier_inclusive_scope_match_invalid")
            if strict.intersection_refs != tuple(
                sorted(expected_strict_intersections)
            ) or inclusive.intersection_refs != tuple(sorted(expected_inclusive_intersections)):
                raise ValueError("relation_effect_frontier_scope_intersection_mismatch")
        if set(carriers_by_review) != set(reviews):
            raise ValueError("relation_effect_frontier_review_carrier_bijection_invalid")
        return carriers_by_review

    @staticmethod
    def _validate_review_carrier(
        *,
        review: SourceCoordinateReviewEvidence,
        carrier: SourceCarrierUsabilityPrerequisite,
    ) -> None:
        if (
            review.visible_slot != carrier.visible_slot
            or review.visible_stem != carrier.visible_stem
        ):
            raise ValueError("relation_effect_frontier_review_carrier_coordinate_mismatch")

    @staticmethod
    def _demands(
        *,
        source_review_vector: MingliSourceCoordinateReviewVector,
        carriers_by_review: dict[
            str,
            SourceCarrierUsabilityPrerequisite,
        ],
    ) -> Iterable[RelationEffectRuleDemand]:
        for review in source_review_vector.reviews:
            carrier = carriers_by_review[review.review_ref]
            strict_reviews = set(carrier.scopes[0].source_review_refs)
            dependency_status = (
                "SCOPE_INVARIANT_RULE_DEMAND"
                if review.review_ref in strict_reviews
                else "MATCH_SCOPE_RULE_FIRST"
            )
            scope_presence = (
                ("EXACT_IDENTITY_ONLY", "ELEMENT_AFFINITY_INCLUDED")
                if dependency_status == "SCOPE_INVARIANT_RULE_DEMAND"
                else ("ELEMENT_AFFINITY_INCLUDED",)
            )
            for intersection in review.relation_intersections:
                yield RelationEffectRuleDemand.issue(
                    carrier_ref=carrier.carrier_ref,
                    visible_slot=review.visible_slot,
                    visible_stem=review.visible_stem,
                    source_review_ref=review.review_ref,
                    source_evidence_ref=review.source_evidence_ref,
                    intersection_ref=intersection.intersection_ref,
                    relation_fact_ref=intersection.relation_fact_ref,
                    relation_type=intersection.relation_type,
                    source_match_kind=review.source_match_kind,
                    source_slot=intersection.source_slot,
                    source_branch=intersection.source_branch,
                    peer_slot=intersection.peer_slot,
                    peer_branch=intersection.peer_branch,
                    scope_presence=scope_presence,
                    dependency_status=dependency_status,
                )
