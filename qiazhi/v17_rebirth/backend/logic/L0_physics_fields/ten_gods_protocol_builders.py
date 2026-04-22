from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple


def build_projection_bridge_protocol(
    *,
    cross_polarity_root_support_factor: float,
    exact_exposed_hidden_gain: float,
    rooted_gain_cap: float,
) -> Dict[str, Any]:
    return {
        "tonggen_direction": "stem<-branch_hidden",
        "tougan_direction": "branch_hidden->visible_stem",
        "same_element_first": True,
        "polarity_second": True,
        "exact_root_support_factor": 1.0,
        "cross_polarity_root_support_factor": cross_polarity_root_support_factor,
        "exact_exposed_hidden_gain": exact_exposed_hidden_gain,
        "same_element_visible_relief": 1.0,
        "rooted_gain_cap": rooted_gain_cap,
        "single_pass_coupling": True,
        "recursive_feedback": False,
        "protocol": "frozen_evidence_single_pass",
    }


def _relation_dynamic_label(
    trace: Dict[str, Any],
    relation_family_label: Callable[[str, str], str],
) -> str:
    kind = str(trace.get("kind") or "").strip()
    family_key = str(trace.get("family_key") or kind).strip()
    if family_key in {"sanhui", "sanhe", "banhe_shengwang", "banhe_muwang", "gonghe", "liuhe", "anhe"}:
        return relation_family_label(family_key, str(trace.get("relation_element") or ""))
    mapping = {
        "chong": "六冲",
        "xing": "三刑",
        "hai": "六害",
        "po": "六破",
        "ke": "相克传导",
        "stem_fusion_transform": "天干五合化气",
        "stem_fusion_stuck": "天干五合羁绊",
    }
    return mapping.get(kind, kind or "关系动态")


def build_relation_dynamics_summary(
    *,
    relation_traces: List[Dict[str, Any]],
    relation_family_label: Callable[[str, str], str],
    relation_trace_formation_ratio: Callable[[Dict[str, Any]], float],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    structured_families = {"sanhui", "sanhe", "banhe_shengwang", "banhe_muwang", "gonghe", "liuhe", "anhe"}
    stability_gain_base = {
        "sanhui": 0.34,
        "sanhe": 0.28,
        "banhe_shengwang": 0.24,
        "banhe_muwang": 0.20,
        "gonghe": 0.16,
        "liuhe": 0.26,
        "anhe": 0.12,
    }
    free_lock_base = {
        "sanhui": 0.12,
        "sanhe": 0.18,
        "banhe_shengwang": 0.20,
        "banhe_muwang": 0.22,
        "gonghe": 0.18,
        "liuhe": 0.28,
        "anhe": 0.24,
    }
    for trace in relation_traces:
        if not isinstance(trace, dict):
            continue
        kind = str(trace.get("kind") or "").strip()
        family_key = str(trace.get("family_key") or kind).strip()
        members = [str(item).strip() for item in (trace.get("members") or []) if str(item).strip()]
        if not kind or not members:
            continue
        details = trace.get("details") if isinstance(trace.get("details"), dict) else {}
        closeness = max(0.0, min(1.0, float(details.get("closeness") or 0.72)))
        conflict_damping = max(0.0, min(1.0, float(trace.get("conflict_damping") or 1.0)))
        visible_support = max(0.0, min(1.0, float(details.get("visible_support_strength") or 0.0)))
        formation_ratio = relation_trace_formation_ratio(trace) if family_key in structured_families else 0.0
        intensity = abs(float(trace.get("intensity") or 0.0))

        energy_axis = "组织化"
        energy_effect_ratio = 0.0
        stability_delta_ratio = 0.0
        free_energy_lock_ratio = 0.0
        note = ""

        if family_key in structured_families:
            energy_axis = "绑定" if family_key in {"liuhe", "anhe"} else "组织化"
            energy_effect_ratio = max(0.0, min(1.0, 0.16 + formation_ratio * 0.46 + visible_support * 0.14))
            stability_delta_ratio = max(
                0.0,
                min(
                    0.78,
                    stability_gain_base.get(family_key, 0.18) + formation_ratio * 0.26 * max(0.42, conflict_damping),
                ),
            )
            free_energy_lock_ratio = max(
                0.0,
                min(0.72, free_lock_base.get(family_key, 0.18) + formation_ratio * 0.24),
            )
            if family_key == "anhe":
                note = "暗合偏蛰伏，结构成形但自由能释放较低。"
            elif family_key == "liuhe":
                note = "六合偏绑定，稳定性常升，但可用自由能容易被锁住。"
            else:
                note = "合局更像组织化与重分配，不等于总能量线性增加。"
        elif kind == "stem_fusion_transform":
            manifestation_mode = str(details.get("manifestation_mode") or "明化").strip()
            support_score = max(0.0, min(1.0, float(details.get("support_score") or 0.0)))
            interference = max(0.0, min(1.0, float(details.get("interference_score") or 0.0)))
            energy_axis = "转化"
            energy_effect_ratio = max(0.0, min(1.0, 0.22 + support_score * 0.42 - interference * 0.16))
            stability_delta_ratio = max(0.0, min(0.52, 0.10 + support_score * 0.18 - interference * 0.12))
            free_energy_lock_ratio = max(0.0, min(0.58, 0.18 + support_score * 0.20))
            note = "明化" if manifestation_mode == "明化" else "暗化蛰伏"
        elif kind == "stem_fusion_stuck":
            support_score = max(0.0, min(1.0, float(details.get("support_score") or 0.0)))
            interference = max(0.0, min(1.0, float(details.get("interference_score") or 0.0)))
            energy_axis = "羁绊"
            energy_effect_ratio = max(0.0, min(1.0, 0.10 + support_score * 0.18 + interference * 0.20))
            stability_delta_ratio = -max(0.10, min(0.52, 0.14 + interference * 0.28))
            free_energy_lock_ratio = max(0.18, min(0.72, 0.24 + support_score * 0.18))
            note = "有支撑但被争合或支扰卡住。"
        elif kind == "chong":
            energy_axis = "激发"
            energy_effect_ratio = max(0.20, min(0.88, 0.24 + closeness * 0.34 + intensity * 2.2))
            stability_delta_ratio = -max(0.48, min(0.92, 0.52 + closeness * 0.24))
            note = "冲不等于没能量，而是把静态资源推成动态事件。"
        elif kind == "xing":
            energy_axis = "内耗"
            energy_effect_ratio = max(0.10, min(0.62, 0.12 + closeness * 0.18 + intensity * 1.6))
            stability_delta_ratio = -max(0.26, min(0.68, 0.30 + closeness * 0.16))
            note = "刑更像结构扭曲，总能量未必小，但有效输出打折。"
        elif kind == "hai":
            energy_axis = "暗损"
            energy_effect_ratio = max(0.08, min(0.46, 0.10 + closeness * 0.14 + intensity * 1.2))
            stability_delta_ratio = -max(0.24, min(0.58, 0.26 + closeness * 0.12))
            note = "害偏慢性损耗，效率和结果先打折。"
        elif kind == "po":
            energy_axis = "解构"
            energy_effect_ratio = max(0.14, min(0.72, 0.16 + closeness * 0.18 + intensity * 1.7))
            stability_delta_ratio = -max(0.42, min(0.86, 0.48 + closeness * 0.18))
            note = "破更像拆结构，原有组织性掉得最快。"
        elif kind == "ke":
            energy_axis = "压制转移"
            energy_effect_ratio = max(0.16, min(0.72, 0.18 + closeness * 0.18 + intensity * 1.5))
            stability_delta_ratio = -max(0.12, min(0.42, 0.14 + closeness * 0.10))
            note = "克不是归零，而是方向性压制与能量转移。"
        else:
            continue

        rows.append(
            {
                "label": _relation_dynamic_label(
                    trace,
                    relation_family_label=relation_family_label,
                ),
                "kind": kind,
                "family_key": family_key,
                "members": members,
                "pillars": [str(item).strip() for item in (trace.get("pillars") or []) if str(item).strip()],
                "energy_axis": energy_axis,
                "energy_effect_ratio": round(max(0.0, min(1.0, energy_effect_ratio)), 4),
                "stability_delta_ratio": round(max(-1.0, min(1.0, stability_delta_ratio)), 4),
                "free_energy_lock_ratio": round(max(0.0, min(1.0, free_energy_lock_ratio)), 4),
                "note": note,
            }
        )

    rows.sort(
        key=lambda row: (
            abs(float(row.get("stability_delta_ratio") or 0.0)) + float(row.get("energy_effect_ratio") or 0.0),
            float(row.get("free_energy_lock_ratio") or 0.0),
        ),
        reverse=True,
    )
    return rows[:12]


def _relation_role_label(role: str) -> str:
    normalized = str(role or "").strip().lower()
    if normalized == "pivot":
        return "中神"
    if normalized == "tomb":
        return "墓库"
    return "长生"


def _relation_unique_members(members: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in members:
        branch = str(item or "").strip()
        if not branch or branch in seen:
            continue
        seen.add(branch)
        out.append(branch)
    return out


def _relation_projection_preview(weights: Dict[str, float]) -> List[str]:
    total = sum(max(0.0, float(v or 0.0)) for v in weights.values())
    if total <= 0.0:
        return []
    ranked = sorted(
        (
            (str(god).strip(), max(0.0, float(weight or 0.0)) / total)
            for god, weight in weights.items()
            if str(god).strip() and max(0.0, float(weight or 0.0)) > 0.0
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return [f"{god}{round(share * 100):.0f}%" for god, share in ranked[:2]]


def _relation_duplicate_notes(
    *,
    branch_counts: Dict[str, Any],
    role_map: Dict[str, Any],
    relation_duplicate_role_bonus: Callable[[str], float],
) -> List[str]:
    notes: List[str] = []
    for branch, raw_count in (branch_counts or {}).items():
        extra_count = max(0, int(raw_count or 0) - 1)
        if extra_count <= 0:
            continue
        role = _relation_role_label(str((role_map or {}).get(branch) or "starter"))
        bonus = relation_duplicate_role_bonus(str((role_map or {}).get(branch) or "starter")) * extra_count
        notes.append(f"{branch}{role}+{round(bonus * 100):.0f}%")
    return notes


def _relation_manifestation_mode(family_key: str, visible_support_strength: float) -> str:
    normalized = str(family_key or "").strip()
    if normalized == "anhe":
        return "暗化"
    return "明化" if float(visible_support_strength or 0.0) >= 0.18 else "暗化"


def _relation_summary_status(
    *,
    formation_ratio: float,
    completion: float,
    conflict_damping: float,
) -> str:
    if completion < 0.999:
        return "候选未全"
    if formation_ratio >= 0.84 and conflict_damping >= 0.9:
        return "强成局"
    if conflict_damping < 0.75:
        return "受扰成局"
    if formation_ratio >= 0.56:
        return "成局"
    return "弱成局"


def build_relation_formation_summary(
    *,
    relation_traces: List[Dict[str, Any]],
    structural_bonuses: List[Dict[str, Any]],
    relation_visible_bonuses: List[Dict[str, Any]],
    relation_source_attenuations: List[Dict[str, Any]],
    relation_family_label: Callable[[str, str], str],
    relation_base_factor: Callable[[str], float],
    relation_full_clean_factor: Callable[[str], float],
    relation_root_intensity: Callable[..., float],
    relation_duplicate_role_bonus: Callable[[str], float],
) -> List[Dict[str, Any]]:
    structural_index: Dict[Tuple[str, Tuple[str, ...]], Dict[str, Any]] = {}
    for row in structural_bonuses:
        if not isinstance(row, dict):
            continue
        family_key = str(row.get("kind") or "").strip()
        members = tuple(str(x) for x in (row.get("matched_branches") or row.get("group") or []) if str(x).strip())
        if not family_key or not members:
            continue
        structural_index[(family_key, members)] = row

    visible_index: Dict[Tuple[str, Tuple[str, ...]], Dict[str, Any]] = {}
    for row in relation_visible_bonuses:
        if not isinstance(row, dict):
            continue
        family_key = str(row.get("family_key") or row.get("kind") or "").strip()
        members = tuple(str(x) for x in (row.get("members") or []) if str(x).strip())
        if not family_key or not members:
            continue
        entry = visible_index.setdefault(
            (family_key, members),
            {"bonus_total": 0.0, "projection_weights": {}, "dominant_hidden_stem": ""},
        )
        entry["bonus_total"] = float(entry.get("bonus_total") or 0.0) + float(row.get("bonus_total") or 0.0)
        if not entry.get("dominant_hidden_stem"):
            entry["dominant_hidden_stem"] = str(row.get("dominant_hidden_stem") or "")
        projection = row.get("projection") if isinstance(row.get("projection"), dict) else {}
        for god, share in projection.items():
            weight = max(0.0, float(share or 0.0)) * float(row.get("bonus_total") or 0.0)
            entry["projection_weights"][str(god)] = float(entry["projection_weights"].get(str(god), 0.0)) + weight

    attenuation_index: Dict[Tuple[str, Tuple[str, ...]], Dict[str, Any]] = {}
    for row in relation_source_attenuations:
        if not isinstance(row, dict):
            continue
        family_key = str(row.get("family_key") or "").strip()
        members = tuple(str(x) for x in (row.get("members") or []) if str(x).strip())
        if not family_key or not members:
            continue
        attenuation_index[(family_key, members)] = row

    summary_rows: List[Dict[str, Any]] = []
    valid_families = {"sanhui", "sanhe", "banhe_shengwang", "banhe_muwang", "gonghe", "liuhe", "anhe"}
    for trace in relation_traces:
        if not isinstance(trace, dict):
            continue
        family_key = str(trace.get("family_key") or trace.get("kind") or "").strip()
        if family_key not in valid_families:
            continue
        intensity = max(0.0, float(trace.get("intensity") or 0.0))
        if intensity <= 0.0:
            continue
        members = [str(x) for x in (trace.get("members") or []) if str(x).strip()]
        if not members:
            continue
        relation_element = str(trace.get("relation_element") or "")
        details = trace.get("details") if isinstance(trace.get("details"), dict) else {}
        display_members = _relation_unique_members(
            [str(x) for x in (details.get("ordered_group") or members) if str(x).strip()]
        )
        if not display_members:
            display_members = _relation_unique_members(members)
        members_key = tuple(members)
        structural = structural_index.get((family_key, members_key), {})
        visible = visible_index.get((family_key, members_key), {})
        family_factor = max(
            relation_base_factor(family_key),
            float(details.get("effective_family_factor") or structural.get("family_factor") or relation_full_clean_factor(family_key)),
        )
        clean_intensity = relation_root_intensity(
            family_key=family_key,
            closeness=1.0,
            strength=1.0,
            completion=1.0,
            duplicate_bonus=0.0,
            conflict_damping=1.0,
        )
        formation_ratio = intensity / clean_intensity if clean_intensity > 0.0 else 0.0
        formation_ratio = max(0.0, min(1.0, formation_ratio))
        formation_percent = round(formation_ratio * 100.0, 1)
        completion = max(0.0, min(1.0, float(trace.get("completion") or 1.0)))
        conflict_damping = max(0.0, min(1.0, float(trace.get("conflict_damping") or 1.0)))
        duplicate_bonus = max(0.0, float(trace.get("duplicate_bonus") or 0.0))
        closeness = max(0.0, float(details.get("closeness") or 0.0))
        strength = max(0.0, float(details.get("strength") or 0.0))
        visible_support_strength = max(
            0.0,
            min(
                1.0,
                float(details.get("visible_support_strength") or structural.get("visible_support_strength") or 0.0),
            ),
        )
        structure_bonus_total = max(0.0, float(structural.get("bonus_total") or 0.0))
        visible_bonus_total = max(0.0, float(visible.get("bonus_total") or 0.0))
        attenuation = attenuation_index.get((family_key, members_key), {})
        source_retention_ratio = max(0.0, min(1.0, float(attenuation.get("source_retention_ratio") or 1.0)))
        source_release_ratio = max(0.0, min(1.0, float(attenuation.get("source_release_ratio") or 0.0)))
        manifestation_mode = str(attenuation.get("manifestation_mode") or _relation_manifestation_mode(family_key, visible_support_strength))
        projection_weights: Dict[str, float] = {}
        structural_projection = structural.get("projection") if isinstance(structural.get("projection"), dict) else {}
        for god, share in structural_projection.items():
            projection_weights[str(god)] = float(projection_weights.get(str(god), 0.0)) + max(0.0, float(share or 0.0)) * structure_bonus_total
        for god, weight in (visible.get("projection_weights") or {}).items():
            projection_weights[str(god)] = float(projection_weights.get(str(god), 0.0)) + max(0.0, float(weight or 0.0))
        projection_preview = _relation_projection_preview(projection_weights)
        branch_counts = details.get("branch_counts") if isinstance(details.get("branch_counts"), dict) else {}
        role_map = details.get("role_map") if isinstance(details.get("role_map"), dict) else {}
        duplicate_notes = _relation_duplicate_notes(
            branch_counts=branch_counts,
            role_map=role_map,
            relation_duplicate_role_bonus=relation_duplicate_role_bonus,
        )
        title = f"{''.join(display_members)}{relation_family_label(family_key, relation_element)}"
        details_fragments = [f"基准x{family_factor:.2f}"]
        if manifestation_mode == "暗化":
            details_fragments.append("暗化蛰伏")
        if visible_support_strength > 0.0:
            details_fragments.append(f"透干支撑{round(visible_support_strength * 100):.0f}%")
        if source_release_ratio > 0.0:
            details_fragments.append(f"源气保留{round(source_retention_ratio * 100):.0f}%")
        if structure_bonus_total > 0.0:
            details_fragments.append(f"结构+{structure_bonus_total:.1f}")
        if visible_bonus_total > 0.0:
            details_fragments.append(f"显神+{visible_bonus_total:.1f}")
        if duplicate_notes:
            details_fragments.append(f"重支{'/'.join(duplicate_notes[:2])}")
        if closeness > 0.0 and closeness < 0.995:
            details_fragments.append(f"远近{round(closeness * 100):.0f}%")
        if strength > 0.0 and abs(strength - 1.0) > 0.02:
            details_fragments.append(f"局势{round(strength * 100):.0f}%")
        if conflict_damping < 0.995:
            details_fragments.append(f"受扰保留{round(conflict_damping * 100):.0f}%")
        if projection_preview:
            details_fragments.append(f"主投影{' / '.join(projection_preview)}")
        summary_rows.append(
            {
                "family_key": family_key,
                "family_label": relation_family_label(family_key, relation_element),
                "formation_label": title,
                "formation_ratio": round(formation_ratio, 4),
                "formation_percent": formation_percent,
                "status": _relation_summary_status(
                    formation_ratio=formation_ratio,
                    completion=completion,
                    conflict_damping=conflict_damping,
                ),
                "relation_element": relation_element,
                "members": members,
                "display_members": display_members,
                "family_factor": round(family_factor, 3),
                "intensity": round(intensity, 4),
                "completion": round(completion, 4),
                "duplicate_bonus": round(duplicate_bonus, 4),
                "duplicate_notes": duplicate_notes,
                "conflict_damping": round(conflict_damping, 4),
                "visible_support_strength": round(visible_support_strength, 4),
                "manifestation_mode": manifestation_mode,
                "source_retention_ratio": round(source_retention_ratio, 4),
                "source_release_ratio": round(source_release_ratio, 4),
                "closeness": round(closeness, 4) if closeness > 0.0 else 0.0,
                "strength": round(strength, 4) if strength > 0.0 else 0.0,
                "structure_bonus_total": round(structure_bonus_total, 3),
                "visible_bonus_total": round(visible_bonus_total, 3),
                "projection_preview": projection_preview,
                "summary": f"{title} {formation_percent:.1f}%（" + "，".join(details_fragments[:5]) + "）",
            }
        )

    summary_rows.sort(
        key=lambda row: (
            float(row.get("formation_percent") or 0.0),
            float(row.get("family_factor") or 0.0),
            float(row.get("structure_bonus_total") or 0.0) + float(row.get("visible_bonus_total") or 0.0),
        ),
        reverse=True,
    )
    return summary_rows[:8]
