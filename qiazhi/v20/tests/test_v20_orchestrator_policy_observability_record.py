from __future__ import annotations

from v20.interaction.orchestrator_policy_observability_record import (
    analyze_policy_observability,
    record_policy_observability,
)
from v20.learning.orchestrator_policy_observability_training import (
    build_policy_observability_training_report,
    read_policy_observability_training_artifact,
    write_policy_observability_training_artifact,
)
from v20.orchestrator.runtime_policy import write_runtime_policy_activate_latest_candidate, write_runtime_policy_rollback
from v20.storage.local_jsonl import LocalJsonlStore
from v20.storage.postgres_ledger_import import build_ledger_postgres_import_plan


def _observation(status: str = "candidate_consumed") -> dict[str, object]:
    return {
        "version": "v20.orchestrator_policy_observability.v1",
        "status": status,
        "active_policy_version": "v20.orchestrator_policy.candidate.test" if status == "candidate_consumed" else "v20.orchestrator_policy.baseline.v1",
        "candidate_policy_version": "v20.orchestrator_policy.candidate.test" if status == "candidate_consumed" else "",
        "rollback_policy_version": "v20.orchestrator_policy.baseline.v1",
        "runtime_applied": status == "candidate_consumed",
        "fallback_active": status != "candidate_consumed",
        "consumer_count": 2,
        "applied_consumer_count": 2 if status == "candidate_consumed" else 0,
        "consumers": (
            {
                "module_key": "mainline_arbitration",
                "status": "applied" if status == "candidate_consumed" else "not_applied",
                "active_policy_version": "v20.orchestrator_policy.candidate.test",
                "applied_adjustment_count": 1 if status == "candidate_consumed" else 0,
                "domain_boost": 0,
                "runtime_mutation": False,
            },
            {
                "module_key": "question_mainline_focus",
                "status": "applied" if status == "candidate_consumed" else "not_applied",
                "active_policy_version": "v20.orchestrator_policy.candidate.test",
                "applied_adjustment_count": 0,
                "domain_boost": 0.04 if status == "candidate_consumed" else 0,
                "runtime_mutation": False,
            },
        ),
        "runtime_mutation": False,
    }


def test_v20_policy_observability_analysis_redacts_to_persistable_fields() -> None:
    analysis = analyze_policy_observability(
        input_id="policy.observe.1",
        source_role="admin",
        policy_observability=_observation(),
    )

    assert analysis["version"] == "v20.orchestrator_policy_observability_analysis.v1"
    assert analysis["active_policy_version"] == "v20.orchestrator_policy.candidate.test"
    assert analysis["applied_consumer_count"] == 2
    assert analysis["runtime_mutation"] is False
    assert "NO_USER_TEXT_PERSISTED" in analysis["guardrails"]


def test_v20_policy_observability_record_and_training_report(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    store = LocalJsonlStore(runtime_dir=tmp_path)

    recorded = record_policy_observability(
        input_id="policy.observe.1",
        source_role="system",
        policy_observability=_observation(),
        store=store,
    )
    record_policy_observability(
        input_id="policy.observe.2",
        source_role="system",
        policy_observability=_observation("baseline_active"),
        store=store,
    )
    report = build_policy_observability_training_report(store=store)

    assert recorded["version"] == "v20.orchestrator_policy_observability_record_result.v1"
    assert recorded["runtime_mutation"] is True
    assert report["version"] == "v20.orchestrator_policy_observability_training_report.v1"
    assert report["status"] == "ready"
    assert report["observation_count"] == 2
    assert report["candidate_consumed_ratio"] == 0.5
    assert report["fallback_ratio"] == 0.5
    assert report["version_summaries"]
    assert report["trend_summary"]["version"] == "v20.orchestrator_policy_observability_trend_summary.v1"
    assert report["trend_summary"]["status"] == "fallback_pressure"
    assert report["strategy_recommendations"]
    assert report["version_switch_timeline"]
    assert report["version_switch_timeline"][0]["event_type"] == "latest_observed_active_policy"
    assert {row["recommendation_key"] for row in report["strategy_recommendations"]} >= {
        "inspect_fallback_pressure",
    }
    assert "TREND_SUMMARY_IS_READ_ONLY" in report["guardrails"]
    assert "AUTO_RECOMMENDATION_DOES_NOT_BLOCK_FAST_TRACK" in report["guardrails"]
    assert {row["active_policy_version"] for row in report["version_summaries"]} == {
        "v20.orchestrator_policy.baseline.v1",
        "v20.orchestrator_policy.candidate.test",
    }
    assert {row["module_key"] for row in report["consumer_summaries"]} == {"mainline_arbitration", "question_mainline_focus"}

    import_plan = build_ledger_postgres_import_plan(
        ledger_name="orchestrator_policy_observability_ledger",
        store=store,
    )
    assert import_plan["status"] == "dry_run"
    assert import_plan["record_count"] == 2


def test_v20_policy_observability_training_builds_version_switch_timeline(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    store = LocalJsonlStore(runtime_dir=tmp_path)
    artifact_dir = tmp_path / "training" / "orchestrator_policy_versions"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "latest.json").write_text(
        """
        {
          "version": "v20.orchestrator_policy_version_candidate.v1",
          "status": "ready_for_replay",
          "candidate_policy_version": "v20.orchestrator_policy.candidate.timeline",
          "runtime_allowed": true,
          "candidate_count": 1,
          "policy_payload": {"question_focus_policy": []}
        }
        """,
        encoding="utf-8",
    )
    write_runtime_policy_rollback(source_role="admin", reason="timeline rollback", store=store)
    write_runtime_policy_activate_latest_candidate(source_role="admin", reason="timeline restore", store=store)

    report = build_policy_observability_training_report(store=store)

    assert report["version_switch_timeline"]
    assert {row["event_type"] for row in report["version_switch_timeline"]} >= {
        "rollback_to_baseline",
        "activate_latest_candidate",
        "current_active_pointer",
    }
    assert report["version_switch_timeline"][0]["runtime_mutation"] is False
    assert "VERSION_SWITCH_TIMELINE_IS_READ_ONLY" in report["guardrails"]


def test_v20_policy_observability_training_artifact(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    store = LocalJsonlStore(runtime_dir=tmp_path)
    record_policy_observability(
        input_id="policy.observe.artifact",
        source_role="system",
        policy_observability=_observation(),
        store=store,
    )

    written = write_policy_observability_training_artifact(store=store)
    status = read_policy_observability_training_artifact()

    assert written["status"] == "written"
    assert written["observation_count"] == 1
    assert status["version"] == "v20.orchestrator_policy_observability_training_report.v1"
    assert status["observation_count"] == 1
