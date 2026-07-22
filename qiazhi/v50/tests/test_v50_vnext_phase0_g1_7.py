from __future__ import annotations

import json
from pathlib import Path

from core.mingli_agent.benchmark import direct_power_user_prompt
from scripts.v50_prepare_vnext_phase0_g1_7 import (
    audit_direct_power_user_policy,
    audit_frontier_policy_freeze,
    audit_human_reference_freeze,
    audit_modality_policy,
    audit_p0_repair_authority,
    prepare_g1_7,
)


def test_direct_power_user_baseline_has_targets_without_internal_protocol() -> None:
    prompt = direct_power_user_prompt(
        chart_payload={"pillars": ["甲子", "乙丑", "丙寅", "丁卯"], "gender": "unknown"}
    )
    audit = audit_direct_power_user_policy()

    assert audit["status"] == "passed"
    assert audit["internal_protocol_tokens_found"] == []
    assert "命局重心" in prompt
    assert "事业与财富" in prompt
    assert "Graph" not in prompt
    assert "Challenge Pack" not in prompt


def test_p0_repair_and_modality_policies_are_machine_closed() -> None:
    repair = audit_p0_repair_authority()
    modality = audit_modality_policy()

    assert repair["status"] == "passed"
    assert repair["checks"]["raw_output_hash_present"] is True
    assert repair["checks"]["review_annotations_separate"] is True
    assert "hypothesis_rewrite" in repair["p0_forbidden_repairs"]
    assert modality["status"] == "passed"
    assert modality["natal_fact_conflict_eligible"] == ["asserted_natal_fact", "derived_natal_claim"]
    assert all(row["actual"] == row["expected"] for row in modality["fixed_regression_cases"])


def test_external_freeze_status_is_not_fabricated() -> None:
    reference = audit_human_reference_freeze()
    frontier = audit_frontier_policy_freeze()

    assert reference["status"] == "pending_human_freeze"
    assert reference["llm_authorship_allowed"] is False
    assert frontier["status"] == "pending_true_frontier_selection"
    assert frontier["selected_policy"] is None
    assert frontier["local_open_stress_promoted"] is False


def test_g1_7_packet_stops_before_live_preflight_and_p0_g2(tmp_path: Path) -> None:
    report = prepare_g1_7(
        run_id="g1-7-test",
        output_dir=tmp_path,
        git_state_override={
            "commit": "test-dirty-snapshot",
            "dirty_tree": True,
            "v50_status": ["?? qiazhi/v50/example.py"],
            "v50_snapshot_tracked": False,
        },
    )

    assert report["status"] == "machine_preparation_passed_external_freeze_pending"
    assert all(report["machine_gates"].values())
    assert not any(report["external_gates"].values())
    assert report["ready_for_p0_g2"] is False
    assert report["sealed_chart_accessed"] is False
    assert report["observed_data"]["final_nonsealed_live_preflight"]["run_performed"] is False
    assert report["boundary_status"]["expert_reference_authored_by_llm"] is False
    assert report["boundary_status"]["sealed_outputs_generated"] is False

    lock = json.loads((tmp_path / "FORMAL_RUN_LOCK_CANDIDATE.json").read_text(encoding="utf-8"))
    assert lock["status"] == "candidate_blocked"
    assert "modality_policy" in lock["review_policy_hashes"]
    assert "fact_review" in lock["review_policy_hashes"]
    assert (tmp_path / "MASTER_AUDIT_REPORT.md").exists()
    assert (tmp_path / "ANALYST_REVIEW_PACKET.md").exists()
