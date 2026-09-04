from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from abu_v60.mingli.agent_contracts import MingliAgentCasePacket
from abu_v60.mingli.agent_root_gate import packet_root_candidate_assessments
from abu_v60.mingli.synthetic_coordinate_discipline import (
    month_command_coordinate_violations,
)


def add_regime_work_path_checks(
    *,
    add: Any,
    gold: Mapping[str, object],
    packets: Mapping[str, MingliAgentCasePacket],
    a_output: Any,
    b_output: Any,
    hour_fact: Any,
    regime_value: Any,
    final_work_path_value: Any,
) -> None:
    """Evaluate whole-chart regime and final-path recompilation."""

    regimes = {"A": a_output.regime_decision, "B": b_output.regime_decision}
    assessments = {
        variant: packet_root_candidate_assessments(packets[variant]) for variant in ("A", "B")
    }
    add(
        "REGIME_PATH_HOUR_FACTS",
        "EXPERIMENT_VALIDITY",
        hour_fact(packets["A"]) == gold["A_hour_fact"]
        and hour_fact(packets["B"]) == gold["B_hour_fact"],
        "A／B 的合法时柱与十神、藏干必须精确等于冻结 Gold。",
        hour_fact(packets["A"]),
        hour_fact(packets["B"]),
    )
    add(
        "REGIME_PATH_SUPPORT_DELTA",
        "EXPECTED_CHANGE",
        not packets["A"].day_master_support.same_element_hidden_support
        and not packets["A"].day_master_support.visible_peer_support
        and not packets["A"].day_master_support.resource_support
        and packets["B"].day_master_support.same_element_hidden_support
        == (gold["B_candidate_coordinate"],)
        and not packets["B"].day_master_support.visible_peer_support,
        "A 必须保持无根、无比、无印；B 只按事实增加戌中戊根，印星不能冒充根。",
        packets["A"].day_master_support.model_dump(mode="json"),
        packets["B"].day_master_support.model_dump(mode="json"),
    )
    b_assessment = assessments["B"][0] if len(assessments["B"]) == 1 else {}
    add(
        "REGIME_PATH_MINIMUM_ROOT_GATE",
        "EXPECTED_CHANGE",
        not assessments["A"]
        and b_assessment.get("coordinate") == gold["B_candidate_coordinate"]
        and b_assessment.get("identity_match") == gold["B_candidate_identity"]
        and b_assessment.get("hidden_rank") == gold["B_hidden_rank"]
        and b_assessment.get("minimum_anti_follow_gate") == gold["B_minimum_anti_follow_gate"],
        "A 没有根候选；B 的戌中戊必须以同字、第一藏干执行最低阻从门。",
        assessments["A"],
        assessments["B"],
    )
    pattern_sets = {
        variant: tuple(item.pattern_ref for item in packets[variant].mechanism_observations)
        for variant in ("A", "B")
    }
    add(
        "REGIME_PATH_CANDIDATE_SETS",
        "EXPECTED_CHANGE",
        set(pattern_sets["A"]) == set(gold["A_expected_pattern_refs"])
        and set(pattern_sets["B"]) == set(gold["B_expected_pattern_refs"]),
        "结构候选必须随完整时柱重编译，但候选成员不等于机制已有效做功。",
        pattern_sets["A"],
        pattern_sets["B"],
    )
    add(
        "REGIME_PATH_TYPED_OUTCOMES",
        "EXPECTED_CHANGE",
        regimes["A"].effective_root_status == gold["A_required_effective_root_status"]
        and not regimes["A"].effective_root_coordinates
        and regimes["A"].classification in gold["A_allowed_regime_classifications"]
        and regimes["B"].effective_root_status == gold["B_required_effective_root_status"]
        and regimes["B"].effective_root_coordinates == (gold["B_candidate_coordinate"],)
        and regimes["B"].classification in gold["B_allowed_regime_classifications"],
        "A／B 必须执行各自有效根结果；Gold 不指定哪张机制卡胜出。",
        regime_value(regimes["A"]),
        regime_value(regimes["B"]),
    )
    final_work = {
        "A": final_work_path_value(a_output, packet=packets["A"]),
        "B": final_work_path_value(b_output, packet=packets["B"]),
    }
    add(
        "REGIME_PATH_FINAL_WORK_PATH_BINDING",
        "EXPECTED_CHANGE",
        bool(final_work["A"]["valid"] and final_work["B"]["valid"]),
        "最终主路径必须绑定唯一 PRIMARY、只引用原局证据，且受限首选不得伪装 CLOSED。",
        final_work["A"],
        final_work["B"],
    )


def add_month_command_regime_checks(
    *,
    add: Any,
    gold: Mapping[str, object],
    packets: Mapping[str, MingliAgentCasePacket],
    outputs: Mapping[str, Any],
    raw_outputs: Mapping[str, Any],
    hour_fact: Any,
    regime_value: Any,
    final_work_path_value: Any,
) -> None:
    """Evaluate month-command coordinates and whole-chart recomputation."""

    regimes = {variant: outputs[variant].regime_decision for variant in ("A", "B")}
    assessments = {
        variant: packet_root_candidate_assessments(packets[variant]) for variant in ("A", "B")
    }
    add(
        "MONTH_COMMAND_HOUR_FACTS",
        "EXPERIMENT_VALIDITY",
        all(hour_fact(packets[variant]) == gold[f"{variant}_hour_fact"] for variant in ("A", "B")),
        "壬水 A／B 的合法时柱、十神与完整藏干必须精确等于冻结 Gold。",
        hour_fact(packets["A"]),
        hour_fact(packets["B"]),
    )
    month_facts = {variant: _month_fact(packets[variant]) for variant in ("A", "B")}
    add(
        "MONTH_COMMAND_COORDINATE_FACTS",
        "EXPERIMENT_VALIDITY",
        all(
            month_facts[variant] == gold["month_fact"]
            and packets[variant].month_command_branch == gold["month_command_branch"]
            for variant in ("A", "B")
        ),
        "月令必须绑定月支卯及其藏干伤官；月干己正官只属于月干坐标。",
        {
            "month_command_branch": packets["A"].month_command_branch,
            "month_fact": month_facts["A"],
        },
        {
            "month_command_branch": packets["B"].month_command_branch,
            "month_fact": month_facts["B"],
        },
    )
    support = {variant: packets[variant].day_master_support for variant in ("A", "B")}
    add(
        "MONTH_COMMAND_SUPPORT_FACTS",
        "EXPERIMENT_VALIDITY",
        not support["A"].same_element_hidden_support
        and not support["A"].same_identity_hidden_support
        and support["B"].same_element_hidden_support == (gold["B_candidate_coordinate"],)
        and support["B"].same_identity_hidden_support == (gold["B_candidate_coordinate"],)
        and all(
            support[variant].visible_peer_support
            == gold[f"{variant}_expected_visible_peer_coordinates"]
            and support[variant].resource_support
            == gold[f"{variant}_expected_resource_coordinates"]
            for variant in ("A", "B")
        ),
        "根、明干同类与印星必须分开保存；A 只有印而无根，B 才新增亥中壬根。",
        support["A"].model_dump(mode="json"),
        support["B"].model_dump(mode="json"),
    )
    relation_memberships = {
        variant: tuple(
            (item.left_slot, item.right_slot, item.relation_type)
            for item in packets[variant].natal_relations
        )
        for variant in ("A", "B")
    }
    add(
        "MONTH_COMMAND_RELATION_COLLATERAL",
        "EXPERIMENT_VALIDITY",
        all(
            relation_memberships[variant] == gold[f"{variant}_expected_relation_memberships"]
            for variant in ("A", "B")
        ),
        "完整时柱造成的午支同支成员变化必须保存，且不得补造原局冲合。",
        relation_memberships["A"],
        relation_memberships["B"],
    )
    b_assessment = assessments["B"][0] if len(assessments["B"]) == 1 else {}
    add(
        "MONTH_COMMAND_MINIMUM_ROOT_GATE",
        "EXPECTED_CHANGE",
        not assessments["A"]
        and b_assessment.get("coordinate") == gold["B_candidate_coordinate"]
        and b_assessment.get("branch") == gold["B_candidate_branch"]
        and b_assessment.get("hidden_order") == gold["B_hidden_order"]
        and b_assessment.get("hidden_rank") == gold["B_hidden_rank"]
        and b_assessment.get("identity_match") == gold["B_candidate_identity"]
        and b_assessment.get("minimum_anti_follow_gate") == gold["B_minimum_anti_follow_gate"]
        and not b_assessment.get("relation_competition_evidence_ids"),
        "A 无根候选；B 的亥中壬必须按同字、第一藏干且无冲合竞争执行最低阻从门。",
        assessments["A"],
        assessments["B"],
    )
    pattern_sets = {
        variant: tuple(item.pattern_ref for item in packets[variant].mechanism_observations)
        for variant in ("A", "B")
    }
    add(
        "MONTH_COMMAND_CANDIDATE_SETS",
        "EXPECTED_CHANGE",
        all(
            set(pattern_sets[variant]) == set(gold[f"{variant}_expected_pattern_refs"])
            for variant in ("A", "B")
        ),
        "结构候选必须随完整时柱重编译；Gold 只冻结候选全集，不指定胜者。",
        pattern_sets["A"],
        pattern_sets["B"],
    )
    add(
        "MONTH_COMMAND_TYPED_REGIME",
        "EXPECTED_CHANGE",
        all(
            _month_command_regime_allowed(variant=variant, regime=regimes[variant], gold=gold)
            for variant in ("A", "B")
        ),
        "A 无根有印只能走假从竞争或未决；B 取得最低根后必须退出直接从势。",
        regime_value(regimes["A"]),
        regime_value(regimes["B"]),
    )
    final_work = {
        variant: final_work_path_value(outputs[variant], packet=packets[variant])
        for variant in ("A", "B")
    }
    add(
        "MONTH_COMMAND_FINAL_WORK_PATH_BINDING",
        "EXPECTED_CHANGE",
        all(final_work[variant]["valid"] for variant in ("A", "B")),
        "最终做功路径必须绑定模型选出的唯一 PRIMARY，Gold 不指定哪张机制卡胜出。",
        final_work["A"],
        final_work["B"],
    )
    violations = {
        variant: {
            "raw": month_command_coordinate_violations(
                raw_outputs[variant], packet=packets[variant]
            ),
            "normalized": month_command_coordinate_violations(
                outputs[variant],
                packet=packets[variant],
            ),
        }
        for variant in ("A", "B")
    }
    add(
        "MONTH_COMMAND_PROSE_COORDINATES_SEPARATED",
        "EXPECTED_CHANGE",
        all(not value["raw"] and not value["normalized"] for value in violations.values()),
        "模型原文和规范化文本都不得把月干己或其正官标签直接说成月令。",
        violations["A"],
        violations["B"],
    )


def _month_command_regime_allowed(
    *,
    variant: str,
    regime: Any,
    gold: Mapping[str, object],
) -> bool:
    if (
        regime.effective_root_status != gold[f"{variant}_required_effective_root_status"]
        or regime.effective_root_coordinates
        != gold[f"{variant}_required_effective_root_coordinates"]
        or regime.rooted_visible_support_status
        != gold[f"{variant}_required_rooted_visible_support_status"]
        or regime.competition_kinds != gold[f"{variant}_required_competition_kinds"]
        or regime.classification not in gold[f"{variant}_allowed_regime_classifications"]
    ):
        return False
    if variant == "A":
        if regime.dominant_chain_status == "CLOSED":
            return regime.classification == "FALSE_FOLLOW_COMPETITION"
        return regime.classification == "UNRESOLVED"
    return True


def _month_fact(packet: MingliAgentCasePacket) -> tuple[object, ...]:
    month = next(item for item in packet.pillars if item.slot == "month")
    return (
        month.pillar,
        month.visible_ten_god,
        month.hidden_stems,
        month.hidden_ten_gods,
    )
