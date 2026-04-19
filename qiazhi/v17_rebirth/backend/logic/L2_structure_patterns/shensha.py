from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    choose_dominant_origin_type,
    collect_origin_types_from_rows,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "shensha",
    "Layer": "L2",
    "Skill_Type": "Pattern",
    "Domain": "Aura",
    "Description": "把传统神煞语义压缩为可量化的物理场强 Buff/Debuff。",
    "Rationale": "神煞是 L2 级的场变量修正项，它并不改变 L0/L1 的质量与矢量，但改变外部压力的感知强度。"
}

DECLARED_PARAMS = {
    "TIAN_YI_THRESHOLD": 40.0,     # 天乙显化所需正印能量
    "YANG_REN_THRESHOLD": 45.0,     # 羊刃显化所需劫财能量
    "RESISTANCE_BUFF": 0.1,         # 天乙抗性加成比例
    "TENSION_MULTIPLIER": 1.4,      # 羊刃张力乘数
    "PRIORITY_BASE": 0.94           # 事实输出优先级
}


def _collect_rows(deity_scores: Dict[str, float], cfg: Dict[str, Any] = {}) -> List[dict]:
    tian_yi_t = float(cfg.get("TIAN_YI_THRESHOLD", DECLARED_PARAMS["TIAN_YI_THRESHOLD"]))
    yang_ren_t = float(cfg.get("YANG_REN_THRESHOLD", DECLARED_PARAMS["YANG_REN_THRESHOLD"]))
    res_buff = float(cfg.get("RESISTANCE_BUFF", DECLARED_PARAMS["RESISTANCE_BUFF"]))
    tens_mul = float(cfg.get("TENSION_MULTIPLIER", DECLARED_PARAMS["TENSION_MULTIPLIER"]))
    prio = float(cfg.get("PRIORITY_BASE", DECLARED_PARAMS["PRIORITY_BASE"]))

    has_tian_yi = deity_scores.get("正印", 0) > tian_yi_t
    has_yang_ren = deity_scores.get("劫财", 0) > yang_ren_t
    
    rows = []
    if has_tian_yi:
        rows.append({
            "plugin": "shensha",
            "fact": f"天乙贵人显化：所在柱抗性 (Resistance) 额外提升 {int(res_buff*100)}%。",
            "label": "护持/守御为主",
            "priority": prio + 0.01,
            "meta": {"resistance_buff": res_buff, "gate": "TIAN_YI_BUFF"}
        })
    if has_yang_ren:
        rows.append({
            "plugin": "shensha",
            "fact": f"羊刃显化：所在场压张力系数 x {tens_mul}。",
            "label": "校准节奏，防范剧烈冲突",
            "priority": prio,
            "meta": {"tension_multiplier": tens_mul, "gate": "YANG_REN_STRESS"}
        })
    return rows


def _shensha_origin_meta(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    origins: List[str] = []
    origins.extend(collect_origin_types_from_rows(iv2.get("liu_chong") or [], member_key="pair"))
    origins.extend(collect_origin_types_from_rows(iv2.get("liu_hai") or [], member_key="pair"))
    origins.extend(collect_origin_types_from_rows(iv2.get("liu_po") or [], member_key="pair"))
    origin_type = choose_dominant_origin_type(origins) if origins else "natal"
    return {
        "origin_type": origin_type,
        "origin_multiplier": relation_origin_multiplier(origin_type),
    }


@dataclass
class ShenshaPlugin(V17PluginSpec):
    plugin_id: str = "shensha"
    causal_tier: int = 3
    registry_priority: float = 0.52

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        from v17_rebirth.backend.logic.configs.manager import get_plugin_config
        cfg = get_plugin_config(self.plugin_id)
        scores = deity_scores_from_tensor(physics_tensor)
        origin_meta = _shensha_origin_meta(physics_tensor)
        rows = _collect_rows(scores, cfg)
        for row in rows:
            if not isinstance(row.get("meta"), dict):
                row["meta"] = {}
            row["meta"]["origin_type"] = origin_meta["origin_type"]
            row["meta"]["origin_multiplier"] = round(float(origin_meta["origin_multiplier"]), 3)
            base_match = float(row["meta"].get("match_ratio", 0.72) or 0.72)
            row["meta"]["match_ratio"] = round(min(0.86, base_match * max(0.9, float(origin_meta["origin_multiplier"]))), 3)
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = ShenshaPlugin()
