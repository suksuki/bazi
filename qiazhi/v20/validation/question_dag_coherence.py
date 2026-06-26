from __future__ import annotations

from collections import Counter
from typing import Any

from v20.interaction.question_dag import QUESTION_DAG_STAGES, role_default_dag_path
from v20.validation.synthetic_schema import SyntheticBaziCase, minimal_synthetic_bazi_cases


ALLOWED_DAG_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("entry", "focus"),
        ("entry", "structure"),
        ("focus", "structure"),
        ("focus", "timing"),
        ("focus", "review"),
        ("focus", "advice"),
        ("structure", "review"),
        ("structure", "timing"),
        ("structure", "advice"),
        ("structure", "closure"),
        ("timing", "review"),
        ("timing", "structure"),
        ("timing", "advice"),
        ("timing", "closure"),
        ("review", "timing"),
        ("review", "advice"),
        ("review", "closure"),
        ("observe", "review"),
        ("observe", "closure"),
        ("advice", "closure"),
    }
)

ROLE_FORBIDDEN_STAGES: dict[str, frozenset[str]] = {
    "guest": frozenset({"review", "observe"}),
    "user": frozenset({"observe"}),
    "analyst": frozenset({"observe"}),
    "admin": frozenset(),
}


def build_question_dag_coherence_report(
    cases: tuple[SyntheticBaziCase, ...] | None = None,
) -> dict[str, Any]:
    rows = tuple(cases or minimal_synthetic_bazi_cases())
    transition_rows = _transition_rows(rows)
    failures = tuple(
        failure
        for case in rows
        for failure in _case_failures(case)
    )
    role_failures = tuple(
        failure
        for role in ("guest", "user", "analyst", "admin")
        for failure in _role_path_failures(role)
    )
    all_failures = failures + role_failures
    return {
        "version": "v20.question_dag_coherence_report.v1",
        "status": "pass" if not all_failures else "needs_review",
        "case_count": len(rows),
        "transition_count": len(transition_rows),
        "transition_rows": transition_rows,
        "transition_support": _transition_support(transition_rows),
        "role_path_checks": tuple(_role_path_check(role) for role in ("guest", "user", "analyst", "admin")),
        "failure_count": len(all_failures),
        "failures": all_failures,
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_DAG_COHERENCE_IS_VALIDATION_ONLY",
            "NO_RUNTIME_POINTER_MUTATION",
            "NO_CORE_FACT_MUTATION",
            "NO_RULE_TRUTH_MUTATION",
        ],
    }


def _case_failures(case: SyntheticBaziCase) -> tuple[str, ...]:
    failures: list[str] = []
    stages = tuple(case.expected.dag_stages)
    unknown = tuple(stage for stage in stages if stage not in QUESTION_DAG_STAGES)
    failures.extend(f"{case.case_id}:unknown_stage:{stage}" for stage in unknown)
    for left, right in zip(stages, stages[1:]):
        if (left, right) not in ALLOWED_DAG_TRANSITIONS:
            failures.append(f"{case.case_id}:invalid_transition:{left}->{right}")
    if stages and stages[-1] not in {"advice", "closure", "timing"}:
        failures.append(f"{case.case_id}:unclosed_terminal:{stages[-1]}")
    return tuple(failures)


def _role_path_failures(role_key: str) -> tuple[str, ...]:
    path = role_default_dag_path(role_key)
    forbidden = ROLE_FORBIDDEN_STAGES.get(role_key, frozenset())
    failures = [f"role:{role_key}:forbidden_stage:{stage}" for stage in path if stage in forbidden]
    for left, right in zip(path, path[1:]):
        if (left, right) not in ALLOWED_DAG_TRANSITIONS:
            failures.append(f"role:{role_key}:invalid_transition:{left}->{right}")
    return tuple(failures)


def _transition_rows(cases: tuple[SyntheticBaziCase, ...]) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        stages = tuple(stage for stage in case.expected.dag_stages if stage in QUESTION_DAG_STAGES)
        for left, right in zip(stages, stages[1:]):
            rows.append(
                {
                    "case_id": case.case_id,
                    "from_stage": left,
                    "to_stage": right,
                    "is_allowed": (left, right) in ALLOWED_DAG_TRANSITIONS,
                }
            )
    return tuple(rows)


def _transition_support(rows: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    counts: Counter[tuple[str, str]] = Counter(
        (str(row["from_stage"]), str(row["to_stage"]))
        for row in rows
    )
    return tuple(
        {
            "from_stage": left,
            "to_stage": right,
            "support_count": count,
        }
        for (left, right), count in sorted(counts.items())
    )


def _role_path_check(role_key: str) -> dict[str, Any]:
    failures = _role_path_failures(role_key)
    return {
        "role_key": role_key,
        "default_path": role_default_dag_path(role_key),
        "forbidden_stages": tuple(sorted(ROLE_FORBIDDEN_STAGES.get(role_key, frozenset()))),
        "ok": not failures,
        "failures": failures,
        "runtime_mutation": False,
    }
