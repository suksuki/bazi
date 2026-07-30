from __future__ import annotations

from datetime import date, time

import pytest
from abu_v60.mingli import (
    SOURCE_DISCUSSION_ABSTAINED_CLAIMS,
    SOURCE_DISCUSSION_RECEIPT_VERSION,
    MingliLifeDomainEvidenceCompiler,
    MingliMechanismEvidenceCompiler,
    MingliQuantFoundationCompiler,
    MingliReadingEnvelope,
    MingliReadingProjector,
    MingliSourceCoordinateReviewCompiler,
    MingliSourceDiscussionAbstentionProjector,
    MingliSourceDiscussionAbstentionReceipt,
    MingliSourceUsabilityPrerequisiteEnvelope,
    MingliSourceUsabilityPrerequisiteProjector,
    MingliTimingEvidenceCompiler,
    StructuralCandidateCompiler,
)
from abu_v60.mingli.calendar import BirthInput, ChartPillars
from abu_v60.mingli.compiler import compile_case
from abu_v60.provenance import canonical_json

ANALYSIS_DATE = date(2026, 7, 29)


def _inputs(
    *,
    pillars: ChartPillars | None = None,
) -> tuple[
    MingliReadingEnvelope,
    MingliSourceUsabilityPrerequisiteEnvelope,
]:
    case_ref = "case-source-discussion"
    life_case_revision_ref = f"{case_ref}-life-v1"
    birth_input = BirthInput(
        calendar_type="solar",
        birth_date=date(2000, 1, 1),
        birth_time=time(12, 0),
        timezone="Asia/Shanghai",
    )
    compiled = compile_case(
        case_ref=case_ref,
        birth_input=birth_input,
        chart=(
            pillars
            or ChartPillars(
                year="己巳",
                month="丙子",
                day="丙寅",
                hour="甲午",
            )
        ),
    )
    quant = MingliQuantFoundationCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=compiled.facts,
    )
    mechanism = MingliMechanismEvidenceCompiler().compile(
        quant_vector=quant,
        facts=compiled.facts,
    )
    source_review = MingliSourceCoordinateReviewCompiler().compile(
        quant_vector=quant,
        facts=compiled.facts,
    )
    prerequisite = MingliSourceUsabilityPrerequisiteProjector().project(
        quant_vector=quant,
        source_review_vector=source_review,
    )
    timing = MingliTimingEvidenceCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref=life_case_revision_ref,
        birth_input=birth_input,
        gender="male",
        pillars=compiled.pillars,
        facts=compiled.facts,
        analysis_date=ANALYSIS_DATE,
        mechanism_vector=mechanism,
    )
    domains = MingliLifeDomainEvidenceCompiler().compile(
        mechanism_vector=mechanism,
        timing_vector=timing,
    )
    reading = MingliReadingProjector().project(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref=life_case_revision_ref,
        facts=compiled.facts,
        candidates=StructuralCandidateCompiler().compile(
            chart_version_ref=compiled.chart_version_ref,
            facts=compiled.facts,
        ),
        quant_vector=quant,
        source_review_vector=source_review,
        mechanism_vector=mechanism,
        timing_vector=timing,
        life_domain_vector=domains,
    )
    return reading, prerequisite


def _reissue_reading(
    reading: MingliReadingEnvelope,
    **updates: object,
) -> MingliReadingEnvelope:
    values = reading.model_dump(
        mode="python",
        exclude={"reading_ref", "reading_hash", "reading_version"},
    )
    values.update(updates)
    return MingliReadingEnvelope.issue(
        reading_version=reading.reading_version,
        **values,
    )


def _reissue_prerequisite(
    prerequisite: MingliSourceUsabilityPrerequisiteEnvelope,
    **updates: object,
) -> MingliSourceUsabilityPrerequisiteEnvelope:
    values = prerequisite.model_dump(
        mode="python",
        exclude={"prerequisite_ref", "prerequisite_hash"},
    )
    values.update(updates)
    return MingliSourceUsabilityPrerequisiteEnvelope.issue(
        **values,
    )


def test_source_discussion_receipt_is_stable_and_binds_complete_lineage() -> None:
    reading, prerequisite = _inputs()
    projector = MingliSourceDiscussionAbstentionProjector()

    first = projector.project(
        reading=reading,
        prerequisite=prerequisite,
    )
    second = projector.project(
        reading=reading,
        prerequisite=prerequisite,
    )

    assert first == second
    assert first.receipt_version == SOURCE_DISCUSSION_RECEIPT_VERSION
    assert first.case_ref == reading.case_ref
    assert first.chart_version_ref == reading.chart_version_ref
    assert (first.reading_ref, first.reading_hash) == (
        reading.reading_ref,
        reading.reading_hash,
    )
    assert (
        first.source_review_vector_ref,
        first.source_review_vector_hash,
    ) == (
        prerequisite.source_review_vector_ref,
        prerequisite.source_review_vector_hash,
    )
    assert (first.prerequisite_ref, first.prerequisite_hash) == (
        prerequisite.prerequisite_ref,
        prerequisite.prerequisite_hash,
    )
    assert first.carrier_refs == tuple(
        item.carrier_ref for item in prerequisite.carriers
    )
    assert first.carrier_count == prerequisite.carrier_count
    assert first.ready_carrier_count == 0
    assert first.abstained_claims == SOURCE_DISCUSSION_ABSTAINED_CLAIMS


def test_source_discussion_derives_blocking_and_non_triggered_requirement_ids() -> None:
    reading, prerequisite = _inputs()

    receipt = MingliSourceDiscussionAbstentionProjector().project(
        reading=reading,
        prerequisite=prerequisite,
    )

    assert receipt.blocking_requirement_ids == (
        "MATCH_SCOPE_RULE",
        "RELATION_EFFECT_RULE",
        "SEASONAL_CAPACITY_RULE",
        "MULTI_SOURCE_AGGREGATION_RULE",
        "ROOT_USABILITY_RULE",
        "PROFESSIONAL_ADMISSION",
    )
    assert receipt.non_triggered_requirement_ids == (
        "RELATION_EFFECT_RULE",
        "MULTI_SOURCE_AGGREGATION_RULE",
    )
    assert receipt.disposition == "ABSTAIN"
    assert receipt.reason == "NO_ADMITTED_PROFESSIONAL_RULE_CHAIN"
    assert receipt.output_mode == "FACTS_AND_GAPS_ONLY"


def test_source_discussion_keeps_clear_relation_coordinates_abstained() -> None:
    reading, prerequisite = _inputs(
        pillars=ChartPillars(
            year="丁巳",
            month="乙巳",
            day="乙丑",
            hour="乙酉",
        )
    )

    receipt = MingliSourceDiscussionAbstentionProjector().project(
        reading=reading,
        prerequisite=prerequisite,
    )

    assert prerequisite.element_affinity_included_review_required_count == 0
    assert "RELATION_EFFECT_RULE" not in receipt.blocking_requirement_ids
    assert "RELATION_EFFECT_RULE" in receipt.non_triggered_requirement_ids
    assert receipt.disposition == "ABSTAIN"
    assert receipt.discussion_allowed is False


def test_source_discussion_fails_closed_on_lineage_profile_and_state_drift() -> None:
    reading, prerequisite = _inputs()
    projector = MingliSourceDiscussionAbstentionProjector()

    with pytest.raises(
        ValueError,
        match="source_discussion_case_chart_lineage_mismatch",
    ):
        projector.project(
            reading=reading,
            prerequisite=_reissue_prerequisite(
                prerequisite,
                case_ref="different-case",
            ),
        )

    with pytest.raises(
        ValueError,
        match="source_discussion_source_review_vector_lineage_mismatch",
    ):
        projector.project(
            reading=reading,
            prerequisite=_reissue_prerequisite(
                prerequisite,
                source_review_vector_ref="different-source-review-vector",
            ),
        )

    with pytest.raises(
        ValueError,
        match="source_discussion_prerequisite_version_not_supported",
    ):
        projector.project(
            reading=reading,
            prerequisite=_reissue_prerequisite(
                prerequisite,
                prerequisite_version=(
                    "v60.mingli-source-usability-prerequisite.999"
                ),
            ),
        )

    assert reading.source_review_profile is not None
    wrong_scope_profile = reading.source_review_profile.model_copy(
        update={"runtime_scope": "PROFESSIONAL_SOURCE_DISCUSSION"}
    )
    with pytest.raises(
        ValueError,
        match="source_discussion_source_review_runtime_scope_mismatch",
    ):
        projector.project(
            reading=_reissue_reading(
                reading,
                source_review_profile=wrong_scope_profile,
            ),
            prerequisite=prerequisite,
        )

    with pytest.raises(
        ValueError,
        match="source_discussion_reading_unresolved_dimensions_missing",
    ):
        projector.project(
            reading=_reissue_reading(
                reading,
                unresolved_dimensions=tuple(
                    item
                    for item in reading.unresolved_dimensions
                    if item != "usability"
                ),
            ),
            prerequisite=prerequisite,
        )

    with pytest.raises(
        ValueError,
        match="source_discussion_ready_carrier_not_supported_by_v001",
    ):
        projector.project(
            reading=reading,
            prerequisite=prerequisite.model_copy(
                update={"ready_carrier_count": 1}
            ),
        )


def test_source_discussion_never_creates_decision_or_professional_claim() -> None:
    reading, prerequisite = _inputs()

    receipt = MingliSourceDiscussionAbstentionProjector().project(
        reading=reading,
        prerequisite=prerequisite,
    )
    serialized = canonical_json(receipt.model_dump(mode="json"))

    assert receipt.provider_invoked is False
    assert receipt.decision_created is False
    assert receipt.discussion_allowed is False
    assert receipt.professional_verdict_allowed is False
    assert receipt.probability_claim_allowed is False
    assert receipt.canonical_write_allowed is False
    assert receipt.read_only is True
    assert "empirical_probability" not in serialized
    assert "EFFECTIVE_WORK" not in serialized

    with pytest.raises(
        ValueError,
        match="source_discussion_receipt_hash_mismatch",
    ):
        MingliSourceDiscussionAbstentionReceipt.model_validate(
            receipt.model_copy(
                update={"reading_hash": "f" * 64}
            ).model_dump(mode="python")
        )
