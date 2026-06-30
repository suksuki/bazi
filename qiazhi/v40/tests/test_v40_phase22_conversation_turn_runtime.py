from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.conversation import build_conversation_turn
from v40.engines import build_native_bazi_runtime
from v40.synthetic import load_synthetic_seeds


def _seed():
    return load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]


def _runtime_with_report(client: TestClient) -> dict[str, object]:
    seed = _seed()
    response = client.post(
        f"{API_PREFIX}/readings/native-report",
        json={
            "request_id": "request.phase22.report.001",
            "reading_id": "reading.phase22.report.001",
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


def test_conversation_turn_answers_one_round_without_rerunning_reading() -> None:
    client = TestClient(create_app())
    report = _runtime_with_report(client)
    seed = report["conversation_seeds"][0]

    response = client.post(
        f"{API_PREFIX}/conversation/turn",
        json={
            "turn_id": "turn.phase22.001",
            "runtime": report["runtime"],
            "question": seed["question"],
            "seed_id": seed["seed_id"],
            "execution_mode": "local",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["reruns_reading"] is False
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["answer_text"]
    assert "DecisionEngine" not in body["answer_text"]
    assert "结构信号" not in body["answer_text"]
    assert body["turn"]["source_seed_id"] == seed["seed_id"]
    assert body["turn"]["next_seeds"]


def test_conversation_turn_contract_blocks_verdict_authority() -> None:
    seed = _seed()
    runtime = build_native_bazi_runtime(
        request_id="request.phase22.local.001",
        reading_id="reading.phase22.local.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
    )

    turn, task, _result, acceptance, telemetry = build_conversation_turn(
        turn_id="turn.phase22.local.001",
        runtime=runtime,
        question="事业上下一步最适合怎么做？",
        execution_mode="local",
    )

    assert turn.accepted is True
    assert task.can_change_verdict is False
    assert task.can_create_chart_facts is False
    assert acceptance.status.value == "accepted"
    assert telemetry.llm_decision_authority is False
    assert turn.can_change_verdict is False
    assert turn.can_create_chart_facts is False


def test_user_ui_contains_independent_conversation_turn_runtime() -> None:
    client = TestClient(create_app())

    response = client.get("/v40/ui")

    assert response.status_code == 200
    assert "/api/v40/conversation/turn" in response.text
    assert "askConversation" in response.text
    assert 'id="conversation"' in response.text
    assert "继续问" in response.text
