from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from v17_rebirth.backend.services.llm_prompt_contracts import build_conflict_prompt_text


def _normalize_conflict_ids(value: Iterable[str] | None) -> List[str]:
    out: List[str] = []
    for raw_id in value or ():
        sid = str(raw_id or "").strip()
        if sid and sid not in out:
            out.append(sid)
    return out


def _read_indexed_rows(meta: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    return [dict(row) for row in (meta.get(key) or []) if isinstance(row, dict)]


def _normalize_single_resolution(raw_payload: Dict[str, Any]) -> Dict[str, Any]:
    winners = [str(cid).strip() for cid in (raw_payload.get("winner_claim_ids") or []) if str(cid).strip()]
    dropped = [
        str(cid).strip()
        for cid in (raw_payload.get("dropped_claim_ids") or [])
        if str(cid).strip() and str(cid).strip() not in winners
    ]
    resolution_type = str(raw_payload.get("resolution_type") or "context_only").strip() or "context_only"
    preferred_arbiter = str(raw_payload.get("preferred_arbiter") or "llm").strip() or "llm"
    try:
        confidence = float(raw_payload.get("confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    return {
        "resolution_type": resolution_type,
        "preferred_arbiter": preferred_arbiter,
        "winner_claim_ids": winners,
        "dropped_claim_ids": dropped,
        "reason": str(raw_payload.get("reason") or "").strip(),
        "confidence": max(0.0, min(1.0, confidence)),
    }


def build_conflict_bundle(*, meta: Dict[str, Any], conflict_id: str) -> Dict[str, Any]:
    return build_conflict_bundles(meta=meta, conflict_ids=[conflict_id])


def build_conflict_bundles(*, meta: Dict[str, Any], conflict_ids: Iterable[str]) -> Dict[str, Any]:
    claims = _read_indexed_rows(meta, "plugin_claims")
    conflicts = [dict(row) for row in (meta.get("plugin_conflicts") or []) if isinstance(row, dict)]
    resolutions = [dict(row) for row in (meta.get("plugin_conflict_resolutions") or []) if isinstance(row, dict)]
    knowledge_snapshot = dict(meta.get("knowledge_snapshot") or {}) if isinstance(meta.get("knowledge_snapshot"), dict) else {}

    target_ids = _normalize_conflict_ids(conflict_ids)
    by_id = {str(row.get("conflict_id") or "").strip(): row for row in conflicts}
    selected_conflicts: List[Dict[str, Any]] = [dict(by_id[cid]) for cid in target_ids if cid in by_id]
    claim_ids = sorted(
        {
            str(cid).strip()
            for conflict in selected_conflicts
            for cid in (conflict.get("claims") or [])
            if str(cid).strip()
        }
    )
    related_claims = [row for row in claims if str(row.get("claim_id") or "").strip() in claim_ids]
    related_resolutions = [
        row for row in resolutions if str(row.get("conflict_id") or "").strip() in target_ids
    ]
    return {
        "conflict_ids": target_ids,
        "conflicts": selected_conflicts,
        "claims": related_claims,
        "resolutions": related_resolutions,
        "knowledge_snapshot": knowledge_snapshot,
    }


def build_llm_conflict_prompt(*, bundle: Dict[str, Any], output_language: str = "zh") -> str:
    if not isinstance(bundle, dict):
        if output_language == "en":
            return "Only standard conflict bundle input is supported; arbitration prompt cannot be generated."
        if output_language == "ko":
            return "표준 충돌 묶음 입력만 지원하므로 중재 프롬프트를 생성할 수 없습니다."
        return "仅支持标准冲突包输入，无法生成仲裁提示。"
    return build_conflict_prompt_text(bundle=bundle, output_language=output_language)


def parse_llm_conflict_reply(*, reply: str, bundle: Dict[str, Any]) -> Dict[str, Any]:
    raw = str(reply or "").strip()
    conflicts = bundle.get("conflicts") if isinstance(bundle.get("conflicts"), list) else []
    conflict_ids = [str(row.get("conflict_id") or "").strip() for row in conflicts if str(row.get("conflict_id") or "").strip()]
    target_claim_ids = [
        str(row.get("claim_id") or "").strip()
        for row in (bundle.get("claims") or [])
        if isinstance(row, dict) and str(row.get("claim_id") or "").strip()
    ]
    if not raw:
        base = {
            "resolution_type": "context_only",
            "preferred_arbiter": "llm",
            "winner_claim_ids": [],
            "dropped_claim_ids": [],
            "reason": "LLM 未返回结构化内容，保留为上下文待复核。",
            "confidence": 0.0,
        }
        if len(conflict_ids) > 1:
            return {"results_by_conflict": {cid: dict(base) for cid in conflict_ids}}
        return base

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
        base = {
            "resolution_type": resolution_type,
            "preferred_arbiter": preferred_arbiter,
            "winner_claim_ids": target_claim_ids[:1],
            "dropped_claim_ids": target_claim_ids[1:],
            "reason": raw[:300],
            "confidence": 0.35,
        }
        if len(conflict_ids) > 1:
            return {"results_by_conflict": {cid: dict(base) for cid in conflict_ids}}
        return base

    if len(conflict_ids) > 1 and "results_by_conflict" in payload:
        raw_map = payload.get("results_by_conflict") if isinstance(payload.get("results_by_conflict"), dict) else {}
        parsed_map: Dict[str, Dict[str, Any]] = {}
        for conflict_id, raw_item in raw_map.items():
            sid = str(conflict_id or "").strip()
            if not sid:
                continue
            if not isinstance(raw_item, dict):
                continue
            normalized = _normalize_single_resolution(raw_item)
            parsed_map[sid] = normalized
        return {"results_by_conflict": parsed_map}

    parsed = _normalize_single_resolution(payload)
    if len(conflict_ids) <= 1:
        return parsed
    return {"results_by_conflict": {cid: dict(parsed) for cid in conflict_ids}}


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


def apply_llm_conflict_results(
    *,
    meta: Dict[str, Any],
    conflict_ids: List[str],
    bundle: Dict[str, Any],
    reply: str,
    parsed: Dict[str, Any],
) -> Dict[str, Any]:
    normalized_conflict_ids = _normalize_conflict_ids(conflict_ids)
    if not normalized_conflict_ids:
        return dict(meta or {})
    conflicts = [dict(row) for row in (bundle.get("conflicts") or []) if isinstance(row, dict)]
    conflicts_by_id = {str(row.get("conflict_id") or "").strip(): row for row in conflicts if str(row.get("conflict_id") or "").strip()}
    claims = [dict(row) for row in (bundle.get("claims") or []) if isinstance(row, dict)]
    all_resolutions = [dict(row) for row in (bundle.get("resolutions") or []) if isinstance(row, dict)]
    resolutions_by_conflict = {
        str(row.get("conflict_id") or "").strip(): row
        for row in all_resolutions
        if str(row.get("conflict_id") or "").strip()
    }
    knowledge_snapshot = dict(bundle.get("knowledge_snapshot") or {})
    results_by_conflict = parsed.get("results_by_conflict") if isinstance(parsed.get("results_by_conflict"), dict) else {}

    out = dict(meta or {})
    for conflict_id in normalized_conflict_ids:
        if conflict_id not in conflicts_by_id:
            continue
        row = results_by_conflict.get(conflict_id) if isinstance(results_by_conflict, dict) else None
        single_parsed = dict(row) if isinstance(row, dict) else dict(parsed)
        if "results_by_conflict" in single_parsed:
            del single_parsed["results_by_conflict"]
        if not single_parsed:
            single_parsed = {
                "resolution_type": "context_only",
                "preferred_arbiter": "llm",
                "winner_claim_ids": [],
                "dropped_claim_ids": [],
                "reason": "LLM 未返回该冲突结构化结果，转入上下文待复核。",
                "confidence": 0.0,
            }
        out = apply_llm_conflict_result(
            meta=out,
            conflict_id=conflict_id,
            bundle={
                "conflict_id": conflict_id,
                "conflicts": [dict(conflicts_by_id[conflict_id])],
                "claims": claims,
                "resolutions": (
                    [dict(row)] if (row := resolutions_by_conflict.get(conflict_id)) is not None else []
                ),
                "knowledge_snapshot": knowledge_snapshot,
            },
            reply=reply,
            parsed=single_parsed,
        )
    return out
