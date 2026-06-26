from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.learning.question_dag_policy_replay import read_question_dag_policy_replay_artifact
from v20.learning.question_ranking_learning import read_question_ranking_learning_artifact
from v20.learning.question_review_training import read_question_review_training_artifact
from v20.learning.role_question_click_training import read_role_question_click_training_artifact
from v20.learning.question_source_training import read_question_source_training_artifact
from v20.interaction.question_atoms import question_atoms_by_key
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env
from v20.validation.next_question_synthetic import read_next_question_synthetic_validation_artifact


QUESTION_RUNTIME_POINTER_VERSION = "v20.question_runtime_pointer.v1"
QUESTION_ACTIVE_POINTER_VERSION = "v20.question_runtime_active_pointer.v1"
QUESTION_BASELINE_VERSION = "v20.question_policy.baseline.v1"
QUESTION_POINTER_AUDIT_LEDGER = "question_runtime_pointer_audit"
QUESTION_POINTER_RELATIVE_PATH = "training/question_policy_versions/active_pointer.json"


def build_question_runtime_pointer(*, store: LocalJsonlStore | None = None) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    source = read_question_source_training_artifact()
    ranking = read_question_ranking_learning_artifact()
    dag = read_question_dag_policy_replay_artifact()
    next_question = read_next_question_synthetic_validation_artifact()
    click = read_role_question_click_training_artifact()
    review = read_question_review_training_artifact()
    candidate = _candidate_policy(source=source, ranking=ranking, dag=dag, next_question=next_question, click=click, review=review)
    active_pointer = _read_active_pointer(storage)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    active_version = _active_version(candidate_version, active_pointer)
    runtime_applied = bool(candidate_version and active_version == candidate_version and candidate.get("eligible_for_runtime"))
    return {
        "version": QUESTION_RUNTIME_POINTER_VERSION,
        "status": "candidate_active" if runtime_applied else ("candidate_ready" if candidate.get("eligible_for_runtime") else "blocked"),
        "policy_family": "question_policy",
        "active_policy_version": active_version,
        "candidate_policy_version": candidate_version,
        "rollback_policy_version": QUESTION_BASELINE_VERSION,
        "active_pointer_source": str(active_pointer.get("source", "")) if active_pointer else "baseline",
        "candidate": candidate,
        "policy_payload": candidate.get("policy_payload", {}) if runtime_applied else {},
        "runtime_applied": runtime_applied,
        "runtime_allowed": runtime_applied,
        "blocking_gate": "" if runtime_applied else str(candidate.get("blocking_gate", "")),
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_RUNTIME_POINTER_READ_ONLY",
            "QUESTION_POINTER_USES_SOURCE_RANKING_DAG_ARTIFACTS",
            "NO_NEW_QUESTION_GENERATION",
            "NO_CHART_FACT_MUTATION",
        ],
    }


def write_question_runtime_pointer_activate_candidate(
    *,
    source_role: str,
    reason: str = "",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    if source_role not in {"admin", "lab", "system"}:
        raise ValueError(f"Unsupported question pointer activation source_role: {source_role}")
    storage = store or local_jsonl_store_from_env()
    source = read_question_source_training_artifact()
    ranking = read_question_ranking_learning_artifact()
    dag = read_question_dag_policy_replay_artifact()
    next_question = read_next_question_synthetic_validation_artifact()
    click = read_role_question_click_training_artifact()
    review = read_question_review_training_artifact()
    candidate = _candidate_policy(source=source, ranking=ranking, dag=dag, next_question=next_question, click=click, review=review)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    if not candidate.get("eligible_for_runtime") or not candidate_version:
        return {
            "version": "v20.question_runtime_pointer_activation_result.v1",
            "status": "blocked_by_machine_gate",
            "candidate_policy_version": candidate_version,
            "active_policy_version": QUESTION_BASELINE_VERSION,
            "candidate": candidate,
            "runtime_mutation": False,
            "guardrails": [
                "QUESTION_MACHINE_GATE_REQUIRED",
                "NO_POINTER_WRITE_ON_BLOCKED_ACTIVATION",
                "NO_HUMAN_REVIEW_FALLBACK",
            ],
        }
    previous = _read_active_pointer(storage)
    previous_active = str(previous.get("active_policy_version", "")) or QUESTION_BASELINE_VERSION
    pointer = {
        "version": QUESTION_ACTIVE_POINTER_VERSION,
        "status": "candidate_active",
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": QUESTION_BASELINE_VERSION,
        "source": "admin_question_optimizer_activate_candidate",
        "source_role": source_role,
        "reason": reason[:240],
        "candidate_summary": _candidate_summary(candidate),
        "policy_payload": candidate.get("policy_payload", {}),
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
        "guardrails": [
            "QUESTION_ACTIVATION_WRITES_VERSION_POINTER_ONLY",
            "QUESTION_POLICY_REORDERS_ONLY",
            "NO_NEW_QUESTION_GENERATION",
        ],
    }
    path = _write_active_pointer(storage, pointer)
    audit = _append_pointer_audit(storage, "v20.question_runtime_pointer_activation_audit.v1", pointer)
    return {
        "version": "v20.question_runtime_pointer_activation_result.v1",
        "status": "candidate_active",
        "active_pointer_path": str(path),
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "candidate": candidate,
        "audit": audit,
        "runtime_mutation": True,
        "guardrails": [
            "QUESTION_POINTER_AUDIT_APPEND_ONLY",
            "QUESTION_POLICY_CAN_ROLL_BACK_TO_BASELINE",
            "RUNTIME_CONSUMES_VERSIONED_QUESTION_POLICY",
        ],
    }


def _candidate_policy(
    *,
    source: dict[str, object],
    ranking: dict[str, object],
    dag: dict[str, object],
    next_question: dict[str, object],
    click: dict[str, object],
    review: dict[str, object],
) -> dict[str, object]:
    source_rows = _source_policy_rows(source)
    rank_policy = _rank_policy(ranking)
    dag_rows = _dag_transition_rows(dag)
    next_question_policy = _next_question_plan_policy(next_question)
    feedback_policy = _next_question_feedback_policy(click)
    review_policy = _question_review_feedback_policy(review)
    policy_payload: dict[str, object] = {}
    if source_rows:
        policy_payload["question_source_weight_policy"] = source_rows
    if rank_policy:
        policy_payload["question_rank_policy"] = rank_policy
    if dag_rows:
        policy_payload["question_dag_transition_policy"] = dag_rows
    if next_question_policy:
        policy_payload["next_question_plan_policy"] = next_question_policy
    if feedback_policy:
        existing = policy_payload.get("next_question_plan_policy", {})
        policy_payload["next_question_plan_policy"] = _merge_next_question_policies(existing, feedback_policy)
    if review_policy:
        existing = policy_payload.get("next_question_plan_policy", {})
        policy_payload["next_question_plan_policy"] = _merge_next_question_policies(existing, review_policy)
    blocking_gate = "" if policy_payload else _blocking_gate(source=source, ranking=ranking, dag=dag, next_question=next_question)
    version_seed = json.dumps(policy_payload, ensure_ascii=False, sort_keys=True)
    candidate_version = f"v20.question_policy.candidate.{_hash(version_seed)}" if policy_payload else ""
    return {
        "version": "v20.question_runtime_policy_candidate.v1",
        "status": "ready" if policy_payload else "blocked",
        "candidate_policy_version": candidate_version,
        "eligible_for_runtime": bool(policy_payload),
        "question_source_policy_count": len(source_rows),
        "question_rank_policy_ready": bool(rank_policy),
        "question_dag_transition_count": len(dag_rows),
        "next_question_plan_policy_ready": bool(next_question_policy),
        "next_question_feedback_policy_ready": bool(feedback_policy),
        "question_review_feedback_policy_ready": bool(review_policy),
        "blocking_gate": blocking_gate,
        "policy_payload": policy_payload,
        "source_reports": {
            "question_source_training_status": source.get("status", "not_built"),
            "question_ranking_training_status": ranking.get("status", "not_built"),
            "question_dag_policy_replay_status": dag.get("status", "not_built"),
            "question_dag_candidate_win": _dag_candidate_win(dag),
            "next_question_synthetic_validation_status": next_question.get("status", "not_built"),
            "role_question_click_training_status": click.get("status", "not_built"),
            "question_review_training_status": review.get("status", "not_built"),
        },
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_CANDIDATE_FROM_MACHINE_ARTIFACTS",
            "RANKING_POLICY_REORDERS_ONLY",
            "DAG_POLICY_REQUIRES_OFFLINE_REPLAY_WIN",
        ],
    }


def _source_policy_rows(source: dict[str, object]) -> list[dict[str, object]]:
    if source.get("status") != "ready":
        return []
    rows = []
    for proposal in source.get("training_proposals", ()):
        if not isinstance(proposal, dict):
            continue
        source_key = str(proposal.get("source_key", ""))
        if not source_key:
            continue
        rows.append(
            {
                "source_key": source_key,
                "source_weight_delta": _source_weight_delta(proposal),
                "sample_count": int(proposal.get("sample_count", 0) or 0),
                "average_graph_score": float(proposal.get("average_graph_score", 0.0) or 0.0),
                "average_question_score": float(proposal.get("average_question_score", 0.0) or 0.0),
                "source": "question_source_training",
            }
        )
    return sorted(rows, key=lambda row: str(row["source_key"]))


def _rank_policy(ranking: dict[str, object]) -> dict[str, object]:
    if ranking.get("status") != "ready":
        return {}
    policy = ranking.get("shadow_policy", {})
    if not isinstance(policy, dict):
        return {}
    return {
        "policy_id": str(policy.get("policy_id", "v20.question_ranking.pointer_policy")),
        "domain_weights": _float_map(policy.get("domain_weights", {})),
        "stage_weights": _float_map(policy.get("stage_weights", {})),
        "status_weights": _float_map(policy.get("status_weights", {})),
        "question_key_weights": _float_map(policy.get("question_key_weights", {})),
        "rule_prefix_weights": _float_map(policy.get("rule_prefix_weights", {})),
        "feature_count_weight": float(policy.get("feature_count_weight", 0.004) or 0.004),
        "max_feature_count": int(policy.get("max_feature_count", 8) or 8),
        "alignment_weight": float(policy.get("alignment_weight", 0.18) or 0.18),
        "max_adjustment": float(policy.get("max_adjustment", 0.12) or 0.12),
        "source": "question_runtime_pointer",
        "status": "active",
        "guardrails": [
            "POINTER_PROMOTED",
            "RANKING_POLICY_REORDERS_ONLY",
            "NO_NEW_QUESTION_GENERATION",
        ],
    }


def _dag_transition_rows(dag: dict[str, object]) -> list[dict[str, object]]:
    if dag.get("status") != "ready_for_review" or not _dag_candidate_win(dag):
        return []
    comparisons = [row for row in dag.get("comparisons", ()) if isinstance(row, dict)]
    rows = []
    for row in comparisons:
        if str(row.get("comparison_key", "")) != "synthetic_transition_support":
            continue
        rows.append(
            {
                "transition_policy": "synthetic_transition_support",
                "offline_score": float(row.get("offline_score", 0.0) or 0.0),
                "risk_count": int(row.get("risk_count", 0) or 0),
                "candidate_effect": str(row.get("candidate_effect", "")),
                "source": "question_dag_policy_replay",
            }
        )
    return rows


def _next_question_plan_policy(next_question: dict[str, object]) -> dict[str, object]:
    if next_question.get("status") != "ready":
        return {}
    policy = next_question.get("candidate_policy", {})
    if not isinstance(policy, dict) or policy.get("status") != "ready":
        return {}
    return {
        "policy_id": "v20.next_question_plan.synthetic_pointer",
        "stage_boosts": _float_map(policy.get("stage_boosts", {})),
        "topic_boosts": _float_map(policy.get("topic_boosts", {})),
        "source": "next_question_synthetic_validation",
        "status": "active",
        "guardrails": [
            "POINTER_PROMOTED",
            "NEXT_QUESTION_POLICY_REORDERS_ONLY",
            "NO_NEW_QUESTION_GENERATION",
        ],
    }


def _next_question_feedback_policy(click: dict[str, object]) -> dict[str, object]:
    if click.get("status") != "ready":
        return {}
    policy = click.get("next_question_feedback_policy", {})
    if not isinstance(policy, dict) or policy.get("status") != "ready":
        return {}
    return {
        "policy_id": "v20.next_question.feedback_pointer",
        "atom_boosts": _float_map(policy.get("atom_boosts", {})),
        "atom_penalties": _float_map(policy.get("atom_penalties", {})),
        "topic_boosts": _float_map(policy.get("topic_boosts", {})),
        "stage_boosts": _float_map(policy.get("stage_boosts", {})),
        "source": "role_question_click_training",
        "status": "active",
        "guardrails": [
            "STRUCTURED_CLICK_REWARD_ONLY",
            "NEXT_QUESTION_POLICY_REORDERS_ONLY",
            "NO_NEW_QUESTION_GENERATION",
        ],
    }


def _question_review_feedback_policy(review: dict[str, object]) -> dict[str, object]:
    if review.get("status") != "ready":
        return {}
    atom_boosts: dict[str, float] = {}
    atom_penalties: dict[str, float] = {}
    for recommendation in review.get("recommendations", ()):
        if not isinstance(recommendation, dict):
            continue
        recommendation_type = str(recommendation.get("recommendation_type", ""))
        question_key = str(recommendation.get("question_key", ""))
        role_target = str(recommendation.get("role_target", "user")) or "user"
        if not question_key:
            continue
        atoms = question_atoms_by_key(question_key, role_key=role_target)
        if not atoms and role_target not in {"user", "guest"}:
            atoms = question_atoms_by_key(question_key, role_key="user")
        magnitude = 0.0
        if recommendation_type == "approve_question_candidate":
            magnitude = 0.025
        elif recommendation_type == "rewrite_question_candidate":
            magnitude = -0.025
        elif recommendation_type == "suppress_question_candidate":
            magnitude = -0.06
        for atom in atoms:
            if magnitude > 0:
                atom_boosts[atom.atom_id] = round(atom_boosts.get(atom.atom_id, 0.0) + magnitude, 4)
            elif magnitude < 0:
                atom_penalties[atom.atom_id] = round(atom_penalties.get(atom.atom_id, 0.0) + magnitude, 4)
    if not atom_boosts and not atom_penalties:
        return {}
    return {
        "policy_id": "v20.next_question.review_feedback_pointer",
        "atom_boosts": atom_boosts,
        "atom_penalties": atom_penalties,
        "topic_boosts": {},
        "stage_boosts": {},
        "source": "question_review_training",
        "status": "active",
        "guardrails": [
            "STRUCTURED_REVIEW_RECOMMENDATIONS_ONLY",
            "NEXT_QUESTION_POLICY_REORDERS_ONLY",
            "NO_NEW_QUESTION_GENERATION",
        ],
    }


def _merge_next_question_policies(base: object, feedback: dict[str, object]) -> dict[str, object]:
    merged = dict(base) if isinstance(base, dict) else {
        "policy_id": "v20.next_question.combined_pointer",
        "status": "active",
        "source": "combined_next_question_policy",
        "guardrails": [],
    }
    merged["policy_id"] = "v20.next_question.combined_pointer"
    merged["status"] = "active"
    merged["source"] = "synthetic_click_and_review_feedback"
    merged["stage_boosts"] = _sum_float_maps(merged.get("stage_boosts", {}), feedback.get("stage_boosts", {}))
    merged["topic_boosts"] = _sum_float_maps(merged.get("topic_boosts", {}), feedback.get("topic_boosts", {}))
    merged["atom_boosts"] = _sum_float_maps(merged.get("atom_boosts", {}), feedback.get("atom_boosts", {}))
    merged["atom_penalties"] = _sum_float_maps(merged.get("atom_penalties", {}), feedback.get("atom_penalties", {}))
    merged["guardrails"] = tuple(
        dict.fromkeys(
            tuple(merged.get("guardrails", ()))
            + tuple(feedback.get("guardrails", ()))
            + ("COMBINED_SYNTHETIC_AND_CLICK_FEEDBACK",)
        )
    )
    return merged


def _sum_float_maps(left: object, right: object) -> dict[str, float]:
    rows = _float_map(left)
    for key, value in _float_map(right).items():
        rows[key] = round(rows.get(key, 0.0) + value, 4)
    return rows


def _source_weight_delta(row: dict[str, object]) -> float:
    graph = float(row.get("average_graph_score", 0.0) or 0.0)
    question = float(row.get("average_question_score", 0.0) or 0.0)
    sample_bonus = min(0.02, int(row.get("sample_count", 0) or 0) * 0.002)
    return round(min(0.06, 0.01 + graph * 0.04 + question * 0.02 + sample_bonus), 4)


def _float_map(value: object) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    rows: dict[str, float] = {}
    for key, raw in value.items():
        try:
            rows[str(key)] = round(float(raw or 0.0), 4)
        except (TypeError, ValueError):
            continue
    return rows


def _dag_candidate_win(dag: dict[str, object]) -> bool:
    impact = dag.get("impact_summary", {}) if isinstance(dag.get("impact_summary"), dict) else {}
    return bool(impact.get("candidate_win"))


def _blocking_gate(
    *,
    source: dict[str, object],
    ranking: dict[str, object],
    dag: dict[str, object],
    next_question: dict[str, object],
) -> str:
    gates = []
    if source.get("status") != "ready":
        gates.append("question_source_training_not_ready")
    elif not source.get("training_proposals"):
        gates.append("question_source_training_has_no_candidates")
    if ranking.get("status") != "ready":
        gates.append("question_ranking_training_not_ready")
    elif not isinstance(ranking.get("shadow_policy"), dict):
        gates.append("question_ranking_shadow_policy_missing")
    if dag.get("status") != "ready_for_review":
        gates.append("question_dag_policy_replay_not_ready")
    elif not _dag_candidate_win(dag):
        gates.append("question_dag_policy_replay_candidate_not_win")
    if next_question.get("status") != "ready":
        gates.append("next_question_synthetic_validation_not_ready")
    return ",".join(gates) or "question_policy_payload_empty"


def _candidate_summary(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_policy_version": candidate.get("candidate_policy_version", ""),
        "question_source_policy_count": candidate.get("question_source_policy_count", 0),
        "question_rank_policy_ready": candidate.get("question_rank_policy_ready", False),
        "question_dag_transition_count": candidate.get("question_dag_transition_count", 0),
        "next_question_plan_policy_ready": candidate.get("next_question_plan_policy_ready", False),
        "next_question_feedback_policy_ready": candidate.get("next_question_feedback_policy_ready", False),
        "question_review_feedback_policy_ready": candidate.get("question_review_feedback_policy_ready", False),
        "blocking_gate": candidate.get("blocking_gate", ""),
    }


def _active_version(candidate_version: str, active_pointer: dict[str, object]) -> str:
    active = str(active_pointer.get("active_policy_version", "")) if active_pointer else ""
    if active == candidate_version or active == QUESTION_BASELINE_VERSION:
        return active or QUESTION_BASELINE_VERSION
    return QUESTION_BASELINE_VERSION


def _read_active_pointer(store: LocalJsonlStore) -> dict[str, object]:
    path = store.runtime_dir / QUESTION_POINTER_RELATIVE_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict) or payload.get("version") != QUESTION_ACTIVE_POINTER_VERSION:
        return {}
    return dict(payload) | {"source_path": path}


def _write_active_pointer(store: LocalJsonlStore, payload: dict[str, object]) -> Path:
    path = store.runtime_dir / QUESTION_POINTER_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _append_pointer_audit(store: LocalJsonlStore, event_version: str, pointer: dict[str, object]) -> dict[str, object]:
    return store.append_record(
        QUESTION_POINTER_AUDIT_LEDGER,
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
                "QUESTION_POINTER_AUDIT_APPEND_ONLY",
                "NO_SECRET_VALUES_RENDERED",
            ],
        },
    )


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]
