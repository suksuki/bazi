"""V12.94：极简冲突仲裁 LLM（仅 JSON：decision / reason）；V12.95：完整审计回传。"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Mapping, Sequence

from app.llm.client import QwenClient

_LOG = logging.getLogger(__name__)

# V13.02：批量 user 提示长度软顶，避免多冲突 × 长物理上下文撑爆上下文窗口（与 system / completion 共用配额）
_BATCH_USER_CHAR_BUDGET = 26_000


def _build_batch_user_message(rows: List[Dict[str, Any]], lang: str) -> str:
    """在保持条数不变的前提下压缩每条 JSON/摘要，使总字符数落在预算内。"""
    n = max(len(rows), 1)
    ctx_cap = max(420, min(2000, 11_000 // n))
    summary_cap = max(160, min(640, 900 // n))
    prefix = "以下多条冲突请逐条裁决，输出 JSON 数组，长度必须等于冲突条数 " f"（{len(rows)}）。\n\n"

    def one_pass(cc: int, sc: int) -> str:
        blocks_local: List[str] = []
        for i, row in enumerate(rows):
            cands = row.get("candidate_plugins") if isinstance(row.get("candidate_plugins"), list) else []
            cands_s = [str(x).strip() for x in cands if str(x).strip()]
            ctx = row.get("conflict_context") if isinstance(row.get("conflict_context"), dict) else {}
            ctx_block = ""
            if ctx:
                try:
                    ctx_block = "\n物理证据(JSON)：\n" + json.dumps(ctx, ensure_ascii=False)[:cc]
                except (TypeError, ValueError):
                    ctx_block = ""
            summary = str(row.get("conflict_summary") or "")[:sc]
            blocks_local.append(
                f"[冲突#{i}]\n语言={lang}。\n摘要：{summary}{ctx_block}\n"
                f"候选插件 id（必须择一）：{json.dumps(cands_s, ensure_ascii=False)}"
            )
        return prefix + "\n\n---\n\n".join(blocks_local)

    user = one_pass(ctx_cap, summary_cap)
    for _ in range(8):
        if len(user) <= _BATCH_USER_CHAR_BUDGET:
            return user
        ctx_cap = max(380, int(ctx_cap * 0.72))
        summary_cap = max(140, int(summary_cap * 0.82))
        user = one_pass(ctx_cap, summary_cap)
    if len(user) > _BATCH_USER_CHAR_BUDGET:
        _LOG.warning(
            "batch_conflict_arbiter_llm user prompt still over budget len=%s budget=%s rows=%s",
            len(user),
            _BATCH_USER_CHAR_BUDGET,
            len(rows),
        )
    return user

_SYSTEM = (
    "你是排盘引擎的冲突仲裁子模块。只输出一行合法 JSON 对象，禁止 Markdown、禁止解释。"
    '格式严格为：{"decision":"<Plugin_ID>","reason":"<中文理由与整合结论>","certainty":"CONFIDENT"|"UNCERTAIN"}。'
    "decision 必须从用户给出的候选 plugin id 中原样选择一个。"
    "reason 在 800 字以内：除说明择一依据外，允许做跨证据的简短联想，并给出一句有温度的整合性收束（非套话）。"
    "certainty=UNCERTAIN 仅在你对候选与物理证据的取舍非常不确定时使用；其余情况输出 CONFIDENT。"
    "用户会附带物理证据 JSON，请优先依据其中的 verified_fact_lines、global_entropy、"
    "decision_inbox_match_scores 与 conflict_point 做取舍。"
)


def _extract_json_array(text: str) -> List[Any] | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    start = raw.find("[")
    end = raw.rfind("]")
    if start < 0 or end <= start:
        return None
    chunk = raw[start : end + 1]
    try:
        arr = json.loads(chunk)
    except json.JSONDecodeError:
        return None
    return arr if isinstance(arr, list) else None


def _extract_json_object(text: str) -> Dict[str, Any] | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    chunk = raw[start : end + 1]
    try:
        obj = json.loads(chunk)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _audit_shell(
    messages: list[dict[str, str]],
    raw_response: str,
    conflict_context: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    return {
        "messages": messages,
        "raw_response": str(raw_response or "")[:8000],
        "conflict_context": dict(conflict_context or {}),
    }


async def invoke_conflict_arbiter_llm(
    *,
    client: QwenClient,
    conflict_summary: str,
    candidate_plugins: Sequence[str],
    lang: str = "zh",
    conflict_context: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    调用 LLM。成功时 ``decision`` 合法；始终返回 ``audit``（prompt_messages / raw_response / conflict_context）。
    """
    cands = [str(x).strip() for x in candidate_plugins if str(x).strip()]
    if not cands:
        return {"decision": "", "reason": "", "certainty": "CONFIDENT", "audit": _audit_shell([], "", conflict_context)}
    ctx = dict(conflict_context or {})
    ctx_block = ""
    if ctx:
        try:
            ctx_block = "\n物理证据上下文(JSON)：\n" + json.dumps(ctx, ensure_ascii=False)[:4000]
        except (TypeError, ValueError):
            ctx_block = ""
    user = (
        f"语言={lang}。\n冲突摘要：{conflict_summary[:800]}{ctx_block}\n"
        f"候选插件 id（必须择一）：{json.dumps(cands, ensure_ascii=False)}"
    )
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user},
    ]
    raw = ""
    try:
        raw, _tel = await client.chat_with_telemetry(
            messages,
            temperature=0.05,
            max_tokens=900,
            stop=["Thinking Process:", "Reasoning:", "思考过程", "推理过程"],
        )
    except Exception:
        _LOG.debug("conflict_arbiter_llm chat failed", exc_info=True)
        return {"decision": "", "reason": "", "certainty": "CONFIDENT", "audit": _audit_shell(messages, "", conflict_context)}
    obj = _extract_json_object(str(raw or ""))
    audit = _audit_shell(messages, str(raw or ""), conflict_context)
    if not obj:
        return {"decision": "", "reason": "", "certainty": "CONFIDENT", "audit": audit}
    decision = str(obj.get("decision") or "").strip()
    reason = str(obj.get("reason") or "").strip()
    cert = str(obj.get("certainty") or "CONFIDENT").strip().upper()
    if cert not in ("CONFIDENT", "UNCERTAIN"):
        cert = "CONFIDENT"
    if decision not in cands:
        return {"decision": "", "reason": reason or "", "certainty": cert, "audit": audit}
    return {"decision": decision, "reason": reason[:800], "certainty": cert, "audit": audit}


_BATCH_SYSTEM = (
    "你是排盘引擎的批量冲突仲裁子模块。只输出一行合法 JSON 数组，禁止 Markdown、禁止解释。"
    "数组长度必须与输入 conflicts 条数完全一致，顺序一一对应（index 0 对第 1 条冲突）。"
    '每项严格为：{"index":<int>,"decision":"<Plugin_ID>","reason":"<中文理由与整合结论>","certainty":"CONFIDENT"|"UNCERTAIN"}。'
    "decision 必须从该条冲突对应的候选 plugin id 列表中原样选择一个。"
    "每条 reason 在 800 字以内：可适度串联本条与其它条目共通的物理线索，并给出有温度的整合收束。"
    "certainty=UNCERTAIN 仅在对该条裁决非常不确定时使用；其余为 CONFIDENT。"
    "用户会附带每条冲突的物理证据 JSON，请逐条独立裁决。"
)


async def invoke_batch_conflict_arbiter_llm(
    *,
    client: QwenClient,
    items: Sequence[Mapping[str, Any]],
    lang: str = "zh",
) -> Dict[str, Any]:
    """
    批量仲裁：``items`` 每项至少含 ``conflict_summary``、``candidate_plugins``、``conflict_context``（可选）。
    成功时 ``results`` 与 ``items`` 等长；``audit`` 含共用 prompt / raw_response。
    """
    rows: List[Dict[str, Any]] = [dict(x) if isinstance(x, dict) else {} for x in items]
    if not rows:
        return {"results": [], "audit": _audit_shell([], "", None), "raw": ""}

    user = _build_batch_user_message(rows, lang)
    messages = [
        {"role": "system", "content": _BATCH_SYSTEM},
        {"role": "user", "content": user},
    ]
    raw = ""
    max_tokens = min(3200, 280 + 320 * len(rows))
    try:
        raw, _tel = await client.chat_with_telemetry(
            messages,
            temperature=0.05,
            max_tokens=max_tokens,
            stop=["Thinking Process:", "Reasoning:", "思考过程", "推理过程"],
        )
    except Exception:
        _LOG.debug("batch_conflict_arbiter_llm chat failed", exc_info=True)
        return {"results": [], "audit": _audit_shell(messages, "", None), "raw": ""}

    arr = _extract_json_array(str(raw or ""))
    audit = _audit_shell(messages, str(raw or ""), {"protocol": "batch_arbitration_audit_shell.v1", "n": len(rows)})
    if not arr or len(arr) != len(rows):
        _LOG.warning(
            "batch_conflict_arbiter_llm length mismatch want=%s got=%s",
            len(rows),
            len(arr) if arr else 0,
        )
        return {"results": [], "audit": audit, "raw": str(raw or "")}

    out_results: List[Dict[str, Any]] = []
    for i, row in enumerate(rows):
        cands = row.get("candidate_plugins") if isinstance(row.get("candidate_plugins"), list) else []
        cands_s = [str(x).strip() for x in cands if str(x).strip()]
        cell = arr[i] if i < len(arr) else None
        if not isinstance(cell, dict):
            return {"results": [], "audit": audit, "raw": str(raw or "")}
        idx = cell.get("index", i)
        try:
            idx_int = int(idx)
        except (TypeError, ValueError):
            idx_int = i
        if idx_int != i:
            _LOG.warning("batch_conflict_arbiter_llm index mismatch at %s got=%s", i, idx_int)
            return {"results": [], "audit": audit, "raw": str(raw or "")}
        decision = str(cell.get("decision") or "").strip()
        reason = str(cell.get("reason") or "").strip()
        cert = str(cell.get("certainty") or "CONFIDENT").strip().upper()
        if cert not in ("CONFIDENT", "UNCERTAIN"):
            cert = "CONFIDENT"
        if decision not in cands_s:
            return {"results": [], "audit": audit, "raw": str(raw or "")}
        out_results.append({"index": i, "decision": decision, "reason": reason[:800], "certainty": cert})

    return {"results": out_results, "audit": audit, "raw": str(raw or "")}


__all__ = ["invoke_batch_conflict_arbiter_llm", "invoke_conflict_arbiter_llm"]
