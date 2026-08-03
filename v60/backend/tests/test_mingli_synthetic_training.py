from __future__ import annotations

import pytest
from abu_v60.db import engine
from abu_v60.db.schema import mingli_synthetic_suite_run_requests
from abu_v60.mingli.agent_root_gate import packet_root_candidate_assessments
from abu_v60.mingli.synthetic_experiment_catalog import (
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT,
)
from abu_v60.mingli.synthetic_experiment_seed import seed_synthetic_experiment
from abu_v60.mingli.synthetic_experiment_service import SyntheticExperimentService
from abu_v60.mingli.synthetic_suite_catalog import (
    CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_SUITE,
    HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_SUITE,
    HIDDEN_RANK_DEV_SUITE,
    REGIME_WORK_PATH_GENERALIZATION_DEV_SUITE,
)
from abu_v60.mingli.synthetic_suite_contracts import SyntheticSuiteCandidateIdentity
from abu_v60.mingli.synthetic_suite_service import SyntheticSuiteService
from abu_v60.mingli.synthetic_training_contracts import SyntheticSuiteRunRequestInput
from abu_v60.mingli.synthetic_training_service import (
    SyntheticTrainingService,
    SyntheticTrainingServiceError,
    _bounded_training_error,
)
from abu_v60.mingli.synthetic_training_store import MingliSyntheticTrainingStore
from sqlalchemy import inspect, text


class _Runtime:
    def __init__(self, candidate: SyntheticSuiteCandidateIdentity) -> None:
        self._candidate = candidate

    def candidate_identity(self) -> dict[str, object]:
        return self._candidate.model_dump(mode="json")


def _candidate(seed: str = "1") -> SyntheticSuiteCandidateIdentity:
    return SyntheticSuiteCandidateIdentity(
        agent_profile_ref=f"agent-profile:{seed}",
        agent_profile_hash=seed * 64,
        provider_id="test-provider",
        model_ref=f"test-model:{seed}",
        model_digest="2" * 64,
        provider_profile_ref=f"provider-profile:{seed}",
        provider_profile_hash="3" * 64,
        prompt_ref=f"prompt:{seed}",
        prompt_hash="4" * 64,
        agent_reading_version="v60.mingli-agent-reading.005",
    )


def _delete_request(request_ref: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM mingli.synthetic_suite_run_requests
                WHERE request_ref = :request_ref
                """
            ),
            {"request_ref": request_ref},
        )


def test_cross_day_master_pair_is_real_calendar_bound_and_method_narrow() -> None:
    experiment = HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_EXPERIMENT
    seeded = seed_synthetic_experiment(engine, experiment_ref=experiment.experiment_ref)
    by_case = {item["case_ref"]: item for item in seeded["members"]}
    service = SyntheticExperimentService(engine)
    expected = {
        "A": ("庚辰", "己卯", "丙子", "癸巳"),
        "B": ("庚辰", "己卯", "丙子", "庚寅"),
    }
    expected_gate = {"A": "PRESENT", "B": "NOT_DETERMINED"}
    expected_rank = {"A": "PRIMARY_QI", "B": "SECONDARY_QI"}

    for member in experiment.members:
        materialized = by_case[member.case_ref]
        packet = service._packet(
            case_ref=member.case_ref,
            reading_ref=str(materialized["reading_ref"]),
        )
        assert tuple(item.pillar for item in packet.pillars) == expected[member.variant]
        assessments = packet_root_candidate_assessments(packet)
        assert len(assessments) == 1
        assert assessments[0]["coordinate"] == "hour支藏丙"
        assert assessments[0]["identity_match"] == "EXACT_DAY_MASTER"
        assert assessments[0]["hidden_rank"] == expected_rank[member.variant]
        assert assessments[0]["minimum_anti_follow_gate"] == expected_gate[member.variant]
        assert assessments[0]["relation_competition_evidence_ids"] == ()


def test_training_status_reopens_runs_when_the_evaluation_contract_changes() -> None:
    catalog = SyntheticSuiteService(engine).catalog()
    old = next(
        item for item in catalog["suites"] if item["suite_ref"] == HIDDEN_RANK_DEV_SUITE.suite_ref
    )
    current_candidate = SyntheticSuiteCandidateIdentity.model_validate(
        old["runs"][0]["candidate_identity"]
    )
    service = SyntheticTrainingService(engine, runtime=_Runtime(current_candidate))  # type: ignore[arg-type]

    status = service.status(requester_account_ref="v60-test-training-status")
    by_ref = {item["suite_ref"]: item for item in status["suites"]}

    assert by_ref[HIDDEN_RANK_DEV_SUITE.suite_ref]["candidate_state"] == "READY_FOR_DEV_RUN"
    assert (
        by_ref[HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_SUITE.suite_ref]["candidate_state"]
        == "READY_FOR_DEV_RUN"
    )
    assert status["recommended_suite_ref"] == (
        CANDIDATE_PARTITION_FALSIFIER_GENERALIZATION_DEV_SUITE.suite_ref
    )
    assert status["browser_direct_model_call_allowed"] is False


def test_training_request_is_idempotent_recoverable_and_server_candidate_bound() -> None:
    account_ref = "v60-test-synthetic-training-request"
    service = SyntheticTrainingService(engine, runtime=_Runtime(_candidate()))  # type: ignore[arg-type]
    status = service.status(requester_account_ref=account_ref)
    suite = next(
        item for item in status["suites"] if item["suite_ref"] == status["recommended_suite_ref"]
    )
    payload = SyntheticSuiteRunRequestInput(
        suite_ref=suite["suite_ref"],
        expected_suite_definition_hash=suite["suite_definition_hash"],
        expected_execution_fingerprint=suite["execution_fingerprint"],
        idempotency_key="qa:synthetic-training:recoverable",
    )
    first = service.create_request(requester_account_ref=account_ref, payload=payload)
    try:
        replay = service.create_request(requester_account_ref=account_ref, payload=payload)
        second_key = service.create_request(
            requester_account_ref=account_ref,
            payload=payload.model_copy(
                update={"idempotency_key": "qa:synthetic-training:second-click"}
            ),
        )
        exact = service.get_request(
            requester_account_ref=account_ref,
            request_ref=first.request_ref,
        )
        assert first == replay == second_key == exact
        assert first.status == "QUEUED"
        assert first.candidate_identity == _candidate()
        assert first.total_count == suite["experiment_count"]
        assert len(first.projection_hash) == 64
        with pytest.raises(
            SyntheticTrainingServiceError,
            match="mingli_synthetic_training_execution_already_active",
        ):
            service.create_request(
                requester_account_ref="another-account",
                payload=payload.model_copy(
                    update={"idempotency_key": "qa:synthetic-training:foreign-click"}
                ),
            )
        with pytest.raises(
            SyntheticTrainingServiceError,
            match="mingli_synthetic_training_request_not_found",
        ):
            service.get_request(
                requester_account_ref="another-account",
                request_ref=first.request_ref,
            )
    finally:
        _delete_request(first.request_ref)


def test_training_store_progress_and_disposition_form_one_terminal_projection() -> None:
    store = MingliSyntheticTrainingStore(engine)
    suite = HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_DEV_SUITE
    definition = suite.public_definition()
    stored = store.ensure_queued(
        requester_account_ref="v60-test-training-progress",
        suite_ref=suite.suite_ref,
        suite_definition_hash=str(definition["suite_definition_hash"]),
        candidate_identity=_candidate("5"),
        execution_fingerprint="6" * 64,
        idempotency_key="qa:synthetic-training:progress",
        total_count=1,
    )
    request_ref = str(stored["request_ref"])
    try:
        assert store.claim(request_ref=request_ref)
        store.record_progress(
            request_ref=request_ref,
            event="START",
            position=1,
            total=1,
            experiment_ref=suite.experiment_refs[0],
        )
        store.record_progress(
            request_ref=request_ref,
            event="SEALED",
            position=1,
            total=1,
            experiment_ref=suite.experiment_refs[0],
        )
        store.mark_sealing(request_ref=request_ref)
        store.succeed(
            request_ref=request_ref,
            suite_run_ref="suite-run:test",
            suite_run_hash="7" * 64,
            review_disposition="CANDIDATE_REVISION_REQUIRED",
        )
        terminal = store.get(request_ref=request_ref)
        assert terminal is not None
        assert terminal["status"] == "SUCCEEDED"
        assert terminal["completed_count"] == terminal["total_count"] == 1
        assert terminal["review_disposition"] == "CANDIDATE_REVISION_REQUIRED"
    finally:
        _delete_request(request_ref)


def test_queued_training_request_fails_when_execution_contract_drifts() -> None:
    candidate = _candidate("8")
    suite = REGIME_WORK_PATH_GENERALIZATION_DEV_SUITE
    definition = suite.public_definition()
    store = MingliSyntheticTrainingStore(engine)
    stored = store.ensure_queued(
        requester_account_ref="v60-test-training-execution-drift",
        suite_ref=suite.suite_ref,
        suite_definition_hash=str(definition["suite_definition_hash"]),
        candidate_identity=candidate,
        execution_fingerprint="9" * 64,
        idempotency_key="qa:synthetic-training:execution-drift",
        total_count=len(suite.experiment_refs),
    )
    request_ref = str(stored["request_ref"])
    service = SyntheticTrainingService(engine, runtime=_Runtime(candidate), store=store)  # type: ignore[arg-type]
    try:
        service.run_request(request_ref=request_ref)

        terminal = store.get(request_ref=request_ref)
        assert terminal is not None
        assert terminal["status"] == "FAILED"
        assert terminal["error_code"] == "MINGLI_SYNTHETIC_TRAINING_EXECUTION_DRIFT"
    finally:
        _delete_request(request_ref)


def test_schema_metadata_matches_synthetic_training_request_table() -> None:
    actual = {
        item["name"]
        for item in inspect(engine).get_columns(
            "synthetic_suite_run_requests",
            schema="mingli",
        )
    }
    assert actual == set(mingli_synthetic_suite_run_requests.c.keys())
    assert _bounded_training_error(Exception("x" * 200)) == "X" * 160
