from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "officer_see_hurt",
    "Layer": "L2",
    "Skill_Type": "Pattern",
    "Domain": "Risk",
    "Description": "检测正官与伤官同时偏强时的秩序—表达摩擦。",
    "Rationale": "经典「做功」冲突对，不仅产生能级损耗，更是心理叙事层面的防线崩塌点。"
}

DECLARED_PARAMS = {
    "OFFICER_THRESHOLD": 20.0,     # 正官激活阈值
    "HURTING_THRESHOLD": 16.0,     # 伤官激活阈值
    "DEFENSE_CAP": 0.5,            # 防御上限打折系数
    "PRIORITY": 0.94               # 事实输出优先级
}


def _collect_rows(deity_scores: Dict[str, float], cfg: Dict[str, Any] = {}) -> List[dict]:
    off_t = float(cfg.get("OFFICER_THRESHOLD", DECLARED_PARAMS["OFFICER_THRESHOLD"]))
    hurt_t = float(cfg.get("HURTING_THRESHOLD", DECLARED_PARAMS["HURTING_THRESHOLD"]))
    cap = float(cfg.get("DEFENSE_CAP", DECLARED_PARAMS["DEFENSE_CAP"]))
    prio = float(cfg.get("PRIORITY", DECLARED_PARAMS["PRIORITY"]))

    officer = float(deity_scores.get("正官", 0.0))
    hurting = float(deity_scores.get("伤官", 0.0))
    if officer < off_t or hurting < hurt_t:
        return []
    return [
        {
            "plugin": "officer_see_hurt",
            "fact": f"伤官见官：防御层级崩塌。正官防御上限强制封锁至 {int(cap*100)}%。",
            "label": "先统一沟通口径，再推进外部谈判动作。",
            "priority": prio,
            "meta": {
                "defense_cap_ratio": cap,
                "risk_signal": "STRUCTURAL_RISK_COLLAPSE"
            }
        }
    ]


@dataclass
class OfficerSeeHurtPlugin(V17PluginSpec):
    plugin_id: str = "officer_see_hurt"
    causal_tier: int = 3
    registry_priority: float = 0.88

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        # Legacy compatibility plugin.
        # Runtime ownership of "伤官见官/伤官伤尽" now lives in `l2.risk.risk_matrix`
        # so we do not emit duplicated facts from this historical path.
        return []


PLUGIN = OfficerSeeHurtPlugin()
