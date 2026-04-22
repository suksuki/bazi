from __future__ import annotations

from typing import Callable, Dict, List, Tuple


def collect_visible_stems(
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
    *,
    parse_gz: Callable[[str], Tuple[str, str]],
) -> List[str]:
    stems: List[str] = []
    for key in ("year", "month", "day", "hour"):
        stem, _ = parse_gz(str(four_pillars.get(key, "")).strip())
        if stem:
            stems.append(stem)
    for gz in (luck_pillar, flow_pillar):
        stem, _ = parse_gz(gz)
        if stem:
            stems.append(stem)
    return stems


def visible_stem_scope_weights(
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
    *,
    parse_gz: Callable[[str], Tuple[str, str]],
) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    for key in ("year", "month", "day", "hour"):
        stem, _ = parse_gz(str(four_pillars.get(key, "")).strip())
        if stem:
            rows.append((key, stem))
    for scope, gz in (("luck", luck_pillar), ("flow", flow_pillar)):
        stem, _ = parse_gz(gz)
        if stem:
            rows.append((scope, stem))
    return rows


def cross_polarity_root_support(
    stem: str,
    root_strengths: Dict[str, float],
    *,
    stem_element_map: Dict[str, str],
    stem_yin_map: Dict[str, bool],
    cross_polarity_root_support_factor: float,
) -> float:
    stem_element = stem_element_map.get(stem, "")
    stem_yin = stem_yin_map.get(stem)
    if not stem_element or stem_yin is None:
        return 0.0
    support = 0.0
    factor = max(0.0, float(cross_polarity_root_support_factor or 0.0))
    for root_stem, strength in root_strengths.items():
        if root_stem == stem:
            continue
        if stem_element_map.get(root_stem, "") != stem_element:
            continue
        if stem_yin_map.get(root_stem) == stem_yin:
            support += max(0.0, float(strength or 0.0))
        else:
            support += max(0.0, float(strength or 0.0)) * factor
    return support


def same_element_visible(
    hidden_stem: str,
    visible_stems: List[str],
    *,
    stem_element_map: Dict[str, str],
) -> bool:
    hidden_element = stem_element_map.get(hidden_stem, "")
    if not hidden_element:
        return False
    return any(stem_element_map.get(stem, "") == hidden_element for stem in visible_stems)
