import pytest
from abu_v60.decision import (
    CognitiveDecisionLedger,
    DecisionAuthority,
    DecisionCandidate,
    DecisionKind,
    DecisionLedgerError,
    DecisionRequest,
    DecisionRouter,
    DecisionRouteStatus,
)


class _ScalarResult:
    def __init__(self, value: str | None) -> None:
        self._value = value

    def scalar_one_or_none(self) -> str | None:
        return self._value


class _MemoryDecisionConnection:
    def __init__(self) -> None:
        self.records: dict[str, str] = {}
        self.insert_attempts = 0

    def execute(
        self,
        statement: object,
        parameters: dict[str, object],
    ) -> _ScalarResult:
        sql = str(statement)
        decision_id = str(parameters["decision_id"])
        if "INSERT INTO cognition.decision_records" in sql:
            self.insert_attempts += 1
            if decision_id in self.records:
                return _ScalarResult(None)
            self.records[decision_id] = str(parameters["record_hash"])
            return _ScalarResult(decision_id)
        if "SELECT record_hash" in sql:
            return _ScalarResult(self.records.get(decision_id))
        raise AssertionError(f"unexpected_sql:{sql}")


def _request(**overrides: object) -> DecisionRequest:
    values: dict[str, object] = {
        "request_id": "decision-request-1",
        "decision_kind": DecisionKind.INTERPRETATION,
        "subject_ref": "case:test",
        "evidence_refs": ("evidence:1",),
        "candidates": (),
        "llm_allowed": False,
        "human_required": False,
        "correlation_id": "correlation-1",
        "causation_id": "cause-1",
    }
    values.update(overrides)
    return DecisionRequest(**values)


def test_system_resolves_deterministic_fact_before_llm() -> None:
    route = DecisionRouter().route(
        _request(
            decision_kind=DecisionKind.FACT,
            deterministic_result={"pillar": "甲子"},
            llm_allowed=True,
        )
    )
    assert route.status is DecisionRouteStatus.RESOLVED
    assert route.authority is DecisionAuthority.SYSTEM
    assert route.result == {"pillar": "甲子"}


def test_world_outcome_cannot_fall_through_to_llm() -> None:
    route = DecisionRouter().route(
        _request(
            decision_kind=DecisionKind.WORLD_OUTCOME,
            candidates=(
                DecisionCandidate(candidate_ref="outcome:a"),
                DecisionCandidate(candidate_ref="outcome:b"),
            ),
            llm_allowed=True,
        )
    )
    assert route.status is DecisionRouteStatus.UNRESOLVED
    assert route.authority is DecisionAuthority.SYSTEM


def test_one_rule_qualified_candidate_is_system_selected() -> None:
    route = DecisionRouter().route(
        _request(
            candidates=(
                DecisionCandidate(candidate_ref="path:a", qualified=False),
                DecisionCandidate(candidate_ref="path:b", qualified=True),
            )
        )
    )
    assert route.status is DecisionRouteStatus.RESOLVED
    assert route.authority is DecisionAuthority.RULE_ENGINE
    assert route.selected_candidate_ref == "path:b"


def test_competing_interpretations_route_to_bounded_llm() -> None:
    route = DecisionRouter().route(
        _request(
            candidates=(
                DecisionCandidate(candidate_ref="path:a"),
                DecisionCandidate(candidate_ref="path:b"),
            ),
            llm_allowed=True,
        )
    )
    assert route.status is DecisionRouteStatus.PENDING
    assert route.authority is DecisionAuthority.LLM_REASONER


def test_human_consent_never_routes_to_llm() -> None:
    route = DecisionRouter().route(
        _request(
            decision_kind=DecisionKind.HUMAN_CONSENT,
            candidates=(DecisionCandidate(candidate_ref="consent:yes"),),
            llm_allowed=True,
        )
    )
    assert route.status is DecisionRouteStatus.PENDING
    assert route.authority is DecisionAuthority.HUMAN


def test_missing_evidence_remains_unresolved() -> None:
    route = DecisionRouter().route(_request())
    assert route.status is DecisionRouteStatus.UNRESOLVED
    assert route.authority is DecisionAuthority.NONE


def test_decision_ledger_persists_once_and_replays_exact_record() -> None:
    connection = _MemoryDecisionConnection()
    ledger = CognitiveDecisionLedger()
    request = _request(
        decision_kind=DecisionKind.WORLD_OUTCOME,
        deterministic_result={"outcome_ref": "world-event:1"},
    )

    first = ledger.route_and_record(connection=connection, request=request)
    replay = ledger.route_and_record(connection=connection, request=request)

    assert first.decision_id == replay.decision_id
    assert first.record_hash == replay.record_hash
    assert first.already_recorded is False
    assert replay.already_recorded is True
    assert connection.insert_attempts == 2
    assert connection.records == {first.decision_id: first.record_hash}


def test_decision_ledger_rejects_same_identity_with_changed_payload() -> None:
    connection = _MemoryDecisionConnection()
    ledger = CognitiveDecisionLedger()
    first = _request(
        decision_kind=DecisionKind.DOMAIN_INFERENCE,
        deterministic_result={"result": "SUPPORTED"},
    )
    changed = _request(
        decision_kind=DecisionKind.DOMAIN_INFERENCE,
        deterministic_result={"result": "NOT_SUPPORTED"},
    )

    ledger.route_and_record(connection=connection, request=first)

    with pytest.raises(DecisionLedgerError, match="decision_record_conflict"):
        ledger.route_and_record(connection=connection, request=changed)
