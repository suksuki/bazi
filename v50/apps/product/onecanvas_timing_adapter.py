from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from core.contracts import Gender
from product.structural_variant_compiler import pillar_nodes


RefTransform = Callable[[str], str]
ObservationRefFactory = Callable[[dict[str, Any]], str]


def project_canonical_timing(
    *,
    canonical: dict[str, Any],
    day_stem: str,
    baseline_timing: dict[str, Any] | None = None,
    source_mode: str | None = None,
    source_ref_transform: RefTransform | None = None,
    observation_ref_factory: ObservationRefFactory | None = None,
) -> dict[str, Any]:
    """Adapt canonical temporal facts to the stable OneCanvas display contract.

    Callers: onecanvas_structural and the retained R1 fixture builder. Retire
    after OneCanvas consumes the canonical TemporalSnapshot projection directly,
    at final Workspace integration.
    """
    baseline = baseline_timing or {}
    transform = source_ref_transform or (lambda value: value)
    calculation_refs = [
        transform(str(value))
        for value in canonical.get("calculation_refs") or []
    ]
    resolved_source_mode = source_mode or (
        "hypothetical" if canonical.get("birth_anchor") else "derived"
    )
    sequence = deepcopy(canonical.get("luck_sequence") or [])
    for item in sequence:
        if observation_ref_factory is not None:
            item["observation_ref"] = observation_ref_factory(item)
        item["nodes"] = pillar_nodes(
            pillar=str(item.get("pillar") or ""),
            slot="luck",
            day_stem=day_stem,
            source_mode=resolved_source_mode,
            source_refs=calculation_refs,
        )

    gender = _gender(canonical.get("gender"))
    resolution_level = str(canonical.get("resolution_level") or "")
    recomputation_status = str(
        canonical.get("recomputation_status")
        or canonical.get("status")
        or ""
    )
    exact = resolution_level == "active_dayun_resolved"
    if gender == Gender.UNKNOWN:
        status = "recalculation_unavailable"
    elif recomputation_status == "recomputed_unchanged":
        status = "recalculated_unchanged"
    else:
        status = "recalculated_changed"

    current = _current_luck(sequence, canonical)
    birth_year_anchored = bool(
        isinstance(canonical.get("birth_anchor"), dict)
        and canonical["birth_anchor"].get("birth_year")
    )
    result = {
        **deepcopy(canonical),
        "status": status,
        "gender": gender.value,
        "chart_type": chart_type_label(gender),
        "current_luck_status": str(canonical.get("current_luck_status") or "unresolved"),
        "luck_sequence": sequence,
        "luck_age_range": list(
            canonical.get("luck_age_range")
            or ([current.get("start_age"), current.get("end_age")] if current else [None, None])
        ),
        "calculation_refs": calculation_refs,
        "confidence": 0.94 if exact else 0.5 if sequence else 0.0,
        "formal_reference": {
            "luck_pillar": str(baseline.get("luck_pillar") or ""),
            "luck_year_range": list(baseline.get("luck_year_range") or []),
        },
        "calculation_mode": (
            str(canonical.get("calculation_mode") or "calendar_exact")
            if exact
            else "structural_sequence_only" if sequence
            else "gender_required"
        ),
        "exact_timing_status": (
            "resolved_from_birth_year_and_four_pillars"
            if exact and birth_year_anchored
            else "resolved" if exact
            else "unavailable"
        ),
        "limitations": _limitations(
            exact=exact,
            birth_year_anchored=birth_year_anchored,
            sequence_available=bool(sequence),
        ),
    }
    if gender == Gender.UNKNOWN:
        result.update({
            "current_luck_status": "unresolved",
            "luck_pillar": "",
            "luck_year_range": [],
            "luck_age_range": [None, None],
            "luck_sequence": [],
            "formal_reference": {"luck_pillar": "", "luck_year_range": []},
            "failure_reason": "需先确认乾造或坤造，才能确定大运顺逆与序列",
        })
    return result


def chart_type_label(gender: Gender | str) -> str:
    normalized = _gender(gender)
    if normalized == Gender.MALE:
        return "乾造"
    if normalized == Gender.FEMALE:
        return "坤造"
    return "命造未定"


def _gender(value: Any) -> Gender:
    try:
        return value if isinstance(value, Gender) else Gender(str(value or Gender.UNKNOWN.value))
    except ValueError:
        return Gender.UNKNOWN


def _current_luck(
    sequence: list[dict[str, Any]],
    canonical: dict[str, Any],
) -> dict[str, Any] | None:
    pillar = str(canonical.get("luck_pillar") or "")
    year_range = list(canonical.get("luck_year_range") or [])
    return next((
        item
        for item in sequence
        if str(item.get("pillar") or "") == pillar
        and [item.get("start_year"), item.get("end_year")] == year_range
    ), None)


def _limitations(
    *,
    exact: bool,
    birth_year_anchored: bool,
    sequence_available: bool,
) -> list[str]:
    if exact and birth_year_anchored:
        return [
            "当前大运由出生年份与完整四柱反查候选定位",
            "该定位属于结构实验，不修改正式出生档案",
            "未纳入出生地点与真太阳时校正",
        ]
    if exact:
        return ["当前大运由已验证出生历法事实计算"]
    if sequence_available:
        return [
            "结构实验只派生大运顺逆与干支序列",
            "未解析到真实出生日期前，不继承原盘起运岁数、年份窗口或当前大运",
        ]
    return ["性别缺失时不得推断、继承或猜测大运顺逆"]
