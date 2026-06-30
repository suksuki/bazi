from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.contracts.output import AcceptanceStatus
from v40.engines import build_native_bazi_runtime
from v40.expression import (
    OllamaExpressionConfig,
    OllamaExpressionError,
    accept_expression_result,
    build_expression_task_from_runtime,
    build_ollama_expression_prompt,
    render_ollama_expression_result,
)
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _runtime():
    seed = load_synthetic_seeds(SEED_PATH)[0]
    return build_native_bazi_runtime(
        request_id="request.phase17.ollama.001",
        reading_id="reading.phase17.ollama.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
    )


def _config() -> OllamaExpressionConfig:
    return OllamaExpressionConfig(
        provider="ollama_native",
        host="127.0.0.1",
        port=11434,
        model="gemma4:latest",
        timeout_seconds=3.0,
        temperature=0.2,
        max_tokens=256,
        enabled=True,
        execute=True,
    )


def test_ollama_prompt_preserves_expression_only_boundary() -> None:
    runtime = _runtime()
    task = build_expression_task_from_runtime(task_id="task.phase17.prompt", runtime=runtime)

    prompt = build_ollama_expression_prompt(task=task, runtime=runtime)

    assert "只负责把已给出的结论和建议改写成自然中文" in prompt
    assert "严禁改变结论" in prompt
    assert "必须至少逐字保留一条" in prompt
    assert "禁止表达的断言" in prompt
    assert runtime.verdicts[0].allowed_assertions[0] in prompt


def test_ollama_provider_result_passes_acceptance_with_fake_transport() -> None:
    runtime = _runtime()
    task = build_expression_task_from_runtime(task_id="task.phase17.ollama", runtime=runtime)
    captured: dict[str, object] = {}

    def fake_transport(url: str, payload: dict[str, object], timeout_seconds: float) -> dict[str, object]:
        captured["url"] = url
        captured["payload"] = payload
        captured["timeout_seconds"] = timeout_seconds
        return {
            "model": "gemma4:latest",
            "message": {
                "role": "assistant",
                "content": f"结论\n- {runtime.verdicts[0].allowed_assertions[0]}\n建议\n- {runtime.advice_plans[0].action_points[0]}",
                "thinking": "checked expression boundary",
            },
        }

    result = render_ollama_expression_result(
        result_id="result.phase17.ollama",
        task=task,
        runtime=runtime,
        config=_config(),
        transport=fake_transport,
    )
    acceptance = accept_expression_result(
        result_id="acceptance.phase17.ollama",
        task=task,
        result=result,
        runtime=runtime,
    )

    assert str(captured["url"]).endswith("/api/chat")
    assert captured["payload"]["model"] == "gemma4:latest"
    assert captured["payload"]["think"] is True
    assert captured["payload"]["options"]["num_predict"] >= 2400
    assert captured["timeout_seconds"] >= 180
    assert captured["payload"]["messages"][0]["role"] == "system"
    assert captured["payload"]["messages"][1]["role"] == "user"
    assert result.provider == "ollama_native"
    assert result.raw_thinking == "checked expression boundary"
    assert acceptance.status == AcceptanceStatus.ACCEPTED


def test_ollama_provider_extracts_json_text_and_embedded_thinking_from_chat_content() -> None:
    runtime = _runtime()
    task = build_expression_task_from_runtime(task_id="task.phase17.ollama.json", runtime=runtime)

    def fake_transport(_url: str, _payload: dict[str, object], _timeout_seconds: float) -> dict[str, object]:
        return {
            "model": "gemma4:latest",
            "message": {
                "role": "assistant",
                "content": (
                    "<think>内部核对允许断言和建议边界。</think>"
                    '{"text": "结论\\n- '
                    + runtime.verdicts[0].allowed_assertions[0]
                    + "\\n建议\\n- "
                    + runtime.advice_plans[0].action_points[0]
                    + '"}'
                ),
            },
        }

    result = render_ollama_expression_result(
        result_id="result.phase17.ollama.json",
        task=task,
        runtime=runtime,
        config=_config(),
        transport=fake_transport,
    )

    assert result.text.startswith("结论")
    assert result.raw_thinking == "内部核对允许断言和建议边界。"


def test_ollama_provider_reports_thinking_token_budget_exhaustion() -> None:
    runtime = _runtime()
    task = build_expression_task_from_runtime(task_id="task.phase17.ollama.empty", runtime=runtime)

    with pytest.raises(OllamaExpressionError, match="thinking token budget"):
        render_ollama_expression_result(
            result_id="result.phase17.ollama.empty",
            task=task,
            runtime=runtime,
            config=_config(),
            transport=lambda _url, _payload, _timeout: {"model": "gemma4:latest", "message": {"content": ""}, "done_reason": "length"},
        )


def test_ollama_provider_disabled_does_not_fallback() -> None:
    runtime = _runtime()
    task = build_expression_task_from_runtime(task_id="task.phase17.disabled", runtime=runtime)
    disabled = OllamaExpressionConfig(
        provider="ollama_native",
        host="127.0.0.1",
        port=11434,
        model="gemma4:latest",
        timeout_seconds=3.0,
        temperature=0.2,
        max_tokens=256,
        enabled=False,
        execute=False,
    )

    with pytest.raises(OllamaExpressionError, match="disabled"):
        render_ollama_expression_result(
            result_id="result.phase17.disabled",
            task=task,
            runtime=runtime,
            config=disabled,
            transport=lambda _url, _payload, _timeout: {"response": "should not run"},
        )


def test_ollama_provider_status_api_reports_non_secret_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("V40_LLM_HOST", "192.168.0.19")
    monkeypatch.setenv("V40_LLM_PORT", "11434")
    monkeypatch.setenv("V40_LLM_MODEL", "gemma4:latest")
    client = TestClient(create_app())

    response = client.get(f"{API_PREFIX}/expression/provider/ollama")

    assert response.status_code == 200
    body = response.json()
    assert body["base_url"] == "http://192.168.0.19:11434"
    assert body["model"] == "gemma4:latest"
    assert body["effective_thinking_max_tokens"] >= 2400
    assert body["effective_thinking_timeout_seconds"] >= 180
    assert "password" not in str(body).lower()
    assert body["writes_v30_state"] is False
