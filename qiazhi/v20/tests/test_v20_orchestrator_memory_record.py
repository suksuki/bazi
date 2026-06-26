from __future__ import annotations

from pathlib import Path

from v20.interaction.orchestrator_memory_record import (
    analyze_orchestrator_memory_signal,
    record_orchestrator_memory_signal,
)
from v20.learning.orchestrator_memory_training import build_orchestrator_memory_training_report
from v20.storage.local_jsonl import LocalJsonlStore
from v20.storage.postgres_ledger_import import build_ledger_postgres_import_plan
from v20.tests.support_paths import read_v20_text


def test_v20_orchestrator_memory_record_is_append_only_and_training_readable(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    result = record_orchestrator_memory_signal(
        input_id="memory.record.case",
        source_role="analyst",
        brain_memory_signal=_memory_signal(),
        store=store,
    )
    report = build_orchestrator_memory_training_report(store=store)

    assert result["version"] == "v20.orchestrator_memory_record_result.v1"
    assert result["storage"]["ledger_name"] == "orchestrator_memory_ledger"
    assert result["runtime_mutation"] is True
    assert result["analysis"]["runtime_mutation"] is False
    assert "NO_RAW_USER_TEXT_PERSISTED" in result["analysis"]["guardrails"]
    assert report["memory_signal_count"] == 1
    assert report["compiled_signal_count"] == 1


def test_v20_orchestrator_memory_record_rejects_raw_text_markers() -> None:
    bad = _memory_signal()
    bad["user_text"] = "raw text should not be persisted"

    try:
        analyze_orchestrator_memory_signal(
            input_id="memory.bad",
            source_role="analyst",
            brain_memory_signal=bad,
        )
    except ValueError as exc:
        assert "raw text" in str(exc)
    else:
        raise AssertionError("raw text marker should be rejected")


def test_v20_orchestrator_memory_ledger_can_build_postgres_dry_run_plan(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    record_orchestrator_memory_signal(
        input_id="memory.postgres.case",
        source_role="admin",
        brain_memory_signal=_memory_signal(),
        store=store,
    )

    plan = build_ledger_postgres_import_plan(
        ledger_name="orchestrator_memory_ledger",
        store=store,
        database_url="",
    )
    blocked = build_ledger_postgres_import_plan(
        ledger_name="orchestrator_memory_ledger",
        store=store,
        database_url="",
        apply=True,
    )

    assert plan["status"] == "dry_run"
    assert plan["record_count"] == 1
    assert plan["target_table"] == "v20_feedback_ledger"
    assert plan["runtime_mutation"] is False
    assert blocked["status"] == "blocked_missing_V20_DATABASE_URL"


def test_v20_orchestrator_memory_record_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/orchestrator/memory/analyze" in server_text
    assert "/api/v20/orchestrator/memory/record" in server_text
    assert "record_orchestrator_memory_signal" in server_text


def _memory_signal() -> dict[str, object]:
    return {
        "version": "v20.orchestrator_brain_memory_signal.v1",
        "status": "active",
        "memory_key": "brain.memory.test",
        "primary_mainline_key": "mainline.career.guan_shang_yin",
        "primary_title": "伤官见官",
        "primary_domain": "career",
        "selected_question_key": "q_career_structure",
        "selected_question_domain": "career",
        "question_focus_status": "already_aligned",
        "coordination_status": "需复核",
        "coordination_flags": ["mainline_quality_review"],
        "signal_count": 1,
        "signals": [
            {
                "signal_key": "brain.practitioner.test",
                "signal_type": "practitioner_structured_choice",
                "domain": "career",
                "target": "orchestrator.mainline_arbitration_memory",
                "direction": "accept_primary",
                "strength": 0.9,
                "allowed_use": "offline_orchestrator_memory_training",
                "runtime_rule_mutation": False,
            }
        ],
        "runtime_mutation": False,
    }
