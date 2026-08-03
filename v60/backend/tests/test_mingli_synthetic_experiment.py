from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from abu_v60.db import engine
from abu_v60.db.schema import mingli_synthetic_experiment_runs
from abu_v60.mingli.agent_normalization_receipt import (
    MingliAgentNormalizationDelta,
)
from abu_v60.mingli.agent_regime import (
    normalize_regime_decision,
    reconcile_day_master_state,
)
from abu_v60.mingli.agent_root_gate import root_candidate_assessments
from abu_v60.mingli.agent_runtime import MINGLI_AGENT_PROMPT_VIEW_MAX_CHARS
from abu_v60.mingli.agent_service import (
    MingliAgentService,
    MingliAgentServiceError,
)
from abu_v60.mingli.stage import MingliStageError, MingliStageService
from abu_v60.mingli.stage_contracts import MingliStageMode
from abu_v60.mingli.synthetic_experiment_catalog import (
    FIRST_SYNTHETIC_EXPERIMENT,
    FIRST_SYNTHETIC_EXPERIMENT_MEMBERS,
    FIRST_SYNTHETIC_EXPERIMENT_REF,
    HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT,
    HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
    HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT,
    HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
    ROOT_IDENTITY_SYNTHETIC_EXPERIMENT,
    ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
    SYNTHETIC_EXPERIMENT_ANALYSIS_DATE,
    SYNTHETIC_RESEARCH_ACCOUNT_REF,
    resolve_research_stage_subject,
    synthetic_experiment_public_definition,
    synthetic_experiment_public_definitions,
)
from abu_v60.mingli.synthetic_experiment_contracts import (
    SyntheticExperimentEvaluation,
)
from abu_v60.mingli.synthetic_experiment_evaluator import (
    evaluate_synthetic_experiment,
)
from abu_v60.mingli.synthetic_experiment_seed import (
    seed_first_synthetic_experiment,
    seed_synthetic_experiment,
)
from abu_v60.mingli.synthetic_experiment_service import (
    SyntheticExperimentError,
    SyntheticExperimentService,
)
from abu_v60.provenance import canonical_json, content_hash
from sqlalchemy import inspect, text


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


def _seed_and_packets() -> tuple[dict[str, Any], dict[str, Any]]:
    seeded = seed_first_synthetic_experiment(engine)
    by_case = {item["case_ref"]: item for item in seeded["members"]}
    service = SyntheticExperimentService(engine)
    packets = {
        member.variant: service._packet(
            case_ref=member.case_ref,
            reading_ref=str(by_case[member.case_ref]["reading_ref"]),
        )
        for member in FIRST_SYNTHETIC_EXPERIMENT_MEMBERS
    }
    return by_case, packets


def _seed_root_identity_and_packets() -> tuple[dict[str, Any], dict[str, Any]]:
    seeded = seed_synthetic_experiment(
        engine,
        experiment_ref=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
    )
    by_case = {item["case_ref"]: item for item in seeded["members"]}
    service = SyntheticExperimentService(engine)
    packets = {
        member.variant: service._packet(
            case_ref=member.case_ref,
            reading_ref=str(by_case[member.case_ref]["reading_ref"]),
        )
        for member in ROOT_IDENTITY_SYNTHETIC_EXPERIMENT.members
    }
    return by_case, packets


def _seed_experiment_and_packets(experiment: Any) -> dict[str, Any]:
    seeded = seed_synthetic_experiment(
        engine,
        experiment_ref=experiment.experiment_ref,
    )
    by_case = {item["case_ref"]: item for item in seeded["members"]}
    service = SyntheticExperimentService(engine)
    return {
        member.variant: service._packet(
            case_ref=member.case_ref,
            reading_ref=str(by_case[member.case_ref]["reading_ref"]),
        )
        for member in experiment.members
    }


def _passing_readings(*, issues: tuple[str, ...] = ()) -> dict[str, Any]:
    a_regime = SimpleNamespace(
        classification="UNRESOLVED",
        effective_root_status="ABSENT",
        effective_root_coordinates=(),
    )
    b_regime = SimpleNamespace(
        classification="ORDINARY_WEAK",
        effective_root_status="PRESENT",
        effective_root_coordinates=("hour支藏甲",),
    )
    return {
        "A": SimpleNamespace(
            output=SimpleNamespace(
                regime_decision=a_regime,
                day_master_state="UNCERTAIN",
                server_issue_keys=(),
            )
        ),
        "B": SimpleNamespace(
            output=SimpleNamespace(
                regime_decision=b_regime,
                day_master_state="WEAK",
                server_issue_keys=issues,
            )
        ),
    }


def _passing_root_identity_readings(
    *,
    a_status: str = "UNRESOLVED",
    b_status: str = "PRESENT",
    issues: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "A": SimpleNamespace(
            output=SimpleNamespace(
                regime_decision=SimpleNamespace(
                    classification=("ORDINARY_WEAK" if a_status == "PRESENT" else "UNRESOLVED"),
                    effective_root_status=a_status,
                    effective_root_coordinates=(("hour支藏乙",) if a_status == "PRESENT" else ()),
                ),
                day_master_state="WEAK",
                server_issue_keys=issues,
            )
        ),
        "B": SimpleNamespace(
            output=SimpleNamespace(
                regime_decision=SimpleNamespace(
                    classification="ORDINARY_WEAK",
                    effective_root_status=b_status,
                    effective_root_coordinates=(("hour支藏甲",) if b_status == "PRESENT" else ()),
                ),
                day_master_state="WEAK",
                server_issue_keys=issues,
            )
        ),
    }


def _hidden_rank_readings(
    *,
    a_status: str,
    b_status: str,
    a_thesis: str = "",
    b_thesis: str = "",
    a_raw_thesis: str | None = None,
    b_raw_thesis: str | None = None,
) -> dict[str, Any]:
    def reading(status: str, thesis: str, raw_thesis: str | None) -> Any:
        return SimpleNamespace(
            normalization_receipt=(
                None
                if raw_thesis is None
                else SimpleNamespace(raw_output={"whole_chart_thesis": raw_thesis})
            ),
            output=SimpleNamespace(
                regime_decision=SimpleNamespace(
                    classification="ORDINARY_WEAK",
                    effective_root_status=status,
                    effective_root_coordinates=(("hour支藏乙",) if status == "PRESENT" else ()),
                ),
                day_master_state="WEAK",
                whole_chart_thesis=thesis,
                server_issue_keys=(),
            )
        )

    return {
        "A": reading(a_status, a_thesis, a_raw_thesis),
        "B": reading(b_status, b_thesis, b_raw_thesis),
    }


def test_public_definition_seals_full_inputs_and_inference_limit() -> None:
    definition = synthetic_experiment_public_definition()
    identity = {key: value for key, value in definition.items() if key != "definition_hash"}

    assert definition["definition_hash"] == content_hash(identity)
    assert definition["family"] == "CONTROLLED_LEGAL_HOUR_PAIR"
    assert definition["controlled_members"]["A"]["birth_input"]["birth_time"] == "09:00:00"
    assert definition["controlled_members"]["B"]["expected_pillars"] == (
        "丙戌",
        "戊戌",
        "甲戌",
        "丙寅",
    )
    assert "不能把判型变化单独归因于根气" in definition["inference_limit"]
    mutated = {**identity, "inference_limit": "错误地宣称根气单变量"}
    assert content_hash(mutated) != definition["definition_hash"]


def test_catalog_has_four_unique_real_calendar_experiments() -> None:
    definitions = synthetic_experiment_public_definitions()
    assert len(definitions) == 4
    assert len({item["experiment_ref"] for item in definitions}) == 4
    assert definitions[0]["experiment_ref"] == FIRST_SYNTHETIC_EXPERIMENT_REF
    assert definitions[1]["experiment_ref"] == ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF
    assert definitions[1]["family"] == "CONTROLLED_ROOT_IDENTITY_PAIR"
    assert definitions[1]["changed_input"] == {
        "field": "birth_time",
        "A": "06:00:00",
        "B": "04:00:00",
    }
    assert definitions[1]["full_pillar_delta"] == {
        "A": ["己巳", "己巳", "甲午", "丁卯"],
        "B": ["己巳", "己巳", "甲午", "丙寅"],
        "changed_slots": ["hour"],
        "legal_hour_pillar_change": "丁卯 → 丙寅",
    }
    assert "不证明卯中乙无根" in definitions[1]["inference_limit"]
    assert definitions[2]["experiment_ref"] == (HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF)
    assert definitions[2]["changed_input"] == {
        "field": "birth_time",
        "A": "06:00:00",
        "B": "08:00:00",
    }
    assert definitions[3]["experiment_ref"] == (HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF)
    assert definitions[3]["changed_input"] == {
        "field": "birth_time",
        "A": "08:00:00",
        "B": "14:00:00",
    }
    assert all(
        item["catalog_version"] == "v60.mingli-synthetic-experiment-catalog.002"
        for item in definitions[2:]
    )
    for definition in definitions:
        identity = {key: value for key, value in definition.items() if key != "definition_hash"}
        assert definition["definition_hash"] == content_hash(identity)


def test_schema_metadata_matches_synthetic_run_table() -> None:
    actual = {
        item["name"]
        for item in inspect(engine).get_columns(
            "synthetic_experiment_runs",
            schema="mingli",
        )
    }
    assert actual == set(mingli_synthetic_experiment_runs.c.keys())


def test_catalog_routes_multiple_experiments_and_isolates_run_history() -> None:
    service = SyntheticExperimentService(engine)
    catalog = service.catalog()
    assert catalog["catalog_version"] == ("v60.mingli-synthetic-experiment-catalog.003")
    entries = {item["experiment_ref"]: item for item in catalog["experiments"]}
    assert set(entries) == {
        FIRST_SYNTHETIC_EXPERIMENT_REF,
        ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
        HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
        HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
    }
    for experiment_ref, entry in entries.items():
        assert all(run["experiment_ref"] == experiment_ref for run in entry["runs"])
        if entry["runs"]:
            assert entry["run_status"] == "SEALED"
            assert entry["latest_run_ref"] == entry["runs"][0]["run_ref"]
            assert entry["latest_outcome"] == entry["runs"][0]["outcome"]
        else:
            assert entry["run_status"] == "NOT_RUN"
            assert entry["latest_run_ref"] is None
    first_run = entries[FIRST_SYNTHETIC_EXPERIMENT_REF]["latest_run_ref"]
    assert first_run is not None
    with pytest.raises(
        SyntheticExperimentError,
        match="mingli_synthetic_experiment_run_mismatch",
    ):
        service.snapshot(
            experiment_ref=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
            run_ref=first_run,
            variant="A",
        )


def test_seed_uses_real_calendar_and_shared_materialization_without_leaking_gold() -> None:
    first = seed_first_synthetic_experiment(engine)
    replay = seed_first_synthetic_experiment(engine)

    assert replay == first
    assert first["analysis_date"] == SYNTHETIC_EXPERIMENT_ANALYSIS_DATE.isoformat()
    assert len(first["members"]) == 2
    assert all(
        item["materialization_version"] == "v60.mingli-case-materialization.001"
        and len(item["reading_hash"]) == 64
        and item["subject_kind"] == "CANONICAL_SYNTHETIC"
        for item in first["members"]
    )
    with engine.connect() as connection:
        profiles = (
            connection.execute(
                text(
                    """
                SELECT input_json
                FROM identity.profiles
                WHERE account_ref = :account_ref
                  AND input_json ->> 'experiment_ref' = :experiment_ref
                ORDER BY profile_ref
                """
                ),
                {
                    "account_ref": SYNTHETIC_RESEARCH_ACCOUNT_REF,
                    "experiment_ref": FIRST_SYNTHETIC_EXPERIMENT_REF,
                },
            )
            .scalars()
            .all()
        )
    assert len(profiles) == 2
    assert all(payload["gold_in_profile"] is False for payload in profiles)
    assert all(
        "effective_root_status" not in str(payload) and "regime_classification" not in str(payload)
        for payload in profiles
    )


def test_root_identity_seed_is_idempotent_and_keeps_gold_out_of_cases() -> None:
    first = seed_synthetic_experiment(
        engine,
        experiment_ref=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
    )
    replay = seed_synthetic_experiment(
        engine,
        experiment_ref=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
    )
    assert replay == first
    assert first["analysis_date"] == "2026-08-03"
    assert len(first["members"]) == 2
    with engine.connect() as connection:
        profiles = (
            connection.execute(
                text(
                    """
                SELECT input_json
                FROM identity.profiles
                WHERE account_ref = :account_ref
                  AND input_json ->> 'experiment_ref' = :experiment_ref
                ORDER BY profile_ref
                """
                ),
                {
                    "account_ref": SYNTHETIC_RESEARCH_ACCOUNT_REF,
                    "experiment_ref": ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
                },
            )
            .scalars()
            .all()
        )
    assert len(profiles) == 2
    assert all(payload["gold_in_profile"] is False for payload in profiles)
    assert all("minimum_anti_follow_gate" not in str(payload) for payload in profiles)


def test_research_cases_are_hidden_from_normal_subjects_and_guard_agent_generation() -> None:
    by_case, _ = _seed_and_packets()
    owner_account_ref = _owner_account_ref()
    standard = MingliStageService(engine)

    subjects = standard.subjects(account_ref=owner_account_ref)
    assert all(not item["subject_id"].startswith("research:") for item in subjects)
    with pytest.raises(MingliStageError, match="mingli_stage_subject_not_found"):
        standard.project(
            account_ref=owner_account_ref,
            subject_id=FIRST_SYNTHETIC_EXPERIMENT_MEMBERS[0].subject_id,
            stage_mode=MingliStageMode.NATAL_4,
        )

    member = FIRST_SYNTHETIC_EXPERIMENT_MEMBERS[0]
    materialized = by_case[member.case_ref]
    with pytest.raises(MingliAgentServiceError, match="mingli_agent_case_not_found"):
        MingliAgentService(engine).generate(
            requester_account_ref=owner_account_ref,
            case_ref=member.case_ref,
            expected_reading_ref=str(materialized["reading_ref"]),
            expected_reading_hash=str(materialized["reading_hash"]),
        )


def test_research_stage_is_explicitly_scoped_and_pins_base_reading() -> None:
    by_case, _ = _seed_and_packets()
    member = FIRST_SYNTHETIC_EXPERIMENT_MEMBERS[0]
    materialized = by_case[member.case_ref]
    service = MingliStageService(
        engine,
        current_date_provider=lambda _: SYNTHETIC_EXPERIMENT_ANALYSIS_DATE,
        research_subject_resolver=resolve_research_stage_subject,
    )
    stage = service.project(
        account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
        subject_id=member.subject_id,
        stage_mode=MingliStageMode.NATAL_4,
        pinned_reading_ref=str(materialized["reading_ref"]),
        pinned_reading_hash=str(materialized["reading_hash"]),
    )

    assert stage.projection_version == "v60.mingli-stage-projection.004"
    assert stage.identity_badge == "研究合成命盘"
    assert stage.privacy_scope == "SYNTHETIC_RESEARCH"
    assert stage.reading_ref == materialized["reading_ref"]
    assert stage.reading_hash == materialized["reading_hash"]
    with pytest.raises(
        MingliStageError,
        match="mingli_stage_pinned_reading_binding_incomplete",
    ):
        service.project(
            account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
            subject_id=member.subject_id,
            stage_mode=MingliStageMode.NATAL_4,
            pinned_reading_ref=str(materialized["reading_ref"]),
        )
    with pytest.raises(
        MingliStageError,
        match="mingli_stage_pinned_reading_lineage_conflict",
    ):
        service.project(
            account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
            subject_id=member.subject_id,
            stage_mode=MingliStageMode.NATAL_4,
            pinned_reading_ref=str(materialized["reading_ref"]),
            pinned_reading_hash="0" * 64,
        )


def test_snapshot_binding_closes_both_experiment_members() -> None:
    by_case, _ = _seed_root_identity_and_packets()
    stage_service = MingliStageService(
        engine,
        current_date_provider=lambda _: ROOT_IDENTITY_SYNTHETIC_EXPERIMENT.analysis_date,
        research_subject_resolver=resolve_research_stage_subject,
    )
    readings: dict[str, Any] = {}
    stages: dict[str, Any] = {}
    for member in ROOT_IDENTITY_SYNTHETIC_EXPERIMENT.members:
        materialized = by_case[member.case_ref]
        readings[member.variant] = SimpleNamespace(
            case_ref=member.case_ref,
            reading_ref=str(materialized["reading_ref"]),
            reading_hash=str(materialized["reading_hash"]),
        )
        stages[member.variant] = stage_service.project(
            account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
            subject_id=member.subject_id,
            stage_mode=MingliStageMode.NATAL_4,
            pinned_reading_ref=str(materialized["reading_ref"]),
            pinned_reading_hash=str(materialized["reading_hash"]),
        )

    SyntheticExperimentService._validate_sealed_members(
        experiment=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT,
        readings=readings,
        stages=stages,
    )
    wrong_b = SimpleNamespace(
        **{
            **readings["B"].__dict__,
            "case_ref": FIRST_SYNTHETIC_EXPERIMENT_MEMBERS[1].case_ref,
        }
    )
    with pytest.raises(
        SyntheticExperimentError,
        match="mingli_synthetic_experiment_member_reading_mismatch",
    ):
        SyntheticExperimentService._validate_sealed_members(
            experiment=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT,
            readings={**readings, "B": wrong_b},
            stages=stages,
        )
    with pytest.raises(
        SyntheticExperimentError,
        match="mingli_synthetic_experiment_sealed_stage_mismatch",
    ):
        SyntheticExperimentService._validate_sealed_members(
            experiment=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT,
            readings=readings,
            stages={
                **stages,
                "B": stages["B"].model_copy(
                    update={"subject_id": ROOT_IDENTITY_SYNTHETIC_EXPERIMENT.members[0].subject_id}
                ),
            },
        )


def test_first_pair_packet_expands_source_capacity_and_has_expected_controls() -> None:
    _, packets = _seed_and_packets()
    a_packet, b_packet = packets["A"], packets["B"]

    assert a_packet.packet_version == "v60.mingli-agent-case-packet.003"
    assert [item.pillar for item in a_packet.pillars] == ["丙戌", "戊戌", "甲戌", "己巳"]
    assert [item.pillar for item in b_packet.pillars] == ["丙戌", "戊戌", "甲戌", "丙寅"]
    assert a_packet.day_master_support.same_element_hidden_support == ()
    assert b_packet.day_master_support.same_element_hidden_support == ("hour支藏甲",)
    assert max(len(item.source_refs) for item in a_packet.evidence_catalog) == 27
    prompt_length = len(canonical_json(a_packet.model_prompt_view()))
    assert 18000 < prompt_length <= MINGLI_AGENT_PROMPT_VIEW_MAX_CHARS
    assert a_packet.timing_analysis_date == b_packet.timing_analysis_date == "2026-08-02"

    method = b_packet.model_prompt_view()["professional_adjudication"]["day_master_regime_method"]
    root = method["root_candidate_assessments"][0]
    assert root == {
        "coordinate": "hour支藏甲",
        "identity_match": "EXACT_DAY_MASTER",
        "hidden_order": 1,
        "hidden_rank": "PRIMARY_QI",
        "branch": "寅",
        "relation_competition_evidence_ids": (),
        "minimum_anti_follow_gate": "PRESENT",
        "gate_reason": (
            "日主同字位于该支第一藏干，且该支没有准入的原局冲合成员关系；"
            "仅在阻断直接从势的窄范围内，最低有效根成立。"
        ),
    }
    assert "DAY_MASTER_STRONG" in method["minimum_anti_follow_scope"]["does_not_prove"]


def test_root_identity_pair_distinguishes_candidate_identity_without_overclaim() -> None:
    _, packets = _seed_root_identity_and_packets()
    a_packet, b_packet = packets["A"], packets["B"]
    assert [item.pillar for item in a_packet.pillars] == [
        "己巳",
        "己巳",
        "甲午",
        "丁卯",
    ]
    assert [item.pillar for item in b_packet.pillars] == [
        "己巳",
        "己巳",
        "甲午",
        "丙寅",
    ]
    assert a_packet.day_master_support.same_element_hidden_support == ("hour支藏乙",)
    assert a_packet.day_master_support.same_identity_hidden_support == ()
    assert b_packet.day_master_support.same_element_hidden_support == ("hour支藏甲",)
    assert b_packet.day_master_support.same_identity_hidden_support == ("hour支藏甲",)
    assessments = {
        variant: root_candidate_assessments(
            day_master_stem=packet.day_master_stem,
            pillars=packet.pillars,
            same_element_candidates=(packet.day_master_support.same_element_hidden_support),
            same_identity_candidates=(packet.day_master_support.same_identity_hidden_support),
            natal_relations=packet.natal_relations,
        )[0]
        for variant, packet in packets.items()
    }
    assert assessments["A"]["identity_match"] == "SAME_ELEMENT_DIFFERENT_STEM"
    assert assessments["A"]["hidden_rank"] == "PRIMARY_QI"
    assert assessments["A"]["minimum_anti_follow_gate"] == "NOT_DETERMINED"
    assert assessments["B"]["identity_match"] == "EXACT_DAY_MASTER"
    assert assessments["B"]["hidden_rank"] == "PRIMARY_QI"
    assert assessments["B"]["minimum_anti_follow_gate"] == "PRESENT"
    assert all(item["relation_competition_evidence_ids"] == () for item in assessments.values())


def test_same_element_different_stem_whole_chart_verdict_is_not_erased() -> None:
    _, packets = _seed_root_identity_and_packets()
    a_packet = packets["A"]
    issues: set[str] = set()
    normalized = normalize_regime_decision(
        {
            "method_asset_ref": "REGIME_WEAK_VS_FOLLOW_TREND_001",
            "classification": "ORDINARY_WEAK",
            "effective_root_status": "PRESENT",
            "effective_root_coordinates": ["hour支藏乙"],
            "rooted_visible_support_status": "ABSENT",
            "dominant_chain_status": "UNRESOLVED",
            "competition_kinds": [],
            "evidence_ids": [a_packet.day_master_support.evidence_id],
        },
        packet=a_packet,
        day_master_state="WEAK",
        normalization_issues=issues,
    )
    assert normalized["effective_root_status"] == "PRESENT"
    assert normalized["effective_root_coordinates"] == ["hour支藏乙"]
    assert normalized["classification"] == "ORDINARY_WEAK"
    assert issues == set()


def test_minimum_anti_follow_gate_promotes_only_high_certainty_primary_root() -> None:
    _, packets = _seed_and_packets()
    issues: set[str] = set()
    normalized = normalize_regime_decision(
        {
            "method_asset_ref": "REGIME_WEAK_VS_FOLLOW_TREND_001",
            "classification": "UNRESOLVED",
            "effective_root_status": "UNRESOLVED",
            "effective_root_coordinates": [],
            "rooted_visible_support_status": "ABSENT",
            "dominant_chain_status": "UNRESOLVED",
            "competition_kinds": [],
            "evidence_ids": [packets["B"].day_master_support.evidence_id],
        },
        packet=packets["B"],
        day_master_state="WEAK",
        normalization_issues=issues,
    )

    assert normalized["effective_root_status"] == "PRESENT"
    assert normalized["effective_root_coordinates"] == ["hour支藏甲"]
    assert normalized["classification"] == "ORDINARY_WEAK"
    assert issues == {
        "DAY_MASTER_EFFECTIVE_ROOT_GATE",
        "DAY_MASTER_REGIME",
    }

    prose = {
        "day_master_state": "WEAK",
        "day_master_rationale": "时支只有一处微弱甲木余气，所以暂时保留未决。",
    }
    reconcile_day_master_state(
        prose,
        classification="ORDINARY_WEAK",
        packet=packets["B"],
        normalization_issues=issues,
    )
    assert "余气" not in prose["day_master_rationale"]
    assert "时支寅的第一藏干甲与日主同字" in prose["day_master_rationale"]
    assert "按普通身弱" in prose["day_master_rationale"]
    assert "DAY_MASTER_ROOT_RANK" in issues

    residual = root_candidate_assessments(
        day_master_stem="甲",
        pillars=(
            SimpleNamespace(
                slot="hour",
                branch="寅",
                hidden_stems=("丙", "戊", "甲"),
            ),
        ),
        same_element_candidates=("hour支藏甲",),
        same_identity_candidates=("hour支藏甲",),
        natal_relations=(),
    )
    clashed = root_candidate_assessments(
        day_master_stem="甲",
        pillars=(
            SimpleNamespace(
                slot="hour",
                branch="寅",
                hidden_stems=("甲", "丙", "戊"),
            ),
        ),
        same_element_candidates=("hour支藏甲",),
        same_identity_candidates=("hour支藏甲",),
        natal_relations=(
            SimpleNamespace(
                relation_type="six_clash_membership",
                left_slot="hour",
                right_slot="year",
                evidence_id="E006",
            ),
        ),
    )
    assert residual[0]["minimum_anti_follow_gate"] == "NOT_DETERMINED"
    assert clashed[0]["minimum_anti_follow_gate"] == "NOT_DETERMINED"
    assert clashed[0]["relation_competition_evidence_ids"] == ("E006",)


def test_minimum_anti_follow_gate_does_not_turn_uncertain_state_into_weak() -> None:
    _, packets = _seed_and_packets()
    issues: set[str] = set()
    normalized = normalize_regime_decision(
        {
            "method_asset_ref": "REGIME_WEAK_VS_FOLLOW_TREND_001",
            "classification": "UNRESOLVED",
            "effective_root_status": "UNRESOLVED",
            "effective_root_coordinates": [],
            "rooted_visible_support_status": "ABSENT",
            "dominant_chain_status": "UNRESOLVED",
            "competition_kinds": [],
            "evidence_ids": [packets["B"].day_master_support.evidence_id],
        },
        packet=packets["B"],
        day_master_state="UNCERTAIN",
        normalization_issues=issues,
    )
    prose = {
        "day_master_state": "UNCERTAIN",
        "day_master_rationale": "寅中甲根已经出现，但全盘强弱仍待比较。",
    }
    reconcile_day_master_state(
        prose,
        classification=normalized["classification"],
        packet=packets["B"],
        normalization_issues=issues,
    )

    assert normalized["effective_root_status"] == "PRESENT"
    assert normalized["classification"] == "UNRESOLVED"
    assert prose["day_master_state"] == "UNCERTAIN"
    assert "这只排除直接从势，强弱仍须继续比较" in prose["day_master_rationale"]


def test_evaluator_separates_experiment_invalidity_from_model_failure() -> None:
    _, packets = _seed_and_packets()
    passing = evaluate_synthetic_experiment(
        experiment=FIRST_SYNTHETIC_EXPERIMENT,
        readings=_passing_readings(),
        packets=packets,
    )
    reordered = packets["B"].model_copy(
        update={"mechanism_observations": tuple(reversed(packets["B"].mechanism_observations))}
    )
    reordered_result = evaluate_synthetic_experiment(
        experiment=FIRST_SYNTHETIC_EXPERIMENT,
        readings=_passing_readings(),
        packets={**packets, "B": reordered},
    )
    date_drift = packets["B"].model_copy(update={"timing_analysis_date": "2026-08-03"})
    no_root_support = packets["B"].day_master_support.model_copy(
        update={
            "same_identity_hidden_support": (),
            "same_element_hidden_support": (),
        }
    )
    root_compiler_drift = packets["B"].model_copy(update={"day_master_support": no_root_support})
    month_hold_drift = packets["B"].model_copy(update={"month_command_branch": "辰"})

    assert passing["outcome"] == "PASS"
    assert reordered_result["outcome"] == "PASS"
    assert (
        evaluate_synthetic_experiment(
            experiment=FIRST_SYNTHETIC_EXPERIMENT,
            readings=_passing_readings(),
            packets={**packets, "B": date_drift},
        )["outcome"]
        == "INVALID_EXPERIMENT"
    )
    invalid_root = evaluate_synthetic_experiment(
        experiment=FIRST_SYNTHETIC_EXPERIMENT,
        readings=_passing_readings(),
        packets={**packets, "B": root_compiler_drift},
    )
    assert invalid_root["outcome"] == "INVALID_EXPERIMENT"
    assert (
        next(item for item in invalid_root["checks"] if item["check_ref"] == "ROOT_CANDIDATE_FLIP")[
            "group"
        ]
        == "EXPERIMENT_VALIDITY"
    )
    assert (
        evaluate_synthetic_experiment(
            experiment=FIRST_SYNTHETIC_EXPERIMENT,
            readings=_passing_readings(issues=("DAY_MASTER_REGIME",)),
            packets=packets,
        )["outcome"]
        == "PRODUCT_SAFE_MODEL_FAIL"
    )
    hold_invalid = evaluate_synthetic_experiment(
        experiment=FIRST_SYNTHETIC_EXPERIMENT,
        readings=_passing_readings(),
        packets={**packets, "B": month_hold_drift},
    )
    assert hold_invalid["outcome"] == "INVALID_EXPERIMENT"
    assert hold_invalid["drift_checks"] == ["MONTH_COMMAND_HOLD"]
    assert SyntheticExperimentEvaluation.model_validate(hold_invalid).outcome == (
        "INVALID_EXPERIMENT"
    )


def test_root_identity_evaluator_scores_only_the_natal_minimum_gate() -> None:
    _, packets = _seed_root_identity_and_packets()
    passing = evaluate_synthetic_experiment(
        experiment=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT,
        readings=_passing_root_identity_readings(),
        packets=packets,
    )
    whole_chart_a_present = evaluate_synthetic_experiment(
        experiment=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT,
        readings=_passing_root_identity_readings(a_status="PRESENT"),
        packets=packets,
    )
    wrong_a = evaluate_synthetic_experiment(
        experiment=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT,
        readings=_passing_root_identity_readings(a_status="ABSENT"),
        packets=packets,
    )
    wrong_b = evaluate_synthetic_experiment(
        experiment=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT,
        readings=_passing_root_identity_readings(b_status="UNRESOLVED"),
        packets=packets,
    )
    month_drift = packets["B"].model_copy(update={"month_command_branch": "辰"})

    assert passing["outcome"] == "PASS"
    assert whole_chart_a_present["outcome"] == "PASS"
    assert passing["changed_pass_count"] == 3
    assert passing["hold_pass_count"] == 4
    assert {
        item["check_ref"] for item in passing["checks"] if item["group"] == "EXPERIMENT_VALIDITY"
    } >= {"ROOT_IDENTITY_CONTRAST", "MINIMUM_GATE_CONTRAST"}
    assert wrong_a["outcome"] == "MODEL_FAIL"
    assert wrong_b["outcome"] == "MODEL_FAIL"
    invalid = evaluate_synthetic_experiment(
        experiment=ROOT_IDENTITY_SYNTHETIC_EXPERIMENT,
        readings=_passing_root_identity_readings(),
        packets={**packets, "B": month_drift},
    )
    assert invalid["outcome"] == "INVALID_EXPERIMENT"
    assert invalid["drift_checks"] == ["MONTH_COMMAND_HOLD"]
    assert all(item["check_ref"] != "TIMING_COORDINATES_HOLD" for item in passing["checks"])
    assert SyntheticExperimentEvaluation.model_validate(passing).dev_gold_version == (
        "v60.mingli-synthetic-experiment-dev-gold.003"
    )


def test_hidden_rank_pairs_lock_rank_facts_without_inventing_rank_weights() -> None:
    primary_secondary_packets = _seed_experiment_and_packets(
        HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT
    )
    secondary_tertiary_packets = _seed_experiment_and_packets(
        HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT
    )
    primary_secondary = evaluate_synthetic_experiment(
        experiment=HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT,
        readings=_hidden_rank_readings(a_status="PRESENT", b_status="UNRESOLVED"),
        packets=primary_secondary_packets,
    )
    secondary_tertiary = evaluate_synthetic_experiment(
        experiment=HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT,
        readings=_hidden_rank_readings(a_status="PRESENT", b_status="UNRESOLVED"),
        packets=secondary_tertiary_packets,
    )

    assert primary_secondary["outcome"] == "PASS"
    assert secondary_tertiary["outcome"] == "PASS"
    assert primary_secondary["changed_pass_count"] == 4
    assert secondary_tertiary["changed_pass_count"] == 4
    assert primary_secondary["hold_pass_count"] == 3
    assert secondary_tertiary["hold_pass_count"] == 3
    assert all(
        item["status"] == "PASS"
        for evaluation in (primary_secondary, secondary_tertiary)
        for item in evaluation["checks"]
    )
    rank_facts = next(
        item
        for item in primary_secondary["checks"]
        if item["check_ref"] == "HIDDEN_RANK_GATE_FACTS"
    )
    assert (rank_facts["A"]["branch"], rank_facts["A"]["hidden_order"]) == (
        "卯",
        1,
    )
    assert (rank_facts["B"]["branch"], rank_facts["B"]["hidden_order"]) == (
        "辰",
        2,
    )
    wrong_tertiary = evaluate_synthetic_experiment(
        experiment=HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT,
        readings=_hidden_rank_readings(a_status="UNRESOLVED", b_status="ABSENT"),
        packets=secondary_tertiary_packets,
    )
    assert wrong_tertiary["outcome"] == "MODEL_FAIL"
    for a_status, b_status in (
        ("PRESENT", "PRESENT"),
        ("UNRESOLVED", "UNRESOLVED"),
        ("UNRESOLVED", "PRESENT"),
    ):
        allowed = evaluate_synthetic_experiment(
            experiment=HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT,
            readings=_hidden_rank_readings(
                a_status=a_status,
                b_status=b_status,
            ),
            packets=secondary_tertiary_packets,
        )
        assert allowed["outcome"] == "PASS"
    for a_status, b_status in (("ABSENT", "PRESENT"), ("PRESENT", "ABSENT")):
        rejected = evaluate_synthetic_experiment(
            experiment=HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT,
            readings=_hidden_rank_readings(
                a_status=a_status,
                b_status=b_status,
            ),
            packets=secondary_tertiary_packets,
        )
        assert rejected["outcome"] == "MODEL_FAIL"
    prose_overclaim = evaluate_synthetic_experiment(
        experiment=HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT,
        readings=_hidden_rank_readings(
            a_status="UNRESOLVED",
            b_status="UNRESOLVED",
            b_thesis="第三藏干权重极低，可视为无根。",
        ),
        packets=secondary_tertiary_packets,
    )
    assert prose_overclaim["outcome"] == "MODEL_FAIL"
    assert next(
        item
        for item in prose_overclaim["checks"]
        if item["check_ref"] == "HIDDEN_RANK_PROSE_WITHIN_SCOPE"
    )["B"] == ("FIXED_HIDDEN_RANK_WEIGHT", "RANK_ONLY_ROOT_INVALIDATION")
    scoped_prose = evaluate_synthetic_experiment(
        experiment=HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT,
        readings=_hidden_rank_readings(
            a_status="UNRESOLVED",
            b_status="UNRESOLVED",
            b_thesis="第三藏干不等于无根，也没有固定权重。",
        ),
        packets=secondary_tertiary_packets,
    )
    assert scoped_prose["outcome"] == "PASS"
    assert (
        SyntheticExperimentEvaluation.model_validate(secondary_tertiary).dev_gold_version
        == "v60.mingli-synthetic-experiment-dev-gold.004"
    )


@pytest.mark.parametrize(
    ("experiment", "variant", "prose"),
    (
        (HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT, "B", "未中藏有微弱比肩乙木。"),
        (HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT, "A", "卯中乙根系尚浅。"),
        (HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT, "A", "辰中乙无力，可忽略。"),
    ),
)
def test_hidden_rank_checker_catches_implicit_strength_shortcuts(
    experiment: Any,
    variant: str,
    prose: str,
) -> None:
    packets = _seed_experiment_and_packets(experiment)
    statuses = (
        ("PRESENT", "UNRESOLVED")
        if experiment is HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT
        else ("UNRESOLVED", "UNRESOLVED")
    )
    raw_theses = {"a_raw_thesis": None, "b_raw_thesis": None}
    raw_theses[f"{variant.lower()}_raw_thesis"] = prose
    evaluation = evaluate_synthetic_experiment(
        experiment=experiment,
        readings=_hidden_rank_readings(
            a_status=statuses[0],
            b_status=statuses[1],
            **raw_theses,
        ),
        packets=packets,
    )
    check = next(
        item
        for item in evaluation["checks"]
        if item["check_ref"] == "HIDDEN_RANK_PROSE_WITHIN_SCOPE"
    )

    assert evaluation["outcome"] == "MODEL_FAIL"
    assert check["status"] == "FAIL"


def test_hidden_rank_checker_preserves_explicitly_unresolved_strength_language() -> None:
    packets = _seed_experiment_and_packets(HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT)
    evaluation = evaluate_synthetic_experiment(
        experiment=HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT,
        readings=_hidden_rank_readings(
            a_status="UNRESOLVED",
            b_status="UNRESOLVED",
            b_thesis="日主整体偏弱，但辰中乙的根强弱尚未裁定。",
        ),
        packets=packets,
    )

    assert evaluation["outcome"] == "PASS"


def test_hidden_rank_unresolved_regime_can_be_model_complete_without_server_repair() -> None:
    packets = _seed_experiment_and_packets(HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT)
    for packet in packets.values():
        issues: set[str] = set()
        normalized = normalize_regime_decision(
            {
                "method_asset_ref": "REGIME_WEAK_VS_FOLLOW_TREND_001",
                "classification": "UNRESOLVED",
                "effective_root_status": "UNRESOLVED",
                "effective_root_coordinates": [],
                "rooted_visible_support_status": "ABSENT",
                "dominant_chain_status": "UNRESOLVED",
                "competition_kinds": ["HIDDEN_RESOURCE"],
                "evidence_ids": [packet.day_master_support.evidence_id],
            },
            packet=packet,
            day_master_state="WEAK",
            normalization_issues=issues,
        )

        assert normalized["effective_root_status"] == "UNRESOLVED"
        assert normalized["rooted_visible_support_status"] == "ABSENT"
        assert normalized["competition_kinds"] == ["HIDDEN_RESOURCE"]
        assert issues == set()


def test_hidden_rank_prompt_scaffolds_only_packet_legal_regime_and_method_slots() -> None:
    packets = _seed_experiment_and_packets(HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT)
    for packet in packets.values():
        adjudication = packet.model_prompt_view()["professional_adjudication"]
        regime = adjudication["output_field_contract"]["regime_decision"][
            "packet_specific_allowed_projections"
        ]
        by_status = {item["effective_root_status"]: item for item in regime["options"]}
        unresolved = by_status["UNRESOLVED"]
        scaffold = adjudication["candidate_method_cards"]["hypothesis_output_scaffold"]

        assert unresolved["effective_root_coordinates"] == ()
        assert unresolved["classification"] == "UNRESOLVED"
        assert unresolved["required_competition_kinds"] == ("HIDDEN_RESOURCE",)
        assert unresolved["forbidden_competition_kinds"] == ("VISIBLE_PEER",)
        assert unresolved["required_evidence_ids"] == (
            packet.day_master_support.evidence_id,
        )
        assert scaffold["mode"] == "FIXED_SLOTS_COPY_EXACTLY"
        for slot in scaffold["slots"]:
            assert all(
                ruling["method_card_ref"] == slot["method_card_ref"]
                for ruling in slot["method_rulings_exact_order"]
            )


def test_model_trace_projects_bounded_field_deltas_and_honest_legacy_state() -> None:
    deltas = (
        MingliAgentNormalizationDelta(
            stage="PROFESSIONAL_ADJUDICATION",
            path="/hypotheses",
            before_present=True,
            after_present=True,
            before=[{"long": "raw" * 1000}],
            after=[{"long": "normalized" * 1000}],
        ),
        MingliAgentNormalizationDelta(
            stage="PROFESSIONAL_ADJUDICATION",
            path="/regime_decision/effective_root_status",
            before_present=True,
            after_present=True,
            before="NONE",
            after="PRESENT",
        ),
    )
    receipt = SimpleNamespace(
        changes=deltas,
        receipt_ref="receipt:field-level",
        receipt_hash="a" * 64,
        raw_output_hash="b" * 64,
        normalized_output_hash="c" * 64,
        server_issue_keys=("DAY_MASTER_REGIME",),
    )
    field_trace = SyntheticExperimentService._model_trace(
        SimpleNamespace(
            normalization_receipt=receipt,
            agent_reading_ref="agent-reading:field-level",
        )
    )
    legacy_trace = SyntheticExperimentService._model_trace(
        SimpleNamespace(
            normalization_receipt=None,
            agent_reading_ref="agent-reading:legacy",
            output=SimpleNamespace(
                model_dump=lambda **_: {"server_issue_keys": []},
                server_issue_keys=(),
            ),
        )
    )

    assert field_trace["availability"] == "FIELD_LEVEL"
    assert field_trace["change_count"] == 2
    assert [item["path"] for item in field_trace["key_deltas"]] == [
        "/regime_decision/effective_root_status"
    ]
    assert legacy_trace["availability"] == "LEGACY_NOT_CAPTURED"
    assert legacy_trace["key_deltas"] == []
    assert "不会补造" in legacy_trace["limitation"]
