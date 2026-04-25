from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from v17_rebirth.backend.services.decision_brain_protocol import DecisionBrainPlan, build_plan_claim
from v17_rebirth.backend.services.llm_prompt_contracts import build_plan_prompt_text
from v17_rebirth.backend.services.decision_batches import build_decision_batches


def safe_plan_ids(raw_ids: Any) -> List[str]:
    if isinstance(raw_ids, str):
        raw_ids = [raw_ids]
    if not isinstance(raw_ids, list):
        return []
    out: List[str] = []
    for item in raw_ids:
        sid = str(item or "").strip()
        if sid and sid not in out:
            out.append(sid)
    return out


def is_plan_terminal(status: str) -> bool:
    normalized = str(status or "").strip().upper()
    return normalized in {"COMMITTED", "REJECTED", "FAILED", "DONE"}


def are_decisions_settled(rows: List[Dict[str, Any]]) -> bool:
    if not rows:
        return False
    terminal_states = {"APPROVED", "REJECTED", "COMMITTED", "FAILED", "DONE"}
    for row in rows:
        if str(row.get("status") or "").strip().upper() not in terminal_states:
            return False
    return True


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def build_plan_claim_proxy(*, routing: str, routing_reason: str, routing_features: Dict[str, Any]) -> Dict[str, Any]:
    claim = build_plan_claim(
        routing=routing,
        routing_reason=routing_reason,
        routing_features={
            "decision_count": int(routing_features.get("decision_count") or 0),
            "conflict_pairs": int(routing_features.get("conflict_pairs") or 0),
            "duplicate_events": int(routing_features.get("duplicate_events") or 0),
            "max_abs_ratio": safe_float(routing_features.get("max_abs_ratio"), 0.0),
            "total_abs_ratio": safe_float(routing_features.get("total_abs_ratio"), 0.0),
        },
    )
    claim["routing_reason"] = routing_reason
    return claim


def decision_route_reason(
    payload: Dict[str, Any],
    rows: List[Dict[str, Any]],
    *,
    plan_auto_approve_max_count: int = 8,
    plan_auto_approve_max_ratio: float = 0.18,
    plan_auto_approve_max_sum: float = 1.0,
) -> Dict[str, Any]:
    explicit = str(payload.get("routing") or payload.get("route") or payload.get("routing_hint") or "").strip().lower()
    if explicit in {"system", "llm", "user"}:
        routing_reason = "payload routing_hint has explicit route"
        routing_features = {}
        return {
            "routing": explicit,
            "routing_reason": routing_reason,
            "routing_policy": "explicit_payload_routing",
            "routing_features": routing_features,
            "routing_claim": build_plan_claim_proxy(
                routing=explicit,
                routing_reason=routing_reason,
                routing_features=routing_features,
            ),
        }

    total_abs = 0.0
    max_abs = 0.0
    conflict_pairs = 0
    duplicate_events = 0
    target_by_sign: Dict[str, set[float]] = {}
    exclusivity_count: Dict[str, int] = {}
    decision_count = len(rows)

    for row in rows:
        impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
        ratio = safe_float(impact.get("impact_ratio", 0.0), 0.0)
        abs_ratio = abs(ratio)
        total_abs += abs_ratio
        max_abs = max(max_abs, abs_ratio)

        target = str(row.get("target_god") or impact.get("target_god") or "").strip() or "untargeted"
        target_by_sign.setdefault(target, set()).add(-1.0 if ratio < 0 else 1.0 if ratio > 0 else 0.0)

        event_key = str(row.get("exclusivity_key") or row.get("source_event") or "").strip()
        if event_key:
            exclusivity_count[event_key] = exclusivity_count.get(event_key, 0) + 1

        text = str(row.get("label") or row.get("title") or row.get("hint") or "").strip()
        if any(keyword in text for keyword in ("格局", "坍塌", "翻盘", "断裂", "冲", "刑", "害", "破", "夺", "离", "转化")):
            total_abs += 0.03

    for value in target_by_sign.values():
        signs = {item for item in value if item != 0.0}
        if len(signs) >= 2:
            conflict_pairs += 1

    duplicate_events = sum(1 for count in exclusivity_count.values() if count > 1)
    conflict_signal = conflict_pairs > 0 or duplicate_events > 0
    ratio_sum = safe_float(
        sum(safe_float((row.get("physical_impact") or {}).get("impact_ratio", 0.0), 0.0) for row in rows),
        0.0,
    )

    if not conflict_signal and decision_count <= plan_auto_approve_max_count and max_abs <= plan_auto_approve_max_ratio and abs(ratio_sum) <= plan_auto_approve_max_sum:
        routing = "system"
        reason = "low risk and低冲突批次，系统可自动执行"
    elif not conflict_signal and max_abs <= max(plan_auto_approve_max_ratio * 1.8, 0.25):
        routing = "llm"
        reason = "中等风险批次，先交由模型进行价值校验"
    else:
        routing = "user"
        reason = "高风险/冲突批次，建议人工裁定"

    routing_features = {
        "decision_count": decision_count,
        "conflict_pairs": conflict_pairs,
        "duplicate_events": duplicate_events,
        "max_abs_ratio": round(max_abs, 4),
        "total_abs_ratio": round(total_abs, 4),
        "net_ratio": round(ratio_sum, 4),
    }

    return {
        "routing": routing,
        "routing_reason": reason,
        "routing_policy": "local_batch_heuristic",
        "routing_features": routing_features,
        "routing_claim": build_plan_claim_proxy(
            routing=routing,
            routing_reason=reason,
            routing_features=routing_features,
        ),
    }


def build_llm_plan_prompt(*, rows: List[Dict[str, Any]], action: str, anchor: str, output_language: str = "zh") -> str:
    if not rows:
        if output_language == "en":
            return "No executable candidates were found, so no batch prompt can be generated."
        if output_language == "ko":
            return "실행 가능한 후보가 없어 배치 프롬프트를 생성할 수 없습니다."
        return "未检测到可执行候选，无法生成批量提示词。"
    return build_plan_prompt_text(rows=rows, action=action, anchor=anchor, max_rows=16, output_language=output_language)


def safe_decision_label(row: Dict[str, Any]) -> str:
    return str(row.get("label") or row.get("title") or row.get("hint") or row.get("id") or "").strip()


def safe_decision_trace(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build compact evidence bundles so plan 结算过程可追溯，不依赖 LLM 回答文本。"""
    out: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        label = safe_decision_label(row)
        if not label and not str(row.get("id") or "").strip():
            continue
        target = str(
            row.get("target_god")
            or (row.get("physical_impact") or {}).get("target_god")
            or ""
        ).strip()
        impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
        try:
            impact_ratio = float(impact.get("impact_ratio", 0.0) or 0.0)
        except (TypeError, ValueError):
            impact_ratio = 0.0
        try:
            priority = float(row.get("priority", 0.0) or 0.0)
        except (TypeError, ValueError):
            priority = 0.0
        out.append(
            {
                "trace_index": idx,
                "decision_id": str(row.get("id") or f"row_{idx}").strip(),
                "label": label,
                "source": str(row.get("source") or row.get("plugin_id") or "unknown").strip(),
                "target_god": target,
                "impact_ratio": round(impact_ratio, 6),
                "priority": round(priority, 6),
                "exclusivity_key": str(row.get("exclusivity_key") or "").strip(),
                "routing_hint": str(row.get("arbiter_type") or "user").strip(),
                "source_event": str(row.get("source_event") or "").strip(),
            }
        )
    return out


def boolish(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    raw = str(value).strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


def build_physics_sync_payload(pt: Dict[str, Any]) -> Dict[str, Any]:
    auto_resolutions = [dict(x) for x in pt.get("auto_resolutions", []) if isinstance(x, dict)]
    llm_arbitration_context = [dict(x) for x in pt.get("llm_arbitration_context", []) if isinstance(x, dict)]
    auto_decisions = [dict(x) for x in pt.get("auto_decisions", []) if isinstance(x, dict)]
    if not auto_decisions:
        auto_decisions = [*auto_resolutions, *llm_arbitration_context]
    payload: Dict[str, Any] = {
        "type": "PHYSICS_SYNC",
        "decision_inbox_contract": str(pt.get("decision_inbox_contract") or "v17.decision.inbox.v2"),
        "pending_decisions": [dict(x) for x in pt.get("pending_decisions", []) if isinstance(x, dict)],
        "manual_decisions": [dict(x) for x in pt.get("manual_decisions", []) if isinstance(x, dict)],
        "manual_inbox": [dict(x) for x in pt.get("manual_decisions", []) if isinstance(x, dict)],
        "auto_decisions": auto_decisions,
        "auto_resolutions": auto_resolutions,
        "llm_arbitration_context": llm_arbitration_context,
        "decision_brain_state": dict(pt.get("decision_brain_state") or {}),
        "decision_batches": [dict(x) for x in pt.get("decision_batches_cache", []) if isinstance(x, dict)],
    }
    return payload


def event_for_publish(event: Dict[str, Any], *, physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(event)
    request_verdict = boolish(out.get("request_verdict"), default=True)
    if request_verdict:
        return out
    out["signal"] = "PHYSICS_SYNC"
    out["payload"] = build_physics_sync_payload(physics_tensor)
    return out


def read_plan_state(pt: Dict[str, Any], decision_brain_key: str, plan_queue_key: str) -> Dict[str, Any]:
    raw = pt.get(decision_brain_key)
    if isinstance(raw, dict):
        plans = raw.get(plan_queue_key)
        if isinstance(plans, list):
            return {plan_queue_key: [dict(x) for x in plans if isinstance(x, dict)]}
    return {plan_queue_key: []}


def find_plan_by_id(pt: Dict[str, Any], plan_id: str, *, decision_brain_key: str, plan_queue_key: str) -> Optional[Dict[str, Any]]:
    normalized = str(plan_id or "").strip()
    if not normalized:
        return None
    state = read_plan_state(pt, decision_brain_key=decision_brain_key, plan_queue_key=plan_queue_key)
    rows = state.get(plan_queue_key)
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("plan_id") or "").strip() == normalized:
            return row
    return None


def write_plan_state(pt: Dict[str, Any], *, plan: DecisionBrainPlan, decision_brain_key: str, plan_queue_key: str, max_queue: int) -> None:
    state = read_plan_state(pt, decision_brain_key=decision_brain_key, plan_queue_key=plan_queue_key)
    plans = state.get(plan_queue_key)
    if not isinstance(plans, list):
        plans = []
    replaced = False
    for idx, row in enumerate(plans):
        if str(row.get("plan_id") or "").strip() == str(plan.plan_id):
            plans[idx] = plan.to_dict()
            replaced = True
            break
    if not replaced:
        plans.insert(0, plan.to_dict())
    if len(plans) > int(max_queue):
        plans = plans[: int(max_queue)]
    pt[decision_brain_key] = {plan_queue_key: plans}


def pick_pending_decisions(pt: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = pt.get("pending_decisions")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    manual = pt.get("manual_decisions")
    if isinstance(manual, list):
        return [row for row in manual if isinstance(row, dict)]
    return []


def index_pending_decisions(pt: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    rows = pick_pending_decisions(pt)
    by_id: Dict[str, Dict[str, Dict[str, Any]]] = {}
    by_label: Dict[str, Dict[str, Dict[str, Any]]] = {}
    by_title: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for row in rows:
        rid = str(row.get("id") or "").strip()
        label = str(row.get("label") or row.get("title") or "").strip()
        title = str(row.get("title") or "").strip()
        if rid:
            by_id[rid] = row
        if label:
            by_label[label] = row
        if title:
            by_title[title] = row
    return {"id": by_id, "label": by_label, "title": by_title}


def collect_matched_decisions(
    pt: Dict[str, Any],
    *,
    decision_ids: List[str] | None = None,
    decision_labels: List[str] | None = None,
) -> List[Dict[str, Any]]:
    ids = safe_plan_ids(decision_ids or [])
    labels = safe_plan_ids(decision_labels or [])
    if not ids and not labels:
        return []
    idx = index_pending_decisions(pt)
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _append(row: Dict[str, Any]) -> None:
        rid = str(row.get("id") or row.get("label") or row.get("title") or "").strip()
        if not rid or rid in seen:
            return
        seen.add(rid)
        out.append(row)

    for sid in ids:
        candidate = idx["id"].get(sid)
        if candidate:
            _append(candidate)
        candidate = idx["label"].get(sid)
        if candidate:
            _append(candidate)
        candidate = idx["title"].get(sid)
        if candidate:
            _append(candidate)

    for lab in labels:
        candidate = idx["label"].get(lab)
        if candidate:
            _append(candidate)
            continue
        candidate = idx["title"].get(lab)
        if candidate:
            _append(candidate)
    return out


def resolve_target(row: Dict[str, Any], *, fallback_target: str = "") -> str:
    if not isinstance(row, dict):
        return ""
    candidate = str(row.get("target_god") or "").strip()
    if candidate:
        return candidate
    impact = row.get("physical_impact")
    if isinstance(impact, dict):
        candidate = str(impact.get("target_god") or "").strip()
        if candidate:
            return candidate
    return str(fallback_target or "").strip()


def fallback_match_pending_decisions(
    pt: Dict[str, Any],
    *,
    action: str,
    fallback_target: str,
    source_hint: str,
) -> List[Dict[str, Any]]:
    rows = pick_pending_decisions(pt)
    if not rows:
        return []

    normalized_target = str(fallback_target or "").strip()
    normalized_action = str(action or "").strip().lower()
    source_hint_norm = str(source_hint or "").strip().lower()

    candidates: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or "").strip().upper()
        if status in {"APPROVED", "REJECTED", "COMMITTED", "FAILED", "DONE"}:
            continue
        row_target = resolve_target(row, fallback_target=normalized_target)
        if normalized_target and row_target != normalized_target:
            continue

        label = str(row.get("label") or "").strip().lower()
        title = str(row.get("title") or "").strip().lower()
        source = str(row.get("source") or "").strip().lower()
        if not normalized_action:
            candidates.append(row)
            continue

        action_match = (
            normalized_action in label
            or normalized_action in title
            or label in normalized_action
            or title in normalized_action
            or source_hint_norm and source_hint_norm in source
            or source in source_hint_norm
        )
        if action_match:
            candidates.append(row)

    deduped: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for row in candidates:
        rid = str(row.get("id") or row.get("label") or row.get("title") or "").strip()
        if rid and rid in seen_ids:
            continue
        if rid:
            seen_ids.add(rid)
        deduped.append(row)
    return deduped


def resolve_batch_decisions(pt: Dict[str, Any], batch_ids: List[str]) -> List[Dict[str, Any]]:
    if not batch_ids:
        return []
    cache = pt.get("decision_batches_cache")
    if not isinstance(cache, list):
        return []
    rows = []
    for item in cache:
        if not isinstance(item, dict):
            continue
        batch_id = str(item.get("batch_id") or "").strip()
        if batch_id not in batch_ids:
            continue
        rows.extend(safe_plan_ids(item.get("decision_ids")))
    return collect_matched_decisions(pt, decision_ids=rows)


def impact_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, float] = {}
    for row in rows:
        impact = row.get("physical_impact")
        if not isinstance(impact, dict):
            impact = {}
        ratio = float(impact.get("impact_ratio", 0.0) or 0.0)
        target = str(row.get("target_god") or impact.get("target_god") or "untargeted").strip()
        out[target] = out.get(target, 0.0) + ratio
    return {key: round(value, 6) for key, value in out.items()}


def seed_plan_from_payload(
    payload: Dict[str, Any],
    *,
    session_id: str,
    rows: List[Dict[str, Any]],
    signal: str,
    auto_approve_max: int = 8,
    plan_auto_count: int = 8,
) -> DecisionBrainPlan:
    route = decision_route_reason(payload, rows) if signal == "PLAN_SUBMIT" else {}
    effective_routing = str(
        route.get("routing") or payload.get("routing") or payload.get("route") or "system"
    ).strip().lower()
    if effective_routing not in {"system", "llm", "user"}:
        effective_routing = "system"
    if signal in {"PLAN_APPROVE", "PLAN_REJECT", "PLAN_ESCALATE", "PLAN_WITHDRAW"} and effective_routing == "system":
        # 人工确认的 plan 按执行路径处理时，明确标记为 system，避免被后续策略误判成非执行。
        effective_routing = "system"
    action = str(payload.get("action") or "").strip()
    if not action and rows:
        action = str(rows[0].get("label") or rows[0].get("title") or "").strip()
    anchor = str(payload.get("anchor") or "").strip()
    if not anchor and rows:
        anchor = str(rows[0].get("exclusivity_key") or rows[0].get("source_event") or rows[0].get("source") or "").strip()
    if not anchor:
        anchor = str(payload.get("source") or "manual").strip() or "manual"
    decision_ids = safe_plan_ids(payload.get("decision_ids"))
    if not decision_ids:
        decision_id = str(payload.get("decision_id") or "").strip()
        if decision_id:
            decision_ids.append(decision_id)
    if not decision_ids:
        decision_ids = [str(r.get("id") or r.get("label") or r.get("title") or "").strip() for r in rows if str(r.get("id") or r.get("label") or r.get("title") or "").strip()]
    status = "DRAFT"
    if signal == "PLAN_APPROVE":
        status = "APPROVED"
    elif signal == "PLAN_REJECT":
        status = "REJECTED"
    elif signal in {"PLAN_ESCALATE", "PLAN_WITHDRAW"}:
        status = "AWAIT_REVIEW"
    elif signal == "PLAN_SUBMIT":
        status = "AWAIT_REVIEW"
    return DecisionBrainPlan.from_dict(
        {
            "plan_id": str(payload.get("plan_id") or f"plan_{int(datetime.now(timezone.utc).timestamp() * 1000)}"),
            "anchor": anchor,
            "batch_ids": safe_plan_ids(payload.get("batch_ids") or payload.get("batch_id")),
            "routing": effective_routing,
            "creator": str(payload.get("creator") or "user").strip() or "user",
            "status": status,
            "impact_summary": impact_summary(rows),
            "residual_estimate": float(payload.get("residual_estimate") or 0.0),
            "meta": {
                "signal": signal,
                "action": action,
                "source": str(payload.get("source") or "oracle"),
                "rows": len(rows),
                "decision_ids": decision_ids,
                "routing_reason": route.get("routing_reason"),
                "routing_policy": route.get("routing_policy"),
                "routing_features": route.get("routing_features"),
                "routing_claim": route.get("routing_claim"),
                "decision_trace": safe_decision_trace(rows),
                "decision_trace_contract": "v17.decision.trace.v1",
                "decision_count": len(rows),
            },
            "session_id": session_id,
        },
        session_id=session_id,
    )


def mark_plan_decisions(pt: Dict[str, Any], rows: List[Dict[str, Any]], *, status: str, plan_id: str) -> None:
    row_ids = {str(r.get("id") or "").strip() for r in rows if str(r.get("id") or "").strip()}
    if not row_ids:
        return
    for name in ("pending_decisions", "manual_decisions"):
        section = pt.get(name)
        if not isinstance(section, list):
            continue
        for row in section:
            rid = str(row.get("id") or "").strip()
            if rid and rid in row_ids:
                row["status"] = status
                row["plan_id"] = plan_id


def emit_decision_batch_cache(pt: Dict[str, Any]) -> None:
    arbitration = {
        "manual_decisions": [dict(x) for x in pick_pending_decisions(pt)],
        "auto_resolutions": [dict(x) for x in pt.get("auto_resolutions", []) if isinstance(x, dict)],
        "llm_arbitration_context": [dict(x) for x in pt.get("llm_arbitration_context", []) if isinstance(x, dict)],
    }
    pt["decision_batches_cache"] = build_decision_batches(arbitration=arbitration).get("all", [])


def normalize_plan_signal(payload_signal: str, status: str) -> str:
    direct = str(payload_signal or "").strip().upper()
    if direct in {"PLAN_SUBMIT", "PLAN_APPROVE", "PLAN_REJECT", "PLAN_ESCALATE", "PLAN_WITHDRAW"}:
        return direct
    if direct == "ACTION_TAKEN":
        if str(status or "").strip().upper() == "REJECTED":
            return "PLAN_REJECT"
        return "PLAN_APPROVE"
    return "PLAN_SUBMIT"
