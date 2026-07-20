from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any

from core.contracts import (
    BirthInputCanonical,
    CalendarType,
    Gender,
    PillarConstraint,
    PillarTargetDraft,
)
from core.engines.bazi.chart_constraints import solve_chart_constraints, validate_four_pillars
from core.engines.bazi.pillar_cycle import (
    BIRTH_YEAR_MAX,
    BIRTH_YEAR_MIN,
    BRANCHES,
    JIAZI,
    STEMS,
    birth_year_options_by_pillar as _birth_year_options_by_pillar,
    branches_by_stem as _branches_by_stem,
    cycle_year_options_by_pillar as _cycle_year_options_by_pillar,
    hour_pillar_options as _hour_pillar_options,
    month_pillar_options as _month_pillar_options,
    stems_by_branch as _stems_by_branch,
)
from core.engines.bazi.temporal_service import CanonicalTemporalService
from product.structural_variant_compiler import (
    compile_onecanvas_structural_variant,
    refresh_temporal_nodes,
)
from product.onecanvas_timing_adapter import project_canonical_timing


class OneCanvasStructuralError(ValueError):
    pass


_TEMPORAL_SERVICE = CanonicalTemporalService()


def selection_catalog_payload() -> dict[str, Any]:
    return {
        "schema_version": "deepbazi.onecanvas_selection_catalog.v5",
        "stems": list(STEMS),
        "branches": list(BRANCHES),
        "branches_by_stem": _branches_by_stem(),
        "stems_by_branch": _stems_by_branch(),
        "year": list(JIAZI),
        "month_by_year": {
            pillar: _month_pillar_options(year_pillar=pillar)
            for pillar in JIAZI
        },
        "day": list(JIAZI),
        "hour_by_day": {
            pillar: _hour_pillar_options(day_pillar=pillar)
            for pillar in JIAZI
        },
        "cycle_year_anchor_by_year_pillar": _cycle_year_options_by_pillar(),
        "actual_birth_year_candidates_by_year_pillar": _birth_year_options_by_pillar(),
        "birth_year_by_year_pillar": _birth_year_options_by_pillar(),
        "birth_year_range": [BIRTH_YEAR_MIN, BIRTH_YEAR_MAX],
        "annual_observations": [
            {"year": year, "pillar": _TEMPORAL_SERVICE.derive_annual_pillar(year)}
            for year in range(BIRTH_YEAR_MIN, BIRTH_YEAR_MAX + 1)
        ],
        "gender_options": [
            {"value": Gender.MALE.value, "label": "乾造"},
            {"value": Gender.FEMALE.value, "label": "坤造"},
        ],
        "authority": "server_side_pillar_target_solver",
        "boundaries": [
            "年柱与日柱以天干或地支临时锁定后组成合法六十甲子",
            "月柱只来自当前年干对应的十二个合法候选",
            "时柱只来自当前日干对应的十二个合法候选",
            "流年只选择公历年份，干支由时间引擎派生",
            "干支纪年锚点与实际公历出生年份候选分开披露",
            "结构组合不自动声明存在真实出生日期",
        ],
    }


def resolve_pillar_target(
    *,
    desired: dict[str, Any],
    baseline_pillars: list[str],
    cycle_year_anchor: int | None = None,
    target_draft_id: str = "",
    selected_variant_id: str = "",
) -> dict[str, Any]:
    if len(baseline_pillars) != 4:
        raise OneCanvasStructuralError("onecanvas_four_pillars_required")
    required = ("year", "month", "day", "hour")
    if any(slot not in desired for slot in required):
        raise OneCanvasStructuralError("onecanvas_target_incomplete")

    constraints = {
        slot: _target_constraint(desired.get(slot), slot=slot)
        for slot in required
    }
    requested_pillars = {
        slot: _requested_pillar(desired.get(slot))
        for slot in required
    }
    draft = PillarTargetDraft(
        target_draft_id=target_draft_id or "onecanvas-target",
        year=constraints["year"],
        month=constraints["month"],
        day=constraints["day"],
        hour=constraints["hour"],
        cycle_year_anchor=cycle_year_anchor,
    )

    core_resolution = solve_chart_constraints(
        draft=draft,
        baseline_pillars=baseline_pillars,
    )

    selected = core_resolution.selected_variant
    if selected_variant_id:
        selected = next(
            (item for item in core_resolution.candidates if item.variant_id == selected_variant_id),
            None,
        )
        if selected is None:
            raise OneCanvasStructuralError("onecanvas_selected_variant_not_in_resolution")
    pillars = list(selected.pillars) if selected is not None else []
    normalized_slots = [
        slot
        for slot, before, after in zip(required, requested_pillars.values(), pillars)
        if before and before != after
    ] if pillars else []
    changed_pillars = [
        {"slot": slot, "before": before, "after": after}
        for slot, before, after in zip(required, baseline_pillars, pillars)
        if before != after
    ] if pillars else []

    resolved_anchor = core_resolution.cycle_year_anchor
    invalidated = [
        {
            "field": "sexagenary_year_anchor" if item.field == "cycle_year_anchor" else item.field,
            "reason": item.code,
            "previous_value": cycle_year_anchor,
        }
        for item in core_resolution.invalidated_constraints
    ]

    legal_variants = [
        {
            "variant_ref": item.variant_id,
            "pillars": list(item.pillars),
            "cycle_year_anchor": item.cycle_year_anchor,
            "presentation_distance": item.presentation_distance,
            "source_mode": "hypothetical",
            "validity": "ganzhi_structural",
        }
        for item in core_resolution.candidates
    ]
    return {
        "schema_version": "deepbazi.chart_constraint_resolution.v1",
        "resolution_id": core_resolution.resolution_id,
        "target_draft_id": core_resolution.target_draft_id,
        "status": core_resolution.status,
        "candidate_count": core_resolution.candidate_count,
        "legal_variants": legal_variants,
        "candidates_truncated": core_resolution.candidates_truncated,
        "ranking_is_presentation_only": core_resolution.ranking_is_presentation_only,
        "selection_required": core_resolution.status == "multiple_solutions" and selected is None,
        "user_selected_variant_ref": selected_variant_id or None,
        "selected_pillars": pillars,
        "normalized_slots": normalized_slots,
        "changed_pillars": changed_pillars,
        "cycle_year_anchor": resolved_anchor,
        "invalidated_anchor_reasons": invalidated,
        "conflict_reasons": [
            {"field": item.field, "reason": item.code, "detail": item.detail}
            for item in core_resolution.conflicts
        ],
        "releasable_constraints": list(core_resolution.releasable_constraints),
        "target_draft": draft.model_dump(mode="json"),
        "core_resolution_id": core_resolution.resolution_id,
        "compiler_version": "v50.global_chart_constraint_solver.v1",
        "source_refs": [
            "calendar.sexagenary_cycle",
            "calendar.five_tigers",
            "calendar.five_rats",
        ],
    }


def compile_target_draft(
    *,
    desired: dict[str, Any],
    baseline_pillars: list[str],
    baseline_relations: list[dict[str, Any]],
    formal_path: dict[str, Any],
    baseline_timing: dict[str, Any],
    analysis_year: int,
    gender: str,
    cycle_year_anchor: int | None = None,
    target_draft_id: str = "",
    selected_variant_id: str = "",
) -> dict[str, Any]:
    resolution = resolve_pillar_target(
        desired=desired,
        baseline_pillars=baseline_pillars,
        cycle_year_anchor=cycle_year_anchor,
        target_draft_id=target_draft_id,
        selected_variant_id=selected_variant_id,
    )
    if not resolution["selected_pillars"]:
        return {"resolution": resolution, "variant": None}
    variant = compile_structural_variant(
        selected_pillars=resolution["selected_pillars"],
        baseline_pillars=baseline_pillars,
        baseline_relations=baseline_relations,
        formal_path=formal_path,
        baseline_timing=baseline_timing,
        analysis_year=analysis_year,
        gender=gender,
        birth_year_hint=resolution["cycle_year_anchor"],
    )
    variant["selection_context"].update({
        "target_draft_id": resolution["target_draft_id"],
        "constraint_resolution_id": resolution["resolution_id"],
        "cycle_year_anchor": resolution["cycle_year_anchor"],
        "actual_birth_year_candidate": (
            variant.get("timing_recalculation", {})
            .get("calendar_resolution", {})
            .get("resolved_birth_year")
        ),
    })
    return {"resolution": resolution, "variant": variant}


def _target_constraint(value: Any, *, slot: str) -> PillarConstraint:
    """Normalize legacy complete targets and explicit partial target drafts."""
    if isinstance(value, PillarConstraint):
        return value
    if isinstance(value, dict):
        try:
            return PillarConstraint.model_validate(value)
        except ValueError as exc:
            raise OneCanvasStructuralError(f"onecanvas_{slot}_constraint_invalid") from exc
    if not isinstance(value, str) or len(value) != 2:
        raise OneCanvasStructuralError(f"onecanvas_{slot}_constraint_invalid")
    if slot in {"month", "hour"}:
        return PillarConstraint(branch=value[1])
    return PillarConstraint(pillar=value)


def _requested_pillar(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, PillarConstraint):
        return value.pillar
    if isinstance(value, dict):
        return str(value.get("pillar") or "")
    return ""


def compile_structural_variant(
    *,
    selected_pillars: list[str],
    baseline_pillars: list[str],
    baseline_relations: list[dict[str, Any]],
    formal_path: dict[str, Any],
    baseline_timing: dict[str, Any],
    analysis_year: int,
    gender: str,
    birth_year_hint: int | None = None,
) -> dict[str, Any]:
    _validate_pillars(selected_pillars=selected_pillars, baseline_pillars=baseline_pillars)
    try:
        resolved_gender = Gender(gender)
    except ValueError as exc:
        raise OneCanvasStructuralError("onecanvas_gender_invalid") from exc
    digest = hashlib.sha256("|".join(selected_pillars).encode("utf-8")).hexdigest()[:12]
    birth = BirthInputCanonical(
        birth_input_id=f"onecanvas-structural:{digest}",
        gender=resolved_gender,
        calendar_type=CalendarType.SOLAR,
        birth_date="2000-01-01",
        birth_time="12:00",
        timezone="UTC",
        year_pillar=selected_pillars[0],
        month_pillar=selected_pillars[1],
        day_pillar=selected_pillars[2],
        hour_pillar=selected_pillars[3],
        input_quality="hypothetical_pillar_structure",
        warnings=["not_resolved_to_real_birth_datetime"],
    )
    structural_timing = _TEMPORAL_SERVICE.resolve_structural_dayun(
        pillars=selected_pillars,
        gender=resolved_gender,
        analysis_year=analysis_year,
        timezone="Asia/Shanghai",
        baseline=baseline_timing,
    )
    timing_projection = project_canonical_timing(
        canonical=structural_timing,
        day_stem=selected_pillars[2][0],
        baseline_timing=baseline_timing,
    )
    variant = compile_onecanvas_structural_variant(
        axis="composite",
        index=int(digest[:6], 16),
        birth=birth,
        baseline_pillars=baseline_pillars,
        baseline_relations=baseline_relations,
        formal_path=formal_path,
        timing_recalculation=timing_projection,
    )
    variant["variant_id"] = f"composite-variant-{digest}"
    variant["edit_axis"] = "composite"
    variant["selected_pillar"] = ""
    variant["display_label"] = " · ".join(selected_pillars)
    variant["selection_context"] = {
        "disclosure_mode": "structural_pillar_combination",
        "selected_pillars": selected_pillars,
        "gender": resolved_gender.value,
        "chart_type": (
            "乾造" if resolved_gender == Gender.MALE
            else "坤造" if resolved_gender == Gender.FEMALE
            else "命造未定"
        ),
        "birth_year_hint": birth_year_hint,
        "maps_to_real_birth_datetime": False,
        "raw_birth_datetime_in_fixture": False,
    }
    if birth_year_hint is not None and resolved_gender != Gender.UNKNOWN:
        canonical_timing = _TEMPORAL_SERVICE.resolve_from_birth_year(
            pillars=selected_pillars,
            birth_year_anchor=birth_year_hint,
            gender=resolved_gender,
            analysis_year=analysis_year,
            timezone="Asia/Shanghai",
            baseline=baseline_timing,
        )
        timing = project_canonical_timing(
            canonical=canonical_timing,
            day_stem=selected_pillars[2][0],
            baseline_timing=baseline_timing,
        )
        calendar_resolution = dict(canonical_timing.get("calendar_resolution") or {})
        if canonical_timing.get("resolution_level") == "active_dayun_resolved":
            refresh_temporal_nodes(variant=variant, timing=timing)
            variant["selection_context"]["maps_to_real_birth_datetime"] = True
            variant["time_range"] = f"{birth_year_hint} 年锚定；当前大运由完整四柱反查定位"
        else:
            unresolved = deepcopy(variant["timing_recalculation"])
            unresolved["birth_year_hint"] = birth_year_hint
            unresolved["calendar_resolution"] = calendar_resolution
            unresolved["current_luck_status"] = "unresolved"
            unresolved["luck_pillar"] = ""
            unresolved["luck_year_range"] = []
            unresolved["luck_age_range"] = [None, None]
            unresolved["exact_timing_status"] = "birth_year_no_consistent_match"
            unresolved["missing_inputs"] = ["matching_birth_datetime_for_selected_four_pillars"]
            unresolved["failure_reason"] = "所选出生年份与当前四柱未反查到一致历法时刻，当前大运不作猜测"
            variant["timing_recalculation"] = unresolved
            variant["time_range"] = f"{birth_year_hint} 年锚定；四柱尚未形成一致历法候选"
    elif birth_year_hint is not None:
        variant["time_range"] = f"{birth_year_hint} 年纪年锚点；命造未定，当前大运不作推断"
    else:
        variant["time_range"] = "结构实验；未选择出生年份，当前大运待定位"
    return variant


def _validate_pillars(*, selected_pillars: list[str], baseline_pillars: list[str]) -> None:
    if len(selected_pillars) != 4 or len(baseline_pillars) != 4:
        raise OneCanvasStructuralError("onecanvas_four_pillars_required")
    issues = validate_four_pillars(selected_pillars)
    if not issues:
        return
    code = issues[0].code
    legacy_codes = {
        "invalid_year_jiazi": "onecanvas_year_pillar_invalid",
        "invalid_day_jiazi": "onecanvas_day_pillar_invalid",
        "month_pillar_not_legal_for_year": "onecanvas_month_pillar_not_legal_for_year",
        "hour_pillar_not_legal_for_day": "onecanvas_hour_pillar_not_legal_for_day",
    }
    raise OneCanvasStructuralError(legacy_codes.get(code, f"onecanvas_{code}"))
