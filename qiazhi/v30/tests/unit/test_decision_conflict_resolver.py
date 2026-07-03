from __future__ import annotations

from v30.brain.conflict_resolver import (
    DECISION_CONFLICT_RESOLVER_VERSION,
    resolve_decision_conflicts,
)
from v30.brain.contracts import DecisionCandidate
from v30.brain.decision_engine import build_decision_result
from v30.production.adapters import signals_from_diagnosis
from v30.production.signal_registry import build_signal_registry
from v30.runtime import create_smoke_runtime


def test_conflict_resolver_explains_branch_calibration_and_counter_evidence_without_mutation() -> None:
    candidates = [
        DecisionCandidate(
            candidate_id="candidate:career:stable",
            claim_id="claim:career:stable",
            domain="career",
            claim_text="事业主线先稳住职责和资质承接。",
            evidence_refs=["ev:career:role"],
            confidence=0.71,
            score_components={"path_coherence": 0.56, "counter_evidence": 0.28},
            requires_calibration=True,
            source_signal_ids=["sig:career:role", "sig:path:guan-yin"],
            signal_source_summary={
                "source_type_counts": {"diagnosis_claim": 1, "path": 1},
                "source_module_counts": {"diagnosis_router": 1, "path_engine": 1},
            },
        ),
        DecisionCandidate(
            candidate_id="candidate:career:breakthrough",
            claim_id="claim:career:breakthrough",
            domain="career",
            claim_text="事业也存在转型突破分支。",
            evidence_refs=["ev:career:output"],
            confidence=0.64,
            score_components={"path_coherence": 0.52, "counter_evidence": 0.0},
            source_signal_ids=["sig:career:output"],
            signal_source_summary={
                "source_type_counts": {"diagnosis_claim": 1},
                "source_module_counts": {"diagnosis_router": 1},
            },
        ),
    ]

    payload = resolve_decision_conflicts(candidates)

    assert payload["version"] == DECISION_CONFLICT_RESOLVER_VERSION
    assert payload["score_mutation_allowed"] is False
    assert payload["verdict_mutation_allowed"] is False
    assert [row["conflict_type"] for row in payload["conflicts"]] == [
        "close_branch_probability",
        "requires_calibration",
        "counter_evidence_present",
    ]
    summary = payload["summary"]
    assert summary["version"] == "v30.decision_conflict_resolver_summary.v1"
    assert summary["candidate_count"] == 2
    assert summary["conflict_count"] == 3
    assert summary["signal_bound_candidate_count"] == 2
    assert summary["candidate_signal_count"] == 3
    audit = payload["audit"][0]
    assert audit["domain"] == "career"
    assert audit["confidence_gap"] == 0.07
    assert audit["top_source_signal_count"] == 2
    assert audit["source_type_counts"]["diagnosis_claim"] == 2
    assert audit["score_mutation_allowed"] is False


def test_decision_engine_uses_conflict_resolver_without_changing_verdict_shape() -> None:
    diagnosis = {
        "claims": [
            {
                "claim_id": "claim:career:stable",
                "domain": "career",
                "claim_level": "domain",
                "claim_text": "事业主线更适合先稳住职责和资质承接。",
                "evidence_ids": ["ev:career:role"],
                "path_ids": ["path:guan-yin"],
            },
            {
                "claim_id": "claim:career:breakthrough",
                "domain": "career",
                "claim_level": "domain",
                "claim_text": "事业也存在转型突破分支，需要看输出是否能承接压力。",
                "evidence_ids": ["ev:career:output"],
                "path_ids": ["path:shi-shang"],
            },
        ],
        "paths": [
            {
                "path_id": "path:guan-yin",
                "score": 0.72,
                "domain_targets": ["career"],
                "evidence_ids": ["ev:career:role"],
            },
            {
                "path_id": "path:shi-shang",
                "score": 0.66,
                "domain_targets": ["career"],
                "evidence_ids": ["ev:career:output"],
            },
        ],
        "portraits": [],
        "features": [],
        "matched_rules": [],
    }
    claim_scores = [
        {
            "claim_id": "claim:career:stable",
            "domain": "career",
            "claim_level": "domain",
            "score": 0.72,
            "requires_question": False,
            "components": {"path_coherence": 0.56, "counter_evidence": 0.0, "missing_context_penalty": 0.0},
        },
        {
            "claim_id": "claim:career:breakthrough",
            "domain": "career",
            "claim_level": "domain",
            "score": 0.66,
            "requires_question": False,
            "components": {"path_coherence": 0.52, "counter_evidence": 0.0, "missing_context_penalty": 0.0},
        },
    ]
    registry = build_signal_registry(
        reading_id="pytest-dca15-conflict",
        signals=signals_from_diagnosis(diagnosis),
    )

    baseline = build_decision_result(
        reading_id="pytest-dca15-conflict",
        active_stage_id="stage:career",
        diagnosis=diagnosis,
        claim_scores=claim_scores,
    )
    signal_bound = build_decision_result(
        reading_id="pytest-dca15-conflict",
        active_stage_id="stage:career",
        diagnosis=diagnosis,
        claim_scores=claim_scores,
        signal_registry=registry.model_dump(mode="json"),
    )

    assert [(row["domain"], row["assertion_level"], row["headline"]) for row in signal_bound["verdicts"]] == [
        (row["domain"], row["assertion_level"], row["headline"]) for row in baseline["verdicts"]
    ]
    assert signal_bound["verdicts"][0]["assertion_level"] == "mixed"
    assert signal_bound["decision_input_bundle"]["conflicts"][0]["conflict_type"] == "close_branch_probability"
    summary = signal_bound["conflict_resolver_summary"]
    assert summary["resolver_version"] == DECISION_CONFLICT_RESOLVER_VERSION
    assert summary["mode"] == "compatibility"
    assert summary["conflict_count"] == 1
    assert summary["score_mutation_allowed"] is False
    assert summary["verdict_mutation_allowed"] is False
    assert signal_bound["conflict_resolver_audit"][0]["signal_bound_candidate_count"] == 2
    assert signal_bound["verdicts"][0]["trace"]["conflict_resolver"]["conflict_count"] == 1
    assert "decision_conflict_resolver_explanation_quality" in signal_bound["training_signal"]["targets"]


def test_runtime_exposes_conflict_resolver_projection_while_preserving_smoke_verdict_count() -> None:
    runtime = create_smoke_runtime("pytest-dca15-conflict-runtime")
    central = runtime.question_plan.policy_effect["central_reading_state"]

    assert len(central["decision_verdicts"]) == 9
    assert central["conflict_resolver_summary"]["version"] == "v30.decision_conflict_resolver_summary.v1"
    assert central["conflict_resolver_summary"]["score_mutation_allowed"] is False
    assert central["conflict_resolver_summary"]["verdict_mutation_allowed"] is False
    assert central["conflict_resolver_audit"]
    assert central["decision_result"]["conflict_resolver_summary"]["candidate_count"] >= len(central["decision_verdicts"])
