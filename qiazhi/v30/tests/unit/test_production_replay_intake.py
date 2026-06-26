from __future__ import annotations

import subprocess
import sys

from v30.validation import build_production_replay_intake_batch, build_production_replay_intake_row, run_synthetic_tier


def test_production_replay_intake_row_selects_metadata_only_candidate() -> None:
    metadata = {
        "version": "v30.production_replay_metadata.v1",
        "case_id": "case-ready",
        "source": "production",
        "calendar_type": "solar",
        "chart_status": "ready",
        "boundary_tags": ["calendar_solar"],
        "readiness_tags": ["chart_ready"],
        "module_contract_tags": ["m4_model_signal_ready", "m5_ranked_decision_ready"],
        "m4_model_signal_ready": True,
        "m5_ranked_decision_ready": True,
        "m6_practical_contract_ready": True,
        "api_projection_contract_ready": True,
        "projection_leak_scan_passed": True,
        "privacy_guard": {
            "metadata_only": True,
            "no_private_user_content": True,
            "no_chart_fact_mutation": True,
            "forbidden_key_scan_passed": True,
        },
    }

    row = build_production_replay_intake_row(
        metadata,
        source_artifact={"family": "518k_sample", "artifact_record_id": "artifact-1"},
    )

    assert row["version"] == "v30.production_replay_intake.v1"
    assert row["selection_status"] == "calibration_ready"
    assert row["calibration_candidate"] is True
    assert row["source_artifact"]["artifact_record_id"] == "artifact-1"
    assert row["privacy_guard"]["no_private_user_content"] is True
    assert row["fact_import_policy"]["chart_facts_imported"] is False
    assert row["fact_import_policy"]["private_content_imported"] is False
    assert "birth_date" not in row
    assert "raw_payload" not in row


def test_production_replay_intake_blocks_private_or_pending_rows() -> None:
    private_row = build_production_replay_intake_row(
        {
            "version": "v30.production_replay_metadata.v1",
            "case_id": "case-private",
            "chart_status": "ready",
            "calendar_type": "solar",
            "m4_model_signal_ready": True,
            "m5_ranked_decision_ready": True,
            "m6_practical_contract_ready": True,
            "api_projection_contract_ready": True,
            "projection_leak_scan_passed": True,
            "privacy_guard": {
                "metadata_only": True,
                "no_private_user_content": True,
                "no_chart_fact_mutation": True,
                "forbidden_key_scan_passed": True,
            },
            "birth_date": "1990-01-01",
        }
    )
    pending_row = build_production_replay_intake_row(
        {
            "version": "v30.production_replay_metadata.v1",
            "case_id": "case-pending",
            "chart_status": "pending",
            "calendar_type": "lunar",
            "projection_leak_scan_passed": True,
            "privacy_guard": {
                "metadata_only": True,
                "no_private_user_content": True,
                "no_chart_fact_mutation": True,
                "forbidden_key_scan_passed": True,
            },
        }
    )

    assert private_row["selection_status"] == "blocked"
    assert "privacy_guard_failed" in private_row["hold_reasons"]
    assert pending_row["selection_status"] == "hold_pending"
    assert "chart_status_pending" in pending_row["hold_reasons"]


def test_production_replay_intake_batch_from_real_case_pack() -> None:
    synthetic = run_synthetic_tier("real_case_calibration_pack")
    metadata_rows = [
        row.observed["production_replay_metadata"]
        for row in synthetic.results
        if row.observed.get("production_replay_metadata")
    ]
    batch = build_production_replay_intake_batch(
        metadata_rows,
        artifact_review={
            "version": "v30.release_artifact_review.v1",
            "status": "ready",
            "artifact_index": [{"family": "518k_sample", "artifact_record_id": "sample-artifact"}],
        },
    )

    assert batch["version"] == "v30.production_replay_intake_batch.v1"
    assert batch["summary"]["row_count"] >= 30
    assert batch["summary"]["calibration_ready_count"] >= 20
    assert batch["summary"]["hold_pending_count"] >= 1
    assert batch["summary"]["blocked_count"] >= 1
    assert batch["summary"]["privacy_guard_pass_count"] == batch["summary"]["row_count"]
    assert set(batch["summary"]["calendar_types"]) >= {"solar", "lunar"}
    assert "unknown_hour" in batch["summary"]["boundary_tag_counts"]
    assert batch["artifact_review_link"]["artifact_families"] == ["518k_sample"]


def test_production_replay_intake_script_outputs_summary() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_production_replay_intake.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.production_replay_intake_batch.v1" in result.stdout
    assert "calibration_ready=" in result.stdout
