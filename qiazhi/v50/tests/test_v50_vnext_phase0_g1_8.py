from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from core.mingli_agent.phase0_governance import load_json
from scripts.v50_prepare_vnext_phase0_expert_reference_workspace import (
    apply_erratum,
    freeze_candidate,
    prepare_workspace,
    validate_workspace,
)
from scripts.v50_prepare_vnext_phase0_frontier_selection import (
    DEFAULT_POLICY,
    SELECTION_FIXTURES,
    SELECTION_MANIFEST,
    prepare_selection,
)
from scripts.v50_prepare_vnext_phase0_g1_8 import prepare_g1_8
from scripts.v50_prepare_vnext_phase0_snapshot import prepare_snapshot
from scripts.v50_run_vnext_phase0_benchmark import DEVELOPMENT_FIXTURE_PACK_PATH, DEVELOPMENT_SET_PATH, run_benchmark


def test_expert_workspace_is_hash_complete_but_semantically_human_only(tmp_path: Path) -> None:
    result = prepare_workspace(output_dir=tmp_path)
    workspace_path = Path(result["workspace_path"])
    workspace = load_json(workspace_path)
    strict = validate_workspace(workspace=workspace, require_frozen=True)

    assert result["chart_count"] == 10
    assert result["fact_hashes_present"] is True
    assert result["semantic_content_authored_by_machine"] is False
    assert strict["status"] == "failed"
    assert any(error.startswith("semantic_field_empty:") for error in strict["errors"])
    with pytest.raises(ValueError, match="expert_reference_freeze_rejected"):
        freeze_candidate(workspace_path=workspace_path, output_path=tmp_path / "must-not-exist.json")


def test_expert_workspace_rejects_reality_or_model_output_fields(tmp_path: Path) -> None:
    result = prepare_workspace(output_dir=tmp_path)
    workspace = load_json(Path(result["workspace_path"]))
    workspace["references"][0]["actual_career"] = "forbidden reality"
    workspace["references"][1]["model_output"] = {"hypothesis": "forbidden"}

    audit = validate_workspace(workspace=workspace, require_frozen=False)

    assert audit["status"] == "failed"
    assert audit["forbidden_field_hits"] == ["actual_career", "model_output"]


def test_frozen_expert_reference_only_changes_through_signed_versioned_erratum(tmp_path: Path) -> None:
    result = prepare_workspace(output_dir=tmp_path / "workspace")
    workspace_path = Path(result["workspace_path"])
    workspace = load_json(workspace_path)
    semantic_fields = [
        key
        for key, value in workspace["references"][0].items()
        if isinstance(value, list) and key not in {"pillars", "revision_history"}
    ]
    item = {
        "statement": "测试用人工专业判断",
        "reason": "测试冻结与勘误合同",
        "evidence_basis": "structural",
        "source_refs": ["F001"],
    }
    for row in workspace["references"]:
        for field in semantic_fields:
            row[field] = [dict(item)]
        row["status"] = "frozen"
        row["author"] = "human-test-author"
        row["frozen_at"] = "2026-07-16T00:00:00Z"
        row["human_signature"] = "human-test-signature"
    workspace_path.write_text(json.dumps(workspace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    frozen_path = tmp_path / "expert-frozen-v1.json"
    freeze_candidate(workspace_path=workspace_path, output_path=frozen_path)
    frozen = load_json(frozen_path)
    chart_id = frozen["references"][0]["chart_id"]
    old_value = frozen["references"][0]["must_notice"]
    old_hash = sha256(
        json.dumps(old_value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    erratum = {
        "version": "deepbazi.vnext_phase0.expert_reference_erratum.v1",
        "status": "draft_human_signoff",
        "erratum_id": "ER-TEST-001",
        "base_reference_sha256": sha256(frozen_path.read_bytes()).hexdigest(),
        "target_version": "deepbazi.vnext_phase0.expert_reference_space.v2.1",
        "reason": "测试版本化勘误",
        "changes": [
            {
                "chart_id": chart_id,
                "field": "must_notice",
                "old_value_sha256": old_hash,
                "new_value": [{**item, "statement": "测试用修订判断"}],
                "reason": "修订专业判断",
                "source_refs": ["F001"],
            }
        ],
        "author": "human-test-author",
        "signed_at": "2026-07-16T01:00:00Z",
        "human_signature": "human-test-erratum-signature",
    }
    erratum_path = tmp_path / "erratum.json"
    erratum_path.write_text(json.dumps(erratum, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="erratum_not_human_signed"):
        apply_erratum(base_path=frozen_path, erratum_path=erratum_path, output_path=tmp_path / "rejected.json")

    erratum["status"] = "human_signed"
    erratum_path.write_text(json.dumps(erratum, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    updated_path = tmp_path / "expert-frozen-v2-1.json"
    result = apply_erratum(base_path=frozen_path, erratum_path=erratum_path, output_path=updated_path)
    updated = load_json(updated_path)

    assert result["status"] == "versioned_erratum_candidate_written"
    assert updated["references"][0]["must_notice"][0]["statement"] == "测试用修订判断"
    assert updated["references"][0]["revision_history"][-1]["erratum_id"] == "ER-TEST-001"


def test_frontier_selection_plans_three_repeats_without_formal_assets(tmp_path: Path) -> None:
    report = run_benchmark(
        run_id="g1-8-selection-plan",
        live=False,
        dry_run=True,
        model_selection_run=True,
        repeats=3,
        selected_lanes=["direct_frontier"],
        base_url="http://127.0.0.1:9",
        same_model="not-used",
        frontier_base_url="http://127.0.0.1:9",
        frontier_model="candidate-model",
        frontier_kind="true_frontier",
        frontier_max_tokens=4200,
        selected_case_ids=[],
        retry_failures=False,
        output_dir=tmp_path,
        manifest_path=SELECTION_MANIFEST,
        fixture_pack_path=SELECTION_FIXTURES,
    )

    assert report["scope"]["model_selection_run"] is True
    assert report["scope"]["repeats"] == 3
    assert report["observed_data"]["planned_count"] == 15
    assert report["scope"]["resource_access"]["formal_manifest_accessed"] is False
    assert report["scope"]["resource_access"]["expert_reference_accessed"] is False
    assert report["boundary_status"]["formal_outputs_generated"] is False


def test_empty_frontier_policy_stays_pending_without_fabricating_candidate(tmp_path: Path) -> None:
    report = prepare_selection(
        policy_path=DEFAULT_POLICY,
        output_dir=tmp_path,
        execute=False,
        run_id="g1-8-frontier-empty",
    )

    assert report["status"] == "pending_candidate_configuration"
    assert report["candidate_count"] == 0
    assert report["selected_candidate"] is None
    assert report["automatic_winner_claimed"] is False


def test_model_selection_mode_rejects_any_non_selection_manifest(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires_isolated_selection_manifest"):
        run_benchmark(
            run_id="g1-8-invalid-selection-scope",
            live=False,
            dry_run=True,
            model_selection_run=True,
            repeats=3,
            selected_lanes=["direct_frontier"],
            base_url="http://127.0.0.1:9",
            same_model="not-used",
            frontier_base_url="http://127.0.0.1:9",
            frontier_model="candidate-model",
            frontier_kind="true_frontier",
            frontier_max_tokens=4200,
            selected_case_ids=[],
            retry_failures=False,
            output_dir=tmp_path,
            manifest_path=DEVELOPMENT_SET_PATH,
            fixture_pack_path=DEVELOPMENT_FIXTURE_PACK_PATH,
        )


def test_snapshot_refuses_to_freeze_untracked_v50(tmp_path: Path) -> None:
    candidate = prepare_snapshot(output_dir=tmp_path / "candidate", freeze=False)

    assert candidate["status"] == "candidate_blocked"
    assert "v50_code_snapshot_not_committed" in candidate["blockers"]
    assert candidate["boundaries"]["automatic_git_commit_performed"] is False
    with pytest.raises(ValueError, match="snapshot_freeze_rejected"):
        prepare_snapshot(output_dir=tmp_path / "frozen", freeze=True)


def test_g1_8_completes_machine_workbench_but_never_starts_g2(tmp_path: Path) -> None:
    report = prepare_g1_8(run_id="g1-8-test", output_dir=tmp_path)

    assert report["status"] == "machine_workbench_complete_external_inputs_pending"
    assert all(report["machine_deliverables"].values())
    assert not any(report["external_inputs"].values())
    assert report["ready_for_p0_g2"] is False
    assert report["final_nonsealed_live_preflight"]["performed"] is False
    assert report["boundary_status"]["live_model_calls_performed"] is False
    assert report["boundary_status"]["sealed_formal_charts_executed"] is False
    assert report["boundary_status"]["p0_g2_started"] is False

    manifest = json.loads((tmp_path / "ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    paths = {row["path"] for row in manifest["files"]}
    assert "human-expert-reference/EXPERT_REFERENCE_AUTHORING_WORKSPACE.json" in paths
    assert "frontier-selection/FRONTIER_SELECTION_REPORT.json" in paths
    assert "execution-snapshot/EXECUTION_SNAPSHOT_CANDIDATE.json" in paths
