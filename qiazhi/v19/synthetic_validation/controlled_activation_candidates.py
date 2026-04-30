from __future__ import annotations

from typing import Any, Dict, List

from v19.synthetic_validation.dry_run_shadow_scoring import build_p43_feedback_ledger


P44_CONTROLLED_ACTIVATION_PACKET_VERSION = "v19.p44.controlled_activation_packet.v1"
P44_ROLLBACK_MANIFEST_VERSION = "v19.p44.rollback_manifest.v1"
P44_RELEASE_CANDIDATE_REGRESSION_VERSION = "v19.p44.release_candidate_regression.v1"

P44_GUARDRAILS = [
    "P43_FEEDBACK_LEDGER_REQUIRED",
    "CONTROLLED_ACTIVATION_CANDIDATE_PACKET_ONLY",
    "R0_R1_DRY_RUN_PASSED_ONLY",
    "ROLLBACK_MANIFEST_REQUIRED",
    "ENGINE_DISABLED_UNTIL_RELEASE_EXECUTION",
    "NO_USER_ANSWER_MUTATION",
    "NO_RUNTIME_RULE_ACTIVATION",
]


def build_p44_controlled_activation_packet() -> Dict[str, Any]:
    ledger = build_p43_feedback_ledger()
    activation_candidates = [
        _activation_candidate(row)
        for row in ledger.get("items") or []
        if row.get("feedback_status") == "dry_run_passed" and row.get("risk_level") in {"R0", "R1"}
    ]
    shadow_hold = [
        _hold_candidate(row)
        for row in ledger.get("items") or []
        if row.get("feedback_status") == "shadow_scored"
    ]
    return {
        "ok": ledger.get("ok") is True,
        "version": P44_CONTROLLED_ACTIVATION_PACKET_VERSION,
        "status": "controlled_activation_packet_ready_no_runtime_activation",
        "summary": {
            "source_candidate_count": ledger["summary"]["candidate_count"],
            "activation_candidate_count": len(activation_candidates),
            "shadow_hold_count": len(shadow_hold),
            "ring0_canary_count": sum(1 for row in activation_candidates if row.get("release_ring") == "ring0_canary"),
            "ring1_internal_count": sum(1 for row in activation_candidates if row.get("release_ring") == "ring1_internal"),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "activation_updated_count": 0,
            "runtime_mutation": False,
            "by_topic_lane": _count_by(activation_candidates, "topic_lane"),
            "shadow_hold_by_topic_lane": _count_by(shadow_hold, "topic_lane"),
        },
        "activation_candidates": activation_candidates,
        "shadow_hold": shadow_hold,
        "release_policy": {
            "ring0_canary": "R0 dry-run passed candidates may enter the smallest controlled release ring later.",
            "ring1_internal": "R1 dry-run passed candidates are internal-release candidates only.",
            "shadow_hold": "R2 candidates remain shadow scored and cannot enter controlled release yet.",
        },
        "guardrails": P44_GUARDRAILS,
    }


def build_p44_rollback_manifest() -> Dict[str, Any]:
    packet = build_p44_controlled_activation_packet()
    rollback_items = [
        {
            "rollback_id": f"p44.rollback.{_slug(str(row.get('knowledge_id') or 'unknown'))}",
            "candidate_rule_id": row.get("candidate_rule_id"),
            "knowledge_id": row.get("knowledge_id"),
            "topic_lane": row.get("topic_lane"),
            "release_ring": row.get("release_ring"),
            "rollback_action": "disable_engine_and_remove_from_release_ring",
            "answer_mutation": False,
            "runtime_mutation": False,
        }
        for row in packet.get("activation_candidates") or []
    ]
    return {
        "ok": packet.get("ok") is True,
        "version": P44_ROLLBACK_MANIFEST_VERSION,
        "status": "rollback_manifest_ready_no_runtime_activation",
        "summary": {
            "activation_candidate_count": packet["summary"]["activation_candidate_count"],
            "rollback_item_count": len(rollback_items),
            "missing_rollback_count": packet["summary"]["activation_candidate_count"] - len(rollback_items),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "items": rollback_items,
        "guardrails": P44_GUARDRAILS,
    }


def run_p44_release_candidate_regression() -> Dict[str, Any]:
    packet = build_p44_controlled_activation_packet()
    rollback = build_p44_rollback_manifest()
    failures = []
    if packet.get("ok") is not True:
        failures.append({"failure_type": "p44_packet_not_ready", "detail": "Controlled activation packet is not ready."})
    if packet["summary"]["engine_enabled_count"] != 0:
        failures.append({"failure_type": "engine_activation_not_allowed", "detail": "P44 cannot enable engines."})
    if packet["summary"]["answer_mutation_count"] != 0:
        failures.append({"failure_type": "answer_mutation_not_allowed", "detail": "P44 cannot mutate user answers."})
    if rollback["summary"]["missing_rollback_count"] != 0:
        failures.append({"failure_type": "rollback_manifest_incomplete", "detail": "Every activation candidate requires rollback coverage."})
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P44_RELEASE_CANDIDATE_REGRESSION_VERSION,
        "status": status,
        "summary": {
            "activation_candidate_count": packet["summary"]["activation_candidate_count"],
            "shadow_hold_count": packet["summary"]["shadow_hold_count"],
            "ring0_canary_count": packet["summary"]["ring0_canary_count"],
            "ring1_internal_count": packet["summary"]["ring1_internal_count"],
            "rollback_item_count": rollback["summary"]["rollback_item_count"],
            "missing_rollback_count": rollback["summary"]["missing_rollback_count"],
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "activation_updated_count": 0,
            "runtime_mutation": False,
        },
        "activation_packet": packet,
        "rollback_manifest": rollback,
        "failures": failures,
        "guardrails": P44_GUARDRAILS,
    }


def _activation_candidate(row: Dict[str, Any]) -> Dict[str, Any]:
    risk = str(row.get("risk_level") or "R1")
    return {
        "activation_candidate_id": f"p44.activation.{_slug(str(row.get('knowledge_id') or 'unknown'))}",
        "candidate_rule_id": row.get("candidate_rule_id"),
        "knowledge_id": row.get("knowledge_id"),
        "topic_lane": row.get("topic_lane"),
        "risk_level": risk,
        "release_ring": "ring0_canary" if risk == "R0" else "ring1_internal",
        "engine_enabled": False,
        "answer_mutation": False,
        "runtime_mutation": False,
    }


def _hold_candidate(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "hold_id": f"p44.hold.{_slug(str(row.get('knowledge_id') or 'unknown'))}",
        "candidate_rule_id": row.get("candidate_rule_id"),
        "knowledge_id": row.get("knowledge_id"),
        "topic_lane": row.get("topic_lane"),
        "risk_level": row.get("risk_level"),
        "hold_reason": "r2_shadow_scoring_only_until_release_safety_review",
        "engine_enabled": False,
        "runtime_mutation": False,
    }


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_")


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
