from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

from core.contracts.chart import (
    ChartResolution,
    ChartVariant,
    ConstraintIssue,
    PillarConstraint,
    PillarTargetDraft,
)
from core.engines.bazi.pillar_cycle import (
    BRANCHES,
    JIAZI,
    STEMS,
    birth_year_options_by_pillar,
    hour_pillar_options,
    month_pillar_options,
)


MAX_RETURNED_CANDIDATES = 512


def solve_chart_constraints(
    *,
    draft: PillarTargetDraft,
    baseline_pillars: list[str] | tuple[str, str, str, str] | None = None,
) -> ChartResolution:
    """Return every legal chart solution represented by a target draft.

    Candidate ranking is presentation-only. A multiple result is never silently
    promoted to a selected chart.
    """
    constraints = {
        "year": draft.year,
        "month": draft.month,
        "day": draft.day,
        "hour": draft.hour,
    }
    conflicts = _constraint_issues(constraints)
    if conflicts:
        return _resolution(
            draft=draft,
            status="no_solution",
            candidate_count=0,
            candidates=[],
            conflicts=conflicts,
            invalidated_constraints=[],
            cycle_year_anchor=draft.cycle_year_anchor,
        )

    year_candidates = _filter(JIAZI, draft.year)
    day_candidates = _filter(JIAZI, draft.day)
    invalidated: list[ConstraintIssue] = []
    cycle_year_anchor = draft.cycle_year_anchor
    if cycle_year_anchor is not None:
        compatible_years = [
            pillar
            for pillar in year_candidates
            if cycle_year_anchor in birth_year_options_by_pillar().get(pillar, [])
        ]
        if compatible_years:
            year_candidates = compatible_years
        else:
            invalidated.append(ConstraintIssue(
                field="cycle_year_anchor",
                code="incompatible_with_year_constraint",
                detail=str(cycle_year_anchor),
            ))
            cycle_year_anchor = None

    candidate_rows: list[tuple[str, str, str, str]] = []
    for year_pillar in year_candidates:
        for month_pillar in _filter(month_pillar_options(year_pillar=year_pillar), draft.month):
            for day_pillar in day_candidates:
                for hour_pillar in _filter(hour_pillar_options(day_pillar=day_pillar), draft.hour):
                    candidate_rows.append((year_pillar, month_pillar, day_pillar, hour_pillar))

    if not candidate_rows:
        conflicts = [_unsatisfied_issue(draft)]
        return _resolution(
            draft=draft,
            status="no_solution",
            candidate_count=0,
            candidates=[],
            conflicts=conflicts,
            invalidated_constraints=invalidated,
            cycle_year_anchor=cycle_year_anchor,
        )

    baseline = tuple(baseline_pillars or ())
    candidate_rows.sort(key=lambda row: (_presentation_distance(row, baseline), _canonical_key(row)))
    candidate_count = len(candidate_rows)
    candidates = [
        _variant(row, cycle_year_anchor=cycle_year_anchor, baseline=baseline)
        for row in candidate_rows[:MAX_RETURNED_CANDIDATES]
    ]
    status = "single_solution" if candidate_count == 1 else "multiple_solutions"
    return _resolution(
        draft=draft,
        status=status,
        candidate_count=candidate_count,
        candidates=candidates,
        conflicts=[],
        invalidated_constraints=invalidated,
        cycle_year_anchor=cycle_year_anchor,
    )


def validate_four_pillars(
    pillars: Iterable[str],
) -> list[ConstraintIssue]:
    values = list(pillars)
    if len(values) != 4:
        return [ConstraintIssue(field="pillars", code="four_pillars_required")]
    slots = ("year", "month", "day", "hour")
    issues = _constraint_issues({
        slot: PillarConstraint(pillar=value)
        for slot, value in zip(slots, values, strict=True)
    })
    if issues:
        return issues
    year, month, day, hour = values
    if month not in month_pillar_options(year_pillar=year):
        issues.append(ConstraintIssue(
            field="month_pillar",
            code="month_pillar_not_legal_for_year",
            detail=f"{year}:{month}",
        ))
    if hour not in hour_pillar_options(day_pillar=day):
        issues.append(ConstraintIssue(
            field="hour_pillar",
            code="hour_pillar_not_legal_for_day",
            detail=f"{day}:{hour}",
        ))
    return issues


def _constraint_issues(
    constraints: dict[str, PillarConstraint],
) -> list[ConstraintIssue]:
    issues: list[ConstraintIssue] = []
    for slot, constraint in constraints.items():
        pillar = str(constraint.pillar or "").strip()
        stem = str(constraint.stem or "").strip()
        branch = str(constraint.branch or "").strip()
        field = f"{slot}_pillar"
        if pillar:
            if len(pillar) < 1 or pillar[0] not in STEMS:
                issues.append(ConstraintIssue(field=field, code=f"invalid_{slot}_stem", detail=pillar))
                continue
            if len(pillar) < 2 or pillar[1] not in BRANCHES:
                issues.append(ConstraintIssue(field=field, code=f"invalid_{slot}_branch", detail=pillar))
                continue
            if len(pillar) != 2 or pillar not in JIAZI:
                issues.append(ConstraintIssue(field=field, code=f"invalid_{slot}_jiazi", detail=pillar))
                continue
        if stem and stem not in STEMS:
            issues.append(ConstraintIssue(field=f"{slot}.stem", code=f"invalid_{slot}_stem", detail=stem))
        if branch and branch not in BRANCHES:
            issues.append(ConstraintIssue(field=f"{slot}.branch", code=f"invalid_{slot}_branch", detail=branch))
        if pillar and stem and pillar[0] != stem:
            issues.append(ConstraintIssue(field=field, code=f"conflicting_{slot}_stem", detail=f"{pillar}:{stem}"))
        if pillar and branch and pillar[1] != branch:
            issues.append(ConstraintIssue(field=field, code=f"conflicting_{slot}_branch", detail=f"{pillar}:{branch}"))
    return issues


def _filter(values: Iterable[str], constraint: PillarConstraint) -> list[str]:
    pillar = str(constraint.pillar or "").strip()
    stem = str(constraint.stem or "").strip()
    branch = str(constraint.branch or "").strip()
    return [
        value
        for value in values
        if (not pillar or value == pillar)
        and (not stem or value[0] == stem)
        and (not branch or value[1] == branch)
    ]


def _unsatisfied_issue(draft: PillarTargetDraft) -> ConstraintIssue:
    if draft.year.pillar and draft.month.pillar:
        return ConstraintIssue(
            field="month_pillar",
            code="month_pillar_not_legal_for_year",
            detail=f"{draft.year.pillar}:{draft.month.pillar}",
        )
    if draft.day.pillar and draft.hour.pillar:
        return ConstraintIssue(
            field="hour_pillar",
            code="hour_pillar_not_legal_for_day",
            detail=f"{draft.day.pillar}:{draft.hour.pillar}",
        )
    return ConstraintIssue(field="target_draft", code="constraints_have_no_legal_chart_solution")


def _variant(
    row: tuple[str, str, str, str],
    *,
    cycle_year_anchor: int | None,
    baseline: tuple[str, ...],
) -> ChartVariant:
    payload = {
        "pillars": list(row),
        "cycle_year_anchor": cycle_year_anchor,
    }
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return ChartVariant(
        variant_id=f"chart-variant-{digest}",
        pillars=list(row),
        cycle_year_anchor=cycle_year_anchor,
        presentation_distance=_presentation_distance(row, baseline),
    )


def _presentation_distance(row: tuple[str, str, str, str], baseline: tuple[str, ...]) -> int:
    if len(baseline) != 4:
        return 0
    return sum(value != baseline[index] for index, value in enumerate(row))


def _canonical_key(row: tuple[str, str, str, str]) -> tuple[int, int, int, int]:
    return tuple(JIAZI.index(value) for value in row)


def _resolution(
    *,
    draft: PillarTargetDraft,
    status: str,
    candidate_count: int,
    candidates: list[ChartVariant],
    conflicts: list[ConstraintIssue],
    invalidated_constraints: list[ConstraintIssue],
    cycle_year_anchor: int | None,
) -> ChartResolution:
    digest_source = {
        "draft": draft.model_dump(mode="json"),
        "status": status,
        "candidate_count": candidate_count,
        "candidate_ids": [candidate.variant_id for candidate in candidates],
        "cycle_year_anchor": cycle_year_anchor,
    }
    digest = hashlib.sha256(
        json.dumps(digest_source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return ChartResolution(
        resolution_id=f"chart-resolution-{digest}",
        target_draft_id=draft.target_draft_id,
        status=status,
        candidate_count=candidate_count,
        candidates=candidates,
        selected_variant=candidates[0] if status == "single_solution" else None,
        conflicts=conflicts,
        releasable_constraints=_releasable_constraints(draft, conflicts),
        invalidated_constraints=invalidated_constraints,
        cycle_year_anchor=cycle_year_anchor,
        candidates_truncated=candidate_count > len(candidates),
    )


def _releasable_constraints(
    draft: PillarTargetDraft,
    conflicts: list[ConstraintIssue],
) -> list[str]:
    """Name the smallest user constraints that can be relaxed after a conflict."""
    if not conflicts:
        return []
    releasable: list[str] = []
    for issue in conflicts:
        if issue.code == "month_pillar_not_legal_for_year":
            releasable.extend(["month.pillar", "year.pillar"])
        elif issue.code == "hour_pillar_not_legal_for_day":
            releasable.extend(["hour.pillar", "day.pillar"])
        elif issue.field == "target_draft":
            for slot in ("year", "month", "day", "hour"):
                constraint = getattr(draft, slot)
                if constraint.pillar:
                    releasable.append(f"{slot}.pillar")
                if constraint.stem:
                    releasable.append(f"{slot}.stem")
                if constraint.branch:
                    releasable.append(f"{slot}.branch")
        else:
            normalized = issue.field.replace("_pillar", ".pillar")
            releasable.append(normalized)
    return list(dict.fromkeys(releasable))
