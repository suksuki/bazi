from __future__ import annotations

from datetime import datetime
from typing import Any

from v30.contracts import BirthInput, FlowContext, LuckCycleContext, SixPillarContext


LUCK_FLOW_ENGINE_VERSION = "v30.luck_flow_engine.v1"


def build_luck_flow_contexts(
    *,
    birth_input: BirthInput,
    local_dt: datetime,
    natal_pillars: dict[str, str],
    target_dt: datetime,
) -> tuple[LuckCycleContext, FlowContext, SixPillarContext]:
    flow = _build_flow_context(target_dt)
    luck = _build_luck_cycle_context(birth_input=birth_input, local_dt=local_dt, target_year=target_dt.year)
    six = _build_six_pillar_context(natal_pillars=natal_pillars, luck=luck, flow=flow)
    return luck, flow, six


def _build_luck_cycle_context(
    *,
    birth_input: BirthInput,
    local_dt: datetime,
    target_year: int,
) -> LuckCycleContext:
    if birth_input.gender == "unknown":
        return LuckCycleContext(
            status="pending",
            missing_requirements=["gender_required_for_luck_direction"],
            trace={"engine": LUCK_FLOW_ENGINE_VERSION, "reason": "gender_unknown"},
            guardrails=["NO_LUCK_CYCLE_WITHOUT_DIRECTION_INPUT"],
        )
    try:
        from lunar_python import Solar
    except ImportError:
        return LuckCycleContext(
            status="blocked",
            missing_requirements=["lunar_python_dependency"],
            trace={"engine": LUCK_FLOW_ENGINE_VERSION, "reason": "dependency_missing"},
            guardrails=["NO_LUCK_CYCLE_WITHOUT_DETERMINISTIC_ENGINE"],
        )
    gender_flag = 1 if birth_input.gender == "male" else 0
    yun = Solar.fromYmdHms(
        local_dt.year,
        local_dt.month,
        local_dt.day,
        local_dt.hour,
        local_dt.minute,
        local_dt.second,
    ).getLunar().getEightChar().getYun(gender_flag)
    cycles: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for row in yun.getDaYun():
        payload = {
            "index": int(row.getIndex()),
            "pillar": str(row.getGanZhi() or ""),
            "start_year": int(row.getStartYear()),
            "end_year": int(row.getEndYear()),
            "start_age": int(row.getStartAge()),
            "end_age": int(row.getEndAge()),
        }
        cycles.append(payload)
        if payload["start_year"] <= target_year <= payload["end_year"]:
            current = payload
    current_pillar = str(current.get("pillar") or "")
    status = "ready" if current_pillar else "pending"
    missing = [] if current_pillar else ["current_luck_pillar"]
    return LuckCycleContext(
        status=status,
        direction="forward" if yun.isForward() else "backward",
        start_age=int(yun.getStartYear()) if hasattr(yun, "getStartYear") else None,
        start_year=int(cycles[1]["start_year"]) if len(cycles) > 1 else None,
        start_solar=str(yun.getStartSolar()) if hasattr(yun, "getStartSolar") else "",
        current_luck_pillar=current_pillar,
        current_luck=current,
        luck_cycles=cycles,
        missing_requirements=missing,
        trace={
            "engine": "lunar_python",
            "version": LUCK_FLOW_ENGINE_VERSION,
            "gender": birth_input.gender,
            "target_year": target_year,
        },
        guardrails=[
            "LUCK_CYCLE_FROM_DETERMINISTIC_CALENDAR_ENGINE",
            "LUCK_CYCLE_CONTEXT_NOT_FIXED_EVENT_PREDICTION",
        ],
    )


def _build_flow_context(target_dt: datetime) -> FlowContext:
    try:
        from lunar_python import Solar
    except ImportError:
        return FlowContext(
            status="blocked",
            target_date=target_dt.date().isoformat(),
            trace={"engine": LUCK_FLOW_ENGINE_VERSION, "reason": "dependency_missing"},
            guardrails=["NO_FLOW_CONTEXT_WITHOUT_DETERMINISTIC_ENGINE"],
        )
    lunar = Solar.fromYmdHms(target_dt.year, target_dt.month, target_dt.day, 12, 0, 0).getLunar()
    return FlowContext(
        status="ready",
        target_date=target_dt.date().isoformat(),
        flow_year_pillar=str(lunar.getYearInGanZhiExact()),
        flow_month_pillar=str(lunar.getMonthInGanZhiExact()),
        trace={"engine": "lunar_python", "version": LUCK_FLOW_ENGINE_VERSION},
        guardrails=[
            "FLOW_CONTEXT_FROM_DETERMINISTIC_CALENDAR_ENGINE",
            "FLOW_CONTEXT_NOT_FIXED_EVENT_PREDICTION",
        ],
    )


def _build_six_pillar_context(
    *,
    natal_pillars: dict[str, str],
    luck: LuckCycleContext,
    flow: FlowContext,
) -> SixPillarContext:
    missing: list[str] = []
    if not luck.current_luck_pillar:
        missing.append("current_luck_pillar")
    if not flow.flow_year_pillar:
        missing.append("flow_year_pillar")
    pillars = [
        {"layer": "natal_year", "pillar": natal_pillars.get("year", "")},
        {"layer": "natal_month", "pillar": natal_pillars.get("month", "")},
        {"layer": "natal_day", "pillar": natal_pillars.get("day", "")},
        {"layer": "natal_hour", "pillar": natal_pillars.get("hour", "")},
    ]
    if luck.current_luck_pillar:
        pillars.append({"layer": "luck", "pillar": luck.current_luck_pillar})
    if flow.flow_year_pillar:
        pillars.append({"layer": "flow_year", "pillar": flow.flow_year_pillar})
    return SixPillarContext(
        status="ready" if not missing else "pending",
        natal_pillars=natal_pillars,
        luck_pillar=luck.current_luck_pillar,
        flow_year_pillar=flow.flow_year_pillar,
        flow_month_pillar=flow.flow_month_pillar,
        pillars=pillars,
        missing_requirements=missing,
        guardrails=[
            "SIX_PILLAR_CONTEXT_SUMMARY_NOT_NEW_CHART_FACT_SOURCE",
            "NO_TIMING_VERDICT_WITHOUT_TIME_LAYER_EVIDENCE",
        ],
    )
