from __future__ import annotations

import pytest
from abu_v60.db import engine
from abu_v60.experience import HomeExperienceService
from abu_v60.knowledge import (
    KnowledgeAuthority,
    bazi_source_coordinate_review_profile,
)
from abu_v60.mingli import (
    MingliQuantFoundationCompiler,
    MingliSourceCoordinateReviewCompiler,
    MingliSourceReviewVectorStore,
)
from abu_v60.mingli.calendar import ChartPillars
from abu_v60.mingli.compiler import compile_research_case
from abu_v60.provenance import canonical_json
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

EXPECTED_SOURCE_REVIEW_PROFILE_HASH = (
    "e21e13ff2f79dbd4c180b34ee651996c30a0ac545931d3ce95d1b96a6a5b145c"
)


def _compile(
    pillars: ChartPillars,
) -> tuple[tuple[dict[str, object], ...], object]:
    compiled = compile_research_case(
        case_ref=f"test-source-review-{pillars.year}-{pillars.month}",
        chart=pillars,
    )
    quant = MingliQuantFoundationCompiler().compile(
        case_ref=compiled.life_case_payload["case_ref"],
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=compiled.facts,
    )
    return compiled.facts, quant


def test_source_review_profile_is_hash_locked_and_cannot_infer_effect() -> None:
    profile = bazi_source_coordinate_review_profile()

    assert profile.profile_hash == EXPECTED_SOURCE_REVIEW_PROFILE_HASH
    assert profile.runtime_scope == "SOURCE_COORDINATE_RELATION_REVIEW"
    assert profile.professionally_reviewed is False
    assert {item.admitted_fact_type for item in profile.rules} == {
        "six_clash_membership",
        "six_harmony_membership",
    }
    assert all(item.effect_conclusion_allowed is False for item in profile.rules)
    assert "usable_root" in profile.forbidden_conclusions
    assert "relation_effect" in profile.forbidden_conclusions

    authority = KnowledgeAuthority()
    assert authority.active_source_review_profile() is profile
    assert authority.source_review_manifest()[0]["active"] is True


def test_source_review_distinguishes_clear_clash_and_harmony_coordinates() -> None:
    facts, quant = _compile(
        ChartPillars(
            year="壬辰",
            month="庚戌",
            day="辛卯",
            hour="辛卯",
        )
    )
    compiler = MingliSourceCoordinateReviewCompiler()

    first = compiler.compile(quant_vector=quant, facts=facts)
    second = compiler.compile(
        quant_vector=quant,
        facts=tuple(reversed(facts)),
    )

    assert first == second
    assert first.source_evidence_count == len(quant.source_manifestation_evidence)
    assert first.review_required_count > 0
    assert first.six_clash_intersection_count > 0
    assert first.six_harmony_intersection_count > 0
    assert first.professional_verdict_allowed is False
    assert first.probability_claim_allowed is False
    assert first.canonical_write_allowed is False
    assert all(
        item.relation_effect_status == "UNRESOLVED" and item.root_usability_status == "UNRESOLVED"
        for item in first.reviews
    )
    serialized = canonical_json(first.model_dump(mode="json"))
    assert "ROOTED" not in serialized
    assert "EFFECTIVE_WORK" not in serialized
    assert "support_score" not in serialized


def test_source_review_reports_no_intersection_without_promoting_root() -> None:
    facts, quant = _compile(
        ChartPillars(
            year="丁巳",
            month="乙巳",
            day="乙丑",
            hour="乙酉",
        )
    )

    vector = MingliSourceCoordinateReviewCompiler().compile(
        quant_vector=quant,
        facts=facts,
    )

    assert vector.review_required_count == 0
    assert vector.clear_coordinate_count == vector.source_evidence_count
    assert all(
        item.review_states == ("NO_ADMITTED_RELATION_INTERSECTION",)
        and item.root_usability_status == "UNRESOLVED"
        for item in vector.reviews
    )


def test_source_review_fails_closed_on_unadmitted_relation_claims() -> None:
    facts, quant = _compile(
        ChartPillars(
            year="壬辰",
            month="庚戌",
            day="辛卯",
            hour="辛卯",
        )
    )
    relation = next(item for item in facts if item["fact_type"] == "six_clash_membership")
    malformed = {
        **relation,
        "fact_json": {
            **relation["fact_json"],
            "effect_not_inferred": False,
        },
    }
    mutated = tuple(
        malformed if item["fact_ref"] == relation["fact_ref"] else item for item in facts
    )

    with pytest.raises(
        ValueError,
        match="source_review_relation_claims_not_admitted",
    ):
        MingliSourceCoordinateReviewCompiler().compile(
            quant_vector=quant,
            facts=mutated,
        )


def test_source_review_fails_closed_on_cross_case_or_misaligned_relation() -> None:
    facts, quant = _compile(
        ChartPillars(
            year="壬辰",
            month="庚戌",
            day="辛卯",
            hour="辛卯",
        )
    )
    relation = next(item for item in facts if item["fact_type"] == "six_clash_membership")
    cross_case = {
        **relation,
        "case_ref": "different-case",
    }
    with pytest.raises(ValueError, match="source_review_fact_lineage_mismatch"):
        MingliSourceCoordinateReviewCompiler().compile(
            quant_vector=quant,
            facts=tuple(
                cross_case if item["fact_ref"] == relation["fact_ref"] else item for item in facts
            ),
        )

    misaligned = {
        **relation,
        "fact_json": {
            **relation["fact_json"],
            "left_branch": "子",
        },
    }
    with pytest.raises(
        ValueError,
        match="source_review_relation_coordinate_claim_mismatch",
    ):
        MingliSourceCoordinateReviewCompiler().compile(
            quant_vector=quant,
            facts=tuple(
                misaligned if item["fact_ref"] == relation["fact_ref"] else item for item in facts
            ),
        )


def test_source_review_store_is_idempotent_and_append_only() -> None:
    with engine.connect() as connection:
        account_ref = str(
            connection.execute(
                text(
                    """
                    SELECT owner_account_ref
                    FROM mingli.cases
                    WHERE subject_kind = 'HUMAN_OWNER'
                      AND status = 'ACTIVE'
                    GROUP BY owner_account_ref
                    HAVING count(*) = 1
                    ORDER BY owner_account_ref
                    LIMIT 1
                    """
                )
            ).scalar_one()
        )
    snapshot = HomeExperienceService(engine).snapshot(
        account_ref=account_ref,
    )
    store = MingliSourceReviewVectorStore(engine)
    expected = snapshot["mingli"]["source_coordinate_review"]
    prerequisite = snapshot["mingli"]["source_usability_prerequisite"]
    persisted = store.get(vector_ref=str(expected["vector_ref"]))

    reading = snapshot["mingli"]["reading"]
    lab = snapshot["lab"]
    assert reading["source_review_vector_ref"] == expected["vector_ref"]
    assert reading["source_review_vector_hash"] == expected["vector_hash"]
    assert lab["source_review_vector_ref"] == expected["vector_ref"]
    assert lab["source_review_vector_hash"] == expected["vector_hash"]
    assert lab["source_coordinate_reviews"] == expected["reviews"]
    assert prerequisite["source_review_vector_ref"] == expected["vector_ref"]
    assert prerequisite["source_review_vector_hash"] == expected["vector_hash"]
    assert lab["source_usability_prerequisite_ref"] == (prerequisite["prerequisite_ref"])
    assert lab["source_usability_prerequisite_hash"] == (prerequisite["prerequisite_hash"])
    assert lab["source_usability_prerequisite_carriers"] == (prerequisite["carriers"])
    assert (
        prerequisite
        == HomeExperienceService(engine).snapshot(
            account_ref=account_ref,
        )["mingli"]["source_usability_prerequisite"]
    )
    assert persisted.model_dump(mode="json") == expected
    with engine.connect() as connection:
        count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM mingli.source_coordinate_review_vectors
                WHERE vector_ref = :vector_ref
                """
            ),
            {"vector_ref": expected["vector_ref"]},
        ).scalar_one()
    assert count == 1

    with (
        pytest.raises(
            DBAPIError,
            match="mingli_source_review_vectors_are_append_only",
        ),
        engine.begin() as connection,
    ):
        connection.execute(
            text(
                """
                UPDATE mingli.source_coordinate_review_vectors
                SET vector_version = 'forbidden-rewrite'
                WHERE vector_ref = :vector_ref
                """
            ),
            {"vector_ref": expected["vector_ref"]},
        )
