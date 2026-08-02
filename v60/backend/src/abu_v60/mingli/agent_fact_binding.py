from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from abu_v60.mingli.agent_contracts import MingliAgentCasePacket


def bind_packet_fact_fields(
    value: Any,
    *,
    packet: MingliAgentCasePacket,
) -> Any:
    """Replace model-copied facts with packet-owned coordinates and scope."""

    if not isinstance(value, dict):
        return value
    value = dict(value)
    roots = packet.day_master_support.same_element_hidden_support
    value["support_selection"] = {
        "root_status": "PRESENT" if roots else "NONE",
        "root_coordinates": list(roots),
        "peer_coordinates": list(packet.day_master_support.visible_peer_support),
        "resource_coordinates": list(packet.day_master_support.resource_support),
    }
    _bind_life_image(value=value, packet=packet)
    _bind_timing_fact_fields(value=value, packet=packet)
    return value


_IMAGE_SUBJECTS = {
    "甲": "挺直乔木",
    "乙": "柔韧藤木",
    "丙": "高悬日火",
    "丁": "守夜灯火",
    "戊": "厚重山岭",
    "己": "细作田畴",
    "庚": "待炼矿铁",
    "辛": "经琢珠玉",
    "壬": "奔行江水",
    "癸": "润物雨露",
}
_SEASON_SCENES = {
    **{branch: "早春原野" for branch in "寅卯辰"},
    **{branch: "盛夏旷野" for branch in "巳午未"},
    **{branch: "清秋庭野" for branch in "申酉戌"},
    **{branch: "寒冬山野" for branch in "亥子丑"},
}
_ELEMENT_LABELS = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}
_NON_IMAGE_TERMS = (
    "知识分子",
    "知识工作者",
    "专业技术",
    "艺术家",
    "思考者",
    "技能变现",
    "模型",
    "框架",
    "工坊",
    "身强",
    "身弱",
    "用神",
    "忌神",
    "格局",
)


def _bind_life_image(*, value: dict[str, Any], packet: MingliAgentCasePacket) -> None:
    life_image = value.get("life_image")
    life_image = life_image if isinstance(life_image, dict) else {}
    corpus = "\n".join(str(life_image.get(key, "")) for key in ("title", "image", "explanation"))
    valid_shape = (
        isinstance(life_image.get("title"), str)
        and len(life_image["title"].strip()) >= 2
        and isinstance(life_image.get("image"), str)
        and len(life_image["image"].strip()) >= 8
        and isinstance(life_image.get("explanation"), str)
        and len(life_image["explanation"].strip()) >= 16
    )
    if valid_shape and not any(term in corpus for term in _NON_IMAGE_TERMS):
        return
    scene = _SEASON_SCENES[packet.month_command_branch]
    subject = _IMAGE_SUBJECTS[packet.day_master_stem]
    roots = len(packet.day_master_support.same_element_hidden_support)
    peers = len(packet.day_master_support.visible_peer_support)
    resources = len(packet.day_master_support.resource_support)
    root_image = "脚下已有同类根系可依" if roots else "脚下没有同类根系可依"
    peer_image = f"近旁有{peers}处同类彼此呼应" if peers else "近旁少见同类呼应"
    resource_image = f"暗处仍有{resources}处生扶维持气息" if resources else "暗处也少见生扶接续"
    life_image.update(
        {
            "title": f"{scene}里的{subject}"[:24],
            "image": f"{scene}里，{subject}迎着时令展开；{root_image}，{peer_image}，{resource_image}。",
            "explanation": (
                f"日主为{packet.day_master_stem}{_ELEMENT_LABELS[packet.day_master_element]}，"
                f"生在{packet.month_command_branch}月；地支同类根{roots}处，"
                f"明干同类{peers}处，印星生扶{resources}处。"
                "因此画面强调的是它如何承载、借力并继续生长。"
            ),
            "evidence_ids": [
                packet.pillars[1].evidence_id,
                packet.day_master_support.evidence_id,
            ],
        }
    )
    value["life_image"] = life_image


def _bind_timing_fact_fields(
    *,
    value: dict[str, Any],
    packet: MingliAgentCasePacket,
) -> None:
    timing = value.get("timing")
    if not isinstance(timing, dict):
        return
    timing = dict(timing)
    coordinates = {item.layer: item.evidence_id for item in packet.timing_coordinates}
    relations = {
        layer: {item.evidence_id for item in packet.timing_relations if item.left_layer == layer}
        for layer in ("DAYUN", "ANNUAL")
    }
    natal = {item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"}
    dayun_allowed = natal | {coordinates["DAYUN"]} | relations["DAYUN"]
    allowed_by_layer = {
        "DAYUN": dayun_allowed,
        "ANNUAL": dayun_allowed | {coordinates["ANNUAL"]} | relations["ANNUAL"],
    }
    for key, layer in (("dayun", "DAYUN"), ("annual", "ANNUAL")):
        reading = timing.get(key)
        if not isinstance(reading, dict):
            continue
        reading = dict(reading)
        raw_evidence = reading.get("evidence_ids")
        evidence = raw_evidence if isinstance(raw_evidence, list) else []
        raw_relations = reading.get("relation_evidence_ids")
        relation_values = raw_relations if isinstance(raw_relations, list) else []
        selected_relations = list(
            dict.fromkeys(
                item for item in (*relation_values, *evidence) if item in relations[layer]
            )
        )
        filtered = [item for item in evidence if item in allowed_by_layer[layer]]
        reading["coordinate_evidence_id"] = coordinates[layer]
        reading["relation_evidence_ids"] = selected_relations
        reading["evidence_ids"] = list(
            dict.fromkeys((*filtered, coordinates[layer], *selected_relations))
        )[:8]
        timing[key] = reading
    value["timing"] = timing
