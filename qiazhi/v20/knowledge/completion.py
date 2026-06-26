from __future__ import annotations

from v20.knowledge.catalog import build_knowledge_catalog
from v20.knowledge.coverage import build_knowledge_coverage_report
from v20.knowledge.directory import build_knowledge_directory_manifest
from v20.knowledge.directory_seeds import build_full_directory_seed_library
from v20.knowledge.draft_import import build_knowledge_draft_import_preview
from v20.knowledge.feature_model import build_bazi_feature_graph_model_contract
from v20.knowledge.macro_dimensions import build_macro_dimension_catalog
from v20.knowledge.release import build_knowledge_release_manifest
from v20.knowledge.review_queue import build_knowledge_review_queue
from v20.knowledge.rule_library import build_knowledge_rule_library, validate_knowledge_rule_library
from v20.knowledge.source_catalog import build_knowledge_source_catalog
from v20.validation.knowledge_rule_library import build_knowledge_rule_validation_report


def build_knowledge_completion_report() -> dict[str, object]:
    catalog = build_knowledge_catalog()
    directory = build_knowledge_directory_manifest()
    directory_seeds = build_full_directory_seed_library()
    source_catalog = build_knowledge_source_catalog()
    coverage = build_knowledge_coverage_report()
    release = build_knowledge_release_manifest()
    rule_library = build_knowledge_rule_library()
    rule_contract = validate_knowledge_rule_library()
    rule_validation = build_knowledge_rule_validation_report()
    macro_dimensions = build_macro_dimension_catalog()
    feature_model = build_bazi_feature_graph_model_contract()
    draft_preview = build_knowledge_draft_import_preview(limit=1)
    review_queue = build_knowledge_review_queue(limit_per_domain=1)
    blockers = _mainline_blockers(
        catalog=catalog,
        directory=directory,
        directory_seeds=directory_seeds,
        source_catalog=source_catalog,
        coverage=coverage,
        release=release,
        rule_library=rule_library,
        rule_contract=rule_contract,
        rule_validation=rule_validation,
        macro_dimensions=macro_dimensions,
        feature_model=feature_model,
    )
    mainline_complete = not blockers
    unit_count = int(catalog.get("unit_count", 0) or 0)
    reviewed_unit_count = int(catalog.get("reviewed_unit_count", 0) or 0)
    definition_count = int(rule_library.get("definition_count", 0) or 0)
    synthetic_covered_count = int(rule_validation.get("synthetic_covered_count", 0) or 0)
    return {
        "version": "v20.knowledge_completion_report.v1",
        "status": "complete_for_v20_mainline" if mainline_complete else "needs_work",
        "mainline_complete": mainline_complete,
        "completion_scope": "reviewed_seed_knowledge_rule_library_for_v20_mainline",
        "depth_scope": "full_classical_canon_and_v19_draft_import_remain_expansion_backlog",
        "completion_percent": 100 if mainline_complete else 0,
        "unit_count": unit_count,
        "reviewed_unit_count": reviewed_unit_count,
        "directory_status": directory.get("status", ""),
        "directory_node_count": directory.get("node_count", 0),
        "directory_p0_node_count": directory.get("p0_node_count", 0),
        "directory_mainline_fill_order": directory.get("mainline_fill_order", ()),
        "full_directory_seed_status": directory_seeds.get("status", ""),
        "full_directory_content_status": directory_seeds.get("full_content_status", ""),
        "full_directory_content_doc": directory_seeds.get("full_content_doc", ""),
        "full_directory_seed_count": directory_seeds.get("seed_count", 0),
        "full_directory_seed_node_count": directory_seeds.get("directory_node_count", 0),
        "full_directory_seed_runtime_allowed_count": directory_seeds.get("runtime_allowed_count", 0),
        "domain_count": catalog.get("domain_count", 0),
        "source_count": source_catalog.get("source_count", 0),
        "coverage_gap_count": coverage.get("gap_count", 0),
        "definition_count": definition_count,
        "rule_definition_count": definition_count,
        "rule_atom_count": rule_library.get("atom_count", 0),
        "portrait_output_count": rule_library.get("portrait_output_count", 0),
        "question_output_count": rule_library.get("question_output_count", 0),
        "synthetic_covered_count": synthetic_covered_count,
        "missing_synthetic_count": rule_validation.get("missing_synthetic_count", 0),
        "runtime_allowed_count": rule_validation.get("runtime_allowed_count", 0),
        "mainline_blockers": blockers,
        "ready_artifacts": {
            "catalog": catalog.get("status", ""),
            "directory": directory.get("status", ""),
            "full_directory_seed_library": directory_seeds.get("status", ""),
            "source_catalog": source_catalog.get("status", ""),
            "coverage": coverage.get("status", ""),
            "release": release.get("status", ""),
            "rule_library": rule_library.get("status", ""),
            "rule_contract": rule_contract.get("status", ""),
            "rule_validation": rule_validation.get("status", ""),
            "feature_graph_model": feature_model.get("status", ""),
        },
        "rule_validation_state_counts": rule_validation.get("state_counts", {}),
        "macro_dimension_status": macro_dimensions.get("status", ""),
        "macro_dimension_count": macro_dimensions.get("dimension_count", 0),
        "macro_dimensions": macro_dimensions.get("current_primary_dimensions", ()),
        "feature_graph_model_status": feature_model.get("status", ""),
        "feature_graph_phase1_object_count": len(feature_model.get("phase1_objects", ())),
        "feature_graph_topic_projection_count": feature_model.get("topic_projection_count", 0),
        "feature_graph_decision_states": feature_model.get("decision_state_keys", ()),
        "feature_graph_chain": feature_model.get("mainline_chain", ()),
        "knowledge_axes": _knowledge_axes(catalog),
        "recommended_status_surface": "/api/v20/admin/mainline-status",
        "next_mainline_step": "rule_subcondition_iteration_and_replay_eval" if mainline_complete else "clear_knowledge_blockers",
        "expansion_backlog": {
            "status": "not_blocking_mainline",
            "draft_candidate_count": draft_preview.get("candidate_count", 0),
            "review_queue_candidate_count": review_queue.get("candidate_count", 0),
            "first_wave_approval_is_separate_gate": True,
        },
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_COMPLETION_REPORT_IS_READ_ONLY",
            "MAINLINE_COMPLETE_DOES_NOT_MEAN_FULL_BAZI_CANON_COMPLETE",
            "DRAFT_IMPORT_BACKLOG_DOES_NOT_BLOCK_REVIEWED_SEED_MAINLINE",
            "RUNTIME_RULE_ACTIVATION_ALLOWED_WITH_TRACE",
        ],
    }


def _knowledge_axes(catalog: dict[str, object]) -> dict[str, object]:
    tags = set(str(tag) for tag in catalog.get("retrieval_tags", ()) if str(tag))
    return {
        "macro_present": bool({"macro", "qishi", "climate", "palace", "time_stack"} & tags),
        "micro_present": bool({"micro", "zuogong", "tomb_storage", "sheng_ke_zhi_hua"} & tags),
        "blind_school_present": "blind_school" in tags,
        "zuogong_present": "zuogong" in tags,
        "application_present": "application" in tags,
        "macro_tags": sorted(tags & {"macro", "qishi", "climate", "palace", "time_stack", "tiaohou"}),
        "micro_tags": sorted(tags & {"micro", "zuogong", "tomb_storage", "sheng_ke_zhi_hua", "branch_mechanism"}),
        "application_tags": sorted(tags & {"application", "study", "family", "social", "mobility", "asset", "cashflow"}),
    }


def _mainline_blockers(
    *,
    catalog: dict[str, object],
    directory: dict[str, object],
    directory_seeds: dict[str, object],
    source_catalog: dict[str, object],
    coverage: dict[str, object],
    release: dict[str, object],
    rule_library: dict[str, object],
    rule_contract: dict[str, object],
    rule_validation: dict[str, object],
    macro_dimensions: dict[str, object],
    feature_model: dict[str, object],
) -> tuple[str, ...]:
    blockers = []
    if catalog.get("status") != "ready":
        blockers.append("knowledge_catalog_not_ready")
    if directory.get("status") != "directory_ready_full_seed_library_ready":
        blockers.append("knowledge_directory_not_ready")
    if int(directory.get("p0_node_count", 0) or 0) < 9:
        blockers.append("knowledge_directory_p0_incomplete")
    if directory_seeds.get("status") != "full_directory_seeded_for_review":
        blockers.append("full_directory_seed_library_not_ready")
    if int(directory_seeds.get("directory_node_count", 0) or 0) < 13:
        blockers.append("full_directory_seed_node_coverage_incomplete")
    if int(directory_seeds.get("runtime_allowed_count", 0) or 0) != 0:
        blockers.append("directory_seed_runtime_activation_leaked")
    if int(catalog.get("unit_count", 0) or 0) != int(catalog.get("reviewed_unit_count", 0) or 0):
        blockers.append("unreviewed_seed_units")
    if source_catalog.get("status") != "ready":
        blockers.append("source_catalog_not_ready")
    if coverage.get("status") != "pass" or int(coverage.get("gap_count", 0) or 0) != 0:
        blockers.append("knowledge_coverage_has_gaps")
    if release.get("status") != "ready_for_release_review":
        blockers.append("release_manifest_not_ready")
    if rule_library.get("status") != "ready":
        blockers.append("rule_library_not_ready")
    if rule_contract.get("status") != "pass" or rule_contract.get("ok") is not True:
        blockers.append("rule_contract_validation_failed")
    if rule_validation.get("status") != "active_ready" or rule_validation.get("ok") is not True:
        blockers.append("rule_validation_not_ready")
    if int(rule_validation.get("missing_synthetic_count", 0) or 0) != 0:
        blockers.append("missing_synthetic_rule_coverage")
    if int(rule_validation.get("missing_synthetic_count", 0) or 0) != 0:
        blockers.append("synthetic_coverage_incomplete")
    if int(rule_validation.get("runtime_allowed_count", 0) or 0) != int(rule_validation.get("definition_count", 0) or 0):
        blockers.append("runtime_activation_not_complete")
    if feature_model.get("status") != "phase1_contract_ready":
        blockers.append("feature_graph_model_not_ready")
    if "TopicProjection" not in set(feature_model.get("phase1_objects", ())):
        blockers.append("topic_projection_contract_missing")
    if any(
        isinstance(row, dict) and row.get("content_status") != "ready"
        for row in macro_dimensions.get("dimensions", ())
    ):
        blockers.append("macro_dimension_topic_units_not_complete")
    return tuple(blockers)
