from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from v20.validation.knowledge_rule_library import build_knowledge_rule_validation_report


def build_rule_promotion_gate_report(domain: str = "", *, limit: int = 64) -> dict[str, object]:
    validation = build_knowledge_rule_validation_report(domain, limit=limit)
    packets = tuple(_packet_from_validation(row) for row in validation.get("definitions", ()) if isinstance(row, dict))
    lane_counts = Counter(str(row["review_lane"]) for row in packets)
    action_counts = Counter(str(row["recommended_action"]) for row in packets)
    return {
        "version": "v20.rule_promotion_gate_report.v1",
        "status": "ready" if packets else "empty",
        "domain": domain.strip(),
        "packet_count": len(packets),
        "runtime_promotion_candidate_count": sum(1 for row in packets if row["runtime_promotion_candidate"]),
        "shadow_weight_candidate_count": sum(1 for row in packets if row["shadow_weight_candidate"]),
        "blocked_count": sum(1 for row in packets if row["review_lane"].startswith("blocked")),
        "needs_subcondition_count": sum(1 for row in packets if row["review_lane"] == "needs_subcondition_split"),
        "lane_counts": dict(sorted(lane_counts.items())),
        "recommended_actions": dict(sorted(action_counts.items())),
        "packets": packets,
        "upstream": {
            "validation_status": validation.get("status", ""),
            "definition_count": validation.get("definition_count", 0),
            "synthetic_covered_count": validation.get("synthetic_covered_count", 0),
            "missing_synthetic_count": validation.get("missing_synthetic_count", 0),
        },
        "runtime_mutation": False,
        "guardrails": [
            "PROMOTION_GATE_IS_REVIEW_SIGNAL",
            "NO_AUTOMATIC_RUNTIME_RULE_ACTIVATION",
            "DECISION_REGISTRY_REQUIRED_FOR_ANY_PROMOTION",
            "HUMAN_REVIEWS_PACKETS_NOT_RAW_RULES",
        ],
    }


def build_rule_promotion_packet_summary(domain: str = "", *, limit: int = 64) -> dict[str, object]:
    gate = build_rule_promotion_gate_report(domain, limit=limit)
    packets = [row for row in gate.get("packets", ()) if isinstance(row, dict)]
    return {
        "version": "v20.rule_promotion_packet_summary.v1",
        "status": gate["status"],
        "domain": gate["domain"],
        "packet_count": gate["packet_count"],
        "runtime_promotion_candidate_count": gate["runtime_promotion_candidate_count"],
        "shadow_weight_candidate_count": gate["shadow_weight_candidate_count"],
        "blocked_count": gate["blocked_count"],
        "needs_subcondition_count": gate["needs_subcondition_count"],
        "lane_counts": gate["lane_counts"],
        "recommended_actions": gate["recommended_actions"],
        "packets": [
            {
                "packet_id": row["packet_id"],
                "domain": row["domain"],
                "source_knowledge_id": row["source_knowledge_id"],
                "portrait": row["portrait"],
                "question": row["question"],
                "review_lane": row["review_lane"],
                "recommended_action": row["recommended_action"],
                "human_decision_options": row["human_decision_options"],
                "risk": row["risk"],
            }
            for row in packets
        ],
        "runtime_mutation": False,
    }


def _packet_from_validation(row: dict[str, object]) -> dict[str, Any]:
    validation_state = str(row.get("validation_state", ""))
    review_lane = _review_lane(validation_state)
    recommended_action = _recommended_action(review_lane)
    packet_id = _packet_id(row)
    return {
        "version": "v20.rule_promotion_packet.v1",
        "packet_id": packet_id,
        "rule_key": row.get("rule_key", ""),
        "source_knowledge_id": row.get("source_knowledge_id", ""),
        "domain": row.get("domain", ""),
        "title": row.get("title", ""),
        "portrait": row.get("portrait", ""),
        "question": row.get("question", ""),
        "atom_count": row.get("atom_count", 0),
        "synthetic_state": row.get("synthetic_state", ""),
        "synthetic_case_count": row.get("synthetic_case_count", 0),
        "synthetic_confidence": row.get("synthetic_confidence", 0.0),
        "support_quality": row.get("support_quality", ""),
        "support_ratio": row.get("support_ratio", 0.0),
        "top_matched_feature_ids": row.get("top_matched_feature_ids", ()),
        "validation_state": validation_state,
        "review_lane": review_lane,
        "recommended_action": recommended_action,
        "human_decision_options": _human_decision_options(review_lane),
        "shadow_weight_candidate": review_lane == "candidate_for_shadow_weight_review",
        "runtime_promotion_candidate": False,
        "risk": _risk(row, review_lane),
        "decision_registry_required": True,
        "required_evidence_before_runtime": _required_evidence(review_lane),
        "guardrails": [
            "PACKET_IS_REVIEW_OBJECT",
            "NO_RUNTIME_ACTIVATION_FROM_PACKET",
            "HUMAN_OR_ADMIN_DECISION_REQUIRED",
        ],
    }


def _review_lane(validation_state: str) -> str:
    if validation_state == "blocked_by_contract_failure":
        return "blocked_contract_failure"
    if validation_state == "needs_synthetic_case":
        return "blocked_missing_synthetic_case"
    if validation_state == "needs_rule_or_case_fix":
        return "blocked_rule_or_case_mismatch"
    if validation_state == "synthetic_passed_needs_subconditions":
        return "needs_subcondition_split"
    if validation_state == "synthetic_passed_waiting_for_corpus_prior":
        return "waiting_for_corpus_prior"
    if validation_state == "shadow_validated_ready_for_review":
        return "candidate_for_shadow_weight_review"
    return "manual_review_required"


def _recommended_action(review_lane: str) -> str:
    actions = {
        "blocked_contract_failure": "fix_contract_before_any_review",
        "blocked_missing_synthetic_case": "generate_synthetic_case_then_revalidate",
        "blocked_rule_or_case_mismatch": "repair_rule_atoms_or_expected_case",
        "needs_subcondition_split": "split_rule_by_feature_signature_and_add_counterexamples",
        "waiting_for_corpus_prior": "build_or_import_corpus_prior",
        "candidate_for_shadow_weight_review": "create_decision_registry_review_for_shadow_weight",
        "manual_review_required": "manual_architect_review",
    }
    return actions.get(review_lane, "manual_architect_review")


def _human_decision_options(review_lane: str) -> tuple[str, ...]:
    if review_lane == "candidate_for_shadow_weight_review":
        return ("approve_shadow_weight", "request_more_cases", "defer", "reject")
    if review_lane == "needs_subcondition_split":
        return ("split_rule", "add_counterexample", "defer", "reject")
    if review_lane == "blocked_missing_synthetic_case":
        return ("generate_synthetic_case", "defer", "reject")
    if review_lane.startswith("blocked"):
        return ("fix", "defer", "reject")
    return ("review", "defer", "reject")


def _required_evidence(review_lane: str) -> tuple[str, ...]:
    common = ("DecisionRegistry record", "rollback plan", "runtime scope")
    if review_lane == "candidate_for_shadow_weight_review":
        return (*common, "shadow weight eval artifact")
    if review_lane == "needs_subcondition_split":
        return (*common, "subcondition candidates", "counterexample cases")
    if review_lane == "blocked_missing_synthetic_case":
        return (*common, "domain synthetic case")
    return common


def _risk(row: dict[str, object], review_lane: str) -> str:
    support_ratio = float(row.get("support_ratio", 0.0) or 0.0)
    domain = str(row.get("domain", ""))
    if review_lane.startswith("blocked"):
        return "high"
    if support_ratio >= 0.95:
        return "medium_high"
    if domain in {"career", "relationship", "health"}:
        return "medium"
    return "low"


def _packet_id(row: dict[str, object]) -> str:
    raw = "|".join(
        str(row.get(key, ""))
        for key in ("rule_key", "source_knowledge_id", "domain", "validation_state")
    )
    return f"v20.rule_promotion_packet.{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"
