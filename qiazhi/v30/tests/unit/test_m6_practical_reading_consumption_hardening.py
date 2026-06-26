from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_m6_practical_reading_consumption_hardening,
    run_m6_practical_reading_consumption_hardening,
)


DOMAINS = ("career", "wealth", "relationship", "health", "timing")


def _m5_closeout(*, blocked: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.m5_calibration_replay_closeout.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "m5_calibration_replay_closed" if ready else "m5_calibration_replay_closeout_blocked",
            "m5_calibration_replay_closed": ready,
            "m5_ranked_decision_steady_support_ready": ready,
            "m5_ready_for_m6_consumption": ready,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
    }


def _domain_payload(domain: str, *, raw_leak: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": "v30.practical_domain_reading.v2",
        "label": domain,
        "summary": f"{domain} summary",
        "customer_takeaway": f"{domain} takeaway",
        "action_prompt": f"{domain} prompt",
        "calculation_basis": {"version": "v30.practical_domain_calculation_basis.v1"},
        "ranked_decision_links": {
            "strength": "balanced",
            "structure_pattern": "ordinary_structure_review",
            "useful_god": "balance_review",
        },
        "model_signal_context": {
            "version": "v30.practical_model_signal_context.v1",
            "top_energy_bands": [{"family": "output", "energy_band": "medium"}],
        },
        "domain_insights": [
            {"insight_type": "opportunity_path"},
            {"insight_type": "pressure_or_risk_path"},
            {"insight_type": "calibration_path"},
        ],
        "action_steps": ["step1", "step2", "step3"],
        "calibration_prompts": ["prompt1", "prompt2"],
        "module_trace": {
            "version": "v30.m6_practical_module_trace.v1",
            "uses_m1_m2_facts": True,
            "uses_m3_structure_evidence": True,
            "uses_m4_model_signal": True,
            "uses_m5_ranked_decisions": True,
            "raw_model_score_visible": False,
            "chart_fact_mutation_allowed": False,
        },
        "quality_contract": {
            "version": "v30.practical_reading_quality.v1",
            "boundary": "practical_reading_quality_trains_expression_not_chart_facts",
        },
        "evidence_ids": ["evidence:1"],
        "explanation_units": ["one", "two", "three"],
        "blocked_claims": ["fixed_event_prediction"],
    }
    if raw_leak:
        payload["raw_score"] = 0.9
    return payload


def _suite(suite_id: str, *, raw_leak: bool = False, passed: bool = True) -> dict[str, object]:
    results = []
    for index in range(30):
        results.append({
            "case_id": f"{suite_id}.{index}",
            "passed": passed,
            "failures": [] if passed else ["failed"],
            "observed": {
                "practical_reading_context": {
                    "status": "ready",
                    "domain_readings": {
                        domain: _domain_payload(domain, raw_leak=raw_leak and index == 0 and domain == "career")
                        for domain in DOMAINS
                    },
                }
            },
        })
    return {
        "suite_id": suite_id,
        "passed": passed,
        "case_count": 30,
        "passed_count": 30 if passed else 29,
        "failed_count": 0 if passed else 1,
        "results": results,
    }


def _business(*, refresh_blocked: bool = False) -> tuple[dict[str, object], dict[str, object]]:
    acceptance = {
        "version": "v30.real_business_bazi_reading_acceptance.v1",
        "decision": {
            "business_bazi_reading_ready": True,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "acceptance_summary": {
            "ready_case_count": 12,
            "m6_practical_ready_count": 12,
            "customer_projection_leak_free_count": 12,
        },
    }
    refresh = {
        "version": "v30.real_business_answer_refresh_regression.v1",
        "decision": {
            "answer_refresh_regression_ready": not refresh_blocked,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "refresh_summary": {
            "answer_case_count": 5,
            "passed_answer_case_count": 4 if refresh_blocked else 5,
            "stable_core_fingerprint_count": 4 if refresh_blocked else 5,
        },
    }
    return acceptance, refresh


def _training(*, missing: bool = False) -> list[dict[str, object]]:
    if missing:
        return []
    return [
        {
            "signal_id": "v30.training_signal.practical_reading_quality",
            "domain": "practical_reading",
            "signal_type": "reading_domain_coverage",
            "strength": 0.95,
            "source_case_ids": ["case1"],
            "payload": {
                "reading_domain_count": 5,
                "module_trace_count": 150,
                "boundary": "v30.training_signal.practical_reading_quality_validates_runtime_context_not_chart_fact",
            },
        }
    ]


def _build(**overrides):
    acceptance, refresh = _business()
    payload = {
        "m5_closeout": _m5_closeout(),
        "m6_contract_synthetic": _suite("v30.synthetic.m6_practical_reading_contract"),
        "real_case_synthetic": _suite("v30.synthetic.real_case_calibration_pack"),
        "business_acceptance": acceptance,
        "answer_refresh_regression": refresh,
        "training_signals": _training(),
    }
    payload.update(overrides)
    return build_m6_practical_reading_consumption_hardening(**payload)


def test_m6_practical_reading_consumption_hardening_ready(tmp_path: Path) -> None:
    result = _build(artifact_dir=tmp_path)
    decision = result["decision"]

    assert result["version"] == "v30.m6_practical_reading_consumption_hardening.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "m6_practical_reading_consumption_hardening_ready"
    assert decision["ready_for_m6_closeout"] is True
    assert decision["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["next_task"] == "M6 Practical Reading Closeout"
    assert Path(str(result["artifact_uri"])).exists()


def test_m6_consumption_blocks_missing_m5_closeout() -> None:
    result = _build(m5_closeout=_m5_closeout(blocked=True))

    assert result["status"] == "blocked"
    assert "m5_closeout_ready_for_m6" in result["decision"]["failed_hardening_check_ids"]


def test_m6_consumption_blocks_raw_score_leak() -> None:
    result = _build(m6_contract_synthetic=_suite("v30.synthetic.m6_practical_reading_contract", raw_leak=True))

    assert result["status"] == "blocked"
    assert "m6_no_raw_score_or_fixed_claim_leak" in result["decision"]["failed_hardening_check_ids"]


def test_m6_consumption_blocks_missing_training_signal() -> None:
    result = _build(training_signals=_training(missing=True))

    assert result["status"] == "blocked"
    assert "m6_training_signal_boundary_locked" in result["decision"]["failed_hardening_check_ids"]


def test_m6_consumption_blocks_answer_refresh_regression() -> None:
    acceptance, refresh = _business(refresh_blocked=True)
    result = _build(business_acceptance=acceptance, answer_refresh_regression=refresh)

    assert result["status"] == "blocked"
    assert "m6_business_reading_and_answer_refresh_ready" in result["decision"]["failed_hardening_check_ids"]


def test_m6_practical_reading_consumption_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_m6_practical_reading_consumption_hardening(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "m6_practical_reading_consumption_hardening_ready"
    assert result["decision"]["domain_payload_count"] >= 100
