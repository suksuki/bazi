from __future__ import annotations

from copy import deepcopy

from v30.runtime import attach_hidden_factor_state, create_smoke_runtime
from v30.validation.central_brain_acceptance import (
    CENTRAL_BRAIN_ACCEPTANCE_VERSION,
    build_central_brain_acceptance,
    run_central_brain_acceptance,
)


def _payloads() -> dict[str, object]:
    runtime = create_smoke_runtime("unit-bt1-central-brain")
    amplifier = attach_hidden_factor_state(
        runtime,
        {
            "state_id": "unit-bt1-central-brain:hidden_factor_state",
            "reading_id": "unit-bt1-central-brain",
            "context_id": runtime.chart_context.context_id,
            "status": "amplifier_candidate",
            "amplifier_candidate": True,
            "confidence": 0.82,
            "special_years": ["2020"],
            "repeated_states": ["career_breakthrough"],
            "evidence_ids": [],
            "boundaries": ["feedback_conditioned_not_chart_fact"],
            "feedback": [],
        },
    )
    result = run_central_brain_acceptance()
    return {
        "runtime_payload": runtime.model_dump(mode="json"),
        "amplifier_runtime_payload": amplifier.model_dump(mode="json"),
        "role_projection_payloads": result["role_summary"]["role_rows"],
        "chart_fact_before": runtime.chart_context.model_dump(mode="json"),
        "chart_fact_after": runtime.chart_context.model_dump(mode="json"),
    }


def _builder_payloads() -> dict[str, object]:
    runtime = create_smoke_runtime("unit-bt1-builder")
    amplifier = attach_hidden_factor_state(
        runtime,
        {
            "state_id": "unit-bt1-builder:hidden_factor_state",
            "reading_id": "unit-bt1-builder",
            "context_id": runtime.chart_context.context_id,
            "status": "amplifier_candidate",
            "amplifier_candidate": True,
            "confidence": 0.82,
            "special_years": ["2020"],
            "repeated_states": ["career_breakthrough"],
            "evidence_ids": [],
            "boundaries": ["feedback_conditioned_not_chart_fact"],
            "feedback": [],
        },
    )
    from v30.brain import build_expression_role_state
    from v30.presentation import build_presentation_model

    roles = ("guest", "user", "practitioner", "admin", "lab")
    return {
        "runtime_payload": runtime.model_dump(mode="json"),
        "amplifier_runtime_payload": amplifier.model_dump(mode="json"),
        "role_projection_payloads": {
            role: build_presentation_model(
                runtime,
                role_key=role,
                client="admin" if role in {"admin", "lab"} else "web",
            ).model_dump(mode="json")
            for role in roles
        },
        "expression_role_states": {
            role: build_expression_role_state(
                reading_id=runtime.reading_id,
                role_key=role,
                locale=runtime.chart_context.locale,
                client="admin" if role in {"admin", "lab"} else "web",
            )
            for role in roles
        },
        "chart_fact_before": runtime.chart_context.model_dump(mode="json"),
        "chart_fact_after": runtime.chart_context.model_dump(mode="json"),
    }


def test_bt1_central_brain_acceptance_ready() -> None:
    result = build_central_brain_acceptance(**_builder_payloads())

    assert result["version"] == CENTRAL_BRAIN_ACCEPTANCE_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "bt1_central_brain_acceptance_ready"
    assert result["decision"]["central_brain_completion"] == 90
    assert result["decision"]["passed_acceptance_check_count"] == 5
    assert result["role_summary"]["guest_user_diagnostics_hidden"] is True
    assert result["role_summary"]["diagnostic_roles_have_diagnostics"] is True
    assert result["boundary_summary"]["chart_fact_fingerprint_preserved"] is True
    assert result["boundary_summary"]["policy_pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "BT2"


def test_bt1_blocks_missing_read_only_boundary() -> None:
    payloads = _builder_payloads()
    runtime_payload = deepcopy(payloads["runtime_payload"])
    effect = runtime_payload["question_plan"]["policy_effect"]  # type: ignore[index]
    trace = effect["central_brain_trace"]
    trace["boundaries"] = [
        row for row in trace["boundaries"]
        if row != "central_brain_does_not_mutate_chart_facts"
    ]
    payloads["runtime_payload"] = runtime_payload

    result = build_central_brain_acceptance(**payloads)

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "bt1_central_brain_acceptance_blocked"
    assert "central_brain_read_only_boundary" in result["decision"]["failed_check_ids"]
    assert result["decision"]["chart_fact_mutation_allowed"] is False


def test_bt1_blocks_customer_diagnostic_leak() -> None:
    payloads = _builder_payloads()
    role_payloads = deepcopy(payloads["role_projection_payloads"])
    role_payloads["user"]["diagnostics"] = {"central_brain": {"version": "leak"}}  # type: ignore[index]
    payloads["role_projection_payloads"] = role_payloads

    result = build_central_brain_acceptance(**payloads)

    assert result["status"] == "blocked"
    assert "role_projection_boundaries_ready" in result["decision"]["failed_check_ids"]
