from __future__ import annotations

from array import array
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from importlib.metadata import version
from typing import Any

from lunar_python import Solar

from core.audit.chart_universe import (
    UNIVERSE_SIZE,
    chart_index,
    chart_key,
    hour_options_for,
    structural_invalid_reasons,
)
from core.contracts import BirthInputCanonical
from core.engines import BirthCalendarResolutionError, resolve_birth_input_pillars
from core.engines.bazi.pillar_cycle import BIRTH_YEAR_MAX, BIRTH_YEAR_MIN
from core.engines.bazi.temporal_service import (
    DEFAULT_CALENDAR_PROFILE,
    TEMPORAL_SERVICE_VERSION,
    CanonicalTemporalService,
)
from core.engines.birth_calendar import BIRTH_PILLAR_ENGINE_VERSION


JIE_NAMES = (
    "小寒",
    "立春",
    "惊蛰",
    "清明",
    "立夏",
    "芒种",
    "小暑",
    "立秋",
    "白露",
    "寒露",
    "立冬",
    "大雪",
)
BRANCH_REPRESENTATIVE_TIMES = (
    time(0, 30),
    time(2, 0),
    time(4, 0),
    time(6, 0),
    time(8, 0),
    time(10, 0),
    time(12, 0),
    time(14, 0),
    time(16, 0),
    time(18, 0),
    time(20, 0),
    time(22, 0),
)

BOUNDARY_SOLAR_TERM = 1
BOUNDARY_ZI_ROLLOVER = 2
BOUNDARY_RANGE_EDGE = 4
BOUNDARY_LABELS = {
    BOUNDARY_SOLAR_TERM: "SOLAR_TERM_BOUNDARY_ADJACENT",
    BOUNDARY_ZI_ROLLOVER: "ZI_ROLLOVER_POLICY_SENSITIVE",
    BOUNDARY_RANGE_EDGE: "RANGE_EDGE_SENSITIVE",
}


@dataclass(frozen=True)
class CalendarRange:
    range_id: str
    label: str
    start: datetime
    end: datetime
    exact_start: datetime | None = None
    exact_end: datetime | None = None
    source: str = ""

    def contains(self, value: datetime) -> bool:
        return self.start <= value < self.end

    def as_dict(self) -> dict[str, Any]:
        return {
            "range_id": self.range_id,
            "label": self.label,
            "effective_start_local_civil": self.start.isoformat(),
            "effective_end_exclusive_local_civil": self.end.isoformat(),
            "exact_start_backend": self.exact_start.isoformat() if self.exact_start else None,
            "exact_end_backend": self.exact_end.isoformat() if self.exact_end else None,
            "source": self.source,
        }


@dataclass
class RangeAccumulator:
    definition: CalendarRange
    realizable: bytearray = field(default_factory=lambda: bytearray(UNIVERSE_SIZE))
    first_witness_minute: array = field(
        default_factory=lambda: array("q", [-1]) * UNIVERSE_SIZE
    )
    boundary_flags: bytearray = field(default_factory=lambda: bytearray(UNIVERSE_SIZE))
    timestamp_observation_count: int = 0
    solar_term_boundary_event_count: int = 0
    zi_rollover_policy_event_count: int = 0

    def record(self, pillars: tuple[str, str, str, str], at: datetime) -> None:
        index = chart_index(pillars)
        self.timestamp_observation_count += 1
        if not self.realizable[index]:
            self.realizable[index] = 1
            self.first_witness_minute[index] = civil_minute(at)

    def mark_boundary(self, pillars: tuple[str, str, str, str], flag: int) -> None:
        self.boundary_flags[chart_index(pillars)] |= flag

    @property
    def realizable_count(self) -> int:
        return sum(self.realizable)

    @property
    def unseen_count(self) -> int:
        return UNIVERSE_SIZE - self.realizable_count

    @property
    def boundary_ambiguous_chart_count(self) -> int:
        return sum(bool(value) for value in self.boundary_flags)

    def boundary_count(self, flag: int) -> int:
        return sum(bool(value & flag) for value in self.boundary_flags)


@dataclass
class CalendarScanResult:
    ranges: dict[str, RangeAccumulator]
    calendar_days_scanned: int
    canonical_resolution_call_count: int
    annual_authority_crosscheck_count: int
    actual_timestamp_structural_failure_count: int
    canonical_raw_late_zi_invalid_count: int
    canonical_raw_late_zi_invalid_samples: list[dict[str, Any]]
    jie_boundary_count: int
    boundary_samples: list[dict[str, Any]]
    policy: dict[str, Any]


class CanonicalCalendarReader:
    """Audit adapter over existing formal temporal and birth-calendar owners."""

    def __init__(self, timezone: str = "Asia/Shanghai") -> None:
        self.timezone = timezone
        self.temporal_service = CanonicalTemporalService()
        self.canonical_resolution_call_count = 0
        self.canonical_raw_late_zi_invalid_count = 0
        self.canonical_raw_late_zi_invalid_samples: list[dict[str, Any]] = []
        self._canonical_raw_late_zi_invalid_timestamps: set[datetime] = set()

    def official_pillars(self, at: datetime) -> tuple[str, str, str, str]:
        self.canonical_resolution_call_count += 1
        birth = BirthInputCanonical(
            birth_input_id=f"ra0:{at.isoformat(timespec='minutes')}",
            gender="unknown",
            calendar_type="solar",
            birth_date=at.date().isoformat(),
            birth_time=at.strftime("%H:%M"),
            timezone=self.timezone,
            true_solar_time_policy="not_applied",
            input_quality="ra0_calendar_realizability_audit",
        )
        try:
            resolved = resolve_birth_input_pillars(birth)
            pillars = (
                resolved.year_pillar,
                resolved.month_pillar,
                resolved.day_pillar,
                resolved.hour_pillar,
            )
        except BirthCalendarResolutionError as exc:
            if str(exc) != "birth_calendar_returned_invalid_pillars" or at.hour != 23:
                raise
            raw = self._raw_pillars(at, sect=2)
            raw_reasons = structural_invalid_reasons(raw)
            if not raw_reasons:
                raise
            pillars = (raw[0], raw[1], raw[2], hour_options_for(raw[2])[0])
            is_new_timestamp = at not in self._canonical_raw_late_zi_invalid_timestamps
            self._canonical_raw_late_zi_invalid_timestamps.add(at)
            self.canonical_raw_late_zi_invalid_count = len(
                self._canonical_raw_late_zi_invalid_timestamps
            )
            if is_new_timestamp and len(self.canonical_raw_late_zi_invalid_samples) < 12:
                self.canonical_raw_late_zi_invalid_samples.append({
                    "timestamp": at.isoformat(),
                    "raw_chart_key": chart_key(raw),
                    "raw_invalid_reasons": list(raw_reasons),
                    "audit_normalized_chart_key": chart_key(pillars),
                    "normalization_source": "formal_five_rats_for_formal_sect_2_day_pillar",
                })
        reasons = structural_invalid_reasons(pillars)
        if reasons:
            raise ValueError(f"canonical_timestamp_returned_invalid_chart:{','.join(reasons)}")
        return pillars

    def sensitivity_pillars(self, at: datetime, *, sect: int) -> tuple[str, str, str, str]:
        pillars = self._raw_pillars(at, sect=sect)
        reasons = structural_invalid_reasons(pillars)
        if reasons:
            raise ValueError(f"sensitivity_timestamp_returned_invalid_chart:{','.join(reasons)}")
        return pillars

    @staticmethod
    def _raw_pillars(at: datetime, *, sect: int) -> tuple[str, str, str, str]:
        lunar = Solar.fromYmdHms(
            at.year,
            at.month,
            at.day,
            at.hour,
            at.minute,
            0,
        ).getLunar()
        eight_char = lunar.getEightChar()
        eight_char.setSect(sect)
        return (
            eight_char.getYear(),
            eight_char.getMonth(),
            eight_char.getDay(),
            eight_char.getTime(),
        )

    def annual_crosscheck(self, year: int) -> bool:
        official = self.official_pillars(datetime(year, 7, 1, 12, 0))[0]
        return official == self.temporal_service.derive_annual_pillar(year)

    def policy_manifest(self) -> dict[str, Any]:
        return {
            "temporal_service_version": TEMPORAL_SERVICE_VERSION,
            "birth_pillar_engine_version": BIRTH_PILLAR_ENGINE_VERSION,
            "calendar_profile": DEFAULT_CALENDAR_PROFILE,
            "calendar_dependency": f"lunar_python.{version('lunar_python')}",
            "year_boundary": "lichun_exact_backend_effective_at_first_supported_minute",
            "month_boundary": "twelve_jie_exact_backend_effective_at_first_supported_minute",
            "day_rollover_formal": "midnight_lunar_python_sect_2",
            "day_rollover_sensitivity": "late_zi_lunar_python_sect_1_read_only_comparison",
            "late_zi_audit_normalization": "when canonical raw sect_2 day and hour stem disagree, retain rejection evidence and derive Zi hour from the formal day pillar using existing Five Rats rules",
            "input_precision": "minute",
            "timezone": self.timezone,
            "timezone_application": "validated_label_local_civil_time_not_converted_by_birth_pillar_engine",
            "true_solar_time": "not_applied",
            "historical_dst": "not_normalized_by_birth_pillar_engine_local_civil_input_used_as_supplied",
            "product_birth_year_support": [BIRTH_YEAR_MIN, BIRTH_YEAR_MAX],
            "llm_used": False,
            "formal_algorithm_modified": False,
        }


def default_audit_ranges() -> tuple[CalendarRange, CalendarRange, CalendarRange]:
    reference_start_exact = lichun(1984)
    reference_end_exact = lichun(2044)
    extended_start_exact = lichun(1804)
    extended_end_exact = reference_end_exact
    return (
        CalendarRange(
            range_id="reference_60y_1984_2044",
            label="1984 LiChun to 2044 LiChun",
            start=ceil_minute(reference_start_exact),
            end=ceil_minute(reference_end_exact),
            exact_start=reference_start_exact,
            exact_end=reference_end_exact,
            source="requested_reference_jiazi_cycle",
        ),
        CalendarRange(
            range_id="product_supported_1900_2100",
            label="Current product full supported civil-date range",
            start=datetime(BIRTH_YEAR_MIN, 1, 1, 0, 0),
            end=datetime(BIRTH_YEAR_MAX + 1, 1, 1, 0, 0),
            source="pillar_cycle.BIRTH_YEAR_MIN_MAX",
        ),
        CalendarRange(
            range_id="extended_4_jiazi_1804_2044",
            label="Four Jiazi cycles: 1804 LiChun to 2044 LiChun",
            start=ceil_minute(extended_start_exact),
            end=ceil_minute(extended_end_exact),
            exact_start=extended_start_exact,
            exact_end=extended_end_exact,
            source="calendar_engine_capability_probe_four_jiazi_cycles",
        ),
    )


def scan_calendar_realizability(
    ranges: tuple[CalendarRange, ...] | list[CalendarRange],
    *,
    timezone: str = "Asia/Shanghai",
    boundary_sample_limit: int = 48,
) -> CalendarScanResult:
    if not ranges:
        raise ValueError("at_least_one_calendar_range_required")
    if any(item.start >= item.end for item in ranges):
        raise ValueError("calendar_range_start_must_precede_end")

    reader = CanonicalCalendarReader(timezone=timezone)
    accumulators = {item.range_id: RangeAccumulator(definition=item) for item in ranges}
    scan_start = min(item.start for item in ranges)
    scan_end = max(item.end for item in ranges)
    boundary_by_date = _jie_boundaries_by_date(scan_start, scan_end)
    boundary_samples: list[dict[str, Any]] = []
    actual_timestamp_structural_failure_count = 0
    annual_crosschecks = 0
    days_scanned = 0

    current = scan_start.date()
    final_date = (scan_end - timedelta(minutes=1)).date()
    while current <= final_date:
        days_scanned += 1
        noon = datetime.combine(current, time(12, 0))
        base_pillars = reader.official_pillars(noon)
        if current.month == 7 and current.day == 1:
            annual_crosschecks += 1
            if base_pillars[0] != reader.temporal_service.derive_annual_pillar(current.year):
                raise ValueError(f"annual_authority_mismatch:{current.year}")

        terms = boundary_by_date.get(current, ())
        if terms:
            samples = {datetime.combine(current, item) for item in BRANCH_REPRESENTATIVE_TIMES}
            samples.add(datetime.combine(current, time(23, 30)))
            for _, exact in terms:
                transition = ceil_minute(exact)
                samples.update({transition - timedelta(minutes=1), transition, transition + timedelta(minutes=1)})
            for at in sorted(value for value in samples if value.date() == current):
                pillars = reader.official_pillars(at)
                actual_timestamp_structural_failure_count += _record_in_ranges(
                    accumulators, pillars, at
                )
        else:
            year_pillar, month_pillar, day_pillar, _ = base_pillars
            for branch_time, hour_pillar in zip(
                BRANCH_REPRESENTATIVE_TIMES,
                hour_options_for(day_pillar),
                strict=True,
            ):
                at = datetime.combine(current, branch_time)
                pillars = (year_pillar, month_pillar, day_pillar, hour_pillar)
                actual_timestamp_structural_failure_count += _record_in_ranges(
                    accumulators, pillars, at
                )

        for term_name, exact in terms:
            transition = ceil_minute(exact)
            before = transition - timedelta(minutes=1)
            after = transition
            before_pillars = reader.official_pillars(before)
            after_pillars = reader.official_pillars(after)
            for accumulator in accumulators.values():
                touched = False
                if accumulator.definition.contains(before):
                    accumulator.mark_boundary(before_pillars, BOUNDARY_SOLAR_TERM)
                    touched = True
                if accumulator.definition.contains(after):
                    accumulator.mark_boundary(after_pillars, BOUNDARY_SOLAR_TERM)
                    touched = True
                if touched:
                    accumulator.solar_term_boundary_event_count += 1
            if len(boundary_samples) < boundary_sample_limit:
                boundary_samples.append({
                    "boundary_type": "solar_term",
                    "term": term_name,
                    "exact_backend_timestamp": exact.isoformat(),
                    "effective_minute": transition.isoformat(),
                    "before_chart_key": chart_key(before_pillars),
                    "after_chart_key": chart_key(after_pillars),
                })

        zi_time = datetime.combine(current, time(23, 30))
        active_zi_ranges = [
            item for item in accumulators.values() if item.definition.contains(zi_time)
        ]
        if active_zi_ranges:
            if terms:
                official_zi = reader.official_pillars(zi_time)
            else:
                official_zi = (
                    base_pillars[0],
                    base_pillars[1],
                    base_pillars[2],
                    hour_options_for(base_pillars[2])[0],
                )
            alternate_zi = reader.sensitivity_pillars(zi_time, sect=1)
            if official_zi != alternate_zi:
                for accumulator in active_zi_ranges:
                    accumulator.mark_boundary(official_zi, BOUNDARY_ZI_ROLLOVER)
                    accumulator.mark_boundary(alternate_zi, BOUNDARY_ZI_ROLLOVER)
                    accumulator.zi_rollover_policy_event_count += 1
                if len(boundary_samples) < boundary_sample_limit:
                    boundary_samples.append({
                        "boundary_type": "zi_rollover_policy",
                        "timestamp": zi_time.isoformat(),
                        "formal_sect_2_chart_key": chart_key(official_zi),
                        "sensitivity_sect_1_chart_key": chart_key(alternate_zi),
                    })

        current += timedelta(days=1)

    _mark_range_edges(accumulators, reader, boundary_samples, boundary_sample_limit)
    return CalendarScanResult(
        ranges=accumulators,
        calendar_days_scanned=days_scanned,
        canonical_resolution_call_count=reader.canonical_resolution_call_count,
        annual_authority_crosscheck_count=annual_crosschecks,
        actual_timestamp_structural_failure_count=actual_timestamp_structural_failure_count,
        canonical_raw_late_zi_invalid_count=reader.canonical_raw_late_zi_invalid_count,
        canonical_raw_late_zi_invalid_samples=reader.canonical_raw_late_zi_invalid_samples,
        jie_boundary_count=sum(len(items) for items in boundary_by_date.values()),
        boundary_samples=boundary_samples,
        policy=reader.policy_manifest(),
    )


def boundary_labels(value: int) -> list[str]:
    return [label for flag, label in BOUNDARY_LABELS.items() if value & flag]


def civil_minute(value: datetime) -> int:
    return value.toordinal() * 1440 + value.hour * 60 + value.minute


def datetime_from_civil_minute(value: int) -> datetime:
    ordinal, minute_of_day = divmod(value, 1440)
    hour, minute = divmod(minute_of_day, 60)
    return datetime.combine(date.fromordinal(ordinal), time(hour, minute))


def ceil_minute(value: datetime) -> datetime:
    base = value.replace(second=0, microsecond=0)
    return base if value.second == 0 and value.microsecond == 0 else base + timedelta(minutes=1)


@lru_cache(maxsize=None)
def jie_boundaries(year: int) -> tuple[tuple[str, datetime], ...]:
    table = Solar.fromYmd(year, 7, 1).getLunar().getJieQiTable()
    rows: list[tuple[str, datetime]] = []
    for name in JIE_NAMES:
        solar = table[name]
        if solar.getYear() != year:
            continue
        rows.append((
            name,
            datetime(
                solar.getYear(),
                solar.getMonth(),
                solar.getDay(),
                solar.getHour(),
                solar.getMinute(),
                solar.getSecond(),
            ),
        ))
    if len(rows) != 12:
        raise ValueError(f"expected_twelve_jie_boundaries:{year}:{len(rows)}")
    return tuple(sorted(rows, key=lambda item: item[1]))


def lichun(year: int) -> datetime:
    return next(value for name, value in jie_boundaries(year) if name == "立春")


def _jie_boundaries_by_date(
    start: datetime,
    end: datetime,
) -> dict[date, tuple[tuple[str, datetime], ...]]:
    rows: dict[date, list[tuple[str, datetime]]] = defaultdict(list)
    for year in range(start.year - 1, end.year + 2):
        for name, value in jie_boundaries(year):
            if start - timedelta(days=1) <= value < end + timedelta(days=1):
                rows[value.date()].append((name, value))
    return {
        key: tuple(sorted(values, key=lambda item: item[1]))
        for key, values in rows.items()
    }


def _record_in_ranges(
    accumulators: dict[str, RangeAccumulator],
    pillars: tuple[str, str, str, str],
    at: datetime,
) -> int:
    reasons = structural_invalid_reasons(pillars)
    if reasons:
        raise ValueError(f"actual_timestamp_structural_failure:{at.isoformat()}:{','.join(reasons)}")
    for accumulator in accumulators.values():
        if accumulator.definition.contains(at):
            accumulator.record(pillars, at)
    return 0


def _mark_range_edges(
    accumulators: dict[str, RangeAccumulator],
    reader: CanonicalCalendarReader,
    boundary_samples: list[dict[str, Any]],
    sample_limit: int,
) -> None:
    for accumulator in accumulators.values():
        start = accumulator.definition.start
        end_before = accumulator.definition.end - timedelta(minutes=1)
        for label, value in (("start", start), ("end", end_before)):
            pillars = reader.official_pillars(value)
            accumulator.mark_boundary(pillars, BOUNDARY_RANGE_EDGE)
            if len(boundary_samples) < sample_limit:
                boundary_samples.append({
                    "boundary_type": "range_edge",
                    "range_id": accumulator.definition.range_id,
                    "edge": label,
                    "timestamp": value.isoformat(),
                    "chart_key": chart_key(pillars),
                })
