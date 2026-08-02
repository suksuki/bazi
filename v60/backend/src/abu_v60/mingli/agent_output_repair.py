from __future__ import annotations

from typing import TYPE_CHECKING, Any

MINGLI_AGENT_OUTPUT_REPAIR_VERSION = "v60.mingli-agent-output-repair.001"

if TYPE_CHECKING:
    from abu_v60.mingli.agent_contracts import MingliAgentCasePacket


_DOMAIN_KEYS = {
    "personality": ("DOMAIN_PERSONALITY", "性情"),
    "career": ("DOMAIN_CAREER", "事业"),
    "wealth": ("DOMAIN_WEALTH", "财富"),
    "relationship": ("DOMAIN_RELATIONSHIP", "关系"),
    "family": ("DOMAIN_FAMILY", "家庭"),
}
_DAY_MASTER_STATES = {
    "身强": "STRONG",
    "强": "STRONG",
    "身弱": "WEAK",
    "弱": "WEAK",
    "中和": "BALANCED",
    "平衡": "BALANCED",
    "从势": "FOLLOWING_TENDENCY",
    "专旺": "SPECIALIZED_TENDENCY",
    "不确定": "UNCERTAIN",
}
_TRANSFORMATIONS = {
    "GENERATES",
    "CONTROLS",
    "SUPPORTS",
    "CONSTRAINS",
    "CHANNELS",
    "COMPETES",
}
_TOP_LEVEL_KEYS = {
    "first_look",
    "whole_chart_thesis",
    "day_master_state",
    "support_selection",
    "day_master_rationale",
    "day_master_evidence_ids",
    "hypotheses",
    "excluded_candidates",
    "hypothesis_decision",
    "work_path",
    "life_image",
    "domains",
    "timing",
    "server_issue_keys",
}


def repair_local_output_fields(
    value: Any,
    *,
    packet: MingliAgentCasePacket,
) -> Any:
    """Keep one malformed projection field from erasing the whole Reading."""

    if not isinstance(value, dict):
        return value
    result = {key: item for key, item in value.items() if key in _TOP_LEVEL_KEYS}
    issues: set[str] = set()
    _repair_day_master(result=result, packet=packet, issues=issues)
    _repair_hypotheses(result=result, issues=issues)
    _repair_work_path(result=result, packet=packet, issues=issues)
    _repair_domains(result=result, packet=packet, issues=issues)
    _repair_timing(result=result, packet=packet, issues=issues)
    result["server_issue_keys"] = sorted(issues)
    return result


def _repair_day_master(
    *,
    result: dict[str, Any],
    packet: MingliAgentCasePacket,
    issues: set[str],
) -> None:
    state = result.get("day_master_state")
    if state not in {
        "STRONG",
        "WEAK",
        "BALANCED",
        "FOLLOWING_TENDENCY",
        "SPECIALIZED_TENDENCY",
        "UNCERTAIN",
    }:
        mapped = _DAY_MASTER_STATES.get(str(state).strip())
        if mapped is None:
            mapped = "UNCERTAIN"
            issues.add("DAY_MASTER")
        result["day_master_state"] = mapped
    result["day_master_evidence_ids"] = [
        *(item.evidence_id for item in packet.pillars),
        packet.day_master_support.evidence_id,
    ]


def _repair_hypotheses(*, result: dict[str, Any], issues: set[str]) -> None:
    hypotheses = result.get("hypotheses")
    if not isinstance(hypotheses, list) or len(hypotheses) != 2:
        return
    repaired: list[dict[str, Any]] = []
    for index, raw in enumerate(hypotheses):
        if not isinstance(raw, dict):
            repaired.append(raw)
            continue
        item = dict(raw)
        semantic_key = f"HYPOTHESIS_H{index + 1}"
        name, name_bad = _text(
            item.get("name"),
            minimum=2,
            maximum=48,
            fallback=f"第{index + 1}条整盘解释",
        )
        thesis, thesis_bad = _text(
            item.get("thesis"),
            minimum=12,
            maximum=300,
            fallback="这条解释需要重新形成完整的整盘因果链后再比较。",
        )
        failure, failure_bad = _text(
            item.get("failure_condition"),
            minimum=6,
            maximum=140,
            fallback="关键条件不成立时重判",
        )
        if name_bad or thesis_bad or failure_bad:
            issues.add(semantic_key)
        item.update(
            {
                "name": name,
                "thesis": thesis,
                "failure_condition": failure,
            }
        )
        repaired.append(item)
    first, second = repaired
    if (
        isinstance(first, dict)
        and isinstance(second, dict)
        and (first.get("name") == second.get("name") or first.get("thesis") == second.get("thesis"))
    ):
        second["name"] = f"{second.get('name', '替代路径')}的替代解释"[:48]
        second["thesis"] = (
            f"另一条路径从{second['name']}解释全盘；它必须在关键条件上"
            "比当前主线更连贯，才足以翻转主次。"
        )[:300]
        issues.add("HYPOTHESIS_H2")
    result["hypotheses"] = repaired


def _repair_work_path(
    *,
    result: dict[str, Any],
    packet: MingliAgentCasePacket,
    issues: set[str],
) -> None:
    raw = result.get("work_path")
    item = raw if isinstance(raw, dict) else {}
    path, path_bad = _text(
        item.get("path_statement"),
        minimum=12,
        maximum=260,
        fallback="本条主路径尚未形成完整、可核对的源端与目标说明。",
    )
    condition, condition_bad = _text(
        item.get("condition"),
        minimum=6,
        maximum=160,
        fallback="待整盘路径重新推演",
    )
    transformations = item.get("transformation_codes")
    transformations = transformations if isinstance(transformations, list) else []
    transformations = list(
        dict.fromkeys(code for code in transformations if code in _TRANSFORMATIONS)
    )[:4]
    evidence = _evidence(
        item.get("evidence_ids"),
        allowed=_natal_ids(packet),
        fallback=(),
        maximum=10,
    )
    closure = item.get("closure")
    if closure not in {"CLOSED", "CONDITIONAL", "BROKEN", "UNCERTAIN"}:
        closure = "UNCERTAIN"
    malformed = (
        not isinstance(raw, dict)
        or path_bad
        or condition_bad
        or not transformations
        or item.get("closure") != closure
        or not evidence
    )
    if malformed:
        issues.add("WORK_PATH")
    result["work_path"] = {
        "path_statement": path,
        "transformation_codes": transformations or ["CHANNELS"],
        "closure": closure,
        "condition": condition,
        "evidence_ids": evidence,
    }


def _repair_domains(
    *,
    result: dict[str, Any],
    packet: MingliAgentCasePacket,
    issues: set[str],
) -> None:
    raw_domains = result.get("domains")
    raw_domains = raw_domains if isinstance(raw_domains, dict) else {}
    domains: dict[str, Any] = {}
    for key, (semantic_key, label) in _DOMAIN_KEYS.items():
        raw = raw_domains.get(key)
        item = raw if isinstance(raw, dict) else {}
        headline, headline_bad = _text(
            item.get("headline"),
            minimum=4,
            maximum=48,
            fallback=f"{label}判断待重新推演",
        )
        conclusion, conclusion_bad = _text(
            item.get("conclusion"),
            minimum=16,
            maximum=260,
            fallback=f"本条原始回答没有形成完整、可核对的{label}判断。",
        )
        condition, condition_bad = _text(
            item.get("condition"),
            minimum=6,
            maximum=160,
            fallback="待下一次整盘推演补齐",
        )
        chain = _narrative(item.get("causal_chain"))
        evidence = _evidence(
            item.get("evidence_ids"),
            allowed=_natal_ids(packet),
            fallback=(),
            maximum=8,
        )
        confidence = item.get("confidence")
        malformed = (
            not isinstance(raw, dict)
            or headline_bad
            or conclusion_bad
            or condition_bad
            or chain is None
            or not evidence
            or confidence not in {"LOW", "MEDIUM"}
        )
        if malformed:
            issues.add(semantic_key)
        domains[key] = {
            "headline": headline,
            "conclusion": conclusion,
            "causal_chain": chain or ["本条因果链需要重新推演"],
            "condition": condition,
            "evidence_ids": evidence,
            "confidence": confidence if confidence in {"LOW", "MEDIUM"} else "MEDIUM",
        }
    result["domains"] = domains


def _repair_timing(
    *,
    result: dict[str, Any],
    packet: MingliAgentCasePacket,
    issues: set[str],
) -> None:
    raw = result.get("timing")
    timing = raw if isinstance(raw, dict) else {}
    natal, natal_bad = _text(
        timing.get("natal_baseline"),
        minimum=12,
        maximum=180,
        fallback="原局基线尚未形成完整、可核对的时间判断。",
    )
    if not isinstance(raw, dict) or natal_bad:
        issues.add("TIMING_NATAL")
    coordinates = {item.layer: item for item in packet.timing_coordinates}
    repaired_layers: dict[str, Any] = {}
    for key, layer, semantic_key in (
        ("dayun", "DAYUN", "TIMING_DAYUN"),
        ("annual", "ANNUAL", "TIMING_ANNUAL"),
    ):
        item_raw = timing.get(key)
        item = item_raw if isinstance(item_raw, dict) else {}
        conclusion, conclusion_bad = _text(
            item.get("conclusion"),
            minimum=12,
            maximum=260,
            fallback=f"{coordinates[layer].pillar}{coordinates[layer].ten_god_label}进入{layer}层，具体作用需重新推演。",
        )
        chain = _narrative(item.get("activation_chain"))
        if not isinstance(item_raw, dict) or conclusion_bad or chain is None:
            issues.add(semantic_key)
        relations = {
            relation.evidence_id
            for relation in packet.timing_relations
            if relation.left_layer == layer
        }
        allowed = _natal_ids(packet) | {
            coordinates[layer].evidence_id,
            *relations,
        }
        repaired_layers[key] = {
            "coordinate_evidence_id": coordinates[layer].evidence_id,
            "relation_evidence_ids": _evidence(
                item.get("relation_evidence_ids"),
                allowed=relations,
                fallback=(),
                maximum=6,
            ),
            "conclusion": conclusion,
            "activation_chain": chain or ["本条时间因果链需要重新推演"],
            "evidence_ids": _evidence(
                item.get("evidence_ids"),
                allowed=allowed,
                fallback=(coordinates[layer].evidence_id,),
                maximum=8,
            ),
            "confidence": (
                item.get("confidence") if item.get("confidence") in {"LOW", "MEDIUM"} else "MEDIUM"
            ),
        }
    signals = timing.get("verification_signals")
    signals = signals if isinstance(signals, list) else []
    signals = [
        item.strip()[:160] for item in signals if isinstance(item, str) and len(item.strip()) >= 4
    ][:2]
    result["timing"] = {
        "natal_baseline": natal,
        "natal_evidence_ids": _evidence(
            timing.get("natal_evidence_ids"),
            allowed=_natal_ids(packet),
            fallback=_natal_basis(packet),
            maximum=8,
        ),
        **repaired_layers,
        "verification_signals": signals or ["以现实反馈复核主次解释是否需要翻转"],
    }


def _text(
    value: Any,
    *,
    minimum: int,
    maximum: int,
    fallback: str,
) -> tuple[str, bool]:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        return fallback, True
    stripped = value.strip()
    return stripped[:maximum], len(stripped) > maximum


def _narrative(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    valid = [
        item.strip()[:160] for item in value if isinstance(item, str) and len(item.strip()) >= 4
    ]
    return valid[:1] or None


def _evidence(
    value: Any,
    *,
    allowed: set[str],
    fallback: tuple[str, ...],
    maximum: int,
) -> list[str]:
    items = value if isinstance(value, list) else []
    result = list(dict.fromkeys(item for item in items if item in allowed))
    return (result or list(fallback))[:maximum]


def _natal_ids(packet: MingliAgentCasePacket) -> set[str]:
    return {item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"}


def _natal_basis(packet: MingliAgentCasePacket) -> tuple[str, ...]:
    return (
        packet.pillars[1].evidence_id,
        packet.day_master_support.evidence_id,
    )
