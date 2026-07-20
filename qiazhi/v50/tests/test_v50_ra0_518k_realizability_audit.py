from __future__ import annotations

import gzip
import json
from datetime import datetime
from pathlib import Path

from core.audit.calendar_realizability import (
    BOUNDARY_SOLAR_TERM,
    BOUNDARY_ZI_ROLLOVER,
    CalendarRange,
    CanonicalCalendarReader,
    ceil_minute,
    default_audit_ranges,
    jie_boundaries,
    lichun,
    scan_calendar_realizability,
)
from core.audit.chart_universe import (
    UNIVERSE_SIZE,
    audit_structural_universe,
    chart_index,
    chart_key,
    hour_options_for,
    iter_structural_universe,
    month_options_for,
    pillars_at_index,
    structural_invalid_reasons,
)
from scripts.v50_run_ra0_518k_realizability_audit import (
    FIXTURE_PATH,
    inspect_legacy_518k,
    sha256_file,
    write_deterministic_gzip_jsonl,
)


def test_structural_universe_reconciles_exactly_to_518400() -> None:
    result = audit_structural_universe()

    assert UNIVERSE_SIZE == 518_400
    assert result.record_count == 518_400
    assert result.unique_chart_key_count == 518_400
    assert result.duplicate_count == 0
    assert result.structurally_valid_count == 518_400
    assert result.structurally_invalid_count == 0
    assert result.invalid_reason_distribution == {}


def test_chart_index_round_trips_formal_universe_without_duplicate_identity() -> None:
    samples = [0, 1, 11, 12, 719, 720, 259_199, UNIVERSE_SIZE - 1]
    for index in samples:
        pillars = pillars_at_index(index)
        assert chart_index(pillars) == index
        assert len(chart_key(pillars).split("|")) == 4

    assert sum(1 for _ in iter_structural_universe()) == UNIVERSE_SIZE


def test_five_tigers_and_five_rats_positive_and_negative_fixtures() -> None:
    assert month_options_for("甲子")[0] == "丙寅"
    assert month_options_for("己巳")[0] == "丙寅"
    assert hour_options_for("甲子")[0] == "甲子"
    assert hour_options_for("己巳")[0] == "甲子"

    assert structural_invalid_reasons(("甲子", "丙寅", "甲子", "甲子")) == ()
    assert "month_pillar_not_legal_for_year" in structural_invalid_reasons(
        ("甲子", "戊寅", "甲子", "甲子")
    )
    assert "hour_pillar_not_legal_for_day" in structural_invalid_reasons(
        ("甲子", "丙寅", "甲子", "丙子")
    )
    assert "invalid_year_jiazi" in structural_invalid_reasons(
        ("甲丑", "丙寅", "甲子", "甲子")
    )


def test_machine_fixtures_match_formal_structural_rules() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    for fixture in payload["positive_fixtures"]:
        if "pillars" not in fixture or "expected_invalid_reasons" not in fixture:
            continue
        assert list(structural_invalid_reasons(tuple(fixture["pillars"]))) == fixture[
            "expected_invalid_reasons"
        ]

    for fixture in payload["structural_negative_fixtures"]:
        reasons = structural_invalid_reasons(tuple(fixture["pillars"]))
        assert fixture["expected_invalid_reason"] in reasons


def test_lichun_and_jie_boundaries_use_formal_minute_precision() -> None:
    reader = CanonicalCalendarReader()
    exact = lichun(1984)
    transition = ceil_minute(exact)

    assert exact.isoformat() == "1984-02-04T23:18:44"
    assert reader.official_pillars(transition.replace(minute=18))[0] == "癸亥"
    assert reader.official_pillars(transition)[0] == "甲子"

    jingzhe = next(value for name, value in jie_boundaries(1984) if name == "惊蛰")
    jingzhe_minute = ceil_minute(jingzhe)
    assert reader.official_pillars(jingzhe_minute.replace(minute=24))[1] == "丙寅"
    assert reader.official_pillars(jingzhe_minute)[1] == "丁卯"


def test_zi_rollover_sensitivity_does_not_change_formal_policy() -> None:
    reader = CanonicalCalendarReader()
    at = datetime(1987, 5, 12, 23, 30)

    formal = reader.official_pillars(at)
    sensitivity = reader.sensitivity_pillars(at, sect=1)

    assert formal == ("丁卯", "乙巳", "辛酉", "戊子")
    assert sensitivity == ("丁卯", "乙巳", "壬戌", "庚子")
    assert reader.canonical_raw_late_zi_invalid_count == 1
    assert reader.policy_manifest()["day_rollover_formal"] == "midnight_lunar_python_sect_2"


def test_forward_scan_keeps_unseen_separate_from_structural_invalidity() -> None:
    audit_range = CalendarRange(
        range_id="fixture",
        label="LiChun boundary fixture",
        start=datetime(1984, 2, 4, 23, 18),
        end=datetime(1984, 2, 6, 0, 0),
        source="test",
    )
    result = scan_calendar_realizability([audit_range])
    row = result.ranges["fixture"]

    assert result.actual_timestamp_structural_failure_count == 0
    assert 0 < row.realizable_count < UNIVERSE_SIZE
    assert row.unseen_count == UNIVERSE_SIZE - row.realizable_count
    assert row.boundary_count(BOUNDARY_SOLAR_TERM) > 0
    assert row.boundary_count(BOUNDARY_ZI_ROLLOVER) > 0
    assert row.solar_term_boundary_event_count == 1
    assert row.zi_rollover_policy_event_count >= 1


def test_requested_ranges_are_independent_and_cover_exact_cycle_boundaries() -> None:
    reference, product, extended = default_audit_ranges()

    assert reference.range_id == "reference_60y_1984_2044"
    assert reference.start == ceil_minute(lichun(1984))
    assert reference.end == ceil_minute(lichun(2044))
    assert product.start == datetime(1900, 1, 1)
    assert product.end == datetime(2101, 1, 1)
    assert extended.start == ceil_minute(lichun(1804))
    assert extended.end == ceil_minute(lichun(2044))
    assert reference.start != product.start != extended.start


def test_deterministic_gzip_has_stable_hash_and_zero_timestamp(tmp_path: Path) -> None:
    rows = [
        {"chart_key": "甲子|丙寅|甲子|甲子", "calendar_realizable": True},
        {"chart_key": "甲子|丙寅|甲子|乙丑", "calendar_realizable": False},
    ]
    first = tmp_path / "first.jsonl.gz"
    second = tmp_path / "second.jsonl.gz"

    write_deterministic_gzip_jsonl(first, rows)
    write_deterministic_gzip_jsonl(second, rows)

    assert sha256_file(first) == sha256_file(second)
    with gzip.open(first, "rt", encoding="utf-8") as handle:
        assert [json.loads(line) for line in handle] == rows


def test_legacy_518k_contract_is_not_misreported_as_entity_chart_corpus(tmp_path: Path) -> None:
    generator = tmp_path / "corpus_518k.py"
    generator.write_text(
        "TARGET_CASE_COUNT = 518_400\n"
        "class CorpusCaseSummary:\n"
        "    case_id: str\n"
        "    day_master: str\n",
        encoding="utf-8",
    )
    index = tmp_path / "index.json"
    index.write_text(json.dumps({"entries": [{"run_id": "one"}]}), encoding="utf-8")

    result = inspect_legacy_518k(generator_path=generator, index_path=index)

    assert result["claimed_target_case_count"] == 518_400
    assert result["actual_entity_record_count"] == 0
    assert result["four_pillar_schema_present"] is False
    assert result["five_tigers_applied"] is False
    assert result["five_rats_applied"] is False
    assert result["legacy_validation_run_count"] == 1
