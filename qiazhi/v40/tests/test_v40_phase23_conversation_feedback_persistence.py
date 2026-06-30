from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.synthetic import load_synthetic_seeds


SEED_PATH = Path("qiazhi/v40/data/synthetic/native_bazi_seeds.json")


def _report(client: TestClient) -> dict[str, object]:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    response = client.post(
        f"{API_PREFIX}/readings/native-report",
        json={
            "request_id": "request.phase23.report.001",
            "reading_id": "reading.phase23.report.001",
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


def test_conversation_turn_returns_local_training_label_without_global_write() -> None:
    client = TestClient(create_app())
    report = _report(client)
    seed = report["conversation_seeds"][0]

    response = client.post(
        f"{API_PREFIX}/conversation/turn",
        json={
            "turn_id": "turn.phase23.feedback.001",
            "runtime": report["runtime"],
            "question": seed["question"],
            "seed_id": seed["seed_id"],
            "execution_mode": "local",
            "persist": False,
            "persist_training_label": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    label = body["training_label"]
    assert body["persisted"] is False
    assert body["training_label_persisted"] is False
    assert label["event_id"] == "label:turn.phase23.feedback.001"
    assert label["reading_id"] == "reading.phase23.report.001"
    assert label["local_only"] is True
    assert label["chart_fact_mutation_allowed"] is False
    assert label["target_ids"]
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False


def test_phase23_conversation_storage_schema_is_v40_only() -> None:
    schema = Path("qiazhi/v40/deploy/postgres_v40_schema.sql").read_text(encoding="utf-8")
    repository = Path("qiazhi/v40/v40/storage/postgres.py").read_text(encoding="utf-8")

    assert "v40_conversation_turns" in schema
    assert "idx_v40_conversation_turns_reading" in schema
    assert "save_conversation_turn" in repository
    assert "list_conversation_turns" in repository
    assert "INSERT INTO v40_conversation_turns" in repository
    assert "FROM v40_conversation_turns" in repository
    assert "v30_conversation" not in schema
    assert "v30_conversation" not in repository
