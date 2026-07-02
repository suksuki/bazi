from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.conversation import build_conversation_seeds
from v40.engines import build_native_bazi_runtime
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _runtime():
    seed = load_synthetic_seeds(SEED_PATH)[0]
    return build_native_bazi_runtime(
        request_id="request.phase21.seeds.001",
        reading_id="reading.phase21.seeds.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
    )


def test_conversation_seeds_are_invited_followups_not_auto_dialogue() -> None:
    runtime = _runtime()

    seeds = build_conversation_seeds(runtime=runtime, accepted_text="结论已经形成。", role_key="user")

    assert seeds
    assert all(seed.generated_after_report for seed in seeds)
    assert all(seed.auto_start is False for seed in seeds)
    assert all(seed.question for seed in seeds)
    assert all(seed.role_visibility == ["user", "practitioner"] for seed in seeds)
    assert any(seed.source_probe_ids or seed.source_verdict_ids or seed.source_advice_ids for seed in seeds)


def test_native_report_returns_conversation_seeds_after_accepted_report() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    client = TestClient(create_app())

    response = client.post(
        f"{API_PREFIX}/readings/native-report",
        json={
            "request_id": "request.phase21.report.001",
            "reading_id": "reading.phase21.report.001",
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "user_question": seed.question,
            "topic": Topic.CAREER.value,
            "role_key": "user",
            "execution_mode": "local",
            "persist": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["conversation_seeds"]
    assert body["runtime"]["conversation_seeds"] == body["conversation_seeds"]
    assert body["conversation_seeds"][0]["auto_start"] is False


def test_user_ui_exposes_invited_conversation_seed_container() -> None:
    client = TestClient(create_app())

    response = client.get("/v40/ui")

    assert response.status_code == 200
    assert 'id="seedCards"' in response.text
    assert 'id="followupHub"' in response.text
    assert "conversation_seeds" in response.text
    assert "question-chip" in response.text
    assert "conversation-mode" in response.text
