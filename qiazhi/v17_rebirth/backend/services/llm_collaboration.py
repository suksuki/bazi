from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List


LLM_COLLABORATION_CONTRACT_VERSION = "v17.llm.collaboration.v1.0"
EVIDENCE_REVIEW_PROMPT_VERSION = "v17.evidence.review.v1.0"

REVIEW_ACTIONS = (
    "keep_strong",
    "keep_candidate",
    "downgrade_to_candidate",
    "ask_practitioner",
    "needs_more_evidence",
)


def _safe_str(value: Any, default: str = "") -> str:
    return str(value or "").strip() or default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _safe_list(value: Any) -> List[Any]:
    return [item for item in (value or []) if item is not None] if isinstance(value, list) else []


def _compact_evidence_items(items: Iterable[Dict[str, Any]], max_items: int = 12) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        evidence_id = _safe_str(raw.get("evidence_id") or raw.get("claim_id") or raw.get("title"))
        if not evidence_id:
            continue
        out.append(
            {
                "evidence_id": evidence_id,
                "claim_id": _safe_str(raw.get("claim_id")),
                "title": _safe_str(raw.get("title") or raw.get("summary"))[:160],
                "summary": _safe_str(raw.get("summary"))[:280],
                "source_plugin": _safe_str(raw.get("source_plugin")),
                "evidence_type": _safe_str(raw.get("evidence_type"), "diagnostic"),
                "target_god": _safe_str(raw.get("target_god")),
                "confidence": round(_safe_float(raw.get("confidence")), 4),
                "match_ratio": round(_safe_float(raw.get("match_ratio")), 4),
                "candidate_status": _safe_str(raw.get("candidate_status")),
                "observe_only": _safe_bool(raw.get("observe_only")),
                "detail_keys": [str(item) for item in _safe_list(raw.get("detail_keys"))[:8]],
            }
        )
        if len(out) >= max_items:
            break
    return out


def build_evidence_review_contract(
    *,
    items: List[Dict[str, Any]],
    summary: Dict[str, Any] | None = None,
    session_id: str = "",
    chart_fingerprint: str = "",
    verdict_text: str = "",
    reviewer_role: str = "user",
    max_items: int = 12,
) -> Dict[str, Any]:
    compact_items = _compact_evidence_items(items, max_items=max_items)
    safe_summary = summary if isinstance(summary, dict) else {}
    return {
        "prompt_contract_version": LLM_COLLABORATION_CONTRACT_VERSION,
        "task_type": "evidence_chain_review",
        "policy_version": EVIDENCE_REVIEW_PROMPT_VERSION,
        "session_id": _safe_str(session_id, "default"),
        "chart_fingerprint": _safe_str(chart_fingerprint),
        "reviewer_role": _safe_str(reviewer_role, "user"),
        "summary": {
            "total": int(_safe_float(safe_summary.get("total"), len(items))),
            "candidate_count": int(_safe_float(safe_summary.get("candidate_count"), 0)),
            "risk_count": int(_safe_float(safe_summary.get("risk_count"), 0)),
            "observe_only_count": int(_safe_float(safe_summary.get("observe_only_count"), 0)),
            "truncated": max(0, len(items) - len(compact_items)),
        },
        "verdict_text": _safe_str(verdict_text)[:600],
        "evidence_items": compact_items,
        "output_contract": {
            "review_version": "v17.evidence.review.result.v1",
            "overall_status_scope": ["supported", "mixed", "insufficient", "needs_practitioner"],
            "review_action_scope": list(REVIEW_ACTIONS),
            "required_item_fields": ["evidence_id", "review_action", "reason", "confidence", "risk_flags"],
            "confidence_range": "[0.0,1.0]",
            "output_format": "json",
            "fallback_when_unparseable": "needs_practitioner",
        },
    }


def build_evidence_review_prompt_text(contract: Dict[str, Any]) -> str:
    lines = [
        "你是 V17 证据链复核器（Reviewer），只输出结构化 JSON。",
        "任务：审阅 evidence_bundle，判断每条证据是否足以支撑强断语。",
        "边界：不得新增命理事实，不得改写物理层、参数、authority 或发布状态。",
        "输出仅为 JSON，不要附加解释文本、Markdown 或代码块。",
        "",
        "## Review Contract",
        json.dumps(contract, ensure_ascii=False, indent=2),
        "",
        "## Expected JSON",
        json.dumps(
            {
                "review_version": "v17.evidence.review.result.v1",
                "overall_status": "mixed",
                "items": [
                    {
                        "evidence_id": "example",
                        "review_action": "keep_candidate",
                        "reason": "证据可保留为候选，但不足以写成强断语。",
                        "confidence": 0.7,
                        "risk_flags": ["candidate_not_final"],
                    }
                ],
                "summary": {
                    "strong_count": 0,
                    "candidate_count": 1,
                    "risk_count": 0,
                    "practitioner_review_required": True,
                },
            },
            ensure_ascii=False,
        ),
    ]
    return "\n".join(lines).strip()


def build_evidence_review_draft(contract: Dict[str, Any]) -> Dict[str, Any]:
    rows = _safe_list(contract.get("evidence_items"))
    result_items: List[Dict[str, Any]] = []
    strong_count = 0
    candidate_count = 0
    risk_count = 0
    practitioner_required = False
    for row in rows:
        if not isinstance(row, dict):
            continue
        confidence = _safe_float(row.get("confidence"))
        match_ratio = _safe_float(row.get("match_ratio"))
        evidence_type = _safe_str(row.get("evidence_type"))
        candidate_status = _safe_str(row.get("candidate_status"))
        observe_only = _safe_bool(row.get("observe_only"))
        risk_flags: List[str] = []
        if observe_only:
            risk_flags.append("observe_only")
        if candidate_status and candidate_status not in {"confirmed", "accepted", "strong"}:
            risk_flags.append("candidate_not_final")
        if confidence and confidence < 0.55:
            risk_flags.append("low_confidence")
        if evidence_type in {"risk", "break_risk"}:
            risk_flags.append("risk_evidence")
            risk_count += 1
        if observe_only or "candidate_not_final" in risk_flags:
            action = "keep_candidate"
            reason = "证据适合保留为候选或观察项，暂不应写成强断语。"
            candidate_count += 1
        elif confidence >= 0.72 or match_ratio >= 0.72:
            action = "keep_strong"
            reason = "证据强度较高，可支撑较明确表达，但仍需保留来源。"
            strong_count += 1
        elif confidence <= 0.0 and match_ratio <= 0.0:
            action = "needs_more_evidence"
            reason = "当前证据缺少置信或命中指标，建议补充来源后再判断。"
            practitioner_required = True
        else:
            action = "ask_practitioner"
            reason = "证据处于中间态，建议由命理师结合盘面复核。"
            practitioner_required = True
            candidate_count += 1
        if action in {"ask_practitioner", "needs_more_evidence"}:
            practitioner_required = True
        result_items.append(
            {
                "evidence_id": _safe_str(row.get("evidence_id")),
                "review_action": action,
                "reason": reason,
                "confidence": round(max(confidence, match_ratio, 0.45 if action == "ask_practitioner" else 0.0), 3),
                "risk_flags": risk_flags,
            }
        )
    if not result_items:
        overall_status = "insufficient"
        practitioner_required = True
    elif practitioner_required:
        overall_status = "needs_practitioner"
    elif candidate_count or risk_count:
        overall_status = "mixed"
    else:
        overall_status = "supported"
    return {
        "review_version": "v17.evidence.review.result.v1",
        "overall_status": overall_status,
        "items": result_items,
        "summary": {
            "strong_count": strong_count,
            "candidate_count": candidate_count,
            "risk_count": risk_count,
            "practitioner_review_required": practitioner_required,
        },
    }
