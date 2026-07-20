from __future__ import annotations

import hashlib
import json
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lunar_python import Solar

from core.contracts.base import CalendarType, Gender
from core.contracts.birth import BirthInputCanonical
from core.engines.bazi.chart_constraints import validate_four_pillars
from core.engines.bazi.dayun import annual_pillar, dayun_sequence, structural_dayun_sequence
from core.engines.bazi.pillar_cycle import BIRTH_YEAR_MAX, BIRTH_YEAR_MIN


TEMPORAL_SERVICE_VERSION = "v50.canonical_temporal_service.v1"
DEFAULT_RULE_PROFILE = "v50.dayun.standard.v1"
DEFAULT_CALENDAR_PROFILE = "lunar_python.sect2.v1"


class CanonicalTemporalService:
    """The sole application-facing authority for DaYun and annual timing facts."""

    def derive_annual_pillar(self, year: int) -> str:
        return annual_pillar(year)

    def resolve_world_timing(
        self,
        *,
        birth_input: BirthInputCanonical,
        analysis_year: int,
        limit: int = 12,
        baseline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve timing or explicitly refuse legacy/research-invalid pillar facts.

        Formal intake must use the strict birth calendar authority. This read-only
        boundary lets old research fixtures remain inspectable without deriving,
        inheriting or fabricating DaYun from an invalid chart.
        """
        try:
            return self.resolve_exact_dayun(
                birth_input=birth_input,
                analysis_year=analysis_year,
                limit=limit,
                baseline=baseline,
            )
        except ValueError as exc:
            reason = str(exc)
            if not (
                reason.startswith("invalid_")
                or reason.endswith("_not_legal_for_year")
                or reason.endswith("_not_legal_for_day")
            ):
                raise
            pillars = [
                birth_input.year_pillar,
                birth_input.month_pillar,
                birth_input.day_pillar,
                birth_input.hour_pillar,
            ]
            fingerprint = self.derivation_fingerprint(
                pillars=pillars,
                gender=birth_input.gender,
                analysis_year=analysis_year,
                timezone=birth_input.timezone,
                birth_anchor={"source_mode": "legacy_or_research_read_only"},
            )
            return {
                "schema_version": TEMPORAL_SERVICE_VERSION,
                "resolution_level": "pillar_facts_rejected",
                "status": "unresolved",
                "recomputation_status": "unresolved",
                "fact_integrity_status": "rejected",
                "rejection_reasons": [reason],
                "gender": birth_input.gender.value,
                "direction": "unresolved",
                "analysis_year": analysis_year,
                "annual_pillar": annual_pillar(analysis_year),
                "luck_sequence": [],
                "current_luck_status": "unresolved",
                "luck_pillar": "",
                "luck_year_range": [],
                "luck_age_range": [None, None],
                "birth_anchor": None,
                "missing_inputs": ["valid_four_pillars_required_for_dayun"],
                "calculation_refs": [f"calendar.sexagenary_year:{analysis_year}"],
                "derivation_fingerprint": fingerprint,
                "formal_state_modified": False,
            }

    def resolve_structural_dayun(
        self,
        *,
        pillars: list[str] | tuple[str, str, str, str],
        gender: Gender | str,
        analysis_year: int,
        timezone: str = "Asia/Shanghai",
        limit: int = 10,
        baseline: dict[str, Any] | None = None,
        rule_profile: str = DEFAULT_RULE_PROFILE,
        calendar_profile: str = DEFAULT_CALENDAR_PROFILE,
    ) -> dict[str, Any]:
        normalized_pillars = self._validated_pillars(pillars)
        normalized_gender = self._gender(gender)
        self._validate_timezone(timezone)
        fingerprint = self.derivation_fingerprint(
            pillars=normalized_pillars,
            gender=normalized_gender,
            analysis_year=analysis_year,
            timezone=timezone,
            birth_anchor=None,
            rule_profile=rule_profile,
            calendar_profile=calendar_profile,
        )
        if normalized_gender == Gender.UNKNOWN:
            return self._unresolved(
                pillars=normalized_pillars,
                gender=normalized_gender,
                analysis_year=analysis_year,
                fingerprint=fingerprint,
                reason="gender_required_for_luck_direction",
                resolution_level="structural_valid",
            )

        direction, sequence = structural_dayun_sequence(
            year_pillar=normalized_pillars[0],
            month_pillar=normalized_pillars[1],
            gender=normalized_gender,
            limit=limit,
        )
        return {
            "schema_version": TEMPORAL_SERVICE_VERSION,
            "resolution_level": "structural_valid",
            "status": self._comparison_status(sequence=sequence, baseline=baseline),
            "recomputation_status": self._comparison_status(sequence=sequence, baseline=baseline),
            "gender": normalized_gender.value,
            "direction": direction,
            "analysis_year": analysis_year,
            "annual_pillar": annual_pillar(analysis_year),
            "luck_sequence": sequence,
            "current_luck_status": "unresolved",
            "luck_pillar": "",
            "luck_year_range": [],
            "luck_age_range": [None, None],
            "birth_anchor": None,
            "missing_inputs": ["real_birth_datetime_or_compatible_birth_year_anchor"],
            "calculation_refs": [
                "calendar.sexagenary_cycle",
                "calendar.five_tigers",
                "calendar.dayun_direction",
            ],
            "derivation_fingerprint": fingerprint,
            "rule_profile": rule_profile,
            "calendar_profile": calendar_profile,
            "formal_state_modified": False,
        }

    def resolve_calendar_candidates(
        self,
        *,
        pillars: list[str] | tuple[str, str, str, str],
        birth_year_anchor: int,
        timezone: str = "Asia/Shanghai",
    ) -> dict[str, Any]:
        normalized_pillars = self._validated_pillars(pillars)
        self._validate_timezone(timezone)
        if birth_year_anchor < BIRTH_YEAR_MIN or birth_year_anchor > BIRTH_YEAR_MAX:
            raise ValueError("birth_year_anchor_out_of_supported_range")
        matches = [
            solar
            for solar in Solar.fromBaZi(*normalized_pillars, sect=2, base_year=birth_year_anchor)
            if solar.getYear() == birth_year_anchor
        ]
        candidates = [
            {
                "candidate_ref": self._candidate_ref(solar.toYmdHms()),
                "birth_date": f"{solar.getYear():04d}-{solar.getMonth():02d}-{solar.getDay():02d}",
                "birth_time": f"{solar.getHour():02d}:{solar.getMinute():02d}",
                "timezone": timezone,
            }
            for solar in matches
        ]
        return {
            "status": "no_match" if not candidates else "candidate",
            "birth_year_anchor": birth_year_anchor,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "candidate_refs": [item["candidate_ref"] for item in candidates],
            "method": "four_pillars_reverse_lookup_sect_2",
            "formal_birth_record_modified": False,
        }

    def resolve_from_birth_year(
        self,
        *,
        pillars: list[str] | tuple[str, str, str, str],
        gender: Gender | str,
        birth_year_anchor: int,
        analysis_year: int,
        timezone: str = "Asia/Shanghai",
        limit: int = 12,
        baseline: dict[str, Any] | None = None,
        rule_profile: str = DEFAULT_RULE_PROFILE,
        calendar_profile: str = DEFAULT_CALENDAR_PROFILE,
    ) -> dict[str, Any]:
        normalized_pillars = self._validated_pillars(pillars)
        normalized_gender = self._gender(gender)
        self._validate_timezone(timezone)
        fingerprint = self.derivation_fingerprint(
            pillars=normalized_pillars,
            gender=normalized_gender,
            analysis_year=analysis_year,
            timezone=timezone,
            birth_anchor={"birth_year": birth_year_anchor},
            rule_profile=rule_profile,
            calendar_profile=calendar_profile,
        )
        if normalized_gender == Gender.UNKNOWN:
            return self._unresolved(
                pillars=normalized_pillars,
                gender=normalized_gender,
                analysis_year=analysis_year,
                fingerprint=fingerprint,
                reason="gender_required_for_luck_direction",
                resolution_level="structural_valid",
                birth_anchor={"birth_year": birth_year_anchor},
            )

        calendar_resolution = self.resolve_calendar_candidates(
            pillars=normalized_pillars,
            birth_year_anchor=birth_year_anchor,
            timezone=timezone,
        )
        if not calendar_resolution["candidates"]:
            structural = self.resolve_structural_dayun(
                pillars=normalized_pillars,
                gender=normalized_gender,
                analysis_year=analysis_year,
                timezone=timezone,
                limit=limit,
                baseline=baseline,
                rule_profile=rule_profile,
                calendar_profile=calendar_profile,
            )
            return {
                **structural,
                "derivation_fingerprint": fingerprint,
                "birth_anchor": {"birth_year": birth_year_anchor},
                "calendar_resolution": calendar_resolution,
                "missing_inputs": ["matching_birth_datetime_for_selected_four_pillars"],
            }

        exact_results = [
            self.resolve_exact_dayun(
                birth_input=BirthInputCanonical(
                    birth_input_id=f"temporal-reverse:{candidate['candidate_ref']}",
                    gender=normalized_gender,
                    calendar_type=CalendarType.SOLAR,
                    birth_date=candidate["birth_date"],
                    birth_time=candidate["birth_time"],
                    timezone=timezone,
                    year_pillar=normalized_pillars[0],
                    month_pillar=normalized_pillars[1],
                    day_pillar=normalized_pillars[2],
                    hour_pillar=normalized_pillars[3],
                    input_quality="calendar_verified_supplied",
                    warnings=["sandbox_candidate_not_formal_birth_record"],
                ),
                analysis_year=analysis_year,
                limit=limit,
                baseline=baseline,
                rule_profile=rule_profile,
                calendar_profile=calendar_profile,
            )
            for candidate in calendar_resolution["candidates"]
        ]
        signatures = {
            (
                str(item.get("luck_pillar") or ""),
                tuple(item.get("luck_year_range") or []),
                str(item.get("direction") or ""),
            )
            for item in exact_results
        }
        if len(signatures) != 1 or not next(iter(signatures))[0]:
            structural = self.resolve_structural_dayun(
                pillars=normalized_pillars,
                gender=normalized_gender,
                analysis_year=analysis_year,
                timezone=timezone,
                limit=limit,
                baseline=baseline,
                rule_profile=rule_profile,
                calendar_profile=calendar_profile,
            )
            return {
                **structural,
                "resolution_level": "calendar_resolved",
                "derivation_fingerprint": fingerprint,
                "birth_anchor": {"birth_year": birth_year_anchor},
                "calendar_resolution": {
                    **calendar_resolution,
                    "status": "ambiguous_current_luck",
                },
                "missing_inputs": ["unique_current_luck_across_calendar_candidates"],
            }

        result = dict(exact_results[0])
        result.update({
            "resolution_level": "active_dayun_resolved",
            "current_luck_status": "resolved_from_birth_year",
            "birth_anchor": {"birth_year": birth_year_anchor},
            "calendar_resolution": {**calendar_resolution, "status": "resolved"},
            "derivation_fingerprint": fingerprint,
            "calculation_mode": "birth_year_anchored_reverse_lookup",
            "formal_state_modified": False,
        })
        return result

    def resolve_exact_dayun(
        self,
        *,
        birth_input: BirthInputCanonical,
        analysis_year: int,
        limit: int = 12,
        baseline: dict[str, Any] | None = None,
        rule_profile: str = DEFAULT_RULE_PROFILE,
        calendar_profile: str = DEFAULT_CALENDAR_PROFILE,
    ) -> dict[str, Any]:
        pillars = self._validated_pillars([
            birth_input.year_pillar,
            birth_input.month_pillar,
            birth_input.day_pillar,
            birth_input.hour_pillar,
        ])
        self._validate_timezone(birth_input.timezone)
        gender = self._gender(birth_input.gender)
        birth_anchor = {
            "calendar_type": birth_input.calendar_type.value,
            "birth_date": birth_input.birth_date,
            "birth_time": birth_input.birth_time,
            "timezone": birth_input.timezone,
            "lunar_leap_month": birth_input.lunar_leap_month,
        }
        fingerprint = self.derivation_fingerprint(
            pillars=pillars,
            gender=gender,
            analysis_year=analysis_year,
            timezone=birth_input.timezone,
            birth_anchor=birth_anchor,
            rule_profile=rule_profile,
            calendar_profile=calendar_profile,
        )
        if gender == Gender.UNKNOWN:
            return self._unresolved(
                pillars=pillars,
                gender=gender,
                analysis_year=analysis_year,
                fingerprint=fingerprint,
                reason="gender_required_for_luck_direction",
                resolution_level="calendar_resolved",
                birth_anchor=birth_anchor,
            )
        sequence = dayun_sequence(birth_input, limit=limit)
        current = self.locate_observation_date(sequence=sequence, analysis_year=analysis_year)
        status = self._comparison_status(sequence=sequence, current=current, baseline=baseline)
        direction = self._direction_from_sequence(pillars=pillars, gender=gender, sequence=sequence)
        return {
            "schema_version": TEMPORAL_SERVICE_VERSION,
            "resolution_level": "active_dayun_resolved" if current else "calendar_resolved",
            "status": status,
            "recomputation_status": status,
            "gender": gender.value,
            "direction": direction,
            "analysis_year": analysis_year,
            "annual_pillar": annual_pillar(analysis_year),
            "luck_sequence": sequence,
            "current_luck_status": "resolved" if current else "unresolved",
            "luck_pillar": str(current["pillar"] if current else ""),
            "luck_year_range": [current["start_year"], current["end_year"]] if current else [],
            "luck_age_range": [current["start_age"], current["end_age"]] if current else [None, None],
            "birth_anchor": birth_anchor,
            "missing_inputs": [] if current else ["analysis_year_outside_resolved_luck_range"],
            "calculation_refs": [
                f"calendar.sexagenary_year:{analysis_year}",
                "calendar.lunar_python.eight_char_yun",
            ],
            "derivation_fingerprint": fingerprint,
            "rule_profile": rule_profile,
            "calendar_profile": calendar_profile,
            "formal_state_modified": False,
        }

    def locate_observation_date(
        self,
        *,
        sequence: list[dict[str, Any]],
        analysis_year: int,
    ) -> dict[str, Any] | None:
        return next(
            (
                period
                for period in sequence
                if period.get("start_year") is not None
                and period.get("end_year") is not None
                and int(period["start_year"]) <= analysis_year <= int(period["end_year"])
            ),
            None,
        )

    def derivation_fingerprint(
        self,
        *,
        pillars: list[str] | tuple[str, str, str, str],
        gender: Gender | str,
        analysis_year: int,
        timezone: str,
        birth_anchor: Any,
        rule_profile: str = DEFAULT_RULE_PROFILE,
        calendar_profile: str = DEFAULT_CALENDAR_PROFILE,
    ) -> str:
        normalized_gender = self._gender(gender)
        payload = {
            "service": TEMPORAL_SERVICE_VERSION,
            "pillars": list(pillars),
            "gender": normalized_gender.value,
            "analysis_year": int(analysis_year),
            "timezone": timezone,
            "birth_anchor": birth_anchor,
            "rule_profile": rule_profile,
            "calendar_profile": calendar_profile,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return f"temporal-fingerprint:{hashlib.sha256(encoded).hexdigest()}"

    def is_current(
        self,
        result: dict[str, Any],
        *,
        pillars: list[str] | tuple[str, str, str, str],
        gender: Gender | str,
        analysis_year: int,
        timezone: str,
        birth_anchor: Any,
        rule_profile: str = DEFAULT_RULE_PROFILE,
        calendar_profile: str = DEFAULT_CALENDAR_PROFILE,
    ) -> bool:
        expected = self.derivation_fingerprint(
            pillars=pillars,
            gender=gender,
            analysis_year=analysis_year,
            timezone=timezone,
            birth_anchor=birth_anchor,
            rule_profile=rule_profile,
            calendar_profile=calendar_profile,
        )
        return str(result.get("derivation_fingerprint") or "") == expected

    @staticmethod
    def _validated_pillars(
        pillars: list[str] | tuple[str, str, str, str],
    ) -> list[str]:
        normalized = [str(value or "").strip() for value in pillars]
        issues = validate_four_pillars(normalized)
        if issues:
            raise ValueError(issues[0].code)
        return normalized

    @staticmethod
    def _gender(value: Gender | str) -> Gender:
        try:
            return value if isinstance(value, Gender) else Gender(value)
        except ValueError as exc:
            raise ValueError("invalid_gender_for_temporal_resolution") from exc

    @staticmethod
    def _validate_timezone(value: str) -> None:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("invalid_temporal_timezone") from exc

    @staticmethod
    def _candidate_ref(value: str) -> str:
        return f"calendar-candidate:{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"

    @staticmethod
    def _comparison_status(
        *,
        sequence: list[dict[str, Any]],
        current: dict[str, Any] | None = None,
        baseline: dict[str, Any] | None,
    ) -> str:
        if not baseline:
            return "recomputed"
        comparisons: list[bool] = []
        if baseline.get("luck_sequence"):
            comparisons.append(
                [str(item.get("pillar") or "") for item in sequence]
                == [str(item.get("pillar") or "") for item in baseline["luck_sequence"]]
            )
        if str(baseline.get("luck_pillar") or ""):
            comparisons.append(
                str(current.get("pillar") if current else "")
                == str(baseline["luck_pillar"])
            )
        if baseline.get("luck_year_range"):
            comparisons.append(
                ([current.get("start_year"), current.get("end_year")] if current else [])
                == list(baseline["luck_year_range"])
            )
        if not comparisons:
            return "recomputed"
        return "recomputed_unchanged" if all(comparisons) else "recomputed_changed"

    @staticmethod
    def _direction_from_sequence(
        *,
        pillars: list[str],
        gender: Gender,
        sequence: list[dict[str, Any]],
    ) -> str:
        direction, _ = structural_dayun_sequence(
            year_pillar=pillars[0],
            month_pillar=pillars[1],
            gender=gender,
            limit=max(1, min(2, len(sequence) or 1)),
        )
        return direction

    @staticmethod
    def _unresolved(
        *,
        pillars: list[str],
        gender: Gender,
        analysis_year: int,
        fingerprint: str,
        reason: str,
        resolution_level: str,
        birth_anchor: Any = None,
    ) -> dict[str, Any]:
        return {
            "schema_version": TEMPORAL_SERVICE_VERSION,
            "resolution_level": resolution_level,
            "status": "unresolved",
            "recomputation_status": "unresolved",
            "gender": gender.value,
            "direction": "unresolved",
            "analysis_year": analysis_year,
            "annual_pillar": annual_pillar(analysis_year),
            "luck_sequence": [],
            "current_luck_status": "unresolved",
            "luck_pillar": "",
            "luck_year_range": [],
            "luck_age_range": [None, None],
            "birth_anchor": birth_anchor,
            "missing_inputs": [reason],
            "calculation_refs": [f"calendar.sexagenary_year:{analysis_year}"],
            "derivation_fingerprint": fingerprint,
            "formal_state_modified": False,
        }
