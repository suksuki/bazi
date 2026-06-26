from __future__ import annotations

from typing import Any


RELEASE_ARTIFACT_REVIEW_VERSION = "v30.release_artifact_review.v1"


def build_release_artifact_review(
    checks: list[Any],
    *,
    policy_lineages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    check_map = {
        str(getattr(check, "check_id", "")): check
        for check in checks
        if getattr(check, "check_id", "")
    }
    check_statuses = {
        check_id: str(getattr(check, "status", ""))
        for check_id, check in check_map.items()
    }
    runtime_summary = _summary(check_map.get("runtime_smoke"))
    llm_summary = _summary(check_map.get("llm_live_smoke"))
    post_seal_summary = _summary(check_map.get("post_seal_contracts"))
    synthetic_summary = _summary(check_map.get("synthetic_all"))
    sample_summary = _summary(check_map.get("518k_sample"))
    shard_summary = _summary(check_map.get("518k_shard"))
    policy_lineage_summary = _policy_lineage_summary(runtime_summary, policy_lineages or [])
    artifact_index = _artifact_index(
        llm_summary=llm_summary,
        sample_summary=sample_summary,
        shard_summary=shard_summary,
    )
    projection_contract_summary = _projection_contract_summary(post_seal_summary, synthetic_summary)
    review_sections = [
        "release_gate_checks",
        "llm_live_smoke_artifact",
        "synthetic_suite_summary",
        "518k_artifacts",
        "policy_lineage",
        "projection_contracts",
    ]
    missing_sections = [
        section for section, present in {
            "llm_live_smoke_artifact": bool(llm_summary.get("artifact_uri")),
            "synthetic_suite_summary": bool(synthetic_summary.get("suite_id")),
            "518k_artifacts": bool(sample_summary.get("artifact_record_id")),
            "policy_lineage": bool(policy_lineage_summary.get("active_policy_versions")),
            "projection_contracts": bool(projection_contract_summary.get("projection_contract_version")),
        }.items()
        if not present
    ]
    return {
        "version": RELEASE_ARTIFACT_REVIEW_VERSION,
        "status": "ready" if not missing_sections else "partial",
        "check_count": len(check_map),
        "check_statuses": check_statuses,
        "admin_review_sections": review_sections,
        "missing_sections": missing_sections,
        "artifact_index": artifact_index,
        "synthetic_suite_summary": {
            "suite_id": synthetic_summary.get("suite_id", ""),
            "case_count": synthetic_summary.get("case_count", 0),
            "passed_count": synthetic_summary.get("passed_count", 0),
            "failed_count": synthetic_summary.get("failed_count", 0),
            "tier_coverage": synthetic_summary.get("tier_coverage", {}),
        },
        "corpus_518k_summary": _corpus_summary(sample_summary, shard_summary),
        "policy_lineage_summary": policy_lineage_summary,
        "projection_contract_summary": projection_contract_summary,
        "promotion_review": {
            "eligible_checks": sum(1 for status in check_statuses.values() if status == "passed"),
            "failed_checks": sorted(check_id for check_id, status in check_statuses.items() if status != "passed"),
            "policy_promotion_allowed": False,
            "promotion_boundary": "r6_artifact_review_is_observability_only_not_policy_promotion",
        },
        "boundary": "release_artifact_review_groups_admin_diagnostics_without_mutating_policy_or_chart_facts",
    }


def _summary(check: Any | None) -> dict[str, Any]:
    if check is None:
        return {}
    summary = getattr(check, "summary", {})
    return summary if isinstance(summary, dict) else {}


def _artifact_index(
    *,
    llm_summary: dict[str, Any],
    sample_summary: dict[str, Any],
    shard_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    if llm_summary.get("artifact_uri"):
        rows.append(
            {
                "family": "llm_live_smoke",
                "run_id": str(llm_summary.get("run_id") or ""),
                "artifact_uri": str(llm_summary.get("artifact_uri") or ""),
                "status": str(llm_summary.get("smoke_status") or ""),
                "search_backend": "runtime_file",
            }
        )
    for family, summary in (("518k_sample", sample_summary), ("518k_shard", shard_summary)):
        if summary.get("artifact_record_id") or summary.get("artifact_uri"):
            rows.append(
                {
                    "family": family,
                    "run_id": str(summary.get("run_id") or ""),
                    "artifact_record_id": str(summary.get("artifact_record_id") or ""),
                    "artifact_uri": str(summary.get("artifact_uri") or ""),
                    "index_uri": str(summary.get("index_uri") or ""),
                    "index_entry_uri": str(summary.get("index_entry_uri") or ""),
                    "promotion_signal": str(summary.get("promotion_signal") or ""),
                    "search_backend": str(summary.get("artifact_search_backend") or ""),
                    "searchable": bool(summary.get("artifact_searchable")),
                }
            )
    return rows


def _corpus_summary(sample_summary: dict[str, Any], shard_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "sample": _corpus_row(sample_summary),
        "shard": _corpus_row(shard_summary),
        "artifact_record_ids": [
            str(row.get("artifact_record_id") or "")
            for row in (sample_summary, shard_summary)
            if row.get("artifact_record_id")
        ],
        "boundary": "corpus_artifacts_are_release_evidence_not_training_promotion",
    }


def _corpus_row(summary: dict[str, Any]) -> dict[str, Any]:
    if not summary:
        return {}
    return {
        "run_id": str(summary.get("run_id") or ""),
        "case_count": int(summary.get("case_count", 0) or 0),
        "promotion_signal": str(summary.get("promotion_signal") or ""),
        "artifact_record_id": str(summary.get("artifact_record_id") or ""),
        "artifact_uri": str(summary.get("artifact_uri") or ""),
        "index_uri": str(summary.get("index_uri") or ""),
        "coverage_metric_keys": sorted((summary.get("coverage_metrics", {}) or {}).keys())
        if isinstance(summary.get("coverage_metrics"), dict) else [],
        "drift_metric_keys": sorted((summary.get("drift_metrics", {}) or {}).keys())
        if isinstance(summary.get("drift_metrics"), dict) else [],
    }


def _policy_lineage_summary(
    runtime_summary: dict[str, Any],
    policy_lineages: list[dict[str, Any]],
) -> dict[str, Any]:
    active = runtime_summary.get("active_policy_versions", {})
    active = active if isinstance(active, dict) else {}
    lineages = [
        {
            "family": str(row.get("family") or ""),
            "lineage_id": str(row.get("lineage_id") or ""),
            "active_artifact_id": str(row.get("active_artifact_id") or ""),
            "previous_artifact_id": str(row.get("previous_artifact_id") or ""),
            "validation_artifact_count": len(row.get("validation_artifacts", []))
            if isinstance(row.get("validation_artifacts"), list) else 0,
            "boundary_count": len(row.get("boundaries", []))
            if isinstance(row.get("boundaries"), list) else 0,
        }
        for row in policy_lineages
        if isinstance(row, dict)
    ]
    return {
        "active_policy_versions": active,
        "families": sorted(active),
        "lineage_count": len(lineages),
        "lineages": lineages,
        "boundary": "policy_lineage_summary_is_read_only_release_diagnostic",
    }


def _projection_contract_summary(
    post_seal_summary: dict[str, Any],
    synthetic_summary: dict[str, Any],
) -> dict[str, Any]:
    tier_coverage = synthetic_summary.get("tier_coverage", {})
    tier_coverage = tier_coverage if isinstance(tier_coverage, dict) else {}
    return {
        "projection_contract_version": str(post_seal_summary.get("projection_contract_version") or ""),
        "user_leak_scan_passed": bool(post_seal_summary.get("user_leak_scan_passed")),
        "admin_diagnostics_visible": bool(post_seal_summary.get("admin_diagnostics_visible")),
        "phase_seal_passed_count": int(post_seal_summary.get("phase_seal_passed_count", 0) or 0),
        "api_projection_contract_count": int(tier_coverage.get("api_projection_contract_count", 0) or 0),
        "api_projection_leak_pass_count": int(tier_coverage.get("api_projection_leak_pass_count", 0) or 0),
        "production_replay_metadata_count": int(tier_coverage.get("production_replay_metadata_count", 0) or 0),
        "boundary": "projection_contract_summary_reviews_visibility_without_rewriting_projection",
    }
