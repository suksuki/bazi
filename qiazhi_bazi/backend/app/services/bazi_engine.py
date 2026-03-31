"""基础排盘引擎：输入日期时间，生成四柱干支，并提供大运/流年摘要。"""
from __future__ import annotations

from datetime import datetime

from app.schemas.bazi_metadata import FourPillars, StemBranchPair

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
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    try:
        from lunar_python import Lunar, Solar
    except ImportError as exc:
        raise RuntimeError("缺少依赖 lunar_python，请先安装后再进行精确排盘。") from exc

    if calendar == "lunar":
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
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    try:
        from lunar_python import Lunar, Solar
    except ImportError as exc:
        raise RuntimeError("缺少依赖 lunar_python，请先安装后再进行精确排盘。") from exc

    if calendar == "lunar":
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
