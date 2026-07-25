from __future__ import annotations

import pytest

from core.contracts import BirthInputCanonical
from core.contracts.chart import PillarConstraint, PillarTargetDraft
from core.engines import BirthCalendarResolutionError, resolve_birth_input_pillars
from core.engines.bazi.chart_constraints import solve_chart_constraints
from core.engines.bazi.temporal_service import CanonicalTemporalService


def _birth(**updates: object) -> BirthInputCanonical:
    payload: dict[str, object] = {
        "birth_input_id": "birth:l2-authority",
        "gender": "male",
        "calendar_type": "solar",
        "birth_date": "1987-05-12",
        "birth_time": "18:00",
        "birth_location": "Shanghai",
        "timezone": "Asia/Shanghai",
        "input_quality": "user_birth_profile",
    }
    payload.update(updates)
    return BirthInputCanonical(**payload)


@pytest.mark.parametrize(
    ("updates", "error"),
    [
        ({"year_pillar": "A子", "month_pillar": "乙巳", "day_pillar": "辛酉", "hour_pillar": "丁酉"}, "invalid_year_stem"),
        ({"year_pillar": "丁A", "month_pillar": "乙巳", "day_pillar": "辛酉", "hour_pillar": "丁酉"}, "invalid_year_branch"),
        ({"year_pillar": "甲丑", "month_pillar": "丙寅", "day_pillar": "辛酉", "hour_pillar": "丁酉"}, "invalid_year_jiazi"),
        ({"year_pillar": "丁卯", "month_pillar": "丙寅", "day_pillar": "辛酉", "hour_pillar": "丁酉"}, "month_pillar_not_legal_for_year"),
        ({"year_pillar": "丁卯", "month_pillar": "乙巳", "day_pillar": "辛酉", "hour_pillar": "乙酉"}, "hour_pillar_not_legal_for_day"),
    ],
)
def test_supplied_pillars_are_strictly_validated(updates: dict[str, object], error: str) -> None:
    with pytest.raises(BirthCalendarResolutionError, match=error):
        resolve_birth_input_pillars(_birth(**updates))


def test_supplied_formal_pillars_must_match_declared_calendar_moment() -> None:
    with pytest.raises(BirthCalendarResolutionError, match="supplied_pillars_calendar_mismatch"):
        resolve_birth_input_pillars(_birth(
            year_pillar="丁巳",
            month_pillar="乙巳",
            day_pillar="乙丑",
            hour_pillar="乙酉",
            input_quality="calendar_verified_supplied",
        ))

    with pytest.raises(BirthCalendarResolutionError, match="invalid_birth_timezone"):
        resolve_birth_input_pillars(_birth(timezone="Mars/Olympus_Mons"))


def test_pillar_fact_sources_remain_explicit() -> None:
    verified = resolve_birth_input_pillars(_birth(
        year_pillar="丁卯",
        month_pillar="乙巳",
        day_pillar="辛酉",
        hour_pillar="丁酉",
        input_quality="calendar_verified_supplied",
    ))
    assert verified.input_quality == "calendar_verified_supplied"
    assert verified.pillar_fact_source == "calendar_verified_supplied"

    hypothetical = resolve_birth_input_pillars(_birth(
        year_pillar="丁巳",
        month_pillar="乙巳",
        day_pillar="乙丑",
        hour_pillar="乙酉",
        input_quality="structurally_legal_hypothetical",
    ))
    assert hypothetical.input_quality == "structurally_legal_hypothetical"
    assert hypothetical.pillar_fact_source == "structurally_legal_hypothetical"
    assert "not_resolved_to_real_birth_datetime" in hypothetical.warnings


def _draft(**constraints: PillarConstraint) -> PillarTargetDraft:
    return PillarTargetDraft(
        target_draft_id="draft:l2",
        **constraints,
    )


def test_global_solver_returns_zero_one_and_many_without_silent_commit() -> None:
    single = solve_chart_constraints(
        draft=_draft(
            year=PillarConstraint(pillar="丁巳"),
            month=PillarConstraint(branch="巳"),
            day=PillarConstraint(pillar="乙丑"),
            hour=PillarConstraint(branch="酉"),
        ),
        baseline_pillars=["庚寅", "丁亥", "庚戌", "壬午"],
    )
    assert single.status == "single_solution"
    assert single.selected_variant is not None
    assert single.selected_variant.pillars == ["丁巳", "乙巳", "乙丑", "乙酉"]

    none = solve_chart_constraints(
        draft=_draft(
            year=PillarConstraint(pillar="丁巳"),
            month=PillarConstraint(pillar="丙寅"),
            day=PillarConstraint(pillar="乙丑"),
            hour=PillarConstraint(branch="酉"),
        ),
        baseline_pillars=["庚寅", "丁亥", "庚戌", "壬午"],
    )
    assert none.status == "no_solution"
    assert none.selected_variant is None
    assert none.conflicts
    assert none.releasable_constraints == ["month.pillar", "year.pillar"]

    many = solve_chart_constraints(
        draft=_draft(
            year=PillarConstraint(pillar="丁巳"),
            month=PillarConstraint(branch="巳"),
            day=PillarConstraint(stem="乙"),
            hour=PillarConstraint(branch="酉"),
        ),
        baseline_pillars=["庚寅", "丁亥", "庚戌", "壬午"],
    )
    assert many.status == "multiple_solutions"
    assert many.candidate_count == 6
    assert many.selected_variant is None
    assert many.ranking_is_presentation_only is True


def test_global_solver_is_order_independent_and_constraint_monotonic() -> None:
    first = _draft(
        year=PillarConstraint(stem="丁"),
        month=PillarConstraint(branch="巳"),
        day=PillarConstraint(stem="乙"),
        hour=PillarConstraint(branch="酉"),
    )
    second = PillarTargetDraft.model_validate({
        "target_draft_id": "draft:l2",
        "hour": {"branch": "酉"},
        "day": {"stem": "乙"},
        "month": {"branch": "巳"},
        "year": {"stem": "丁"},
    })
    resolved_first = solve_chart_constraints(draft=first, baseline_pillars=["庚寅", "丁亥", "庚戌", "壬午"])
    resolved_second = solve_chart_constraints(draft=second, baseline_pillars=["庚寅", "丁亥", "庚戌", "壬午"])
    assert [item.pillars for item in resolved_first.candidates] == [item.pillars for item in resolved_second.candidates]

    relaxed = solve_chart_constraints(
        draft=first.model_copy(update={"hour": PillarConstraint()}),
        baseline_pillars=["庚寅", "丁亥", "庚戌", "壬午"],
    )
    assert relaxed.candidate_count >= resolved_first.candidate_count


def test_incompatible_cycle_year_anchor_is_explicitly_invalidated() -> None:
    result = solve_chart_constraints(
        draft=PillarTargetDraft(
            target_draft_id="draft:anchor",
            cycle_year_anchor=1977,
            year=PillarConstraint(pillar="甲子"),
            month=PillarConstraint(branch="寅"),
            day=PillarConstraint(pillar="乙丑"),
            hour=PillarConstraint(branch="酉"),
        ),
        baseline_pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
    )
    assert result.cycle_year_anchor is None
    assert result.invalidated_constraints[0].field == "cycle_year_anchor"


def test_canonical_temporal_service_separates_structural_calendar_and_active_levels() -> None:
    service = CanonicalTemporalService()
    structural = service.resolve_structural_dayun(
        pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
        gender="male",
        analysis_year=2026,
    )
    assert structural["resolution_level"] == "structural_valid"
    assert structural["direction"] == "reverse"
    assert [item["pillar"] for item in structural["luck_sequence"][:5]] == ["甲辰", "癸卯", "壬寅", "辛丑", "庚子"]
    assert structural["current_luck_status"] == "unresolved"

    calendar = service.resolve_calendar_candidates(
        pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
        birth_year_anchor=1977,
        timezone="Asia/Shanghai",
    )
    assert calendar["status"] == "candidate"
    assert calendar["candidate_count"] >= 1
    assert calendar["formal_birth_record_modified"] is False

    active = service.resolve_from_birth_year(
        pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
        gender="male",
        birth_year_anchor=1977,
        analysis_year=2026,
        timezone="Asia/Shanghai",
    )
    assert active["resolution_level"] == "active_dayun_resolved"
    assert active["luck_pillar"] == "庚子"
    assert active["luck_year_range"] == [2018, 2027]
    assert active["derivation_fingerprint"]


def test_partial_draft_never_silently_selects_a_chart() -> None:
    result = solve_chart_constraints(
        draft=_draft(year=PillarConstraint(stem="丁")),
        baseline_pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
    )
    assert result.status == "multiple_solutions"
    assert result.selected_variant is None
    assert result.candidate_count > 1


def test_temporal_comparison_uses_only_baseline_facts_that_are_present() -> None:
    service = CanonicalTemporalService()
    active = service.resolve_from_birth_year(
        pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
        gender="male",
        birth_year_anchor=1977,
        analysis_year=2026,
        timezone="Asia/Shanghai",
        baseline={"luck_pillar": "庚子", "luck_year_range": [2018, 2027]},
    )
    assert active["recomputation_status"] == "recomputed_unchanged"


def test_temporal_fingerprint_invalidates_stale_results() -> None:
    service = CanonicalTemporalService()
    original = service.resolve_structural_dayun(
        pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
        gender="male",
        analysis_year=2026,
        timezone="Asia/Shanghai",
    )
    assert service.is_current(
        original,
        pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
        gender="male",
        analysis_year=2026,
        timezone="Asia/Shanghai",
        birth_anchor=None,
    )
    assert not service.is_current(
        original,
        pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
        gender="female",
        analysis_year=2026,
        timezone="Asia/Shanghai",
        birth_anchor=None,
    )


def test_legacy_invalid_chart_remains_readable_but_cannot_derive_dayun() -> None:
    service = CanonicalTemporalService()
    result = service.resolve_world_timing(
        birth_input=_birth(
            year_pillar="戊午",
            month_pillar="己午",
            day_pillar="乙卯",
            hour_pillar="甲子",
            input_quality="synthetic_fixture",
        ),
        analysis_year=2026,
    )
    assert result["resolution_level"] == "pillar_facts_rejected"
    assert result["fact_integrity_status"] == "rejected"
    assert result["luck_sequence"] == []
    assert result["luck_pillar"] == ""
    assert result["formal_state_modified"] is False
