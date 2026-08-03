from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from abu_v60.mingli.agent_contracts import MingliAgentCasePacket
from abu_v60.mingli.agent_root_gate import packet_root_candidate_assessments


def add_decision_discipline_checks(
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
    """Evaluate the unseen whole-chart pair without preselecting its winner."""

    outputs = {"A": a_output, "B": b_output}
    regimes = {variant: outputs[variant].regime_decision for variant in ("A", "B")}
    assessments = {
        variant: packet_root_candidate_assessments(packets[variant]) for variant in ("A", "B")
    }
    add(
        "DECISION_DISCIPLINE_HOUR_FACTS",
        "EXPERIMENT_VALIDITY",
        all(hour_fact(packets[variant]) == gold[f"{variant}_hour_fact"] for variant in ("A", "B")),
        "庚金 A／B 的合法时柱、十神与完整藏干必须精确等于冻结 Gold。",
        hour_fact(packets["A"]),
        hour_fact(packets["B"]),
    )
    support_values = {variant: packets[variant].day_master_support for variant in ("A", "B")}
    add(
        "DECISION_DISCIPLINE_SUPPORT_FACTS",
        "EXPERIMENT_VALIDITY",
        not support_values["A"].same_identity_hidden_support
        and not support_values["A"].same_element_hidden_support
        and support_values["B"].same_identity_hidden_support == (gold["B_candidate_coordinate"],)
        and support_values["B"].same_element_hidden_support == (gold["B_candidate_coordinate"],)
        and all(
            support_values[variant].visible_peer_support
            == gold[f"{variant}_expected_visible_peer_coordinates"]
            and support_values[variant].resource_support
            == gold[f"{variant}_expected_resource_coordinates"]
            for variant in ("A", "B")
        ),
        "根、明干同类与藏印必须分开保存；A 藏印不能冒充根，B 只增加申中庚根。",
        support_values["A"].model_dump(mode="json"),
        support_values["B"].model_dump(mode="json"),
    )
    a_relations = tuple(item.relation_type for item in packets["A"].natal_relations)
    b_relations = tuple(item.relation_type for item in packets["B"].natal_relations)
    add(
        "DECISION_DISCIPLINE_RELATION_COLLATERAL",
        "EXPERIMENT_VALIDITY",
        a_relations == ("same_branch_membership",) and not b_relations,
        "A 的午午同支成员必须保存、B 必须消失；两盘均不得补造六冲或六合。",
        a_relations,
        b_relations,
    )
    b_assessment = assessments["B"][0] if len(assessments["B"]) == 1 else {}
    add(
        "DECISION_DISCIPLINE_MINIMUM_ROOT_GATE",
        "EXPECTED_CHANGE",
        not assessments["A"]
        and b_assessment.get("coordinate") == gold["B_candidate_coordinate"]
        and b_assessment.get("branch") == gold["B_candidate_branch"]
        and b_assessment.get("hidden_order") == gold["B_hidden_order"]
        and b_assessment.get("hidden_rank") == gold["B_hidden_rank"]
        and b_assessment.get("identity_match") == gold["B_candidate_identity"]
        and b_assessment.get("minimum_anti_follow_gate") == gold["B_minimum_anti_follow_gate"]
        and not b_assessment.get("relation_competition_evidence_ids"),
        "B 的申中庚必须按同字、第一藏干且无冲合竞争执行最低阻从门；A 无根候选。",
        assessments["A"],
        assessments["B"],
    )
    pattern_sets = {
        variant: tuple(item.pattern_ref for item in packets[variant].mechanism_observations)
        for variant in ("A", "B")
    }
    add(
        "DECISION_DISCIPLINE_CANDIDATE_UNIVERSE",
        "MUST_HOLD",
        all(
            set(pattern_sets[variant]) == set(gold[f"{variant}_expected_pattern_refs"])
            for variant in ("A", "B")
        )
        and set(pattern_sets["A"]) == set(pattern_sets["B"]),
        "A／B 必须保持同一组三张机制候选，Gold 不预选胜者或被排除卡。",
        pattern_sets["A"],
        pattern_sets["B"],
    )
    add(
        "DECISION_DISCIPLINE_TYPED_REGIME",
        "EXPECTED_CHANGE",
        _regime_allowed(variant="A", regime=regimes["A"], gold=gold)
        and _regime_allowed(variant="B", regime=regimes["B"], gold=gold),
        "A 无根但有藏印时必须在假从竞争或未决出口；B 有最低根后必须退出直接从势。",
        regime_value(regimes["A"]),
        regime_value(regimes["B"]),
    )
    partitions = {
        variant: _candidate_partition_value(outputs[variant], packets[variant])
        for variant in ("A", "B")
    }
    add(
        "DECISION_DISCIPLINE_CANDIDATE_PARTITION",
        "EXPECTED_CHANGE",
        all(partitions[variant]["valid"] for variant in ("A", "B")),
        "H1、H2 与排除账本必须不重不漏地分割三张候选，不能静默遗漏或重复排除。",
        partitions["A"],
        partitions["B"],
    )
    final_work = {
        variant: final_work_path_value(outputs[variant], packet=packets[variant])
        for variant in ("A", "B")
    }
    add(
        "DECISION_DISCIPLINE_FINAL_WORK_PATH_BINDING",
        "EXPECTED_CHANGE",
        all(final_work[variant]["valid"] for variant in ("A", "B")),
        "最终做功路径必须绑定模型选出的唯一 PRIMARY；Gold 不指定哪张机制卡胜出。",
        final_work["A"],
        final_work["B"],
    )


def _regime_allowed(*, variant: str, regime: Any, gold: Mapping[str, object]) -> bool:
    if regime.effective_root_status != gold[f"{variant}_required_effective_root_status"]:
        return False
    if regime.effective_root_coordinates != gold[f"{variant}_required_effective_root_coordinates"]:
        return False
    if (
        regime.rooted_visible_support_status
        != gold[f"{variant}_required_rooted_visible_support_status"]
        or regime.competition_kinds != gold[f"{variant}_required_competition_kinds"]
        or regime.classification not in gold[f"{variant}_allowed_regime_classifications"]
    ):
        return False
    if variant == "A":
        if regime.dominant_chain_status == "CLOSED":
            return regime.classification == "FALSE_FOLLOW_COMPETITION"
        return regime.classification == "UNRESOLVED"
    return regime.classification in gold["B_allowed_regime_classifications"]


def _candidate_partition_value(
    output: Any,
    packet: MingliAgentCasePacket,
) -> dict[str, object]:
    universe = {item.evidence_id for item in packet.mechanism_observations}
    selected = [item.method_card_ref for item in output.hypotheses]
    excluded = [item.method_card_ref for item in output.excluded_candidates]
    valid = bool(
        len(universe) == 3
        and len(selected) == 2
        and len(set(selected)) == 2
        and len(excluded) == 1
        and len(set(excluded)) == 1
        and set(selected).isdisjoint(excluded)
        and set(selected) | set(excluded) == universe
    )
    return {
        "valid": valid,
        "universe": tuple(sorted(universe)),
        "selected": tuple(selected),
        "excluded": tuple(excluded),
    }
