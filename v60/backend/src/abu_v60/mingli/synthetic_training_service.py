from __future__ import annotations

import re
from collections.abc import Mapping
from threading import Lock
from typing import Any

from sqlalchemy.engine import Engine

from abu_v60.mingli.agent_runtime import (
    MingliAgentRuntime,
    MingliAgentRuntimeError,
    configured_mingli_agent_runtime,
)
from abu_v60.mingli.synthetic_experiment_catalog import (
    SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION,
    resolve_synthetic_experiment,
)
from abu_v60.mingli.synthetic_experiment_gold import synthetic_experiment_dev_gold
from abu_v60.mingli.synthetic_experiment_service import SyntheticExperimentService
from abu_v60.mingli.synthetic_suite_catalog import (
    SYNTHETIC_SUITE_RUNNER_VERSION,
    SYNTHETIC_SUITES,
    SyntheticSuiteDefinition,
    resolve_synthetic_suite,
)
from abu_v60.mingli.synthetic_suite_contracts import SyntheticSuiteCandidateIdentity
from abu_v60.mingli.synthetic_suite_service import (
    SyntheticSuiteService,
    SyntheticSuiteServiceError,
)
from abu_v60.mingli.synthetic_training_contracts import (
    SYNTHETIC_TRAINING_STATUS_VERSION,
    SyntheticSuiteRunRequestInput,
    SyntheticSuiteRunRequestProjection,
    synthetic_training_execution_fingerprint,
)
from abu_v60.mingli.synthetic_training_store import (
    MingliSyntheticTrainingStore,
    SyntheticTrainingStoreError,
)
from abu_v60.provenance import content_hash


class SyntheticTrainingServiceError(ValueError):
    pass


class SyntheticTrainingService:
    """Bind one server-owned candidate to a recoverable DEV Suite request."""

    def __init__(
        self,
        engine: Engine,
        *,
        runtime: MingliAgentRuntime | None = None,
        store: MingliSyntheticTrainingStore | None = None,
    ) -> None:
        self._engine = engine
        self._runtime = runtime or configured_mingli_agent_runtime()
        self._store = store or MingliSyntheticTrainingStore(engine)
        self._run_lock = Lock()

    def status(self, *, requester_account_ref: str) -> dict[str, Any]:
        candidate = self._candidate()
        candidate_hash = content_hash(candidate.model_dump(mode="json"))
        suite_service = SyntheticSuiteService(self._engine)
        catalog = suite_service.catalog()
        catalog_by_ref = {item["suite_ref"]: item for item in catalog["suites"]}
        suites = []
        for suite in SYNTHETIC_SUITES:
            if suite.mode != "DEV" or suite.availability != "ACTIVE":
                continue
            definition = suite.public_definition()
            execution_fingerprint = self._execution_fingerprint(
                suite=suite,
                candidate_hash=candidate_hash,
            )
            entry = catalog_by_ref.get(suite.suite_ref, {"runs": []})
            sealed = next(
                (
                    run
                    for run in entry.get("runs", [])
                    if self._run_matches_execution(
                        suite=suite,
                        run=run,
                        candidate=candidate,
                    )
                ),
                None,
            )
            suites.append(
                {
                    "suite_ref": suite.suite_ref,
                    "suite_definition_hash": definition["suite_definition_hash"],
                    "title": suite.title,
                    "question": suite.question,
                    "experiment_count": len(suite.experiment_refs),
                    "execution_fingerprint": execution_fingerprint,
                    "candidate_state": (
                        "CURRENT_CANDIDATE_ALREADY_SEALED"
                        if sealed is not None
                        else "READY_FOR_DEV_RUN"
                    ),
                    "sealed_suite_run_ref": (
                        sealed["suite_run_ref"] if sealed is not None else None
                    ),
                    "sealed_suite_run_hash": (
                        sealed["suite_run_hash"] if sealed is not None else None
                    ),
                }
            )
        recommended = next(
            (
                item
                for item in reversed(suites)
                if item["candidate_state"] == "READY_FOR_DEV_RUN"
            ),
            suites[-1] if suites else None,
        )
        latest = self._store.latest(requester_account_ref=requester_account_ref)
        return {
            "status_version": SYNTHETIC_TRAINING_STATUS_VERSION,
            "server_run_request_allowed": True,
            "browser_direct_model_call_allowed": False,
            "candidate_identity": candidate.model_dump(mode="json"),
            "candidate_identity_hash": candidate_hash,
            "suites": suites,
            "recommended_suite_ref": recommended["suite_ref"] if recommended else None,
            "latest_request": self._project(latest) if latest is not None else None,
            "qualification_effect": "DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION",
        }

    def create_request(
        self,
        *,
        requester_account_ref: str,
        payload: SyntheticSuiteRunRequestInput,
    ) -> SyntheticSuiteRunRequestProjection:
        suite = self._active_suite(payload.suite_ref)
        definition = suite.public_definition()
        candidate = self._candidate()
        candidate_hash = content_hash(candidate.model_dump(mode="json"))
        execution_fingerprint = self._execution_fingerprint(
            suite=suite,
            candidate_hash=candidate_hash,
        )
        if (
            payload.expected_suite_definition_hash != definition["suite_definition_hash"]
            or payload.expected_execution_fingerprint != execution_fingerprint
        ):
            raise SyntheticTrainingServiceError("mingli_synthetic_training_preflight_conflict")
        replay = self._store.by_idempotency(
            requester_account_ref=requester_account_ref,
            idempotency_key=payload.idempotency_key,
        )
        if replay is not None:
            if (
                replay["suite_ref"] != suite.suite_ref
                or replay["execution_fingerprint"] != execution_fingerprint
            ):
                raise SyntheticTrainingServiceError(
                    "mingli_synthetic_training_idempotency_conflict"
                )
            return self._project(replay)
        if self._matching_run(suite=suite, candidate=candidate) is not None:
            raise SyntheticTrainingServiceError(
                "mingli_synthetic_training_current_candidate_already_sealed"
            )
        try:
            stored = self._store.ensure_queued(
                requester_account_ref=requester_account_ref,
                suite_ref=suite.suite_ref,
                suite_definition_hash=str(definition["suite_definition_hash"]),
                candidate_identity=candidate,
                execution_fingerprint=execution_fingerprint,
                idempotency_key=payload.idempotency_key,
                total_count=len(suite.experiment_refs),
            )
        except SyntheticTrainingStoreError as exc:
            raise SyntheticTrainingServiceError(str(exc)) from exc
        return self._project(stored)

    def get_request(
        self,
        *,
        requester_account_ref: str,
        request_ref: str,
    ) -> SyntheticSuiteRunRequestProjection:
        stored = self._store.get(
            request_ref=request_ref,
            requester_account_ref=requester_account_ref,
        )
        if stored is None:
            raise SyntheticTrainingServiceError("mingli_synthetic_training_request_not_found")
        return self._project(stored)

    def run_request(self, *, request_ref: str) -> None:
        with self._run_lock:
            stored = self._store.get(request_ref=request_ref)
            if stored is None or stored["status"] != "QUEUED":
                return
            if not self._store.claim(request_ref=request_ref):
                return
            try:
                candidate = SyntheticSuiteCandidateIdentity.model_validate(
                    stored["candidate_identity_json"]
                )
                current_candidate = self._candidate()
                if candidate != current_candidate:
                    raise SyntheticTrainingServiceError("mingli_synthetic_training_candidate_drift")
                suite = self._active_suite(str(stored["suite_ref"]))
                definition = suite.public_definition()
                if definition["suite_definition_hash"] != stored["suite_definition_hash"]:
                    raise SyntheticTrainingServiceError("mingli_synthetic_training_suite_drift")
                candidate_hash = content_hash(candidate.model_dump(mode="json"))
                current_execution_fingerprint = self._execution_fingerprint(
                    suite=suite,
                    candidate_hash=candidate_hash,
                )
                if (
                    stored["candidate_identity_hash"] != candidate_hash
                    or stored["execution_fingerprint"] != current_execution_fingerprint
                ):
                    raise SyntheticTrainingServiceError(
                        "mingli_synthetic_training_execution_drift"
                    )
                experiment_service = SyntheticExperimentService(
                    self._engine,
                    runtime=self._runtime,
                )
                runner = SyntheticSuiteService(
                    self._engine,
                    experiment_service=experiment_service,
                    candidate_identity=candidate,
                )
                run = runner.run_suite(
                    suite_ref=suite.suite_ref,
                    progress=lambda event, position, total, experiment_ref: (
                        self._store.record_progress(
                            request_ref=request_ref,
                            event=event,
                            position=position,
                            total=total,
                            experiment_ref=experiment_ref,
                        )
                    ),
                )
                self._store.mark_sealing(request_ref=request_ref)
                self._store.succeed(
                    request_ref=request_ref,
                    suite_run_ref=str(run["suite_run_ref"]),
                    suite_run_hash=str(run["suite_run_hash"]),
                    review_disposition=_review_disposition(run),
                )
            except Exception as exc:  # noqa: BLE001 - persisted bounded failure state
                self._store.fail(
                    request_ref=request_ref,
                    error_code=_bounded_training_error(exc),
                )

    def _candidate(self) -> SyntheticSuiteCandidateIdentity:
        try:
            return SyntheticSuiteCandidateIdentity.model_validate(
                self._runtime.candidate_identity()
            )
        except (MingliAgentRuntimeError, ValueError) as exc:
            raise SyntheticTrainingServiceError(str(exc)) from exc

    @staticmethod
    def _active_suite(suite_ref: str) -> SyntheticSuiteDefinition:
        try:
            suite = resolve_synthetic_suite(suite_ref)
        except ValueError as exc:
            raise SyntheticTrainingServiceError(str(exc)) from exc
        if suite.mode != "DEV" or suite.availability != "ACTIVE":
            raise SyntheticTrainingServiceError("mingli_synthetic_suite_mode_locked")
        return suite

    def _matching_run(
        self,
        *,
        suite: SyntheticSuiteDefinition,
        candidate: SyntheticSuiteCandidateIdentity,
    ) -> Mapping[str, Any] | None:
        entry = SyntheticSuiteService(self._engine).catalog()
        suite_entry = next(
            (item for item in entry["suites"] if item["suite_ref"] == suite.suite_ref),
            None,
        )
        if suite_entry is None:
            return None
        return next(
            (
                run
                for run in suite_entry["runs"]
                if self._run_matches_execution(
                    suite=suite,
                    run=run,
                    candidate=candidate,
                )
            ),
            None,
        )

    @staticmethod
    def _run_matches_execution(
        *,
        suite: SyntheticSuiteDefinition,
        run: Mapping[str, Any],
        candidate: SyntheticSuiteCandidateIdentity,
    ) -> bool:
        if (
            run.get("suite_definition_hash") != suite.public_definition()["suite_definition_hash"]
            or run.get("runner_version") != SYNTHETIC_SUITE_RUNNER_VERSION
            or run.get("candidate_identity") != candidate.model_dump(mode="json")
        ):
            return False
        current_contracts = {
            experiment_ref: _experiment_contract(experiment_ref)
            for experiment_ref in suite.experiment_refs
        }
        items = run.get("items", [])
        if (
            not isinstance(items, list)
            or tuple(item.get("experiment_ref") for item in items if isinstance(item, Mapping))
            != suite.experiment_refs
        ):
            return False
        return all(
            isinstance(item, Mapping)
            and item.get("execution_status") == "SEALED"
            and item.get("evaluator_version")
            == current_contracts[str(item["experiment_ref"])]["evaluator_version"]
            and item.get("dev_gold_version")
            == current_contracts[str(item["experiment_ref"])]["dev_gold_version"]
            and item.get("dev_gold_hash")
            == current_contracts[str(item["experiment_ref"])]["dev_gold_hash"]
            for item in items
        )

    @staticmethod
    def _execution_fingerprint(
        *,
        suite: SyntheticSuiteDefinition,
        candidate_hash: str,
    ) -> str:
        definition = suite.public_definition()
        return synthetic_training_execution_fingerprint(
            suite_definition_hash=str(definition["suite_definition_hash"]),
            candidate_identity_hash=candidate_hash,
            runner_version=SYNTHETIC_SUITE_RUNNER_VERSION,
            experiment_contracts=tuple(
                _experiment_contract(experiment_ref) for experiment_ref in suite.experiment_refs
            ),
        )

    @staticmethod
    def _project(stored: Mapping[str, Any]) -> SyntheticSuiteRunRequestProjection:
        identity = {
            "request_version": stored["request_version"],
            "request_ref": stored["request_ref"],
            "request_hash": stored["request_hash"],
            "suite_ref": stored["suite_ref"],
            "suite_definition_hash": stored["suite_definition_hash"],
            "candidate_identity": stored["candidate_identity_json"],
            "candidate_identity_hash": stored["candidate_identity_hash"],
            "execution_fingerprint": stored["execution_fingerprint"],
            "status": stored["status"],
            "progress_event": stored["progress_event"],
            "current_position": stored["current_position"],
            "completed_count": stored["completed_count"],
            "total_count": stored["total_count"],
            "current_experiment_ref": stored["current_experiment_ref"],
            "suite_run_ref": stored["suite_run_ref"],
            "suite_run_hash": stored["suite_run_hash"],
            "review_disposition": stored["review_disposition"],
            "error_code": stored["error_code"],
            "created_at": stored["created_at"],
            "updated_at": stored["updated_at"],
        }
        return SyntheticSuiteRunRequestProjection(
            **identity,
            projection_hash=content_hash(
                {
                    **identity,
                    "candidate_identity": stored["candidate_identity_json"],
                    "created_at": stored["created_at"].isoformat(),
                    "updated_at": stored["updated_at"].isoformat(),
                }
            ),
        )


def _experiment_contract(experiment_ref: str) -> dict[str, str]:
    definition = resolve_synthetic_experiment(experiment_ref).public_definition()
    gold, gold_hash = synthetic_experiment_dev_gold(experiment_ref)
    return {
        "experiment_ref": experiment_ref,
        "definition_hash": str(definition["definition_hash"]),
        "evaluator_version": SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION,
        "dev_gold_version": str(gold["gold_version"]),
        "dev_gold_hash": gold_hash,
    }


def _review_disposition(run: Mapping[str, Any]) -> str:
    counts = run.get("counts", {})
    if counts.get("runner_errors", 0):
        return "EXECUTION_REPAIR_REQUIRED"
    if any(item.get("outcome") == "INVALID_EXPERIMENT" for item in run.get("items", [])):
        return "EXPERIMENT_REVISION_REQUIRED"
    if counts.get("review_required", 0) or run.get("error_clusters"):
        return "CANDIDATE_REVISION_REQUIRED"
    return "MODEL_INDEPENDENT_DEV"


_SAFE_ERROR = re.compile(r"^[A-Za-z0-9_]+$")


def _bounded_training_error(error: Exception) -> str:
    candidate = str(error).split(":", 1)[0].strip()
    if candidate and _SAFE_ERROR.fullmatch(candidate):
        return candidate.upper()[:160]
    if isinstance(error, SyntheticSuiteServiceError):
        return "SYNTHETIC_SUITE_SERVICE_ERROR"
    return "UNEXPECTED_TRAINING_ERROR"
