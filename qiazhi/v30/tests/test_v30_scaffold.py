from __future__ import annotations

import ast
from pathlib import Path

import pytest
from fastapi import HTTPException

from v30.api.app import API_PREFIX, UI_PREFIX, app
from v30.api.app import AnswerRequest, AuthRegisterRequest, ReadingRequest, create_app
from v30.config import load_settings
from v30.presentation.client_model import build_presentation_model
from v30.runtime import create_smoke_runtime
from v30.storage.names import V30_TABLES, redis_key, require_v30_table
from v30.storage.postgres_schema import schema_sql


ROOT = Path(__file__).resolve().parents[1]


def test_no_runtime_imports_from_v20() -> None:
    for path in ROOT.rglob("*.py"):
        if ".git" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("v20"), f"{path} imports {alias.name}"
            if isinstance(node, ast.ImportFrom):
                assert node.module is None or not node.module.startswith("v20"), (
                    f"{path} imports from {node.module}"
                )


def test_v30_prefixes_and_settings() -> None:
    settings = load_settings()
    assert API_PREFIX == "/api/v30"
    assert UI_PREFIX == "/v30/ui"
    assert settings.redis_prefix == "v30"
    assert settings.runtime_dir.name == ".runtime"


def test_storage_names_are_v30_only() -> None:
    assert all(table.startswith("v30_") for table in V30_TABLES)
    assert require_v30_table("v30_readings") == "v30_readings"
    assert redis_key("local", "reading", "abc").startswith("v30:")
    assert "v20_" not in schema_sql()


def test_api_routes_are_v30_only() -> None:
    route_paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/v30/health" in route_paths
    assert "/api/v30/ui/capabilities" in route_paths
    assert "/api/v30/readings" in route_paths
    assert "/api/v30/readings/history" in route_paths
    assert "/api/v30/admin/training/run" in route_paths
    assert "/api/v30/admin/training/m3-background/run" in route_paths
    assert "/api/v30/admin/training/m3-background/status" in route_paths
    assert "/api/v30/admin/training/system-closeout" in route_paths
    assert "/api/v30/admin/training/candidate-quarantine" in route_paths
    assert "/api/v30/admin/validation/synthetic-coverage-manifest" in route_paths
    assert "/api/v30/admin/validation/518k/artifacts" in route_paths
    assert "/api/v30/admin/validation/518k/readiness-matrix" in route_paths
    assert "/api/v30/admin/validation/artifacts" in route_paths
    assert "/api/v30/admin/support/brain-training-synthetic-closeout" in route_paths
    assert "/api/v30/admin/productization/multi-user-terminal-locale-readiness" in route_paths
    assert "/api/v30/admin/productization/session-owner-boundary-readiness" in route_paths
    assert "/api/v30/admin/productization/locale-terminology-readiness" in route_paths
    assert "/api/v30/admin/productization/terminal-contract-freeze" in route_paths
    assert "/api/v30/admin/productization/closeout" in route_paths
    assert "/api/v30/admin/llm/bazi-context-prompt-readiness" in route_paths
    assert "/api/v30/admin/llm/bazi-answer-generator-readiness" in route_paths
    assert "/api/v30/admin/llm/bazi-output-acceptance-readiness" in route_paths
    assert "/api/v30/admin/llm/bazi-training-synthetic-readiness" in route_paths
    assert "/api/v30/admin/llm/bazi-role-locale-production-smoke" in route_paths
    assert "/api/v30/admin/llm/bazi-closeout" in route_paths
    assert "/api/v30/admin/mainline/bazi-intelligence-requirements-coverage" in route_paths
    assert "/api/v30/admin/mainline/bazi-backend-api-journey-acceptance" in route_paths
    assert "/api/v30/admin/mainline/intelligent-question-interaction-audit" in route_paths
    assert "/api/v30/admin/mainline/question-model-signal-training-readiness" in route_paths
    assert "/api/v30/admin/mainline/intelligent-question-chain-readiness" in route_paths
    assert "/api/v30/admin/mainline/intelligent-question-closeout" in route_paths
    assert "/api/v30/admin/mainline/main-module-completion-review" in route_paths
    assert "/api/v30/admin/mainline/customer-surface-bazi-context-reconciliation" in route_paths
    assert "/api/v30/admin/m3/source-backlog" in route_paths
    assert "/api/v30/admin/m3/source-backlog-closeout" in route_paths
    assert "/api/v30/admin/m5/evidence-consumption-hardening" in route_paths
    assert "/api/v30/admin/m5/calibration-replay-review" in route_paths
    assert "/api/v30/admin/m5/calibration-replay-closeout" in route_paths
    assert "/api/v30/admin/m6/practical-reading-consumption-hardening" in route_paths
    assert "/api/v30/admin/m6/practical-reading-closeout" in route_paths
    assert "/api/v30/admin/m7/real-case-calibration-steady-state-review" in route_paths
    assert "/api/v30/admin/m7/real-case-calibration-closeout" in route_paths
    assert "/api/v30/admin/m8/projection-api-contract-closeout" in route_paths
    assert "/api/v30/admin/iq/intelligent-question-support-review" in route_paths
    assert "/api/v30/admin/llm/bazi-expression-support-review" in route_paths
    assert "/api/v30/admin/training/synthetic-support-review" in route_paths
    assert "/api/v30/admin/training/latent-policy-observability" in route_paths
    assert "/api/v30/admin/training/latent-attribute-review" in route_paths
    assert "/api/v30/admin/training/latent-attribute-closeout" in route_paths
    assert "/api/v30/admin/mainline/core-chain-steady-state-summary" in route_paths
    assert "/api/v30/admin/mainline/evidence-driven-calibration-queue" in route_paths
    assert "/api/v30/admin/mainline/await-new-calibration-evidence" in route_paths
    assert "/api/v30/admin/mainline/core-calibration-steady-state-queue" in route_paths
    assert "/api/v30/admin/release/artifact-review" in route_paths
    assert "/api/v30/admin/release/status-review" in route_paths
    assert "/api/v30/admin/release/production-replay-intake" in route_paths
    assert "/api/v30/admin/release/production-replay-intake/search" in route_paths
    assert "/api/v30/admin/business/real-bazi-acceptance" in route_paths
    assert "/api/v30/admin/business/reading-regression-pack" in route_paths
    assert "/api/v30/admin/business/answer-refresh-regression" in route_paths
    assert "/api/v30/admin/business/boundary-blocked-input-regression" in route_paths
    assert "/api/v30/admin/business/api-contract-freeze" in route_paths
    assert "/api/v30/admin/business/acceptance-closeout" in route_paths
    assert "/api/v30/admin/business/steady-state" in route_paths
    assert "/api/v30/admin/brain/acceptance" in route_paths
    assert "/api/v30/admin/brain/session-replay" in route_paths
    assert "/api/v30/admin/brain/failure-routing" in route_paths
    assert "/api/v30/admin/release/candidate-review" in route_paths
    assert "/api/v30/admin/release/candidate-gate-review" in route_paths
    assert "/api/v30/admin/release/boundary-finalization" in route_paths
    assert "/api/v30/admin/release/external-dry-run" in route_paths
    assert "/api/v30/admin/release/full-pytest-decision" in route_paths
    assert "/api/v30/admin/release/blocked-status" in route_paths
    assert "/api/v30/admin/release/post-boundary-authorization" in route_paths
    assert "/api/v30/admin/mainline/selection-after-release-pause" in route_paths
    assert "/api/v30/admin/core/monitoring-loop" in route_paths
    assert "/api/v30/admin/core/lightweight-monitoring-checks" in route_paths
    assert "/api/v30/admin/core/calibration-observation-summary" in route_paths
    assert "/api/v30/admin/core/calibration-drift-watch" in route_paths
    assert "/api/v30/admin/core/focused-calibration-evidence-queue" in route_paths
    assert "/api/v30/admin/core/calibration-queue-review" in route_paths
    assert "/api/v30/admin/core/calibration-watch-closeout" in route_paths
    assert "/api/v30/admin/core/monitoring-cadence-baseline" in route_paths
    assert "/api/v30/admin/core/monitoring-cadence-documentation-sync" in route_paths
    assert "/api/v30/admin/core/monitoring-steady-state" in route_paths
    assert "/api/v30/admin/core/monitoring-s0-status" in route_paths
    assert "/api/v30/admin/calibration/frozen-core-review" in route_paths
    assert "/api/v30/admin/calibration/targeted-candidate-review" in route_paths
    assert "/api/v30/admin/calibration/targeted-validation-gate" in route_paths
    assert "/api/v30/admin/calibration/targeted-pointer-review" in route_paths
    assert "/api/v30/admin/calibration/targeted-pointer-decision" in route_paths
    assert "/api/v30/admin/calibration/targeted-closeout" in route_paths
    assert "/api/v30/admin/mainline/selection" in route_paths
    assert "/api/v30/admin/runs/{reading_id}/question-replay" in route_paths
    assert "/api/v30/admin/policies/question/comparison" in route_paths
    assert "/api/v30/admin/policies/lineage" in route_paths
    assert "/api/v30/admin/runtime/config" in route_paths
    assert "/api/v30/admin/runtime/db" in route_paths
    assert "/api/v30/admin/runtime/db/config" in route_paths
    assert "/api/v30/admin/runtime/db/apply-schema" in route_paths
    assert "/api/v30/admin/runtime/redis" in route_paths
    assert "/api/v30/admin/runtime/redis/config" in route_paths
    assert "/api/v30/admin/runtime/llm" in route_paths
    assert "/api/v30/admin/runtime/llm/config" in route_paths
    assert "/api/v30/admin/runtime/llm/test" in route_paths
    assert "/api/v30/readings/{reading_id}/hidden-factor/feedback" in route_paths
    assert "/api/v30/readings/{reading_id}/hidden-factor/state" in route_paths
    assert "/v30/ui" in route_paths
    assert not any(path.startswith("/api/v20") or path.startswith("/v20/ui") for path in route_paths)


def test_admin_runtime_config_endpoints_are_v30_safe(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    monkeypatch.delenv("V30_DATABASE_URL", raising=False)
    monkeypatch.delenv("V30_REDIS_URL", raising=False)
    monkeypatch.delenv("V30_LLM_API_KEY", raising=False)
    monkeypatch.delenv("V30_LLM_ENABLED", raising=False)
    local_app = create_app()

    route = next(route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/admin/runtime/config")
    status = route.endpoint()
    assert status["version"] == "v30.admin_runtime_config_status.v1"
    assert status["database"]["repository"] == "memory"
    assert status["database"]["database_url_configured"] is False
    assert status["redis"]["redis_url"] == ""
    assert status["llm"]["api_key_configured"] is False

    db_config_route = next(
        route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/admin/runtime/db/config"
    )
    saved = db_config_route.endpoint(
        {
            "repository": "postgres",
            "database_url": "postgresql://qiazhi_v30_app:secret@127.0.0.1:5432/qiazhi_v30?sslmode=prefer",
        }
    )
    assert saved["status"] == "saved"
    assert saved["restart_required"] is True
    assert "V30_DATABASE_URL" in saved["updated_env"]
    assert "qiazhi_v30_app:secret" not in str(saved)

    llm_config_route = next(
        route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/admin/runtime/llm/config"
    )
    llm_saved = llm_config_route.endpoint(
        {
            "enabled": True,
            "execute_llm": False,
            "provider": "ollama_native",
            "host": "127.0.0.1",
            "port": "11434",
            "model": "gemma4:latest",
            "api_key": "llm-secret",
        }
    )
    assert llm_saved["status"] == "saved"
    assert llm_saved["restart_required"] is False
    assert "V30_LLM_API_KEY" in llm_saved["updated_env"]
    assert "llm-secret" not in str(llm_saved)


def test_admin_release_artifact_review_endpoint_is_observability_only(monkeypatch) -> None:
    from datetime import datetime, timezone

    from v30.api import app as app_module
    from v30.validation import release_gate as release_gate_module
    from v30.validation.release_gate import ReleaseGateCheck, ReleaseGateResult

    checks = [
        ReleaseGateCheck(
            check_id="runtime_smoke",
            status="passed",
            summary={"active_policy_versions": {"question_policy": "question_policy.v30-baseline"}},
        ),
        ReleaseGateCheck(
            check_id="llm_live_smoke",
            status="passed",
            summary={"run_id": "llm-smoke", "artifact_uri": "/tmp/llm.json", "smoke_status": "unconfigured"},
        ),
        ReleaseGateCheck(
            check_id="post_seal_contracts",
            status="passed",
            summary={
                "projection_contract_version": "v30.api_projection_contract.v1",
                "user_leak_scan_passed": True,
                "admin_diagnostics_visible": True,
                "phase_seal_passed_count": 8,
            },
        ),
        ReleaseGateCheck(
            check_id="synthetic_all",
            status="passed",
            summary={
                "suite_id": "v30.synthetic.all",
                "case_count": 95,
                "passed_count": 95,
                "failed_count": 0,
                "tier_coverage": {
                    "api_projection_contract_count": 30,
                    "api_projection_leak_pass_count": 30,
                    "production_replay_metadata_count": 30,
                },
            },
        ),
        ReleaseGateCheck(
            check_id="518k_sample",
            status="passed",
            summary={
                "run_id": "sample",
                "case_count": 2,
                "promotion_signal": "eligible",
                "artifact_record_id": "v30.518k.artifact.sample",
                "artifact_uri": "/tmp/sample.json",
                "index_uri": "/tmp/index.json",
                "coverage_metrics": {"interaction_state_coverage": 2},
                "drift_metrics": {},
            },
        ),
    ]

    def fake_release_gate(**_: object) -> ReleaseGateResult:
        now = datetime.now(timezone.utc)
        return ReleaseGateResult(
            run_id="v30.release_gate.quick.fake",
            mode="quick",
            status="passed",
            checks=checks,
            promotion_signal="eligible",
            started_at=now,
            finished_at=now,
        )

    class FakeLineage:
        def model_dump(self, mode: str = "json") -> dict[str, object]:
            return {
                "family": "question_policy",
                "lineage_id": "question_policy:baseline:lineage",
                "active_artifact_id": "question_policy.v30-baseline",
                "validation_artifacts": [],
                "boundaries": ["read_only"],
            }

    monkeypatch.setattr(release_gate_module, "run_release_gate", fake_release_gate)
    monkeypatch.setattr(app_module, "build_promotion_lineage", lambda **_: FakeLineage())
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/artifact-review"
    )
    payload = route.endpoint(sample_limit=1)

    assert payload["version"] == "v30.admin_release_artifact_review.v1"
    assert payload["release_gate_status"] == "passed"
    review = payload["artifact_review"]
    assert review["version"] == "v30.release_artifact_review.v1"
    assert review["synthetic_suite_summary"]["case_count"] == 95
    assert review["corpus_518k_summary"]["sample"]["artifact_record_id"] == "v30.518k.artifact.sample"
    assert review["policy_lineage_summary"]["lineage_count"] == 4
    assert review["projection_contract_summary"]["projection_contract_version"] == "v30.api_projection_contract.v1"
    assert review["promotion_review"]["policy_promotion_allowed"] is False


def test_admin_release_status_review_selects_next_mainline() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/status-review"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.post_seal_status_review.v1"
    assert payload["core_module_summary"]["phase_sealed_count"] == 8
    assert payload["next_mainline_selection"]["task_id"] == "R13"
    assert payload["next_mainline_selection"]["selected_track"] == "external_release_boundary"
    assert payload["reopen_rules"]["core_modules_reopen_only_on_validation_failure"] is True


def test_admin_production_replay_intake_endpoint_is_metadata_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/production-replay-intake"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.production_replay_intake_batch.v1"
    assert payload["summary"]["row_count"] >= 30
    assert payload["summary"]["calibration_ready_count"] >= 20
    assert payload["summary"]["privacy_guard_pass_count"] == payload["summary"]["row_count"]
    assert payload["boundary"] == "production_replay_intake_batch_is_metadata_only_and_does_not_promote_policy"


def test_admin_production_replay_intake_search_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V30_REPOSITORY", "local_json")
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    local_app = create_app()
    intake_route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/production-replay-intake"
    )
    search_route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/production-replay-intake/search"
    )

    persisted = intake_route.endpoint(persist=True, selection_status="calibration_ready", module_ready="m4")
    assert persisted["store_write"]["stored_count"] == 30
    assert persisted["store_search"]["count"] == 25

    searched = search_route.endpoint(selection_status="calibration_ready", module_ready="m4")
    assert searched["version"] == "v30.production_replay_search.v1"
    assert searched["count"] == 25
    assert searched["summary"]["calibration_ready_count"] == 25


def test_admin_real_business_bazi_acceptance_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import real_business_bazi_reading_acceptance as b1_module

    def fake_acceptance(*, case_limit: int = 12) -> dict[str, object]:
        return {
            "version": "v30.real_business_bazi_reading_acceptance.v1",
            "status": "completed",
            "decision": {
                "business_bazi_reading_ready": True,
                "decision_status": "b1_real_business_bazi_reading_accepted",
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "acceptance_summary": {"accepted_case_count": case_limit, "ready_case_count": case_limit},
            "policy_boundary": {
                "full_pytest_run_by_default": False,
                "full_518k_run_by_default": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
        }

    monkeypatch.setattr(b1_module, "run_real_business_bazi_reading_acceptance", fake_acceptance)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/business/real-bazi-acceptance"
    )
    payload = route.endpoint(case_limit=10)

    assert payload["version"] == "v30.real_business_bazi_reading_acceptance.v1"
    assert payload["decision"]["decision_status"] == "b1_real_business_bazi_reading_accepted"
    assert payload["acceptance_summary"]["accepted_case_count"] == 10
    assert payload["decision"]["full_pytest_required"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False


def test_admin_business_reading_regression_pack_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import real_business_bazi_reading_regression_pack as b2_module

    def fake_regression_pack(*, case_limit: int = 24) -> dict[str, object]:
        return {
            "version": "v30.real_business_bazi_reading_regression_pack.v1",
            "status": "completed",
            "decision": {
                "business_reading_regression_ready": True,
                "decision_status": "b2_business_reading_regression_pack_ready",
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "regression_summary": {"regression_case_count": case_limit, "passed_case_count": case_limit},
            "policy_boundary": {
                "full_pytest_run_by_default": False,
                "full_518k_run_by_default": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
        }

    monkeypatch.setattr(b2_module, "run_real_business_bazi_reading_regression_pack", fake_regression_pack)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/business/reading-regression-pack"
    )
    payload = route.endpoint(case_limit=20)

    assert payload["version"] == "v30.real_business_bazi_reading_regression_pack.v1"
    assert payload["decision"]["decision_status"] == "b2_business_reading_regression_pack_ready"
    assert payload["regression_summary"]["regression_case_count"] == 20
    assert payload["decision"]["full_pytest_required"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False


def test_admin_business_answer_refresh_regression_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import real_business_answer_refresh_regression as b3_module

    def fake_answer_refresh(*, case_limit: int = 5) -> dict[str, object]:
        return {
            "version": "v30.real_business_answer_refresh_regression.v1",
            "status": "completed",
            "decision": {
                "answer_refresh_regression_ready": True,
                "decision_status": "b3_answer_refresh_regression_ready",
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "refresh_summary": {"answer_case_count": case_limit, "passed_answer_case_count": case_limit},
            "policy_boundary": {
                "full_pytest_run_by_default": False,
                "full_518k_run_by_default": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
        }

    monkeypatch.setattr(b3_module, "run_real_business_answer_refresh_regression", fake_answer_refresh)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/business/answer-refresh-regression"
    )
    payload = route.endpoint(case_limit=5)

    assert payload["version"] == "v30.real_business_answer_refresh_regression.v1"
    assert payload["decision"]["decision_status"] == "b3_answer_refresh_regression_ready"
    assert payload["refresh_summary"]["answer_case_count"] == 5
    assert payload["decision"]["full_pytest_required"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False


def test_admin_business_boundary_blocked_input_regression_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import real_business_boundary_blocked_input_regression as b4_module

    def fake_boundary_regression(*, case_limit: int = 5) -> dict[str, object]:
        return {
            "version": "v30.real_business_boundary_blocked_input_regression.v1",
            "status": "completed",
            "decision": {
                "boundary_blocked_input_ready": True,
                "decision_status": "b4_boundary_blocked_input_regression_ready",
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "boundary_summary": {"boundary_case_count": case_limit, "passed_boundary_case_count": case_limit},
            "policy_boundary": {
                "full_pytest_run_by_default": False,
                "full_518k_run_by_default": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
        }

    monkeypatch.setattr(b4_module, "run_real_business_boundary_blocked_input_regression", fake_boundary_regression)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/business/boundary-blocked-input-regression"
    )
    payload = route.endpoint(case_limit=5)

    assert payload["version"] == "v30.real_business_boundary_blocked_input_regression.v1"
    assert payload["decision"]["decision_status"] == "b4_boundary_blocked_input_regression_ready"
    assert payload["boundary_summary"]["boundary_case_count"] == 5
    assert payload["decision"]["full_pytest_required"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False


def test_admin_business_api_contract_freeze_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import real_business_api_contract_freeze as b5_module

    def fake_contract_freeze() -> dict[str, object]:
        return {
            "version": "v30.real_business_api_contract_freeze.v1",
            "status": "completed",
            "decision": {
                "api_contract_freeze_ready": True,
                "decision_status": "b5_business_api_contract_frozen",
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
                "external_release_ready": False,
            },
            "freeze_summary": {"gate_count": 4, "passed_gate_count": 4},
            "policy_boundary": {
                "full_pytest_run_by_default": False,
                "full_518k_run_by_default": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
                "external_release_allowed": False,
            },
        }

    monkeypatch.setattr(b5_module, "run_real_business_api_contract_freeze", fake_contract_freeze)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/business/api-contract-freeze"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.real_business_api_contract_freeze.v1"
    assert payload["decision"]["decision_status"] == "b5_business_api_contract_frozen"
    assert payload["freeze_summary"]["passed_gate_count"] == 4
    assert payload["decision"]["full_pytest_required"] is False
    assert payload["decision"]["external_release_ready"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False


def test_admin_business_acceptance_closeout_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import real_business_acceptance_closeout as b6_module

    def fake_closeout() -> dict[str, object]:
        return {
            "version": "v30.real_business_acceptance_closeout.v1",
            "status": "completed",
            "decision": {
                "business_acceptance_closeout_ready": True,
                "decision_status": "b6_business_acceptance_closed",
                "business_track_paused": True,
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "accepted_business_gate": {"gate_status": "frozen_default_gate"},
            "policy_boundary": {
                "full_pytest_run_allowed_by_default": False,
                "full_518k_run_allowed_by_default": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
                "business_track_auto_continue_allowed": False,
            },
        }

    monkeypatch.setattr(b6_module, "run_real_business_acceptance_closeout", fake_closeout)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/business/acceptance-closeout"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.real_business_acceptance_closeout.v1"
    assert payload["decision"]["decision_status"] == "b6_business_acceptance_closed"
    assert payload["decision"]["business_track_paused"] is True
    assert payload["decision"]["full_pytest_required"] is False
    assert payload["policy_boundary"]["business_track_auto_continue_allowed"] is False


def test_admin_business_steady_state_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import real_business_steady_state as s1_module

    def fake_steady_state() -> dict[str, object]:
        return {
            "version": "v30.real_business_steady_state.v1",
            "status": "completed",
            "decision": {
                "business_steady_state_ready": True,
                "decision_status": "s1_business_acceptance_steady_state_ready",
                "routine_business_gate_ready": True,
                "business_track_paused": True,
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "routine_business_gate": {
                "default_gate": "B1-B5",
                "business_track_auto_continue_allowed": False,
            },
            "policy_boundary": {
                "full_pytest_run_allowed_by_default": False,
                "full_518k_run_allowed_by_default": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
                "business_track_auto_continue_allowed": False,
            },
        }

    monkeypatch.setattr(s1_module, "run_real_business_steady_state", fake_steady_state)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/business/steady-state"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.real_business_steady_state.v1"
    assert payload["decision"]["decision_status"] == "s1_business_acceptance_steady_state_ready"
    assert payload["routine_business_gate"]["default_gate"] == "B1-B5"
    assert payload["decision"]["full_pytest_required"] is False
    assert payload["policy_boundary"]["business_track_auto_continue_allowed"] is False


def test_admin_central_brain_acceptance_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import central_brain_acceptance as bt1_module

    def fake_acceptance() -> dict[str, object]:
        return {
            "version": "v30.central_brain_acceptance.v1",
            "status": "completed",
            "decision": {
                "central_brain_acceptance_ready": True,
                "decision_status": "bt1_central_brain_acceptance_ready",
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "boundary_summary": {
                "chart_fact_fingerprint_preserved": True,
                "policy_pointer_write_allowed": False,
                "db_or_redis_direct_write_allowed": False,
            },
            "next_mainline_selection": {"task_id": "BT2"},
        }

    monkeypatch.setattr(bt1_module, "run_central_brain_acceptance", fake_acceptance)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/brain/acceptance"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.central_brain_acceptance.v1"
    assert payload["decision"]["decision_status"] == "bt1_central_brain_acceptance_ready"
    assert payload["decision"]["chart_fact_mutation_allowed"] is False
    assert payload["boundary_summary"]["policy_pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "BT2"


def test_admin_central_brain_session_replay_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import central_brain_session_replay as bt2_module

    def fake_replay() -> dict[str, object]:
        return {
            "version": "v30.central_brain_session_replay.v1",
            "status": "completed",
            "decision": {
                "central_brain_session_replay_ready": True,
                "decision_status": "bt2_central_brain_session_replay_ready",
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "replay_summary": {
                "chart_fact_fingerprint_preserved": True,
                "user_diagnostics_hidden": True,
                "practitioner_central_brain_visible": True,
            },
            "next_mainline_selection": {"task_id": "BT3"},
        }

    monkeypatch.setattr(bt2_module, "run_central_brain_session_replay", fake_replay)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/brain/session-replay"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.central_brain_session_replay.v1"
    assert payload["decision"]["decision_status"] == "bt2_central_brain_session_replay_ready"
    assert payload["decision"]["chart_fact_mutation_allowed"] is False
    assert payload["replay_summary"]["chart_fact_fingerprint_preserved"] is True
    assert payload["next_mainline_selection"]["task_id"] == "BT3"


def test_admin_central_brain_failure_routing_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import central_brain_failure_routing as bt3_module

    def fake_routing() -> dict[str, object]:
        return {
            "version": "v30.brain_failure_route.v1",
            "status": "completed",
            "decision": {
                "brain_failure_routing_ready": True,
                "decision_status": "bt3_brain_failure_routing_ready",
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "policy_boundary": {
                "operator_plan_only": True,
                "runtime_mutation_allowed": False,
                "chart_fact_mutation_allowed": False,
                "policy_pointer_write_allowed": False,
            },
            "next_mainline_selection": {"task_id": "BT4"},
        }

    monkeypatch.setattr(bt3_module, "run_central_brain_failure_routing", fake_routing)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/brain/failure-routing"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.brain_failure_route.v1"
    assert payload["decision"]["decision_status"] == "bt3_brain_failure_routing_ready"
    assert payload["policy_boundary"]["operator_plan_only"] is True
    assert payload["policy_boundary"]["runtime_mutation_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "BT4"


def test_admin_training_system_closeout_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import training_system_closeout as bt4_module

    def fake_closeout(*, training_run_id: str = "bt4-closeout") -> dict[str, object]:
        return {
            "version": "v30.training_system_closeout.v1",
            "status": "completed",
            "decision": {
                "training_system_closeout_ready": True,
                "decision_status": "bt4_training_system_closeout_ready",
                "training_completion": 97,
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "training_summary": {
                "training_run_id": training_run_id,
                "status": "applied",
                "promoted_count": 4,
            },
            "policy_boundary": {
                "closeout_admin_endpoint_read_only": True,
                "runtime_mutation_allowed": False,
                "chart_fact_mutation_allowed": False,
                "training_signal_may_change_chart_facts": False,
            },
            "next_mainline_selection": {"task_id": "BT5"},
        }

    monkeypatch.setattr(bt4_module, "run_training_system_closeout", fake_closeout)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/training/system-closeout"
    )
    payload = route.endpoint(training_run_id="bt4-closeout")

    assert payload["version"] == "v30.training_system_closeout.v1"
    assert payload["decision"]["decision_status"] == "bt4_training_system_closeout_ready"
    assert payload["decision"]["training_completion"] == 97
    assert payload["policy_boundary"]["closeout_admin_endpoint_read_only"] is True
    assert payload["policy_boundary"]["runtime_mutation_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "BT5"


def test_admin_training_candidate_quarantine_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import training_candidate_quarantine as bt5_module

    def fake_quarantine(*, training_run_id: str = "bt5-quarantine") -> dict[str, object]:
        return {
            "version": "v30.training_candidate_quarantine.v1",
            "status": "completed",
            "decision": {
                "training_candidate_quarantine_ready": True,
                "decision_status": "bt5_training_candidate_quarantine_ready",
                "training_completion": 99,
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "quarantine_summary": {
                "candidate_id": f"{training_run_id}.question_policy.failed",
                "status": "quarantined",
                "pointer_unchanged": True,
            },
            "policy_boundary": {
                "closeout_admin_endpoint_read_only": True,
                "runtime_mutation_allowed": False,
                "chart_fact_mutation_allowed": False,
                "failed_candidate_pointer_write_allowed": False,
            },
            "next_mainline_selection": {"task_id": "BT6"},
        }

    monkeypatch.setattr(bt5_module, "run_training_candidate_quarantine", fake_quarantine)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/training/candidate-quarantine"
    )
    payload = route.endpoint(training_run_id="bt5-quarantine")

    assert payload["version"] == "v30.training_candidate_quarantine.v1"
    assert payload["decision"]["decision_status"] == "bt5_training_candidate_quarantine_ready"
    assert payload["decision"]["training_completion"] == 99
    assert payload["policy_boundary"]["failed_candidate_pointer_write_allowed"] is False
    assert payload["quarantine_summary"]["status"] == "quarantined"
    assert payload["next_mainline_selection"]["task_id"] == "BT6"


def test_admin_latent_attribute_training_review_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import latent_attribute_admin_training_review as hf_module

    def fake_review(*, review_id: str = "", artifact_dir=None) -> dict[str, object]:
        return {
            "version": "v30.latent_attribute_admin_training_review.v1",
            "status": "completed",
            "decision": {
                "review_ready": True,
                "decision_status": "hf_r26_latent_attribute_admin_training_review_ready",
                "candidate_count": 3,
                "passed_check_count": 5,
                "check_count": 5,
                "failed_check_ids": [],
            },
            "candidate_summary": {
                "candidate_count": 3,
                "auto_apply_allowed_count": 0,
                "pointer_promotion_allowed_count": 0,
                "chart_fact_mutation_allowed_count": 0,
            },
            "policy_boundary": {
                "review_only": True,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "next_mainline_selection": {"task_id": "HF-R2.7"},
        }

    monkeypatch.setattr(hf_module, "run_latent_attribute_admin_training_review", fake_review)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/training/latent-attribute-review"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.latent_attribute_admin_training_review.v1"
    assert payload["decision"]["decision_status"] == "hf_r26_latent_attribute_admin_training_review_ready"
    assert payload["candidate_summary"]["candidate_count"] == 3
    assert payload["policy_boundary"]["auto_apply_training_allowed"] is False
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "HF-R2.7"


def test_admin_latent_attribute_workflow_closeout_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import latent_attribute_workflow_closeout as hf_module

    def fake_closeout(*, closeout_id: str = "", artifact_dir=None) -> dict[str, object]:
        return {
            "version": "v30.latent_attribute_workflow_closeout.v1",
            "status": "completed",
            "decision": {
                "closeout_ready": True,
                "decision_status": "hf_r28_latent_attribute_workflow_closeout_ready",
                "passed_check_count": 7,
                "check_count": 7,
                "failed_check_ids": [],
            },
            "workflow_summary": {
                "admin_review_is_read_only": True,
                "customer_policy_internals_hidden": True,
                "blocked_training_routes": ["calendar_conversion", "chart_facts", "flow_timing", "luck_cycle"],
            },
            "policy_boundary": {
                "closeout_only": True,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "next_mainline_selection": {"task_id": "HF-S1"},
        }

    monkeypatch.setattr(hf_module, "run_latent_attribute_workflow_closeout", fake_closeout)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/training/latent-attribute-closeout"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.latent_attribute_workflow_closeout.v1"
    assert payload["decision"]["decision_status"] == "hf_r28_latent_attribute_workflow_closeout_ready"
    assert payload["workflow_summary"]["admin_review_is_read_only"] is True
    assert payload["policy_boundary"]["auto_apply_training_allowed"] is False
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "HF-S1"


def test_admin_synthetic_coverage_manifest_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import synthetic_coverage_manifest as bt6_module

    def fake_manifest() -> dict[str, object]:
        return {
            "version": "v30.synthetic_coverage_manifest.v1",
            "status": "completed",
            "decision": {
                "synthetic_coverage_manifest_ready": True,
                "decision_status": "bt6_synthetic_coverage_manifest_ready",
                "synthetic_completion": 96,
                "full_pytest_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "summary": {
                "implemented_tier_count": 22,
                "planned_tiers": ["central_brain", "training_pipeline"],
                "major_node_only_tiers": ["all"],
            },
            "policy_boundary": {
                "manifest_is_read_only": True,
                "chart_fact_mutation_allowed": False,
                "synthetic_tier_may_claim_destiny_truth": False,
            },
            "next_mainline_selection": {"task_id": "BT7"},
        }

    monkeypatch.setattr(bt6_module, "run_synthetic_coverage_manifest", fake_manifest)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/validation/synthetic-coverage-manifest"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.synthetic_coverage_manifest.v1"
    assert payload["decision"]["decision_status"] == "bt6_synthetic_coverage_manifest_ready"
    assert payload["decision"]["synthetic_completion"] == 96
    assert payload["policy_boundary"]["manifest_is_read_only"] is True
    assert payload["policy_boundary"]["synthetic_tier_may_claim_destiny_truth"] is False
    assert payload["next_mainline_selection"]["task_id"] == "BT7"


def test_admin_brain_training_synthetic_closeout_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import brain_training_synthetic_closeout as bt10_module

    def fake_closeout(
        *,
        sample_limit: int = 8,
        shard_id: int = 7,
        shard_limit: int = 16,
        settings=None,
    ) -> dict[str, object]:
        return {
            "version": "v30.brain_training_synthetic_closeout.v1",
            "status": "completed",
            "decision": {
                "closeout_ready": True,
                "decision_status": "bt10_support_systems_steady_state_ready",
                "support_systems_steady_state": True,
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
            "completion_summary": {
                "central_brain_completion": 100,
                "training_completion": 100,
                "synthetic_completion": 100,
                "validation_518k_completion": 95,
            },
            "policy_boundary": {
                "closeout_is_read_only": True,
                "full_pytest_run_allowed_by_default": False,
                "synthetic_all_run_allowed_by_default": False,
                "full_518k_run_allowed_by_default": False,
            },
            "next_mainline_selection": {"task_id": "BT-S1"},
        }

    monkeypatch.setattr(bt10_module, "run_brain_training_synthetic_closeout", fake_closeout)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/support/brain-training-synthetic-closeout"
    )
    payload = route.endpoint(sample_limit=2, shard_id=7, shard_limit=2)

    assert payload["version"] == "v30.brain_training_synthetic_closeout.v1"
    assert payload["decision"]["decision_status"] == "bt10_support_systems_steady_state_ready"
    assert payload["completion_summary"]["central_brain_completion"] == 100
    assert payload["completion_summary"]["training_completion"] == 100
    assert payload["completion_summary"]["synthetic_completion"] == 100
    assert payload["completion_summary"]["validation_518k_completion"] == 95
    assert payload["policy_boundary"]["closeout_is_read_only"] is True
    assert payload["next_mainline_selection"]["task_id"] == "BT-S1"


def test_admin_multi_user_terminal_locale_readiness_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import multi_user_terminal_locale_readiness as u1_module

    def fake_readiness(reading_id: str = "u1-multi-user-terminal-locale") -> dict[str, object]:
        return {
            "version": "v30.multi_user_terminal_locale_readiness.v1",
            "task": {"task_id": "U1"},
            "matrix_summary": {
                "combination_count": 72,
                "customer_roles": ["guest", "user"],
                "diagnostic_roles": ["admin", "analyst", "lab", "practitioner"],
            },
            "completion_summary": {
                "multi_user_projection_completion": 80,
                "multi_terminal_projection_completion": 78,
                "multi_locale_projection_completion": 76,
                "current_scope_ready": True,
            },
            "decision": {
                "readiness_ready": True,
                "decision_status": "u1_projection_readiness_ready",
                "chart_fact_mutation_allowed": False,
                "full_pytest_required": False,
            },
            "next_mainline_selection": {"task_id": "U2"},
        }

    monkeypatch.setattr(u1_module, "run_multi_user_terminal_locale_readiness", fake_readiness)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/productization/multi-user-terminal-locale-readiness"
    )
    payload = route.endpoint(reading_id="u1-scaffold")

    assert payload["version"] == "v30.multi_user_terminal_locale_readiness.v1"
    assert payload["matrix_summary"]["combination_count"] == 72
    assert payload["decision"]["decision_status"] == "u1_projection_readiness_ready"
    assert payload["decision"]["chart_fact_mutation_allowed"] is False
    assert payload["completion_summary"]["current_scope_ready"] is True
    assert payload["next_mainline_selection"]["task_id"] == "U2"


def test_admin_session_owner_boundary_readiness_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import session_owner_boundary_readiness as u2_module

    def fake_readiness() -> dict[str, object]:
        return {
            "version": "v30.session_owner_boundary_readiness.v1",
            "task": {"task_id": "U2"},
            "completion_summary": {
                "durable_auth_session_productization": 60,
                "multi_user_projection_completion": 88,
                "current_scope_ready": True,
            },
            "decision": {
                "readiness_ready": True,
                "decision_status": "u2_session_owner_boundary_ready",
                "full_login_introduced": False,
                "chart_fact_mutation_allowed": False,
                "full_pytest_required": False,
            },
            "next_mainline_selection": {"task_id": "U3"},
        }

    monkeypatch.setattr(u2_module, "run_session_owner_boundary_readiness", fake_readiness)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/productization/session-owner-boundary-readiness"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.session_owner_boundary_readiness.v1"
    assert payload["decision"]["decision_status"] == "u2_session_owner_boundary_ready"
    assert payload["decision"]["full_login_introduced"] is False
    assert payload["decision"]["chart_fact_mutation_allowed"] is False
    assert payload["completion_summary"]["durable_auth_session_productization"] == 60
    assert payload["next_mainline_selection"]["task_id"] == "U3"


def test_admin_locale_terminology_readiness_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import locale_terminology_readiness as u3_module

    def fake_readiness(reading_id: str = "u3-locale-terminology") -> dict[str, object]:
        return {
            "version": "v30.locale_terminology_readiness.v1",
            "task": {"task_id": "U3"},
            "completion_summary": {
                "multi_locale_projection_completion": 88,
                "deep_locale_content_completion": 75,
                "current_scope_ready": True,
            },
            "decision": {
                "readiness_ready": True,
                "decision_status": "u3_locale_terminology_ready",
                "chart_fact_mutation_allowed": False,
                "llm_translation_required": False,
                "full_pytest_required": False,
            },
            "next_mainline_selection": {"task_id": "U4"},
        }

    monkeypatch.setattr(u3_module, "run_locale_terminology_readiness", fake_readiness)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/productization/locale-terminology-readiness"
    )
    payload = route.endpoint(reading_id="u3-scaffold")

    assert payload["version"] == "v30.locale_terminology_readiness.v1"
    assert payload["decision"]["decision_status"] == "u3_locale_terminology_ready"
    assert payload["decision"]["chart_fact_mutation_allowed"] is False
    assert payload["decision"]["llm_translation_required"] is False
    assert payload["completion_summary"]["multi_locale_projection_completion"] == 88
    assert payload["next_mainline_selection"]["task_id"] == "U4"


def test_admin_terminal_contract_freeze_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import terminal_contract_freeze as u4_module

    def fake_freeze(reading_id: str = "u4-terminal-contract") -> dict[str, object]:
        return {
            "version": "v30.terminal_contract_freeze.v1",
            "task": {"task_id": "U4"},
            "completion_summary": {
                "multi_terminal_projection_completion": 92,
                "productized_terminal_ui_completion": 65,
                "role_session_client_locale_productization": 95,
                "current_scope_ready": True,
            },
            "decision": {
                "freeze_ready": True,
                "decision_status": "u4_terminal_contract_frozen",
                "ui_redesign_required": False,
                "chart_fact_mutation_allowed": False,
                "full_pytest_required": False,
            },
            "next_mainline_selection": {"task_id": "U5"},
        }

    monkeypatch.setattr(u4_module, "run_terminal_contract_freeze", fake_freeze)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/productization/terminal-contract-freeze"
    )
    payload = route.endpoint(reading_id="u4-scaffold")

    assert payload["version"] == "v30.terminal_contract_freeze.v1"
    assert payload["decision"]["decision_status"] == "u4_terminal_contract_frozen"
    assert payload["decision"]["ui_redesign_required"] is False
    assert payload["decision"]["chart_fact_mutation_allowed"] is False
    assert payload["completion_summary"]["multi_terminal_projection_completion"] == 92
    assert payload["next_mainline_selection"]["task_id"] == "U5"


def test_admin_productization_closeout_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import productization_closeout as u5_module

    def fake_closeout(reading_id: str = "u5-productization-closeout") -> dict[str, object]:
        return {
            "version": "v30.productization_closeout.v1",
            "task": {"task_id": "U5"},
            "completion_summary": {
                "role_session_client_locale_productization": 100,
                "multi_user_projection_completion": 100,
                "multi_terminal_projection_completion": 100,
                "multi_language_projection_completion": 100,
                "current_scope_ready": True,
            },
            "decision": {
                "closeout_ready": True,
                "decision_status": "u5_productization_steady_state_ready",
                "productization_steady_state": True,
                "full_login_required": False,
                "ui_redesign_required": False,
                "chart_fact_mutation_allowed": False,
                "full_pytest_required": False,
            },
            "next_mainline_selection": {"task_id": "U-S1"},
        }

    monkeypatch.setattr(u5_module, "run_productization_closeout", fake_closeout)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/productization/closeout"
    )
    payload = route.endpoint(reading_id="u5-scaffold")

    assert payload["version"] == "v30.productization_closeout.v1"
    assert payload["decision"]["decision_status"] == "u5_productization_steady_state_ready"
    assert payload["decision"]["productization_steady_state"] is True
    assert payload["decision"]["full_login_required"] is False
    assert payload["decision"]["ui_redesign_required"] is False
    assert payload["completion_summary"]["role_session_client_locale_productization"] == 100
    assert payload["next_mainline_selection"]["task_id"] == "U-S1"


def test_admin_bazi_llm_context_prompt_readiness_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import bazi_llm_context_prompt_readiness as bl_module

    def fake_readiness(reading_id: str = "bl1-bl3-bazi-llm-context-prompt") -> dict[str, object]:
        return {
            "version": "v30.bazi_llm_context_prompt_readiness.v1",
            "task": {"task_id": "BL1-BL3"},
            "completion_summary": {
                "bazi_llm_context_compiler_completion": 70,
                "prompt_contract_registry_completion": 65,
                "context_budget_verifier_completion": 65,
                "bazi_llm_mainline_completion": 55,
                "current_scope_ready": True,
            },
            "checks": [],
            "decision": {
                "readiness_ready": True,
                "decision_status": "bl1_bl3_bazi_llm_context_prompt_ready",
                "check_count": 8,
                "passed_check_count": 8,
                "chart_fact_mutation_allowed": False,
            },
            "next_mainline_selection": {"task_id": "BL4"},
        }

    monkeypatch.setattr(bl_module, "run_bazi_llm_context_prompt_readiness", fake_readiness)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/llm/bazi-context-prompt-readiness"
    )
    payload = route.endpoint(reading_id="pytest-bl")

    assert payload["version"] == "v30.bazi_llm_context_prompt_readiness.v1"
    assert payload["decision"]["decision_status"] == "bl1_bl3_bazi_llm_context_prompt_ready"
    assert payload["decision"]["chart_fact_mutation_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "BL4"


def test_admin_bazi_llm_answer_generator_readiness_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import bazi_llm_answer_generator_readiness as bl4_module

    def fake_readiness(reading_id: str = "bl4-bazi-llm-answer-generator") -> dict[str, object]:
        return {
            "version": "v30.bazi_llm_answer_generator_readiness.v1",
            "task": {"task_id": "BL4"},
            "completion_summary": {
                "bazi_llm_answer_generator_completion": 70,
                "bazi_llm_mainline_completion": 65,
                "current_scope_ready": True,
            },
            "checks": [],
            "decision": {
                "readiness_ready": True,
                "decision_status": "bl4_bazi_llm_answer_generator_ready",
                "check_count": 5,
                "passed_check_count": 5,
                "llm_execution_required": False,
                "chart_fact_mutation_allowed": False,
            },
            "next_mainline_selection": {"task_id": "BL5"},
        }

    monkeypatch.setattr(bl4_module, "run_bazi_llm_answer_generator_readiness", fake_readiness)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/llm/bazi-answer-generator-readiness"
    )
    payload = route.endpoint(reading_id="pytest-bl4")

    assert payload["version"] == "v30.bazi_llm_answer_generator_readiness.v1"
    assert payload["decision"]["decision_status"] == "bl4_bazi_llm_answer_generator_ready"
    assert payload["decision"]["llm_execution_required"] is False
    assert payload["next_mainline_selection"]["task_id"] == "BL5"


def test_admin_bazi_llm_output_acceptance_readiness_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import bazi_llm_output_acceptance_readiness as bl5_module

    def fake_readiness(reading_id: str = "bl5-bazi-llm-output-acceptance") -> dict[str, object]:
        return {
            "version": "v30.bazi_llm_output_acceptance_readiness.v1",
            "task": {"task_id": "BL5"},
            "completion_summary": {
                "bazi_llm_output_acceptance_completion": 72,
                "bazi_llm_mainline_completion": 70,
                "current_scope_ready": True,
            },
            "checks": [],
            "decision": {
                "readiness_ready": True,
                "decision_status": "bl5_bazi_llm_output_acceptance_ready",
                "check_count": 5,
                "passed_check_count": 5,
                "live_llm_required": False,
                "chart_fact_mutation_allowed": False,
            },
            "next_mainline_selection": {"task_id": "BL6"},
        }

    monkeypatch.setattr(bl5_module, "run_bazi_llm_output_acceptance_readiness", fake_readiness)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/llm/bazi-output-acceptance-readiness"
    )
    payload = route.endpoint(reading_id="pytest-bl5")

    assert payload["version"] == "v30.bazi_llm_output_acceptance_readiness.v1"
    assert payload["decision"]["decision_status"] == "bl5_bazi_llm_output_acceptance_ready"
    assert payload["decision"]["live_llm_required"] is False
    assert payload["next_mainline_selection"]["task_id"] == "BL6"


def test_admin_bazi_llm_training_synthetic_readiness_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import bazi_llm_training_synthetic_readiness as bl6_module

    def fake_readiness() -> dict[str, object]:
        return {
            "version": "v30.bazi_llm_training_synthetic_readiness.v1",
            "task": {"task_id": "BL6"},
            "completion_summary": {
                "bazi_llm_training_signal_completion": 72,
                "bazi_llm_synthetic_tier_completion": 75,
                "bazi_llm_mainline_completion": 75,
                "current_scope_ready": True,
            },
            "checks": [],
            "decision": {
                "readiness_ready": True,
                "decision_status": "bl6_bazi_llm_training_synthetic_ready",
                "check_count": 5,
                "passed_check_count": 5,
                "live_llm_required": False,
                "chart_fact_mutation_allowed": False,
            },
            "next_mainline_selection": {"task_id": "BL7"},
        }

    monkeypatch.setattr(bl6_module, "run_bazi_llm_training_synthetic_readiness", fake_readiness)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/llm/bazi-training-synthetic-readiness"
    )
    payload = route.endpoint()

    assert payload["version"] == "v30.bazi_llm_training_synthetic_readiness.v1"
    assert payload["decision"]["decision_status"] == "bl6_bazi_llm_training_synthetic_ready"
    assert payload["decision"]["live_llm_required"] is False
    assert payload["next_mainline_selection"]["task_id"] == "BL7"


def test_admin_bazi_llm_role_locale_production_smoke_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import bazi_llm_role_locale_production_smoke as bl7_module

    def fake_smoke(reading_id: str = "bl7-bazi-llm-role-locale-smoke") -> dict[str, object]:
        return {
            "version": "v30.bazi_llm_role_locale_production_smoke.v1",
            "task": {"task_id": "BL7"},
            "completion_summary": {
                "bazi_llm_role_contract_completion": 82,
                "bazi_llm_locale_contract_completion": 80,
                "bazi_llm_mainline_completion": 80,
                "current_scope_ready": True,
            },
            "checks": [],
            "decision": {
                "readiness_ready": True,
                "decision_status": "bl7_bazi_llm_role_locale_smoke_ready",
                "check_count": 5,
                "passed_check_count": 5,
                "live_llm_required": False,
                "chart_fact_mutation_allowed": False,
                "policy_pointer_write_allowed": False,
            },
            "next_mainline_selection": {"task_id": "BL8"},
        }

    monkeypatch.setattr(bl7_module, "run_bazi_llm_role_locale_production_smoke", fake_smoke)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/llm/bazi-role-locale-production-smoke"
    )
    payload = route.endpoint(reading_id="pytest-bl7")

    assert payload["version"] == "v30.bazi_llm_role_locale_production_smoke.v1"
    assert payload["decision"]["decision_status"] == "bl7_bazi_llm_role_locale_smoke_ready"
    assert payload["decision"]["policy_pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "BL8"


def test_admin_bazi_llm_closeout_endpoint_is_read_only(monkeypatch) -> None:
    from v30.validation import bazi_llm_closeout as bl8_module

    def fake_closeout(reading_id: str = "bl8-bazi-llm-closeout") -> dict[str, object]:
        return {
            "version": "v30.bazi_llm_closeout.v1",
            "task": {"task_id": "BL8"},
            "completion_summary": {
                "bazi_llm_mainline_completion": 88,
                "current_scope_ready": True,
            },
            "checks": [],
            "decision": {
                "closeout_ready": True,
                "decision_status": "bl8_bazi_llm_steady_state_ready",
                "check_count": 5,
                "passed_check_count": 5,
                "bazi_llm_steady_state": True,
                "optional_live_smoke_allowed": True,
                "live_llm_required": False,
                "chart_fact_mutation_allowed": False,
                "policy_pointer_write_allowed": False,
            },
            "next_mainline_selection": {"task_id": "BL-S1"},
        }

    monkeypatch.setattr(bl8_module, "run_bazi_llm_closeout", fake_closeout)
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/llm/bazi-closeout"
    )
    payload = route.endpoint(reading_id="pytest-bl8")

    assert payload["version"] == "v30.bazi_llm_closeout.v1"
    assert payload["decision"]["decision_status"] == "bl8_bazi_llm_steady_state_ready"
    assert payload["decision"]["optional_live_smoke_allowed"] is True
    assert payload["decision"]["live_llm_required"] is False
    assert payload["next_mainline_selection"]["task_id"] == "BL-S1"


def test_admin_release_candidate_review_endpoint_is_read_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V30_REPOSITORY", "local_json")
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/candidate-review"
    )
    payload = route.endpoint(run_quick_gate=False, sample_limit=1)

    assert payload["version"] == "v30.release_candidate_review.v1"
    assert payload["decision"]["release_candidate_gate_recommended"] is False
    assert "release_gate_not_run_for_review" in payload["decision"]["blockers"]
    assert payload["post_seal_summary"]["completed_task_count"] == 12
    assert payload["release_candidate_gate"]["policy_pointer_promotion_allowed"] is False
    assert payload["boundary"] == (
        "release_candidate_review_is_read_only_and_does_not_mutate_chart_facts_or_policy_pointers"
    )


def test_admin_release_candidate_gate_review_endpoint_runs_standard_gate() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/candidate-gate-review"
    )
    payload = route.endpoint(sample_limit=2, shard_id=7, shard_limit=3)

    assert payload["version"] == "v30.release_candidate_gate_review.v1"
    assert payload["decision"]["release_boundary_ready"] is True
    assert payload["decision"]["policy_promotion_allowed"] is False
    assert payload["release_gate_summary"]["mode"] == "standard"
    assert payload["release_gate_summary"]["check_count"] == 7
    assert payload["corpus_518k_summary"]["sample_case_count"] == 2
    assert payload["corpus_518k_summary"]["shard_case_count"] == 3
    assert payload["next_mainline_selection"]["task_id"] == "R12"


def test_admin_release_boundary_finalization_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/boundary-finalization"
    )
    payload = route.endpoint(sample_limit=2, shard_id=7, shard_limit=3, full_pytest_status="")

    assert payload["version"] == "v30.release_boundary_finalization.v1"
    assert payload["decision"]["internal_release_candidate_finalized"] is True
    assert payload["decision"]["external_release_ready"] is False
    assert payload["decision"]["full_pytest_required_before_external_release"] is True
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["evidence_bundle_summary"]["completed_post_seal_task_count"] == 12
    assert payload["next_mainline_selection"]["task_id"] == "R13"


def test_admin_frozen_core_calibration_review_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/calibration/frozen-core-review"
    )
    payload = route.endpoint(run_gate=False)

    assert payload["version"] == "v30.frozen_core_calibration_review.v1"
    assert payload["frozen_core_scope"]["completion_state"] == "M1-M8_100_percent_current_scope_frozen"
    assert payload["decision"]["calibration_baseline_ready"] is False
    assert "frozen_core_calibration_tiers_not_run" in payload["decision"]["blockers"]
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert payload["boundary"] == (
        "frozen_core_calibration_review_validates_calibration_readiness_without_reopening_core_completion"
    )


def test_admin_targeted_calibration_candidate_review_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/calibration/targeted-candidate-review"
    )
    payload = route.endpoint(run_gate=False)

    assert payload["version"] == "v30.targeted_calibration_candidate_review.v1"
    assert payload["decision"]["targeted_calibration_review_ready"] is False
    assert "f1_calibration_baseline_not_ready" in payload["decision"]["blockers"]
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert payload["boundary"] == (
        "targeted_calibration_candidate_review_reviews_candidates_without_mutating_chart_facts_or_policy_pointers"
    )


def test_admin_targeted_calibration_validation_gate_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/calibration/targeted-validation-gate"
    )
    payload = route.endpoint(run_gate=False, sample_limit=1)

    assert payload["version"] == "v30.targeted_calibration_validation_gate.v1"
    assert payload["decision"]["validation_gate_ready"] is False
    assert "f2_candidate_review_not_ready" in payload["decision"]["blockers"]
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert payload["boundary"] == (
        "targeted_calibration_validation_gate_validates_candidates_without_mutating_policy_or_chart_facts"
    )


def test_admin_targeted_calibration_pointer_review_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/calibration/targeted-pointer-review"
    )
    payload = route.endpoint(run_gate=False, sample_limit=1)

    assert payload["version"] == "v30.targeted_calibration_pointer_review.v1"
    assert payload["decision"]["pointer_review_ready"] is False
    assert "f3_validation_gate_not_ready" in payload["decision"]["blockers"]
    assert payload["operator_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["operator_boundary"]["automatic_pointer_write_allowed"] is False
    assert payload["operator_boundary"]["chart_fact_mutation_allowed"] is False
    assert payload["boundary"] == (
        "targeted_calibration_pointer_review_inspects_evidence_without_mutating_policy_or_chart_facts"
    )


def test_admin_targeted_calibration_pointer_decision_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/calibration/targeted-pointer-decision"
    )
    payload = route.endpoint(run_gate=False, sample_limit=1, operator_decision="defer")

    assert payload["version"] == "v30.targeted_calibration_pointer_decision.v1"
    assert payload["decision"]["pointer_decision_recorded"] is False
    assert "f4_pointer_review_not_ready" in payload["decision"]["blockers"]
    assert payload["operator_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["operator_boundary"]["chart_fact_mutation_allowed"] is False
    assert payload["pointer_write_summary"]["pointer_write_performed"] is False
    assert payload["boundary"] == (
        "targeted_calibration_pointer_decision_records_decision_without_mutating_policy_or_chart_facts"
    )


def test_admin_targeted_calibration_closeout_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/calibration/targeted-closeout"
    )
    payload = route.endpoint(run_gate=False, sample_limit=1)

    assert payload["version"] == "v30.targeted_calibration_closeout.v1"
    assert payload["decision"]["closeout_ready"] is False
    assert "f5_pointer_decision_not_recorded" in payload["decision"]["blockers"]
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert payload["policy_boundary"]["core_module_reopen_allowed"] is False
    assert payload["boundary"] == (
        "targeted_calibration_closeout_records_monitoring_without_mutating_policy_or_chart_facts"
    )


def test_admin_mainline_selection_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/mainline/selection"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.mainline_selection.v1"
    assert payload["status"] == "ready_for_next_mainline"
    assert payload["decision"]["selected_task_id"] == "R13"
    assert payload["decision"]["full_pytest_run_now"] is False
    assert payload["verification_policy"]["full_pytest_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["core_completion_state"]["m1_m8_reopen_allowed"] is False
    assert payload["boundary"] == "m0_selects_next_mainline_after_f6_without_mutating_policy_or_chart_facts"


def test_admin_external_release_dry_run_endpoint_defers_full_pytest_by_default() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/external-dry-run"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8, full_pytest_decision="defer")

    assert payload["version"] == "v30.external_release_dry_run.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "external_release_dry_run_deferred_full_pytest"
    assert payload["decision"]["external_release_ready"] is False
    assert payload["decision"]["full_pytest_deferred"] is True
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["external_release_requirements"]["full_pytest_required_before_external_release"] is True
    assert payload["boundary"] == "r13_records_external_release_dry_run_without_running_full_pytest_by_default"


def test_admin_external_release_full_pytest_decision_endpoint_defers_by_default() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/full-pytest-decision"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8, full_pytest_decision="defer")

    assert payload["version"] == "v30.external_release_full_pytest_decision.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "external_release_full_pytest_deferred"
    assert payload["decision"]["external_release_ready"] is False
    assert payload["decision"]["external_release_blocked"] is True
    assert payload["decision"]["full_pytest_deferred"] is True
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["boundary"] == (
        "r14_makes_full_pytest_execution_explicit_and_keeps_external_release_blocked_when_deferred"
    )


def test_admin_external_release_blocked_status_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/blocked-status"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.external_release_blocked_status.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "external_release_blocked_pending_full_pytest"
    assert payload["decision"]["external_release_ready"] is False
    assert payload["decision"]["external_release_blocked"] is True
    assert payload["policy_boundary"]["external_release_allowed"] is False
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "R16"
    assert payload["boundary"] == "r15_records_external_release_blocked_pending_full_pytest"


def test_admin_post_release_boundary_authorization_endpoint_pauses_by_default() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/release/post-boundary-authorization"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8, authorization_decision="pause")

    assert payload["version"] == "v30.post_release_boundary_authorization.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "release_boundary_paused_pending_full_pytest_authorization"
    assert payload["decision"]["release_boundary_paused"] is True
    assert payload["decision"]["full_pytest_authorized"] is False
    assert payload["decision"]["full_pytest_run_triggered"] is False
    assert payload["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "M0"
    assert payload["boundary"] == "r16_records_pause_or_full_pytest_authorization_without_running_full_pytest"


def test_admin_mainline_selection_after_release_pause_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/mainline/selection-after-release-pause"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.mainline_selection_after_release_pause.v1"
    assert payload["status"] == "ready_for_next_mainline"
    assert payload["decision"]["decision_status"] == "core_monitoring_and_calibration_loop_selected"
    assert payload["decision"]["selected_task_id"] == "P0"
    assert payload["selected_non_release_mainline"]["title"] == "Core Module Monitoring And Calibration Loop"
    assert payload["policy_boundary"]["external_release_allowed"] is False
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["boundary"] == "m0_after_release_pause_selects_non_release_mainline"


def test_admin_core_monitoring_loop_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/monitoring-loop"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.core_monitoring_loop.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "core_monitoring_loop_ready"
    assert payload["decision"]["regression_detected"] is False
    assert payload["decision"]["core_module_reopen_recommended"] is False
    assert payload["monitoring_baseline_summary"]["check_count"] == 4
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "P1"
    assert payload["boundary"] == "p0_core_monitoring_loop_records_lightweight_monitoring_without_full_pytest"


def test_admin_lightweight_core_monitoring_checks_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/lightweight-monitoring-checks"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.lightweight_core_monitoring_checks.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "lightweight_core_monitoring_checks_passed"
    assert payload["decision"]["regression_detected"] is False
    assert payload["check_summary"]["passed_check_count"] == 4
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "P2"
    assert payload["boundary"] == "p1_executes_lightweight_core_monitoring_checks_without_full_pytest"


def test_admin_core_calibration_observation_summary_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/calibration-observation-summary"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.core_calibration_observation_summary.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "core_calibration_observation_summary_ready"
    assert payload["decision"]["stable_observation_count"] == 4
    assert payload["decision"]["regression_detected"] is False
    assert payload["decision"]["focused_module_fix_required"] is False
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "P3"
    assert payload["boundary"] == "p2_summarizes_core_calibration_observations_without_full_pytest"


def test_admin_core_calibration_drift_watch_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/calibration-drift-watch"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.core_calibration_drift_watch.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "core_calibration_drift_watch_ready"
    assert payload["decision"]["drift_detected"] is False
    assert payload["decision"]["focused_module_fix_required"] is False
    assert payload["drift_watch_policy"]["full_pytest_trigger"] == "explicit_release_or_full_freeze_decision_only"
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "P4"
    assert payload["boundary"] == "p3_establishes_core_calibration_drift_watch_without_full_pytest"


def test_admin_focused_core_calibration_evidence_queue_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/focused-calibration-evidence-queue"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.focused_core_calibration_evidence_queue.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "focused_core_calibration_evidence_queue_ready"
    assert payload["decision"]["queued_evidence_count"] == 0
    assert payload["decision"]["queue_item_count"] == 0
    assert payload["decision"]["focused_module_fix_required"] is False
    assert payload["queue_policy"]["batch_key"] == "m1_m8_module_target"
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "P5"
    assert payload["boundary"] == "p4_builds_focused_core_calibration_evidence_queue_without_full_pytest"


def test_admin_core_calibration_queue_review_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/calibration-queue-review"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.core_calibration_queue_review.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "core_calibration_queue_review_ready"
    assert payload["decision"]["reviewed_module_count"] == 0
    assert payload["decision"]["focused_module_fix_required"] is False
    assert payload["review_policy"]["fix_execution_allowed"] is False
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "P6"
    assert payload["boundary"] == "p5_reviews_core_calibration_queue_without_full_pytest"


def test_admin_core_calibration_watch_closeout_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/calibration-watch-closeout"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.core_calibration_watch_closeout.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "core_calibration_watch_closeout_ready"
    assert payload["decision"]["passed_closeout_check_count"] == 4
    assert payload["decision"]["current_cycle_closed"] is True
    assert payload["decision"]["future_monitoring_ready"] is True
    assert payload["watch_cycle_summary"]["future_evidence_entrypoint"] == "P4 Focused Core Calibration Evidence Queue"
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "P7"
    assert payload["boundary"] == "p6_closes_core_calibration_watch_without_full_pytest"


def test_admin_core_monitoring_cadence_baseline_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/monitoring-cadence-baseline"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.core_monitoring_cadence_baseline.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "core_monitoring_cadence_baseline_ready"
    assert payload["decision"]["current_cycle_closed"] is True
    assert payload["decision"]["future_monitoring_ready"] is True
    assert payload["cadence_rules"]["default_cadence"] == "on_new_calibration_evidence_only"
    assert payload["trigger_matrix"][1]["entrypoint"] == "P4 Focused Core Calibration Evidence Queue"
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "P8"
    assert payload["boundary"] == "p7_establishes_core_monitoring_cadence_without_full_pytest"


def test_admin_core_monitoring_cadence_documentation_sync_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/monitoring-cadence-documentation-sync"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.core_monitoring_cadence_documentation_sync.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "core_monitoring_cadence_documentation_sync_ready"
    assert payload["decision"]["synced_document_count"] == payload["decision"]["required_document_count"]
    assert payload["documentation_policy"]["default_cadence"] == "on_new_calibration_evidence_only"
    assert payload["documentation_policy"]["future_evidence_entrypoint"] == "P4 Focused Core Calibration Evidence Queue"
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "P9"
    assert payload["boundary"] == "p8_syncs_core_monitoring_cadence_docs_without_full_pytest"


def test_admin_core_monitoring_steady_state_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/monitoring-steady-state"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.core_monitoring_steady_state.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "core_monitoring_steady_state_ready"
    assert payload["decision"]["waiting_for_new_evidence"] is True
    assert payload["steady_state_policy"]["default_action"] == "wait_for_new_calibration_evidence"
    assert payload["steady_state_policy"]["new_evidence_entrypoint"] == "P4 Focused Core Calibration Evidence Queue"
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "S0"
    assert payload["boundary"] == "p9_enters_core_monitoring_steady_state_without_full_pytest"


def test_admin_core_monitoring_s0_status_endpoint_is_read_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/core/monitoring-s0-status"
    )
    payload = route.endpoint(run_gate=False, sample_limit=8)

    assert payload["version"] == "v30.core_monitoring_s0_status.v1"
    assert payload["status"] == "completed"
    assert payload["decision"]["decision_status"] == "core_monitoring_s0_status_ready"
    assert payload["decision"]["waiting_for_new_evidence"] is True
    assert payload["decision"]["new_core_monitoring_task_allowed_by_default"] is False
    assert payload["s0_policy"]["new_evidence_entrypoint"] == "P4 Focused Core Calibration Evidence Queue"
    assert payload["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert payload["policy_boundary"]["pointer_write_allowed"] is False
    assert payload["next_mainline_selection"]["task_id"] == "S0"
    assert payload["boundary"] == "s0_records_steady_state_without_full_pytest"


def test_ui_capabilities_expose_projection_params() -> None:
    route = next(route for route in app.routes if getattr(route, "path", "") == "/api/v30/ui/capabilities")
    payload = route.endpoint()
    assert payload["version"] == "v30.ui_capabilities.v1"
    assert payload["default_role"] == "user"
    assert payload["default_locale"] == "zh"
    assert payload["default_client"] == "web"
    assert [row["key"] for row in payload["locales"]] == ["zh", "en", "ko"]
    assert [row["key"] for row in payload["clients"]] == ["web", "mobile", "admin"]
    assert [row["key"] for row in payload["roles"]] == ["guest", "user", "practitioner", "admin"]
    assert payload["supported_view_params"]["role"] == ["guest", "user", "practitioner", "admin"]
    assert payload["api_contract"]["version"] == "v30.ui_api_contract.v1"
    assert "selected_option" in payload["api_contract"]["structured_answer_fields"]
    assert payload["api_contract"]["interaction_brain_result_contract"] == "v30.unified_interaction_brain_result.v1"
    assert payload["api_contract"]["diagnostic_summary_contract"] == "v30.interaction_brain_diagnostics_summary.v1"
    assert payload["api_contract"]["synthetic_tier"] == "interaction_brain_structured_constraints"
    assert payload["api_contract"]["dedicated_interactions_endpoint"] == "deferred_until_answer_endpoint_stable"
    assert payload["api_contract"]["enhance_answer_with_llm"].endswith("/answer/llm")
    assert payload["api_contract"]["llm_answer_enhancement_mode"] == "fast_answer_then_optional_llm_enhancement"
    assert payload["boundary"] == "ui_capabilities_describe_projection_not_bazi_facts"


def test_product_auth_allows_only_one_admin(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    local_app = create_app()
    route = next(route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/auth/register")

    first = route.endpoint(
        AuthRegisterRequest(
            username="admin@example.com",
            password="secret123",
            display_name="管理员",
            role="admin",
        )
    )

    assert first["status"] == "registered"
    assert first["user"]["role"] == "admin"
    with pytest.raises(HTTPException) as exc:
        route.endpoint(
            AuthRegisterRequest(
                username="second-admin@example.com",
                password="secret123",
                display_name="第二管理员",
                role="admin",
            )
        )
    assert exc.value.status_code == 409
    assert exc.value.detail == "admin already exists"


def test_smoke_runtime_and_view_contract() -> None:
    runtime = create_smoke_runtime(reading_id="test-reading")
    view = build_presentation_model(runtime, role_key="user", locale="zh", client="web")
    payload = view.model_dump(mode="json")
    assert payload["reading_id"] == "test-reading"
    assert payload["role_key"] == "user"
    assert payload["layout"]["version"] == "v30.presentation.v1"
    assert payload["layout"]["role_profile"]["role_key"] == "user"
    assert payload["layout"]["role_profile"]["surface"] == "customer_reading"
    assert payload["layout"]["portrait_projection_view_summary"]["roles"] == ["user"]
    assert payload["layout"]["rendered_question_label_summary"]["roles"] == ["user"]
    assert payload["header"]["title"] == "启智 V30"
    assert payload["questions"]
    assert all(question["anchor_status"] == "bound" for question in payload["questions"])
    assert all("score" in question for question in payload["questions"])
    assert all("stage" in question for question in payload["questions"])
    assert all("options" in question for question in payload["questions"])
    assert all(question["label_source"] == "expression_rendered_question_label" for question in payload["questions"])
    assert runtime.question_plan.recommended_questions
    assert payload["questions"][0]["question_id"] == "q_v30_user_career_direction"
    assert payload["questions"][0]["interaction_type"] == "user_question"
    assert not any(question["topic"] == "hidden_factor" for question in payload["questions"])
    assert any(row["topic"] == "hidden_factor" for row in runtime.question_plan.recommended_questions)
    assert runtime.question_plan.hidden_factor_probes


def test_api_local_json_repository_persists_reading(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V30_REPOSITORY", "local_json")
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.delenv("V30_DATABASE_URL", raising=False)
    monkeypatch.delenv("V30_REDIS_URL", raising=False)
    local_app = create_app()
    route_paths = {getattr(route, "path", "") for route in local_app.routes}
    assert "/api/v30/readings" in route_paths
    assert "/api/v30/readings/history" in route_paths
    # Call endpoint function directly to avoid TestClient compatibility issues in this environment.
    create_route = next(route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/readings")
    response = create_route.endpoint(type("Payload", (), {"reading_id": "api-local", "day_master": "甲", "day_master_element": "wood", "locale": "zh"})())
    assert response["reading_id"] == "api-local"
    assert response["trace_id"]
    assert (tmp_path / ".runtime" / "readings" / "api-local.json").exists()
    assert (tmp_path / ".runtime" / "traces" / f"{response['trace_id']}.json").exists()

    trace_route = next(
        route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/admin/runs/{reading_id}/trace"
    )
    trace_response = trace_route.endpoint("api-local")
    assert trace_response["reading_id"] == "api-local"
    assert trace_response["trace_id"] == response["trace_id"]
    assert trace_response["trace"]["trace_id"] == response["trace_id"]

    feedback_route = next(
        route
        for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/readings/{reading_id}/hidden-factor/feedback"
    )
    state_payload = feedback_route.endpoint(
        "api-local",
        {
            "feedback_id": "api-hidden-feedback",
            "special_event_year": 2024,
            "repeated_state": "career_pressure_repeat",
        },
    )
    assert state_payload["reading_id"] == "api-local"
    assert state_payload["status"] in {"dialogue_in_progress", "amplifier_candidate"}
    state_route = next(
        route
        for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/readings/{reading_id}/hidden-factor/state"
    )
    stored_state = state_route.endpoint("api-local")
    assert stored_state["state_id"] == "api-local:hidden_factor_state"

    answer_route = next(
        route
        for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/readings/{reading_id}/questions/{question_id}/answer"
    )
    answer_response = answer_route.endpoint(
        "api-local",
        "q_v30_hidden_factor_boundary_discovery",
        AnswerRequest(
            answer="2021 and 2024 repeated as career pressure.",
            outcome_status="answered",
            selected_option="domain:career",
            structured_payload={
                "years": [2021, 2024],
                "state_tags": ["career_pressure"],
                "intensity": "medium",
                "recurrence": "repeated",
                "confidence": "certain",
            },
            confidence=0.82,
            feedback_tags=["career", "hidden_factor_followup"],
        ),
    )
    assert answer_response["accepted"] is True
    assert answer_response["question_outcome_consumed"] is True
    assert answer_response["interaction_brain_result"]["version"] == "v30.unified_interaction_brain_result.v1"
    assert answer_response["interaction_brain_result"]["valid"] is True
    assert answer_response["interaction_brain_result"]["allowed_to_update_hidden_factor"] is True
    assert answer_response["interaction_brain_result"]["chart_fact_mutation_allowed"] is False
    assert answer_response["interaction_brain_result"]["hidden_factor_feedback_saved"] is True
    assert answer_response["interaction_brain_result"]["hidden_factor_state_status"] in {"dialogue_in_progress", "amplifier_candidate"}
    assert "hidden_factor_feedback_payload" not in answer_response["interaction_brain_result"]
    assert answer_response["view"]["reading_surface"]["version"] == "v30.customer_reading_surface.v1"
    assert answer_response["view"]["answer_panel"]["llm_metadata"]["status"] in {"accepted", "fallback", "deferred"}
    updated_trace = trace_route.endpoint("api-local")
    outcomes = updated_trace["trace"]["question_plan"]["session_state"]["question_outcomes"]
    assert outcomes[0]["question_id"] == "q_v30_hidden_factor_boundary_discovery"
    assert outcomes[0]["boundary"] == "question_outcome_feedback_not_chart_fact"
    assert outcomes[0]["interaction_turn_signal"]["structured_payload"]["state_tags"] == ["career_pressure"]
    assert outcomes[0]["interaction_turn_signal"]["allowed_to_update_chart_facts"] is False
    replay = updated_trace["trace"]["question_plan"]["policy_effect"]["adaptive_question_diagnostics"]
    assert replay["decision_count"] == len(updated_trace["trace"]["question_plan"]["recommended_questions"])
    assert replay["replay_controls"]["can_replay_from_runtime_trace"] is True

    view_route = next(
        route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/readings/{reading_id}/view"
    )
    view_payload = view_route.endpoint("api-local", role="admin", locale="zh", client="web")
    assert view_payload["diagnostics"]["hidden_factor_state"]["state_id"] == "api-local:hidden_factor_state"
    assert view_payload["diagnostics"]["latent_bazi_profile"]["version"] == "v30.latent_bazi_profile.v1"
    assert view_payload["diagnostics"]["latent_bazi_profile"]["reading_id"] == "api-local"
    assert view_payload["diagnostics"]["latent_bazi_profile"]["chart_fact_mutation_allowed"] is False
    assert view_payload["diagnostics"]["latent_bazi_profile_summary"]["active_state_tags"] == ["career_pressure"]
    assert view_payload["diagnostics"]["latent_bazi_attributes"]["version"] == "v30.latent_bazi_attributes.v1"
    assert view_payload["diagnostics"]["latent_bazi_attributes"]["status"] == "inferred"
    assert view_payload["diagnostics"]["latent_bazi_attributes"]["chart_fact_mutation_allowed"] is False
    assert view_payload["diagnostics"]["latent_bazi_attributes"]["calculation_modifiers"]["individualization_ready"] is True
    assert "career_bias" in view_payload["diagnostics"]["latent_bazi_attributes_summary"]["active_domain_biases"]
    latent_debug = view_payload["reading_surface"]["core_bazi_reading"]["latent_bazi_attributes"]
    assert latent_debug["display_mode"] == "debug_raw_values"
    assert latent_debug["debug_temporary_remove_later"] is True
    assert latent_debug["status"] == "inferred"
    assert latent_debug["boundary"] == "customer_latent_attributes_debug_raw_values_are_temporary_projection_not_chart_fact"
    debug_sections = {section["section_id"]: section for section in latent_debug["debug_sections"]}
    assert set(debug_sections) == {"global_attributes", "ten_god_modifiers", "domain_biases", "stability_thresholds"}
    global_rows = {row["key"]: row for row in debug_sections["global_attributes"]["rows"]}
    ten_god_rows = {row["key"]: row for row in debug_sections["ten_god_modifiers"]["rows"]}
    domain_rows = {row["key"]: row for row in debug_sections["domain_biases"]["rows"]}
    threshold_rows = {row["key"]: row for row in debug_sections["stability_thresholds"]["rows"]}
    assert global_rows["resource_index"]["score"] > 0.5
    assert global_rows["risk_index"]["score"] > 0.5
    assert ten_god_rows["authority"]["score"] > 1.0
    assert ten_god_rows["resource"]["score"] > 1.0
    assert domain_rows["career_bias"]["score"] > 0.5
    assert threshold_rows["event_trigger_sensitivity"]["score"] > 0.5
    assert view_payload["diagnostics"]["latent_bazi_individualized_projection"]["version"] == "v30.latent_bazi_individualized_model_projection.v1"
    assert view_payload["diagnostics"]["latent_bazi_individualized_projection"]["individualization_ready"] is True
    assert view_payload["diagnostics"]["latent_bazi_individualized_projection"]["chart_fact_mutation_allowed"] is False
    assert view_payload["diagnostics"]["latent_bazi_individualized_projection"]["base_ten_god_energy_mutation_allowed"] is False
    assert view_payload["diagnostics"]["latent_bazi_individualized_projection"]["ranked_decision_mutation_allowed"] is False
    assert "career" in view_payload["diagnostics"]["latent_bazi_individualized_projection_summary"]["adjusted_domains"]
    assert "api-local:uib:q_v30_hidden_factor_boundary_discovery" in view_payload["diagnostics"]["hidden_factor_state"]["feedback_ids"]
    assert "career_pressure" in view_payload["diagnostics"]["hidden_factor_state"]["repeated_states"]
    assert view_payload["diagnostics"]["question_outcomes"][0]["question_id"] == "q_v30_hidden_factor_boundary_discovery"
    assert view_payload["diagnostics"]["interaction_brain_summary"]["version"] == "v30.interaction_brain_diagnostics_summary.v1"
    assert view_payload["diagnostics"]["interaction_brain_summary"]["latest_constraint_valid"] is True
    assert view_payload["diagnostics"]["interaction_brain_summary"]["chart_fact_mutation_allowed"] is False
    assert view_payload["diagnostics"]["interaction_brain_summary"]["internal_feedback_payload_visible"] is True
    assert "question_dialogue_outcome_consumed" in view_payload["diagnostics"]["question_dialogue_graph"]["policy_notes"]
    assert "persisted_hidden_factor_state_can_condition_followups" in view_payload["diagnostics"]["question_dialogue_graph"]["policy_notes"]
    assert view_payload["diagnostics"]["llm_output_contract_summary"]["validation_status"] == "passed"
    assert view_payload["diagnostics"]["llm_output_contract_summary"]["contract_count"] == 4
    assert view_payload["diagnostics"]["llm_provider_readiness"]["version"] == "v30.llm_provider_readiness.v1"
    assert view_payload["diagnostics"]["llm_answer_draft_call"]["version"] in {
        "v30.llm_answer_draft_call.v1",
        "v30.bazi_llm_answer_draft_call.v1",
    }
    assert view_payload["diagnostics"]["macro_portrait_view_summary"]["roles"] == ["admin"]
    assert view_payload["diagnostics"]["rendered_question_label_summary"]["fallback_count"] == 0
    assert view_payload["diagnostics"]["adaptive_question_diagnostics"]["version"] == "v30.adaptive_question_diagnostics.v1"

    replay_route = next(
        route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/admin/runs/{reading_id}/question-replay"
    )
    replay_payload = replay_route.endpoint("api-local")
    assert replay_payload["reading_id"] == "api-local"
    assert replay_payload["adaptive_question_diagnostics"]["decision_rows"]

    artifact_route = next(
        route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/admin/validation/518k/artifacts"
    )
    artifact_payload = artifact_route.endpoint(mode="sample", limit=5)
    assert artifact_payload["backend"] == "json_fallback"
    assert "artifacts" in artifact_payload

    readiness_route = next(
        route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/admin/validation/518k/readiness-matrix"
    )
    readiness_payload = readiness_route.endpoint(sample_limit=2, shard_id=7, shard_limit=2)
    assert readiness_payload["version"] == "v30.518k_readiness_matrix.v1"
    assert readiness_payload["decision"]["decision_status"] == "bt9_518k_readiness_matrix_ready"
    assert readiness_payload["mode_readiness"]["full"]["run_executed"] is False
    assert readiness_payload["next_mainline_selection"]["task_id"] == "BT10"


def test_api_birth_input_creates_ready_runtime_or_returns_trace(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V30_REPOSITORY", "local_json")
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    local_app = create_app()
    create_route = next(route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/readings")

    ready_response = create_route.endpoint(
        ReadingRequest(
            reading_id="api-birth-ready",
            locale="zh",
            target_year=2030,
            actor_id="user-001",
            session_id="session-001",
            birth_input={
                "input_id": "api-birth-ready-input",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            },
        )
    )
    assert ready_response["status"] == "ready"
    assert ready_response["trace_id"] == "api-birth-ready:trace:birth-input"
    assert ready_response["chart_build"]["pillars"]["day"] == "庚子"
    assert (tmp_path / ".runtime" / "readings" / "api-birth-ready.json").exists()

    view_route = next(
        route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/readings/{reading_id}/view"
    )
    view_payload = view_route.endpoint("api-birth-ready", role="admin", locale="zh", client="web")
    assert view_payload["chart_summary"]["day_master"] == "庚"
    assert view_payload["diagnostics"]["actor_context"]["actor_id"] == "user-001"
    assert view_payload["diagnostics"]["actor_context"]["session_id"] == "session-001"
    assert view_payload["diagnostics"]["chart_build_source"]["source_type"] == "birth_input"
    assert view_payload["diagnostics"]["calendar_conversion_trace"]["status"] == "ready"

    user_view = view_route.endpoint("api-birth-ready", role="user", locale="zh", client="web")
    assert user_view["reading_surface"]["surface_type"] == "customer_reading_loop"
    assert user_view["reading_surface"]["time_context"]["version"] == "v30.customer_time_context.v1"
    assert user_view["reading_surface"]["time_context"]["target_year"] == 2030
    assert len(user_view["reading_surface"]["time_context"]["six_pillars"]) >= 6
    assert user_view["reading_surface"]["time_context"]["current_luck"]["pillar"]
    top_question_id = user_view["reading_surface"]["next_question"]["question_id"]
    answer_route = next(
        route
        for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/readings/{reading_id}/questions/{question_id}/answer"
    )
    interaction_response = answer_route.endpoint(
        "api-birth-ready",
        top_question_id,
        AnswerRequest(
            answer="我主要想先看事业方向，近两年压力比较明显。",
            role="user",
            locale="en",
            client="mobile",
            outcome_status="answered",
            selected_option="career:pressure",
            confidence=0.74,
            feedback_tags=["customer_loop", "career"],
        ),
    )
    assert interaction_response["accepted"] is True
    assert interaction_response["view"]["locale"] == "en"
    assert interaction_response["view"]["client"] == "mobile"
    assert interaction_response["view"]["layout"]["density"] == "compact"
    assert interaction_response["view"]["reading_surface"]["surface_type"] == "customer_reading_loop"
    assert interaction_response["view"]["reading_surface"]["next_question"]["question_id"] != top_question_id
    assert interaction_response["view"]["answer_panel"]["source"] in {
        "llm_bounded_answer_draft",
        "llm_bazi_answer_draft",
        "rule_bound_fallback",
        "rule_bound_llm_deferred",
    }
    assert interaction_response["view"]["answer_panel"]["llm_metadata"]["boundary"] in {
        "llm_answer_draft_expression_only_no_chart_fact_mutation",
        "llm_fallback_keeps_rule_answer_and_does_not_mutate_chart_facts",
        "fast_sync_mode_returns_rule_bound_rbd_answer_without_waiting_for_llm",
    }
    history_route = next(
        route for route in local_app.routes if getattr(route, "path", "") == "/api/v30/readings/history"
    )
    history_payload = history_route.endpoint(
        actor_id="user-001",
        session_id="session-001",
        role="user",
        locale="zh",
        client="web",
        limit=10,
    )
    assert history_payload["version"] == "v30.reading_history_projection.v1"
    assert history_payload["count"] == 1
    assert history_payload["owner_filter"]["version"] == "v30.reading_history_ownership.v1"
    assert history_payload["owner_filter"]["scope"] == "actor_and_session"
    assert history_payload["owner_filter"]["actor_id_present"] is True
    assert history_payload["owner_filter"]["session_id_present"] is True
    assert "actor_id" not in history_payload["owner_filter"]
    assert "session_id" not in history_payload["owner_filter"]
    assert history_payload["visibility_contract"]["guest_user_internal_fields_hidden"] is True
    assert history_payload["diagnostics"] == {}
    assert history_payload["items"][0]["reading_id"] == "api-birth-ready"
    assert history_payload["items"][0]["visible_next_question_id"]
    assert history_payload["items"][0]["owner_match"]["scope"] == "actor_and_session"
    assert history_payload["items"][0]["owner_match"]["diagnostic_ids_visible"] is False
    assert "actor_context" not in history_payload["items"][0]
    assert "trace_id" not in history_payload["items"][0]
    assert "internal_next_question_id" not in history_payload["items"][0]
    admin_history = history_route.endpoint(
        actor_id="user-001",
        session_id="session-001",
        role="admin",
        locale="zh",
        client="admin",
        limit=10,
    )
    assert admin_history["owner_filter"]["actor_id"] == "user-001"
    assert admin_history["owner_filter"]["session_id"] == "session-001"
    assert admin_history["visibility_contract"]["diagnostic_role"] is True
    assert admin_history["diagnostics"]["trace_ids"] == ["api-birth-ready:trace:birth-input"]
    assert admin_history["items"][0]["actor_context"]["actor_id"] == "user-001"
    assert admin_history["items"][0]["actor_context"]["session_id"] == "session-001"
    assert admin_history["items"][0]["trace_id"] == "api-birth-ready:trace:birth-input"
    assert admin_history["items"][0]["internal_next_question_id"]

    practitioner_history = history_route.endpoint(
        actor_id="user-001",
        session_id="session-001",
        role="practitioner",
        locale="zh",
        client="web",
        limit=10,
    )
    assert practitioner_history["visibility_contract"]["diagnostic_role"] is True
    assert practitioner_history["items"][0]["actor_context"]["actor_id"] == "user-001"

    with pytest.raises(HTTPException) as exc_info:
        history_route.endpoint(actor_id="", session_id="", role="user", locale="zh", client="web", limit=10)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "actor_id or session_id is required"
    with pytest.raises(HTTPException) as actor_only_exc:
        history_route.endpoint(actor_id="user-001", session_id="", role="user", locale="zh", client="web", limit=10)
    assert actor_only_exc.value.status_code == 400
    assert actor_only_exc.value.detail == "actor_id and session_id are required for customer history"
    with pytest.raises(HTTPException) as session_only_exc:
        history_route.endpoint(actor_id="", session_id="session-001", role="guest", locale="zh", client="mobile", limit=10)
    assert session_only_exc.value.status_code == 400
    assert session_only_exc.value.detail == "actor_id and session_id are required for customer history"

    pending_response = create_route.endpoint(
        ReadingRequest(
            reading_id="api-birth-unknown-hour",
            locale="zh",
            birth_input={
                "input_id": "api-birth-unknown-hour-input",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "timezone": "Asia/Shanghai",
                "unknown_hour": True,
            },
        )
    )
    assert pending_response["status"] == "pending"
    assert "trace_id" not in pending_response
    assert pending_response["chart_build"]["pillars"] == {}
    assert "unknown_hour_blocks_hour_pillar" in pending_response["failures"]
    assert not (tmp_path / ".runtime" / "readings" / "api-birth-unknown-hour.json").exists()
