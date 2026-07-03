from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse

from v40 import __version__
from v40.api.models import (
    AcceptanceWindowFromRuntimeRequest,
    BaziProfileCreateRequest,
    BaziProfileUpdateRequest,
    BatchTrainerV1Request,
    CandidateWeightFromBatchRequest,
    CandidateWeightFromReplayBatchRequest,
    ConsentGrantRequest,
    ConversationTurnRequest,
    DirectTrainingActivationEvidenceRequest,
    EvaluationBatchFromRuntimeRequest,
    EvaluationRunFromRuntimeRequest,
    ExpressionFromRuntimeRequest,
    MingliAssetMigrationGateRequest,
    NativeBatchFromSeedsRequest,
    NativeBaziRuntimeRequest,
    NativeReadingReportRequest,
    OnlineCutoverDecisionRequest,
    PractitionerCalibrationRequest,
    PractitionerLensActionRequest,
    PractitionerReviewAssignRequest,
    PractitionerReviewCreateRequest,
    PractitionerReviewResultRequest,
    ProbeAnswerRequest,
    RealCaseAcceptancePackRequest,
    RealCaseExpansionEvidenceRequest,
    ReleaseReadinessFromBatchesRequest,
    ReleaseReadinessFromEvidenceBatchesRequest,
    ShadowCompareBatchRequest,
    SyntheticCasesFromSeedsRequest,
    TrainingExampleFromReadingRequest,
    TrainingExampleReplayRequest,
    TrainingReplayBatchRequest,
    TrainingImpactFromEvaluationRequest,
    UserLoginRequest,
    UserRegisterRequest,
    WeightActivationExecutionRequest,
    WeightActivationReviewRequest,
)
from v40.auth.accounts import (
    BUILTIN_ADMIN_USER_ID,
    build_builtin_admin_account,
    build_user_account,
    build_user_session,
    is_builtin_admin_identifier,
    normalize_email,
    normalize_login_identifier,
    verify_password,
)
from v40.auth import resolve_user_app_session_context
from v40.auth.session import USER_APP_ROLE_COOKIE, USER_APP_SESSION_COOKIE, role_context_from_payload_or_session
from v40.contracts.evaluation import EvaluationCaseSpec, ReleaseGateResult
from v40.contracts.context import EngineContext
from v40.contracts.manifest import contract_manifest
from v40.contracts.output import LLMExpressionResult
from v40.contracts.training import LabelSource, TrainablePolicyRegistry, TrainingLabelEvent
from v40.contracts.user import BaziProfileRecord, UserAccountInternal, UserSessionRecord
from v40.conversation import build_conversation_seeds, build_conversation_turn, build_training_label_from_conversation_turn
from v40.engines import build_native_bazi_runtime
from v40.evaluation import (
    build_acceptance_window_from_runtime,
    build_evaluation_batch_summary,
    build_release_readiness_from_batches,
    build_release_readiness_from_evidence_batches,
    build_shadow_compare_batch_summary,
    build_shadow_compare_result,
    build_training_replay_batch_summary,
    evaluate_cases_against_runtime,
    evaluate_native_seeds,
    evaluate_runtime_against_case,
    replay_training_example,
)
from v40.migration import V30ExportEnvelope, build_mingli_asset_migration_gate, build_runtime_from_v30_export
from v40.migration.admin_v30_profiles import (
    build_chart_payload_from_v30_birth_input,
    convert_v30_profile_to_v40,
    default_v30_product_store_path,
    load_v30_product_store,
    select_v30_admin_profiles,
)
from v40.probes import build_probe_answer_result
from v40.review import (
    build_consent_grant,
    build_practitioner_review_request,
    build_practitioner_review_result,
    build_review_queue_item,
)
from v40.project import (
    build_horizontal_runtime_context_status,
    build_mingli_depth_index,
    build_module_migration_status,
    build_online_cutover_decision_pack,
    build_production_cutover_checklist,
    build_direct_training_activation_evidence,
    build_real_case_acceptance_pack,
    build_real_case_expansion_evidence_pack,
    build_project_status,
    build_release_candidate_audit,
    build_production_smoke,
    build_trainable_runtime_spine_status,
    build_v30_replacement_readiness,
)
from v40.storage import V40PostgresRepository
from v40.storage.config import v40_repository_configured
from v40.synthetic import build_evaluation_cases_from_seeds
from v40.expression import (
    OllamaExpressionError,
    accept_expression_result,
    build_expression_telemetry,
    build_expression_task_from_runtime,
    list_ollama_models,
    render_local_expression_result,
    render_ollama_expression_result,
    resolve_ollama_expression_config,
)
from v40.training import (
    build_batch_trainer_v1,
    build_candidate_weight_version_from_batch,
    build_candidate_weight_version_from_replay_batch,
    build_practitioner_lens_action,
    build_training_example_from_labels,
    build_training_impact_from_evaluation,
    build_weight_activation_execution,
    build_weight_activation_review,
)


API_PREFIX = "/api/v40"


_MEMORY_ACCOUNTS_BY_EMAIL: dict[str, UserAccountInternal] = {}
_MEMORY_ACCOUNTS_BY_ID: dict[str, UserAccountInternal] = {}
_MEMORY_SESSIONS: dict[str, UserSessionRecord] = {}
_MEMORY_PROFILES_BY_USER: dict[str, dict[str, BaziProfileRecord]] = {}
_MEMORY_ADMIN_PROFILES_BOOTSTRAPPED = False


def _surface_beta_check(key: str, label: str, ready: bool, evidence: str) -> dict[str, object]:
    return {
        "key": key,
        "label": label,
        "ready": ready,
        "evidence": evidence,
    }


def _build_surface_beta_readiness() -> dict[str, object]:
    html = _user_ui_html()
    checks = [
        _surface_beta_check(
            "report_first",
            "报告优先",
            "/api/v40/readings/native-report" in html and "判断与建议" in html and "核心判断" in html,
            "用户先看到完整报告，而不是先进入聊天。",
        ),
        _surface_beta_check(
            "conversation_after_report",
            "报告后追问",
            "/api/v40/conversation/turn" in html and "followupHub" in html,
            "智能对话独立于测算报告之后。",
        ),
        _surface_beta_check(
            "feedback_to_training",
            "反馈入训练",
            "/api/v40/training/labels" in html and "reportFeedback" in html,
            "用户反馈进入本地训练素材，不直接改生产权重。",
        ),
        _surface_beta_check(
            "practitioner_calibration",
            "命理师校准",
            "practitioner-lens-action" in html and "专业视角" in html and "lensToggleButton" in html,
            "命理师可校准分支，校准只影响训练素材。",
        ),
        _surface_beta_check(
            "admin_separated",
            "Admin 分离",
            "/admin/v40" not in html,
            "用户主页面不暴露 Admin 控制面。",
        ),
        _surface_beta_check(
            "no_local_fallback_when_llm_required",
            "无静默 fallback",
            "没有使用备用文本" in html and "智能服务未完成" in html,
            "模型不可用时明确提示，不伪造智能表达。",
        ),
    ]
    ready_count = sum(1 for check in checks if check["ready"])
    percent = int(round(ready_count / len(checks) * 100)) if checks else 0
    return {
        "beta_ready_percent": percent,
        "beta_status": "ready" if percent == 100 else "review",
        "ready_count": ready_count,
        "check_count": len(checks),
        "checks": checks,
    }


def _build_expression_bundle(
    *,
    task_id: str,
    result_id: str,
    acceptance_id: str,
    runtime,
    role_key,
    topic,
    execution_mode: str,
    provider_text: str = "",
    provider: str = "local_expression_adapter",
    model: str = "v40.expression.contract.v1",
    raw_thinking: str = "",
) -> tuple[object, LLMExpressionResult, object, object]:
    task = build_expression_task_from_runtime(
        task_id=task_id,
        runtime=runtime,
        role_key=role_key,
        topic=topic,
    )
    if execution_mode == "provider_text":
        result = LLMExpressionResult(
            result_id=result_id,
            task_id=task.task_id,
            reading_id=runtime.reading_id,
            text=provider_text,
            raw_thinking=raw_thinking,
            provider=provider,
            model=model,
        )
    elif execution_mode == "ollama":
        result = render_ollama_expression_result(
            result_id=result_id,
            task=task,
            runtime=runtime,
        )
    else:
        result = render_local_expression_result(
            result_id=result_id,
            task=task,
            runtime=runtime,
            provider=provider,
            model=model,
        )
    acceptance = accept_expression_result(
        result_id=acceptance_id,
        task=task,
        result=result,
        runtime=runtime,
    )
    telemetry = build_expression_telemetry(
        telemetry_id=f"telemetry:{result_id}",
        task=task,
        result=result,
        acceptance=acceptance,
        execution_mode=execution_mode,
    )
    return task, result, acceptance, telemetry


def _resolve_active_policy_engine_context(payload_engine_context: EngineContext | None) -> EngineContext | None:
    if payload_engine_context is not None:
        return payload_engine_context
    if not v40_repository_configured():
        return None
    try:
        repository = V40PostgresRepository.from_env()
        active_registry = repository.get_active_trainable_policy_registry()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="V40 active policy registry is unavailable") from exc
    if not active_registry:
        return None
    policy_version = str(active_registry.get("active_policy_version") or "").strip()
    if not policy_version:
        return None
    return EngineContext(engine_policy_version=policy_version)


def _repository_or_none() -> V40PostgresRepository | None:
    if not v40_repository_configured():
        return None
    return V40PostgresRepository.from_env()


def _load_account_by_email(email: str) -> UserAccountInternal | None:
    clean_email = normalize_email(email)
    repository = _repository_or_none()
    if repository is not None:
        account = repository.get_user_account_by_email(clean_email)
        if account is not None:
            return account
        if is_builtin_admin_identifier(clean_email):
            return _save_and_return_builtin_admin(repository)
        return None
    account = _MEMORY_ACCOUNTS_BY_EMAIL.get(clean_email)
    if account is not None:
        return account
    if is_builtin_admin_identifier(clean_email):
        return _save_and_return_builtin_admin(None)
    return None


def _load_account_by_login(identifier: str) -> UserAccountInternal | None:
    return _load_account_by_email(normalize_login_identifier(identifier))


def _load_account_by_id(user_id: str) -> UserAccountInternal | None:
    repository = _repository_or_none()
    if repository is not None:
        account = repository.get_user_account_by_id(user_id)
        if account is not None:
            return account
        if user_id == BUILTIN_ADMIN_USER_ID:
            return _save_and_return_builtin_admin(repository)
        return None
    account = _MEMORY_ACCOUNTS_BY_ID.get(user_id)
    if account is not None:
        return account
    if user_id == BUILTIN_ADMIN_USER_ID:
        return _save_and_return_builtin_admin(None)
    return None


def _save_and_return_builtin_admin(repository: V40PostgresRepository | None) -> UserAccountInternal:
    account = build_builtin_admin_account()
    if repository is not None:
        existing = repository.get_user_account_by_email(account.email) or repository.get_user_account_by_id(account.user_id)
        if existing is not None:
            return existing
        repository.save_user_account(account)
        return account
    _MEMORY_ACCOUNTS_BY_EMAIL[account.email] = account
    _MEMORY_ACCOUNTS_BY_ID[account.user_id] = account
    return account


def _save_account(account: UserAccountInternal) -> bool:
    repository = _repository_or_none()
    if repository is not None:
        repository.save_user_account(account)
        return True
    _MEMORY_ACCOUNTS_BY_EMAIL[account.email] = account
    _MEMORY_ACCOUNTS_BY_ID[account.user_id] = account
    return False


def _save_session(session: UserSessionRecord) -> bool:
    repository = _repository_or_none()
    if repository is not None:
        repository.save_user_session(session)
        return True
    _MEMORY_SESSIONS[session.session_id] = session
    return False


def _session_token_from_request(request: Request) -> str:
    return (
        request.cookies.get(USER_APP_SESSION_COOKIE, "").strip()
        or request.headers.get("x-v40-session-id", "").strip()
    )


def _authenticated_account(request: Request) -> tuple[UserAccountInternal, UserSessionRecord]:
    session_id = _session_token_from_request(request)
    if not session_id:
        raise HTTPException(status_code=401, detail="Please login first")
    repository = _repository_or_none()
    session = repository.get_user_session(session_id) if repository is not None else _MEMORY_SESSIONS.get(session_id)
    if session is None or session.revoked:
        raise HTTPException(status_code=401, detail="Session is not valid")
    if session.expires_at and session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session has expired")
    account = _load_account_by_id(session.user_id)
    if account is None or not account.active:
        raise HTTPException(status_code=401, detail="Account is not active")
    return account, session


def _optional_authenticated_account(request: Request) -> tuple[UserAccountInternal, UserSessionRecord] | None:
    try:
        return _authenticated_account(request)
    except HTTPException:
        return None


def _set_user_cookies(response: Response, *, session: UserSessionRecord, account: UserAccountInternal) -> None:
    max_age = 60 * 60 * 24 * 30
    response.set_cookie(USER_APP_SESSION_COOKIE, session.session_id, httponly=True, samesite="lax", max_age=max_age)
    response.set_cookie(USER_APP_ROLE_COOKIE, account.role_key, httponly=True, samesite="lax", max_age=max_age)


def _clear_user_cookies(response: Response) -> None:
    response.delete_cookie(USER_APP_SESSION_COOKIE)
    response.delete_cookie(USER_APP_ROLE_COOKIE)


def _profile_from_create_payload(*, user_id: str, payload: BaziProfileCreateRequest) -> BaziProfileRecord:
    profile_id = f"profile:{secrets.token_urlsafe(18)}"
    gender = payload.gender.strip() or payload.chart_facts.gender
    chart = payload.chart_facts.model_copy(update={"gender": gender})
    return BaziProfileRecord(
        profile_id=profile_id,
        user_id=user_id,
        display_name=payload.display_name.strip(),
        gender=gender,
        chart_facts=chart,
        birth_input=payload.birth_input,
        ziwei_chart_facts=payload.ziwei_chart_facts,
        is_default=payload.is_default,
        tags=payload.tags,
    )


def _save_profile(profile: BaziProfileRecord) -> bool:
    repository = _repository_or_none()
    if repository is not None:
        repository.save_bazi_profile(profile)
        return True
    user_profiles = _MEMORY_PROFILES_BY_USER.setdefault(profile.user_id, {})
    if profile.is_default:
        user_profiles.update({key: value.model_copy(update={"is_default": False}) for key, value in user_profiles.items()})
    user_profiles[profile.profile_id] = profile
    return False


def _list_profiles(user_id: str) -> list[dict[str, object]]:
    repository = _repository_or_none()
    if repository is not None:
        return repository.list_bazi_profiles(user_id=user_id)
    if user_id == BUILTIN_ADMIN_USER_ID:
        _bootstrap_memory_admin_profiles()
    profiles = [profile for profile in _MEMORY_PROFILES_BY_USER.get(user_id, {}).values() if not profile.deleted]
    profiles.sort(key=lambda item: (not item.is_default, item.display_name))
    return [profile.model_dump(mode="json") for profile in profiles]


def _bootstrap_memory_admin_profiles() -> None:
    global _MEMORY_ADMIN_PROFILES_BOOTSTRAPPED
    if _MEMORY_ADMIN_PROFILES_BOOTSTRAPPED or _MEMORY_PROFILES_BY_USER.get(BUILTIN_ADMIN_USER_ID):
        return
    _MEMORY_ADMIN_PROFILES_BOOTSTRAPPED = True
    source_store_path = default_v30_product_store_path()
    if not source_store_path.exists():
        return
    store = load_v30_product_store(source_store_path)
    source_profiles = select_v30_admin_profiles(store)
    user_profiles = _MEMORY_PROFILES_BY_USER.setdefault(BUILTIN_ADMIN_USER_ID, {})
    for index, source_profile in enumerate(source_profiles):
        try:
            profile = convert_v30_profile_to_v40(
                source_profile,
                user_id=BUILTIN_ADMIN_USER_ID,
                chart_builder=build_chart_payload_from_v30_birth_input,
                is_default=index == 0,
            )
        except Exception:
            continue
        if profile.profile_id not in user_profiles:
            if profile.is_default:
                user_profiles.update({key: value.model_copy(update={"is_default": False}) for key, value in user_profiles.items()})
            user_profiles[profile.profile_id] = profile


def _delete_profile(*, user_id: str, profile_id: str) -> bool:
    repository = _repository_or_none()
    if repository is not None:
        repository.delete_bazi_profile(user_id=user_id, profile_id=profile_id)
        return True
    profile = _MEMORY_PROFILES_BY_USER.get(user_id, {}).get(profile_id)
    if profile:
        _MEMORY_PROFILES_BY_USER[user_id][profile_id] = profile.model_copy(update={"deleted": True, "is_default": False})
    return False


def create_app() -> FastAPI:
    app = FastAPI(title="Qiazhi V40", version=__version__)

    @app.get(f"{API_PREFIX}/health")
    def health() -> dict[str, object]:
        runtime_dir = os.getenv("V40_RUNTIME_DIR", str(Path(__file__).resolve().parents[2] / ".runtime"))
        return {
            "ok": True,
            "package": "v40",
            "version": __version__,
            "api_prefix": API_PREFIX,
            "admin_prefix": "/admin/v40",
            "ui_prefix": "/v40/ui",
            "runtime_dir": runtime_dir,
            "repository": os.getenv("V40_REPOSITORY", "postgres"),
            "database_boundary": "qiazhi_v40",
            "postgres_table_prefix": "v40_",
            "repository_configured": v40_repository_configured(),
            "redis_prefix": os.getenv("V40_REDIS_PREFIX", "v40"),
            "v30_runtime_import_allowed": False,
            "boundary": "v40_health_reports_independent_runtime_boundaries",
        }

    @app.get(f"{API_PREFIX}/contracts")
    def contracts() -> dict[str, object]:
        return contract_manifest()

    @app.get("/v40/ui", response_class=HTMLResponse)
    def user_ui() -> HTMLResponse:
        return HTMLResponse(_user_ui_html())

    @app.get(f"{API_PREFIX}/session/context")
    def user_app_session_context(request: Request) -> dict[str, object]:
        session = resolve_user_app_session_context(request)
        account_pair = _optional_authenticated_account(request)
        account = account_pair[0].public() if account_pair else None
        return {
            "version": "v40.user_app_session_context_response.v1",
            "session": session.model_dump(mode="json"),
            "role_key": session.role_key,
            "role_context": session.role_context.model_dump(mode="json"),
            "authenticated": session.authenticated,
            "user": account.model_dump(mode="json") if account else None,
            "admin_control_plane_separated": session.admin_control_plane_separated,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "user_app_session_context_is_server_derived_and_does_not_expose_admin_control",
        }

    @app.post(f"{API_PREFIX}/auth/register")
    def register_user(payload: UserRegisterRequest, response: Response) -> dict[str, object]:
        try:
            if is_builtin_admin_identifier(payload.email):
                raise HTTPException(status_code=403, detail="Built-in admin cannot be registered from the user app")
            if _load_account_by_email(payload.email) is not None:
                raise HTTPException(status_code=409, detail="Email already registered")
            account = build_user_account(
                email=payload.email,
                password=payload.password,
                display_name=payload.display_name,
                role_key=payload.role_key,
            )
            account_persisted = _save_account(account)
            session = build_user_session(user_id=account.user_id, role_key=account.role_key)
            session_persisted = _save_session(session)
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 user repository is unavailable") from exc
        _set_user_cookies(response, session=session, account=account)
        return {
            "version": "v40.user_register_response.v1",
            "user": account.public().model_dump(mode="json"),
            "session": session.model_dump(mode="json"),
            "account_persisted": account_persisted,
            "session_persisted": session_persisted,
            "admin_registered": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "user_registration_creates_v40_user_app_account_without_admin_control",
        }

    @app.post(f"{API_PREFIX}/auth/login")
    def login_user(payload: UserLoginRequest, response: Response) -> dict[str, object]:
        try:
            account = _load_account_by_login(payload.email)
            if account is None or not verify_password(
                payload.password,
                password_hash=account.password_hash,
                password_salt=account.password_salt,
            ):
                raise HTTPException(status_code=401, detail="Email or password is incorrect")
            session = build_user_session(user_id=account.user_id, role_key=account.role_key)
            session_persisted = _save_session(session)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 user repository is unavailable") from exc
        _set_user_cookies(response, session=session, account=account)
        return {
            "version": "v40.user_login_response.v1",
            "user": account.public().model_dump(mode="json"),
            "session": session.model_dump(mode="json"),
            "session_persisted": session_persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "user_login_creates_v40_user_app_session_without_admin_control",
        }

    @app.post(f"{API_PREFIX}/auth/logout")
    def logout_user(request: Request, response: Response) -> dict[str, object]:
        session_id = _session_token_from_request(request)
        revoked = False
        if session_id:
            try:
                repository = _repository_or_none()
                if repository is not None:
                    repository.revoke_user_session(session_id)
                elif session_id in _MEMORY_SESSIONS:
                    _MEMORY_SESSIONS[session_id] = _MEMORY_SESSIONS[session_id].model_copy(update={"revoked": True})
                revoked = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 user repository is unavailable") from exc
        _clear_user_cookies(response)
        return {
            "version": "v40.user_logout_response.v1",
            "revoked": revoked,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "user_logout_revokes_user_app_session_without_admin_control",
        }

    @app.get(f"{API_PREFIX}/auth/me")
    def current_user(request: Request) -> dict[str, object]:
        account, session = _authenticated_account(request)
        return {
            "version": "v40.current_user_response.v1",
            "user": account.public().model_dump(mode="json"),
            "session": session.model_dump(mode="json"),
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "current_user_reads_v40_user_app_session_only",
        }

    @app.get(f"{API_PREFIX}/profiles")
    def list_profiles(request: Request) -> dict[str, object]:
        account, _session = _authenticated_account(request)
        try:
            profiles = _list_profiles(account.user_id)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 profile repository is unavailable") from exc
        return {
            "version": "v40.bazi_profiles_response.v1",
            "profiles": profiles,
            "user_id": account.user_id,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "bazi_profiles_are_scoped_to_authenticated_v40_user",
        }

    @app.post(f"{API_PREFIX}/profiles")
    def create_profile(payload: BaziProfileCreateRequest, request: Request) -> dict[str, object]:
        account, _session = _authenticated_account(request)
        profile = _profile_from_create_payload(user_id=account.user_id, payload=payload)
        try:
            persisted = _save_profile(profile)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 profile repository is unavailable") from exc
        return {
            "version": "v40.bazi_profile_create_response.v1",
            "profile": profile.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "bazi_profile_created_for_authenticated_v40_user_only",
        }

    @app.put(f"{API_PREFIX}/profiles/{{profile_id}}")
    def update_profile(profile_id: str, payload: BaziProfileUpdateRequest, request: Request) -> dict[str, object]:
        account, _session = _authenticated_account(request)
        if payload.profile.profile_id != profile_id:
            raise HTTPException(status_code=422, detail="Profile id mismatch")
        if payload.profile.user_id != account.user_id:
            raise HTTPException(status_code=403, detail="Profile does not belong to current user")
        try:
            persisted = _save_profile(payload.profile)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 profile repository is unavailable") from exc
        return {
            "version": "v40.bazi_profile_update_response.v1",
            "profile": payload.profile.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "bazi_profile_update_is_scoped_to_authenticated_v40_user",
        }

    @app.delete(f"{API_PREFIX}/profiles/{{profile_id}}")
    def delete_profile(profile_id: str, request: Request) -> dict[str, object]:
        account, _session = _authenticated_account(request)
        try:
            persisted = _delete_profile(user_id=account.user_id, profile_id=profile_id)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 profile repository is unavailable") from exc
        return {
            "version": "v40.bazi_profile_delete_response.v1",
            "profile_id": profile_id,
            "deleted": True,
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "bazi_profile_delete_is_scoped_to_authenticated_v40_user",
        }

    @app.get(f"{API_PREFIX}/surface/beta-readiness")
    def surface_beta_readiness() -> dict[str, object]:
        return {
            "version": "v40.surface_beta_readiness_response.v1",
            "readiness": _build_surface_beta_readiness(),
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "surface_beta_readiness_observes_user_surface_without_mutation",
        }

    @app.post(f"{API_PREFIX}/runtime/native-bazi")
    def native_bazi_runtime(payload: NativeBaziRuntimeRequest, request: Request) -> dict[str, object]:
        role_key, role_context, session = role_context_from_payload_or_session(
            request=request,
            payload_role_key=payload.role_key,
            payload_role_context=payload.role_context,
        )
        runtime = build_native_bazi_runtime(
            request_id=payload.request_id,
            reading_id=payload.reading_id,
            chart=payload.chart_facts,
            user_question=payload.user_question,
            topic=payload.topic,
            role_key=role_key,
            ziwei_chart=payload.ziwei_chart_facts,
            locale_context=payload.locale_context,
            role_context=role_context,
            client_context=payload.client_context,
            engine_context=_resolve_active_policy_engine_context(payload.engine_context),
        )
        persisted = False
        if payload.persist:
            repository = _repository_or_none()
            if repository is not None:
                repository.save_runtime(runtime)
                persisted = True
        return {
            "version": "v40.native_bazi_runtime_response.v1",
            "runtime": runtime.model_dump(mode="json"),
            "session": session.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "native_bazi_runtime_uses_v40_engine_skeleton_without_v30_runtime",
        }

    @app.post(f"{API_PREFIX}/readings/native-report")
    def native_reading_report(payload: NativeReadingReportRequest, request: Request) -> dict[str, object]:
        role_key, role_context, session = role_context_from_payload_or_session(
            request=request,
            payload_role_key=payload.role_key,
            payload_role_context=payload.role_context,
        )
        runtime = build_native_bazi_runtime(
            request_id=payload.request_id,
            reading_id=payload.reading_id,
            chart=payload.chart_facts,
            user_question=payload.user_question,
            topic=payload.topic,
            role_key=role_key,
            ziwei_chart=payload.ziwei_chart_facts,
            locale_context=payload.locale_context,
            role_context=role_context,
            client_context=payload.client_context,
            engine_context=_resolve_active_policy_engine_context(payload.engine_context),
        )
        try:
            task, result, acceptance, telemetry = _build_expression_bundle(
                task_id=f"task:{payload.reading_id}:report",
                result_id=f"result:{payload.reading_id}:report",
                acceptance_id=f"acceptance:{payload.reading_id}:report",
                runtime=runtime,
                role_key=role_key,
                topic=payload.topic,
                execution_mode=payload.execution_mode,
                provider_text=payload.provider_text,
                provider=payload.provider,
                model=payload.model,
                raw_thinking=payload.raw_thinking,
            )
        except OllamaExpressionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        conversation_seeds = build_conversation_seeds(
            runtime=runtime,
            accepted_text=acceptance.accepted_text,
            role_key=role_key,
        )
        enriched_runtime = runtime.model_copy(
            update={
                "expression_task": task,
                "expression_result": result,
                "acceptance_result": acceptance,
                "expression_telemetry": telemetry,
                "conversation_seeds": conversation_seeds,
            }
        )
        persisted = False
        if payload.persist:
            repository = _repository_or_none()
            if repository is not None:
                repository.save_runtime(enriched_runtime)
                persisted = True
        return {
            "version": "v40.native_reading_report_response.v1",
            "runtime": enriched_runtime.model_dump(mode="json"),
            "surface_bundle": enriched_runtime.surface_bundle.model_dump(mode="json") if enriched_runtime.surface_bundle else {},
            "accepted_text": acceptance.accepted_text,
            "accepted": acceptance.status.value == "accepted",
            "session": session.model_dump(mode="json"),
            "conversation_seeds": [seed.model_dump(mode="json") for seed in conversation_seeds],
            "expression": {
                "task": task.model_dump(mode="json"),
                "result": result.model_dump(mode="json"),
                "acceptance": acceptance.model_dump(mode="json"),
                "telemetry": telemetry.model_dump(mode="json"),
            },
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "native_reading_report_is_product_runtime_entry_without_llm_verdict_authority",
        }

    @app.post(f"{API_PREFIX}/conversation/turn")
    def conversation_turn(payload: ConversationTurnRequest) -> dict[str, object]:
        try:
            turn, task, result, acceptance, telemetry = build_conversation_turn(
                turn_id=payload.turn_id,
                runtime=payload.runtime,
                question=payload.question,
                seed_id=payload.seed_id,
                selected_option=payload.selected_option,
                role_key=payload.role_key,
                topic=payload.topic,
                probe_answer_results=payload.probe_answer_results,
                execution_mode=payload.execution_mode,
                provider_text=payload.provider_text,
                provider=payload.provider,
                model=payload.model,
                raw_thinking=payload.raw_thinking,
            )
        except OllamaExpressionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        training_label = build_training_label_from_conversation_turn(
            event_id=f"label:{turn.turn_id}",
            turn=turn,
            seed_id=payload.seed_id,
        )
        persisted = False
        training_label_persisted = False
        if payload.persist:
            repository = _repository_or_none()
            if repository is not None:
                repository.save_conversation_turn(turn)
                persisted = True
                if payload.persist_training_label:
                    repository.save_training_label_event(training_label)
                    training_label_persisted = True
        return {
            "version": "v40.conversation_turn_response.v1",
            "turn": turn.model_dump(mode="json"),
            "answer_text": turn.answer_text,
            "accepted": turn.accepted,
            "next_seeds": [seed.model_dump(mode="json") for seed in turn.next_seeds],
            "training_label": training_label.model_dump(mode="json"),
            "expression": {
                "task": task.model_dump(mode="json"),
                "result": result.model_dump(mode="json"),
                "acceptance": acceptance.model_dump(mode="json"),
                "telemetry": telemetry.model_dump(mode="json"),
            },
            "persisted": persisted,
            "training_label_persisted": training_label_persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "reruns_reading": False,
            "boundary": "conversation_turn_is_independent_dialogue_runtime_after_report",
        }

    @app.get(f"{API_PREFIX}/conversation/turns")
    def list_conversation_turns(
        limit: int = Query(default=20, ge=1, le=100),
        reading_id: str = "",
    ) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            turns = repository.list_conversation_turns(limit=limit, reading_id=reading_id)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.conversation_turns_response.v1",
            "turns": turns,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "conversation_turns_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/synthetic/cases/from-seeds")
    def synthetic_cases_from_seeds(payload: SyntheticCasesFromSeedsRequest) -> dict[str, object]:
        cases = build_evaluation_cases_from_seeds(payload.seeds)
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                for case in cases:
                    repository.save_evaluation_case(case)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.synthetic_cases_from_seeds_response.v1",
            "cases": [case.model_dump(mode="json") for case in cases],
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "synthetic_cases_are_evaluation_contracts_not_real_world_truth",
        }

    @app.post(f"{API_PREFIX}/evaluation/native-batch/from-seeds")
    def native_batch_from_seeds(payload: NativeBatchFromSeedsRequest) -> dict[str, object]:
        runtimes, cases, runs, summary = evaluate_native_seeds(
            batch_id=payload.batch_id,
            seeds=payload.seeds,
            candidate_version=payload.candidate_version,
            role_key=payload.role_key,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                for runtime in runtimes:
                    repository.save_runtime(runtime)
                for case in cases:
                    repository.save_evaluation_case(case)
                for run in runs:
                    repository.save_evaluation_run(run)
                    if run.release_gate:
                        repository.save_release_gate(run.release_gate)
                repository.save_evaluation_batch_summary(summary)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.native_batch_from_seeds_response.v1",
            "summary": summary.model_dump(mode="json"),
            "runs": [run.model_dump(mode="json") for run in runs],
            "runtime_refs": [runtime.reading_id for runtime in runtimes],
            "case_refs": [case.case_id for case in cases],
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "native_batch_from_seeds_evaluates_v40_native_runtime_without_v30_state",
        }

    @app.post(f"{API_PREFIX}/shadow-compare")
    def shadow_compare(payload: V30ExportEnvelope, persist: bool = False) -> dict[str, object]:
        runtime = build_runtime_from_v30_export(payload)
        compare = build_shadow_compare_result(
            compare_id=f"compare:{payload.export_id}",
            envelope=payload,
            runtime_result=runtime,
        )
        persisted = False
        if persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_runtime(runtime)
                repository.save_shadow_compare(compare)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.shadow_compare_response.v1",
            "runtime": runtime.model_dump(mode="json"),
            "compare": compare.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "shadow_compare_endpoint_imports_plain_json_without_touching_v30_runtime",
        }

    @app.get(f"{API_PREFIX}/shadow-compare/runs")
    def shadow_compare_runs(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            runs = repository.list_shadow_compare_runs(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.shadow_compare_runs_response.v1",
            "runs": runs,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "shadow_compare_history_reads_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/migration/mingli-assets/gate")
    def mingli_asset_migration_gate(payload: MingliAssetMigrationGateRequest) -> dict[str, object]:
        gate = build_mingli_asset_migration_gate(
            gate_id=payload.gate_id,
            reading_id=payload.reading_id,
            assets=payload.assets,
        )
        return {
            "version": "v40.mingli_asset_migration_gate_response.v1",
            "gate": gate.model_dump(mode="json"),
            "signals": [signal.model_dump(mode="json") for signal in gate.signals],
            "persisted": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "mingli_asset_migration_gate_endpoint_converts_plain_assets_without_production_write",
        }

    @app.post(f"{API_PREFIX}/shadow-compare/batch")
    def shadow_compare_batch(payload: ShadowCompareBatchRequest) -> dict[str, object]:
        runtimes = [build_runtime_from_v30_export(envelope) for envelope in payload.exports]
        compares = [
            build_shadow_compare_result(
                compare_id=f"compare:{payload.batch_id}:{envelope.export_id}",
                envelope=envelope,
                runtime_result=runtime,
            )
            for envelope, runtime in zip(payload.exports, runtimes)
        ]
        summary = build_shadow_compare_batch_summary(batch_id=payload.batch_id, compares=compares)
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                for runtime, compare in zip(runtimes, compares):
                    repository.save_runtime(runtime)
                    repository.save_shadow_compare(compare)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.shadow_compare_batch_response.v1",
            "summary": summary.model_dump(mode="json"),
            "compares": [compare.model_dump(mode="json") for compare in compares],
            "runtime_refs": [runtime.reading_id for runtime in runtimes],
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "shadow_compare_batch_imports_plain_json_without_touching_v30_runtime",
        }

    @app.post(f"{API_PREFIX}/evaluation/cases")
    def save_evaluation_case(payload: EvaluationCaseSpec) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            repository.save_evaluation_case(payload)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_case_save_response.v1",
            "saved": True,
            "case_id": payload.case_id,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_case_saved_as_v40_measurement_contract_only",
        }

    @app.get(f"{API_PREFIX}/evaluation/cases")
    def list_evaluation_cases(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            cases = repository.list_evaluation_cases(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_cases_response.v1",
            "cases": cases,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_cases_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/evaluation/runs/from-runtime")
    def build_evaluation_run(payload: EvaluationRunFromRuntimeRequest) -> dict[str, object]:
        run = evaluate_runtime_against_case(
            run_id=payload.run_id,
            case_spec=payload.case_spec,
            runtime=payload.runtime,
            candidate_version=payload.candidate_version,
            build_release_gate=payload.build_release_gate,
            expression_telemetry=payload.expression_telemetry,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_evaluation_run(run)
                if run.release_gate:
                    repository.save_release_gate(run.release_gate)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_run_from_runtime_response.v1",
            "run": run.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_run_built_by_deterministic_metrics_without_llm_judge",
        }

    @app.get(f"{API_PREFIX}/evaluation/runs")
    def list_evaluation_runs(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            runs = repository.list_evaluation_runs(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_runs_response.v1",
            "runs": runs,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_runs_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/evaluation/batches/from-runtime")
    def build_evaluation_batch(payload: EvaluationBatchFromRuntimeRequest) -> dict[str, object]:
        runs, summary = evaluate_cases_against_runtime(
            batch_id=payload.batch_id,
            cases=payload.cases,
            runtime=payload.runtime,
            candidate_version=payload.candidate_version,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                for run in runs:
                    repository.save_evaluation_run(run)
                    if run.release_gate:
                        repository.save_release_gate(run.release_gate)
                repository.save_evaluation_batch_summary(summary)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_batch_from_runtime_response.v1",
            "summary": summary.model_dump(mode="json"),
            "runs": [run.model_dump(mode="json") for run in runs],
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_batch_built_by_deterministic_metrics_without_llm_judge",
        }

    @app.get(f"{API_PREFIX}/evaluation/batches")
    def list_evaluation_batches(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            batches = repository.list_evaluation_batches(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.evaluation_batches_response.v1",
            "batches": batches,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "evaluation_batches_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/acceptance/windows/from-runtime")
    def build_acceptance_window(payload: AcceptanceWindowFromRuntimeRequest) -> dict[str, object]:
        runs, window = build_acceptance_window_from_runtime(
            window_id=payload.window_id,
            cases=payload.cases,
            runtime=payload.runtime,
            candidate_version=payload.candidate_version,
            expression_telemetry=payload.expression_telemetry,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                for run in runs:
                    repository.save_evaluation_run(run)
                    if run.release_gate:
                        repository.save_release_gate(run.release_gate)
                repository.save_evaluation_batch_summary(
                    build_evaluation_batch_summary(
                        batch_id=f"acceptance:{payload.window_id}",
                        candidate_version=payload.candidate_version,
                        runs=runs,
                    )
                )
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.acceptance_window_from_runtime_response.v1",
            "window": window.model_dump(mode="json"),
            "runs": [run.model_dump(mode="json") for run in runs],
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "acceptance_window_scores_real_cases_and_persists_evidence_without_policy_write",
        }

    @app.post(f"{API_PREFIX}/training/labels")
    def save_training_label(payload: TrainingLabelEvent) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            repository.save_training_label_event(payload)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_label_save_response.v1",
            "saved": True,
            "event_id": payload.event_id,
            "local_only": payload.local_only,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_label_saved_as_feedback_signal_without_weight_write",
        }

    @app.post(f"{API_PREFIX}/calibration/practitioner-selection")
    def save_practitioner_calibration(payload: PractitionerCalibrationRequest) -> dict[str, object]:
        event = TrainingLabelEvent(
            event_id=payload.event_id,
            reading_id=payload.reading_id,
            source=LabelSource.PRACTITIONER_SELECTION,
            target_type=payload.target_type,
            target_ids=payload.target_ids,
            label=payload.label,
            strength=payload.strength,
            confidence=payload.confidence,
            reason=payload.reason,
            evidence_refs=payload.evidence_refs,
            created_by_role=payload.created_by_role,
            local_only=True,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_training_label_event(event)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.practitioner_calibration_response.v1",
            "event": event.model_dump(mode="json"),
            "persisted": persisted,
            "applies_to_current_reading": True,
            "writes_v40_weight": False,
            "writes_v30_state": False,
            "boundary": "practitioner_calibration_records_training_label_without_direct_weight_write",
        }

    @app.post(f"{API_PREFIX}/calibration/practitioner-lens-action")
    def save_practitioner_lens_action(payload: PractitionerLensActionRequest) -> dict[str, object]:
        try:
            event, overlay = build_practitioner_lens_action(
                action_id=payload.action_id,
                runtime=payload.runtime,
                action_key=payload.action_key,
                target_type=payload.target_type,
                target_ids=payload.target_ids,
                note=payload.note,
                created_by_role=payload.created_by_role,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        event_persisted = False
        overlay_persisted = False
        if payload.persist or payload.persist_overlay:
            try:
                repository = V40PostgresRepository.from_env()
                if payload.persist:
                    repository.save_training_label_event(event)
                    event_persisted = True
                if payload.persist_overlay:
                    repository.save_local_overlay(overlay)
                    overlay_persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.practitioner_lens_action_response.v1",
            "event": event.model_dump(mode="json"),
            "overlay": overlay.model_dump(mode="json"),
            "event_persisted": event_persisted,
            "overlay_persisted": overlay_persisted,
            "applies_to_current_reading": True,
            "writes_v40_weight": False,
            "writes_v40_production": False,
            "writes_v30_state": False,
            "changes_verdict": False,
            "changes_chart_facts": False,
            "boundary": "practitioner_lens_action_records_local_training_feedback_without_direct_decision_mutation",
        }

    @app.post(f"{API_PREFIX}/consent/grants")
    def create_consent_grant(payload: ConsentGrantRequest) -> dict[str, object]:
        try:
            grant = build_consent_grant(
                grant_id=payload.grant_id,
                reading_id=payload.reading_id,
                granted_by_role=payload.granted_by_role,
                allow_practitioner_review=payload.allow_practitioner_review,
                allow_training_use=payload.allow_training_use,
                note=payload.note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_consent_grant(grant)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.consent_grant_response.v1",
            "consent_grant": grant.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "consent_grant_created_as_user_app_contract_without_admin_control",
        }

    @app.post(f"{API_PREFIX}/practitioner/review-requests")
    def create_practitioner_review_request(payload: PractitionerReviewCreateRequest) -> dict[str, object]:
        try:
            review_request = build_practitioner_review_request(
                review_request_id=payload.review_request_id,
                consent_grant=payload.consent_grant,
                runtime=payload.runtime,
                requested_topic=payload.requested_topic,
                requested_by_role=payload.requested_by_role,
                note=payload.note,
            )
            queue_item = build_review_queue_item(review_request)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_practitioner_review_request(review_request)
                repository.save_practitioner_review_queue_item(queue_item)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.practitioner_review_request_response.v1",
            "review_request": review_request.model_dump(mode="json"),
            "queue_item": queue_item.model_dump(mode="json"),
            "persisted": persisted,
            "raw_runtime_returned": False,
            "chart_facts_returned": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "practitioner_review_request_queues_anonymized_case_without_runtime_or_chart_fact_leakage",
        }

    @app.get(f"{API_PREFIX}/practitioner/review-queue")
    def list_practitioner_review_queue(
        limit: int = Query(default=20, ge=1, le=100),
        status: str = "",
        assigned_to_practitioner_ref: str = "",
    ) -> dict[str, object]:
        if not v40_repository_configured():
            return {
                "version": "v40.practitioner_review_queue_response.v1",
                "queue_items": [],
                "repository_configured": False,
                "persisted_queue_available": False,
                "writes_v30_state": False,
                "writes_v40_production": False,
                "boundary": "practitioner_review_queue_endpoint_requires_repository_for_persisted_items",
            }
        try:
            repository = V40PostgresRepository.from_env()
            queue_items = repository.list_practitioner_review_queue(
                limit=limit,
                status=status or None,
                assigned_to_practitioner_ref=assigned_to_practitioner_ref,
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.practitioner_review_queue_response.v1",
            "queue_items": queue_items,
            "repository_configured": True,
            "persisted_queue_available": True,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "practitioner_review_queue_reads_v40_persisted_queue_without_raw_case_data",
        }

    @app.post(f"{API_PREFIX}/practitioner/review-queue/assign")
    def assign_practitioner_review_queue(payload: PractitionerReviewAssignRequest) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            queue_item = repository.assign_practitioner_review_queue_item(
                queue_item_id=payload.queue_item_id,
                practitioner_ref=payload.practitioner_ref,
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        if queue_item is None:
            raise HTTPException(status_code=404, detail="Review queue item was not found")
        return {
            "version": "v40.practitioner_review_queue_assign_response.v1",
            "queue_item": queue_item,
            "assigned": True,
            "changes_verdict": False,
            "changes_chart_facts": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "practitioner_review_assignment_updates_queue_metadata_without_decision_mutation",
        }

    @app.post(f"{API_PREFIX}/practitioner/review-results")
    def create_practitioner_review_result(payload: PractitionerReviewResultRequest) -> dict[str, object]:
        try:
            result = build_practitioner_review_result(
                result_id=payload.result_id,
                review_request=payload.review_request,
                reviewer_role=payload.reviewer_role,
                decision=payload.decision,
                selected_signal_ids=payload.selected_signal_ids,
                selected_verdict_ids=payload.selected_verdict_ids,
                advice_notes=payload.advice_notes,
                probe_suggestions=payload.probe_suggestions,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        persisted = False
        training_label_persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_practitioner_review_result(result)
                persisted = True
                training_label_persisted = bool(result.training_label_events)
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.practitioner_review_result_response.v1",
            "review_result": result.model_dump(mode="json"),
            "training_label_events": [event.model_dump(mode="json") for event in result.training_label_events],
            "persisted": persisted,
            "training_label_persisted": training_label_persisted,
            "changes_verdict": False,
            "changes_chart_facts": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "practitioner_review_result_returns_training_material_without_direct_decision_or_weight_mutation",
        }

    @app.post(f"{API_PREFIX}/probes/answer")
    def answer_probe(payload: ProbeAnswerRequest) -> dict[str, object]:
        try:
            result = build_probe_answer_result(
                answer_id=payload.answer_id,
                runtime=payload.runtime,
                probe_id=payload.probe_id,
                answer_text=payload.answer_text,
                selected_option=payload.selected_option,
                mismatch_area=payload.mismatch_area,
                created_by_role=payload.created_by_role,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        event_persisted = False
        overlay_persisted = False
        if payload.persist or payload.persist_overlay:
            try:
                repository = V40PostgresRepository.from_env()
                if payload.persist:
                    repository.save_training_label_event(result.training_label)
                    event_persisted = True
                if payload.persist_overlay:
                    repository.save_local_overlay(result.local_overlay)
                    overlay_persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.probe_answer_response.v1",
            "result": result.model_dump(mode="json"),
            "answer_signal": result.answer_signal.model_dump(mode="json"),
            "hidden_attribute_update": result.hidden_attribute_update.model_dump(mode="json"),
            "training_label": result.training_label.model_dump(mode="json"),
            "local_overlay": result.local_overlay.model_dump(mode="json"),
            "refined_advice_points": result.refined_advice_points,
            "user_message": result.user_message,
            "event_persisted": event_persisted,
            "overlay_persisted": overlay_persisted,
            "applies_to_current_reading": True,
            "reruns_reading": False,
            "changes_verdict": False,
            "changes_chart_facts": False,
            "writes_v40_production": False,
            "writes_v30_state": False,
            "boundary": "probe_answer_creates_answer_signal_hidden_attribute_overlay_and_training_label_without_decision_mutation",
        }

    @app.post(f"{API_PREFIX}/expression/from-runtime")
    def expression_from_runtime(payload: ExpressionFromRuntimeRequest) -> dict[str, object]:
        try:
            task, result, acceptance, telemetry = _build_expression_bundle(
                task_id=payload.task_id,
                result_id=payload.result_id,
                acceptance_id=payload.acceptance_id,
                runtime=payload.runtime,
                role_key=payload.role_key,
                topic=payload.topic,
                execution_mode=payload.execution_mode,
                provider_text=payload.provider_text,
                provider=payload.provider,
                model=payload.model,
                raw_thinking=payload.raw_thinking,
            )
        except OllamaExpressionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "version": "v40.expression_from_runtime_response.v1",
            "task": task.model_dump(mode="json"),
            "result": result.model_dump(mode="json"),
            "acceptance": acceptance.model_dump(mode="json"),
            "telemetry": telemetry.model_dump(mode="json"),
            "accepted": acceptance.status.value == "accepted",
            "execution_mode": payload.execution_mode,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "expression_from_runtime_allows_llm_language_but_not_verdict_authority",
        }

    @app.get(f"{API_PREFIX}/expression/provider/ollama")
    def ollama_expression_provider_status() -> dict[str, object]:
        config = resolve_ollama_expression_config()
        return {
            "version": "v40.ollama_expression_provider_status.v1",
            "provider": config.provider,
            "base_url": config.base_url,
            "model": config.model,
            "timeout_seconds": config.timeout_seconds,
            "effective_thinking_timeout_seconds": config.effective_thinking_timeout_seconds,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "effective_thinking_max_tokens": config.effective_thinking_max_tokens,
            "enabled": config.enabled,
            "execute": config.execute,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "ollama_expression_provider_status_exposes_v40_llm_config_without_secrets",
        }

    @app.get(f"{API_PREFIX}/expression/provider/ollama/models")
    def ollama_expression_provider_models() -> dict[str, object]:
        try:
            return list_ollama_models()
        except OllamaExpressionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get(f"{API_PREFIX}/training/labels")
    def list_training_labels(
        limit: int = Query(default=20, ge=1, le=100),
        reading_id: str = "",
    ) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            events = repository.list_training_label_events(limit=limit, reading_id=reading_id)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_labels_response.v1",
            "events": events,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_labels_read_v40_feedback_events_only",
        }

    @app.get(f"{API_PREFIX}/calibration/local-overlays")
    def list_local_overlays(
        limit: int = Query(default=20, ge=1, le=100),
        reading_id: str = "",
    ) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            overlays = repository.list_local_overlays(limit=limit, reading_id=reading_id)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.local_overlays_response.v1",
            "overlays": overlays,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "local_overlays_read_current_reading_feedback_scope_only",
        }

    @app.post(f"{API_PREFIX}/training/example-from-reading")
    def build_training_example_from_reading(payload: TrainingExampleFromReadingRequest) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            label_rows = repository.list_training_label_events(reading_id=payload.reading_id, limit=100)
            overlay_rows = repository.list_local_overlays(reading_id=payload.reading_id, limit=100)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        label_events = [
            TrainingLabelEvent.model_validate(row["label_json"])
            for row in label_rows
            if row.get("label_json")
        ]
        if not label_events:
            raise HTTPException(status_code=422, detail="No training labels found for reading_id")
        overlay_refs = [
            str(row["overlay_id"])
            for row in overlay_rows
            if row.get("overlay_id")
        ]
        example = build_training_example_from_labels(
            example_id=payload.example_id,
            reading_id=payload.reading_id,
            label_events=label_events,
            topic=payload.topic,
            input_snapshot_ref=payload.input_snapshot_ref,
            runtime_output_ref=payload.runtime_output_ref,
            local_overlay_refs=overlay_refs,
        )
        persisted = False
        if payload.persist:
            try:
                repository.save_training_example(example)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_example_from_reading_response.v1",
            "example": example.model_dump(mode="json"),
            "label_count": len(label_events),
            "local_overlay_count": len(overlay_refs),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_example_compiles_feedback_material_without_weight_write",
        }

    @app.get(f"{API_PREFIX}/training/examples")
    def list_training_examples(
        limit: int = Query(default=20, ge=1, le=100),
        reading_id: str = "",
    ) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            examples = repository.list_training_examples(limit=limit, reading_id=reading_id)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_examples_response.v1",
            "examples": examples,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_examples_read_compiled_feedback_material_only",
        }

    @app.post(f"{API_PREFIX}/training/replay-example")
    def replay_training_example_from_runtime(payload: TrainingExampleReplayRequest) -> dict[str, object]:
        replay = replay_training_example(
            replay_id=payload.replay_id,
            training_example=payload.training_example,
            runtime=payload.runtime,
            candidate_version=payload.candidate_version,
            include_source_example=payload.include_source_example,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_training_example_replay(replay)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_example_replay_response.v1",
            "replay": replay.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_example_replay_scores_feedback_without_weight_write",
        }

    @app.get(f"{API_PREFIX}/training/example-replays")
    def list_training_example_replays(
        limit: int = Query(default=20, ge=1, le=100),
        reading_id: str = "",
    ) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            replays = repository.list_training_example_replays(limit=limit, reading_id=reading_id)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_example_replays_response.v1",
            "replays": replays,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_example_replays_read_feedback_validation_material_only",
        }

    @app.post(f"{API_PREFIX}/training/replay-batches")
    def build_training_replay_batch(payload: TrainingReplayBatchRequest) -> dict[str, object]:
        summary = build_training_replay_batch_summary(
            batch_id=payload.batch_id,
            candidate_version=payload.candidate_version,
            replays=payload.replays,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_training_replay_batch_summary(summary)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_replay_batch_response.v1",
            "summary": summary.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_replay_batch_summary_generated_without_weight_write",
        }

    @app.get(f"{API_PREFIX}/training/replay-batches")
    def list_training_replay_batches(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            batches = repository.list_training_replay_batches(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_replay_batches_response.v1",
            "batches": batches,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_replay_batches_read_feedback_validation_batches_only",
        }

    @app.post(f"{API_PREFIX}/training/impact-from-evaluation")
    def build_training_impact(payload: TrainingImpactFromEvaluationRequest) -> dict[str, object]:
        diff = build_training_impact_from_evaluation(
            evaluation_run=payload.evaluation_run,
            training_run_id=payload.training_run_id,
            base_version=payload.base_version,
            candidate_version=payload.candidate_version,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_training_impact_diff(diff)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_impact_from_evaluation_response.v1",
            "impact": diff.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_impact_diff_generated_without_applying_production_weight",
        }

    @app.get(f"{API_PREFIX}/training/impact-diffs")
    def list_training_impacts(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            impacts = repository.list_training_impact_diffs(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.training_impact_diffs_response.v1",
            "impacts": impacts,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "training_impact_diffs_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/training/policy-registries")
    def save_trainable_policy_registry(payload: TrainablePolicyRegistry) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            repository.save_trainable_policy_registry(payload)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.trainable_policy_registry_save_response.v1",
            "saved": True,
            "registry_id": payload.registry_id,
            "active_policy_version": payload.active_policy_version,
            "candidate_policy_version": payload.candidate_policy_version,
            "active": payload.active,
            "previous_registry_id": payload.previous_registry_id,
            "previous_policy_version": payload.previous_policy_version,
            "unit_count": len(payload.units),
            "writes_v30_state": False,
            "writes_v40_production": payload.active,
            "writes_v40_policy": payload.active,
            "changes_chart_facts": False,
            "boundary": "trainable_policy_registry_saved_as_active_policy_with_rollback_without_fact_mutation",
        }

    @app.get(f"{API_PREFIX}/training/policy-registries/active")
    def active_trainable_policy_registry() -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            registry = repository.get_active_trainable_policy_registry()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.active_trainable_policy_registry_response.v1",
            "registry": registry or {},
            "active_policy_version": str((registry or {}).get("active_policy_version") or "baseline"),
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "active_trainable_policy_registry_reads_current_high_iteration_policy_without_mutation",
        }

    @app.get(f"{API_PREFIX}/training/policy-registries")
    def list_trainable_policy_registries(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            registries = repository.list_trainable_policy_registries(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.trainable_policy_registries_response.v1",
            "registries": registries,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "trainable_policy_registries_read_v40_repository_with_active_and_rollback_history",
        }

    @app.post(f"{API_PREFIX}/training/batch-trainer-v1")
    def run_batch_trainer_v1(payload: BatchTrainerV1Request) -> dict[str, object]:
        try:
            result = build_batch_trainer_v1(
                training_run_id=payload.training_run_id,
                base_registry=payload.base_registry,
                attributions=payload.attributions,
                label_events=payload.label_events,
                candidate_policy_version=payload.candidate_policy_version,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        impact_persisted = False
        registry_persisted = False
        if payload.persist_impact or payload.persist_registry:
            try:
                repository = V40PostgresRepository.from_env()
                if payload.persist_registry:
                    repository.save_trainable_policy_registry(result.candidate_registry)
                    registry_persisted = True
                if payload.persist_impact:
                    repository.save_training_impact_diff(result.impact_diff)
                    impact_persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.batch_trainer_v1_response.v1",
            "result": result.model_dump(mode="json"),
            "candidate_registry": result.candidate_registry.model_dump(mode="json"),
            "impact": result.impact_diff.model_dump(mode="json"),
            "registry_persisted": registry_persisted,
            "impact_persisted": impact_persisted,
            "active_policy_applied": registry_persisted and result.active_policy_applied,
            "rollback_registry_id": result.rollback_registry_id,
            "policy_version_used_next": result.candidate_registry.active_policy_version if registry_persisted else payload.base_registry.active_policy_version,
            "writes_v30_state": False,
            "writes_v40_production": registry_persisted,
            "writes_v40_policy": registry_persisted,
            "changes_chart_facts": False,
            "boundary": "batch_trainer_v1_applies_validated_policy_immediately_with_rollback_without_approval_gate_or_fact_mutation",
        }

    @app.post(f"{API_PREFIX}/weights/candidates/from-batch")
    def build_candidate_weight(payload: CandidateWeightFromBatchRequest) -> dict[str, object]:
        try:
            weight_version = build_candidate_weight_version_from_batch(
                summary=payload.batch_summary,
                weight_version_id=payload.weight_version_id,
                source_training_run_id=payload.source_training_run_id,
                release_gate_id=payload.release_gate_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_global_weight_version(weight_version)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.candidate_weight_from_batch_response.v1",
            "weight_version": weight_version.model_dump(mode="json"),
            "persisted": persisted,
            "active": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "candidate_weight_version_registered_without_activation",
        }

    @app.post(f"{API_PREFIX}/weights/candidates/from-replay-batch")
    def build_candidate_weight_from_replay_batch(payload: CandidateWeightFromReplayBatchRequest) -> dict[str, object]:
        try:
            weight_version = build_candidate_weight_version_from_replay_batch(
                summary=payload.replay_batch_summary,
                weight_version_id=payload.weight_version_id,
                source_training_run_id=payload.source_training_run_id,
                release_gate_id=payload.release_gate_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_global_weight_version(weight_version)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.candidate_weight_from_replay_batch_response.v1",
            "weight_version": weight_version.model_dump(mode="json"),
            "persisted": persisted,
            "active": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "candidate_weight_version_registered_from_replay_batch_without_activation",
        }

    @app.get(f"{API_PREFIX}/weights/candidates")
    def list_candidate_weights(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            weights = repository.list_global_weight_versions(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.candidate_weights_response.v1",
            "weights": weights,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "candidate_weights_read_v40_repository_without_activation",
        }

    @app.post(f"{API_PREFIX}/release-readiness/from-batches")
    def build_release_readiness(payload: ReleaseReadinessFromBatchesRequest) -> dict[str, object]:
        summary = build_release_readiness_from_batches(
            readiness_id=payload.readiness_id,
            candidate_version=payload.candidate_version,
            batches=payload.batches,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_release_readiness(summary)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.release_readiness_from_batches_response.v1",
            "summary": summary.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "release_readiness_aggregated_without_activation",
        }

    @app.post(f"{API_PREFIX}/release-readiness/from-evidence-batches")
    def build_release_readiness_from_mixed_evidence(payload: ReleaseReadinessFromEvidenceBatchesRequest) -> dict[str, object]:
        summary = build_release_readiness_from_evidence_batches(
            readiness_id=payload.readiness_id,
            candidate_version=payload.candidate_version,
            evaluation_batches=payload.evaluation_batches,
            replay_batches=payload.replay_batches,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_release_readiness(summary)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.release_readiness_from_evidence_batches_response.v1",
            "summary": summary.model_dump(mode="json"),
            "persisted": persisted,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "release_readiness_aggregates_evaluation_and_replay_batches_without_activation",
        }

    @app.get(f"{API_PREFIX}/release-readiness")
    def list_release_readiness(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            readiness = repository.list_release_readiness(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.release_readiness_response.v1",
            "readiness": readiness,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "release_readiness_read_v40_repository_without_activation",
        }

    @app.post(f"{API_PREFIX}/weights/activation-reviews")
    def build_activation_review(payload: WeightActivationReviewRequest) -> dict[str, object]:
        review = build_weight_activation_review(
            review_id=payload.review_id,
            weight_version=payload.weight_version,
            release_readiness=payload.release_readiness,
            reviewed_by_role=payload.reviewed_by_role,
        )
        persisted = False
        if payload.persist:
            try:
                repository = V40PostgresRepository.from_env()
                repository.save_weight_activation_review(review)
                persisted = True
            except Exception as exc:
                raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.weight_activation_review_response.v1",
            "review": review.model_dump(mode="json"),
            "persisted": persisted,
            "activation_applied": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "activation_review_recorded_without_applying_weight",
        }

    @app.get(f"{API_PREFIX}/weights/activation-reviews")
    def list_activation_reviews(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            reviews = repository.list_weight_activation_reviews(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.weight_activation_reviews_response.v1",
            "reviews": reviews,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "activation_reviews_read_v40_repository_without_activation",
        }

    @app.post(f"{API_PREFIX}/weights/activate")
    def activate_weight(payload: WeightActivationExecutionRequest) -> dict[str, object]:
        if payload.confirm_phrase != "ACTIVATE_V40_WEIGHT":
            raise HTTPException(status_code=422, detail="Activation requires explicit confirmation phrase")
        try:
            execution = build_weight_activation_execution(
                execution_id=payload.execution_id,
                review=payload.review,
                weight_version=payload.weight_version,
                rollback_version_id=payload.rollback_version_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        try:
            repository = V40PostgresRepository.from_env()
            applied = repository.activate_global_weight_version(execution)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.weight_activation_execution_response.v1",
            "execution": applied.model_dump(mode="json"),
            "activation_applied": True,
            "writes_v30_state": False,
            "writes_v40_weight": True,
            "boundary": "activation_execution_updates_v40_weight_only_with_explicit_confirmation",
        }

    @app.get(f"{API_PREFIX}/weights/activation-executions")
    def list_activation_executions(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            executions = repository.list_weight_activation_executions(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.weight_activation_executions_response.v1",
            "executions": executions,
            "writes_v30_state": False,
            "boundary": "activation_executions_read_v40_repository_only",
        }

    @app.post(f"{API_PREFIX}/release-gates")
    def save_release_gate(payload: ReleaseGateResult) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            repository.save_release_gate(payload)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.release_gate_save_response.v1",
            "saved": True,
            "gate_id": payload.gate_id,
            "recommendation": payload.recommendation.value,
            "production_write_allowed": False,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "release_gate_record_saved_without_applying_production_weight",
        }

    @app.get(f"{API_PREFIX}/release-gates")
    def list_release_gates(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            gates = repository.list_release_gates(limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.release_gates_response.v1",
            "gates": gates,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "release_gates_read_v40_repository_only",
        }

    @app.get(f"{API_PREFIX}/lab/summary")
    def lab_summary() -> dict[str, object]:
        try:
            repository = V40PostgresRepository.from_env()
            summary = repository.lab_summary()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="V40 repository is unavailable") from exc
        return {
            "version": "v40.lab_summary_response.v1",
            "summary": summary,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "lab_summary_reads_v40_control_plane_state_only",
        }

    @app.get(f"{API_PREFIX}/project/status")
    def project_status() -> dict[str, object]:
        lab_snapshot: dict[str, object] | None = None
        try:
            repository = V40PostgresRepository.from_env()
            lab_snapshot = repository.lab_summary()
        except Exception:
            lab_snapshot = None
        status = build_project_status(lab_summary=lab_snapshot)
        return {
            "version": "v40.project_status_response.v1",
            "status": status,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "project_status_reads_v40_progress_without_mutation",
        }

    @app.get(f"{API_PREFIX}/project/mingli-depth-index")
    def mingli_depth_index() -> dict[str, object]:
        lab_snapshot: dict[str, object] | None = None
        try:
            repository = V40PostgresRepository.from_env()
            lab_snapshot = repository.lab_summary()
        except Exception:
            lab_snapshot = None
        return {
            "version": "v40.mingli_depth_index_response.v1",
            "index": build_mingli_depth_index(lab_summary=lab_snapshot),
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "mingli_depth_index_reads_v40_evidence_without_migration_enablement",
        }

    @app.get(f"{API_PREFIX}/project/module-migration-status")
    def module_migration_status() -> dict[str, object]:
        return {
            "version": "v40.module_migration_status_response.v1",
            "status": build_module_migration_status(),
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "module_migration_status_reads_static_rc2_plan_without_mutation",
        }

    @app.get(f"{API_PREFIX}/project/trainable-runtime-spine")
    def trainable_runtime_spine() -> dict[str, object]:
        return {
            "version": "v40.trainable_runtime_spine_response.v1",
            "status": build_trainable_runtime_spine_status(),
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "trainable_runtime_spine_reads_policy_training_plan_without_mutation",
        }

    @app.get(f"{API_PREFIX}/project/horizontal-runtime-context")
    def horizontal_runtime_context() -> dict[str, object]:
        return {
            "version": "v40.horizontal_runtime_context_response.v1",
            "status": build_horizontal_runtime_context_status(),
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "horizontal_runtime_context_reads_platform_context_plan_without_mutation",
        }

    @app.get(f"{API_PREFIX}/project/v30-replacement-readiness")
    def v30_replacement_readiness() -> dict[str, object]:
        lab_snapshot: dict[str, object] | None = None
        try:
            repository = V40PostgresRepository.from_env()
            lab_snapshot = repository.lab_summary()
        except Exception:
            lab_snapshot = None
        readiness = build_v30_replacement_readiness(
            lab_summary=lab_snapshot,
            surface_readiness=_build_surface_beta_readiness(),
        )
        return {
            "version": "v40.v30_replacement_readiness_response.v1",
            "readiness": readiness,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "v30_replacement_readiness_reads_v40_evidence_without_mutation",
        }

    @app.get(f"{API_PREFIX}/project/production-cutover-checklist")
    def production_cutover_checklist() -> dict[str, object]:
        lab_snapshot: dict[str, object] | None = None
        weights: list[dict[str, object]] = []
        try:
            repository = V40PostgresRepository.from_env()
            lab_snapshot = repository.lab_summary()
            weights = repository.list_global_weight_versions(limit=20)
        except Exception:
            lab_snapshot = None
            weights = []
        replacement = build_v30_replacement_readiness(
            lab_summary=lab_snapshot,
            surface_readiness=_build_surface_beta_readiness(),
        )
        llm_config = resolve_ollama_expression_config()
        checklist = build_production_cutover_checklist(
            replacement_readiness=replacement,
            weights=weights,
            llm_ready=llm_config.enabled and llm_config.execute,
            repository_configured=v40_repository_configured(),
        )
        return {
            "version": "v40.production_cutover_checklist_response.v1",
            "checklist": checklist,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "production_cutover_checklist_reads_v40_evidence_without_switching_traffic",
        }

    @app.post(f"{API_PREFIX}/project/real-case-expansion-evidence")
    def real_case_expansion_evidence(payload: RealCaseExpansionEvidenceRequest) -> dict[str, object]:
        evidence = build_real_case_expansion_evidence_pack(
            cases=payload.cases,
            acceptance_windows=payload.acceptance_windows,
            target_case_count=payload.target_case_count,
            min_cases_per_topic=payload.min_cases_per_topic,
            min_trainable_case_count=payload.min_trainable_case_count,
        )
        return {
            "version": "v40.real_case_expansion_evidence_response.v1",
            "evidence": evidence,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "real_case_expansion_evidence_reads_cases_without_cutover_or_policy_write",
        }

    @app.post(f"{API_PREFIX}/project/direct-training-activation-evidence")
    def direct_training_activation_evidence(payload: DirectTrainingActivationEvidenceRequest) -> dict[str, object]:
        evidence = build_direct_training_activation_evidence(result=payload.result)
        return {
            "version": "v40.direct_training_activation_evidence_response.v1",
            "evidence": evidence,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "direct_training_activation_evidence_reads_active_policy_without_mutation",
        }

    @app.post(f"{API_PREFIX}/project/online-cutover-decision")
    def online_cutover_decision(payload: OnlineCutoverDecisionRequest) -> dict[str, object]:
        decision = build_online_cutover_decision_pack(
            project_status=payload.project_status,
            cutover_checklist=payload.cutover_checklist,
            real_case_evidence=payload.real_case_evidence,
            training_activation_evidence=payload.training_activation_evidence,
            release_candidate_audit=payload.release_candidate_audit,
        )
        return {
            "version": "v40.online_cutover_decision_response.v1",
            "decision": decision,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "online_cutover_decision_reads_evidence_without_switching_traffic",
        }

    @app.post(f"{API_PREFIX}/project/real-case-acceptance-pack")
    def real_case_acceptance_pack(payload: RealCaseAcceptancePackRequest) -> dict[str, object]:
        pack = build_real_case_acceptance_pack(
            cases=payload.cases,
            acceptance_window=payload.acceptance_window,
            real_case_evidence=payload.real_case_evidence,
            online_cutover_decision=payload.online_cutover_decision,
            min_owner_review_case_count=payload.min_owner_review_case_count,
        )
        return {
            "version": "v40.real_case_acceptance_pack_response.v1",
            "pack": pack,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "traffic_switch_allowed_by_system": False,
            "boundary": "real_case_acceptance_pack_reads_evidence_without_cutover",
        }

    @app.get(f"{API_PREFIX}/project/release-candidate-audit")
    def release_candidate_audit() -> dict[str, object]:
        lab_snapshot: dict[str, object] | None = None
        weights: list[dict[str, object]] = []
        try:
            repository = V40PostgresRepository.from_env()
            lab_snapshot = repository.lab_summary()
            weights = repository.list_global_weight_versions(limit=20)
        except Exception:
            lab_snapshot = None
            weights = []
        surface = _build_surface_beta_readiness()
        replacement = build_v30_replacement_readiness(lab_summary=lab_snapshot, surface_readiness=surface)
        llm_config = resolve_ollama_expression_config()
        cutover = build_production_cutover_checklist(
            replacement_readiness=replacement,
            weights=weights,
            llm_ready=llm_config.enabled and llm_config.execute,
            repository_configured=v40_repository_configured(),
        )
        audit = build_release_candidate_audit(
            project_status=build_project_status(lab_summary=lab_snapshot),
            surface_readiness=surface,
            replacement_readiness=replacement,
            cutover_checklist=cutover,
        )
        return {
            "version": "v40.release_candidate_audit_response.v1",
            "audit": audit,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "release_candidate_audit_reads_v40_readiness_without_releasing_traffic",
        }

    @app.get(f"{API_PREFIX}/project/production-smoke")
    def production_smoke() -> dict[str, object]:
        lab_snapshot: dict[str, object] | None = None
        weights: list[dict[str, object]] = []
        try:
            repository = V40PostgresRepository.from_env()
            lab_snapshot = repository.lab_summary()
            weights = repository.list_global_weight_versions(limit=20)
        except Exception:
            lab_snapshot = None
            weights = []
        project = build_project_status(lab_summary=lab_snapshot)
        surface = _build_surface_beta_readiness()
        replacement = build_v30_replacement_readiness(lab_summary=lab_snapshot, surface_readiness=surface)
        llm_config = resolve_ollama_expression_config()
        cutover = build_production_cutover_checklist(
            replacement_readiness=replacement,
            weights=weights,
            llm_ready=llm_config.enabled and llm_config.execute,
            repository_configured=v40_repository_configured(),
        )
        audit = build_release_candidate_audit(
            project_status=project,
            surface_readiness=surface,
            replacement_readiness=replacement,
            cutover_checklist=cutover,
        )
        smoke = build_production_smoke(
            project_status=project,
            surface_readiness=surface,
            replacement_readiness=replacement,
            cutover_checklist=cutover,
            release_candidate_audit=audit,
        )
        return {
            "version": "v40.production_smoke_response.v1",
            "smoke": smoke,
            "writes_v30_state": False,
            "writes_v40_production": False,
            "boundary": "production_smoke_reads_v40_readiness_without_switching_traffic",
        }

    return app


def _user_ui_html() -> str:
    template = Path(__file__).with_name("user_ui.html")
    if template.exists():
        return template.read_text(encoding="utf-8")
    raise RuntimeError("V40 user UI template is missing")


app = create_app()
