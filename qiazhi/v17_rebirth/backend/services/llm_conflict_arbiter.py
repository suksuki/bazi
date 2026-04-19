from __future__ import annotations

import json
from typing import Any, Dict, List


def build_conflict_bundle(*, meta: Dict[str, Any], conflict_id: str) -> Dict[str, Any]:
    claims = [dict(row) for row in (meta.get("plugin_claims") or []) if isinstance(row, dict)]
    conflicts = [dict(row) for row in (meta.get("plugin_conflicts") or []) if isinstance(row, dict)]
    resolutions = [dict(row) for row in (meta.get("plugin_conflict_resolutions") or []) if isinstance(row, dict)]
    knowledge_snapshot = dict(meta.get("knowledge_snapshot") or {}) if isinstance(meta.get("knowledge_snapshot"), dict) else {}

    target_conflict = next(
        (row for row in conflicts if str(row.get("conflict_id") or "").strip() == str(conflict_id or "").strip()),
        {},
    )
    claim_ids = [str(cid).strip() for cid in (target_conflict.get("claims") or []) if str(cid).strip()]
    related_claims = [row for row in claims if str(row.get("claim_id") or "").strip() in claim_ids]
    related_resolutions = [
        row for row in resolutions if str(row.get("conflict_id") or "").strip() == str(conflict_id or "").strip()
    ]
    return {
        "conflict": target_conflict,
        "claims": related_claims,
        "resolutions": related_resolutions,
        "knowledge_snapshot": knowledge_snapshot,
    }


def build_llm_conflict_prompt(*, bundle: Dict[str, Any]) -> str:
    conflict = bundle.get("conflict") if isinstance(bundle.get("conflict"), dict) else {}
    claims = bundle.get("claims") if isinstance(bundle.get("claims"), list) else []
    knowledge = bundle.get("knowledge_snapshot") if isinstance(bundle.get("knowledge_snapshot"), dict) else {}
    lines: List[str] = []
    lines.append("你是 V17 Brain 的冲突仲裁器。请阅读冲突包，并只输出 JSON。")
    lines.append("目标：给出 resolution_type、preferred_arbiter、winner_claim_ids、dropped_claim_ids、reason、confidence。")
    lines.append("resolution_type 仅可为 merge / reject / escalate_user / context_only。")
    lines.append("preferred_arbiter 仅可为 system / llm / user。")
    lines.append("")
    lines.append("## Conflict")
    lines.append(json.dumps(conflict, ensure_ascii=False, indent=2))
    lines.append("")
    lines.append("## Claims")
    lines.append(json.dumps(claims, ensure_ascii=False, indent=2))
    lines.append("")
    lines.append("## Knowledge Snapshot")
    lines.append(json.dumps(knowledge, ensure_ascii=False, indent=2))
    lines.append("")
    lines.append("仅输出 JSON，不要附加解释。")
    return "\n".join(lines)


def parse_llm_conflict_reply(*, reply: str, bundle: Dict[str, Any]) -> Dict[str, Any]:
    raw = str(reply or "").strip()
    target_claim_ids = [
        str(row.get("claim_id") or "").strip()
        for row in (bundle.get("claims") or [])
        if isinstance(row, dict) and str(row.get("claim_id") or "").strip()
    ]
    if not raw:
        return {
            "resolution_type": "context_only",
            "preferred_arbiter": "llm",
            "winner_claim_ids": [],
            "dropped_claim_ids": [],
            "reason": "LLM 未返回结构化内容，保留为上下文待复核。",
            "confidence": 0.0,
        }

    payload: Dict[str, Any] | None = None
    for candidate in (raw, raw.strip("`"), raw.replace("```json", "").replace("```", "").strip()):
        try:
            loaded = json.loads(candidate)
            if isinstance(loaded, dict):
                payload = loaded
                break
        except Exception:
            continue

    if payload is None:
        lowered = raw.lower()
        if "user" in lowered or "人工" in raw or "升级" in raw:
            resolution_type = "escalate_user"
            preferred_arbiter = "user"
        elif "reject" in lowered or "驳回" in raw:
            resolution_type = "reject"
            preferred_arbiter = "llm"
        else:
            resolution_type = "merge"
            preferred_arbiter = "system"
        return {
            "resolution_type": resolution_type,
            "preferred_arbiter": preferred_arbiter,
            "winner_claim_ids": target_claim_ids[:1],
            "dropped_claim_ids": target_claim_ids[1:],
            "reason": raw[:300],
            "confidence": 0.35,
        }

    winners = [
        str(cid).strip()
        for cid in (payload.get("winner_claim_ids") or [])
        if str(cid).strip() in target_claim_ids
    ]
    dropped = [
        str(cid).strip()
        for cid in (payload.get("dropped_claim_ids") or [])
        if str(cid).strip() in target_claim_ids and str(cid).strip() not in winners
    ]
    resolution_type = str(payload.get("resolution_type") or "context_only").strip() or "context_only"
    preferred_arbiter = str(payload.get("preferred_arbiter") or "llm").strip() or "llm"
    try:
        confidence = float(payload.get("confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    return {
        "resolution_type": resolution_type,
        "preferred_arbiter": preferred_arbiter,
        "winner_claim_ids": winners,
        "dropped_claim_ids": dropped,
        "reason": str(payload.get("reason") or "").strip(),
        "confidence": max(0.0, min(1.0, confidence)),
    }


def apply_llm_conflict_result(
    *,
    meta: Dict[str, Any],
    conflict_id: str,
    bundle: Dict[str, Any],
    reply: str,
    parsed: Dict[str, Any],
) -> Dict[str, Any]:
    cloned = dict(meta or {})
    conflicts = [dict(row) for row in (cloned.get("plugin_conflicts") or []) if isinstance(row, dict)]
    resolutions = [dict(row) for row in (cloned.get("plugin_conflict_resolutions") or []) if isinstance(row, dict)]
    brain_actions = [dict(row) for row in (cloned.get("brain_action_queue") or []) if isinstance(row, dict)]

    next_queue = "llm"
    resolution_type = str(parsed.get("resolution_type") or "context_only").strip()
    preferred_arbiter = str(parsed.get("preferred_arbiter") or "llm").strip()
    if resolution_type == "merge" and preferred_arbiter == "system":
        next_queue = "system"
    elif resolution_type == "escalate_user" or preferred_arbiter == "user":
        next_queue = "user"

    for row in conflicts:
        if str(row.get("conflict_id") or "").strip() != str(conflict_id or "").strip():
            continue
        row["resolution_status"] = "resolved_llm"
        row["resolved_by"] = "llm"
        row["llm_resolution_type"] = resolution_type
        row["llm_preferred_arbiter"] = preferred_arbiter
        row["llm_confidence"] = float(parsed.get("confidence", 0.0) or 0.0)
        row["next_queue"] = next_queue
        break

    updated = False
    for row in resolutions:
        if str(row.get("conflict_id") or "").strip() != str(conflict_id or "").strip():
            continue
        row["status"] = "resolved_llm"
        row["resolved_by"] = "llm"
        row["llm_reply"] = str(reply or "").strip()
        row["llm_result"] = dict(parsed)
        row["winner_claim_ids"] = list(parsed.get("winner_claim_ids") or [])
        row["winner_claim_id"] = (parsed.get("winner_claim_ids") or [None])[0]
        row["dropped_claim_ids"] = list(parsed.get("dropped_claim_ids") or [])
        row["applied_to_settlement"] = False
        row["next_queue"] = next_queue
        updated = True

    if not updated:
        resolutions.append(
            {
                "resolution_id": f"llm:{conflict_id}",
                "conflict_id": str(conflict_id or "").strip(),
                "status": "resolved_llm",
                "resolved_by": "llm",
                "policy": "llm_conflict_bundle",
                "winner_claim_ids": list(parsed.get("winner_claim_ids") or []),
                "winner_claim_id": (parsed.get("winner_claim_ids") or [None])[0],
                "dropped_claim_ids": list(parsed.get("dropped_claim_ids") or []),
                "applied_to_settlement": False,
                "next_queue": next_queue,
                "llm_reply": str(reply or "").strip(),
                "llm_result": dict(parsed),
                "reason": str(parsed.get("reason") or "").strip(),
            }
        )

    brain_actions = [
        row
        for row in brain_actions
        if str(row.get("conflict_id") or "").strip() != str(conflict_id or "").strip()
    ]
    brain_actions.append(
        {
            "action_id": f"brain:{conflict_id}",
            "conflict_id": str(conflict_id or "").strip(),
            "action_type": (
                "system_merge_suggestion"
                if next_queue == "system"
                else "manual_escalation"
                if next_queue == "user"
                else "llm_context_hold"
            ),
            "queue": next_queue,
            "winner_claim_ids": list(parsed.get("winner_claim_ids") or []),
            "dropped_claim_ids": list(parsed.get("dropped_claim_ids") or []),
            "reason": str(parsed.get("reason") or "").strip(),
            "confidence": float(parsed.get("confidence", 0.0) or 0.0),
            "source_plugins": [
                str(row.get("plugin_id") or "").strip()
                for row in (bundle.get("claims") or [])
                if isinstance(row, dict) and str(row.get("plugin_id") or "").strip()
            ][:6],
        }
    )

    cloned["plugin_conflicts"] = conflicts
    cloned["plugin_conflict_resolutions"] = resolutions
    cloned["brain_action_queue"] = brain_actions
    return cloned
