from __future__ import annotations

import json
import urllib.error

import pytest

from core.mingli_agent.contracts import BirthIntakeDraft
from core.mingli_agent.reasoner import (
    OllamaCognitiveModel,
    _extract_completed_json_string,
    _extract_first_completed_json_array_string,
)


class _Response:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class _StreamingResponse:
    def __init__(self, payloads: list[dict]):
        self.payloads = payloads

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def __iter__(self):
        return iter(
            [json.dumps(payload).encode("utf-8") + b"\n" for payload in self.payloads]
        )


def _model() -> OllamaCognitiveModel:
    return OllamaCognitiveModel(base_url="http://ollama.invalid", model="test-model", timeout_seconds=1)


def test_transport_failure_is_not_replayed_as_an_expensive_schema_retry(monkeypatch):
    monkeypatch.setenv("V50_MINGLI_SCHEMA_ATTEMPTS", "2")
    calls = 0

    def fail(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise urllib.error.URLError("offline")

    monkeypatch.setattr("core.mingli_agent.model_client.urllib.request.urlopen", fail)

    with pytest.raises(ValueError, match="model_generation_failed"):
        _model().generate(prompt="extract", schema=BirthIntakeDraft)

    assert calls == 1


def test_invalid_schema_is_not_replayed_as_a_second_expensive_model_call(monkeypatch):
    monkeypatch.setenv("V50_MINGLI_SCHEMA_ATTEMPTS", "2")
    responses = iter([
        _Response({"response": '{"gender":"unsupported"}'}),
    ])
    calls = 0

    def respond(*args, **kwargs):
        nonlocal calls
        calls += 1
        return next(responses)

    monkeypatch.setattr("core.mingli_agent.model_client.urllib.request.urlopen", respond)

    model = _model()
    with pytest.raises(ValueError, match="model_generation_failed"):
        model.generate(prompt="extract", schema=BirthIntakeDraft)

    assert calls == 1
    assert model.last_metrics["schema_attempts"] == 1


def test_streaming_transport_emits_text_without_a_second_model_call(monkeypatch):
    raw = json.dumps({
        "name": "测试档案",
        "gender": "male",
        "calendar_type": "solar",
        "birth_date": "1987-05-12",
        "birth_time": "18:00",
        "birth_location": "上海",
        "timezone": "Asia/Shanghai",
        "time_precision": "exact",
        "ready_for_confirmation": True,
    }, ensure_ascii=False)
    split = len(raw) // 2
    response = _StreamingResponse([
        {"response": raw[:split], "done": False},
        {
            "response": raw[split:],
            "done": True,
            "total_duration": 1_000_000,
            "eval_count": 20,
        },
    ])
    requests = []

    def respond(request, *args, **kwargs):
        requests.append(json.loads(request.data.decode("utf-8")))
        return response

    monkeypatch.setattr("core.mingli_agent.model_client.urllib.request.urlopen", respond)
    chunks: list[str] = []
    result = _model().generate(
        prompt="extract",
        schema=BirthIntakeDraft,
        on_text_chunk=chunks.append,
    )

    assert result.name == "测试档案"
    assert "".join(chunks) == raw
    assert len(requests) == 1
    assert requests[0]["stream"] is True


def test_partial_json_string_waits_for_a_complete_escaped_value() -> None:
    partial = '{"first_look":"先看\\"巳酉丑'
    assert _extract_completed_json_string(partial, key="first_look") is None
    complete = partial + '\\"与丁火。","other":1}'
    assert _extract_completed_json_string(complete, key="first_look") == '先看"巳酉丑"与丁火。'


def test_partial_json_array_waits_for_the_first_complete_direction() -> None:
    partial = '{"domain":"career","causal_chain":["命局结构先经过'
    assert _extract_first_completed_json_array_string(partial, key="causal_chain") is None
    complete = partial + '输出路径","再进入环境互动"]}'
    assert (
        _extract_first_completed_json_array_string(complete, key="causal_chain")
        == "命局结构先经过输出路径"
    )
