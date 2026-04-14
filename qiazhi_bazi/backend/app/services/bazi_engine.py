"""基础排盘引擎：输入日期时间，生成四柱干支，并提供大运/流年摘要。

L0 原子元数据（藏干、通根系数）在物理推断链路入口装载，见 `app.core.bazi.engine` /
`PhysicsInferenceSkill.infer` 中的 `ensure_l0_for_physics`。
"""
from __future__ import annotations

from datetime import datetime
import re

from app.schemas.bazi_metadata import FourPillars, StemBranchPair


def _normalize_date_time(date_str: str, time_str: str) -> tuple[str, str]:
    d = str(date_str or "").strip().replace("/", "-")
    t = str(time_str or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        raise ValueError(f"date must be YYYY-MM-DD, got: {date_str!r}")
    if not t:
        t = "12:00"
    if re.fullmatch(r"\d{2}:\d{2}:\d{2}", t):
        t = t[:5]
    if re.fullmatch(r"\d{1}:\d{2}", t):
        t = f"0{t}"
    if not re.fullmatch(r"\d{2}:\d{2}", t):
        raise ValueError(f"time must be HH:MM, got: {time_str!r}")
    return d, t

def _split_pillar(pillar: str) -> StemBranchPair:
    if not pillar or len(pillar) < 2:
        raise ValueError(f"非法干支结果: {pillar}")
    return StemBranchPair(stem=pillar[0], branch=pillar[1])


def get_bazi(date_str: str, time_str: str = "12:00", calendar: str = "solar") -> FourPillars:
    """
    将输入日期时间映射为四柱干支（精确历法）。
    - calendar=solar: date_str 为公历 YYYY-MM-DD
    - calendar=lunar: date_str 为农历 YYYY-MM-DD（暂按平年处理，不含闰月）
    """
    d, t = _normalize_date_time(date_str, time_str)
    dt = datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M")
    try:
        from lunar_python import Lunar, Solar
    except ImportError as exc:
        raise RuntimeError("缺少依赖 lunar_python，请先安装后再进行精确排盘。") from exc

    cal = str(calendar or "solar").strip().lower()
    if cal == "lunar":
        lunar = Lunar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
        ec = lunar.getEightChar()
    else:
        solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
        ec = solar.getLunar().getEightChar()

    return FourPillars(
        year=_split_pillar(ec.getYear()),
        month=_split_pillar(ec.getMonth()),
        day=_split_pillar(ec.getDay()),
        hour=_split_pillar(ec.getTime()),
    )


def get_timeline_snapshot(
    date_str: str,
    time_str: str = "12:00",
    calendar: str = "solar",
    gender: int = 1,
    reference_year: int | None = None,
) -> dict:
    """
    返回当前流年与当前大运摘要。
    说明：gender 先默认 1（男命）以输出可视化信息，后续可接前端性别输入。
    """
    d, t = _normalize_date_time(date_str, time_str)
    dt = datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M")
    try:
        from lunar_python import Lunar, Solar
    except ImportError as exc:
        raise RuntimeError("缺少依赖 lunar_python，请先安装后再进行精确排盘。") from exc

    cal = str(calendar or "solar").strip().lower()
    if cal == "lunar":
        lunar = Lunar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
    else:
        solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
        lunar = solar.getLunar()
    ec = lunar.getEightChar()

    year = reference_year or datetime.now().year
    liunian = Solar.fromYmd(year, 6, 15).getLunar().getYearInGanZhi()

    dayun_now = "未知"
    try:
        yun = ec.getYun(gender)
        for dy in yun.getDaYun():
            if dy.getStartYear() <= year <= dy.getEndYear():
                dayun_now = dy.getGanZhi()
                break
        if dayun_now == "未知":
            arr = yun.getDaYun()
            if arr:
                dayun_now = arr[0].getGanZhi()
    except Exception:
        dayun_now = "未知"

    return {"liunian": str(liunian), "dayun": str(dayun_now), "reference_year": year}
