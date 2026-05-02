from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.learning.training_iteration import run_training_iteration
from v20.storage.local_jsonl import local_jsonl_store_from_env

ProgressCallback = Callable[[str], None]


def run_self_evolution_cycle(
    *,
    write: bool = False,
    include_rule_batch: bool = True,
    corpus_preview_limit: int = 0,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    training = run_training_iteration(
        write=False,
        include_rule_batch=include_rule_batch,
        corpus_preview_limit=corpus_preview_limit,
        progress=progress,
    )
    manifest = build_self_evolution_manifest(training)
    if write:
        return write_self_evolution_artifact(manifest, output_dir=output_dir)
    return manifest


def build_self_evolution_manifest(training_report: dict[str, object]) -> dict[str, object]:
    results = training_report.get("results", {})
    if not isinstance(results, dict):
        results = {}
    requests = _active_item_requests(results)
    blockers = _blocked_reasons(training_report, results)
    status = "blocked" if blockers else ("active_ready" if requests["total_request_count"] else "clean")
    status = "active_ready" if not blockers and requests["total_request_count"] else status
    return {
        "version": "v20.self_evolution_manifest.v1",
        "run_id": _run_id(),
        "status": status,
        "training_status": training_report.get("status", ""),
        "quality_status": training_report.get("quality_status", ""),
        "phase_count": training_report.get("phase_count", 0),
        "failure_count": training_report.get("failure_count", 0),
        "quality_finding_count": training_report.get("quality_finding_count", 0),
        "source_versions": _source_versions(results),
        "active_item_requests": requests,
        "blocked_reasons": blockers,
        "activation_policy": {
            "runtime_activation_allowed": True,
            "required_status_before_runtime": "active",
            "required_gates": (
                "contract_shape",
                "evidence_pack_link",
                "runtime_feedback_loop",
            ),
        },
        "algorithm_tracks": {
            "active_now": (
                "symbolic_expert_system",
                "defeasible_reasoning",
                "certainty_factor",
                "active_learning_synthetic_gaps",
                "feature_cooccurrence_mining",
                "runtime_replay_evaluation",
                "learning_to_rank_question_order",
                "bayesian_confidence_calibration",
            ),
            "active_iterative": (
                "embedding_retrieval_recall",
                "coverage_gap_clustering",
                "weak_supervision_signal_grouping",
                "pairwise_preference_ranking",
            ),
            "deferred": (
                "gnn_rule_graph_embedding",
                "reinforcement_learning_dialog_policy",
                "neural_conclusion_generation",
            ),
        },
        "artifact_inputs": tuple(results.keys()),
        "runtime_mutation": False,
        "guardrails": (
            "SELF_EVOLUTION_IS_BACKEND_SCRIPT_ONLY",
            "LLM_GENERATES_ACTIVE_ITEMS_NOT_CORE_TRUTH",
            "SYNTHETIC_CASES_VALIDATE_STRUCTURE_NOT_DESTINY",
            "CORPUS_IS_PRIOR_AND_COVERAGE_NOT_RULE_TRUTH",
            "MANIFEST_CAN_FEED_ACTIVE_RULES_AND_POLICIES",
            "CONTINUOUS_ITERATION_REFINES_ACTIVE_OUTPUTS",
        ),
    }


def write_self_evolution_artifact(
    manifest: dict[str, object],
    *,
    output_dir: Path | None = None,
) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    root = output_dir or runtime_dir / "training" / "evolution"
    root.mkdir(parents=True, exist_ok=True)
    run_id = str(manifest.get("run_id", _run_id()))
    run_dir = root / _safe(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "latest.json"
    manifest_path = run_dir / "manifest.json"
    payload = manifest | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.self_evolution_artifact_write.v1",
        "status": "written",
        "manifest_status": manifest.get("status", ""),
        "latest_path": str(latest_path),
        "manifest_path": str(manifest_path),
        "total_request_count": manifest.get("active_item_requests", {}).get("total_request_count", 0)
        if isinstance(manifest.get("active_item_requests"), dict)
        else 0,
        "runtime_mutation": True,
        "guardrails": (
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "ACTIVE_PACKAGE_OUTPUT_ALLOWED",
        ),
    }


def read_self_evolution_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "evolution") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.self_evolution_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {
        "latest_path": str(latest_path),
        "runtime_mutation": False,
    }


def _active_item_requests(results: dict[str, object]) -> dict[str, object]:
    rule_requests = _rule_active_item_requests(results)
    portrait_requests = _portrait_active_item_requests(results)
    feature_requests = _feature_active_item_requests(results)
    question_requests = _question_active_item_requests(results)
    synthetic_requests = _synthetic_case_requests(results)
    total = sum(
        len(rows)
        for rows in (rule_requests, portrait_requests, feature_requests, question_requests, synthetic_requests)
    )
    return {
        "version": "v20.self_evolution_active_item_requests.v1",
        "total_request_count": total,
        "rule_active_item_requests": tuple(rule_requests),
        "portrait_active_item_requests": tuple(portrait_requests),
        "feature_active_item_requests": tuple(feature_requests),
        "question_active_item_requests": tuple(question_requests),
        "synthetic_case_requests": tuple(synthetic_requests),
    }


def _rule_active_item_requests(results: dict[str, object]) -> list[dict[str, object]]:
    training = _dict(results.get("rule_synthetic_training"))
    rows = _dict_list(training.get("rule_domain_training"))
    requests = []
    for row in rows:
        domain = str(row.get("domain", ""))
        action = str(row.get("training_action", ""))
        if action == "eligible_for_active_weight":
            requests.append(
                _request(
                    "rule_active_item",
                    domain,
                    "activate_rule_weight_from_synthetic_pass",
                    source="rule_synthetic_training",
                    evidence={"case_count": row.get("case_count", 0), "synthetic_confidence": row.get("synthetic_confidence", 0.0)},
                )
            )
        elif action:
            requests.append(
                _request(
                    "rule_active_item",
                    domain,
                    action,
                    source="rule_synthetic_training",
                    evidence={"failure_count": row.get("fail_count", 0), "case_ids": row.get("case_ids", ())},
                )
            )
    return requests[:32]


def _portrait_active_item_requests(results: dict[str, object]) -> list[dict[str, object]]:
    replay = _dict(results.get("rule_replay_eval"))
    domain_counts = Counter(str(row.get("domain", "")) for row in _dict_list(replay.get("evaluations")) if row.get("domain"))
    requests = [
        _request(
            "portrait_active_item",
            domain,
            "activate_topic_projection_axis_for_runtime_rule",
            source="rule_runtime_replay",
            evidence={"runtime_replay_rows": count},
        )
        for domain, count in sorted(domain_counts.items())
    ]
    return requests[:24]


def _feature_active_item_requests(results: dict[str, object]) -> list[dict[str, object]]:
    dynamic = _dict(results.get("dynamic_decision_training"))
    coverage = _dict(dynamic.get("coverage_summary"))
    requests = []
    for domain in _list(coverage.get("decision_domains")):
        requests.append(
            _request(
                "feature_active_item",
                str(domain),
                "check_feature_state_coverage_and_counterevidence",
                source="dynamic_decision_training",
                evidence={"coverage": "decision_domain_seen"},
            )
        )
    return requests[:24]


def _question_active_item_requests(results: dict[str, object]) -> list[dict[str, object]]:
    dynamic = _dict(results.get("dynamic_decision_training"))
    coverage = _dict(dynamic.get("coverage_summary"))
    requests = []
    for question_key in _list(coverage.get("question_keys")):
        requests.append(
            _request(
                "question_active_item",
                str(question_key),
                "evaluate_question_ranking_against_current_chart_features",
                source="dynamic_decision_training",
                evidence={"coverage": "question_key_seen"},
            )
        )
    return requests[:24]


def _synthetic_case_requests(results: dict[str, object]) -> list[dict[str, object]]:
    requests = []
    split = _dict(results.get("rule_subcondition_split"))
    for packet in _dict_list(split.get("packets")):
        if int(packet.get("counterexample_signal_count", 0) or 0) > 0:
            requests.append(
                _request(
                    "synthetic_case",
                    str(packet.get("domain", "")),
                    "materialize_counterexample_case_for_rule_subcondition",
                    source="rule_subcondition_split",
                    evidence={
                        "rule_key": packet.get("rule_key", ""),
                        "counterexample_signal_count": packet.get("counterexample_signal_count", 0),
                    },
                )
            )
    training = _dict(results.get("rule_synthetic_training"))
    suite = _dict(training.get("suite"))
    for failure in _list(suite.get("failures")):
        requests.append(
            _request(
                "synthetic_case",
                "unknown",
                "repair_or_add_synthetic_case_for_failure",
                source="rule_synthetic_training",
                evidence={"failure": failure},
            )
        )
    return requests[:32]


def _blocked_reasons(training_report: dict[str, object], results: dict[str, object]) -> tuple[str, ...]:
    blockers = [str(row) for row in training_report.get("failures", ()) if str(row)]
    for key, payload in results.items():
        if isinstance(payload, dict) and payload.get("status") in {"fail", "blocked"}:
            blockers.append(f"{key}:status:{payload.get('status')}")
    return tuple(dict.fromkeys(blockers))


def _source_versions(results: dict[str, object]) -> dict[str, object]:
    return {
        key: value.get("version", "")
        for key, value in results.items()
        if isinstance(value, dict) and value.get("version")
    }


def _request(kind: str, target: str, action: str, *, source: str, evidence: dict[str, object]) -> dict[str, object]:
    return {
        "version": "v20.self_evolution_request.v1",
        "request_type": kind,
        "target": target,
        "recommended_action": action,
        "source_artifact": source,
        "evidence": evidence,
        "active_item_status": "active_request",
        "runtime_allowed": True,
    }


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    if not isinstance(value, (list, tuple)):
        return []
    return list(value)


def _dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [row for row in value if isinstance(row, dict)]


def _run_id() -> str:
    return f"v20.evolution.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value.strip())
