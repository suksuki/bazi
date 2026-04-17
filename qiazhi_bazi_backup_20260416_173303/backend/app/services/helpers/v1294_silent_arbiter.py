"""V12.94 / V12.98：analyze-clash 路径上的静默冲突仲裁（AUTO_LLM 批量 LLM）。"""

from __future__ import annotations

import copy
import logging
import uuid
from typing import Any, Dict, List, Mapping, Optional, Tuple

from app.core.runtime_config import get_runtime_config
from app.llm.client import QwenClient
from app.logic.brain.conflict_arbiter_llm import invoke_batch_conflict_arbiter_llm
from app.logic.brain.decision_hub import (
    append_arbitration_audit_feed,
    append_silent_arbiter_meta,
    build_arbitration_audit_entry,
    build_arbitration_physics_context,
    build_arbitration_theme,
    conflict_display_name,
    conflict_pattern_signature,
    load_gold_arbiter_matching,
    merge_silent_arbiter_into_assertion_tree,
    persist_arbitration_log_to_snapshot,
    should_auto_resolve,
)

_LOG = logging.getLogger(__name__)


def _entropy_cap_from_runtime() -> float:
    cfg = get_runtime_config()
    b = cfg.get("brain")
    if isinstance(b, dict):
        v = b.get("auto_arbiter_max_entropy")
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return max(0.05, min(0.99, float(v)))
    return 0.3


def _primary_conflict_from_metadata(metadata: Mapping[str, Any]) -> Dict[str, Any]:
    cm = metadata.get("conflict_matrix") if isinstance(metadata.get("conflict_matrix"), dict) else {}
    pts = cm.get("points") if isinstance(cm.get("points"), list) else []
    if pts and isinstance(pts[0], dict):
        p0 = pts[0]
        return {"kind": str(p0.get("kind") or ""), "detail": str(p0.get("detail") or "")}
    return {"kind": "", "detail": ""}


def _global_entropy_value(physics_tensor: Mapping[str, Any]) -> float:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    ge = meta.get("global_entropy")
    if isinstance(ge, dict):
        v = ge.get("value")
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    return 0.5


def _inbox_hot_scores(physics_tensor: Mapping[str, Any]) -> List[float]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    inbox = meta.get("decision_inbox_v1") if isinstance(meta.get("decision_inbox_v1"), dict) else {}
    rows = inbox.get("match_scores") if isinstance(inbox.get("match_scores"), list) else []
    out: List[float] = []
    for x in rows:
        if isinstance(x, dict):
            try:
                out.append(float(x.get("score") or 0.0))
            except (TypeError, ValueError):
                continue
    out.sort(reverse=True)
    return out


def _candidate_plugins_from_inbox(physics_tensor: Mapping[str, Any], limit: int = 6) -> List[str]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    inbox = meta.get("decision_inbox_v1") if isinstance(meta.get("decision_inbox_v1"), dict) else {}
    rows = inbox.get("match_scores") if isinstance(inbox.get("match_scores"), list) else []
    scored: List[Tuple[float, str]] = []
    for x in rows:
        if not isinstance(x, dict):
            continue
        pid = str(x.get("plugin_id") or "").strip()
        if not pid:
            continue
        try:
            sc = float(x.get("score") or 0.0)
        except (TypeError, ValueError):
            sc = 0.0
        scored.append((sc, pid))
    scored.sort(key=lambda t: t[0], reverse=True)
    seen: set[str] = set()
    out: List[str] = []
    for _sc, pid in scored:
        if pid in seen:
            continue
        seen.add(pid)
        out.append(pid)
        if len(out) >= limit:
            break
    return out


def _effective_entropy_for_high_tension(
    base_entropy: float,
    *,
    reason_code: str,
    score_spread: float,
) -> float:
    """M3 高分张力且插件分差极小时，视为可自动裁决的低结构风险。"""
    if reason_code != "M3_HIGH_TENSION_PENDING":
        return base_entropy
    if score_spread < 0.08:
        return min(base_entropy, 0.55)
    return base_entropy


async def maybe_apply_v1294_silent_arbiter_to_analyze_clash(
    *,
    out: Dict[str, Any],
    session_id: Optional[int],
    lang: str,
    client: QwenClient,
) -> Dict[str, Any]:
    """
    当 Active Probing 为 ``M3_HIGH_TENSION_PENDING`` 且冲突点经黄金账本对齐可走自动裁决时：
    将冲突入队并 **一次性** 调用批量仲裁 LLM，再原子写入多条 LAW / 审计，并解除本轮 blocking interrupt（无需弹窗）。
    """
    active = out.get("active_probing") if isinstance(out.get("active_probing"), dict) else {}
    reason = str(active.get("reason_code") or "").strip()
    interrupt = out.get("interrupt_request") if isinstance(out.get("interrupt_request"), dict) else {}
    if reason != "M3_HIGH_TENSION_PENDING" or not interrupt:
        return out

    metadata = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    physics_tensor = out.get("physics_tensor") if isinstance(out.get("physics_tensor"), dict) else {}
    meta_m = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}

    scores = _inbox_hot_scores(physics_tensor)
    spread = (scores[0] - scores[1]) if len(scores) >= 2 else 1.0
    base_w = _global_entropy_value(physics_tensor)
    eff_w = _effective_entropy_for_high_tension(base_w, reason_code=reason, score_spread=spread)

    meta_m["pending_arbitration_queue_v1"] = []
    cm = metadata.get("conflict_matrix") if isinstance(metadata.get("conflict_matrix"), dict) else {}
    pts_raw = cm.get("points") if isinstance(cm.get("points"), list) else []
    point_dicts: List[Dict[str, str]] = []
    for p in pts_raw:
        if isinstance(p, dict):
            point_dicts.append({"kind": str(p.get("kind") or ""), "detail": str(p.get("detail") or "")})
    if not point_dicts:
        point_dicts = [_primary_conflict_from_metadata(metadata)]

    for conflict in point_dicts:
        gold: set[str] = set()
        if session_id and int(session_id) > 0:
            try:
                from app.db.session import session_scope

                with session_scope() as s:
                    gold, _ = load_gold_arbiter_matching(s, conflict)
            except Exception:
                _LOG.debug("v1294 gold ledger load skipped", exc_info=True)
        route = should_auto_resolve(
            conflict,
            conflict_weight=eff_w,
            gold_pattern_keys=gold or None,
            entropy_cap=_entropy_cap_from_runtime(),
            physics_meta_sink=meta_m,
        )
        if route == "USER":
            meta_m["pending_arbitration_queue_v1"] = []
            return out

    queue = list(meta_m.get("pending_arbitration_queue_v1") or []) if isinstance(meta_m.get("pending_arbitration_queue_v1"), list) else []
    if not queue:
        return out

    candidates = _candidate_plugins_from_inbox(physics_tensor)
    if len(candidates) < 2:
        meta_m["pending_arbitration_queue_v1"] = []
        return out

    interrupt_before = copy.deepcopy(interrupt) if isinstance(interrupt, dict) else {}
    flow_before = str(metadata.get("flow_state") or "").strip()
    batch_id = f"arb-batch-{uuid.uuid4().hex[:14]}"

    enriched: List[Dict[str, Any]] = []
    for item in queue:
        c = item.get("conflict") if isinstance(item.get("conflict"), dict) else {}
        conflict = {"kind": str(c.get("kind") or ""), "detail": str(c.get("detail") or "")}
        gb = "GOLD ledger (pattern union)"
        if session_id and int(session_id) > 0:
            try:
                from app.db.session import session_scope

                with session_scope() as s:
                    _, gb = load_gold_arbiter_matching(s, conflict)
            except Exception:
                pass
        sig = conflict_pattern_signature(conflict)
        summary = f"reason={reason}; entropy={eff_w:.3f}; spread={spread:.3f}; conflict={sig}"
        phys_ctx = build_arbitration_physics_context(
            metadata=metadata,
            physics_tensor=physics_tensor,
            conflict=conflict,
            routing_note=summary,
        )
        theme = build_arbitration_theme(conflict, candidates)
        enriched.append(
            {
                "conflict": conflict,
                "sig": sig,
                "gold_badge": gb,
                "phys_ctx": phys_ctx,
                "summary": summary,
                "theme": theme,
                "cname": conflict_display_name(conflict),
            }
        )

    batch_items = [
        {
            "conflict_summary": str(e.get("summary") or ""),
            "candidate_plugins": list(candidates),
            "conflict_context": dict(e.get("phys_ctx") or {}),
        }
        for e in enriched
    ]
    batch = await invoke_batch_conflict_arbiter_llm(client=client, items=batch_items, lang=lang)
    results = batch.get("results") if isinstance(batch.get("results"), list) else []
    if len(results) != len(enriched):
        meta_m["pending_arbitration_queue_v1"] = []
        _LOG.warning("v1298 batch arbiter length mismatch want=%s got=%s", len(enriched), len(results))
        return out

    for r in results:
        if isinstance(r, dict) and str(r.get("certainty") or "CONFIDENT").strip().upper() == "UNCERTAIN":
            _LOG.info("v1299 auto_llm UNCERTAIN; skip silent default_accept")
            return out

    audit_batch = batch.get("audit") if isinstance(batch.get("audit"), dict) else {}
    msgs = audit_batch.get("messages") if isinstance(audit_batch.get("messages"), list) else []
    safe_messages = [{"role": str(m.get("role") or ""), "content": str(m.get("content") or "")} for m in msgs if isinstance(m, dict)]
    raw_batch = str(batch.get("raw") or audit_batch.get("raw_response") or "")

    tree = out.get("assertion_tree") if isinstance(out.get("assertion_tree"), dict) else {}
    merged_tree: Dict[str, Any] = dict(tree)
    n_batch = len(enriched)
    plugin_ids_applied: List[str] = []

    for i, e in enumerate(enriched):
        r = results[i] if i < len(results) and isinstance(results[i], dict) else {}
        plugin_id = str(r.get("decision") or "").strip()
        reason_txt = str(r.get("reason") or "").strip() or "LLM 批量仲裁（静默）"
        if not plugin_id:
            meta_m["pending_arbitration_queue_v1"] = []
            _LOG.warning("v1298 batch arbiter empty decision at index=%s", i)
            return out
        plugin_ids_applied.append(plugin_id)
        sig = str(e.get("sig") or "")
        audit_id = f"arb-{uuid.uuid4().hex[:16]}"
        audit_bundle: Dict[str, Any] = {
            "arbitration_audit_id": audit_id,
            "arbitration_theme": str(e.get("theme") or ""),
            "prompt_messages": safe_messages,
            "candidate_plugins": list(candidates),
            "raw_llm_response": raw_batch,
            "raw_llm_reason": reason_txt,
            "gold_badge": str(e.get("gold_badge") or ""),
            "rollback_interrupt": interrupt_before,
            "rollback_flow_state": flow_before,
            "batch_id": batch_id,
            "batch_index": i,
            "batch_total": n_batch,
        }
        merged_tree = merge_silent_arbiter_into_assertion_tree(
            merged_tree,
            plugin_id=plugin_id,
            reason=reason_txt,
            conflict_signature=sig,
            audit_bundle=audit_bundle,
        )
        hist = merged_tree.get("silent_arbiter_history_v1") if isinstance(merged_tree.get("silent_arbiter_history_v1"), list) else []
        entry = hist[-1] if hist else {}
        law_nid = ""
        if isinstance(entry, dict):
            law_nid = str(entry.get("law_node_id") or "").strip()
            append_silent_arbiter_meta(meta_m, dict(entry))

        audit_entry = build_arbitration_audit_entry(
            conflict_name=str(e.get("cname") or ""),
            conflict_context=dict(e.get("phys_ctx") or {}),
            messages=safe_messages,
            raw_response=raw_batch,
            decision_plugin_id=plugin_id,
            reason=reason_txt,
            gold_badge=str(e.get("gold_badge") or ""),
            arbitration_theme=str(e.get("theme") or ""),
            candidate_plugins=candidates,
            law_node_id=law_nid,
            rollback_interrupt=interrupt_before,
            rollback_flow_state=flow_before,
            entry_id=audit_id,
            batch_id=batch_id,
            batch_index=i,
            batch_total=n_batch,
        )
        append_arbitration_audit_feed(meta_m, audit_entry)
        if session_id and int(session_id) > 0:
            try:
                from app.db.session import session_scope

                with session_scope() as s:
                    persist_arbitration_log_to_snapshot(s, consultation_id=int(session_id), entry=audit_entry)
            except Exception:
                _LOG.debug("v1295 arbitration_logs persist skipped", exc_info=True)

    meta_m["pending_arbitration_queue_v1"] = []
    cand_set = {str(x).strip() for x in candidates if str(x).strip()}
    inbox0 = meta_m.get("decision_inbox_v1") if isinstance(meta_m.get("decision_inbox_v1"), dict) else {}
    scores0 = inbox0.get("match_scores") if isinstance(inbox0.get("match_scores"), list) else []
    filtered_scores = [
        row
        for row in scores0
        if not (isinstance(row, dict) and str(row.get("plugin_id") or "").strip() in cand_set)
    ]
    meta_m["decision_inbox_v1"] = {**inbox0, "match_scores": filtered_scores}
    meta_m["auto_llm_default_accept_plugin_ids_v1"] = list(plugin_ids_applied)
    out["assertion_tree"] = merged_tree

    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    val = md.get("verdict_anchor_layer")
    if isinstance(val, dict):
        vac = dict(val)
        vac["assertion_tree"] = merged_tree
        md = dict(md)
        md["verdict_anchor_layer"] = vac
        out["metadata"] = md

    # 解除本轮 blocking：不向前端投递待确认 interrupt
    out["interrupt_request"] = {}
    active2 = dict(active)
    active2["block_mode"] = False
    active2["reason_code"] = "M3_AUTO_ARBITER_SILENT"
    active2["interrupt"] = None
    active2["probe_plan"] = [
        "V12.98：已通过黄金账本对齐 + 批量 LLM 静默裁决，跳过「确认卡片 / 选策略」弹窗。",
        f"批量 batch_id={batch_id}，共 {len(plugin_ids_applied)} 条冲突。",
        f"仲裁插件：{', '.join(plugin_ids_applied)}",
    ]
    out["active_probing"] = active2

    md_cur = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    if str(md_cur.get("flow_state") or "").strip().lower() == "probe_waiting":
        md_cur = dict(md_cur)
        md_cur["flow_state"] = "unknown"
        out["metadata"] = md_cur

    _LOG.info(
        "v1298 silent batch arbiter applied batch_id=%s count=%s session_id=%s",
        batch_id,
        len(plugin_ids_applied),
        session_id,
    )
    return out
