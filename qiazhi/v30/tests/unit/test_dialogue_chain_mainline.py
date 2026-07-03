from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v30.api.app import create_app
from v30.dialogue_chain import append_dialogue_turn, start_dialogue_session
from v30.dialogue_chain.seed_router import route_dialogue_seed
from v30.runtime import create_smoke_runtime


def test_dialogue_seed_router_understands_user_wealth_current_year_question() -> None:
    runtime = create_smoke_runtime("pytest-dialogue-seed", day_master="庚")

    seed = route_dialogue_seed(runtime, "我今年财运如何？", source="user")

    assert seed.macro_domain == "wealth"
    assert seed.time_scope == "current_year"
    assert seed.user_intent == "ask_conclusion"
    assert seed.answer_priority == "answer_first"
    assert seed.boundary == "dialogue_seed_is_intent_not_chart_fact"


def test_dialogue_session_answers_first_then_generates_next_question_without_chart_mutation() -> None:
    runtime = create_smoke_runtime("pytest-dialogue-session", day_master="庚")
    before_chart = runtime.chart_context.model_dump(mode="json")

    session = start_dialogue_session(runtime, "我今年财运如何？")

    assert session.turn_count == 1
    assert session.active_domain == "wealth"
    first_turn = session.turns[0]
    assert first_turn.answer_contract["must_answer_user_seed"] is True
    assert first_turn.answer_contract["chart_fact_mutation_allowed"] is False
    assert "财" in first_turn.answer.display_text
    assert first_turn.answer.conclusion_items
    assert first_turn.answer.advice_items
    assert first_turn.selected_next_question is not None
    assert runtime.chart_context.model_dump(mode="json") == before_chart

    next_session = append_dialogue_turn(
        runtime,
        session,
        text=f"{first_turn.selected_next_question.label}：风险边界",
        selected_option="wealth:risk",
    )

    assert next_session.turn_count == 2
    assert next_session.memory_summary.domain_counts["wealth"] == 2
    assert next_session.turns[-1].training_signal["has_next_question"] is True
    assert runtime.chart_context.model_dump(mode="json") == before_chart


def test_dialogue_api_creates_session_and_appends_turn_without_runtime_chart_mutation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    app = create_app()
    client = TestClient(app)
    reading_id = "pytest-dialogue-api"

    client.get(f"/api/v30/readings/{reading_id}")
    before = client.get(f"/api/v30/readings/{reading_id}").json()["chart_context"]

    seeds = client.get(f"/api/v30/readings/{reading_id}/dialogue-seeds").json()
    assert seeds["items"]
    assert any(row["label"] == "我今年财运如何？" for row in seeds["items"])

    created = client.post(
        f"/api/v30/readings/{reading_id}/dialogues",
        json={"seed_text": "我今年财运如何？", "source": "user", "role": "user", "locale": "zh", "client": "web"},
    )
    assert created.status_code == 200
    session = created.json()["session"]
    dialogue_id = session["dialogue_id"]
    assert session["turn_count"] == 1
    assert session["turns"][0]["answer"]["conclusion_items"]
    assert session["turns"][0]["selected_next_question"]["question_id"]

    appended = client.post(
        f"/api/v30/readings/{reading_id}/dialogues/{dialogue_id}/turns",
        json={
            "text": "你的财务更偏主动争取、合作分配，还是保守积累？：风险边界",
            "selected_option": "wealth:risk",
            "role": "user",
            "locale": "zh",
            "client": "web",
        },
    )
    assert appended.status_code == 200
    next_session = appended.json()["session"]
    assert next_session["turn_count"] == 2
    assert next_session["memory_summary"]["domain_counts"]["wealth"] == 2
    assert appended.json()["answer_interaction_serialized"] is True

    listed = client.get(f"/api/v30/readings/{reading_id}/dialogues").json()
    assert listed["count"] == 1
    assert listed["items"][0]["dialogue_id"] == dialogue_id

    after = client.get(f"/api/v30/readings/{reading_id}").json()["chart_context"]
    assert after == before
