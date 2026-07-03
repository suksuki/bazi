from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v30.api.app import create_app
from v30.brain.practitioner_interaction import (
    build_admin_intelligence_replay,
    build_practitioner_interaction_state,
    build_practitioner_selection_record,
    find_option_set,
    apply_practitioner_selection_effects_to_thinking,
)
from v30.presentation.thinking import build_thinking_projection
from v30.runtime import create_smoke_runtime


def test_practitioner_selection_builds_belief_delta_without_chart_fact_mutation() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-practitioner-state", locale="zh")
    thinking = build_thinking_projection(runtime)
    option_set = _first_option_set(thinking)
    option_id = option_set["options"][0]["option_id"]

    selection = build_practitioner_selection_record(
        option_set,
        selected_option_ids=[option_id],
        action="select",
        confidence=0.82,
        actor_id="pytest-practitioner",
    )
    state = build_practitioner_interaction_state(runtime.reading_id, thinking, [selection], role_key="practitioner")
    overlaid = apply_practitioner_selection_effects_to_thinking(thinking, [selection])

    assert state["version"] == "v30.practitioner_interaction_state.v1"
    assert state["selection_count"] == 1
    assert state["chart_fact_mutation_allowed"] is False
    assert selection["effect"]["belief_delta"]["direction"] == "raise"
    assert "four_pillars" in selection["effect"]["training_signal"]["blocked_targets"]
    assert overlaid["practitioner_selection_effects"]["chart_fact_mutation_allowed"] is False
    assert any(
        point.get("selected_by_practitioner")
        for step in overlaid["steps"]
        for point in step.get("stage_points", [])
    )


def test_admin_intelligence_replay_exposes_stage_option_and_selection() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-admin-replay", locale="zh")
    thinking = build_thinking_projection(runtime)
    option_set = _first_option_set(thinking)
    selection = build_practitioner_selection_record(
        option_set,
        selected_option_ids=[option_set["options"][0]["option_id"]],
        action="rank",
        confidence=0.78,
    )

    replay = build_admin_intelligence_replay(runtime.reading_id, thinking, [selection])

    assert replay["version"] == "v30.admin_intelligence_replay.v1"
    assert replay["summary"]["stage_point_candidate_count"] >= replay["summary"]["stage_point_selected_count"] >= 1
    assert replay["summary"]["option_set_count"] >= 1
    assert replay["summary"]["practitioner_selection_count"] == 1
    assert replay["chart_fact_mutation_allowed"] is False


def test_practitioner_options_include_decision_verdict_branch_calibration() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-practitioner-decision-options", locale="zh")
    thinking = build_thinking_projection(runtime)
    option_sets = [
        row for row in build_practitioner_interaction_state(runtime.reading_id, thinking, role_key="practitioner")["option_sets"]
        if str(row.get("stage_id") or "") == "journey_decision_verdicts"
    ]

    assert option_sets
    assert all(row["source_type"] == "stage_point_branch" for row in option_sets)
    assert all(row["visibility"]["practitioner"] == "interactive" for row in option_sets)
    assert all(row["boundary"] == "branch_option_set_is_practitioner_calibration_not_customer_choice" for row in option_sets)


def test_practitioner_selection_api_and_admin_replay_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    app = create_app()
    client = TestClient(app)
    reading_id = "pytest-practitioner-api"

    client.get(f"/api/v30/readings/{reading_id}")
    option_state = client.get(f"/api/v30/readings/{reading_id}/practitioner/options").json()
    option_set = option_state["option_sets"][0]
    option_id = option_set["options"][0]["option_id"]
    response = client.post(
        f"/api/v30/readings/{reading_id}/practitioner/selections",
        json={
            "option_set_id": option_set["option_set_id"],
            "selected_option_ids": [option_id],
            "action": "select",
            "confidence": 0.8,
            "actor_id": "pytest",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["accepted"] is True
    assert payload["selection"]["effect"]["chart_fact_mutation_allowed"] is False
    assert payload["interaction_state"]["selection_count"] == 1
    assert payload["central_reading_state"]["version"] == "v30.central_reading_state.v1"
    assert payload["central_feedback_overlay"]["practitioner_selection_count"] == 1
    assert payload["central_feedback_overlay"]["chart_fact_mutation_allowed"] is False

    replay = client.get(f"/api/v30/admin/readings/{reading_id}/intelligence-replay").json()
    assert replay["summary"]["practitioner_selection_count"] == 1
    assert replay["chart_fact_mutation_allowed"] is False


def _first_option_set(thinking: dict[str, object]) -> dict[str, object]:
    for step in thinking["steps"]:
        for option_set in step.get("stage_point_set", {}).get("option_sets", []):
            found = find_option_set(thinking, option_set["option_set_id"], role_key="practitioner")
            if found:
                return found
    raise AssertionError("expected at least one practitioner option set")
