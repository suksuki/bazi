from __future__ import annotations

import json
from datetime import datetime, timezone

from v20.learning.role_view_policy_candidates import build_role_view_policy_candidate_report
from v20.learning.role_view_policy_calibration import build_role_view_policy_calibration_report
from v20.learning.role_view_policy_promotion import build_role_view_policy_promotion_gate
from v20.learning.role_view_policy_replay import build_role_view_policy_replay_report
from v20.role_view.policy import POLICY_VERSION
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


ROLE_VIEW_RUNTIME_POINTER_VERSION = "v20.role_view_runtime_pointer.v1"
ROLE_VIEW_ACTIVE_POINTER_VERSION = "v20.role_view_runtime_active_pointer.v1"
ROLE_VIEW_POINTER_AUDIT_LEDGER = "role_view_policy_pointer_audit"
ROLE_VIEW_POINTER_RELATIVE_PATH = "training/role_view_policy_versions/active_pointer.json"


def build_role_view_runtime_pointer(*, store: LocalJsonlStore | None = None) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    candidate = build_role_view_policy_candidate_report(store=storage)
    replay = build_role_view_policy_replay_report(policy_candidate_report=candidate)
    active_pointer = _read_active_pointer(storage)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    active_version = _active_version(candidate_version, active_pointer)
    rollout_switch = bool(candidate_version and active_version == candidate_version)
    calibration = build_role_view_policy_calibration_report(replay_report=replay, store=storage)
    promotion_gate = build_role_view_policy_promotion_gate(
        replay_report=replay,
        calibration_report=calibration,
        runtime_rollout_switch=rollout_switch,
    )
    replay_result = replay.get("replay_result", {}) if isinstance(replay.get("replay_result"), dict) else {}
    candidate_payload = candidate.get("policy_payload", {}) if isinstance(candidate.get("policy_payload"), dict) else {}
    answer_governance_policy = _answer_governance_style_policy(storage)
    runtime_applied = _runtime_applied(candidate, replay, promotion_gate, active_version)
    answer_governance_applied = bool(answer_governance_policy)
    policy_payload = candidate_payload if runtime_applied else {}
    if answer_governance_policy:
        policy_payload = dict(policy_payload)
        policy_payload["answer_governance_style_policy"] = answer_governance_policy
    return {
        "version": ROLE_VIEW_RUNTIME_POINTER_VERSION,
        "status": _pointer_status(
            candidate,
            replay,
            runtime_applied=runtime_applied,
            answer_governance_applied=answer_governance_applied,
            active_version=active_version,
            active_pointer=active_pointer,
        ),
        "policy_family": "role_view_policy",
        "active_policy_version": active_version,
        "candidate_policy_version": candidate_version,
        "rollback_policy_version": POLICY_VERSION,
        "active_pointer_source": str(active_pointer.get("source", "")) if active_pointer else "baseline",
        "candidate_status": candidate.get("status", ""),
        "replay_status": replay.get("status", ""),
        "candidate_count": candidate.get("candidate_count", 0),
        "comparison_count": replay.get("comparison_count", 0),
        "policy_payload_counts": _payload_counts(candidate_payload) | (
            {"answer_governance_style_policy": len(answer_governance_policy)}
            if answer_governance_policy
            else {}
        ),
        "replay_result": replay_result,
        "replay_impact_summary": replay.get("impact_summary", {}),
        "promotion_gate": promotion_gate,
        "calibration": calibration,
        "ab_test_summary": replay.get("ab_test_summary", {}),
        "replay_ab_test_summary": replay.get("ab_test_summary", {}),
        "policy_payload": policy_payload,
        "rollout_mode": "fast_iteration" if runtime_applied else ("answer_governance_direct" if answer_governance_applied else "baseline_until_candidate_ready"),
        "runtime_applied": runtime_applied,
        "runtime_answer_governance_applied": answer_governance_applied,
        "runtime_effect": "role_view_candidate_policy_active" if runtime_applied else ("role_answer_governance_policy_active" if answer_governance_applied else "baseline_role_view_policy_active"),
        "runtime_allowed": bool(runtime_applied or answer_governance_applied),
        "blocking_gate": "" if runtime_applied or answer_governance_applied else _blocking_gate(candidate, replay_result, promotion_gate),
        "guardrails": [
            "ROLE_VIEW_RUNTIME_POINTER_FAST_ITERATION",
            "ROLE_VIEW_POINTER_ONLY_REORDERS_VIEW_QUESTIONS",
            "ROLE_ANSWER_GOVERNANCE_TRAINING_APPLIES_DIRECTLY",
            "ROLE_VIEW_POLICY_PROMOTION_REQUIRES_REPLAY",
            "ROLE_VIEW_POLICY_PROMOTION_REQUIRES_GATE",
            "ROLE_VIEW_ACTIVE_POINTER_CAN_ROLL_BACK_TO_BASELINE",
            "ROLE_VIEW_POLICY_DOES_NOT_CHANGE_CHART_FACTS",
        ],
        "runtime_mutation": False,
    }


def write_role_view_runtime_pointer_rollback(
    *,
    source_role: str,
    reason: str = "",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    if source_role not in {"admin", "lab", "system"}:
        raise ValueError(f"Unsupported role-view rollback source_role: {source_role}")
    storage = store or local_jsonl_store_from_env()
    previous = _read_active_pointer(storage)
    previous_active = str(previous.get("active_policy_version", "")) or POLICY_VERSION
    pointer = {
        "version": ROLE_VIEW_ACTIVE_POINTER_VERSION,
        "status": "rolled_back_to_baseline",
        "active_policy_version": POLICY_VERSION,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": POLICY_VERSION,
        "source": "admin_role_view_rollback",
        "source_role": source_role,
        "reason": reason[:240],
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
        "guardrails": [
            "ROLE_VIEW_ROLLBACK_WRITES_VERSION_POINTER_ONLY",
            "NO_CHART_FACT_MUTATION",
            "NO_RULE_TRUTH_MUTATION",
        ],
    }
    path = _write_active_pointer(storage, pointer)
    audit = _append_pointer_audit(storage, "v20.role_view_policy_pointer_rollback_audit.v1", pointer)
    return {
        "version": "v20.role_view_runtime_pointer_rollback_result.v1",
        "status": "rolled_back",
        "active_pointer_path": str(path),
        "active_policy_version": POLICY_VERSION,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": POLICY_VERSION,
        "audit": audit,
        "runtime_mutation": True,
        "guardrails": [
            "ROLE_VIEW_ROLLBACK_WRITES_VERSION_POINTER_ONLY",
            "ROLE_VIEW_POINTER_AUDIT_APPEND_ONLY",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
        ],
    }


def write_role_view_runtime_pointer_activate_candidate(
    *,
    source_role: str,
    reason: str = "",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    if source_role not in {"admin", "lab", "system"}:
        raise ValueError(f"Unsupported role-view activation source_role: {source_role}")
    storage = store or local_jsonl_store_from_env()
    candidate = build_role_view_policy_candidate_report(store=storage)
    replay = build_role_view_policy_replay_report(policy_candidate_report=candidate)
    calibration = build_role_view_policy_calibration_report(replay_report=replay, store=storage)
    gate = build_role_view_policy_promotion_gate(
        replay_report=replay,
        calibration_report=calibration,
        runtime_rollout_switch=True,
    )
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    if not candidate_version or gate.get("eligible_for_runtime") is not True:
        return {
            "version": "v20.role_view_runtime_pointer_activation_result.v1",
            "status": "blocked_by_promotion_gate",
            "active_policy_version": POLICY_VERSION,
            "candidate_policy_version": candidate_version,
            "promotion_gate": gate,
            "runtime_mutation": False,
            "guardrails": [
                "ROLE_VIEW_PROMOTION_GATE_REQUIRED_FOR_ACTIVATION",
                "NO_POINTER_WRITE_ON_BLOCKED_ACTIVATION",
                "CORE_FACTS_REMAIN_DETERMINISTIC",
            ],
        }
    previous = _read_active_pointer(storage)
    previous_active = str(previous.get("active_policy_version", "")) or POLICY_VERSION
    pointer = {
        "version": ROLE_VIEW_ACTIVE_POINTER_VERSION,
        "status": "candidate_active",
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": POLICY_VERSION,
        "source": "admin_role_view_activate_candidate",
        "source_role": source_role,
        "reason": reason[:240],
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
        "guardrails": [
            "ROLE_VIEW_ACTIVATION_WRITES_VERSION_POINTER_ONLY",
            "NO_CHART_FACT_MUTATION",
            "NO_RULE_TRUTH_MUTATION",
        ],
    }
    path = _write_active_pointer(storage, pointer)
    audit = _append_pointer_audit(storage, "v20.role_view_policy_pointer_activation_audit.v1", pointer)
    return {
        "version": "v20.role_view_runtime_pointer_activation_result.v1",
        "status": "candidate_active",
        "active_pointer_path": str(path),
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "promotion_gate": gate,
        "audit": audit,
        "runtime_mutation": True,
        "guardrails": [
            "ROLE_VIEW_ACTIVATION_WRITES_VERSION_POINTER_ONLY",
            "ROLE_VIEW_POINTER_AUDIT_APPEND_ONLY",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
        ],
    }


def _payload_counts(payload: dict[str, object]) -> dict[str, int]:
    return {
        key: len(value)
        for key, value in sorted(payload.items())
        if isinstance(value, list)
    }


def _pointer_status(
    candidate: dict[str, object],
    replay: dict[str, object],
    *,
    runtime_applied: bool,
    answer_governance_applied: bool,
    active_version: str,
    active_pointer: dict[str, object],
) -> str:
    if runtime_applied:
        return "candidate_active"
    if answer_governance_applied:
        return "answer_governance_active"
    if active_pointer and active_version == POLICY_VERSION and int(candidate.get("candidate_count", 0) or 0) > 0:
        return "baseline_active_candidate_shadow"
    if int(candidate.get("candidate_count", 0) or 0) <= 0:
        return "not_enough_data"
    if replay.get("status") == "ready_for_review":
        return "candidate_replay_ready"
    return str(replay.get("status", "")) or "preflight"


def _runtime_applied(candidate: dict[str, object], replay: dict[str, object], promotion_gate: dict[str, object], active_version: str) -> bool:
    return (
        int(candidate.get("candidate_count", 0) or 0) > 0
        and replay.get("status") == "ready_for_review"
        and promotion_gate.get("eligible_for_runtime") is True
        and active_version == str(candidate.get("candidate_policy_version", ""))
    )


def _blocking_gate(candidate: dict[str, object], replay_result: dict[str, object], promotion_gate: dict[str, object]) -> str:
    if int(candidate.get("candidate_count", 0) or 0) <= 0:
        return "not_enough_data"
    if promotion_gate.get("blocking_gate"):
        return str(promotion_gate.get("blocking_gate"))
    return str(replay_result.get("blocking_gate", "")) or "role_view_runtime_pointer_not_enabled"


def _active_version(candidate_version: str, active_pointer: dict[str, object]) -> str:
    active = str(active_pointer.get("active_policy_version", "")) if active_pointer else ""
    if active == candidate_version or active == POLICY_VERSION:
        return active
    return POLICY_VERSION


def _answer_governance_style_policy(store: LocalJsonlStore) -> list[dict[str, object]]:
    report = _read_answer_governance_training_report(store)
    targets = report.get("parameter_targets", {}) if isinstance(report, dict) else {}
    if not isinstance(targets, dict):
        targets = {}
    weight = float(targets.get("role_answer_governance_weight", 0.0) or 0.0)
    prompt_budget_weight = float(targets.get("prompt_context_budget_weight", 0.0) or 0.0)
    stream_quality_weight = float(targets.get("stream_answer_quality_weight", 0.0) or 0.0)
    if weight <= 0:
        return []
    average_quality = float(report.get("average_quality_score", 0.0) or 0.0)
    stream_summary = report.get("stream_answer_governance_summary", {})
    stream_average_quality = (
        float(stream_summary.get("average_quality_score", 0.0) or 0.0)
        if isinstance(stream_summary, dict)
        else 0.0
    )
    rows = []
    for role_key, style_policy in (
        ("guest", "compress_to_plain_boundary"),
        ("user", "preserve_guided_boundary"),
        ("analyst", "preserve_review_boundary"),
        ("admin", "preserve_full_governance_signal"),
        ("lab", "preserve_full_governance_signal"),
    ):
        rows.append(
            {
                "source_role": role_key,
                "style_policy": style_policy,
                "style_weight_delta": round(weight, 4),
                "prompt_context_budget_delta": round(prompt_budget_weight, 4),
                "stream_answer_quality_delta": round(stream_quality_weight, 4),
                "average_quality_score": average_quality,
                "stream_average_quality_score": stream_average_quality,
                "source": "answer_governance_training",
                "runtime_allowed": True,
            }
        )
    return rows


def _read_answer_governance_training_report(store: LocalJsonlStore) -> dict[str, object]:
    for path in (
        store.runtime_dir / "training" / "answer_governance" / "latest.json",
        store.runtime_dir / "training" / "iteration" / "latest.json",
    ):
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("version") == "v20.answer_governance_training_report.v1":
            return payload
        results = payload.get("results", {})
        report = results.get("answer_governance_training", {}) if isinstance(results, dict) else {}
        if isinstance(report, dict) and report.get("version") == "v20.answer_governance_training_report.v1":
            return report
    return {}


def _read_active_pointer(store: LocalJsonlStore) -> dict[str, object]:
    path = store.runtime_dir / ROLE_VIEW_POINTER_RELATIVE_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    if payload.get("version") != ROLE_VIEW_ACTIVE_POINTER_VERSION:
        return {}
    return dict(payload) | {"source_path": path}


def _write_active_pointer(store: LocalJsonlStore, payload: dict[str, object]) -> object:
    path = store.runtime_dir / ROLE_VIEW_POINTER_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _append_pointer_audit(store: LocalJsonlStore, event_version: str, pointer: dict[str, object]) -> dict[str, object]:
    return store.append_record(
        ROLE_VIEW_POINTER_AUDIT_LEDGER,
        {
            "version": event_version,
            "source_role": pointer.get("source_role", ""),
            "active_policy_version": pointer.get("active_policy_version", ""),
            "candidate_policy_version": pointer.get("candidate_policy_version", ""),
            "previous_active_policy_version": pointer.get("previous_active_policy_version", ""),
            "rollback_policy_version": pointer.get("rollback_policy_version", ""),
            "reason": pointer.get("reason", ""),
            "runtime_mutation": False,
            "guardrails": [
                "ROLE_VIEW_POINTER_AUDIT_APPEND_ONLY",
                "NO_SECRET_VALUES_RENDERED",
                "NO_USER_TEXT_REQUIRED",
            ],
        },
    )
