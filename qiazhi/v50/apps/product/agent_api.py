from __future__ import annotations

import logging
from datetime import datetime, timezone
import os
from typing import Any, Callable
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from core.abu_runtime import AbuCapabilityRegistry, AbuRuntimeContext, resolve_abu_command
from core.contracts import BirthInputCanonical
from core.engines import BirthCalendarResolutionError, resolve_birth_input_pillars
from core.life_case import (
    LifeCase,
    build_case_revision_insight,
    build_reality_evidence,
    commit_case_revision,
    complete_monthly_review,
    ensure_temporal_snapshot,
    formal_projection_record,
    normalize_period_key,
    upsert_reality_evidence,
)
from core.life_domains import LifeDomain, domain_access_allowed, domain_manifest
from core.mingli_agent import (
    ChartWorldInstance,
    MingliAgent,
    MingliCognitiveRecord,
    OllamaCognitiveModel,
    apply_deliberation_selection,
    apply_probe_response,
    build_deliberation_view,
    undo_deliberation_selection,
)
from experience.workspace import select_case_workspace_period
from product.agent_api_contracts import (
    AbuResolveRequest,
    CaseRevisionCommitRequest,
    CaseStartRequest,
    CaseTurnRequest,
    DeliberationSelectionRequest,
    DeliberationUndoRequest,
    DomainExploreRequest,
    IntakeRequest,
    MonthlyReviewRequest,
    ProbePlanRequest,
    ProbeResponseRequest,
    RealityEvidenceRequest,
    TemporalSelectRequest,
)
from product.agent_case_policy import (
    case_summary as _case_summary,
    is_current_cognitive_record as _is_current_cognitive_record,
    is_domain_eligible as _is_domain_eligible,
    is_historical_life_case as _is_historical_life_case,
)
from product.agent_case_store import AgentCaseStore, build_agent_case_store
from product.agent_command_service import (
    BaselineCaseCommand,
    DomainExplorationCommand,
    DomainInsightValidationError,
    DomainReasoningError,
)
from product.agent_job_store import AgentJobStore, build_agent_job_store
from product.agent_runtime import AgentRuntimeServices, build_agent_runtime
from product.agent_probe_support import (
    fallback_probe_revision as _fallback_probe_revision,
    probe_revision_request as _probe_revision_request,
    public_revision as _public_revision,
)
from product.agent_reading_projection import (
    public_reading_view as _public_reading_view,
    reliability_outcome_payload as _reliability_outcome_payload,
)
from product.product_store import ProductStore, birth_input_from_profile


AGENT_API_PREFIX = "/api/v50/agent"
LOGGER = logging.getLogger(__name__)


def create_agent_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    agent: MingliAgent | None = None,
    case_store: AgentCaseStore | None = None,
    job_store: AgentJobStore | None = None,
    runtime: AgentRuntimeServices | None = None,
    agent_injected: bool | None = None,
) -> APIRouter:
    router = APIRouter(prefix=AGENT_API_PREFIX, tags=["mingli-agent"])
    injected_agent = agent is not None if agent_injected is None else agent_injected
    resolved_agent = runtime.agent if runtime is not None else agent or MingliAgent()
    resolved_case_store = runtime.context.case_store if runtime is not None else case_store or build_agent_case_store()
    resolved_job_store = runtime.context.job_store if runtime is not None else job_store or build_agent_job_store()
    runtime = runtime or build_agent_runtime(
        product_store=product_store,
        session_cookie=session_cookie,
        agent=resolved_agent,
        case_store=resolved_case_store,
        job_store=resolved_job_store,
    )
    agent = runtime.agent
    case_store = runtime.context.case_store
    job_store = runtime.context.job_store
    context = runtime.context
    account_for = context.account_for
    load_case = context.load_case
    mode_for = context.mode_for
    workspace_for = context.workspace_for
    workspace_state_for = context.workspace_state_for
    life_case_for = context.life_case_for
    save_case_row = context.save_case_row
    intake_agent = agent if injected_agent else MingliAgent(
        OllamaCognitiveModel(
            base_url=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"),
            model=os.getenv("V50_ABU_INTAKE_MODEL", "qwen3:8b"),
            timeout_seconds=int(os.getenv("V50_ABU_INTAKE_TIMEOUT_SECONDS", "45")),
            num_ctx=8192,
        )
    )
    probe_planner = runtime.probe_planner
    baseline_commands = runtime.baseline_commands
    domain_commands = runtime.domain_commands
    jobs = runtime.jobs
    recovered_interrupted_jobs = jobs.recovered_interrupted_jobs
    capability_registry = AbuCapabilityRegistry()

    @router.get("/manifest")
    def manifest() -> dict[str, Any]:
        return {
            "version": "deepbazi.mingli_agent.v1",
            "cognitive_authority": "llm_mingli_agent",
            "reasoning_model": agent.model.model,
            "pattern_model": agent.pattern_model.model,
            "work_model": agent.work_model.model,
            "domain_model": agent.domain_model.model,
            "intake_model": intake_agent.model.model,
            "life_domains": domain_manifest(),
            "interaction": "abu_conversation_first",
            "case_storage": case_store.storage_name,
            "deterministic_brain_used": False,
            "template_reading_fallback": False,
            "model_policy": agent.model_policy.manifest(),
            "probe_modes": ["guest", "member", "practitioner", "research"],
            "case_belief_updates_only": True,
            "progressive_cognition": True,
            "production_first_run_protocol": "workspace_bootstrap_then_background_baseline_v1",
            "first_run_blocking_core_llm_call_budget": 0,
            "missing_baseline_background_llm_call_budget": 1,
            "domain_reasoning": "on_demand_only",
            "domain_progressive_preview": True,
            "domain_exact_request_cache": True,
            "job_storage": job_store.storage_name,
            "interrupted_jobs_recovered_on_startup": recovered_interrupted_jobs,
        }

    @router.get("/abu/capabilities")
    def abu_capabilities() -> dict[str, Any]:
        return {"status": "ready", "capabilities": capability_registry.manifest()}

    @router.post("/abu/resolve")
    def resolve_abu(payload: AbuResolveRequest, request: Request) -> dict[str, Any]:
        account = account_for(request)
        plan = resolve_abu_command(
            message=payload.message,
            context=AbuRuntimeContext(
                has_case=payload.has_case,
                has_profile=payload.has_profile,
                has_account=account is not None,
                active_mode=payload.active_mode,
                active_domain=payload.active_domain,
            ),
            registry=capability_registry,
        )
        return {"status": "command_resolved", "plan": plan.model_dump(mode="json")}

    @router.post("/intake")
    def parse_intake(payload: IntakeRequest) -> dict[str, Any]:
        try:
            draft = intake_agent.parse_birth_intake(message=payload.message, current=payload.current_draft)
        except Exception as exc:  # noqa: BLE001 - returned as a visible product error.
            raise HTTPException(status_code=503, detail=f"birth_intake_model_failed:{type(exc).__name__}") from exc
        return {"status": "ready_for_confirmation" if draft.ready_for_confirmation else "needs_clarification", "draft": draft.model_dump(mode="json")}

    @router.post("/cases")
    def start_case(payload: CaseStartRequest, request: Request) -> dict[str, Any]:
        account = account_for(request)
        profile: dict[str, object] | None = None
        if payload.profile_id:
            if account is None:
                raise HTTPException(status_code=401, detail="authentication_required")
            profile = product_store.get_profile(user_id=str(account["user_id"]), profile_id=payload.profile_id)
            if profile is None:
                raise HTTPException(status_code=404, detail="profile_not_found")
            birth_input = birth_input_from_profile(profile)
        elif payload.birth_input is not None:
            birth_input = payload.birth_input
        else:
            raise HTTPException(status_code=422, detail="birth_input_or_profile_required")
        try:
            birth_input = resolve_birth_input_pillars(birth_input)
        except BirthCalendarResolutionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not all([birth_input.year_pillar, birth_input.month_pillar, birth_input.day_pillar, birth_input.hour_pillar]):
            raise HTTPException(status_code=422, detail="four_pillars_resolution_failed")
        if account is not None and profile is None:
            profile = product_store.save_profile(user_id=str(account["user_id"]), birth_input=birth_input)

        case_id = f"mingli-case-{uuid4().hex[:20]}"
        reading_id = f"agent-reading-{uuid4().hex[:16]}"
        active_mode = mode_for(account, payload.active_mode)
        if payload.progressive:
            job_id = f"cognitive-job-{uuid4().hex[:20]}"
            user_id = str(account["user_id"]) if account else None
            job_store.create(
                job_id=job_id,
                case_id=case_id,
                user_id=user_id,
                payload={
                    "version": "deepbazi.progressive_cognitive_job.v1",
                    "reading_id": reading_id,
                    "active_mode": active_mode,
                },
            )
            jobs.submit_baseline(
                job_id=job_id,
                case_id=case_id,
                reading_id=reading_id,
                birth_input=birth_input,
                profile=profile,
                user_id=user_id,
                active_mode=active_mode,
            )
            return {
                "status": "cognitive_job_started",
                "job_id": job_id,
                "case_id": case_id,
                "saved": account is not None,
                "profile": profile,
            }
        try:
            result = baseline_commands.execute(BaselineCaseCommand(
                case_id=case_id,
                reading_id=reading_id,
                birth_input=birth_input,
                profile_id=str(profile.get("profile_id")) if profile else None,
                user_id=str(account["user_id"]) if account else None,
                active_mode=active_mode,
            ))
        except Exception as exc:  # noqa: BLE001 - cognition failure must not become a template fallback.
            raise HTTPException(status_code=503, detail=f"mingli_cognition_failed:{type(exc).__name__}:{exc}") from exc
        if not result.committed:
            response: dict[str, Any] = {
                "status": f"baseline_{result.record.review.disposition}",
                "case_id": case_id,
                "saved": account is not None,
                "profile": profile,
                "outcome": _reliability_outcome_payload(
                    world=result.world,
                    record=result.record,
                ),
            }
            if result.record.review.disposition == "competing":
                response["reading"] = _public_reading_view(
                    world=result.world,
                    record=result.record,
                    workspace=result.workspace,
                    probe_plan=probe_planner.plan(
                        record=result.record,
                        role_mode=active_mode,
                    ),
                )
            return response
        life_case = result.life_case
        assert life_case is not None
        return {
            "status": "first_reading_ready",
            "case_id": case_id,
            "saved": account is not None,
            "profile": profile,
            "reading": _public_reading_view(
                world=result.world,
                record=result.record,
                workspace=result.workspace,
                probe_plan=probe_planner.plan(record=result.record, role_mode=active_mode),
                life_case=life_case,
            ),
        }

    @router.get("/jobs/{job_id}")
    def get_job(job_id: str, request: Request, after: int = 0) -> dict[str, Any]:
        account = account_for(request)
        user_id = str(account["user_id"]) if account else None
        job = job_store.get(job_id=job_id, user_id=user_id)
        if job is None:
            raise HTTPException(status_code=404, detail="cognitive_job_not_found")
        events = [item for item in job.get("events", []) if int(item.get("sequence", 0)) > after]
        return {
            "status": job.get("status", "queued"),
            "job_id": job_id,
            "case_id": job["case_id"],
            "events": events,
            "last_sequence": max([after, *[int(item.get("sequence", 0)) for item in events]]),
        }

    @router.get("/cases")
    def list_cases(request: Request, include_history: bool = False) -> dict[str, Any]:
        account = account_for(request)
        if account is None:
            raise HTTPException(status_code=401, detail="authentication_required")
        rows = case_store.list_for_user(user_id=str(account["user_id"]))
        current_rows = [row for row in rows if _is_current_cognitive_record(row)]
        historical_rows = [row for row in rows if _is_historical_life_case(row)]
        return {
            "status": "ready",
            "cases": [_case_summary(row) for row in current_rows],
            "historical_cases": [_case_summary(row) for row in historical_rows] if include_history else [],
            "historical_cases_hidden": 0 if include_history else len(historical_rows),
            "legacy_cases_hidden": len(rows) - len(current_rows) - len(historical_rows),
        }

    @router.get("/cases/{case_id}")
    def get_case(
        case_id: str,
        request: Request,
        active_mode: str | None = None,
        historical: bool = False,
    ) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        world = ChartWorldInstance.model_validate(row["world"])
        run_record = MingliCognitiveRecord.model_validate(row["record"])
        life_case = LifeCase.model_validate(row["life_case"]) if row.get("life_case") else None
        read_only = bool(life_case and (life_case.status != "active" or not life_case.chart_version.active))
        if read_only and not historical:
            raise HTTPException(status_code=409, detail="life_case_superseded_read_only")
        if not read_only and not _is_current_cognitive_record(row):
            raise HTTPException(status_code=409, detail="cognitive_record_requires_recompute")
        record = formal_projection_record(life_case=life_case, fallback_record=run_record) if life_case else run_record
        workspace = workspace_for(row, record)
        selected_mode = mode_for(account, active_mode)
        workspace_state = workspace_state_for(row, case_id=case_id, active_mode=selected_mode)
        profile = None
        if account is not None and row.get("profile_id"):
            profile = product_store.get_profile(
                user_id=str(account["user_id"]),
                profile_id=str(row["profile_id"]),
            )
        response: dict[str, Any] = {
            "status": "historical_read_only" if read_only else "ready",
            "case_id": case_id,
            "read_only": read_only,
            "read_only_reason": "出生资料已经更新；此案例仅供历史审计。" if read_only else "",
            "workspace_state": workspace_state.model_dump(mode="json"),
            "case_context": {
                "profile_id": row.get("profile_id"),
                "profile": profile,
                "birth_input": row.get("birth_input"),
                "saved": account is not None and bool(row.get("profile_id")),
            },
        }
        response["outcome"] = _reliability_outcome_payload(world=world, record=record)
        if record.reliability_disposition != "blocked":
            reading = _public_reading_view(
                world=world,
                record=record,
                workspace=workspace,
                probe_plan=probe_planner.plan(record=record, role_mode=selected_mode),
                life_case=life_case,
                workspace_state=workspace_state,
            )
            if read_only:
                reading["probe_plan"] = None
            response["reading"] = reading
        return response

    @router.get("/cases/{case_id}/deliberation")
    def get_case_deliberation(
        case_id: str,
        request: Request,
        active_mode: str | None = None,
        active_domain: LifeDomain = LifeDomain.WHOLE_CHART,
    ) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        life_case_for(row, write=False)
        record = MingliCognitiveRecord.model_validate(row["record"])
        workspace = workspace_for(row, record)
        selected_mode = mode_for(account, active_mode)
        if selected_mode not in {"practitioner", "research"}:
            raise HTTPException(status_code=403, detail="professional_deliberation_required")
        return {
            "status": "deliberation_ready",
            "case_id": case_id,
            "deliberation": build_deliberation_view(
                record=record,
                workspace=workspace,
                role_mode=selected_mode,
                active_domain=active_domain,
            ).model_dump(mode="json"),
        }

    @router.post("/cases/{case_id}/deliberation/select")
    def select_case_deliberation(
        case_id: str,
        payload: DeliberationSelectionRequest,
        request: Request,
    ) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        if account is None:
            raise HTTPException(status_code=401, detail="authentication_required")
        life_case_for(row, write=True)
        world = ChartWorldInstance.model_validate(row["world"])
        record = MingliCognitiveRecord.model_validate(row["record"])
        workspace = workspace_for(row, record)
        selected_mode = mode_for(account, payload.active_mode)
        if selected_mode not in {"practitioner", "research"}:
            raise HTTPException(status_code=403, detail="professional_deliberation_required")
        try:
            workspace, receipt = apply_deliberation_selection(
                record=record,
                workspace=workspace,
                role_mode=selected_mode,
                actor_id=str(account["user_id"]),
                stage_id=payload.stage_id,
                option_id=payload.option_id,
                action=payload.action,
                active_domain=payload.active_domain,
                rationale=payload.rationale,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        row["case_belief_state"] = workspace.model_dump(mode="json")
        save_case_row(case_id=case_id, row=row, account=account)
        return {
            "status": "deliberation_applied",
            "case_id": case_id,
            "receipt": receipt.model_dump(mode="json"),
            "reading": _public_reading_view(
                world=world,
                record=record,
                workspace=workspace,
                probe_plan=probe_planner.plan(record=record, role_mode=selected_mode),
                active_domain=payload.active_domain,
                life_case=row.get("life_case"),
            ),
        }

    @router.post("/cases/{case_id}/deliberation/undo")
    def undo_case_deliberation(
        case_id: str,
        payload: DeliberationUndoRequest,
        request: Request,
    ) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        if account is None:
            raise HTTPException(status_code=401, detail="authentication_required")
        life_case_for(row, write=True)
        world = ChartWorldInstance.model_validate(row["world"])
        record = MingliCognitiveRecord.model_validate(row["record"])
        workspace = workspace_for(row, record)
        selected_mode = mode_for(account, payload.active_mode)
        if selected_mode not in {"practitioner", "research"}:
            raise HTTPException(status_code=403, detail="professional_deliberation_required")
        try:
            workspace, receipt = undo_deliberation_selection(
                record=record,
                workspace=workspace,
                role_mode=selected_mode,
                actor_id=str(account["user_id"]),
                active_domain=payload.active_domain,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        row["case_belief_state"] = workspace.model_dump(mode="json")
        save_case_row(case_id=case_id, row=row, account=account)
        return {
            "status": "deliberation_undone",
            "case_id": case_id,
            "receipt": receipt.model_dump(mode="json"),
            "reading": _public_reading_view(
                world=world,
                record=record,
                workspace=workspace,
                probe_plan=probe_planner.plan(record=record, role_mode=selected_mode),
                active_domain=payload.active_domain,
                life_case=row.get("life_case"),
            ),
        }

    def execute_domain_exploration(
        *,
        case_id: str,
        domain: LifeDomain,
        payload: DomainExploreRequest,
        row: dict[str, Any],
        account: dict[str, object] | None,
        on_stage: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        record = MingliCognitiveRecord.model_validate(row["record"])
        if not _is_domain_eligible(row):
            raise HTTPException(status_code=409, detail="cognitive_record_requires_recompute")
        workspace = workspace_for(row, record)
        active_mode = mode_for(account, payload.active_mode)
        workspace_state = workspace_state_for(
            row,
            case_id=case_id,
            active_mode=active_mode,
        ).model_copy(update={
            "active_domain": domain.value,
            "active_mode": active_mode,
            "conversation_focus": f"domain:{domain.value}",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        if not domain_access_allowed(domain, role_mode=active_mode):
            raise HTTPException(
                status_code=403,
                detail="domain_not_available_for_product_mode",
            )
        try:
            result = domain_commands.execute(
                DomainExplorationCommand(
                    case_id=case_id,
                    domain=domain,
                    user_question=payload.user_question,
                    active_mode=active_mode,
                    user_id=str(account["user_id"]) if account else row.get("user_id"),
                    row=row,
                    workspace=workspace,
                    workspace_state=workspace_state,
                ),
                on_event=on_stage,
            )
        except DomainReasoningError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except DomainInsightValidationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        exploration = result.exploration
        if result.status != "domain_exploration_ready":
            return {
                "status": result.status,
                "case_id": case_id,
                "domain": domain.value,
                "cache_hit": False,
                "formal_insight": {
                    "status": "draft",
                    "committed": False,
                    "review": exploration.review.model_dump(mode="json"),
                },
                "domain_outcome": {
                    "state": exploration.review.disposition,
                    "case_revision_candidate": exploration.case_revision_candidate,
                    "issues": [
                        {
                            "code": item.code,
                            "message": item.message,
                            "category": item.category,
                        }
                        for item in exploration.review.issues
                    ],
                },
                "reading": _public_reading_view(
                    world=result.world,
                    record=result.record,
                    workspace=result.workspace,
                    probe_plan=probe_planner.plan(
                        record=result.record,
                        role_mode=active_mode,
                    ),
                    active_domain=LifeDomain.WHOLE_CHART,
                    life_case=result.life_case,
                    workspace_state=result.workspace_state,
                ),
            }

        assert result.domain_insight is not None
        assert result.validation is not None
        return {
            "status": result.status,
            "case_id": case_id,
            "domain": domain.value,
            "cache_hit": result.cache_hit,
            "formal_insight": {
                "insight_id": result.domain_insight.insight_id,
                "status": "committed",
                "validation": result.validation.model_dump(mode="json"),
            },
            "reading": _public_reading_view(
                world=result.world,
                record=result.record,
                workspace=result.workspace,
                probe_plan=probe_planner.plan(
                    record=result.record,
                    role_mode=active_mode,
                    scenario="timing" if domain is LifeDomain.LIFE_TIMING else "domain",
                    domain=domain,
                ),
                active_domain=domain,
                life_case=result.life_case,
                workspace_state=result.workspace_state,
            ),
        }

    @router.post("/cases/{case_id}/domains/{domain}")
    def explore_case_domain(case_id: str, domain: LifeDomain, payload: DomainExploreRequest, request: Request) -> dict[str, Any]:
        if domain is LifeDomain.WHOLE_CHART:
            raise HTTPException(status_code=409, detail="whole_chart_already_available")
        row, account = load_case(case_id, request)
        if payload.progressive:
            # Validate access before returning a background job id.
            record = MingliCognitiveRecord.model_validate(row["record"])
            if not _is_domain_eligible(row):
                raise HTTPException(status_code=409, detail="cognitive_record_requires_recompute")
            selected_mode = mode_for(account, payload.active_mode)
            if not domain_access_allowed(domain, role_mode=selected_mode):
                raise HTTPException(status_code=403, detail="domain_not_available_for_product_mode")
            job_id = f"domain-job-{uuid4().hex[:20]}"
            user_id = str(account["user_id"]) if account else row.get("user_id")
            job_store.create(
                job_id=job_id,
                case_id=case_id,
                user_id=user_id,
                payload={"kind": "domain", "domain": domain.value},
            )
            jobs.submit_domain(
                job_id=job_id,
                case_id=case_id,
                domain=domain,
                execute=lambda on_stage: execute_domain_exploration(
                    case_id=case_id,
                    domain=domain,
                    payload=payload,
                    row=row,
                    account=account,
                    on_stage=on_stage,
                ),
            )
            return {
                "status": "domain_job_started",
                "job_id": job_id,
                "case_id": case_id,
                "domain": domain.value,
                "baseline_record_id": record.record_id,
            }
        return execute_domain_exploration(
            case_id=case_id,
            domain=domain,
            payload=payload,
            row=row,
            account=account,
        )

    @router.post("/cases/{case_id}/turn")
    def continue_case(case_id: str, payload: CaseTurnRequest, request: Request) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        world = ChartWorldInstance.model_validate(row["world"])
        record = MingliCognitiveRecord.model_validate(row["record"])
        if not _is_current_cognitive_record(row):
            raise HTTPException(status_code=409, detail="cognitive_record_requires_recompute")
        workspace = workspace_for(row, record)
        active_mode = mode_for(account, payload.active_mode)
        try:
            turn = agent.continue_case(world=world, record=record, user_message=payload.message)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=f"mingli_turn_failed:{type(exc).__name__}:{exc}") from exc
        revision = {
            "user_message": payload.message,
            "turn": turn.model_dump(mode="json"),
        }
        record = record.model_copy(update={
            "revisions": [*record.revisions, revision],
        })
        row["record"] = record.model_dump(mode="json")
        save_case_row(case_id=case_id, row=row, account=account)
        return {
            "status": "turn_ready",
            "case_id": case_id,
            "turn": turn.model_dump(mode="json"),
            "reading": _public_reading_view(
                world=world,
                record=record,
                workspace=workspace,
                probe_plan=probe_planner.plan(record=record, role_mode=active_mode),
                life_case=row.get("life_case"),
            ),
        }

    @router.post("/cases/{case_id}/probe-plan")
    def get_probe_plan(case_id: str, payload: ProbePlanRequest, request: Request) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        life_case_for(row, write=True)
        record = MingliCognitiveRecord.model_validate(row["record"])
        workspace = workspace_for(row, record)
        active_mode = mode_for(account, payload.active_mode)
        if not domain_access_allowed(payload.domain, role_mode=active_mode):
            raise HTTPException(status_code=403, detail="domain_not_available_for_product_mode")
        plan = probe_planner.plan(
            record=record,
            role_mode=active_mode,
            scenario=payload.scenario,
            domain=payload.domain,
        )
        if plan.source_probe_id in workspace.answered_probe_ids or any(
            item.source_probe_id == plan.source_probe_id for item in workspace.probe_history
        ):
            return {"status": "no_active_probe", "probe_plan": None}
        return {"status": "probe_plan_ready", "probe_plan": plan.model_dump(mode="json")}

    @router.post("/cases/{case_id}/probe-respond")
    def respond_to_probe(case_id: str, payload: ProbeResponseRequest, request: Request) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        life_case = life_case_for(row, write=True)
        world = ChartWorldInstance.model_validate(row["world"])
        record = MingliCognitiveRecord.model_validate(row["record"])
        workspace = workspace_for(row, record)
        active_mode = mode_for(account, payload.active_mode)
        if not domain_access_allowed(payload.domain, role_mode=active_mode):
            raise HTTPException(status_code=403, detail="domain_not_available_for_product_mode")
        plan = probe_planner.plan(
            record=record,
            role_mode=active_mode,
            scenario=payload.scenario,
            domain=payload.domain,
        )
        if plan.plan_id != payload.plan_id:
            raise HTTPException(status_code=409, detail="probe_plan_stale")
        idempotency_key = f"probe:{plan.source_probe_id}:{payload.option_id}"
        existing_evidence = next(
            (item for item in life_case.reality_evidence if item.idempotency_key == idempotency_key),
            None,
        )
        if existing_evidence is not None:
            return {
                "status": "case_belief_unchanged",
                "idempotent_replay": True,
                "evidence": existing_evidence.model_dump(mode="json"),
                "reading": _public_reading_view(
                    world=world,
                    record=record,
                    workspace=workspace,
                    probe_plan=plan,
                    life_case=life_case,
                    workspace_state=workspace_state_for(row, case_id=case_id, active_mode=active_mode),
                ),
            }
        if plan.source_probe_id in workspace.answered_probe_ids or any(
            item.source_probe_id == plan.source_probe_id for item in workspace.probe_history
        ):
            raise HTTPException(status_code=409, detail="probe_already_answered")
        source = "research_observation" if active_mode == "research" else "practitioner_reported" if active_mode == "practitioner" else "user_reported"
        selected = next(item for item in plan.options if item.option_id == payload.option_id)
        canonical_evidence = build_reality_evidence(
            life_case=life_case,
            idempotency_key=idempotency_key,
            source="probe",
            source_ref=plan.source_probe_id,
            summary=payload.event_note or selected.label,
            period_key=(
                f"{payload.year_value:04d}-01"
                if payload.year_value is not None
                else workspace_state_for(row, case_id=case_id, active_mode=active_mode).selected_period
            ),
            domain=plan.domain.value,
            kind=plan.evidence_kind,
            structured_payload={
                "plan_id": plan.plan_id,
                "source_probe_id": plan.source_probe_id,
                "option_id": selected.option_id,
                "option_label": selected.label,
                "year_value": payload.year_value,
                "recurrence_count": payload.recurrence_count,
                "hidden_attribute_observations": selected.hidden_attribute_observations,
                "hypothesis_updates": selected.hypothesis_updates,
                "assertion_updates": selected.assertion_updates,
            },
        )
        try:
            workspace, receipt = apply_probe_response(
                workspace=workspace,
                plan=plan,
                option_id=payload.option_id,
                source=source,
                year_value=payload.year_value,
                event_note=payload.event_note,
                recurrence_count=payload.recurrence_count,
                evidence_id=canonical_evidence.evidence_id,
                recorded_at=canonical_evidence.recorded_at,
                persist_legacy_history=False,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        life_case, evidence, evidence_created = upsert_reality_evidence(
            life_case=life_case,
            evidence=canonical_evidence,
        )
        try:
            turn = agent.continue_case(
                world=world,
                record=record,
                user_message=_probe_revision_request(
                    plan=plan,
                    option_label=selected.label,
                    evidence=evidence.model_dump(mode="json"),
                    workspace=workspace,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("probe_revision_llm_failed case_id=%s error=%s", case_id, exc)
            turn = _fallback_probe_revision(plan=plan, option_label=selected.label)
        revision = {
            "kind": "probe_revision",
            "evidence_id": receipt.evidence_id,
            "plan_id": plan.plan_id,
            "source_probe_id": plan.source_probe_id,
            "affected_hidden_attributes": receipt.updated_hidden_attribute_ids,
            "chart_facts_modified": False,
            "turn": turn.model_dump(mode="json"),
        }
        record = record.model_copy(update={
            "user_evidence": [
                *record.user_evidence,
                {
                    "evidence_id": receipt.evidence_id,
                    "reference_only": True,
                    "authority": "LifeCase.reality_evidence",
                },
            ],
            "revisions": [*record.revisions, revision],
        })
        row["case_belief_state"] = workspace.model_dump(mode="json")
        row.pop("workspace", None)
        row["record"] = record.model_dump(mode="json")
        row["life_case"] = life_case.model_dump(mode="json")
        save_case_row(case_id=case_id, row=row, account=account)
        return {
            "status": "case_belief_updated",
            "receipt": receipt.model_dump(mode="json"),
            "evidence_created": evidence_created,
            "evidence_id": evidence.evidence_id,
            "revision": _public_revision(revision),
            "reading": {
                **_public_reading_view(
                    world=world,
                    record=record,
                    workspace=workspace,
                    probe_plan=plan,
                    life_case=life_case,
                    workspace_state=workspace_state_for(row, case_id=case_id, active_mode=active_mode),
                ),
                "latest_revision": _public_revision(revision),
            },
        }

    @router.post("/cases/{case_id}/temporal/select")
    def select_case_period(
        case_id: str,
        payload: TemporalSelectRequest,
        request: Request,
    ) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        life_case = life_case_for(row, write=True)
        active_mode = mode_for(account, payload.active_mode)
        try:
            period = normalize_period_key(payload.period_key)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        workspace_state = select_case_workspace_period(
            workspace=workspace_state_for(row, case_id=case_id, active_mode=active_mode),
            period_key=period,
        )
        life_case, snapshot, created = ensure_temporal_snapshot(
            life_case=life_case,
            period_key=period,
            system_period_key=workspace_state.system_period,
        )
        row["workspace_state"] = workspace_state.model_dump(mode="json")
        row["life_case"] = life_case.model_dump(mode="json")
        save_case_row(case_id=case_id, row=row, account=account)
        world = ChartWorldInstance.model_validate(row["world"])
        run_record = MingliCognitiveRecord.model_validate(row["record"])
        record = formal_projection_record(life_case=life_case, fallback_record=run_record)
        belief_state = workspace_for(row, record)
        return {
            "status": "temporal_context_selected",
            "case_id": case_id,
            "snapshot_created": created,
            "workspace_state": workspace_state.model_dump(mode="json"),
            "temporal_snapshot": snapshot.model_dump(mode="json"),
            "reading": _public_reading_view(
                world=world,
                record=record,
                workspace=belief_state,
                probe_plan=probe_planner.plan(
                    record=record,
                    role_mode=active_mode,
                    scenario="timing",
                    domain=LifeDomain.LIFE_TIMING,
                ),
                active_domain=LifeDomain.LIFE_TIMING,
                life_case=life_case,
                workspace_state=workspace_state,
            ),
        }

    @router.get("/cases/{case_id}/reality-evidence")
    def list_case_reality_evidence(
        case_id: str,
        request: Request,
        period_key: str | None = None,
    ) -> dict[str, Any]:
        row, _ = load_case(case_id, request)
        life_case = life_case_for(row, write=False)
        period = normalize_period_key(period_key) if period_key else None
        evidence = [
            item
            for item in life_case.reality_evidence
            if period is None or item.period_key == period
        ]
        return {
            "status": "reality_evidence_ready",
            "case_id": case_id,
            "period_key": period,
            "evidence": [item.model_dump(mode="json") for item in evidence],
        }

    @router.post("/cases/{case_id}/reality-evidence")
    def record_case_reality_evidence(
        case_id: str,
        payload: RealityEvidenceRequest,
        request: Request,
    ) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        life_case = life_case_for(row, write=True)
        active_mode = mode_for(account, payload.active_mode)
        if payload.source == "research" and active_mode != "research":
            raise HTTPException(status_code=403, detail="research_evidence_role_required")
        if payload.source == "practitioner" and active_mode not in {"practitioner", "research"}:
            raise HTTPException(status_code=403, detail="practitioner_evidence_role_required")
        try:
            evidence = build_reality_evidence(
                life_case=life_case,
                idempotency_key=payload.idempotency_key,
                source=payload.source,
                source_ref=payload.source_ref,
                summary=payload.summary,
                period_key=payload.period_key,
                domain=payload.domain,
                kind=payload.kind,
                occurred_at=payload.occurred_at,
                confirmation_status=payload.confirmation_status,
                severity=payload.severity,
                subjective_impact=payload.subjective_impact,
                structured_payload=payload.structured_payload,
            )
            life_case, evidence, created = upsert_reality_evidence(
                life_case=life_case,
                evidence=evidence,
            )
            workspace_state = workspace_state_for(row, case_id=case_id, active_mode=active_mode)
            life_case, snapshot, _ = ensure_temporal_snapshot(
                life_case=life_case,
                period_key=evidence.period_key,
                system_period_key=workspace_state.system_period,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        row["life_case"] = life_case.model_dump(mode="json")
        save_case_row(case_id=case_id, row=row, account=account)
        return {
            "status": "reality_evidence_recorded" if created else "reality_evidence_idempotent",
            "case_id": case_id,
            "created": created,
            "evidence": evidence.model_dump(mode="json"),
            "temporal_snapshot": snapshot.model_dump(mode="json"),
            "formal_authority": "LifeCase.reality_evidence",
        }

    @router.post("/cases/{case_id}/monthly-review")
    def review_case_month(
        case_id: str,
        payload: MonthlyReviewRequest,
        request: Request,
    ) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        life_case = life_case_for(row, write=True)
        try:
            life_case, review, candidate = complete_monthly_review(
                life_case=life_case,
                period_key=payload.period_key,
                temporal_snapshot_id=payload.temporal_snapshot_id,
                evidence_refs=payload.evidence_refs,
                verdict=payload.verdict,
                user_note=payload.user_note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        row["life_case"] = life_case.model_dump(mode="json")
        save_case_row(case_id=case_id, row=row, account=account)
        return {
            "status": "case_revision_candidate_ready",
            "case_id": case_id,
            "monthly_review": review.model_dump(mode="json"),
            "candidate": candidate.model_dump(mode="json"),
            "auto_committed": False,
        }

    @router.post("/cases/{case_id}/case-revisions/commit")
    def commit_case_revision_candidate(
        case_id: str,
        payload: CaseRevisionCommitRequest,
        request: Request,
    ) -> dict[str, Any]:
        row, account = load_case(case_id, request)
        life_case = life_case_for(row, write=True)
        world = ChartWorldInstance.model_validate(row["world"])
        try:
            insight = build_case_revision_insight(
                life_case=life_case,
                candidate_id=payload.candidate_id,
            )
            life_case, receipt = commit_case_revision(
                life_case=life_case,
                insight=insight,
                world=world,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        row["life_case"] = life_case.model_dump(mode="json")
        save_case_row(case_id=case_id, row=row, account=account)
        return {
            "status": "life_case_revision_committed",
            "case_id": case_id,
            "case_version": life_case.case_version,
            "insight": insight.model_copy(update={"status": "committed"}).model_dump(mode="json"),
            "validation": receipt.model_dump(mode="json"),
            "previous_versions": [item.model_dump(mode="json") for item in life_case.version_history],
        }

    @router.post("/cases/{case_id}/claim")
    def claim_case(case_id: str, request: Request) -> dict[str, Any]:
        account = account_for(request)
        if account is None:
            raise HTTPException(status_code=401, detail="authentication_required")
        row = case_store.get(case_id=case_id)
        if row is None:
            raise HTTPException(status_code=404, detail="mingli_case_not_found")
        life_case_for(row, write=True)
        profile_id = row.get("profile_id")
        profile = None
        if not profile_id:
            birth_input = BirthInputCanonical.model_validate(row["birth_input"])
            profile = product_store.save_profile(user_id=str(account["user_id"]), birth_input=birth_input)
            profile_id = str(profile["profile_id"])
            row["profile_id"] = profile_id
        else:
            profile = product_store.get_profile(user_id=str(account["user_id"]), profile_id=str(profile_id))
        save_case_row(case_id=case_id, row=row, account=account)
        return {"status": "case_claimed", "case_id": case_id, "profile_id": profile_id, "profile": profile}

    return router
