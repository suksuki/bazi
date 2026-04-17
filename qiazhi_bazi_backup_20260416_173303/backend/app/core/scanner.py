"""基础物理扫描器：识别冲合特征。"""
from __future__ import annotations

from app.schemas.bazi_metadata import ConflictMatrix, FourPillars, PhysicalScanner


class Scanner:
    """对外统一入口，后续可扩展更多物理规则。"""

    def __init__(self) -> None:
        self._physical = PhysicalScanner()

    def scan(self, pillars: FourPillars) -> ConflictMatrix:
        return self._physical.scan(pillars)
