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
    FIRST_SYNTHETIC_EXPERIMENT_MEMBERS,
    SYNTHETIC_EXPERIMENT_ANALYSIS_DATE,
    SYNTHETIC_RESEARCH_ACCOUNT_REF,
    resolve_research_stage_subject,
    synthetic_experiment_public_definition,
)
from abu_v60.mingli.synthetic_experiment_contracts import (
    SyntheticExperimentEvaluation,
)
from abu_v60.mingli.synthetic_experiment_seed import (
    seed_first_synthetic_experiment,
)
from abu_v60.mingli.synthetic_experiment_service import (
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


def test_schema_metadata_matches_synthetic_run_table() -> None:
    actual = {
        item["name"]
        for item in inspect(engine).get_columns(
            "synthetic_experiment_runs",
            schema="mingli",
        )
    }
    assert actual == set(mingli_synthetic_experiment_runs.c.keys())


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
        profiles = connection.execute(
            text(
                """
                    SELECT input_json
                FROM identity.profiles
                WHERE account_ref = :account_ref
                ORDER BY profile_ref
                """
            ),
            {"account_ref": SYNTHETIC_RESEARCH_ACCOUNT_REF},
        ).scalars().all()
    assert len(profiles) == 2
    assert all(payload["gold_in_profile"] is False for payload in profiles)
    assert all(
        "effective_root_status" not in str(payload)
        and "regime_classification" not in str(payload)
        for payload in profiles
    )


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

    method = b_packet.model_prompt_view()["professional_adjudication"][
        "day_master_regime_method"
    ]
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
    assert "DAY_MASTER_STRONG" in method["minimum_anti_follow_scope"][
        "does_not_prove"
    ]


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
    passing = SyntheticExperimentService._evaluate(
        readings=_passing_readings(),
        packets=packets,
    )
    reordered = packets["B"].model_copy(
        update={
            "mechanism_observations": tuple(
                reversed(packets["B"].mechanism_observations)
            )
        }
    )
    reordered_result = SyntheticExperimentService._evaluate(
        readings=_passing_readings(),
        packets={**packets, "B": reordered},
    )
    date_drift = packets["B"].model_copy(
        update={"timing_analysis_date": "2026-08-03"}
    )
    no_root_support = packets["B"].day_master_support.model_copy(
        update={
            "same_identity_hidden_support": (),
            "same_element_hidden_support": (),
        }
    )
    root_compiler_drift = packets["B"].model_copy(
        update={"day_master_support": no_root_support}
    )
    month_hold_drift = packets["B"].model_copy(
        update={"month_command_branch": "辰"}
    )

    assert passing["outcome"] == "PASS"
    assert reordered_result["outcome"] == "PASS"
    assert SyntheticExperimentService._evaluate(
        readings=_passing_readings(),
        packets={**packets, "B": date_drift},
    )["outcome"] == "INVALID_EXPERIMENT"
    invalid_root = SyntheticExperimentService._evaluate(
        readings=_passing_readings(),
        packets={**packets, "B": root_compiler_drift},
    )
    assert invalid_root["outcome"] == "INVALID_EXPERIMENT"
    assert next(
        item for item in invalid_root["checks"] if item["check_ref"] == "ROOT_CANDIDATE_FLIP"
    )["group"] == "EXPERIMENT_VALIDITY"
    assert SyntheticExperimentService._evaluate(
        readings=_passing_readings(issues=("DAY_MASTER_REGIME",)),
        packets=packets,
    )["outcome"] == "PRODUCT_SAFE_MODEL_FAIL"
    hold_invalid = SyntheticExperimentService._evaluate(
        readings=_passing_readings(),
        packets={**packets, "B": month_hold_drift},
    )
    assert hold_invalid["outcome"] == "INVALID_EXPERIMENT"
    assert hold_invalid["drift_checks"] == ["MONTH_COMMAND_HOLD"]
    assert SyntheticExperimentEvaluation.model_validate(hold_invalid).outcome == (
        "INVALID_EXPERIMENT"
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
