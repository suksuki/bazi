from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


RELEASE_CANDIDATE_GATE_REVIEW_VERSION = "v30.release_candidate_gate_review.v1"


def build_release_candidate_gate_review(*, release_gate_result: dict[str, Any]) -> dict[str, Any]:
    release_gate_result = release_gate_result if isinstance(release_gate_result, dict) else {}
    checks = release_gate_result.get("checks", [])
    checks = checks if isinstance(checks, list) else []
    check_statuses = {
        str(row.get("check_id") or ""): str(row.get("status") or "")
        for row in checks
        if isinstance(row, dict) and row.get("check_id")
    }
    artifact_review = (
        release_gate_result.get("artifact_review", {})
        if isinstance(release_gate_result.get("artifact_review"), dict) else {}
    )
    corpus = artifact_review.get("corpus_518k_summary", {}) if isinstance(artifact_review.get("corpus_518k_summary"), dict) else {}
    sample = corpus.get("sample", {}) if isinstance(corpus.get("sample"), dict) else {}
    shard = corpus.get("shard", {}) if isinstance(corpus.get("shard"), dict) else {}
    decision = _decision(
        mode=str(release_gate_result.get("mode") or ""),
        status=str(release_gate_result.get("status") or ""),
        promotion_signal=str(release_gate_result.get("promotion_signal") or ""),
        check_statuses=check_statuses,
        artifact_review_status=str(artifact_review.get("status") or ""),
    )
    return {
        "version": RELEASE_CANDIDATE_GATE_REVIEW_VERSION,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "decision": decision,
        "release_gate_summary": {
            "run_id": str(release_gate_result.get("run_id") or ""),
            "mode": str(release_gate_result.get("mode") or ""),
            "status": str(release_gate_result.get("status") or ""),
            "promotion_signal": str(release_gate_result.get("promotion_signal") or ""),
            "check_count": len(checks),
            "check_statuses": check_statuses,
        },
        "artifact_review_summary": {
            "version": str(artifact_review.get("version") or ""),
            "status": str(artifact_review.get("status") or ""),
            "check_count": int(artifact_review.get("check_count", 0) or 0),
            "missing_sections": artifact_review.get("missing_sections", [])
            if isinstance(artifact_review.get("missing_sections"), list) else [],
            "failed_checks": (
                artifact_review.get("promotion_review", {})
                if isinstance(artifact_review.get("promotion_review"), dict) else {}
            ).get("failed_checks", []),
        },
        "corpus_518k_summary": {
            "sample_case_count": int(sample.get("case_count", 0) or 0),
            "sample_artifact_record_id": str(sample.get("artifact_record_id") or ""),
            "shard_case_count": int(shard.get("case_count", 0) or 0),
            "shard_artifact_record_id": str(shard.get("artifact_record_id") or ""),
            "artifact_record_ids": corpus.get("artifact_record_ids", [])
            if isinstance(corpus.get("artifact_record_ids"), list) else [],
            "boundary": "r11_reviews_sample_and_selected_shard_artifacts_not_full_518k",
        },
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "requires_explicit_human_release_boundary": True,
            "full_pytest_required_before_external_release": True,
            "full_518k_required_before_external_release": False,
            "boundary": "r11_standard_gate_is_release_candidate_evidence_not_pointer_promotion",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "release_candidate_gate_review_is_read_only_and_does_not_mutate_chart_facts_or_policy_pointers",
    }


def _decision(
    *,
    mode: str,
    status: str,
    promotion_signal: str,
    check_statuses: dict[str, str],
    artifact_review_status: str,
) -> dict[str, Any]:
    blockers = []
    required_checks = {
        "runtime_smoke",
        "production_api_smoke",
        "llm_live_smoke",
        "post_seal_contracts",
        "synthetic_all",
        "518k_sample",
        "518k_shard",
    }
    missing_checks = sorted(required_checks - set(check_statuses))
    if mode != "standard":
        blockers.append("release_gate_mode_not_standard")
    if status != "passed":
        blockers.append("release_gate_not_passed")
    if promotion_signal != "eligible":
        blockers.append("release_gate_not_eligible")
    if missing_checks:
        blockers.append("required_standard_checks_missing:" + ",".join(missing_checks))
    failed_checks = sorted(check_id for check_id, check_status in check_statuses.items() if check_status != "passed")
    if failed_checks:
        blockers.append("standard_checks_failed:" + ",".join(failed_checks))
    if artifact_review_status != "ready":
        blockers.append("release_artifact_review_not_ready")
    ready = not blockers
    return {
        "release_boundary_ready": ready,
        "policy_promotion_allowed": False,
        "decision_status": "standard_gate_passed" if ready else "standard_gate_blocked",
        "blockers": blockers,
        "rationale": (
            "Standard release-candidate gate passed with sample and selected shard evidence; proceed to release-boundary finalization review without automatic pointer promotion."
            if ready
            else "Standard release-candidate gate needs the listed blockers closed before release-boundary finalization."
        ),
    }


def _next_selection(decision: dict[str, Any]) -> dict[str, Any]:
    if decision["release_boundary_ready"]:
        return {
            "task_id": "R12",
            "title": "Release Boundary Finalization Review",
            "selected_track": "release_boundary",
            "scope": [
                "review R1-R11 evidence bundle",
                "decide whether to run full pytest before external release",
                "keep policy pointer promotion explicit and human-approved",
            ],
        }
    return {
        "task_id": "R12",
        "title": "Standard Gate Evidence Gap Closure",
        "selected_track": "release_readiness",
        "scope": [
            "close standard gate blockers",
            "rerun standard release-candidate gate",
            "do not promote policy pointers while blocked",
        ],
    }
