from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    detect_interaction_layer,
    infer_manifestation_state,
    relation_effect_multiplier,
    relation_origin_multiplier,
    summarize_relation_conditions,
)
from v17_rebirth.backend.logic.configs.manager import get_plugin_config
from v17_rebirth.backend.logic.core_engine.work_evidence_protocol import build_work_evidence
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_branch_sanhui",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "地支三会方局成势算法。",
    "Rationale": "三会不同于三合，强调同一方位连续三支汇成背景势能。"
}

DECLARED_PARAMS = {
    "MEETING_GAIN": 1.65,
    "SOURCE_RETENTION": 0.72,
    "MIN_MEETING_STRENGTH": 0.55,
}


def _daymaster(physics_tensor: Dict[str, Any]) -> str:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    day_gz = str(four.get("day", "")).strip()
    return day_gz[0] if len(day_gz) >= 2 else "壬"


def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    hits = iv2.get("san_hui") if isinstance(iv2.get("san_hui"), list) else []
    if not hits:
        return []

    cfg = get_plugin_config("l1.physics.op_branch_sanhui")
    meeting_gain = float(cfg.get("MEETING_GAIN", DECLARED_PARAMS["MEETING_GAIN"]))
    source_retention = float(cfg.get("SOURCE_RETENTION", DECLARED_PARAMS["SOURCE_RETENTION"]))
    min_strength = float(cfg.get("MIN_MEETING_STRENGTH", DECLARED_PARAMS["MIN_MEETING_STRENGTH"]))
    daymaster = _daymaster(physics_tensor)
    rows: List[dict] = []

    for hit in hits:
        if not isinstance(hit, dict):
            continue
        branches = [str(item) for item in (hit.get("matched_branches") or hit.get("group") or []) if str(item).strip()]
        if len(set(branches)) < 3:
            continue
        strength = float(hit.get("strength") or 1.0)
        if strength < min_strength:
            continue
        ordered_group = [str(item) for item in (hit.get("ordered_group") or hit.get("group") or branches) if str(item).strip()]
        pivot_branch = str(hit.get("pivot_branch") or hit.get("mid_branch") or "")
        if not pivot_branch and len(ordered_group) >= 2:
            pivot_branch = ordered_group[1]
        if not pivot_branch:
            pivot_branch = branches[0]
        target_god = _branch_dominant_ten_god(pivot_branch, daymaster) or "核心"
        condition = summarize_relation_conditions(
            relation_family="sanhui",
            pair_or_group=ordered_group or branches,
            interaction_v2=iv2,
        )
        condition_state = str(condition.get("condition_state") or "supported")
        condition_multiplier = relation_effect_multiplier(condition_state)
        origin_type = str(condition.get("origin_type") or hit.get("origin_type") or "natal")
        origin_multiplier = relation_origin_multiplier(origin_type)
        interaction_layer = detect_interaction_layer(hit, relation_family="sanhui", member_key="group")
        manifestation_state = infer_manifestation_state(
            rows=[hit],
            relation_family="sanhui",
            member_set=branches,
            origin_types=[origin_type],
        )
        impact_ratio = (meeting_gain - 1.0) * max(0.55, strength) * condition_multiplier * origin_multiplier
        match_ratio = max(
            0.0,
            min(
                0.94,
                (0.42 + 0.42 * min(1.0, strength)) * max(0.55, condition_multiplier) * origin_multiplier,
            ),
        )
        actor_members = [branch for branch in branches if branch != pivot_branch] or list(branches)
        receiver_members = [pivot_branch] if pivot_branch else branches[:1]
        rows.append(
            {
                "plugin": "l1.physics.op_branch_sanhui",
                "fact": f"三会成势：{'/'.join(ordered_group or branches)} 汇成方局，{target_god} 被背景会气持续推高（{manifestation_state}）。",
                "label": "先承认方气背景，再看冲合刑害是否打断显化。",
                "priority": round(min(0.98, 0.755 + 0.14 * max(0.0, min(1.0, strength))), 3),
                "meta": {
                    "target_god": target_god,
                    "meeting_strength": round(strength, 3),
                    "source_retention": round(source_retention, 3),
                    "impact_ratio": round(impact_ratio, 3) if condition_state == "supported" else 0.0,
                    "match_ratio": round(match_ratio, 3),
                    "condition_state": condition_state,
                    "condition_blockers": list(condition.get("blockers") or []),
                    "condition_multiplier": condition_multiplier,
                    "origin_type": origin_type,
                    "origin_multiplier": round(origin_multiplier, 3),
                    "interaction_layer": interaction_layer,
                    "manifestation_state": manifestation_state,
                    "relation_family": "sanhui",
                    "meeting_group": ordered_group or branches,
                    "pivot_branch": pivot_branch,
                    "element": str(hit.get("element") or ""),
                    "work_evidence": build_work_evidence(
                        relation_family="sanhui",
                        target_god=target_god,
                        members=ordered_group or branches,
                        actor_members=actor_members,
                        receiver_members=receiver_members,
                        effect_type="benefit",
                        layer=interaction_layer,
                        origin_scope=origin_type,
                        condition_state=condition_state,
                        impact_ratio=impact_ratio if condition_state == "supported" else 0.0,
                        match_ratio=match_ratio,
                        path_strength=abs(impact_ratio) * max(0.7, strength),
                        targets=[target_god],
                    ),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=target_god,
                        relation_family="sanhui",
                        relation_members=ordered_group or branches,
                    ),
                },
            }
        )
    return rows


@dataclass
class ThreeMeetingPlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_sanhui"
    causal_tier: int = 4
    registry_priority: float = 0.69

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(
            _collect_rows(physics_tensor),
            causal_tier=self.causal_tier,
            default_plugin_id=self.plugin_id,
        )


PLUGIN = ThreeMeetingPlugin()
