from __future__ import annotations

from copy import deepcopy

from v30.validation.real_business_bazi_reading_acceptance import (
    REAL_BUSINESS_BAZI_READING_ACCEPTANCE_VERSION,
    build_real_business_bazi_reading_acceptance,
)


def _ready_case(case_id: str, *, calendar_type: str = "solar") -> dict[str, object]:
    return {
        "case_id": case_id,
        "passed": True,
        "failures": [],
        "observed": {
            "real_case_fixture": {
                "calendar_type": calendar_type,
                "chart_status": "ready",
                "gender_status": "known",
            },
            "production_replay_metadata": {
                "calendar_type": calendar_type,
                "chart_status": "ready",
            },
            "customer_reading_surface": {
                "surface_type": "customer_reading_loop",
                "core_bazi_reading": {},
                "domain_cards": [{"domain": "career"}],
            },
            "api_projection_contract": {
                "version": "v30.api_projection_contract.v1",
                "leak_scan": {"passed": True},
                "customer_surface_order": ["core_bazi_reading", "domain_cards", "questions"],
            },
            "core_bazi_reading": {
                "surface_type": "core_bazi_calculation",
                "four_pillars": ["甲子", "乙丑", "丙寅", "丁卯"],
                "base_fact_summary": {"status": "ready"},
            },
            "practical_reading_context": {
                "status": "ready",
                "domain_readings": {
                    "career": {},
                    "wealth": {},
                    "relationship": {},
                    "health": {},
                    "timing": {},
                },
            },
            "ranked_decisions": {
                "strength": {},
                "structure_pattern": {},
                "useful_god": {},
            },
            "model_signal_summary": {"version": "v30.model_signal_summary.v1"},
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


def test_b1_accepts_business_bazi_reading_loop_from_canonical_cases() -> None:
    rows = [_ready_case(f"case_{idx:02d}", calendar_type="solar" if idx % 2 else "lunar") for idx in range(12)]
    result = build_real_business_bazi_reading_acceptance(synthetic_result=_suite(rows), case_limit=12)

    assert result["version"] == REAL_BUSINESS_BAZI_READING_ACCEPTANCE_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "b1_real_business_bazi_reading_accepted"
    assert result["acceptance_summary"]["ready_case_count"] == 12
    assert result["decision"]["full_pytest_required"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "B2"


def test_b1_blocks_missing_practical_reading_or_customer_projection_leak() -> None:
    rows = [_ready_case(f"case_{idx:02d}", calendar_type="solar" if idx % 2 else "lunar") for idx in range(12)]
    broken = deepcopy(rows[-1])
    observed = broken["observed"]
    assert isinstance(observed, dict)
    observed["practical_reading_context"] = {"status": "ready", "domain_readings": {"career": {}}}
    observed["customer_reading_surface"] = {
        "surface_type": "customer_reading_loop",
        "policy_effect": {"raw_score": 0.9},
    }
    rows[-1] = broken

    result = build_real_business_bazi_reading_acceptance(synthetic_result=_suite(rows), case_limit=12)

    failed = result["acceptance_rows"][-1]
    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "b1_real_business_bazi_reading_blocked"
    assert "business_reading_acceptance_rows_failed" in result["decision"]["blockers"]
    assert "m6_practical_reading_ready" in failed["failed_check_ids"]
    assert "customer_projection_no_internal_leak" in failed["failed_check_ids"]
