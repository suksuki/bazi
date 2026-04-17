from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class PhysicsAdapter:
    """Read-only adapter for core/physics deity signals."""

    root: Path

    def available_sources(self) -> Dict[str, str]:
        backup_src = self.root / "qiazhi_bazi_backup_20260416_173303" / "backend" / "app" / "core" / "physics"
        legacy_src = self.root / "legacy" / "core" / "physics"
        return {
            "backup_core_physics": str(backup_src),
            "legacy_core_physics": str(legacy_src),
        }

    def read_deity_scores(self, raw_physics: Dict[str, Any]) -> Dict[str, float]:
        # 只读信号模式：不触碰物理内核，直接消费上游计算结果
        src = raw_physics.get("deity_scores") if isinstance(raw_physics, dict) else {}
        if not isinstance(src, dict):
            return {}
        out: Dict[str, float] = {}
        for k, v in src.items():
            key = str(k).strip()
            if not key:
                continue
            try:
                out[key] = float(v)
            except (TypeError, ValueError):
                continue
        return out
