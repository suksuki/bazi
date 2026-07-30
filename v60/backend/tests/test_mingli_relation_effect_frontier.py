from __future__ import annotations

from datetime import date, time

import pytest
from abu_v60.mingli import (
    RELATION_EFFECT_REQUIRED_RULE_DIMENSIONS,
    RELATION_EFFECT_RESEARCH_FRONTIER_VERSION,
    MingliLifeDomainEvidenceCompiler,
    MingliMechanismEvidenceCompiler,
    MingliQuantFoundationCompiler,
    MingliReadingProjector,
    MingliRelationEffectResearchFrontierEnvelope,
    MingliRelationEffectResearchFrontierProjector,
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


def _bundle(
    pillars: ChartPillars,
    *,
    reverse_facts: bool = False,
) -> dict[str, object]:
    case_ref = f"case-relation-frontier-{pillars.year}-{pillars.month}"
    birth_input = BirthInput(
        calendar_type="solar",
        birth_date=date(2000, 1, 1),
        birth_time=time(12, 0),
        timezone="Asia/Shanghai",
    )
    compiled = compile_case(
        case_ref=case_ref,
        birth_input=birth_input,
        chart=pillars,
    )
    facts = (
        tuple(reversed(compiled.facts))
        if reverse_facts
        else compiled.facts
    )
    quant = MingliQuantFoundationCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=facts,
    )
    source_review = MingliSourceCoordinateReviewCompiler().compile(
        quant_vector=quant,
        facts=facts,
    )
    prerequisite = MingliSourceUsabilityPrerequisiteProjector().project(
        quant_vector=quant,
        source_review_vector=source_review,
    )
    mechanism = MingliMechanismEvidenceCompiler().compile(
        quant_vector=quant,
        facts=facts,
    )
    timing = MingliTimingEvidenceCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref=f"{case_ref}-life-v1",
        birth_input=birth_input,
        gender="male",
        pillars=compiled.pillars,
        facts=facts,
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
        life_case_revision_ref=f"{case_ref}-life-v1",
        facts=facts,
        candidates=StructuralCandidateCompiler().compile(
            chart_version_ref=compiled.chart_version_ref,
            facts=facts,
        ),
        quant_vector=quant,
        source_review_vector=source_review,
        mechanism_vector=mechanism,
        timing_vector=timing,
        life_domain_vector=domains,
    )
    refusal = MingliSourceDiscussionAbstentionProjector().project(
        reading=reading,
        prerequisite=prerequisite,
    )
    return {
        "reading": reading,
        "source_review": source_review,
        "prerequisite": prerequisite,
        "refusal": refusal,
    }


def _frontier(bundle: dict[str, object]):
    return MingliRelationEffectResearchFrontierProjector().project(
        reading=bundle["reading"],
        source_review_vector=bundle["source_review"],
        prerequisite=bundle["prerequisite"],
        refusal=bundle["refusal"],
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
    return MingliSourceUsabilityPrerequisiteEnvelope.issue(**values)


def _reissue_refusal(
    refusal: MingliSourceDiscussionAbstentionReceipt,
    **updates: object,
) -> MingliSourceDiscussionAbstentionReceipt:
    values = refusal.model_dump(
        mode="python",
        exclude={
            "receipt_ref",
            "receipt_hash",
            "receipt_version",
            "abstained_claims",
            "disposition",
            "reason",
            "output_mode",
            "provider_invoked",
            "decision_created",
            "discussion_allowed",
            "professional_verdict_allowed",
            "probability_claim_allowed",
            "canonical_write_allowed",
            "read_only",
        },
    )
    values.update(updates)
    return MingliSourceDiscussionAbstentionReceipt.issue(**values)


def test_relation_effect_frontier_classifies_real_10_7_3_review_shape() -> None:
    pillars = ChartPillars(
        year="己巳",
        month="丙子",
        day="丙寅",
        hour="甲午",
    )
    first_bundle = _bundle(pillars)
    reversed_bundle = _bundle(pillars, reverse_facts=True)

    first = _frontier(first_bundle)
    second = _frontier(reversed_bundle)
    source_review = first_bundle["source_review"]

    assert first == second
    assert first.frontier_version == RELATION_EFFECT_RESEARCH_FRONTIER_VERSION
    assert source_review.source_evidence_count == 10
    assert source_review.clear_coordinate_count == 7
    assert source_review.review_required_count == 3
    assert first.demand_count == 3
    assert first.scope_invariant_rule_demand_count == 1
    assert first.match_scope_rule_first_count == 2
    assert first.admitted_effect_rule_count == 0
    assert {
        (item.source_match_kind, item.dependency_status)
        for item in first.demands
    } == {
        ("EXACT_IDENTITY", "SCOPE_INVARIANT_RULE_DEMAND"),
        ("SAME_ELEMENT_DIFFERENT_IDENTITY", "MATCH_SCOPE_RULE_FIRST"),
    }
    assert all(
        item.required_rule_dimensions
        == RELATION_EFFECT_REQUIRED_RULE_DIMENSIONS
        and item.effect_status == "UNRESOLVED"
        and item.usability_status == "UNRESOLVED"
        and item.selection_authority is False
        for item in first.demands
    )


def test_relation_effect_frontier_keeps_clear_case_empty_and_abstained() -> None:
    frontier = _frontier(
        _bundle(
            ChartPillars(
                year="丁巳",
                month="乙巳",
                day="乙丑",
                hour="乙酉",
            )
        )
    )

    assert frontier.demands == ()
    assert frontier.demand_count == 0
    assert frontier.scope_invariant_rule_demand_count == 0
    assert frontier.match_scope_rule_first_count == 0
    assert frontier.admitted_effect_rule_count == 0
    assert frontier.source_discussion_disposition == "ABSTAIN"
    assert frontier.effect_status == "UNRESOLVED"
    assert frontier.usability_status == "UNRESOLVED"


def test_relation_effect_frontier_binds_exact_upstream_lineage() -> None:
    bundle = _bundle(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    frontier = _frontier(bundle)

    assert (frontier.reading_ref, frontier.reading_hash) == (
        bundle["reading"].reading_ref,
        bundle["reading"].reading_hash,
    )
    assert (
        frontier.source_review_vector_ref,
        frontier.source_review_vector_hash,
    ) == (
        bundle["source_review"].vector_ref,
        bundle["source_review"].vector_hash,
    )
    assert (frontier.prerequisite_ref, frontier.prerequisite_hash) == (
        bundle["prerequisite"].prerequisite_ref,
        bundle["prerequisite"].prerequisite_hash,
    )
    assert (
        frontier.refusal_receipt_ref,
        frontier.refusal_receipt_hash,
    ) == (
        bundle["refusal"].receipt_ref,
        bundle["refusal"].receipt_hash,
    )
    assert {item.intersection_ref for item in frontier.demands} == {
        relation.intersection_ref
        for review in bundle["source_review"].reviews
        for relation in review.relation_intersections
    }


def test_relation_effect_frontier_fails_closed_on_version_or_lineage_drift() -> None:
    bundle = _bundle(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    projector = MingliRelationEffectResearchFrontierProjector()

    with pytest.raises(
        ValueError,
        match="relation_effect_frontier_prerequisite_version_not_supported",
    ):
        projector.project(
            reading=bundle["reading"],
            source_review_vector=bundle["source_review"],
            prerequisite=_reissue_prerequisite(
                bundle["prerequisite"],
                prerequisite_version=(
                    "v60.mingli-source-usability-prerequisite.999"
                ),
            ),
            refusal=bundle["refusal"],
        )

    with pytest.raises(
        ValueError,
        match="relation_effect_frontier_reading_lineage_mismatch",
    ):
        projector.project(
            reading=bundle["reading"],
            source_review_vector=bundle["source_review"],
            prerequisite=bundle["prerequisite"],
            refusal=_reissue_refusal(
                bundle["refusal"],
                reading_ref="different-reading",
            ),
        )

    other = _bundle(
        ChartPillars(
            year="丁巳",
            month="乙巳",
            day="乙丑",
            hour="乙酉",
        )
    )
    with pytest.raises(
        ValueError,
        match="relation_effect_frontier_case_chart_lineage_mismatch",
    ):
        projector.project(
            reading=bundle["reading"],
            source_review_vector=other["source_review"],
            prerequisite=bundle["prerequisite"],
            refusal=bundle["refusal"],
        )


def test_relation_effect_frontier_has_no_effect_or_decision_authority() -> None:
    frontier = _frontier(
        _bundle(
            ChartPillars(
                year="己巳",
                month="丙子",
                day="丙寅",
                hour="甲午",
            )
        )
    )
    serialized = canonical_json(frontier.model_dump(mode="json"))

    assert frontier.provider_invoked is False
    assert frontier.decision_created is False
    assert frontier.gate_invoked is False
    assert frontier.selection_authority is False
    assert frontier.professional_verdict_allowed is False
    assert frontier.probability_claim_allowed is False
    assert frontier.canonical_write_allowed is False
    assert frontier.read_only is True
    for forbidden in (
        "ROOTED",
        "EFFECTIVE_WORK",
        "empirical_probability",
        "auspicious",
    ):
        assert forbidden not in serialized

    with pytest.raises(
        ValueError,
        match="relation_effect_frontier_hash_mismatch",
    ):
        MingliRelationEffectResearchFrontierEnvelope.model_validate(
            frontier.model_copy(
                update={"reading_hash": "f" * 64}
            ).model_dump(mode="python")
        )
