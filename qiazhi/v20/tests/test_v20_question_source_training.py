from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars
from v20.interaction.question_source_record import (
    analyze_question_source_ranking_report,
    record_question_source_ranking_report,
)
from v20.learning.question_source_training import build_question_source_training_report
from v20.storage.local_jsonl import LocalJsonlStore


def test_v20_question_source_ranking_report_can_be_recorded_without_runtime_mutation(tmp_path) -> None:
    runtime = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="question.source.record")
    report = runtime["question_source_ranking_report"]
    store = LocalJsonlStore(runtime_dir=tmp_path)

    analysis = analyze_question_source_ranking_report(
        input_id="question.source.record",
        source_role="analyst",
        question_source_ranking_report=report,
    )
    recorded = record_question_source_ranking_report(
        input_id="question.source.record",
        source_role="analyst",
        question_source_ranking_report=report,
        store=store,
    )

    assert analysis["version"] == "v20.question_source_ranking_analysis.v1"
    assert analysis["runtime_mutation"] is False
    assert analysis["question_count"] == len(runtime["questions"])
    assert recorded["version"] == "v20.question_source_ranking_record_result.v1"
    assert recorded["runtime_mutation"] is True
    assert recorded["storage"]["ledger_name"] == "question_source_ranking_ledger"


def test_v20_question_source_training_aggregates_recorded_reports(tmp_path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    runtime = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="question.source.training")
    for index in range(3):
        record_question_source_ranking_report(
            input_id=f"question.source.training.{index}",
            source_role="analyst",
            question_source_ranking_report=runtime["question_source_ranking_report"],
            store=store,
        )

    training = build_question_source_training_report(store=store)

    assert training["version"] == "v20.question_source_training_report.v1"
    assert training["status"] == "ready"
    assert training["report_count"] == 3
    assert training["compiled_source_row_count"] >= len(runtime["questions"])
    assert training["source_summaries"]
    assert any(row["target"] == "question_source_graph_quality_policy" for row in training["training_proposals"])
    assert "NO_RUNTIME_QUESTION_ORDER_MUTATION" in training["guardrails"]
