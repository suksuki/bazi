from __future__ import annotations

from copy import deepcopy

from v30.validation.real_bazi_product_reading_acceptance import (
    REAL_BAZI_PRODUCT_READING_ACCEPTANCE_VERSION,
    build_real_bazi_product_reading_acceptance,
    run_real_bazi_product_reading_acceptance,
)


def test_rbd_s110_accepts_product_reading_output() -> None:
    result = run_real_bazi_product_reading_acceptance(reading_id="test-rbd-s110-accepted")

    assert result["version"] == REAL_BAZI_PRODUCT_READING_ACCEPTANCE_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "rbd_s110_product_reading_accepted"
    assert result["decision"]["full_pytest_required"] is False
    assert result["policy_boundary"]["full_518k_required"] is False
    assert result["next_mainline_selection"]["task_id"] == "RBD-S1.11"
    domains = {row["domain"]: row for row in result["domain_acceptance_rows"]}
    assert set(domains) >= {"career", "wealth", "relationship", "health", "timing"}
    assert all(row["ready"] for row in domains.values())
    answer_check = next(row for row in result["checks"] if row["check_id"] == "answer_panel_uses_rbd_not_generic_template")
    assert answer_check["passed"] is True
    assert answer_check["observed"]["answer_has_rbd_terms"] is True


def test_rbd_s110_blocks_generic_answer_and_customer_internal_leak() -> None:
    accepted = run_real_bazi_product_reading_acceptance(reading_id="test-rbd-s110-broken-source")
    runtime_payload = {"reading_id": "broken"}
    user_view = {
        "reading_surface": deepcopy(_surface_from_result(accepted)),
        "answer_panel": {
            "question_id": "q_v30_user_wealth_tendency",
            "text": "可以进入具体问题，但仍按候选路径表达，不做确定断语。",
        },
    }
    user_view["reading_surface"]["policy_effect"] = {"matched_rules": []}  # type: ignore[index]
    admin_view = {"diagnostics": {"real_bazi_diagnosis": deepcopy(_diagnosis_from_result(accepted))}}

    result = build_real_bazi_product_reading_acceptance(
        runtime_payload=runtime_payload,
        user_view=user_view,
        admin_view=admin_view,
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "rbd_s110_product_reading_blocked"
    assert set(result["decision"]["failed_check_ids"]) >= {
        "answer_panel_uses_rbd_not_generic_template",
        "customer_projection_no_rbd_internal_leak",
    }
    assert result["decision"]["chart_fact_mutation_allowed"] is False


def _surface_from_result(result: dict[str, object]) -> dict[str, object]:
    # Rebuild a clean runtime surface through the public runner so the failure test mutates only its target fields.
    from v30.presentation import build_presentation_model
    from v30.runtime import create_smoke_runtime

    runtime = create_smoke_runtime(
        "test-rbd-s110-surface-copy",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    return build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")["reading_surface"]


def _diagnosis_from_result(result: dict[str, object]) -> dict[str, object]:
    from v30.presentation import build_presentation_model
    from v30.runtime import create_smoke_runtime

    runtime = create_smoke_runtime(
        "test-rbd-s110-diagnosis-copy",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    admin = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    return admin["diagnostics"]["real_bazi_diagnosis"]
