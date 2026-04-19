from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
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
}


def _clamp_ratio(value: float, *, low: float = -0.5, high: float = 0.5) -> float:
    return max(low, min(high, float(value)))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

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

        scores = physics_tensor.get("ten_gods_absolute", {})
        meta = physics_tensor.get("meta", {})
        iv2 = meta.get("interaction_v2", {})
        results: List[V17Fact] = []

        # 1. 羊刃逢冲 (Blade Clash)
        clashes = iv2.get("liu_chong", [])
        if clashes:
            found_blade = False
            for cl in clashes:
                brs = cl.get("pair") or []
                if any(b in {"子", "午", "卯", "酉"} for b in brs):
                    found_blade = True
                    break
            if found_blade:
                blade_ratio = _clamp_ratio(blade_clash_impulse / 10.0, low=0.05, high=0.4)
                match_ratio = _clamp01(0.55 + 0.12 * len(clashes))
                results.append(V17Fact(
                    plugin_id=self.plugin_id,
                    text="检测到「羊刃逢冲」结构：能级存在瞬间爆发式波动风险。",
                    causal_tier=self.causal_tier,
                    priority=0.95,
                    decision_hint="建议配置【动态平衡阀】，防止系统因应力过大崩溃。",
                    meta={
                        "impact_ratio": round(blade_ratio, 2),
                        "match_ratio": round(match_ratio, 3),
                        "target_god": "比肩",
                        "risk_driver": "blade_clash",
                    }
                ))

        # 2. 枭神夺食 (Owl Food)
        owl = float(scores.get("偏印", 0))
        food = float(scores.get("食神", 0))
        owl_threshold = max(5.0, food * (1.0 + max(0.0, owl_food_cap)))
        if food > 0.0 and owl > owl_threshold:
            match_ratio = _clamp01((owl - owl_threshold) / max(food, 1.0))
            results.append(V17Fact(
                plugin_id=self.plugin_id,
                text="结构呈现「枭神夺食」态势：输出通道受阻，存在内耗熵增。",
                causal_tier=self.causal_tier,
                priority=0.88,
                decision_hint="优先疏通【偏财】通路缓解压制。",
                    meta={
                        "impact_ratio": round(-_clamp_ratio(owl_food_cap, low=0.05, high=0.4), 2),
                        "match_ratio": round(match_ratio, 3),
                        "target_god": "食神",
                        "risk_driver": "owl_food",
                    }
                ))

        # 3. 伤官见官 (Officer See Hurt)
        hurt = float(scores.get("伤官", 0))
        offist = float(scores.get("正官", 0))
        if hurt > 10.0 and offist > 10.0:
            overlap = min(hurt, offist)
            spread = max(hurt, offist)
            match_ratio = _clamp01(overlap / max(spread, 1.0))
            results.append(V17Fact(
                plugin_id=self.plugin_id,
                text="检测到「伤官见官」：秩序约束与意志扩张发生剧烈摩擦。",
                causal_tier=self.causal_tier,
                priority=0.9,
                decision_hint="引入【印星】进行调和调停；避免在当前时点发起系统性改革。",
                    meta={
                        "impact_ratio": round(-_clamp_ratio(officer_crush_limit, low=0.1, high=0.5), 2),
                        "match_ratio": round(match_ratio, 3),
                        "target_god": "正官",
                        "risk_driver": "officer_crush",
                    }
                ))

        return results

PLUGIN = RiskMatrixPlugin()
