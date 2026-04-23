from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from v17_rebirth.testing.practitioner_benchmarks import (
    PRACTITIONER_BENCHMARK_CASES,
    PractitionerBenchmarkCase,
    practitioner_dynamic_families,
    practitioner_relation_families,
    run_practitioner_case,
)
from v17_rebirth.testing.synthetic_lab import (
    SYNTHETIC_AUTHORITY_CASES,
    SYNTHETIC_CASES,
    SYNTHETIC_CORE_CASES,
    SYNTHETIC_PATTERN_CASES,
    SYNTHETIC_RISK_CASES,
)


TUNING_BRIDGE_VERSION = "v17.synthetic_tuning_bridge.v1"


@dataclass(frozen=True)
class BenchmarkIssue:
    case_id: str
    issue_type: str
    message: str
    parameter_family: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "issue_type": self.issue_type,
            "message": self.message,
            "parameter_family": self.parameter_family,
        }


@dataclass(frozen=True)
class BenchmarkAudit:
    case_id: str
    passed: bool
    issues: tuple[BenchmarkIssue, ...]
    suggested_synthetic_cases: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "passed": bool(self.passed),
            "issues": [issue.to_dict() for issue in self.issues],
            "suggested_synthetic_cases": list(self.suggested_synthetic_cases),
        }


def audit_practitioner_case(case: PractitionerBenchmarkCase) -> BenchmarkAudit:
    run = run_practitioner_case(case)
    issues: list[BenchmarkIssue] = []
    relation_families = practitioner_relation_families(run)
    dynamic_families = practitioner_dynamic_families(run)

    for family in case.expected_relation_families:
        if family not in relation_families:
            issues.append(
                BenchmarkIssue(
                    case_id=case.case_id,
                    issue_type="missing_relation_family",
                    message=f"Expected relation family {family} was not emitted.",
                    parameter_family=f"relation_formation.{family}",
                )
            )
    for family in case.expected_dynamic_families:
        if family not in dynamic_families:
            issues.append(
                BenchmarkIssue(
                    case_id=case.case_id,
                    issue_type="missing_dynamic_family",
                    message=f"Expected dynamic family {family} was not emitted.",
                    parameter_family=f"relation_dynamics.{family}",
                )
            )
    for family in case.forbidden_relation_families:
        if family in relation_families or family in dynamic_families:
            issues.append(
                BenchmarkIssue(
                    case_id=case.case_id,
                    issue_type="forbidden_family_present",
                    message=f"Forbidden family {family} was emitted.",
                    parameter_family=f"relation_gate.{family}",
                )
            )
    for god in case.expected_top_contains:
        if god not in run.top:
            issues.append(
                BenchmarkIssue(
                    case_id=case.case_id,
                    issue_type="missing_top_god",
                    message=f"Expected top god {god} was not in top axis.",
                    parameter_family="ten_gods.calibration",
                )
            )
    if case.expected_leader and (not run.top or run.top[0] != case.expected_leader):
        actual = run.top[0] if run.top else "none"
        issues.append(
            BenchmarkIssue(
                case_id=case.case_id,
                issue_type="leader_mismatch",
                message=f"Expected leader {case.expected_leader}, got {actual}.",
                parameter_family="authority.leader_axis",
            )
        )

    suggested = _suggest_cases_for_issues(issues)
    return BenchmarkAudit(
        case_id=case.case_id,
        passed=not issues,
        issues=tuple(issues),
        suggested_synthetic_cases=tuple(suggested),
    )


def build_tuning_bridge_report(
    cases: Iterable[PractitionerBenchmarkCase] = PRACTITIONER_BENCHMARK_CASES,
) -> dict[str, Any]:
    audits = [audit_practitioner_case(case) for case in cases]
    family_counts: Counter[str] = Counter()
    case_suggestions: dict[str, list[str]] = {}
    for audit in audits:
        for issue in audit.issues:
            family_counts[issue.parameter_family] += 1
        if audit.suggested_synthetic_cases:
            case_suggestions[audit.case_id] = list(audit.suggested_synthetic_cases)

    return {
        "protocol": TUNING_BRIDGE_VERSION,
        "benchmark_count": len(audits),
        "passed_count": sum(1 for audit in audits if audit.passed),
        "failed_count": sum(1 for audit in audits if not audit.passed),
        "audits": [audit.to_dict() for audit in audits],
        "parameter_family_counts": dict(family_counts),
        "case_suggestions": case_suggestions,
        "synthetic_catalog_size": len(_catalog_index()),
        "learning_loop_state": (
            "ready_for_parameter_candidate_generation"
            if family_counts
            else "benchmarks_green_collect_more_feedback"
        ),
        "parameter_candidate_plan": build_parameter_candidate_plan(dict(family_counts)),
    }


def build_parameter_candidate_plan(parameter_family_counts: dict[str, int]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for family, count in sorted(
        parameter_family_counts.items(),
        key=lambda item: (-int(item[1] or 0), str(item[0])),
    ):
        suggestions = _suggest_cases_for_issues(
            [
                BenchmarkIssue(
                    case_id="aggregate",
                    issue_type="parameter_family_hotspot",
                    message=f"{family} has {count} benchmark issue(s).",
                    parameter_family=family,
                )
            ]
        )
        candidates.append(
            {
                "candidate_id": f"candidate::{family}",
                "parameter_family": family,
                "issue_count": int(count or 0),
                "recommended_action": _recommended_action_for_family(family),
                "safety_gate": "manual_review_required",
                "synthetic_cases": suggestions,
            }
        )
    return candidates


def _suggest_cases_for_issues(issues: list[BenchmarkIssue]) -> list[str]:
    if not issues:
        return []
    catalog = _catalog_index()
    scored: defaultdict[str, int] = defaultdict(int)
    for issue in issues:
        tokens = _family_tokens(issue.parameter_family)
        for row in catalog:
            haystack = " ".join(
                [
                    str(row.get("case_id") or ""),
                    str(row.get("layer") or ""),
                    " ".join(row.get("tags") or []),
                    str(row.get("description") or ""),
                ]
            ).lower()
            for token in tokens:
                if token and token in haystack:
                    scored[str(row["case_id"])] += 1
    return [
        case_id
        for case_id, _score in sorted(scored.items(), key=lambda item: (-item[1], item[0]))[:8]
    ]


def _catalog_index() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in [
        *SYNTHETIC_CASES,
        *SYNTHETIC_RISK_CASES,
        *SYNTHETIC_AUTHORITY_CASES,
        *SYNTHETIC_PATTERN_CASES,
        *SYNTHETIC_CORE_CASES,
    ]:
        rows.append(
            {
                "case_id": str(case.case_id),
                "layer": str(case.layer),
                "description": str(case.description),
                "tags": list(getattr(case, "tags", ()) or ()),
            }
        )
    return rows


def _family_tokens(parameter_family: str) -> tuple[str, ...]:
    raw = str(parameter_family or "").lower()
    aliases = {
        "relation_formation": ("relation",),
        "relation_dynamics": ("relation",),
        "relation_gate": ("relation",),
        "ten_gods": ("static", "authority", "core"),
        "authority": ("authority", "core"),
    }
    tokens = [part for part in raw.replace("_", ".").split(".") if part]
    out: list[str] = []
    for token in tokens:
        out.append(token)
        out.extend(aliases.get(token, ()))
    return tuple(dict.fromkeys(out))


def _recommended_action_for_family(parameter_family: str) -> str:
    family = str(parameter_family or "")
    if family.startswith("relation_formation."):
        return "review_relation_family_factor_and_visibility_gate"
    if family.startswith("relation_dynamics."):
        return "review_energy_stability_axis_and_runtime_damping"
    if family.startswith("relation_gate."):
        return "review_family_gate_conditions_before_tuning_weights"
    if family.startswith("ten_gods."):
        return "review_static_basis_root_projection_and_decomposition"
    if family.startswith("authority."):
        return "review_authority_layer_weights_and_hard_constraints"
    return "review_related_protocol_before_parameter_change"
