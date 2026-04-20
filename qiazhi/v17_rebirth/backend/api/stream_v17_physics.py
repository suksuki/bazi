from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def _safe_parse_birth_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        # Accept "Z" suffix for web clients.
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _pillars_from_lunar(*, birth_time: datetime, gender: Optional[str], flow_year: int) -> Tuple[Dict[str, str], str, str]:
    """
    与 legacy BaziProfile 一致：使用 lunar_python 排四柱；流年用年中点规避立春边界；
    大运按 lunar 大运表匹配 flow_year（起运前空干支则顺延至首个有效大运）。
    """
    from lunar_python import Lunar, Solar

    lunar = Lunar.fromDate(birth_time)
    ec = lunar.getEightChar()
    four_pillars = {
        "year": str(ec.getYear() or ""),
        "month": str(ec.getMonth() or ""),
        "day": str(ec.getDay() or ""),
        "hour": str(ec.getTime() or ""),
    }

    gender_code = 1 if str(gender or "").lower() == "male" else 0
    yun = ec.getYun(gender_code)
    luck_pillar = "—"
    for dy in yun.getDaYun():
        sy, ey = int(dy.getStartYear()), int(dy.getEndYear())
        if sy <= flow_year <= ey:
            gz = dy.getGanZhi()
            if isinstance(gz, str) and len(gz.strip()) >= 2:
                luck_pillar = gz.strip()
                break
    if luck_pillar == "—":
        for dy in yun.getDaYun():
            gz = dy.getGanZhi()
            if not (isinstance(gz, str) and len(gz.strip()) >= 2):
                continue
            sy = int(dy.getStartYear())
            if flow_year < sy:
                luck_pillar = gz.strip()
                break

    solar = Solar.fromYmd(int(flow_year), 6, 15)
    ygz = solar.getLunar().getYearInGanZhi()
    flow_pillar = str(ygz).strip() if ygz else "—"

    return four_pillars, luck_pillar, flow_pillar


def _should_rebuild_physics_core(
    *,
    current_physics: Dict[str, Any] | None,
    birth_time: Optional[str],
    gender: Optional[str],
    flow_year: Optional[int],
) -> bool:
    current = current_physics if isinstance(current_physics, dict) else {}
    if not current:
        return True

    if flow_year is not None:
        try:
            current_flow_year = int(current.get("flow_year")) if current.get("flow_year") is not None else None
        except (TypeError, ValueError):
            current_flow_year = None
        if current_flow_year != int(flow_year):
            return True

    if gender is not None:
        current_gender = str(current.get("gender") or "").strip().lower() or None
        request_gender = str(gender or "").strip().lower() or None
        if current_gender != request_gender:
            return True

    if birth_time is not None:
        current_birth = str(current.get("birth_time") or "").strip() or None
        parsed_request = _safe_parse_birth_time(birth_time)
        request_birth = parsed_request.isoformat() if parsed_request is not None else str(birth_time or "").strip() or None
        if current_birth != request_birth:
            return True

    return False


def _pillar(stems: List[str], branches: List[str], idx: int) -> str:
    return f"{stems[idx % len(stems)]}{branches[idx % len(branches)]}"


def _run_v17_physics_core(
    *,
    birth_time: Optional[datetime],
    gender: Optional[str],
    flow_year: Optional[int] = None,
) -> Dict[str, Any]:
    from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
    from v17_rebirth.backend.services.physics_layers import sync_runtime_aliases

    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    dt = birth_time or datetime(1977, 5, 8, 18, 0, 0)
    gender_norm = "male" if str(gender or "").lower() == "male" else "female"
    fy = int(flow_year) if flow_year is not None else datetime.now().year

    luck_pillar = "—"
    flow_pillar = "—"
    try:
        four_pillars, luck_pillar, flow_pillar = _pillars_from_lunar(
            birth_time=dt,
            gender=gender,
            flow_year=fy,
        )
    except Exception:
        year_idx = dt.year
        month_idx = dt.year * 12 + dt.month
        day_idx = dt.toordinal()
        hour_idx = day_idx * 12 + (dt.hour // 2)
        four_pillars = {
            "year": _pillar(stems, branches, year_idx),
            "month": _pillar(stems, branches, month_idx),
            "day": _pillar(stems, branches, day_idx),
            "hour": _pillar(stems, branches, hour_idx),
        }

    # 真实十神分值：基于日主干支阴阳五行生克关系（L0 层 ten_gods_engine）
    scores, ten_gods, total_energy_index, energy_meta = calc_deity_scores(
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
        gender=gender_norm,
        birth_time=dt,
        flow_year=fy,
    )
    facts = [
        {
            "fact": f"四柱落位：年{four_pillars['year']} 月{four_pillars['month']} 日{four_pillars['day']} 时{four_pillars['hour']}",
            "weight": 0.98,
            "tier": 0,
        },
        {
            "fact": f"大运（{fy}）：{luck_pillar}；流年：{flow_pillar}",
            "weight": 0.96,
            "tier": 0,
        },
        {
            "fact": f"十神主轴：{'、'.join(ten_gods)}",
            "weight": 0.82,
            "tier": 1,
        },
        {
            "fact": "命局主线已进入 V17 叙事织造阶段",
            "weight": 0.52,
            "tier": 2,
        },
    ]
    # V17.32: 序列化 Evolution Ledger（从 EvolutionLedger 对象转为 JSON-safe dict）
    from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger
    raw_ledger = energy_meta.pop("ledger", None)
    ten_gods_ledger = raw_ledger.to_dict() if isinstance(raw_ledger, EvolutionLedger) else {}

    payload = {
        "ten_gods_base_l0": dict(scores),
        "ten_gods_runtime": dict(scores),
        "total_energy_index": total_energy_index,
        "energy_meta": energy_meta,
        "ten_gods_ledger": ten_gods_ledger,
        "facts": facts,
        "four_pillars": four_pillars,
        "luck_pillar": luck_pillar,
        "flow_pillar": flow_pillar,
        "flow_year": fy,
        "ten_gods": ten_gods,
        "gender": gender_norm,
        "birth_time": dt.isoformat(),
    }
    sync_runtime_aliases(payload, scores)
    return payload
