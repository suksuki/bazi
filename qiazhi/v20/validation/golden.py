from __future__ import annotations

import os
from typing import Any

from v20.validation.case_matrix import build_regression_golden_cases, matrix_golden_manifest
from v20.validation.synthetic_schema import SyntheticCase

_BASE_GOLDEN_CASES: tuple[SyntheticCase, ...] = (
    SyntheticCase(
        case_id="v20.golden.branch_relation_wealth_material",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        expected_feature_domains=("strength", "branch", "wealth", "useful_god"),
        expected_question_keys=("q_strength_assessment", "q_branch_relation_detail"),
        expected_rule_candidate_domains=("strength",),
    ),
)


def _read_case_count_from_env(
    env_name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    try:
        value = int(os.getenv(env_name, str(default)))
    except ValueError:
        return default
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def build_golden_cases(*, matrix_case_count: int | None = None) -> tuple[SyntheticCase, ...]:
    target = matrix_case_count if matrix_case_count is not None else _read_case_count_from_env(
        "V20_GOLDEN_CASE_TARGET",
        default=40,
        minimum=0,
        maximum=2000,
    )
    matrix_cases = build_regression_golden_cases(
        case_count=target,
        with_question_keys=False,
        with_feature_domains=False,
    )
    rows: dict[str, SyntheticCase] = {}
    for case in _BASE_GOLDEN_CASES:
        rows[case.case_id] = case
    rows.update({case.case_id: case for case in matrix_cases})
    return tuple(rows.values())


GOLDEN_CASES = build_golden_cases()


def golden_matrix_manifest() -> dict[str, Any]:
    return matrix_golden_manifest(case_count=len(GOLDEN_CASES) - len(_BASE_GOLDEN_CASES))
