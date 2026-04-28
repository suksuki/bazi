from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from v17_rebirth.backend.services.v18_1_predictive_engine import (
    PredictiveServiceError,
    predictive_runtime_facade,
    predictive_service,
)
from v17_rebirth.backend.services.auth_service import get_request_user

router = APIRouter()


def _ok(payload: dict) -> dict:
    return {"ok": True, "code": "OK", "data": payload}


def _fail(error: PredictiveServiceError, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=error.status,
        content={
            "ok": False,
            "code": error.code,
            "message": error.message,
            "details": details or {},
        },
    )


def _fail_value(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"ok": False, "code": "CONTRACT_SCHEMA_INVALID", "message": message, "details": {}},
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


def _enrich_actor_context(payload: dict, request: Optional[Request] = None) -> dict:
    next_payload = dict(payload)
    next_payload["actor_role"] = _actor_role(request, payload)
    next_payload["actor_user_id"] = _actor_user_id(request, payload)
    if request is not None:
        user = get_request_user(request)
        if user:
            next_payload["actor_username"] = str(user.get("username") or user.get("id") or "").strip()
    return next_payload


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
async def feedback_collector(payload: dict):
    try:
        result = predictive_service.append_feedback(payload)
        return _ok(result)
    except PredictiveServiceError as exc:
        return _fail(exc)


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
        return _ok({"card_id": card.card_id, "status": card.status, "version": card.version})
    except PredictiveServiceError as exc:
        return _fail(exc)
    except ValueError as exc:
        return _fail_value(str(exc))


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
