from __future__ import annotations

from datetime import date

import pytest
from abu_v60.db import engine
from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.mingli.showcases import (
    ABU_CASE_REF,
    DUODUO_CASE_REF,
    seed_mingli_showcases,
)
from abu_v60.mingli.stage import MingliStageError, MingliStageService
from abu_v60.mingli.stage_contracts import (
    MingliStageColumn,
    MingliStageMode,
    MingliStageProjection,
)
from sqlalchemy import text


def _owner_account_ref() -> str:
    with engine.connect() as connection:
        return str(
            connection.execute(
                text(
                    """
                    SELECT owner_account_ref
                    FROM mingli.cases
                    WHERE subject_kind = 'HUMAN_OWNER'
                      AND status = 'ACTIVE'
                    ORDER BY created_at, case_ref
                    LIMIT 1
                    """
                )
            ).scalar_one()
        )


def test_character_showcase_seed_is_idempotent_and_does_not_replace_references() -> None:
    first = seed_mingli_showcases(engine)
    replay = seed_mingli_showcases(engine)

    assert replay == first
    with engine.connect() as connection:
        rows = (
            connection.execute(
                text(
                    """
                SELECT case_ref, subject_kind, pillars_json
                FROM mingli.cases AS c
                JOIN mingli.chart_versions AS cv USING (case_ref)
                WHERE case_ref IN (:abu_case_ref, :duoduo_case_ref)
                ORDER BY case_ref
                """
                ),
                {
                    "abu_case_ref": ABU_CASE_REF,
                    "duoduo_case_ref": DUODUO_CASE_REF,
                },
            )
            .mappings()
            .all()
        )
        historical_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM mingli.cases AS c
                JOIN identity.profiles AS p USING (profile_ref)
                WHERE c.subject_kind = 'HUMAN_REFERENCE'
                  AND p.display_name IN ('Abu', '多多')
                """
            )
        ).scalar_one()
    assert {row["subject_kind"] for row in rows} == {"CANONICAL_SYNTHETIC"}
    assert {row["case_ref"] for row in rows} == {ABU_CASE_REF, DUODUO_CASE_REF}
    assert historical_count >= 2


def test_four_and_six_column_stages_are_exact_and_effects_stay_unresolved() -> None:
    seed_mingli_showcases(engine)
    service = MingliStageService(
        engine,
        current_date_provider=lambda _: date(2026, 8, 1),
    )
    account_ref = _owner_account_ref()

    natal = service.project(
        account_ref=account_ref,
        subject_id="abu",
        stage_mode=MingliStageMode.NATAL_4,
    )
    six = service.project(
        account_ref=account_ref,
        subject_id="duoduo",
        stage_mode=MingliStageMode.NATAL_DAYUN_YEAR_6,
        selected_year=2026,
    )

    assert [column.pillar for column in natal.columns] == ["戊寅", "癸亥", "壬戌", "丙午"]
    assert len(natal.columns) == 4
    assert len(natal.bodies) == 8
    assert [column.pillar for column in six.columns] == [
        "辛巳",
        "癸巳",
        "辛未",
        "丁酉",
        "乙未",
        "丙午",
    ]
    assert len(six.columns) == 6
    assert len(six.bodies) == 12
    assert [relation.relation_type for relation in six.relations] == [
        "six_harmony_membership",
        "six_harmony_membership",
    ]
    assert all(
        relation.effect_status == "UNRESOLVED" and relation.usable_source_status == "UNRESOLVED"
        for relation in six.relations
    )
    assert six.professional_verdict_allowed is False
    assert six.current_dayun_start_date == date(2020, 9, 28)
    assert six.current_dayun_end_date == date(2030, 9, 28)
    assert six.dayun_boundary_precision == "START_SOLAR_DATE_TIME_UNRESOLVED_ON_BOUNDARY_DAY"
    assert six.dayun_calculation_policy == "LUNAR_PYTHON_YUN_SECT_1_START_SOLAR_DATE_BOUNDARIES"
    assert six.dayun_resolution_status == "RESOLVED_OUTSIDE_BOUNDARY_DAY"


def test_stage_keeps_foundation_binding_when_relation_result_is_empty() -> None:
    seed_mingli_showcases(engine)
    stage = MingliStageService(
        engine,
        current_date_provider=lambda _: date(2026, 8, 1),
    ).project(
        account_ref=_owner_account_ref(),
        subject_id="abu",
        stage_mode=MingliStageMode.NATAL_4,
    )
    foundation = KnowledgeAuthority().active_foundation_profile()
    values = stage.model_dump(
        mode="python",
        exclude={
            "projection_ref",
            "projection_hash",
            "projection_version",
            "read_only",
        },
    )
    values["relations"] = ()

    zero_relation_stage = MingliStageProjection.issue(**values)

    assert zero_relation_stage.relations == ()
    assert zero_relation_stage.foundation_profile_ref == foundation.source_ref
    assert zero_relation_stage.foundation_profile_hash == foundation.profile_hash
    assert foundation.source_ref in zero_relation_stage.source_refs


def _column(
    *,
    slot: str,
    source_layer: str,
    pillar: str,
) -> MingliStageColumn:
    return MingliStageColumn(
        column_ref=f"column:{slot}",
        slot=slot,
        label=slot,
        source_layer=source_layer,
        pillar=pillar,
        stem=pillar[0],
        branch=pillar[1],
        coordinate_ref=f"coordinate:{slot}",
        start_year=2000 if source_layer == "DAYUN" else None,
        end_year=2009 if source_layer == "DAYUN" else None,
        start_date=date(2000, 1, 1) if source_layer == "DAYUN" else None,
        end_date=date(2010, 1, 1) if source_layer == "DAYUN" else None,
        calculation_status="DETERMINISTIC_COORDINATE",
    )


def test_relation_facts_bind_exact_duplicate_branch_slots_in_both_directions() -> None:
    columns = (
        _column(slot="NATAL_YEAR", source_layer="NATAL", pillar="甲寅"),
        _column(slot="NATAL_MONTH", source_layer="NATAL", pillar="丙寅"),
        _column(slot="NATAL_DAY", source_layer="NATAL", pillar="乙亥"),
    )
    facts = (
        {
            "fact_ref": "fact:year-day",
            "fact_type": "six_harmony_membership",
            "fact_json": {
                "left_slot": "year",
                "left_branch": "寅",
                "right_slot": "day",
                "right_branch": "亥",
            },
        },
        {
            "fact_ref": "fact:month-day-reversed",
            "fact_type": "six_harmony_membership",
            "fact_json": {
                "left_slot": "day",
                "left_branch": "亥",
                "right_slot": "month",
                "right_branch": "寅",
            },
        },
    )
    foundation = KnowledgeAuthority().active_foundation_profile()

    relations = MingliStageService._relations(
        columns=columns,
        facts=facts,
        relation_definitions=foundation.relations,
        rule_ref=foundation.source_ref,
        rule_hash=foundation.profile_hash,
    )
    by_columns = {
        (relation.left_column_ref, relation.right_column_ref): relation for relation in relations
    }

    assert by_columns[("column:NATAL_YEAR", "column:NATAL_DAY")].evidence_refs == (
        "coordinate:NATAL_YEAR",
        "coordinate:NATAL_DAY",
        "fact:year-day",
    )
    assert by_columns[("column:NATAL_MONTH", "column:NATAL_DAY")].evidence_refs == (
        "coordinate:NATAL_MONTH",
        "coordinate:NATAL_DAY",
        "fact:month-day-reversed",
    )


def test_temporal_same_branch_pair_cannot_reuse_natal_relation_fact() -> None:
    columns = (
        _column(slot="NATAL_YEAR", source_layer="NATAL", pillar="甲寅"),
        _column(slot="NATAL_DAY", source_layer="NATAL", pillar="乙亥"),
        _column(slot="DAYUN", source_layer="DAYUN", pillar="丁亥"),
    )
    facts = (
        {
            "fact_ref": "fact:year-day",
            "fact_type": "six_harmony_membership",
            "fact_json": {
                "left_slot": "year",
                "left_branch": "寅",
                "right_slot": "day",
                "right_branch": "亥",
            },
        },
    )
    foundation = KnowledgeAuthority().active_foundation_profile()

    relations = MingliStageService._relations(
        columns=columns,
        facts=facts,
        relation_definitions=foundation.relations,
        rule_ref=foundation.source_ref,
        rule_hash=foundation.profile_hash,
    )
    by_columns = {
        (relation.left_column_ref, relation.right_column_ref): relation for relation in relations
    }

    assert "fact:year-day" in by_columns[("column:NATAL_YEAR", "column:NATAL_DAY")].evidence_refs
    assert by_columns[("column:NATAL_YEAR", "column:DAYUN")].evidence_refs == (
        "coordinate:NATAL_YEAR",
        "coordinate:DAYUN",
    )


def test_selected_annual_label_does_not_follow_pre_lichun_current_date() -> None:
    seed_mingli_showcases(engine)
    service = MingliStageService(
        engine,
        current_date_provider=lambda _: date(2026, 1, 1),
    )
    stage = service.project(
        account_ref=_owner_account_ref(),
        subject_id="abu",
        stage_mode=MingliStageMode.NATAL_DAYUN_YEAR_6,
        selected_year=2026,
    )

    assert stage.columns[4].pillar == "乙丑"
    assert stage.columns[5].pillar == "丙午"
    assert stage.selected_year == 2026


def test_owner_stage_binds_the_latest_reading_identity() -> None:
    stage = MingliStageService(engine).project(
        account_ref=_owner_account_ref(),
        subject_id="current",
        stage_mode=MingliStageMode.NATAL_4,
    )

    assert stage.subject_kind == "HUMAN_OWNER"
    assert stage.reading_ref is not None
    assert stage.reading_hash is not None
    assert stage.reading_ref in stage.source_refs


def test_owner_current_six_columns_are_the_private_golden_case() -> None:
    stage = MingliStageService(
        engine,
        current_date_provider=lambda _: date(2026, 8, 1),
    ).project(
        account_ref=_owner_account_ref(),
        subject_id="current",
        stage_mode=MingliStageMode.NATAL_DAYUN_YEAR_6,
        selected_year=2026,
    )

    assert stage.subject_kind == "HUMAN_OWNER"
    assert stage.privacy_scope == "PRIVATE_OWNER"
    assert [column.pillar for column in stage.columns] == [
        "丁巳",
        "乙巳",
        "乙丑",
        "乙酉",
        "庚子",
        "丙午",
    ]
    assert stage.current_dayun_start_date == date(2018, 4, 18)
    assert stage.current_dayun_end_date == date(2028, 4, 18)


def test_abu_stage_refuses_boundary_day_and_selects_either_side() -> None:
    seed_mingli_showcases(engine)
    account_ref = _owner_account_ref()
    before = MingliStageService(
        engine,
        current_date_provider=lambda _: date(2017, 7, 30),
    ).project(
        account_ref=account_ref,
        subject_id="abu",
        stage_mode=MingliStageMode.NATAL_DAYUN_YEAR_6,
        selected_year=2017,
    )
    after = MingliStageService(
        engine,
        current_date_provider=lambda _: date(2017, 8, 1),
    ).project(
        account_ref=account_ref,
        subject_id="abu",
        stage_mode=MingliStageMode.NATAL_DAYUN_YEAR_6,
        selected_year=2017,
    )

    assert (
        before.columns[4].pillar,
        before.columns[4].start_date,
        before.columns[4].end_date,
    ) == ("甲子", date(2007, 7, 31), date(2017, 7, 31))
    assert (
        after.columns[4].pillar,
        after.columns[4].start_date,
        after.columns[4].end_date,
    ) == ("乙丑", date(2017, 7, 31), date(2027, 7, 31))

    with pytest.raises(
        MingliStageError,
        match="mingli_stage_dayun_boundary_unresolved",
    ):
        MingliStageService(
            engine,
            current_date_provider=lambda _: date(2017, 7, 31),
        ).project(
            account_ref=account_ref,
            subject_id="abu",
            stage_mode=MingliStageMode.NATAL_DAYUN_YEAR_6,
            selected_year=2017,
        )


def test_stage_rejects_five_column_and_non_whitelisted_subject_requests() -> None:
    service = MingliStageService(engine)
    account_ref = _owner_account_ref()

    with pytest.raises(MingliStageError, match="four_does_not_accept_year"):
        service.project(
            account_ref=account_ref,
            subject_id="current",
            stage_mode=MingliStageMode.NATAL_4,
            selected_year=2026,
        )
    with pytest.raises(MingliStageError, match="subject_not_found"):
        service.project(
            account_ref=account_ref,
            subject_id="v60-synthetic-case-yanzhou-v1",
            stage_mode=MingliStageMode.NATAL_4,
        )
