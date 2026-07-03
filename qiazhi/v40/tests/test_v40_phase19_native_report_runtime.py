from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _seed_payload() -> dict[str, object]:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    return {
        "request_id": "request.phase19.report.001",
        "reading_id": "reading.phase19.report.001",
        "chart_facts": seed.chart_facts.model_dump(mode="json"),
        "user_question": seed.question,
        "topic": Topic.CAREER.value,
        "role_key": "user",
        "execution_mode": "local",
        "persist": False,
    }


def test_native_report_endpoint_returns_runtime_expression_and_telemetry() -> None:
    client = TestClient(create_app())

    response = client.post(f"{API_PREFIX}/readings/native-report", json=_seed_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "v40.native_reading_report_response.v1"
    assert body["accepted"] is True
    assert body["accepted_text"]
    assert body["runtime"]["reading_id"] == "reading.phase19.report.001"
    assert body["runtime"]["expression_task"]["version"] == "v40.llm_expression_task.v1"
    assert body["runtime"]["expression_result"]["provider"] == "local_expression_adapter"
    assert body["runtime"]["acceptance_result"]["status"] == "accepted"
    assert body["runtime"]["expression_telemetry"]["accepted"] is True
    assert body["surface_bundle"]["report_first"] is True
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False


def test_native_report_persist_true_does_not_block_without_repository() -> None:
    client = TestClient(create_app())
    payload = _seed_payload()
    payload["persist"] = True
    payload["reading_id"] = "reading.phase19.report.persist.no.repository"

    response = client.post(f"{API_PREFIX}/readings/native-report", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["persisted"] is False
    assert body["accepted_text"]


def test_native_report_provider_text_mode_accepts_external_expression() -> None:
    client = TestClient(create_app())
    payload = _seed_payload()
    payload.update(
        {
            "reading_id": "reading.phase19.report.provider-text",
            "execution_mode": "provider_text",
            "provider": "test_provider",
            "model": "test-model",
            "provider_text": "结论\n- 事业线索更适合从木、火、土的资源与输出方式切入，先稳住主线再判断突破窗口。",
            "raw_thinking": "provider checked the allowed assertion",
        }
    )

    response = client.post(f"{API_PREFIX}/readings/native-report", json=payload)

    assert response.status_code == 200
    body = response.json()
    telemetry = body["expression"]["telemetry"]
    assert telemetry["provider"] == "test_provider"
    assert telemetry["model"] == "test-model"
    assert telemetry["execution_mode"] == "provider_text"
    assert telemetry["thinking_trace_available"] is True
    assert body["accepted"] is True
