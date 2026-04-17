"""V17.12 AutoScanner：在编排入口预物化 manifest / 动态算子索引（与 plugin_discovery 协同）。"""
from __future__ import annotations


class AutoScanner:
    """幂等预热：首次进入 VerdictOrchestrator 快照时拉全量 Spec 列表（含 manifest 行）。"""

    _warmed: bool = False

    @classmethod
    def ensure_loaded(cls) -> None:
        if cls._warmed:
            return
        from v17_rebirth.backend.logic import plugin_discovery as pd

        pd.warm_manifest_operators()
        cls._warmed = True

    @classmethod
    def reset(cls) -> None:
        cls._warmed = False
