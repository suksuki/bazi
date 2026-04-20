from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "narrative_clip",
    "Layer": "L3",
    "Skill_Type": "Narrative",
    "Domain": "Logic",
    "Description": "现代叙事剪辑器。根据日主意图（Will-Proxy）生成针对性的执行建议。",
    "Rationale": "L3 层负责将深奥的物理事实“翻译”成现代决策语境下的可执行话术。"
}

DECLARED_PARAMS = {
    "SEAL_THRESHOLD": 30.0,        # 稳定性叙事所需的印星能量
    "WEALTH_THRESHOLD": 20.0,      # 扩张性叙事所需的财星能量
    "PRIORITY_STABLE": 0.85,       # 稳健策事实优先级
    "PRIORITY_AGGRESSIVE": 0.86    # 扩张事实优先级
}


def _collect_rows(deity_scores: Dict[str, float]) -> List[dict]:
    cai = float(deity_scores.get("正财", 0.0) + deity_scores.get("偏财", 0.0))
    if cai < 22:
        return []
    return [
        {
            "plugin": "narrative_clip",
            "fact": "财星信号偏强，现金流与承诺节奏需要显式对齐。",
            "label": "把资源承诺写入可验收里程碑，避免口头扩张。",
            "priority": 0.62,
            "conflict_level": 2,
        }
    ]


@dataclass
class NarrativeClipPlugin(V17PluginSpec):
    plugin_id: str = "narrative_clip"
    causal_tier: int = 2
    registry_priority: float = 0.48

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        from v17_rebirth.backend.logic.configs.manager import get_plugin_config
        cfg = get_plugin_config(self.plugin_id)
        seal_t = float(cfg.get("SEAL_THRESHOLD", DECLARED_PARAMS["SEAL_THRESHOLD"]))
        wealth_t = float(cfg.get("WEALTH_THRESHOLD", DECLARED_PARAMS["WEALTH_THRESHOLD"]))
        prio_s = float(cfg.get("PRIORITY_STABLE", DECLARED_PARAMS["PRIORITY_STABLE"]))
        prio_a = float(cfg.get("PRIORITY_AGGRESSIVE", DECLARED_PARAMS["PRIORITY_AGGRESSIVE"]))

        meta = physics_tensor.get("meta", {})
        will = meta.get("will_proxy", "stable")
        scores = deity_scores_from_tensor(physics_tensor)
        
        rows = []
        if will == "stable":
            seal = scores.get("正印", 0) + scores.get("偏印", 0)
            if seal > seal_t:
                rows.append({
                    "plugin": "narrative_clip",
                    "fact": f"Will-Proxy [Stable] 激活：当前印星能量已超阈值 {int(seal_t)}，触发深度防御提示。",
                    "label": "先校准边界与传统，再谈扩张。",
                    "priority": prio_s,
                    "meta": {"will_focus": "STABILITY"}
                })
        else:
            wealth = scores.get("正财", 0) + scores.get("偏财", 0)
            if wealth > wealth_t:
                rows.append({
                    "plugin": "narrative_clip",
                    "fact": f"Will-Proxy [Aggressive] 激活：资源能量已达标 {int(wealth_t)}，开启扩张性叙事。",
                    "label": "把资源承诺写入可验收里程碑，避免口头扩张。",
                    "priority": prio_a,
                    "meta": {"will_focus": "GROWTH"}
                })
                
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = NarrativeClipPlugin()
