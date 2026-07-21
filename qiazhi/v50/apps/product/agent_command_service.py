from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.contracts import BirthInputCanonical
from core.life_case import (
    LifeCase,
    build_baseline_insight,
    build_workspace_state,
    commit_baseline_life_case,
    validate_formal_insight,
)
from core.mingli_agent import (
    CaseCognitiveWorkspace,
    ChartWorldInstance,
    MingliAgent,
    MingliCognitiveRecord,
    build_case_workspace,
    compile_chart_world,
)
from product.agent_case_store import AgentCaseStore


CommandEventSink = Callable[[str, dict[str, Any]], None]


@dataclass(frozen=True)
class BaselineCaseCommand:
    case_id: str
    reading_id: str
    birth_input: BirthInputCanonical
    profile_id: str | None
    user_id: str | None
    active_mode: str


@dataclass(frozen=True)
class BaselineCaseResult:
    world: ChartWorldInstance
    record: MingliCognitiveRecord
    workspace: CaseCognitiveWorkspace
    life_case: LifeCase | None
    validation: Any

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
        world = compile_chart_world(
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
        insight_draft = build_baseline_insight(record=record, world=world)
        _emit(on_event, "formal_insight_draft_ready", {
            "status": "draft",
            "insight_id": insight_draft.insight_id,
            "claim": insight_draft.claim,
            "persisted": False,
        })
        workspace = build_case_workspace(record)
        life_case: LifeCase | None = None
        if record.review.commit_eligible:
            life_case, validation = commit_baseline_life_case(
                insight=insight_draft,
                world=world,
                profile_id=command.profile_id,
            )
            _emit(on_event, "baseline_validated", {
                "status": "validated",
                "validation": validation.model_dump(mode="json"),
                "persisted": False,
            })
        else:
            validation = validate_formal_insight(insight=insight_draft, world=world)

        row = {
            "case_id": command.case_id,
            "profile_id": command.profile_id,
            "birth_input": command.birth_input.model_dump(mode="json"),
            "world": world.model_dump(mode="json"),
            "record": record.model_dump(mode="json"),
            "case_belief_state": workspace.model_dump(mode="json"),
            "workspace_state": build_workspace_state(
                case_id=command.case_id,
                active_mode=command.active_mode,
            ).model_dump(mode="json"),
            "life_case": life_case.model_dump(mode="json") if life_case else None,
            "insight_validation": validation.model_dump(mode="json"),
            "first_run": {
                "protocol": "single_call_baseline_v1",
                "blocking_core_llm_calls": len(record.stage_receipts),
                "unselected_domains_precomputed": False,
            },
            "status": "active" if life_case else record.review.disposition,
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
            validation=validation,
        )


def _emit(sink: CommandEventSink | None, event_type: str, payload: dict[str, Any]) -> None:
    if sink is not None:
        sink(event_type, payload)
