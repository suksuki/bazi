from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional, Tuple
from urllib import request
from urllib.parse import urlparse

from .llm_bridge import V17_ROLE_JUDGE, V17_ROLE_WEAVER, V17_ROLES, V17LlmBridge
from v17_rebirth.backend.narrative.semantic_fusion import build_role_user_prompt


def _normalize_fuse_role(role: str) -> str:
    r = str(role or "").strip().upper() or V17_ROLE_WEAVER
    return V17_ROLE_JUDGE if r == V17_ROLE_JUDGE else V17_ROLE_WEAVER


def _fuse_role_extras(role: str) -> Dict[str, Any]:
    rid = _normalize_fuse_role(role)
    return {"role_style": rid, "v17_role_label": V17_ROLES.get(rid, rid)}


@dataclass(frozen=True)
class LlmStreamStep:
    """编排器与 partial 文本共用一队列时的步进标记（已派发 / 已联通 / 正文）。"""

    kind: str
    data: Any


class AsyncEventEmitter:
    """异步订阅：在 POST 前、首字到达等节点广播，供编排层转为 NDJSON 帧。"""

    def __init__(self) -> None:
        self._subs: Dict[str, List[Callable[[Any], Awaitable[None]]]] = {}

    def on(self, event: str, handler: Callable[[Any], Awaitable[None]]) -> None:
        self._subs.setdefault(str(event), []).append(handler)

    async def emit(self, event: str, payload: Any) -> None:
        key = str(event)
        for fn in list(self._subs.get(key, [])):
            await fn(payload)


_FUSE_OUTBOUND_SEM: Optional[asyncio.BoundedSemaphore] = None
_FUSE_SEM_CAP: int = 0


def _fuse_max_parallel() -> int:
    """批处理闸门：全局向 LLM 的并发上限（默认 3，禁止数十路洪泛）。可用 QIAZHI_V17_FUSE_MAX_PARALLEL 覆盖。"""
    try:
        v = int(str(os.getenv("QIAZHI_V17_FUSE_MAX_PARALLEL", "3") or "3").strip())
        return max(1, min(12, v))
    except (TypeError, ValueError):
        return 3


def _fuse_outbound_sem() -> asyncio.BoundedSemaphore:
    """全局 BoundedSemaphore；容量变更时重建，保证「出一组、占一组、释一组」。"""
    global _FUSE_OUTBOUND_SEM, _FUSE_SEM_CAP
    cap = _fuse_max_parallel()
    if _FUSE_OUTBOUND_SEM is None or _FUSE_SEM_CAP != cap:
        _FUSE_OUTBOUND_SEM = asyncio.BoundedSemaphore(cap)
        _FUSE_SEM_CAP = cap
    return _FUSE_OUTBOUND_SEM


async def _mirror_legacy_emitter(ev: Dict[str, Any], llm_emitter: Optional[AsyncEventEmitter]) -> None:
    """兼容旧 AsyncEventEmitter：仅映射 dispatched；首字改由 streaming/connected 语义覆盖。"""
    if llm_emitter is None:
        return
    if ev.get("status") == "dispatched":
        await llm_emitter.emit("dispatched", ev.get("payload") or {})


async def _emit_fuse_step_legacy(
    step_ev: Dict[str, Any],
    *,
    status_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]],
    llm_emitter: Optional[AsyncEventEmitter],
    on_llm_partial: Optional[Callable[[str], Awaitable[None]]],
    stream_buf: Dict[str, str],
) -> None:
    """将 V17.19 步进帧同步为旧 status_callback / partial 语义（编排层零改）。"""
    st = step_ev.get("step")
    if st == "dispatching":
        data = step_ev.get("data") if isinstance(step_ev.get("data"), dict) else {}
        ev: Dict[str, Any] = {"status": "dispatched", "payload": data}
        if status_callback is not None:
            await status_callback(ev)
        await _mirror_legacy_emitter(ev, llm_emitter)
    elif st == "handshake":
        lat = int(step_ev.get("latency") or 0)
        ev = {"status": "connected", "latency": lat}
        if status_callback is not None:
            await status_callback(ev)
    elif st == "weaving":
        delta = str(step_ev.get("token") or "")
        if not delta:
            return
        stream_buf["acc"] += delta
        acc = stream_buf["acc"]
        ev = {"status": "streaming", "chunk": acc}
        if status_callback is not None:
            await status_callback(ev)
        if on_llm_partial is not None:
            await on_llm_partial(acc)
    elif st == "complete":
        if status_callback is not None:
            await status_callback({"status": "complete", "result": step_ev.get("result")})
    elif st == "error":
        if status_callback is not None:
            await status_callback({"status": "error", "result": step_ev.get("result")})


try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[misc, assignment]


def _fuse_hard_sec() -> float:
    """V17.16：整段 fuse（含 HTTP/SSE）硬熔断上限，默认 10.0s；可用 QIAZHI_V17_FUSE_HARD_SEC 覆盖。"""
    try:
        v = float(str(os.getenv("QIAZHI_V17_FUSE_HARD_SEC", "10.0") or "10.0").strip())
        return max(0.5, min(120.0, v))
    except (TypeError, ValueError):
        return 10.0


def _fuse_ttft_sec() -> float:
    """V17.17：首字（首 token）预算，默认 20.0s；可用 QIAZHI_V17_LLM_TTFT_SEC 覆盖。"""
    try:
        v = float(str(os.getenv("QIAZHI_V17_LLM_TTFT_SEC", "20.0") or "20.0").strip())
        return max(1.0, min(120.0, v))
    except (TypeError, ValueError):
        return 20.0


def _sse_line_idle_sec() -> float:
    """行间读 SSE 最大等待；默认 30s 以利本地大模型长间隔吐字。可用 QIAZHI_V17_SSE_STALL_SEC 覆盖。"""
    try:
        v = float(str(os.getenv("QIAZHI_V17_SSE_STALL_SEC", "30") or "30").strip())
        return max(5.0, min(120.0, v))
    except (TypeError, ValueError):
        return 30.0


def _v1721_reasoning_suppressed_body_patch() -> Dict[str, Any]:
    """
    V17.21：请求体尽力关闭推理链扩展字段；未知键多数 OpenAI 兼容栈会忽略。
    设 QIAZHI_V17_DISABLE_REASONING=0 可关闭本补丁。
    """
    raw = str(os.getenv("QIAZHI_V17_DISABLE_REASONING", "1") or "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return {}
    return {"thinking": False, "reasoning_effort": "none"}


def _fuse_max_tokens_default() -> int:
    """叙事织造默认生成长度上限；默认 512 减轻本地 Ollama 卡顿。可用 QIAZHI_V17_FUSE_MAX_TOKENS 覆盖。"""
    try:
        v = int(str(os.getenv("QIAZHI_V17_FUSE_MAX_TOKENS", "512") or "512").strip())
        return max(64, min(8192, v))
    except (TypeError, ValueError):
        return 512

# 熔断时写入 llm_meta.error 与降级正文的人类可读前缀
_LOCAL_COMPUTE_EXHAUST_MSG = "[本地算力透支] 引擎思考超时，请尝试精简意志注入。"


def _log_will_dispatch(model: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[V17-WILL] {ts} Dispatching to {model}...", flush=True)


def _merge_physics_ssot_rows(
    rows: List[str],
    physics_tensor: Optional[Dict[str, Any]],
) -> List[str]:
    """V17.20：六柱事实行仅取自 physics_tensor（PhysicsCanonicalService），并剔除 Body 回灌柱位 echo。"""
    if not isinstance(physics_tensor, dict):
        return list(rows)
    from v17_rebirth.backend.services.physics_canonical import PhysicsCanonicalService, strip_client_pillar_echoes

    canon = PhysicsCanonicalService.materialize_prompt_lines(physics_tensor)
    tail = strip_client_pillar_echoes([str(x) for x in rows if str(x).strip()])
    return canon + tail


def build_llm_audit_payload(
    clean_fragments: list[str],
    *,
    will_proxy: str,
    decision_anchor: str,
    action_signal: bool,
    max_tokens: int = 512,
    role_style: str = V17_ROLE_WEAVER,
    physics_tensor: Optional[Dict[str, Any]] = None,
    session_id: str = "",
) -> Dict[str, Any]:
    """与 fuse() 即将发送的 System/User 对齐，供 SNAPSHOT（llm_audit_preview）在调用 LLM 前下发。"""
    rows = [str(x).strip() for x in clean_fragments if str(x).strip()]
    rows = _merge_physics_ssot_rows(rows, physics_tensor)
    rid = _normalize_fuse_role(str(role_style or V17_ROLE_WEAVER))
    if not rows:
        return {
            "audit_empty_fragments": True,
            "full_prompt_trace": _build_full_prompt_trace(
                system_prompt="",
                user_prompt="",
                messages=[],
                decision_anchor=str(decision_anchor or ""),
            ),
            "llm_system_prompt": "",
            "llm_user_prompt": "",
            "llm_request_messages": [],
            **_fuse_role_extras(rid),
        }
    system_prompt = build_v17_system_prompt(
        will_proxy=str(will_proxy or "stable"),
        decision_anchor=str(decision_anchor or ""),
        action_signal=bool(action_signal),
        role_style=rid,
        session_id=str(session_id or ""),
    )
    user_prompt = build_role_user_prompt(
        rows,
        role_id=rid,
        decision_anchor=str(decision_anchor or ""),
        list_cap=16,
        will_proxy=str(will_proxy or "stable"),
    )
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return {
        "full_prompt_trace": _build_full_prompt_trace(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            messages=messages,
            decision_anchor=str(decision_anchor or ""),
        ),
        "llm_system_prompt": system_prompt,
        "llm_user_prompt": user_prompt,
        "llm_request_messages": messages,
        "max_tokens_preview": int(max_tokens or _fuse_max_tokens_default()),
        **_fuse_role_extras(rid),
    }


def _parse_timeout(cfg: Dict[str, str], key: str, default: float) -> float:
    try:
        v = float(str(cfg.get(key) or "").strip() or default)
        return max(1.0, min(600.0, v))
    except (TypeError, ValueError):
        return default


def build_v17_system_prompt(
    *,
    will_proxy: str,
    decision_anchor: str,
    action_signal: bool,
    role_style: str = V17_ROLE_WEAVER,
    session_id: str = "",
) -> str:
    """多态角色 System；物理锚定仅经 PhysicsService.get_metadata(session_id)，禁止从 kwargs/body 注入柱位。"""
    from v17_rebirth.backend.narrative.semantic_fusion import build_v17_role_system_prompt
    from v17_rebirth.backend.services.physics_service import PhysicsService

    rid = _normalize_fuse_role(str(role_style or V17_ROLE_WEAVER))
    base = build_v17_role_system_prompt(
        role_id=rid,
        will_proxy=will_proxy,
        decision_anchor=decision_anchor,
        action_signal=action_signal,
    )
    sid = str(session_id or "").strip()
    if not sid:
        return base
    p = PhysicsService.get_metadata(sid)
    fp = p.get("four_pillars") if isinstance(p.get("four_pillars"), dict) else {}
    y, mo, d, h = fp.get("year"), fp.get("month"), fp.get("day"), fp.get("hour")
    luck, flow, fy = p.get("luck_pillar"), p.get("flow_pillar"), p.get("flow_year")
    anchor = (
        f"\n\n【元数据主权·仅服务端】"
        f"四柱：{y} / {mo} / {d} / {h}；大运：{luck}；流年：{flow}；流年锚年：{fy}。"
    )
    return base + anchor


_SENSITIVE_PATTERNS = (
    re.compile(r"sk-[a-zA-Z0-9]{10,}", re.I),
    re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]{20,}", re.I),
    re.compile(r"Basic\s+[A-Za-z0-9+/=]{40,}", re.I),
)

# 原始 SSE / JSON 审计体积上限，避免撑爆帧
_MAX_RAW_TRACE_CHARS = 400_000


def _endpoint_host(base_url: str) -> str:
    try:
        u = urlparse(str(base_url or "").strip())
        host = (u.hostname or "").strip()
        return host or ""
    except Exception:
        return ""


def _build_full_prompt_trace(
    *,
    system_prompt: str,
    user_prompt: str,
    messages: List[Dict[str, str]],
    decision_anchor: str,
) -> Dict[str, Any]:
    anchor = str(decision_anchor or "").strip()
    sys_t = str(system_prompt or "")
    return {
        "system_role": sys_t,
        "user_role": str(user_prompt or ""),
        "request_messages": messages,
        "decision_anchor_literal_in_system_role": bool(anchor and anchor in sys_t),
        "decision_anchor_len": len(anchor),
    }


def _blob_may_contain_secret(blob: str) -> bool:
    s = str(blob or "")
    return any(p.search(s) for p in _SENSITIVE_PATTERNS)


def transport_safe_llm_meta(meta: Dict[str, Any], *, llm_endpoint_host: str) -> Dict[str, Any]:
    """
    V17.15：发往客户端的 llm_meta 若疑似夹带密钥，仅保留模型侧信息与角色设定。
    """
    try:
        dumped = json.dumps(meta, ensure_ascii=False, default=str)
    except Exception:
        dumped = str(meta)
    if not _blob_may_contain_secret(dumped):
        return meta
    sys_p = str(meta.get("llm_system_prompt") or "")
    usr_p = str(meta.get("llm_user_prompt") or "")
    fpt = meta.get("full_prompt_trace")
    fpt_out: Dict[str, Any] = {}
    if isinstance(fpt, dict):
        fpt_out = {
            "system_role": str(fpt.get("system_role") or "")[:8000],
            "user_role": str(fpt.get("user_role") or "")[:8000],
            "decision_anchor_literal_in_system_role": bool(fpt.get("decision_anchor_literal_in_system_role")),
            "decision_anchor_len": fpt.get("decision_anchor_len"),
        }
    return {
        "ok": meta.get("ok"),
        "engine_state": meta.get("engine_state"),
        "elapsed_ms": meta.get("elapsed_ms"),
        "model": str(meta.get("model") or "").strip(),
        "provider": str(meta.get("provider") or "").strip(),
        "llm_endpoint_host": llm_endpoint_host,
        "error_id": meta.get("error_id"),
        "error": meta.get("error"),
        "llm_system_prompt": sys_p[:12000],
        "llm_user_prompt": usr_p[:12000],
        "full_prompt_trace": fpt_out,
        "llm_raw_response_json": "[REDACTED: suspected credential in trace]",
        "llm_meta_redacted": True,
        "prompt_dead_audit_unlock": meta.get("prompt_dead_audit_unlock"),
        "fuse_hard_circuit_sec": meta.get("fuse_hard_circuit_sec"),
        "llm_ttft_sec": meta.get("llm_ttft_sec"),
        "ttft_break": meta.get("ttft_break"),
    }


def _cap_raw_trace(s: str) -> str:
    t = str(s or "")
    if len(t) <= _MAX_RAW_TRACE_CHARS:
        return t
    return t[: _MAX_RAW_TRACE_CHARS // 2] + "\n…[truncated]…\n" + t[-_MAX_RAW_TRACE_CHARS // 2 :]


def _pack_llm_meta(
    cfg: Dict[str, str],
    *,
    decision_anchor: str,
    ok: bool,
    engine_state: str,
    elapsed_ms: int,
    error_id: str,
    error: str,
    system_prompt: str,
    user_prompt: str,
    messages: List[Dict[str, str]],
    llm_reply: str,
    raw_json: str,
    http_timeout: float,
    fuse_wait: float,
    stream: Optional[bool] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    host = _endpoint_host(str(cfg.get("base_url") or ""))
    meta: Dict[str, Any] = {
        "ok": ok,
        "engine_state": engine_state,
        "elapsed_ms": elapsed_ms,
        "model": str(cfg.get("model", "")).strip(),
        "provider": str(cfg.get("provider", "")).strip(),
        "error_id": error_id,
        "llm_endpoint_host": host,
        "http_timeout_sec": http_timeout,
        "fuse_wait_timeout_sec": fuse_wait,
        "llm_system_prompt": system_prompt,
        "llm_user_prompt": user_prompt,
        "llm_request_messages": messages,
        "llm_reply": llm_reply,
        "llm_raw_response_json": _cap_raw_trace(raw_json),
        "full_prompt_trace": _build_full_prompt_trace(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            messages=messages,
            decision_anchor=str(decision_anchor or ""),
        ),
    }
    if error:
        meta["error"] = error
    if stream is not None:
        meta["stream"] = stream
    if extras:
        meta.update(extras)
    return transport_safe_llm_meta(meta, llm_endpoint_host=host)


def _parse_chat_blob_stream_parts(blob: Dict[str, Any]) -> Tuple[str, str]:
    """
    拆出 (正文增量, 推理链增量)。
    显式支持 delta / message 下的 content、reasoning_content、reasoning（OpenAI 兼容与思考模型）。
    """
    chs = blob.get("choices")
    ch0 = chs[0] if isinstance(chs, list) and chs and isinstance(chs[0], dict) else {}
    c_out, r_out = "", ""
    if isinstance(ch0, dict):
        delta = ch0.get("delta") if isinstance(ch0.get("delta"), dict) else {}
        c_out = str((delta or {}).get("content") or "").strip()
        r_parts: List[str] = []
        for key in ("reasoning_content", "reasoning", "thinking", "thought"):
            v = str((delta or {}).get(key) or "").strip()
            if v:
                r_parts.append(v)
        r_out = "".join(r_parts).strip()
        msg = ch0.get("message") if isinstance(ch0.get("message"), dict) else {}
        if not c_out:
            c_out = str((msg or {}).get("content") or "").strip()
        if not r_out:
            for key in ("reasoning_content", "reasoning", "thinking", "thought"):
                v = str((msg or {}).get(key) or "").strip()
                if v:
                    r_out = v
                    break
    resp = str(blob.get("response") or "").strip()
    if resp and not c_out:
        c_out = resp
    return c_out, r_out


def _chunk_text_from_chat_blob(blob: Dict[str, Any]) -> Optional[str]:
    """优先正文；无正文时有推理链则返回推理增量（兼容旧调用）。"""
    c, r = _parse_chat_blob_stream_parts(blob)
    if c:
        return c
    if r:
        return r
    return None


def _sse_stream_parts(line: str) -> Tuple[str, str]:
    """解析单行 SSE / NDJSON，返回 (正文增量, 推理增量)。"""
    s = str(line or "").strip()
    if not s or s == "data: [DONE]":
        return "", ""
    raw = s[5:].strip() if s.startswith("data:") else s
    if raw == "[DONE]":
        return "", ""
    try:
        blob = json.loads(raw)
    except json.JSONDecodeError:
        return "", ""
    if not isinstance(blob, dict):
        return "", ""
    return _parse_chat_blob_stream_parts(blob)


def _sse_delta_content(line: str) -> Optional[str]:
    """
    单行 SSE 的「有效增量」：优先正文 content；若无则取 reasoning / thought 任一片段。
    V17.21：推理类片段视为有效 token（用于首包活性与读行策略），正文织造仍仅用 content 分支。
    """
    c, r = _sse_stream_parts(line)
    if c:
        return c
    if r:
        return r
    return None


@dataclass
class V17MicroLlmClient:
    """OpenAI-compatible micro client：流式 chat + ActionQueue 可中断。"""

    bridge: V17LlmBridge

    def _auth_headers(self, cfg: Dict[str, str]) -> Dict[str, str]:
        h: Dict[str, str] = {}
        key = str(cfg.get("api_key") or "").strip()
        user = str(cfg.get("username") or "").strip()
        pw = str(cfg.get("password") or "").strip()
        if key:
            h["Authorization"] = f"Bearer {key}"
        elif user and pw:
            token = base64.b64encode(f"{user}:{pw}".encode("utf-8")).decode("utf-8")
            h["Authorization"] = f"Basic {token}"
        return h

    async def fuse(
        self,
        *,
        fragments: list[str],
        will_proxy: str,
        max_tokens: int = 512,
        decision_anchor: str = "",
        action_signal: bool = False,
        action_queue: Optional[asyncio.Queue[Dict[str, Any]]] = None,
        on_llm_partial: Optional[Callable[[str], Awaitable[None]]] = None,
        role_style: str = V17_ROLE_WEAVER,
        llm_emitter: Optional[AsyncEventEmitter] = None,
        status_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        physics_tensor: Optional[Dict[str, Any]] = None,
        session_id: str = "",
    ) -> AsyncIterator[Dict[str, Any]]:
        """V17.19：异步生成器步进（dispatching / handshake / weaving / complete|error）；编排层仍由 legacy 回调驱动。"""
        _ = action_queue
        cfg = self.bridge.resolve()
        rid = _normalize_fuse_role(str(role_style or V17_ROLE_WEAVER))
        ttft = _fuse_ttft_sec()
        hard = max(_fuse_hard_sec(), ttft + 2.0)
        outer_fuse_sec = min(120.0, max(hard, ttft + 15.0, 45.0))
        fuse_wait_cfg = _parse_timeout(cfg, "fuse_wait_timeout_sec", 30.0)
        http_timeout = min(120.0, max(_parse_timeout(cfg, "http_timeout_sec", 60.0), ttft + 5.0))
        fuse_meta = min(fuse_wait_cfg, hard)
        system_prompt = build_v17_system_prompt(
            will_proxy=str(will_proxy or "stable"),
            decision_anchor=str(decision_anchor or ""),
            action_signal=bool(action_signal),
            role_style=rid,
            session_id=str(session_id or ""),
        )
        row_in = [str(x).strip() for x in fragments if str(x).strip()]
        row_in = _merge_physics_ssot_rows(row_in, physics_tensor)
        user_prompt = build_role_user_prompt(
            row_in,
            role_id=rid,
            decision_anchor=str(decision_anchor or ""),
            list_cap=16,
            will_proxy=str(will_proxy or "stable"),
        )
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        body: Dict[str, Any] = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": int(max_tokens or _fuse_max_tokens_default()),
            "stream": True,
            **_v1721_reasoning_suppressed_body_patch(),
        }
        base_url = str(cfg.get("base_url") or "").strip()
        started = time.perf_counter()
        stream_buf: Dict[str, str] = {"acc": ""}

        async def _legacy_sink(ev: Dict[str, Any]) -> None:
            if status_callback is not None:
                await status_callback(ev)
            await _mirror_legacy_emitter(ev, llm_emitter)

        def _fail_extras(raw_rows: List[str], *, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            out: Dict[str, Any] = {
                **_fuse_role_extras(rid),
                "facts": raw_rows,
                "prompt_dead_audit_unlock": True,
                "fuse_hard_circuit_sec": outer_fuse_sec,
                "llm_ttft_sec": ttft,
            }
            if extra:
                out.update(extra)
            return out

        async def _yield_step(step_ev: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
            await _emit_fuse_step_legacy(
                step_ev,
                status_callback=status_callback,
                llm_emitter=llm_emitter,
                on_llm_partial=on_llm_partial,
                stream_buf=stream_buf,
            )
            yield step_ev

        async def _event_stream() -> AsyncIterator[Dict[str, Any]]:
            _log_will_dispatch(str(cfg.get("model") or "unknown").strip() or "unknown")
            prompt_payload = {
                "messages": messages,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "body": {
                    "model": body.get("model"),
                    "stream": bool(body.get("stream")),
                    "max_tokens": body.get("max_tokens"),
                },
            }
            async for ev in _yield_step({"step": "dispatching", "data": prompt_payload}):
                yield ev
            if httpx is None:
                async for ev in _yield_step({"step": "handshake", "latency": 0}):
                    yield ev
                out = await self._fuse_urllib_fallback(
                    cfg=cfg,
                    body={**body, "stream": False},
                    messages=messages,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    decision_anchor=str(decision_anchor or ""),
                    http_timeout=http_timeout,
                    fuse_wait=min(fuse_meta, ttft),
                    started=started,
                    fragments=fragments,
                    on_llm_partial=on_llm_partial,
                    fuse_llm_extras=_fuse_role_extras(rid),
                    step_sink=_legacy_sink,
                )
                ut = str((out or {}).get("text") or "").strip()
                if ut:
                    yield {"step": "weaving", "token": ut}
                async for ev in _yield_step({"step": "complete", "result": out}):
                    yield ev
                return

            endpoint = base_url.rstrip("/") + "/chat/completions"
            headers = {"Content-Type": "application/json", **self._auth_headers(cfg)}
            timeout = httpx.Timeout(http_timeout, connect=min(10.0, http_timeout))
            acc: List[str] = []
            sse_raw_lines: List[str] = []
            saw_first_token = False
            stall_sec = float(_sse_line_idle_sec())

            async def _stream_once() -> AsyncIterator[Dict[str, Any]]:
                nonlocal acc, saw_first_token
                first_token_emitted = False
                # 首包活性：_sse_delta_content 将 reasoning/thought 与 content 同等视为「已见增量」，避免长推理静默。
                has_seen_delta = False
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream("POST", endpoint, json=body, headers=headers) as resp:
                        resp.raise_for_status()
                        lat_ms = int((time.perf_counter() - started) * 1000)
                        async for ev in _yield_step({"step": "handshake", "latency": lat_ms}):
                            yield ev
                        if on_llm_partial is not None:
                            boot = (
                                "「裁决」已启封，候引擎吐字…"
                                if rid == V17_ROLE_JUDGE
                                else "「织造」已启封，候引擎吐字…"
                            )
                            await on_llm_partial(boot)
                        line_iter = resp.aiter_lines().__aiter__()
                        t_first = time.perf_counter()
                        while True:
                            try:
                                if not has_seen_delta:
                                    budget = ttft - (time.perf_counter() - t_first)
                                    if budget <= 0:
                                        await resp.aclose()
                                        raise asyncio.TimeoutError("llm_ttft_break_no_first_token")
                                    line = await asyncio.wait_for(
                                        line_iter.__anext__(),
                                        timeout=min(max(budget, 0.001), stall_sec),
                                    )
                                else:
                                    line = await asyncio.wait_for(line_iter.__anext__(), timeout=stall_sec)
                            except StopAsyncIteration:
                                break
                            ls = str(line or "").strip()
                            if ls.startswith("data:"):
                                sse_raw_lines.append(ls[:20000])
                            eff = _sse_delta_content(line)
                            c_part, _r_part = _sse_stream_parts(line)
                            if eff:
                                has_seen_delta = True
                                saw_first_token = True
                            if c_part:
                                if not first_token_emitted:
                                    first_token_emitted = True
                                acc.append(c_part)
                                # 裁决/织造均须流式步进，否则编排层 partial_q 长时间无正文，前端误判「仍在连接」。
                                if rid in (V17_ROLE_WEAVER, V17_ROLE_JUDGE):
                                    async for ev in _yield_step({"step": "weaving", "token": c_part}):
                                        yield ev
                            await asyncio.sleep(0)

            raw_sse_joined = ""
            try:
                async for ev in _stream_once():
                    yield ev
                raw_sse_joined = "\n".join(sse_raw_lines)
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                error_id = f"V17-LLM-{uuid.uuid4().hex[:8].upper()}"
                raw_rows = [str(x).strip() for x in fragments if str(x).strip()][:6]
                fail_text = f"[叙事引擎重连中][{error_id}] " + " | ".join(raw_rows)
                raw_sse_joined = raw_sse_joined or "\n".join(sse_raw_lines)
                extra: Dict[str, Any] = {}
                err_detail = str(exc)
                if isinstance(exc, TimeoutError):
                    if saw_first_token:
                        extra["sse_line_idle_sec"] = float(stall_sec)
                    else:
                        extra["ttft_break"] = True
                    err_detail = f"{_LOCAL_COMPUTE_EXHAUST_MSG} ({exc!s})"
                    extra["local_compute_exhaust"] = True
                fail_payload = {
                    "text": fail_text.strip(),
                    "llm_meta": _pack_llm_meta(
                        cfg,
                        decision_anchor=str(decision_anchor or ""),
                        ok=False,
                        engine_state="reconnecting",
                        elapsed_ms=elapsed_ms,
                        error_id=error_id,
                        error=err_detail,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        messages=messages,
                        llm_reply="",
                        raw_json=raw_sse_joined,
                        http_timeout=http_timeout,
                        fuse_wait=fuse_meta,
                        extras=_fail_extras(raw_rows, extra=extra or None),
                    ),
                }
                async for ev in _yield_step({"step": "error", "result": fail_payload}):
                    yield ev
                return

            elapsed_ms = int((time.perf_counter() - started) * 1000)
            text = "".join(acc).strip()
            raw_sse_joined = raw_sse_joined or "\n".join(sse_raw_lines)
            if not text:
                out_fb = await self._fuse_urllib_fallback(
                    cfg=cfg,
                    body={**body, "stream": False},
                    messages=messages,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    decision_anchor=str(decision_anchor or ""),
                    http_timeout=http_timeout,
                    fuse_wait=min(fuse_meta, ttft),
                    started=started,
                    fragments=fragments,
                    on_llm_partial=on_llm_partial,
                    prior_stream_raw_json=raw_sse_joined,
                    fuse_llm_extras=_fuse_role_extras(rid),
                    step_sink=_legacy_sink,
                )
                fb = str((out_fb or {}).get("text") or "").strip()
                if fb:
                    yield {"step": "weaving", "token": fb}
                async for ev in _yield_step({"step": "complete", "result": out_fb}):
                    yield ev
                return
            ok_payload = {
                "text": text,
                "llm_meta": _pack_llm_meta(
                    cfg,
                    decision_anchor=str(decision_anchor or ""),
                    ok=True,
                    engine_state="ok",
                    elapsed_ms=elapsed_ms,
                    error_id="",
                    error="",
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    messages=messages,
                    llm_reply=text,
                    raw_json=raw_sse_joined,
                    http_timeout=http_timeout,
                    fuse_wait=fuse_meta,
                    stream=True,
                    extras=_fuse_role_extras(rid),
                ),
            }
            async for ev in _yield_step({"step": "complete", "result": ok_payload}):
                yield ev

        try:
            async with asyncio.timeout(outer_fuse_sec):
                async with _fuse_outbound_sem():
                    async for step_ev in _event_stream():
                        yield step_ev
        except TimeoutError as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            error_id = f"V17-LLM-{uuid.uuid4().hex[:8].upper()}"
            raw_rows = [str(x).strip() for x in fragments if str(x).strip()][:6]
            timeout_payload = {
                "text": f"[叙事引擎重连中][{error_id}] " + " | ".join(raw_rows),
                "llm_meta": _pack_llm_meta(
                    cfg,
                    decision_anchor=str(decision_anchor or ""),
                    ok=False,
                    engine_state="reconnecting",
                    elapsed_ms=elapsed_ms,
                    error_id=error_id,
                    error=f"{_LOCAL_COMPUTE_EXHAUST_MSG} (outer {outer_fuse_sec}s) {exc!s}",
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    messages=messages,
                    llm_reply="",
                    raw_json="",
                    http_timeout=http_timeout,
                    fuse_wait=fuse_meta,
                    extras=_fail_extras(
                        raw_rows,
                        extra={"hard_circuit_outer": True, "local_compute_exhaust": True},
                    ),
                ),
            }
            async for ev in _yield_step({"step": "error", "result": timeout_payload}):
                yield ev

    async def iter_fuse(
        self,
        *,
        fragments: list[str],
        will_proxy: str,
        max_tokens: int = 512,
        decision_anchor: str = "",
        action_signal: bool = False,
        action_queue: Optional[asyncio.Queue[Dict[str, Any]]] = None,
        on_llm_partial: Optional[Callable[[str], Awaitable[None]]] = None,
        role_style: str = V17_ROLE_WEAVER,
        llm_emitter: Optional[AsyncEventEmitter] = None,
        status_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        physics_tensor: Optional[Dict[str, Any]] = None,
        session_id: str = "",
    ) -> AsyncIterator[Dict[str, Any]]:
        """与 `fuse()` 同源步进帧（V17.19 字典形态）。"""
        async for ev in self.fuse(
            fragments=fragments,
            will_proxy=will_proxy,
            max_tokens=max_tokens,
            decision_anchor=decision_anchor,
            action_signal=action_signal,
            action_queue=action_queue,
            on_llm_partial=on_llm_partial,
            role_style=role_style,
            llm_emitter=llm_emitter,
            status_callback=status_callback,
            physics_tensor=physics_tensor,
            session_id=session_id,
        ):
            yield ev

    async def _fuse_urllib_fallback(
        self,
        *,
        cfg: Dict[str, str],
        body: dict,
        messages: List[Dict[str, str]],
        system_prompt: str,
        user_prompt: str,
        decision_anchor: str,
        http_timeout: float,
        fuse_wait: float,
        started: float,
        fragments: list[str],
        on_llm_partial: Optional[Callable[[str], Awaitable[None]]] = None,
        prior_stream_raw_json: str = "",
        fuse_llm_extras: Optional[Dict[str, Any]] = None,
        step_sink: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> dict:
        """无 httpx 时退回同步非流式（不可 token 级中断）。"""
        try:
            text, raw_http_json = await asyncio.wait_for(
                self._chat_urllib(str(cfg.get("base_url") or ""), str(cfg.get("api_key") or ""), body, http_timeout_sec=http_timeout),
                timeout=fuse_wait,
            )
            if on_llm_partial and text:
                await on_llm_partial(text)
            if step_sink is not None and str(text or "").strip():
                await step_sink({"status": "streaming", "chunk": str(text or "").strip()})
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            merged_raw = "\n".join([x for x in [prior_stream_raw_json.strip(), raw_http_json.strip()] if x]).strip()
            return {
                "text": str(text or "").strip(),
                "llm_meta": _pack_llm_meta(
                    cfg,
                    decision_anchor=str(decision_anchor or ""),
                    ok=True,
                    engine_state="ok",
                    elapsed_ms=elapsed_ms,
                    error_id="",
                    error="",
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    messages=messages,
                    llm_reply=str(text or "").strip(),
                    raw_json=merged_raw or raw_http_json,
                    http_timeout=http_timeout,
                    fuse_wait=fuse_wait,
                    stream=False,
                    extras=dict(fuse_llm_extras or {}),
                ),
            }
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            error_id = f"V17-LLM-{uuid.uuid4().hex[:8].upper()}"
            raw_rows = [str(x).strip() for x in fragments if str(x).strip()][:6]
            ex: Dict[str, Any] = {
                **(fuse_llm_extras or {}),
                "prompt_dead_audit_unlock": True,
                "fuse_hard_circuit_sec": _fuse_hard_sec(),
            }
            if raw_rows:
                ex["facts"] = raw_rows
            err_msg = str(exc)
            if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
                err_msg = f"{_LOCAL_COMPUTE_EXHAUST_MSG} ({exc!s})"
                ex["local_compute_exhaust"] = True
            return {
                "text": f"[叙事引擎重连中][{error_id}] " + " | ".join(raw_rows),
                "llm_meta": _pack_llm_meta(
                    cfg,
                    decision_anchor=str(decision_anchor or ""),
                    ok=False,
                    engine_state="reconnecting",
                    elapsed_ms=elapsed_ms,
                    error_id=error_id,
                    error=err_msg,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    messages=messages,
                    llm_reply="",
                    raw_json=prior_stream_raw_json.strip(),
                    http_timeout=http_timeout,
                    fuse_wait=fuse_wait,
                    extras=ex,
                ),
            }

    async def _chat_urllib(self, base_url: str, api_key: str, body: dict, *, http_timeout_sec: float) -> Tuple[str, str]:
        def _sync_call() -> Tuple[str, str]:
            endpoint = base_url.rstrip("/") + "/chat/completions"
            payload = json.dumps(body).encode("utf-8")
            req = request.Request(endpoint, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")
            cfg = self.bridge.resolve()
            for k, v in self._auth_headers(cfg).items():
                req.add_header(k, v)
            with request.urlopen(req, timeout=float(http_timeout_sec)) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            raw_str = json.dumps(raw, ensure_ascii=False) if isinstance(raw, dict) else str(raw)
            text = (
                (((raw.get("choices") or [{}])[0] or {}).get("message") or {}).get("content")
                if isinstance(raw, dict)
                else ""
            )
            return str(text or "").strip(), raw_str

        return await asyncio.to_thread(_sync_call)
