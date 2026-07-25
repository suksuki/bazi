from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal


CanvasRole = Literal["guest", "member", "practitioner", "research", "admin"]

POSITION_LABELS = {
    "year": "年柱",
    "month": "月柱",
    "day": "日柱",
    "hour": "时柱",
}
POSITION_SLOT_TYPES = {
    "year": "natal_year",
    "month": "natal_month",
    "day": "natal_day",
    "hour": "natal_hour",
}
BRANCH_POLARITY = {
    "子": "yang", "丑": "yin", "寅": "yang", "卯": "yin",
    "辰": "yang", "巳": "yin", "午": "yang", "未": "yin",
    "申": "yang", "酉": "yin", "戌": "yang", "亥": "yin",
}
RELATION_LABELS = {
    "generates": "相生",
    "controls": "相克",
    "same_element_support": "同气",
    "stores": "藏干",
    "roots": "通根",
    "forms_half_combination": "半合",
    "forms_triple_combination": "三合",
    "clashes": "相冲",
    "harmonizes": "相合",
    "harms": "相害",
    "breaks": "相破",
    "punishes": "相刑",
    "position_link": "同柱",
}
LAYER_DEFINITIONS = (
    (
        "overview",
        "总览",
        "先看已提交主路径，以及与它直接相关的关键支持和牵制。",
        set(),
    ),
    (
        "five_element",
        "五行",
        "只看正式路径中的生、泄、克、制与同气支持。",
        {"generates", "controls", "same_element_support"},
    ),
    (
        "combination_conflict",
        "合冲",
        "只看会影响正式路径的合、冲、刑、害与破。",
        {
            "harmonizes",
            "forms_half_combination",
            "forms_triple_combination",
            "clashes",
            "punishes",
            "harms",
            "breaks",
        },
    ),
    (
        "roots_reveal",
        "根透",
        "查看路径节点的通根、藏干、透出与同柱承载。",
        {"roots", "stores", "position_link"},
    ),
    (
        "timing",
        "时运",
        "查看大运与流年如何进入当前正式结构。",
        set(),
    ),
    (
        "work_path",
        "做功",
        "只显示当前角色获准查看的结构化路径。",
        set(),
    ),
)
CHANGE_GROUPS = (
    ("introduced", "新增"),
    ("removed", "消失"),
    ("activated", "激活"),
    ("reinforced", "增强支持"),
    ("weakened", "受到制约"),
    ("blocked", "路径受阻"),
    ("reopened", "重新打开"),
    ("unchanged", "保持不变"),
)
TEMPORAL_PATH_UPDATE_POLICY_VERSION = "deepbazi.temporal-path-update.ra3.v1"


class ReadOnlyCanvasUnavailable(ValueError):
    pass


def canvas_role(account_role: str) -> CanvasRole:
    return {
        "admin": "admin",
        "research_master": "research",
        "research": "research",
        "practitioner": "practitioner",
        "member": "member",
    }.get(str(account_role).strip().lower(), "guest")  # type: ignore[return-value]


def slot_ref_for_position(position: str) -> str:
    for prefix in POSITION_LABELS:
        if position.startswith(f"{prefix}_"):
            return f"slot-natal-{prefix}"
    return ""


def refs(values: list[str], *, fallback: str) -> list[str]:
    normalized = [str(item).strip() for item in values if str(item).strip()]
    return list(dict.fromkeys(normalized or [fallback]))


def parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def bounded(value: str, limit: int) -> str:
    clean = " ".join(str(value).split())
    return clean if len(clean) <= limit else f"{clean[: limit - 1]}…"
