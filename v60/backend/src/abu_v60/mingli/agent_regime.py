from __future__ import annotations

from typing import TYPE_CHECKING, Any

from abu_v60.mingli.agent_regime_contracts import (
    REGIME_WEAK_VS_FOLLOW_METHOD_REF,
)
from abu_v60.mingli.agent_root_gate import minimum_anti_follow_root_coordinates

if TYPE_CHECKING:
    from abu_v60.mingli.agent_contracts import MingliAgentCasePacket

_FACT_STATUSES = {"PRESENT", "ABSENT", "UNRESOLVED"}
_CHAIN_STATUSES = {"CLOSED", "OPEN", "UNRESOLVED"}
_COMPETITION_ORDER = (
    "VISIBLE_PEER",
    "HIDDEN_RESOURCE",
    "COMBINATION_UNRESOLVED",
)
_WEAK_FOLLOW_STATES = {"WEAK", "FOLLOWING_TENDENCY", "UNCERTAIN"}
_NON_WEAK_STATES = {"STRONG", "BALANCED", "SPECIALIZED_TENDENCY"}
_PILLAR_SLOT_LABELS = {"year": "年", "month": "月", "day": "日", "hour": "时"}


def normalize_regime_decision(
    raw_value: Any,
    *,
    packet: MingliAgentCasePacket,
    day_master_state: object,
    normalization_issues: set[str],
) -> dict[str, Any]:
    """Derive a regime classification from typed Agent judgments and packet facts."""

    raw = dict(raw_value) if isinstance(raw_value, dict) else {}
    changed = not isinstance(raw_value, dict)
    candidates = tuple(packet.day_master_support.same_element_hidden_support)
    minimum_roots = minimum_anti_follow_root_coordinates(packet)
    peers = tuple(packet.day_master_support.visible_peer_support)
    resources = tuple(packet.day_master_support.resource_support)

    root_status = raw.get("effective_root_status")
    raw_coordinates = raw.get("effective_root_coordinates")
    coordinates = tuple(
        dict.fromkeys(
            item
            for item in (raw_coordinates if isinstance(raw_coordinates, list) else [])
            if isinstance(item, str) and item in candidates
        )
    )
    if not candidates:
        changed = changed or root_status != "ABSENT" or bool(raw_coordinates)
        root_status = "ABSENT"
        coordinates = ()
    elif minimum_roots:
        merged_coordinates = tuple(
            dict.fromkeys(
                (
                    *minimum_roots,
                    *(coordinates if root_status == "PRESENT" else ()),
                )
            )
        )
        gate_repaired = (
            root_status != "PRESENT"
            or list(merged_coordinates) != raw_coordinates
        )
        changed = (
            changed
            or gate_repaired
        )
        root_status = "PRESENT"
        coordinates = merged_coordinates
        if gate_repaired:
            normalization_issues.add("DAY_MASTER_EFFECTIVE_ROOT_GATE")
    elif root_status == "PRESENT" and coordinates:
        changed = changed or list(coordinates) != raw_coordinates
    elif root_status in {"ABSENT", "UNRESOLVED"}:
        changed = changed or root_status != "UNRESOLVED" or bool(raw_coordinates)
        root_status = "UNRESOLVED"
        coordinates = ()
    else:
        changed = True
        root_status = "UNRESOLVED"
        coordinates = ()

    rooted_support = raw.get("rooted_visible_support_status")
    if not peers:
        changed = changed or rooted_support != "ABSENT"
        rooted_support = "ABSENT"
    elif (
        rooted_support == "PRESENT" and root_status != "PRESENT"
    ) or rooted_support not in _FACT_STATUSES:
        changed = True
        rooted_support = "UNRESOLVED"

    chain_status = raw.get("dominant_chain_status")
    if chain_status not in _CHAIN_STATUSES:
        changed = True
        chain_status = "UNRESOLVED"

    raw_competition = raw.get("competition_kinds")
    raw_competition = raw_competition if isinstance(raw_competition, list) else []
    competition = {
        item
        for item in raw_competition
        if item in _COMPETITION_ORDER and item == "COMBINATION_UNRESOLVED"
    }
    if peers and rooted_support != "PRESENT":
        competition.add("VISIBLE_PEER")
    if resources:
        competition.add("HIDDEN_RESOURCE")
    competition_kinds = tuple(item for item in _COMPETITION_ORDER if item in competition)
    changed = changed or list(competition_kinds) != raw_competition

    classification = _derive_classification(
        day_master_state=day_master_state,
        root_status=str(root_status),
        rooted_support_status=str(rooted_support),
        chain_status=str(chain_status),
        competition_kinds=competition_kinds,
    )
    changed = changed or raw.get("classification") != classification

    allowed_evidence = {
        item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"
    }
    raw_evidence = raw.get("evidence_ids")
    evidence_ids = list(
        dict.fromkeys(
            item
            for item in (raw_evidence if isinstance(raw_evidence, list) else [])
            if item in allowed_evidence
        )
    )
    support_evidence = packet.day_master_support.evidence_id
    if support_evidence not in evidence_ids:
        evidence_ids.append(support_evidence)
    changed = changed or evidence_ids != raw_evidence
    changed = changed or raw.get("method_asset_ref") != REGIME_WEAK_VS_FOLLOW_METHOD_REF
    if changed:
        normalization_issues.add("DAY_MASTER_REGIME")

    return {
        "method_asset_ref": REGIME_WEAK_VS_FOLLOW_METHOD_REF,
        "classification": classification,
        "effective_root_status": root_status,
        "effective_root_coordinates": list(coordinates),
        "rooted_visible_support_status": rooted_support,
        "dominant_chain_status": chain_status,
        "competition_kinds": list(competition_kinds),
        "evidence_ids": evidence_ids[:10],
    }


def reconcile_day_master_state(
    value: dict[str, Any],
    *,
    classification: str,
    packet: MingliAgentCasePacket,
    normalization_issues: set[str],
) -> None:
    """Keep the public state consistent without inventing a stronger verdict."""

    state = value.get("day_master_state")
    replacement: str | None = None
    rationale: str | None = None
    if classification == "ORDINARY_WEAK" and state != "WEAK":
        replacement = "WEAK"
        rationale = "有效根或透而有根的同类支持已成立，因此退出从势竞争，按普通身弱重判。"
    elif classification == "FALSE_FOLLOW_COMPETITION" and state not in {
        "WEAK",
        "UNCERTAIN",
    }:
        replacement = "UNCERTAIN"
        rationale = "原局虽缺有效根，但浮比、藏印或未决组合仍构成竞争，不能直接判从。"
    elif classification == "UNRESOLVED" and state == "FOLLOWING_TENDENCY":
        replacement = "UNCERTAIN"
        rationale = "从势所需的有效根排除与异类主导链尚未同时闭合，暂保留竞争解释。"
    elif classification == "FOLLOW_TREND" and state != "FOLLOWING_TENDENCY":
        replacement = "FOLLOWING_TENDENCY"
        rationale = "有效根与有根同类均已排除，竞争证据为空且异类主导链闭合，进入从势工作判断。"
    if replacement is None:
        _repair_minimum_root_rationale(
            value,
            classification=classification,
            packet=packet,
            normalization_issues=normalization_issues,
        )
        return
    value["day_master_state"] = replacement
    value["day_master_rationale"] = rationale
    normalization_issues.add("DAY_MASTER_REGIME")
    _repair_minimum_root_rationale(
        value,
        classification=classification,
        packet=packet,
        normalization_issues=normalization_issues,
    )


def _repair_minimum_root_rationale(
    value: dict[str, Any],
    *,
    classification: str,
    packet: MingliAgentCasePacket,
    normalization_issues: set[str],
) -> None:
    minimum_roots = minimum_anti_follow_root_coordinates(packet)
    if not minimum_roots:
        return
    current = str(value.get("day_master_rationale") or "")
    if (
        "DAY_MASTER_EFFECTIVE_ROOT_GATE" not in normalization_issues
        and "余气" not in current
    ):
        return
    coordinate = minimum_roots[0]
    slot = coordinate.split("支藏", maxsplit=1)[0]
    pillar = next(item for item in packet.pillars if item.slot == slot)
    slot_label = _PILLAR_SLOT_LABELS[slot]
    conclusion = (
        "因此退出直接从势，按普通身弱继续比较全盘泄耗、生扶、财与官杀压力。"
        if classification == "ORDINARY_WEAK"
        else "这只排除直接从势，强弱仍须继续比较全盘泄耗、生扶、财与官杀压力。"
    )
    value["day_master_rationale"] = (
        f"日主{packet.day_master_stem}生于{packet.month_command_branch}月；"
        f"{slot_label}支{pillar.branch}的第一藏干{packet.day_master_stem}与日主同字，"
        f"在最低阻从范围内构成有效根。{conclusion}"
    )
    normalization_issues.add("DAY_MASTER_ROOT_RANK")


def _derive_classification(
    *,
    day_master_state: object,
    root_status: str,
    rooted_support_status: str,
    chain_status: str,
    competition_kinds: tuple[str, ...],
) -> str:
    if day_master_state in _NON_WEAK_STATES:
        return "NON_WEAK_OUTSIDE_SCOPE"
    if day_master_state not in _WEAK_FOLLOW_STATES:
        return "UNRESOLVED"
    if (
        root_status == "PRESENT" or rooted_support_status == "PRESENT"
    ) and day_master_state == "UNCERTAIN":
        return "UNRESOLVED"
    if root_status == "PRESENT" or rooted_support_status == "PRESENT":
        return "ORDINARY_WEAK"
    if root_status == "UNRESOLVED" or rooted_support_status == "UNRESOLVED":
        return "UNRESOLVED"
    if chain_status != "CLOSED":
        return "UNRESOLVED"
    if competition_kinds:
        return "FALSE_FOLLOW_COMPETITION"
    return "FOLLOW_TREND"
