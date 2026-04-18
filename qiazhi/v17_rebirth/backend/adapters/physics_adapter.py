from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from v17_rebirth.backend.services.physics_layers import read_runtime_scores


@dataclass
class PhysicsAdapter:
    """V17.14：只读物理张量；十神分值 + L1 全带宽（interaction_v2 / interaction_delta）。"""

    root: Path

    def available_sources(self) -> Dict[str, str]:
        return {
            "v17_rebirth_internal": str(self.root / "qiazhi" / "v17_rebirth" / "backend" / "logic"),
        }

    def read_deity_scores(self, raw_physics: Dict[str, Any]) -> Dict[str, float]:
        return read_runtime_scores(raw_physics)

    def read_interaction_v2(self, raw_physics: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw_physics, dict):
            return {}
        meta = raw_physics.get("meta")
        if not isinstance(meta, dict):
            return {}
        v2 = meta.get("interaction_v2")
        return dict(v2) if isinstance(v2, dict) else {}

    def read_interaction_delta(self, raw_physics: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw_physics, dict):
            return {}
        d = raw_physics.get("interaction_delta")
        return dict(d) if isinstance(d, dict) else {}

    def read_physics_bundle(self, raw_physics: Dict[str, Any]) -> Dict[str, Any]:
        """供 collect_v17_facts 单点读取：十神 + 地支拓扑 + 冲突增量。"""
        return {
            "deity_scores": self.read_deity_scores(raw_physics),
            "ten_gods_absolute_intensity": self.read_deity_scores(raw_physics),
            "interaction_v2": self.read_interaction_v2(raw_physics),
            "interaction_delta": self.read_interaction_delta(raw_physics),
        }
