from __future__ import annotations

from fastapi.testclient import TestClient

from v20.corpus.coverage import FULL_CORPUS_TARGET_COUNT, build_corpus_coverage_plan
from v20.learning.evolution import build_evolution_dry_run_plan
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


def test_v20_corpus_validation_learning_endpoints_are_wired() -> None:
    client = TestClient(app)
    corpus = client.get("/api/v20/corpus/coverage").json()
    suite = client.get("/api/v20/validation/synthetic-suite").json()
    evolution = client.get("/api/v20/learning/evolution-plan").json()

    assert corpus["plan"]["target_case_count"] == 518_400
    assert corpus["runtime_mutation"] is False
    assert suite["ok"] is True
    assert suite["runtime_mutation"] is False
    assert evolution["status"] == "ready_for_dry_run"
    assert evolution["runtime_mutation"] is False
