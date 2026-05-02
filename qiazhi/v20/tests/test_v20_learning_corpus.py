from __future__ import annotations

from fastapi.testclient import TestClient

from v20.corpus.artifacts import (
    build_corpus_artifacts,
    find_similar_cases,
    read_corpus_artifact_status,
    read_corpus_cluster_model,
    read_corpus_coverage_summary,
    read_corpus_training_artifacts,
)
from v20.corpus.coverage import FULL_CORPUS_TARGET_COUNT, build_corpus_coverage_plan
from v20.corpus.enumerator import canonical_case_at, hour_pillar_for, iter_canonical_cases, month_pillar_for
from v20.corpus.full_precompute import build_full_precompute_manifest, preview_full_precompute_batch, shard_for_index
from v20.corpus.job_runner import FullPrecomputeJobConfig, read_full_precompute_status, run_full_precompute_job
from v20.learning.evolution import build_evolution_dry_run_plan
from v20.learning.decision_registry_iteration import build_decision_registry_iteration_report
from v20.decision.knowledge_bridge import build_knowledge_rule_review_overlay
from v20.learning.rule_activation import (
    build_rule_activation_report,
    build_rule_activation_packet_summary,
)
from v20.learning.rule_replay_eval import build_rule_replay_eval_report
from v20.learning.rule_subcondition_split import build_rule_subcondition_split_report
from v20.learning.run_plan import build_learning_run_plan
from v20.validation.rule_synthetic import build_rule_synthetic_training_report, run_rule_synthetic_suite
from v20.server import app
from v20.validation.knowledge_rule_library import build_knowledge_rule_validation_report
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
    rule_suite = run_rule_synthetic_suite()
    rule_training = build_rule_synthetic_training_report()
    evolution = build_evolution_dry_run_plan(validation_report=suite)

    assert suite["ok"] is True
    assert suite["runtime_mutation"] is False
    assert rule_suite["ok"] is True
    assert rule_suite["case_count"] >= 4
    assert rule_training["status"] == "ready"
    assert "FULL_CORPUS_REMAINS_PRIOR_AND_COVERAGE_ONLY" in rule_training["guardrails"]
    assert all(row["runtime_allowed"] is True for row in rule_training["rule_domain_training"])
    assert evolution["status"] == "ready_for_dry_run"
    assert "learning_to_rank_question_order" in evolution["allowed_algorithm_tracks"]
    assert "neural_conclusion_generation" in evolution["deferred_algorithm_tracks"]
    assert evolution["runtime_mutation"] is False


def test_v20_knowledge_rule_validation_marks_synthetic_and_corpus_gaps() -> None:
    report = build_knowledge_rule_validation_report()
    useful_god = build_knowledge_rule_validation_report("useful_god")

    assert report["status"] == "active_ready"
    assert report["ok"] is True
    assert report["definition_count"] >= 12
    assert report["synthetic_covered_count"] == report["definition_count"]
    assert report["missing_synthetic_count"] == 0
    assert report["corpus_signal_count"] >= 1
    assert report["runtime_allowed_count"] == 0
    assert "split_by_exact_feature_signature_and_counterexamples" in report["review_actions"]
    assert useful_god["synthetic_covered_count"] == useful_god["definition_count"]
    assert all(row["synthetic_state"] == "synthetic_passed" for row in useful_god["definitions"])
    assert "CORPUS_SUPPORT_IS_PRIOR_NOT_RULE_TRUTH" in report["guardrails"]


def test_v20_rule_activation_batches_active_rules_for_iteration() -> None:
    gate = build_rule_activation_report()
    summary = build_rule_activation_packet_summary()
    split = build_rule_subcondition_split_report(per_rule=3)
    replay = build_rule_replay_eval_report(per_rule=3)
    registry = build_decision_registry_iteration_report(per_rule=3)
    overlay = build_knowledge_rule_review_overlay()

    assert gate["status"] == "ready"
    assert gate["packet_count"] >= 12
    assert gate["runtime_activation_candidate_count"] >= 1
    assert gate["blocked_count"] == 0
    assert gate["needs_subcondition_count"] == 0
    assert gate["subcondition_active_ready_count"] >= 1
    assert "subcondition_active_ready" in gate["lane_counts"]
    assert "DECISION_REGISTRY_RECORDS_ITERATION_HISTORY" in gate["guardrails"]
    assert summary["packet_count"] == gate["packet_count"]
    assert all("iteration_options" in row for row in summary["packets"])
    assert any("activate_subconditions_for_replay_eval" in row["iteration_options"] for row in summary["packets"])
    assert split["status"] == "ready"
    assert split["packet_count"] == gate["subcondition_active_ready_count"]
    assert split["subcondition_count"] >= split["packet_count"]
    assert split["quality_status"] == "active_ready"
    assert all(row["runtime_allowed"] is True for row in split["packets"])
    assert replay["status"] == "ready"
    assert replay["subcondition_active_ready_count"] == gate["subcondition_active_ready_count"]
    assert replay["evaluated_packet_count"] == replay["subcondition_active_ready_count"]
    assert replay["replay_eval_ready_count"] <= replay["evaluated_packet_count"]
    assert replay["eval_status_counts"]
    assert replay["subcondition_eval_count"] >= split["subcondition_count"]
    assert replay["portrait_mapping_ok_count"] <= replay["evaluated_packet_count"]
    assert replay["decision_domain_ok_count"] <= replay["evaluated_packet_count"]
    assert replay["runtime_activation_count"] == 0
    assert all(row["runtime_allowed"] is True for row in replay["evaluations"])
    assert all(row["next_action"] in {"continue_runtime_replay", "collect_more_runtime_replay"} for row in replay["evaluations"])
    assert "RULE_REPLAY_EVAL_IS_CONTINUOUS_ITERATION" in replay["guardrails"]
    assert registry["status"] == "ready"
    assert registry["decision_record_count"] >= split["packet_count"]
    assert registry["runtime_activation_count"] == 0
    assert registry["system_iteration_count"] >= 1
    assert "DECISION_REGISTRY_IS_ITERATION_LEDGER" in registry["guardrails"]
    assert overlay["status"] == "ready"
    assert overlay["validation_status"] == "active_ready"
    assert overlay["runtime_activation_candidate_count"] == 0
    assert "RUNTIME_USES_LIGHTWEIGHT_BRIDGE" in overlay["guardrails"]
    decision_ids = [row["decision_id"] for row in registry["records"]]
    assert len(decision_ids) == len(set(decision_ids))


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
    config = FullPrecomputeJobConfig(run_id="test_518k_job", start=0, limit=3, status_every=1)
    result = run_full_precompute_job(config, runtime_dir=tmp_path)
    status = read_full_precompute_status("test_518k_job", runtime_dir=tmp_path)
    latest = read_full_precompute_status(runtime_dir=tmp_path)
    snapshot_path = tmp_path / "corpus" / "full_precompute" / "test_518k_job" / "snapshots.jsonl"

    assert result["status"] == "completed"
    assert result["completed_from_start"] == 3
    assert status["next_index"] == 3
    assert status["processed"] == 3
    assert status["total"] == 3
    assert status["progress_percent"] == 100.0
    assert status["speed_per_second"] >= 0
    assert latest["run_id"] == "test_518k_job"
    assert snapshot_path.exists()
    assert len(snapshot_path.read_text(encoding="utf-8").splitlines()) == 3
    resumed = run_full_precompute_job(config, runtime_dir=tmp_path)
    assert resumed["processed_this_session"] == 0


def test_v20_corpus_artifacts_build_coverage_index_and_similarity(tmp_path) -> None:
    config = FullPrecomputeJobConfig(run_id="test_artifacts", start=0, limit=6, status_every=2)
    run_full_precompute_job(config, runtime_dir=tmp_path)
    status = build_corpus_artifacts("test_artifacts", runtime_dir=tmp_path, status_every=2)
    artifact_status = read_corpus_artifact_status("test_artifacts", runtime_dir=tmp_path)
    latest_artifact_status = read_corpus_artifact_status(runtime_dir=tmp_path)
    summary = read_corpus_coverage_summary("test_artifacts", runtime_dir=tmp_path)
    clusters = read_corpus_cluster_model("test_artifacts", runtime_dir=tmp_path)
    training = read_corpus_training_artifacts("test_artifacts", runtime_dir=tmp_path)
    similar = find_similar_cases("v20.full_corpus.case.000000", run_id="test_artifacts", runtime_dir=tmp_path, limit=3)

    assert status["status"] == "completed"
    assert status["processed"] == 6
    assert artifact_status["status"] == "completed"
    assert artifact_status["runtime_mutation"] is False
    assert latest_artifact_status["run_id"] == "test_artifacts"
    assert latest_artifact_status["status"] == "completed"
    assert summary["case_count"] == 6
    assert summary["distributions"]["feature_domains"]["strength"] == 6
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


def test_v20_corpus_artifacts_can_skip_disposable_sqlite_cache(tmp_path) -> None:
    config = FullPrecomputeJobConfig(run_id="test_artifacts_no_sqlite", start=0, limit=3, status_every=1)
    run_full_precompute_job(config, runtime_dir=tmp_path)
    status = build_corpus_artifacts(
        "test_artifacts_no_sqlite",
        runtime_dir=tmp_path,
        status_every=1,
        build_sqlite_cache=False,
    )
    artifact_status = read_corpus_artifact_status("test_artifacts_no_sqlite", runtime_dir=tmp_path)
    sqlite_path = tmp_path / "corpus" / "full_precompute" / "test_artifacts_no_sqlite" / "artifacts" / "corpus_index.sqlite"

    assert status["status"] == "completed"
    assert status["local_sqlite_cache"]["enabled"] is False
    assert status["local_sqlite_cache"]["authority"] == "postgres_or_versioned_jsonl_artifacts"
    assert "sqlite_cache" not in status["artifact_outputs"]
    assert not sqlite_path.exists()
    assert artifact_status["local_sqlite_cache"]["enabled"] is False


def test_v20_corpus_validation_learning_endpoints_are_wired() -> None:
    client = TestClient(app)
    corpus = client.get("/api/v20/corpus/coverage").json()
    precompute = client.get("/api/v20/corpus/full-precompute/manifest").json()
    preview = client.get("/api/v20/corpus/full-precompute/preview?start=0&limit=1").json()
    status = client.get("/api/v20/corpus/full-precompute/status").json()
    artifact_status = client.get("/api/v20/corpus/artifacts/status").json()
    artifact_summary = client.get("/api/v20/corpus/artifacts/coverage-summary").json()
    artifact_clusters = client.get("/api/v20/corpus/artifacts/cluster-model").json()
    artifact_training = client.get("/api/v20/corpus/artifacts/training").json()
    suite = client.get("/api/v20/validation/synthetic-suite").json()
    rule_suite = client.get("/api/v20/validation/rule-synthetic-suite").json()
    knowledge_rule_validation = client.get("/api/v20/validation/knowledge-rule-library").json()
    knowledge_rule_overlay = client.get("/api/v20/knowledge/rule-review-overlay").json()
    activation = client.get("/api/v20/learning/rule-activation").json()
    activation_packets = client.get("/api/v20/learning/rule-activation-packets").json()
    subcondition_split = client.get("/api/v20/learning/rule-subcondition-split?per_rule=3").json()
    replay_eval = client.get("/api/v20/learning/rule-replay-eval?per_rule=3").json()
    decision_registry_iteration = client.get("/api/v20/learning/decision-registry-iteration?per_rule=3").json()
    rule_training = client.get("/api/v20/learning/rule-synthetic-training").json()
    evolution = client.get("/api/v20/learning/evolution-plan").json()
    run_plan = client.get("/api/v20/learning/run-plan").json()

    assert corpus["plan"]["target_case_count"] == 518_400
    assert corpus["runtime_mutation"] is False
    assert precompute["target_case_count"] == 518_400
    assert precompute["runtime_mutation"] is False
    assert preview["returned_count"] == 1
    assert preview["snapshots"][0]["label_snapshot"]["snapshot_hash"]
    assert status["runtime_mutation"] is False
    assert artifact_status["runtime_mutation"] is False
    assert artifact_summary["runtime_mutation"] is False
    assert artifact_clusters["runtime_mutation"] is False
    assert artifact_training["runtime_mutation"] is False
    assert suite["ok"] is True
    assert suite["runtime_mutation"] is False
    assert rule_suite["ok"] is True
    assert rule_suite["runtime_mutation"] is False
    assert knowledge_rule_validation["runtime_mutation"] is False
    assert knowledge_rule_validation["status"] == "active_ready"
    assert knowledge_rule_validation["missing_synthetic_count"] == 0
    assert knowledge_rule_overlay["runtime_mutation"] is False
    assert knowledge_rule_overlay["status"] == "ready"
    assert activation["runtime_mutation"] is False
    assert activation["status"] == "ready"
    assert activation["runtime_activation_candidate_count"] == 0
    assert activation_packets["runtime_mutation"] is False
    assert activation_packets["packet_count"] == activation["packet_count"]
    assert subcondition_split["runtime_mutation"] is False
    assert subcondition_split["packet_count"] == activation["subcondition_active_ready_count"]
    assert replay_eval["runtime_mutation"] is False
    assert replay_eval["status"] == "ready"
    assert replay_eval["replay_eval_ready_count"] == replay_eval["evaluated_packet_count"]
    assert replay_eval["runtime_activation_count"] == 0
    assert decision_registry_iteration["runtime_mutation"] is False
    assert decision_registry_iteration["decision_record_count"] >= subcondition_split["subcondition_count"]
    assert decision_registry_iteration["runtime_activation_count"] == 0
    assert rule_training["status"] == "ready"
    assert rule_training["runtime_mutation"] is False
    assert evolution["status"] == "ready_for_dry_run"
    assert evolution["runtime_mutation"] is False
    assert run_plan["target_case_count"] == 518_400
    assert run_plan["runtime_mutation"] is False
