from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from abu_v60.mingli.agent_contracts import (
    MingliAgentCasePacket,
    MingliAgentReadingEnvelope,
)
from abu_v60.mingli.agent_root_gate import packet_root_candidate_assessments
from abu_v60.mingli.synthetic_experiment_catalog import (
    FIRST_SYNTHETIC_EXPERIMENT_REF,
    ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF,
    SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION,
    SyntheticExperimentDefinition,
)
from abu_v60.mingli.synthetic_experiment_contracts import SyntheticExperimentOutcome
from abu_v60.mingli.synthetic_experiment_gold import synthetic_experiment_dev_gold


def evaluate_synthetic_experiment(
    *,
    experiment: SyntheticExperimentDefinition,
    readings: Mapping[str, MingliAgentReadingEnvelope],
    packets: Mapping[str, MingliAgentCasePacket],
) -> dict[str, Any]:
    a_output, b_output = readings["A"].output, readings["B"].output
    a_regime, b_regime = a_output.regime_decision, b_output.regime_decision
    if a_regime is None or b_regime is None:
        raise ValueError("mingli_synthetic_experiment_regime_missing")
    gold, gold_hash = synthetic_experiment_dev_gold(experiment.experiment_ref)
    checks: list[dict[str, Any]] = []

    def add(
        check_ref: str,
        group: str,
        passed: bool,
        statement: str,
        a_value: object,
        b_value: object,
    ) -> None:
        checks.append(
            {
                "check_ref": check_ref,
                "group": group,
                "status": "PASS" if passed else "FAIL",
                "statement": statement,
                "A": a_value,
                "B": b_value,
            }
        )

    _add_common_checks(
        add=add,
        experiment=experiment,
        packets=packets,
        include_mechanism_hold=(
            experiment.experiment_ref == FIRST_SYNTHETIC_EXPERIMENT_REF
        ),
        include_timing_hold=(
            experiment.experiment_ref == FIRST_SYNTHETIC_EXPERIMENT_REF
        ),
    )
    if experiment.experiment_ref == FIRST_SYNTHETIC_EXPERIMENT_REF:
        _add_first_pair_checks(
            add=add,
            gold=gold,
            packets=packets,
            a_output=a_output,
            b_output=b_output,
        )
    elif experiment.experiment_ref == ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF:
        _add_root_identity_checks(
            add=add,
            gold=gold,
            packets=packets,
            a_output=a_output,
            b_output=b_output,
        )
    else:
        raise ValueError("mingli_synthetic_experiment_evaluator_not_found")
    return _finalize(
        checks=checks,
        readings=readings,
        gold=gold,
        gold_hash=gold_hash,
    )


def _add_common_checks(
    *,
    add: Any,
    experiment: SyntheticExperimentDefinition,
    packets: Mapping[str, MingliAgentCasePacket],
    include_mechanism_hold: bool,
    include_timing_hold: bool,
) -> None:
    a_packet, b_packet = packets["A"], packets["B"]
    members = experiment.member_by_variant
    add(
        "LEGAL_HOUR_DELTA",
        "EXPERIMENT_VALIDITY",
        tuple(item.pillar for item in a_packet.pillars) == members["A"].expected_pillars
        and tuple(item.pillar for item in b_packet.pillars)
        == members["B"].expected_pillars
        and tuple(item.pillar for item in a_packet.pillars[:3])
        == tuple(item.pillar for item in b_packet.pillars[:3]),
        "两份命盘必须精确等于历法锁定的 A／B 四柱，且只有时柱位置不同。",
        [item.pillar for item in a_packet.pillars],
        [item.pillar for item in b_packet.pillars],
    )
    add(
        "PACKET_CONTEXT_BINDING",
        "EXPERIMENT_VALIDITY",
        a_packet.case_ref == members["A"].case_ref
        and b_packet.case_ref == members["B"].case_ref
        and a_packet.subject_kind == b_packet.subject_kind == "CANONICAL_SYNTHETIC"
        and a_packet.gender == b_packet.gender == "male"
        and a_packet.birth_timezone == b_packet.birth_timezone == "Asia/Shanghai"
        and a_packet.timing_analysis_date
        == b_packet.timing_analysis_date
        == experiment.analysis_date.isoformat(),
        "A／B 必须绑定各自实验 Case，并保持合成身份、性别、时区和分析日期一致。",
        _packet_context(a_packet),
        _packet_context(b_packet),
    )
    holds: list[tuple[str, str, object, object]] = [
        (
            "DAY_MASTER_HOLD",
            "日主必须保持。",
            a_packet.day_master_stem,
            b_packet.day_master_stem,
        ),
        (
            "MONTH_COMMAND_HOLD",
            "月令必须保持。",
            a_packet.month_command_branch,
            b_packet.month_command_branch,
        ),
        (
            "VISIBLE_PEERS_HOLD",
            "明干同类不得漂移。",
            a_packet.day_master_support.visible_peer_support,
            b_packet.day_master_support.visible_peer_support,
        ),
        (
            "RESOURCE_SUPPORT_HOLD",
            "印星生扶不得漂移。",
            a_packet.day_master_support.resource_support,
            b_packet.day_master_support.resource_support,
        ),
    ]
    if include_timing_hold:
        holds.append(
            (
                "TIMING_COORDINATES_HOLD",
                "固定分析日的大运与流年坐标不得漂移。",
                tuple(
                    (
                        item.layer,
                        item.pillar,
                        item.ten_god_label,
                        item.start_year,
                        item.end_year,
                    )
                    for item in a_packet.timing_coordinates
                ),
                tuple(
                    (
                        item.layer,
                        item.pillar,
                        item.ten_god_label,
                        item.start_year,
                        item.end_year,
                    )
                    for item in b_packet.timing_coordinates
                ),
            )
        )
    if include_mechanism_hold:
        holds.append(
            (
                "MECHANISM_SET_HOLD",
                "候选机制集合不得漂移。",
                tuple(sorted(item.pattern_ref for item in a_packet.mechanism_observations)),
                tuple(sorted(item.pattern_ref for item in b_packet.mechanism_observations)),
            )
        )
    for check_ref, statement, a_value, b_value in holds:
        add(check_ref, "MUST_HOLD", a_value == b_value, statement, a_value, b_value)


def _add_first_pair_checks(
    *,
    add: Any,
    gold: Mapping[str, object],
    packets: Mapping[str, MingliAgentCasePacket],
    a_output: Any,
    b_output: Any,
) -> None:
    a_packet, b_packet = packets["A"], packets["B"]
    a_regime, b_regime = a_output.regime_decision, b_output.regime_decision
    add(
        "ROOT_CANDIDATE_FLIP",
        "EXPERIMENT_VALIDITY",
        not a_packet.day_master_support.same_element_hidden_support
        and b_packet.day_master_support.same_element_hidden_support
        == ("hour支藏甲",),
        "根候选应从无变为寅中甲木主气坐标。",
        a_packet.day_master_support.same_element_hidden_support,
        b_packet.day_master_support.same_element_hidden_support,
    )
    add(
        "B_EFFECTIVE_ROOT",
        "EXPECTED_CHANGE",
        b_regime.effective_root_status == gold["B_effective_root_status"]
        and b_regime.effective_root_coordinates == gold["B_effective_root_coordinates"],
        "B 必须真正裁定新增根候选是否有效，不能只复述候选存在。",
        a_regime.effective_root_status,
        {
            "status": b_regime.effective_root_status,
            "coordinates": b_regime.effective_root_coordinates,
        },
    )
    add(
        "B_REGIME_EXIT_FOLLOW",
        "EXPECTED_CHANGE",
        b_regime.classification == gold["B_regime_classification"]
        and b_output.day_master_state == gold["B_required_day_master_state"],
        "B 的完整时柱证据支持有效根后，应退出从势并进入普通身弱工作判断；"
        "本实验不把变化单独归因于根气。",
        {
            "classification": a_regime.classification,
            "day_master_state": a_output.day_master_state,
        },
        {
            "classification": b_regime.classification,
            "day_master_state": b_output.day_master_state,
        },
    )
    add(
        "A_NO_FORCED_FOLLOW",
        "EXPECTED_CHANGE",
        a_regime.classification in gold["A_allowed_regime_classifications"],
        "A 无根不等于必须判从；主导链未闭合时允许保持未决。",
        a_regime.classification,
        b_regime.classification,
    )


def _add_root_identity_checks(
    *,
    add: Any,
    gold: Mapping[str, object],
    packets: Mapping[str, MingliAgentCasePacket],
    a_output: Any,
    b_output: Any,
) -> None:
    a_packet, b_packet = packets["A"], packets["B"]
    a_regime, b_regime = a_output.regime_decision, b_output.regime_decision
    assessments = {
        "A": packet_root_candidate_assessments(a_packet),
        "B": packet_root_candidate_assessments(b_packet),
    }
    a_assessment = assessments["A"][0] if len(assessments["A"]) == 1 else None
    b_assessment = assessments["B"][0] if len(assessments["B"]) == 1 else None
    add(
        "ROOT_IDENTITY_CONTRAST",
        "EXPERIMENT_VALIDITY",
        a_packet.day_master_support.same_element_hidden_support
        == (gold["A_candidate_coordinate"],)
        and not a_packet.day_master_support.same_identity_hidden_support
        and b_packet.day_master_support.same_element_hidden_support
        == (gold["B_candidate_coordinate"],)
        and b_packet.day_master_support.same_identity_hidden_support
        == (gold["B_candidate_coordinate"],),
        "两盘都必须只有一个木根候选，但 A 为同元素异字，B 为日主同字。",
        {
            "same_element": a_packet.day_master_support.same_element_hidden_support,
            "same_identity": a_packet.day_master_support.same_identity_hidden_support,
        },
        {
            "same_element": b_packet.day_master_support.same_element_hidden_support,
            "same_identity": b_packet.day_master_support.same_identity_hidden_support,
        },
    )
    add(
        "MINIMUM_GATE_CONTRAST",
        "EXPERIMENT_VALIDITY",
        a_assessment is not None
        and a_assessment["identity_match"] == gold["A_candidate_identity"]
        and a_assessment["minimum_anti_follow_gate"]
        == gold["A_minimum_anti_follow_gate"]
        and b_assessment is not None
        and b_assessment["identity_match"] == gold["B_candidate_identity"]
        and b_assessment["minimum_anti_follow_gate"]
        == gold["B_minimum_anti_follow_gate"],
        "最低阻从门必须区分同元素异字与日主同字，不能把两者自动等价。",
        a_assessment,
        b_assessment,
    )
    add(
        "A_DIFFERENT_STEM_IS_NOT_DISCARDED",
        "EXPECTED_CHANGE",
        a_regime.effective_root_status in gold["A_allowed_effective_root_statuses"]
        and (
            a_regime.effective_root_coordinates == (gold["A_candidate_coordinate"],)
            if a_regime.effective_root_status == "PRESENT"
            else not a_regime.effective_root_coordinates
        )
        and a_regime.classification in gold["A_allowed_regime_classifications"],
        "A 的卯中乙不满足最低同字门，但仍须交由整盘裁决；不得由窄门自动判成无效根。",
        {
            "status": a_regime.effective_root_status,
            "classification": a_regime.classification,
            "coordinates": a_regime.effective_root_coordinates,
        },
        {
            "status": b_regime.effective_root_status,
            "classification": b_regime.classification,
            "coordinates": b_regime.effective_root_coordinates,
        },
    )
    add(
        "B_EXACT_ROOT_PRESENT",
        "EXPECTED_CHANGE",
        b_regime.effective_root_status == gold["B_effective_root_status"]
        and b_regime.effective_root_coordinates == gold["B_effective_root_coordinates"],
        "B 的寅中甲满足同字、第一藏干且无准入冲合竞争，最低阻从有效根必须成立。",
        a_regime.effective_root_status,
        {
            "status": b_regime.effective_root_status,
            "coordinates": b_regime.effective_root_coordinates,
        },
    )
    add(
        "WHOLE_CHART_REGIME_NOT_OVERCLAIMED",
        "EXPECTED_CHANGE",
        a_regime.classification in gold["A_allowed_regime_classifications"]
        and b_regime.classification in gold["B_allowed_regime_classifications"],
        "本实验只裁定最低根门；B 可以退出直接从势，但不能由此强迫整盘身强结论。",
        a_regime.classification,
        b_regime.classification,
    )


def _finalize(
    *,
    checks: list[dict[str, Any]],
    readings: Mapping[str, MingliAgentReadingEnvelope],
    gold: Mapping[str, object],
    gold_hash: str,
) -> dict[str, Any]:
    issue_keys = {
        variant: list(readings[variant].output.server_issue_keys)
        for variant in ("A", "B")
    }
    validity_failed = any(
        item["status"] == "FAIL"
        and item["group"] in {"EXPERIMENT_VALIDITY", "MUST_HOLD"}
        for item in checks
    )
    model_failed = any(
        item["status"] == "FAIL" and item["group"] == "EXPECTED_CHANGE"
        for item in checks
    )
    outcome: SyntheticExperimentOutcome = (
        "INVALID_EXPERIMENT"
        if validity_failed
        else "PRODUCT_SAFE_MODEL_FAIL"
        if issue_keys["A"] or issue_keys["B"]
        else "MODEL_FAIL"
        if model_failed
        else "PASS"
    )
    return {
        "evaluator_version": SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION,
        "dev_gold_version": gold["gold_version"],
        "dev_gold_hash": gold_hash,
        "outcome": outcome,
        "checks": checks,
        "server_issue_keys": issue_keys,
        "changed_pass_count": sum(
            item["status"] == "PASS" and item["group"] == "EXPECTED_CHANGE"
            for item in checks
        ),
        "hold_pass_count": sum(
            item["status"] == "PASS" and item["group"] == "MUST_HOLD"
            for item in checks
        ),
        "drift_checks": [
            item["check_ref"]
            for item in checks
            if item["status"] == "FAIL" and item["group"] == "MUST_HOLD"
        ],
        "qualification_effect": gold["qualification_effect"],
        "summary": {
            "PASS": "本组开发实验通过，但只进入复核，不代表方法已取得资格。",
            "PRODUCT_SAFE_MODEL_FAIL": "服务端修正后产品没有越界，但模型原始判断尚未独立通过。",
            "MODEL_FAIL": "实验结构有效，但模型没有完成该变与保持的全部要求。",
            "INVALID_EXPERIMENT": "控制变量发生漂移，本轮结果不能用于评价模型。",
        }[outcome],
    }


def _packet_context(packet: MingliAgentCasePacket) -> dict[str, object]:
    return {
        "case_ref": packet.case_ref,
        "subject_kind": packet.subject_kind,
        "gender": packet.gender,
        "timezone": packet.birth_timezone,
        "analysis_date": packet.timing_analysis_date,
    }
