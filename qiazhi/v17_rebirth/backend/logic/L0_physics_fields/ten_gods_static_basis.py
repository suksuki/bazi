from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple


def branch_stage_for_daymaster(
    daymaster: str,
    branch: str,
    *,
    stem_element_map: Dict[str, str],
    chang_sheng_table: Dict[str, List[str]],
    chang_sheng_stages: List[str],
    chang_sheng_bonus_map: Dict[str, float],
) -> Tuple[str, float]:
    dm_element = stem_element_map.get(daymaster, "")
    if not dm_element or not branch:
        return "", 0.0
    table = chang_sheng_table.get(dm_element, [])
    if branch not in table:
        return "", 0.0
    stage = chang_sheng_stages[table.index(branch)]
    return stage, float(chang_sheng_bonus_map.get(stage, 0.0))


def split_stage_component(stage_name: str, stage_component: float) -> Dict[str, float]:
    if stage_component <= 0.0:
        return {
            "momentum_stage_lu": 0.0,
            "momentum_stage_blade": 0.0,
            "momentum_stage_general": 0.0,
        }
    if stage_name == "临官":
        return {
            "momentum_stage_lu": stage_component,
            "momentum_stage_blade": 0.0,
            "momentum_stage_general": 0.0,
        }
    if stage_name == "帝旺":
        return {
            "momentum_stage_lu": 0.0,
            "momentum_stage_blade": stage_component,
            "momentum_stage_general": 0.0,
        }
    return {
        "momentum_stage_lu": 0.0,
        "momentum_stage_blade": 0.0,
        "momentum_stage_general": stage_component,
    }


def accumulate_stem_energy(
    *,
    stem: str,
    stem_scope: str,
    daymaster: str,
    source_factor: float,
    season_multiplier: float,
    root_strengths: Dict[str, float],
    stem_source_retention_map: Optional[Dict[Tuple[str, str], Dict[str, Any]]],
    acc: Dict[str, float],
    decomposition: Dict[str, Dict[str, float]],
    pillar_label: str,
    proximity_factor: Optional[float] = None,
    ledger: Optional[Any],
    get_l0_val: Callable[[str, float], float],
    stem_base: float,
    ten_god_from_stems: Callable[[str, str], str],
    add_decomposition: Callable[..., None],
    cross_polarity_root_support: Callable[[str, Dict[str, float]], float],
    logger: Optional[Any] = None,
) -> None:
    if not stem:
        return
    energy = float(stem_base) * source_factor * season_multiplier
    source_retention = 1.0
    source_retention_kind = ""
    if stem_scope and isinstance(stem_source_retention_map, dict):
        source_row = stem_source_retention_map.get((stem_scope, stem))
        if isinstance(source_row, dict):
            source_retention = max(0.0, min(1.0, float(source_row.get("retention") or 1.0)))
            source_retention_kind = str(source_row.get("kind") or "")
    energy *= source_retention
    manifest_energy = energy
    exact_root_strength = max(0.0, float(root_strengths.get(stem, 0.0) or 0.0))
    cross_support = cross_polarity_root_support(stem, root_strengths)
    root_strength = exact_root_strength + cross_support
    root_bonus = 0.0
    if root_strength > 0.0:
        rooted_gain = 1.0 + (get_l0_val("ROOTED_GAIN", 1.5) - 1.0) * min(1.0, root_strength)
        root_bonus = manifest_energy * (rooted_gain - 1.0)
        energy = manifest_energy + root_bonus
    god = ten_god_from_stems(daymaster, stem)
    if pillar_label != "日" and god in {"比肩", "劫财"} and root_strength < 0.35:
        floating_floor = get_l0_val("FLOATING_PEER_FACTOR", 0.72)
        floating_ratio = max(0.0, min(1.0, root_strength / 0.35))
        peer_factor = floating_floor + (1.0 - floating_floor) * floating_ratio
        energy *= peer_factor
        manifest_energy *= peer_factor
        root_bonus *= peer_factor
    if energy == energy:
        acc[god] = acc.get(god, 0.0) + energy
        add_decomposition(decomposition, god, manifest=manifest_energy, root=root_bonus)
    elif logger is not None:
        logger.warning(f"[V17-PHYSICS-NAN] Attempted to add NaN energy for {god} at {pillar_label}干")
    if ledger is not None:
        parts = [f"{stem}→{god}"]
        if proximity_factor is not None:
            parts.append(f"贴身×{proximity_factor:.2f}")
        if exact_root_strength > 0.0:
            parts.append(f"本根×{min(1.0, exact_root_strength):.2f}")
        if cross_support > 0.0:
            parts.append(f"异阴阳根×{min(1.0, cross_support):.2f}")
        if pillar_label != "日" and god in {"比肩", "劫财"} and root_strength < 0.35:
            floating_floor = get_l0_val("FLOATING_PEER_FACTOR", 0.72)
            floating_ratio = max(0.0, min(1.0, root_strength / 0.35))
            peer_factor = floating_floor + (1.0 - floating_floor) * floating_ratio
            parts.append(f"浮木×{peer_factor:.2f}")
        if abs(season_multiplier - 1.0) > 0.01:
            parts.append(f"季×{season_multiplier:.1f}")
        if source_retention < 0.999:
            parts.append(f"源气留存×{source_retention:.2f}")
            if source_retention_kind:
                parts.append(source_retention_kind)
        reason = f"{pillar_label}干 {'·'.join(parts)}"
        ledger.append_entry(god, acc[god], f"L0_STEM_{pillar_label}", reason)


def accumulate_branch_energy(
    *,
    branch: str,
    branch_scope: str,
    daymaster: str,
    source_factor: float,
    void_factor: float,
    month_branch: str,
    apply_month_order: bool,
    visible_stems: List[str],
    branch_source_retention_map: Optional[Dict[Tuple[str, str, str], Dict[str, Any]]],
    acc: Dict[str, float],
    decomposition: Dict[str, Dict[str, float]],
    pillar_label: str,
    ledger: Optional[Any],
    get_l0_val: Callable[[str, float], float],
    branch_hidden: Dict[str, List[Tuple[str, float]]],
    branch_base: float,
    stem_element_map: Dict[str, str],
    ten_god_from_stems: Callable[[str, str], str],
    add_decomposition: Callable[..., None],
    same_element_visible: Callable[[str, List[str]], bool],
    season_multiplier_fn: Callable[[str, str], float],
    branch_stage_for_daymaster_fn: Callable[[str, str], Tuple[str, float]],
    split_stage_component_fn: Callable[[str, float], Dict[str, float]],
    logger: Optional[Any] = None,
) -> None:
    if not branch:
        return
    stage_name, stage_bonus_ratio = branch_stage_for_daymaster_fn(daymaster, branch)
    for hidden_stem, h_w in branch_hidden.get(branch, []):
        hidden_element = stem_element_map.get(hidden_stem, "")
        sm = 1.0
        if apply_month_order and branch == month_branch and hidden_element:
            sm = season_multiplier_fn(hidden_element, month_branch)
        source_retention = 1.0
        manifestation_mode = ""
        if branch_scope and isinstance(branch_source_retention_map, dict):
            source_row = branch_source_retention_map.get((branch_scope, branch, hidden_stem))
            if isinstance(source_row, dict):
                source_retention = max(0.0, min(1.0, float(source_row.get("retention") or 1.0)))
                manifestation_mode = str(source_row.get("manifestation_mode") or "")
        raw_base_energy = float(branch_base) * h_w * source_factor * void_factor * source_retention
        exposed = hidden_stem in visible_stems
        same_element = same_element_visible(hidden_stem, visible_stems)
        support_factor = 1.0
        if exposed:
            support_factor = get_l0_val("EXPOSED_HIDDEN_GAIN", 1.2)
        elif not same_element:
            support_factor = get_l0_val(
                "UNEXPOSED_MAIN_HIDDEN_FACTOR" if float(h_w) >= 0.6 else "UNEXPOSED_AUX_HIDDEN_FACTOR",
                0.58 if float(h_w) >= 0.6 else 0.42,
            )
        energy = raw_base_energy * sm * support_factor
        god = ten_god_from_stems(daymaster, hidden_stem)
        base_component = raw_base_energy * support_factor
        momentum_component = raw_base_energy * max(0.0, sm - 1.0) * support_factor
        stage_component = 0.0
        if hidden_element and hidden_element == stem_element_map.get(daymaster, "") and stage_bonus_ratio > 0.0:
            stage_component = raw_base_energy * stage_bonus_ratio * support_factor
            energy += stage_component
        stage_breakdown = split_stage_component_fn(stage_name, stage_component)
        if energy == energy:
            acc[god] = acc.get(god, 0.0) + energy
            if exposed or same_element:
                add_decomposition(
                    decomposition,
                    god,
                    root=base_component,
                    momentum_month_order=momentum_component,
                    momentum_stage=stage_component,
                    momentum_stage_lu=stage_breakdown["momentum_stage_lu"],
                    momentum_stage_blade=stage_breakdown["momentum_stage_blade"],
                    momentum_stage_general=stage_breakdown["momentum_stage_general"],
                )
            else:
                add_decomposition(
                    decomposition,
                    god,
                    hidden=base_component,
                    momentum_month_order=momentum_component,
                    momentum_stage=stage_component,
                    momentum_stage_lu=stage_breakdown["momentum_stage_lu"],
                    momentum_stage_blade=stage_breakdown["momentum_stage_blade"],
                    momentum_stage_general=stage_breakdown["momentum_stage_general"],
                )
        elif logger is not None:
            logger.warning(f"[V17-PHYSICS-NAN] Attempted to add NaN energy for {god} at {pillar_label}支")
        if ledger is not None:
            parts = [f"{branch}藏{hidden_stem}→{god}"]
            if exposed:
                parts.append("透干×1.2")
            elif not same_element:
                latent_factor = get_l0_val(
                    "UNEXPOSED_MAIN_HIDDEN_FACTOR" if float(h_w) >= 0.6 else "UNEXPOSED_AUX_HIDDEN_FACTOR",
                    0.58 if float(h_w) >= 0.6 else 0.42,
                )
                parts.append(f"潜藏×{latent_factor:.2f}")
            if void_factor < 1.0:
                parts.append(f"空亡×{void_factor:.1f}")
            if abs(sm - 1.0) > 0.01:
                parts.append(f"季×{sm:.1f}")
            if stage_component > 0.0 and stage_name:
                parts.append(f"{stage_name}势×{stage_bonus_ratio:.2f}")
            if source_retention < 0.999:
                parts.append(f"源气留存×{source_retention:.2f}")
                if manifestation_mode:
                    parts.append(manifestation_mode)
            reason = f"{pillar_label}支 {'·'.join(parts)}"
            ledger.append_entry(god, acc[god], f"L0_BRANCH_{pillar_label}", reason)
