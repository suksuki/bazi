from __future__ import annotations

from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.mingli.reading_versions import MINGLI_READING_VERSION
from abu_v60.mingli.source_discussion_contracts import (
    MingliSourceDiscussionAbstentionReceipt,
)
from abu_v60.mingli.source_usability_contracts import (
    SOURCE_USABILITY_PREREQUISITE_VERSION,
    SOURCE_USABILITY_REQUIREMENT_ORDER,
    MingliSourceUsabilityPrerequisiteEnvelope,
    SourceUsabilityRequirementId,
)

SOURCE_REVIEW_RUNTIME_SCOPE = "SOURCE_COORDINATE_RELATION_REVIEW"
SOURCE_DISCUSSION_REQUIRED_UNRESOLVED_DIMENSIONS = frozenset(
    {"relation_effect", "usability"}
)


class MingliSourceDiscussionAbstentionProjector:
    """Stop source-effect discussion when no professional rule chain exists."""

    def project(
        self,
        *,
        reading: MingliReadingEnvelope,
        prerequisite: MingliSourceUsabilityPrerequisiteEnvelope,
    ) -> MingliSourceDiscussionAbstentionReceipt:
        reading, prerequisite = self._validated_inputs(
            reading=reading,
            prerequisite=prerequisite,
        )
        self._validate_lineage(
            reading=reading,
            prerequisite=prerequisite,
        )
        blocking_statuses: set[SourceUsabilityRequirementId] = set()
        non_triggered_statuses: set[SourceUsabilityRequirementId] = set()
        for carrier in prerequisite.carriers:
            for requirement in carrier.requirements:
                (
                    non_triggered_statuses
                    if requirement.status == "NOT_TRIGGERED"
                    else blocking_statuses
                ).add(requirement.requirement_id)

        return MingliSourceDiscussionAbstentionReceipt.issue(
            case_ref=reading.case_ref,
            chart_version_ref=reading.chart_version_ref,
            reading_ref=reading.reading_ref,
            reading_hash=reading.reading_hash,
            source_review_vector_ref=prerequisite.source_review_vector_ref,
            source_review_vector_hash=prerequisite.source_review_vector_hash,
            prerequisite_ref=prerequisite.prerequisite_ref,
            prerequisite_hash=prerequisite.prerequisite_hash,
            carrier_refs=tuple(
                carrier.carrier_ref for carrier in prerequisite.carriers
            ),
            carrier_count=prerequisite.carrier_count,
            ready_carrier_count=prerequisite.ready_carrier_count,
            blocking_requirement_ids=self._ordered_requirement_ids(
                blocking_statuses
            ),
            non_triggered_requirement_ids=self._ordered_requirement_ids(
                non_triggered_statuses
            ),
        )

    @staticmethod
    def _validated_inputs(
        *,
        reading: MingliReadingEnvelope,
        prerequisite: MingliSourceUsabilityPrerequisiteEnvelope,
    ) -> tuple[
        MingliReadingEnvelope,
        MingliSourceUsabilityPrerequisiteEnvelope,
    ]:
        if prerequisite.ready_carrier_count != 0 or any(
            carrier.discussion_ready for carrier in prerequisite.carriers
        ):
            raise ValueError(
                "source_discussion_ready_carrier_not_supported_by_v001"
            )
        validated_reading = MingliReadingEnvelope.model_validate(
            reading.model_dump(mode="python")
        )
        validated_prerequisite = (
            MingliSourceUsabilityPrerequisiteEnvelope.model_validate(
                prerequisite.model_dump(mode="python")
            )
        )
        if validated_reading.reading_version != MINGLI_READING_VERSION:
            raise ValueError("source_discussion_reading_version_not_supported")
        if (
            validated_prerequisite.prerequisite_version
            != SOURCE_USABILITY_PREREQUISITE_VERSION
        ):
            raise ValueError(
                "source_discussion_prerequisite_version_not_supported"
            )
        source_review_profile = validated_reading.source_review_profile
        if source_review_profile is None:
            raise ValueError("source_discussion_source_review_profile_missing")
        if (
            source_review_profile.runtime_scope
            != SOURCE_REVIEW_RUNTIME_SCOPE
        ):
            raise ValueError(
                "source_discussion_source_review_runtime_scope_mismatch"
            )
        if source_review_profile.professionally_reviewed:
            raise ValueError(
                "source_discussion_professionally_reviewed_profile_not_supported"
            )
        if not SOURCE_DISCUSSION_REQUIRED_UNRESOLVED_DIMENSIONS <= set(
            validated_reading.unresolved_dimensions
        ):
            raise ValueError(
                "source_discussion_reading_unresolved_dimensions_missing"
            )
        return validated_reading, validated_prerequisite

    @staticmethod
    def _validate_lineage(
        *,
        reading: MingliReadingEnvelope,
        prerequisite: MingliSourceUsabilityPrerequisiteEnvelope,
    ) -> None:
        if (
            prerequisite.case_ref != reading.case_ref
            or prerequisite.chart_version_ref != reading.chart_version_ref
        ):
            raise ValueError("source_discussion_case_chart_lineage_mismatch")
        if (
            reading.quant_vector_ref is None
            or reading.quant_vector_hash is None
            or prerequisite.quant_vector_ref != reading.quant_vector_ref
            or prerequisite.quant_vector_hash != reading.quant_vector_hash
        ):
            raise ValueError("source_discussion_quant_vector_lineage_mismatch")
        if (
            reading.source_review_vector_ref is None
            or reading.source_review_vector_hash is None
            or prerequisite.source_review_vector_ref
            != reading.source_review_vector_ref
            or prerequisite.source_review_vector_hash
            != reading.source_review_vector_hash
        ):
            raise ValueError(
                "source_discussion_source_review_vector_lineage_mismatch"
            )

    @staticmethod
    def _ordered_requirement_ids(
        requirement_ids: set[SourceUsabilityRequirementId],
    ) -> tuple[SourceUsabilityRequirementId, ...]:
        return tuple(
            requirement_id
            for requirement_id in SOURCE_USABILITY_REQUIREMENT_ORDER
            if requirement_id in requirement_ids
        )
