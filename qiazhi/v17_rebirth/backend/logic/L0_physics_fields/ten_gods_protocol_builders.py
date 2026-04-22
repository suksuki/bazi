from __future__ import annotations

from typing import Any, Callable, Dict, List


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
