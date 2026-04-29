from __future__ import annotations

from copy import deepcopy

from v19.synthetic_validation import DEFAULT_SYNTHETIC_CASES, SyntheticCase, run_synthetic_validation


def test_default_synthetic_cases_pass() -> None:
    result = run_synthetic_validation(DEFAULT_SYNTHETIC_CASES)

    assert result["status"] == "pass"
    assert result["summary"]["total"] >= 10
    assert result["summary"]["failed"] == 0
    assert "DOES_NOT_PROVE_REAL_WORLD_ACCURACY" in result["boundaries"]


def test_validation_runner_fail_case() -> None:
    base = DEFAULT_SYNTHETIC_CASES[0]
    failing_case = SyntheticCase(
        case_id="synthetic.expected_failure",
        chart=base.chart,
        expected_inference_signals={"day_master_state.tendency": "impossible_value"},
        expected_domain_adapter_outputs=base.expected_domain_adapter_outputs,
        forbidden_outputs=base.forbidden_outputs,
        tags=["expected_failure"],
    )

    result = run_synthetic_validation([failing_case])

    assert result["status"] == "fail"
    assert result["summary"]["failed"] == 1
    assert result["drift_report"]["drift_count"] >= 1


def test_forbidden_output_fail() -> None:
    base = DEFAULT_SYNTHETIC_CASES[0]
    forbidden_case = SyntheticCase(
        case_id="synthetic.forbidden_failure",
        chart=base.chart,
        expected_inference_signals={},
        expected_domain_adapter_outputs={},
        forbidden_outputs=["day_master_state"],
        tags=["forbidden_failure"],
    )

    result = run_synthetic_validation([forbidden_case])

    assert result["status"] == "fail"
    assert result["cases"][0]["failures"][0]["failure_type"] == "forbidden_output_present"


def test_drift_and_regression_reports_are_generated() -> None:
    base = DEFAULT_SYNTHETIC_CASES[0]
    failing_case = SyntheticCase(
        case_id="synthetic.drift_report_failure",
        chart=base.chart,
        expected_inference_signals={"ten_god_structure.peer.strength": "none"},
        expected_domain_adapter_outputs={},
        forbidden_outputs=[],
        tags=["drift_report"],
    )

    result = run_synthetic_validation([failing_case])

    assert result["drift_report"]["items"]
    assert result["regression_report"]["items"]


def test_domain_adapter_illegal_signal_failures_are_detectable() -> None:
    base = deepcopy(DEFAULT_SYNTHETIC_CASES[0].to_dict())
    base["expected_domain_adapter_outputs"] = {
        "wealth_signals.undefined_signal.value": "high",
    }
    failing_case = SyntheticCase.from_mapping(base)

    result = run_synthetic_validation([failing_case])

    assert result["status"] == "fail"
    assert any(
        failure["failure_type"] == "expectation_mismatch"
        for failure in result["cases"][0]["failures"]
    )
