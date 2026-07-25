from __future__ import annotations

from scripts.v50_run_cognitive_authority_baseline import run_baseline


def test_cognitive_authority_baseline_is_balanced_and_keeps_tools_out_of_first_look() -> None:
    report = run_baseline(run_id="unit")
    observed = report["observed_data"]
    assert report["status"] == "passed"
    assert report["professional_quality_status"] == "pending_expert_review"
    assert report["ready_for_cognitive_promotion"] is False
    assert observed["case_count"] == 35
    assert observed["split_counts"] == {"development": 5, "acceptance": 24, "blind": 6}
    assert observed["structure_family_count"] >= 24
    assert observed["independent_pattern_tool_leak_count"] == 0
    assert observed["challenge_pack_missing_count"] < observed["case_count"]
    assert report["expert_review_packet"]["status"] == "awaiting_live_outputs"
    assert report["boundary_status"]["expected_contract_visible_to_model"] is False
    assert report["boundary_status"]["training_performed"] is False
    assert report["boundary_status"]["automated_quality_used_as_professional_judge"] is False
