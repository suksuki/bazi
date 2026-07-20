#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


V50_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = V50_ROOT / "data" / "validation" / "fixtures"
DOC_DIR = V50_ROOT / "docs" / "research" / "validation"
V1_PATH = FIXTURE_DIR / "synthetic_chart_taxonomy_v1.json"
V2_PATH = FIXTURE_DIR / "synthetic_chart_taxonomy_v2.json"
CONTRACT_PATH = FIXTURE_DIR / "synthetic_chart_taxonomy_v2_expected_contracts.json"
PROBE_PATH = FIXTURE_DIR / "probe_semantic_taxonomy_v1.json"
V2_DOC = DOC_DIR / "V50_SYNTHETIC_CHART_TAXONOMY_V2.md"
PROBE_DOC = DOC_DIR / "V50_PROBE_SEMANTIC_TAXONOMY.md"


NEW_ARCHETYPES = [
    ("half_triple_combination", "丁巳 乙酉 甲寅 戊辰", "combination_bridge", "mobility"),
    ("resource_peer_overload_output_blocked", "壬子 癸亥 甲寅 乙卯", "resource_support", "resource_support"),
    ("climate_regulation_dominant", "癸丑 乙丑 丁亥 壬子", "environment_path", "stability"),
    ("mediation_path", "庚申 壬子 甲寅 丙寅", "resource_support", "pressure_transformation"),
    ("month_risk_pulse", "戊午 庚申 乙亥 辛酉", "activation_path", "risk_control"),
    ("timing_insufficient", "甲辰 丙寅 戊午 庚申", "baseline_structure", "stability"),
    ("unsupported_relationship_domain", "辛酉 丁酉 乙卯 己卯", "unsupported_domain", "unsupported"),
    ("unsupported_health_domain", "壬辰 戊申 丙午 癸巳", "unsupported_domain", "unsupported"),
]


def build_c2_taxonomies() -> dict[str, Any]:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    v1 = json.loads(V1_PATH.read_text(encoding="utf-8"))
    archetypes = [_from_v1(case) for case in v1["cases"]]
    archetypes.extend(_new_archetype(*row) for row in NEW_ARCHETYPES)
    cases: list[dict[str, Any]] = []
    contracts: list[dict[str, Any]] = []
    jiazi = _jiazi()
    for archetype_index, archetype in enumerate(archetypes):
        year, month, day, _hour = archetype["chart"].split()
        for variant in range(3):
            hour = jiazi[(archetype_index * 3 + variant) % len(jiazi)]
            seed_id = f"c2.{archetype['case_type']}.{variant + 1:02d}"
            chart = f"{year} {month} {day} {hour}"
            contract = _contract(archetype, seed_id=seed_id)
            case = {
                "case_id": seed_id,
                "chart_seed_id": seed_id,
                "structure_archetype_id": f"archetype.{archetype['case_type']}",
                "case_type": archetype["case_type"],
                "chart": chart,
                "variation_axis": "hour_pillar_controlled_variant",
                "contract_status": "candidate_pending_review",
                "birth_input": {
                    "birth_input_id": f"birth.{seed_id}",
                    "name": seed_id,
                    "gender": "male" if (archetype_index + variant) % 2 == 0 else "female",
                    "calendar_type": "solar",
                    "birth_date": "1980-06-01",
                    "birth_time": "explicit",
                    "birth_location": "Shanghai",
                    "timezone": "Asia/Shanghai",
                    "year_pillar": year,
                    "month_pillar": month,
                    "day_pillar": day,
                    "hour_pillar": hour,
                    "input_quality": "explicit_pillars",
                },
                "timing_variant_id": _timing_variant(archetype["case_type"], variant),
                "domain": _domain(archetype["case_type"]),
                "expected_contract_ref": f"contract.{seed_id}",
                "expected_contract": contract["expected_contract"],
            }
            cases.append(case)
            contracts.append(contract)
    payload = {
        "version": "v50.synthetic_chart_taxonomy.v2",
        "status": "candidate_pending_review",
        "independent_seed_definition": "unique four-pillar chart plus archetype and expected contract",
        "case_count": len(cases),
        "archetype_count": len(archetypes),
        "unique_chart_count": len({case["chart"] for case in cases}),
        "training_performed": False,
        "theory_modified": False,
        "cases": cases,
    }
    V2_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    CONTRACT_PATH.write_text(json.dumps({"version": "v50.synthetic_expected_contracts.v2", "contracts": contracts}, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    probe_payload = _probe_taxonomy()
    PROBE_PATH.write_text(json.dumps(probe_payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    V2_DOC.write_text(_v2_doc(payload), encoding="utf-8")
    PROBE_DOC.write_text(_probe_doc(probe_payload), encoding="utf-8")
    return {"case_count": len(cases), "archetype_count": len(archetypes), "unique_chart_count": payload["unique_chart_count"], "probe_signature_count": len(probe_payload["signatures"])}


def _from_v1(case: dict[str, Any]) -> dict[str, Any]:
    path = str(case.get("expected_path", ["baseline_structure"])[0])
    return {
        "case_type": case["case_type"], "chart": case["chart"], "expected_top_node": case.get("expected_top_node", []),
        "expected_path": case.get("expected_path", []), "expected_structure": case.get("expected_structure", []),
        "expected_ablation": case.get("expected_ablation", []), "must_not": case.get("must_not", []),
        "theme": _theme(path),
    }


def _new_archetype(case_type: str, chart: str, path: str, theme: str) -> dict[str, Any]:
    month_branch = chart.split()[1][1]
    return {"case_type": case_type, "chart": chart, "expected_top_node": [f"{month_branch}:month_branch"], "expected_path": [path], "expected_structure": [case_type], "expected_ablation": [f"remove_{month_branch}:month_branch"], "must_not": [], "theme": theme}


def _contract(archetype: dict[str, Any], *, seed_id: str) -> dict[str, Any]:
    path = archetype["expected_path"][0] if archetype["expected_path"] else "baseline_structure"
    roles = []
    if "bridge" in path or "combination" in path:
        roles.append("bridge_node")
    if "converter" in path or "output" in path:
        roles.append("converter_node")
    if "anchor" in path or "storage" in path:
        roles.append("anchor_node")
    domain = _domain(archetype["case_type"])
    state_dimensions = ["timing_activation"]
    state_dimensions.extend(["output_drive", "pressure_handling"] if domain == "career" else ["wealth_path", "accumulation_capacity"] if domain == "wealth" else [])
    expected = {
        "expected_structure": list(archetype["expected_structure"]),
        "expected_key_nodes": list(archetype["expected_top_node"]),
        "expected_node_roles": roles,
        "expected_top_paths": list(archetype["expected_path"]),
        "expected_mechanism_ast_shape": ["source", "path", "target", "state_delta"],
        "expected_state_dimensions": state_dimensions,
        "expected_theme_type": archetype["theme"],
        "expected_timing_effect": "insufficient" if "insufficient" in archetype["case_type"] else "activation_expected" if any(token in archetype["case_type"] for token in ("luck", "year", "month")) else "baseline_or_overlay",
        "expected_decision_confidence_band": "not_available" if domain == "unsupported" else "low_or_medium",
        "must_not": sorted(set([*archetype["must_not"], "month_command_unconditional_master", "fake_relationship_judgment", "hard_filled_mechanism_ast"])),
    }
    return {"contract_id": f"contract.{seed_id}", "chart_seed_id": seed_id, "review_status": "candidate_pending_review", "expected_contract": expected}


def _domain(case_type: str) -> str:
    if "unsupported" in case_type:
        return "unsupported"
    if any(token in case_type for token in ("wealth", "peer_competes", "output_to_wealth")):
        return "wealth"
    return "career"


def _theme(path: str) -> str:
    if "wealth" in path:
        return "accumulation"
    if "pressure" in path or "control" in path:
        return "pressure_transformation"
    if "resource" in path:
        return "resource_support"
    if "combination" in path or "clash" in path:
        return "mobility"
    return "stability"


def _timing_variant(case_type: str, variant: int) -> str:
    layer = "luck" if "luck" in case_type else "year" if "year" in case_type else "month" if "month" in case_type else "natal"
    return f"timing.{layer}.variant_{variant + 1}"


def _jiazi() -> list[str]:
    stems, branches = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
    return [stems[index % 10] + branches[index % 12] for index in range(60)]


def _probe_taxonomy() -> dict[str, Any]:
    mode_map = {
        "guest_trust": ["self_recognition", "career_mode_clarification", "current_stage_clarification", "unsupported_domain_boundary"],
        "member_decision": ["current_stage_clarification", "timing_readiness", "risk_tolerance", "action_preference", "wealth_pressure"],
        "practitioner_workbench": ["practitioner_client_context", "mechanism_priority", "reality_context_gap", "batch_triage_focus"],
        "research_evidence": ["theory_evidence_classification", "counter_evidence_classification", "validation_status_annotation", "contribution_readiness"],
    }
    signatures = []
    for mode, intents in mode_map.items():
        for intent in intents:
            signatures.append({"signature_id": f"{mode}.{intent}", "product_mode": mode, "domain": "mode_specific", "primary_intent": intent, "hidden_attribute_targets": [intent], "confidence_targets": ["evidence_trust"], "sensitivity_level": "low", "response_shape": "single_choice", "expected_information_gain_band": "medium"})
    return {"version": "v50.probe_semantic_taxonomy.v1", "signature_count": len(signatures), "signatures": signatures, "training_performed": False, "llm_used": False}


def _v2_doc(payload: dict[str, Any]) -> str:
    return f"# V50 Synthetic Chart Taxonomy v2\n\n- Status: candidate pending review\n- Archetypes: {payload['archetype_count']}\n- Independent chart candidates: {payload['unique_chart_count']}\n- Runtime / Theory modified: false\n\nGenerated candidates do not become structural evidence until their expected contracts pass validation.\n"


def _probe_doc(payload: dict[str, Any]) -> str:
    return f"# V50 Probe Semantic Taxonomy v1\n\n- Semantic signatures: {payload['signature_count']}\n- Evidence class: Behavior Evidence\n- LLM used: false\n- High-sensitivity active probing: forbidden\n"


if __name__ == "__main__":
    print(json.dumps(build_c2_taxonomies(), ensure_ascii=False, indent=2))
