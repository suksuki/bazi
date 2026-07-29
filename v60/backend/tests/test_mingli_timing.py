from __future__ import annotations

from datetime import date, time

import pytest
from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.mingli import (
    MingliMechanismEvidenceCompiler,
    MingliQuantFoundationCompiler,
    MingliTimingEvidenceCompiler,
)
from abu_v60.mingli.calendar import (
    CALENDAR_ENGINE_VERSION,
    BirthInput,
    resolve_four_pillars,
)
from abu_v60.mingli.compiler import CompiledCase, compile_case

ANALYSIS_DATE = date(2026, 7, 29)


def _compile_timing(
    *,
    case_ref: str,
    birth_date: date,
    birth_time: time,
):
    birth_input = BirthInput(
        calendar_type="solar",
        birth_date=birth_date,
        birth_time=birth_time,
        timezone="Asia/Shanghai",
    )
    chart = resolve_four_pillars(birth_input)
    compiled = compile_case(
        case_ref=case_ref,
        birth_input=birth_input,
        chart=chart,
    )
    timing = MingliTimingEvidenceCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref=f"{case_ref}-life-v1",
        birth_input=birth_input,
        gender="male",
        pillars=compiled.pillars,
        facts=compiled.facts,
        analysis_date=ANALYSIS_DATE,
    )
    return birth_input, compiled, timing


def _mechanism(*, case_ref: str, compiled: CompiledCase):
    quant = MingliQuantFoundationCompiler().compile(
        case_ref=case_ref,
        chart_version_ref=compiled.chart_version_ref,
        pillars=compiled.pillars,
        facts=compiled.facts,
    )
    return MingliMechanismEvidenceCompiler().compile(
        quant_vector=quant,
        facts=compiled.facts,
    )


def test_liu_jin_timing_coordinates_are_real_and_bounded() -> None:
    _, _, timing = _compile_timing(
        case_ref="case-liu-jin-timing",
        birth_date=date(1977, 5, 8),
        birth_time=time(17, 30),
    )

    assert [
        (
            item.layer,
            item.pillar,
            item.ten_god_label,
            item.start_year,
            item.end_year,
        )
        for item in timing.coordinates
    ] == [
        ("DAYUN", "庚子", "正官", 2018, 2027),
        ("ANNUAL", "丙午", "伤官", None, None),
        ("MONTHLY", "乙未", "比肩", None, None),
    ]
    assert {
        (
            item.timing_layer,
            item.natal_slot,
            item.relation_type,
        )
        for item in timing.relation_evidence
    } == {
        ("DAYUN", "day", "six_harmony_membership"),
        ("MONTHLY", "day", "six_clash_membership"),
    }
    assert timing.activation_status == "UNRESOLVED"
    assert timing.effect_status == "UNRESOLVED"
    assert timing.calibration_status == "NOT_CALIBRATED"
    assert "auspiciousness" in timing.forbidden_conclusions
    assert "reality_event" in timing.forbidden_conclusions


def test_yanzhou_timing_coordinates_feed_dream_without_deciding_story() -> None:
    _, _, timing = _compile_timing(
        case_ref="case-yanzhou-timing",
        birth_date=date(1991, 8, 14),
        birth_time=time(9, 20),
    )

    assert [
        (item.layer, item.pillar, item.ten_god_label)
        for item in timing.coordinates
    ] == [
        ("DAYUN", "壬辰", "七杀"),
        ("ANNUAL", "丙午", "比肩"),
        ("MONTHLY", "乙未", "正印"),
    ]
    assert {
        (
            item.timing_layer,
            item.natal_slot,
            item.relation_type,
        )
        for item in timing.relation_evidence
    } == {
        ("DAYUN", "day", "same_branch_membership"),
        ("ANNUAL", "year", "six_harmony_membership"),
        ("MONTHLY", "year", "same_branch_membership"),
    }
    assert all(
        item.effect_status == "UNRESOLVED"
        for item in timing.relation_evidence
    )


def test_timing_vector_is_stable_under_fact_order_and_profile_is_pinned() -> None:
    birth_input, compiled, first = _compile_timing(
        case_ref="case-timing-stability",
        birth_date=date(1977, 5, 8),
        birth_time=time(17, 30),
    )
    replay = MingliTimingEvidenceCompiler().compile(
        case_ref="case-timing-stability",
        chart_version_ref=compiled.chart_version_ref,
        life_case_revision_ref="case-timing-stability-life-v1",
        birth_input=birth_input,
        gender="male",
        pillars=compiled.pillars,
        facts=tuple(reversed(compiled.facts)),
        analysis_date=ANALYSIS_DATE,
    )
    profile = KnowledgeAuthority().active_timing_evidence_profile()

    assert replay == first
    assert replay.vector_hash == first.vector_hash
    assert profile.calendar_engine_version == CALENDAR_ENGINE_VERSION
    assert profile.professionally_reviewed is False
    assert profile.runtime_scope == "DETERMINISTIC_TIMING_COORDINATES"


def test_timing_rejects_mechanism_from_another_chart() -> None:
    birth_input, compiled, _ = _compile_timing(
        case_ref="case-timing-lineage",
        birth_date=date(1977, 5, 8),
        birth_time=time(17, 30),
    )
    _, other, _ = _compile_timing(
        case_ref="case-other-lineage",
        birth_date=date(1991, 8, 14),
        birth_time=time(9, 20),
    )

    with pytest.raises(
        ValueError,
        match="timing_vector_mechanism_lineage_mismatch",
    ):
        MingliTimingEvidenceCompiler().compile(
            case_ref="case-timing-lineage",
            chart_version_ref=compiled.chart_version_ref,
            life_case_revision_ref="case-timing-lineage-life-v1",
            birth_input=birth_input,
            gender="male",
            pillars=compiled.pillars,
            facts=compiled.facts,
            analysis_date=ANALYSIS_DATE,
            mechanism_vector=_mechanism(
                case_ref="case-other-lineage",
                compiled=other,
            ),
        )
