from __future__ import annotations

from v30.validation.synthetic_coverage_manifest import build_synthetic_coverage_manifest


def test_synthetic_coverage_manifest_accepts_current_and_planned_tiers() -> None:
    result = build_synthetic_coverage_manifest()

    assert result["version"] == "v30.synthetic_coverage_manifest.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "bt6_synthetic_coverage_manifest_ready"
    assert result["decision"]["synthetic_completion"] == 99
    assert result["summary"]["implemented_tier_count"] >= 20
    assert "central_brain" in result["summary"]["implemented_tiers"]
    assert "training_pipeline" in result["summary"]["implemented_tiers"]
    assert "training_pipeline" not in result["summary"]["planned_tiers"]
    assert "all" in result["summary"]["major_node_only_tiers"]
    assert result["policy_boundary"]["synthetic_tier_may_claim_destiny_truth"] is False
    assert result["next_mainline_selection"]["task_id"] == "BT9"


def test_synthetic_coverage_manifest_marks_planned_bt7_bt8_tiers() -> None:
    result = build_synthetic_coverage_manifest()
    rows = {row["tier"]: row for row in result["tiers"]}

    assert rows["central_brain"]["status"] == "implemented"
    assert rows["central_brain"]["implemented"] is True
    assert rows["central_brain"]["case_count"] >= 5
    assert rows["training_pipeline"]["status"] == "implemented"
    assert rows["training_pipeline"]["implemented"] is True
    assert rows["training_pipeline"]["case_count"] >= 80
    assert rows["smoke"]["status"] == "implemented"
    assert rows["smoke"]["case_count"] == 5


def test_synthetic_coverage_manifest_blocks_undocumented_tier() -> None:
    result = build_synthetic_coverage_manifest(
        synthetic_suites={"smoke": (object(),), "unknown_future_tier": (object(),)},
        tier_contracts={"smoke": {"protects": ["smoke"], "module_scope": ["M3"], "truth_claim": "contract_only"}},
    )

    assert result["status"] == "blocked"
    assert "required_manifest_tiers_are_documented" in result["decision"]["failed_check_ids"]
    assert result["summary"]["undocumented_tiers"] == ["unknown_future_tier"]
    assert result["next_mainline_selection"]["task_id"] == "BT6-FR"
