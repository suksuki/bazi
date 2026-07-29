import pytest
from abu_v60.decision import (
    CognitiveDecisionKernel,
    CognitiveDecisionLedger,
    DecisionCandidate,
    DecisionKind,
    DecisionLedgerError,
    DecisionProposal,
    DecisionRequest,
    DecisionRouteStatus,
    EpistemicGate,
    GateDisposition,
)


class _ScalarResult:
    def __init__(self, value: str | None) -> None:
        self._value = value

    def scalar_one_or_none(self) -> str | None:
        return self._value


class _MemoryConnection:
    def __init__(self) -> None:
        self.records: dict[str, str] = {}

    def execute(self, statement: object, parameters: dict[str, object]) -> _ScalarResult:
        sql = str(statement)
        decision_id = str(parameters["decision_id"])
        if "INSERT INTO cognition.decision_records" in sql:
            if decision_id in self.records:
                return _ScalarResult(None)
            self.records[decision_id] = str(parameters["record_hash"])
            return _ScalarResult(decision_id)
        if "SELECT record_hash" in sql:
            return _ScalarResult(self.records.get(decision_id))
        raise AssertionError(f"unexpected_sql:{sql}")


def _request() -> DecisionRequest:
    return DecisionRequest(
        request_id="interpretation:1",
        decision_kind=DecisionKind.INTERPRETATION,
        subject_ref="case:1",
        evidence_refs=("evidence:a", "evidence:b", "evidence:counter"),
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
        causation_id="cause:1",
    )


def _proposal(**overrides: object) -> DecisionProposal:
    values: dict[str, object] = {
        "proposal_ref": "proposal:1",
        "request_id": "interpretation:1",
        "reasoner_runtime_ref": "v60.bounded-reasoner-runtime.002",
        "provider_id": "test-bounded-reasoner",
        "model_ref": "test-model:v1",
        "model_profile_ref": "test-profile:v1",
        "model_profile_hash": "b" * 64,
        "prompt_ref": "prompt:compare-qualified-candidates:v1",
        "provider_response_ref": "provider-response:1",
        "context_hash": "a" * 64,
        "selected_candidate_ref": "candidate:a",
        "reviewed_candidate_refs": ("candidate:a", "candidate:b"),
        "evidence_refs_used": ("evidence:a",),
        "counter_evidence_refs": ("evidence:counter",),
        "confidence": 0.62,
        "rationale_summary": "Candidate A is better supported by the admitted evidence.",
    }
    values.update(overrides)
    return DecisionProposal(**values)


def test_gate_admits_only_bounded_comparison_and_ledger_replays() -> None:
    request = _request()
    ledger = CognitiveDecisionLedger()
    route = CognitiveDecisionKernel().route(request)
    assert route.status is DecisionRouteStatus.PENDING

    proposal = _proposal()
    receipt = EpistemicGate().evaluate(
        request=request,
        route=route,
        proposal=proposal,
    )
    assert receipt.disposition is GateDisposition.ADMITTED
    assert receipt.decision_record_allowed is True
    assert receipt.canonical_domain_write_allowed is False

    connection = _MemoryConnection()
    first = ledger.record_admitted_proposal(
        connection=connection,
        request=request,
        proposal=proposal,
        gate_receipt=receipt,
    )
    replay = ledger.record_admitted_proposal(
        connection=connection,
        request=request,
        proposal=proposal,
        gate_receipt=receipt,
    )
    assert first.route.selected_candidate_ref == "candidate:a"
    assert first.record_hash == replay.record_hash
    assert replay.already_recorded is True


@pytest.mark.parametrize(
    ("proposal", "reason"),
    (
        (
            _proposal(reviewed_candidate_refs=("candidate:a",)),
            "qualified_candidate_comparison_incomplete",
        ),
        (
            _proposal(selected_candidate_ref="candidate:unknown"),
            "selected_candidate_not_qualified",
        ),
        (
            _proposal(evidence_refs_used=("evidence:future",)),
            "proposal_uses_unbound_evidence",
        ),
        (
            _proposal(evidence_refs_used=("evidence:b",)),
            "selected_candidate_evidence_not_cited",
        ),
    ),
)
def test_gate_rejects_incomplete_or_unbound_proposal(
    proposal: DecisionProposal,
    reason: str,
) -> None:
    request = _request()
    receipt = EpistemicGate().evaluate(
        request=request,
        route=CognitiveDecisionKernel().route(request),
        proposal=proposal,
    )

    assert receipt.disposition is GateDisposition.REJECTED
    assert receipt.reason == reason
    assert receipt.decision_record_allowed is False
    assert receipt.selected_candidate_ref is None


def test_pending_llm_route_cannot_be_recorded_without_admitted_proposal() -> None:
    with pytest.raises(
        DecisionLedgerError,
        match="non_final_decision_cannot_be_recorded",
    ):
        CognitiveDecisionLedger().route_and_record(
            connection=_MemoryConnection(),
            request=_request(),
        )
