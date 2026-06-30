from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.admin.app import ADMIN_PREFIX, create_admin_app
from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.contracts.evaluation import EvaluationCaseSpec, ExpectedVerdict, ForbiddenAssertion
from v40.contracts.output import AcceptanceStatus, LLMExpressionResult
from v40.engines import build_native_bazi_runtime
from v40.evaluation import evaluate_runtime_against_case
from v40.expression import (
    OllamaExpressionConfig,
    accept_expression_result,
    build_expression_telemetry,
    build_expression_task_from_runtime,
    list_ollama_models,
)
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _runtime():
    seed = load_synthetic_seeds(SEED_PATH)[0]
    return build_native_bazi_runtime(
        request_id="request.phase18.telemetry.001",
        reading_id="reading.phase18.telemetry.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
    )


def _case() -> EvaluationCaseSpec:
    return EvaluationCaseSpec(
        case_id="case.phase18.telemetry.001",
        topic=Topic.CAREER,
        expected_verdicts=[ExpectedVerdict(topic=Topic.CAREER, expected_keywords=["事业"])],
        forbidden_assertions=[ForbiddenAssertion(text="保证升职发财", reason="overclaim")],
    )


def test_ollama_model_discovery_reads_tags_without_mutation() -> None:
    config = OllamaExpressionConfig(
        provider="ollama_native",
        host="192.168.0.7",
        port=11434,
        model="gemma4:latest",
        timeout_seconds=3.0,
        temperature=0.2,
        max_tokens=256,
        enabled=True,
        execute=True,
    )

    discovery = list_ollama_models(
        config=config,
        transport=lambda url, _payload, timeout: {
            "models": [
                {"name": "gemma4:latest"},
                {"model": "qwen3:14b"},
            ],
            "url": url,
            "timeout": timeout,
        },
    )

    assert discovery["models"] == ["gemma4:latest", "qwen3:14b"]
    assert discovery["configured_model_available"] is True
    assert discovery["writes_v30_state"] is False
    assert discovery["writes_v40_production"] is False


def test_model_discovery_api_and_admin_surface(monkeypatch) -> None:
    def fake_discovery():
        return {
            "version": "v40.ollama_model_discovery.v1",
            "provider": "ollama_native",
            "base_url": "http://127.0.0.1:11434",
            "configured_model": "gemma4:latest",
            "model_count": 1,
            "models": ["gemma4:latest"],
            "configured_model_available": True,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "test",
        }

    monkeypatch.setattr("v40.api.app.list_ollama_models", fake_discovery)
    runtime_client = TestClient(create_app())
    runtime_response = runtime_client.get(f"{API_PREFIX}/expression/provider/ollama/models")

    assert runtime_response.status_code == 200
    assert runtime_response.json()["models"] == ["gemma4:latest"]

    admin_client = TestClient(create_admin_app())
    page = admin_client.get(ADMIN_PREFIX)

    assert page.status_code == 200
    assert "/admin/v40/api/llm" in page.text
    assert "/admin/v40/api/llm-models" in page.text
    assert "<h2>LLM</h2>" in page.text


def test_expression_telemetry_enters_evaluation_metrics_and_release_gate() -> None:
    runtime = _runtime()
    task = build_expression_task_from_runtime(task_id="task.phase18.telemetry", runtime=runtime)
    result = LLMExpressionResult(
        result_id="result.phase18.telemetry",
        task_id=task.task_id,
        reading_id=runtime.reading_id,
        text=f"结论\n- {runtime.verdicts[0].allowed_assertions[0]}",
        raw_thinking="checked evidence and advice boundary",
        provider="ollama_native",
        model="gemma4:latest",
    )
    acceptance = accept_expression_result(
        result_id="acceptance.phase18.telemetry",
        task=task,
        result=result,
        runtime=runtime,
    )
    telemetry = build_expression_telemetry(
        telemetry_id="telemetry.phase18.accepted",
        task=task,
        result=result,
        acceptance=acceptance,
        execution_mode="ollama",
    )

    run = evaluate_runtime_against_case(
        run_id="run.phase18.telemetry.accepted",
        case_spec=_case(),
        runtime=runtime,
        candidate_version="v40-phase18",
        expression_telemetry=telemetry,
    )

    assert telemetry.acceptance_status == AcceptanceStatus.ACCEPTED
    assert run.expression_telemetry is not None
    assert run.metric_summary.expression_acceptance_rate == 1.0
    assert run.metric_summary.expression_thinking_trace_rate == 1.0
    assert run.release_gate is not None
    assert run.release_gate.llm_boundary_gate_passed is True


def test_rejected_expression_telemetry_blocks_llm_gate() -> None:
    runtime = _runtime()
    task = build_expression_task_from_runtime(task_id="task.phase18.telemetry.reject", runtime=runtime)
    result = LLMExpressionResult(
        result_id="result.phase18.telemetry.reject",
        task_id=task.task_id,
        reading_id=runtime.reading_id,
        text="DecisionEngine 判断你保证升职发财，policy_key 已命中。",
        provider="ollama_native",
        model="gemma4:latest",
    )
    acceptance = accept_expression_result(
        result_id="acceptance.phase18.telemetry.reject",
        task=task,
        result=result,
        runtime=runtime,
    )
    telemetry = build_expression_telemetry(
        telemetry_id="telemetry.phase18.reject",
        task=task,
        result=result,
        acceptance=acceptance,
        execution_mode="ollama",
    )

    run = evaluate_runtime_against_case(
        run_id="run.phase18.telemetry.reject",
        case_spec=_case(),
        runtime=runtime,
        candidate_version="v40-phase18",
        expression_telemetry=telemetry,
    )

    assert run.metric_summary.expression_acceptance_rate == 0.0
    assert "expression_acceptance_not_accepted" in run.metric_summary.failed_reasons
    assert run.release_gate is not None
    assert run.release_gate.llm_boundary_gate_passed is False
