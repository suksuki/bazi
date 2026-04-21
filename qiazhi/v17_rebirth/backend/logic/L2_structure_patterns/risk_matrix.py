from __future__ import annotations
from typing import Any, Dict, List
from dataclasses import dataclass
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    detect_interaction_layer,
    choose_dominant_origin_type,
    collect_origin_types_from_rows,
    infer_manifestation_state,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.core_engine.work_evidence_protocol import build_work_evidence
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import ten_god_from_stems
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

V17_SKILL_MANIFEST = {
    "id": "l2.risk.risk_matrix",
    "Layer": "L2",
    "Skill_Type": "Pattern",
    "Domain": "Risk",
    "Description": "高阶风险结构检测矩阵（羊刃/枭神/官伤等）。",
    "Rationale": "将 L0 碎化的结构冲突转化为 L2 可决策的风险叙事。"
}

DECLARED_PARAMS = {
    "BLADE_CLASH_IMPULSE": 2.2,     # 羊刃逢冲的波动倍率
    "OWL_FOOD_CAP": 0.4,           # 枭神夺食的能量封锁阈值
    "OFFICER_CRUSH_LIMIT": 0.5,     # 伤官见官的防御折损
    "OFFICER_EXHAUST_RATIO": 2.2,   # 伤官伤尽的强弱比阈值
    "OFFICER_EXHAUST_SUPPORT_MAX": 0.42,  # 官星仍有明显根气/成局时，不判伤尽
}


def _clamp_ratio(value: float, *, low: float = -0.5, high: float = 0.5) -> float:
    return max(low, min(high, float(value)))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _officer_support_relief(physics_tensor: Dict[str, Any], *, daymaster: str) -> float:
    """官杀若已获成局金势或明透支持，伤官见官不应满额打压。"""
    fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    visible_sources = [
        ("year", str(fp.get("year", "")).strip()),
        ("month", str(fp.get("month", "")).strip()),
        ("day", str(fp.get("day", "")).strip()),
        ("hour", str(fp.get("hour", "")).strip()),
        ("luck", str(physics_tensor.get("luck_pillar", "")).strip()),
        ("flow", str(physics_tensor.get("flow_pillar", "")).strip()),
    ]
    scope_weights = {
        "year": 0.35,
        "month": 0.45,
        "day": 0.25,
        "hour": 0.35,
        "luck": 0.85,
        "flow": 0.2,
    }
    support = 0.0
    for scope, gz in visible_sources:
        if len(gz) < 2:
            continue
        stem = gz[0]
        god = ten_god_from_stems(daymaster, stem)
        if god in {"正官", "七杀"}:
            support += float(scope_weights.get(scope, 0.3))

    iv2 = (physics_tensor.get("meta") or {}).get("interaction_v2") if isinstance((physics_tensor.get("meta") or {}).get("interaction_v2"), dict) else {}
    for row in iv2.get("san_he") or []:
        if not isinstance(row, dict):
            continue
        members = {str(item).strip() for item in (row.get("group") or []) if str(item).strip()}
        if {"巳", "酉", "丑"}.issubset(members):
            support += 1.2
            break

    stem_fusion_v1 = (physics_tensor.get("meta") or {}).get("stem_fusion_v1")
    cases = stem_fusion_v1.get("cases") if isinstance(stem_fusion_v1, dict) else []
    for case in cases or []:
        if not isinstance(case, dict):
            continue
        stems = [str(x).strip() for x in (case.get("stems") or []) if str(x).strip()]
        if "庚" in stems or "辛" in stems:
            support += 0.25
            break

    return _clamp01(support / 3.0)


def _formed_officer_cluster_factor(physics_tensor: Dict[str, Any]) -> float:
    """原局已成金局且运上明透官星时，官杀簇不应被单一伤官结构近乎抹平。"""
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    has_natal_metal_sanhe = False
    for row in iv2.get("san_he") or []:
        if not isinstance(row, dict):
            continue
        group = {str(item).strip() for item in (row.get("group") or []) if str(item).strip()}
        if {"巳", "酉", "丑"}.issubset(group) and str(row.get("origin_type") or "").strip().lower() == "natal":
            has_natal_metal_sanhe = True
            break
    if not has_natal_metal_sanhe:
        return 0.0

    luck_gz = str(physics_tensor.get("luck_pillar", "")).strip()
    luck_stem = luck_gz[0] if len(luck_gz) >= 2 else ""
    if luck_stem not in {"庚", "辛"}:
        return 0.0
    return 0.22 if luck_stem == "庚" else 0.18


def _origin_meta(rows: List[Dict[str, Any]], *, member_key: str, members: List[str] | None = None) -> Dict[str, Any]:
    origin_types = collect_origin_types_from_rows(rows, member_key=member_key, members=members)
    origin_type = choose_dominant_origin_type(origin_types)
    return {
        "origin_type": origin_type,
        "origin_multiplier": relation_origin_multiplier(origin_type),
    }


def _manifestation_profile(*, rows: List[Dict[str, Any]], relation_family: str, member_set: List[str] | None, origin_types: List[str]) -> Dict[str, Any]:
    has_pair = any("pair" in row and isinstance(row, dict) and row.get("pair") for row in rows)
    interaction_layer = detect_interaction_layer(
        row=rows[0] if rows else None,
        relation_family=relation_family,
        member_key="pair" if has_pair else "group",
    )
    return {
        "interaction_layer": interaction_layer,
        "manifestation_state": infer_manifestation_state(
            rows=rows,
            relation_family=relation_family,
            member_set=member_set or [],
            origin_types=origin_types,
        ),
    }


def _officer_manifestation(*, hurt: float, offist: float, relief: float, cluster: float, is_contest: bool) -> str:
    if offist >= 14.0 and hurt > 20.0 and (relief + cluster) >= 0.72:
        return "manifested"
    if offist > 10.0 and (is_contest or hurt > 25.0):
        return "supported"
    return "contested"


def _owl_manifestation(*, food: float, owl: float, scores: Dict[str, Any]) -> str:
    if food <= 0:
        return "latent"
    imbalance = owl / max(food, 1.0)
    if imbalance >= 1.5 and (float(scores.get("比肩", 0.0) or 0.0) > 18.0):
        return "supported"
    if imbalance >= 1.25:
        return "contested"
    return "latent"

@dataclass
class RiskMatrixPlugin(V17PluginSpec):
    plugin_id: str = "l2.risk.risk_matrix"
    causal_tier: int = 2

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        from v17_rebirth.backend.logic.configs.manager import get_plugin_config

        cfg = get_plugin_config(self.plugin_id)
        blade_clash_impulse = float(cfg.get("BLADE_CLASH_IMPULSE", DECLARED_PARAMS["BLADE_CLASH_IMPULSE"]))
        owl_food_cap = float(cfg.get("OWL_FOOD_CAP", DECLARED_PARAMS["OWL_FOOD_CAP"]))
        officer_crush_limit = float(cfg.get("OFFICER_CRUSH_LIMIT", DECLARED_PARAMS["OFFICER_CRUSH_LIMIT"]))
        officer_exhaust_ratio = float(cfg.get("OFFICER_EXHAUST_RATIO", DECLARED_PARAMS["OFFICER_EXHAUST_RATIO"]))
        officer_exhaust_support_max = float(
            cfg.get("OFFICER_EXHAUST_SUPPORT_MAX", DECLARED_PARAMS["OFFICER_EXHAUST_SUPPORT_MAX"])
        )

        scores = physics_tensor.get("ten_gods_absolute", {})
        meta = physics_tensor.get("meta", {})
        iv2 = meta.get("interaction_v2", {})
        results: List[V17Fact] = []
        four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(four.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        month_gz = str(four.get("month", "")).strip()
        month_branch = month_gz[1] if len(month_gz) >= 2 else ""
        officer_relief = _officer_support_relief(physics_tensor, daymaster=daymaster)
        cluster_factor = _formed_officer_cluster_factor(physics_tensor)

        def _projection_meta(target_god: str) -> Dict[str, Any]:
            projection = god_cluster_projection(
                physics_tensor=physics_tensor,
                base_god=target_god,
                day_master=daymaster,
                focus_branches=[month_branch] if month_branch else [],
            )
            return {
                "target_god": target_god,
                "projection_share": round(float((projection or {}).get(target_god, 1.0)), 4),
                "cluster_projection": projection,
            }

        # 1. 羊刃逢冲 (Blade Clash)
        clashes = iv2.get("liu_chong", [])
        found_blade = False
        if clashes:
            for cl in clashes:
                brs = cl.get("pair") or []
                if any(b in {"子", "午", "卯", "酉"} for b in brs):
                    found_blade = True
                    break
        if found_blade:
            origin_meta = _origin_meta(clashes, member_key="pair", members=["子", "午", "卯", "酉"])
            manifestation = _manifestation_profile(
                rows=clashes,
                relation_family="liu_chong",
                member_set=["子", "午", "卯", "酉"],
                origin_types=[origin_meta["origin_type"]],
            )
            match_ratio = _clamp01((0.52 + 0.08 * max(0, len(clashes) - 1)) * origin_meta["origin_multiplier"])
            results.append(V17Fact(
                plugin_id=self.plugin_id,
                text="检测到「羊刃逢冲」结构：能级存在瞬间爆发式波动风险。",
                causal_tier=self.causal_tier,
                priority=0.95,
                decision_hint="优先作为结构风险描述，不直接改写十神底数。",
                meta={
                    "impact_ratio": 0.0,
                    "observe_only": True,
                    "claim_type": "risk_observation",
                    "entity_scope": "risk",
                    "exclusivity_key": "risk:blade_clash",
                    "source_event": "blade_clash",
                    "match_ratio": round(match_ratio, 3),
                    "risk_driver": "blade_clash",
                    **manifestation,
                    **_projection_meta("比肩"),
                    "work_evidence": build_work_evidence(
                        relation_family="risk_blade_clash",
                        target_god="比肩",
                        members=["子", "午", "卯", "酉"],
                        effect_type="harm",
                        layer="branch",
                        origin_scope=str(origin_meta["origin_type"] or "natal"),
                        condition_state=str(manifestation.get("manifestation_state") or ""),
                        impact_ratio=0.0,
                        match_ratio=round(match_ratio, 3),
                        path_strength=0.16 + match_ratio * 0.28 + 0.04 * max(0, len(clashes) - 1),
                        targets=["比肩"],
                    ),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god="比肩",
                        relation_family="blade_clash",
                        relation_members=["子", "午", "卯", "酉"],
                    ),
                    **origin_meta,
                }
            ))

        # 2. 枭神夺食 (Owl Food)
        owl = float(scores.get("偏印", 0))
        food = float(scores.get("食神", 0))
        owl_threshold = max(5.0, food * (1.0 + max(0.0, owl_food_cap)))
        if food > 0.0 and owl > owl_threshold:
            manifestation_state = _owl_manifestation(food=food, owl=owl, scores=scores)
            match_ratio = _clamp01(0.45 + 0.4 * ((owl - owl_threshold) / max(owl, 1.0)))
            results.append(V17Fact(
                plugin_id=self.plugin_id,
                text="结构呈现「枭神夺食」态势：输出通道受阻，存在内耗熵增。",
                causal_tier=self.causal_tier,
                priority=0.88,
                decision_hint="优先作为结构失衡描述，不直接按食神减损结算。",
                    meta={
                        "impact_ratio": 0.0,
                        "observe_only": True,
                        "claim_type": "risk_observation",
                        "entity_scope": "risk",
                        "exclusivity_key": "risk:owl_food",
                        "source_event": "owl_food",
                        "match_ratio": round(match_ratio, 3),
                        "risk_driver": "owl_food",
                        "interaction_layer": "cross_layer",
                        "manifestation_state": manifestation_state,
                        "observe_only": True,
                        "work_evidence": build_work_evidence(
                            relation_family="risk_owl_food",
                            target_god="食神",
                            members=[],
                            effect_type="harm",
                            layer="cross_layer",
                            origin_scope="natal",
                            condition_state=manifestation_state,
                            impact_ratio=0.0,
                            match_ratio=round(match_ratio, 3),
                            path_strength=max(0.14, min(0.42, (owl - owl_threshold) / max(owl_threshold, 1.0))),
                            targets=["食神"],
                            actor_gods=["偏印"],
                            receiver_gods=["食神"],
                        ),
                        **_projection_meta("食神"),
                        "static_basis": build_static_basis(
                            physics_tensor=physics_tensor,
                            target_god="食神",
                            relation_family="owl_food",
                            relation_members=[],
                        ),
                        "origin_type": "natal",
                        "origin_multiplier": 1.0,
                    }
                ))
            food_use_bias = round(0.08 + match_ratio * 0.16, 3)
            owl_taboo_bias = round(0.07 + match_ratio * 0.14, 3)
            results.append(V17Fact(
                plugin_id=self.plugin_id,
                text="结构候选「枭印夺食」：偏印压住食神，输出路径受阻，食神更应被保护。",
                causal_tier=self.causal_tier,
                priority=0.84,
                decision_hint="此类结构不改十神底数，但会把食神推向用侧、把偏印推向忌侧。",
                meta={
                    "impact_ratio": 0.0,
                    "observe_only": True,
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "pattern_candidate": "枭印夺食",
                    "exclusivity_key": "pattern:food_output_profile",
                    "source_event": "pattern:owl_food",
                    "target_god": "食神",
                    "match_ratio": round(match_ratio, 3),
                    "risk_driver": "owl_food_pattern",
                    "interaction_layer": "cross_layer",
                    "manifestation_state": manifestation_state,
                    "intent_vector": {"食神": food_use_bias},
                    "god_ring_bias": {
                        "use_bias": {"食神": food_use_bias},
                        "taboo_bias": {"偏印": owl_taboo_bias},
                        "reason": "枭印夺食",
                    },
                    "work_evidence": build_work_evidence(
                        relation_family="owl_food_pattern",
                        target_god="食神",
                        members=[],
                        effect_type="benefit",
                        layer="cross_layer",
                        origin_scope="natal",
                        condition_state=manifestation_state,
                        impact_ratio=0.0,
                        match_ratio=round(match_ratio, 3),
                        path_strength=max(0.1, min(0.36, (owl - owl_threshold) / max(owl_threshold, 1.0))),
                        targets=["食神"],
                        counterpart_gods=["偏印"],
                        actor_gods=["偏印"],
                        receiver_gods=["食神"],
                    ),
                    **_projection_meta("食神"),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god="食神",
                        relation_family="owl_food_pattern",
                        relation_members=[],
                    ),
                    "origin_type": "natal",
                    "origin_multiplier": 1.0,
                }
            ))

        # 3. 伤官见官 (Officer See Hurt)
        hurt = float(scores.get("伤官", 0))
        offist = float(scores.get("正官", 0))
        officer_support_total = _clamp01(officer_relief + cluster_factor)
        exhaust_ratio = hurt / max(offist, 1.0)
        if hurt > 10.0 and offist > 10.0:
            overlap = min(hurt, offist)
            spread = max(hurt, offist)
            origin_meta = _origin_meta(clashes, member_key="pair")
            manifestation_state = _officer_manifestation(
                hurt=hurt,
                offist=offist,
                relief=officer_relief,
                cluster=cluster_factor,
                is_contest=offist >= 12.0 and (officer_relief + cluster_factor) >= 0.85,
            )
            if offist >= 12.0 and (officer_relief + cluster_factor) >= 0.85:
                match_ratio = _clamp01(
                    (0.46 + 0.28 * (overlap / max(spread, 1.0)))
                    * max(0.94, origin_meta["origin_multiplier"])
                    * (1.0 - 0.18 * max(0.0, min(1.0, cluster_factor)))
                )
                results.append(V17Fact(
                    plugin_id=self.plugin_id,
                    text="检测到「伤官见官」争衡态：伤官与官星互相争执，但官气已有成局与透干支撑。",
                    causal_tier=self.causal_tier,
                    priority=0.86,
                    decision_hint="此处更适合作为结构对峙描述，不宜直接按官弱受损处理。",
                    meta={
                        "impact_ratio": 0.0,
                        "observe_only": True,
                        "claim_type": "risk_observation",
                        "entity_scope": "risk",
                        "exclusivity_key": "risk:officer_hurt",
                        "source_event": "officer_hurt_contest",
                        "match_ratio": round(match_ratio, 3),
                        "risk_driver": "officer_hurt_contest",
                        "interaction_layer": "cross_layer",
                        "manifestation_state": manifestation_state,
                        "observe_only": True,
                        "officer_support_relief": round(officer_relief, 3),
                        "formed_officer_cluster_factor": round(cluster_factor, 3),
                        "work_evidence": build_work_evidence(
                            relation_family="risk_officer_hurt_contest",
                            target_god="正官",
                            members=[],
                            effect_type="disrupt",
                            layer="cross_layer",
                            origin_scope=str(origin_meta["origin_type"] or "natal"),
                            condition_state=manifestation_state,
                            impact_ratio=0.0,
                            match_ratio=round(match_ratio, 3),
                            path_strength=max(0.12, min(0.4, overlap / max(spread, 1.0))) * max(0.72, 1.0 - cluster_factor * 0.3),
                            targets=["正官"],
                            actor_gods=["伤官"],
                            receiver_gods=["正官"],
                        ),
                        **_projection_meta("正官"),
                        "static_basis": build_static_basis(
                            physics_tensor=physics_tensor,
                            target_god="正官",
                            relation_family="officer_hurt_contest",
                            relation_members=[],
                        ),
                        **origin_meta,
                    }
                ))
                pattern_match = _clamp01(
                    0.4
                    + 0.22 * (overlap / max(spread, 1.0))
                    + 0.12 * officer_support_total
                )
                taboo_bias = round(0.08 + pattern_match * 0.16, 3)
                use_bias = round(0.05 + pattern_match * 0.12 * max(0.55, officer_support_total), 3)
                results.append(V17Fact(
                    plugin_id=self.plugin_id,
                    text="结构候选「伤官见官」：伤官直撄官星，表达欲与秩序面形成持续对顶。",
                    causal_tier=self.causal_tier,
                    priority=0.84,
                    decision_hint="此类结构不直接改数值，但会把伤官推向忌侧、把正官推向用侧。",
                    meta={
                        "impact_ratio": 0.0,
                        "observe_only": True,
                        "claim_type": "pattern_candidate",
                        "entity_scope": "pattern",
                        "pattern_candidate": "伤官见官",
                        "exclusivity_key": "pattern:officer_hurt_profile",
                        "source_event": "pattern:officer_hurt_manifest",
                        "target_god": "伤官",
                        "match_ratio": round(pattern_match, 3),
                        "risk_driver": "officer_hurt_manifest",
                        "interaction_layer": "cross_layer",
                        "manifestation_state": manifestation_state,
                        "intent_vector": {"伤官": -taboo_bias},
                        "god_ring_bias": {
                            "use_bias": {"正官": use_bias},
                            "taboo_bias": {"伤官": taboo_bias},
                            "reason": "伤官见官",
                        },
                        "work_evidence": build_work_evidence(
                            relation_family="officer_hurt_manifest",
                            target_god="伤官",
                            members=[],
                            effect_type="harm",
                            layer="cross_layer",
                            origin_scope=str(origin_meta["origin_type"] or "natal"),
                            condition_state=manifestation_state,
                            impact_ratio=0.0,
                            match_ratio=round(pattern_match, 3),
                            path_strength=0.08 + pattern_match * 0.18,
                            targets=["伤官"],
                            counterpart_gods=["正官"],
                            actor_gods=["伤官"],
                            receiver_gods=["正官"],
                        ),
                        **_projection_meta("伤官"),
                        "static_basis": build_static_basis(
                            physics_tensor=physics_tensor,
                            target_god="伤官",
                            relation_family="officer_hurt_manifest",
                            relation_members=[],
                        ),
                        **origin_meta,
                    }
                ))
            else:
                match_ratio = _clamp01(
                    (0.5 + 0.35 * (overlap / max(spread, 1.0)))
                    * max(0.94, origin_meta["origin_multiplier"])
                    * (1.0 - 0.62 * officer_relief)
                    * (1.0 - cluster_factor)
                )
                results.append(V17Fact(
                    plugin_id=self.plugin_id,
                    text="检测到「伤官见官」：秩序约束与意志扩张发生剧烈摩擦。",
                    causal_tier=self.causal_tier,
                    priority=0.9,
                    decision_hint="优先作为官伤冲突描述，不直接按官星减损结算。",
                    meta={
                        "impact_ratio": 0.0,
                        "observe_only": True,
                        "claim_type": "risk_observation",
                        "entity_scope": "risk",
                        "exclusivity_key": "risk:officer_hurt",
                        "source_event": "officer_crush",
                        "match_ratio": round(match_ratio, 3),
                        "risk_driver": "officer_crush",
                        "interaction_layer": "cross_layer",
                        "manifestation_state": manifestation_state,
                        "observe_only": True,
                        "officer_support_relief": round(officer_relief, 3),
                        "formed_officer_cluster_factor": round(cluster_factor, 3),
                        "work_evidence": build_work_evidence(
                            relation_family="risk_officer_crush",
                            target_god="正官",
                            members=[],
                            effect_type="harm",
                            layer="cross_layer",
                            origin_scope=str(origin_meta["origin_type"] or "natal"),
                            condition_state=manifestation_state,
                            impact_ratio=0.0,
                            match_ratio=round(match_ratio, 3),
                            path_strength=max(0.15, min(0.45, overlap / max(spread, 1.0))) * max(0.68, 1.0 - officer_relief * 0.5),
                            targets=["正官"],
                            actor_gods=["伤官"],
                            receiver_gods=["正官"],
                        ),
                        **_projection_meta("正官"),
                        "static_basis": build_static_basis(
                            physics_tensor=physics_tensor,
                            target_god="正官",
                            relation_family="officer_crush",
                            relation_members=[],
                        ),
                        **origin_meta,
                    }
                ))
                pattern_match = _clamp01(
                    0.46
                    + 0.28 * (overlap / max(spread, 1.0))
                    + 0.1 * max(0.0, 1.0 - officer_support_total)
                )
                taboo_bias = round(0.1 + pattern_match * 0.18, 3)
                use_bias = round(0.04 + pattern_match * 0.08 * max(0.35, 1.0 - cluster_factor), 3)
                results.append(V17Fact(
                    plugin_id=self.plugin_id,
                    text="结构候选「伤官见官」：伤官冲官未尽，才性与秩序互相牵扯，易成忌点。",
                    causal_tier=self.causal_tier,
                    priority=0.86,
                    decision_hint="此类结构用于体用判断时，通常把伤官向忌侧拉动。",
                    meta={
                        "impact_ratio": 0.0,
                        "observe_only": True,
                        "claim_type": "pattern_candidate",
                        "entity_scope": "pattern",
                        "pattern_candidate": "伤官见官",
                        "exclusivity_key": "pattern:officer_hurt_profile",
                        "source_event": "pattern:officer_hurt_crush",
                        "target_god": "伤官",
                        "match_ratio": round(pattern_match, 3),
                        "risk_driver": "officer_hurt_pattern",
                        "interaction_layer": "cross_layer",
                        "manifestation_state": manifestation_state,
                        "intent_vector": {"伤官": -taboo_bias},
                        "god_ring_bias": {
                            "use_bias": {"正官": use_bias},
                            "taboo_bias": {"伤官": taboo_bias},
                            "reason": "伤官见官",
                        },
                        "work_evidence": build_work_evidence(
                            relation_family="officer_hurt_pattern",
                            target_god="伤官",
                            members=[],
                            effect_type="harm",
                            layer="cross_layer",
                            origin_scope=str(origin_meta["origin_type"] or "natal"),
                            condition_state=manifestation_state,
                            impact_ratio=0.0,
                            match_ratio=round(pattern_match, 3),
                            path_strength=0.1 + pattern_match * 0.2,
                            targets=["伤官"],
                            counterpart_gods=["正官"],
                            actor_gods=["伤官"],
                            receiver_gods=["正官"],
                        ),
                        **_projection_meta("伤官"),
                        "static_basis": build_static_basis(
                            physics_tensor=physics_tensor,
                            target_god="伤官",
                            relation_family="officer_hurt_pattern",
                            relation_members=[],
                        ),
                        **origin_meta,
                    }
                ))

        if hurt >= 18.0:
            origin_meta = _origin_meta(clashes, member_key="pair")
            exhaust_match = _clamp01(
                0.38
                + 0.22 * min(1.0, max(0.0, exhaust_ratio - 1.0) / max(officer_exhaust_ratio - 1.0, 0.2))
                + 0.18 * max(0.0, 1.0 - officer_support_total)
                + (0.08 if offist <= 10.0 else 0.0)
            )
            if (
                exhaust_ratio >= officer_exhaust_ratio
                or (offist <= 10.0 and officer_support_total <= officer_exhaust_support_max)
            ) and officer_support_total <= officer_exhaust_support_max:
                use_bias = round(0.1 + exhaust_match * 0.2, 3)
                taboo_bias = round(0.08 + exhaust_match * 0.16, 3)
                results.append(V17Fact(
                    plugin_id=self.plugin_id,
                    text="结构候选「伤官伤尽」：伤官势成一边倒，官星失去承载，才华可脱束外放。",
                    causal_tier=self.causal_tier,
                    priority=0.87,
                    decision_hint="此类结构会把伤官推向喜用，把正官推向忌侧，但仍不直接改十神底数。",
                    meta={
                        "impact_ratio": 0.0,
                        "observe_only": True,
                        "claim_type": "pattern_candidate",
                        "entity_scope": "pattern",
                        "pattern_candidate": "伤官伤尽",
                        "exclusivity_key": "pattern:officer_hurt_profile",
                        "source_event": "pattern:officer_hurt_exhaust",
                        "target_god": "伤官",
                        "match_ratio": round(exhaust_match, 3),
                        "risk_driver": "officer_hurt_exhaust",
                        "interaction_layer": "cross_layer",
                        "manifestation_state": "manifested" if officer_support_total <= 0.25 else "supported",
                        "intent_vector": {"伤官": use_bias},
                        "god_ring_bias": {
                            "use_bias": {"伤官": use_bias},
                            "taboo_bias": {"正官": taboo_bias},
                            "reason": "伤官伤尽",
                        },
                        "officer_support_relief": round(officer_relief, 3),
                        "formed_officer_cluster_factor": round(cluster_factor, 3),
                        "exhaust_ratio": round(exhaust_ratio, 3),
                        "work_evidence": build_work_evidence(
                            relation_family="officer_hurt_exhaust",
                            target_god="伤官",
                            members=[],
                            effect_type="benefit",
                            layer="cross_layer",
                            origin_scope=str(origin_meta["origin_type"] or "natal"),
                            condition_state="manifested" if officer_support_total <= 0.25 else "supported",
                            impact_ratio=0.0,
                            match_ratio=round(exhaust_match, 3),
                            path_strength=0.12 + exhaust_match * 0.2,
                            targets=["伤官"],
                            counterpart_gods=["正官"],
                            actor_gods=["伤官"],
                            receiver_gods=["正官"],
                        ),
                        **_projection_meta("伤官"),
                        "static_basis": build_static_basis(
                            physics_tensor=physics_tensor,
                            target_god="伤官",
                            relation_family="officer_hurt_exhaust",
                            relation_members=[],
                        ),
                        **origin_meta,
                    }
                ))

        return results

PLUGIN = RiskMatrixPlugin()
