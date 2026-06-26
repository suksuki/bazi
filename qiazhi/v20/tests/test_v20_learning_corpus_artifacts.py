from __future__ import annotations

import json
import shutil

import pytest

from v20.corpus.artifacts import (
    build_corpus_artifacts,
    find_similar_cases,
    read_corpus_artifact_status,
    read_corpus_cluster_model,
    read_corpus_coverage_summary,
    read_corpus_training_artifacts,
)
from v20.corpus.enumerator import canonical_case_at, hour_pillar_for, iter_canonical_cases, month_pillar_for
from v20.corpus.full_precompute import build_full_precompute_manifest, preview_full_precompute_batch, shard_for_index
from v20.corpus.job_runner import FullPrecomputeJobConfig, read_full_precompute_status, run_full_precompute_job
from v20.learning_orchestrator.nightly_executor import read_nightly_executor_status, run_nightly_executor_skeleton


@pytest.fixture(scope="module")
def precomputed_corpus_run(tmp_path_factory):
    runtime_dir = tmp_path_factory.mktemp("v20_corpus_artifact_source")
    run_id = "test_artifacts_source"
    config = FullPrecomputeJobConfig(run_id=run_id, start=0, limit=2, status_every=1)
    run_full_precompute_job(config, runtime_dir=runtime_dir)
    return runtime_dir, run_id


def _copy_precomputed_run(source_runtime_dir, source_run_id: str, target_runtime_dir, target_run_id: str) -> None:
    source = source_runtime_dir / "corpus" / "full_precompute" / source_run_id
    target = target_runtime_dir / "corpus" / "full_precompute" / target_run_id
    shutil.copytree(source, target)
    progress_path = target / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    progress["run_id"] = target_run_id
    progress["run_dir"] = str(target)
    progress_path.write_text(json.dumps(progress, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    latest_path = target_runtime_dir / "corpus" / "full_precompute" / "latest_status.json"
    latest_path.write_text(json.dumps(progress, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def test_v20_nightly_executor_skeleton_runs_limited_resumable_shard(tmp_path) -> None:
    result = run_nightly_executor_skeleton(
        run_id="test_nightly_executor",
        limit=1,
        status_every=1,
        runtime_dir=tmp_path,
    )
    status = read_nightly_executor_status("test_nightly_executor", runtime_dir=tmp_path)

    assert result["status"] == "completed"
    assert result["executor_mode"] == "skeleton_limited_shard"
    assert result["target_case_count"] == 518_400
    assert result["executed_case_count"] == 1
    assert result["completed_case_count"] == 1
    assert result["progress_percent"] == 100
    assert "NO_LLM_CALL" in result["guardrails"]
    assert "NO_RUNTIME_POINTER_MUTATION" in result["guardrails"]
    assert status["run_id"] == "test_nightly_executor"
    assert status["runtime_mutation"] is False


def test_v20_full_corpus_enumerator_maps_518k_valid_pillar_space() -> None:
    first = canonical_case_at(0)
    last = canonical_case_at(518_399)
    sample = iter_canonical_cases(start=720, limit=3)

    assert first.pillar_displays == ("甲子", "丙寅", "甲子", "甲子")
    assert last.case_id == "v20.full_corpus.case.518399"
    assert last.pillar_displays[0] == "癸亥"
    assert month_pillar_for("甲", 0) == "丙寅"
    assert month_pillar_for("癸", 11) == "乙丑"
    assert hour_pillar_for("甲", 0) == "甲子"
    assert hour_pillar_for("癸", 11) == "癸亥"
    assert len(sample) == 3
    assert sample[0].pillar_displays[1] == "丁卯"


def test_v20_full_precompute_preview_builds_structural_label_snapshots() -> None:
    manifest = build_full_precompute_manifest(shard_count=16, batch_size=512, per_case_ms=1.6)
    preview = preview_full_precompute_batch(start=0, limit=1)
    first_snapshot = preview["snapshots"][0]["label_snapshot"]
    shard = shard_for_index(518_399, shard_count=16)

    assert manifest["status"] == "ready_for_dry_run"
    assert manifest["target_case_count"] == 518_400
    assert manifest["cost_estimate"]["dgx_required_for_deterministic_labels"] is False
    assert "corpus_label_snapshot_jsonl" in manifest["artifact_outputs"]
    assert preview["runtime_mutation"] is False
    assert preview["returned_count"] == 1
    assert first_snapshot["snapshot_hash"]
    assert first_snapshot["label_policy"] == "structural_features_and_decision_portrait_projection_axes_only"
    assert first_snapshot["feature_domains"]
    assert first_snapshot["portrait_domains"]
    assert first_snapshot["wealth_material_level"] in {"visible", "hidden_only", "not_visible"}
    assert first_snapshot["useful_god_candidate_count"] >= 1
    assert first_snapshot["mainline_domains"]
    assert first_snapshot["evidence_density"]["mainline_count"] == len(first_snapshot["mainline_domains"])
    assert "NO_DESTINY_TRUTH_LABEL" in first_snapshot["guardrails"]
    assert shard["shard_id"] == "v20.corpus.shard.015"


def test_v20_full_precompute_job_writes_resumable_progress(tmp_path) -> None:
    config = FullPrecomputeJobConfig(run_id="test_518k_job", start=0, limit=1, status_every=1)
    result = run_full_precompute_job(config, runtime_dir=tmp_path)
    status = read_full_precompute_status("test_518k_job", runtime_dir=tmp_path)
    latest = read_full_precompute_status(runtime_dir=tmp_path)
    snapshot_path = tmp_path / "corpus" / "full_precompute" / "test_518k_job" / "snapshots.jsonl"

    assert result["status"] == "completed"
    assert result["completed_from_start"] == 1
    assert status["next_index"] == 1
    assert status["processed"] == 1
    assert status["total"] == 1
    assert status["progress_percent"] == 100.0
    assert status["speed_per_second"] >= 0
    assert latest["run_id"] == "test_518k_job"
    assert snapshot_path.exists()
    assert len(snapshot_path.read_text(encoding="utf-8").splitlines()) == 1
    resumed = run_full_precompute_job(config, runtime_dir=tmp_path)
    assert resumed["processed_this_session"] == 0


def test_v20_corpus_artifacts_build_coverage_index_and_similarity(tmp_path, precomputed_corpus_run) -> None:
    source_runtime_dir, source_run_id = precomputed_corpus_run
    _copy_precomputed_run(source_runtime_dir, source_run_id, tmp_path, "test_artifacts")
    status = build_corpus_artifacts("test_artifacts", runtime_dir=tmp_path, status_every=2)
    artifact_status = read_corpus_artifact_status("test_artifacts", runtime_dir=tmp_path)
    latest_artifact_status = read_corpus_artifact_status(runtime_dir=tmp_path)
    summary = read_corpus_coverage_summary("test_artifacts", runtime_dir=tmp_path)
    clusters = read_corpus_cluster_model("test_artifacts", runtime_dir=tmp_path)
    training = read_corpus_training_artifacts("test_artifacts", runtime_dir=tmp_path)
    similar = find_similar_cases("v20.full_corpus.case.000000", run_id="test_artifacts", runtime_dir=tmp_path, limit=3)

    assert status["status"] == "completed"
    assert status["processed"] == 2
    assert artifact_status["status"] == "completed"
    assert artifact_status["runtime_mutation"] is False
    assert latest_artifact_status["run_id"] == "test_artifacts"
    assert latest_artifact_status["status"] == "completed"
    assert summary["case_count"] == 2
    assert summary["distributions"]["feature_domains"]["strength"] == 2
    assert "wealth_material_level" in summary["distributions"]
    assert "mainline_domains" in summary["distributions"]
    assert summary["averages"]["portrait_axis_count"] > 0
    assert summary["cluster_count"] >= 1
    assert clusters["status"] == "ready"
    assert "wealth_material_level" in clusters["signature_dimensions"]
    assert "mainline_domains" in clusters["signature_dimensions"]
    assert clusters["clusters"][0]["centroid_tags"]
    assert training["status"] == "ready"
    assert training["portrait_axis_training"]["status"] == "ready"
    assert training["rule_proposal_training"]["status"] == "ready"
    assert similar["status"] == "ready"
    assert similar["match_count"] >= 1
    assert similar["candidate_count"] >= similar["match_count"]
    assert "wealth_material_level" in similar["query"]
    assert "mainline_domains" in similar["query"]
    assert similar["matches"][0]["shared_tag_count"] >= 1
    assert "wealth_material_level" in similar["matches"][0]
    assert "mainline_domains" in similar["matches"][0]
    assert "NO_DESTINY_OUTCOME_INFERENCE" in similar["guardrails"]


def test_v20_corpus_artifacts_can_skip_disposable_sqlite_cache(tmp_path, precomputed_corpus_run) -> None:
    source_runtime_dir, source_run_id = precomputed_corpus_run
    _copy_precomputed_run(source_runtime_dir, source_run_id, tmp_path, "test_artifacts_no_sqlite")
    status = build_corpus_artifacts(
        "test_artifacts_no_sqlite",
        runtime_dir=tmp_path,
        status_every=1,
        build_sqlite_cache=False,
    )
    artifact_status = read_corpus_artifact_status("test_artifacts_no_sqlite", runtime_dir=tmp_path)
    sqlite_path = tmp_path / "corpus" / "full_precompute" / "test_artifacts_no_sqlite" / "artifacts" / "corpus_index.sqlite"

    assert status["status"] == "completed"
    assert status["processed"] == 2
    assert status["local_sqlite_cache"]["enabled"] is False
    assert status["local_sqlite_cache"]["authority"] == "postgres_or_versioned_jsonl_artifacts"
    assert "sqlite_cache" not in status["artifact_outputs"]
    assert not sqlite_path.exists()
    assert artifact_status["local_sqlite_cache"]["enabled"] is False
