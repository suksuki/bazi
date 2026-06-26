from __future__ import annotations

from v30.validation.synthetic_archetype_rule_claim_calibration import (
    SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION,
    build_synthetic_archetype_rule_claim_calibration,
    run_synthetic_archetype_rule_claim_calibration,
)


def _case(*, case_id: str = "syn_cal1.test", passed: bool = True) -> dict[str, object]:
    expected_domains = ["wealth", "career", "relationship", "health", "structure", "useful_god", "timing"]
    expected_mechanisms = ["官印相生", "财官印制化"]
    return {
        "case_id": case_id,
        "label": "test archetype",
        "expected": {
            "strength": "weak",
            "useful_god": "resource_or_self_support_review",
            "domains": expected_domains,
            "mechanisms": expected_mechanisms,
        },
        "observed": {
            "diagnosis_status": "ready",
            "claim_count": 71,
            "claim_domain_counts": {
                "wealth": 8,
                "career": 7,
                "relationship": 7,
                "health": 3,
                "structure": 28,
                "useful_god": 10,
                "timing": 3,
            },
            "blocked_overclaim_count": 156,
            "needs_calibration_count": 23,
            "path_count": 10,
            "path_domain_counts": {"wealth": 5, "career": 8, "structure": 10},
            "mechanism_counts": {"官印相生": 3, "财官印制化": 3},
            "graph_node_count": 261,
            "ranked_primary_candidates": {
                "strength": "weak" if passed else "strong",
                "structure_pattern": "ordinary_structure_review",
                "useful_god": "resource_or_self_support_review",
            },
            "ranked_has_scores": True,
            "practical_domain_summaries": {
                "wealth": "财运主线沿财官印制化展开，需要看结构和压力。",
                "career": "事业主线落在官印相生，先看职责压力。",
                "relationship": "关系判断看沟通压力和结构牵引。",
                "health": "健康只看压力节律，不做医学诊断。",
                "timing": "大运流年只作阶段复核。",
            },
            "practical_domain_claim_counts": {
                "wealth": 5,
                "career": 5,
                "relationship": 5,
                "health": 3,
                "timing": 3,
            },
            "practical_domain_claim_quality": {
                "wealth": _quality(),
                "career": _quality(),
                "relationship": _quality(),
                "health": _quality(),
                "timing": _quality(),
            },
            "rbd_boundary": "real_bazi_diagnosis_consumes_m1_to_m6_evidence_without_mutating_chart_facts",
        },
    }


def test_syn_cal1_builds_ready_archetype_calibration() -> None:
    result = build_synthetic_archetype_rule_claim_calibration(case_observations=[_case(case_id=f"case{i}") for i in range(4)])

    assert result["version"] == SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "syn_cal1_archetype_rule_claim_calibration_ready"
    assert result["decision"]["passed_case_count"] == 4
    assert result["calibration_queue"] == []
    assert result["policy_boundary"]["real_person_truth_label_allowed"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "SYN-CAL2"


def test_syn_cal1_routes_failed_archetype_to_readonly_queue() -> None:
    result = build_synthetic_archetype_rule_claim_calibration(
        case_observations=[_case(case_id="pass1"), _case(case_id="pass2"), _case(case_id="pass3"), _case(case_id="fail", passed=False)]
    )

    assert result["status"] == "blocked"
    assert result["decision"]["failed_case_ids"] == ["fail"]
    assert result["calibration_queue"]
    assert result["calibration_queue"][0]["chart_fact_mutation_allowed"] is False
    assert "M5" in result["calibration_queue"][0]["target_modules"]
    assert result["next_mainline_selection"]["task_id"] == "SYN-CAL1-FR"


def test_syn_cal1_runner_passes_current_runtime_archetypes() -> None:
    result = run_synthetic_archetype_rule_claim_calibration()

    assert result["decision"]["decision_status"] == "syn_cal1_archetype_rule_claim_calibration_ready"
    assert result["decision"]["case_count"] == 4
    assert result["decision"]["external_release_allowed"] is False
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert all(
        row["checks"]["m6_core_claim_quality_ready"] is True
        for row in result["case_reviews"]
    )


def _quality() -> dict[str, object]:
    return {
        "version": "v30.core_bazi_claim_quality.v1",
        "quality_ready": True,
        "uses_traceable_claims": True,
        "chart_fact_mutation_allowed": False,
        "fixed_event_prediction_allowed": False,
        "generic_language_hits": [],
    }
