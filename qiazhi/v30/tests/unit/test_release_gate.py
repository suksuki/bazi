from __future__ import annotations

import subprocess
import sys

from v30.validation import SYNTHETIC_SUITES, run_release_gate


def test_release_gate_quick_composes_runtime_synthetic_and_518k_sample() -> None:
    result = run_release_gate(mode="quick", sample_limit=2)
    assert result.status == "passed"
    assert result.promotion_signal == "eligible"
    assert [row.check_id for row in result.checks] == [
        "runtime_smoke",
        "production_api_smoke",
        "llm_live_smoke",
        "post_seal_contracts",
        "synthetic_all",
        "518k_sample",
    ]
    assert result.checks[1].summary["health_ok"] is True
    assert result.checks[1].summary["created_status"] == "ready"
    assert result.checks[1].summary["projection_contract_version"] == "v30.api_projection_contract.v1"
    assert result.checks[1].summary["customer_core_surface_type"] == "core_bazi_calculation"
    assert result.checks[1].summary["answer_accepted"] is True
    assert result.checks[1].summary["question_outcome_consumed"] is True
    assert result.checks[1].summary["answer_panel_present"] is True
    assert result.checks[1].summary["interaction_state_version"] == "v30.interaction_state.v1"
    assert result.checks[1].summary["visible_next_question_changed"] is True
    assert result.checks[1].summary["history_count"] == 1
    assert result.checks[1].summary["history_owner_scope"] == "actor_and_session"
    assert result.checks[1].summary["history_user_owner_ids_hidden"] is True
    assert result.checks[1].summary["history_user_diagnostics_hidden"] is True
    assert result.checks[1].summary["user_history_internal_fields_hidden"] is True
    assert result.checks[1].summary["admin_history_diagnostics_visible"] is True
    assert result.checks[2].summary["smoke_status"] in {
        "unconfigured",
        "configured_not_executed",
        "accepted",
        "fallback",
        "drift_rejected",
    }
    assert result.checks[2].summary["call_status"] in {"accepted", "fallback"}
    assert result.checks[2].summary["no_chart_fact_mutation_proof"]["chart_facts_unchanged"] is True
    assert result.checks[2].summary["no_chart_fact_mutation_proof"]["ranked_decisions_unchanged"] is True
    assert result.checks[2].summary["no_chart_fact_mutation_proof"]["model_signal_unchanged"] is True
    assert result.checks[2].summary["no_chart_fact_mutation_proof"]["interaction_state_unchanged"] is True
    assert result.checks[2].summary["artifact_uri"]
    assert result.checks[3].summary["projection_contract_version"] == "v30.api_projection_contract.v1"
    assert result.checks[3].summary["user_leak_scan_passed"] is True
    assert result.checks[3].summary["admin_diagnostics_visible"] is True
    assert result.checks[3].summary["phase_seal_passed_count"] == 8
    assert set(result.checks[3].summary["phase_seal_coverage"]) == {
        "M1_birthinput_chart_facts",
        "M2_base_fact_explanation",
        "M3_evidence_rule_structure_spine",
        "M4_ten_god_energy_model",
        "M5_ranked_decisions",
        "M6_practical_reading_output",
        "M7_real_case_calibration",
        "M8_api_projection",
    }
    assert all(
        payload["passed"] is True
        for payload in result.checks[3].summary["phase_seal_coverage"].values()
    )
    assert result.checks[4].summary["case_count"] == len(SYNTHETIC_SUITES["all"])
    assert result.checks[4].summary["tier_coverage"]["interaction_loop_case_count"] == len(SYNTHETIC_SUITES["interaction_loop"])
    assert result.checks[4].summary["tier_coverage"]["real_case_calibration_pack_case_count"] == len(SYNTHETIC_SUITES["real_case_calibration_pack"])
    assert result.checks[4].summary["tier_coverage"]["api_projection_contract_count"] >= len(SYNTHETIC_SUITES["real_case_calibration_pack"])
    assert result.checks[4].summary["tier_coverage"]["api_projection_leak_pass_count"] >= len(SYNTHETIC_SUITES["real_case_calibration_pack"])
    assert result.checks[4].summary["tier_coverage"]["m6_practical_domain_contract_count"] >= 100
    assert result.checks[4].summary["tier_coverage"]["production_replay_metadata_count"] >= len(SYNTHETIC_SUITES["real_case_calibration_pack"])
    assert result.checks[4].summary["tier_coverage"]["production_replay_metadata_privacy_guard_pass_count"] == result.checks[4].summary["tier_coverage"]["production_replay_metadata_count"]
    assert result.checks[4].summary["tier_coverage"]["production_replay_metadata_projection_leak_pass_count"] == result.checks[4].summary["tier_coverage"]["production_replay_metadata_count"]
    assert result.checks[5].summary["case_count"] == 2
    assert result.checks[5].summary["artifact_uri"]
    assert result.checks[5].summary["index_uri"]
    assert result.checks[5].summary["index_entry_uri"]
    assert result.checks[5].summary["artifact_record_id"]
    assert "artifact_search_backend" in result.checks[5].summary
    assert "artifact_searchable" in result.checks[5].summary
    assert result.checks[5].summary["coverage_metrics"]["interaction_state_coverage"] == 2
    assert result.checks[5].summary["coverage_metrics"]["model_signal_summary_coverage"] == 2
    assert result.artifact_review["version"] == "v30.release_artifact_review.v1"
    assert result.artifact_review["status"] == "ready"
    assert result.artifact_review["check_count"] == 6
    assert result.artifact_review["synthetic_suite_summary"]["case_count"] == len(SYNTHETIC_SUITES["all"])
    assert result.artifact_review["corpus_518k_summary"]["sample"]["case_count"] == 2
    assert result.artifact_review["corpus_518k_summary"]["artifact_record_ids"]
    assert result.artifact_review["projection_contract_summary"]["projection_contract_version"] == "v30.api_projection_contract.v1"
    assert result.artifact_review["projection_contract_summary"]["production_replay_metadata_count"] >= len(SYNTHETIC_SUITES["real_case_calibration_pack"])
    assert result.artifact_review["policy_lineage_summary"]["active_policy_versions"]
    assert result.artifact_review["promotion_review"]["policy_promotion_allowed"] is False


def test_release_gate_standard_includes_selected_518k_shard() -> None:
    result = run_release_gate(mode="standard", sample_limit=2, shard_id=7, shard_limit=3)
    assert result.status == "passed"
    assert [row.check_id for row in result.checks] == [
        "runtime_smoke",
        "production_api_smoke",
        "llm_live_smoke",
        "post_seal_contracts",
        "synthetic_all",
        "518k_sample",
        "518k_shard",
    ]
    assert result.checks[6].summary["shard_ids"] == [7]
    assert result.checks[6].summary["case_count"] == 3
    assert result.checks[6].summary["index_uri"]
    assert result.checks[6].summary["artifact_record_id"]
    assert result.artifact_review["corpus_518k_summary"]["shard"]["case_count"] == 3
    assert len(result.artifact_review["corpus_518k_summary"]["artifact_record_ids"]) == 2


def test_release_gate_script_quick() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_release_gate.py", "--sample-limit", "2"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "eligible mode=quick checks=6" in result.stdout
    assert "- production_api_smoke: passed" in result.stdout
    assert "- llm_live_smoke: passed" in result.stdout
    assert "- post_seal_contracts: passed" in result.stdout
    assert "- synthetic_all: passed" in result.stdout
