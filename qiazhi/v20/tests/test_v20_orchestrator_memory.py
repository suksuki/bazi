from __future__ import annotations

from v20.access.projection import project_runtime_for_role
from v20.api.runtime import run_runtime_from_pillars


def test_v20_brain_memory_signal_compiles_session_calibration_without_runtime_mutation() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "乙亥",
        "壬午",
        input_id="orchestrator.brain.memory",
        user_text="我想看事业",
        practitioner_selections=(
            {
                "control_key": "control.mainline_arbitration",
                "option": "切换到次级主线",
                "source_decision_keys": (),
            },
        ),
        latent_event_answers=(
            {
                "scenario_id": "latent.career_transition",
                "year_option": "25_to_30",
                "result_option": "platform_change",
                "intensity": "clear",
                "confidence": "high",
            },
        ),
    )

    signal = result["brain_memory_signal"]
    rows = signal["signals"]

    assert signal["version"] == "v20.orchestrator_brain_memory_signal.v1"
    assert signal["status"] == "active"
    assert signal["memory_key"].startswith("brain.memory.")
    assert signal["runtime_mutation"] is False
    assert signal["primary_mainline_key"] == result["mainline_arbitration"]["primary_mainline"]["candidate_key"]
    assert signal["selected_question_key"] == result["selected_question"]["question_key"]
    assert signal["coordination_status"] == result["brain_state"]["public_summary"]["coordination_status"]
    assert signal["signal_count"] == len(rows)
    assert any(row["signal_type"] == "practitioner_structured_choice" for row in rows)
    assert any(row["direction"] == "switch_to_supporting" for row in rows)
    assert any(row["signal_type"] == "latent_event_preference" for row in rows)
    assert all(row["runtime_rule_mutation"] is False for row in rows)
    assert "NO_RUNTIME_RULE_OR_MAINLINE_MUTATION" in signal["guardrails"]
    pointer = result["orchestrator_policy_pointer"]
    assert pointer["version"] == "v20.orchestrator_runtime_policy_pointer.v1"
    assert pointer["fast_iteration_enabled"] is True
    assert pointer["auto_learning_enabled"] is True
    assert pointer["shadow_signal_ref"] == signal["memory_key"]
    assert pointer["rollback_policy_version"] == "v20.orchestrator_policy.baseline.v1"
    assert isinstance(pointer["runtime_applied"], bool)
    assert result["reasoning_orchestrator"]["primary_outputs"]["brain_memory_signal"] == "brain_memory_signal.memory_key"
    assert result["reasoning_orchestrator"]["primary_outputs"]["orchestrator_policy_pointer"] == "orchestrator_policy_pointer.active_policy_version"
    assert result["reasoning_orchestrator"]["primary_outputs"]["orchestrator_policy_observability"] == "orchestrator_policy_observability.status"
    assert any(row["step_key"] == "brain_memory_signal" for row in result["reasoning_orchestrator"]["steps"])
    assert any(row["step_key"] == "orchestrator_policy_pointer" for row in result["reasoning_orchestrator"]["steps"])
    assert any(row["step_key"] == "orchestrator_policy_observability" for row in result["reasoning_orchestrator"]["steps"])


def test_v20_brain_memory_signal_is_training_visible_not_user_projected() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "乙亥",
        "壬午",
        input_id="orchestrator.brain.memory.role",
        user_text="我想看事业",
    )

    user = project_runtime_for_role(result, "user")
    analyst = project_runtime_for_role(result, "analyst")
    admin = project_runtime_for_role(result, "admin")

    assert "brain_memory_signal" not in user
    assert "orchestrator_policy_pointer" in user
    assert "orchestrator_policy_observability" not in user
    assert "brain_memory_signal" in analyst
    assert "brain_memory_signal" in admin
    assert "orchestrator_policy_pointer" in analyst
    assert "orchestrator_policy_observability" in analyst
    assert "orchestrator_policy_observability" in admin
    assert analyst["brain_memory_signal"]["runtime_mutation"] is False
