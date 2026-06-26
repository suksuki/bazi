from __future__ import annotations

from copy import deepcopy

from v30.validation.real_business_bazi_reading_regression_pack import (
    REAL_BUSINESS_BAZI_READING_REGRESSION_PACK_VERSION,
    build_real_business_bazi_reading_regression_pack,
)


DOMAINS = ("career", "wealth", "relationship", "health", "timing")


def _domain_payload(domain: str) -> dict[str, object]:
    return {
        "summary": f"{domain} summary",
        "customer_takeaway": f"{domain} takeaway",
        "action_prompt": f"{domain} action",
        "calculation_basis": {"version": "v30.practical_domain_calculation_basis.v1"},
        "module_trace": {
            "version": "v30.m6_practical_module_trace.v1",
            "uses_m1_m2_facts": True,
            "uses_m5_ranked_decisions": True,
        },
        "quality_contract": {"version": "v30.practical_reading_quality.v1"},
    }


def _ready_case(
    case_id: str,
    *,
    calendar_type: str = "solar",
    leap: bool = False,
    true_solar: bool = False,
    unknown_gender: bool = False,
) -> dict[str, object]:
    domain_cards = [
        {
            "domain": domain,
            "summary": f"{domain} summary",
            "customer_takeaway": f"{domain} takeaway",
            "action_prompt": f"{domain} action",
        }
        for domain in DOMAINS
    ]
    return {
        "case_id": case_id,
        "passed": True,
        "failures": [],
        "observed": {
            "real_case_fixture": {
                "status": "ready",
                "calendar_type": calendar_type,
                "lunar_is_leap_month": leap,
                "use_true_solar_time": true_solar,
                "gender_status": "unknown" if unknown_gender else "known",
            },
            "production_replay_metadata": {
                "chart_status": "ready",
                "calendar_type": calendar_type,
                "lunar_is_leap_month": leap,
                "use_true_solar_time": true_solar,
                "unknown_gender": unknown_gender,
                "privacy_guard": {
                    "metadata_only": True,
                    "no_private_user_content": True,
                    "no_chart_fact_mutation": True,
                },
            },
            "customer_reading_surface": {
                "surface_type": "customer_reading_loop",
                "reading_summary": {"primary_message": "核心测算摘要"},
                "domain_cards": domain_cards,
            },
            "api_projection_contract": {
                "version": "v30.api_projection_contract.v1",
                "leak_scan": {"passed": True},
            },
            "core_bazi_reading": {
                "surface_type": "core_bazi_calculation",
                "base_fact_summary": {
                    "status": "ready",
                    "pillar_count": 4,
                    "element_distribution": {"木": 2},
                },
                "base_fact_explanations": {
                    "version": "v30.base_bazi_fact_explanations.v1",
                    "boundary": "base_fact_explanations_are_deterministic_context_not_ranked_decisions",
                },
                "m1_m2_completion_summary": {
                    "version": "v30.m1_m2_completion_summary.v1",
                    "status": "ready",
                },
                "ranked_decisions": {
                    "strength": {"primary_candidate": "balanced"},
                    "structure_pattern": {"primary_candidate": "ordinary"},
                    "useful_god": {"primary_candidate": "water"},
                },
                "practical_domains": domain_cards,
            },
            "practical_reading_context": {
                "status": "ready",
                "domain_readings": {domain: _domain_payload(domain) for domain in DOMAINS},
            },
        },
    }


def _suite(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "suite_id": "v30.synthetic.real_case_calibration_pack",
        "passed": all(row["passed"] for row in rows),
        "case_count": len(rows),
        "passed_count": sum(1 for row in rows if row["passed"]),
        "failed_count": sum(1 for row in rows if not row["passed"]),
        "results": rows,
    }


def _ready_rows(count: int = 24) -> list[dict[str, object]]:
    rows = []
    for idx in range(count):
        rows.append(
            _ready_case(
                f"case_{idx:02d}",
                calendar_type="lunar" if idx % 5 == 0 else "solar",
                leap=idx == 5,
                true_solar=idx == 6,
                unknown_gender=idx == 7,
            )
        )
    return rows


def test_b2_builds_expanded_business_reading_regression_pack() -> None:
    result = build_real_business_bazi_reading_regression_pack(synthetic_result=_suite(_ready_rows()), case_limit=24)

    assert result["version"] == REAL_BUSINESS_BAZI_READING_REGRESSION_PACK_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "b2_business_reading_regression_pack_ready"
    assert result["regression_summary"]["regression_case_count"] == 24
    assert result["regression_summary"]["passed_case_count"] == 24
    assert result["regression_summary"]["coverage"]["leap_lunar_case_count"] == 1
    assert result["regression_summary"]["coverage"]["true_solar_case_count"] == 1
    assert result["next_mainline_selection"]["task_id"] == "B3"
    assert result["policy_boundary"]["full_pytest_run_by_default"] is False


def test_b2_blocks_incomplete_domain_cards_and_practical_contracts() -> None:
    rows = _ready_rows()
    broken = deepcopy(rows[-1])
    observed = broken["observed"]
    assert isinstance(observed, dict)
    surface = observed["customer_reading_surface"]
    practical = observed["practical_reading_context"]
    assert isinstance(surface, dict)
    assert isinstance(practical, dict)
    surface["domain_cards"] = [{"domain": "career", "summary": "career"}]
    practical["domain_readings"] = {"career": _domain_payload("career")}
    rows[-1] = broken

    result = build_real_business_bazi_reading_regression_pack(synthetic_result=_suite(rows), case_limit=24)

    failed = result["regression_rows"][-1]
    assert result["status"] == "blocked"
    assert "business_reading_regression_rows_failed" in result["decision"]["blockers"]
    assert "domain_cards_complete" in failed["failed_check_ids"]
    assert "practical_domain_contracts_ready" in failed["failed_check_ids"]
