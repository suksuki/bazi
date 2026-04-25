from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from v17_rebirth.testing.learning_campaign import audit_practitioner_benchmarks
from v17_rebirth.testing.practitioner_benchmarks import PractitionerBenchmarkCase, run_practitioner_case
from v17_rebirth.testing.synthetic_batch_lab import build_synthetic_batch_report


SHADOW_RUN_REPORT_VERSION = "v17.practitioner.shadow_run_report.v1"


def build_practitioner_shadow_run_report(
    *,
    experiment: dict[str, Any],
    benchmark_export: dict[str, Any],
) -> dict[str, Any]:
    experiment_obj = experiment if isinstance(experiment, dict) else {}
    benchmark_export_obj = benchmark_export if isinstance(benchmark_export, dict) else {}
    synthetic = build_synthetic_batch_report()
    static_practitioner = audit_practitioner_benchmarks()
    accepted = _audit_accepted_benchmark_export(benchmark_export_obj)
    synthetic_failed = int(synthetic.get("failed_count") or 0)
    static_failed = int(static_practitioner.get("failed_count") or 0)
    accepted_failed = int(accepted.get("failed_count") or 0)
    synthetic_passed = synthetic_failed == 0
    practitioner_passed = static_failed == 0 and accepted_failed == 0
    regression_count = synthetic_failed + static_failed + accepted_failed
    improvement_count = _int_value(experiment_obj.get("measured_improvement_count"))
    verdict = "promote" if synthetic_passed and practitioner_passed and regression_count == 0 and improvement_count > 0 else "rework"
    report = {
        "ok": True,
        "protocol": SHADOW_RUN_REPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment": experiment_obj,
        "synthetic": {
            "protocol": synthetic.get("protocol"),
            "passed": synthetic_passed,
            "case_count": int(synthetic.get("case_count") or 0),
            "failed_count": synthetic_failed,
            "passed_count": int(synthetic.get("passed_count") or 0),
            "regression_count": synthetic_failed,
            "anomalies": synthetic.get("anomalies") if isinstance(synthetic.get("anomalies"), list) else [],
        },
        "practitioner_benchmarks": {
            "protocol": "v17.practitioner.shadow_run_benchmark_audit.v1",
            "passed": practitioner_passed,
            "static_case_count": int(static_practitioner.get("case_count") or 0),
            "static_failed_count": static_failed,
            "accepted_case_count": int(accepted.get("case_count") or 0),
            "accepted_failed_count": accepted_failed,
            "regression_count": static_failed + accepted_failed,
            "static_report": static_practitioner,
            "accepted_report": accepted,
        },
        "benchmark_export": benchmark_export_obj,
        "scorecard": {
            "synthetic_passed": synthetic_passed,
            "practitioner_passed": practitioner_passed,
            "improvement_count": improvement_count,
            "regression_count": regression_count,
            "verdict": verdict,
            "summary": _summary(
                synthetic_passed=synthetic_passed,
                practitioner_passed=practitioner_passed,
                improvement_count=improvement_count,
                regression_count=regression_count,
                accepted_case_count=int(accepted.get("case_count") or 0),
            ),
        },
        "guardrails": [
            "shadow run report is generated from current runtime checks",
            "candidate patch is not applied automatically",
            "promote requires explicit measured improvements and zero regressions",
            "scorecard import still records applied=false",
        ],
    }
    return report


def _audit_accepted_benchmark_export(benchmark_export: dict[str, Any]) -> dict[str, Any]:
    seeds = benchmark_export.get("benchmark_cases")
    rows = seeds if isinstance(seeds, list) else []
    signals: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    case_count = 0
    passed_count = 0
    for seed in rows:
        if not isinstance(seed, dict):
            continue
        case = _case_from_seed(seed)
        case_count += 1
        before = len(findings)
        try:
            run = run_practitioner_case(case)
        except Exception as exc:
            findings.append(
                {
                    "source": "accepted_practitioner_benchmark",
                    "case_id": case.case_id,
                    "severity": "P0",
                    "message": f"runtime crash: {exc}",
                    "parameter_family": "runtime.stability",
                }
            )
            continue
        top = list(run.top[:6])
        signals.append(
            {
                "case_id": case.case_id,
                "description": case.description,
                "audit_focus": list(case.audit_focus),
                "expected_top_contains": list(case.expected_top_contains),
                "top": top,
                "reviewer_note": case.reviewer_note,
            }
        )
        if run.total <= 0:
            findings.append(
                {
                    "source": "accepted_practitioner_benchmark",
                    "case_id": case.case_id,
                    "severity": "P1",
                    "message": "non-positive total energy",
                    "parameter_family": "ten_gods.calibration",
                }
            )
        for god in case.expected_top_contains:
            if god not in run.top:
                findings.append(
                    {
                        "source": "accepted_practitioner_benchmark",
                        "case_id": case.case_id,
                        "severity": "P1",
                        "message": f"expected top axis missing: {god}",
                        "parameter_family": "authority.leader_axis",
                    }
                )
        if len(findings) == before:
            passed_count += 1
    return {
        "protocol": "v17.practitioner.accepted_benchmark_shadow.v1",
        "state": "green" if not findings else "needs_review",
        "case_count": case_count,
        "passed_count": passed_count,
        "failed_count": case_count - passed_count,
        "signals": signals,
        "findings": findings,
    }


def _case_from_seed(seed: dict[str, Any]) -> PractitionerBenchmarkCase:
    return PractitionerBenchmarkCase(
        case_id=str(seed.get("case_id") or "").strip() or "accepted.runtime.case",
        description=str(seed.get("description") or "").strip(),
        four_pillars=dict(seed.get("four_pillars") if isinstance(seed.get("four_pillars"), dict) else {}),
        luck_pillar=str(seed.get("luck_pillar") or "-").strip() or "-",
        flow_pillar=str(seed.get("flow_pillar") or "-").strip() or "-",
        gender=str(seed.get("gender") or "male").strip() or "male",
        audit_focus=tuple(_list_text(seed.get("audit_focus"))),
        expected_top_contains=tuple(_list_text(seed.get("expected_top_contains"))),
        reviewer_note=str(seed.get("reviewer_note") or "").strip(),
    )


def _summary(
    *,
    synthetic_passed: bool,
    practitioner_passed: bool,
    improvement_count: int,
    regression_count: int,
    accepted_case_count: int,
) -> str:
    if synthetic_passed and practitioner_passed and regression_count == 0 and improvement_count > 0:
        return f"shadow run 通过，记录 {improvement_count} 项改善，覆盖 {accepted_case_count} 条 accepted practitioner benchmark。"
    if synthetic_passed and practitioner_passed and regression_count == 0:
        return f"shadow run 基线通过，覆盖 {accepted_case_count} 条 accepted practitioner benchmark；尚未记录候选 patch 改善，建议继续返工或补充 A/B 结果。"
    return f"shadow run 发现 {regression_count} 项退化或失败，暂不建议发布。"


def _list_text(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item or "").strip() for item in value if str(item or "").strip()]


def _int_value(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except Exception:
        return 0
