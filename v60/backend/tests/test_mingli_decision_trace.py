from __future__ import annotations

from copy import deepcopy

import pytest
from abu_v60.decision import (
    CognitiveDecisionKernel,
    DecisionCandidate,
    DecisionKind,
    DecisionProposal,
    DecisionRequest,
    EpistemicGate,
)
from abu_v60.mingli.mechanism_decision import (
    MechanismComparisonUnavailableError,
    _verified_decision_trace,
)
from abu_v60.provenance import content_hash, stable_ref


def _request() -> DecisionRequest:
    return DecisionRequest(
        request_id="attention-request:1",
        decision_kind=DecisionKind.INTERPRETATION,
        subject_ref="mechanism-vector:1",
        evidence_refs=("evidence:a", "evidence:b"),
        candidates=(
            DecisionCandidate(
                candidate_ref="candidate:a",
                evidence_refs=("evidence:a",),
            ),
            DecisionCandidate(
                candidate_ref="candidate:b",
                evidence_refs=("evidence:b",),
            ),
        ),
        llm_allowed=True,
        correlation_id="correlation:1",
        causation_id="mechanism-vector:1",
    )


def _record(request: DecisionRequest) -> dict[str, object]:
    proposal: dict[str, object] = {
        "request_id": request.request_id,
        "reasoner_runtime_ref": "reasoner-runtime:1",
        "provider_id": "bounded-provider",
        "model_ref": "bounded-model:1",
        "model_profile_ref": "model-profile:1",
        "model_profile_hash": "a" * 64,
        "prompt_ref": "prompt:1",
        "provider_response_ref": "provider-response:1",
        "context_hash": "b" * 64,
        "selected_candidate_ref": "candidate:a",
        "reviewed_candidate_refs": ["candidate:a", "candidate:b"],
        "evidence_refs_used": ["evidence:a", "evidence:b"],
        "counter_evidence_refs": ["evidence:b"],
        "confidence": 0.91,
        "rationale_summary": "Compare both candidates and inspect candidate A first.",
    }
    proposal["proposal_ref"] = stable_ref(
        "v60-reasoner-proposal",
        {
            "runtime_ref": proposal["reasoner_runtime_ref"],
            "request_id": proposal["request_id"],
            "provider_id": proposal["provider_id"],
            "model_ref": proposal["model_ref"],
            "model_profile_ref": proposal["model_profile_ref"],
            "model_profile_hash": proposal["model_profile_hash"],
            "prompt_ref": proposal["prompt_ref"],
            "provider_response_ref": proposal["provider_response_ref"],
            "context_hash": proposal["context_hash"],
            "output": {
                key: proposal[key]
                for key in (
                    "selected_candidate_ref",
                    "reviewed_candidate_refs",
                    "evidence_refs_used",
                    "counter_evidence_refs",
                    "confidence",
                    "rationale_summary",
                )
            },
        },
    )
    gate_identity = {
        "gate_version": "v60.epistemic-gate.001",
        "request_id": request.request_id,
        "proposal_ref": proposal["proposal_ref"],
        "proposal_hash": content_hash(proposal),
        "disposition": "ADMITTED",
        "reason": "bounded_reasoner_proposal_admitted",
    }
    return {
        "kernel_version": "v60.cognitive-decision-kernel.004",
        "request": request.model_dump(mode="json"),
        "route": {
            "request_id": request.request_id,
            "status": "RESOLVED",
            "authority": "LLM_REASONER",
            "selected_candidate_ref": "candidate:a",
            "result": None,
            "reason": "bounded_reasoner_proposal_admitted",
        },
        "proposal": proposal,
        "gate_receipt": {
            "receipt_ref": stable_ref(
                "v60-epistemic-gate-receipt",
                gate_identity,
            ),
            "gate_version": "v60.epistemic-gate.001",
            "request_id": request.request_id,
            "proposal_ref": proposal["proposal_ref"],
            "proposal_hash": content_hash(proposal),
            "disposition": "ADMITTED",
            "reason": "bounded_reasoner_proposal_admitted",
            "selected_candidate_ref": "candidate:a",
            "decision_record_allowed": True,
            "canonical_domain_write_allowed": False,
        },
    }


def test_decision_trace_verifies_identity_coverage_and_authority_boundary() -> None:
    request = _request()
    record = _record(request)

    trace = _verified_decision_trace(
        decision_ref=_decision_ref(request),
        decision_hash=content_hash(record),
        row_authority="LLM_REASONER",
        row_status="RESOLVED",
        record=record,
        request=request,
        expected_context_hash="b" * 64,
    )

    assert trace["trace_integrity_status"] == "VERIFIED"
    assert trace["attention_candidate_refs"] == [
        "candidate:a",
        "candidate:b",
    ]
    assert trace["reviewed_candidate_refs"] == [
        "candidate:a",
        "candidate:b",
    ]
    assert trace["candidate_coverage_complete"] is True
    assert trace["candidate_coverage_semantics"] == ("PROVIDER_REVIEWED_ATTENTION_CANDIDATES")
    assert trace["selected_evidence_bound"] is True
    assert trace["selected_evidence_use_semantics"] == ("PROVIDER_CITED_BOUND_EVIDENCE")
    assert trace["evidence_use_semantics"] == ("PROVIDER_CITED_BOUND_EVIDENCE")
    assert trace["gate_disposition"] == "ADMITTED"
    assert trace["provider_counter_evidence_refs"] == ["evidence:b"]
    assert trace["counter_evidence_semantics"] == ("BOUND_REF_ONLY_NOT_PROFESSIONALLY_ADMITTED")
    assert trace["professional_selection_qualified"] is False
    assert trace["professional_verdict_allowed"] is False
    assert trace["probability_claim_allowed"] is False
    assert trace["canonical_domain_write_allowed"] is False


def test_decision_trace_fails_closed_on_hash_or_candidate_coverage_drift() -> None:
    request = _request()
    record = _record(request)

    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_decision_record_hash_invalid",
    ):
        _verified_decision_trace(
            decision_ref=_decision_ref(request),
            decision_hash="0" * 64,
            row_authority="LLM_REASONER",
            row_status="RESOLVED",
            record=record,
            request=request,
            expected_context_hash="b" * 64,
        )

    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_decision_identity_invalid",
    ):
        _verified_decision_trace(
            decision_ref="decision:wrong",
            decision_hash=content_hash(record),
            row_authority="LLM_REASONER",
            row_status="RESOLVED",
            record=record,
            request=request,
            expected_context_hash="b" * 64,
        )

    kernel_version_drift = deepcopy(record)
    kernel_version_drift["kernel_version"] = "not-a-kernel-version"
    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_decision_kernel_version_invalid",
    ):
        _verified_decision_trace(
            decision_ref=_decision_ref(request),
            decision_hash=content_hash(kernel_version_drift),
            row_authority="LLM_REASONER",
            row_status="RESOLVED",
            record=kernel_version_drift,
            request=request,
            expected_context_hash="b" * 64,
        )

    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_decision_reasoner_context_invalid",
    ):
        _verified_decision_trace(
            decision_ref=_decision_ref(request),
            decision_hash=content_hash(record),
            row_authority="LLM_REASONER",
            row_status="RESOLVED",
            record=record,
            request=request,
            expected_context_hash="c" * 64,
        )

    forged_rule = deepcopy(record)
    forged_rule.pop("proposal")
    forged_rule.pop("gate_receipt")
    forged_rule["route"] = {
        "request_id": request.request_id,
        "status": "RESOLVED",
        "authority": "RULE_ENGINE",
        "selected_candidate_ref": "candidate:a",
        "result": None,
        "reason": "one_qualified_candidate_remains",
    }
    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_decision_route_not_canonical",
    ):
        _verified_decision_trace(
            decision_ref=_decision_ref(request),
            decision_hash=content_hash(forged_rule),
            row_authority="RULE_ENGINE",
            row_status="RESOLVED",
            record=forged_rule,
            request=request,
            expected_context_hash=None,
        )

    proposal_shape_drift = deepcopy(record)
    drifted_proposal = proposal_shape_drift["proposal"]
    drifted_gate = proposal_shape_drift["gate_receipt"]
    assert isinstance(drifted_proposal, dict)
    assert isinstance(drifted_gate, dict)
    drifted_proposal["unexpected_field"] = "not-in-contract"
    drifted_gate["proposal_hash"] = content_hash(drifted_proposal)
    drifted_gate["receipt_ref"] = stable_ref(
        "v60-epistemic-gate-receipt",
        {
            "gate_version": drifted_gate["gate_version"],
            "request_id": drifted_gate["request_id"],
            "proposal_ref": drifted_gate["proposal_ref"],
            "proposal_hash": drifted_gate["proposal_hash"],
            "disposition": drifted_gate["disposition"],
            "reason": drifted_gate["reason"],
        },
    )
    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_decision_proposal_gate_contract_invalid",
    ):
        _verified_decision_trace(
            decision_ref=_decision_ref(request),
            decision_hash=content_hash(proposal_shape_drift),
            row_authority="LLM_REASONER",
            row_status="RESOLVED",
            record=proposal_shape_drift,
            request=request,
            expected_context_hash="b" * 64,
        )

    gate_identity_drift = deepcopy(record)
    drifted_gate = gate_identity_drift["gate_receipt"]
    assert isinstance(drifted_gate, dict)
    drifted_gate["gate_version"] = "not-a-gate-version"
    drifted_gate["reason"] = "not-an-admission-reason"
    drifted_gate["receipt_ref"] = stable_ref(
        "v60-epistemic-gate-receipt",
        {
            "gate_version": drifted_gate["gate_version"],
            "request_id": drifted_gate["request_id"],
            "proposal_ref": drifted_gate["proposal_ref"],
            "proposal_hash": drifted_gate["proposal_hash"],
            "disposition": drifted_gate["disposition"],
            "reason": drifted_gate["reason"],
        },
    )
    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_decision_gate_not_canonical",
    ):
        _verified_decision_trace(
            decision_ref=_decision_ref(request),
            decision_hash=content_hash(gate_identity_drift),
            row_authority="LLM_REASONER",
            row_status="RESOLVED",
            record=gate_identity_drift,
            request=request,
            expected_context_hash="b" * 64,
        )

    incomplete = deepcopy(record)
    proposal = incomplete["proposal"]
    gate = incomplete["gate_receipt"]
    assert isinstance(proposal, dict)
    assert isinstance(gate, dict)
    proposal["reviewed_candidate_refs"] = ["candidate:a"]
    proposal["proposal_ref"] = stable_ref(
        "v60-reasoner-proposal",
        {
            "runtime_ref": proposal["reasoner_runtime_ref"],
            "request_id": proposal["request_id"],
            "provider_id": proposal["provider_id"],
            "model_ref": proposal["model_ref"],
            "model_profile_ref": proposal["model_profile_ref"],
            "model_profile_hash": proposal["model_profile_hash"],
            "prompt_ref": proposal["prompt_ref"],
            "provider_response_ref": proposal["provider_response_ref"],
            "context_hash": proposal["context_hash"],
            "output": {
                key: proposal[key]
                for key in (
                    "selected_candidate_ref",
                    "reviewed_candidate_refs",
                    "evidence_refs_used",
                    "counter_evidence_refs",
                    "confidence",
                    "rationale_summary",
                )
            },
        },
    )
    incomplete["gate_receipt"] = (
        EpistemicGate()
        .evaluate(
            request=request,
            route=CognitiveDecisionKernel().route(request),
            proposal=DecisionProposal.model_validate(proposal),
        )
        .model_dump(mode="json")
    )

    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_decision_evidence_coverage_invalid",
    ):
        _verified_decision_trace(
            decision_ref=_decision_ref(request),
            decision_hash=content_hash(incomplete),
            row_authority="LLM_REASONER",
            row_status="RESOLVED",
            record=incomplete,
            request=request,
            expected_context_hash="b" * 64,
        )


def test_decision_trace_supports_single_candidate_rule_engine_route() -> None:
    request = DecisionRequest(
        request_id="attention-request:rule",
        decision_kind=DecisionKind.INTERPRETATION,
        subject_ref="mechanism-vector:rule",
        evidence_refs=("evidence:rule",),
        candidates=(
            DecisionCandidate(
                candidate_ref="candidate:rule",
                evidence_refs=("evidence:rule",),
            ),
        ),
        llm_allowed=True,
        correlation_id="correlation:rule",
        causation_id="mechanism-vector:rule",
    )
    record = {
        "kernel_version": "v60.cognitive-decision-kernel.004",
        "request": request.model_dump(mode="json"),
        "route": {
            "request_id": request.request_id,
            "status": "RESOLVED",
            "authority": "RULE_ENGINE",
            "selected_candidate_ref": "candidate:rule",
            "result": None,
            "reason": "one_qualified_candidate_remains",
        },
    }

    trace = _verified_decision_trace(
        decision_ref=_decision_ref(request),
        decision_hash=content_hash(record),
        row_authority="RULE_ENGINE",
        row_status="RESOLVED",
        record=record,
        request=request,
        expected_context_hash=None,
    )

    assert trace["reviewed_candidate_refs"] == ["candidate:rule"]
    assert trace["candidate_coverage_semantics"] == ("RULE_ENGINE_SINGLE_ATTENTION_CANDIDATE")
    assert trace["evidence_refs_used"] == []
    assert trace["evidence_use_semantics"] == ("REQUEST_BOUND_NOT_PROVIDER_USED")
    assert trace["selected_evidence_bound"] is True
    assert trace["selected_evidence_use_semantics"] == ("REQUEST_BOUND_RULE_NOT_PROVIDER_CITED")
    assert trace["gate_disposition"] == "NOT_REQUIRED"
    assert trace["proposal_ref"] is None
    assert trace["gate_receipt_ref"] is None
    assert trace["provider_id"] is None
    assert trace["selection_rationale_contract"] == (
        "DETERMINISTIC_SINGLE_CANDIDATE_ROUTE_REASON_ONLY"
    )
    assert trace["provider_confidence_semantics"] == ("NOT_RECORDED_RULE_ENGINE_ROUTE")
    assert trace["professional_selection_qualified"] is False

    rule_shape_drift = deepcopy(record)
    rule_shape_drift["proposal"] = {}
    rule_shape_drift["gate_receipt"] = {}
    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_decision_record_shape_invalid",
    ):
        _verified_decision_trace(
            decision_ref=_decision_ref(request),
            decision_hash=content_hash(rule_shape_drift),
            row_authority="RULE_ENGINE",
            row_status="RESOLVED",
            record=rule_shape_drift,
            request=request,
            expected_context_hash=None,
        )

    forged_llm = deepcopy(record)
    forged_llm["route"] = {
        "request_id": request.request_id,
        "status": "RESOLVED",
        "authority": "LLM_REASONER",
        "selected_candidate_ref": "candidate:rule",
        "result": None,
        "reason": "bounded_reasoner_proposal_admitted",
    }
    forged_llm["proposal"] = {}
    forged_llm["gate_receipt"] = {}
    with pytest.raises(
        MechanismComparisonUnavailableError,
        match="mechanism_decision_route_not_canonical",
    ):
        _verified_decision_trace(
            decision_ref=_decision_ref(request),
            decision_hash=content_hash(forged_llm),
            row_authority="LLM_REASONER",
            row_status="RESOLVED",
            record=forged_llm,
            request=request,
            expected_context_hash="b" * 64,
        )


def _decision_ref(request: DecisionRequest) -> str:
    return stable_ref(
        "v60-decision",
        {
            "request_id": request.request_id,
            "decision_kind": request.decision_kind.value,
            "subject_ref": request.subject_ref,
        },
    )
