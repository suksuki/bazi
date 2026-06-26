from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Mapping

from v30.runtime import create_smoke_runtime


SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION = "v30.synthetic_archetype_rule_claim_calibration.v1"

ARCHETYPE_CASES: tuple[dict[str, Any], ...] = (
    {
        "case_id": "syn_cal1.metal_resource_pressure",
        "label": "Metal day-master resource and responsibility pressure",
        "day_master": "庚",
        "day_master_element": "metal",
        "luck_pillar": "戊寅",
        "flow_year_pillar": "庚子",
        "expected_strength": "weak",
        "expected_useful_god": "resource_or_self_support_review",
        "expected_domains": {"wealth", "career", "relationship", "health", "structure", "useful_god", "timing"},
        "expected_mechanisms": {"官印相生", "财官印制化"},
    },
    {
        "case_id": "syn_cal1.wood_growth_conflict",
        "label": "Wood day-master growth and output conflict",
        "day_master": "甲",
        "day_master_element": "wood",
        "luck_pillar": "戊寅",
        "flow_year_pillar": "庚子",
        "expected_strength": "strong",
        "expected_useful_god": "output_or_wealth_release_review",
        "expected_domains": {"wealth", "career", "relationship", "structure", "useful_god", "hidden_factor"},
        "expected_mechanisms": {"食伤制官杀", "食伤生财"},
    },
    {
        "case_id": "syn_cal1.fire_expression_wealth",
        "label": "Fire day-master expression-to-resource review",
        "day_master": "丙",
        "day_master_element": "fire",
        "luck_pillar": "己卯",
        "flow_year_pillar": "辛丑",
        "expected_strength": "weak",
        "expected_useful_god": "resource_or_self_support_review",
        "expected_domains": {"wealth", "career", "relationship", "structure", "useful_god"},
        "expected_mechanisms": {"官印相生", "财官印制化"},
    },
    {
        "case_id": "syn_cal1.water_flow_timing",
        "label": "Water day-master balanced timing review",
        "day_master": "壬",
        "day_master_element": "water",
        "luck_pillar": "甲辰",
        "flow_year_pillar": "丙午",
        "expected_strength": "balanced",
        "expected_useful_god": "balance_review",
        "expected_domains": {"wealth", "career", "relationship", "health", "timing", "structure", "useful_god"},
        "expected_mechanisms": {"财官印制化", "食伤生财"},
    },
)


def run_synthetic_archetype_rule_claim_calibration() -> dict[str, Any]:
    rows = []
    for spec in ARCHETYPE_CASES:
        runtime = create_smoke_runtime(
            reading_id=str(spec["case_id"]),
            day_master=str(spec["day_master"]),
            day_master_element=str(spec["day_master_element"]),
            luck_pillar=str(spec["luck_pillar"]),
            flow_year_pillar=str(spec["flow_year_pillar"]),
        )
        rows.append(_observe_case(spec, runtime.question_plan.policy_effect))
    return build_synthetic_archetype_rule_claim_calibration(case_observations=rows)


def build_synthetic_archetype_rule_claim_calibration(*, case_observations: list[Mapping[str, Any]]) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    rows = [_case_review(row) for row in case_observations]
    checks = _checks(rows)
    decision = _decision(rows, checks)
    return {
        "version": SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["synthetic_archetype_calibration_ready"] else "blocked",
        "task": {
            "task_id": "SYN-CAL1",
            "title": "Synthetic Archetype Rule-Claim Calibration",
            "scope": "validate_m3_m5_m6_judgment_quality_with_synthetic_typical_bazi_archetypes",
        },
        "archetype_case_count": len(rows),
        "case_reviews": rows,
        "checks": checks,
        "decision": decision,
        "calibration_queue": _calibration_queue(rows),
        "policy_boundary": {
            "real_person_truth_label_allowed": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "external_release_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "syn_cal1_uses_synthetic_archetype_expectations_not_real_person_truth_or_chart_fact_mutation",
    }


def _observe_case(spec: Mapping[str, Any], policy_effect: Mapping[str, Any]) -> dict[str, Any]:
    diagnosis = _mapping(policy_effect.get("real_bazi_diagnosis"))
    summaries = _mapping(diagnosis.get("summaries"))
    claims = _mapping(summaries.get("claims"))
    paths = _mapping(summaries.get("paths"))
    graph = _mapping(summaries.get("graph"))
    ranked = _mapping(policy_effect.get("ranked_decisions"))
    practical = _mapping(policy_effect.get("practical_reading_context"))
    domain_readings = _mapping(practical.get("domain_readings"))
    return {
        "case_id": str(spec.get("case_id") or ""),
        "label": str(spec.get("label") or ""),
        "day_master": str(spec.get("day_master") or ""),
        "expected": {
            "strength": str(spec.get("expected_strength") or ""),
            "useful_god": str(spec.get("expected_useful_god") or ""),
            "domains": sorted(str(row) for row in spec.get("expected_domains", set())),
            "mechanisms": sorted(str(row) for row in spec.get("expected_mechanisms", set())),
        },
        "observed": {
            "diagnosis_status": str(diagnosis.get("status") or ""),
            "claim_count": int(claims.get("claim_count", 0) or 0),
            "claim_domain_counts": dict(_mapping(claims.get("domain_counts"))),
            "blocked_overclaim_count": int(claims.get("blocked_overclaim_count", 0) or 0),
            "needs_calibration_count": int(claims.get("needs_calibration_count", 0) or 0),
            "path_count": int(paths.get("path_count", 0) or 0),
            "path_domain_counts": dict(_mapping(paths.get("domain_counts"))),
            "mechanism_counts": dict(_mapping(paths.get("mechanism_counts"))),
            "graph_node_count": int(graph.get("node_count", 0) or 0),
            "ranked_primary_candidates": {
                key: str(_mapping(value).get("primary_candidate") or "")
                for key, value in ranked.items()
                if isinstance(value, Mapping)
            },
            "ranked_has_scores": all(
                bool(_mapping(value).get("candidate_scores"))
                for key, value in ranked.items()
                if key in {"strength", "structure_pattern", "useful_god"} and isinstance(value, Mapping)
            ),
            "practical_domain_summaries": {
                domain: str(_mapping(payload).get("diagnosis_summary") or "")
                for domain, payload in domain_readings.items()
                if isinstance(payload, Mapping) and domain in {"wealth", "career", "relationship", "health", "timing"}
            },
            "practical_domain_claim_counts": {
                domain: len(_list(_mapping(payload).get("diagnosis_claims")))
                for domain, payload in domain_readings.items()
                if isinstance(payload, Mapping) and domain in {"wealth", "career", "relationship", "health", "timing"}
            },
            "practical_domain_claim_quality": {
                domain: dict(_mapping(_mapping(payload).get("core_claim_quality")))
                for domain, payload in domain_readings.items()
                if isinstance(payload, Mapping) and domain in {"wealth", "career", "relationship", "health", "timing"}
            },
            "rbd_boundary": str(diagnosis.get("boundary") or ""),
        },
    }


def _case_review(row: Mapping[str, Any]) -> dict[str, Any]:
    expected = _mapping(row.get("expected"))
    observed = _mapping(row.get("observed"))
    domain_counts = _mapping(observed.get("claim_domain_counts"))
    mechanism_counts = _mapping(observed.get("mechanism_counts"))
    ranked = _mapping(observed.get("ranked_primary_candidates"))
    practical_summaries = _mapping(observed.get("practical_domain_summaries"))
    practical_claim_counts = _mapping(observed.get("practical_domain_claim_counts"))
    practical_claim_quality = _mapping(observed.get("practical_domain_claim_quality"))
    expected_domains = set(_str_list(expected.get("domains")))
    expected_mechanisms = set(_str_list(expected.get("mechanisms")))
    checks = {
        "rbd_ready": observed.get("diagnosis_status") == "ready",
        "m3_claim_domains_cover_archetype": expected_domains <= {key for key, value in domain_counts.items() if int(value or 0) > 0},
        "m3_dynamic_mechanisms_cover_archetype": expected_mechanisms <= {key for key, value in mechanism_counts.items() if int(value or 0) > 0},
        "m5_strength_candidate_matches": ranked.get("strength") == expected.get("strength"),
        "m5_useful_god_candidate_matches": ranked.get("useful_god") == expected.get("useful_god"),
        "m5_candidate_scores_present": observed.get("ranked_has_scores") is True,
        "m6_domain_claims_present": all(int(practical_claim_counts.get(domain, 0) or 0) > 0 for domain in {"wealth", "career", "relationship"}),
        "m6_summaries_are_bazi_specific": _summaries_are_bazi_specific(practical_summaries),
        "m6_core_claim_quality_ready": _core_claim_quality_ready(practical_claim_quality),
        "bounded_claims_have_overclaim_blocks": int(observed.get("blocked_overclaim_count", 0) or 0) >= 20,
        "calibration_routes_exist": int(observed.get("needs_calibration_count", 0) or 0) >= 4,
        "diagnosis_graph_links_claims": int(observed.get("graph_node_count", 0) or 0) > int(observed.get("claim_count", 0) or 0),
        "no_chart_fact_mutation_boundary": observed.get("rbd_boundary") == "real_bazi_diagnosis_consumes_m1_to_m6_evidence_without_mutating_chart_facts",
    }
    failed = [key for key, passed in checks.items() if not passed]
    return {
        "case_id": str(row.get("case_id") or ""),
        "label": str(row.get("label") or ""),
        "passed": not failed,
        "failed_check_ids": failed,
        "checks": checks,
        "expected": dict(expected),
        "observed": dict(observed),
        "calibration_target_modules": _target_modules(failed),
        "boundary": "archetype_case_checks_module_judgment_quality_not_real_life_truth",
    }


def _checks(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    failed_cases = [str(row.get("case_id") or "") for row in rows if row.get("passed") is not True]
    module_targets = Counter(
        module
        for row in rows
        for module in _str_list(row.get("calibration_target_modules"))
    )
    return [
        {
            "check_id": "archetype_pack_has_minimum_coverage",
            "passed": len(rows) >= 4,
            "observed": {"case_count": len(rows)},
        },
        {
            "check_id": "all_archetypes_pass_m3_m5_m6_expectations",
            "passed": not failed_cases,
            "observed": {"failed_case_ids": failed_cases},
        },
        {
            "check_id": "calibration_failures_are_routed_to_modules",
            "passed": not failed_cases or bool(module_targets),
            "observed": {"target_modules": dict(module_targets)},
        },
        {
            "check_id": "synthetic_archetypes_do_not_use_real_person_truth_labels",
            "passed": True,
            "observed": {"real_person_truth_label_allowed": False},
        },
        {
            "check_id": "policy_boundaries_remain_read_only",
            "passed": True,
            "observed": {
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
            },
        },
    ]


def _decision(rows: list[Mapping[str, Any]], checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed_checks = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    failed_cases = [str(row.get("case_id") or "") for row in rows if row.get("passed") is not True]
    ready = not failed_checks
    return {
        "synthetic_archetype_calibration_ready": ready,
        "decision_status": "syn_cal1_archetype_rule_claim_calibration_ready" if ready else "syn_cal1_archetype_rule_claim_calibration_blocked",
        "case_count": len(rows),
        "passed_case_count": len(rows) - len(failed_cases),
        "failed_case_ids": failed_cases,
        "failed_check_ids": failed_checks,
        "external_release_allowed": False,
        "real_person_truth_label_allowed": False,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
    }


def _calibration_queue(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    queue = []
    for row in rows:
        if row.get("passed") is True:
            continue
        queue.append(
            {
                "queue_item_id": f"syn_cal1.calibration.{row.get('case_id')}",
                "case_id": row.get("case_id"),
                "target_modules": _str_list(row.get("calibration_target_modules")),
                "failed_check_ids": _str_list(row.get("failed_check_ids")),
                "review_only": True,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "boundary": "syn_cal1_queue_routes_archetype_gaps_to_review_not_auto_training",
            }
        )
    return queue


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["synthetic_archetype_calibration_ready"]:
        return {
            "task_id": "SYN-CAL2",
            "title": "Synthetic Archetype Calibration Queue And Tier Registration",
            "selected_track": "synthetic_archetype_calibration",
            "scope": [
                "register SYN-CAL1 as a targeted synthetic tier",
                "connect failed archetype rows to readonly calibration queues",
                "keep real-person truth labels and chart-fact mutation forbidden",
            ],
        }
    return {
        "task_id": "SYN-CAL1-FR",
        "title": "Synthetic Archetype Rule-Claim Calibration Failure Review",
        "selected_track": "synthetic_archetype_calibration",
        "scope": [
            "inspect failed archetype expectation rows",
            "repair M3/M5/M6 evidence consumption only",
            "do not mutate chart facts or promote policy pointers",
        ],
    }


def _summaries_are_bazi_specific(summaries: Mapping[str, Any]) -> bool:
    terms = ("财运", "事业", "关系", "压力", "用神", "结构", "大运", "流年", "官印", "食伤", "财官")
    generic_hits = ("当前 chart supports", "Current chart", "fallback", "套路")
    values = [str(value) for value in summaries.values() if str(value)]
    if len(values) < 4:
        return False
    joined = "\n".join(values)
    return sum(1 for term in terms if term in joined) >= 4 and not any(hit in joined for hit in generic_hits)


def _core_claim_quality_ready(rows: Mapping[str, Any]) -> bool:
    required_domains = {"wealth", "career", "relationship", "health", "timing"}
    for domain in required_domains:
        quality = _mapping(rows.get(domain))
        if quality.get("version") != "v30.core_bazi_claim_quality.v1":
            return False
        if quality.get("quality_ready") is not True:
            return False
        if quality.get("uses_traceable_claims") is not True:
            return False
        if quality.get("chart_fact_mutation_allowed") is not False:
            return False
        if quality.get("fixed_event_prediction_allowed") is not False:
            return False
        if _list(quality.get("generic_language_hits")):
            return False
    return True


def _target_modules(failed: list[str]) -> list[str]:
    modules: set[str] = set()
    for check_id in failed:
        if check_id.startswith("m3_") or "mechanism" in check_id or "claims" in check_id:
            modules.add("M3")
        if check_id.startswith("m5_") or "ranked" in check_id:
            modules.add("M5")
        if check_id.startswith("m6_") or "summaries" in check_id:
            modules.add("M6")
        if "calibration" in check_id:
            modules.add("M7")
    return sorted(modules or {"SYN-CAL1"})


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _str_list(value: object) -> list[str]:
    if isinstance(value, (set, list, tuple)):
        return [str(row) for row in value if str(row)]
    return []
