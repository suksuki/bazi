from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict
from urllib import request
from urllib.parse import urlparse

from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import (
    normalize_wealth_profile_meta,
    resolve_wealth_profile,
)
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import (
    normalize_wealth_code_meta,
    resolve_wealth_code,
)
from v17_rebirth.backend.services.llm_prompt_contracts import (
    WEALTH_ASSERTION_PROMPT_VERSION,
    build_wealth_assertion_prompt_bundle,
    build_wealth_assertion_prompt_text,
)
from v17_rebirth.infrastructure.llm_bridge import get_runtime_llm_config

WEALTH_ASSERTION_PREVIEW_PROTOCOL = "v17.topic.wealth_assertion_preview.v1"

LlmChatCallable = Callable[..., Dict[str, Any]]


def _normalize_output_language(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"en", "ko"}:
        return raw
    return "zh"


def _endpoint_host(base_url: str) -> str:
    try:
        parsed = urlparse(str(base_url or "").strip())
        return str(parsed.hostname or "").strip()
    except Exception:
        return ""


def _profile_from_inputs(
    *,
    wealth_profile: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
) -> tuple[Dict[str, Any], str]:
    if isinstance(wealth_profile, dict) and wealth_profile:
        return normalize_wealth_profile_meta(wealth_profile), "payload.wealth_profile"
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    if isinstance(meta.get("wealth_profile"), dict) and meta.get("wealth_profile"):
        return normalize_wealth_profile_meta(meta.get("wealth_profile")), "physics.meta.wealth_profile"
    if pt:
        resolved = resolve_wealth_profile(pt).get("wealth_profile")
        return normalize_wealth_profile_meta(resolved), "computed.from_server_physics"
    return {}, "missing"


def _code_from_inputs(
    *,
    wealth_code: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
) -> tuple[Dict[str, Any], str]:
    if isinstance(wealth_code, dict) and wealth_code:
        return normalize_wealth_code_meta(wealth_code), "payload.wealth_code"
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    if isinstance(meta.get("wealth_code"), dict) and meta.get("wealth_code"):
        return normalize_wealth_code_meta(meta.get("wealth_code")), "physics.meta.wealth_code"
    if pt:
        resolved = resolve_wealth_code(pt).get("wealth_code")
        return normalize_wealth_code_meta(resolved), "computed.from_server_physics"
    return {}, "missing"


def _system_prompt(lang: str) -> str:
    if lang == "en":
        return (
            "You are the V17 backstage wealth reading writer. "
            "Use only the supplied wealth_code/wealth_profile prompt contract. "
            "Do not request, infer, or reinterpret raw BaZi chart data."
        )
    if lang == "ko":
        return (
            "당신은 V17 백스테이지 재물 해석 작성자입니다. "
            "제공된 wealth_code/wealth_profile 프롬프트 계약만 사용하십시오. "
            "원국 자료를 요청하거나 재해석하지 마십시오."
        )
    return (
        "你是 V17 后台财富解读预览器。"
        "只能使用输入的 wealth_code/wealth_profile prompt contract。"
        "不得请求、推断或重新解释原始八字。"
    )


def _max_tokens(lang: str) -> int:
    return 520 if lang == "zh" else 760


def _raw_chat_llm(
    *,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
    timeout_sec: float,
) -> Dict[str, Any]:
    endpoint = str(base_url or "").rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
        "thinking": False,
        "reasoning_effort": "none",
    }
    started = time.perf_counter()
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = request.Request(endpoint, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    with request.urlopen(req, timeout=timeout_sec) as resp:
        code = int(getattr(resp, "status", 200))
        raw_text = resp.read().decode("utf-8")
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    reply = ""
    try:
        raw = json.loads(raw_text)
        if isinstance(raw, dict):
            choice = (raw.get("choices") or [{}])[0]
            msg = (
                choice.get("message")
                if isinstance(choice, dict) and isinstance(choice.get("message"), dict)
                else {}
            )
            reply = str(msg.get("content") or msg.get("reasoning") or msg.get("thinking") or "").strip()
    except Exception:
        raw = raw_text
    return {
        "ok": bool(reply),
        "http_status": code,
        "endpoint": endpoint,
        "elapsed_ms": elapsed_ms,
        "reply": reply,
        "raw_response_json": raw if isinstance(raw, dict) else str(raw)[:12000],
    }


def _timeout_from_config(cfg: Dict[str, Any]) -> float:
    try:
        raw = str(cfg.get("http_timeout_sec") or "").strip() or 20.0
        return max(1.0, min(120.0, float(raw)))
    except (TypeError, ValueError):
        return 20.0


def build_wealth_assertion_preview(
    *,
    wealth_code: Dict[str, Any] | None = None,
    wealth_profile: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
    output_language: Any = "zh",
    execute_llm: bool = True,
    llm_chat: LlmChatCallable | None = None,
) -> Dict[str, Any]:
    lang = _normalize_output_language(output_language)
    code, code_source = _code_from_inputs(
        wealth_code=wealth_code,
        physics_tensor=physics_tensor,
    )
    profile, profile_source = _profile_from_inputs(
        wealth_profile=wealth_profile,
        physics_tensor=physics_tensor,
    )
    prompt_bundle = build_wealth_assertion_prompt_bundle(wealth_code=code, wealth_profile=profile, output_language=lang)
    prompt_text = build_wealth_assertion_prompt_text(wealth_code=code, wealth_profile=profile, output_language=lang)
    messages = [
        {"role": "system", "content": _system_prompt(lang)},
        {"role": "user", "content": prompt_text},
    ]
    cfg = get_runtime_llm_config()
    base_url = str(cfg.get("base_url") or "").strip()
    model = str(cfg.get("model") or "").strip()
    llm_ready = bool(base_url and model)
    max_tokens = _max_tokens(lang)
    preview: Dict[str, Any] = {
        "protocol": WEALTH_ASSERTION_PREVIEW_PROTOCOL,
        "policy_version": WEALTH_ASSERTION_PROMPT_VERSION,
        "mode": "backstage_preview",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_language": lang,
        "code_source": code_source,
        "code_present": bool(code),
        "profile_source": profile_source,
        "profile_present": bool(profile),
        "material_present": bool(code or profile),
        "safety": {
            "llm_input_scope": "wealth_code_first_profile_fallback",
            "raw_chart_access": False,
            "physics_mutation": False,
            "parameter_mutation": False,
            "body_use_mutation": False,
        },
        "wealth_code": code,
        "wealth_profile": profile,
        "prompt_contract": prompt_bundle,
        "prompt_text": prompt_text,
        "llm_request": {
            "provider": str(cfg.get("provider") or "").strip(),
            "model": model,
            "llm_endpoint_host": _endpoint_host(base_url),
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "execute_llm": bool(execute_llm),
        },
        "llm_result": {
            "ok": False,
            "skipped": True,
            "reason": "execute_llm_disabled" if not execute_llm else "not_dispatched",
            "reply": "",
        },
    }
    if not code and not profile:
        preview["llm_result"] = {
            "ok": False,
            "skipped": True,
            "reason": "missing_wealth_material",
            "reply": "",
        }
        return preview
    if not execute_llm:
        return preview
    if not llm_ready:
        preview["llm_result"] = {
            "ok": False,
            "skipped": True,
            "reason": "llm_config_incomplete",
            "reply": "",
        }
        return preview
    chat = llm_chat or _raw_chat_llm
    try:
        result = chat(
            base_url=base_url,
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2,
            timeout_sec=_timeout_from_config(cfg),
        )
        preview["llm_result"] = {
            "ok": bool(result.get("ok")),
            "skipped": False,
            "http_status": result.get("http_status"),
            "endpoint_host": _endpoint_host(str(result.get("endpoint") or base_url)),
            "elapsed_ms": int(result.get("elapsed_ms") or 0),
            "reply": str(result.get("reply") or "").strip(),
            "raw_response_json": result.get("raw_response_json", {}),
        }
    except Exception as exc:
        preview["llm_result"] = {
            "ok": False,
            "skipped": False,
            "reason": "llm_dispatch_failed",
            "error": f"{type(exc).__name__}: {exc}",
            "reply": "",
        }
    return preview


def attach_wealth_assertion_preview_meta(meta: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(meta or {})
    out["wealth_assertion_preview"] = dict(preview or {})
    audits = out.get("topic_assertion_audits") if isinstance(out.get("topic_assertion_audits"), list) else []
    compact = {
        "protocol": WEALTH_ASSERTION_PREVIEW_PROTOCOL,
        "policy_version": WEALTH_ASSERTION_PROMPT_VERSION,
        "created_at": str(preview.get("created_at") or ""),
        "topic": "wealth",
        "code_present": bool(preview.get("code_present")),
        "code_source": str(preview.get("code_source") or ""),
        "profile_present": bool(preview.get("profile_present")),
        "profile_source": str(preview.get("profile_source") or ""),
        "llm_ok": bool((preview.get("llm_result") or {}).get("ok"))
        if isinstance(preview.get("llm_result"), dict)
        else False,
        "llm_skipped": bool((preview.get("llm_result") or {}).get("skipped"))
        if isinstance(preview.get("llm_result"), dict)
        else False,
    }
    out["topic_assertion_audits"] = [compact, *audits[:9]]
    return out


def summarize_wealth_assertion_preview(
    preview: Dict[str, Any],
    *,
    include_prompt: bool = False,
    include_reply: bool = True,
) -> Dict[str, Any]:
    if not isinstance(preview, dict) or not preview:
        return {
            "protocol": WEALTH_ASSERTION_PREVIEW_PROTOCOL,
            "preview_present": False,
        }
    profile = preview.get("wealth_profile") if isinstance(preview.get("wealth_profile"), dict) else {}
    code = preview.get("wealth_code") if isinstance(preview.get("wealth_code"), dict) else {}
    channels = profile.get("primary_channels") if isinstance(profile.get("primary_channels"), list) else []
    top_channel = channels[0] if channels and isinstance(channels[0], dict) else {}
    llm_request = preview.get("llm_request") if isinstance(preview.get("llm_request"), dict) else {}
    llm_result = preview.get("llm_result") if isinstance(preview.get("llm_result"), dict) else {}
    summary: Dict[str, Any] = {
        "protocol": str(preview.get("protocol") or WEALTH_ASSERTION_PREVIEW_PROTOCOL),
        "policy_version": str(preview.get("policy_version") or WEALTH_ASSERTION_PROMPT_VERSION),
        "preview_present": True,
        "mode": str(preview.get("mode") or "backstage_preview"),
        "created_at": str(preview.get("created_at") or ""),
        "output_language": str(preview.get("output_language") or "zh"),
        "code_source": str(preview.get("code_source") or ""),
        "code_present": bool(preview.get("code_present")),
        "profile_source": str(preview.get("profile_source") or ""),
        "profile_present": bool(preview.get("profile_present")),
        "material_present": bool(preview.get("material_present")),
        "safety": preview.get("safety") if isinstance(preview.get("safety"), dict) else {},
        "wealth_code_summary": {
            "score": code.get("score"),
            "confidence": code.get("confidence"),
            "risk": code.get("risk"),
            "primary_wealth_path": code.get("primary_wealth_path") if isinstance(code.get("primary_wealth_path"), dict) else {},
            "wealth_source": code.get("wealth_source") if isinstance(code.get("wealth_source"), dict) else {},
            "monetization_engine": code.get("monetization_engine") if isinstance(code.get("monetization_engine"), dict) else {},
            "carrier": code.get("carrier") if isinstance(code.get("carrier"), dict) else {},
            "wealth_vault": code.get("wealth_vault") if isinstance(code.get("wealth_vault"), dict) else {},
            "leakage_points": code.get("leakage_points") if isinstance(code.get("leakage_points"), list) else [],
            "flow_year_watchlist": code.get("flow_year_watchlist") if isinstance(code.get("flow_year_watchlist"), list) else [],
        },
        "wealth_profile_summary": {
            "score": profile.get("score"),
            "confidence": profile.get("confidence"),
            "risk": profile.get("risk"),
            "stance": str(profile.get("stance") or ""),
            "visibility": str(profile.get("visibility") or ""),
            "usable_state": str(profile.get("usable_state") or ""),
            "top_channel": top_channel,
        },
        "llm_request_summary": {
            "provider": str(llm_request.get("provider") or ""),
            "model": str(llm_request.get("model") or ""),
            "llm_endpoint_host": str(llm_request.get("llm_endpoint_host") or ""),
            "max_tokens": llm_request.get("max_tokens"),
            "temperature": llm_request.get("temperature"),
            "execute_llm": bool(llm_request.get("execute_llm")),
        },
        "llm_result_summary": {
            "ok": bool(llm_result.get("ok")),
            "skipped": bool(llm_result.get("skipped")),
            "reason": str(llm_result.get("reason") or ""),
            "error": str(llm_result.get("error") or ""),
            "http_status": llm_result.get("http_status"),
            "endpoint_host": str(llm_result.get("endpoint_host") or ""),
            "elapsed_ms": int(llm_result.get("elapsed_ms") or 0),
        },
    }
    if include_reply:
        summary["llm_result_summary"]["reply"] = str(llm_result.get("reply") or "")
    else:
        summary["llm_result_summary"]["reply_preview"] = str(llm_result.get("reply") or "")[:180]
    if include_prompt:
        summary["prompt_text"] = str(preview.get("prompt_text") or "")
        prompt_contract = preview.get("prompt_contract")
        if isinstance(prompt_contract, dict):
            summary["prompt_contract"] = prompt_contract
    return summary
