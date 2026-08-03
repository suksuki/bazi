from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from sqlalchemy.engine import Engine

from abu_v60.mingli.agent_contracts import MingliAgentReadingEnvelope
from abu_v60.mingli.agent_store import MingliAgentReadingStore
from abu_v60.mingli.synthetic_experiment_catalog import (
    SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION,
    SYNTHETIC_RESEARCH_ACCOUNT_REF,
    resolve_synthetic_experiment,
)
from abu_v60.mingli.synthetic_experiment_contracts import (
    SyntheticExperimentEvaluation,
)
from abu_v60.mingli.synthetic_experiment_gold import synthetic_experiment_dev_gold
from abu_v60.mingli.synthetic_experiment_service import SyntheticExperimentService
from abu_v60.mingli.synthetic_experiment_store import (
    MingliSyntheticExperimentRunStore,
)
from abu_v60.mingli.synthetic_suite_catalog import (
    HIDDEN_RANK_DEV_SUITE_REF,
    SYNTHETIC_SUITE_CATALOG_VERSION,
    SYNTHETIC_SUITE_MODE_CATALOG,
    SYNTHETIC_SUITE_RUNNER_VERSION,
    SYNTHETIC_SUITES,
    SyntheticSuiteDefinition,
    resolve_synthetic_suite,
)
from abu_v60.mingli.synthetic_suite_contracts import (
    SYNTHETIC_SUITE_REVIEW_PROJECTION_VERSION,
    SYNTHETIC_SUITE_RUN_VERSION,
    SyntheticSuiteCandidateIdentity,
    SyntheticSuiteRunIdentity,
    SyntheticSuiteRunItem,
    SyntheticSuiteVariantReview,
    derive_error_clusters,
    derive_suite_counts,
)
from abu_v60.mingli.synthetic_suite_store import (
    MingliSyntheticSuiteRunStore,
    MingliSyntheticSuiteRunStoreError,
)
from abu_v60.provenance import content_hash

SuiteProgress = Callable[[str, int, int, str], None]


class SyntheticSuiteServiceError(ValueError):
    pass


class SyntheticSuiteService:
    """Run ordered DEV experiments and seal a replayable batch summary."""

    def __init__(
        self,
        engine: Engine,
        *,
        experiment_service: SyntheticExperimentService | None = None,
        candidate_identity: SyntheticSuiteCandidateIdentity | None = None,
    ) -> None:
        self._engine = engine
        self._experiments = experiment_service or SyntheticExperimentService(engine)
        self._experiment_runs = MingliSyntheticExperimentRunStore(engine)
        self._suite_runs = MingliSyntheticSuiteRunStore(engine)
        self._agent_readings = MingliAgentReadingStore(engine)
        self._attempted_candidate = candidate_identity

    def run_suite(
        self,
        *,
        suite_ref: str,
        progress: SuiteProgress | None = None,
    ) -> dict[str, Any]:
        suite = self._resolve_active_dev_suite(suite_ref)
        self._validate_rank_bridge(suite)
        if self._attempted_candidate is None:
            raise SyntheticSuiteServiceError("mingli_synthetic_suite_attempted_candidate_required")
        items: list[SyntheticSuiteRunItem] = []
        candidate = self._attempted_candidate
        total = len(suite.experiment_refs)
        for position, experiment_ref in enumerate(suite.experiment_refs, start=1):
            if progress is not None:
                progress("START", position, total, experiment_ref)
            try:
                run = self._experiments.run_experiment(experiment_ref=experiment_ref)
            except ValueError as exc:
                item = self._error_item(
                    position=position,
                    experiment_ref=experiment_ref,
                    error_code=_bounded_error_code(exc),
                )
                event = "ERROR"
            else:
                item, item_candidate = self._sealed_item(
                    position=position,
                    expected_experiment_ref=experiment_ref,
                    run=run,
                )
                if candidate != item_candidate:
                    raise SyntheticSuiteServiceError(
                        "mingli_synthetic_suite_candidate_identity_mismatch"
                    )
                event = "SEALED"
            items.append(item)
            if progress is not None:
                progress(event, position, total, experiment_ref)
        canonical_items = self._apply_secondary_repeat_stability(tuple(items))
        counts, outcomes = derive_suite_counts(canonical_items)
        definition = suite.public_definition()
        identity = SyntheticSuiteRunIdentity(
            suite_run_version=SYNTHETIC_SUITE_RUN_VERSION,
            suite_ref=suite.suite_ref,
            suite_definition_hash=str(definition["suite_definition_hash"]),
            suite_mode="DEV",
            runner_version=SYNTHETIC_SUITE_RUNNER_VERSION,
            candidate_identity=candidate,
            status=("COMPLETED_WITH_ERRORS" if counts.runner_errors else "COMPLETED"),
            items=canonical_items,
            counts=counts,
            outcomes=outcomes,
            error_clusters=derive_error_clusters(canonical_items),
            qualification_effect="DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION",
        )
        self._validate_run_bindings(suite=suite, run=identity.model_dump(mode="json"))
        try:
            stored = self._suite_runs.ensure(identity=identity)
        except MingliSyntheticSuiteRunStoreError as exc:
            raise SyntheticSuiteServiceError(str(exc)) from exc
        self._validate_stored_run(suite=suite, run=stored)
        return stored

    def catalog(self, *, suite_run_ref: str | None = None) -> dict[str, Any]:
        if suite_run_ref is not None:
            run = self._suite_runs.get(suite_run_ref=suite_run_ref)
            if run is None:
                raise SyntheticSuiteServiceError("mingli_synthetic_suite_run_not_found")
            suite = resolve_synthetic_suite(str(run["suite_ref"]))
            self._validate_stored_run(suite=suite, run=run)
            definition = suite.public_definition()
            return self._catalog_response(
                (
                    {
                        **definition,
                        "run_status": "SEALED",
                        "latest_suite_run_ref": run["suite_run_ref"],
                        "runs": [self._public_run(run)],
                    },
                )
            )
        entries: list[dict[str, Any]] = []
        for suite in SYNTHETIC_SUITES:
            definition = suite.public_definition()
            history = self._suite_runs.history(suite_ref=suite.suite_ref)
            for run in history:
                self._validate_stored_run(suite=suite, run=run)
            entries.append(
                {
                    **definition,
                    "run_status": "SEALED" if history else "NOT_RUN",
                    "latest_suite_run_ref": (history[0]["suite_run_ref"] if history else None),
                    "runs": [self._public_run(item) for item in history],
                }
            )
        return self._catalog_response(tuple(entries))

    @staticmethod
    def _catalog_response(entries: tuple[dict[str, Any], ...]) -> dict[str, Any]:
        return {
            "catalog_version": SYNTHETIC_SUITE_CATALOG_VERSION,
            "modes": SYNTHETIC_SUITE_MODE_CATALOG,
            "suites": list(entries),
            "browser_generation_allowed": False,
            "read_only": True,
        }

    def _sealed_item(
        self,
        *,
        position: int,
        expected_experiment_ref: str,
        run: Mapping[str, Any],
    ) -> tuple[SyntheticSuiteRunItem, SyntheticSuiteCandidateIdentity]:
        if run.get("experiment_ref") != expected_experiment_ref:
            raise SyntheticSuiteServiceError("mingli_synthetic_suite_child_experiment_mismatch")
        definition = resolve_synthetic_experiment(expected_experiment_ref).public_definition()
        if run.get("definition_hash") != definition["definition_hash"]:
            raise SyntheticSuiteServiceError("mingli_synthetic_suite_child_definition_mismatch")
        evaluation = SyntheticExperimentEvaluation.model_validate(run["evaluation_json"])
        variant_reviews = tuple(
            SyntheticSuiteVariantReview(
                variant=variant,
                reason_keys=tuple(
                    sorted(
                        f"SERVER_REPAIR:{key}"
                        for key in evaluation.server_issue_keys.model_dump()[variant]
                    )
                ),
            )
            for variant in ("A", "B")
        )
        check_reasons = tuple(
            sorted(
                f"CHECK_FAIL:{item.group}:{item.check_ref}"
                for item in evaluation.checks
                if item.status == "FAIL"
            )
        )
        reasons = tuple(
            sorted(
                set(check_reasons).union(
                    reason for review in variant_reviews for reason in review.reason_keys
                )
            )
        )
        gold, gold_hash = synthetic_experiment_dev_gold(run["experiment_ref"])
        contract_status = (
            "CURRENT"
            if evaluation.evaluator_version == SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION
            and evaluation.dev_gold_version == gold["gold_version"]
            and evaluation.dev_gold_hash == gold_hash
            else "SUPERSEDED"
        )
        candidate = self._candidate_identity(run)
        return (
            SyntheticSuiteRunItem(
                position=position,
                experiment_ref=run["experiment_ref"],
                definition_hash=run["definition_hash"],
                execution_status="SEALED",
                experiment_run_ref=run["run_ref"],
                experiment_run_hash=run["run_hash"],
                outcome=evaluation.outcome,
                evaluator_version=evaluation.evaluator_version,
                dev_gold_version=evaluation.dev_gold_version,
                dev_gold_hash=evaluation.dev_gold_hash,
                model_independence=_model_independence(evaluation),
                changed_pass_count=evaluation.changed_pass_count,
                hold_pass_count=evaluation.hold_pass_count,
                review_contract_status=contract_status,
                review_required=bool(reasons),
                review_reason_keys=reasons,
                variant_reviews=variant_reviews,
                error_code=None,
            ),
            candidate,
        )

    @staticmethod
    def _error_item(
        *,
        position: int,
        experiment_ref: str,
        error_code: str,
    ) -> SyntheticSuiteRunItem:
        definition = resolve_synthetic_experiment(experiment_ref).public_definition()
        reason = f"RUNNER_ERROR:{error_code}"
        return SyntheticSuiteRunItem(
            position=position,
            experiment_ref=experiment_ref,
            definition_hash=str(definition["definition_hash"]),
            execution_status="ERROR",
            review_required=True,
            review_reason_keys=(reason,),
            variant_reviews=(),
            error_code=error_code,
        )

    def _candidate_identity(
        self,
        run: Mapping[str, Any],
    ) -> SyntheticSuiteCandidateIdentity:
        readings = tuple(
            self._agent_readings.get(
                requester_account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
                agent_reading_ref=str(run[field]),
            )
            for field in (
                "member_a_agent_reading_ref",
                "member_b_agent_reading_ref",
            )
        )
        identities = tuple(_candidate_from_reading(item) for item in readings)
        if identities[0] != identities[1]:
            raise SyntheticSuiteServiceError("mingli_synthetic_suite_member_candidate_mismatch")
        return identities[0]

    def _apply_secondary_repeat_stability(
        self,
        items: tuple[SyntheticSuiteRunItem, ...],
    ) -> tuple[SyntheticSuiteRunItem, ...]:
        expected_refs = resolve_synthetic_suite(HIDDEN_RANK_DEV_SUITE_REF).experiment_refs
        if tuple(item.experiment_ref for item in items) != expected_refs or any(
            item.execution_status != "SEALED" for item in items
        ):
            return items
        first_run = self._experiment_runs.get(run_ref=str(items[0].experiment_run_ref))
        second_run = self._experiment_runs.get(run_ref=str(items[1].experiment_run_ref))
        if first_run is None or second_run is None:
            raise SyntheticSuiteServiceError("mingli_synthetic_suite_child_run_missing")
        first_reading = self._load_reading(first_run["member_b_agent_reading_ref"])
        second_reading = self._load_reading(second_run["member_a_agent_reading_ref"])
        if _regime_projection(first_reading) == _regime_projection(second_reading):
            return items
        reason = "CHECK_FAIL:EXPECTED_CHANGE:SECONDARY_REPEAT_STABILITY"
        return tuple(
            item.model_copy(
                update={
                    "review_required": True,
                    "review_reason_keys": tuple(
                        sorted(set(item.review_reason_keys).union({reason}))
                    ),
                }
            )
            for item in items
        )

    def _validate_stored_run(
        self,
        *,
        suite: SyntheticSuiteDefinition,
        run: Mapping[str, Any],
    ) -> None:
        self._validate_run_bindings(suite=suite, run=run)

    def _validate_run_bindings(
        self,
        *,
        suite: SyntheticSuiteDefinition,
        run: Mapping[str, Any],
    ) -> None:
        definition = suite.public_definition()
        if (
            run["suite_ref"] != suite.suite_ref
            or run["suite_definition_hash"] != definition["suite_definition_hash"]
            or tuple(item["experiment_ref"] for item in run["items"]) != suite.experiment_refs
        ):
            raise SyntheticSuiteServiceError("mingli_synthetic_suite_definition_drift")
        expected_hashes = {
            experiment_ref: resolve_synthetic_experiment(experiment_ref).public_definition()[
                "definition_hash"
            ]
            for experiment_ref in suite.experiment_refs
        }
        for item in run["items"]:
            if item["definition_hash"] != expected_hashes[item["experiment_ref"]]:
                raise SyntheticSuiteServiceError("mingli_synthetic_suite_item_definition_drift")
            if item["execution_status"] != "SEALED":
                continue
            child = self._experiment_runs.get(run_ref=item["experiment_run_ref"])
            if (
                child is None
                or child["experiment_ref"] != item["experiment_ref"]
                or child["definition_hash"] != item["definition_hash"]
                or child["run_hash"] != item["experiment_run_hash"]
            ):
                raise SyntheticSuiteServiceError("mingli_synthetic_suite_child_run_mismatch")

    def _public_run(self, run: Mapping[str, Any]) -> dict[str, Any]:
        items = tuple(self._current_review_projection(item) for item in run["items"])
        counts, _ = derive_suite_counts(items)
        review_projection = {
            "projection_version": SYNTHETIC_SUITE_REVIEW_PROJECTION_VERSION,
            "source_suite_run_ref": run["suite_run_ref"],
            "source_suite_run_hash": run["suite_run_hash"],
            "items": [item.model_dump(mode="json") for item in items],
            "counts": counts.model_dump(mode="json"),
            "error_clusters": [
                item.model_dump(mode="json") for item in derive_error_clusters(items)
            ],
        }
        return {
            **run,
            "created_at": run["created_at"].isoformat(),
            "current_review_projection": {
                **review_projection,
                "projection_hash": content_hash(review_projection),
            },
        }

    @staticmethod
    def _current_review_projection(
        raw_item: Mapping[str, Any],
    ) -> SyntheticSuiteRunItem:
        item = dict(raw_item)
        if item["execution_status"] != "SEALED":
            return SyntheticSuiteRunItem.model_validate(item)
        gold, gold_hash = synthetic_experiment_dev_gold(item["experiment_ref"])
        current = (
            item["evaluator_version"] == SYNTHETIC_EXPERIMENT_EVALUATOR_VERSION
            and item["dev_gold_version"] == gold["gold_version"]
            and item["dev_gold_hash"] == gold_hash
        )
        item["review_contract_status"] = "CURRENT" if current else "SUPERSEDED"
        if not current:
            item["review_reason_keys"] = sorted(
                set(item["review_reason_keys"]).union({"REVIEW_CONTRACT:SUPERSEDED"})
            )
            item["review_required"] = True
        return SyntheticSuiteRunItem.model_validate(item)

    @staticmethod
    def _resolve_active_dev_suite(suite_ref: str) -> SyntheticSuiteDefinition:
        try:
            suite = resolve_synthetic_suite(suite_ref)
        except ValueError as exc:
            raise SyntheticSuiteServiceError(str(exc)) from exc
        if suite.mode != "DEV" or suite.availability != "ACTIVE":
            raise SyntheticSuiteServiceError("mingli_synthetic_suite_mode_locked")
        return suite

    @staticmethod
    def _validate_rank_bridge(suite: SyntheticSuiteDefinition) -> None:
        if suite.suite_ref != HIDDEN_RANK_DEV_SUITE_REF:
            return
        first = resolve_synthetic_experiment(suite.experiment_refs[0])
        second = resolve_synthetic_experiment(suite.experiment_refs[1])
        first_member = first.member_by_variant["B"]
        second_member = second.member_by_variant["A"]
        if (
            first_member.birth_input != second_member.birth_input
            or first_member.expected_pillars != second_member.expected_pillars
        ):
            raise SyntheticSuiteServiceError("mingli_synthetic_suite_secondary_bridge_drift")

    def _load_reading(self, agent_reading_ref: str) -> MingliAgentReadingEnvelope:
        return self._agent_readings.get(
            requester_account_ref=SYNTHETIC_RESEARCH_ACCOUNT_REF,
            agent_reading_ref=agent_reading_ref,
        )


def _candidate_from_reading(
    reading: MingliAgentReadingEnvelope,
) -> SyntheticSuiteCandidateIdentity:
    return SyntheticSuiteCandidateIdentity(
        agent_profile_ref=reading.agent_profile_ref,
        agent_profile_hash=reading.agent_profile_hash,
        provider_id=reading.provider_id,
        model_ref=reading.model_ref,
        model_digest=reading.model_digest,
        provider_profile_ref=reading.provider_profile_ref,
        provider_profile_hash=reading.provider_profile_hash,
        prompt_ref=reading.prompt_ref,
        prompt_hash=reading.prompt_hash,
        agent_reading_version=reading.agent_reading_version,
    )


def _model_independence(
    evaluation: SyntheticExperimentEvaluation,
) -> str:
    validity_failed = any(
        item.status == "FAIL" and item.group in {"EXPERIMENT_VALIDITY", "MUST_HOLD"}
        for item in evaluation.checks
    )
    expected_failed = any(
        item.status == "FAIL" and item.group == "EXPECTED_CHANGE" for item in evaluation.checks
    )
    return (
        "NOT_EVALUABLE"
        if validity_failed
        else "FAIL"
        if expected_failed or evaluation.server_issue_keys.A or evaluation.server_issue_keys.B
        else "PASS"
    )


def _regime_projection(reading: MingliAgentReadingEnvelope) -> tuple[object, ...]:
    regime = reading.output.regime_decision
    if regime is None:
        return (reading.output.day_master_state, None)
    return (
        reading.output.day_master_state,
        regime.classification,
        regime.effective_root_status,
        regime.effective_root_coordinates,
    )


_SAFE_ERROR = re.compile(r"^[A-Za-z0-9_]+$")


def _bounded_error_code(error: ValueError) -> str:
    candidate = str(error).split(":", 1)[0].strip()
    if candidate and _SAFE_ERROR.fullmatch(candidate):
        return candidate.upper()
    return "UNEXPECTED_VALUE_ERROR"
