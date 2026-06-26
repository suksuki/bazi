from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from v20.learning.role_question_click_training import build_role_question_click_training_report
from v20.role_view.policy import POLICY_VERSION, role_view_policy
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


POLICY_FAMILY = "role_view_policy"
BASELINE_POLICY_VERSION = POLICY_VERSION


def build_role_view_policy_candidate_report(
    *,
    click_training_report: dict[str, object] | None = None,
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    report = click_training_report or build_role_question_click_training_report(store=store)
    candidates = _candidate_rows(report)
    candidate_hash = _hash_json(candidates)
    return {
        "version": "v20.role_view_policy_candidate_report.v1",
        "status": "ready_for_replay" if candidates else "not_enough_data",
        "policy_family": POLICY_FAMILY,
        "baseline_policy_version": BASELINE_POLICY_VERSION,
        "candidate_policy_version": f"v20.role_view_policy.candidate.{candidate_hash}",
        "source_report_version": report.get("version", ""),
        "source_click_count": report.get("click_count", 0),
        "candidate_count": len(candidates),
        "candidate_hash": candidate_hash,
        "candidates": candidates,
        "policy_payload": _policy_payload(candidates),
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_VIEW_POLICY_CANDIDATE_IS_OFFLINE_ONLY",
            "NO_RUNTIME_ROLE_VIEW_POLICY_MUTATION",
            "NO_CHART_FACT_MUTATION",
            "PROMOTION_REQUIRES_REPLAY",
        ],
    }


def write_role_view_policy_candidate_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_role_view_policy_candidate_report(store=storage)
    directory = output_dir or storage.runtime_dir / "training" / "role_view_policy_candidates"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"role_view_policy_candidate_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.role_view_policy_candidate_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "candidate_policy_version": report["candidate_policy_version"],
        "candidate_count": report["candidate_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_POLICY_PROMOTION",
        ],
    }


def read_role_view_policy_candidate_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "role_view_policy_candidates") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.role_view_policy_candidate_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _candidate_rows(report: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for recommendation in report.get("recommendations", ()):
        if not isinstance(recommendation, dict):
            continue
        role = str(recommendation.get("source_role", ""))
        if not role:
            continue
        rec_type = str(recommendation.get("recommendation_type", ""))
        key = str(recommendation.get("recommendation_key", ""))
        if rec_type == "review_question_limit_and_ordering":
            rows.append(_question_limit_candidate(role, key, recommendation))
        elif rec_type == "consider_group_boost":
            rows.append(_boost_candidate(role, "group", key, recommendation))
        elif rec_type == "consider_domain_boost":
            rows.append(_boost_candidate(role, "domain", key, recommendation))
        elif rec_type == "consider_strategy_boost":
            rows.append(_boost_candidate(role, "strategy", key, recommendation))
        elif rec_type == "review_seed_question_fit":
            rows.append(_seed_fit_candidate(role, key, recommendation))
        elif rec_type in {"boost_question_candidate", "suppress_question_candidate", "keep_collecting_reward"}:
            rows.append(_reward_candidate(role, key, recommendation, rec_type))
    return [row for row in rows if row]


def _question_limit_candidate(role: str, key: str, recommendation: dict[str, object]) -> dict[str, object]:
    policy = role_view_policy(role)
    return {
        "candidate_id": _candidate_id("question_limit", role, key),
        "candidate_type": "role_view_question_limit_policy",
        "source_role": role,
        "suggested_action": "review_question_limit_and_ordering",
        "current_question_limit": policy.question_limit,
        "suggested_question_limit": policy.question_limit,
        "source_recommendation_key": key,
        "basis": recommendation.get("basis", ""),
        "status": "candidate",
        "next_gate": "role_view_policy_replay",
        "runtime_allowed": False,
    }


def _boost_candidate(role: str, boost_type: str, key: str, recommendation: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_id": _candidate_id(boost_type, role, key),
        "candidate_type": f"role_view_{boost_type}_boost_policy",
        "source_role": role,
        "boost_type": boost_type,
        "boost_key": key.rsplit(".", 1)[-1],
        "suggested_action": f"consider_{boost_type}_boost",
        "source_recommendation_key": key,
        "basis": recommendation.get("basis", ""),
        "status": "candidate",
        "next_gate": "role_view_policy_replay",
        "runtime_allowed": False,
    }


def _seed_fit_candidate(role: str, key: str, recommendation: dict[str, object]) -> dict[str, object]:
    seed_key = _seed_key_from_recommendation(key, role)
    return {
        "candidate_id": _candidate_id("seed_fit", role, key),
        "candidate_type": "role_view_seed_fit_policy",
        "source_role": role,
        "seed_key": seed_key,
        "suggested_action": "review_seed_question_fit",
        "source_recommendation_key": key,
        "basis": recommendation.get("basis", ""),
        "status": "candidate",
        "next_gate": "role_view_policy_replay",
        "runtime_allowed": False,
    }


def _seed_key_from_recommendation(key: str, role: str) -> str:
    prefix = f"role_view.seed.review.{role}."
    if key.startswith(prefix):
        return key.removeprefix(prefix)
    return key


def _policy_payload(candidates: list[dict[str, object]]) -> dict[str, object]:
    payload: dict[str, object] = {
        "question_limit_policy": [],
        "group_boost_policy": [],
        "domain_boost_policy": [],
        "strategy_boost_policy": [],
        "seed_fit_policy": [],
        "reward_policy": [],
    }
    for row in candidates:
        candidate_type = str(row.get("candidate_type", ""))
        if candidate_type == "role_view_question_limit_policy":
            payload["question_limit_policy"].append(row)
        elif candidate_type == "role_view_group_boost_policy":
            payload["group_boost_policy"].append(row)
        elif candidate_type == "role_view_domain_boost_policy":
            payload["domain_boost_policy"].append(row)
        elif candidate_type == "role_view_strategy_boost_policy":
            payload["strategy_boost_policy"].append(row)
        elif candidate_type == "role_view_seed_fit_policy":
            payload["seed_fit_policy"].append(row)
        elif candidate_type == "role_view_reward_policy":
            payload["reward_policy"].append(row)
    return payload


def _reward_candidate(role: str, key: str, recommendation: dict[str, object], rec_type: str) -> dict[str, object]:
    return {
        "candidate_id": _candidate_id("reward", role, key),
        "candidate_type": "role_view_reward_policy",
        "source_role": role,
        "suggested_action": rec_type,
        "question_key": key.rsplit(".", 1)[-1],
        "source_recommendation_key": key,
        "basis": recommendation.get("basis", ""),
        "status": "candidate",
        "next_gate": "role_view_policy_replay",
        "runtime_allowed": False,
    }


def _candidate_id(*parts: str) -> str:
    return "role_view.candidate." + _hash_json(parts)


def _hash_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
