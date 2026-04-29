from __future__ import annotations

import hashlib
import logging
import time
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from v17_rebirth.backend.services.v18_1_predictive_engine import (
    PredictiveServiceError,
    predictive_runtime_facade,
    predictive_service,
)
from v17_rebirth.backend.services.core_bazi_feature_layer import core_bazi_feature_service
from v17_rebirth.backend.services.core_bazi_strength_model import core_bazi_strength_service
from v17_rebirth.backend.services.core_bazi_structure_effect_layer import core_bazi_structure_effect_service
from v17_rebirth.backend.services.core_bazi_wealth_domain import wealth_domain_service
from v17_rebirth.backend.services.auth_service import get_request_user

router = APIRouter()
logger = logging.getLogger(__name__)


_ERROR_COPY: dict[str, dict[str, str]] = {
    "RULE_SCOPE_VIOLATION": {
        "zh": "这个问题目前不在系统的可验证规则范围内。你可以改问财运趋势、收入稳定性，或财富机会与风险。",
        "en": "This question is outside the current verifiable rule scope. Try asking about wealth trends, income stability, or financial risk and opportunity.",
        "ko": "이 질문은 현재 검증 가능한 규칙 범위 밖에 있습니다. 재물 흐름, 수입 안정성, 기회와 리스크에 대해 질문해 주세요.",
    },
    "CONTRACT_SCHEMA_INVALID": {
        "zh": "这次请求缺少必要信息。请补齐问题和出生信息后再试。",
        "en": "Some required information is missing. Please complete the question and birth details, then try again.",
        "ko": "필수 정보가 부족합니다. 질문과 출생 정보를 보완한 뒤 다시 시도해 주세요.",
    },
    "LEDGER_NOT_FOUND": {
        "zh": "没有找到这条预测记录。请确认链接是否完整，或重新生成一次预测。",
        "en": "This prediction record was not found. Check the link or generate a new prediction.",
        "ko": "이 예측 기록을 찾을 수 없습니다. 링크를 확인하거나 새 예측을 생성해 주세요.",
    },
    "RATE_LIMITED": {
        "zh": "请求有点太频繁了。请稍等一下再试。",
        "en": "Too many requests in a short time. Please wait a moment and try again.",
        "ko": "짧은 시간에 요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
    },
    "DUPLICATE_FEEDBACK": {
        "zh": "这条反馈已经记录过了。谢谢，你的反馈会进入学习信号。",
        "en": "This feedback has already been recorded. Thank you; it will be used as a learning signal.",
        "ko": "이 피드백은 이미 기록되었습니다. 감사합니다. 학습 신호로 반영됩니다.",
    },
    "FEEDBACK_LOCKED": {
        "zh": "这条记录当前不能重复写入。你可以刷新后查看最新状态。",
        "en": "This record cannot be written again right now. Refresh to view the latest state.",
        "ko": "이 기록은 지금 중복 저장할 수 없습니다. 새로고침 후 최신 상태를 확인해 주세요.",
    },
    "LOCK_BUSY": {
        "zh": "系统正在处理同一条记录。请稍等片刻再试。",
        "en": "The system is already processing this record. Please try again shortly.",
        "ko": "시스템이 같은 기록을 처리 중입니다. 잠시 후 다시 시도해 주세요.",
    },
    "ADMIN_REQUIRED": {
        "zh": "这个操作需要管理员权限。",
        "en": "This action requires admin permission.",
        "ko": "이 작업에는 관리자 권한이 필요합니다.",
    },
    "BAZI_KNOWLEDGE_COMPILER_INVALID": {
        "zh": "这条知识单元暂时不能转换为规则候选，请先检查 feature mapping。",
        "en": "This knowledge unit cannot be converted yet. Please review its feature mapping.",
        "ko": "이 지식 단위는 아직 규칙 후보로 변환할 수 없습니다. feature mapping을 확인해 주세요.",
    },
    "KB_AUDIT_MODEL_UNCONFIGURED": {
        "zh": "审计模型暂未配置，系统将使用本地安全审计结果。",
        "en": "The audit model is not configured. The system will use local safety audit results.",
        "ko": "감사 모델이 설정되지 않았습니다. 로컬 안전 감사 결과를 사용합니다.",
    },
    "CORE_BAZI_CHART_INVALID": {
        "zh": "命盘结构信息不完整。请提供四柱，至少需要日干和月支。",
        "en": "The chart structure is incomplete. Please provide the four pillars, including at least the day stem and month branch.",
        "ko": "명식 구조 정보가 부족합니다. 최소한 일간과 월지를 포함한 사주를 제공해 주세요.",
    },
    "CORE_FEATURE_BUNDLE_NOT_FOUND": {
        "zh": "没有找到这份基础命理特征包。请重新抽取一次。",
        "en": "This core Bazi feature bundle was not found. Please extract it again.",
        "ko": "해당 기본 명리 feature bundle을 찾을 수 없습니다. 다시 추출해 주세요.",
    },
    "CORE_STRENGTH_INPUT_INVALID": {
        "zh": "强弱评估缺少基础命理特征包。请先完成 Core Feature 抽取。",
        "en": "Strength evaluation requires a core Bazi feature bundle. Please extract Core Features first.",
        "ko": "강약 평가에는 기본 명리 feature bundle이 필요합니다. 먼저 Core Feature를 추출해 주세요.",
    },
    "CORE_STRENGTH_BUNDLE_NOT_FOUND": {
        "zh": "没有找到这份强弱证据包。请重新评估一次。",
        "en": "This strength evidence bundle was not found. Please evaluate it again.",
        "ko": "해당 강약 증거 bundle을 찾을 수 없습니다. 다시 평가해 주세요.",
    },
    "CORE_STRUCTURE_INPUT_INVALID": {
        "zh": "结构作用评估缺少基础特征包或强弱证据包。请先完成 Core Feature 与 Strength 评估。",
        "en": "Structure effect evaluation requires both the core feature bundle and strength evidence bundle. Please complete Core Feature extraction and Strength evaluation first.",
        "ko": "구조 작용 평가에는 Core Feature bundle과 강약 증거 bundle이 모두 필요합니다. 먼저 두 평가를 완료해 주세요.",
    },
    "CORE_STRUCTURE_BUNDLE_NOT_FOUND": {
        "zh": "没有找到这份结构作用证据包。请重新评估一次。",
        "en": "This structure effect evidence bundle was not found. Please evaluate it again.",
        "ko": "해당 구조 작용 증거 bundle을 찾을 수 없습니다. 다시 평가해 주세요.",
    },
    "WEALTH_DOMAIN_INPUT_INVALID": {
        "zh": "财富结构评估缺少 Core Feature、Strength 或 Structure Effect 证据包。",
        "en": "Wealth evaluation requires Core Feature, Strength, and Structure Effect bundles.",
        "ko": "재물 구조 평가에는 Core Feature, Strength, Structure Effect bundle이 필요합니다.",
    },
    "WEALTH_DOMAIN_UNSUPPORTED_INTENT": {
        "zh": "这个问题不属于当前财富域支持范围。请改问财运趋势、收入稳定性，或财富风险机会。",
        "en": "This question is outside the supported wealth-domain intents. Ask about wealth outlook, income stability, or risk and opportunity.",
        "ko": "이 질문은 현재 재물 도메인 지원 범위 밖입니다. 재물 흐름, 수입 안정성, 기회와 리스크로 질문해 주세요.",
    },
    "WEALTH_DOMAIN_BUNDLE_NOT_FOUND": {
        "zh": "没有找到这份财富结构证据包。请重新评估一次。",
        "en": "This wealth-domain evidence bundle was not found. Please evaluate it again.",
        "ko": "해당 재물 도메인 증거 bundle을 찾을 수 없습니다. 다시 평가해 주세요.",
    },
    "DEFAULT": {
        "zh": "系统暂时无法完成这次请求。请稍后重试，或换一个财富相关问题。",
        "en": "The system could not complete this request right now. Please try again later, or ask a wealth-related question.",
        "ko": "현재 요청을 완료할 수 없습니다. 잠시 후 다시 시도하거나 재물 관련 질문으로 바꿔 주세요.",
    },
}

_RATE_LIMIT_FALLBACK: dict[str, dict[str, Any]] = {}
_DEDUP_FALLBACK: dict[str, float] = {}


def _ok(payload: dict) -> dict:
    return {"ok": True, "code": "OK", "data": payload}


def _fail(error: PredictiveServiceError, details: dict | None = None) -> JSONResponse:
    user_message = _user_error_message(error.code)
    return JSONResponse(
        status_code=error.status,
        content={
            "ok": False,
            "code": error.code,
            "message": user_message["zh"],
            "user_message": user_message,
            "details": details or {},
        },
    )


def _fail_value(message: str) -> JSONResponse:
    user_message = _user_error_message("CONTRACT_SCHEMA_INVALID")
    return JSONResponse(
        status_code=400,
        content={"ok": False, "code": "CONTRACT_SCHEMA_INVALID", "message": user_message["zh"], "user_message": user_message, "details": {}},
    )


def _extract_prediction_id(payload: dict) -> str:
    prediction_id = str(payload.get("prediction_id") or payload.get("id") or "").strip()
    if not prediction_id:
        raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "prediction_id required")
    return prediction_id


def _actor_role(request: Optional[Request], payload: Optional[dict] = None) -> str:
    actor = "system"
    if payload:
        actor = str(payload.get("actor_role") or actor).strip().lower()
    if request is None:
        return actor
    user = get_request_user(request)
    if not user:
        return actor
    return str(user.get("role") or actor).strip().lower()


def _actor_user_id(request: Optional[Request], payload: Optional[dict] = None) -> int:
    if payload and "actor_user_id" in payload:
        try:
            return int(payload.get("actor_user_id"))
        except (TypeError, ValueError):
            pass
    if request is None:
        return 0
    user = get_request_user(request)
    if not user:
        return 0
    user_id = int(user.get("id") or 0)
    return user_id


def _safe_str(value: object, default: str = "") -> str:
    text = str(value) if value is not None else ""
    return text.strip() or default


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _user_error_message(code: str) -> dict[str, str]:
    return dict(_ERROR_COPY.get(_safe_str(code).upper()) or _ERROR_COPY["DEFAULT"])


def _client_identity(request: Request) -> str:
    forwarded = _safe_str(request.headers.get("x-forwarded-for")).split(",")[0].strip()
    host = forwarded or _safe_str(getattr(request.client, "host", "unknown"), "unknown")
    raw = f"{host}:{_safe_str(request.headers.get('user-agent'))[:120]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _redis_get_json(key: str) -> Any:
    try:
        return predictive_service._redis.get_json(key)
    except Exception as exc:
        logger.warning("v18_1 redis get failed; using in-process fallback key=%s error=%s", key, exc)
        return None


def _redis_set_json(key: str, value: Any, ttl_seconds: int) -> bool:
    try:
        predictive_service._redis.set_json(key, value, ttl_seconds=ttl_seconds)
        return True
    except Exception as exc:
        logger.warning("v18_1 redis set failed; using in-process fallback key=%s error=%s", key, exc)
        return False


def _rate_limit(request: Request, bucket: str, *, limit: int, window_seconds: int, key_extra: str = "") -> None:
    identity = _client_identity(request)
    now = time.time()
    window = int(now // max(1, window_seconds))
    key = f"rate:v18_1:{bucket}:{identity}:{key_extra}:{window}"
    current = _redis_get_json(key)
    if isinstance(current, dict):
        count = _safe_int(current.get("count"), 0)
        if count >= limit:
            raise PredictiveServiceError("RATE_LIMITED", "rate limited", 429)
        _redis_set_json(key, {"count": count + 1, "updated_at": now}, ttl_seconds=window_seconds + 2)
        return
    if current is not None:
        count = _safe_int(current, 0)
        if count >= limit:
            raise PredictiveServiceError("RATE_LIMITED", "rate limited", 429)
        _redis_set_json(key, count + 1, ttl_seconds=window_seconds + 2)
        return

    fallback = _RATE_LIMIT_FALLBACK.get(key)
    if fallback and float(fallback.get("expires_at", 0)) > now:
        count = _safe_int(fallback.get("count"), 0)
        if count >= limit:
            raise PredictiveServiceError("RATE_LIMITED", "rate limited", 429)
        fallback["count"] = count + 1
        return
    _RATE_LIMIT_FALLBACK[key] = {"count": 1, "expires_at": now + window_seconds}
    _redis_set_json(key, {"count": 1, "updated_at": now}, ttl_seconds=window_seconds + 2)


def _dedupe_once(request: Request, bucket: str, fingerprint: str, ttl_seconds: int = 86400) -> None:
    now = time.time()
    identity = _client_identity(request)
    digest = hashlib.sha256(f"{identity}:{fingerprint}".encode("utf-8")).hexdigest()
    key = f"dedupe:v18_1:{bucket}:{digest}"
    if _redis_get_json(key):
        raise PredictiveServiceError("DUPLICATE_FEEDBACK", "duplicate feedback", 409)
    expires_at = _DEDUP_FALLBACK.get(key)
    if expires_at and expires_at > now:
        raise PredictiveServiceError("DUPLICATE_FEEDBACK", "duplicate feedback", 409)
    _DEDUP_FALLBACK[key] = now + ttl_seconds
    _redis_set_json(key, {"seen": True, "created_at": now}, ttl_seconds=ttl_seconds)


def _enrich_actor_context(payload: dict, request: Optional[Request] = None) -> dict:
    next_payload = dict(payload)
    next_payload["actor_role"] = _actor_role(request, payload)
    next_payload["actor_user_id"] = _actor_user_id(request, payload)
    if request is not None:
        user = get_request_user(request)
        if user:
            next_payload["actor_username"] = str(user.get("username") or user.get("id") or "").strip()
    return next_payload


@router.api_route("/api/v18_1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def v18_1_underscore_api_alias(path: str, request: Request):
    """Compatibility alias for clients opened from backend origin.

    The Next.js frontend proxy uses /api/v18_1/* because filesystem route
    segments with dots are awkward. If a browser opens the app through the
    backend origin instead of the Next origin, that proxy layer is absent, so
    this alias safely re-dispatches to the canonical /api/v18.1/* routes.
    """
    body = await request.body()
    target_path = f"/api/v18.1/{path}"
    scope = dict(request.scope)
    scope["path"] = target_path
    scope["raw_path"] = target_path.encode("utf-8")
    scope["path_params"] = {}
    scope.pop("route", None)
    scope.pop("endpoint", None)

    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    messages: list[dict] = []

    async def send(message: dict):
        messages.append(message)

    await request.app(scope, receive, send)
    status_code = 500
    headers: list[tuple[bytes, bytes]] = []
    chunks: list[bytes] = []
    for message in messages:
        if message.get("type") == "http.response.start":
            status_code = int(message.get("status") or 500)
            headers = list(message.get("headers") or [])
        elif message.get("type") == "http.response.body":
            chunk = message.get("body") or b""
            if chunk:
                chunks.append(chunk)
    response_headers: dict[str, str] = {}
    for key, value in headers:
        text_key = key.decode("latin-1")
        if text_key.lower() in {"content-length", "transfer-encoding"}:
            continue
        response_headers[text_key] = value.decode("latin-1")
    return Response(content=b"".join(chunks), status_code=status_code, headers=response_headers)


def _require_admin(request: Request) -> dict:
    user = get_request_user(request)
    if not user or str(user.get("role") or "").strip().lower() != "admin":
        raise PredictiveServiceError("ADMIN_REQUIRED", "admin role required", 403)
    return user


def _latest_audit_event_dict() -> dict:
    if not predictive_service._rule_audit_events:
        return {}
    return predictive_service._rule_audit_events[-1].to_dict()


def _bootstrap_audit_step(
    *,
    step_key: str,
    status: str,
    rule_id: str,
    actor_role: str,
    actor_user_id: int,
    details: dict,
    error: str = "",
) -> dict:
    predictive_service._append_audit_event(
        rule_id=rule_id,
        event_type=f"ADMIN_BOOTSTRAP_{step_key.upper()}_{status.upper()}",
        severity="error" if status == "failed" else "info",
        message=error or f"admin bootstrap step {step_key} {status}",
        actor_role=actor_role,
        actor_user_id=actor_user_id,
        source="admin-rule-bootstrap",
        details=details,
    )
    predictive_service._persist()
    event = _latest_audit_event_dict()
    return {
        "step_key": step_key,
        "status": status,
        "object_id": _safe_str(details.get("object_id")),
        "audit_event_id": _safe_str(event.get("event_hash")),
        "audit_event_type": _safe_str(event.get("event_type")),
        "error": error,
        "details": details,
    }


@router.post("/v18.1/admin/rule-bootstrap/wealth")
@router.post("/api/v18.1/admin/rule-bootstrap/wealth")
async def admin_bootstrap_wealth_rule(payload: dict, request: Request):
    steps: list[dict] = []
    try:
        user = _require_admin(request)
        actor_role = "admin"
        actor_user_id = int(user.get("id") or 0)
        suffix = _safe_str(payload.get("bootstrap_id"), str(int(time.time())))
        safe_suffix = "".join(ch if ch.isalnum() else "_" for ch in suffix)[:48]
        rule_id = _safe_str(payload.get("rule_id"), "bootstrap.wealth.baseline")
        version = _safe_str(payload.get("version"), f"v{safe_suffix}")
        card_id = _safe_str(payload.get("knowledge_card_id"), f"kc.bootstrap.wealth.{safe_suffix}")
        case_id = _safe_str(payload.get("test_case_id"), f"tc.bootstrap.wealth.{safe_suffix}")

        card = predictive_service.register_knowledge_card(
            {
                "card_id": card_id,
                "knowledge_domain": "wealth",
                "title": "Bootstrap Wealth Prediction Rule",
                "summary": "Minimal active wealth rule used to prove the audited Agent prediction lifecycle.",
                "status": "draft",
                "version": "v1",
                "source_refs": ["admin-bootstrap:p3-b"],
                "tags": ["wealth", "bootstrap", "agent"],
                "content": {
                    "principle": "complete birth data allows a baseline wealth signal to be evaluated through Contract-first prediction.",
                    "guardrail": "This bootstrap creates only a sandbox candidate first; activation happens after Rule Test and Reviewer approve.",
                },
                "created_by": "admin-bootstrap",
            },
            actor_role=actor_role,
            actor_user_id=actor_user_id,
        )
        steps.append(
            _bootstrap_audit_step(
                step_key="knowledge_card",
                status="passed",
                rule_id=rule_id,
                actor_role=actor_role,
                actor_user_id=actor_user_id,
                details={"object_id": card.get("card_id"), "status": card.get("status"), "version": card.get("version")},
            )
        )

        candidate = predictive_service.build_sandbox_rule_candidate(
            {
                "knowledge_card_id": card_id,
                "rule_candidate": {
                    "rule_id": rule_id,
                    "knowledge_card_id": card_id,
                    "theory_family": "bootstrap_wealth",
                    "condition": {"complete_birth_fields": True},
                    "effect": {"wealth": 0.62},
                    "priority": 0.72,
                    "evidence_strength": 0.84,
                    "conflict_policy": "merge",
                    "version": version,
                    "owner_plugin": "plugin.agent",
                    "status": "experimental",
                    "effect_scope": ["wealth"],
                    "allowed_topics": ["wealth"],
                },
            },
            actor_role=actor_role,
            actor_user_id=actor_user_id,
        )
        rule_payload = dict(candidate.get("rule_payload") or {})
        steps.append(
            _bootstrap_audit_step(
                step_key="sandbox_candidate",
                status="passed",
                rule_id=rule_id,
                actor_role=actor_role,
                actor_user_id=actor_user_id,
                details={
                    "object_id": candidate.get("candidate_id"),
                    "candidate_state": candidate.get("candidate_state"),
                    "rule_id": rule_payload.get("rule_id"),
                    "version": rule_payload.get("version"),
                    "content_hash": rule_payload.get("content_hash"),
                },
            )
        )

        test_case = predictive_service.register_rule_test_case(
            {
                "case_id": case_id,
                "source": "synthetic",
                "chart_snapshot": {"matched_facts": ["complete_birth_fields"], "four_pillars": {"year": "甲子"}},
                "query_intent": {"topic": "wealth", "intent": "prediction"},
                "expected_conclusions": ["wealth"],
                "expected_evidence_patterns": ["complete_birth_fields", "wealth"],
                "forbidden_conclusions": ["bankruptcy", "破产"],
                "tags": ["wealth", "bootstrap", "synthetic"],
            },
            actor_role=actor_role,
            actor_user_id=actor_user_id,
        )
        steps.append(
            _bootstrap_audit_step(
                step_key="synthetic_test_case",
                status="passed",
                rule_id=rule_id,
                actor_role=actor_role,
                actor_user_id=actor_user_id,
                details={"object_id": test_case.get("case_id"), "source": test_case.get("source")},
            )
        )

        test_run = predictive_runtime_facade.run_rule_test_v02(
            {
                "rule_candidate_id": candidate.get("candidate_id"),
                "test_case_ids": [test_case.get("case_id")],
            },
            actor_role,
            actor_user_id,
        )
        if _safe_str(test_run.get("overall_status")) != "pass":
            raise PredictiveServiceError("RULE_TEST_FAILED", "bootstrap candidate did not pass Rule Test Engine", 409)
        steps.append(
            _bootstrap_audit_step(
                step_key="rule_test_run",
                status="passed",
                rule_id=rule_id,
                actor_role=actor_role,
                actor_user_id=actor_user_id,
                details={
                    "object_id": test_run.get("run_id"),
                    "overall_status": test_run.get("overall_status"),
                    "pass_count": test_run.get("pass_count"),
                    "fail_count": test_run.get("fail_count"),
                    "warning_count": test_run.get("warning_count"),
                },
            )
        )

        pr = predictive_service.append_knowledge_pr(
            {
                "prediction_id": f"bootstrap-{safe_suffix}",
                "requested_by": "admin",
                "knowledge_card_id": card_id,
                "target_status": "validated",
                "rule_candidate_id": candidate.get("candidate_id"),
            }
        )
        steps.append(
            _bootstrap_audit_step(
                step_key="knowledge_pr",
                status="passed",
                rule_id=rule_id,
                actor_role=actor_role,
                actor_user_id=actor_user_id,
                details={
                    "object_id": pr.get("pr_id"),
                    "review_state": pr.get("review_state"),
                    "rule_candidate_id": pr.get("rule_candidate_id"),
                },
            )
        )

        reviewed = predictive_service.review_knowledge_pr(
            {
                "pr_id": pr.get("pr_id"),
                "decision": "approve",
                "actor_user_id": actor_user_id,
            },
            actor_role=actor_role,
        )
        materialized = dict(reviewed.get("materialized_rule") or {})
        steps.append(
            _bootstrap_audit_step(
                step_key="reviewer_approve",
                status="passed",
                rule_id=rule_id,
                actor_role=actor_role,
                actor_user_id=actor_user_id,
                details={
                    "object_id": reviewed.get("pr_id"),
                    "review_state": reviewed.get("review_state"),
                    "materialized_rule_id": materialized.get("rule_id"),
                    "version": materialized.get("version"),
                    "content_hash": materialized.get("content_hash"),
                    "status": materialized.get("status"),
                },
            )
        )

        activated = predictive_service.update_rule_status(
            rule_id,
            "active",
            actor_role=actor_role,
            actor_user_id=actor_user_id,
            version=version,
        )
        steps.append(
            _bootstrap_audit_step(
                step_key="activate",
                status="passed",
                rule_id=rule_id,
                actor_role=actor_role,
                actor_user_id=actor_user_id,
                details={
                    "object_id": activated.rule_id,
                    "rule_id": activated.rule_id,
                    "version": activated.version,
                    "content_hash": activated.content_hash,
                    "status": activated.status,
                    "approved_by": activated.approved_by,
                    "approved_at": activated.approved_at,
                },
            )
        )

        active_rules = [rule.to_dict() for rule in predictive_service.list_rules(status="active")]
        steps.append(
            _bootstrap_audit_step(
                step_key="active_snapshot_refresh",
                status="passed",
                rule_id=rule_id,
                actor_role=actor_role,
                actor_user_id=actor_user_id,
                details={"object_id": "active_rules_snapshot", "active_rule_count": len(active_rules)},
            )
        )

        return _ok(
            {
                "steps": steps,
                "active_rule": activated.to_dict(),
                "active_rules": active_rules,
                "knowledge_card": card,
                "rule_candidate": candidate,
                "rule_test_run": test_run,
                "knowledge_pr": reviewed,
            }
        )
    except PredictiveServiceError as exc:
        steps.append(
            _bootstrap_audit_step(
                step_key="bootstrap",
                status="failed",
                rule_id=_safe_str(payload.get("rule_id"), "bootstrap.wealth.baseline"),
                actor_role="admin",
                actor_user_id=_actor_user_id(request, payload),
                details={"object_id": "admin_bootstrap", "code": exc.code},
                error=exc.message,
            )
        )
        user_message = _user_error_message(exc.code)
        return JSONResponse(
            status_code=exc.status,
            content={"ok": False, "code": exc.code, "message": user_message["zh"], "user_message": user_message, "details": {}, "data": {"steps": steps}},
        )
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/rule-kernels")
@router.post("/api/v18.1/rule-kernels")
async def register_rule_kernel(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        data = predictive_service.register_rule(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(data)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/rule-kernels/{rule_id}")
@router.get("/api/v18.1/rule-kernels/{rule_id}")
async def get_rule_kernel(rule_id: str):
    try:
        rule = predictive_service.get_rule(rule_id)
        return _ok(rule.to_dict())
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/rule-kernels")
@router.get("/api/v18.1/rule-kernels")
async def list_rule_kernels(
    effect_scope: str | None = None,
    status: str | None = None,
    owner_plugin: str | None = None,
):
    rules = predictive_service.list_rules(effect_scope=effect_scope, status=status, owner_plugin=owner_plugin)
    return _ok({"items": [r.to_dict() for r in rules], "total": len(rules)})


@router.post("/v18.1/rule-kernels/{rule_id}/status")
@router.post("/api/v18.1/rule-kernels/{rule_id}/status")
async def update_rule_kernel_status(rule_id: str, payload: dict, request: Request):
    try:
        target_status = str(payload.get("target_status") or "").strip()
        if not target_status:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "target_status required")
        payload = _enrich_actor_context(payload, request)
        version = _safe_str(payload.get("version"))
        rule = predictive_service.update_rule_status(
            rule_id,
            target_status,
            actor_role=_safe_str(payload.get("actor_role"), _actor_role(request, payload)),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
            version=version or None,
        )
        return _ok(
            {
                "rule_id": rule.rule_id,
                "status": rule.status,
                "version": rule.version,
                "content_hash": rule.content_hash,
                "created_by": rule.created_by,
                "approved_by": rule.approved_by,
                "approved_at": rule.approved_at,
            }
        )
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/rules/quality-scores")
@router.get("/api/v18.1/rules/quality-scores")
async def rule_quality_scores():
    try:
        return _ok(predictive_service.query_rule_quality_scores())
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/rules/quality-scores/recompute")
@router.post("/api/v18.1/rules/quality-scores/recompute")
async def rule_quality_scores_recompute():
    try:
        return _ok(predictive_service.recompute_rule_quality_scores())
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/rules/{rule_id}/quality-score")
@router.get("/api/v18.1/rules/{rule_id}/quality-score")
async def rule_quality_score_get(rule_id: str, version: str | None = None):
    try:
        return _ok(predictive_service.get_rule_quality_score(rule_id, version=version))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/rule-retrieval")
@router.post("/api/v18.1/rule-retrieval")
async def rule_retrieval(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(dict(payload), request)
        rules = predictive_runtime_facade.run_rule_retrieval(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok({"prediction_id": str(payload.get("prediction_id", "")).strip(), "candidates": [r.to_dict() for r in rules], "retrieval_state": "ok"})
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/rule-resolver")
@router.post("/api/v18.1/rule-resolver")
async def rule_resolver(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        data = predictive_runtime_facade.run_resolver(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(data)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/prediction-contracts/builder")
@router.post("/api/v18.1/prediction-contracts/builder")
async def prediction_contract_builder(payload: dict):
    try:
        resolved_rules = payload.get("resolved_rules", {})
        contract_payload = payload
        if "resolved_rules" in payload and "prediction_id" not in payload:
            contract_payload = payload.get("contract", payload)
        contract = predictive_service.build_contract(contract_payload, resolved_rules=resolved_rules)
        contract_dict = contract.__dict__ if hasattr(contract, "__dict__") else {}
        return _ok(
            {
                "prediction_contract": contract_dict,
            }
        )
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/predictions/contract-pipeline")
@router.post("/api/v18.1/predictions/contract-pipeline")
async def prediction_contract_pipeline(payload: dict, request: Request):
    try:
        _rate_limit(request, "contract_pipeline", limit=60, window_seconds=60)
        payload = _enrich_actor_context(payload, request)
        result = predictive_runtime_facade.run_prediction_contract_pipeline(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


def _extract_contract(payload: dict) -> dict:
    if "contract" in payload and isinstance(payload.get("contract"), dict):
        return dict(payload["contract"])
    if "prediction_contract" in payload and isinstance(payload.get("prediction_contract"), dict):
        return dict(payload["prediction_contract"])
    if "contract_payload" in payload and isinstance(payload.get("contract_payload"), dict):
        return dict(payload["contract_payload"])
    return dict(payload)


@router.post("/v18.1/prediction-ledger/records")
@router.post("/api/v18.1/prediction-ledger/records")
async def prediction_ledger_write(payload: dict):
    try:
        prediction_id = _extract_prediction_id(payload)
        contract = _extract_contract(payload)
        record = predictive_service.write_ledger_record(payload={"prediction_id": prediction_id}, contract=contract)
        return _ok(
            {
                "ledger_id": f"led_{prediction_id}",
                "prediction_id": prediction_id,
                "prediction_hash": record.prediction_hash,
                "schema_version": record.schema_version,
                "state": record.state,
            }
        )
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/prediction-ledger/records/{prediction_id}")
@router.get("/api/v18.1/prediction-ledger/records/{prediction_id}")
async def prediction_ledger_get(prediction_id: str):
    try:
        record = predictive_service.get_ledger(prediction_id)
        return _ok({"record": record})
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/predictions/{prediction_id}/ledger")
@router.get("/api/v18.1/predictions/{prediction_id}/ledger")
async def prediction_ledger_get_alias(prediction_id: str):
    try:
        return _ok({"record": predictive_service.get_ledger(prediction_id)})
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/predictions/{prediction_id}/replay")
@router.get("/api/v18.1/predictions/{prediction_id}/replay")
async def prediction_replay(prediction_id: str):
    try:
        return _ok(predictive_service.replay_prediction(prediction_id))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/predictions/{prediction_id}/public-replay")
@router.get("/api/v18.1/predictions/{prediction_id}/public-replay")
async def prediction_public_replay(prediction_id: str, request: Request):
    try:
        _rate_limit(request, "public_replay", limit=120, window_seconds=60, key_extra=prediction_id[:32])
        return _ok(predictive_service.public_replay_prediction(prediction_id))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/predictions/{prediction_id}/explain")
@router.post("/api/v18.1/predictions/{prediction_id}/explain")
async def prediction_explain(prediction_id: str, payload: dict, request: Request):
    try:
        _rate_limit(request, "prediction_explain", limit=60, window_seconds=60, key_extra=prediction_id[:32])
        result = predictive_service.explain_prediction(prediction_id, dict(payload or {}))
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/llm-output-verifier")
@router.post("/api/v18.1/llm-output-verifier")
async def llm_output_verifier(payload: dict):
    try:
        result = predictive_service.run_verifier(payload)
        status = result["result"]
        return _ok({"result": status, "checks": result["checks"], "action": result["action"], "verifier_run_id": result["verifier_run_id"]})
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/feedback")
@router.post("/api/v18.1/feedback")
async def feedback_collector(payload: dict, request: Request):
    try:
        _rate_limit(request, "feedback", limit=30, window_seconds=60)
        fingerprint = f"generic:{_safe_str(payload.get('prediction_id'))}:{_safe_str(payload.get('feedback_type'))}:{_safe_str(payload.get('conclusion_ref') or payload.get('conclusion_id'))}"
        _dedupe_once(request, "feedback", fingerprint)
        result = predictive_service.append_feedback(payload)
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/predictions/{prediction_id}/feedback")
@router.post("/api/v18.1/predictions/{prediction_id}/feedback")
async def prediction_feedback(prediction_id: str, payload: dict, request: Request):
    try:
        _rate_limit(request, "prediction_feedback", limit=30, window_seconds=60, key_extra=prediction_id[:32])
        if not _safe_str(payload.get("request_id")):
            fingerprint = f"{prediction_id}:{_safe_str(payload.get('feedback_type'))}:{_safe_str(payload.get('conclusion_ref') or payload.get('conclusion_id'))}"
            _dedupe_once(request, "feedback", fingerprint)
        result = predictive_service.append_prediction_feedback(prediction_id, payload)
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/feedback")
@router.get("/api/v18.1/feedback")
async def feedback_list(prediction_id: str | None = None, offset: int = 0, limit: int = 100):
    try:
        return _ok(predictive_service.query_feedback(prediction_id=prediction_id, offset=offset, limit=limit))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/trust-metrics")
@router.get("/api/v18.1/trust-metrics")
async def trust_metrics(request: Request):
    try:
        _rate_limit(request, "trust_metrics", limit=120, window_seconds=60)
        return _ok(predictive_service.query_trust_metrics())
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/core-bazi/features/extract")
@router.post("/api/v18.1/core-bazi/features/extract")
async def core_bazi_features_extract(payload: dict, request: Request):
    try:
        _rate_limit(request, "core_bazi_feature_extract", limit=60, window_seconds=60)
        return _ok(core_bazi_feature_service.extract_and_store(payload))
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/core-bazi/features/{bundle_id}")
@router.get("/api/v18.1/core-bazi/features/{bundle_id}")
async def core_bazi_features_get(bundle_id: str, request: Request):
    try:
        _rate_limit(request, "core_bazi_feature_get", limit=120, window_seconds=60)
        return _ok(core_bazi_feature_service.get_bundle(bundle_id))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/core-bazi/strength/evaluate")
@router.post("/api/v18.1/core-bazi/strength/evaluate")
async def core_bazi_strength_evaluate(payload: dict, request: Request):
    try:
        _rate_limit(request, "core_bazi_strength_evaluate", limit=60, window_seconds=60)
        return _ok(core_bazi_strength_service.evaluate_and_store(payload))
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/core-bazi/strength/{strength_bundle_id}")
@router.get("/api/v18.1/core-bazi/strength/{strength_bundle_id}")
async def core_bazi_strength_get(strength_bundle_id: str, request: Request):
    try:
        _rate_limit(request, "core_bazi_strength_get", limit=120, window_seconds=60)
        return _ok(core_bazi_strength_service.get_bundle(strength_bundle_id))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/core-bazi/structure/evaluate")
@router.post("/api/v18.1/core-bazi/structure/evaluate")
async def core_bazi_structure_evaluate(payload: dict, request: Request):
    try:
        _rate_limit(request, "core_bazi_structure_evaluate", limit=60, window_seconds=60)
        return _ok(core_bazi_structure_effect_service.evaluate_and_store(payload))
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/core-bazi/structure/{structure_bundle_id}")
@router.get("/api/v18.1/core-bazi/structure/{structure_bundle_id}")
async def core_bazi_structure_get(structure_bundle_id: str, request: Request):
    try:
        _rate_limit(request, "core_bazi_structure_get", limit=120, window_seconds=60)
        return _ok(core_bazi_structure_effect_service.get_bundle(structure_bundle_id))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/domain/wealth/evaluate")
@router.post("/api/v18.1/domain/wealth/evaluate")
async def wealth_domain_evaluate(payload: dict, request: Request):
    try:
        _rate_limit(request, "wealth_domain_evaluate", limit=60, window_seconds=60)
        return _ok(wealth_domain_service.evaluate_and_store(payload))
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/domain/wealth/{wealth_bundle_id}")
@router.get("/api/v18.1/domain/wealth/{wealth_bundle_id}")
async def wealth_domain_get(wealth_bundle_id: str, request: Request):
    try:
        _rate_limit(request, "wealth_domain_get", limit=120, window_seconds=60)
        return _ok(wealth_domain_service.get_bundle(wealth_bundle_id))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/learning/insights")
@router.get("/api/v18.1/learning/insights")
async def learning_insights():
    try:
        return _ok(predictive_service.query_learning_insights())
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/learning/insights/{insight_id}")
@router.get("/api/v18.1/learning/insights/{insight_id}")
async def learning_insight_get(insight_id: str):
    try:
        return _ok(predictive_service.get_learning_insight(insight_id))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/learning/suggestions")
@router.get("/api/v18.1/learning/suggestions")
async def learning_suggestions():
    try:
        return _ok(predictive_service.query_candidate_rule_suggestions())
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/learning/suggestions/{suggestion_id}/knowledge-card")
@router.post("/api/v18.1/learning/suggestions/{suggestion_id}/knowledge-card")
async def learning_suggestion_to_knowledge_card(suggestion_id: str, payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_service.create_knowledge_card_from_suggestion(
            suggestion_id,
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/knowledge-pr-queue")
@router.post("/api/v18.1/knowledge-pr-queue")
async def knowledge_pr_queue(payload: dict, request: Request):
    try:
        payload = dict(payload)
        if "requested_by" not in payload:
            payload["requested_by"] = _actor_role(request, payload)
        result = predictive_service.append_knowledge_pr(payload)
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/knowledge-pr-queue")
@router.get("/api/v18.1/knowledge-pr-queue")
async def knowledge_pr_queue_list(
    review_state: str | None = None,
    rule_id: str | None = None,
    knowledge_card_id: str | None = None,
    offset: int = 0,
    limit: int = 100,
):
    try:
        result = predictive_service.query_knowledge_pr_queue(
            review_state=review_state,
            rule_id=rule_id,
            knowledge_card_id=knowledge_card_id,
            offset=offset,
            limit=limit,
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/knowledge-pr-queue/{pr_id}/review")
@router.post("/api/v18.1/knowledge-pr-queue/{pr_id}/review")
async def knowledge_pr_queue_review(pr_id: str, payload: dict, request: Request):
    try:
        payload = dict(payload)
        payload["pr_id"] = pr_id
        result = predictive_service.review_knowledge_pr(payload, actor_role=_actor_role(request, payload))
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/rule-candidates/sandbox")
@router.post("/api/v18.1/rule-candidates/sandbox")
async def rule_candidate_sandbox(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_service.build_sandbox_rule_candidate(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/rule-candidates/sandbox")
@router.get("/api/v18.1/rule-candidates/sandbox")
async def rule_candidate_sandbox_list(
    candidate_state: str | None = "sandbox",
    rule_id: str | None = None,
    knowledge_card_id: str | None = None,
    offset: int = 0,
    limit: int = 100,
):
    try:
        return _ok(
            predictive_service.query_rule_candidates(
                candidate_state=candidate_state,
                rule_id=rule_id,
                knowledge_card_id=knowledge_card_id,
                offset=offset,
                limit=limit,
            )
        )
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/knowledge-cards")
@router.post("/api/v18.1/knowledge-cards")
async def knowledge_cards_submit(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_service.register_knowledge_card(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/knowledge-cards")
@router.get("/api/v18.1/knowledge-cards")
async def knowledge_cards_list(
    knowledge_domain: str | None = None,
    status: str | None = None,
    tag: str | None = None,
):
    try:
        cards = predictive_service.list_knowledge_cards(
            knowledge_domain=knowledge_domain,
            status=status,
            tag=tag,
        )
        return _ok({"items": [card.to_dict() for card in cards], "total": len(cards)})
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/knowledge-cards/{card_id}")
@router.get("/api/v18.1/knowledge-cards/{card_id}")
async def knowledge_card_get(card_id: str, version: str | None = None):
    try:
        card = predictive_service.get_knowledge_card(card_id, version=version)
        return _ok(card.to_dict())
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/knowledge-cards/{card_id}/status")
@router.post("/api/v18.1/knowledge-cards/{card_id}/status")
async def knowledge_card_status_update(card_id: str, payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        target_status = str(payload.get("target_status") or "").strip()
        if not target_status:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "target_status required")
        version = _safe_str(payload.get("version"))
        card = predictive_service.update_knowledge_card_status(
            card_id=card_id,
            target_status=target_status,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
            version=version or None,
        )
        return _ok(
            {
                "card_id": card.card_id,
                "status": card.status,
                "version": card.version,
                "content_hash": card.content_hash,
                "created_by": card.created_by,
                "approved_by": card.approved_by,
                "approved_at": card.approved_at,
            }
        )
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/knowledge-base/units")
@router.post("/api/v18.1/knowledge-base/units")
async def bazi_knowledge_unit_create(payload: dict, request: Request):
    try:
        _require_admin(request)
        payload = _enrich_actor_context(payload, request)
        result = predictive_service.register_bazi_knowledge_unit(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/knowledge-base/units")
@router.get("/api/v18.1/knowledge-base/units")
async def bazi_knowledge_units_list(
    domain: str | None = None,
    category: str | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 100,
):
    try:
        return _ok(
            predictive_service.list_bazi_knowledge_units(
                domain=domain,
                category=category,
                status=status,
                offset=offset,
                limit=limit,
            )
        )
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/knowledge-base/units/{knowledge_id}")
@router.get("/api/v18.1/knowledge-base/units/{knowledge_id}")
async def bazi_knowledge_unit_get(knowledge_id: str):
    try:
        return _ok(predictive_service.get_bazi_knowledge_unit(knowledge_id))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/knowledge-base/units/{knowledge_id}/review")
@router.post("/api/v18.1/knowledge-base/units/{knowledge_id}/review")
async def bazi_knowledge_unit_review(knowledge_id: str, payload: dict, request: Request):
    try:
        _require_admin(request)
        payload = _enrich_actor_context(payload, request)
        return _ok(
            predictive_service.review_bazi_knowledge_unit(
                knowledge_id,
                payload,
                actor_role=_safe_str(payload.get("actor_role"), "system"),
                actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
            )
        )
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/knowledge-base/units/{knowledge_id}/deprecate")
@router.post("/api/v18.1/knowledge-base/units/{knowledge_id}/deprecate")
async def bazi_knowledge_unit_deprecate(knowledge_id: str, payload: dict, request: Request):
    try:
        _require_admin(request)
        payload = _enrich_actor_context(payload, request)
        return _ok(
            predictive_service.deprecate_bazi_knowledge_unit(
                knowledge_id,
                payload,
                actor_role=_safe_str(payload.get("actor_role"), "system"),
                actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
            )
        )
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/knowledge-base/units/{knowledge_id}/to-rule-candidate")
@router.post("/api/v18.1/knowledge-base/units/{knowledge_id}/to-rule-candidate")
async def bazi_knowledge_unit_to_rule_candidate(knowledge_id: str, payload: dict, request: Request):
    try:
        _require_admin(request)
        payload = _enrich_actor_context(payload, request)
        return _ok(
            predictive_service.bazi_knowledge_unit_to_rule_candidate(
                knowledge_id,
                payload,
                actor_role=_safe_str(payload.get("actor_role"), "system"),
                actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
            )
        )
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/knowledge-base/units/{knowledge_id}/dry-run-audit")
@router.post("/api/v18.1/knowledge-base/units/{knowledge_id}/dry-run-audit")
async def bazi_knowledge_unit_dry_run_audit(knowledge_id: str, payload: dict, request: Request):
    try:
        _require_admin(request)
        payload = _enrich_actor_context(payload, request)
        return _ok(
            predictive_service.dry_run_bazi_knowledge_audit(
                knowledge_id,
                payload,
                actor_role=_safe_str(payload.get("actor_role"), "system"),
                actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
            )
        )
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/rule-tests/run")
@router.post("/api/v18.1/rule-tests/run")
async def rule_test_run(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_runtime_facade.run_rule_test(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/rule-test-cases")
@router.post("/api/v18.1/rule-test-cases")
async def rule_test_case_create(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_service.register_rule_test_case(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/rule-test-cases")
@router.get("/api/v18.1/rule-test-cases")
async def rule_test_case_list(
    source: str | None = None,
    tag: str | None = None,
    offset: int = 0,
    limit: int = 100,
):
    try:
        return _ok(predictive_service.query_rule_test_cases(source=source, tag=tag, offset=offset, limit=limit))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/rule-test-runs")
@router.post("/api/v18.1/rule-test-runs")
async def rule_test_run_v02(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_runtime_facade.run_rule_test_v02(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/rule-test-runs/{run_id}")
@router.get("/api/v18.1/rule-test-runs/{run_id}")
async def rule_test_run_get_v02(run_id: str):
    try:
        return _ok(predictive_service.get_rule_test_run(run_id))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/rule-test-suites")
@router.post("/api/v18.1/rule-test-suites")
async def register_rule_test_suite(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_service.register_rule_test_suite(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/rule-test-suites")
@router.get("/api/v18.1/rule-test-suites")
async def rule_test_suites_list(
    rule_id: str | None = None,
    suite_id: str | None = None,
    status: str | None = None,
):
    try:
        suites = predictive_service.list_rule_test_suites(rule_id=rule_id, suite_id=suite_id, status=status)
        return _ok({"items": [suite.to_dict() for suite in suites], "total": len(suites)})
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/rule-test-suites/{suite_id}")
@router.get("/api/v18.1/rule-test-suites/{suite_id}")
async def rule_test_suite_get(suite_id: str, version: str | None = None):
    try:
        suite = predictive_service.get_rule_test_suite(suite_id, version=version)
        return _ok(suite.to_dict())
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/rule-test-suites/{suite_id}/status")
@router.post("/api/v18.1/rule-test-suites/{suite_id}/status")
async def rule_test_suite_status_update(suite_id: str, payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        target_status = str(payload.get("target_status") or "").strip()
        if not target_status:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "target_status required")
        version = _safe_str(payload.get("version"))
        suite = predictive_service.update_rule_test_suite_status(
            suite_id=suite_id,
            target_status=target_status,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
            version=version or None,
        )
        return _ok({"suite_id": suite.suite_id, "status": suite.status, "version": suite.version})
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/rule-test-suites/{suite_id}/deprecate")
@router.post("/api/v18.1/rule-test-suites/{suite_id}/deprecate")
async def rule_test_suite_deprecate(suite_id: str, payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        version = _safe_str(payload.get("version"))
        suite = predictive_service.deprecate_rule_test_suite(
            suite_id=suite_id,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
            version=version or None,
        )
        return _ok({"suite_id": suite.suite_id, "status": suite.status, "version": suite.version})
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/rule-test-suites/{suite_id}/run")
@router.post("/api/v18.1/rule-test-suites/{suite_id}/run")
async def rule_test_suite_run(suite_id: str, payload: dict, request: Request, suite_version: str | None = None):
    try:
        payload = _enrich_actor_context(payload, request)
        payload = dict(payload)
        payload["suite_id"] = suite_id
        if suite_version:
            payload["suite_version"] = suite_version
        result = predictive_runtime_facade.run_rule_test(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/rule-tests/results")
@router.get("/api/v18.1/rule-tests/results")
async def rule_test_results(
    rule_id: str | None = None,
    suite_id: str | None = None,
    run_id: str | None = None,
    quality_gate: str | None = None,
    min_quality_score: float | None = None,
    max_quality_score: float | None = None,
    sort: str = "desc",
    offset: int = 0,
    limit: int = 50,
):
    try:
        result = predictive_service.query_rule_test_results(
            rule_id=rule_id,
            suite_id=suite_id,
            run_id=run_id,
            quality_gate=quality_gate,
            min_quality_score=min_quality_score,
            max_quality_score=max_quality_score,
            sort=sort,
            offset=offset,
            limit=limit,
        )
        return _ok(
            {
                "items": result["items"],
                "total_matched": result["total_matched"],
                "total_returned": result["total_returned"],
                "offset": result["offset"],
                "limit": result["limit"],
                "total": len(result["items"]),
            }
        )
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/rule-tests/dashboard")
@router.get("/api/v18.1/rule-tests/dashboard")
async def rule_test_dashboard(
    rule_id: str | None = None,
    suite_id: str | None = None,
    quality_gate: str | None = None,
    min_quality_score: float | None = None,
    max_quality_score: float | None = None,
    execution_mode: str | None = None,
    start_at: str | None = None,
    end_at: str | None = None,
    granularity: str = "day",
    trend_points: int = 30,
    latest_runs_limit: int = 10,
):
    try:
        result = predictive_service.get_rule_test_dashboard(
            rule_id=rule_id,
            suite_id=suite_id,
            quality_gate=quality_gate,
            min_quality_score=min_quality_score,
            max_quality_score=max_quality_score,
            execution_mode=execution_mode,
            start_at=start_at,
            end_at=end_at,
            granularity=granularity,
            trend_points=trend_points,
            latest_runs_limit=latest_runs_limit,
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/rule-test-engine/config")
@router.get("/api/v18.1/rule-test-engine/config")
async def rule_test_engine_config(version: str | None = None):
    try:
        result = predictive_service.get_rule_test_engine_config(version=version)
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/rule-audit-events")
@router.get("/api/v18.1/rule-audit-events")
@router.get("/v18.1/audit/events")
@router.get("/api/v18.1/audit/events")
async def rule_audit_events(
    rule_id: str | None = None,
    event_type: str | None = None,
    actor_role: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    sort: str = "desc",
    offset: int = 0,
    limit: int = 200,
):
    try:
        result = predictive_service.query_rule_audit_events(
            rule_id=rule_id,
            event_type=event_type,
            actor_role=actor_role,
            created_after=created_after,
            created_before=created_before,
            sort=sort,
            offset=offset,
            limit=limit,
        )
        return _ok(
            {
                "items": result["items"],
                "total_matched": result["total_matched"],
                "total_returned": result["total_returned"],
                "offset": result["offset"],
                "limit": result["limit"],
                "total": len(result["items"]),
            }
        )
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.get("/v18.1/audit/hash-chain")
@router.get("/api/v18.1/audit/hash-chain")
async def audit_hash_chain():
    try:
        return _ok(predictive_service.verify_audit_hash_chain())
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/storage/migrate-json-to-postgres")
@router.post("/api/v18.1/storage/migrate-json-to-postgres")
async def storage_migrate_json_to_postgres(payload: dict):
    try:
        return _ok(predictive_service.migrate_json_to_postgres(dsn=_safe_str(payload.get("dsn")) or None))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/agent/sessions")
@router.post("/api/v18.1/agent/sessions")
async def agent_session_create(payload: dict, request: Request):
    try:
        surface = _safe_str(payload.get("surface"))
        bucket = "demo_session" if surface == "landing_demo" or payload.get("is_demo") else "agent_session"
        _rate_limit(request, bucket, limit=20 if bucket == "demo_session" else 40, window_seconds=60)
        payload = _enrich_actor_context(payload, request)
        result = predictive_runtime_facade.create_agent_session(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "user"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/agent/sessions/{session_id}/turns")
@router.post("/api/v18.1/agent/sessions/{session_id}/turns")
async def agent_session_turn(session_id: str, payload: dict, request: Request):
    try:
        surface = _safe_str(payload.get("surface"))
        bucket = "demo_turn" if surface == "landing_demo" or payload.get("is_demo") else "agent_turn"
        _rate_limit(request, bucket, limit=10 if bucket == "demo_turn" else 30, window_seconds=60, key_extra=session_id[:32])
        payload = _enrich_actor_context(payload, request)
        result = predictive_runtime_facade.append_agent_turn(
            session_id,
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "user"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.get("/v18.1/agent/sessions/{session_id}")
@router.get("/api/v18.1/agent/sessions/{session_id}")
async def agent_session_get(session_id: str):
    try:
        return _ok(predictive_runtime_facade.get_agent_session(session_id))
    except PredictiveServiceError as exc:
        return _fail(exc)


@router.post("/v18.1/consumer-agent/bootstrap")
@router.post("/api/v18.1/consumer-agent/bootstrap")
async def consumer_agent_bootstrap(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_service.build_consumer_agent_bootstrap(payload)
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/consumer-agent/decompose")
@router.post("/api/v18.1/consumer-agent/decompose")
async def consumer_agent_decompose(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_service.decompose_user_question(payload)
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/consumer-agent/action-plan")
@router.post("/api/v18.1/consumer-agent/action-plan")
async def consumer_agent_action_plan(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_service.build_agent_action_plan(payload)
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/shadow-compare")
@router.post("/api/v18.1/shadow-compare")
async def shadow_compare(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_runtime_facade.run_shadow_compare(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


@router.post("/v18.1/wealth-pilot/run")
@router.post("/api/v18.1/wealth-pilot/run")
async def wealth_pilot_run(payload: dict, request: Request):
    try:
        payload = _enrich_actor_context(payload, request)
        result = predictive_runtime_facade.run_wealth_pilot(
            payload,
            actor_role=_safe_str(payload.get("actor_role"), "system"),
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
        )
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)


def _ensure_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        raw = float(value)
        if raw != raw:
            return default
        if raw < 0.0:
            return 0.0
        return raw
    except (TypeError, ValueError):
        return default
