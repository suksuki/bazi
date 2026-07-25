from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.contracts import BirthInputCanonical
from core.life_case import (
    LifeCase,
    build_baseline_insight,
    build_domain_insight,
    commit_baseline_life_case,
    commit_domain_insight,
    validate_formal_insight,
)
from core.life_domains import LifeDomain
from core.mingli_agent import (
    CaseBeliefState,
    ChartWorldInstance,
    MingliAgent,
    MingliCognitiveRecord,
    build_case_belief_state,
    compile_chart_world,
)
from core.mingli_agent.assertion_gate import isolate_cognition_assertions
from core.mingli_agent.contracts import DomainExploration
from core.contracts.professional_review import ProfessionalReviewBundle
from core.mingli_agent.professional_review import review_professional_record
from core.mingli_agent.reasoning_review import review_cognition
from core.mingli_agent.reliability import cognition_semantic_signature
from experience.workspace import CaseWorkspaceState, build_case_workspace_state
from product.agent_case_store import AgentCaseStore
from product.formal_insight_state import cognition_background


CommandEventSink = Callable[[str, dict[str, Any]], None]


class DomainReasoningError(RuntimeError):
    pass


class DomainInsightValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class BaselineCaseCommand:
    case_id: str
    reading_id: str
    birth_input: BirthInputCanonical
    profile_id: str | None
    user_id: str | None
    active_mode: str
    world: ChartWorldInstance | None = None


@dataclass(frozen=True)
class BaselineCaseResult:
    world: ChartWorldInstance
    record: MingliCognitiveRecord
    workspace: CaseBeliefState
    life_case: LifeCase | None
    professional_review: ProfessionalReviewBundle
    validation: Any
    metrics: dict[str, Any]

    @property
    def committed(self) -> bool:
        return self.life_case is not None


class BaselineCaseCommandService:
    """Single owner for synchronous and progressive baseline execution."""

    def __init__(self, *, agent: MingliAgent, case_store: AgentCaseStore) -> None:
        self._agent = agent
        self._case_store = case_store

    def execute(
        self,
        command: BaselineCaseCommand,
        *,
        on_event: CommandEventSink | None = None,
    ) -> BaselineCaseResult:
        previous = self._case_store.get(
            case_id=command.case_id,
            user_id=command.user_id,
        ) or {}
        cached = _cached_baseline_result(previous)
        if cached is not None:
            _emit(on_event, "baseline_cache_reused", {
                "status": "committed" if cached.committed else "professional_unreleased",
                "insight_id": (
                    cached.life_case.baseline_insight.insight_id
                    if cached.life_case is not None
                    else ""
                ),
                "model_calls": 0,
            })
            return cached
        world = command.world or compile_chart_world(
            reading_id=command.reading_id,
            birth_input=command.birth_input,
        )
        _emit(on_event, "chart_ready", {
            "pillars": world.pillars,
            "world_id": world.world_id,
            "profile_id": command.profile_id,
            "ziwei": {
                "status": world.ziwei_profile.get("status", "unavailable"),
                "reasoning_ready": bool(world.ziwei_profile.get("reasoning_ready")),
                "calculator": world.ziwei_profile.get("calculator"),
                "life_palace": world.ziwei_profile.get("life_palace"),
                "body_palace": world.ziwei_profile.get("body_palace"),
                "warnings": list(world.ziwei_profile.get("warnings") or []),
            },
        })
        record = self._agent.first_baseline_reading(
            case_id=command.case_id,
            world=world,
            on_stage=on_event,
        )
        run_metrics = _baseline_run_metrics(record)
        professional_review = review_professional_record(
            record=record,
            world=world,
            persistence_status="persisted",
        )
        insight_draft = build_baseline_insight(
            record=record,
            world=world,
            professional_review=professional_review,
        )
        _emit(on_event, "formal_insight_draft_ready", {
            "status": "draft",
            "insight_id": insight_draft.insight_id,
            "claim": insight_draft.claim,
            "persisted": False,
        })
        workspace = build_case_belief_state(record)
        life_case: LifeCase | None = None
        if (
            record.review.commit_eligible
            and professional_review.overlay.professional_release_status
            in {"passed", "partially_blocked"}
        ):
            life_case, validation = commit_baseline_life_case(
                insight=insight_draft,
                world=world,
                profile_id=command.profile_id,
            )
            _emit(on_event, "baseline_validated", {
                "status": "reviewed",
                "validation": validation.model_dump(mode="json"),
                "persisted": False,
            })
        else:
            validation = validate_formal_insight(insight=insight_draft, world=world)

        invalidated_while_running = str(previous.get("status") or "") == "superseded"
        stored_life_case = life_case
        if invalidated_while_running and life_case is not None:
            stored_life_case = life_case.model_copy(update={
                "status": "superseded",
                "chart_version": life_case.chart_version.model_copy(update={"active": False}),
            })
            life_case = None
        previous.pop("workspace", None)
        row = {
            **previous,
            "case_id": command.case_id,
            "profile_id": command.profile_id,
            "birth_input": command.birth_input.model_dump(mode="json"),
            "world": world.model_dump(mode="json"),
            "record": record.model_dump(mode="json"),
            "professional_assertions": [
                item.model_dump(mode="json") for item in professional_review.assertions
            ],
            "professional_review_overlay": professional_review.overlay.model_dump(mode="json"),
            "case_belief_state": workspace.model_dump(mode="json"),
            "workspace_state": build_case_workspace_state(
                case_id=command.case_id,
                active_mode=command.active_mode,
            ).model_dump(mode="json"),
            "life_case": stored_life_case.model_dump(mode="json") if stored_life_case else None,
            "insight_validation": validation.model_dump(mode="json"),
            "first_run": {
                "protocol": "minimal_whole_chart_baseline_v1",
                "blocking_core_llm_calls": len(record.stage_receipts),
                "unselected_domains_precomputed": False,
                "run_metrics": run_metrics,
            },
            "background_cognition": cognition_background(
                (
                    previous.get("background_cognition")
                    if isinstance(previous.get("background_cognition"), dict)
                    else None
                ),
                operational_status=(
                    "superseded"
                    if invalidated_while_running
                    else "completed" if life_case else "completed_partial"
                ),
                insight_status="committed" if stored_life_case else "partial",
                persistence_status="persisted",
                professional_release_status=(
                    professional_review.overlay.professional_release_status
                ),
                active=not invalidated_while_running,
                attempt_count=max(
                    1,
                    int(
                        (
                            previous.get("background_cognition")
                            if isinstance(previous.get("background_cognition"), dict)
                            else {}
                        ).get("attempt_count")
                        or 0
                    ),
                ),
                run_metrics=run_metrics,
            ),
            "status": (
                "superseded"
                if invalidated_while_running
                else "active" if life_case else "professional_blocked"
            ),
        }
        self._case_store.save(
            case_id=command.case_id,
            user_id=command.user_id,
            profile_id=command.profile_id,
            payload=row,
        )
        return BaselineCaseResult(
            world=world,
            record=record,
            workspace=workspace,
            life_case=life_case,
            professional_review=professional_review,
            validation=validation,
            metrics=run_metrics,
        )


@dataclass(frozen=True)
class LocalBaselineReconciliationResult:
    row: dict[str, Any]
    committed: bool
    isolated_assertion_count: int


class BaselineAssertionReconciliationService:
    """Re-evaluate a stored draft locally without another model call."""

    def reconcile(
        self,
        *,
        row: dict[str, Any],
        profile_id: str | None,
    ) -> LocalBaselineReconciliationResult:
        raw_record = row.get("record")
        raw_world = row.get("world")
        if not isinstance(raw_record, dict) or not isinstance(raw_world, dict):
            return LocalBaselineReconciliationResult(
                row=row,
                committed=False,
                isolated_assertion_count=0,
            )
        source_record = MingliCognitiveRecord.model_validate(raw_record)
        world = ChartWorldInstance.model_validate(raw_world)
        if source_record.assertion_gate.decisions:
            cognition = source_record.cognition
            assertion_gate = source_record.assertion_gate
        else:
            cognition, assertion_gate = isolate_cognition_assertions(
                draft=source_record.cognition,
                world=world,
            )
        review = review_cognition(
            draft=cognition,
            world=world,
            model=source_record.model,
            repaired=bool(assertion_gate.repaired_count),
            assertion_gate=assertion_gate,
        )
        record = source_record.model_copy(update={
            "cognition": cognition,
            "review": review,
            "assertion_gate": assertion_gate,
            "reliability_disposition": review.disposition,
            "reliability_signature": cognition_semantic_signature(cognition),
        })
        life_case: LifeCase | None = None
        professional_review = review_professional_record(
            record=record,
            world=world,
            persistence_status="persisted",
        )
        insight = build_baseline_insight(
            record=record,
            world=world,
            professional_review=professional_review,
        )
        validation = validate_formal_insight(
            insight=insight,
            world=world,
        )
        if (
            review.commit_eligible
            and professional_review.overlay.professional_release_status
            in {"passed", "partially_blocked"}
            and validation.passed
        ):
            life_case, validation = commit_baseline_life_case(
                insight=insight,
                world=world,
                profile_id=profile_id,
            )
        background = row.get("background_cognition")
        background = background if isinstance(background, dict) else {}
        archives = row.get("record_archive")
        archives = list(archives) if isinstance(archives, list) else []
        if not any(
            isinstance(item, dict) and item.get("record_id") == source_record.record_id
            for item in archives
        ):
            archives.append(source_record.model_dump(mode="json"))
        reconciled = {
            **row,
            "record": record.model_dump(mode="json"),
            "professional_assertions": [
                item.model_dump(mode="json") for item in professional_review.assertions
            ],
            "professional_review_overlay": professional_review.overlay.model_dump(mode="json"),
            "record_archive": archives[-3:],
            "life_case": life_case.model_dump(mode="json") if life_case else None,
            "insight_validation": validation.model_dump(mode="json"),
            "background_cognition": cognition_background(
                background,
                operational_status="completed_local" if life_case else "completed_partial",
                insight_status="committed" if life_case else "partial",
                persistence_status="persisted",
                professional_release_status=(
                    professional_review.overlay.professional_release_status
                ),
                attempt_count=max(1, int(background.get("attempt_count") or 0)),
                local_reconciliation="assertion_gate_v1",
            ),
            "status": "active" if life_case else "professional_blocked",
        }
        return LocalBaselineReconciliationResult(
            row=reconciled,
            committed=life_case is not None,
            isolated_assertion_count=assertion_gate.candidate_count + assertion_gate.suppressed_count,
        )


@dataclass(frozen=True)
class DomainExplorationCommand:
    case_id: str
    domain: LifeDomain
    user_question: str
    active_mode: str
    user_id: str | None
    row: dict[str, Any]
    workspace: CaseBeliefState
    workspace_state: CaseWorkspaceState


@dataclass(frozen=True)
class DomainExplorationResult:
    status: str
    world: ChartWorldInstance
    record: MingliCognitiveRecord
    workspace: CaseBeliefState
    workspace_state: CaseWorkspaceState
    life_case: LifeCase
    exploration: DomainExploration
    previous_exploration: DomainExploration | None
    domain_insight: Any | None = None
    validation: Any | None = None

    @property
    def cache_hit(self) -> bool:
        return bool(
            self.previous_exploration
            and self.exploration.generated_at == self.previous_exploration.generated_at
        )


class DomainExplorationCommandService:
    """Single owner for synchronous and progressive domain exploration."""

    def __init__(self, *, agent: MingliAgent, case_store: AgentCaseStore) -> None:
        self._agent = agent
        self._case_store = case_store

    def execute(
        self,
        command: DomainExplorationCommand,
        *,
        on_event: CommandEventSink | None = None,
    ) -> DomainExplorationResult:
        row = command.row
        world = ChartWorldInstance.model_validate(row["world"])
        record = MingliCognitiveRecord.model_validate(row["record"])
        previous_exploration = record.domain_explorations.get(command.domain)
        life_case = LifeCase.model_validate(row["life_case"])
        try:
            exploration = self._agent.explore_domain(
                world=world,
                record=record,
                domain=command.domain,
                user_question=command.user_question,
                baseline_insight_id=life_case.baseline_insight.insight_id,
                baseline_case_version=life_case.case_version,
                chart_version_id=life_case.chart_version.version_id,
                temporal_scope=(
                    command.workspace_state.selected_period
                    if command.domain is LifeDomain.LIFE_TIMING
                    else "current"
                ),
                on_stage=on_event,
            )
        except Exception as exc:  # noqa: BLE001 - caller maps this to the stable API error.
            raise DomainReasoningError(
                f"domain_reasoning_failed:{type(exc).__name__}:{exc}"
            ) from exc
        row["workspace_state"] = command.workspace_state.model_dump(mode="json")
        if not exploration.review.commit_eligible or exploration.case_revision_candidate:
            pending = dict(row.get("pending_domain_explorations") or {})
            pending[command.domain.value] = exploration.model_dump(mode="json")
            row["pending_domain_explorations"] = pending
            if exploration.case_revision_candidate:
                row["case_revision_candidates"] = [
                    *(row.get("case_revision_candidates") or []),
                    exploration.case_revision_candidate,
                ]
            self._save(command)
            return DomainExplorationResult(
                status=(
                    "case_revision_candidate"
                    if exploration.case_revision_candidate
                    else f"domain_{exploration.review.disposition}"
                ),
                world=world,
                record=record,
                workspace=command.workspace,
                workspace_state=command.workspace_state,
                life_case=life_case,
                exploration=exploration,
                previous_exploration=previous_exploration,
            )

        record = record.model_copy(update={
            "domain_explorations": {
                **record.domain_explorations,
                command.domain: exploration,
            },
            "revisions": [
                *record.revisions,
                {
                    "kind": "domain_exploration",
                    "domain": command.domain.value,
                    "user_question": command.user_question,
                    "review_passed": exploration.review.passed,
                },
            ],
        })
        row["record"] = record.model_dump(mode="json")
        domain_insight = build_domain_insight(
            record=record,
            exploration=exploration,
            world=world,
            case_version=life_case.case_version,
        )
        try:
            life_case, validation = commit_domain_insight(
                life_case=life_case,
                insight=domain_insight,
                world=world,
            )
        except ValueError as exc:
            raise DomainInsightValidationError(
                f"domain_insight_validation_failed:{exc}"
            ) from exc
        row["life_case"] = life_case.model_dump(mode="json")
        self._save(command)
        return DomainExplorationResult(
            status="domain_exploration_ready",
            world=world,
            record=record,
            workspace=command.workspace,
            workspace_state=command.workspace_state,
            life_case=life_case,
            exploration=exploration,
            previous_exploration=previous_exploration,
            domain_insight=domain_insight,
            validation=validation,
        )

    def _save(self, command: DomainExplorationCommand) -> None:
        command.row.pop("workspace", None)
        self._case_store.save(
            case_id=command.case_id,
            user_id=command.user_id,
            profile_id=command.row.get("profile_id"),
            payload=command.row,
        )


def _emit(sink: CommandEventSink | None, event_type: str, payload: dict[str, Any]) -> None:
    if sink is not None:
        sink(event_type, payload)


def _baseline_run_metrics(record: MingliCognitiveRecord) -> dict[str, Any]:
    receipts = list(record.stage_receipts)
    durations = [max(0, int(item.get("duration_ms") or 0)) for item in receipts]
    input_tokens = [
        int(item["prompt_eval_count"])
        for item in receipts
        if isinstance(item.get("prompt_eval_count"), int)
    ]
    output_tokens = [
        int(item["eval_count"])
        for item in receipts
        if isinstance(item.get("eval_count"), int)
    ]
    context_items = list(record.context_manifest)
    routes = list(record.model_routes)
    return {
        "contract": "baseline_core_cognition_v1",
        "model_calls": len(receipts),
        "input_tokens": sum(input_tokens),
        "output_tokens": sum(output_tokens),
        "token_metrics_available": bool(input_tokens or output_tokens),
        "knowledge_retrieval_count": sum(int(item.get("knowledge_count") or 0) for item in context_items),
        "fact_input_count": sum(int(item.get("fact_count") or 0) for item in context_items),
        "latency_ms": {
            "total": sum(durations),
            "average": round(sum(durations) / len(durations)) if durations else 0,
            "slowest": max(durations, default=0),
        },
        "max_output_tokens": max((int(item.get("max_tokens") or 0) for item in routes), default=0),
        "schema_attempts": sum(int(item.get("schema_attempts") or 1) for item in receipts),
        "case_store_operations": {"reads": 1, "writes": 1},
        "generated_sections": [
            "whole_chart_structure",
            "primary_work_path",
            "pivots_and_support",
            "competing_hypotheses",
            "uncertainty",
        ],
        "deferred_sections": [
            "career",
            "wealth",
            "relationship",
            "health",
            "timing",
            "xiangfa_detail",
            "long_form_expression",
        ],
        "automatic_full_reruns": 0,
        "partial_results_retained": True,
    }


def _cached_baseline_result(row: dict[str, Any]) -> BaselineCaseResult | None:
    raw_life_case = row.get("life_case")
    raw_world = row.get("world")
    raw_record = row.get("record")
    if not all(isinstance(item, dict) for item in (raw_world, raw_record)):
        return None
    try:
        world = ChartWorldInstance.model_validate(raw_world)
        record = MingliCognitiveRecord.model_validate(raw_record)
        professional_review = review_professional_record(
            record=record,
            world=world,
            persistence_status="persisted",
        )
        life_case = (
            LifeCase.model_validate(raw_life_case)
            if isinstance(raw_life_case, dict)
            else None
        )
        baseline = life_case.baseline_insight if life_case is not None else None
        formally_released = bool(
            life_case is not None
            and life_case.status == "active"
            and life_case.chart_version.active
            and baseline is not None
            and baseline.status == "committed"
            and baseline.professional_review_overlay is not None
            and baseline.professional_release_status in {"passed", "partially_blocked"}
        )
        if formally_released:
            assert baseline is not None
            validation = validate_formal_insight(insight=baseline, world=world)
        else:
            life_case = None
            validation = validate_formal_insight(
                insight=build_baseline_insight(
                    record=record,
                    world=world,
                    professional_review=professional_review,
                ),
                world=world,
            )
        raw_workspace = row.get("case_belief_state") or row.get("workspace")
        workspace = (
            CaseBeliefState.model_validate(raw_workspace)
            if isinstance(raw_workspace, dict)
            else build_case_belief_state(record)
        )
    except (TypeError, ValueError):
        return None
    return BaselineCaseResult(
        world=world,
        record=record,
        workspace=workspace,
        life_case=life_case,
        professional_review=professional_review,
        validation=validation,
        metrics={
            "contract": "baseline_cache_reuse_v1",
            "model_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "knowledge_retrieval_count": 0,
            "fact_input_count": 0,
            "latency_ms": {"total": 0, "average": 0, "slowest": 0},
            "case_store_operations": {"reads": 1, "writes": 0},
            "automatic_full_reruns": 0,
            "partial_results_retained": True,
            "cache_hit": True,
        },
    )
