from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from v30.api.app import AnswerRequest, ReadingRequest, create_app
from v30.contracts import V30Model
from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime
from v30.validation.corpus_518k import run_518k_validation
from v30.validation.llm_live_smoke import run_llm_live_smoke
from v30.validation.production_replay_metadata import summarize_production_replay_metadata
from v30.validation.release_artifact_review import build_release_artifact_review
from v30.validation.synthetic_case import run_synthetic_tier


ReleaseGateMode = Literal["quick", "standard"]


class ReleaseGateCheck(V30Model):
    check_id: str
    status: str
    summary: dict[str, Any] = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list)


class ReleaseGateResult(V30Model):
    run_id: str
    mode: ReleaseGateMode
    status: str
    checks: list[ReleaseGateCheck]
    promotion_signal: str
    started_at: datetime
    finished_at: datetime
    artifact_review: dict[str, Any] = Field(default_factory=dict)


def run_release_gate(
    *,
    mode: ReleaseGateMode = "quick",
    include_shard: bool = False,
    shard_id: int = 0,
    sample_limit: int = 8,
    shard_limit: int = 16,
) -> ReleaseGateResult:
    started_at = datetime.now(timezone.utc)
    checks = [
        _runtime_smoke_check(),
        _production_api_smoke_check(),
        _llm_live_smoke_check(),
        _post_seal_contracts_check(),
        _synthetic_all_check(),
        _corpus_sample_check(sample_limit),
    ]
    if include_shard or mode == "standard":
        checks.append(_corpus_shard_check(shard_id, shard_limit))
    failed = [check for check in checks if check.status != "passed"]
    finished_at = datetime.now(timezone.utc)
    artifact_review = build_release_artifact_review(checks)
    return ReleaseGateResult(
        run_id=f"v30.release_gate.{mode}.{started_at.strftime('%Y%m%d%H%M%S')}",
        mode=mode,
        status="passed" if not failed else "failed",
        checks=checks,
        promotion_signal="eligible" if not failed else "blocked",
        started_at=started_at,
        finished_at=finished_at,
        artifact_review=artifact_review,
    )


def _runtime_smoke_check() -> ReleaseGateCheck:
    runtime = create_smoke_runtime("v30-release-gate-runtime")
    failures: list[str] = []
    if not runtime.question_plan.recommended_questions:
        failures.append("runtime_missing_question_recommendations")
    if not runtime.question_plan.policy_effect.get("active_policy_versions"):
        failures.append("runtime_missing_active_policy_versions")
    if runtime.question_plan.policy_effect.get("active_policy_versions", {}).get("question_policy", "").startswith("v20"):
        failures.append("runtime_policy_points_to_v20")
    return ReleaseGateCheck(
        check_id="runtime_smoke",
        status="passed" if not failures else "failed",
        failures=failures,
        summary={
            "reading_id": runtime.reading_id,
            "question_count": len(runtime.question_plan.recommended_questions),
            "active_policy_versions": runtime.question_plan.policy_effect.get("active_policy_versions", {}),
            "mainline_quality_gate": runtime.mainline_state.quality_gate,
        },
    )


def _production_api_smoke_check() -> ReleaseGateCheck:
    failures: list[str] = []
    summary: dict[str, Any] = {
        "execution": "in_process_fastapi_route_contract",
        "routes_checked": [],
        "stable_surface_keys": [],
        "boundary": "production_api_smoke_validates_customer_loop_contract_not_chart_fact_mutation",
    }
    previous_env = {
        "V30_REPOSITORY": os.environ.get("V30_REPOSITORY"),
        "V30_RUNTIME_DIR": os.environ.get("V30_RUNTIME_DIR"),
        "V30_REDIS_URL": os.environ.get("V30_REDIS_URL"),
    }
    with tempfile.TemporaryDirectory(prefix="v30-r2-api-smoke-") as tmp_dir:
        try:
            os.environ["V30_REPOSITORY"] = "local_json"
            os.environ["V30_RUNTIME_DIR"] = str(Path(tmp_dir) / ".runtime")
            os.environ.pop("V30_REDIS_URL", None)
            smoke_app = create_app()
            health_route = _route_endpoint(smoke_app, "/api/v30/health")
            create_route = _route_endpoint(smoke_app, "/api/v30/readings")
            view_route = _route_endpoint(smoke_app, "/api/v30/readings/{reading_id}/view")
            answer_route = _route_endpoint(
                smoke_app,
                "/api/v30/readings/{reading_id}/questions/{question_id}/answer",
            )
            history_route = _route_endpoint(smoke_app, "/api/v30/readings/history")

            health = health_route()
            if health.get("ok") is not True or health.get("package") != "v30":
                failures.append("api_health_contract_failed")
            summary["routes_checked"].append("/api/v30/health")

            create_payload = ReadingRequest(
                reading_id="r2-production-api-smoke",
                locale="zh",
                target_year=2030,
                actor_id="r2-user",
                session_id="r2-session",
                birth_input={
                    "input_id": "r2-production-api-smoke-input",
                    "calendar_type": "solar",
                    "birth_date": "1990-02-04",
                    "birth_time": "23:30",
                    "timezone": "Asia/Shanghai",
                    "gender": "female",
                },
            )
            created = create_route(create_payload)
            if created.get("status") != "ready" or not created.get("trace_id"):
                failures.append("api_create_reading_not_ready")
            summary["routes_checked"].append("/api/v30/readings")

            user_view = view_route("r2-production-api-smoke", role="user", locale="zh", client="web")
            user_surface = user_view.get("reading_surface", {}) if isinstance(user_view, dict) else {}
            user_contract = user_view.get("projection_contract", {}) if isinstance(user_view, dict) else {}
            user_next = user_surface.get("next_question", {}) if isinstance(user_surface, dict) else {}
            question_id = user_next.get("question_id") if isinstance(user_next, dict) else ""
            stable_keys = {"reading_surface", "questions", "answer_panel", "projection_contract"}
            missing_keys = sorted(stable_keys - set(user_view))
            if missing_keys:
                failures.append("api_user_view_missing_stable_keys:" + ",".join(missing_keys))
            if user_view.get("diagnostics"):
                failures.append("api_user_view_diagnostics_visible")
            if user_contract.get("version") != "v30.api_projection_contract.v1":
                failures.append("api_user_projection_contract_missing")
            if user_contract.get("leak_scan", {}).get("passed") is not True:
                failures.append("api_user_projection_leak_scan_failed")
            if user_surface.get("core_bazi_reading", {}).get("surface_type") != "core_bazi_calculation":
                failures.append("api_user_core_bazi_reading_missing")
            if not question_id:
                failures.append("api_user_visible_next_question_missing")
            summary["routes_checked"].append("/api/v30/readings/{reading_id}/view:user")

            admin_view = view_route("r2-production-api-smoke", role="admin", locale="zh", client="admin")
            admin_contract = admin_view.get("projection_contract", {}) if isinstance(admin_view, dict) else {}
            if admin_contract.get("diagnostics_visible") is not True or not admin_view.get("diagnostics"):
                failures.append("api_admin_diagnostics_missing")
            summary["routes_checked"].append("/api/v30/readings/{reading_id}/view:admin")

            answer = answer_route(
                "r2-production-api-smoke",
                str(question_id),
                AnswerRequest(
                    answer="我主要想先看事业方向，近两年压力比较明显。",
                    role="user",
                    locale="zh",
                    client="web",
                    outcome_status="answered",
                    selected_option="career:pressure",
                    confidence=0.78,
                    feedback_tags=["r2_api_smoke", "customer_loop"],
                ),
            )
            answer_view = answer.get("view", {}) if isinstance(answer, dict) else {}
            answer_surface = answer_view.get("reading_surface", {}) if isinstance(answer_view, dict) else {}
            interaction_state = answer.get("interaction_state", {}) if isinstance(answer, dict) else {}
            if answer.get("accepted") is not True or answer.get("question_outcome_consumed") is not True:
                failures.append("api_answer_not_consumed")
            if not answer.get("next_question_id"):
                failures.append("api_answer_visible_next_question_missing")
            if not answer.get("internal_next_question_id"):
                failures.append("api_answer_internal_next_question_missing")
            if not isinstance(interaction_state, dict) or interaction_state.get("version") != "v30.interaction_state.v1":
                failures.append("api_answer_interaction_state_missing")
            if not answer_view.get("answer_panel"):
                failures.append("api_answer_panel_missing")
            if answer_surface.get("next_question", {}).get("question_id") == question_id:
                failures.append("api_answer_did_not_refresh_visible_next_question")
            summary["routes_checked"].append("/api/v30/readings/{reading_id}/questions/{question_id}/answer")

            history = history_route(
                actor_id="r2-user",
                session_id="r2-session",
                role="user",
                locale="zh",
                client="web",
                limit=10,
            )
            admin_history = history_route(
                actor_id="r2-user",
                session_id="r2-session",
                role="admin",
                locale="zh",
                client="admin",
                limit=10,
            )
            history_item = history.get("items", [{}])[0] if history.get("items") else {}
            admin_history_item = admin_history.get("items", [{}])[0] if admin_history.get("items") else {}
            owner_filter = history.get("owner_filter", {}) if isinstance(history.get("owner_filter"), dict) else {}
            visibility_contract = history.get("visibility_contract", {}) if isinstance(history.get("visibility_contract"), dict) else {}
            admin_owner_filter = admin_history.get("owner_filter", {}) if isinstance(admin_history.get("owner_filter"), dict) else {}
            admin_visibility_contract = admin_history.get("visibility_contract", {}) if isinstance(admin_history.get("visibility_contract"), dict) else {}
            admin_history_diagnostics = admin_history.get("diagnostics", {}) if isinstance(admin_history.get("diagnostics"), dict) else {}
            if history.get("version") != "v30.reading_history_projection.v1" or history.get("count") != 1:
                failures.append("api_history_user_projection_missing")
            if owner_filter.get("version") != "v30.reading_history_ownership.v1":
                failures.append("api_history_owner_filter_missing")
            if owner_filter.get("scope") != "actor_and_session":
                failures.append("api_history_owner_filter_scope_not_exact")
            if "actor_id" in owner_filter or "session_id" in owner_filter:
                failures.append("api_history_user_owner_ids_visible")
            if visibility_contract.get("guest_user_internal_fields_hidden") is not True or history.get("diagnostics"):
                failures.append("api_history_user_visibility_contract_failed")
            if "actor_context" in history_item or "internal_next_question_id" in history_item:
                failures.append("api_history_user_internal_fields_visible")
            if not history_item.get("visible_next_question_id"):
                failures.append("api_history_visible_next_question_missing")
            if history_item.get("owner_match", {}).get("diagnostic_ids_visible") is not False:
                failures.append("api_history_user_owner_match_not_sanitized")
            if admin_owner_filter.get("actor_id") != "r2-user" or admin_owner_filter.get("session_id") != "r2-session":
                failures.append("api_history_admin_owner_filter_ids_missing")
            if admin_visibility_contract.get("diagnostic_role") is not True or not admin_history_diagnostics.get("trace_ids"):
                failures.append("api_history_admin_visibility_contract_failed")
            if not admin_history_item.get("actor_context") or not admin_history_item.get("internal_next_question_id"):
                failures.append("api_history_admin_diagnostics_missing")
            summary["routes_checked"].append("/api/v30/readings/history")

            summary.update(
                {
                    "health_ok": health.get("ok") is True,
                    "created_status": created.get("status", ""),
                    "reading_id": created.get("reading_id", ""),
                    "trace_id": created.get("trace_id", ""),
                    "projection_contract_version": user_contract.get("version", ""),
                    "customer_core_surface_type": user_surface.get("core_bazi_reading", {}).get("surface_type", ""),
                    "answer_accepted": answer.get("accepted") is True,
                    "question_outcome_consumed": answer.get("question_outcome_consumed") is True,
                    "answer_panel_present": bool(answer_view.get("answer_panel")),
                    "interaction_state_version": interaction_state.get("version", "") if isinstance(interaction_state, dict) else "",
                    "visible_next_question_changed": answer_surface.get("next_question", {}).get("question_id") != question_id,
                    "history_count": history.get("count", 0),
                    "history_owner_scope": owner_filter.get("scope", ""),
                    "history_user_owner_ids_hidden": "actor_id" not in owner_filter and "session_id" not in owner_filter,
                    "history_user_diagnostics_hidden": history.get("diagnostics") == {},
                    "user_history_internal_fields_hidden": "actor_context" not in history_item and "internal_next_question_id" not in history_item,
                    "admin_history_diagnostics_visible": bool(admin_history_item.get("actor_context"))
                    and bool(admin_history_item.get("internal_next_question_id")),
                    "stable_surface_keys": sorted(stable_keys),
                }
            )
        except Exception as exc:  # pragma: no cover - defensive gate summary for unexpected API failures.
            failures.append(f"api_smoke_exception:{type(exc).__name__}:{exc}")
        finally:
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    return ReleaseGateCheck(
        check_id="production_api_smoke",
        status="passed" if not failures else "failed",
        summary=summary,
        failures=failures,
    )


def _route_endpoint(app: Any, path: str) -> Any:
    return next(route.endpoint for route in app.routes if getattr(route, "path", "") == path)


def _llm_live_smoke_check() -> ReleaseGateCheck:
    result = run_llm_live_smoke(
        reading_id="v30-release-gate-llm-live-smoke",
        write_artifact=True,
    )
    failures = list(result.failures)
    mutation = result.summary.get("no_chart_fact_mutation_proof", {})
    if isinstance(mutation, dict):
        if mutation.get("chart_facts_unchanged") is not True:
            failures.append("llm_live_smoke_chart_fact_mutation")
        if mutation.get("ranked_decisions_unchanged") is not True:
            failures.append("llm_live_smoke_ranked_decision_mutation")
        if mutation.get("model_signal_unchanged") is not True:
            failures.append("llm_live_smoke_model_signal_mutation")
        if mutation.get("interaction_state_unchanged") is not True:
            failures.append("llm_live_smoke_interaction_state_mutation")
    else:
        failures.append("llm_live_smoke_missing_no_mutation_proof")
    return ReleaseGateCheck(
        check_id="llm_live_smoke",
        status="passed" if result.passed and not failures else "failed",
        failures=failures,
        summary={
            **result.summary,
            "run_id": result.run_id,
            "artifact_uri": result.artifact_uri,
            "boundary": "release_gate_records_llm_live_smoke_without_requiring_provider_configuration",
        },
    )


def _post_seal_contracts_check() -> ReleaseGateCheck:
    runtime = create_smoke_runtime("v30-release-gate-post-seal")
    user_view = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    admin_view = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    surface = user_view.get("reading_surface", {})
    core = surface.get("core_bazi_reading", {}) if isinstance(surface, dict) else {}
    projection_contract = user_view.get("projection_contract", {})
    admin_contract = admin_view.get("projection_contract", {})
    ranked = core.get("ranked_decisions", {}) if isinstance(core, dict) else {}
    practical_domains = core.get("practical_domains", []) if isinstance(core, dict) else []
    leak_scan = projection_contract.get("leak_scan", {}) if isinstance(projection_contract, dict) else {}
    phase_seal_coverage = _phase_seal_coverage(
        runtime=runtime,
        core=core,
        ranked=ranked,
        practical_domains=practical_domains,
        projection_contract=projection_contract,
        leak_scan=leak_scan,
    )
    failures: list[str] = []
    if core.get("surface_type") != "core_bazi_calculation":
        failures.append("core_bazi_reading_missing")
    if not {"strength", "structure_pattern", "useful_god"} <= set(ranked):
        failures.append("ranked_decisions_missing_from_customer_core_reading")
    if len(practical_domains) < 3:
        failures.append("practical_domain_cards_missing")
    if projection_contract.get("version") != "v30.api_projection_contract.v1":
        failures.append("api_projection_contract_missing")
    if projection_contract.get("customer_surface_order", [])[:2] != ["core_bazi_reading", "domain_cards"]:
        failures.append("customer_surface_order_not_core_first")
    if leak_scan.get("passed") is not True or leak_scan.get("forbidden_token_hits"):
        failures.append("customer_projection_leak_scan_failed")
    if user_view.get("diagnostics"):
        failures.append("user_diagnostics_visible")
    if admin_contract.get("diagnostics_visible") is not True or not admin_view.get("diagnostics"):
        failures.append("admin_diagnostics_missing")
    missing_phase_seals = [
        module_id for module_id, payload in phase_seal_coverage.items()
        if isinstance(payload, dict) and payload.get("passed") is not True
    ]
    if missing_phase_seals:
        failures.append("phase_seal_coverage_missing:" + ",".join(missing_phase_seals))
    return ReleaseGateCheck(
        check_id="post_seal_contracts",
        status="passed" if not failures else "failed",
        failures=failures,
        summary={
            "core_surface_type": core.get("surface_type", ""),
            "ranked_decision_domains": sorted(ranked),
            "practical_domain_count": len(practical_domains),
            "projection_contract_version": projection_contract.get("version", ""),
            "user_leak_scan_passed": leak_scan.get("passed", False),
            "user_leak_scan_hits": leak_scan.get("forbidden_token_hits", []),
            "admin_diagnostics_visible": admin_contract.get("diagnostics_visible", False),
            "phase_seal_coverage": phase_seal_coverage,
            "phase_seal_passed_count": sum(
                1 for payload in phase_seal_coverage.values()
                if isinstance(payload, dict) and payload.get("passed") is True
            ),
            "boundary": "post_seal_release_contracts_validate_projection_and_core_modules_not_chart_facts",
        },
    )


def _phase_seal_coverage(
    *,
    runtime: Any,
    core: dict[str, Any],
    ranked: dict[str, Any],
    practical_domains: list[Any],
    projection_contract: dict[str, Any],
    leak_scan: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    fact_integrity = core.get("fact_integrity", {}) if isinstance(core.get("fact_integrity"), dict) else {}
    base_explanations = core.get("base_fact_explanations", {}) if isinstance(core.get("base_fact_explanations"), dict) else {}
    model_signal = runtime.question_plan.policy_effect.get("model_signal_summary", {})
    practical = runtime.question_plan.policy_effect.get("practical_reading_context", {})
    practical_domain_readings = practical.get("domain_readings", {}) if isinstance(practical, dict) and isinstance(practical.get("domain_readings"), dict) else {}
    return {
        "M1_birthinput_chart_facts": {
            "passed": bool(core.get("chart_build")) and len(core.get("four_pillars", [])) >= 4 and fact_integrity.get("deterministic") is True,
            "evidence": ["chart_build", "four_pillars", "fact_integrity"],
        },
        "M2_base_fact_explanation": {
            "passed": base_explanations.get("version") == "v30.base_bazi_fact_explanations.v1"
            and bool(core.get("visible_ten_gods"))
            and bool(core.get("five_elements")),
            "evidence": ["base_fact_explanations", "visible_ten_gods", "five_elements"],
        },
        "M3_evidence_rule_structure_spine": {
            "passed": bool(runtime.structure_state.evidence_ids)
            and bool(runtime.structure_state.graph_nodes)
            and bool(runtime.mainline_state.quality_gate),
            "evidence": ["structure_state.evidence_ids", "structure_state.graph_nodes", "mainline_state.quality_gate"],
        },
        "M4_ten_god_energy_model": {
            "passed": isinstance(model_signal, dict)
            and model_signal.get("version") == "v30.model_signal_summary.v1"
            and model_signal.get("raw_score_visible") is False,
            "evidence": ["model_signal_summary", "raw_score_visible_false"],
        },
        "M5_ranked_decisions": {
            "passed": {"strength", "structure_pattern", "useful_god"} <= set(ranked),
            "evidence": sorted(ranked),
        },
        "M6_practical_reading_output": {
            "passed": len(practical_domain_readings) >= 5 and len(practical_domains) >= 3,
            "evidence": ["practical_reading_context.domain_readings", "core_bazi_reading.practical_domains"],
        },
        "M7_real_case_calibration": {
            "passed": True,
            "evidence": ["synthetic_all.real_case_calibration_pack_required", "release_gate.synthetic_all_check"],
        },
        "M8_api_projection": {
            "passed": projection_contract.get("version") == "v30.api_projection_contract.v1"
            and leak_scan.get("passed") is True,
            "evidence": ["projection_contract", "projection_leak_scan"],
        },
    }


def _synthetic_all_check() -> ReleaseGateCheck:
    result = run_synthetic_tier("all")
    failures = [failure for row in result.results for failure in row.failures]
    interaction_loop_count = sum(1 for row in result.results if ".interaction_loop." in row.case_id)
    real_case_calibration_count = sum(1 for row in result.results if ".real_case_calibration." in row.case_id)
    api_projection_contract_count = sum(
        1 for row in result.results
        if isinstance(row.observed.get("api_projection_contract"), dict)
        and row.observed.get("api_projection_contract", {}).get("version") == "v30.api_projection_contract.v1"
    )
    user_leak_pass_count = sum(
        1 for row in result.results
        if isinstance(row.observed.get("api_projection_contract"), dict)
        and isinstance(row.observed.get("api_projection_contract", {}).get("leak_scan"), dict)
        and row.observed["api_projection_contract"]["leak_scan"].get("passed") is True
    )
    m6_contract_count = sum(
        sum(
            1
            for contract in row.observed.get("real_case_fixture", {}).get("practical_domain_contracts", {}).values()
            if isinstance(contract, dict)
            and contract.get("version") == "v30.practical_domain_reading.v2"
        )
        for row in result.results
        if isinstance(row.observed.get("real_case_fixture"), dict)
        and isinstance(row.observed.get("real_case_fixture", {}).get("practical_domain_contracts"), dict)
    )
    production_replay_metadata_rows = [
        row.observed.get("production_replay_metadata", {})
        for row in result.results
        if isinstance(row.observed.get("production_replay_metadata"), dict)
        and row.observed.get("production_replay_metadata")
    ]
    production_replay_metadata_summary = summarize_production_replay_metadata(production_replay_metadata_rows)
    if api_projection_contract_count < real_case_calibration_count:
        failures.append("api_projection_contract_coverage_below_real_case_pack")
    if user_leak_pass_count < api_projection_contract_count:
        failures.append("api_projection_leak_scan_not_all_passed")
    if m6_contract_count < 100:
        failures.append("m6_practical_contract_coverage_below_real_case_pack")
    if production_replay_metadata_summary["row_count"] < real_case_calibration_count:
        failures.append("production_replay_metadata_coverage_below_real_case_pack")
    if production_replay_metadata_summary["privacy_guard_pass_count"] < production_replay_metadata_summary["row_count"]:
        failures.append("production_replay_metadata_privacy_guard_not_all_passed")
    if production_replay_metadata_summary["projection_leak_scan_pass_count"] < production_replay_metadata_summary["row_count"]:
        failures.append("production_replay_metadata_projection_leak_scan_not_all_passed")
    return ReleaseGateCheck(
        check_id="synthetic_all",
        status="passed" if result.passed and not failures else "failed",
        failures=failures,
        summary={
            "suite_id": result.suite_id,
            "case_count": result.case_count,
            "passed_count": result.passed_count,
            "failed_count": result.failed_count,
            "tier_coverage": {
                "interaction_loop_case_count": interaction_loop_count,
                "real_case_calibration_pack_case_count": real_case_calibration_count,
                "api_projection_contract_count": api_projection_contract_count,
                "api_projection_leak_pass_count": user_leak_pass_count,
                "m6_practical_domain_contract_count": m6_contract_count,
                "production_replay_metadata": production_replay_metadata_summary,
                "production_replay_metadata_count": production_replay_metadata_summary["row_count"],
                "production_replay_metadata_privacy_guard_pass_count": production_replay_metadata_summary["privacy_guard_pass_count"],
                "production_replay_metadata_projection_leak_pass_count": production_replay_metadata_summary["projection_leak_scan_pass_count"],
                "boundary": "release_gate_summarizes_validation_coverage_not_chart_facts",
            },
        },
    )


def _corpus_sample_check(limit: int) -> ReleaseGateCheck:
    result = run_518k_validation(mode="sample", limit=limit)
    return ReleaseGateCheck(
        check_id="518k_sample",
        status="passed" if result.promotion_signal == "eligible" else "failed",
        failures=[str(row.get("cluster_key", "unknown_518k_failure")) for row in result.failure_clusters],
        summary={
            "run_id": result.run_id,
            "case_count": result.case_count,
            "promotion_signal": result.promotion_signal,
            "artifact_uri": result.artifact_uri,
            "index_uri": result.index_uri,
            "index_entry_uri": result.index_entry_uri,
            "artifact_record_id": result.artifact_record_id,
            "artifact_search_backend": result.artifact_search_backend,
            "artifact_searchable": result.artifact_searchable,
            "coverage_metrics": result.coverage_metrics,
            "drift_metrics": result.drift_metrics,
        },
    )


def _corpus_shard_check(shard_id: int, limit: int) -> ReleaseGateCheck:
    result = run_518k_validation(mode="shard", shard_id=shard_id, limit=limit)
    return ReleaseGateCheck(
        check_id="518k_shard",
        status="passed" if result.promotion_signal == "eligible" else "failed",
        failures=[str(row.get("cluster_key", "unknown_518k_failure")) for row in result.failure_clusters],
        summary={
            "run_id": result.run_id,
            "case_count": result.case_count,
            "shard_ids": result.shard_ids,
            "promotion_signal": result.promotion_signal,
            "artifact_uri": result.artifact_uri,
            "index_uri": result.index_uri,
            "index_entry_uri": result.index_entry_uri,
            "artifact_record_id": result.artifact_record_id,
            "artifact_search_backend": result.artifact_search_backend,
            "artifact_searchable": result.artifact_searchable,
            "coverage_metrics": result.coverage_metrics,
            "drift_metrics": result.drift_metrics,
        },
    )
