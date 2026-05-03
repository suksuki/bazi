from __future__ import annotations

from collections import Counter
from typing import Any

from v20.features.schema import FeatureLayer
from v20.rules.catalog import build_bazi_rule_catalog


RULE_RUNTIME_VERSION = "v20.rule_runtime_report.v1"

CONDITION_ALIASES: dict[str, tuple[str, ...]] = {
    "answer_text": ("answer_boundary", "governance", "no_fortune"),
    "authority": ("authority", "正官", "七杀", "career"),
    "authority_star": ("authority", "正官", "七杀"),
    "auxiliary_symbol": ("archive", "shensha", "auxiliary"),
    "BaziFeature": ("feature.", "feature_binding"),
    "branch_pair": ("branch_relation", "clash", "harmony", "harm", "break", "punishment"),
    "branch_relation": ("branch_relation", "clash", "harmony", "harm", "break", "punishment"),
    "calendar_assumption": ("calendar", "calendar_assumption"),
    "calendar_metadata": ("calendar", "calendar_assumption"),
    "capacity": ("capacity_state", "strength"),
    "capacity_state": ("capacity_state", "strength"),
    "channel": ("output_to_wealth", "output_channel", "wealth_material"),
    "clear_mixed": ("pattern", "mixed", "authority"),
    "climate_bias": ("element_distribution", "climate", "season"),
    "combination_pair": ("combination", "branch_relation"),
    "core_arbitration_attempt": ("governance", "llm_no_arbitration"),
    "counterevidence": ("counter", "boundary", "governance"),
    "day_branch": ("day_branch", "palace", "branch_relation"),
    "day_master": ("day_master",),
    "direction": ("branch_relation", "flow", "time_relation"),
    "dominant_qi": ("pattern", "month_command"),
    "dry_wet_context": ("element_distribution", "climate"),
    "element_distribution": ("element_distribution", "element"),
    "element_pressure": ("element_distribution", "support_pressure", "capacity_state"),
    "EvidencePack": ("evidence_pack_required", "governance", "evidence"),
    "explicit_time_layer": ("time_layer", "luck", "flow"),
    "fire_water_balance": ("element_distribution", "fire", "water"),
    "flow_obstruction": ("branch_relation", "element_distribution", "time_relation"),
    "flow_trigger": ("time_relation", "time_layer"),
    "food_star": ("食神", "food"),
    "generation": ("element_distribution", "generation", "flow"),
    "health": ("health", "non_medical_boundary"),
    "hidden_content": ("hidden", "vault", "storage"),
    "hidden_stem": ("hidden", "vault"),
    "host_guest": ("blind_lifa", "palace"),
    "llm_output": ("llm", "governance"),
    "luck_context": ("luck", "time_layer"),
    "luck_or_flow_clash": ("luck", "flow", "clash", "time_relation"),
    "mainline_evidence": ("evidence", "feature_binding"),
    "mediating_element": ("element_distribution", "mediation"),
    "mediation": ("element_distribution", "mediation", "resource"),
    "month_command": ("month_command", "calendar", "pattern"),
    "natal_structure": ("chart_fact", "pillar", "day_master"),
    "natal_target": ("time_relation", "pillar", "branch_relation"),
    "nayin": ("archive", "nayin"),
    "non_medical_boundary": ("health", "governance", "boundary"),
    "official_star": ("正官", "authority"),
    "opening_trigger": ("vault", "storage", "time_relation"),
    "output": ("食神", "伤官", "output"),
    "output_conflict": ("伤官", "authority", "output_authority"),
    "output_star": ("食神", "伤官", "output"),
    "output_wealth_authority_pressure": ("wealth", "authority", "output", "pressure"),
    "palace_position": ("palace", "pillar", "branch_relation"),
    "palace_role": ("palace", "pillar"),
    "partial_resource": ("偏印", "resource"),
    "path_continuity": ("blind_lifa", "branch_relation", "feature_binding"),
    "peer_star": ("比肩", "劫财", "peer"),
    "pillar_display": ("pillar", "chart_fact"),
    "pillar_position": ("pillar", "palace"),
    "pressure_path": ("support_pressure", "capacity_state", "pressure"),
    "pressure_score": ("pressure_score", "support_pressure"),
    "relation_type": ("branch_relation", "clash", "harmony", "harm", "break", "punishment"),
    "resource": ("正印", "偏印", "resource"),
    "resource_buffer": ("resource", "正印", "偏印"),
    "resource_mediation": ("resource", "mediation"),
    "resource_peer_support": ("resource", "peer", "support"),
    "resource_star": ("正印", "偏印", "resource"),
    "review_status": ("archive", "requires_review"),
    "revealed_god": ("visible", "ten_god"),
    "root_presence": ("root", "support_pressure", "capacity_state"),
    "season": ("calendar", "month_command"),
    "season_support": ("month_command", "element_distribution"),
    "source_layer": ("visible", "hidden", "ten_god"),
    "source_school": ("archive", "school"),
    "spouse_palace": ("spouse", "palace", "day_branch"),
    "spouse_star": ("spouse", "romance", "ten_god"),
    "storage_branch": ("vault", "storage"),
    "strength_state": ("capacity_state", "strength"),
    "support_or_suppression_need": ("support_pressure", "useful_god"),
    "support_score": ("support_score", "support_pressure"),
    "supporting_structure": ("pattern", "resource", "support"),
    "ten_god_relation": ("ten_god", "visible", "hidden"),
    "ten_god_structure": ("ten_god", "pattern"),
    "time_relation": ("time_relation", "luck", "flow"),
    "time_source": ("time", "calendar"),
    "time_trigger": ("time_relation", "time_layer"),
    "transform_element": ("element_distribution", "combination"),
    "value": ("element_distribution", "ten_god"),
    "variant_text": ("archive", "variant"),
    "verdict_pattern": ("no_fortune", "governance", "answer_boundary"),
    "visible_hidden": ("visible", "hidden", "ten_god"),
    "visible_hidden_weight": ("visible", "hidden", "element_distribution", "weight"),
    "wealth_counter": ("wealth", "counter"),
    "wealth_material": ("wealth_material", "正财", "偏财", "wealth"),
    "wealth_source": ("wealth_material", "wealth"),
    "wealth_star": ("正财", "偏财", "wealth"),
}


def build_rule_runtime_report(feature_layer: FeatureLayer, *, catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    catalog_payload = catalog or build_bazi_rule_catalog()
    trace = feature_layer.discovery_trace if isinstance(feature_layer.discovery_trace, dict) else {}
    evidence_atoms = tuple(row for row in trace.get("evidence_atoms", ()) if isinstance(row, dict))
    evidence_index = _evidence_index(evidence_atoms, feature_layer)
    rules = tuple(_execute_rule(row, evidence_index) for row in catalog_payload.get("rules", ()))
    status_counts = Counter(str(row["match_status"]) for row in rules)
    node_counts = Counter(str(row["directory_node"]) for row in rules)
    matched_nodes = Counter(str(row["directory_node"]) for row in rules if row["match_status"] in {"matched", "partial"})
    covered_nodes = tuple(sorted(node_counts, key=lambda row: int(row[1:])))
    return {
        "version": RULE_RUNTIME_VERSION,
        "status": "rulespec_engine_ready",
        "source": "bazi_rule_spec_catalog",
        "engine": "rulespec_evidence_atom_engine_phase1",
        "engine_policy": "active_rulespec_engine_continuous_iteration",
        "rule_count": len(rules),
        "executed_rule_count": len(rules),
        "matched_rule_count": status_counts.get("matched", 0),
        "partial_rule_count": status_counts.get("partial", 0),
        "review_required_rule_count": status_counts.get("review_required", 0),
        "blocked_rule_count": status_counts.get("blocked", 0),
        "archive_rule_count": status_counts.get("archive_only", 0),
        "not_matched_rule_count": status_counts.get("not_matched", 0),
        "runtime_allowed_count": sum(1 for row in rules if row["runtime_allowed"]),
        "directory_node_count": len(node_counts),
        "covered_directory_nodes": covered_nodes,
        "matched_directory_nodes": tuple(sorted(matched_nodes, key=lambda row: int(row[1:]))),
        "coverage_by_node": dict(sorted(node_counts.items(), key=lambda item: int(item[0][1:]))),
        "match_coverage_by_node": dict(sorted(matched_nodes.items(), key=lambda item: int(item[0][1:]))),
        "rules": rules,
        "catalog_guardrails": tuple(catalog_payload.get("guardrails", ())),
        "runtime_mutation": False,
        "guardrails": (
            "RULESPEC_ENGINE_IS_PRIMARY_RULE_RUNTIME",
            "LEGACY_DECISION_ENGINE_IS_COMPATIBILITY_BRIDGE",
            "RULE_RUNTIME_CONSUMES_EVIDENCE_ATOMS",
            "RULE_RUNTIME_DOES_NOT_OUTPUT_FORTUNE_VERDICT",
            "ACTIVE_RULES_ITERATE_WITH_RUNTIME_FEEDBACK",
            "BLOCKED_GOVERNANCE_RULES_REMAIN_BOUNDARY_GUARDS",
        ),
    }


def _execute_rule(rule: dict[str, Any], evidence_index: tuple[dict[str, str], ...]) -> dict[str, Any]:
    conditions = tuple(row for row in rule.get("conditions", ()) if isinstance(row, dict))
    matched_condition_ids: list[str] = []
    matched_atom_ids: list[str] = []
    condition_results: list[dict[str, Any]] = []
    for condition in conditions:
        atom_ids = _condition_atom_ids(condition, evidence_index)
        matched = bool(atom_ids)
        if matched:
            matched_condition_ids.append(str(condition.get("condition_id", "")))
            matched_atom_ids.extend(atom_ids)
        condition_results.append(
            {
                "condition_id": condition.get("condition_id", ""),
                "evidence_type": condition.get("evidence_type", ""),
                "matched": matched,
                "matched_evidence_atom_ids": tuple(atom_ids),
            }
        )
    match_status = _match_status(rule, len(matched_condition_ids), len(conditions))
    return {
        "rule_id": rule.get("rule_id", ""),
        "title": rule.get("title", ""),
        "directory_node": rule.get("directory_node", ""),
        "domain": rule.get("domain", ""),
        "layer": rule.get("layer", ""),
        "runtime_status": rule.get("runtime_status", ""),
        "decision_state": rule.get("decision_state", ""),
        "match_status": match_status,
        "match_score": round(len(matched_condition_ids) / len(conditions), 3) if conditions else 0.0,
        "condition_count": len(conditions),
        "matched_condition_count": len(matched_condition_ids),
        "matched_condition_ids": tuple(matched_condition_ids),
        "matched_evidence_atom_ids": tuple(dict.fromkeys(matched_atom_ids)),
        "condition_results": tuple(condition_results),
        "counter_evidence": tuple(rule.get("counter_evidence", ())),
        "projections": tuple(rule.get("projections", ())),
        "bridges_to_runtime_rules": tuple(rule.get("bridges_to_runtime_rules", ())),
        "runtime_allowed": bool(rule.get("runtime_allowed")),
        "core_seed_bridge_required": False,
        "structural_only": True,
        "runtime_mutation": False,
    }


def _evidence_index(evidence_atoms: tuple[dict[str, Any], ...], feature_layer: FeatureLayer) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for atom in evidence_atoms:
        haystack = " ".join(
            str(atom.get(key, ""))
            for key in ("atom_id", "domain", "evidence_type", "title", "layer", "target_feature_ids")
        ).lower()
        rows.append({"atom_id": str(atom.get("atom_id", "")), "haystack": haystack})
    for feature in feature_layer.features:
        rows.append(
            {
                "atom_id": f"feature:{feature.feature_id}",
                "haystack": " ".join(
                    str(value)
                    for value in (
                        feature.feature_id,
                        feature.domain,
                        feature.title,
                        feature.readiness,
                    )
                ).lower(),
            }
        )
    return tuple(rows)


def _condition_atom_ids(condition: dict[str, Any], evidence_index: tuple[dict[str, str], ...]) -> tuple[str, ...]:
    evidence_type = str(condition.get("evidence_type", ""))
    aliases = CONDITION_ALIASES.get(evidence_type, (evidence_type,))
    lowered_aliases = tuple(alias.lower() for alias in aliases if alias)
    return tuple(
        row["atom_id"]
        for row in evidence_index
        if any(alias in row["haystack"] for alias in lowered_aliases)
    )[:10]


def _match_status(rule: dict[str, Any], matched_count: int, condition_count: int) -> str:
    runtime_status = str(rule.get("runtime_status", ""))
    if runtime_status == "blocked":
        return "blocked"
    if runtime_status == "archive_only":
        return "archive_only"
    if condition_count and matched_count == condition_count:
        return "matched"
    if matched_count:
        return "partial"
    if runtime_status == "review_required":
        return "review_required"
    return "not_matched"
