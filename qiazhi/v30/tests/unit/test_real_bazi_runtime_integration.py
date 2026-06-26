from __future__ import annotations

from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime


def test_runtime_attaches_real_bazi_diagnosis_payload() -> None:
    runtime = create_smoke_runtime(
        "rbd-runtime-integration",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    diagnosis = runtime.question_plan.policy_effect["real_bazi_diagnosis"]

    assert diagnosis["version"] == "v30.real_bazi_diagnosis.runtime_integration.v1"
    assert diagnosis["status"] == "ready"
    assert diagnosis["summaries"]["claims"]["claim_count"] >= 50
    assert diagnosis["summaries"]["graph"]["node_count"] > diagnosis["summaries"]["claims"]["claim_count"]
    assert diagnosis["routes"]["wealth"]["selected_domain"] == "wealth"
    assert diagnosis["routes"]["wealth"]["selected_claim_count"] > 0
    assert diagnosis["public_projection"]["domain_summaries"]["wealth"]
    assert diagnosis["storage_policy"]["authoritative_facts_stored_here"] is False


def test_practical_reading_consumes_real_bazi_claims() -> None:
    runtime = create_smoke_runtime(
        "rbd-practical-integration",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    practical = runtime.question_plan.policy_effect["practical_reading_context"]
    wealth = practical["domain_readings"]["wealth"]
    career = practical["domain_readings"]["career"]

    assert "RBD_real_bazi_diagnosis" in wealth["depends_on_modules"]
    assert wealth["module_trace"]["uses_real_bazi_diagnosis"] is True
    assert wealth["diagnosis_summary"].startswith("财运沿")
    assert wealth["diagnosis_claims"]
    assert wealth["diagnosis_paths"]
    assert wealth["portrait_dimensions"]
    assert wealth["customer_takeaway"] == wealth["diagnosis_summary"]
    assert wealth["core_claim_quality"]["version"] == "v30.core_bazi_claim_quality.v1"
    assert wealth["core_claim_quality"]["quality_ready"] is True
    assert wealth["core_claim_quality"]["generic_language_hits"] == []
    assert wealth["core_claim_quality"]["chart_fact_mutation_allowed"] is False
    assert "事业落在" in career["diagnosis_summary"]
    assert wealth["rbd_reading_boundary"] == "practical_domain_reading_consumes_rbd_claims_without_fixed_event_or_chart_fact_mutation"


def test_customer_surface_projects_real_bazi_diagnosis_without_raw_trace() -> None:
    runtime = create_smoke_runtime(
        "rbd-customer-surface",
        day_master="庚",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    payload = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    surface = payload["reading_surface"]
    wealth = next(card for card in surface["domain_cards"] if card["domain"] == "wealth")

    assert surface["diagnosis_overview"]
    assert surface["reading_summary"]["diagnosis_overview"] == surface["diagnosis_overview"]
    assert wealth["diagnosis_summary"].startswith("财运沿")
    assert wealth["diagnosis_claims"]
    assert wealth["diagnosis_paths"]
    assert wealth["portrait_dimensions"]
    assert wealth["core_claim_quality"]["version"] == "v30.core_bazi_claim_quality.v1"
    assert wealth["core_claim_quality"]["quality_ready"] is True
    assert wealth["core_claim_quality"]["uses_traceable_claims"] is True
    assert wealth["core_claim_quality"]["fixed_event_prediction_allowed"] is False
    assert surface["structure_dynamics"]["top_paths"][0]["diagnosis_statement"]
    rendered = str(surface)
    assert "policy_effect" not in rendered
    assert "matched_rule" not in rendered
    assert "raw_score" not in rendered
    assert "feature_evidence" not in rendered


def test_admin_diagnostics_can_inspect_real_bazi_diagnosis() -> None:
    runtime = create_smoke_runtime("rbd-admin-diagnostics", day_master="庚")
    payload = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    diagnosis = payload["diagnostics"]["real_bazi_diagnosis"]

    assert diagnosis["version"] == "v30.real_bazi_diagnosis.runtime_integration.v1"
    assert diagnosis["summaries"]["rules"]["match_count"] > 0
    assert diagnosis["summaries"]["graph"]["edge_count"] > 0
    assert diagnosis["selected_routes"]["overview"]["central_brain_generated_facts"] is False
