from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from typing import Any

from abu_v60.mingli.agent_contracts import (
    MingliAgentCasePacket,
    MingliAgentReadingEnvelope,
)
from abu_v60.mingli.agent_root_gate import packet_root_candidate_assessments
from abu_v60.mingli.synthetic_decision_integrity import (
    add_raw_decision_integrity_checks,
)
from abu_v60.mingli.synthetic_experiment_catalog import (
    FIRST_SYNTHETIC_EXPERIMENT_REF,
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT_REF,
    HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
    HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
    REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT_REF,
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
        include_mechanism_hold=(experiment.experiment_ref == FIRST_SYNTHETIC_EXPERIMENT_REF),
        include_timing_hold=(experiment.experiment_ref == FIRST_SYNTHETIC_EXPERIMENT_REF),
        include_resource_hold=(
            experiment.experiment_ref
            in {FIRST_SYNTHETIC_EXPERIMENT_REF, ROOT_IDENTITY_SYNTHETIC_EXPERIMENT_REF}
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
    elif experiment.experiment_ref in {
        HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
        HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
        HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT_REF,
    }:
        _add_hidden_rank_checks(
            add=add,
            gold=gold,
            packets=packets,
            a_output=a_output,
            b_output=b_output,
            raw_outputs={
                variant: _raw_provider_output(readings[variant])
                for variant in ("A", "B")
            },
        )
    elif experiment.experiment_ref == REGIME_WORK_PATH_GENERALIZATION_EXPERIMENT_REF:
        _add_regime_work_path_checks(
            add=add,
            gold=gold,
            packets=packets,
            a_output=a_output,
            b_output=b_output,
        )
    else:
        raise ValueError("mingli_synthetic_experiment_evaluator_not_found")
    add_raw_decision_integrity_checks(
        add=add,
        readings=readings,
        packets=packets,
    )
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
    include_resource_hold: bool,
) -> None:
    a_packet, b_packet = packets["A"], packets["B"]
    members = experiment.member_by_variant
    add(
        "LEGAL_HOUR_DELTA",
        "EXPERIMENT_VALIDITY",
        tuple(item.pillar for item in a_packet.pillars) == members["A"].expected_pillars
        and tuple(item.pillar for item in b_packet.pillars) == members["B"].expected_pillars
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
    ]
    if include_resource_hold:
        holds.append(
            (
                "RESOURCE_SUPPORT_HOLD",
                "印星生扶不得漂移。",
                a_packet.day_master_support.resource_support,
                b_packet.day_master_support.resource_support,
            )
        )
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
        and b_packet.day_master_support.same_element_hidden_support == ("hour支藏甲",),
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
        a_packet.day_master_support.same_element_hidden_support == (gold["A_candidate_coordinate"],)
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
        and a_assessment["minimum_anti_follow_gate"] == gold["A_minimum_anti_follow_gate"]
        and b_assessment is not None
        and b_assessment["identity_match"] == gold["B_candidate_identity"]
        and b_assessment["minimum_anti_follow_gate"] == gold["B_minimum_anti_follow_gate"],
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


def _add_regime_work_path_checks(
    *,
    add: Any,
    gold: Mapping[str, object],
    packets: Mapping[str, MingliAgentCasePacket],
    a_output: Any,
    b_output: Any,
) -> None:
    regimes = {"A": a_output.regime_decision, "B": b_output.regime_decision}
    assessments = {
        variant: packet_root_candidate_assessments(packets[variant])
        for variant in ("A", "B")
    }
    add(
        "REGIME_PATH_HOUR_FACTS",
        "EXPERIMENT_VALIDITY",
        _hour_fact(packets["A"]) == gold["A_hour_fact"]
        and _hour_fact(packets["B"]) == gold["B_hour_fact"],
        "A／B 的合法时柱与十神、藏干必须精确等于冻结 Gold。",
        _hour_fact(packets["A"]),
        _hour_fact(packets["B"]),
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
        and b_assessment.get("minimum_anti_follow_gate")
        == gold["B_minimum_anti_follow_gate"],
        "A 没有根候选；B 的戌中戊必须以同字、第一藏干执行最低阻从门。",
        assessments["A"],
        assessments["B"],
    )
    pattern_sets = {
        variant: tuple(
            item.pattern_ref for item in packets[variant].mechanism_observations
        )
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
        regimes["A"].effective_root_status
        == gold["A_required_effective_root_status"]
        and not regimes["A"].effective_root_coordinates
        and regimes["A"].classification in gold["A_allowed_regime_classifications"]
        and regimes["B"].effective_root_status
        == gold["B_required_effective_root_status"]
        and regimes["B"].effective_root_coordinates
        == (gold["B_candidate_coordinate"],)
        and regimes["B"].classification in gold["B_allowed_regime_classifications"],
        "A／B 必须执行各自有效根结果；Gold 不指定哪张机制卡胜出。",
        _regime_value(regimes["A"]),
        _regime_value(regimes["B"]),
    )
    final_work = {
        "A": _final_work_path_value(a_output, packet=packets["A"]),
        "B": _final_work_path_value(b_output, packet=packets["B"]),
    }
    add(
        "REGIME_PATH_FINAL_WORK_PATH_BINDING",
        "EXPECTED_CHANGE",
        bool(final_work["A"]["valid"] and final_work["B"]["valid"]),
        "最终主路径必须绑定唯一 PRIMARY、只引用原局证据，且受限首选不得伪装 CLOSED。",
        final_work["A"],
        final_work["B"],
    )


def _final_work_path_value(output: Any, *, packet: MingliAgentCasePacket) -> dict[str, object]:
    primaries = [item for item in output.hypotheses if item.role == "PRIMARY"]
    primary = primaries[0] if len(primaries) == 1 else None
    path = output.work_path
    natal_ids = {
        item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"
    }
    valid = bool(
        primary is not None
        and path.selected_hypothesis_id == primary.hypothesis_id
        and path.method_card_ref == primary.method_card_ref
        and set(path.evidence_ids).issubset(natal_ids)
        and len(path.transformation_codes) == len(set(path.transformation_codes))
        and (primary.adjudication == "SUPPORTED" or path.closure != "CLOSED")
    )
    return {
        "valid": valid,
        "primary": (
            None
            if primary is None
            else {
                "hypothesis_id": primary.hypothesis_id,
                "method_card_ref": primary.method_card_ref,
                "adjudication": primary.adjudication,
            }
        ),
        "work_path": {
            "selected_hypothesis_id": path.selected_hypothesis_id,
            "method_card_ref": path.method_card_ref,
            "closure": path.closure,
            "transformation_codes": path.transformation_codes,
            "evidence_ids": path.evidence_ids,
        },
    }


def _add_hidden_rank_checks(
    *,
    add: Any,
    gold: Mapping[str, object],
    packets: Mapping[str, MingliAgentCasePacket],
    a_output: Any,
    b_output: Any,
    raw_outputs: Mapping[str, Any],
) -> None:
    assessments = {
        variant: packet_root_candidate_assessments(packets[variant]) for variant in ("A", "B")
    }
    selected = {
        variant: values[0] if len(values) == 1 else None for variant, values in assessments.items()
    }
    add(
        "HIDDEN_RANK_FACT_CONTRAST",
        "EXPERIMENT_VALIDITY",
        all(
            packets[variant].day_master_support.same_element_hidden_support
            == (gold[f"{variant}_candidate_coordinate"],)
            and packets[variant].day_master_support.same_identity_hidden_support
            == (gold[f"{variant}_candidate_coordinate"],)
            for variant in ("A", "B")
        ),
        "两盘都必须只有一个日主同字根候选；坐标相同不代表支位与藏干顺序相同。",
        {
            "coordinate": packets["A"].day_master_support.same_identity_hidden_support,
            "pillar": packets["A"].pillars[-1].pillar,
        },
        {
            "coordinate": packets["B"].day_master_support.same_identity_hidden_support,
            "pillar": packets["B"].pillars[-1].pillar,
        },
    )
    add(
        "HIDDEN_RANK_GATE_FACTS",
        "EXPERIMENT_VALIDITY",
        all(
            selected[variant] is not None
            and selected[variant]["coordinate"] == gold[f"{variant}_candidate_coordinate"]
            and selected[variant]["branch"] == gold[f"{variant}_branch"]
            and selected[variant]["hidden_order"] == gold[f"{variant}_hidden_order"]
            and selected[variant]["hidden_rank"] == gold[f"{variant}_hidden_rank"]
            and selected[variant]["identity_match"] == "EXACT_DAY_MASTER"
            and selected[variant]["minimum_anti_follow_gate"]
            == gold[f"{variant}_minimum_anti_follow_gate"]
            for variant in ("A", "B")
        ),
        "Evaluator 必须同时核对坐标、支位、藏干顺序、位阶与最低门，不能只比较同名坐标。",
        selected["A"],
        selected["B"],
    )
    hour_facts = {variant: _hour_fact(packets[variant]) for variant in ("A", "B")}
    add(
        "HOUR_COLLATERAL_FACTS",
        "EXPERIMENT_VALIDITY",
        all(hour_facts[variant] == gold[f"{variant}_hour_fact"] for variant in ("A", "B")),
        "时干十神与完整藏干／十神序列必须保存；这些差异只作 collateral，不进入位阶因果评分。",
        hour_facts["A"],
        hour_facts["B"],
    )
    regimes = {
        "A": a_output.regime_decision,
        "B": b_output.regime_decision,
    }
    for variant in ("A", "B"):
        other = "B" if variant == "A" else "A"
        add(
            f"{variant}_HIDDEN_RANK_OUTCOME_WITHIN_SCOPE",
            "EXPECTED_CHANGE",
            _hidden_rank_outcome_allowed(
                variant=variant,
                gold=gold,
                regime=regimes[variant],
            ),
            (
                f"{variant} 的最低门结果必须被执行，但位阶本身不得被扩写为固定权重、"
                "无根或必然身强弱。"
            ),
            _regime_value(regimes[variant]),
            _regime_value(regimes[other]),
        )
    add(
        "HIDDEN_RANK_TYPED_REGIME_WITHIN_SCOPE",
        "EXPECTED_CHANGE",
        all(
            regimes[variant].classification in gold[f"{variant}_allowed_regime_classifications"]
            for variant in ("A", "B")
        ),
        "本组只裁定藏干位阶与最低根门；不得由此强迫整盘强弱、用神或吉凶结论。",
        regimes["A"].classification,
        regimes["B"].classification,
    )
    prose_violations = {
        variant: tuple(
            sorted(
                {
                    violation
                    for output in (
                        a_output if variant == "A" else b_output,
                        raw_outputs.get(variant),
                    )
                    if output is not None
                    for violation in _hidden_rank_prose_violations(
                        output,
                        packet=packets[variant],
                    )
                }
            )
        )
        for variant in ("A", "B")
    }
    add(
        "HIDDEN_RANK_PROSE_WITHIN_SCOPE",
        "EXPECTED_CHANGE",
        not prose_violations["A"] and not prose_violations["B"],
        "正文不得为藏干位阶编造固定强弱或权重，也不得仅凭位阶宣称无根、无效或不可用。",
        prose_violations["A"],
        prose_violations["B"],
    )


def _hidden_rank_outcome_allowed(
    *,
    variant: str,
    gold: Mapping[str, object],
    regime: Any,
) -> bool:
    required = gold.get(f"{variant}_required_effective_root_status")
    allowed = gold.get(f"{variant}_allowed_effective_root_statuses")
    status_allowed = (
        regime.effective_root_status == required
        if required is not None
        else regime.effective_root_status in allowed
    )
    coordinate = gold[f"{variant}_candidate_coordinate"]
    coordinates_allowed = (
        regime.effective_root_coordinates == (coordinate,)
        if regime.effective_root_status == "PRESENT"
        else not regime.effective_root_coordinates
    )
    return bool(
        status_allowed
        and coordinates_allowed
        and regime.classification in gold[f"{variant}_allowed_regime_classifications"]
    )


def _regime_value(regime: Any) -> dict[str, object]:
    return {
        "classification": regime.classification,
        "effective_root_status": regime.effective_root_status,
        "effective_root_coordinates": regime.effective_root_coordinates,
    }


def _hour_fact(packet: MingliAgentCasePacket) -> tuple[object, ...]:
    hour = packet.pillars[-1]
    return (
        hour.pillar,
        hour.visible_ten_god,
        hour.hidden_stems,
        hour.hidden_ten_gods,
    )


_RANK_MARKER = re.compile(
    r"第一藏干|第二藏干|第三藏干|主气位置|第二藏气|第三藏气|余气|末气"
)
_RANK_WEIGHT = re.compile(r"权重|占比|比例|百分|\d+(?:\.\d+)?\s*%")
_RANK_INVALIDITY = re.compile(r"无根|无效|不可用|不成根|可忽略|忽略不计")
_RANK_STRENGTH_SHORTCUT = re.compile(
    r"微弱|极弱|薄弱|根系?尚浅|根浅|无力|力弱"
)
_SAFE_SCOPE_MARKERS = (
    "不等于",
    "不能判",
    "不得判",
    "不可直接判",
    "并非",
    "不是",
    "不代表",
    "未必",
    "没有固定",
    "不设固定",
    "强弱尚未裁定",
    "强弱未定",
    "不能仅凭",
    "不可仅凭",
)


def _hidden_rank_prose_violations(
    output: Any,
    *,
    packet: MingliAgentCasePacket,
) -> tuple[str, ...]:
    violations: set[str] = set()
    assessments = packet_root_candidate_assessments(packet)
    if len(assessments) != 1:
        return ()
    assessment = assessments[0]
    coordinate = str(assessment["coordinate"])
    branch = str(assessment["branch"] or "")
    stem = coordinate.rsplit("藏", maxsplit=1)[-1]
    for sentence in re.split(r"[。！？；;\n]", _hidden_rank_reasoning_text(output)):
        candidate_linked = (
            bool(_RANK_MARKER.search(sentence))
            or coordinate in sentence
            or (
                bool(branch)
                and branch in sentence
                and stem in sentence
            )
            or (
                not packet.day_master_support.visible_peer_support
                and any(marker in sentence for marker in ("比肩", "劫财"))
                and bool(_RANK_STRENGTH_SHORTCUT.search(sentence))
            )
        )
        if not candidate_linked:
            continue
        safe_scope = any(marker in sentence for marker in _SAFE_SCOPE_MARKERS)
        if _RANK_WEIGHT.search(sentence) and not safe_scope:
            violations.add("FIXED_HIDDEN_RANK_WEIGHT")
        if _RANK_INVALIDITY.search(sentence) and not safe_scope:
            violations.add("RANK_ONLY_ROOT_INVALIDATION")
        if _RANK_STRENGTH_SHORTCUT.search(sentence) and not safe_scope:
            violations.add("RANK_ONLY_STRENGTH_SHORTCUT")
    return tuple(sorted(violations))


def _hidden_rank_reasoning_text(output: Any) -> str:
    if hasattr(output, "model_dump"):
        output = output.model_dump(mode="json")
    return "\n".join(_iter_text(output))


def _iter_text(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_text(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_text(item)
    elif hasattr(value, "__dict__"):
        yield from _iter_text(vars(value))


def _raw_provider_output(reading: MingliAgentReadingEnvelope) -> Any:
    receipt = getattr(reading, "normalization_receipt", None)
    return None if receipt is None else receipt.raw_output


def _finalize(
    *,
    checks: list[dict[str, Any]],
    readings: Mapping[str, MingliAgentReadingEnvelope],
    gold: Mapping[str, object],
    gold_hash: str,
) -> dict[str, Any]:
    issue_keys = {
        variant: list(readings[variant].output.server_issue_keys) for variant in ("A", "B")
    }
    validity_failed = any(
        item["status"] == "FAIL" and item["group"] in {"EXPERIMENT_VALIDITY", "MUST_HOLD"}
        for item in checks
    )
    model_failed = any(
        item["status"] == "FAIL" and item["group"] == "EXPECTED_CHANGE" for item in checks
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
            item["status"] == "PASS" and item["group"] == "EXPECTED_CHANGE" for item in checks
        ),
        "hold_pass_count": sum(
            item["status"] == "PASS" and item["group"] == "MUST_HOLD" for item in checks
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
