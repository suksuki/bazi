from __future__ import annotations

import re
from typing import Protocol

_STEMS = "甲乙丙丁戊己庚辛壬癸"
_MANIFESTATION_TERMS = ("透出", "透干", "明透", "透于天干")
_TEN_GOD_GROUPS = {
    "食伤": {"食神", "伤官"},
    "官杀": {"正官", "七杀"},
    "财星": {"正财", "偏财"},
    "印星": {"正印", "偏印"},
    "比劫": {"比肩", "劫财"},
}


class PillarFact(Protocol):
    slot: str
    stem: str
    visible_ten_god: str


def manifestation_claim_conflicts(
    prose: str,
    *,
    pillars: tuple[PillarFact, ...],
    additional_visible: tuple[tuple[str, str], ...] = (),
) -> bool:
    """Detect claims that promote hidden stems or ten gods to visible stems."""

    visible_stems = {item.stem for item in pillars} | {
        stem for stem, _ in additional_visible
    }
    visible_ten_gods = {item.visible_ten_god for item in pillars} | {
        ten_god for _, ten_god in additional_visible
    }
    visible_by_slot = {item.slot: item.visible_ten_god for item in pillars}
    slot_names = {"年": "year", "月": "month", "日": "day", "时": "hour"}
    for clause in re.split(r"[，,。；;\n]", prose):
        named_groups = [
            members
            for label, members in _TEN_GOD_GROUPS.items()
            if label in clause or any(member in clause for member in members)
        ]
        named_slots = re.findall(r"([年月日时])(?:柱)?(?:天)?干", clause)
        if len(named_groups) == 1 and any(
            visible_by_slot[slot_names[slot]] not in named_groups[0] for slot in named_slots
        ):
            return True
        if not any(term in clause for term in _MANIFESTATION_TERMS):
            continue
        without_hidden = re.sub(r"(?:藏有?|所藏|藏干)[^、/和与]{0,4}", "", clause)
        named_stems = set(re.findall(f"[{_STEMS}]", without_hidden))
        if named_stems - visible_stems:
            return True
        for label, members in _TEN_GOD_GROUPS.items():
            if label in clause and not visible_ten_gods & members:
                return True
        named_ten_gods = {
            member for members in _TEN_GOD_GROUPS.values() for member in members if member in clause
        }
        if named_ten_gods - visible_ten_gods:
            return True
    return False


def resolution_ruling_conflicts(
    *,
    check_code: str,
    ruling: str,
    rationale: str,
) -> bool:
    """Catch a RESOLUTION check that describes an active blocker as support."""

    if not check_code.endswith("_RESOLUTION") or ruling != "SUPPORTS":
        return False
    resolved_terms = (
        "不构成阻断",
        "不足以阻断",
        "不占上风",
        "已有救应",
        "得到化解",
        "能够承接",
        "已被制约",
    )
    blocker_terms = (
        "竞争",
        "争夺",
        "压制",
        "抑制",
        "截断",
        "受阻",
        "耗尽",
        "过度消耗",
        "激烈作用",
    )
    return any(term in rationale for term in blocker_terms) and not any(
        term in rationale for term in resolved_terms
    )
