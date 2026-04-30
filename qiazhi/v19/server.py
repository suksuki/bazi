from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import json
import os
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, urlsplit

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from v19.guided_evidence_pack import evidence_pack_to_prompt_context
from v19.llm import build_agent_messages, call_llm, list_llm_models, probe_llm, test_llm_chat
from v19.agent import build_agent_turn
from v19.agent.income_stability import derive_income_stability
from v19.agent.renderers import render_income_stability_answer
from v19.knowledge_store import knowledge_status, list_knowledge_units, retrieve_knowledge, seed_knowledge
from v19.bazi_source_archive import (
    build_rule_proposal_from_knowledge_draft,
    create_excerpt_record,
    create_knowledge_draft,
    create_source_record,
    list_excerpt_records,
    list_knowledge_drafts,
    list_source_records,
    seed_current_knowledge_drafts,
    seed_source_archive,
    source_governance_overview,
    source_archive_status,
    update_knowledge_draft_review,
    update_source_record_status,
)
from v19.bazi_rule_db import (
    bazi_rule_db_status,
    build_structural_rule_signals,
    ingest_current_knowledge_drafts_to_rule_db,
    knowledge_rule_signal_coverage,
    list_bazi_rules,
)
from v19.bazi_guided_questions import build_guided_question_answer, build_guided_question_context, guided_answer_to_plain_text
from v19.rule_graph_runtime_context import build_rule_graph_runtime_context
from v19.synthetic_validation import (
    P11_GUIDED_SYNTHETIC_CASES,
    run_guided_synthetic_collision,
    run_p54_framework_chain_audit,
    run_p59_silent_evolution_cycle,
    run_p60_domain_route_eval,
    run_p60_silent_evolution_extension,
    run_p60_smart_approval_gate,
    build_p61_domain_route_backfill_candidates,
    build_p61_domain_route_backfill_eval_dataset,
    run_p61_domain_route_backfill_regression,
    build_p62_silent_training_ledger,
    run_p62_silent_training_ledger_regression,
    build_p63_silent_eval_queue,
    run_p63_silent_eval_queue_regression,
    build_p64_interactive_calibration_design,
    run_p64_interactive_calibration_design_regression,
    build_p65_mainline_completion_audit,
    run_p65_mainline_completion_regression,
)
from v19.lab_interfaces import (
    approve_bazi_rule_proposal,
    create_promotion_request,
    create_bazi_rule_proposal,
    create_guided_question_proposal,
    create_knowledge_batch_proposal_drafts,
    create_knowledge_review_batch,
    create_p21_knowledge_pack_review_packet,
    create_proposal_validation_run,
    create_proposal_review_approval_preflight,
    create_proposal_review_packet,
    create_revision_proposal,
    execute_p26_knowledge_to_rules,
    execute_p27_smart_rule_activation,
    execute_proposal_review_packet_approval,
    guided_question_answer_quality_report,
    guided_question_diversity_audit,
    guided_question_feedback_summary,
    guided_question_audit_report,
    activate_revision_record,
    approve_guided_question_proposal,
    approve_revision_proposal,
    create_governance_release,
    lab_status,
    label_contract,
    create_synthetic_promotion_candidate,
    list_active_rule_revisions,
    list_bazi_rule_proposals,
    list_bazi_rule_versions,
    list_feedback,
    list_guided_question_audits,
    list_guided_question_feedback,
    list_guided_question_library_versions,
    list_guided_question_proposals,
    list_governance_releases,
    list_knowledge_batch_proposal_runs,
    list_knowledge_review_batches,
    list_promotion_requests,
    list_proposal_validation_runs,
    list_proposal_review_packets,
    list_revision_proposals,
    list_rule_impacts,
    list_synthetic_promotion_candidates,
    list_validation_cases,
    list_validation_runs,
    register_feedback,
    review_synthetic_promotion_candidate,
    record_guided_question_audit,
    record_proposal_review_packet_decision,
    run_validation_cases,
    seed_p14_knowledge_review_batches,
    seed_p21_knowledge_review_batches,
    seed_validation_cases,
    update_promotion_status,
    update_guided_question_review,
    record_bazi_rule_version,
    record_guided_question_library_version,
    validate_bazi_rule_proposal,
    validate_guided_question_proposal,
    validate_revision_proposal,
)
from v19.runtime import (
    create_auth_session,
    create_bazi_profile,
    create_or_append_session,
    delete_bazi_profile,
    delete_auth_session,
    ensure_local_database,
    get_auth_session,
    get_bazi_profile,
    import_v17_admin_bazi_profiles,
    get_session,
    list_bazi_profiles,
    list_sessions,
    load_settings,
    normalize_settings_payload,
    public_settings,
    resolve_llm_base_url,
    save_settings,
    test_db,
    utc_now,
    update_bazi_profile,
)


ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"

app = FastAPI(title="V19 Standalone Agent", version="0.2.0")
LLM_EXECUTOR = ThreadPoolExecutor(max_workers=4)
VALID_ROLES = {"guest", "user", "practitioner", "admin"}
AUTH_COOKIE = "v19_auth_session"
ADMIN_USERNAME = os.getenv("V19_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("V19_ADMIN_PASSWORD", "abcd1235")
ADMIN_DEFAULT_PASSWORD_USED = os.getenv("V19_ADMIN_PASSWORD", "") == ""
ALLOW_ROLE_QUERY_FALLBACK = os.getenv("V19_ALLOW_ROLE_QUERY_FALLBACK", "1").lower() not in {"0", "false", "no"}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": "v19_standalone_agent", "version": "0.2.0"}


@app.get("/api/auth/me")
def auth_me(request: Request) -> Dict[str, Any]:
    session = _request_auth_session(request)
    role = _request_role(request) if session else "guest"
    return {
        "ok": True,
        "data": {
            "authenticated": bool(session),
            "role": role,
            "user_id": (session or {}).get("user_id", ""),
            "username": (session or {}).get("username", ""),
            "admin_default_password_used": ADMIN_DEFAULT_PASSWORD_USED,
            "role_query_fallback_enabled": ALLOW_ROLE_QUERY_FALLBACK,
        },
    }


@app.post("/api/auth/guest")
def auth_guest(response: Response) -> Dict[str, Any]:
    session = create_auth_session("guest", username="guest")
    _set_auth_cookie(response, session["token"])
    return {"ok": True, "data": _public_auth_session(session)}


@app.post("/api/auth/user/register")
def auth_user_register(payload: Dict[str, Any], response: Response) -> Dict[str, Any]:
    username = _clean_auth_name((payload or {}).get("username"), "local_user")
    session = create_auth_session("user", username=username)
    _set_auth_cookie(response, session["token"])
    return {"ok": True, "data": _public_auth_session(session)}


@app.post("/api/auth/user/login")
def auth_user_login(payload: Dict[str, Any], response: Response) -> Dict[str, Any]:
    username = _clean_auth_name((payload or {}).get("username"), "local_user")
    session = create_auth_session("user", username=username)
    _set_auth_cookie(response, session["token"])
    return {"ok": True, "data": _public_auth_session(session)}


@app.post("/api/auth/login")
def auth_login(payload: Dict[str, Any], response: Response) -> Dict[str, Any]:
    body = dict(payload or {})
    username = _clean_auth_name(body.get("username"), "local_user")
    password = str(body.get("password") or "")
    if username == ADMIN_USERNAME:
        if password != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail={"ok": False, "code": "ADMIN_LOGIN_FAILED", "message": "Admin login failed."})
        session = create_auth_session("admin", user_id="admin", username="admin")
        _set_auth_cookie(response, session["token"])
        return {"ok": True, "data": {**_public_auth_session(session), "admin_default_password_used": ADMIN_DEFAULT_PASSWORD_USED}}
    if username.lower().startswith("practitioner"):
        configured = os.getenv("V19_PRACTITIONER_PASSWORD", "")
        if configured and password != configured:
            raise HTTPException(status_code=401, detail={"ok": False, "code": "PRACTITIONER_LOGIN_FAILED", "message": "Practitioner login failed."})
        if not configured and not password:
            raise HTTPException(status_code=401, detail={"ok": False, "code": "PRACTITIONER_PASSWORD_REQUIRED", "message": "Practitioner password is required for local gate."})
        session = create_auth_session("practitioner", username=username)
        _set_auth_cookie(response, session["token"])
        return {"ok": True, "data": _public_auth_session(session)}
    session = create_auth_session("user", username=username)
    _set_auth_cookie(response, session["token"])
    return {"ok": True, "data": _public_auth_session(session)}


@app.post("/api/auth/practitioner/login")
def auth_practitioner_login(payload: Dict[str, Any], response: Response) -> Dict[str, Any]:
    body = dict(payload or {})
    username = _clean_auth_name(body.get("username"), "local_practitioner")
    password = str(body.get("password") or "")
    configured = os.getenv("V19_PRACTITIONER_PASSWORD", "")
    if configured and password != configured:
        raise HTTPException(status_code=401, detail={"ok": False, "code": "PRACTITIONER_LOGIN_FAILED", "message": "Practitioner login failed."})
    if not configured and not password:
        raise HTTPException(status_code=401, detail={"ok": False, "code": "PRACTITIONER_PASSWORD_REQUIRED", "message": "Practitioner password is required for local gate."})
    session = create_auth_session("practitioner", username=username)
    _set_auth_cookie(response, session["token"])
    return {"ok": True, "data": _public_auth_session(session)}


@app.post("/api/auth/admin/login")
def auth_admin_login(payload: Dict[str, Any], response: Response) -> Dict[str, Any]:
    body = dict(payload or {})
    username = str(body.get("username") or "")
    password = str(body.get("password") or "")
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail={"ok": False, "code": "ADMIN_LOGIN_FAILED", "message": "Admin login failed."})
    session = create_auth_session("admin", user_id="admin", username="admin")
    _set_auth_cookie(response, session["token"])
    return {"ok": True, "data": {**_public_auth_session(session), "admin_default_password_used": ADMIN_DEFAULT_PASSWORD_USED}}


@app.post("/api/auth/logout")
def auth_logout(request: Request, response: Response) -> Dict[str, Any]:
    token = request.cookies.get(AUTH_COOKIE, "")
    delete_auth_session(token)
    response.delete_cookie(AUTH_COOKIE, path="/")
    return {"ok": True}


@app.get("/api/profiles")
def profiles_get(request: Request) -> Dict[str, Any]:
    session = _require_auth(request)
    return {"ok": True, "data": {"items": list_bazi_profiles(str(session.get("user_id") or "")), "role": session.get("role")}}


@app.post("/api/profiles")
def profiles_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    session = _require_auth(request)
    profile = create_bazi_profile(str(session.get("user_id") or ""), dict(payload or {}))
    return {"ok": True, "data": profile}


@app.get("/api/profiles/{profile_id}")
def profile_get(profile_id: str, request: Request) -> Dict[str, Any]:
    session = _require_auth(request)
    profile = get_bazi_profile(profile_id, str(session.get("user_id") or ""))
    if not profile:
        raise HTTPException(status_code=404, detail={"ok": False, "code": "PROFILE_NOT_FOUND", "message": "Bazi profile not found."})
    return {"ok": True, "data": profile}


@app.put("/api/profiles/{profile_id}")
def profile_put(profile_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    session = _require_auth(request)
    profile = update_bazi_profile(profile_id, str(session.get("user_id") or ""), dict(payload or {}))
    if not profile:
        raise HTTPException(status_code=404, detail={"ok": False, "code": "PROFILE_NOT_FOUND", "message": "Bazi profile not found."})
    return {"ok": True, "data": profile}


@app.delete("/api/profiles/{profile_id}")
def profile_delete(profile_id: str, request: Request) -> Dict[str, Any]:
    session = _require_auth(request)
    deleted = delete_bazi_profile(profile_id, str(session.get("user_id") or ""))
    if not deleted:
        raise HTTPException(status_code=404, detail={"ok": False, "code": "PROFILE_NOT_FOUND", "message": "Bazi profile not found."})
    return {"ok": True, "data": {"deleted": True, "profile_id": profile_id}}


@app.post("/api/agent/turn")
def agent_turn(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    settings = load_settings()
    role = _request_role(request, dict(payload or {}).get("role"))
    payload = {**dict(payload or {}), "role": role}
    result = build_agent_turn(payload)
    if not result.get("ok"):
        return result

    data = dict(result.get("data") or {})
    income_stability = derive_income_stability(dict(data.get("chart") or {}))
    data["inference_context"] = {
        "supported_theme": "income_stability",
        "income_stability": income_stability,
        "guardrails": [
            "BACKEND_INFERENCE_FIRST",
            "WEALTH_DOMAIN_SIGNAL_NOT_PREDICTION",
            "LLM_EXPLAINS_EVIDENCE_ONLY",
        ],
    }
    data["algorithm_status"] = _algorithm_status()
    selected_question_key = str(payload.get("selected_question_key") or "").strip()
    data["rule_graph_runtime_context"] = build_rule_graph_runtime_context(
        data,
        message=str(payload.get("message") or ""),
        selected_question_key=selected_question_key,
    )
    data["knowledge_context"] = retrieve_knowledge(data, str(payload.get("message") or ""), settings=settings)
    data["guided_question_context"] = build_guided_question_context(data)
    data["guided_question_answer"] = build_guided_question_answer(data, selected_question_key, str(payload.get("message") or ""))
    deterministic_guided_answer = data["guided_question_answer"].get("available") is True
    prior_session = get_session(str(payload.get("session_id") or ""), settings=settings)
    prior_turns = list((prior_session or {}).get("turns") or [])
    llm = dict(settings.get("llm") or {})
    deterministic_income = _mentions_income_stability(str(payload.get("message") or ""))
    if deterministic_income:
        deterministic_text = render_income_stability_answer(income_stability)
        data["deterministic_outputs"] = {
            "income_stability": {
                "renderer": "v19.income_stability.deterministic_renderer.v1",
                "primary_user_output": True,
                "llm_may_override": False,
            }
        }
        data["agent_reply"] = {
            "role": "v19_deterministic_income_renderer",
            "content": deterministic_text.splitlines(),
            "guardrails": [
                "DETERMINISTIC_PRIMARY_OUTPUT",
                "LLM_NOT_USED_FOR_PRIMARY_INCOME_STABILITY",
                "WEALTH_DOMAIN_SIGNAL_NOT_PREDICTION",
                "NO_FORTUNE",
            ],
        }
    if deterministic_guided_answer:
        fallback_text = guided_answer_to_plain_text(data["guided_question_answer"], "zh")
        data["guided_question_answer"]["text"] = {"zh": fallback_text}
        data["guided_question_answer"]["content"] = {"zh": fallback_text.splitlines()}
        deterministic_outputs = dict(data.get("deterministic_outputs") or {})
        deterministic_outputs["guided_question_answer"] = {
            "renderer": "v19.guided_question_answer.text.v1",
            "primary_user_output": True,
            "llm_may_rephrase": True,
        }
        data["deterministic_outputs"] = deterministic_outputs
        data["agent_reply"] = {
            "role": "v19_guided_question_answer_renderer",
            "content": fallback_text.splitlines(),
            "guardrails": [
                "QUESTION_TO_ANSWER_WORKFLOW",
                "STRUCTURED_FACTS_PRIMARY",
                "NO_RESULT_MUTATION",
                "NO_FORTUNE",
            ],
        }
    elif data["knowledge_context"].get("items"):
        titles = ", ".join(str(item.get("title") or item.get("knowledge_id")) for item in data["knowledge_context"]["items"][:3])
        data["agent_reply"]["content"].append(f"Knowledge context applied: {titles}")
    assistant_text = "\n".join(data["agent_reply"]["content"])
    llm_status = {"enabled": bool(llm.get("enabled")), "used": False, "execute_llm": bool(llm.get("execute_llm", True))}

    if deterministic_guided_answer and llm.get("enabled") and llm.get("execute_llm", True):
        try:
            raw_llm_text = _call_llm_guarded(llm, _guided_answer_rewrite_messages(data["guided_question_answer"], str(payload.get("message") or "")))
            assistant_text = _guard_guided_answer_rewrite(raw_llm_text, fallback_text, data["guided_question_answer"])
            llm_rejected = assistant_text != raw_llm_text
            data["guided_question_answer"]["text"] = {"zh": assistant_text}
            data["guided_question_answer"]["content"] = {"zh": assistant_text.splitlines() or [assistant_text]}
            data["agent_reply"] = {
                "role": "v19_guided_question_answer_llm_rewriter" if not llm_rejected else "v19_guided_question_answer_composer_contract_fallback",
                "content": assistant_text.splitlines() or [assistant_text],
                "guardrails": [
                    "LLM_REPHRASES_STRUCTURED_FACTS_ONLY",
                    "NO_RESULT_MUTATION",
                    "NO_FORTUNE",
                ],
            }
            llm_status = {
                "enabled": True,
                "used": not llm_rejected,
                "execute_llm": True,
                "reason": "guided_answer_text_rewrite_only" if not llm_rejected else "guided_answer_llm_rewrite_rejected_contract_fallback",
                "provider": llm.get("provider"),
                "model": llm.get("model"),
                "base_url": resolve_llm_base_url(llm),
            }
        except Exception as exc:
            llm_status = {"enabled": True, "used": False, "execute_llm": True, "reason": "guided_answer_llm_failed_fallback_text_used", "error": str(exc)}
    elif deterministic_guided_answer and llm.get("enabled"):
        llm_status = {
            "enabled": True,
            "used": False,
            "execute_llm": False,
            "reason": "guided_answer_text_fallback_llm_disabled",
        }
    elif deterministic_income and llm.get("enabled"):
        llm_status = {
            "enabled": True,
            "used": False,
            "execute_llm": False,
            "reason": "deterministic_income_stability_renderer_is_primary",
        }
    elif llm.get("enabled") and llm.get("execute_llm", True):
        try:
            messages = build_agent_messages(data, str(payload.get("message") or ""), prior_turns)
            assistant_text = _call_llm_guarded(llm, messages)
            data["agent_reply"] = {
                "role": "v19_llm_agent",
                "content": assistant_text.splitlines() or [assistant_text],
                "guardrails": ["structure_context_only", "llm_enabled", "auditable_context"],
            }
            llm_status = {
                "enabled": True,
                "used": True,
                "execute_llm": True,
                "provider": llm.get("provider"),
                "model": llm.get("model"),
                "base_url": resolve_llm_base_url(llm),
            }
        except Exception as exc:
            llm_status = {"enabled": True, "used": False, "execute_llm": True, "error": str(exc)}

    turn = {
        "created_at": utc_now(),
        "user": {
            "birth_input": payload.get("birth_input"),
            "selected_year": payload.get("selected_year"),
            "message": str(payload.get("message") or ""),
        },
        "assistant": {
            "role": data["agent_reply"]["role"],
            "text": assistant_text,
            "structured": data,
            "llm_status": llm_status,
        },
    }
    session = create_or_append_session(payload, turn, settings=settings)
    data["session"] = {
        "session_id": session["session_id"],
        "role": session.get("role") or role,
        "user_id": session.get("user_id") or "",
        "turn_count": len(session.get("turns") or []),
        "storage": session.get("storage"),
    }
    data["history"] = [
        {
            "user": (item.get("user") or {}).get("message"),
            "assistant": (item.get("assistant") or {}).get("text"),
            "created_at": item.get("created_at"),
        }
        for item in (session.get("turns") or [])[-12:]
    ]
    data["llm_status"] = llm_status
    result["data"] = data
    return result


@app.post("/api/agent/structure")
def agent_structure_preview(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    role = _request_role(request, dict(payload or {}).get("role"))
    body = {**dict(payload or {}), "role": role, "message": str((payload or {}).get("message") or "structure_preview")}
    try:
        result = build_agent_turn(body)
    except Exception as exc:
        return {"ok": False, "code": "STRUCTURE_INPUT_INVALID", "message": str(exc)}
    if not result.get("ok"):
        return result
    data = dict(result.get("data") or {})
    income_stability = derive_income_stability(dict(data.get("chart") or {}))
    data["inference_context"] = {
        "supported_theme": "income_stability",
        "income_stability": income_stability,
        "runtime_scope": "structure_preview_question_routing_signal_only",
        "guardrails": [
            "QUESTION_ROUTING_SIGNAL_ONLY",
            "NO_RESULT_CARD_RENDER",
            "NO_LLM",
            "NO_FORTUNE",
        ],
    }
    data["rule_graph_runtime_context"] = build_rule_graph_runtime_context(data, message=str(body.get("message") or ""))
    data["guided_question_context"] = build_guided_question_context(data)
    return {
        "ok": True,
        "code": "OK",
        "data": {
            "birth_input": data.get("birth_input"),
            "chart": data.get("chart"),
            "time_context": data.get("time_context"),
            "luck_cycles": data.get("luck_cycles"),
            "inference_context": data.get("inference_context"),
            "rule_graph_runtime_context": data.get("rule_graph_runtime_context"),
            "guided_question_context": data.get("guided_question_context"),
            "guardrails": ["STRUCTURE_PREVIEW_ONLY", "QUESTION_ROUTING_SIGNAL_ONLY", "NO_RESULT_CARD_RENDER", "NO_LLM"],
        },
    }


@app.post("/api/lab/guided-question-audit")
def lab_guided_question_audit_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    settings = load_settings()
    body = dict(payload or {})
    profile_id = str(body.get("profile_id") or "").strip()
    if profile_id:
        profile = get_bazi_profile(profile_id, "")
        if not profile:
            return {"ok": False, "code": "PROFILE_NOT_FOUND", "message": "Bazi profile not found for audit."}
        birth_input = profile.get("birth_input") or {}
    else:
        birth_input = body.get("birth_input") or {}
    selected_year = body.get("selected_year")
    message = str(body.get("message") or "").strip()
    selected_question_key = str(body.get("selected_question_key") or "").strip()
    if not message and selected_question_key:
        message = selected_question_key
    base_payload = {
        "birth_input": birth_input,
        "selected_year": selected_year,
        "message": message,
        "selected_question_key": selected_question_key,
        "role": "practitioner",
    }
    result = build_agent_turn(base_payload)
    if not result.get("ok"):
        return result
    data = dict(result.get("data") or {})
    income_stability = derive_income_stability(dict(data.get("chart") or {}))
    data["inference_context"] = {
        "supported_theme": "income_stability",
        "income_stability": income_stability,
        "guardrails": ["AUDIT_INFERENCE_CONTEXT", "NO_RESULT_MUTATION", "NO_LLM"],
    }
    data["rule_graph_runtime_context"] = build_rule_graph_runtime_context(
        data,
        message=message,
        selected_question_key=selected_question_key,
    )
    data["knowledge_context"] = retrieve_knowledge(data, message, settings=settings)
    data["guided_question_context"] = build_guided_question_context(data)
    answer = build_guided_question_answer(data, selected_question_key, message)
    audit = _guided_question_audit_report(data, answer)
    audit_payload = {
        "profile_id": profile_id,
        "selected_year": selected_year,
        "selected_question_key": selected_question_key,
        "message": message,
        "question_contract": answer.get("question_contract"),
        "intent": answer.get("intent"),
        "retrieved_facts": answer.get("retrieved_facts"),
        "observed_facts": answer.get("observed_facts"),
        "composed_text": answer.get("composed_text"),
        "audit": audit,
        "guardrails": ["AUDIT_ONLY", "NO_SESSION_WRITE", "NO_LLM", "NO_RESULT_MUTATION"],
    }
    saved = record_guided_question_audit(audit_payload, settings) if body.get("save") is True else None
    return {"ok": True, "data": {**audit_payload, "saved_audit": saved}}


@app.get("/api/lab/guided-question-audits")
def lab_guided_question_audits_get(request: Request, status: str = "", question_key: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_guided_question_audits(load_settings(), status=status, question_key=question_key)


@app.get("/api/lab/guided-question-audits/report")
def lab_guided_question_audit_report_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return guided_question_audit_report(load_settings())


@app.get("/api/lab/guided-question-answer-quality")
def lab_guided_question_answer_quality_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return guided_question_answer_quality_report(load_settings())


@app.post("/api/lab/structural-rule-signals")
def lab_structural_rule_signals_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    body = dict(payload or {})
    profile_id = str(body.get("profile_id") or "").strip()
    if profile_id:
        profile = get_bazi_profile(profile_id, "")
        if not profile:
            return {"ok": False, "code": "PROFILE_NOT_FOUND", "message": "Bazi profile not found for structural-rule signal review."}
        birth_input = profile.get("birth_input") or {}
    else:
        birth_input = body.get("birth_input") or {}
    base_payload = {
        "birth_input": birth_input,
        "selected_year": body.get("selected_year"),
        "message": str(body.get("message") or "structural rule signal review"),
        "role": "practitioner",
    }
    result = build_agent_turn(base_payload)
    if not result.get("ok"):
        return result
    data = dict(result.get("data") or {})
    income_stability = derive_income_stability(dict(data.get("chart") or {}))
    report = build_structural_rule_signals(
        dict(data.get("chart") or {}),
        dict(data.get("time_context") or {}),
        {
            "supported_theme": "income_stability",
            "income_stability": income_stability,
            "guardrails": ["STRUCTURAL_SIGNAL_REVIEW_CONTEXT", "NO_RESULT_MUTATION"],
        },
    )
    return {
        "ok": True,
        "data": {
            "profile_id": profile_id,
            "selected_year": body.get("selected_year"),
            "structural_rule_signals": report,
            "guardrails": ["REVIEW_ONLY", "NO_RESULT_MUTATION", "NO_FORTUNE", "NO_RULE_ACTIVATION"],
        },
    }


@app.post("/api/lab/knowledge-rule-signal-coverage")
def lab_knowledge_rule_signal_coverage_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    body = dict(payload or {})
    profile_id = str(body.get("profile_id") or "").strip()
    if profile_id:
        profile = get_bazi_profile(profile_id, "")
        if not profile:
            return {"ok": False, "code": "PROFILE_NOT_FOUND", "message": "Bazi profile not found for knowledge/rule coverage review."}
        birth_input = profile.get("birth_input") or {}
    else:
        birth_input = body.get("birth_input") or {}
    base_payload = {
        "birth_input": birth_input,
        "selected_year": body.get("selected_year"),
        "message": str(body.get("message") or "knowledge rule signal coverage review"),
        "role": "practitioner",
    }
    result = build_agent_turn(base_payload)
    if not result.get("ok"):
        return result
    data = dict(result.get("data") or {})
    income_stability = derive_income_stability(dict(data.get("chart") or {}))
    report = knowledge_rule_signal_coverage(
        dict(data.get("chart") or {}),
        dict(data.get("time_context") or {}),
        {
            "supported_theme": "income_stability",
            "income_stability": income_stability,
            "guardrails": ["KNOWLEDGE_RULE_COVERAGE_REVIEW_CONTEXT", "NO_RESULT_MUTATION"],
        },
    )
    return {
        "ok": True,
        "data": {
            "profile_id": profile_id,
            "selected_year": body.get("selected_year"),
            "knowledge_rule_signal_coverage": report,
            "guardrails": ["REVIEW_ONLY", "NO_RESULT_MUTATION", "NO_FORTUNE", "NO_RULE_ACTIVATION"],
        },
    }


@app.get("/api/agent/sessions")
def agent_sessions(request: Request) -> Dict[str, Any]:
    return {"ok": True, "data": {"items": list_sessions(settings=load_settings())}}


@app.get("/api/agent/sessions/{session_id}")
def agent_session_get(session_id: str, request: Request) -> Dict[str, Any]:
    session = get_session(session_id, settings=load_settings())
    if not session:
        return {"ok": False, "code": "SESSION_NOT_FOUND", "message": "Session not found."}
    return {"ok": True, "data": session}


@app.get("/api/labels")
def public_labels_get(locale: str = "zh") -> Dict[str, Any]:
    return label_contract(locale, load_settings())


@app.post("/api/agent/feedback")
def agent_feedback_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    role = _request_role(request, dict(payload or {}).get("actor_role"))
    body = {**dict(payload or {}), "actor_role": role}
    return register_feedback(body, load_settings())


@app.get("/api/admin/settings")
def admin_settings_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    settings = load_settings()
    return {"ok": True, "data": public_settings(settings)}


@app.post("/api/admin/settings")
def admin_settings_save(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    settings = normalize_settings_payload(load_settings(), dict(payload or {}))
    save_settings(settings)
    return {"ok": True, "data": public_settings(settings)}


@app.post("/api/admin/db/test")
def admin_db_test(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    settings = normalize_settings_payload(load_settings(), {"db": dict((payload or {}).get("db") or {})})
    return test_db(settings)


@app.post("/api/admin/db/ensure-database")
def admin_db_ensure_database(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    settings = normalize_settings_payload(load_settings(), {"db": dict((payload or {}).get("db") or {})})
    return ensure_local_database(settings)


@app.post("/api/admin/llm/test")
def admin_llm_test(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    settings = normalize_settings_payload(load_settings(), {"llm": dict((payload or {}).get("llm") or {})})
    return probe_llm(settings)


@app.post("/api/admin/llm/models")
def admin_llm_models(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    settings = normalize_settings_payload(load_settings(), {"llm": dict((payload or {}).get("llm") or {})})
    return list_llm_models(settings)


@app.post("/api/admin/llm/chat-test")
def admin_llm_chat_test(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    body = dict(payload or {})
    settings = normalize_settings_payload(load_settings(), {"llm": dict(body.get("llm") or {})})
    return test_llm_chat(settings, prompt=str(body.get("prompt") or ""))


@app.get("/api/admin/knowledge/status")
def admin_knowledge_status(request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return knowledge_status(load_settings())


@app.get("/api/admin/knowledge/units")
def admin_knowledge_units(request: Request, domain: str = "", q: str = "") -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return list_knowledge_units(load_settings(), domain=domain, q=q)


@app.post("/api/admin/knowledge/seed")
def admin_knowledge_seed(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return seed_knowledge(load_settings(), force=bool((payload or {}).get("force")))


@app.post("/api/admin/knowledge/search")
def admin_knowledge_search(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    body = dict(payload or {})
    context = dict(body.get("context") or {})
    return retrieve_knowledge(context, str(body.get("q") or ""), settings=load_settings(), limit=int(body.get("limit") or 8))


@app.get("/api/admin/bazi-source-archive/status")
def admin_bazi_source_archive_status(request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return source_archive_status()


@app.get("/api/admin/bazi-source-archive/governance-overview")
def admin_bazi_source_archive_governance_overview(request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return source_governance_overview()


@app.get("/api/admin/bazi-source-archive/sources")
def admin_bazi_source_archive_sources(
    request: Request,
    source_type: str = "",
    risk_level: str = "",
    ingestion_status: str = "",
    q: str = "",
) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return list_source_records(source_type=source_type, risk_level=risk_level, ingestion_status=ingestion_status, q=q)


@app.post("/api/admin/bazi-source-archive/seed")
def admin_bazi_source_archive_seed(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return seed_source_archive(force=bool((payload or {}).get("force")))


@app.post("/api/admin/bazi-source-archive/sources")
def admin_bazi_source_archive_source_create(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return create_source_record(dict(payload or {}))


@app.post("/api/admin/bazi-source-archive/sources/{source_id}/status")
def admin_bazi_source_archive_source_status(source_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return update_source_record_status(source_id, dict(payload or {}))


@app.get("/api/admin/bazi-source-archive/excerpts")
def admin_bazi_source_archive_excerpts(
    request: Request,
    source_id: str = "",
    risk_level: str = "",
    status: str = "",
    q: str = "",
) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return list_excerpt_records(source_id=source_id, risk_level=risk_level, status=status, q=q)


@app.post("/api/admin/bazi-source-archive/excerpts")
def admin_bazi_source_archive_excerpt_create(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return create_excerpt_record(dict(payload or {}))


@app.get("/api/admin/bazi-source-archive/knowledge-drafts")
def admin_bazi_source_archive_knowledge_drafts(
    request: Request,
    domain: str = "",
    risk_level: str = "",
    q: str = "",
) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return list_knowledge_drafts(domain=domain, risk_level=risk_level, q=q)


@app.post("/api/admin/bazi-source-archive/knowledge-drafts")
def admin_bazi_source_archive_knowledge_draft_create(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return create_knowledge_draft(dict(payload or {}))


@app.post("/api/admin/bazi-source-archive/knowledge-drafts/seed-current")
def admin_bazi_source_archive_knowledge_draft_seed_current(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return seed_current_knowledge_drafts(force=bool((payload or {}).get("force")))


@app.post("/api/admin/bazi-source-archive/knowledge-drafts/{draft_id}/review")
def admin_bazi_source_archive_knowledge_draft_review(draft_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return update_knowledge_draft_review(draft_id, dict(payload or {}))


@app.post("/api/admin/bazi-source-archive/knowledge-drafts/{draft_id}/create-rule-proposal")
def admin_bazi_source_archive_knowledge_draft_create_rule_proposal(draft_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    prepared = build_rule_proposal_from_knowledge_draft(draft_id, dict(payload or {}))
    if not prepared.get("ok"):
        return prepared
    created = create_bazi_rule_proposal(dict(prepared.get("proposal_payload") or {}), load_settings())
    if not created.get("ok"):
        return created
    return {
        "ok": True,
        "item": created.get("item"),
        "source_draft": prepared.get("source_draft"),
        "storage": {"source_archive": prepared.get("storage"), "rule_ledger": created.get("storage")},
        "guardrails": ["FROM_KNOWLEDGE_DRAFT", "RULE_PROPOSAL_ONLY", "VALIDATION_REQUIRED", "NO_RUNTIME_INFERENCE_MUTATION"],
    }


@app.get("/api/admin/bazi-rule-db/status")
def admin_bazi_rule_db_status(request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return bazi_rule_db_status()


@app.get("/api/admin/bazi-rule-db/rules")
def admin_bazi_rule_db_rules(request: Request, domain: str = "", risk_level: str = "", q: str = "") -> Dict[str, Any]:
    _require_role(request, {"admin"})
    return list_bazi_rules(domain=domain, risk_level=risk_level, q=q)


@app.post("/api/admin/bazi-rule-db/ingest-current")
def admin_bazi_rule_db_ingest_current(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    body = dict(payload or {})
    return ingest_current_knowledge_drafts_to_rule_db(force=bool(body.get("force")), enable_engine=body.get("enable_engine") is not False)


@app.post("/api/admin/profiles/import-v17")
def admin_profiles_import_v17(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    body = dict(payload or {})
    owner_id = str(body.get("owner_id") or "admin").strip() or "admin"
    source = body.get("source_path") or None
    return import_v17_admin_bazi_profiles(source, owner_id=owner_id)


@app.post("/api/admin/guided-question/draft")
def admin_guided_question_draft(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"admin"})
    body = dict(payload or {})
    settings = load_settings()
    llm = dict(settings.get("llm") or {})
    draft = _guided_question_draft_fallback(body)
    llm_status = {"enabled": bool(llm.get("enabled")), "used": False}
    if llm.get("enabled") and llm.get("execute_llm", True):
        try:
            messages = _guided_question_draft_messages(body)
            raw = _call_llm_guarded(llm, messages)
            parsed = _parse_json_object(raw)
            if parsed:
                draft = _normalize_guided_question_draft(parsed, body)
                llm_status = {"enabled": True, "used": True, "model": llm.get("model"), "base_url": resolve_llm_base_url(llm)}
            else:
                llm_status = {"enabled": True, "used": False, "reason": "llm_returned_non_json"}
        except Exception as exc:
            llm_status = {"enabled": True, "used": False, "error": str(exc)}
    return {
        "ok": True,
        "draft": draft,
        "llm_status": llm_status,
        "guardrails": ["DRAFT_ONLY", "HUMAN_REVIEW_REQUIRED", "NO_RUNTIME_MUTATION", "NO_AUTO_PROPOSAL_CREATION"],
    }


@app.get("/api/lab/status")
def lab_status_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return lab_status(load_settings())


@app.post("/api/lab/feedback")
def lab_feedback_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return register_feedback(dict(payload or {}), load_settings())


@app.get("/api/lab/feedback")
def lab_feedback_get(request: Request, role: str = "", status: str = "", subject_type: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_feedback(load_settings(), role=role, status=status, subject_type=subject_type)


@app.get("/api/lab/guided-question-feedback")
def lab_guided_question_feedback_get(request: Request, question_key: str = "", status: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_guided_question_feedback(load_settings(), question_key=question_key, status=status)


@app.get("/api/lab/guided-question-feedback/summary")
def lab_guided_question_feedback_summary_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return guided_question_feedback_summary(load_settings())


@app.post("/api/lab/guided-question-feedback/{question_key}/review")
def lab_guided_question_feedback_review_post(question_key: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return update_guided_question_review(question_key, dict(payload or {}), load_settings())


@app.get("/api/lab/rule-impacts")
def lab_rule_impacts_get(request: Request, feedback_id: str = "", rule_id: str = "", signal: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_rule_impacts(load_settings(), feedback_id=feedback_id, rule_id=rule_id, signal=signal)


@app.post("/api/lab/validation/seed")
def lab_validation_seed(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return seed_validation_cases(load_settings(), force=bool((payload or {}).get("force")))


@app.get("/api/lab/validation/cases")
def lab_validation_cases_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_validation_cases(load_settings())


@app.post("/api/lab/validation/run")
def lab_validation_run_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return run_validation_cases(load_settings())


@app.get("/api/lab/validation/runs")
def lab_validation_runs_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_validation_runs(load_settings())


@app.get("/api/lab/synthetic-collision")
def lab_synthetic_collision_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    result = run_guided_synthetic_collision(P11_GUIDED_SYNTHETIC_CASES)
    return {
        "ok": True,
        "matrix": "P11_SYNTHETIC_EXPANSION",
        "case_count": len(P11_GUIDED_SYNTHETIC_CASES),
        "run": result,
    }


@app.post("/api/lab/synthetic-collision/run")
def lab_synthetic_collision_run_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    result = run_guided_synthetic_collision(P11_GUIDED_SYNTHETIC_CASES)
    return {
        "ok": True,
        "matrix": "P11_SYNTHETIC_EXPANSION",
        "case_count": len(P11_GUIDED_SYNTHETIC_CASES),
        "run": result,
    }


@app.get("/api/lab/framework-chain-audit")
def lab_framework_chain_audit_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P54_FRAMEWORK_CHAIN_AUDIT",
        "audit": run_p54_framework_chain_audit(),
    }


@app.post("/api/lab/silent-evolution/run")
def lab_silent_evolution_run_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P59_SILENT_EVOLUTION_SYSTEM",
        "cycle": run_p59_silent_evolution_cycle(),
    }


@app.get("/api/lab/domain-route-eval")
def lab_domain_route_eval_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P60_DOMAIN_ROUTE_EVAL",
        "eval": run_p60_domain_route_eval(),
    }


@app.post("/api/lab/smart-approval-gate/run")
def lab_smart_approval_gate_run_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P60_SMART_APPROVAL_GATE",
        "gate": run_p60_smart_approval_gate(),
    }


@app.post("/api/lab/silent-evolution-extension/run")
def lab_silent_evolution_extension_run_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P60_SILENT_EVOLUTION_EXTENSION",
        "extension": run_p60_silent_evolution_extension(),
    }


@app.get("/api/lab/domain-route-backfill")
def lab_domain_route_backfill_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P61_DOMAIN_ROUTE_BACKFILL",
        "registry": build_p61_domain_route_backfill_candidates(),
        "eval_dataset": build_p61_domain_route_backfill_eval_dataset(),
    }


@app.post("/api/lab/domain-route-backfill/run")
def lab_domain_route_backfill_run_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P61_DOMAIN_ROUTE_BACKFILL",
        "regression": run_p61_domain_route_backfill_regression(),
    }


@app.get("/api/lab/silent-training-ledger")
def lab_silent_training_ledger_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P62_SILENT_TRAINING_LEDGER",
        "ledger": build_p62_silent_training_ledger(),
    }


@app.post("/api/lab/silent-training-ledger/run")
def lab_silent_training_ledger_run_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P62_SILENT_TRAINING_LEDGER",
        "regression": run_p62_silent_training_ledger_regression(),
    }


@app.get("/api/lab/silent-eval-queue")
def lab_silent_eval_queue_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P63_SILENT_EVAL_QUEUE",
        "queue": build_p63_silent_eval_queue(),
    }


@app.post("/api/lab/silent-eval-queue/run")
def lab_silent_eval_queue_run_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P63_SILENT_EVAL_QUEUE",
        "regression": run_p63_silent_eval_queue_regression(),
    }


@app.get("/api/lab/interactive-calibration-design")
def lab_interactive_calibration_design_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P64_INTERACTIVE_CALIBRATION_DESIGN",
        "design": build_p64_interactive_calibration_design(),
    }


@app.post("/api/lab/interactive-calibration-design/run")
def lab_interactive_calibration_design_run_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P64_INTERACTIVE_CALIBRATION_DESIGN",
        "regression": run_p64_interactive_calibration_design_regression(),
    }


@app.get("/api/lab/mainline-completion-audit")
def lab_mainline_completion_audit_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P65_MAINLINE_COMPLETION_AUDIT",
        "audit": build_p65_mainline_completion_audit(),
    }


@app.post("/api/lab/mainline-completion-audit/run")
def lab_mainline_completion_audit_run_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return {
        "ok": True,
        "stage": "P65_MAINLINE_COMPLETION_AUDIT",
        "regression": run_p65_mainline_completion_regression(),
    }


@app.get("/api/lab/guided-question-diversity-audit")
def lab_guided_question_diversity_audit_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return guided_question_diversity_audit(load_settings())


@app.get("/api/lab/synthetic-promotions")
def lab_synthetic_promotions_get(request: Request, status: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_synthetic_promotion_candidates(load_settings(), status=status)


@app.post("/api/lab/synthetic-promotions")
def lab_synthetic_promotion_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_synthetic_promotion_candidate(dict(payload or {}), load_settings())


@app.post("/api/lab/synthetic-promotions/{candidate_id}/review")
def lab_synthetic_promotion_review_post(candidate_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return review_synthetic_promotion_candidate(candidate_id, dict(payload or {}), load_settings())


@app.get("/api/lab/governance-releases")
def lab_governance_releases_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_governance_releases(load_settings())


@app.post("/api/lab/governance-releases")
def lab_governance_release_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_governance_release(dict(payload or {}), load_settings())


@app.get("/api/lab/knowledge-review-batches")
def lab_knowledge_review_batches_get(request: Request, status: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_knowledge_review_batches(load_settings(), status=status)


@app.post("/api/lab/knowledge-review-batches")
def lab_knowledge_review_batch_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_knowledge_review_batch(dict(payload or {}), load_settings())


@app.post("/api/lab/knowledge-review-batches/seed-p14")
def lab_knowledge_review_batch_seed_p14_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return seed_p14_knowledge_review_batches(load_settings())


@app.post("/api/lab/knowledge-review-batches/seed-p21")
def lab_knowledge_review_batch_seed_p21_post(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return seed_p21_knowledge_review_batches(load_settings())


@app.get("/api/lab/knowledge-batch-proposal-runs")
def lab_knowledge_batch_proposal_runs_get(request: Request, status: str = "", batch_key: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_knowledge_batch_proposal_runs(load_settings(), status=status, batch_key=batch_key)


@app.post("/api/lab/knowledge-review-batches/{batch_id}/proposal-drafts")
def lab_knowledge_review_batch_proposal_drafts_post(batch_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_knowledge_batch_proposal_drafts(batch_id, dict(payload or {}), load_settings())


@app.post("/api/lab/p21/review-packet")
def lab_p21_review_packet_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_p21_knowledge_pack_review_packet(dict(payload or {}), load_settings())


@app.get("/api/lab/proposal-validation-runs")
def lab_proposal_validation_runs_get(request: Request, status: str = "", source_run_id: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_proposal_validation_runs(load_settings(), status=status, source_run_id=source_run_id)


@app.post("/api/lab/proposal-validation-runs")
def lab_proposal_validation_run_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_proposal_validation_run(dict(payload or {}), load_settings())


@app.get("/api/lab/proposal-review-packets")
def lab_proposal_review_packets_get(request: Request, status: str = "", validation_run_id: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_proposal_review_packets(load_settings(), status=status, validation_run_id=validation_run_id)


@app.post("/api/lab/proposal-review-packets")
def lab_proposal_review_packet_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_proposal_review_packet(dict(payload or {}), load_settings())


@app.post("/api/lab/proposal-review-packets/{packet_id}/decisions")
def lab_proposal_review_packet_decision_post(packet_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return record_proposal_review_packet_decision(packet_id, dict(payload or {}), load_settings())


@app.post("/api/lab/proposal-review-packets/{packet_id}/approval-preflight")
def lab_proposal_review_packet_approval_preflight_post(packet_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_proposal_review_approval_preflight(packet_id, dict(payload or {}), load_settings())


@app.post("/api/lab/proposal-review-packets/{packet_id}/controlled-approval")
def lab_proposal_review_packet_controlled_approval_post(packet_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return execute_proposal_review_packet_approval(packet_id, dict(payload or {}), load_settings())


@app.post("/api/lab/p26/knowledge-to-rules")
def lab_p26_knowledge_to_rules_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return execute_p26_knowledge_to_rules(dict(payload or {}), load_settings())


@app.post("/api/lab/p27/smart-rule-gate")
def lab_p27_smart_rule_gate_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return execute_p27_smart_rule_activation(dict(payload or {}), load_settings())


@app.post("/api/lab/promotions")
def lab_promotion_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_promotion_request(dict(payload or {}), load_settings())


@app.get("/api/lab/promotions")
def lab_promotions_get(request: Request, status: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_promotion_requests(load_settings(), status=status)


@app.post("/api/lab/promotions/{promotion_id}/status")
def lab_promotion_status_post(promotion_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return update_promotion_status(promotion_id, dict(payload or {}), load_settings())


@app.post("/api/lab/revisions")
def lab_revision_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_revision_proposal(dict(payload or {}), load_settings())


@app.post("/api/lab/guided-question-proposals")
def lab_guided_question_proposal_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_guided_question_proposal(dict(payload or {}), load_settings())


@app.get("/api/lab/guided-question-proposals")
def lab_guided_question_proposals_get(request: Request, status: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_guided_question_proposals(load_settings(), status=status)


@app.post("/api/lab/guided-question-proposals/{proposal_id}/validate")
def lab_guided_question_proposal_validate_post(proposal_id: str, request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return validate_guided_question_proposal(proposal_id, load_settings())


@app.post("/api/lab/guided-question-proposals/{proposal_id}/approve")
def lab_guided_question_proposal_approve_post(proposal_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return approve_guided_question_proposal(proposal_id, dict(payload or {}), load_settings())


@app.get("/api/lab/guided-question-library/versions")
def lab_guided_question_library_versions_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_guided_question_library_versions(load_settings())


@app.post("/api/lab/guided-question-library/versions")
def lab_guided_question_library_version_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return record_guided_question_library_version(dict(payload or {}), load_settings())


@app.post("/api/lab/bazi-rule-proposals")
def lab_bazi_rule_proposal_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return create_bazi_rule_proposal(dict(payload or {}), load_settings())


@app.get("/api/lab/bazi-rule-proposals")
def lab_bazi_rule_proposals_get(request: Request, status: str = "", domain: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_bazi_rule_proposals(load_settings(), status=status, domain=domain)


@app.post("/api/lab/bazi-rule-proposals/{proposal_id}/validate")
def lab_bazi_rule_proposal_validate_post(proposal_id: str, request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return validate_bazi_rule_proposal(proposal_id, load_settings())


@app.post("/api/lab/bazi-rule-proposals/{proposal_id}/approve")
def lab_bazi_rule_proposal_approve_post(proposal_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return approve_bazi_rule_proposal(proposal_id, dict(payload or {}), load_settings())


@app.get("/api/lab/bazi-rule-knowledge/versions")
def lab_bazi_rule_versions_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_bazi_rule_versions(load_settings())


@app.post("/api/lab/bazi-rule-knowledge/versions")
def lab_bazi_rule_version_post(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return record_bazi_rule_version(dict(payload or {}), load_settings())


@app.get("/api/lab/revisions")
def lab_revisions_get(request: Request, status: str = "", rule_id: str = "") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_revision_proposals(load_settings(), status=status, rule_id=rule_id)


@app.post("/api/lab/revisions/{revision_id}/validate")
def lab_revision_validate_post(revision_id: str, request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return validate_revision_proposal(revision_id, load_settings())


@app.post("/api/lab/revisions/{revision_id}/approve")
def lab_revision_approve_post(revision_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return approve_revision_proposal(revision_id, dict(payload or {}), load_settings())


@app.post("/api/lab/revisions/{revision_id}/activate")
def lab_revision_activate_post(revision_id: str, payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return activate_revision_record(revision_id, dict(payload or {}), load_settings())


@app.get("/api/lab/active-revisions")
def lab_active_revisions_get(request: Request) -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return list_active_rule_revisions(load_settings())


@app.get("/api/lab/labels")
def lab_labels_get(request: Request, locale: str = "zh") -> Dict[str, Any]:
    _require_role(request, {"practitioner", "admin"})
    return label_contract(locale, load_settings())


def _call_llm_guarded(llm: Dict[str, Any], messages: list[Dict[str, str]]) -> str:
    http_timeout = _float(llm.get("http_timeout_sec"), 15.0)
    fuse_timeout = _float(llm.get("fuse_wait_timeout_sec"), 20.0)
    timeout = max(5.0, min(max(fuse_timeout, http_timeout + 5.0), 120.0))
    future = LLM_EXECUTOR.submit(call_llm, llm, messages)
    try:
        return future.result(timeout=timeout)
    except FuturesTimeoutError as exc:
        future.cancel()
        raise TimeoutError(f"LLM fuse timeout after {timeout:g}s; returned structure + knowledge fallback.") from exc


def _guided_answer_rewrite_messages(answer: Dict[str, Any], user_message: str) -> list[Dict[str, str]]:
    compact = {
        "question_key": answer.get("question_key"),
        "question_text": answer.get("question_text"),
        "question_contract": answer.get("question_contract"),
        "intent": answer.get("intent"),
        "answer_kind": answer.get("answer_kind"),
        "summary": answer.get("summary"),
        "sections": answer.get("sections"),
        "retrieved_facts": answer.get("retrieved_facts"),
        "observed_facts": answer.get("observed_facts"),
        "evidence_pack": evidence_pack_to_prompt_context(dict(answer.get("evidence_pack") or {})),
        "knowledge_context": answer.get("knowledge_context"),
        "composed_text": answer.get("composed_text"),
        "result_relation": answer.get("result_relation"),
        "guardrails": answer.get("guardrails"),
    }
    return [
        {
            "role": "system",
            "content": (
                "你是 V19 八字结构回答的文字编辑器。只把给定结构事实改写成自然中文，不新增事实、不改结论、不做预测。"
                "不要使用表格、标题、项目符号、英文 key、规则名或审计口吻。"
                "用用户能听懂的话回答当前问题，控制在 2 到 4 个自然段。"
                "边界只作为写作约束，不要机械复述免责声明；除非用户明确询问边界，否则不要单独写“不是预测”或“不改变 income_stability”这类句子。"
                "优先使用 knowledge_context 中的结构解释知识来组织语言，尤其是月令、日主、藏干、十神、五行、墓库、地支关系和时间背景边界。"
                "回答必须像在解释用户刚问的问题：先回应问题意图，再说观察到的结构事实，再用一两句普通话说明它代表的结构意义。"
                "不要输出 rule_id、signal_id、internal key、debug 字段；如果问题超出支持范围，只说明当前支持结构阅读，并引导用户改问一个结构问题。"
                "如果 intent.supported=false，只能说明当前不支持这个问题，不能绕开限制作答。"
                "优先保持 composed_text 的意思，不能加入 retrieved_facts 或 observed_facts 之外的新事实。"
            ),
        },
        {"role": "user", "content": "用户问题：\n" + (user_message or "")},
        {"role": "user", "content": "只能使用这些结构事实组织回答：\n" + json.dumps(compact, ensure_ascii=False, sort_keys=True)},
    ]


def _looks_truncated_guided_answer(text: str) -> bool:
    clean = str(text or "").strip()
    if len(clean) < 24:
        return False
    if clean.count("“") != clean.count("”"):
        return True
    if clean.count("‘") != clean.count("’"):
        return True
    if clean.count("（") != clean.count("）"):
        return True
    if clean.count("(") != clean.count(")"):
        return True
    bad_tails = (
        "，",
        "、",
        "：",
        "；",
        ",",
        ":",
        ";",
        "的",
        "和",
        "与",
        "或",
        "而",
        "及",
        "以及",
        "因为",
        "所以",
        "但是",
        "并且",
        "同时",
        "其中",
        "例如",
        "比如",
        "包括",
        "位于",
        "出现于",
    )
    if clean.endswith(bad_tails):
        return True
    sentence_tails = "。！？.!?）】”’」』"
    if len(clean) >= 120 and clean[-1] not in sentence_tails:
        return True
    return False


def _guard_guided_answer_rewrite(text: str, fallback_text: str, answer: Dict[str, Any]) -> str:
    clean = str(text or "").strip()
    if not clean:
        return fallback_text
    if _looks_truncated_guided_answer(clean):
        return fallback_text
    intent = dict(answer.get("intent") or {})
    if intent.get("supported") is False and "不支持" not in clean and "不会硬编" not in clean:
        return fallback_text
    forbidden = ["一定", "必然", "发财", "破财", "今年会", "明年会", "好运", "坏运", "财运很好", "财运很差", "婚姻会", "健康会"]
    if any(term in clean for term in forbidden):
        return fallback_text
    return clean


def _guided_question_audit_report(data: Dict[str, Any], answer: Dict[str, Any]) -> Dict[str, Any]:
    contract = dict(answer.get("question_contract") or {})
    intent = dict(answer.get("intent") or {})
    retrieved = dict(answer.get("retrieved_facts") or {})
    observed = dict(answer.get("observed_facts") or {})
    text = str((answer.get("composed_text") or {}).get("zh") or "")
    checks = [
        _audit_check("question_contract_present", bool(contract), "Question contract is attached to the answer."),
        _audit_check("intent_present", bool(intent.get("intent_id")), "Intent router produced an intent_id."),
        _audit_check("support_scope_present", "supported" in intent, "Intent router explicitly marks supported/unsupported."),
        _audit_check("retrieved_facts_present", bool(retrieved), "Fact retriever returned a payload."),
        _audit_check("observed_facts_present", bool(observed), "Observed facts are attached for review."),
        _audit_check("answer_text_present", bool(text.strip()), "Answer composer produced Chinese text."),
        _audit_check("answer_not_truncated", not _looks_truncated_guided_answer(text), "Answer text does not look cut off."),
        _audit_check("no_internal_answer_markers", not any(marker in text for marker in ["answer_empty", "GUIDED_ANSWER", "DETERMINISTIC_RESULT_CARD", "rule_id", "signal_id", "question_basis", "source_signal_id"]), "Answer text hides internal/debug markers."),
        _audit_check("no_prediction_terms", not any(term in text for term in ["一定", "必然", "发财", "破财", "今年会", "明年会", "好运", "坏运", "财运很好", "财运很差", "婚姻会", "健康会"]), "Answer text avoids prediction wording."),
        _audit_check("contract_intent_matches_router", not contract or contract.get("intent") == intent.get("answer_kind"), "Question contract intent matches routed answer kind."),
        _audit_check("unsupported_does_not_retrieve_chart_facts", intent.get("supported") is not False or not retrieved.get("chart_anchor"), "Unsupported intents do not retrieve chart facts."),
        _audit_check("time_context_marked_context_only", _audit_time_context_marked(retrieved), "Time context is marked as context-only."),
        _audit_check("relations_have_layers", _audit_relations_have_layers(retrieved), "Retrieved branch relations include layer labels."),
        _audit_check("llm_not_used_in_audit", True, "Audit endpoint does not call LLM."),
    ]
    failed = [row for row in checks if not row["passed"]]
    return {
        "status": "pass" if not failed else "fail",
        "failed_count": len(failed),
        "checks": checks,
        "question_count": len(((data.get("guided_question_context") or {}).get("questions")) or []),
        "signal_count": len(((data.get("guided_question_context") or {}).get("signals")) or []),
        "contract_version": contract.get("registry_version") or "",
    }


def _audit_check(name: str, passed: bool, note: str) -> Dict[str, Any]:
    return {"name": name, "passed": bool(passed), "note": note}


def _audit_time_context_marked(retrieved: Dict[str, Any]) -> bool:
    time_context = dict(retrieved.get("time_context") or {})
    return not time_context or time_context.get("scope") == "time_context_only_no_income_stability_mutation"


def _audit_relations_have_layers(retrieved: Dict[str, Any]) -> bool:
    relations = retrieved.get("relations")
    if not relations:
        return True
    return all(isinstance(row, dict) and bool(row.get("layer")) for row in relations)


def _guided_question_draft_messages(payload: Dict[str, Any]) -> list[Dict[str, str]]:
    context = {
        "question_key": str(payload.get("question_key") or "").strip(),
        "feedback_summary": str(payload.get("feedback_summary") or "").strip()[:2000],
        "reviewer_note": str(payload.get("reviewer_note") or "").strip()[:2000],
        "allowed_actions": ["add", "edit", "deprecate", "reorder_path"],
        "allowed_depth": ["beginner", "intermediate"],
        "allowed_required_context": ["chart", "result", "time_relation"],
        "forbidden": ["fortune prediction", "future wealth", "good/bad fortune", "什么时候发财", "未来财运", "今年好坏"],
    }
    return [
        {
            "role": "system",
            "content": (
                "You draft governance proposal JSON for a Guided Bazi Agent question library. "
                "Return only valid JSON. Draft only, no approval, no validation, no runtime mutation. "
                "Do not write prediction or fortune questions. Keep labels structural and bounded."
            ),
        },
        {
            "role": "user",
            "content": (
                "Create a proposal draft with keys: proposed_action, proposed_question_key, proposed_label, "
                "proposed_metadata, rationale. proposed_label must include zh, en, ko. "
                "proposed_metadata must include depth, required_context, related_questions, forbidden_prediction=true.\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]


def _guided_question_draft_fallback(payload: Dict[str, Any]) -> Dict[str, Any]:
    question_key = str(payload.get("question_key") or "q_income_stability").strip() or "q_income_stability"
    note = str(payload.get("reviewer_note") or payload.get("feedback_summary") or "").strip()
    return {
        "proposed_action": "edit",
        "proposed_question_key": question_key,
        "proposed_label": {
            "zh": "请基于结构说明这个问题应如何被理解，而不是作为预测。",
            "en": "Explain how this question should be understood structurally, not as prediction.",
            "ko": "이 질문을 예측이 아니라 구조적으로 어떻게 이해해야 하는지 설명하세요.",
        },
        "proposed_metadata": {
            "depth": "beginner",
            "required_context": ["chart", "result"],
            "related_questions": ["q_read_result_not_fortune", "follow_rule_basis"],
            "forbidden_prediction": True,
        },
        "rationale": note or "Draft generated from guided question feedback. Human review, validation, and approval are required.",
    }


def _normalize_guided_question_draft(raw: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    fallback = _guided_question_draft_fallback(payload)
    draft = dict(fallback)
    action = str(raw.get("proposed_action") or fallback["proposed_action"]).strip()
    if action in {"add", "edit", "deprecate", "reorder_path"}:
        draft["proposed_action"] = action
    key = str(raw.get("proposed_question_key") or fallback["proposed_question_key"]).strip()
    draft["proposed_question_key"] = key or fallback["proposed_question_key"]
    if isinstance(raw.get("proposed_label"), dict):
        label = dict(fallback["proposed_label"])
        for locale in ["zh", "en", "ko"]:
            if str(raw["proposed_label"].get(locale) or "").strip():
                label[locale] = str(raw["proposed_label"][locale]).strip()
        draft["proposed_label"] = label
    if isinstance(raw.get("proposed_metadata"), dict):
        meta = dict(fallback["proposed_metadata"])
        incoming = dict(raw["proposed_metadata"])
        depth = str(incoming.get("depth") or meta["depth"]).strip()
        if depth in {"beginner", "intermediate"}:
            meta["depth"] = depth
        required = incoming.get("required_context") or incoming.get("required") or meta["required_context"]
        if isinstance(required, list):
            clean_required = [str(item).strip() for item in required if str(item).strip() in {"chart", "result", "time_relation"}]
            if clean_required:
                meta["required_context"] = clean_required
        related = incoming.get("related_questions") or meta["related_questions"]
        if isinstance(related, list):
            meta["related_questions"] = [str(item).strip() for item in related if str(item).strip()][:8]
        meta["forbidden_prediction"] = True
        draft["proposed_metadata"] = meta
    if str(raw.get("rationale") or "").strip():
        draft["rationale"] = str(raw["rationale"]).strip()
    return draft


def _parse_json_object(raw: str) -> Dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _mentions_income_stability(message: str) -> bool:
    text = str(message or "").lower()
    return (
        "income_stability" in text
        or "income stability" in text
        or "收入稳定" in text
        or "소득 안정" in text
        or "수입 안정" in text
    )


def _request_role(request: Request, fallback: Any = "") -> str:
    session = _request_auth_session(request)
    if session:
        return str(session.get("role") or "guest")
    referer_role = ""
    try:
        referer_role = parse_qs(urlsplit(str(request.headers.get("referer") or "")).query).get("role", [""])[0]
    except Exception:
        referer_role = ""
    dev_role = request.query_params.get("role") or request.headers.get("x-v19-role") or referer_role if ALLOW_ROLE_QUERY_FALLBACK else ""
    raw = str(dev_role or fallback or "guest").strip().lower()
    return raw if raw in VALID_ROLES else "guest"


def _require_role(request: Request, allowed: set[str]) -> str:
    role = _request_role(request)
    if role not in allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "ok": False,
                "code": "ROLE_FORBIDDEN",
                "role": role,
                "allowed": sorted(allowed),
                "message": "Role is not allowed for this V19 surface.",
            },
        )
    return role


def _request_auth_session(request: Request) -> Dict[str, Any] | None:
    return get_auth_session(request.cookies.get(AUTH_COOKIE, ""))


def _require_auth(request: Request) -> Dict[str, Any]:
    session = _request_auth_session(request)
    if not session:
        raise HTTPException(status_code=401, detail={"ok": False, "code": "AUTH_REQUIRED", "message": "Authentication required."})
    return session


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        AUTH_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=60 * 60 * 24 * 7,
    )


def _public_auth_session(session: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "role": session.get("role", "guest"),
        "user_id": session.get("user_id", ""),
        "username": session.get("username", ""),
    }


def _clean_auth_name(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    return text[:80] if text else fallback


def _income_stability_local_line(bundle: Dict[str, Any]) -> str:
    signals = {str(row.get("key")): str(row.get("value")) for row in bundle.get("signals", []) if isinstance(row, dict)}
    return (
        "Income Stability backend inference: "
        f"income_stability={signals.get('income_stability', 'unknown')}; "
        f"self_capacity={signals.get('self_capacity', 'unknown')}; "
        f"wealth_presence={signals.get('wealth_presence', 'unknown')}; "
        f"wealth_accessibility={signals.get('wealth_accessibility', 'unknown')}; "
        f"volatility={signals.get('volatility', 'unknown')}. "
        "Scope: wealth-domain structure signal, not fortune prediction."
    )


def _algorithm_status() -> Dict[str, Any]:
    return {
        "system_name": "V19 Standalone Agent Lab",
        "public_product_ready": False,
        "chart_structure": {
            "status": "prototype",
            "provenance": "v19.agent.structure.build_chart",
            "limitations": [
                "solar_term_boundaries_are_approximate",
                "lunar_input_converted_to_solar_before_structure",
                "timezone_and_birthplace_not_modeled",
                "day_pillar_requires_domain_verification",
            ],
        },
        "time_structure": {
            "status": "context_only",
            "provenance": "v19.agent.structure.build_luck_cycles/build_flow_year",
            "limitations": [
                "luck_cycle_start_age_is_approximate",
                "flow_year_does_not_modify_income_stability_in_P4",
            ],
        },
        "knowledge": {
            "status": "evidence_store",
            "not_rule_db": True,
            "provenance": "v19.knowledge_store reviewed evidence templates",
        },
        "income_stability": {
            "status": "deterministic_structure_signal",
            "provenance": "v19.agent.income_stability.derive_income_stability",
            "is_prediction": False,
        },
        "llm": {
            "status": "optional_explanation",
            "primary_for_income_stability": False,
        },
    }


def _float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")


@app.get("/favicon.ico")
def favicon() -> FileResponse:
    return FileResponse(FRONTEND / "assets" / "favicon.png")


@app.get("/entry")
def entry() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")


@app.get("/oracle")
def oracle() -> FileResponse:
    return FileResponse(FRONTEND / "oracle.html")


@app.get("/v19")
def v19_oracle() -> FileResponse:
    return FileResponse(FRONTEND / "oracle.html")


@app.get("/profiles")
def profiles_page() -> FileResponse:
    return FileResponse(FRONTEND / "profiles.html")


@app.get("/lab")
def lab(request: Request) -> FileResponse:
    _require_role(request, {"practitioner", "admin"})
    return FileResponse(FRONTEND / "lab.html")


@app.get("/admin")
def admin(request: Request) -> FileResponse:
    _require_role(request, {"admin"})
    return FileResponse(FRONTEND / "admin.html")


app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")
