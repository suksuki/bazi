from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from v20.learning.rule_subcondition_split import build_rule_subcondition_split_report
from v20.validation.knowledge_rule_library import build_knowledge_rule_validation_report


def build_rule_activation_report(domain: str = "", *, limit: int = 0) -> dict[str, object]:
    validation = build_knowledge_rule_validation_report(domain, limit=limit)
    split = build_rule_subcondition_split_report(domain, limit=limit)
    split_by_rule_key = {
        str(row.get("rule_key", "")): row
        for row in split.get("packets", ())
        if isinstance(row, dict) and row.get("rule_key")
    }
    packets = tuple(
        _packet_from_validation(row, split_by_rule_key.get(str(row.get("rule_key", "")), {}))
        for row in validation.get("definitions", ())
        if isinstance(row, dict)
    )
    lane_counts = Counter(str(row["activation_lane"]) for row in packets)
    action_counts = Counter(str(row["iteration_action"]) for row in packets)
    return {
        "version": "v20.rule_activation_report.v1",
        "status": "ready" if packets else "empty",
        "domain": domain.strip(),
        "packet_count": len(packets),
        "runtime_activation_candidate_count": sum(1 for row in packets if row["runtime_activation_candidate"]),
        "active_weight_candidate_count": sum(1 for row in packets if row["active_weight_candidate"]),
        "blocked_count": sum(1 for row in packets if row["activation_lane"].startswith("blocked")),
        "needs_subcondition_count": sum(1 for row in packets if row["activation_lane"] == "needs_subcondition_split"),
        "subcondition_active_ready_count": sum(1 for row in packets if row["activation_lane"] == "subcondition_active_ready"),
        "lane_counts": dict(sorted(lane_counts.items())),
        "iteration_actions": dict(sorted(action_counts.items())),
        "packets": packets,
        "upstream": {
            "validation_status": validation.get("status", ""),
            "definition_count": validation.get("definition_count", 0),
            "synthetic_covered_count": validation.get("synthetic_covered_count", 0),
            "missing_synthetic_count": validation.get("missing_synthetic_count", 0),
            "subcondition_split_status": split.get("status", ""),
            "subcondition_packet_count": split.get("packet_count", 0),
            "subcondition_count": split.get("subcondition_count", 0),
        },
        "runtime_mutation": False,
        "guardrails": [
            "RULE_ACTIVATION_IS_ITERATION_SIGNAL",
            "RULES_ACTIVATE_AND_ITERATE_CONTINUOUSLY",
            "DECISION_REGISTRY_RECORDS_ITERATION_HISTORY",
            "SYSTEM_ACTIVATES_PACKETS_AND_RECORDS_FEEDBACK",
        ],
    }


def build_rule_activation_packet_summary(domain: str = "", *, limit: int = 0) -> dict[str, object]:
    gate = build_rule_activation_report(domain, limit=limit)
    packets = [row for row in gate.get("packets", ()) if isinstance(row, dict)]
    return {
        "version": "v20.rule_activation_packet_summary.v1",
        "status": gate["status"],
        "domain": gate["domain"],
        "packet_count": gate["packet_count"],
        "runtime_activation_candidate_count": gate["runtime_activation_candidate_count"],
        "active_weight_candidate_count": gate["active_weight_candidate_count"],
        "blocked_count": gate["blocked_count"],
        "needs_subcondition_count": gate["needs_subcondition_count"],
        "subcondition_active_ready_count": gate["subcondition_active_ready_count"],
        "lane_counts": gate["lane_counts"],
        "iteration_actions": gate["iteration_actions"],
        "packets": [
            {
                "packet_id": row["packet_id"],
                "domain": row["domain"],
                "source_knowledge_id": row["source_knowledge_id"],
                "portrait": row["portrait"],
                "question": row["question"],
                "activation_lane": row["activation_lane"],
                "iteration_action": row["iteration_action"],
                "iteration_options": row["iteration_options"],
                "subcondition_count": row.get("subcondition_count", 0),
                "counterexample_candidate_count": row.get("counterexample_candidate_count", 0),
                "risk": row["risk"],
            }
            for row in packets
        ],
        "runtime_mutation": False,
    }


def _packet_from_validation(row: dict[str, object], split_packet: dict[str, object]) -> dict[str, Any]:
    validation_state = str(row.get("validation_state", ""))
    activation_lane = _activation_lane(validation_state, split_packet)
    iteration_action = _iteration_action(activation_lane)
    packet_id = _packet_id(row)
    return {
        "version": "v20.rule_activation_packet.v1",
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
        "subcondition_count": len(split_packet.get("subconditions", ())) if split_packet else 0,
        "counterexample_candidate_count": len(split_packet.get("counterexample_candidates", ())) if split_packet else 0,
        "subcondition_packet_id": split_packet.get("packet_id", "") if split_packet else "",
        "subcondition_quality_status": (
            "ready"
            if split_packet
            and split_packet.get("corpus_state") in {"ready", "missing_corpus_training_fallback"}
            else "missing"
        ),
        "validation_state": validation_state,
        "activation_lane": activation_lane,
        "iteration_action": iteration_action,
        "iteration_options": _iteration_options(activation_lane),
        "active_weight_candidate": activation_lane == "active_weight_ready",
        "runtime_activation_candidate": True,
        "risk": _risk(row, activation_lane),
        "decision_registry_required": False,
        "required_evidence_before_runtime": _required_evidence(activation_lane),
        "guardrails": [
            "PACKET_IS_ACTIVE_RULE_OBJECT",
            "PACKET_FEEDS_ACTIVE_ITERATION",
            "SYSTEM_ITERATION_REQUIRED",
        ],
    }


def _activation_lane(validation_state: str, split_packet: dict[str, object]) -> str:
    if validation_state == "blocked_by_contract_failure":
        return "needs_contract_fix"
    if validation_state == "needs_synthetic_case":
        return "needs_synthetic_case"
    if validation_state == "needs_rule_or_case_fix":
        return "needs_rule_or_case_fix"
    if validation_state == "synthetic_passed_needs_subconditions":
        if split_packet and split_packet.get("subconditions"):
            return "subcondition_active_ready"
        return "needs_subcondition_split"
    if validation_state == "synthetic_passed_fallback_ready":
        if split_packet and split_packet.get("subconditions"):
            return "subcondition_active_ready"
        return "needs_subcondition_split"
    if validation_state == "synthetic_passed_waiting_for_corpus_prior":
        return "waiting_for_corpus_prior"
    if validation_state == "replay_validated_active_ready":
        return "active_weight_ready"
    return "system_iteration_required"


def _iteration_action(activation_lane: str) -> str:
    actions = {
        "needs_contract_fix": "fix_contract_for_active_iteration",
        "needs_synthetic_case": "generate_synthetic_case_then_revalidate",
        "needs_rule_or_case_fix": "repair_rule_atoms_or_expected_case",
        "needs_subcondition_split": "split_rule_by_feature_signature_and_add_counterexamples",
        "subcondition_active_ready": "activate_subconditions_for_replay_eval",
        "waiting_for_corpus_prior": "build_or_import_corpus_prior",
        "subcondition_fallback_ready": "activate_subconditions_for_replay_eval",
        "active_weight_ready": "activate_weight_and_record_iteration",
        "system_iteration_required": "system_iteration",
    }
    return actions.get(activation_lane, "system_iteration")


def _iteration_options(activation_lane: str) -> tuple[str, ...]:
    if activation_lane == "active_weight_ready":
        return ("activate_active_weight", "request_more_cases", "defer", "reject")
    if activation_lane == "needs_subcondition_split":
        return ("split_rule", "add_counterexample", "defer", "reject")
    if activation_lane == "subcondition_active_ready":
        return ("activate_subconditions_for_replay_eval", "add_counterexample", "split_again", "defer", "reject")
    if activation_lane == "subcondition_fallback_ready":
        return ("activate_subconditions_for_replay_eval", "add_counterexample", "split_again", "defer", "reject")
    if activation_lane == "needs_synthetic_case":
        return ("generate_synthetic_case", "defer", "reject")
    if activation_lane.startswith("blocked"):
        return ("fix", "defer", "reject")
    return ("system_iteration", "defer", "reject")


def _required_evidence(activation_lane: str) -> tuple[str, ...]:
    common = ("Iteration record", "runtime rollback note", "runtime scope")
    if activation_lane == "active_weight_ready":
        return (*common, "active weight replay artifact")
    if activation_lane == "needs_subcondition_split":
        return (*common, "subcondition candidates", "counterexample cases")
    if activation_lane == "subcondition_active_ready":
        return (*common, "active subcondition signals", "counterexample cases", "replay eval artifact")
    if activation_lane == "subcondition_fallback_ready":
        return (*common, "active subcondition signals", "fallback feature signature", "replay eval artifact")
    if activation_lane == "needs_synthetic_case":
        return (*common, "domain synthetic case")
    return common


def _risk(row: dict[str, object], activation_lane: str) -> str:
    support_ratio = float(row.get("support_ratio", 0.0) or 0.0)
    domain = str(row.get("domain", ""))
    if activation_lane.startswith("blocked"):
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
    return f"v20.rule_activation_packet.{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"
