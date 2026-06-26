from __future__ import annotations

from dataclasses import replace

from v20.validation.question_dag_coherence import build_question_dag_coherence_report
from v20.validation.synthetic_schema import ExpectedRuntimeOutput, minimal_synthetic_bazi_cases


def test_v20_question_dag_coherence_passes_minimal_synthetic_paths() -> None:
    report = build_question_dag_coherence_report()

    assert report["version"] == "v20.question_dag_coherence_report.v1"
    assert report["status"] == "pass"
    assert report["case_count"] >= 14
    assert report["transition_count"] > 0
    assert report["failure_count"] == 0
    assert all(row["ok"] for row in report["role_path_checks"])
    assert "NO_RUNTIME_POINTER_MUTATION" in report["guardrails"]


def test_v20_question_dag_coherence_reports_invalid_transitions() -> None:
    base = minimal_synthetic_bazi_cases()[0]
    case = replace(
        base,
        expected=ExpectedRuntimeOutput(
            feature_domains=base.expected.feature_domains,
            rule_domains=base.expected.rule_domains,
            portrait_labels=base.expected.portrait_labels,
            question_keys=base.expected.question_keys,
            dag_stages=("entry", "observe", "focus"),
        ),
    )

    report = build_question_dag_coherence_report((case,))

    assert report["status"] == "needs_review"
    assert report["failure_count"] >= 1
    assert any("invalid_transition:entry->observe" in failure for failure in report["failures"])
