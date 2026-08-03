from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from abu_v60.mingli.agent_contracts import (
    MINGLI_AGENT_READING_VERSION,
    MingliAgentCasePacket,
    MingliAgentReadingEnvelope,
)
from abu_v60.mingli.agent_method_cards import (
    FALLBACK_METHOD_CARD_REF,
    method_card_catalog,
)


def add_raw_decision_integrity_checks(
    *,
    add: Any,
    readings: Mapping[str, MingliAgentReadingEnvelope],
    packets: Mapping[str, MingliAgentCasePacket],
) -> None:
    """Measure model-owned method and decision work before server repair."""

    for variant in ("A", "B"):
        reading = readings[variant]
        if getattr(reading, "agent_reading_version", None) != MINGLI_AGENT_READING_VERSION:
            continue
        raw = _raw_provider_output(reading)
        packet = packets[variant]
        cards = method_card_catalog(packet.mechanism_observations)
        candidate_refs = [item.evidence_id for item in packet.mechanism_observations]
        raw_hypotheses = (
            raw.get("hypotheses")
            if isinstance(raw, Mapping) and isinstance(raw.get("hypotheses"), list)
            else []
        )
        raw_method_refs = tuple(
            _string(item.get("method_card_ref")) if isinstance(item, Mapping) else None
            for item in (raw_hypotheses + [None, None])[:2]
        )
        model_selects_cards = len(candidate_refs) > 2
        selected_cards_are_distinct = bool(
            all(item is not None for item in raw_method_refs)
            and len(set(raw_method_refs)) == 2
        )
        method_integrity: list[bool] = []
        for index in range(2):
            item = raw_hypotheses[index] if index < len(raw_hypotheses) else None
            expected_ref = (
                raw_method_refs[index]
                if model_selects_cards
                else (
                    candidate_refs[index]
                    if index < len(candidate_refs)
                    else FALLBACK_METHOD_CARD_REF
                )
            )
            ref_is_admitted = bool(
                expected_ref in cards
                and (
                    not model_selects_cards
                    or (
                        expected_ref in candidate_refs
                        and selected_cards_are_distinct
                    )
                )
            )
            expected_identity = (
                [
                    (expected_ref, check_code)
                    for check_code in cards[str(expected_ref)]["required_checks"]
                ]
                if ref_is_admitted
                else []
            )
            actual_identity = (
                [
                    (
                        _string(ruling.get("method_card_ref")),
                        _string(ruling.get("check_code")),
                    )
                    for ruling in item.get("method_rulings", [])
                    if isinstance(ruling, Mapping)
                ]
                if isinstance(item, Mapping) and isinstance(item.get("method_rulings"), list)
                else []
            )
            passed = bool(
                isinstance(item, Mapping)
                and item.get("hypothesis_id") == f"H{index + 1}"
                and ref_is_admitted
                and _string(item.get("method_card_ref")) == expected_ref
                and actual_identity == expected_identity
            )
            method_integrity.append(passed)
            add(
                f"{variant}_RAW_METHOD_CARD_H{index + 1}_COMPLETE",
                "EXPECTED_CHANGE",
                passed,
                "模型原始输出必须按固定槽完整执行对应方法卡，不能依赖服务端补项。",
                {"expected": expected_identity, "actual": actual_identity},
                None,
            )

        raw_primary_items = [
            item
            for item in raw_hypotheses
            if isinstance(item, Mapping) and item.get("role") == "PRIMARY"
        ]
        raw_primary = raw_primary_items[0] if len(raw_primary_items) == 1 else None
        decision = raw.get("hypothesis_decision") if isinstance(raw, Mapping) else None
        raw_primary_id = (
            _string(raw_primary.get("hypothesis_id"))
            if isinstance(raw_primary, Mapping)
            else None
        )
        decision_winner_id = (
            _string(decision.get("winner_id")) if isinstance(decision, Mapping) else None
        )
        decision_loser_id = (
            _string(decision.get("loser_id")) if isinstance(decision, Mapping) else None
        )
        primary_selection_valid = bool(
            isinstance(raw_primary, Mapping) and raw_primary_id in {"H1", "H2"}
        )
        primary_coherent = bool(
            primary_selection_valid
            and isinstance(decision, Mapping)
            and decision_winner_id == raw_primary_id
            and decision_loser_id in ({"H1", "H2"} - {raw_primary_id})
        )
        add(
            f"{variant}_RAW_PRIMARY_DECISION_COHERENT",
            "EXPECTED_CHANGE",
            primary_coherent,
            "模型必须自己给出唯一 PRIMARY，且胜负回执与该主解释一致。",
            {
                "primary_id": raw_primary_id,
                "winner_id": decision_winner_id,
            },
            None,
        )

        selected_refs = {
            method_ref
            for item in raw_hypotheses
            if isinstance(item, Mapping)
            and (method_ref := _string(item.get("method_card_ref"))) in candidate_refs
        }
        expected_excluded = set(candidate_refs) - selected_refs
        excluded = raw.get("excluded_candidates") if isinstance(raw, Mapping) else None
        excluded_refs = (
            [
                _string(item.get("method_card_ref"))
                for item in excluded
                if isinstance(item, Mapping)
            ]
            if isinstance(excluded, list)
            else []
        )
        candidate_coverage = bool(
            all(item is not None for item in excluded_refs)
            and len(excluded_refs) == len(set(excluded_refs))
            and set(excluded_refs) == expected_excluded
        )
        add(
            f"{variant}_RAW_CANDIDATE_COVERAGE_COMPLETE",
            "EXPECTED_CHANGE",
            candidate_coverage,
            "前两条解释与 excluded ledger 合起来必须覆盖本盘全部候选。",
            {"expected_excluded": sorted(expected_excluded), "actual": excluded_refs},
            None,
        )

        work_path = raw.get("work_path") if isinstance(raw, Mapping) else None
        transformations = (
            work_path.get("transformation_codes") if isinstance(work_path, Mapping) else None
        )
        transformation_form = bool(
            isinstance(transformations, list)
            and transformations
            and len(transformations) <= 4
            and all(isinstance(item, str) for item in transformations)
            and len(transformations) == len(set(transformations))
            and set(transformations).issubset(
                {
                    "GENERATES",
                    "CONTROLS",
                    "SUPPORTS",
                    "CONSTRAINS",
                    "CHANNELS",
                    "COMPETES",
                }
            )
        )
        path_binding = bool(
            isinstance(raw_primary, Mapping)
            and isinstance(work_path, Mapping)
            and _string(work_path.get("selected_hypothesis_id")) == raw_primary_id
            and _string(work_path.get("method_card_ref"))
            == _string(raw_primary.get("method_card_ref"))
        )
        add(
            f"{variant}_RAW_WORK_PATH_PRIMARY_BINDING",
            "EXPECTED_CHANGE",
            path_binding and transformation_form,
            "模型原始主路径必须绑定原始 PRIMARY，并提交唯一且合法的转化动作。",
            work_path,
            None,
        )

        regime_coherent = _raw_regime_is_coherent(raw)
        add(
            f"{variant}_RAW_REGIME_STATE_COHERENT",
            "EXPECTED_CHANGE",
            regime_coherent,
            "模型原始日主状态与弱／从势子审计必须属于同一个合法状态组合。",
            {
                "day_master_state": (
                    raw.get("day_master_state") if isinstance(raw, Mapping) else None
                ),
                "regime_decision": (
                    raw.get("regime_decision") if isinstance(raw, Mapping) else None
                ),
            },
            None,
        )

        expected_issues: set[str] = set()
        expected_issues.update(
            f"HYPOTHESIS_H{index + 1}"
            for index, passed in enumerate(method_integrity)
            if not passed
        )
        if not primary_selection_valid:
            expected_issues.add("PRIMARY_SELECTION")
        if not primary_coherent:
            expected_issues.add("HYPOTHESIS_DECISION")
        if not candidate_coverage:
            expected_issues.add("CANDIDATE_COVERAGE")
        if not path_binding:
            expected_issues.add("WORK_PATH")
        if not transformation_form:
            expected_issues.add("WORK_PATH_FORM")
        if not regime_coherent:
            expected_issues.add("DAY_MASTER_REGIME")
        actual_issues = set(reading.output.server_issue_keys)
        add(
            f"{variant}_RAW_REPAIRS_RECEIPTED",
            "EXPECTED_CHANGE",
            expected_issues.issubset(actual_issues),
            "任何原始方法、主次、覆盖、路径或判型修复都必须留下可训练回执。",
            sorted(expected_issues),
            sorted(actual_issues),
        )


def _raw_regime_is_coherent(raw: object) -> bool:
    if not isinstance(raw, Mapping):
        return False
    state = _string(raw.get("day_master_state"))
    regime = raw.get("regime_decision")
    if not isinstance(regime, Mapping):
        return False
    classification = _string(regime.get("classification"))
    root = _string(regime.get("effective_root_status"))
    rooted_support = _string(regime.get("rooted_visible_support_status"))
    if state in {"STRONG", "BALANCED", "SPECIALIZED_TENDENCY"}:
        return classification == "NON_WEAK_OUTSIDE_SCOPE"
    if classification == "ORDINARY_WEAK":
        return state == "WEAK" and (
            root == "PRESENT" or rooted_support == "PRESENT"
        )
    if classification == "FOLLOW_TREND":
        return bool(
            state == "FOLLOWING_TENDENCY"
            and root == rooted_support == "ABSENT"
            and regime.get("dominant_chain_status") == "CLOSED"
            and not regime.get("competition_kinds")
        )
    if classification == "FALSE_FOLLOW_COMPETITION":
        return bool(
            state in {"WEAK", "UNCERTAIN"}
            and root == rooted_support == "ABSENT"
            and regime.get("competition_kinds")
        )
    return classification == "UNRESOLVED" and state in {"WEAK", "UNCERTAIN"}


def _raw_provider_output(reading: MingliAgentReadingEnvelope) -> Any:
    receipt = getattr(reading, "normalization_receipt", None)
    return None if receipt is None else receipt.raw_output


def _string(value: object) -> str | None:
    return value if isinstance(value, str) else None
