from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
    BRANCH_HIDDEN,
    _collect_root_strengths,
    _collect_visible_stems,
    _parse_gz,
)
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


def _four_pillars(physics_tensor: Dict[str, Any]) -> Dict[str, str]:
    raw = physics_tensor.get("four_pillars")
    return raw if isinstance(raw, dict) else {}


def _hidden_lines(four_pillars: Dict[str, str]) -> List[str]:
    lines: List[str] = []
    pillar_cn = {"year": "年", "month": "月", "day": "日", "hour": "时"}
    for key in ("year", "month", "day", "hour"):
        _, branch = _parse_gz(str(four_pillars.get(key, "")).strip())
        hidden = BRANCH_HIDDEN.get(branch, [])
        if not branch or not hidden:
            continue
        stems = "".join(stem for stem, _weight in hidden)
        lines.append(f"{pillar_cn.get(key, key)}支{branch}藏{stems}")
    return lines


@dataclass
class HiddenStemsFoundationPlugin(V17PluginSpec):
    plugin_id: str = "l0.foundation.hidden_stems.v1"
    causal_tier: int = 5
    registry_priority: float = 0.66

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        four = _four_pillars(physics_tensor)
        lines = _hidden_lines(four)
        if not lines:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"藏干基线：{'；'.join(lines)}。",
                "priority": 0.66,
                "label": "基础物理",
                "meta": {"hidden_stem_lines": list(lines)},
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class RootedStemsFoundationPlugin(V17PluginSpec):
    plugin_id: str = "l0.foundation.rooted_stems.v1"
    causal_tier: int = 5
    registry_priority: float = 0.67

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        four = _four_pillars(physics_tensor)
        luck = str(physics_tensor.get("luck_pillar", "") or "")
        flow = str(physics_tensor.get("flow_pillar", "") or "")
        rooted = sorted(
            stem
            for stem, strength in (_collect_root_strengths(four, luck, flow) or {}).items()
            if float(strength or 0.0) >= 0.18
        )
        if not rooted:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"通根基线：当前可通根天干为 {''.join(rooted)}。",
                "priority": 0.68,
                "label": "基础物理",
                "meta": {"rooted_stems": list(rooted)},
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ExposedHiddenFoundationPlugin(V17PluginSpec):
    plugin_id: str = "l0.foundation.exposed_hidden_stems.v1"
    causal_tier: int = 5
    registry_priority: float = 0.65

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        four = _four_pillars(physics_tensor)
        luck = str(physics_tensor.get("luck_pillar", "") or "")
        flow = str(physics_tensor.get("flow_pillar", "") or "")
        visible = set(_collect_visible_stems(four, luck, flow))
        exposed: List[str] = []
        for key in ("year", "month", "day", "hour"):
            _, branch = _parse_gz(str(four.get(key, "")).strip())
            if not branch:
                continue
            for hidden_stem, _weight in BRANCH_HIDDEN.get(branch, []):
                if hidden_stem in visible:
                    exposed.append(f"{branch}:{hidden_stem}")
        if not exposed:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"透干显影：藏干外透节点 {', '.join(sorted(set(exposed)))}。",
                "priority": 0.65,
                "label": "基础物理",
                "meta": {"exposed_hidden_pairs": sorted(set(exposed))},
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class MonthCommandFoundationPlugin(V17PluginSpec):
    plugin_id: str = "l0.foundation.month_command.v1"
    causal_tier: int = 5
    registry_priority: float = 0.72

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        energy_meta = physics_tensor.get("energy_meta")
        meta = energy_meta if isinstance(energy_meta, dict) else {}
        month_command_god = str(meta.get("month_command_god") or "").strip()
        if not month_command_god:
            return []
        season = meta.get("season_power") if isinstance(meta.get("season_power"), dict) else {}
        month_branch = str(season.get("month_branch") or "").strip()
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"月令主气：月支{month_branch or '未知'}主导 {month_command_god} 轴线，是 L0 旺衰判定的起点。",
                "priority": 0.72,
                "label": "月令主气",
                "meta": {"month_command_god": month_command_god, "month_branch": month_branch},
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    HiddenStemsFoundationPlugin(),
    RootedStemsFoundationPlugin(),
    ExposedHiddenFoundationPlugin(),
    MonthCommandFoundationPlugin(),
]
