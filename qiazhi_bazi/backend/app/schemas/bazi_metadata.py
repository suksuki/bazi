"""BaziMetadata v1.0：四柱、矛盾矩阵、能量流向（不接老系统复杂分值）。"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class FlowState(str, Enum):
    """当前盘面能量流向标签（可扩展）。"""

    UNKNOWN = "unknown"
    GENERATING = "生"
    CONTROLLING = "克"
    SAME = "比劫"
    OUTPUT = "泄"
    RESOURCE = "印"


class StemBranchPair(BaseModel):
    stem: str = Field(..., description="天干一字，如 甲")
    branch: str = Field(..., description="地支一字，如 寅")
    energy_value: int = Field(default=100, description="该柱能量值（0-100）")


class FourPillars(BaseModel):
    """四柱干支。"""

    year: StemBranchPair
    month: StemBranchPair
    day: StemBranchPair
    hour: StemBranchPair


class ConflictPoint(BaseModel):
    """刑冲合化等潜在作用点（扫描结果之一）。"""

    kind: str = Field(..., description="如 clash、combine、punish、harm")
    positions: List[str] = Field(
        default_factory=list,
        description="涉及柱位或地支，如 [month_branch, day_branch]",
    )
    detail: str = Field(default="", description="人可读说明，如 寅申冲")


class ConflictMatrix(BaseModel):
    """盘面扫描出的刑冲合化潜在点集合。"""

    points: List[ConflictPoint] = Field(default_factory=list)


class BaziMetadata(BaseModel):
    """v1.0 协议根对象。"""

    version: str = Field(default="1.0", description="协议版本")
    pillars: Optional[FourPillars] = None
    conflict_matrix: ConflictMatrix = Field(default_factory=ConflictMatrix)
    flow_state: FlowState = FlowState.UNKNOWN
    notes: str = Field(default="", description="可选备注")


_SIX_CLASH = {
    ("子", "午"),
    ("丑", "未"),
    ("寅", "申"),
    ("卯", "酉"),
    ("辰", "戌"),
    ("巳", "亥"),
}

_SIX_COMBINE = {
    ("子", "丑"),
    ("寅", "亥"),
    ("卯", "戌"),
    ("辰", "酉"),
    ("巳", "申"),
    ("午", "未"),
}

_CLASH_LABEL: Dict[frozenset[str], str] = {
    frozenset(("子", "午")): "子午冲",
    frozenset(("丑", "未")): "丑未冲",
    frozenset(("寅", "申")): "寅申冲",
    frozenset(("卯", "酉")): "卯酉冲",
    frozenset(("辰", "戌")): "辰戌冲",
    frozenset(("巳", "亥")): "巳亥冲",
}

_COMBINE_LABEL: Dict[frozenset[str], str] = {
    frozenset(("子", "丑")): "子丑合",
    frozenset(("寅", "亥")): "寅亥合",
    frozenset(("卯", "戌")): "卯戌合",
    frozenset(("辰", "酉")): "辰酉合",
    frozenset(("巳", "申")): "巳申合",
    frozenset(("午", "未")): "午未合",
}


class PhysicalScanner:
    """原子探测器：仅做地支六冲与六合识别。"""

    def scan(self, pillars: FourPillars) -> ConflictMatrix:
        branches = {
            "year_branch": pillars.year.branch,
            "month_branch": pillars.month.branch,
            "day_branch": pillars.day.branch,
            "hour_branch": pillars.hour.branch,
        }
        keys = list(branches.keys())
        points: List[ConflictPoint] = []
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                p1, p2 = keys[i], keys[j]
                b1, b2 = branches[p1], branches[p2]
                pair_key = frozenset((b1, b2))
                pair: Tuple[str, str] = (b1, b2)
                if pair in _SIX_CLASH or (b2, b1) in _SIX_CLASH:
                    points.append(
                        ConflictPoint(
                            kind="clash",
                            positions=[p1, p2],
                            detail=_CLASH_LABEL.get(pair_key, f"{b1}{b2}冲"),
                        )
                    )
                if pair in _SIX_COMBINE or (b2, b1) in _SIX_COMBINE:
                    points.append(
                        ConflictPoint(
                            kind="combine",
                            positions=[p1, p2],
                            detail=_COMBINE_LABEL.get(pair_key, f"{b1}{b2}合"),
                        )
                    )
        return ConflictMatrix(points=points)


def detect_clashes(pillars: FourPillars) -> ConflictMatrix:
    """兼容旧接口：返回原子探测矩阵（含六冲与六合）。"""
    return PhysicalScanner().scan(pillars)
