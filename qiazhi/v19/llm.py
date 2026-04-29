from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from typing import Any, Dict, List

from v19.runtime import resolve_llm_base_url


def probe_llm(settings: Dict[str, Any]) -> Dict[str, Any]:
    llm = _llm_blob(settings)
    base_url = resolve_llm_base_url(llm)
    if not base_url:
        return {"ok": False, "status": "missing_base_url", "message": "LLM base_url or host is required."}
    errors: List[str] = []
    for probe_url in _probe_urls(base_url, llm):
        try:
            request = urllib.request.Request(probe_url, headers=_headers(llm, include_json=False), method="GET")
            with urllib.request.urlopen(request, timeout=_timeout(llm, 3.0)) as response:
                code = int(getattr(response, "status", 200))
            return {
                "ok": True,
                "status": "reachable",
                "message": f"LLM endpoint reachable via {probe_url} (HTTP {code}).",
                "probe_url": probe_url,
                "http_status": code,
                "base_url": base_url,
            }
        except Exception as exc:
            errors.append(f"{probe_url}: {exc}")
    return {"ok": False, "status": "unreachable", "message": " | ".join(errors[-2:]), "base_url": base_url}


def list_llm_models(settings: Dict[str, Any]) -> Dict[str, Any]:
    llm = _llm_blob(settings)
    base_url = resolve_llm_base_url(llm)
    if not base_url:
        return {"ok": False, "status": "missing_base_url", "message": "LLM base_url or host is required.", "models": []}
    errors: List[str] = []
    for models_url in _probe_urls(base_url, llm):
        try:
            request = urllib.request.Request(models_url, headers=_headers(llm, include_json=False), method="GET")
            with urllib.request.urlopen(request, timeout=_timeout(llm, 5.0)) as response:
                code = int(getattr(response, "status", 200))
                raw = json.loads(response.read().decode("utf-8"))
            models = _extract_model_names(raw)
            return {
                "ok": True,
                "status": "loaded",
                "message": f"Loaded {len(models)} model(s).",
                "models": models,
                "models_url": models_url,
                "http_status": code,
                "base_url": base_url,
            }
        except Exception as exc:
            errors.append(f"{models_url}: {exc}")
    return {"ok": False, "status": "load_failed", "message": " | ".join(errors[-2:]), "models": [], "base_url": base_url}


def test_llm_chat(settings: Dict[str, Any], prompt: str | None = None) -> Dict[str, Any]:
    llm = _llm_blob(settings)
    if not str(llm.get("model") or "").strip():
        return {"ok": False, "status": "missing_model", "message": "LLM model is required."}
    try:
        result = chat_llm(
            llm,
            [
                {"role": "system", "content": "Reply concisely. Do not mention fortune telling."},
                {"role": "user", "content": prompt or "请用一句话说明 V19 LLM 节点已连接。"},
            ],
            max_tokens=120,
        )
        return {
            "ok": True,
            "status": "chat_ok",
            "message": f"LLM chat test completed via {result.get('endpoint') or 'unknown endpoint'}.",
            "reply": str(result.get("reply") or ""),
            "endpoint": result.get("endpoint"),
            "http_status": result.get("http_status"),
        }
    except Exception as exc:
        return {"ok": False, "status": "chat_failed", "message": str(exc), "reply": ""}


def build_agent_messages(structure_payload: Dict[str, Any], user_message: str, prior_turns: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    compact = {
        "chart": structure_payload.get("chart"),
        "time_context": structure_payload.get("time_context"),
        "inference_context": structure_payload.get("inference_context"),
        "knowledge_context": structure_payload.get("knowledge_context"),
        "guardrails": ["structure context only", "no unsupported facts", "state uncertainty", "keep audit trail"],
    }
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are V19 Bazi Structure Agent. Use only the supplied structured chart, luck cycle, and flow year context. "
                "Use retrieved_knowledge only as evidence-template context, not as direct prediction. "
                "For income_stability, use only inference_context.income_stability signals and evidence_summary; do not replace it with generic ten-god explanation. "
                "Do not invent missing facts. Do not claim certainty. Keep answers concise and auditable. "
                "If asked for prediction, separate structure from inference and name unsupported areas."
            ),
        },
        {"role": "user", "content": "STRUCTURE_CONTEXT_JSON:\n" + json.dumps(compact, ensure_ascii=False, sort_keys=True)},
    ]
    for turn in prior_turns[-6:]:
        user = str((turn.get("user") or {}).get("message") or "").strip()
        assistant = str((turn.get("assistant") or {}).get("text") or "").strip()
        if user:
            messages.append({"role": "user", "content": user})
        if assistant:
            messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": user_message or "请基于结构上下文继续。"})
    return messages


def call_llm(llm: Dict[str, Any], messages: List[Dict[str, str]], max_tokens: int | None = None) -> str:
    return str(chat_llm(llm, messages, max_tokens=max_tokens).get("reply") or "").strip()


def chat_llm(llm: Dict[str, Any], messages: List[Dict[str, str]], max_tokens: int | None = None) -> Dict[str, Any]:
    base_url = resolve_llm_base_url(llm)
    model = str(llm.get("model") or "").strip()
    if not base_url or not model:
        raise ValueError("LLM base_url and model are required.")

    openai_error = ""
    openai_reasoning = ""
    try:
        result = _chat_openai_compatible(llm, messages, max_tokens=max_tokens)
        if str(result.get("reply") or "").strip():
            return result
        openai_reasoning = str(result.get("reasoning") or "").strip()
    except Exception as exc:
        openai_error = str(exc)

    provider = str(llm.get("provider") or "").strip().lower()
    if "ollama" in provider or openai_error or openai_reasoning:
        try:
            result = _chat_ollama_native(llm, messages, max_tokens=max_tokens)
            if str(result.get("reply") or "").strip():
                return result
            if openai_reasoning:
                result["reply"] = openai_reasoning
                return result
        except Exception as exc:
            if openai_error:
                raise RuntimeError(f"OpenAI-compatible failed: {openai_error}; Ollama native failed: {exc}") from exc
            raise

    if openai_error:
        raise RuntimeError(openai_error)
    raise RuntimeError("LLM returned an empty response.")


def _chat_openai_compatible(llm: Dict[str, Any], messages: List[Dict[str, str]], max_tokens: int | None = None) -> Dict[str, Any]:
    base_url = resolve_llm_base_url(llm)
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": str(llm.get("model") or "").strip(),
        "messages": messages,
        "temperature": float(llm.get("temperature") or 0.2),
        "max_tokens": int(max_tokens or llm.get("max_tokens") or 800),
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, headers=_headers(llm), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=_timeout(llm, 30.0)) as response:
            status = int(getattr(response, "status", 200))
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail[:500]}") from exc

    choices = data.get("choices") if isinstance(data, dict) else None
    if not choices:
        raise RuntimeError("LLM response has no choices.")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else ""
    reasoning = ""
    if isinstance(message, dict):
        reasoning = str(message.get("reasoning") or message.get("thinking") or "").strip()
    return {"reply": str(content or "").strip(), "reasoning": reasoning, "endpoint": endpoint, "http_status": status}


def _chat_ollama_native(llm: Dict[str, Any], messages: List[Dict[str, str]], max_tokens: int | None = None) -> Dict[str, Any]:
    base_url = resolve_llm_base_url(llm)
    endpoint = base_url.rstrip("/").removesuffix("/v1") + "/api/chat"
    payload = {
        "model": str(llm.get("model") or "").strip(),
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": float(llm.get("temperature") or 0.2),
            "num_predict": int(max_tokens or llm.get("max_tokens") or 800),
        },
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, headers=_headers(llm), method="POST")
    with urllib.request.urlopen(request, timeout=_timeout(llm, 30.0)) as response:
        status = int(getattr(response, "status", 200))
        data = json.loads(response.read().decode("utf-8"))

    content = ""
    if isinstance(data, dict):
        message = data.get("message") if isinstance(data.get("message"), dict) else {}
        content = str(message.get("content") or "").strip()
        if not content:
            content = str(message.get("thinking") or "").strip()
        if not content:
            content = str(data.get("response") or "").strip()
    return {"reply": content, "endpoint": endpoint, "http_status": status}


def _llm_blob(settings: Dict[str, Any]) -> Dict[str, Any]:
    if "llm" in settings and isinstance(settings.get("llm"), dict):
        return dict(settings.get("llm") or {})
    return dict(settings or {})


def _probe_urls(base_url: str, llm: Dict[str, Any]) -> List[str]:
    root = base_url.rstrip("/")
    native_root = root.removesuffix("/v1")
    urls = [root + "/models", native_root + "/api/tags"]
    provider = str(llm.get("provider") or "").strip().lower()
    if "ollama" in provider:
        urls.reverse()
    return urls


def _extract_model_names(raw: Any) -> List[str]:
    names: List[str] = []
    if isinstance(raw, dict):
        rows = raw.get("data")
        if isinstance(rows, list):
            for item in rows:
                if isinstance(item, dict) and str(item.get("id") or "").strip():
                    names.append(str(item.get("id")).strip())
        rows = raw.get("models")
        if isinstance(rows, list):
            for item in rows:
                if isinstance(item, dict) and str(item.get("name") or "").strip():
                    names.append(str(item.get("name")).strip())
                elif isinstance(item, str) and item.strip():
                    names.append(item.strip())
    return sorted(dict.fromkeys(names))


def _headers(llm: Dict[str, Any], include_json: bool = True) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if include_json:
        headers["Content-Type"] = "application/json"
    api_key = str(llm.get("api_key") or "").strip()
    username = str(llm.get("username") or "").strip()
    password = str(llm.get("password") or "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif username or password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"
    return headers


def _timeout(llm: Dict[str, Any], fallback: float) -> float:
    try:
        value = float(llm.get("http_timeout_sec") or fallback)
    except (TypeError, ValueError):
        value = fallback
    try:
        fuse = float(llm.get("fuse_wait_timeout_sec") or 0)
    except (TypeError, ValueError):
        fuse = 0
    if fuse > value:
        value = fuse
    return max(1.0, min(600.0, value))
