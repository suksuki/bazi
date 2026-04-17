"""V17.12：旧 registry modern.* 占位。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "L3 Registry parity：will_proxy 与 wealth_risk。"
PLUGIN_RATIONALE = "与旧 PluginRegistry modern.* ID 对齐。"


@dataclass
class WillProxyV1Stub(V17PluginSpec):
    plugin_id: str = "modern.will_proxy.v1"
    causal_tier: int = 2
    registry_priority: float = 0.94
    doc_summary: str = "意志代理（WILL_PROXY）占位。"
    doc_rationale: str = "旧 run_will_proxy_v1；叙事与意图补丁链。"

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return []


@dataclass
class WealthRiskV1Stub(V17PluginSpec):
    plugin_id: str = "modern.wealth_risk.v1"
    causal_tier: int = 2
    registry_priority: float = 0.56
    doc_summary: str = "现代财富风险画像占位。"
    doc_rationale: str = "旧 hook on_verdict_ready；与 narrative_clip 互补。"

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return []


PLUGINS: List[V17PluginSpec] = [WillProxyV1Stub(), WealthRiskV1Stub()]
