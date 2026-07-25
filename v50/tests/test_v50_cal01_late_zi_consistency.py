from __future__ import annotations

import json
from pathlib import Path

from lunar_python import Solar

from core.contracts import BirthInputCanonical
from core.engines import resolve_birth_input_pillars
from core.engines.bazi.chart_constraints import validate_four_pillars
from core.engines.bazi.temporal_service import CanonicalTemporalService
from core.engines.birth_calendar import BIRTH_PILLAR_ENGINE_VERSION, FORMAL_HOUR_RULE_VERSION
from scripts.v50_audit_cal01_late_zi import audit_late_zi


ROOT = Path(__file__).resolve().parents[1]
RA0_SUMMARY = (
    ROOT
    / "reports/v50-lean-consolidation/ra0-518k-realizability-v1"
    / "ra0_518k_execution_summary_v1.json"
)
FIXTURE = ROOT / "tests/fixtures/v50_cal01_late_zi_v1.json"


def _birth(*, birth_date: str, birth_time: str, **updates: object) -> BirthInputCanonical:
    payload: dict[str, object] = {
        "birth_input_id": f"cal01:{birth_date}:{birth_time}",
        "gender": "unknown",
        "calendar_type": "solar",
        "birth_date": birth_date,
        "birth_time": birth_time,
        "timezone": "Asia/Shanghai",
        "input_quality": "user_birth_profile",
    }
    payload.update(updates)
    return BirthInputCanonical(**payload)


def test_formal_midnight_rollover_keeps_late_zi_day_and_hour_consistent() -> None:
    before_zi = resolve_birth_input_pillars(
        _birth(birth_date="1987-05-12", birth_time="22:30")
    )
    late_zi = resolve_birth_input_pillars(
        _birth(birth_date="1987-05-12", birth_time="23:30")
    )
    after_midnight = resolve_birth_input_pillars(
        _birth(birth_date="1987-05-13", birth_time="00:30")
    )

    assert (before_zi.day_pillar, before_zi.hour_pillar) == ("辛酉", "己亥")
    assert (late_zi.day_pillar, late_zi.hour_pillar) == ("辛酉", "戊子")
    assert (after_midnight.day_pillar, after_midnight.hour_pillar) == ("壬戌", "庚子")
    assert validate_four_pillars(
        [
            late_zi.year_pillar,
            late_zi.month_pillar,
            late_zi.day_pillar,
            late_zi.hour_pillar,
        ]
    ) == []


def test_dependency_mismatch_remains_a_negative_fixture_not_formal_output() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    eight_char = Solar.fromYmdHms(1987, 5, 12, 23, 30, 0).getLunar().getEightChar()
    eight_char.setSect(2)
    dependency_pillars = (
        eight_char.getYear(),
        eight_char.getMonth(),
        eight_char.getDay(),
        eight_char.getTime(),
    )

    assert list(dependency_pillars) == fixture["dependency_negative"]["raw_pillars"]
    assert [issue.code for issue in validate_four_pillars(dependency_pillars)] == [
        fixture["dependency_negative"]["expected_invalid_reason"]
    ]
    assert BIRTH_PILLAR_ENGINE_VERSION == "v50.birth_pillar_engine.v2"
    assert FORMAL_HOUR_RULE_VERSION == "v50.five_rats.formal_day.v1"


def test_calendar_verified_late_zi_input_uses_the_same_formal_contract() -> None:
    resolved = resolve_birth_input_pillars(
        _birth(
            birth_date="1987-05-12",
            birth_time="23:30",
            year_pillar="丁卯",
            month_pillar="乙巳",
            day_pillar="辛酉",
            hour_pillar="戊子",
            input_quality="calendar_verified_supplied",
        )
    )

    assert resolved.pillar_fact_source == "calendar_verified_supplied"


def test_reverse_lookup_retains_both_midnight_and_late_zi_witnesses() -> None:
    candidates = CanonicalTemporalService().resolve_calendar_candidates(
        pillars=["丁卯", "乙巳", "辛酉", "戊子"],
        birth_year_anchor=1987,
        timezone="Asia/Shanghai",
    )

    assert [item["birth_time"] for item in candidates["candidates"]] == ["00:00", "23:00"]


def test_ra0_universe_and_4019_dependency_mismatches_remain_frozen_evidence() -> None:
    summary = json.loads(RA0_SUMMARY.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    semantic = summary["semantic_summary"]
    assert semantic["calendar_forward_scan"]["canonical_raw_late_zi_invalid_count"] == fixture[
        "retained_ra0_evidence"
    ]["late_zi_dependency_mismatch_count"]
    assert (
        semantic["reconstructed_universe"]["content_sha256"]
        == fixture["retained_ra0_evidence"]["universe_sha256"]
    )


def test_cal01_audit_is_deterministic_on_a_bounded_fixture_range() -> None:
    from datetime import date

    first = audit_late_zi(start=date(1987, 5, 11), end=date(1987, 5, 14))
    second = audit_late_zi(start=date(1987, 5, 11), end=date(1987, 5, 14))

    assert first == second
    assert first["counts"] == {
        "calendar_days": 3,
        "dependency_late_zi_mismatches": 3,
        "formal_invalid_outputs": 0,
    }
