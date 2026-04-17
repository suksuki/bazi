"""518_400 维干支设计空间：线性下标 → 四柱（统计/静默扫描用，非历法真排盘）。"""
from __future__ import annotations

from app.schemas.bazi_metadata import FourPillars, StemBranchPair

TOTAL_BAZI_COMBINATION_SPACE = 518_400
_RADIX = (60, 60, 36, 4)
_STEMS10 = tuple("甲乙丙丁戊己庚辛壬癸")
_BRANCH12 = tuple("子丑寅卯辰巳午未申酉戌亥")


def _jiazi_from_index(idx: int) -> tuple[str, str]:
    return _STEMS10[idx % 10], _BRANCH12[idx % 12]


def four_pillars_from_linear_index(linear_index: int) -> FourPillars:
    i = int(linear_index) % TOTAL_BAZI_COMBINATION_SPACE
    stride = _RADIX[1] * _RADIX[2] * _RADIX[3]
    y = i // stride
    r = i % stride
    b = _RADIX[2] * _RADIX[3]
    m = r // b
    r2 = r % b
    d = r2 // _RADIX[3]
    h = r2 % _RADIX[3]
    ys, yb = _jiazi_from_index(y)
    ms, mb = _jiazi_from_index(m)
    ds, db = _jiazi_from_index(d + m * 3 + y * 7)
    hs, hb = _jiazi_from_index(h * 11 + d * 5 + m * 2)
    return FourPillars(
        year=StemBranchPair(stem=ys, branch=yb),
        month=StemBranchPair(stem=ms, branch=mb),
        day=StemBranchPair(stem=ds, branch=db),
        hour=StemBranchPair(stem=hs, branch=hb),
    )
