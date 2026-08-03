from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from abu_v60.db import engine
from abu_v60.db.schema import mingli_synthetic_suite_runs
from abu_v60.mingli.synthetic_experiment_catalog import (
    HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
    HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
    resolve_synthetic_experiment,
)
from abu_v60.mingli.synthetic_suite_catalog import (
    HIDDEN_RANK_DEV_SUITE,
    HIDDEN_RANK_DEV_SUITE_REF,
    SYNTHETIC_SUITE_MODE_CATALOG,
    SyntheticSuiteDefinition,
)
from abu_v60.mingli.synthetic_suite_contracts import (
    SYNTHETIC_SUITE_RUN_VERSION,
    SyntheticSuiteCandidateIdentity,
    SyntheticSuiteErrorCluster,
    SyntheticSuiteRunIdentity,
    SyntheticSuiteRunItem,
    SyntheticSuiteVariantReview,
    derive_error_clusters,
    derive_suite_counts,
)
from abu_v60.mingli.synthetic_suite_service import (
    SyntheticSuiteService,
    SyntheticSuiteServiceError,
)
from abu_v60.mingli.synthetic_suite_store import MingliSyntheticSuiteRunStore
from abu_v60.provenance import content_hash, stable_ref
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError


def _candidate(*, prompt_hash: str = "8" * 64) -> SyntheticSuiteCandidateIdentity:
    return SyntheticSuiteCandidateIdentity(
        agent_profile_ref="agent-profile:test",
        agent_profile_hash="1" * 64,
        provider_id="test-provider",
        model_ref="test-model",
        model_digest="2" * 64,
        provider_profile_ref="provider-profile:test",
        provider_profile_hash="3" * 64,
        prompt_ref="prompt:test",
        prompt_hash=prompt_hash,
        agent_reading_version="v60.mingli-agent-reading.005",
    )


def _sealed_item(
    *,
    position: int,
    experiment_ref: str,
    reason_keys: tuple[str, ...] = (),
) -> SyntheticSuiteRunItem:
    definition = resolve_synthetic_experiment(experiment_ref).public_definition()
    variant_reviews = (
        SyntheticSuiteVariantReview(
            variant="A",
            reason_keys=reason_keys,
        ),
        SyntheticSuiteVariantReview(
            variant="B",
            reason_keys=reason_keys,
        ),
    )
    return SyntheticSuiteRunItem(
        position=position,
        experiment_ref=experiment_ref,
        definition_hash=str(definition["definition_hash"]),
        execution_status="SEALED",
        experiment_run_ref=f"experiment-run:{position}",
        experiment_run_hash=str(position) * 64,
        outcome="PASS",
        evaluator_version="v60.mingli-synthetic-experiment-evaluator.005",
        dev_gold_version="v60.mingli-synthetic-experiment-dev-gold.004",
        dev_gold_hash="4" * 64,
        model_independence="FAIL" if reason_keys else "PASS",
        changed_pass_count=3,
        hold_pass_count=3,
        review_contract_status="CURRENT",
        review_required=bool(reason_keys),
        review_reason_keys=reason_keys,
        variant_reviews=variant_reviews,
        error_code=None,
    )


def _error_item(*, position: int, experiment_ref: str) -> SyntheticSuiteRunItem:
    definition = resolve_synthetic_experiment(experiment_ref).public_definition()
    reason = "RUNNER_ERROR:TEST_BOUNDED_FAILURE"
    return SyntheticSuiteRunItem(
        position=position,
        experiment_ref=experiment_ref,
        definition_hash=str(definition["definition_hash"]),
        execution_status="ERROR",
        review_required=True,
        review_reason_keys=(reason,),
        variant_reviews=(),
        error_code="TEST_BOUNDED_FAILURE",
    )


def test_hidden_rank_dev_suite_seals_order_mode_and_bridge() -> None:
    definition = HIDDEN_RANK_DEV_SUITE.public_definition()
    identity = {key: value for key, value in definition.items() if key != "suite_definition_hash"}
    assert definition["suite_definition_hash"] == content_hash(identity)
    assert HIDDEN_RANK_DEV_SUITE.experiment_refs == (
        HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
        HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
    )
    first = resolve_synthetic_experiment(HIDDEN_RANK_DEV_SUITE.experiment_refs[0])
    second = resolve_synthetic_experiment(HIDDEN_RANK_DEV_SUITE.experiment_refs[1])
    assert first.member_by_variant["B"].birth_input == second.member_by_variant["A"].birth_input
    assert first.member_by_variant["B"].expected_pillars == (
        "庚申",
        "辛巳",
        "乙巳",
        "庚辰",
    )
    assert first.member_by_variant["B"].expected_pillars == (
        second.member_by_variant["A"].expected_pillars
    )
    assert {item["mode"]: item["availability"] for item in SYNTHETIC_SUITE_MODE_CATALOG} == {
        "DEV": "ACTIVE",
        "QUALIFICATION": "LOCKED_OWNER_GATE",
        "HOLDOUT": "LOCKED_OWNER_GATE",
    }


def test_error_clusters_count_each_variant_without_inventing_scores() -> None:
    reason = "SERVER_REPAIR:DAY_MASTER_REGIME"
    item = _sealed_item(
        position=1,
        experiment_ref=HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
        reason_keys=(reason,),
    )
    clusters = derive_error_clusters((item,))
    assert len(clusters) == 1
    assert clusters[0].key == reason
    assert clusters[0].label == "日主与根气裁决"
    assert clusters[0].occurrence_count == 2
    assert clusters[0].experiment_count == 1
    assert clusters[0].member_occurrences == (
        f"{item.experiment_ref}:A",
        f"{item.experiment_ref}:B",
    )
    hypothesis = _sealed_item(
        position=1,
        experiment_ref=HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
        reason_keys=("SERVER_REPAIR:HYPOTHESIS_H1",),
    )
    assert derive_error_clusters((hypothesis,))[0].label == "假设结构归槽"
    counts, outcomes = derive_suite_counts((hypothesis,))
    legacy_label = SyntheticSuiteErrorCluster(
        **{
            **derive_error_clusters((hypothesis,))[0].model_dump(),
            "label": "训练运行未完成",
        }
    )
    SyntheticSuiteRunIdentity(
        suite_run_version=SYNTHETIC_SUITE_RUN_VERSION,
        suite_ref="suite:historical-label",
        suite_definition_hash="6" * 64,
        suite_mode="DEV",
        runner_version="v60.mingli-synthetic-suite-runner.001",
        candidate_identity=_candidate(),
        status="COMPLETED",
        items=(hypothesis,),
        counts=counts,
        outcomes=outcomes,
        error_clusters=(legacy_label,),
        qualification_effect="DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION",
    )


def test_runner_continues_bounded_error_and_seals_honest_counts(monkeypatch: Any) -> None:
    calls: list[str] = []

    class _Experiments:
        def run_experiment(self, *, experiment_ref: str) -> dict[str, Any]:
            calls.append(experiment_ref)
            if len(calls) == 1:
                raise ValueError("provider_timeout:https://must-not-leak.example")
            return {"experiment_ref": experiment_ref}

    class _SuiteRuns:
        def ensure(self, *, identity: SyntheticSuiteRunIdentity) -> dict[str, Any]:
            payload = identity.model_dump(mode="json")
            return {
                "suite_run_ref": stable_ref("test-suite-run", payload),
                "suite_run_hash": content_hash(payload),
                "created_at": datetime.now(UTC),
                **payload,
            }

    service = SyntheticSuiteService(  # type: ignore[arg-type]
        engine,
        experiment_service=_Experiments(),
        candidate_identity=_candidate(),
    )
    service._suite_runs = _SuiteRuns()  # type: ignore[assignment]
    monkeypatch.setattr(
        service,
        "_sealed_item",
        lambda *, position, expected_experiment_ref, run: (
            _sealed_item(
                position=position,
                experiment_ref=expected_experiment_ref,
            ),
            _candidate(),
        ),
    )
    monkeypatch.setattr(service, "_validate_run_bindings", lambda **_: None)
    progress: list[tuple[str, int, int, str]] = []
    run = service.run_suite(
        suite_ref=HIDDEN_RANK_DEV_SUITE_REF,
        progress=lambda *event: progress.append(event),
    )

    assert calls == list(HIDDEN_RANK_DEV_SUITE.experiment_refs)
    assert [event[0] for event in progress] == ["START", "ERROR", "START", "SEALED"]
    assert run["status"] == "COMPLETED_WITH_ERRORS"
    assert run["counts"] == {
        "experiments": 2,
        "sealed": 1,
        "runner_errors": 1,
        "review_required": 1,
    }
    assert run["items"][0]["error_code"] == "PROVIDER_TIMEOUT"
    assert "must-not-leak" not in str(run)


def test_locked_suite_rejects_before_any_experiment_runs(monkeypatch: Any) -> None:
    locked = SyntheticSuiteDefinition(
        suite_ref="suite:locked-holdout",
        mode="HOLDOUT",
        availability="LOCKED_OWNER_GATE",
        title="locked",
        question="locked",
        experiment_refs=HIDDEN_RANK_DEV_SUITE.experiment_refs,
        execution_policy="LOCKED",
        inference_limit="locked",
    )
    calls: list[str] = []
    experiments = SimpleNamespace(
        run_experiment=lambda **kwargs: calls.append(kwargs["experiment_ref"])
    )
    service = SyntheticSuiteService(engine, experiment_service=experiments)
    monkeypatch.setattr(
        "abu_v60.mingli.synthetic_suite_service.resolve_synthetic_suite",
        lambda _: locked,
    )
    with pytest.raises(SyntheticSuiteServiceError, match="mingli_synthetic_suite_mode_locked"):
        service.run_suite(suite_ref=locked.suite_ref)
    assert calls == []


def test_candidate_drift_aborts_suite_instead_of_mixing_results(monkeypatch: Any) -> None:
    class _Experiments:
        def run_experiment(self, *, experiment_ref: str) -> dict[str, Any]:
            return {"experiment_ref": experiment_ref}

    service = SyntheticSuiteService(  # type: ignore[arg-type]
        engine,
        experiment_service=_Experiments(),
        candidate_identity=_candidate(prompt_hash="1" * 64),
    )
    monkeypatch.setattr(
        service,
        "_sealed_item",
        lambda *, position, expected_experiment_ref, run: (
            _sealed_item(position=position, experiment_ref=expected_experiment_ref),
            _candidate(prompt_hash=str(position) * 64),
        ),
    )
    with pytest.raises(
        SyntheticSuiteServiceError,
        match="mingli_synthetic_suite_candidate_identity_mismatch",
    ):
        service.run_suite(suite_ref=HIDDEN_RANK_DEV_SUITE_REF)


def test_all_error_suite_identity_still_binds_attempted_candidate() -> None:
    items = (
        _error_item(
            position=1,
            experiment_ref=HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
        ),
        _error_item(
            position=2,
            experiment_ref=HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
        ),
    )
    counts, outcomes = derive_suite_counts(items)

    def identity(prompt_hash: str) -> SyntheticSuiteRunIdentity:
        return SyntheticSuiteRunIdentity(
            suite_run_version=SYNTHETIC_SUITE_RUN_VERSION,
            suite_ref=HIDDEN_RANK_DEV_SUITE_REF,
            suite_definition_hash="7" * 64,
            suite_mode="DEV",
            runner_version="v60.mingli-synthetic-suite-runner.002",
            candidate_identity=_candidate(prompt_hash=prompt_hash),
            status="COMPLETED_WITH_ERRORS",
            items=items,
            counts=counts,
            outcomes=outcomes,
            error_clusters=derive_error_clusters(items),
            qualification_effect="DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION",
        )

    first = identity("1" * 64).model_dump(mode="json")
    second = identity("2" * 64).model_dump(mode="json")
    assert stable_ref("v60-mingli-synthetic-suite-run", first) != stable_ref(
        "v60-mingli-synthetic-suite-run", second
    )
    with pytest.raises(
        ValueError,
        match="mingli_synthetic_suite_attempted_candidate_required",
    ):
        SyntheticSuiteRunIdentity(
            **{
                **first,
                "candidate_identity": None,
            }
        )


def test_invalid_child_binding_never_reaches_append_only_store() -> None:
    class _WrongExperiment:
        def run_experiment(self, *, experiment_ref: str) -> dict[str, Any]:
            del experiment_ref
            return {"experiment_ref": "experiment:wrong", "definition_hash": "0" * 64}

    class _NeverStore:
        ensure_calls = 0

        def ensure(self, *, identity: SyntheticSuiteRunIdentity) -> dict[str, Any]:
            del identity
            self.ensure_calls += 1
            return {}

    service = SyntheticSuiteService(  # type: ignore[arg-type]
        engine,
        experiment_service=_WrongExperiment(),
        candidate_identity=_candidate(),
    )
    store = _NeverStore()
    service._suite_runs = store  # type: ignore[assignment]
    with pytest.raises(
        SyntheticSuiteServiceError,
        match="mingli_synthetic_suite_child_experiment_mismatch",
    ):
        service.run_suite(suite_ref=HIDDEN_RANK_DEV_SUITE_REF)
    assert store.ensure_calls == 0


def test_public_suite_projection_marks_old_review_contract_superseded() -> None:
    item = _sealed_item(
        position=1,
        experiment_ref=HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
    ).model_copy(update={"evaluator_version": "v60.mingli-synthetic-experiment-evaluator.004"})
    sealed_payload = {
        "suite_run_version": "v60.mingli-synthetic-suite-run.001",
        "suite_ref": "suite:test",
        "suite_definition_hash": "4" * 64,
        "suite_mode": "DEV",
        "runner_version": "v60.mingli-synthetic-suite-runner.001",
        "candidate_identity": _candidate().model_dump(mode="json"),
        "status": "COMPLETED",
        "items": [item.model_dump(mode="json")],
        "counts": {
            "experiments": 1,
            "sealed": 1,
            "runner_errors": 0,
            "review_required": 0,
        },
        "outcomes": {
            "PASS": 1,
            "PRODUCT_SAFE_MODEL_FAIL": 0,
            "MODEL_FAIL": 0,
            "INVALID_EXPERIMENT": 0,
        },
        "error_clusters": [],
        "qualification_effect": "DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION",
    }
    projected = SyntheticSuiteService(engine)._public_run(
        {
            "created_at": datetime.now(UTC),
            "suite_run_ref": stable_ref("v60-mingli-synthetic-suite-run", sealed_payload),
            "suite_run_hash": content_hash(sealed_payload),
            **sealed_payload,
        }
    )
    review = projected["current_review_projection"]

    assert projected["items"] == sealed_payload["items"]
    assert projected["counts"] == sealed_payload["counts"]
    assert projected["error_clusters"] == sealed_payload["error_clusters"]
    assert projected["suite_run_hash"] == content_hash(sealed_payload)
    assert review["items"][0]["review_contract_status"] == "SUPERSEDED"
    assert "REVIEW_CONTRACT:SUPERSEDED" in review["items"][0]["review_reason_keys"]
    assert review["error_clusters"][0]["kind"] == "CONTRACT_SUPERSEDED"
    review_identity = {
        key: value for key, value in review.items() if key != "projection_hash"
    }
    assert review["projection_hash"] == content_hash(review_identity)
    assert review["source_suite_run_ref"] == projected["suite_run_ref"]
    assert review["source_suite_run_hash"] == projected["suite_run_hash"]


def test_suite_store_metadata_idempotence_and_append_only_trigger() -> None:
    actual = {
        item["name"]
        for item in inspect(engine).get_columns("synthetic_suite_runs", schema="mingli")
    }
    assert actual == set(mingli_synthetic_suite_runs.c.keys())
    items = (
        _error_item(
            position=1,
            experiment_ref=HIDDEN_RANK_PRIMARY_SECONDARY_EXPERIMENT_REF,
        ),
        _error_item(
            position=2,
            experiment_ref=HIDDEN_RANK_SECONDARY_TERTIARY_EXPERIMENT_REF,
        ),
    )
    counts, outcomes = derive_suite_counts(items)
    identity = SyntheticSuiteRunIdentity(
        suite_run_version=SYNTHETIC_SUITE_RUN_VERSION,
        suite_ref="v60-test-suite-append-only",
        suite_definition_hash="7" * 64,
        suite_mode="DEV",
        runner_version="v60.mingli-synthetic-suite-runner.001",
        candidate_identity=_candidate(),
        status="COMPLETED_WITH_ERRORS",
        items=items,
        counts=counts,
        outcomes=outcomes,
        error_clusters=derive_error_clusters(items),
        qualification_effect="DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION",
    )
    store = MingliSyntheticSuiteRunStore(engine)
    first = store.ensure(identity=identity)
    replay = store.ensure(identity=identity)
    assert replay["suite_run_ref"] == first["suite_run_ref"]
    assert replay["suite_run_hash"] == first["suite_run_hash"]
    with pytest.raises(DBAPIError), engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE mingli.synthetic_suite_runs "
                "SET status = 'COMPLETED' WHERE suite_run_ref = :run_ref"
            ),
            {"run_ref": first["suite_run_ref"]},
        )
    with pytest.raises(DBAPIError), engine.begin() as connection:
        connection.execute(
            text("DELETE FROM mingli.synthetic_suite_runs WHERE suite_run_ref = :run_ref"),
            {"run_ref": first["suite_run_ref"]},
        )
    assert store.get(suite_run_ref=first["suite_run_ref"]) is not None
