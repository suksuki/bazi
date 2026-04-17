"""旧 registry：classical.wangshuai.v1（旺衰）— V17 脱水占位。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "旺衰引擎占位，与旧 classical.wangshuai.v1 ID 对齐。"
PLUGIN_RATIONALE = "全量旺衰逻辑待从备份 wangshuai_engine 脱水迁入。"


@dataclass
class WangshuaiV1Stub(V17PluginSpec):
    plugin_id: str = "classical.wangshuai.v1"
    causal_tier: int = 4
    registry_priority: float = 0.6
    doc_summary: str = "旺衰平衡解析引擎（旧 wangshuai）占位。"
    doc_rationale: str = "旧 hook on_physics_complete；V17 以 deity_scores 与 L0 场论承接。"

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return []


PLUGIN = WangshuaiV1Stub()
