from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

from v19.agent import build_agent_turn
from v19.agent.income_stability import derive_income_stability
from v19.runtime import RUNTIME, _postgres_connection, resolve_postgres_url, utc_now
from v19.bazi_source_archive import create_knowledge_draft, list_knowledge_drafts
from v19.synthetic_validation.guided_cases import P11_GUIDED_SYNTHETIC_CASES, make_synthetic_chart
from v19.synthetic_validation.guided_runner import run_guided_synthetic_collision

LAB_FILE = RUNTIME / "lab_interfaces.json"
LAB_VERSION = "v19.lab_interfaces.v1"
ALLOWED_ROLES = {"user", "analyst", "practitioner", "admin", "system"}
ALLOWED_PROMOTION_STATUS = {"draft_review", "analyst_review", "changes_requested", "approved_for_test", "rejected", "deprecated"}
ALLOWED_GUIDED_QUESTION_REVIEW_STATUS = {"pending", "reviewed", "proposed_change", "rejected"}
ALLOWED_GUIDED_QUESTION_ACTION = {"add", "edit", "deprecate", "reorder_path"}
ALLOWED_GUIDED_QUESTION_PROPOSAL_STATUS = {"draft", "validation_ready", "validation_failed", "approved", "rejected", "active_record"}
FORBIDDEN_GUIDED_QUESTION_TERMS = ["未来财运", "今年好", "今年坏", "什么时候发财", "发财", "命运如何", "fortune", "future wealth", "good luck", "bad luck", "운세", "재물운"]
FORBIDDEN_ANSWER_TERMS = ["一定", "必然", "发财", "破财", "今年会", "明年会", "好运", "坏运", "财运很好", "财运很差", "婚姻会", "健康会"]
INTERNAL_ANSWER_MARKERS = ["answer_empty", "GUIDED_ANSWER", "DETERMINISTIC_RESULT_CARD", "rule_id", "signal_id", "question_basis", "source_signal_id"]
ALLOWED_GUIDED_REQUIRED_CONTEXT = {"chart", "result", "time_relation"}
ALLOWED_GUIDED_DEPTH = {"beginner", "intermediate"}
ALLOWED_BAZI_RULE_DOMAINS = {"day_master_element", "structural_relation", "ten_god_relation", "time_structure", "income_stability"}
ALLOWED_BAZI_RULE_STATUS = {"draft", "validation_ready", "validation_failed", "approved", "rejected", "active_record"}
ALLOWED_SYNTHETIC_PROMOTION_DECISIONS = {"approve", "reject", "needs_knowledge", "needs_rule", "needs_expression"}
ALLOWED_SYNTHETIC_PROMOTION_STATUS = {"draft_review", "analyst_review", "proposal_created", "rejected", "deprecated"}


def lab_status(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    return {
        "ok": True,
        "version": LAB_VERSION,
        "system_name": "V19 Standalone Agent Lab",
        "scope": "evolution_interfaces_only_no_auto_rule_activation",
        "storage": storage,
        "counts": {
            "feedback": len(state["feedback"]),
            "guided_question_feedback": len([row for row in state["feedback"] if row.get("subject_type") == "guided_question"]),
            "guided_question_reviews": len(state["guided_question_reviews"]),
            "guided_question_proposals": len(state["guided_question_proposals"]),
            "guided_question_library_versions": len(state["guided_question_library_versions"]),
            "guided_question_audits": len(state["guided_question_audits"]),
            "bazi_rule_proposals": len(state["bazi_rule_proposals"]),
            "bazi_rule_versions": len(state["bazi_rule_versions"]),
            "synthetic_promotion_candidates": len(state["synthetic_promotion_candidates"]),
            "governance_releases": len(state["governance_releases"]),
            "knowledge_review_batches": len(state["knowledge_review_batches"]),
            "knowledge_batch_proposal_runs": len(state["knowledge_batch_proposal_runs"]),
            "rule_impacts": len(state["rule_impacts"]),
            "revision_proposals": len(state["revision_proposals"]),
            "active_rule_revisions": len(state["active_rule_revisions"]),
            "validation_cases": len(state["validation_cases"]),
            "validation_runs": len(state["validation_runs"]),
            "promotion_requests": len(state["promotion_requests"]),
            "label_terms": len(state["label_contract"].get("terms", {})),
        },
        "guardrails": [
            "NO_AUTO_LEARNING",
            "NO_AUTO_RULE_PROMOTION",
            "NO_PREDICTION_EXPANSION",
            "ANALYST_REVIEW_REQUIRED",
        ],
    }


def register_feedback(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    role = _role(payload.get("actor_role"))
    row = {
        "feedback_id": "fb_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "actor_role": role,
        "actor_id": _clean(payload.get("actor_id"), "anonymous"),
        "subject_type": _clean(payload.get("subject_type"), "agent_turn"),
        "subject_id": _clean(payload.get("subject_id")),
        "rating": _bounded_int(payload.get("rating"), 0, -2, 2),
        "comment": _clean(payload.get("comment")),
        "tags": _string_list(payload.get("tags")),
        "suggested_action": _clean(payload.get("suggested_action")),
        "status": "open",
        "payload": dict(payload.get("payload") or {}),
        "metadata": dict(payload.get("metadata") or {}),
        "guardrails": ["FEEDBACK_IS_SIGNAL_NOT_RULE", "REQUIRES_ANALYST_REVIEW"],
    }
    state["feedback"].append(row)
    impacts = _rule_impacts_from_feedback(row, payload)
    state["rule_impacts"].extend(impacts)
    row["rule_impact_count"] = len(impacts)
    saved = _save_state(state, settings)
    return {"ok": True, "item": row, "storage": saved}


def list_feedback(settings: Dict[str, Any] | None = None, *, role: str = "", status: str = "", subject_type: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["feedback"])
    if role:
        rows = [row for row in rows if row.get("actor_role") == role]
    if status:
        rows = [row for row in rows if row.get("status") == status]
    if subject_type:
        rows = [row for row in rows if row.get("subject_type") == subject_type]
    rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {"ok": True, "count": len(rows), "items": rows[:100], "storage": storage}


def list_guided_question_feedback(settings: Dict[str, Any] | None = None, *, question_key: str = "", status: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = [dict(row) for row in state["feedback"] if row.get("subject_type") == "guided_question"]
    if question_key:
        rows = [row for row in rows if row.get("subject_id") == question_key]
    review_map = _guided_question_review_map(state)
    for row in rows:
        review = review_map.get(str(row.get("subject_id") or ""), {})
        row["review_status"] = review.get("status", "pending")
        row["review_note"] = review.get("note", "")
    if status:
        rows = [row for row in rows if row.get("review_status") == status]
    rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:200],
        "storage": storage,
        "guardrails": ["REVIEW_QUEUE_ONLY", "NO_AUTO_QUESTION_LIBRARY_CHANGE", "NO_AUTO_RANKING_LEARNING"],
    }


def guided_question_feedback_summary(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    review_map = _guided_question_review_map(state)
    buckets: Dict[str, Dict[str, Any]] = {}
    for row in state["feedback"]:
        if row.get("subject_type") != "guided_question":
            continue
        key = _clean(row.get("subject_id"), "unknown_question")
        bucket = buckets.setdefault(
            key,
            {
                "question_key": key,
                "helpful_count": 0,
                "not_helpful_count": 0,
                "neutral_count": 0,
                "total": 0,
                "helpful_rate": 0.0,
                "review_status": review_map.get(key, {}).get("status", "pending"),
                "review_note": review_map.get(key, {}).get("note", ""),
                "latest_feedback_at": "",
                "guardrails": ["SUMMARY_ONLY", "NO_AUTO_LIBRARY_UPDATE"],
            },
        )
        rating = _bounded_int(row.get("rating"), 0, -2, 2)
        if rating > 0:
            bucket["helpful_count"] += 1
        elif rating < 0:
            bucket["not_helpful_count"] += 1
        else:
            bucket["neutral_count"] += 1
        bucket["total"] += 1
        bucket["latest_feedback_at"] = max(str(bucket.get("latest_feedback_at") or ""), str(row.get("created_at") or ""))
    for bucket in buckets.values():
        total = int(bucket.get("total") or 0)
        bucket["helpful_rate"] = round(float(bucket.get("helpful_count") or 0) / total, 3) if total else 0.0
    rows = sorted(buckets.values(), key=lambda row: (int(row.get("total") or 0), str(row.get("latest_feedback_at") or "")), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "items": rows,
        "storage": storage,
        "guardrails": ["QUESTION_FEEDBACK_SUMMARY_ONLY", "ANALYST_REVIEW_REQUIRED", "NO_AUTO_LEARNING"],
    }


def record_guided_question_audit(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    row = {
        "audit_id": "gqa_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "profile_id": _clean(payload.get("profile_id")),
        "selected_year": payload.get("selected_year"),
        "selected_question_key": _clean(payload.get("selected_question_key")),
        "message": _clean(payload.get("message")),
        "audit_status": _clean((payload.get("audit") or {}).get("status"), "unknown"),
        "failed_count": _bounded_int((payload.get("audit") or {}).get("failed_count"), 0, 0, 999),
        "question_contract": dict(payload.get("question_contract") or {}),
        "intent": dict(payload.get("intent") or {}),
        "retrieved_facts": dict(payload.get("retrieved_facts") or {}),
        "observed_facts": dict(payload.get("observed_facts") or {}),
        "composed_text": dict(payload.get("composed_text") or {}),
        "audit": dict(payload.get("audit") or {}),
        "guardrails": ["AUDIT_LEDGER_ONLY", "NO_RUNTIME_MUTATION", "NO_AUTO_RULE_UPDATE"],
    }
    state["guided_question_audits"].append(row)
    saved = _save_state(state, settings)
    return {"ok": True, "item": row, "storage": saved}


def list_guided_question_audits(settings: Dict[str, Any] | None = None, *, status: str = "", question_key: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["guided_question_audits"])
    if status:
        rows = [row for row in rows if row.get("audit_status") == status]
    if question_key:
        rows = [row for row in rows if row.get("selected_question_key") == question_key]
    rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:100],
        "storage": storage,
        "guardrails": ["AUDIT_LEDGER_ONLY", "NO_RUNTIME_MUTATION", "NO_AUTO_RULE_UPDATE"],
    }


def guided_question_audit_report(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["guided_question_audits"])
    by_status: Dict[str, int] = {}
    by_question: Dict[str, int] = {}
    by_intent: Dict[str, int] = {}
    failed_checks: Dict[str, int] = {}
    unsupported: Dict[str, int] = {}
    latest_failures: List[Dict[str, Any]] = []
    for row in rows:
        status = _clean(row.get("audit_status"), "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        key = _clean(row.get("selected_question_key"), "unknown")
        by_question[key] = by_question.get(key, 0) + 1
        intent = _clean((row.get("intent") or {}).get("answer_kind"), "unknown")
        by_intent[intent] = by_intent.get(intent, 0) + 1
        unsupported_reason = _clean((row.get("intent") or {}).get("unsupported_reason"))
        if unsupported_reason:
            unsupported[unsupported_reason] = unsupported.get(unsupported_reason, 0) + 1
        for check in (row.get("audit") or {}).get("checks", []):
            if isinstance(check, dict) and check.get("passed") is False:
                name = _clean(check.get("name"), "unknown_check")
                failed_checks[name] = failed_checks.get(name, 0) + 1
        if status == "fail":
            latest_failures.append(
                {
                    "audit_id": row.get("audit_id"),
                    "created_at": row.get("created_at"),
                    "question_key": row.get("selected_question_key"),
                    "message": row.get("message"),
                    "failed_count": row.get("failed_count"),
                    "failed_checks": [
                        _clean(check.get("name"), "unknown_check")
                        for check in (row.get("audit") or {}).get("checks", [])
                        if isinstance(check, dict) and check.get("passed") is False
                    ],
                }
            )
    latest_failures.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "storage": storage,
        "summary": {
            "by_status": by_status,
            "by_question": _top_counts(by_question),
            "by_intent": _top_counts(by_intent),
            "failed_checks": _top_counts(failed_checks),
            "unsupported_reasons": _top_counts(unsupported),
        },
        "latest_failures": latest_failures[:20],
        "recommendations": _guided_question_audit_recommendations(by_status, failed_checks, unsupported),
        "guardrails": ["AUDIT_REPORT_ONLY", "NO_AUTO_RULE_UPDATE", "NO_AUTO_LIBRARY_UPDATE"],
    }


def guided_question_answer_quality_report(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    items: List[Dict[str, Any]] = []
    for row in state["guided_question_audits"]:
        items.append(_answer_quality_item_from_audit(row))
    for row in state["feedback"]:
        if row.get("subject_type") == "guided_question":
            items.append(_answer_quality_item_from_feedback(row))
    items.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)

    by_status: Dict[str, int] = {}
    by_question: Dict[str, int] = {}
    risk_flags: Dict[str, int] = {}
    for item in items:
        status = _clean(item.get("status"), "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        key = _clean(item.get("question_key"), "unknown")
        by_question[key] = by_question.get(key, 0) + 1
        for flag in item.get("risk_flags") or []:
            flag_key = _clean(flag, "unknown_risk")
            risk_flags[flag_key] = risk_flags.get(flag_key, 0) + 1

    return {
        "ok": True,
        "version": "v19.p7.answer_quality_report.v1",
        "count": len(items),
        "storage": storage,
        "summary": {
            "by_status": by_status,
            "by_question": _top_counts(by_question),
            "risk_flags": _top_counts(risk_flags),
        },
        "items": items[:200],
        "recommendations": _answer_quality_recommendations(by_status, risk_flags),
        "guardrails": ["QUALITY_REPORT_ONLY", "NO_AUTO_LEARNING", "NO_AUTO_RULE_UPDATE", "NO_RUNTIME_MUTATION"],
    }


def update_guided_question_review(question_key: str, payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    key = _clean(question_key)
    if not key:
        return {"ok": False, "code": "QUESTION_KEY_REQUIRED", "message": "question_key is required."}
    status = _clean(payload.get("status"), "reviewed")
    if status not in ALLOWED_GUIDED_QUESTION_REVIEW_STATUS:
        return {"ok": False, "code": "GUIDED_QUESTION_REVIEW_STATUS_INVALID", "message": "Unsupported guided question review status."}
    review = None
    for row in state["guided_question_reviews"]:
        if row.get("question_key") == key:
            review = row
            break
    if not review:
        review = {
            "review_id": "gqr_" + uuid.uuid4().hex[:16],
            "question_key": key,
            "created_at": utc_now(),
            "history": [],
            "guardrails": ["REVIEW_STATUS_ONLY", "NO_AUTO_QUESTION_LIBRARY_CHANGE"],
        }
        state["guided_question_reviews"].append(review)
    review["status"] = status
    review["note"] = _clean(payload.get("note"))
    review["actor_role"] = _role(payload.get("actor_role"))
    review["updated_at"] = utc_now()
    review.setdefault("history", []).append(
        {
            "created_at": utc_now(),
            "status": status,
            "actor_role": review["actor_role"],
            "note": review["note"],
        }
    )
    saved = _save_state(state, settings)
    return {"ok": True, "item": review, "storage": saved}


def create_guided_question_proposal(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    action = _clean(payload.get("proposed_action"), "edit")
    if action not in ALLOWED_GUIDED_QUESTION_ACTION:
        return {"ok": False, "code": "GUIDED_QUESTION_ACTION_INVALID", "message": "Unsupported guided question proposal action."}
    source_key = _clean(payload.get("source_question_key"))
    proposed_key = _clean(payload.get("proposed_question_key"), source_key)
    if action in {"edit", "deprecate", "reorder_path"} and not source_key:
        return {"ok": False, "code": "SOURCE_QUESTION_KEY_REQUIRED", "message": "source_question_key is required for this action."}
    if action in {"add", "edit", "reorder_path"} and not proposed_key:
        return {"ok": False, "code": "PROPOSED_QUESTION_KEY_REQUIRED", "message": "proposed_question_key is required."}
    row = {
        "proposal_id": "gqp_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "source_question_key": source_key,
        "source_feedback_ids": _string_list(payload.get("source_feedback_ids")),
        "proposed_action": action,
        "proposed_question_key": proposed_key,
        "proposed_label": dict(payload.get("proposed_label") or {}),
        "proposed_metadata": dict(payload.get("proposed_metadata") or {}),
        "rationale": _clean(payload.get("rationale")),
        "status": "draft",
        "validation": {"required": True, "passed": False, "checks": []},
        "review": {"approved_by": "", "approved_at": "", "note": ""},
        "history": [
            {
                "created_at": utc_now(),
                "actor_role": _role(payload.get("actor_role")),
                "status": "draft",
                "note": "Guided question proposal created. Proposal only; no runtime mutation.",
            }
        ],
        "guardrails": ["PROPOSAL_ONLY", "NO_AUTO_LIBRARY_UPDATE", "VALIDATION_REQUIRED", "ANALYST_OR_ADMIN_APPROVAL_REQUIRED"],
    }
    state["guided_question_proposals"].append(row)
    saved = _save_state(state, settings)
    return {"ok": True, "item": row, "storage": saved}


def list_guided_question_proposals(settings: Dict[str, Any] | None = None, *, status: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["guided_question_proposals"])
    if status:
        rows = [row for row in rows if row.get("status") == status]
    rows.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
    return {"ok": True, "count": len(rows), "items": rows[:100], "storage": storage, "guardrails": ["PROPOSAL_QUEUE_ONLY", "NO_AUTO_LIBRARY_UPDATE"]}


def validate_guided_question_proposal(proposal_id: str, settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    proposal = _find_guided_question_proposal(state, proposal_id)
    if not proposal:
        return {"ok": False, "code": "GUIDED_QUESTION_PROPOSAL_NOT_FOUND", "message": "Guided question proposal not found."}
    checks = _validate_guided_question_proposal(proposal)
    passed = all(row.get("passed") for row in checks)
    proposal["validation"] = {"required": True, "passed": passed, "checks": checks, "validated_at": utc_now()}
    proposal["status"] = "validation_ready" if passed else "validation_failed"
    proposal["updated_at"] = utc_now()
    _append_guided_question_history(
        proposal,
        actor_role="system",
        status=proposal["status"],
        note="Validation completed. Checks are audit records only; question library unchanged.",
    )
    saved = _save_state(state, settings)
    return {"ok": True, "item": proposal, "passed": passed, "checks": checks, "storage": saved}


def approve_guided_question_proposal(proposal_id: str, payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    proposal = _find_guided_question_proposal(state, proposal_id)
    if not proposal:
        return {"ok": False, "code": "GUIDED_QUESTION_PROPOSAL_NOT_FOUND", "message": "Guided question proposal not found."}
    role = _role(payload.get("actor_role"))
    if role not in {"analyst", "admin"}:
        return {"ok": False, "code": "ROLE_NOT_ALLOWED", "message": "Only analyst/admin can approve guided question proposals."}
    if not dict(proposal.get("validation") or {}).get("passed"):
        return {"ok": False, "code": "VALIDATION_REQUIRED", "message": "Proposal must pass validation before approval."}
    proposal["status"] = "approved"
    proposal["updated_at"] = utc_now()
    proposal["review"] = {
        "approved_by": _clean(payload.get("actor_id"), role),
        "approved_role": role,
        "approved_at": utc_now(),
        "note": _clean(payload.get("note")),
    }
    _append_guided_question_history(
        proposal,
        actor_role=role,
        status="approved",
        note=_clean(payload.get("note"), "Approved after validation. No runtime mutation."),
    )
    saved = _save_state(state, settings)
    return {"ok": True, "item": proposal, "storage": saved}


def record_guided_question_library_version(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    proposal_ids = _string_list(payload.get("included_proposals"))
    proposals = [row for row in state["guided_question_proposals"] if row.get("proposal_id") in proposal_ids]
    if not proposals:
        return {"ok": False, "code": "APPROVED_PROPOSALS_REQUIRED", "message": "At least one approved proposal is required."}
    not_approved = [row.get("proposal_id") for row in proposals if row.get("status") != "approved"]
    if not_approved:
        return {"ok": False, "code": "PROPOSALS_NOT_APPROVED", "message": "All included proposals must be approved.", "proposal_ids": not_approved}
    gate = _p12_synthetic_regression_gate()
    if not gate.get("passed"):
        return {"ok": False, "code": "P12_SYNTHETIC_REGRESSION_FAILED", "message": "P11 synthetic regression must pass before recording an active question-library version.", "regression_gate": gate}
    version = {
        "version_id": "gqlv_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "activated_by": _clean(payload.get("activated_by"), "admin"),
        "activated_by_role": _role(payload.get("activated_by_role")),
        "included_proposals": proposal_ids,
        "changelog": [
            {
                "proposal_id": row.get("proposal_id"),
                "action": row.get("proposed_action"),
                "question_key": row.get("proposed_question_key") or row.get("source_question_key"),
                "source_question_key": row.get("source_question_key"),
                "rationale": row.get("rationale"),
                "review_note": dict(row.get("review") or {}).get("note", ""),
            }
            for row in proposals
        ],
        "question_count": _bounded_int(payload.get("question_count"), len(proposal_ids), 0, 9999),
        "runtime_mutation": False,
        "p12_regression_gate": gate,
        "note": _clean(payload.get("note")),
        "guardrails": ["VERSION_RECORD_ONLY", "NO_RUNTIME_MUTATION", "P12_SYNTHETIC_REGRESSION_REQUIRED", "REQUIRES_FUTURE_ENGINEERING_IMPLEMENTATION"],
    }
    for proposal in proposals:
        proposal["status"] = "active_record"
        proposal["updated_at"] = utc_now()
        _append_guided_question_history(
            proposal,
            actor_role=_role(payload.get("activated_by_role")),
            status="active_record",
            note=f"Included in version record. runtime_mutation=false. version_id={version['version_id']}",
        )
    state["guided_question_library_versions"].append(version)
    saved = _save_state(state, settings)
    return {"ok": True, "item": version, "storage": saved}


def list_guided_question_library_versions(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = sorted(state["guided_question_library_versions"], key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {"ok": True, "count": len(rows), "items": rows[:100], "storage": storage, "guardrails": ["VERSION_RECORDS_ONLY", "NO_RUNTIME_MUTATION"]}


def list_rule_impacts(settings: Dict[str, Any] | None = None, *, feedback_id: str = "", rule_id: str = "", signal: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["rule_impacts"])
    if feedback_id:
        rows = [row for row in rows if row.get("feedback_id") == feedback_id]
    if rule_id:
        rows = [row for row in rows if row.get("rule_id") == rule_id]
    if signal:
        rows = [row for row in rows if row.get("signal") == signal]
    rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:100],
        "guardrails": ["RULE_IMPACT_MAPPING_ONLY", "NO_AUTO_RULE_UPDATE", "ANALYST_REVIEW_REQUIRED"],
        "storage": storage,
    }


def create_bazi_rule_proposal(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    domain = _clean(payload.get("domain"), "income_stability")
    if domain not in ALLOWED_BAZI_RULE_DOMAINS:
        return {"ok": False, "code": "BAZI_RULE_DOMAIN_INVALID", "message": "Unsupported Bazi rule domain."}
    rule_id = _clean(payload.get("rule_id"))
    if not rule_id:
        return {"ok": False, "code": "RULE_ID_REQUIRED", "message": "rule_id is required."}
    row = {
        "proposal_id": "brp_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "rule_id": rule_id,
        "version": _bounded_int(payload.get("version"), 1, 1, 9999),
        "domain": domain,
        "status": "draft",
        "source_feedback_ids": _string_list(payload.get("source_feedback_ids")),
        "input_contract": dict(payload.get("input_contract") or {}),
        "condition": dict(payload.get("condition") or {}),
        "output_contract": dict(payload.get("output_contract") or {}),
        "reasoning_path": _string_list(payload.get("reasoning_path")),
        "evidence": dict(payload.get("evidence") or {}),
        "confidence": _bounded_float(payload.get("confidence"), 0.0, 0.0, 1.0),
        "rationale": _clean(payload.get("rationale")),
        "validation": {"required": True, "passed": False, "checks": []},
        "review": {"approved_by": "", "approved_at": "", "note": ""},
        "history": [
            {
                "created_at": utc_now(),
                "actor_role": _role(payload.get("actor_role")),
                "status": "draft",
                "note": "Bazi rule proposal created. Proposal only; no runtime inference mutation.",
            }
        ],
        "guardrails": ["RULE_PROPOSAL_ONLY", "NO_RUNTIME_INFERENCE_MUTATION", "VALIDATION_REQUIRED", "ANALYST_OR_ADMIN_APPROVAL_REQUIRED"],
    }
    state["bazi_rule_proposals"].append(row)
    saved = _save_state(state, settings)
    return {"ok": True, "item": row, "storage": saved}


def list_bazi_rule_proposals(settings: Dict[str, Any] | None = None, *, status: str = "", domain: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["bazi_rule_proposals"])
    if status:
        rows = [row for row in rows if row.get("status") == status]
    if domain:
        rows = [row for row in rows if row.get("domain") == domain]
    rows.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
    return {"ok": True, "count": len(rows), "items": rows[:100], "storage": storage, "guardrails": ["RULE_PROPOSAL_LEDGER_ONLY", "NO_RUNTIME_INFERENCE_MUTATION"]}


def validate_bazi_rule_proposal(proposal_id: str, settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    proposal = _find_bazi_rule_proposal(state, proposal_id)
    if not proposal:
        return {"ok": False, "code": "BAZI_RULE_PROPOSAL_NOT_FOUND", "message": "Bazi rule proposal not found."}
    checks = _validate_bazi_rule_proposal(proposal)
    passed = all(row.get("passed") for row in checks)
    proposal["validation"] = {"required": True, "passed": passed, "checks": checks, "validated_at": utc_now()}
    proposal["status"] = "validation_ready" if passed else "validation_failed"
    proposal["updated_at"] = utc_now()
    _append_bazi_rule_history(proposal, actor_role="system", status=proposal["status"], note="Schema validation completed. Runtime inference unchanged.")
    saved = _save_state(state, settings)
    return {"ok": True, "item": proposal, "passed": passed, "checks": checks, "storage": saved}


def approve_bazi_rule_proposal(proposal_id: str, payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    proposal = _find_bazi_rule_proposal(state, proposal_id)
    if not proposal:
        return {"ok": False, "code": "BAZI_RULE_PROPOSAL_NOT_FOUND", "message": "Bazi rule proposal not found."}
    role = _role(payload.get("actor_role"))
    if role not in {"analyst", "admin"}:
        return {"ok": False, "code": "ROLE_NOT_ALLOWED", "message": "Only analyst/admin can approve Bazi rule proposals."}
    if not dict(proposal.get("validation") or {}).get("passed"):
        return {"ok": False, "code": "VALIDATION_REQUIRED", "message": "Rule proposal must pass schema validation before approval."}
    proposal["status"] = "approved"
    proposal["updated_at"] = utc_now()
    proposal["review"] = {
        "approved_by": _clean(payload.get("actor_id"), role),
        "approved_role": role,
        "approved_at": utc_now(),
        "note": _clean(payload.get("note")),
    }
    _append_bazi_rule_history(proposal, actor_role=role, status="approved", note=_clean(payload.get("note"), "Approved after schema validation. Runtime inference unchanged."))
    saved = _save_state(state, settings)
    return {"ok": True, "item": proposal, "storage": saved}


def record_bazi_rule_version(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    proposal_ids = _string_list(payload.get("included_proposals"))
    proposals = [row for row in state["bazi_rule_proposals"] if row.get("proposal_id") in proposal_ids]
    if not proposals:
        return {"ok": False, "code": "APPROVED_RULE_PROPOSALS_REQUIRED", "message": "At least one approved rule proposal is required."}
    not_approved = [row.get("proposal_id") for row in proposals if row.get("status") != "approved"]
    if not_approved:
        return {"ok": False, "code": "RULE_PROPOSALS_NOT_APPROVED", "message": "All included rule proposals must be approved.", "proposal_ids": not_approved}
    gate = _p12_synthetic_regression_gate()
    if not gate.get("passed"):
        return {"ok": False, "code": "P12_SYNTHETIC_REGRESSION_FAILED", "message": "P11 synthetic regression must pass before recording an active rule version.", "regression_gate": gate}
    version = {
        "version_id": "brv_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "activated_by": _clean(payload.get("activated_by"), "admin"),
        "activated_by_role": _role(payload.get("activated_by_role")),
        "included_proposals": proposal_ids,
        "rule_count": _bounded_int(payload.get("rule_count"), len(proposal_ids), 0, 9999),
        "runtime_mutation": False,
        "p12_regression_gate": gate,
        "note": _clean(payload.get("note")),
        "changelog": [
            {
                "proposal_id": row.get("proposal_id"),
                "rule_id": row.get("rule_id"),
                "domain": row.get("domain"),
                "version": row.get("version"),
                "rationale": row.get("rationale"),
                "review_note": dict(row.get("review") or {}).get("note", ""),
            }
            for row in proposals
        ],
        "guardrails": ["RULE_VERSION_RECORD_ONLY", "NO_RUNTIME_INFERENCE_MUTATION", "P12_SYNTHETIC_REGRESSION_REQUIRED", "REQUIRES_FUTURE_ENGINEERING_IMPLEMENTATION"],
    }
    for proposal in proposals:
        proposal["status"] = "active_record"
        proposal["updated_at"] = utc_now()
        _append_bazi_rule_history(proposal, actor_role=_role(payload.get("activated_by_role")), status="active_record", note=f"Included in Bazi rule version record. runtime_mutation=false. version_id={version['version_id']}")
    state["bazi_rule_versions"].append(version)
    saved = _save_state(state, settings)
    return {"ok": True, "item": version, "storage": saved}


def list_bazi_rule_versions(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = sorted(state["bazi_rule_versions"], key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {"ok": True, "count": len(rows), "items": rows[:100], "storage": storage, "guardrails": ["RULE_VERSION_RECORDS_ONLY", "NO_RUNTIME_INFERENCE_MUTATION"]}


def create_synthetic_promotion_candidate(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    draft = dict(payload.get("draft") or payload)
    case_id = _clean(draft.get("case_id"))
    if not case_id:
        return {"ok": False, "code": "SYNTHETIC_CASE_ID_REQUIRED", "message": "case_id is required."}
    target = _clean(draft.get("target"), "knowledge_or_rule_review_draft")
    draft_type = _clean(draft.get("draft_type"), _synthetic_draft_type_from_target(target))
    candidate = {
        "candidate_id": "spc_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "case_id": case_id,
        "structure_label": _clean(draft.get("structure_label")),
        "collision_focus": _clean(draft.get("collision_focus")),
        "target": target,
        "draft_type": draft_type,
        "attribution_layer": _clean(draft.get("attribution_layer"), "synthetic"),
        "failure_types": _string_list(draft.get("failure_types")),
        "knowledge_tags": _string_list(draft.get("knowledge_tags")),
        "suggested_action": _clean(draft.get("suggested_action")),
        "status": "draft_review",
        "source_draft": draft,
        "review_decision": {"decision": "pending", "actor_role": "", "note": "", "decided_at": ""},
        "downstream_proposal": {},
        "regression_gate": {"required_before_active_record": True, "matrix": "P11_SYNTHETIC_EXPANSION"},
        "guardrails": ["SYNTHETIC_FAILURE_DRAFT_ONLY", "ANALYST_REVIEW_REQUIRED", "NO_AUTO_LEARNING", "NO_RUNTIME_MUTATION"],
    }
    state["synthetic_promotion_candidates"].append(candidate)
    saved = _save_state(state, settings)
    return {"ok": True, "item": candidate, "storage": saved}


def list_synthetic_promotion_candidates(settings: Dict[str, Any] | None = None, *, status: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["synthetic_promotion_candidates"])
    if status:
        rows = [row for row in rows if row.get("status") == status]
    rows.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:100],
        "storage": storage,
        "guardrails": ["PROMOTION_QUEUE_ONLY", "ANALYST_DECISION_REQUIRED", "P11_REGRESSION_REQUIRED_BEFORE_ACTIVE_RECORD"],
    }


def review_synthetic_promotion_candidate(candidate_id: str, payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    candidate = _find_synthetic_promotion_candidate(state, candidate_id)
    if not candidate:
        return {"ok": False, "code": "SYNTHETIC_PROMOTION_NOT_FOUND", "message": "Synthetic promotion candidate not found."}
    role = _role(payload.get("actor_role"))
    if role not in {"analyst", "admin"}:
        return {"ok": False, "code": "ROLE_NOT_ALLOWED", "message": "Only analyst/admin can review synthetic promotion candidates."}
    decision = _clean(payload.get("decision"), "reject")
    if decision not in ALLOWED_SYNTHETIC_PROMOTION_DECISIONS:
        return {"ok": False, "code": "SYNTHETIC_PROMOTION_DECISION_INVALID", "message": "Unsupported review decision."}
    candidate["review_decision"] = {
        "decision": decision,
        "actor_role": role,
        "actor_id": _clean(payload.get("actor_id"), role),
        "note": _clean(payload.get("note")),
        "decided_at": utc_now(),
    }
    candidate["updated_at"] = utc_now()
    candidate["status"] = "rejected" if decision == "reject" else "analyst_review"
    candidate.setdefault("history", []).append(
        {
            "created_at": utc_now(),
            "actor_role": role,
            "decision": decision,
            "note": _clean(payload.get("note")),
        }
    )
    saved = _save_state(state, settings)
    if decision == "reject":
        return {"ok": True, "item": candidate, "storage": saved, "guardrails": candidate["guardrails"]}

    downstream = _create_synthetic_downstream_proposal(candidate, decision, payload, settings)
    state, _ = _load_state(settings)
    candidate = _find_synthetic_promotion_candidate(state, candidate_id)
    if candidate:
        candidate["downstream_proposal"] = downstream
        candidate["status"] = "proposal_created" if downstream.get("ok") else "analyst_review"
        candidate["updated_at"] = utc_now()
        candidate.setdefault("history", []).append(
            {
                "created_at": utc_now(),
                "actor_role": "system",
                "status": candidate["status"],
                "note": "Downstream proposal creation attempted. Runtime unchanged.",
                "downstream_kind": downstream.get("kind"),
                "downstream_id": downstream.get("proposal_id") or downstream.get("draft_id"),
            }
        )
        saved = _save_state(state, settings)
    return {"ok": True, "item": candidate, "downstream": downstream, "storage": saved}


def create_governance_release(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    role = _role(payload.get("actor_role"))
    if role not in {"analyst", "admin"}:
        return {"ok": False, "code": "ROLE_NOT_ALLOWED", "message": "Only analyst/admin can create governance release records."}
    artifact_ids = {
        "knowledge_draft_ids": _string_list(payload.get("knowledge_draft_ids")),
        "guided_question_version_ids": _string_list(payload.get("guided_question_version_ids")),
        "bazi_rule_version_ids": _string_list(payload.get("bazi_rule_version_ids")),
        "active_revision_ids": _string_list(payload.get("active_revision_ids")),
    }
    if not any(artifact_ids.values()):
        return {"ok": False, "code": "RELEASE_ARTIFACT_REQUIRED", "message": "At least one reviewed/versioned artifact id is required."}
    artifacts, missing = _collect_governance_release_artifacts(state, artifact_ids)
    if missing:
        return {"ok": False, "code": "RELEASE_ARTIFACT_NOT_FOUND", "message": "Some release artifacts were not found.", "missing": missing}
    gate = _p12_synthetic_regression_gate()
    if not gate.get("passed"):
        return {"ok": False, "code": "P13_SYNTHETIC_REGRESSION_FAILED", "message": "P11 synthetic regression must pass before recording a governance release.", "regression_gate": gate}
    release = {
        "release_id": "grl_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "created_by_role": role,
        "created_by": _clean(payload.get("actor_id"), role),
        "release_type": _clean(payload.get("release_type"), "p13_governance_manifest"),
        "status": "release_record",
        "artifact_ids": artifact_ids,
        "artifacts": artifacts,
        "summary": _governance_release_summary(artifacts),
        "p13_regression_gate": gate,
        "runtime_mutation": False,
        "note": _clean(payload.get("note")),
        "guardrails": ["GOVERNANCE_RELEASE_RECORD_ONLY", "NO_RUNTIME_MUTATION", "P11_SYNTHETIC_REGRESSION_REQUIRED", "ANALYST_OR_ADMIN_REVIEW_REQUIRED"],
    }
    state["governance_releases"].append(release)
    saved = _save_state(state, settings)
    return {"ok": True, "item": release, "storage": saved}


def list_governance_releases(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = sorted(state["governance_releases"], key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:100],
        "storage": storage,
        "guardrails": ["GOVERNANCE_RELEASE_RECORDS_ONLY", "NO_RUNTIME_MUTATION", "P11_SYNTHETIC_REGRESSION_REQUIRED"],
    }


def create_knowledge_review_batch(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    drafts = _select_knowledge_review_drafts(payload)
    if not drafts:
        return {"ok": False, "code": "KNOWLEDGE_REVIEW_BATCH_EMPTY", "message": "No knowledge drafts matched the batch filter."}
    batch_key = _clean(payload.get("batch_key")) or "kb_batch_" + _synthetic_slug(payload.get("batch_name") or payload.get("name") or uuid.uuid4().hex[:8])
    if any(row.get("batch_key") == batch_key for row in state["knowledge_review_batches"]):
        return {"ok": False, "code": "KNOWLEDGE_REVIEW_BATCH_EXISTS", "message": "Batch key already exists.", "batch_key": batch_key}
    batch = {
        "batch_id": "krb_" + uuid.uuid4().hex[:16],
        "batch_key": batch_key,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "created_by_role": _role(payload.get("actor_role")),
        "batch_name": _clean(payload.get("batch_name") or payload.get("name"), batch_key),
        "scope": _clean(payload.get("scope"), "knowledge_draft_review"),
        "status": "draft_review",
        "recommended_action": _clean(payload.get("recommended_action"), "analyst_review"),
        "risk_levels": sorted({str(row.get("risk_level") or "") for row in drafts if row.get("risk_level")}),
        "domains": sorted({str(row.get("domain") or "") for row in drafts if row.get("domain")}),
        "categories": sorted({str(row.get("category") or "") for row in drafts if row.get("category")}),
        "draft_ids": [str(row.get("draft_id") or "") for row in drafts if row.get("draft_id")],
        "knowledge_ids": [str(row.get("knowledge_id") or "") for row in drafts if row.get("knowledge_id")],
        "items": [_knowledge_review_batch_item(row) for row in drafts],
        "summary": {
            "draft_count": len(drafts),
            "by_risk_level": _top_counts(_count_by(drafts, "risk_level")),
            "by_domain": _top_counts(_count_by(drafts, "domain")),
            "by_category": _top_counts(_count_by(drafts, "category")),
        },
        "review_policy": _clean(payload.get("review_policy"), "batch_only_no_status_mutation"),
        "note": _clean(payload.get("note")),
        "guardrails": ["REVIEW_BATCH_ONLY", "NO_DRAFT_STATUS_MUTATION", "ANALYST_REVIEW_REQUIRED", "NO_RUNTIME_MUTATION"],
    }
    state["knowledge_review_batches"].append(batch)
    saved = _save_state(state, settings)
    return {"ok": True, "item": batch, "storage": saved}


def seed_p14_knowledge_review_batches(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    specs = [
        {
            "batch_key": "p15.p14.r1_metadata_boundaries",
            "batch_name": "P14 R1 metadata boundaries",
            "knowledge_id_prefix": "p14.",
            "risk_levels": ["R1"],
            "recommended_action": "review_for_proposal_ready",
            "note": "Ten-god family and month-command boundary drafts. Safe to review first.",
            "actor_role": "system",
        },
        {
            "batch_key": "p15.p14.r2_source_version_review",
            "batch_name": "P14 R2 source/version review",
            "knowledge_id_prefix": "p14.",
            "risk_levels": ["R2"],
            "recommended_action": "source_version_review_before_rule_proposal",
            "note": "Stem combination and branch penalty drafts require source/version review.",
            "actor_role": "system",
        },
        {
            "batch_key": "p15.p14.r3_archive_reference_only",
            "batch_name": "P14 R3 archive/reference only",
            "knowledge_id_prefix": "p14.",
            "risk_levels": ["R3"],
            "recommended_action": "archive_reference_only_until_architect_or_analyst_review",
            "note": "Twelve growth phase and useful-god drafts remain archive/reference only.",
            "actor_role": "system",
        },
    ]
    created = []
    skipped = []
    for spec in specs:
        result = create_knowledge_review_batch(spec, settings)
        if result.get("ok"):
            created.append(result.get("item"))
        else:
            skipped.append({"batch_key": spec["batch_key"], "code": result.get("code"), "message": result.get("message")})
    return {
        "ok": True,
        "created_count": len(created),
        "skipped_count": len(skipped),
        "items": created,
        "skipped": skipped,
        "guardrails": ["P14_BATCH_SEED_ONLY", "NO_DRAFT_STATUS_MUTATION", "ANALYST_REVIEW_REQUIRED"],
    }


def list_knowledge_review_batches(settings: Dict[str, Any] | None = None, *, status: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["knowledge_review_batches"])
    if status:
        rows = [row for row in rows if row.get("status") == status]
    rows.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:100],
        "storage": storage,
        "guardrails": ["REVIEW_BATCH_RECORDS_ONLY", "NO_DRAFT_STATUS_MUTATION", "NO_RUNTIME_MUTATION"],
    }


def create_knowledge_batch_proposal_drafts(batch_id: str, payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    batch = _find_knowledge_review_batch(state, batch_id)
    if not batch:
        return {"ok": False, "code": "KNOWLEDGE_REVIEW_BATCH_NOT_FOUND", "message": "Knowledge review batch not found."}
    role = _role(payload.get("actor_role"))
    if role not in {"analyst", "admin"}:
        return {"ok": False, "code": "ROLE_NOT_ALLOWED", "message": "Only analyst/admin can create batch proposal drafts."}
    existing = _find_successful_knowledge_batch_proposal_run(state, batch)
    if existing and payload.get("allow_duplicate") is not True:
        return {
            "ok": False,
            "code": "KNOWLEDGE_BATCH_PROPOSALS_EXIST",
            "message": "Proposal drafts already exist for this batch. Use allow_duplicate=true only for explicit re-review.",
            "item": existing,
            "guardrails": existing.get("guardrails") or [],
        }

    eligible = _knowledge_batch_proposal_eligibility(batch)
    run_id = "kbpr_" + uuid.uuid4().hex[:16]
    if not eligible["eligible"]:
        run = _knowledge_batch_proposal_run_base(run_id, batch, payload, role)
        run.update(
            {
                "status": "blocked",
                "blocked_reason": eligible["reason"],
                "blocked_items": eligible["blocked_items"],
                "summary": {
                    "rule_proposal_count": 0,
                    "question_proposal_count": 0,
                    "blocked_count": len(eligible["blocked_items"]) or len(batch.get("items") or []),
                },
            }
        )
        state["knowledge_batch_proposal_runs"].append(run)
        saved = _save_state(state, settings)
        return {
            "ok": False,
            "code": "KNOWLEDGE_BATCH_PROPOSAL_BLOCKED",
            "message": eligible["reason"],
            "item": run,
            "storage": saved,
            "guardrails": run["guardrails"],
        }

    drafts, missing = _knowledge_drafts_for_batch(batch)
    if missing:
        run = _knowledge_batch_proposal_run_base(run_id, batch, payload, role)
        run.update(
            {
                "status": "blocked",
                "blocked_reason": "Some batch draft ids were not found in the knowledge draft archive.",
                "blocked_items": missing,
                "summary": {"rule_proposal_count": 0, "question_proposal_count": 0, "blocked_count": len(missing)},
            }
        )
        state["knowledge_batch_proposal_runs"].append(run)
        saved = _save_state(state, settings)
        return {
            "ok": False,
            "code": "KNOWLEDGE_BATCH_DRAFTS_MISSING",
            "message": run["blocked_reason"],
            "item": run,
            "storage": saved,
            "guardrails": run["guardrails"],
        }

    rule_items = []
    question_items = []
    errors = []
    if payload.get("create_rule_proposals") is not False:
        for draft in drafts:
            created = create_bazi_rule_proposal(_knowledge_batch_rule_proposal_payload(batch, draft, run_id, payload, role), settings)
            if created.get("ok"):
                item = dict(created.get("item") or {})
                rule_items.append(
                    {
                        "proposal_id": item.get("proposal_id"),
                        "rule_id": item.get("rule_id"),
                        "domain": item.get("domain"),
                        "source_knowledge_id": draft.get("knowledge_id"),
                        "source_draft_id": draft.get("draft_id"),
                    }
                )
            else:
                errors.append(
                    {
                        "kind": "bazi_rule_proposal",
                        "source_knowledge_id": draft.get("knowledge_id"),
                        "code": created.get("code"),
                        "message": created.get("message"),
                    }
                )
    if payload.get("create_question_proposal") is not False:
        created = create_guided_question_proposal(_knowledge_batch_question_proposal_payload(batch, drafts, run_id, payload, role), settings)
        if created.get("ok"):
            item = dict(created.get("item") or {})
            question_items.append(
                {
                    "proposal_id": item.get("proposal_id"),
                    "question_key": item.get("proposed_question_key"),
                    "source_question_key": item.get("source_question_key"),
                }
            )
        else:
            errors.append({"kind": "guided_question_proposal", "code": created.get("code"), "message": created.get("message")})

    state, _ = _load_state(settings)
    run = _knowledge_batch_proposal_run_base(run_id, batch, payload, role)
    run.update(
        {
            "status": "proposal_drafts_created" if not errors else "proposal_drafts_partial",
            "rule_proposals": rule_items,
            "guided_question_proposals": question_items,
            "errors": errors,
            "summary": {
                "rule_proposal_count": len(rule_items),
                "question_proposal_count": len(question_items),
                "blocked_count": 0,
                "error_count": len(errors),
            },
        }
    )
    state["knowledge_batch_proposal_runs"].append(run)
    saved = _save_state(state, settings)
    return {
        "ok": not errors,
        "item": run,
        "storage": saved,
        "guardrails": run["guardrails"],
        "rule_proposals": rule_items,
        "guided_question_proposals": question_items,
        "errors": errors,
    }


def list_knowledge_batch_proposal_runs(settings: Dict[str, Any] | None = None, *, status: str = "", batch_key: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["knowledge_batch_proposal_runs"])
    if status:
        rows = [row for row in rows if row.get("status") == status]
    if batch_key:
        rows = [row for row in rows if row.get("batch_key") == batch_key or row.get("batch_id") == batch_key]
    rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {
        "ok": True,
        "count": len(rows),
        "items": rows[:100],
        "storage": storage,
        "guardrails": ["P16_PROPOSAL_RUN_LEDGER_ONLY", "NO_RUNTIME_MUTATION", "R2_R3_ANALYST_REVIEW_BEFORE_PROPOSAL"],
    }


def seed_validation_cases(settings: Dict[str, Any] | None = None, *, force: bool = False) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    existing = {row.get("case_id") for row in state["validation_cases"]}
    added = 0
    for case in _default_validation_cases():
        if case["case_id"] in existing and not force:
            continue
        if force:
            state["validation_cases"] = [row for row in state["validation_cases"] if row.get("case_id") != case["case_id"]]
        state["validation_cases"].append(case)
        added += 1
    saved = _save_state(state, settings)
    return {"ok": True, "status": "seeded", "added": added, "count": len(state["validation_cases"]), "storage": saved}


def list_validation_cases(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    if not state["validation_cases"]:
        seed_validation_cases(settings)
        state, storage = _load_state(settings)
    return {"ok": True, "count": len(state["validation_cases"]), "items": state["validation_cases"], "storage": storage}


def run_validation_cases(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    if not state["validation_cases"]:
        seed_validation_cases(settings)
        state, _ = _load_state(settings)
    results = []
    for case in state["validation_cases"]:
        results.append(_run_case(case))
    passed = sum(1 for row in results if row["passed"])
    run = {
        "run_id": "vr_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "case_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
        "guardrails": ["SYNTHETIC_VALIDATION_ONLY", "NO_RULE_ACTIVATION"],
    }
    state["validation_runs"].append(run)
    saved = _save_state(state, settings)
    return {"ok": True, "run": run, "storage": saved}


def list_validation_runs(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = sorted(state["validation_runs"], key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {"ok": True, "count": len(rows), "items": rows[:30], "storage": storage}


def create_promotion_request(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    row = {
        "promotion_id": "prq_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "kind": _clean(payload.get("kind"), "feedback_to_knowledge"),
        "source_ids": _string_list(payload.get("source_ids")),
        "target_id": _clean(payload.get("target_id")),
        "proposal": _clean(payload.get("proposal")),
        "rationale": _clean(payload.get("rationale")),
        "status": "draft_review",
        "created_by_role": _role(payload.get("created_by_role")),
        "review_notes": [],
        "guardrails": ["REQUEST_ONLY", "NO_AUTO_PROMOTION", "ANALYST_APPROVAL_REQUIRED"],
    }
    state["promotion_requests"].append(row)
    saved = _save_state(state, settings)
    return {"ok": True, "item": row, "storage": saved}


def list_promotion_requests(settings: Dict[str, Any] | None = None, *, status: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["promotion_requests"])
    if status:
        rows = [row for row in rows if row.get("status") == status]
    rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {"ok": True, "count": len(rows), "items": rows[:100], "storage": storage}


def update_promotion_status(promotion_id: str, payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    next_status = _clean(payload.get("status"), "analyst_review")
    if next_status not in ALLOWED_PROMOTION_STATUS:
        return {"ok": False, "code": "PROMOTION_STATUS_INVALID", "message": "Unsupported promotion status."}
    for row in state["promotion_requests"]:
        if row.get("promotion_id") != promotion_id:
            continue
        row["status"] = next_status
        row["updated_at"] = utc_now()
        row.setdefault("review_notes", []).append(
            {
                "created_at": utc_now(),
                "actor_role": _role(payload.get("actor_role")),
                "note": _clean(payload.get("note")),
                "status": next_status,
            }
        )
        saved = _save_state(state, settings)
        return {"ok": True, "item": row, "storage": saved}
    return {"ok": False, "code": "PROMOTION_NOT_FOUND", "message": "Promotion request not found."}


def create_revision_proposal(payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    source_impact_ids = _string_list(payload.get("source_impact_ids") or payload.get("source_rule_impact_ids"))
    target_rule_id = _clean(payload.get("target_rule_id"))
    if not target_rule_id:
        return {"ok": False, "code": "TARGET_RULE_ID_REQUIRED", "message": "target_rule_id is required."}
    current_version = _bounded_int(payload.get("current_rule_version") or payload.get("current_version"), 1, 1, 9999)
    proposed_version = _bounded_int(payload.get("proposed_rule_version") or payload.get("proposed_version"), 2, 1, 9999)
    row = {
        "revision_id": "rev_" + uuid.uuid4().hex[:16],
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "source_impact_ids": source_impact_ids,
        "source_rule_impact_ids": source_impact_ids,
        "target_rule_id": target_rule_id,
        "target_signal": _clean(payload.get("target_signal")),
        "current_rule_version": current_version,
        "proposed_rule_version": proposed_version,
        "current_version": current_version,
        "proposed_version": proposed_version,
        "proposal": _clean(payload.get("proposal")),
        "rationale": _clean(payload.get("rationale")),
        "proposed_change": dict(payload.get("proposed_change") or {}),
        "status": "draft",
        "validation": {"required": True, "latest_run_id": "", "passed": False},
        "review": {"required_role": ["analyst", "admin"], "approved_by": "", "approved_at": "", "notes": []},
        "activation": {"active": False, "activated_by": "", "activated_at": "", "runtime_mutation": False},
        "guardrails": ["PROPOSAL_ONLY", "VALIDATION_REQUIRED", "ANALYST_APPROVAL_REQUIRED", "NO_RUNTIME_MUTATION"],
    }
    state["revision_proposals"].append(row)
    saved = _save_state(state, settings)
    return {"ok": True, "item": row, "storage": saved}


def list_revision_proposals(settings: Dict[str, Any] | None = None, *, status: str = "", rule_id: str = "") -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = list(state["revision_proposals"])
    if status:
        rows = [row for row in rows if row.get("status") == status]
    if rule_id:
        rows = [row for row in rows if row.get("target_rule_id") == rule_id]
    rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return {"ok": True, "count": len(rows), "items": rows[:100], "storage": storage}


def validate_revision_proposal(revision_id: str, settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    revision = _find_revision(state, revision_id)
    if not revision:
        return {"ok": False, "code": "REVISION_NOT_FOUND", "message": "Revision proposal not found."}
    validation = run_validation_cases(settings)
    run = dict(validation.get("run") or {})
    passed = int(run.get("failed") or 0) == 0 and int(run.get("case_count") or 0) > 0
    revision["validation"] = {
        "required": True,
        "latest_run_id": run.get("run_id") or "",
        "passed": passed,
        "passed_count": run.get("passed"),
        "failed_count": run.get("failed"),
    }
    revision["validation_summary"] = {
        "passed": run.get("passed"),
        "failed": run.get("failed"),
        "case_count": run.get("case_count"),
    }
    revision["status"] = "validation_passed" if passed else "validation_failed"
    revision["updated_at"] = utc_now()
    saved = _save_state(state, settings)
    return {"ok": True, "item": revision, "validation_run": run, "storage": saved}


def approve_revision_proposal(revision_id: str, payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    revision = _find_revision(state, revision_id)
    if not revision:
        return {"ok": False, "code": "REVISION_NOT_FOUND", "message": "Revision proposal not found."}
    role = _role(payload.get("actor_role"))
    if role not in {"analyst", "admin"}:
        return {"ok": False, "code": "ROLE_NOT_ALLOWED", "message": "Only analyst/admin can approve revision proposals."}
    if not dict(revision.get("validation") or {}).get("passed"):
        return {"ok": False, "code": "VALIDATION_REQUIRED", "message": "Revision must pass synthetic validation before approval."}
    revision["status"] = "approved"
    revision["updated_at"] = utc_now()
    review = dict(revision.get("review") or {})
    review["approved_by"] = _clean(payload.get("actor_id"), role)
    review["approved_role"] = role
    review["approved_at"] = utc_now()
    review.setdefault("notes", []).append({"created_at": utc_now(), "actor_role": role, "note": _clean(payload.get("note"))})
    revision["review"] = review
    saved = _save_state(state, settings)
    return {"ok": True, "item": revision, "storage": saved}


def activate_revision_record(revision_id: str, payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, _ = _load_state(settings)
    revision = _find_revision(state, revision_id)
    if not revision:
        return {"ok": False, "code": "REVISION_NOT_FOUND", "message": "Revision proposal not found."}
    role = _role(payload.get("actor_role"))
    if role not in {"analyst", "admin"}:
        return {"ok": False, "code": "ROLE_NOT_ALLOWED", "message": "Only analyst/admin can activate revision records."}
    if revision.get("status") != "approved":
        return {"ok": False, "code": "APPROVAL_REQUIRED", "message": "Revision must be approved before activation record is created."}
    gate = _p12_synthetic_regression_gate()
    if not gate.get("passed"):
        return {"ok": False, "code": "P12_SYNTHETIC_REGRESSION_FAILED", "message": "P11 synthetic regression must pass before recording an active revision.", "regression_gate": gate}
    active = {
        "active_revision_id": "arv_" + uuid.uuid4().hex[:16],
        "status": "active_revision_record",
        "revision_id": revision_id,
        "target_rule_id": revision.get("target_rule_id"),
        "target_signal": revision.get("target_signal"),
        "rule_version": revision.get("proposed_rule_version"),
        "proposed_version": revision.get("proposed_rule_version"),
        "activated_at": utc_now(),
        "activated_by_role": role,
        "activated_by": _clean(payload.get("actor_id"), role),
        "runtime_mutation": False,
        "p12_regression_gate": gate,
        "note": _clean(payload.get("note")),
        "guardrails": ["ACTIVE_RECORD_ONLY", "NO_RUNTIME_MUTATION", "P12_SYNTHETIC_REGRESSION_REQUIRED", "REQUIRES_ENGINEERING_IMPLEMENTATION"],
    }
    revision["status"] = "active_revision_record"
    revision["updated_at"] = utc_now()
    revision["activation"] = {"active": True, "activated_by": active["activated_by"], "activated_at": active["activated_at"], "runtime_mutation": False}
    state["active_rule_revisions"].append(active)
    saved = _save_state(state, settings)
    return {"ok": True, "item": active, "revision": revision, "storage": saved}


def list_active_rule_revisions(settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    rows = sorted(state["active_rule_revisions"], key=lambda row: str(row.get("activated_at") or ""), reverse=True)
    return {"ok": True, "count": len(rows), "items": rows[:100], "storage": storage}


def label_contract(locale: str = "zh", settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state, storage = _load_state(settings)
    contract = dict(state["label_contract"])
    terms = contract.get("terms") if isinstance(contract.get("terms"), dict) else {}
    terms = {**_default_label_contract().get("terms", {}), **terms, **_current_product_label_overrides()}
    loc = locale if locale in {"zh", "en", "ko"} else "zh"
    localized = {
        key: {
            "label": dict(value.get("label") or {}).get(loc) or dict(value.get("label") or {}).get("zh") or key,
            "description": dict(value.get("description") or {}).get(loc) or dict(value.get("description") or {}).get("zh") or "",
            "category": value.get("category"),
        }
        for key, value in terms.items()
        if isinstance(value, dict)
    }
    return {
        "ok": True,
        "version": contract.get("version"),
        "locale": loc,
        "supported_locales": ["zh", "en", "ko"],
        "terms": localized,
        "storage": storage,
        "guardrails": ["LABELS_ONLY", "NO_TRANSLATED_RULE_CHANGE"],
    }


def _run_case(case: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if isinstance(case.get("chart"), dict):
            data = {"chart": dict(case.get("chart") or {})}
            result = {"ok": True, "code": "OK", "data": data}
        else:
            result = build_agent_turn(case["input"])
        expected_error = str(case.get("expected_error_code") or "")
        if expected_error:
            actual_error = str(result.get("code") or "")
            return {
                "case_id": case.get("case_id"),
                "passed": actual_error == expected_error,
                "failures": [] if actual_error == expected_error else [{"expected_error_code": expected_error, "actual": actual_error}],
                "observed": {"code": actual_error},
            }
        data = dict(result.get("data") or {})
        income = derive_income_stability(dict(data.get("chart") or {}))
        observed = {row["key"]: row["value"] for row in income.get("signals", []) if isinstance(row, dict)}
        failures = []
        for key, expected in dict(case.get("expected_income_stability") or {}).items():
            actual = observed.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    failures.append({"key": key, "expected": expected, "actual": actual})
            elif actual != expected:
                failures.append({"key": key, "expected": expected, "actual": actual})
        return {"case_id": case.get("case_id"), "passed": not failures, "failures": failures, "observed": observed}
    except Exception as exc:
        return {"case_id": case.get("case_id"), "passed": False, "failures": [{"error": str(exc)}], "observed": {}}


def _default_validation_cases() -> List[Dict[str, Any]]:
    return [
        {
            "case_id": "syn.income_stability.synthetic_stable_structure",
            "title": "Synthetic explicit pillars: stable income-structure signal",
            "chart": make_synthetic_chart(
                "syn.income_stability.synthetic_stable_structure",
                {"year": "戊辰", "month": "己未", "day": "戊午", "hour": "癸亥"},
            ),
            "expected_income_stability": {"income_stability": "stable", "self_capacity": "high", "wealth_accessibility": "clear"},
            "status": "active",
            "guardrails": ["SYNTHETIC_EXPLICIT_PILLARS", "NOT_DOMAIN_TRUTH", "NO_BIRTHDATE"],
        },
        {
            "case_id": "syn.income_stability.synthetic_disrupted_wealth_access",
            "title": "Synthetic explicit pillars: disrupted wealth-access signal",
            "chart": make_synthetic_chart(
                "syn.income_stability.synthetic_disrupted_wealth_access",
                {"year": "戊辰", "month": "丁巳", "day": "戊午", "hour": "壬子"},
            ),
            "expected_income_stability": {"income_stability": "unstable", "wealth_accessibility": "disrupted", "volatility": "medium"},
            "status": "active",
            "guardrails": ["SYNTHETIC_EXPLICIT_PILLARS", "NOT_DOMAIN_TRUTH", "NO_BIRTHDATE"],
        },
    ]


def _default_label_contract() -> Dict[str, Any]:
    return {
        "version": "v19.label_contract.v1",
        "terms": {
            "app_title": {
                "category": "oracle_ui",
                "label": {"zh": "掐指一算", "en": "Qiazhi Bazi", "ko": "Qiazhi Bazi"},
                "description": {"zh": "用户端入口标题。", "en": "User-facing entry title.", "ko": "사용자용 진입 제목입니다."},
            },
            "app_subtitle": {
                "category": "oracle_ui",
                "label": {"zh": "八字测算先看结构，再回答问题；不输出传统断语。", "en": "Structure-first Bazi reading with bounded answers, not fortune claims.", "ko": "구조를 먼저 보고 제한된 답변을 제공하며 운세 단정은 하지 않습니다."},
                "description": {"zh": "用户端副标题。", "en": "User-facing subtitle.", "ko": "사용자용 부제목입니다."},
            },
            "locale_label": {
                "category": "oracle_ui",
                "label": {"zh": "语言", "en": "Language", "ko": "언어"},
                "description": {"zh": "语言切换。", "en": "Locale switcher.", "ko": "언어 전환입니다."},
            },
            "locale_zh": {"category": "oracle_ui", "label": {"zh": "中文", "en": "Chinese", "ko": "중국어"}, "description": {"zh": "语言选项。", "en": "Locale option.", "ko": "언어 옵션입니다."}},
            "locale_en": {"category": "oracle_ui", "label": {"zh": "英文", "en": "English", "ko": "영어"}, "description": {"zh": "语言选项。", "en": "Locale option.", "ko": "언어 옵션입니다."}},
            "locale_ko": {"category": "oracle_ui", "label": {"zh": "韩文", "en": "Korean", "ko": "한국어"}, "description": {"zh": "语言选项。", "en": "Locale option.", "ko": "언어 옵션입니다."}},
            "nav_lab": {
                "category": "oracle_ui",
                "label": {"zh": "Lab 分析端", "en": "Lab Mode", "ko": "Lab 모드"},
                "description": {"zh": "进入分析端。", "en": "Open analyst lab.", "ko": "분석 Lab으로 이동합니다."},
            },
            "entry_title": {"category": "entry_ui", "label": {"zh": "进入掐指一算", "en": "Enter Qiazhi Bazi", "ko": "Qiazhi Bazi 시작"}, "description": {"zh": "入口标题。", "en": "Entry title.", "ko": "진입 제목입니다."}},
            "entry_subtitle": {"category": "entry_ui", "label": {"zh": "选择你的身份。游客试用最快，登录只用于区分入口权限，不改变分析结果。", "en": "Choose your entry. Guest trial is fastest; login only controls surface access and never changes analysis.", "ko": "입장 방식을 선택하세요. 게스트 체험이 가장 빠르며 로그인은 화면 접근만 제어하고 분석 결과는 바꾸지 않습니다."}, "description": {"zh": "入口说明。", "en": "Entry subtitle.", "ko": "진입 설명입니다."}},
            "guest_trial": {"category": "entry_ui", "label": {"zh": "游客试用", "en": "Try as guest", "ko": "게스트로 체험"}, "description": {"zh": "游客入口。", "en": "Guest entry.", "ko": "게스트 진입입니다."}},
            "guest_trial_desc": {"category": "entry_ui", "label": {"zh": "无需账号，直接进入掐指一算。", "en": "No account needed. Open Qiazhi Bazi directly.", "ko": "계정 없이 Qiazhi Bazi로 바로 들어갑니다."}, "description": {"zh": "游客说明。", "en": "Guest description.", "ko": "게스트 설명입니다."}},
            "user_login_register": {"category": "entry_ui", "label": {"zh": "普通用户登录 / 注册", "en": "User login / register", "ko": "사용자 로그인 / 등록"}, "description": {"zh": "用户入口。", "en": "User entry.", "ko": "사용자 진입입니다."}},
            "user_login_desc": {"category": "entry_ui", "label": {"zh": "本地最小账号入口，进入掐指一算用户端。", "en": "Minimal local account entry for Qiazhi Bazi.", "ko": "Qiazhi Bazi 사용자 화면으로 들어가는 최소 로컬 계정入口입니다."}, "description": {"zh": "用户说明。", "en": "User description.", "ko": "사용자 설명입니다."}},
            "login_register": {"category": "entry_ui", "label": {"zh": "登录 / 注册", "en": "Login / register", "ko": "로그인 / 등록"}, "description": {"zh": "统一登录入口。", "en": "Unified login entry.", "ko": "통합 로그인入口입니다."}},
            "login_register_desc": {"category": "entry_ui", "label": {"zh": "登录后系统会自动识别权限；角色只控制入口，不改变分析结果。", "en": "After login, access is resolved automatically; roles control surfaces, not analysis.", "ko": "로그인 후 접근 권한이 자동으로 결정됩니다. 역할은 화면 접근만 제어하고 분석 결과는 바꾸지 않습니다."}, "description": {"zh": "统一登录说明。", "en": "Unified login description.", "ko": "통합 로그인 설명입니다."}},
            "profile_list": {"category": "profile_ui", "label": {"zh": "八字档案", "en": "Bazi profiles", "ko": "사주 프로필"}, "description": {"zh": "档案列表。", "en": "Profile list.", "ko": "프로필 목록입니다."}},
            "profile_list_desc": {"category": "profile_ui", "label": {"zh": "选择已有命盘，或新建一个命盘。", "en": "Choose an existing chart or create a new one.", "ko": "기존 명식을 선택하거나 새 명식을 만드세요."}, "description": {"zh": "档案说明。", "en": "Profile description.", "ko": "프로필 설명입니다."}},
            "new_profile": {"category": "profile_ui", "label": {"zh": "新建命盘", "en": "New chart profile", "ko": "새 명식 만들기"}, "description": {"zh": "新建档案。", "en": "New profile.", "ko": "새 프로필입니다."}},
            "edit_profile": {"category": "profile_ui", "label": {"zh": "修改", "en": "Edit", "ko": "수정"}, "description": {"zh": "修改档案。", "en": "Edit profile.", "ko": "프로필 수정입니다."}},
            "delete_profile": {"category": "profile_ui", "label": {"zh": "删除", "en": "Delete", "ko": "삭제"}, "description": {"zh": "删除档案。", "en": "Delete profile.", "ko": "프로필 삭제입니다."}},
            "delete_profile_confirm": {"category": "profile_ui", "label": {"zh": "确定删除这个八字档案吗？此操作不可恢复。", "en": "Delete this Bazi profile? This cannot be undone.", "ko": "이 사주 프로필을 삭제할까요? 되돌릴 수 없습니다."}, "description": {"zh": "删除确认。", "en": "Delete confirmation.", "ko": "삭제 확인입니다."}},
            "delete_profile_done": {"category": "profile_ui", "label": {"zh": "档案已删除。", "en": "Profile deleted.", "ko": "프로필이 삭제되었습니다."}, "description": {"zh": "删除完成。", "en": "Delete done.", "ko": "삭제 완료입니다."}},
            "profile_name": {"category": "profile_ui", "label": {"zh": "档案名称", "en": "Profile name", "ko": "프로필 이름"}, "description": {"zh": "档案名称。", "en": "Profile name.", "ko": "프로필 이름입니다."}},
            "next_step": {"category": "profile_ui", "label": {"zh": "下一步", "en": "Next", "ko": "다음"}, "description": {"zh": "下一步。", "en": "Next.", "ko": "다음입니다."}},
            "back": {"category": "profile_ui", "label": {"zh": "返回修改", "en": "Back to edit", "ko": "수정으로 돌아가기"}, "description": {"zh": "返回。", "en": "Back.", "ko": "돌아가기입니다."}},
            "confirm_chart": {"category": "profile_ui", "label": {"zh": "确认命盘", "en": "Confirm chart", "ko": "명식 확인"}, "description": {"zh": "确认命盘。", "en": "Confirm chart.", "ko": "명식 확인입니다."}},
            "pillar_confirm_title": {"category": "profile_ui", "label": {"zh": "确认你的命盘", "en": "Confirm your chart", "ko": "명식을 확인하세요"}, "description": {"zh": "确认命盘标题。", "en": "Confirmation title.", "ko": "확인 제목입니다."}},
            "pillar_confirm_desc": {"category": "profile_ui", "label": {"zh": "这是根据你的输入生成的命盘结构。", "en": "This chart structure is generated from your input.", "ko": "이 명식 구조는 입력값으로 생성되었습니다."}, "description": {"zh": "确认命盘说明。", "en": "Confirmation description.", "ko": "확인 설명입니다."}},
            "time_selection_title": {"category": "profile_ui", "label": {"zh": "选择时间背景", "en": "Choose time context", "ko": "시간 맥락 선택"}, "description": {"zh": "时间选择标题。", "en": "Time selection title.", "ko": "시간 선택 제목입니다."}},
            "enter_analysis": {"category": "profile_ui", "label": {"zh": "进入分析", "en": "Enter analysis", "ko": "분석으로 이동"}, "description": {"zh": "进入分析。", "en": "Enter analysis.", "ko": "분석 진입입니다."}},
            "enter_existing_profile": {"category": "profile_ui", "label": {"zh": "进入 Agent", "en": "Open Agent", "ko": "Agent 열기"}, "description": {"zh": "进入已有档案。", "en": "Open profile.", "ko": "프로필 열기입니다."}},
            "select_profile_first": {"category": "profile_ui", "label": {"zh": "请先选择或新建命盘档案。", "en": "Please choose or create a Bazi profile first.", "ko": "먼저 사주 프로필을 선택하거나 만드세요."}, "description": {"zh": "无档案提示。", "en": "No profile notice.", "ko": "프로필 없음 안내입니다."}},
            "back_to_profiles": {"category": "profile_ui", "label": {"zh": "返回档案", "en": "Back to profiles", "ko": "프로필로 돌아가기"}, "description": {"zh": "返回档案。", "en": "Back to profiles.", "ko": "프로필로 돌아가기입니다."}},
            "practitioner_login": {"category": "entry_ui", "label": {"zh": "命理师登录", "en": "Practitioner login", "ko": "명리사 로그인"}, "description": {"zh": "命理师入口。", "en": "Practitioner entry.", "ko": "명리사 진입입니다."}},
            "practitioner_login_desc": {"category": "entry_ui", "label": {"zh": "进入 Lab 分析端，可查看结构、证据和治理入口。", "en": "Open Lab mode for structure, evidence, and governance review.", "ko": "구조, 근거, 거버넌스 검토를 위한 Lab 모드로 들어갑니다."}, "description": {"zh": "命理师说明。", "en": "Practitioner description.", "ko": "명리사 설명입니다."}},
            "username": {"category": "entry_ui", "label": {"zh": "用户名", "en": "Username", "ko": "사용자 이름"}, "description": {"zh": "用户名。", "en": "Username.", "ko": "사용자 이름입니다."}},
            "password": {"category": "entry_ui", "label": {"zh": "密码", "en": "Password", "ko": "비밀번호"}, "description": {"zh": "密码。", "en": "Password.", "ko": "비밀번호입니다."}},
            "login": {"category": "entry_ui", "label": {"zh": "登录", "en": "Login", "ko": "로그인"}, "description": {"zh": "登录。", "en": "Login.", "ko": "로그인입니다."}},
            "register": {"category": "entry_ui", "label": {"zh": "注册", "en": "Register", "ko": "등록"}, "description": {"zh": "注册。", "en": "Register.", "ko": "등록입니다."}},
            "enter_oracle": {"category": "entry_ui", "label": {"zh": "进入用户端", "en": "Enter Oracle", "ko": "Oracle로 이동"}, "description": {"zh": "进入用户端。", "en": "Enter Oracle.", "ko": "Oracle 진입입니다."}},
            "enter_lab": {"category": "entry_ui", "label": {"zh": "进入 Lab", "en": "Enter Lab", "ko": "Lab으로 이동"}, "description": {"zh": "进入 Lab。", "en": "Enter Lab.", "ko": "Lab 진입입니다."}},
            "auth_failed": {"category": "entry_ui", "label": {"zh": "登录失败，请检查输入。", "en": "Login failed. Please check your input.", "ko": "로그인 실패. 입력을 확인하세요."}, "description": {"zh": "登录失败。", "en": "Auth failed.", "ko": "로그인 실패입니다."}},
            "welcome_title": {
                "category": "oracle_ui",
                "label": {"zh": "我现在能帮你看什么？", "en": "What can I help with now?", "ko": "지금 무엇을 도와드릴 수 있나요?"},
                "description": {"zh": "欢迎区标题。", "en": "Welcome title.", "ko": "환영 제목입니다."},
            },
            "welcome_body": {
                "category": "oracle_ui",
                "label": {"zh": "当前版本只支持收入稳定性结构分析。它不会输出传统断语、吉凶判断或完整命运预测。", "en": "This version only supports income stability structure analysis. It does not produce fortune claims, good/bad judgments, or full-life predictions.", "ko": "현재 버전은 소득 안정성 구조 분석만 지원합니다. 운세 단정, 길흉 판단, 평생 예측은 제공하지 않습니다."},
                "description": {"zh": "欢迎区说明。", "en": "Welcome body.", "ko": "환영 설명입니다."},
            },
            "supported_now": {
                "category": "oracle_ui",
                "label": {"zh": "当前支持", "en": "Supported now", "ko": "현재 지원"},
                "description": {"zh": "支持能力标题。", "en": "Supported capability heading.", "ko": "지원 기능 제목입니다."},
            },
            "not_supported": {
                "category": "oracle_ui",
                "label": {"zh": "暂不支持", "en": "Not supported yet", "ko": "아직 지원하지 않음"},
                "description": {"zh": "不支持能力标题。", "en": "Unsupported heading.", "ko": "미지원 기능 제목입니다."},
            },
            "unsupported_full_chart": {
                "category": "oracle_ui",
                "label": {"zh": "完整命盘预测", "en": "Full chart prediction", "ko": "전체 명식 예측"},
                "description": {"zh": "不支持项。", "en": "Unsupported item.", "ko": "미지원 항목입니다."},
            },
            "unsupported_health": {
                "category": "oracle_ui",
                "label": {"zh": "健康 / 婚恋 / 一生命运", "en": "Health, relationships, or life destiny", "ko": "건강, 관계, 평생 운명"},
                "description": {"zh": "不支持项。", "en": "Unsupported item.", "ko": "미지원 항목입니다."},
            },
            "unsupported_fortune_text": {
                "category": "oracle_ui",
                "label": {"zh": "传统断语和吉凶结论", "en": "Traditional fortune text and good/bad conclusions", "ko": "전통식 단정과 길흉 결론"},
                "description": {"zh": "不支持项。", "en": "Unsupported item.", "ko": "미지원 항목입니다."},
            },
            "birth_input": {
                "category": "oracle_ui",
                "label": {"zh": "先输入出生信息", "en": "Start with birth information", "ko": "출생 정보를 먼저 입력하세요"},
                "description": {"zh": "出生输入区标题。", "en": "Birth input heading.", "ko": "출생 입력 제목입니다."},
            },
            "year": {"category": "oracle_ui", "label": {"zh": "年", "en": "Year", "ko": "년"}, "description": {"zh": "年份。", "en": "Year.", "ko": "연도입니다."}},
            "month": {"category": "oracle_ui", "label": {"zh": "月", "en": "Month", "ko": "월"}, "description": {"zh": "月份。", "en": "Month.", "ko": "월입니다."}},
            "day": {"category": "oracle_ui", "label": {"zh": "日", "en": "Day", "ko": "일"}, "description": {"zh": "日期。", "en": "Day.", "ko": "일입니다."}},
            "hour": {"category": "oracle_ui", "label": {"zh": "时", "en": "Hour", "ko": "시"}, "description": {"zh": "小时。", "en": "Hour.", "ko": "시간입니다."}},
            "minute": {"category": "oracle_ui", "label": {"zh": "分", "en": "Minute", "ko": "분"}, "description": {"zh": "分钟。", "en": "Minute.", "ko": "분입니다."}},
            "gender": {"category": "oracle_ui", "label": {"zh": "性别", "en": "Gender", "ko": "성별"}, "description": {"zh": "性别。", "en": "Gender.", "ko": "성별입니다."}},
            "male": {"category": "oracle_ui", "label": {"zh": "男", "en": "Male", "ko": "남성"}, "description": {"zh": "男。", "en": "Male.", "ko": "남성입니다."}},
            "female": {"category": "oracle_ui", "label": {"zh": "女", "en": "Female", "ko": "여성"}, "description": {"zh": "女。", "en": "Female.", "ko": "여성입니다."}},
            "unknown": {"category": "oracle_ui", "label": {"zh": "未知", "en": "Unknown", "ko": "알 수 없음"}, "description": {"zh": "未知。", "en": "Unknown.", "ko": "알 수 없음입니다."}},
            "calendar": {"category": "oracle_ui", "label": {"zh": "历法", "en": "Calendar", "ko": "달력"}, "description": {"zh": "历法。", "en": "Calendar.", "ko": "달력입니다."}},
            "solar": {"category": "oracle_ui", "label": {"zh": "阳历", "en": "Solar", "ko": "양력"}, "description": {"zh": "阳历。", "en": "Solar.", "ko": "양력입니다."}},
            "lunar": {"category": "oracle_ui", "label": {"zh": "阴历", "en": "Lunar", "ko": "음력"}, "description": {"zh": "阴历。", "en": "Lunar.", "ko": "음력입니다."}},
            "lunar_leap_month": {"category": "oracle_ui", "label": {"zh": "闰月", "en": "Leap month", "ko": "윤달"}, "description": {"zh": "仅阴历出生日期使用。", "en": "Only used for lunar birth dates.", "ko": "음력 생년월일에만 사용합니다."}},
            "flow_year": {"category": "oracle_ui", "label": {"zh": "流年", "en": "Flow year", "ko": "세운 연도"}, "description": {"zh": "时间背景。", "en": "Time context.", "ko": "시간 맥락입니다."}},
            "pillar_panel": {"category": "oracle_ui", "label": {"zh": "命盘结构预览", "en": "Pillar structure preview", "ko": "명식 구조 미리보기"}, "description": {"zh": "六柱预览。", "en": "Six-pillar preview.", "ko": "육주 미리보기입니다."}},
            "natal_chart": {"category": "oracle_ui", "label": {"zh": "本命四柱", "en": "Natal chart", "ko": "본명 사주"}, "description": {"zh": "四柱。", "en": "Natal four pillars.", "ko": "본명 사주입니다."}},
            "luck_cycle": {"category": "oracle_ui", "label": {"zh": "大运", "en": "Luck cycle", "ko": "대운"}, "description": {"zh": "时间结构。", "en": "Time structure.", "ko": "시간 구조입니다."}},
            "current_luck_cycle": {"category": "oracle_ui", "label": {"zh": "当前大运", "en": "Current luck cycle", "ko": "현재 대운"}, "description": {"zh": "当前大运。", "en": "Current luck cycle.", "ko": "현재 대운입니다."}},
            "day_master": {"category": "oracle_ui", "label": {"zh": "日主", "en": "Day master", "ko": "일간"}, "description": {"zh": "日柱标记。", "en": "Day pillar marker.", "ko": "일주 표시입니다."}},
            "structure_preview_loading": {"category": "oracle_ui", "label": {"zh": "正在立盘...", "en": "Calculating pillars...", "ko": "명식을 계산 중..."}, "description": {"zh": "结构预览状态。", "en": "Structure preview state.", "ko": "구조 미리보기 상태입니다."}},
            "structure_preview_unavailable": {"category": "oracle_ui", "label": {"zh": "当前输入暂无法立盘", "en": "Structure preview unavailable for this input", "ko": "현재 입력으로는 구조 미리보기를 만들 수 없습니다"}, "description": {"zh": "结构预览错误。", "en": "Structure preview error.", "ko": "구조 미리보기 오류입니다."}},
            "question_context_prefix": {"category": "oracle_ui", "label": {"zh": "基于你的命盘结构", "en": "Based on your chart structure", "ko": "당신의 명식 구조를 기준으로"}, "description": {"zh": "问题引导上下文。", "en": "Question guidance context.", "ko": "질문 안내 맥락입니다."}},
            "month_structure": {"category": "oracle_ui", "label": {"zh": "月令结构", "en": "Month structure", "ko": "월지 구조"}, "description": {"zh": "问题引导上下文。", "en": "Question guidance context.", "ko": "질문 안내 맥락입니다."}},
            "stem": {"category": "oracle_ui", "label": {"zh": "天干", "en": "Stem", "ko": "천간"}, "description": {"zh": "结构术语。", "en": "Structure term.", "ko": "구조 용어입니다."}},
            "branch": {"category": "oracle_ui", "label": {"zh": "地支", "en": "Branch", "ko": "지지"}, "description": {"zh": "结构术语。", "en": "Structure term.", "ko": "구조 용어입니다."}},
            "hidden_stems": {"category": "oracle_ui", "label": {"zh": "藏干", "en": "Hidden stems", "ko": "지장간"}, "description": {"zh": "结构术语。", "en": "Structure term.", "ko": "구조 용어입니다."}},
            "element_wood": {"category": "oracle_ui", "label": {"zh": "木", "en": "Wood", "ko": "목"}, "description": {"zh": "五行。", "en": "Five-phase element.", "ko": "오행입니다."}},
            "element_fire": {"category": "oracle_ui", "label": {"zh": "火", "en": "Fire", "ko": "화"}, "description": {"zh": "五行。", "en": "Five-phase element.", "ko": "오행입니다."}},
            "element_earth": {"category": "oracle_ui", "label": {"zh": "土", "en": "Earth", "ko": "토"}, "description": {"zh": "五行。", "en": "Five-phase element.", "ko": "오행입니다."}},
            "element_metal": {"category": "oracle_ui", "label": {"zh": "金", "en": "Metal", "ko": "금"}, "description": {"zh": "五行。", "en": "Five-phase element.", "ko": "오행입니다."}},
            "element_water": {"category": "oracle_ui", "label": {"zh": "水", "en": "Water", "ko": "수"}, "description": {"zh": "五行。", "en": "Five-phase element.", "ko": "오행입니다."}},
            "yin": {"category": "oracle_ui", "label": {"zh": "阴", "en": "Yin", "ko": "음"}, "description": {"zh": "阴阳。", "en": "Yin-yang polarity.", "ko": "음양입니다."}},
            "yang": {"category": "oracle_ui", "label": {"zh": "阳", "en": "Yang", "ko": "양"}, "description": {"zh": "阴阳。", "en": "Yin-yang polarity.", "ko": "음양입니다."}},
            "structure_only_note": {"category": "oracle_ui", "label": {"zh": "结构说明，不代表吉凶。", "en": "Structure note, not a good/bad judgment.", "ko": "구조 설명이며 길흉 판단이 아닙니다."}, "description": {"zh": "结构提示。", "en": "Structure hint.", "ko": "구조 안내입니다."}},
            "day_master_note": {"category": "oracle_ui", "label": {"zh": "日主是结构基点，不代表命运结论。", "en": "Day master is the structural anchor, not a destiny conclusion.", "ko": "일간은 구조 기준점이며 운명 결론이 아닙니다."}, "description": {"zh": "日主提示。", "en": "Day master hint.", "ko": "일간 안내입니다."}},
            "clash": {"category": "oracle_ui", "label": {"zh": "冲", "en": "Clash", "ko": "충"}, "description": {"zh": "结构关系。", "en": "Structural relation.", "ko": "구조 관계입니다."}},
            "combination": {"category": "oracle_ui", "label": {"zh": "合", "en": "Combination", "ko": "합"}, "description": {"zh": "结构关系。", "en": "Structural relation.", "ko": "구조 관계입니다."}},
            "relation_structure_hint": {"category": "oracle_ui", "label": {"zh": "结构关系提示，不代表结果好坏。", "en": "Structural relation only, not an outcome judgment.", "ko": "구조 관계일 뿐 결과 판단이 아닙니다."}, "description": {"zh": "关系提示。", "en": "Relation hint.", "ko": "관계 안내입니다."}},
            "question_builder": {
                "category": "oracle_ui",
                "label": {"zh": "选择一个合适的问题", "en": "Choose a bounded question", "ko": "범위가 정해진 질문을 선택하세요"},
                "description": {"zh": "问题构建器标题。", "en": "Question builder heading.", "ko": "질문 구성 제목입니다."},
            },
            "custom_question": {"category": "oracle_ui", "label": {"zh": "你也可以修改问题", "en": "You can edit the question", "ko": "질문을 수정할 수 있습니다"}, "description": {"zh": "自定义问题。", "en": "Custom question.", "ko": "사용자 질문입니다."}},
            "q_income_stability": {"category": "oracle_question", "label": {"zh": "我的收入稳定性结构如何？", "en": "How is my income stability structure?", "ko": "나의 소득 안정성 구조는 어떤가요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_income_factors": {"category": "oracle_question", "label": {"zh": "当前结构中哪些因素影响收入稳定？", "en": "Which structure factors affect income stability?", "ko": "현재 구조에서 어떤 요소가 소득 안정성에 영향을 주나요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_income_path_structure": {"category": "oracle_question", "label": {"zh": "如果只按结构看，收入路径是被哪些信号组织起来的？", "en": "Structurally, which signals organize the income path?", "ko": "구조만 보면 소득 경로는 어떤 신호들로 조직되나요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_time_context": {"category": "oracle_question", "label": {"zh": "这个流年只作为时间背景，会触发哪些结构关系？", "en": "As context only, what relations does this flow year trigger?", "ko": "예측이 아닌 시간 맥락으로서 이 세운은 어떤 구조 관계를 만들까요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_structure_overview": {"category": "oracle_question", "label": {"zh": "如果只看结构，这张命盘先呈现哪些特征？", "en": "Looking only at structure, what features appear first?", "ko": "구조만 보면 이 명식에서 먼저 보이는 특징은 무엇인가요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_month_command_anchor": {"category": "oracle_question", "label": {"zh": "月令在这张命盘里先提供了什么结构背景？", "en": "What structural background does the month branch provide here?", "ko": "월지는 이 명식에서 어떤 구조 배경을 먼저 제공하나요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_ten_god_metadata": {"category": "oracle_question", "label": {"zh": "十神标签在这里为什么只是关系元数据，而不是断语？", "en": "Why are Ten God labels relationship metadata here rather than verdicts?", "ko": "여기서 십성 라벨은 왜 단정이 아니라 관계 메타데이터인가요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_element_flow_metadata": {"category": "oracle_question", "label": {"zh": "五行生克在这里应该怎样只按结构关系阅读？", "en": "How should element generation/control be read only as structural relation here?", "ko": "오행 생극은 여기서 구조 관계로만 어떻게 읽어야 하나요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_vault_structure": {"category": "oracle_question", "label": {"zh": "这张命盘里的墓库结构，应该如何只按结构层阅读？", "en": "How should the vault structure in this chart be read only at the structural layer?", "ko": "이 명식의 묘고 구조는 구조 층에서만 어떻게 읽어야 하나요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_wealth_accessibility": {"category": "oracle_question", "label": {"zh": "财富可达性这个信号是由哪些结构支持的？", "en": "Which structures support the wealth accessibility signal?", "ko": "재성 접근성 신호는 어떤 구조가 뒷받침하나요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_volatility_factors": {"category": "oracle_question", "label": {"zh": "哪些结构因素会增加收入稳定性的波动？", "en": "Which structural factors increase income-stability volatility?", "ko": "어떤 구조 요소가 소득 안정성의 변동성을 높이나요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_signal_combination": {"category": "oracle_question", "label": {"zh": "这个结果主要由哪几个结构信号共同形成？", "en": "Which structure signals jointly form this result?", "ko": "이 결과는 어떤 구조 신호들이 함께 만든 것인가요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_time_context_boundary": {"category": "oracle_question", "label": {"zh": "哪些结构关系只是背景，不应该直接理解成预测？", "en": "Which relations are background only and should not be read as prediction?", "ko": "어떤 구조 관계가 배경일 뿐 예측으로 읽으면 안 되나요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_read_result_not_fortune": {"category": "oracle_question", "label": {"zh": "我应该如何阅读这个结果，而不是把它当成断语？", "en": "How should I read this result without treating it as a fortune statement?", "ko": "이 결과를 단정문이 아니라 어떻게 읽어야 하나요?"}, "description": {"zh": "支持问题。", "en": "Supported question.", "ko": "지원 질문입니다."}},
            "q_income_continuity": {"category": "oracle_question", "label": {"zh": "当前结构中，哪些因素会影响收入稳定性的连续性？", "en": "Which current structural factors affect income-stability continuity?", "ko": "현재 구조에서 어떤 요소가 소득 안정성의 연속성에 영향을 주나요?"}, "description": {"zh": "结构问题。", "en": "Structure question.", "ko": "구조 질문입니다."}},
            "q_accessibility_signals": {"category": "oracle_question", "label": {"zh": "哪些结构信号主要影响财富可达性？", "en": "Which structure signals mainly affect wealth accessibility?", "ko": "어떤 구조 신호가 재성 접근성에 주로 영향을 주나요?"}, "description": {"zh": "结构问题。", "en": "Structure question.", "ko": "구조 질문입니다."}},
            "q_cautious_reading": {"category": "oracle_question", "label": {"zh": "哪些结构关系会让结果更需要谨慎阅读？", "en": "Which structural relations make this result require more cautious reading?", "ko": "어떤 구조 관계 때문에 이 결과를 더 신중하게 읽어야 하나요?"}, "description": {"zh": "结构问题。", "en": "Structure question.", "ko": "구조 질문입니다."}},
            "q_primary_auxiliary_signals": {"category": "oracle_question", "label": {"zh": "这个结果中，哪些信号是主信号，哪些只是辅助信号？", "en": "In this result, which signals are primary and which are supporting?", "ko": "이 결과에서 어떤 신호가 주 신호이고 어떤 신호가 보조 신호인가요?"}, "description": {"zh": "结构问题。", "en": "Structure question.", "ko": "구조 질문입니다."}},
            "q_luck_flow_layers": {"category": "oracle_question", "label": {"zh": "大运和流年在这里分别属于哪一层结构？", "en": "Which structural layer do luck cycle and flow year belong to here?", "ko": "여기서 대운과 세운은 각각 어떤 구조 층에 속하나요?"}, "description": {"zh": "时间边界问题。", "en": "Time boundary question.", "ko": "시간 경계 질문입니다."}},
            "q_time_not_inference": {"category": "oracle_question", "label": {"zh": "为什么当前时间结构不直接改变收入稳定性结果？", "en": "Why does the current time structure not directly change the income-stability result?", "ko": "왜 현재 시간 구조가 소득 안정성 결과를 직접 바꾸지 않나요?"}, "description": {"zh": "时间边界问题。", "en": "Time boundary question.", "ko": "시간 경계 질문입니다."}},
            "q_day_master_month_anchor": {"category": "oracle_question", "label": {"zh": "这张命盘先看日主和月令，能读出什么结构基点？", "en": "Starting from the day master and month branch, what structural baseline appears?", "ko": "일간과 월지를 먼저 보면 어떤 구조 기준점이 보이나요?"}, "description": {"zh": "结构基点问题。", "en": "Structural baseline question.", "ko": "구조 기준 질문입니다."}},
            "q_hidden_stem_role": {"category": "oracle_question", "label": {"zh": "藏干在这张命盘里只是补充信息，还是会影响结构理解？", "en": "Are hidden stems only supporting information here, or do they affect structural reading?", "ko": "지장간은 여기서 보조 정보일 뿐인가요, 아니면 구조 이해에 영향을 주나요?"}, "description": {"zh": "藏干结构问题。", "en": "Hidden-stem structure question.", "ko": "지장간 구조 질문입니다."}},
            "q_branch_relation_detail": {"category": "oracle_question", "label": {"zh": "当前看得到的冲合关系，分别发生在本命还是时间背景？", "en": "Do the visible clash/combination relations occur inside the natal chart or in timing context?", "ko": "현재 보이는 충합 관계는 원국 안에서 생기나요, 아니면 시간 배경에서 생기나요?"}, "description": {"zh": "地支关系问题。", "en": "Branch relation question.", "ko": "지지 관계 질문입니다."}},
            "q_time_vs_natal_relation": {"category": "oracle_question", "label": {"zh": "大运、流年和本命发生关系时，哪些只算背景，哪些才算本命结构？", "en": "When luck/flow relates to the natal chart, what is only background and what belongs to natal structure?", "ko": "대운·세운이 원국과 관계를 만들 때 무엇은 배경이고 무엇은 원국 구조인가요?"}, "description": {"zh": "时间分层问题。", "en": "Timing-layer question.", "ko": "시간 층위 질문입니다."}},
            "q_combination_context": {"category": "oracle_question", "label": {"zh": "如果出现合或六合关系，它在这里只表示什么结构连接？", "en": "If a combination relation appears, what structural link does it indicate here?", "ko": "합 관계가 나타난다면 여기서는 어떤 구조 연결만 뜻하나요?"}, "description": {"zh": "六合结构问题。", "en": "Combination structure question.", "ko": "합 구조 질문입니다."}},
            "q_three_harmony_context": {"category": "oracle_question", "label": {"zh": "如果出现三合结构，它在这里只表示什么结构连接？", "en": "If a three-harmony structure appears, what structural link does it indicate here?", "ko": "삼합 구조가 나타난다면 여기서는 어떤 구조 연결만 뜻하나요?"}, "description": {"zh": "三合结构问题。", "en": "Three-harmony structure question.", "ko": "삼합 구조 질문입니다."}},
            "q_no_good_bad": {"category": "oracle_question", "label": {"zh": "这个系统为什么不直接判断“好坏”？", "en": "Why does this system avoid direct good/bad judgments?", "ko": "왜 이 시스템은 직접적인 길흉 판단을 피하나요?"}, "description": {"zh": "边界问题。", "en": "Boundary question.", "ko": "경계 질문입니다."}},
            "q_result_card_boundary": {"category": "oracle_question", "label": {"zh": "为什么结果卡不是传统断语？", "en": "Why is the result card not traditional fortune text?", "ko": "왜 결과 카드는 전통식 단정문이 아닌가요?"}, "description": {"zh": "边界问题。", "en": "Boundary question.", "ko": "경계 질문입니다."}},
            "q_analyst_review_needed": {"category": "oracle_question", "label": {"zh": "哪些内容需要命理师进一步审核？", "en": "Which parts need further practitioner review?", "ko": "어떤 부분은 명리사의 추가 검토가 필요한가요?"}, "description": {"zh": "审核问题。", "en": "Review question.", "ko": "검토 질문입니다."}},
            "question_helpful_prompt": {"category": "oracle_ui", "label": {"zh": "这个引导问题有帮助吗？", "en": "Was this guided question helpful?", "ko": "이 안내 질문이 도움이 되었나요?"}, "description": {"zh": "问题反馈。", "en": "Question feedback.", "ko": "질문 피드백입니다."}},
            "answer_helpful_prompt": {"category": "oracle_ui", "label": {"zh": "这个回答有帮助吗？", "en": "Was this answer helpful?", "ko": "이 답변이 도움이 되었나요?"}, "description": {"zh": "回答反馈。", "en": "Answer feedback.", "ko": "답변 피드백입니다."}},
            "helpful_yes": {"category": "oracle_ui", "label": {"zh": "有帮助", "en": "Helpful", "ko": "도움됨"}, "description": {"zh": "反馈按钮。", "en": "Feedback button.", "ko": "피드백 버튼입니다."}},
            "helpful_no": {"category": "oracle_ui", "label": {"zh": "没帮助", "en": "Not helpful", "ko": "도움 안 됨"}, "description": {"zh": "反馈按钮。", "en": "Feedback button.", "ko": "피드백 버튼입니다."}},
            "question_feedback_saved": {"category": "oracle_ui", "label": {"zh": "问题反馈已记录，等待分析师审核。", "en": "Question feedback recorded for analyst review.", "ko": "질문 피드백이 분석가 검토용으로 기록되었습니다."}, "description": {"zh": "反馈完成。", "en": "Feedback saved.", "ko": "피드백 저장입니다."}},
            "answer_feedback_saved": {"category": "oracle_ui", "label": {"zh": "回答反馈已记录，后续会用于优化问题推荐。", "en": "Answer feedback recorded and will inform future question guidance.", "ko": "답변 피드백이 기록되었고 이후 질문 안내 개선에 참고됩니다."}, "description": {"zh": "回答反馈完成。", "en": "Answer feedback saved.", "ko": "답변 피드백 저장입니다."}},
            "run_analysis": {"category": "oracle_ui", "label": {"zh": "八字测算", "en": "Read Bazi", "ko": "사주 보기"}, "description": {"zh": "主按钮。", "en": "Primary CTA.", "ko": "주요 버튼입니다."}},
            "running": {"category": "oracle_ui", "label": {"zh": "测算中...", "en": "Reading...", "ko": "보는 중..."}, "description": {"zh": "运行状态。", "en": "Running state.", "ko": "실행 상태입니다."}},
            "guided_answer": {"category": "oracle_ui", "label": {"zh": "结构回答", "en": "Structured answer", "ko": "구조 답변"}, "description": {"zh": "针对当前问题的回答区。", "en": "Answer area for the current question.", "ko": "현재 질문에 대한 답변 영역입니다."}},
            "question_answer_only": {"category": "oracle_badge", "label": {"zh": "回答当前问题", "en": "Answers current question", "ko": "현재 질문 답변"}, "description": {"zh": "Answer 区块边界。", "en": "Answer block boundary.", "ko": "답변 블록 경계입니다."}},
            "selected_question": {"category": "oracle_ui", "label": {"zh": "当前问题", "en": "Current question", "ko": "현재 질문"}, "description": {"zh": "Answer 区块中的问题。", "en": "Question shown in the Answer block.", "ko": "답변 블록에 표시되는 질문입니다."}},
            "answer_empty": {"category": "oracle_ui", "label": {"zh": "当前问题暂无结构回答。", "en": "No structured answer is available for this question yet.", "ko": "현재 질문에 대한 구조 답변이 아직 없습니다."}, "description": {"zh": "Answer 空状态。", "en": "Answer empty state.", "ko": "답변 빈 상태입니다."}},
            "result": {"category": "oracle_ui", "label": {"zh": "结构化结果", "en": "Structured result", "ko": "구조화 결과"}, "description": {"zh": "结果标题。", "en": "Result heading.", "ko": "결과 제목입니다."}},
            "chart_structure": {"category": "oracle_ui", "label": {"zh": "四柱结构", "en": "Chart structure", "ko": "사주 구조"}, "description": {"zh": "结构展示。", "en": "Chart structure.", "ko": "사주 구조입니다."}},
            "income_stability_result": {"category": "oracle_ui", "label": {"zh": "收入稳定性结构摘要", "en": "Income stability structure summary", "ko": "소득 안정성 구조 요약"}, "description": {"zh": "结果卡标题。", "en": "Result card heading.", "ko": "결과 카드 제목입니다."}},
            "evidence": {"category": "oracle_ui", "label": {"zh": "规则依据", "en": "Rule basis", "ko": "규칙 근거"}, "description": {"zh": "证据折叠。", "en": "Evidence accordion.", "ko": "근거 접기 영역입니다."}},
            "evidence_summary": {"category": "oracle_ui", "label": {"zh": "这里仅展示结构摘要；详细依据保留在分析端。", "en": "Only the structure summary is shown here; detailed basis stays in analyst review.", "ko": "여기에는 구조 요약만 표시되며 자세한 근거는 분석 검토에 남깁니다."}, "description": {"zh": "用户端证据说明。", "en": "User evidence summary.", "ko": "사용자 근거 요약입니다."}},
            "source_summary": {"category": "oracle_ui", "label": {"zh": "结构输入 + 规则摘要", "en": "Structure input + rule summary", "ko": "구조 입력 + 규칙 요약"}, "description": {"zh": "用户端证据来源。", "en": "User-facing source summary.", "ko": "사용자용 근거 출처입니다."}},
            "next_questions": {"category": "oracle_ui", "label": {"zh": "继续提问", "en": "Ask next", "ko": "이어서 질문"}, "description": {"zh": "下一步追问。", "en": "Follow-up guidance.", "ko": "후속 질문 안내입니다."}},
            "follow_rule_basis": {"category": "oracle_question", "label": {"zh": "查看这条判断的规则依据", "en": "Show the rule basis for this result", "ko": "이 결과의 규칙 근거 보기"}, "description": {"zh": "追问。", "en": "Follow-up.", "ko": "후속 질문입니다."}},
            "follow_time_structure": {"category": "oracle_question", "label": {"zh": "查看流年结构关系", "en": "Show flow-year structure relations", "ko": "세운 구조 관계 보기"}, "description": {"zh": "追问。", "en": "Follow-up.", "ko": "후속 질문입니다."}},
            "follow_feedback": {"category": "oracle_question", "label": {"zh": "提交反馈给分析师", "en": "Submit feedback for analyst review", "ko": "분석가 검토용 피드백 제출"}, "description": {"zh": "追问。", "en": "Follow-up.", "ko": "후속 질문입니다."}},
            "deterministic": {"category": "oracle_badge", "label": {"zh": "规则生成", "en": "Rule-based", "ko": "규칙 기반"}, "description": {"zh": "非 LLM 主结论。", "en": "Not an LLM primary result.", "ko": "LLM 주 결론이 아닙니다."}},
            "context_only": {"category": "oracle_badge", "label": {"zh": "仅作时间背景", "en": "Context only", "ko": "맥락 전용"}, "description": {"zh": "时间边界。", "en": "Time boundary.", "ko": "시간 경계입니다."}},
            "self_capacity": {"category": "signal", "label": {"zh": "自我承载力", "en": "Self capacity", "ko": "자기 수용력"}, "description": {"zh": "内部 key: self_capacity。", "en": "Internal key: self_capacity.", "ko": "내부 key: self_capacity."}},
            "wealth_presence": {"category": "signal", "label": {"zh": "财富结构出现度", "en": "Wealth presence", "ko": "재성 출현도"}, "description": {"zh": "内部 key: wealth_presence。", "en": "Internal key: wealth_presence.", "ko": "내부 key: wealth_presence."}},
            "wealth_accessibility": {"category": "signal", "label": {"zh": "财富可达性", "en": "Wealth accessibility", "ko": "재성 접근성"}, "description": {"zh": "内部 key: wealth_accessibility。", "en": "Internal key: wealth_accessibility.", "ko": "내부 key: wealth_accessibility."}},
            "volatility": {"category": "signal", "label": {"zh": "波动性", "en": "Volatility", "ko": "변동성"}, "description": {"zh": "内部 key: volatility。", "en": "Internal key: volatility.", "ko": "내부 key: volatility."}},
            "structure_binding": {"category": "signal", "label": {"zh": "结构牵制", "en": "Structure binding", "ko": "구조 결속"}, "description": {"zh": "内部 key: structure_binding。", "en": "Internal key: structure_binding.", "ko": "내부 key: structure_binding."}},
            "wealth_structure": {"category": "theme", "label": {"zh": "财富结构", "en": "Wealth structure", "ko": "재물 구조"}, "description": {"zh": "主题 key。", "en": "Theme key.", "ko": "테마 key입니다."}},
            "risk_opportunity": {"category": "theme", "label": {"zh": "风险与机会结构", "en": "Risk and opportunity structure", "ko": "위험과 기회 구조"}, "description": {"zh": "主题 key。", "en": "Theme key.", "ko": "테마 key입니다."}},
            "stable": {"category": "value", "label": {"zh": "稳定", "en": "Stable", "ko": "안정"}, "description": {"zh": "信号值。", "en": "Signal value.", "ko": "신호 값입니다."}},
            "high": {"category": "value", "label": {"zh": "高", "en": "High", "ko": "높음"}, "description": {"zh": "信号值。", "en": "Signal value.", "ko": "신호 값입니다."}},
            "medium": {"category": "value", "label": {"zh": "中", "en": "Medium", "ko": "중간"}, "description": {"zh": "信号值。", "en": "Signal value.", "ko": "신호 값입니다."}},
            "clear": {"category": "value", "label": {"zh": "清晰", "en": "Clear", "ko": "명확"}, "description": {"zh": "信号值。", "en": "Signal value.", "ko": "신호 값입니다."}},
            "low": {"category": "value", "label": {"zh": "低", "en": "Low", "ko": "낮음"}, "description": {"zh": "信号值。", "en": "Signal value.", "ko": "신호 값입니다."}},
            "none": {"category": "value", "label": {"zh": "无", "en": "None", "ko": "없음"}, "description": {"zh": "信号值。", "en": "Signal value.", "ko": "신호 값입니다."}},
            "income_stability": {
                "category": "signal",
                "label": {"zh": "收入稳定性结构信号", "en": "Income Stability Signal", "ko": "소득 안정성 구조 신호"},
                "description": {"zh": "财富域结构信号。", "en": "A wealth-domain structure signal.", "ko": "재물 영역의 구조 신호입니다."},
            },
            "time_structure": {
                "category": "boundary",
                "label": {"zh": "时间结构", "en": "Time Structure", "ko": "시간 구조"},
                "description": {"zh": "时间背景上下文。", "en": "Time-context background.", "ko": "시간 배경 맥락입니다."},
            },
            "knowledge_evidence_store": {
                "category": "system",
                "label": {"zh": "知识证据库", "en": "Knowledge Evidence Store", "ko": "지식 증거 저장소"},
                "description": {"zh": "Reviewed evidence templates，不是可执行规则库。", "en": "Reviewed evidence templates, not an executable rule DB.", "ko": "검토된 증거 템플릿이며 실행 규칙 DB가 아닙니다."},
            },
            "analyst_review_required": {
                "category": "guardrail",
                "label": {"zh": "需要分析师审核", "en": "Analyst Review Required", "ko": "분석가 검토 필요"},
                "description": {"zh": "反馈和 promotion 不会自动激活规则。", "en": "Feedback and promotion requests do not auto-activate rules.", "ko": "피드백과 승격 요청은 규칙을 자동 활성화하지 않습니다."},
            },
        },
    }


def _empty_state() -> Dict[str, Any]:
    return {
        "version": LAB_VERSION,
        "feedback": [],
        "guided_question_reviews": [],
        "guided_question_proposals": [],
        "guided_question_library_versions": [],
        "guided_question_audits": [],
        "bazi_rule_proposals": [],
        "bazi_rule_versions": [],
        "synthetic_promotion_candidates": [],
        "governance_releases": [],
        "knowledge_review_batches": [],
        "knowledge_batch_proposal_runs": [],
        "rule_impacts": [],
        "revision_proposals": [],
        "active_rule_revisions": [],
        "validation_cases": [],
        "validation_runs": [],
        "promotion_requests": [],
        "label_contract": _default_label_contract(),
    }


def _current_product_label_overrides() -> Dict[str, Any]:
    return {
        "run_analysis": {"category": "oracle_ui", "label": {"zh": "八字测算", "en": "Read Bazi", "ko": "사주 보기"}, "description": {"zh": "主按钮。", "en": "Primary CTA.", "ko": "주요 버튼입니다."}},
        "running": {"category": "oracle_ui", "label": {"zh": "测算中...", "en": "Reading...", "ko": "보는 중..."}, "description": {"zh": "运行状态。", "en": "Running state.", "ko": "실행 상태입니다."}},
        "next_questions": {"category": "oracle_ui", "label": {"zh": "继续提问", "en": "Ask next", "ko": "이어서 질문"}, "description": {"zh": "下一步追问。", "en": "Follow-up guidance.", "ko": "후속 질문 안내입니다."}},
        "answer_empty": {
            "category": "oracle_ui",
            "label": {
                "zh": "这个问题暂时没有匹配到可解释的命盘结构，我不会硬编答案。你可以换一个上方推荐问题，或把问题改得更具体一点。",
                "en": "This question does not match an explainable chart structure yet, so the system will not invent an answer. Try a recommended question above or make the question more specific.",
                "ko": "이 질문은 아직 설명 가능한 명식 구조와 연결되지 않아 답변을 지어내지 않습니다. 위 추천 질문을 선택하거나 질문을 더 구체적으로 바꿔 주세요.",
            },
            "description": {"zh": "空状态。", "en": "Empty state.", "ko": "빈 상태입니다."},
        },
        "answer_helpful_prompt": {"category": "oracle_ui", "label": {"zh": "这个回答有帮助吗？", "en": "Was this answer helpful?", "ko": "이 답변이 도움이 되었나요?"}, "description": {"zh": "回答反馈。", "en": "Answer feedback.", "ko": "답변 피드백입니다."}},
        "answer_feedback_saved": {"category": "oracle_ui", "label": {"zh": "回答反馈已记录，后续会用于优化问题推荐。", "en": "Answer feedback recorded and will inform future question guidance.", "ko": "답변 피드백이 기록되었고 이후 질문 안내 개선에 참고됩니다."}, "description": {"zh": "回答反馈完成。", "en": "Answer feedback saved.", "ko": "답변 피드백 저장입니다."}},
    }


def _load_state(settings: Dict[str, Any] | None = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    db = dict((settings or {}).get("db") or {})
    url = resolve_postgres_url(db) if db.get("enabled") else ""
    if url:
        try:
            with _postgres_connection(url) as conn:
                _ensure_db_schema(conn)
                return _db_load_state(conn), {"backend": "postgres"}
        except Exception as exc:
            return _file_load_state(), {"backend": "file", "fallback_reason": str(exc)}
    return _file_load_state(), {"backend": "file"}


def _save_state(state: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    _file_save_state(state)
    db = dict((settings or {}).get("db") or {})
    url = resolve_postgres_url(db) if db.get("enabled") else ""
    if url:
        try:
            with _postgres_connection(url) as conn:
                _ensure_db_schema(conn)
                _db_save_state(conn, state)
            return {"backend": "postgres", "fallback": "file_mirror"}
        except Exception as exc:
            return {"backend": "file", "fallback_reason": str(exc)}
    return {"backend": "file"}


def _file_load_state() -> Dict[str, Any]:
    if not LAB_FILE.exists():
        return _empty_state()
    try:
        payload = json.loads(LAB_FILE.read_text(encoding="utf-8"))
    except Exception:
        return _empty_state()
    state = _empty_state()
    if isinstance(payload, dict):
        for key in ["feedback", "guided_question_reviews", "guided_question_proposals", "guided_question_library_versions", "guided_question_audits", "bazi_rule_proposals", "bazi_rule_versions", "synthetic_promotion_candidates", "governance_releases", "knowledge_review_batches", "knowledge_batch_proposal_runs", "rule_impacts", "revision_proposals", "active_rule_revisions", "validation_cases", "validation_runs", "promotion_requests"]:
            if isinstance(payload.get(key), list):
                state[key] = list(payload[key])
        if isinstance(payload.get("label_contract"), dict):
            state["label_contract"] = dict(payload["label_contract"])
    return state


def _file_save_state(state: Dict[str, Any]) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    LAB_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _ensure_db_schema(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS v19_lab_ledger (
                ledger_key TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                updated_at TIMESTAMPTZ
            )
            """
        )
    conn.commit()


def _db_load_state(conn: Any) -> Dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute("SELECT payload FROM v19_lab_ledger WHERE ledger_key = %s", ("lab_state",))
        row = cur.fetchone()
    if not row:
        return _file_load_state()
    payload = row[0]
    if isinstance(payload, str):
        return dict(json.loads(payload))
    return dict(payload)


def _db_save_state(conn: Any, state: Dict[str, Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO v19_lab_ledger (ledger_key, payload, updated_at)
            VALUES (%s, %s::jsonb, %s)
            ON CONFLICT (ledger_key)
            DO UPDATE SET payload = EXCLUDED.payload, updated_at = EXCLUDED.updated_at
            """,
            ("lab_state", json.dumps(state, ensure_ascii=False, sort_keys=True), utc_now()),
        )
    conn.commit()


def _clean(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _role(value: Any) -> str:
    role = _clean(value, "user")
    return role if role in ALLOWED_ROLES else "user"


def _guided_question_review_map(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(row.get("question_key") or ""): dict(row)
        for row in state.get("guided_question_reviews", [])
        if isinstance(row, dict) and row.get("question_key")
    }


def _top_counts(counts: Dict[str, int], limit: int = 12) -> List[Dict[str, Any]]:
    return [
        {"key": key, "count": value}
        for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = _clean(row.get(key), "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _answer_quality_item_from_audit(row: Dict[str, Any]) -> Dict[str, Any]:
    composed = row.get("composed_text") if isinstance(row.get("composed_text"), dict) else {}
    text = str(composed.get("zh") or composed.get("text") or "")
    context = {
        "question_contract": dict(row.get("question_contract") or {}),
        "intent": dict(row.get("intent") or {}),
        "retrieved_facts": dict(row.get("retrieved_facts") or {}),
        "observed_facts": dict(row.get("observed_facts") or {}),
        "rating": 0,
    }
    quality = _answer_quality_score(text, context)
    return {
        "source_type": "guided_question_audit",
        "source_id": row.get("audit_id"),
        "created_at": row.get("created_at"),
        "question_key": row.get("selected_question_key") or (context["question_contract"].get("key") or ""),
        "answer_kind": context["intent"].get("answer_kind") or "",
        "score": quality["score"],
        "status": quality["status"],
        "risk_flags": quality["risk_flags"],
        "checks": quality["checks"],
        "text_preview": " ".join(text.split())[:220],
        "suggested_review_action": quality["suggested_review_action"],
        "guardrails": ["AUDIT_QUALITY_DERIVED", "NO_RUNTIME_MUTATION"],
    }


def _answer_quality_item_from_feedback(row: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(row.get("payload") or {})
    metadata = dict(row.get("metadata") or {})
    text = str(payload.get("answer_text") or metadata.get("answer_text") or "")
    context = {
        "question_contract": dict(payload.get("question_contract") or metadata.get("question_contract") or {}),
        "intent": dict(payload.get("intent") or metadata.get("intent") or {}),
        "retrieved_facts": dict(payload.get("retrieved_facts") or metadata.get("retrieved_facts") or {}),
        "observed_facts": dict(payload.get("observed_facts") or metadata.get("observed_facts") or {}),
        "rating": _bounded_int(row.get("rating"), 0, -2, 2),
    }
    quality = _answer_quality_score(text, context)
    return {
        "source_type": "guided_question_feedback",
        "source_id": row.get("feedback_id"),
        "created_at": row.get("created_at"),
        "question_key": row.get("subject_id") or metadata.get("question_key") or context["question_contract"].get("key") or "",
        "answer_kind": payload.get("answer_kind") or metadata.get("answer_kind") or context["intent"].get("answer_kind") or "",
        "rating": context["rating"],
        "score": quality["score"],
        "status": quality["status"],
        "risk_flags": quality["risk_flags"],
        "checks": quality["checks"],
        "text_preview": " ".join(text.split())[:220],
        "suggested_review_action": quality["suggested_review_action"],
        "guardrails": ["FEEDBACK_QUALITY_DERIVED", "NO_AUTO_LEARNING", "ANALYST_REVIEW_REQUIRED"],
    }


def _answer_quality_score(text: str, context: Dict[str, Any]) -> Dict[str, Any]:
    clean = str(text or "").strip()
    intent = dict(context.get("intent") or {})
    checks = [
        _quality_check("answer_text_present", bool(clean), "Answer text is present."),
        _quality_check("answer_not_truncated", not _answer_text_looks_truncated(clean), "Answer does not look cut off."),
        _quality_check("no_internal_markers", not any(marker in clean for marker in INTERNAL_ANSWER_MARKERS), "Answer hides internal rule/debug markers."),
        _quality_check("no_prediction_terms", not any(term in clean for term in FORBIDDEN_ANSWER_TERMS), "Answer avoids prediction wording."),
        _quality_check("question_contract_present", bool(context.get("question_contract")), "Question contract is attached."),
        _quality_check("intent_present", bool(intent.get("intent_id") or intent.get("answer_kind")), "Routed intent is attached."),
        _quality_check("retrieved_facts_present", bool(context.get("retrieved_facts")), "Retrieved facts are attached."),
        _quality_check("observed_facts_present", bool(context.get("observed_facts")), "Observed facts are attached."),
        _quality_check(
            "unsupported_has_boundary",
            intent.get("supported") is not False or ("不支持" in clean or "不会硬编" in clean or "结构分析范围" in clean),
            "Unsupported questions have an explicit boundary.",
        ),
        _quality_check("user_feedback_not_negative", _bounded_int(context.get("rating"), 0, -2, 2) >= 0, "User feedback is not negative."),
    ]
    risk_flags = [row["name"] for row in checks if not row["passed"]]
    critical = {"answer_text_present", "answer_not_truncated", "no_internal_markers", "no_prediction_terms", "unsupported_has_boundary"}
    failed_critical = [flag for flag in risk_flags if flag in critical]
    score = max(0, 100 - len(failed_critical) * 30 - (len(risk_flags) - len(failed_critical)) * 10)
    if failed_critical:
        status = "fail"
    elif risk_flags:
        status = "watch"
    else:
        status = "pass"
    return {
        "score": score,
        "status": status,
        "risk_flags": risk_flags,
        "checks": checks,
        "suggested_review_action": _answer_quality_action(status, risk_flags),
    }


def _quality_check(name: str, passed: bool, note: str) -> Dict[str, Any]:
    return {"name": name, "passed": bool(passed), "note": note}


def _answer_text_looks_truncated(text: str) -> bool:
    clean = str(text or "").strip()
    if len(clean) < 24:
        return False
    if clean.count("“") != clean.count("”"):
        return True
    if clean.count("‘") != clean.count("’"):
        return True
    if clean.count("（") != clean.count("）"):
        return True
    if clean.count("(") != clean.count(")"):
        return True
    if clean.endswith(("，", "、", "：", "；", ",", ":", ";", "的", "和", "与", "或", "而", "以及", "因为", "所以", "但是", "并且", "同时", "其中", "例如", "比如", "包括", "位于", "出现于")):
        return True
    if len(clean) >= 120 and clean[-1] not in "。！？.!?）】”’」』":
        return True
    return False


def _answer_quality_action(status: str, risk_flags: List[str]) -> str:
    if status == "pass":
        return "no_action"
    if "answer_not_truncated" in risk_flags:
        return "review_llm_rewrite_or_fallback"
    if "no_internal_markers" in risk_flags:
        return "remove_internal_marker_from_user_copy"
    if "no_prediction_terms" in risk_flags:
        return "tighten_guardrail_or_composer"
    if "user_feedback_not_negative" in risk_flags:
        return "analyst_review_answer_helpfulness"
    return "analyst_review"


def _answer_quality_recommendations(by_status: Dict[str, int], risk_flags: Dict[str, int]) -> List[str]:
    rows: List[str] = []
    if by_status.get("fail"):
        rows.append("Fix fail items before expanding the question library.")
    if risk_flags.get("answer_not_truncated"):
        rows.append("LLM rewrite or frontend rendering produced cut-off text; use deterministic fallback and inspect max token/timeout settings.")
    if risk_flags.get("no_internal_markers"):
        rows.append("Remove internal rule/debug markers from user-facing answer copy.")
    if risk_flags.get("no_prediction_terms"):
        rows.append("Tighten answer guardrails before allowing this wording in production.")
    if risk_flags.get("user_feedback_not_negative"):
        rows.append("Review not-helpful feedback with the retrieved facts and question contract attached.")
    if not rows:
        rows.append("No quality risks detected in saved guided-question answer records.")
    return rows


def _guided_question_audit_recommendations(by_status: Dict[str, int], failed_checks: Dict[str, int], unsupported: Dict[str, int]) -> List[str]:
    recommendations = []
    if by_status.get("fail", 0):
        recommendations.append("先修复失败审计最多的 check，再扩展问题库。")
    if failed_checks.get("relations_have_layers", 0):
        recommendations.append("优先检查地支关系 schema，确保本命、大运、流年关系都有 layer。")
    if failed_checks.get("contract_intent_matches_router", 0):
        recommendations.append("检查 Question Registry 的 intent 和 Intent Router 映射是否一致。")
    if failed_checks.get("answer_text_present", 0):
        recommendations.append("检查 Answer Composer 是否覆盖对应 intent，避免空回答。")
    if unsupported:
        recommendations.append("统计 unsupported 主题，决定是继续拒答，还是新增受控结构主题。")
    if not recommendations:
        recommendations.append("当前审计记录没有暴露高频断裂，可继续用保存审计样本扩大覆盖。")
    return recommendations


def _find_guided_question_proposal(state: Dict[str, Any], proposal_id: str) -> Dict[str, Any] | None:
    clean = _clean(proposal_id)
    for row in state.get("guided_question_proposals", []):
        if row.get("proposal_id") == clean:
            return row
    return None


def _validate_guided_question_proposal(proposal: Dict[str, Any]) -> List[Dict[str, Any]]:
    label = dict(proposal.get("proposed_label") or {})
    metadata = dict(proposal.get("proposed_metadata") or {})
    action = _clean(proposal.get("proposed_action"))
    text = " ".join(str(label.get(locale) or "") for locale in ["zh", "en", "ko"])
    related = _string_list(metadata.get("related_questions"))
    required = _string_list(metadata.get("required_context") or metadata.get("required"))
    depth = _clean(metadata.get("depth"), "beginner")
    checks = [
        {"name": "forbidden_prediction_terms", "passed": not any(term.lower() in text.lower() for term in FORBIDDEN_GUIDED_QUESTION_TERMS)},
        {"name": "required_context_allowed", "passed": all(item in ALLOWED_GUIDED_REQUIRED_CONTEXT for item in required)},
        {"name": "depth_allowed", "passed": depth in ALLOWED_GUIDED_DEPTH},
        {"name": "related_questions_present_for_reorder", "passed": action != "reorder_path" or bool(related)},
        {"name": "zh_label_present", "passed": bool(_clean(label.get("zh"))) or action == "deprecate"},
        {"name": "en_label_present", "passed": bool(_clean(label.get("en"))) or action == "deprecate"},
        {"name": "ko_label_present", "passed": bool(_clean(label.get("ko"))) or action == "deprecate"},
        {"name": "metadata_for_add_or_edit", "passed": action not in {"add", "edit"} or bool(metadata)},
    ]
    return checks


def _append_guided_question_history(proposal: Dict[str, Any], *, actor_role: str, status: str, note: str) -> None:
    proposal.setdefault("history", []).append(
        {
            "created_at": utc_now(),
            "actor_role": actor_role,
            "status": status,
            "note": note,
        }
    )


def _find_bazi_rule_proposal(state: Dict[str, Any], proposal_id: str) -> Dict[str, Any] | None:
    clean = _clean(proposal_id)
    for row in state.get("bazi_rule_proposals", []):
        if row.get("proposal_id") == clean:
            return row
    return None


def _validate_bazi_rule_proposal(proposal: Dict[str, Any]) -> List[Dict[str, Any]]:
    input_contract = dict(proposal.get("input_contract") or {})
    output_contract = dict(proposal.get("output_contract") or {})
    reasoning_path = _string_list(proposal.get("reasoning_path"))
    guardrails = _string_list(proposal.get("guardrails"))
    return [
        {"name": "rule_id_present", "passed": bool(_clean(proposal.get("rule_id")))},
        {"name": "domain_allowed", "passed": proposal.get("domain") in ALLOWED_BAZI_RULE_DOMAINS},
        {"name": "input_contract_required_present", "passed": bool(_string_list(input_contract.get("required")))},
        {"name": "condition_present", "passed": bool(dict(proposal.get("condition") or {}))},
        {"name": "output_signal_present", "passed": bool(_clean(output_contract.get("signal")))},
        {"name": "output_is_not_prediction", "passed": output_contract.get("is_prediction") is False},
        {"name": "output_value_set_present", "passed": bool(_string_list(output_contract.get("value_set")))},
        {"name": "reasoning_path_present", "passed": bool(reasoning_path)},
        {"name": "review_required", "passed": True},
        {"name": "guardrail_no_prediction", "passed": "NO_PREDICTION" in guardrails or "STRUCTURE_ONLY" in guardrails or "NO_RUNTIME_INFERENCE_MUTATION" in guardrails},
    ]


def _append_bazi_rule_history(proposal: Dict[str, Any], *, actor_role: str, status: str, note: str) -> None:
    proposal.setdefault("history", []).append(
        {
            "created_at": utc_now(),
            "actor_role": actor_role,
            "status": status,
            "note": note,
        }
    )


def _find_synthetic_promotion_candidate(state: Dict[str, Any], candidate_id: str) -> Dict[str, Any] | None:
    clean = _clean(candidate_id)
    for row in state.get("synthetic_promotion_candidates", []):
        if row.get("candidate_id") == clean:
            return row
    return None


def _create_synthetic_downstream_proposal(candidate: Dict[str, Any], decision: str, payload: Dict[str, Any], settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    kind = _synthetic_downstream_kind(candidate, decision)
    actor_role = _role(payload.get("actor_role"))
    if kind == "knowledge_draft":
        created = create_knowledge_draft(_synthetic_knowledge_draft_payload(candidate, decision, payload, actor_role))
        item = dict(created.get("item") or {})
        return {
            "ok": bool(created.get("ok")),
            "kind": kind,
            "draft_id": item.get("draft_id") or "",
            "knowledge_id": item.get("knowledge_id") or "",
            "code": created.get("code") or "",
            "message": created.get("message") or "",
            "guardrails": created.get("guardrails") or [],
        }
    if kind == "bazi_rule_proposal":
        created = create_bazi_rule_proposal(_synthetic_rule_proposal_payload(candidate, payload, actor_role), settings)
        item = dict(created.get("item") or {})
        return {
            "ok": bool(created.get("ok")),
            "kind": kind,
            "proposal_id": item.get("proposal_id") or "",
            "rule_id": item.get("rule_id") or "",
            "code": created.get("code") or "",
            "message": created.get("message") or "",
            "guardrails": item.get("guardrails") or [],
        }
    if kind == "guided_question_proposal":
        created = create_guided_question_proposal(_synthetic_guided_question_proposal_payload(candidate, payload, actor_role), settings)
        item = dict(created.get("item") or {})
        return {
            "ok": bool(created.get("ok")),
            "kind": kind,
            "proposal_id": item.get("proposal_id") or "",
            "question_key": item.get("proposed_question_key") or item.get("source_question_key") or "",
            "code": created.get("code") or "",
            "message": created.get("message") or "",
            "guardrails": item.get("guardrails") or [],
        }
    return {"ok": False, "kind": kind, "code": "SYNTHETIC_DOWNSTREAM_KIND_UNSUPPORTED", "message": "No downstream proposal kind mapped."}


def _synthetic_downstream_kind(candidate: Dict[str, Any], decision: str) -> str:
    if decision in {"needs_knowledge", "needs_expression"}:
        return "knowledge_draft"
    if decision == "needs_rule":
        return "bazi_rule_proposal"
    draft_type = _clean(candidate.get("draft_type"))
    if draft_type in {"knowledge_seed", "answer_expression"}:
        return "knowledge_draft"
    if draft_type == "rule_draft":
        return "bazi_rule_proposal"
    if draft_type == "question_recommendation_draft":
        return "guided_question_proposal"
    return "knowledge_draft"


def _synthetic_knowledge_draft_payload(candidate: Dict[str, Any], decision: str, payload: Dict[str, Any], actor_role: str) -> Dict[str, Any]:
    slug = _synthetic_slug(candidate.get("case_id"))
    is_expression = decision == "needs_expression" or _clean(candidate.get("draft_type")) == "answer_expression"
    domain = _clean(payload.get("domain")) or ("answer_expression" if is_expression else "core_structure")
    category = _clean(payload.get("category")) or _clean(candidate.get("attribution_layer"), "synthetic_collision")
    statement = _clean(payload.get("statement")) or (
        f"Synthetic collision review for {candidate.get('case_id')}: {candidate.get('suggested_action') or 'analyst should draft a bounded knowledge update'}."
    )
    return {
        "actor_role": actor_role,
        "knowledge_id": _clean(payload.get("knowledge_id")) or f"synthetic.{slug}.{_synthetic_slug(candidate.get('draft_type'))}",
        "domain": domain,
        "category": category,
        "title": _clean(payload.get("title")) or f"Synthetic review: {candidate.get('case_id')}",
        "statement": statement,
        "structured_facts": {
            "source": "p11_synthetic_collision",
            "case_id": candidate.get("case_id"),
            "target": candidate.get("target"),
            "draft_type": candidate.get("draft_type"),
            "attribution_layer": candidate.get("attribution_layer"),
            "failure_types": candidate.get("failure_types") or [],
            "knowledge_tags": candidate.get("knowledge_tags") or [],
        },
        "source_refs": ["synthetic_collision:P11"],
        "risk_level": _clean(payload.get("risk_level"), "R2"),
        "confidence_prior": _bounded_float(payload.get("confidence_prior"), 0.5, 0.0, 1.0),
        "allowed_usage": ["knowledge_unit_draft", "rule_proposal_source"],
        "forbidden_usage": ["direct_active_rule", "direct_fortune_output", "runtime_inference_without_proposal"],
    }


def _synthetic_rule_proposal_payload(candidate: Dict[str, Any], payload: Dict[str, Any], actor_role: str) -> Dict[str, Any]:
    slug = _synthetic_slug(candidate.get("case_id"))
    domain = _clean(payload.get("domain")) or _synthetic_rule_domain(candidate)
    return {
        "actor_role": actor_role,
        "rule_id": _clean(payload.get("rule_id")) or f"v19.synthetic.{slug}",
        "domain": domain,
        "version": _bounded_int(payload.get("version"), 1, 1, 9999),
        "source_feedback_ids": _string_list(payload.get("source_feedback_ids")),
        "input_contract": {
            "required": ["chart", "guided_question_context", "knowledge_context"],
            "source": "p11_synthetic_collision",
            "case_id": candidate.get("case_id"),
        },
        "condition": {
            "source": "p11_synthetic_collision",
            "case_id": candidate.get("case_id"),
            "target": candidate.get("target"),
            "draft_type": candidate.get("draft_type"),
            "failure_types": candidate.get("failure_types") or [],
            "knowledge_tags": candidate.get("knowledge_tags") or [],
        },
        "output_contract": {
            "signal": _clean(payload.get("output_signal")) or _synthetic_output_signal(candidate, domain),
            "value_set": ["present", "absent", "needs_review"],
            "is_prediction": False,
            "runtime_scope": "proposal_only_no_runtime_inference_mutation",
        },
        "reasoning_path": [
            "read synthetic failure attribution",
            "draft structured rule proposal only",
            "require validation, analyst approval, and P11 regression before any active record",
        ],
        "evidence": {
            "source": "p11_synthetic_collision",
            "case_id": candidate.get("case_id"),
            "attribution_layer": candidate.get("attribution_layer"),
            "suggested_action": candidate.get("suggested_action"),
        },
        "confidence": _bounded_float(payload.get("confidence"), 0.5, 0.0, 1.0),
        "rationale": _clean(payload.get("rationale")) or f"Synthetic collision draft from {candidate.get('case_id')}. Rule proposal only.",
        "guardrails": ["RULE_PROPOSAL_ONLY", "NO_RUNTIME_INFERENCE_MUTATION", "VALIDATION_REQUIRED"],
    }


def _synthetic_guided_question_proposal_payload(candidate: Dict[str, Any], payload: Dict[str, Any], actor_role: str) -> Dict[str, Any]:
    key = _clean(payload.get("source_question_key")) or "q_income_stability"
    return {
        "actor_role": actor_role,
        "proposed_action": _clean(payload.get("proposed_action"), "edit"),
        "source_question_key": key,
        "proposed_question_key": _clean(payload.get("proposed_question_key"), key),
        "source_feedback_ids": _string_list(payload.get("source_feedback_ids")),
        "proposed_label": {
            "zh": _clean(payload.get("label_zh")) or f"复核 {candidate.get('case_id')} 的推荐问题",
            "en": _clean(payload.get("label_en")) or f"Review recommended question for {candidate.get('case_id')}",
            "ko": _clean(payload.get("label_ko")) or f"{candidate.get('case_id')} 추천 질문 검토",
        },
        "proposed_metadata": {
            "depth": "beginner",
            "required_context": ["chart", "result"],
            "related_questions": ["q_income_stability", "q_branch_relation_detail"],
            "source": "p11_synthetic_collision",
            "case_id": candidate.get("case_id"),
        },
        "rationale": _clean(payload.get("rationale")) or f"Synthetic collision recommendation review for {candidate.get('case_id')}.",
    }


def _synthetic_draft_type_from_target(target: str) -> str:
    mapping = {
        "answer_expression_seed_draft": "answer_expression",
        "knowledge_seed_draft": "knowledge_seed",
        "rule_db_structured_fact_draft": "rule_draft",
        "guided_question_ranking_draft": "question_recommendation_draft",
    }
    return mapping.get(_clean(target), "knowledge_seed")


def _synthetic_rule_domain(candidate: Dict[str, Any]) -> str:
    tags = " ".join(_string_list(candidate.get("knowledge_tags")) + _string_list(candidate.get("failure_types")) + [_clean(candidate.get("attribution_layer"))])
    if "income" in tags or "wealth" in tags:
        return "income_stability"
    if "ten_god" in tags:
        return "ten_god_relation"
    if "time" in tags:
        return "time_structure"
    return "structural_relation"


def _synthetic_output_signal(candidate: Dict[str, Any], domain: str) -> str:
    if domain == "income_stability":
        return "income_structure_review_signal"
    if domain == "time_structure":
        return "time_context_review_signal"
    if domain == "ten_god_relation":
        return "ten_god_review_signal"
    return _clean(candidate.get("attribution_layer"), "synthetic_structure_review_signal")


def _synthetic_slug(value: Any) -> str:
    text = _clean(value, "synthetic")
    cleaned = "".join(char.lower() if char.isalnum() else "." for char in text)
    parts = [part for part in cleaned.split(".") if part]
    return ".".join(parts)[:96] or "synthetic"


def _p12_synthetic_regression_gate() -> Dict[str, Any]:
    result = run_guided_synthetic_collision(P11_GUIDED_SYNTHETIC_CASES)
    summary = dict(result.get("summary") or {})
    passed = result.get("status") == "pass" and int(summary.get("failed") or 0) == 0 and int(summary.get("total") or 0) >= 20
    return {
        "required": True,
        "matrix": "P11_SYNTHETIC_EXPANSION",
        "validation_run": result.get("validation_run") or "",
        "status": result.get("status") or "",
        "passed": passed,
        "summary": summary,
        "guardrails": ["SYNTHETIC_REGRESSION_GATE", "NO_AUTO_LEARNING", "NO_RUNTIME_MUTATION"],
    }


def _collect_governance_release_artifacts(state: Dict[str, Any], artifact_ids: Dict[str, List[str]]) -> tuple[Dict[str, List[Dict[str, Any]]], List[Dict[str, str]]]:
    artifacts = {
        "knowledge_drafts": _knowledge_draft_release_items(artifact_ids.get("knowledge_draft_ids") or []),
        "guided_question_versions": _release_items_by_id(state.get("guided_question_library_versions") or [], artifact_ids.get("guided_question_version_ids") or [], "version_id"),
        "bazi_rule_versions": _release_items_by_id(state.get("bazi_rule_versions") or [], artifact_ids.get("bazi_rule_version_ids") or [], "version_id"),
        "active_revisions": _release_items_by_id(state.get("active_rule_revisions") or [], artifact_ids.get("active_revision_ids") or [], "active_revision_id"),
    }
    missing: List[Dict[str, str]] = []
    expected = {
        "knowledge_drafts": artifact_ids.get("knowledge_draft_ids") or [],
        "guided_question_versions": artifact_ids.get("guided_question_version_ids") or [],
        "bazi_rule_versions": artifact_ids.get("bazi_rule_version_ids") or [],
        "active_revisions": artifact_ids.get("active_revision_ids") or [],
    }
    keys = {
        "knowledge_drafts": {"draft_id", "knowledge_id"},
        "guided_question_versions": {"version_id"},
        "bazi_rule_versions": {"version_id"},
        "active_revisions": {"active_revision_id"},
    }
    for group, ids in expected.items():
        found = {
            str(row.get(key) or "")
            for row in artifacts.get(group) or []
            for key in keys[group]
            if row.get(key)
        }
        for item_id in ids:
            if item_id not in found:
                missing.append({"artifact_type": group, "artifact_id": item_id})
    return artifacts, missing


def _knowledge_draft_release_items(ids: List[str]) -> List[Dict[str, Any]]:
    if not ids:
        return []
    try:
        rows = [dict(row) for row in (list_knowledge_drafts().get("items") or [])]
    except Exception:
        rows = []
    wanted = set(ids)
    out = []
    for row in rows:
        if str(row.get("draft_id") or "") in wanted or str(row.get("knowledge_id") or "") in wanted:
            out.append(_compact_release_item(row, ["draft_id", "knowledge_id", "domain", "category", "risk_level", "review_status", "title"]))
    return out


def _release_items_by_id(rows: List[Dict[str, Any]], ids: List[str], id_key: str) -> List[Dict[str, Any]]:
    wanted = set(ids)
    out = []
    for row in rows:
        if str(row.get(id_key) or "") in wanted:
            out.append(_compact_release_item(dict(row), [id_key, "status", "created_at", "activated_by_role", "runtime_mutation", "note"]))
    return out


def _compact_release_item(row: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    item = {key: row.get(key) for key in keys if key in row}
    if "p12_regression_gate" in row:
        gate = dict(row.get("p12_regression_gate") or {})
        item["p12_regression_gate"] = {"passed": gate.get("passed"), "matrix": gate.get("matrix"), "summary": gate.get("summary")}
    if "changelog" in row:
        item["changelog"] = list(row.get("changelog") or [])[:12]
    if "included_proposals" in row:
        item["included_proposals"] = list(row.get("included_proposals") or [])
    return item


def _governance_release_summary(artifacts: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    counts = {key: len(value) for key, value in artifacts.items()}
    return {
        "artifact_count": sum(counts.values()),
        "by_artifact_type": counts,
        "runtime_mutation": False,
        "release_scope": "governance_manifest_only",
    }


def _find_knowledge_review_batch(state: Dict[str, Any], batch_id: str) -> Dict[str, Any] | None:
    clean = _clean(batch_id)
    for row in state.get("knowledge_review_batches", []):
        if row.get("batch_id") == clean or row.get("batch_key") == clean:
            return row
    return None


def _find_successful_knowledge_batch_proposal_run(state: Dict[str, Any], batch: Dict[str, Any]) -> Dict[str, Any] | None:
    batch_id = _clean(batch.get("batch_id"))
    batch_key = _clean(batch.get("batch_key"))
    for row in state.get("knowledge_batch_proposal_runs", []):
        if row.get("status") != "proposal_drafts_created":
            continue
        if row.get("batch_id") == batch_id or row.get("batch_key") == batch_key:
            return row
    return None


def _knowledge_batch_proposal_eligibility(batch: Dict[str, Any]) -> Dict[str, Any]:
    items = [dict(row) for row in (batch.get("items") or []) if isinstance(row, dict)]
    risks = set(_string_list(batch.get("risk_levels")))
    risks.update(str(row.get("risk_level") or "") for row in items if row.get("risk_level"))
    risks.discard("")
    action = _clean(batch.get("recommended_action")).lower()
    blocked_items = []
    for row in items:
        if str(row.get("risk_level") or "") not in {"R0", "R1"}:
            blocked_items.append(_knowledge_batch_blocked_item(row, "Only R0/R1 knowledge drafts can enter P16 proposal drafting."))
    if not items:
        return {"eligible": False, "reason": "Batch has no knowledge draft items.", "blocked_items": []}
    if "source_version" in action or "archive" in action:
        return {
            "eligible": False,
            "reason": "Batch action requires source/version or archive review before proposal drafting.",
            "blocked_items": blocked_items or [_knowledge_batch_blocked_item(row, "Batch action is not proposal-ready.") for row in items],
        }
    if risks - {"R0", "R1"}:
        return {
            "eligible": False,
            "reason": "R2/R3/R4 knowledge batches stay in analyst/source review before P16 proposal drafting.",
            "blocked_items": blocked_items,
        }
    return {"eligible": True, "reason": "Batch is eligible for P16 proposal drafts.", "blocked_items": []}


def _knowledge_batch_blocked_item(row: Dict[str, Any], reason: str) -> Dict[str, Any]:
    return {
        "knowledge_id": row.get("knowledge_id"),
        "draft_id": row.get("draft_id"),
        "risk_level": row.get("risk_level"),
        "reason": reason,
    }


def _knowledge_batch_proposal_run_base(run_id: str, batch: Dict[str, Any], payload: Dict[str, Any], role: str) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at": utc_now(),
        "batch_id": batch.get("batch_id"),
        "batch_key": batch.get("batch_key"),
        "batch_name": batch.get("batch_name"),
        "actor_role": role,
        "actor_id": _clean(payload.get("actor_id"), role),
        "decision": _clean(payload.get("decision"), "generate_rule_and_question_proposal_drafts"),
        "source_risk_levels": list(batch.get("risk_levels") or []),
        "source_domains": list(batch.get("domains") or []),
        "source_knowledge_ids": list(batch.get("knowledge_ids") or []),
        "recommended_action": batch.get("recommended_action"),
        "runtime_mutation": False,
        "note": _clean(payload.get("note"), "P16 batch proposal draft generation. Proposal ledgers only."),
        "rule_proposals": [],
        "guided_question_proposals": [],
        "blocked_items": [],
        "errors": [],
        "summary": {"rule_proposal_count": 0, "question_proposal_count": 0, "blocked_count": 0, "error_count": 0},
        "guardrails": [
            "P16_BATCH_TO_PROPOSAL_DRAFT_ONLY",
            "NO_RUNTIME_MUTATION",
            "NO_AUTO_RULE_ACTIVATION",
            "VALIDATION_AND_APPROVAL_REQUIRED",
            "R2_R3_ANALYST_REVIEW_BEFORE_PROPOSAL",
        ],
    }


def _knowledge_drafts_for_batch(batch: Dict[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    try:
        rows = [dict(row) for row in (list_knowledge_drafts().get("items") or [])]
    except Exception:
        rows = []
    wanted = []
    for item in batch.get("items") or []:
        if not isinstance(item, dict):
            continue
        wanted.extend([_clean(item.get("draft_id")), _clean(item.get("knowledge_id"))])
    wanted.extend(_string_list(batch.get("draft_ids")))
    wanted.extend(_string_list(batch.get("knowledge_ids")))
    order = {item: index for index, item in enumerate([item for item in wanted if item])}
    selected = []
    seen = set()
    for row in rows:
        draft_id = _clean(row.get("draft_id"))
        knowledge_id = _clean(row.get("knowledge_id"))
        if draft_id not in order and knowledge_id not in order:
            continue
        key = draft_id or knowledge_id
        if key in seen:
            continue
        seen.add(key)
        selected.append(row)
    selected.sort(key=lambda row: min(order.get(_clean(row.get("draft_id")), 9999), order.get(_clean(row.get("knowledge_id")), 9999)))
    found = {_clean(row.get("draft_id")) for row in selected} | {_clean(row.get("knowledge_id")) for row in selected}
    missing = []
    for item in batch.get("items") or []:
        if not isinstance(item, dict):
            continue
        draft_id = _clean(item.get("draft_id"))
        knowledge_id = _clean(item.get("knowledge_id"))
        if draft_id not in found and knowledge_id not in found:
            missing.append({"draft_id": draft_id, "knowledge_id": knowledge_id, "reason": "Draft is listed in the batch but absent from the source archive."})
    return selected, missing


def _knowledge_batch_rule_proposal_payload(batch: Dict[str, Any], draft: Dict[str, Any], run_id: str, payload: Dict[str, Any], role: str) -> Dict[str, Any]:
    knowledge_id = _clean(draft.get("knowledge_id"))
    domain = _knowledge_batch_rule_domain(draft)
    signal = _knowledge_batch_output_signal(draft, domain)
    return {
        "actor_role": role,
        "rule_id": f"v19.kb_v2.{_synthetic_slug(knowledge_id)}",
        "domain": domain,
        "version": 1,
        "source_feedback_ids": [],
        "input_contract": {
            "required": ["chart", "knowledge_context", "guided_question_context"],
            "source_batch_id": batch.get("batch_id"),
            "source_batch_key": batch.get("batch_key"),
            "source_knowledge_id": knowledge_id,
        },
        "condition": {
            "source": "p16_knowledge_batch_proposal",
            "source_run_id": run_id,
            "source_batch_key": batch.get("batch_key"),
            "source_draft_id": draft.get("draft_id"),
            "source_knowledge_id": knowledge_id,
            "category": draft.get("category"),
            "risk_level": draft.get("risk_level"),
            "structured_facts": draft.get("structured_facts") or {},
            "conditions": draft.get("conditions") or {},
        },
        "output_contract": {
            "signal": signal,
            "value_set": ["present", "absent", "unknown"],
            "is_prediction": False,
            "runtime_scope": "proposal_only_no_runtime_inference_mutation",
        },
        "reasoning_path": [
            "read P16 reviewed knowledge batch",
            "map each R0/R1 draft into a bounded structural rule proposal",
            "require schema validation, analyst/admin approval, version record, and future engineering implementation",
        ],
        "evidence": {
            "source": "knowledge_review_batch",
            "run_id": run_id,
            "batch_id": batch.get("batch_id"),
            "batch_key": batch.get("batch_key"),
            "source_draft_id": draft.get("draft_id"),
            "source_knowledge_id": knowledge_id,
            "source_excerpt_ids": draft.get("source_excerpt_ids") or [],
            "risk_level": draft.get("risk_level"),
            "review_status_at_generation": draft.get("review_status") or "pending",
            "batch_guardrails": batch.get("guardrails") or [],
        },
        "confidence": _bounded_float(draft.get("confidence_prior"), 0.5, 0.0, 1.0),
        "rationale": _clean(payload.get("rationale")) or f"P16 proposal draft from knowledge batch {batch.get('batch_key')} and draft {knowledge_id}.",
        "guardrails": ["FROM_KNOWLEDGE_BATCH", "RULE_PROPOSAL_ONLY", "NO_RUNTIME_INFERENCE_MUTATION", "NO_PREDICTION", "STRUCTURE_ONLY"],
    }


def _knowledge_batch_question_proposal_payload(batch: Dict[str, Any], drafts: List[Dict[str, Any]], run_id: str, payload: Dict[str, Any], role: str) -> Dict[str, Any]:
    key_suffix = _synthetic_slug(batch.get("batch_key") or batch.get("batch_id")).replace(".", "_")
    knowledge_ids = [_clean(row.get("knowledge_id")) for row in drafts if _clean(row.get("knowledge_id"))]
    return {
        "actor_role": role,
        "source_question_key": _clean(payload.get("source_question_key"), "q_income_stability"),
        "proposed_action": _clean(payload.get("proposed_action"), "add"),
        "proposed_question_key": _clean(payload.get("proposed_question_key"), f"q_kb_v2_{key_suffix}"),
        "proposed_label": {
            "zh": _clean(payload.get("label_zh"), "查看收入稳定性的结构边界依据"),
            "en": _clean(payload.get("label_en"), "Review structural evidence for income stability"),
            "ko": _clean(payload.get("label_ko"), "수입 안정성의 구조 근거 보기"),
        },
        "proposed_metadata": {
            "depth": "intermediate",
            "required_context": ["chart", "result"],
            "related_questions": ["q_income_stability", "follow_rule_basis"],
            "source": "p16_knowledge_batch_proposal",
            "source_run_id": run_id,
            "source_batch_key": batch.get("batch_key"),
            "source_knowledge_ids": knowledge_ids,
            "forbidden_prediction": True,
        },
        "rationale": _clean(payload.get("question_rationale")) or f"P16 guided question proposal from knowledge batch {batch.get('batch_key')}.",
    }


def _knowledge_batch_rule_domain(draft: Dict[str, Any]) -> str:
    blob = " ".join(
        [
            _clean(draft.get("knowledge_id")),
            _clean(draft.get("domain")),
            _clean(draft.get("category")),
            _clean(draft.get("title")),
        ]
    ).lower()
    if "wealth" in blob or "income" in blob:
        return "income_stability"
    if "ten_god" in blob or "十神" in blob:
        return "ten_god_relation"
    if "time" in blob or "luck" in blob or "flow" in blob:
        return "time_structure"
    if "day_master" in blob or "element" in blob:
        return "day_master_element"
    return "structural_relation"


def _knowledge_batch_output_signal(draft: Dict[str, Any], domain: str) -> str:
    blob = " ".join([_clean(draft.get("knowledge_id")), _clean(draft.get("category")), _clean(draft.get("title"))]).lower()
    if "wealth" in blob:
        return "wealth_relation_boundary"
    if "ten_god" in blob:
        return "ten_god_family_boundary"
    if "month_command" in blob:
        return "month_command_boundary"
    if "stem_combination" in blob:
        return "stem_combination_boundary"
    if "branch_penalty" in blob:
        return "branch_penalty_boundary"
    if domain == "income_stability":
        return "income_stability_evidence_boundary"
    return "structural_context_boundary"


def _select_knowledge_review_drafts(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        rows = [dict(row) for row in (list_knowledge_drafts().get("items") or [])]
    except Exception:
        rows = []
    ids = set(_string_list(payload.get("draft_ids") or payload.get("knowledge_ids")))
    risk_levels = set(_string_list(payload.get("risk_levels")))
    domains = set(_string_list(payload.get("domains")))
    categories = set(_string_list(payload.get("categories")))
    prefix = _clean(payload.get("knowledge_id_prefix") or payload.get("prefix"))
    selected = []
    for row in rows:
        knowledge_id = str(row.get("knowledge_id") or "")
        draft_id = str(row.get("draft_id") or "")
        if ids and knowledge_id not in ids and draft_id not in ids:
            continue
        if prefix and not knowledge_id.startswith(prefix):
            continue
        if risk_levels and str(row.get("risk_level") or "") not in risk_levels:
            continue
        if domains and str(row.get("domain") or "") not in domains:
            continue
        if categories and str(row.get("category") or "") not in categories:
            continue
        selected.append(row)
    selected.sort(key=lambda row: (str(row.get("risk_level") or ""), str(row.get("knowledge_id") or "")))
    return selected


def _knowledge_review_batch_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "draft_id": row.get("draft_id"),
        "knowledge_id": row.get("knowledge_id"),
        "title": row.get("title"),
        "domain": row.get("domain"),
        "category": row.get("category"),
        "risk_level": row.get("risk_level"),
        "review_status": row.get("review_status"),
        "recommended_queue": _knowledge_review_recommended_queue(row),
    }


def _knowledge_review_recommended_queue(row: Dict[str, Any]) -> str:
    risk = str(row.get("risk_level") or "")
    if risk in {"R0", "R1"}:
        return "analyst_fast_review"
    if risk == "R2":
        return "source_version_review"
    if risk in {"R3", "R4"}:
        return "archive_reference_only"
    return "analyst_review"


def _string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    text = _clean(value)
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _bounded_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        raw = int(value)
    except (TypeError, ValueError):
        raw = default
    return max(low, min(high, raw))


def _find_revision(state: Dict[str, Any], revision_id: str) -> Dict[str, Any] | None:
    clean = _clean(revision_id)
    for row in state.get("revision_proposals", []):
        if row.get("revision_id") == clean:
            return row
    return None


def _rule_impacts_from_feedback(feedback: Dict[str, Any], payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    evidence_rows = _extract_signal_evidence(payload)
    if not evidence_rows and _feedback_mentions_income_stability(feedback):
        evidence_rows = _default_income_stability_evidence()
    impacts = []
    for row in evidence_rows:
        signal = _clean(row.get("signal") or row.get("key"))
        rule_id = _clean(row.get("rule_id"))
        if not signal or not rule_id:
            continue
        impacts.append(
            {
                "impact_id": "rim_" + uuid.uuid4().hex[:16],
                "created_at": utc_now(),
                "feedback_id": feedback["feedback_id"],
                "subject_type": feedback.get("subject_type"),
                "signal": signal,
                "observed_value": _clean(row.get("value")),
                "rule_id": rule_id,
                "rule_version": row.get("rule_version") or RULE_VERSION_FALLBACK,
                "condition": _clean(row.get("condition")),
                "inputs": list(row.get("inputs") or []),
                "confidence": _bounded_float(row.get("confidence"), 0.5, 0.0, 1.0),
                "impact_type": "candidate_review",
                "status": "open",
                "guardrails": ["ATTRIBUTION_ONLY", "NO_AUTO_RULE_UPDATE"],
            }
        )
    return impacts


RULE_VERSION_FALLBACK = 1


def _extract_signal_evidence(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates: List[Any] = []
    for root_key in ["inference_context", "income_stability", "payload"]:
        root = payload.get(root_key)
        if isinstance(root, dict):
            candidates.extend(_find_signal_evidence(root))
    return [dict(item) for item in candidates if isinstance(item, dict)]


def _find_signal_evidence(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("signal_evidence"), list):
            return [item for item in value["signal_evidence"] if isinstance(item, dict)]
        rows: List[Dict[str, Any]] = []
        for item in value.values():
            rows.extend(_find_signal_evidence(item))
        return rows
    if isinstance(value, list):
        rows: List[Dict[str, Any]] = []
        for item in value:
            rows.extend(_find_signal_evidence(item))
        return rows
    return []


def _feedback_mentions_income_stability(feedback: Dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(feedback.get("subject_type") or ""),
            str(feedback.get("comment") or ""),
            " ".join(str(item) for item in feedback.get("tags", [])),
        ]
    ).lower()
    return "income_stability" in text or "收入稳定" in text


def _default_income_stability_evidence() -> List[Dict[str, Any]]:
    return [
        {"signal": "self_capacity", "rule_id": "v19.income_stability.self_capacity", "rule_version": 1, "condition": "capacity mapping needs review", "inputs": [], "confidence": 0.5},
        {"signal": "wealth_presence", "rule_id": "v19.income_stability.wealth_presence", "rule_version": 1, "condition": "wealth presence mapping needs review", "inputs": [], "confidence": 0.5},
        {"signal": "wealth_accessibility", "rule_id": "v19.income_stability.wealth_accessibility", "rule_version": 1, "condition": "relation accessibility mapping needs review", "inputs": [], "confidence": 0.5},
        {"signal": "volatility", "rule_id": "v19.income_stability.volatility", "rule_version": 1, "condition": "volatility mapping needs review", "inputs": [], "confidence": 0.5},
        {"signal": "structure_binding", "rule_id": "v19.income_stability.structure_binding", "rule_version": 1, "condition": "binding mapping needs review", "inputs": [], "confidence": 0.5},
        {"signal": "income_stability", "rule_id": "v19.income_stability.aggregate", "rule_version": 1, "condition": "aggregate mapping needs review", "inputs": [], "confidence": 0.5},
    ]


def _bounded_float(value: Any, default: float, low: float, high: float) -> float:
    try:
        raw = float(value)
    except (TypeError, ValueError):
        raw = default
    return round(max(low, min(high, raw)), 3)
