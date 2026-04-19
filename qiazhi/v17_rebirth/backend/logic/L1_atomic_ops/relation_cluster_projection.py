from __future__ import annotations

from typing import Any, Dict, Iterable

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN, STEM_ELEMENT, ten_god_from_stems


def _parse_gz(gz: str) -> tuple[str, str]:
    raw = str(gz or "").strip()
    if len(raw) < 2:
        return "", ""
    return raw[0], raw[1]


def god_cluster_projection(
    *,
    physics_tensor: Dict[str, Any],
    base_god: str,
    day_master: str,
    focus_branches: Iterable[str],
) -> Dict[str, float]:
    from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import _get_god_to_element_map

    g2e = _get_god_to_element_map(day_master)
    target_element = g2e.get(str(base_god or ""))
    if not target_element:
        return {}

    candidate_gods = [god for god, element in g2e.items() if element == target_element]
    if not candidate_gods:
        return {}

    weights: Dict[str, float] = {god: 0.0 for god in candidate_gods}
    for branch in [str(branch or "") for branch in focus_branches]:
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
            if STEM_ELEMENT.get(hidden_stem) != target_element:
                continue
            god = ten_god_from_stems(day_master, hidden_stem)
            if god in weights:
                weights[god] = weights.get(god, 0.0) + float(hidden_weight)

    fp = physics_tensor.get("four_pillars", {}) if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    visible_gz = [fp.get(key, "") for key in ("year", "month", "day", "hour")]
    visible_gz.extend([physics_tensor.get("luck_pillar", ""), physics_tensor.get("flow_pillar", "")])
    for gz in visible_gz:
        stem, _branch = _parse_gz(str(gz or ""))
        if not stem or STEM_ELEMENT.get(stem) != target_element:
            continue
        god = ten_god_from_stems(day_master, stem)
        if god in weights:
            weights[god] = weights.get(god, 0.0) + 0.55

    total = sum(weights.values())
    if total <= 0:
        uniform = round(1.0 / len(candidate_gods), 4)
        return {god: uniform for god in candidate_gods}
    return {
        god: round(weight / total, 4)
        for god, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True)
        if weight > 0
    }
