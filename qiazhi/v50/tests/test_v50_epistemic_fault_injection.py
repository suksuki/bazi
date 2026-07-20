from __future__ import annotations

from scripts.v50_run_epistemic_fault_injection import run_fault_injection


def test_epistemic_review_detects_all_declared_fault_classes() -> None:
    report = run_fault_injection()

    assert report["status"] == "passed"
    assert report["observed_data"]["fault_count"] == 10
    assert report["observed_data"]["detected_count"] == 10
    assert report["observed_data"]["undetected_faults"] == []
    assert report["boundary_status"]["verifier_relaxed"] is False
