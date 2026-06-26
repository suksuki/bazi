from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.knowledge.source_registry import SOURCE_FAMILIES
from v30.storage.m3 import write_m3_source_backlog_to_postgres
from v30.validation.m3_core_spine_snapshot import run_m3_core_spine_snapshot


M3_SOURCE_EXTRACTION_BACKLOG_VERSION = "v30.m3_source_extraction_backlog.v1"


def run_m3_source_extraction_backlog(
    *,
    artifact_dir: str | Path | None = None,
    write_db: bool = False,
) -> dict[str, Any]:
    snapshot = run_m3_core_spine_snapshot(
        include_518k_sample=False,
        write_db=False,
    )
    return build_m3_source_extraction_backlog(
        m3_snapshot=snapshot,
        artifact_dir=artifact_dir,
        write_db=write_db,
    )


def build_m3_source_extraction_backlog(
    *,
    m3_snapshot: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
    write_db: bool = False,
) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc)
    backlog_id = f"v30.m3.g4.{created_at.strftime('%Y%m%d%H%M%S%f')}"
    calibration = _mapping(m3_snapshot.get("source_governed_calibration"))
    tag_groups = _mapping(calibration.get("tag_groups"))
    source_queue_tags = _list_of_mappings(tag_groups.get("source_extraction_queue"))
    knowledge_units = _list_of_mappings(m3_snapshot.get("knowledge_units"))
    rule_specs = _list_of_mappings(m3_snapshot.get("rule_specs"))
    portrait_assets = _list_of_mappings(m3_snapshot.get("portrait_assets"))
    rows = _backlog_rows(
        backlog_id=backlog_id,
        source_queue_tags=source_queue_tags,
        knowledge_units=knowledge_units,
        rule_specs=rule_specs,
        portrait_assets=portrait_assets,
    )
    checks = _checks(rows=rows, calibration=calibration)
    decision = _decision(rows=rows, checks=checks)
    payload: dict[str, Any] = {
        "version": M3_SOURCE_EXTRACTION_BACKLOG_VERSION,
        "backlog_id": backlog_id,
        "created_at": created_at.isoformat(),
        "status": "completed" if decision["ready_for_source_backlog_review"] else "blocked",
        "decision": decision,
        "source_summary": {
            "m3_snapshot_id": str(m3_snapshot.get("snapshot_id") or ""),
            "m3_calibration_version": str(calibration.get("version") or ""),
            "source_family_count": len(SOURCE_FAMILIES),
            "source_queue_tag_count": len(source_queue_tags),
            "knowledge_unit_count": len(knowledge_units),
            "rule_spec_count": len(rule_specs),
            "portrait_asset_count": len(portrait_assets),
        },
        "backlog_summary": {
            "backlog_row_count": len(rows),
            "priority_counts": dict(Counter(str(row.get("priority")) for row in rows)),
            "queue_state_counts": dict(Counter(str(row.get("queue_state")) for row in rows)),
            "review_status_counts": dict(Counter(str(row.get("review_status")) for row in rows)),
            "target_domains": sorted({
                domain
                for row in rows
                for domain in _string_list(row.get("target_domains"))
            }),
        },
        "backlog_rows": rows,
        "checks": checks,
        "policy_boundary": {
            "review_only": True,
            "runtime_v20_import_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "source_url_runtime_fetch_required": False,
            "boundary": "m3_g4_source_backlog_operationalizes_source_queue_without_runtime_import_or_policy_promotion",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m3_g4_source_extraction_backlog_is_reviewable_support_data_not_chart_fact_or_policy_layer",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    if write_db:
        payload["db_write"] = write_m3_source_backlog_to_postgres(payload).model_dump(mode="json")
    return payload


def _backlog_rows(
    *,
    backlog_id: str,
    source_queue_tags: list[Mapping[str, Any]],
    knowledge_units: list[Mapping[str, Any]],
    rule_specs: list[Mapping[str, Any]],
    portrait_assets: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    tag_by_source = {
        str(tag.get("source_family_id")): tag
        for tag in source_queue_tags
        if tag.get("source_family_id")
    }
    rows: list[dict[str, Any]] = []
    for order, source in enumerate(SOURCE_FAMILIES, start=1):
        tag = tag_by_source.get(source.source_family_id, {})
        linked_units = _linked_knowledge_units(source.source_family_id, knowledge_units)
        linked_rules = _linked_rules(source.domains, source.rule_families, rule_specs)
        linked_portraits = _linked_portraits(source.domains, portrait_assets)
        target_domains = sorted(set(_string_list(tag.get("target_domains")) or source.domains))
        queue_state = str(tag.get("queue_state") or "needs_initial_mapping")
        priority = _priority(queue_state=queue_state, linked_unit_count=len(linked_units), linked_rule_count=len(linked_rules))
        extraction_stage = _extraction_stage(queue_state, linked_units, linked_rules)
        rows.append(
            {
                "backlog_item_id": f"{backlog_id}.{order:02d}.{source.source_family_id}",
                "source_family_id": source.source_family_id,
                "title": source.title,
                "source_tier": source.source_tier,
                "queue_state": queue_state,
                "priority": priority,
                "review_status": "review_ready",
                "extraction_stage": extraction_stage,
                "target_domains": target_domains,
                "rule_families": source.rule_families,
                "extraction_targets": source.extraction_targets,
                "validation_requirements": source.validation_requirements,
                "source_urls": source.urls,
                "linked_knowledge_unit_ids": [str(row.get("unit_id")) for row in linked_units if row.get("unit_id")],
                "linked_rule_ids": [str(row.get("rule_id")) for row in linked_rules if row.get("rule_id")],
                "linked_portrait_asset_ids": [str(row.get("asset_id")) for row in linked_portraits if row.get("asset_id")],
                "evidence_link_counts": {
                    "knowledge_units": len(linked_units),
                    "rule_specs": len(linked_rules),
                    "portrait_assets": len(linked_portraits),
                },
                "recommended_operator_action": _recommended_action(priority, extraction_stage),
                "runtime_boundary": source.runtime_boundary,
                "runtime_v20_import_allowed": False,
                "chart_fact_mutation_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "fixed_bazi_verdict_allowed": False,
                "boundary": "source_backlog_item_guides_source_governed_extraction_not_runtime_verdicts",
            }
        )
    return rows


def _linked_knowledge_units(source_family_id: str, knowledge_units: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [
        unit
        for unit in knowledge_units
        if source_family_id in _string_list(unit.get("source_family_ids"))
    ]


def _linked_rules(
    domains: list[str],
    rule_families: list[str],
    rule_specs: list[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    domain_set = set(domains)
    family_terms = {term for family in rule_families for term in family.split("_") if term}
    rows: list[Mapping[str, Any]] = []
    for rule in rule_specs:
        rule_id = str(rule.get("rule_id") or "")
        domain = str(rule.get("domain") or "")
        if domain in domain_set or any(term in rule_id for term in family_terms):
            rows.append(rule)
    return rows


def _linked_portraits(domains: list[str], portrait_assets: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    domain_set = set(domains)
    return [asset for asset in portrait_assets if str(asset.get("domain") or "") in domain_set]


def _priority(*, queue_state: str, linked_unit_count: int, linked_rule_count: int) -> str:
    if queue_state == "needs_initial_mapping":
        return "P0"
    if linked_unit_count < 4 or linked_rule_count < 2:
        return "P1"
    return "P2"


def _extraction_stage(
    queue_state: str,
    linked_units: list[Mapping[str, Any]],
    linked_rules: list[Mapping[str, Any]],
) -> str:
    if queue_state == "needs_initial_mapping":
        return "initial_mapping"
    if len(linked_units) < 4:
        return "krp_depth_review"
    if len(linked_rules) < 2:
        return "rule_depth_review"
    return "calibrated_monitoring"


def _recommended_action(priority: str, extraction_stage: str) -> str:
    if priority == "P0":
        return "create_initial_v30_krp_and_rule_mapping"
    if extraction_stage == "krp_depth_review":
        return "add_source_governed_krp_depth_units"
    if extraction_stage == "rule_depth_review":
        return "add_or_link_defeasible_rule_specs"
    return "monitor_with_real_case_and_synthetic_replay"


def _checks(*, rows: list[Mapping[str, Any]], calibration: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "source_governed_calibration_ready",
            "passed": calibration.get("version") == "v30.m3_source_governed_calibration.v1" and calibration.get("status") == "ready",
            "expected": "G1/G2 source-governed calibration is ready",
        },
        {
            "check_id": "all_source_families_have_backlog_rows",
            "passed": len(rows) == len(SOURCE_FAMILIES) and len({row.get("source_family_id") for row in rows}) == len(SOURCE_FAMILIES),
            "expected": "each registered source family has one backlog row",
        },
        {
            "check_id": "backlog_rows_are_reviewable",
            "passed": all(row.get("review_status") == "review_ready" and row.get("priority") in {"P0", "P1", "P2"} for row in rows),
            "expected": "every backlog row has review status and priority",
        },
        {
            "check_id": "evidence_links_present",
            "passed": all(_mapping(row.get("evidence_link_counts")).get("knowledge_units", 0) >= 1 for row in rows),
            "expected": "every source family is linked to at least one V30 K/R/P unit",
        },
        {
            "check_id": "operational_fields_present",
            "passed": all(
                _string_list(row.get("target_domains"))
                and _string_list(row.get("extraction_targets"))
                and _string_list(row.get("validation_requirements"))
                for row in rows
            ),
            "expected": "target domains, extraction targets, and validation requirements are present",
        },
        {
            "check_id": "no_runtime_import_or_mutation_allowed",
            "passed": all(
                not bool(row.get("runtime_v20_import_allowed"))
                and not bool(row.get("chart_fact_mutation_allowed"))
                and not bool(row.get("policy_pointer_promotion_allowed"))
                and not bool(row.get("fixed_bazi_verdict_allowed"))
                for row in rows
            ),
            "expected": "source backlog cannot import V20 runtime, mutate chart facts, promote pointers, or create fixed verdicts",
        },
    ]


def _decision(*, rows: list[Mapping[str, Any]], checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for row in checks if row.get("passed"))
    ready = passed == len(checks)
    return {
        "decision_status": "m3_g4_source_extraction_backlog_ready" if ready else "m3_g4_source_extraction_backlog_blocked",
        "ready_for_source_backlog_review": ready,
        "ready_for_pointer_promotion": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "runtime_v20_import_allowed": False,
        "backlog_row_count": len(rows),
        "passed_checks": passed,
        "total_checks": len(checks),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("ready_for_source_backlog_review"):
        return {
            "next_task": "M3-G5 Backlog Persistence And Admin Review Surface",
            "reason": "G4 backlog artifacts are ready; next connect storage/query surface without changing M3 runtime decisions.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M3-G4 Remediation",
        "reason": "G4 source backlog checks are blocked; fix source mappings before continuing M3.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if str(row)]


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['backlog_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
