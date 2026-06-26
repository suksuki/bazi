from __future__ import annotations

from pydantic import Field

from v30.contracts import V30Model
from v30.core.constants import CONTROLS, GENERATES, YIN_YANG_BY_STEM, element_of_stem


class TenGodPosition(V30Model):
    label: str
    stem: str
    pillar: str
    layer: str
    element: str
    weight: float = Field(default=1.0, ge=0.0)


def ten_god(day_stem: str, target_stem: str) -> str:
    day_element = element_of_stem(day_stem)
    target_element = element_of_stem(target_stem)
    if not day_element or not target_element:
        return ""
    same_polarity = YIN_YANG_BY_STEM.get(day_stem) == YIN_YANG_BY_STEM.get(target_stem)
    if day_element == target_element:
        return "比肩" if same_polarity else "劫财"
    if GENERATES.get(target_element) == day_element:
        return "偏印" if same_polarity else "正印"
    if GENERATES.get(day_element) == target_element:
        return "食神" if same_polarity else "伤官"
    if CONTROLS.get(day_element) == target_element:
        return "偏财" if same_polarity else "正财"
    if CONTROLS.get(target_element) == day_element:
        return "七杀" if same_polarity else "正官"
    return ""
