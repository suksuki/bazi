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
