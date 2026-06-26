from __future__ import annotations

from v30.validation.production_replay_metadata import (
    PRODUCTION_REPLAY_METADATA_BOUNDARY,
    build_production_replay_metadata,
    summarize_production_replay_metadata,
)


def test_build_production_replay_metadata_is_metadata_only() -> None:
    metadata = build_production_replay_metadata(
        {
            "case_id": "fixture-1",
            "status": "ready",
            "calendar_type": "lunar",
            "lunar_is_leap_month": True,
            "use_true_solar_time": True,
            "unknown_hour": False,
            "gender_status": "unknown",
            "has_pillars": True,
            "model_signal_ready": True,
            "ranked_decision_count": 3,
            "projection_matrix_ready": True,
            "practical_domain_contracts": {
                domain: {
                    "version": "v30.practical_domain_reading.v2",
                    "calculation_basis_version": "v30.practical_domain_calculation_basis.v1",
                    "model_signal_context_version": "v30.practical_model_signal_context.v1",
                    "ranked_decision_link_count": 3,
                    "raw_score_leak": False,
                }
                for domain in ("career", "wealth", "relationship", "health", "timing")
            },
        },
        api_projection_contract={
            "version": "v30.api_projection_contract.v1",
            "leak_scan": {"passed": True},
        },
    )

    assert metadata["version"] == "v30.production_replay_metadata.v1"
    assert metadata["boundary"] == PRODUCTION_REPLAY_METADATA_BOUNDARY
    assert metadata["calendar_type"] == "lunar"
    assert metadata["lunar_is_leap_month"] is True
    assert metadata["use_true_solar_time"] is True
    assert metadata["unknown_gender"] is True
    assert metadata["m4_model_signal_ready"] is True
    assert metadata["m5_ranked_decision_ready"] is True
    assert metadata["m6_practical_contract_ready"] is True
    assert metadata["projection_leak_scan_passed"] is True
    assert metadata["privacy_guard"]["metadata_only"] is True
    assert metadata["privacy_guard"]["no_private_user_content"] is True
    assert metadata["privacy_guard"]["forbidden_key_scan_passed"] is True
    forbidden = {"birth_date", "birth_time", "answer", "name", "raw_payload", "user_text"}
    assert forbidden.isdisjoint(metadata)


def test_summarize_production_replay_metadata_counts_replay_tags() -> None:
    rows = [
        build_production_replay_metadata(
            {
                "case_id": "ready",
                "status": "ready",
                "calendar_type": "solar",
                "model_signal_ready": True,
                "ranked_decision_count": 3,
                "projection_matrix_ready": True,
                "practical_domain_contracts": {},
            }
        ),
        build_production_replay_metadata(
            {
                "case_id": "blocked",
                "status": "blocked",
                "calendar_type": "lunar",
                "unknown_hour": True,
                "gender_status": "unknown",
                "projection_matrix_ready": False,
                "practical_domain_contracts": {},
            }
        ),
    ]

    summary = summarize_production_replay_metadata(rows)

    assert summary["version"] == "v30.production_replay_metadata_summary.v1"
    assert summary["row_count"] == 2
    assert summary["ready_count"] == 1
    assert summary["blocked_count"] == 1
    assert summary["calendar_types"] == ["lunar", "solar"]
    assert summary["unknown_hour_count"] == 1
    assert summary["unknown_gender_count"] == 1
    assert summary["privacy_guard_pass_count"] == 2
    assert summary["metadata_only_boundary_count"] == 2
