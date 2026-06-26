from __future__ import annotations

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
import v20.learning.run_plan as learning_run_plan
from v20.learning.run_plan import build_learning_run_plan
from v20.learning_orchestrator.run_plan import build_learning_orchestrator_run_plan
from v20.learning_orchestrator.nightly_executor import read_nightly_executor_status, run_nightly_executor_skeleton
from v20.server import app
from v20.validation.suite import run_synthetic_suite
import v20.server as server_module


def _endpoint(path: str, method: str = "GET"):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", "") == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def test_v20_corpus_coverage_plan_tracks_518k_without_mutation() -> None:
    plan = build_corpus_coverage_plan(shard_count=32, batch_size=128)

    assert plan.target_case_count == FULL_CORPUS_TARGET_COUNT
    assert plan.target_case_count == 518_400
    assert plan.shard_count == 32
    assert sum(shard.case_count for shard in plan.shards) == FULL_CORPUS_TARGET_COUNT
    assert plan.runtime_mutation is False
    assert "NO_DESTINY_TRUTH_LABEL" in plan.guardrails


def test_v20_synthetic_suite_and_evolution_plan_are_dry_run_only() -> None:
    suite = run_synthetic_suite(max_cases=1)
    rule_suite = {
        "ok": True,
        "case_count": 4,
        "runtime_mutation": False,
    }
    rule_training = {
        "status": "ready",
        "guardrails": ["FULL_CORPUS_REMAINS_PRIOR_AND_COVERAGE_ONLY"],
        "rule_domain_training": ({"runtime_allowed": True},),
    }
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
    report = _knowledge_rule_validation_report()
    useful_god = _knowledge_rule_validation_report("useful_god")

    assert report["status"] == "active_ready"
    assert report["ok"] is True
    assert report["definition_count"] >= 12
    assert report["synthetic_covered_count"] == report["definition_count"]
    assert report["missing_synthetic_count"] == 0
    assert report["corpus_signal_count"] >= 1
    assert report["runtime_allowed_count"] == report["definition_count"]
    assert "split_by_exact_feature_signature_and_counterexamples" in report["iteration_actions"]
    assert useful_god["synthetic_covered_count"] == useful_god["definition_count"]
    assert all(row["synthetic_state"] == "synthetic_passed" for row in useful_god["definitions"])
    assert "CORPUS_SUPPORT_IS_PRIOR_NOT_RULE_TRUTH" in report["guardrails"]


def test_v20_rule_activation_batches_active_rules_for_iteration() -> None:
    gate = _rule_activation_report()
    summary = _rule_activation_packet_summary()
    split = _rule_subcondition_split_report()
    replay = _rule_replay_eval_report()
    registry = _decision_registry_iteration_report()
    overlay = _knowledge_rule_review_overlay()

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
    assert replay["runtime_activation_count"] == replay["evaluated_packet_count"]
    assert all(row["runtime_allowed"] is True for row in replay["evaluations"])
    assert all(row["next_action"] in {"continue_runtime_replay", "collect_more_runtime_replay"} for row in replay["evaluations"])
    assert "RULE_REPLAY_EVAL_IS_CONTINUOUS_ITERATION" in replay["guardrails"]
    assert registry["status"] == "ready"
    assert registry["decision_record_count"] >= split["subcondition_count"]
    assert registry["runtime_activation_count"] == registry["decision_record_count"]
    assert registry["system_iteration_count"] >= 1
    assert "DECISION_REGISTRY_IS_ITERATION_LEDGER" in registry["guardrails"]
    assert overlay["status"] == "ready"
    assert overlay["validation_status"] == "active_ready"
    assert overlay["runtime_activation_candidate_count"] >= 1
    assert "RUNTIME_USES_LIGHTWEIGHT_BRIDGE" in overlay["guardrails"]
    decision_ids = [row["decision_id"] for row in registry["records"]]
    assert len(decision_ids) == len(set(decision_ids))


def _knowledge_rule_validation_report(domain: str = "") -> dict[str, object]:
    definitions = (
        {"synthetic_state": "synthetic_passed"},
        {"synthetic_state": "synthetic_passed"},
    )
    return {
        "status": "active_ready",
        "ok": True,
        "definition_count": 12 if not domain else 2,
        "synthetic_covered_count": 12 if not domain else 2,
        "missing_synthetic_count": 0,
        "corpus_signal_count": 1,
        "runtime_allowed_count": 12 if not domain else 2,
        "iteration_actions": ("split_by_exact_feature_signature_and_counterexamples",),
        "definitions": definitions,
        "runtime_mutation": False,
        "guardrails": ("CORPUS_SUPPORT_IS_PRIOR_NOT_RULE_TRUTH",),
    }


def _rule_activation_report() -> dict[str, object]:
    return {
        "status": "ready",
        "packet_count": 12,
        "runtime_activation_candidate_count": 12,
        "blocked_count": 0,
        "needs_subcondition_count": 0,
        "subcondition_active_ready_count": 2,
        "lane_counts": {"subcondition_active_ready": 2},
        "runtime_mutation": False,
        "guardrails": ("DECISION_REGISTRY_RECORDS_ITERATION_HISTORY",),
    }


def _rule_activation_packet_summary() -> dict[str, object]:
    return {
        "packet_count": 12,
        "runtime_mutation": False,
        "packets": (
            {"iteration_options": ("activate_subconditions_for_replay_eval",)},
            {"iteration_options": ("continue_runtime_replay",)},
            {"iteration_options": ("continue_runtime_replay",)},
        ),
    }


def _rule_subcondition_split_report() -> dict[str, object]:
    return {
        "status": "ready",
        "packet_count": 2,
        "subcondition_count": 4,
        "quality_status": "active_ready",
        "runtime_mutation": False,
        "packets": ({"runtime_allowed": True}, {"runtime_allowed": True}),
    }


def _rule_replay_eval_report() -> dict[str, object]:
    return {
        "status": "ready",
        "subcondition_active_ready_count": 2,
        "evaluated_packet_count": 2,
        "replay_eval_ready_count": 2,
        "eval_status_counts": {"ready": 2},
        "subcondition_eval_count": 4,
        "portrait_mapping_ok_count": 2,
        "decision_domain_ok_count": 2,
        "runtime_activation_count": 2,
        "runtime_mutation": False,
        "evaluations": (
            {"runtime_allowed": True, "next_action": "continue_runtime_replay"},
            {"runtime_allowed": True, "next_action": "collect_more_runtime_replay"},
        ),
        "guardrails": ("RULE_REPLAY_EVAL_IS_CONTINUOUS_ITERATION",),
    }


def _decision_registry_iteration_report() -> dict[str, object]:
    return {
        "status": "ready",
        "decision_record_count": 4,
        "runtime_activation_count": 4,
        "system_iteration_count": 1,
        "runtime_mutation": False,
        "records": tuple({"decision_id": f"decision-{index}"} for index in range(4)),
        "guardrails": ("DECISION_REGISTRY_IS_ITERATION_LEDGER",),
    }


def _knowledge_rule_review_overlay() -> dict[str, object]:
    return {
        "status": "ready",
        "validation_status": "active_ready",
        "runtime_activation_candidate_count": 1,
        "runtime_mutation": False,
        "guardrails": ("RUNTIME_USES_LIGHTWEIGHT_BRIDGE",),
    }


def test_v20_learning_run_plan_maps_518k_to_structural_artifacts(monkeypatch) -> None:
    monkeypatch.setattr(learning_run_plan, "build_evolution_dry_run_plan", lambda **_: _evolution_plan())

    run_plan = build_learning_run_plan(corpus_plan=build_corpus_coverage_plan(shard_count=16, batch_size=512))

    assert run_plan["status"] == "ready_for_dry_run"
    assert run_plan["target_case_count"] == 518_400
    assert run_plan["shard_count"] == 16
    assert run_plan["estimated_batch_count"] > 0
    assert "corpus_snapshot_manifest" in run_plan["artifact_outputs"]
    assert run_plan["learning_orchestrator"]["status"] == "ready_for_scheduled_run"
    assert run_plan["learning_orchestrator"]["default_job"]["job_key"] == "nightly"
    assert run_plan["learning_orchestrator"]["dataset"]["full_corpus_enabled"] is True
    assert run_plan["learning_orchestrator"]["completion"]["learning_orchestrator_v1"] == 100
    assert "NO_DESTINY_TRUTH_LABELS" in run_plan["guardrails"]
    assert all(stage["runtime_mutation"] is False for stage in run_plan["stages"])


def _evolution_plan() -> dict[str, object]:
    return {
        "status": "ready_for_dry_run",
        "allowed_algorithm_tracks": ("learning_to_rank_question_order",),
        "deferred_algorithm_tracks": ("neural_conclusion_generation",),
        "blocked_actions": ("destiny_truth_label",),
        "runtime_mutation": False,
    }


def test_v20_learning_orchestrator_models_nightly_518k_without_llm_full_run() -> None:
    plan = build_learning_orchestrator_run_plan("nightly")

    assert plan["status"] == "ready_for_scheduled_run"
    assert plan["job"]["job_key"] == "nightly"
    assert plan["job"]["target_case_count"] == 518_400
    assert plan["job"]["llm_eval_sample_limit"] == 0
    assert plan["dataset"]["deterministic_case_count"] == 518_400
    assert plan["dataset"]["full_corpus_enabled"] is True
    assert plan["sharding"]["shard_count"] == 128
    assert plan["sharding"]["batch_size"] == 512
    assert plan["activation_policy"]["pointer_write"] == "explicit_after_replay_or_admin_activation"
    assert "question_dag_policy" in plan["candidate_policy_targets"]
    assert all(stage["runtime_mutation"] is False for stage in plan["stages"])
    assert "LLM_EVAL_SAMPLED_NOT_FULL_CORPUS" in plan["guardrails"]


def test_v20_learning_orchestrator_weekly_bounds_llm_eval_sample() -> None:
    plan = build_learning_orchestrator_run_plan("weekly")

    assert plan["job"]["job_key"] == "weekly"
    assert plan["job"]["llm_eval_sample_limit"] == 512
    assert "sampled_llm_eval" in [stage["stage_key"] for stage in plan["stages"]]
    assert plan["activation_policy"]["llm_training"] == "disabled"


def test_v20_corpus_validation_learning_endpoints_are_wired(monkeypatch) -> None:
    _stub_learning_endpoint_dependencies(monkeypatch)

    corpus = _endpoint("/api/v20/corpus/coverage")()
    precompute = _endpoint("/api/v20/corpus/full-precompute/manifest")()
    preview = _endpoint("/api/v20/corpus/full-precompute/preview")(start=0, limit=1)
    status = _endpoint("/api/v20/corpus/full-precompute/status")()
    artifact_status = _endpoint("/api/v20/corpus/artifacts/status")()
    artifact_summary = _endpoint("/api/v20/corpus/artifacts/coverage-summary")()
    artifact_clusters = _endpoint("/api/v20/corpus/artifacts/cluster-model")()
    artifact_training = _endpoint("/api/v20/corpus/artifacts/training")()
    suite = _endpoint("/api/v20/validation/synthetic-suite")()
    rule_suite = _endpoint("/api/v20/validation/rule-synthetic-suite")()
    knowledge_rule_validation = _endpoint("/api/v20/validation/knowledge-rule-library")()
    knowledge_rule_overlay = _endpoint("/api/v20/knowledge/rule-review-overlay")()
    activation = _endpoint("/api/v20/learning/rule-activation")()
    activation_packets = _endpoint("/api/v20/learning/rule-activation-packets")()
    subcondition_split = _endpoint("/api/v20/learning/rule-subcondition-split")(per_rule=3)
    replay_eval = _endpoint("/api/v20/learning/rule-replay-eval")(per_rule=3)
    decision_registry_iteration = _endpoint("/api/v20/learning/decision-registry-iteration")(per_rule=3)
    rule_training = _endpoint("/api/v20/learning/rule-synthetic-training")()
    evolution = _endpoint("/api/v20/learning/evolution-plan")()
    run_plan = _endpoint("/api/v20/learning/run-plan")()
    orchestrator_plan = _endpoint("/api/v20/learning/orchestrator/run-plan")(job="nightly")
    nightly_executor = _endpoint("/api/v20/learning/orchestrator/nightly-executor/status")()

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
    assert activation["runtime_activation_candidate_count"] == activation["packet_count"]
    assert activation_packets["runtime_mutation"] is False
    assert activation_packets["packet_count"] == activation["packet_count"]
    assert subcondition_split["runtime_mutation"] is False
    assert subcondition_split["packet_count"] == activation["subcondition_active_ready_count"]
    assert replay_eval["runtime_mutation"] is False
    assert replay_eval["status"] == "ready"
    assert replay_eval["replay_eval_ready_count"] == replay_eval["evaluated_packet_count"]
    assert replay_eval["runtime_activation_count"] == replay_eval["evaluated_packet_count"]
    assert decision_registry_iteration["runtime_mutation"] is False
    assert decision_registry_iteration["decision_record_count"] >= subcondition_split["subcondition_count"]
    assert decision_registry_iteration["runtime_activation_count"] == decision_registry_iteration["decision_record_count"]
    assert rule_training["status"] == "ready"
    assert rule_training["runtime_mutation"] is False
    assert evolution["status"] == "ready_for_dry_run"
    assert evolution["runtime_mutation"] is False
    assert run_plan["target_case_count"] == 518_400
    assert run_plan["runtime_mutation"] is False
    assert orchestrator_plan["job"]["job_key"] == "nightly"
    assert orchestrator_plan["dataset"]["deterministic_case_count"] == 518_400
    assert orchestrator_plan["runtime_mutation"] is False
    assert nightly_executor["runtime_mutation"] is False
    assert "NO_FULL_518K_STARTED_BY_STATUS" in nightly_executor["guardrails"] or "STATUS_READ_ONLY" in nightly_executor["guardrails"]


def _stub_learning_endpoint_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(server_module, "run_synthetic_suite", lambda: {"ok": True, "runtime_mutation": False})
    monkeypatch.setattr(server_module, "run_rule_synthetic_suite", lambda: {"ok": True, "runtime_mutation": False})
    monkeypatch.setattr(server_module, "build_knowledge_rule_validation_report", lambda **_: _knowledge_rule_validation_report())
    monkeypatch.setattr(server_module, "build_knowledge_rule_review_overlay", lambda: _knowledge_rule_review_overlay())
    monkeypatch.setattr(server_module, "build_rule_activation_report", lambda **_: _rule_activation_report())
    monkeypatch.setattr(server_module, "build_rule_activation_packet_summary", lambda **_: _rule_activation_packet_summary())
    monkeypatch.setattr(server_module, "build_rule_subcondition_split_report", lambda **_: _rule_subcondition_split_report())
    monkeypatch.setattr(server_module, "build_rule_replay_eval_report", lambda **_: _rule_replay_eval_report())
    monkeypatch.setattr(server_module, "build_decision_registry_iteration_report", lambda **_: _decision_registry_iteration_report())
    monkeypatch.setattr(
        server_module,
        "build_rule_synthetic_training_report",
        lambda: {"status": "ready", "runtime_mutation": False},
    )
    monkeypatch.setattr(server_module, "build_evolution_dry_run_plan", lambda **_: _evolution_plan())
    monkeypatch.setattr(
        server_module,
        "build_learning_run_plan",
        lambda: {"target_case_count": 518_400, "runtime_mutation": False},
    )
