from __future__ import annotations

from pathlib import Path

from v30.api.app import AnswerRequest, ReadingRequest, create_app
from v30.presentation import build_presentation_model
from v30.presentation.surface_orchestrator import build_surface_orchestration
from v30.runtime import attach_question_outcome, create_smoke_runtime


ROOT = Path(__file__).resolve().parents[2]


def test_presentation_exposes_separated_surface_contract() -> None:
    runtime = create_smoke_runtime("surface-orchestrator-reading")
    payload = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    surface = payload["reading_surface"]
    orchestrator = surface["surface_orchestrator"]

    assert orchestrator["version"] == "v30.surface_orchestrator.v1"
    assert orchestrator["boundary"] == "surface_orchestrator_routes_outputs_without_making_bazi_decisions"
    assert orchestrator["reading_surface_policy"]["report_first"] is True
    assert orchestrator["reading_surface_policy"]["auto_show_conversation"] is False
    assert orchestrator["reading_surface_policy"]["must_show_verdict_before_questions"] is True
    assert orchestrator["output_pipeline"]["version"] == "v30.surface_output_pipeline.v1"
    assert orchestrator["output_pipeline"]["llm_role"] == "expression_and_dialogue_language_after_core_verdict"
    assert orchestrator["output_pipeline"]["decision_authority"] == "DecisionEngineVerdict"
    assert orchestrator["output_pipeline"]["runtime_order"] == [
        "SignalRegistry",
        "DecisionContract",
        "Verdict",
        "Advice",
        "Explanation",
        "DialogueRefinement",
    ]
    assert surface["surface_policy"] == orchestrator["reading_surface_policy"]
    assert surface["calibration_surface"]["entry_policy"]["auto_open"] is False
    assert surface["conversation_surface"]["entry_policy"]["user_invited_only"] is True
    assert surface["conversation_surface"]["entry_policy"]["auto_open"] is False
    assert surface["thinking_surface"]["entry_policy"]["requested_only"] is True
    assert "current_dialogue_turn" not in surface
    assert "next_question" not in surface
    assert "options" not in surface
    assert surface["legacy_dialogue_surface"]["status"] == "hidden_for_customer"
    assert surface["legacy_dialogue_surface"]["direct_fields_exposed"] is False
    assert orchestrator["legacy_compatibility"]["direct_legacy_fields_exposed"] is False

    policy = payload["projection_contract"]["surface_orchestration_policy"]
    assert policy["reading_first"] is True
    assert policy["probe_only_when_valuable"] is True
    assert policy["conversation_user_invited_only"] is True
    assert policy["thinking_requested_only"] is True
    assert policy["frontend_should_not_render_current_dialogue_turn_in_stage_pages"] is True
    assert policy["customer_direct_legacy_fields_hidden"] is True
    output_pipeline = payload["projection_contract"]["surface_output_pipeline_contract"]
    assert output_pipeline["boundary"] == "output_pipeline_turns_engine_signals_into_user_output_without_chart_fact_mutation"


def test_diagnostic_roles_keep_legacy_dialogue_payload_role_gated() -> None:
    runtime = create_smoke_runtime("surface-orchestrator-diagnostic")
    payload = build_presentation_model(runtime, role_key="practitioner", locale="zh", client="web").model_dump(mode="json")
    surface = payload["reading_surface"]
    legacy = surface["legacy_dialogue_surface"]

    assert legacy["status"] == "diagnostic_payload_available"
    assert legacy["direct_fields_exposed"] is True
    assert legacy["payload"]["current_dialogue_turn"]["version"] == "v30.current_dialogue_turn.v1"
    assert surface["current_dialogue_turn"] == legacy["payload"]["current_dialogue_turn"]
    assert surface["next_question"] == legacy["payload"]["next_question"]
    assert surface["options"] == legacy["payload"]["options"]


def test_api_user_views_hide_legacy_dialogue_fields_after_view_and_answer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V30_REPOSITORY", "local_json")
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    local_app = create_app()
    create_route = next(route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/readings")
    view_route = next(
        route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/readings/{reading_id}/view"
    )
    answer_route = next(
        route
        for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/readings/{reading_id}/questions/{question_id}/answer"
    )

    create_route.endpoint(ReadingRequest(reading_id="surface-api-legacy-gate"))
    user_view = view_route.endpoint("surface-api-legacy-gate", role="user", locale="zh", client="web")
    user_surface = user_view["reading_surface"]
    for legacy_key in {"current_dialogue_turn", "next_question", "options"}:
        assert legacy_key not in user_surface
    assert user_surface["legacy_dialogue_surface"]["status"] == "hidden_for_customer"
    assert user_surface["legacy_dialogue_surface"]["direct_fields_exposed"] is False
    assert "payload" not in user_surface["legacy_dialogue_surface"]

    diagnostic_view = view_route.endpoint("surface-api-legacy-gate", role="practitioner", locale="zh", client="web")
    diagnostic_surface = diagnostic_view["reading_surface"]
    diagnostic_legacy = diagnostic_surface["legacy_dialogue_surface"]
    assert diagnostic_legacy["status"] == "diagnostic_payload_available"
    assert diagnostic_legacy["direct_fields_exposed"] is True
    assert diagnostic_surface["current_dialogue_turn"] == diagnostic_legacy["payload"]["current_dialogue_turn"]

    question_id = user_view["questions"][0]["question_id"]
    answer_payload = answer_route.endpoint(
        "surface-api-legacy-gate",
        question_id,
        AnswerRequest(
            answer="先按事业压力看。",
            role="user",
            locale="zh",
            client="web",
            submit_surface="calibration_surface",
            submit_source_id=f"probe:{question_id}",
            submit_contract_version="v30.surface_submit_contract.v1",
            outcome_status="answered",
        ),
    )
    answered_surface = answer_payload["view"]["reading_surface"]
    for legacy_key in {"current_dialogue_turn", "next_question", "options"}:
        assert legacy_key not in answered_surface
    assert answered_surface["legacy_dialogue_surface"]["status"] == "hidden_for_customer"
    assert answer_payload["next_question_id"] is None or isinstance(answer_payload["next_question_id"], str)


def test_hidden_factor_turn_becomes_calibration_probe_not_chat_interrupt() -> None:
    runtime = create_smoke_runtime("surface-orchestrator-probe")
    question = {
        "question_id": "q_v30_hidden_factor_boundary_discovery",
        "label": "确认特殊年份与重复状态，只作为校准线索",
        "topic": "hidden_factor",
        "answer_constraints": {"type": "structured_hidden_factor", "target_hidden_attribute": "amplifier"},
        "options": [
            {"option_id": "hidden_factor:has_repeated_state", "label": "有反复状态", "value": "has_repeated_state"},
            {"option_id": "hidden_factor:skip", "label": "暂不回答", "value": "skip"},
        ],
    }
    turn = {
        "action": "ask",
        "stage_id": "portrait_projection",
        "question": question,
        "why_now": "只校准隐藏线索，不打断报告。",
        "target_claim_ids": ["claim:hidden_factor"],
        "decision_basis": {"selected_action": "ask_hidden_attribute_probe"},
        "visual_hint": {"title": "隐藏线索校准", "chips": ["校准线索"]},
    }

    orchestrator = build_surface_orchestration(
        runtime,
        reading_summary={"status": "ready"},
        final_synthesis={"conclusion": "已形成主结论"},
        domain_cards=[{"domain": "career"}],
        current_dialogue_turn=turn,
        next_question=question,
        dialogue={"version": "v30.customer_dialogue_projection.v1", "status": "ready"},
        questions=[question],
        role_key="user",
        locale="zh",
        client="web",
    )

    calibration = orchestrator["calibration_surface"]
    conversation = orchestrator["conversation_surface"]
    assert calibration["status"] == "available"
    assert calibration["visible_probe_count"] == 1
    card = calibration["visible_probe_cards"][0]
    assert card["version"] == "v30.calibration_probe_card.v1"
    assert card["question_id"] == "q_v30_hidden_factor_boundary_discovery"
    assert card["stage_id"] == "portrait_projection"
    assert card["skippable"] is True
    assert card["target_hidden_attribute"] == "amplifier"
    assert card["submit_contract"]["version"] == "v30.surface_submit_contract.v1"
    assert card["submit_contract"]["submit_surface"] == "calibration_surface"
    assert card["submit_contract"]["submit_source_id"] == "probe:q_v30_hidden_factor_boundary_discovery"
    assert "HiddenAttributeUpdate" in card["output_contract"]
    assert conversation["suggested_question"] == {}
    assert conversation["entry_policy"]["user_invited_only"] is True
    assert conversation["submit_contract"]["submit_surface"] == "conversation_surface"
    assert conversation["submit_contract"]["legacy_answer_endpoint_allowed"] is False


def test_frontend_stage_pages_use_calibration_surface_not_legacy_turn() -> None:
    source = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    assert "function calibrationProbeForStage" in source
    assert "surface?.calibration_surface" in source
    assert "function currentDialogueTurnForStage" not in source
    assert "surface?.current_dialogue_turn || {}" not in source
    assert "currentView?.reading_surface?.current_dialogue_turn" not in source
    assert "data-answer-surface" in source
    assert "submit_surface: submitSurface" in source
    assert "这个旧问题入口已经停用" in source


def test_frontend_conversation_surface_is_invitation_first() -> None:
    source = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    assert "function renderDialogueLauncher" in source
    assert "data-dialogue-open" in source
    assert "function dialogueSurfaceShouldRenderOpen" in source
    assert "if (!dialogueSurfaceShouldRenderOpen())" in source
    assert "target.querySelector(\"[data-dialogue-open]\")?.addEventListener(\"click\", openDialogueChain)" in source
    assert "open: false" in source
    assert "surface.title || \"连续智能对话\"" in source
    assert source.count("turns.map(renderDialogueTurn).join(\"\")") == 1


def test_question_outcome_records_explicit_submit_surface() -> None:
    runtime = create_smoke_runtime("surface-submit-source")
    question_id = runtime.question_anchors[0].question_id

    updated = attach_question_outcome(
        runtime,
        question_id,
        {
            "answer": "用户选择了校准卡",
            "submit_surface": "calibration_surface",
            "submit_source_id": f"probe:{question_id}",
            "submit_contract_version": "v30.surface_submit_contract.v1",
            "outcome_status": "answered",
            "selected_option": "career:pressure",
            "structured_payload": {},
        },
    )

    outcomes = updated.question_plan.session_state["question_outcomes"]
    event = next(row for row in outcomes if row["question_id"] == question_id)
    submit = event["submit_source"]
    assert submit["version"] == "v30.question_outcome_submit_source.v1"
    assert submit["submit_surface"] == "calibration_surface"
    assert submit["submit_source_id"] == f"probe:{question_id}"
    assert submit["submit_contract_version"] == "v30.surface_submit_contract.v1"
    assert submit["legacy"] is False
