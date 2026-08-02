from __future__ import annotations

import pytest
from abu_v60.mingli import (
    MingliQuantFoundationCompiler,
    MingliSourceCoordinateReviewCompiler,
    MingliSourceUsabilityPrerequisiteProjector,
)
from abu_v60.mingli.calendar import ChartPillars
from abu_v60.mingli.compiler import compile_research_case
from abu_v60.provenance import canonical_json


def _compile(pillars: ChartPillars):
    compiled = compile_research_case(
        case_ref=f"test-source-usability-{pillars.year}-{pillars.month}",
        chart=pillars,
    )
    quant = MingliQuantFoundationCompiler().compile(
        case_ref=compiled.life_case_payload["case_ref"],
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=compiled.facts,
    )
    review = MingliSourceCoordinateReviewCompiler().compile(
        quant_vector=quant,
        facts=compiled.facts,
    )
    return compiled, quant, review


def test_source_usability_exposes_two_unselected_scopes_for_real_review_shape() -> None:
    pillars = ChartPillars(
        year="己巳",
        month="丙子",
        day="丙寅",
        hour="甲午",
    )
    compiled, quant, review = _compile(pillars)
    reversed_quant = MingliQuantFoundationCompiler().compile(
        case_ref=compiled.life_case_payload["case_ref"],
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=tuple(reversed(compiled.facts)),
    )
    reversed_review = MingliSourceCoordinateReviewCompiler().compile(
        quant_vector=reversed_quant,
        facts=tuple(reversed(compiled.facts)),
    )
    projector = MingliSourceUsabilityPrerequisiteProjector()

    first = projector.project(
        quant_vector=quant,
        source_review_vector=review,
    )
    second = projector.project(
        quant_vector=reversed_quant,
        source_review_vector=reversed_review,
    )

    assert first == second
    assert first.carrier_count == 4
    assert first.exact_identity_only_clear_count == 5
    assert first.exact_identity_only_review_required_count == 1
    assert first.element_affinity_included_clear_count == 7
    assert first.element_affinity_included_review_required_count == 3
    assert first.competing_carrier_count == 3
    assert first.ready_carrier_count == 0
    assert all(
        tuple(scope.scope_id for scope in carrier.scopes)
        == ("EXACT_IDENTITY_ONLY", "ELEMENT_AFFINITY_INCLUDED")
        and carrier.discussion_ready is False
        and all(scope.selection_authority is False for scope in carrier.scopes)
        for carrier in first.carriers
    )
    year = first.carriers[0]
    assert (year.visible_slot, year.visible_stem) == ("year", "己")
    assert year.scopes[0].source_review_count == 1
    assert year.scopes[0].relation_review_count == 1
    assert year.scopes[1].source_review_count == 3
    assert year.scopes[1].relation_review_count == 1


def test_source_usability_keeps_clear_coordinates_unresolved() -> None:
    _, quant, review = _compile(
        ChartPillars(
            year="丁巳",
            month="乙巳",
            day="乙丑",
            hour="乙酉",
        )
    )

    prerequisite = MingliSourceUsabilityPrerequisiteProjector().project(
        quant_vector=quant,
        source_review_vector=review,
    )

    assert prerequisite.element_affinity_included_review_required_count == 0
    assert prerequisite.ready_carrier_count == 0
    for carrier in prerequisite.carriers:
        requirements = {
            item.requirement_id: item for item in carrier.requirements
        }
        assert requirements["RELATION_EFFECT_RULE"].status == "NOT_TRIGGERED"
        assert requirements["ROOT_USABILITY_RULE"].status == "NOT_ADMITTED"
        assert carrier.scopes[1].root_usability_status == "UNRESOLVED"


def test_source_usability_fails_closed_on_lineage_or_bijection_drift() -> None:
    _, quant, review = _compile(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    projector = MingliSourceUsabilityPrerequisiteProjector()

    with pytest.raises(
        ValueError,
        match="source_usability_case_chart_lineage_mismatch",
    ):
        projector.project(
            quant_vector=quant,
            source_review_vector=review.model_copy(
                update={"case_ref": "different-case"}
            ),
        )

    with pytest.raises(
        ValueError,
        match="source_usability_source_review_bijection_mismatch",
    ):
        projector.project(
            quant_vector=quant,
            source_review_vector=review.model_copy(
                update={"reviews": review.reviews[:-1]}
            ),
        )


def test_source_usability_projection_has_no_effect_or_probability_authority() -> None:
    _, quant, review = _compile(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )

    prerequisite = MingliSourceUsabilityPrerequisiteProjector().project(
        quant_vector=quant,
        source_review_vector=review,
    )
    serialized = canonical_json(prerequisite.model_dump(mode="json"))

    assert prerequisite.professional_verdict_allowed is False
    assert prerequisite.probability_claim_allowed is False
    assert prerequisite.canonical_write_allowed is False
    assert prerequisite.read_only is True
    assert "ROOTED" not in serialized
    assert "EFFECTIVE_WORK" not in serialized
    assert "support_score" not in serialized
    assert "empirical_probability" not in serialized
