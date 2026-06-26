from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from v30.contracts import ChartContext
from v30.contracts import (
    BirthChartBuildResult,
    BirthInput,
    CalendarConversionTrace,
    ChartBuildSource,
    FourPillarResult,
)
from v30.core.constants import HIDDEN_STEMS, VAULT_BRANCHES, element_of_stem
from v30.core.elements import element_distribution
from v30.core.pillars import Pillar, PillarSet, pillar_set_from_displays
from v30.core.luck_flow import build_luck_flow_contexts
from v30.core.relations import RelationHit, branch_relation_hits
from v30.core.ten_gods import TenGodPosition, ten_god
from v30.core.time_context import TimeContext, build_time_context


CHART_CONTEXT_VERSION = "v30.chart_context.v1"
TRUE_SOLAR_LONGITUDE_BY_PLACE = {
    "beijing": 116.4074,
    "北京": 116.4074,
    "shanghai": 121.4737,
    "上海": 121.4737,
    "guangzhou": 113.2644,
    "广州": 113.2644,
    "shenzhen": 114.0579,
    "深圳": 114.0579,
    "hong kong": 114.1694,
    "香港": 114.1694,
    "taipei": 121.5654,
    "台北": 121.5654,
    "seoul": 126.9780,
    "서울": 126.9780,
}
TIMEZONE_STANDARD_MERIDIAN = {
    "Asia/Shanghai": 120.0,
    "Asia/Hong_Kong": 120.0,
    "Asia/Taipei": 120.0,
    "Asia/Seoul": 135.0,
    "Asia/Tokyo": 135.0,
}


def build_chart_context_from_displays(
    *,
    reading_id: str,
    year: str,
    month: str,
    day: str,
    hour: str,
    locale: str = "zh",
    input_id: str = "",
    luck_pillar: str = "",
    flow_year_pillar: str = "",
    flow_month_pillar: str = "",
    luck_cycle_context: Any | None = None,
    flow_context: Any | None = None,
    six_pillar_context: Any | None = None,
    created_at: datetime | None = None,
) -> ChartContext:
    pillar_set = pillar_set_from_displays(year, month, day, hour)
    build_source = ChartBuildSource(
        source_type="explicit_pillars",
        input_id=input_id,
        calendar_assumption="explicit_pillars_no_calendar_conversion",
        status="ready",
        source="explicit_pillars",
        guardrails=[
            "EXPLICIT_PILLARS_TRUSTED_AS_INPUT_FACTS",
            "NO_CALENDAR_CONVERSION_PERFORMED",
        ],
    )
    return build_chart_context(
        reading_id=reading_id,
        pillar_set=pillar_set,
        locale=locale,
        input_id=input_id,
        chart_build_source=build_source,
        luck_pillar=luck_pillar,
        flow_year_pillar=flow_year_pillar,
        flow_month_pillar=flow_month_pillar,
        created_at=created_at,
    )


def build_chart_context(
    *,
    reading_id: str,
    pillar_set: PillarSet,
    locale: str = "zh",
    input_id: str = "",
    chart_build_source: ChartBuildSource | None = None,
    conversion_trace: CalendarConversionTrace | None = None,
    luck_pillar: str = "",
    flow_year_pillar: str = "",
    flow_month_pillar: str = "",
    luck_cycle_context: Any | None = None,
    flow_context: Any | None = None,
    six_pillar_context: Any | None = None,
    created_at: datetime | None = None,
) -> ChartContext:
    pillars = pillar_set.as_map()
    day_master = pillars["day"].stem
    visible = _visible_ten_gods(day_master, pillars)
    hidden = _hidden_ten_gods(day_master, pillars)
    natal_relations = branch_relation_hits(pillars)
    vault_branches = _vault_branches(pillars)
    elements = element_distribution(pillars, hidden)
    time_context = build_time_context(
        pillars,
        day_master=day_master,
        luck_pillar=luck_pillar,
        flow_year_pillar=flow_year_pillar,
        flow_month_pillar=flow_month_pillar,
    )
    time_layers_payload = time_context.model_dump(mode="json")
    if luck_cycle_context is not None:
        time_layers_payload["luck_cycle_context"] = (
            luck_cycle_context.model_dump(mode="json")
            if hasattr(luck_cycle_context, "model_dump")
            else luck_cycle_context
        )
    if flow_context is not None:
        time_layers_payload["flow_context"] = (
            flow_context.model_dump(mode="json")
            if hasattr(flow_context, "model_dump")
            else flow_context
        )
    if six_pillar_context is not None:
        six_payload = (
            six_pillar_context.model_dump(mode="json")
            if hasattr(six_pillar_context, "model_dump")
            else six_pillar_context
        )
        time_layers_payload["six_pillar_context"] = six_payload
        if six_payload.get("status") == "ready":
            time_layers_payload["status"] = "ready"
            time_layers_payload["note"] = "BirthInput-derived luck and flow context supplied; timing remains evidence-bounded."
    context_seed = {
        "reading_id": reading_id,
        "pillars": {key: pillar.display for key, pillar in pillars.items()},
        "time_layers": [_time_layer_seed(row) for row in time_context.layers],
    }
    context_id = "v30.bazi_context." + hashlib.sha256(
        json.dumps(context_seed, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    source_payload = chart_build_source or ChartBuildSource(
        source_type="explicit_pillars",
        input_id=input_id,
        calendar_assumption="explicit_pillars_no_calendar_conversion",
        status="ready",
        source="explicit_pillars",
        guardrails=[
            "EXPLICIT_PILLARS_TRUSTED_AS_INPUT_FACTS",
            "NO_CALENDAR_CONVERSION_PERFORMED",
        ],
    )
    input_payload: dict[str, Any] = {
        "input_id": input_id,
        "calendar_assumption": source_payload.calendar_assumption,
        "source": source_payload.source_type,
        "chart_build_source": source_payload.model_dump(mode="json"),
    }
    if conversion_trace is not None:
        input_payload["conversion_trace"] = conversion_trace.model_dump(mode="json")
    return ChartContext(
        context_id=context_id,
        reading_id=reading_id,
        input_pillars=input_payload,
        natal_pillars={
            "version": CHART_CONTEXT_VERSION,
            "pillars": {key: pillar.model_dump(mode="json") for key, pillar in pillars.items()},
            "visible_ten_gods": [row.model_dump(mode="json") for row in visible],
            "hidden_ten_gods": [row.model_dump(mode="json") for row in hidden],
            "relation_hits": [row.model_dump(mode="json") for row in natal_relations],
            "vault_branches": vault_branches,
            "element_distribution": elements,
            "base_fact_summary": _base_fact_summary(
                day_master=day_master,
                day_master_element=element_of_stem(day_master),
                pillars=pillars,
                visible=visible,
                hidden=hidden,
                relations=natal_relations,
                vault_branches=vault_branches,
                elements=elements,
            ),
            "guardrails": [
                "CHART_FACTS_DETERMINISTIC",
                "NO_LLM_FACT_GENERATION",
                "NO_FORTUNE_CONCLUSION",
            ],
        },
        day_master=day_master,
        day_master_element=element_of_stem(day_master),
        time_layers=time_layers_payload,
        locale=locale,  # type: ignore[arg-type]
        created_at=created_at or datetime.now(timezone.utc),
    )


def build_chart_context_from_birth_input(
    *,
    reading_id: str,
    birth_input: BirthInput,
    locale: str = "zh",
    created_at: datetime | None = None,
) -> BirthChartBuildResult:
    if birth_input.unknown_hour:
        return _birth_input_pending_result(
            reading_id=reading_id,
            birth_input=birth_input,
            failure="unknown_hour_blocks_hour_pillar",
            extra_missing=["known_birth_hour"],
        )
    try:
        local_dt = _parse_birth_local_datetime(birth_input)
    except ValueError as exc:
        return _birth_input_pending_result(
            reading_id=reading_id,
            birth_input=birth_input,
            failure=str(exc),
            trace_status="blocked",
            extra_missing=["valid_birth_datetime"],
        )
    try:
        from lunar_python import Solar
    except ImportError:
        return _birth_input_pending_result(
            reading_id=reading_id,
            birth_input=birth_input,
            failure="lunar_python_dependency_missing",
            trace_status="blocked",
            extra_missing=["lunar_python_dependency"],
        )
    try:
        from lunar_python import Lunar
    except ImportError:
        return _birth_input_pending_result(
            reading_id=reading_id,
            birth_input=birth_input,
            failure="lunar_python_dependency_missing",
            trace_status="blocked",
            extra_missing=["lunar_python_dependency"],
        )

    true_solar = _resolve_true_solar_datetime(birth_input, local_dt)
    if birth_input.use_true_solar_time and true_solar.get("status") != "ready":
        return _birth_input_pending_result(
            reading_id=reading_id,
            birth_input=birth_input,
            failure=str(true_solar.get("failure") or "true_solar_time_conversion_blocked"),
            trace_status="blocked",
            extra_missing=[str(item) for item in true_solar.get("missing_requirements", [])],
        )
    conversion_dt = true_solar.get("datetime") if isinstance(true_solar.get("datetime"), datetime) else local_dt
    try:
        if birth_input.calendar_type == "lunar":
            lunar_month = -conversion_dt.month if birth_input.lunar_is_leap_month else conversion_dt.month
            lunar = Lunar.fromYmdHms(
                conversion_dt.year,
                lunar_month,
                conversion_dt.day,
                conversion_dt.hour,
                conversion_dt.minute,
                conversion_dt.second,
            )
        else:
            lunar = Solar.fromYmdHms(
                conversion_dt.year,
                conversion_dt.month,
                conversion_dt.day,
                conversion_dt.hour,
                conversion_dt.minute,
                conversion_dt.second,
            ).getLunar()
    except Exception as exc:
        failure = "lunar_calendar_conversion_failed" if birth_input.calendar_type == "lunar" else "solar_calendar_conversion_failed"
        return _birth_input_pending_result(
            reading_id=reading_id,
            birth_input=birth_input,
            failure=failure,
            trace_status="blocked",
            extra_missing=[type(exc).__name__],
        )
    year, month, day, hour = [str(row) for row in lunar.getBaZi()]
    effective_solar = lunar.getSolar()
    effective_solar_dt = datetime(
        int(effective_solar.getYear()),
        int(effective_solar.getMonth()),
        int(effective_solar.getDay()),
        int(effective_solar.getHour()),
        int(effective_solar.getMinute()),
        int(effective_solar.getSecond()),
    )
    target_dt = created_at or datetime.now(timezone.utc)
    target_local_dt = target_dt.replace(tzinfo=None) if target_dt.tzinfo else target_dt
    luck_cycle_context, flow_context, six_pillar_context = build_luck_flow_contexts(
        birth_input=birth_input,
        local_dt=effective_solar_dt,
        natal_pillars={"year": year, "month": month, "day": day, "hour": hour},
        target_dt=target_local_dt,
    )
    trace = _ready_birth_input_conversion_trace(
        reading_id,
        birth_input,
        local_dt,
        conversion_dt=conversion_dt,
        effective_solar_dt=effective_solar_dt,
        true_solar=true_solar,
    )
    source = ChartBuildSource(
        source_type="birth_input",
        input_id=birth_input.input_id,
        calendar_assumption=birth_input.calendar_assumption,
        status="ready",
        source=birth_input.source,
        guardrails=[
            "BIRTH_INPUT_REQUIRES_DETERMINISTIC_CALENDAR_CONVERSION",
            "NO_LLM_FACT_GENERATION",
            "NO_SYNTHETIC_FACT_GENERATION",
        ],
    )
    result = FourPillarResult(
        status="ready",
        pillars={
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
        },
        missing_pillars=[],
        chart_build_source=source,
        conversion_trace=trace,
        guardrails=[
            "FOUR_PILLARS_FROM_DETERMINISTIC_CALENDAR_CONVERSION",
            "NO_LLM_FACT_GENERATION",
        ],
    )
    pillar_set = pillar_set_from_displays(year, month, day, hour)
    context = build_chart_context(
        reading_id=reading_id,
        pillar_set=pillar_set,
        locale=locale,
        input_id=birth_input.input_id,
        chart_build_source=source,
        conversion_trace=trace,
        luck_pillar=luck_cycle_context.current_luck_pillar,
        flow_year_pillar=flow_context.flow_year_pillar,
        flow_month_pillar=flow_context.flow_month_pillar,
        luck_cycle_context=luck_cycle_context,
        flow_context=flow_context,
        six_pillar_context=six_pillar_context,
        created_at=created_at,
    )
    return BirthChartBuildResult(
        reading_id=reading_id,
        birth_input=birth_input,
        four_pillar_result=result,
        chart_context=context,
        status="ready",
        failures=[],
    )


def _visible_ten_gods(day_master: str, pillars: dict[str, Pillar]) -> list[TenGodPosition]:
    rows: list[TenGodPosition] = []
    for position, pillar in pillars.items():
        if position == "day":
            continue
        rows.append(
            TenGodPosition(
                label=ten_god(day_master, pillar.stem),
                stem=pillar.stem,
                pillar=position,
                layer="visible",
                element=element_of_stem(pillar.stem),
                weight=1.0,
            )
        )
    return rows


def _hidden_ten_gods(day_master: str, pillars: dict[str, Pillar]) -> tuple[TenGodPosition, ...]:
    rows: list[TenGodPosition] = []
    for position, pillar in pillars.items():
        for stem, weight in HIDDEN_STEMS.get(pillar.branch, ()):
            rows.append(
                TenGodPosition(
                    label=ten_god(day_master, stem),
                    stem=stem,
                    pillar=position,
                    layer="hidden",
                    element=element_of_stem(stem),
                    weight=weight,
                )
            )
    return tuple(rows)


def _vault_branches(pillars: dict[str, Pillar]) -> list[str]:
    return [position for position, pillar in pillars.items() if pillar.branch in VAULT_BRANCHES]


def _base_fact_summary(
    *,
    day_master: str,
    day_master_element: str,
    pillars: dict[str, Pillar],
    visible: list[TenGodPosition],
    hidden: tuple[TenGodPosition, ...],
    relations: list[RelationHit],
    vault_branches: list[str],
    elements: dict[str, float],
) -> dict[str, object]:
    strongest = _extreme_element_names(elements, max)
    weakest = _extreme_element_names(elements, min)
    return {
        "version": "v30.base_bazi_fact_summary.v1",
        "status": "ready",
        "day_master": day_master,
        "day_master_element": day_master_element,
        "pillar_count": len(pillars),
        "visible_ten_god_count": len(visible),
        "hidden_ten_god_count": len(hidden),
        "relation_count": len(relations),
        "visible_ten_god_counts": _label_counts(row.label for row in visible),
        "hidden_ten_god_counts": _label_counts(row.label for row in hidden),
        "hidden_stem_summary": [
            {
                "pillar": row.pillar,
                "stem": row.stem,
                "ten_god": row.label,
                "element": row.element,
                "weight": row.weight,
            }
            for row in hidden
        ],
        "relation_type_counts": _label_counts(row.relation_type for row in relations),
        "relation_families": sorted({row.relation_type for row in relations}),
        "vault_branches": vault_branches,
        "root_fact_summary": _root_fact_summary(
            day_master=day_master,
            day_master_element=day_master_element,
            pillars=pillars,
            hidden=hidden,
            vault_branches=vault_branches,
        ),
        "element_distribution": elements,
        "strongest_elements": strongest,
        "weakest_elements": weakest,
        "fact_sources": [
            "four_pillars",
            "visible_ten_gods",
            "hidden_ten_gods",
            "five_element_distribution",
            "branch_relations",
            "root_and_vault_facts",
        ],
        "guardrails": [
            "BASE_FACTS_FROM_DETERMINISTIC_CHART_CONTEXT",
            "NO_STRENGTH_OR_USEFUL_GOD_VERDICT",
            "NO_LLM_FACT_GENERATION",
        ],
        "boundary": "base_bazi_fact_summary_expands_chart_facts_without_judgment",
}


def _root_fact_summary(
    *,
    day_master: str,
    day_master_element: str,
    pillars: dict[str, Pillar],
    hidden: tuple[TenGodPosition, ...],
    vault_branches: list[str],
) -> dict[str, object]:
    exact_roots = [
        _root_row(row, pillars)
        for row in hidden
        if row.stem == day_master
    ]
    same_element_roots = [
        _root_row(row, pillars)
        for row in hidden
        if row.element == day_master_element
    ]
    return {
        "version": "v30.root_vault_fact_summary.v1",
        "status": "ready",
        "day_master_root_count": len(exact_roots),
        "same_element_root_count": len(same_element_roots),
        "day_master_roots": exact_roots,
        "same_element_roots": same_element_roots,
        "vault_branches": [
            {
                "pillar": position,
                "branch": pillars[position].branch,
                "element": _vault_element(pillars[position].branch),
            }
            for position in vault_branches
            if position in pillars
        ],
        "guardrails": [
            "ROOT_FACTS_ARE_HIDDEN_STEM_PRESENCE_ONLY",
            "NO_STRENGTH_VERDICT_FROM_ROOT_FACTS",
            "NO_USEFUL_GOD_VERDICT_FROM_VAULT_FACTS",
        ],
        "boundary": "root_vault_summary_records_presence_without_strength_or_useful_god_verdict",
    }


def _root_row(row: TenGodPosition, pillars: dict[str, Pillar]) -> dict[str, object]:
    pillar = pillars.get(row.pillar)
    return {
        "pillar": row.pillar,
        "branch": pillar.branch if pillar is not None else "",
        "stem": row.stem,
        "ten_god": row.label,
        "element": row.element,
        "weight": row.weight,
    }


def _vault_element(branch: str) -> str:
    return {
        "辰": "water",
        "戌": "fire",
        "丑": "metal",
        "未": "wood",
    }.get(branch, "")


def _label_counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _extreme_element_names(elements: dict[str, float], fn: Any) -> list[str]:
    if not elements:
        return []
    target = fn(elements.values())
    return sorted(key for key, value in elements.items() if value == target)


def _time_layer_seed(layer: Any) -> dict[str, str]:
    return {
        "layer_key": layer.layer_key,
        "pillar": layer.pillar.display,
        "ten_god": layer.ten_god.label,
    }


def _pending_birth_input_conversion_trace(
    reading_id: str,
    birth_input: BirthInput,
) -> CalendarConversionTrace:
    boundary_flags = [
        "solar_term_boundary_requires_engine",
        "late_zi_hour_boundary_requires_policy",
        "timezone_assumption_recorded",
    ]
    if birth_input.unknown_hour:
        boundary_flags.append("unknown_hour_blocks_hour_pillar")
    if birth_input.use_true_solar_time:
        boundary_flags.append("true_solar_time_requires_location_resolution")
    return CalendarConversionTrace(
        trace_id=f"{reading_id}:calendar-conversion:pending",
        status="pending",
        calendar_type=birth_input.calendar_type,
        timezone=birth_input.timezone,
        use_true_solar_time=birth_input.use_true_solar_time,
        unknown_hour=birth_input.unknown_hour,
        boundary_flags=boundary_flags,
        steps=[
            {
                "step": "birth_input_received",
                "status": "ready",
                "source": birth_input.source,
            },
            {
                "step": "calendar_conversion",
                "status": "pending",
                "reason": "deterministic_calendar_engine_not_implemented",
            },
        ],
        missing_requirements=[
            "deterministic_calendar_conversion_engine",
            "solar_term_boundary_table",
            "late_zi_hour_policy",
        ],
        guardrails=[
            "TRACE_ONLY_UNTIL_CONVERSION_READY",
            "NO_CHART_FACTS_FROM_LLM_OR_TRAINING",
        ],
    )


def _birth_input_pending_result(
    *,
    reading_id: str,
    birth_input: BirthInput,
    failure: str,
    trace_status: str = "pending",
    extra_missing: list[str] | None = None,
) -> BirthChartBuildResult:
    trace = _pending_birth_input_conversion_trace(reading_id, birth_input).model_copy(
        update={
            "status": trace_status,
            "missing_requirements": _dedupe(
                [
                    *_pending_birth_input_conversion_trace(reading_id, birth_input).missing_requirements,
                    *(extra_missing or []),
                ]
            ),
        }
    )
    source = ChartBuildSource(
        source_type="birth_input",
        input_id=birth_input.input_id,
        calendar_assumption=birth_input.calendar_assumption,
        status=trace_status,
        source=birth_input.source,
        guardrails=[
            "BIRTH_INPUT_REQUIRES_DETERMINISTIC_CALENDAR_CONVERSION",
            "NO_LLM_FACT_GENERATION",
            "NO_SYNTHETIC_FACT_GENERATION",
        ],
    )
    missing = ["year", "month", "day", "hour"]
    result = FourPillarResult(
        status=trace_status,
        pillars={},
        missing_pillars=missing,
        chart_build_source=source,
        conversion_trace=trace,
        guardrails=[
            "FOUR_PILLARS_NOT_AVAILABLE_UNTIL_CONVERSION_READY",
            "DO_NOT_FABRICATE_UNKNOWN_HOUR",
        ],
    )
    return BirthChartBuildResult(
        reading_id=reading_id,
        birth_input=birth_input,
        four_pillar_result=result,
        chart_context=None,
        status=trace_status,
        failures=[failure],
    )


def _ready_birth_input_conversion_trace(
    reading_id: str,
    birth_input: BirthInput,
    local_dt: datetime,
    *,
    conversion_dt: datetime | None = None,
    effective_solar_dt: datetime | None = None,
    true_solar: dict[str, object] | None = None,
) -> CalendarConversionTrace:
    boundary_flags = ["timezone_assumption_recorded"]
    if local_dt.hour == 23:
        boundary_flags.append("late_zi_hour_boundary_recorded")
    if birth_input.calendar_type == "solar" and _near_year_month_solar_term_boundary(local_dt):
        boundary_flags.append("solar_term_year_month_boundary_recorded")
    if birth_input.calendar_type == "lunar":
        boundary_flags.append("lunar_calendar_conversion_recorded")
        if birth_input.lunar_is_leap_month:
            boundary_flags.append("lunar_leap_month_recorded")
    if birth_input.use_true_solar_time:
        boundary_flags.append("true_solar_time_adjustment_recorded")
    conversion_dt = conversion_dt or local_dt
    effective_solar_dt = effective_solar_dt or conversion_dt
    true_solar = true_solar or {}
    conversion_step = {
        "step": "lunar_calendar_conversion" if birth_input.calendar_type == "lunar" else "solar_calendar_conversion",
        "status": "ready",
        "engine": "lunar_python",
        "local_datetime": local_dt.isoformat(),
        "conversion_datetime": conversion_dt.isoformat(),
        "effective_solar_datetime": effective_solar_dt.isoformat(),
    }
    if true_solar:
        conversion_step["true_solar"] = {
            key: value for key, value in true_solar.items() if key != "datetime"
        }
    return CalendarConversionTrace(
        trace_id=f"{reading_id}:calendar-conversion:ready",
        status="ready",
        calendar_type=birth_input.calendar_type,
        timezone=birth_input.timezone,
        use_true_solar_time=birth_input.use_true_solar_time,
        unknown_hour=birth_input.unknown_hour,
        boundary_flags=boundary_flags,
        steps=[
            {
                "step": "birth_input_received",
                "status": "ready",
                "source": birth_input.source,
            },
            {
                "step": "timezone_validated",
                "status": "ready",
                "timezone": birth_input.timezone,
            },
            conversion_step,
        ],
        missing_requirements=[],
        guardrails=[
            "DETERMINISTIC_CALENDAR_ENGINE_ONLY",
            "NO_CHART_FACTS_FROM_LLM_OR_TRAINING",
        ],
    )


def _near_year_month_solar_term_boundary(local_dt: datetime) -> bool:
    return local_dt.month == 2 and 3 <= local_dt.day <= 5


def _parse_birth_local_datetime(birth_input: BirthInput) -> datetime:
    try:
        ZoneInfo(birth_input.timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("invalid_timezone") from exc
    try:
        date_part = datetime.strptime(birth_input.birth_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("invalid_birth_date") from exc
    raw_time = str(birth_input.birth_time or "").strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            time_part = datetime.strptime(raw_time, fmt).time()
            return datetime.combine(date_part, time_part)
        except ValueError:
            continue
    raise ValueError("invalid_birth_time")


def _resolve_true_solar_datetime(birth_input: BirthInput, local_dt: datetime) -> dict[str, object]:
    if not birth_input.use_true_solar_time:
        return {"status": "not_requested", "datetime": local_dt}
    longitude = _birth_place_longitude(birth_input.birth_place)
    if longitude is None:
        return {
            "status": "blocked",
            "failure": "birth_place_longitude_resolution_required",
            "missing_requirements": ["birth_place_longitude_resolution"],
        }
    standard_meridian = TIMEZONE_STANDARD_MERIDIAN.get(birth_input.timezone)
    if standard_meridian is None:
        return {
            "status": "blocked",
            "failure": "true_solar_timezone_meridian_policy_missing",
            "missing_requirements": ["true_solar_timezone_meridian_policy"],
        }
    offset_minutes = round((longitude - standard_meridian) * 4)
    adjusted = local_dt + timedelta(minutes=offset_minutes)
    return {
        "status": "ready",
        "datetime": adjusted,
        "birth_place": birth_input.birth_place,
        "longitude": round(longitude, 4),
        "timezone": birth_input.timezone,
        "standard_meridian": standard_meridian,
        "offset_minutes": offset_minutes,
        "policy": "longitude_minus_timezone_meridian_minutes",
    }


def _birth_place_longitude(value: str) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        longitude = float(text)
        if -180.0 <= longitude <= 180.0:
            return longitude
        return None
    except ValueError:
        pass
    return TRUE_SOLAR_LONGITUDE_BY_PLACE.get(text.lower()) or TRUE_SOLAR_LONGITUDE_BY_PLACE.get(text)


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
