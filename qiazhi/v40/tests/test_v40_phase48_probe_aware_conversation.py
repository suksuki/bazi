from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.contracts.probe import ProbeAnswerResult
from v40.contracts.runtime import RuntimeResult
from v40.conversation import build_conversation_turn
from v40.project import build_project_status
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _report_body(reading_id: str = "reading.phase48.conversation.001") -> dict[str, object]:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    client = TestClient(create_app())
    response = client.post(
        f"{API_PREFIX}/readings/native-report",
        json={
            "request_id": f"request.{reading_id}",
            "reading_id": reading_id,
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "user_question": seed.question,
            "topic": Topic.CAREER.value,
            "role_key": "user",
            "execution_mode": "local",
            "persist": False,
        },
    )
    assert response.status_code == 200
    return response.json()


def _probe_answer(runtime: dict[str, object]) -> dict[str, object]:
    client = TestClient(create_app())
    probe = runtime["probes"][0]  # type: ignore[index]
    response = client.post(
        f"{API_PREFIX}/probes/answer",
        json={
            "answer_id": "phase48-probe-answer-001",
            "runtime": runtime,
            "probe_id": probe["probe_id"],  # type: ignore[index]
            "selected_option": "平台资源",
            "created_by_role": "user",
        },
    )
    assert response.status_code == 200
    return response.json()["result"]


def test_conversation_turn_consumes_probe_answer_result_in_api_response() -> None:
    client = TestClient(create_app())
    report = _report_body()
    probe_result = _probe_answer(report["runtime"])

    response = client.post(
        f"{API_PREFIX}/conversation/turn",
        json={
            "turn_id": "phase48-turn-api-001",
            "runtime": report["runtime"],
            "question": "事业上下一步怎么做？",
            "execution_mode": "local",
            "probe_answer_results": [probe_result],
        },
    )

    assert response.status_code == 200
    body = response.json()
    turn = body["turn"]
    assert body["accepted"] is True
    assert "平台资源" in body["answer_text"]
    assert turn["source_answer_signal_ids"] == [probe_result["answer_signal"]["signal_id"]]
    assert turn["source_hidden_attribute_update_ids"] == [probe_result["hidden_attribute_update"]["update_id"]]
    assert any("平台资源" in row for row in turn["calibration_context"])
    assert any("平台资源" in row for row in body["expression"]["task"]["allowed_assertions"])
    assert body["reruns_reading"] is False
    assert body["writes_v40_production"] is False
    assert body["writes_v30_state"] is False


def test_conversation_builder_includes_probe_answer_context_in_task_and_input_cards() -> None:
    report = _report_body("reading.phase48.conversation.builder")
    runtime = RuntimeResult.model_validate(report["runtime"])
    probe_result = ProbeAnswerResult.model_validate(_probe_answer(report["runtime"]))

    turn, task, _result, acceptance, _telemetry = build_conversation_turn(
        turn_id="phase48-turn-builder-001",
        runtime=runtime,
        question="事业上下一步怎么做？",
        execution_mode="local",
        probe_answer_results=[probe_result],
    )

    assert acceptance.status.value == "accepted"
    assert "平台资源" in turn.answer_text
    assert probe_result.answer_signal.signal_id in task.input_card_ids
    assert probe_result.hidden_attribute_update.update_id in task.input_card_ids
    assert "已校准现实线索" in task.instruction
    assert "平台资源" in task.instruction


def test_user_ui_keeps_probe_context_for_followup_without_exposing_internal_type_names() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    assert "currentCalibrationResults" in html
    assert "\"probe_answer\" + \"_results\"" in html
    assert "AnswerSignal" not in html
    assert "HiddenAttributeUpdate" not in html
    assert "ProbeAnswerResult" not in html


def test_phase48_docs_and_project_status_track_probe_aware_conversation() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE48_PROBE_AWARE_CONVERSATION_PLAN.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Probe-Aware Conversation Context" in doc
    assert "ConversationTurnRequest.probe_answer_results" in doc
    assert "source_answer_signal_ids" in doc
    assert "2026-07-01 Phase 48" in spec
    assert "docs/V40_PHASE48_PROBE_AWARE_CONVERSATION_PLAN.md" in readme
    assert status["current_phase"] == 62
    assert status["current_phase_name"] == "Reading History And Conversation Layering"
    assert any(row["range"] == "48" and row["status"] == "complete" for row in status["phase_groups"])
