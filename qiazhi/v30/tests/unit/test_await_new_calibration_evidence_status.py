from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_await_new_calibration_evidence_status,
    run_await_new_calibration_evidence_status,
)


SOURCE_IDS = [
    "real_case_calibration",
    "business_acceptance",
    "518k_distribution",
    "training_signal_distribution",
    "llm_expression_acceptance",
    "question_chain_acceptance",
]


def _e1(*, blocked: bool = False, candidates: int = 0, heavy: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.evidence_driven_calibration_queue.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": (
                "evidence_driven_calibration_queue_has_candidates"
                if candidates
                else "evidence_driven_calibration_queue_ready"
            ),
            "evidence_driven_queue_ready": ready,
            "focused_fix_candidate_count": candidates,
            "focused_module_fix_required": bool(candidates),
            "concrete_evidence_required": True,
            "core_module_reopen_by_default": False,
            "full_pytest_required": heavy,
            "synthetic_all_required": heavy,
            "full_518k_required": heavy,
            "live_llm_required": heavy,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
        "evidence_intake_sources": [{"source_id": source_id} for source_id in SOURCE_IDS],
    }


def test_await_new_calibration_evidence_status_ready(tmp_path: Path) -> None:
    result = build_await_new_calibration_evidence_status(
        evidence_driven_calibration_queue=_e1(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.await_new_calibration_evidence_status.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "await_new_calibration_evidence_ready"
    assert decision["waiting_for_new_calibration_evidence"] is True
    assert result["next_mainline_selection"]["next_task"] == "Await Evidence Or Explicit Major Validation"
    assert Path(str(result["artifact_uri"])).exists()


def test_await_new_calibration_evidence_status_blocks_candidates_or_queue_gap() -> None:
    candidate_result = build_await_new_calibration_evidence_status(
        evidence_driven_calibration_queue=_e1(candidates=1),
    )
    blocked_result = build_await_new_calibration_evidence_status(
        evidence_driven_calibration_queue=_e1(blocked=True),
    )

    assert "no_current_focused_candidates" in candidate_result["decision"]["failed_check_ids"]
    assert candidate_result["next_mainline_selection"]["next_task"] == "Focused Calibration Fix Plan"
    assert "e_s1_evidence_queue_ready" in blocked_result["decision"]["failed_check_ids"]


def test_await_new_calibration_evidence_status_blocks_missing_sources_or_heavy_gate() -> None:
    missing_sources = _e1()
    missing_sources["evidence_intake_sources"] = [{"source_id": "real_case_calibration"}]
    source_result = build_await_new_calibration_evidence_status(
        evidence_driven_calibration_queue=missing_sources,
    )
    heavy_result = build_await_new_calibration_evidence_status(
        evidence_driven_calibration_queue=_e1(heavy=True),
    )

    assert "accepted_evidence_sources_registered" in source_result["decision"]["failed_check_ids"]
    assert "no_heavy_pointer_or_fact_mutation" in heavy_result["decision"]["failed_check_ids"]
    assert heavy_result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False


def test_await_new_calibration_evidence_status_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_await_new_calibration_evidence_status(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "await_new_calibration_evidence_ready"
    assert result["decision"]["waiting_for_new_calibration_evidence"] is True
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
