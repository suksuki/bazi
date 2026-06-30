from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.contracts.output import AcceptanceStatus, LLMExpressionResult
from v40.engines import build_native_bazi_runtime
from v40.expression import accept_expression_result, build_expression_task_from_runtime, render_local_expression_result
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def test_local_expression_result_is_accepted_without_verdict_authority() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    runtime = build_native_bazi_runtime(
        request_id="request.phase16.expression.001",
        reading_id="reading.phase16.expression.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
    )
    task = build_expression_task_from_runtime(
        task_id="task.phase16.expression.001",
        runtime=runtime,
    )
    result = render_local_expression_result(
        result_id="result.phase16.expression.001",
        task=task,
        runtime=runtime,
    )
    acceptance = accept_expression_result(
        result_id="acceptance.phase16.expression.001",
        task=task,
        result=result,
        runtime=runtime,
    )

    assert task.can_change_verdict is False
    assert task.can_create_chart_facts is False
    assert result.changed_verdict is False
    assert result.created_chart_facts is False
    assert acceptance.status == AcceptanceStatus.ACCEPTED
    assert acceptance.accepted_text
    assert acceptance.verdict_mutation_detected is False


def test_expression_acceptance_rejects_overclaim_and_internal_leakage() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    runtime = build_native_bazi_runtime(
        request_id="request.phase16.expression.reject",
        reading_id="reading.phase16.expression.reject",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
    )
    task = build_expression_task_from_runtime(
        task_id="task.phase16.expression.reject",
        runtime=runtime,
    )
    result = LLMExpressionResult(
        result_id="result.phase16.expression.reject",
        task_id=task.task_id,
        reading_id=runtime.reading_id,
        text="DecisionEngine 判断你一定发财，policy_key 已命中。",
        provider="test_provider",
        model="bad-output",
    )
    acceptance = accept_expression_result(
        result_id="acceptance.phase16.expression.reject",
        task=task,
        result=result,
        runtime=runtime,
    )

    assert acceptance.status == AcceptanceStatus.HARD_REJECT
    assert "DecisionEngine" in acceptance.leakage_hits
    assert "一定发财" in acceptance.overclaim_hits
    assert acceptance.accepted_text == ""


def test_expression_acceptance_allows_semantic_rewrite_that_preserves_core_assertion() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    runtime = build_native_bazi_runtime(
        request_id="request.phase16.expression.semantic",
        reading_id="reading.phase16.expression.semantic",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
    )
    task = build_expression_task_from_runtime(
        task_id="task.phase16.expression.semantic",
        runtime=runtime,
    )
    result = LLMExpressionResult(
        result_id="result.phase16.expression.semantic",
        task_id=task.task_id,
        reading_id=runtime.reading_id,
        text=(
            "结论\n"
            "- 在事业发展上，核心线索更适合从木、火、土这三种资源和输出方式切入，"
            "先稳固主线，再判断突破窗口。\n"
            "建议\n"
            "- 优先考虑能承接责任、形成专业资质或稳定交付的方向。"
        ),
        provider="test_provider",
        model="semantic-output",
    )

    acceptance = accept_expression_result(
        result_id="acceptance.phase16.expression.semantic",
        task=task,
        result=result,
        runtime=runtime,
    )

    assert acceptance.status == AcceptanceStatus.ACCEPTED
    assert acceptance.verdict_mutation_detected is False


def test_expression_from_runtime_api_returns_task_result_and_acceptance() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[1]
    runtime = build_native_bazi_runtime(
        request_id="request.phase16.api.001",
        reading_id="reading.phase16.api.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.WEALTH,
    )
    client = TestClient(create_app())

    response = client.post(
        f"{API_PREFIX}/expression/from-runtime",
        json={
            "task_id": "task.phase16.api.001",
            "result_id": "result.phase16.api.001",
            "acceptance_id": "acceptance.phase16.api.001",
            "runtime": runtime.model_dump(mode="json"),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["task"]["can_change_verdict"] is False
    assert body["result"]["provider"] == "local_expression_adapter"
    assert body["acceptance"]["status"] == "accepted"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
