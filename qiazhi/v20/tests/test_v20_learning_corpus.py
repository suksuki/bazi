from __future__ import annotations

from fastapi.testclient import TestClient

from v20.corpus.coverage import FULL_CORPUS_TARGET_COUNT, build_corpus_coverage_plan
from v20.corpus.enumerator import canonical_case_at, hour_pillar_for, iter_canonical_cases, month_pillar_for
from v20.corpus.full_precompute import build_full_precompute_manifest, preview_full_precompute_batch, shard_for_index
from v20.learning.evolution import build_evolution_dry_run_plan
from v20.learning.run_plan import build_learning_run_plan
from v20.server import app
from v20.validation.suite import run_synthetic_suite


def test_v20_corpus_coverage_plan_tracks_518k_without_mutation() -> None:
    plan = build_corpus_coverage_plan(shard_count=32, batch_size=128)

    assert plan.target_case_count == FULL_CORPUS_TARGET_COUNT
    assert plan.target_case_count == 518_400
    assert plan.shard_count == 32
    assert sum(shard.case_count for shard in plan.shards) == FULL_CORPUS_TARGET_COUNT
    assert plan.runtime_mutation is False
    assert "NO_DESTINY_TRUTH_LABEL" in plan.guardrails


def test_v20_synthetic_suite_and_evolution_plan_are_dry_run_only() -> None:
    suite = run_synthetic_suite()
    evolution = build_evolution_dry_run_plan(validation_report=suite)

    assert suite["ok"] is True
    assert suite["runtime_mutation"] is False
    assert evolution["status"] == "ready_for_dry_run"
    assert "learning_to_rank_question_order" in evolution["allowed_algorithm_tracks"]
    assert "neural_conclusion_generation" in evolution["deferred_algorithm_tracks"]
    assert evolution["runtime_mutation"] is False


def test_v20_learning_run_plan_maps_518k_to_structural_artifacts() -> None:
    run_plan = build_learning_run_plan(corpus_plan=build_corpus_coverage_plan(shard_count=16, batch_size=512))

    assert run_plan["status"] == "ready_for_dry_run"
    assert run_plan["target_case_count"] == 518_400
    assert run_plan["shard_count"] == 16
    assert run_plan["estimated_batch_count"] > 0
    assert "corpus_snapshot_manifest" in run_plan["artifact_outputs"]
    assert "NO_DESTINY_TRUTH_LABELS" in run_plan["guardrails"]
    assert all(stage["runtime_mutation"] is False for stage in run_plan["stages"])


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
    preview = preview_full_precompute_batch(start=0, limit=2)
    first_snapshot = preview["snapshots"][0]["label_snapshot"]
    shard = shard_for_index(518_399, shard_count=16)

    assert manifest["status"] == "ready_for_dry_run"
    assert manifest["target_case_count"] == 518_400
    assert manifest["cost_estimate"]["dgx_required_for_deterministic_labels"] is False
    assert "corpus_label_snapshot_jsonl" in manifest["artifact_outputs"]
    assert preview["runtime_mutation"] is False
    assert preview["returned_count"] == 2
    assert first_snapshot["snapshot_hash"]
    assert first_snapshot["label_policy"] == "structural_feature_and_portrait_tags_only"
    assert first_snapshot["feature_domains"]
    assert first_snapshot["portrait_domains"]
    assert "NO_DESTINY_TRUTH_LABEL" in first_snapshot["guardrails"]
    assert shard["shard_id"] == "v20.corpus.shard.015"


def test_v20_corpus_validation_learning_endpoints_are_wired() -> None:
    client = TestClient(app)
    corpus = client.get("/api/v20/corpus/coverage").json()
    precompute = client.get("/api/v20/corpus/full-precompute/manifest").json()
    preview = client.get("/api/v20/corpus/full-precompute/preview?start=0&limit=1").json()
    suite = client.get("/api/v20/validation/synthetic-suite").json()
    evolution = client.get("/api/v20/learning/evolution-plan").json()
    run_plan = client.get("/api/v20/learning/run-plan").json()

    assert corpus["plan"]["target_case_count"] == 518_400
    assert corpus["runtime_mutation"] is False
    assert precompute["target_case_count"] == 518_400
    assert precompute["runtime_mutation"] is False
    assert preview["returned_count"] == 1
    assert preview["snapshots"][0]["label_snapshot"]["snapshot_hash"]
    assert suite["ok"] is True
    assert suite["runtime_mutation"] is False
    assert evolution["status"] == "ready_for_dry_run"
    assert evolution["runtime_mutation"] is False
    assert run_plan["target_case_count"] == 518_400
    assert run_plan["runtime_mutation"] is False
