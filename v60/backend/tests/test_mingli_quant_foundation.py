from __future__ import annotations

import pytest
from abu_v60.knowledge import (
    KnowledgeAuthority,
    KnowledgeProfileSelection,
    bazi_candidate_qualification_profile,
    bazi_foundation_profile,
    bazi_quant_foundation_profile,
)
from abu_v60.mingli import (
    MingliQuantFoundationCompiler,
    resolve_ten_god,
)
from abu_v60.mingli.calendar import ChartPillars
from abu_v60.mingli.compiler import compile_research_case

STEMS = tuple("甲乙丙丁戊己庚辛壬癸")
EXPECTED_TEN_GOD_MATRIX = {
    "甲": ("比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印"),
    "乙": ("劫财", "比肩", "伤官", "食神", "正财", "偏财", "正官", "七杀", "正印", "偏印"),
    "丙": ("偏印", "正印", "比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官"),
    "丁": ("正印", "偏印", "劫财", "比肩", "伤官", "食神", "正财", "偏财", "正官", "七杀"),
    "戊": ("七杀", "正官", "偏印", "正印", "比肩", "劫财", "食神", "伤官", "偏财", "正财"),
    "己": ("正官", "七杀", "正印", "偏印", "劫财", "比肩", "伤官", "食神", "正财", "偏财"),
    "庚": ("偏财", "正财", "七杀", "正官", "偏印", "正印", "比肩", "劫财", "食神", "伤官"),
    "辛": ("正财", "偏财", "正官", "七杀", "正印", "偏印", "劫财", "比肩", "伤官", "食神"),
    "壬": ("食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印", "比肩", "劫财"),
    "癸": ("伤官", "食神", "正财", "偏财", "正官", "七杀", "正印", "偏印", "劫财", "比肩"),
}


def _liu_jin_vector(
    authority: KnowledgeAuthority | None = None,
):
    compiled = compile_research_case(
        case_ref="case-liu-jin-quant-test",
        chart=ChartPillars(
            year="丁巳",
            month="乙巳",
            day="乙丑",
            hour="乙酉",
        ),
        knowledge=authority,
    )
    return MingliQuantFoundationCompiler(authority).compile(
        case_ref="case-liu-jin-quant-test",
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=compiled.facts,
    )


def test_ten_god_mapping_exhaustively_matches_the_frozen_matrix() -> None:
    for day_stem, expected_row in EXPECTED_TEN_GOD_MATRIX.items():
        assert tuple(
            resolve_ten_god(day_stem=day_stem, other_stem=other)
            for other in STEMS
        ) == expected_row


@pytest.mark.parametrize("invalid", ("", "A", "子"))
def test_ten_god_mapping_fails_closed_for_unregistered_stems(invalid: str) -> None:
    with pytest.raises(ValueError, match="not_registered"):
        resolve_ten_god(day_stem="甲", other_stem=invalid)


def test_liujin_quant_vector_separates_membership_from_interpretation() -> None:
    vector = _liu_jin_vector()

    assert vector.day_master_stem == "乙"
    assert vector.day_master_element == "wood"
    assert vector.day_master_polarity == "yin"
    assert vector.visible_stem_total == 4
    assert vector.hidden_stem_membership_total == 10
    assert {
        item.element: (
            item.visible_stem_count,
            item.hidden_stem_membership_count,
            item.total_membership_count,
        )
        for item in vector.element_measurements
    } == {
        "wood": (3, 0, 3),
        "fire": (1, 2, 3),
        "earth": (0, 3, 3),
        "metal": (0, 4, 4),
        "water": (0, 1, 1),
    }
    assert {
        item.polarity: (
            item.visible_stem_count,
            item.hidden_stem_membership_count,
            item.total_membership_count,
        )
        for item in vector.polarity_measurements
    } == {
        "yang": (0, 6, 6),
        "yin": (4, 4, 8),
    }
    assert vector.measurement_semantics == "DETERMINISTIC_UNWEIGHTED_STRUCTURE"
    assert vector.calibration_status == "NOT_CALIBRATED"
    assert "day_master_strength" in vector.forbidden_conclusions
    assert "empirical_probability" in vector.forbidden_conclusions


def test_liujin_ten_god_and_source_evidence_are_coordinate_bound() -> None:
    vector = _liu_jin_vector()
    visible = [
        (item.pillar_slot, item.stem, item.label)
        for item in vector.ten_god_occurrences
        if item.layer == "VISIBLE_STEM"
    ]
    hidden_counts = {
        item.label: item.hidden_membership_count for item in vector.ten_god_counts
    }

    assert visible == [
        ("year", "丁", "食神"),
        ("month", "乙", "比肩"),
        ("day", "乙", "日主"),
        ("hour", "乙", "比肩"),
    ]
    assert hidden_counts == {
        "比肩": 0,
        "劫财": 0,
        "食神": 0,
        "伤官": 2,
        "偏财": 1,
        "正财": 2,
        "七杀": 2,
        "正官": 2,
        "偏印": 1,
        "正印": 0,
    }
    assert len(vector.source_manifestation_evidence) == 2
    assert {
        item.source_match_kind for item in vector.source_manifestation_evidence
    } == {"SAME_ELEMENT_DIFFERENT_IDENTITY"}
    assert all(
        item.effect_status == "EFFECT_UNRESOLVED"
        for item in vector.source_manifestation_evidence
    )
    assert all(
        "rooted" not in item.evidence_states
        for item in vector.source_manifestation_evidence
    )


def test_quant_profile_change_creates_a_new_vector_identity() -> None:
    default = _liu_jin_vector()
    foundation = bazi_foundation_profile()
    candidate = bazi_candidate_qualification_profile()
    quant_v1 = bazi_quant_foundation_profile()
    quant_v2 = quant_v1.model_copy(
        update={
            "profile_version": "1.0.1-test",
            "source_refs": quant_v1.source_refs + ("test-only:quant-profile",),
        }
    )
    authority = KnowledgeAuthority(
        profiles=(foundation,),
        candidate_rule_profiles=(candidate,),
        quant_foundation_profiles=(quant_v1, quant_v2),
        active_selection=KnowledgeProfileSelection.from_profiles(
            foundation=foundation,
            candidate_rules=candidate,
            quant_foundation=quant_v2,
        ),
    )
    upgraded = _liu_jin_vector(authority)

    assert upgraded.quant_profile_ref.endswith("@1.0.1-test")
    assert upgraded.vector_ref != default.vector_ref
    assert upgraded.element_measurements == default.element_measurements
    assert upgraded.ten_god_occurrences != ()
