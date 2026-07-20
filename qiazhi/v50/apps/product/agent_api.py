from __future__ import annotations

import os
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from product.agent_case_store import AgentCaseStore, build_agent_case_store
from product.agent_job_store import AgentJobStore, build_agent_job_store
from product.product_store import ProductStore, birth_input_from_profile
from product.reading_projection import project_living_reading
from core.abu_runtime import AbuCapabilityRegistry, AbuRuntimeContext, resolve_abu_command
from core.contracts import BirthInputCanonical
from core.engines import BirthCalendarResolutionError, resolve_birth_input_pillars
from core.mingli_agent import (
    BirthIntakeDraft,
    CaseCognitiveWorkspace,
    ChartWorldInstance,
    MingliAgent,
    MingliCognitiveRecord,
    OllamaCognitiveModel,
    ProbePlan,
    ProbePlanner,
    apply_deliberation_selection,
    apply_probe_response,
    build_deliberation_view,
    build_case_workspace,
    compile_chart_world,
    undo_deliberation_selection,
)
from core.life_domains import LifeDomain, domain_access_allowed, domain_definition, domain_manifest
from core.life_case import (
    LifeCase,
    build_baseline_insight,
    build_case_revision_insight,
    build_domain_insight,
    build_reality_evidence,
    build_workspace_state,
    commit_baseline_life_case,
    commit_case_revision,
    commit_domain_insight,
    complete_monthly_review,
    ensure_temporal_snapshot,
    formal_projection_record,
    normalize_period_key,
    project_life_case,
    select_workspace_period,
    upsert_reality_evidence,
    validate_formal_insight,
    WorkspaceState,
)
from core.mingli_agent.reasoner import sanitize_public_mingli_payload
from core.mingli_agent.contracts import CaseTurnDraft


AGENT_API_PREFIX = "/api/v50/agent"
LOGGER = logging.getLogger(__name__)


class IntakeRequest(BaseModel):
    message: str = Field(min_length=1, max_length=800)
    current_draft: BirthIntakeDraft | None = None


class CaseStartRequest(BaseModel):
    birth_input: BirthInputCanonical | None = None
    profile_id: str | None = None
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None
    progressive: bool = False


class CaseTurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None


class ProbePlanRequest(BaseModel):
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None
    scenario: Literal["recognition", "domain", "timing", "falsification", "decision"] = "recognition"
    domain: LifeDomain = LifeDomain.WHOLE_CHART


class ProbeResponseRequest(ProbePlanRequest):
    plan_id: str
    option_id: str
    year_value: int | None = Field(default=None, ge=1900, le=2100)
    event_note: str = Field(default="", max_length=300)
    recurrence_count: int | None = Field(default=None, ge=0, le=99)


class DomainExploreRequest(BaseModel):
    user_question: str = Field(default="", max_length=600)
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None
    progressive: bool = False


class DeliberationSelectionRequest(BaseModel):
    active_mode: Literal["practitioner", "research"]
    stage_id: Literal["pattern", "useful_god", "work_path", "ziwei_focus", "domain_assertion"]
    option_id: str = Field(min_length=1, max_length=240)
    action: Literal["select", "support", "challenge", "defer", "research_fork"]
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART
    rationale: str = Field(default="", max_length=600)


class DeliberationUndoRequest(BaseModel):
    active_mode: Literal["practitioner", "research"]
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART


class AbuResolveRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    has_case: bool = False
    has_profile: bool = False
    active_mode: Literal["guest", "member", "practitioner", "research"] = "guest"
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART


class TemporalSelectRequest(BaseModel):
    period_key: str = Field(min_length=7, max_length=7)
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None


class RealityEvidenceRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=180)
    source: Literal["page", "abu", "probe", "monthly_review", "practitioner", "research", "import"]
    summary: str = Field(min_length=1, max_length=800)
    period_key: str = Field(min_length=7, max_length=7)
    domain: str = Field(default="whole_chart", max_length=80)
    source_ref: str = Field(default="", max_length=180)
    kind: str = Field(default="life_event", max_length=80)
    occurred_at: str = Field(default="", max_length=64)
    confirmation_status: Literal["reported", "confirmed", "corrected", "withdrawn"] = "reported"
    severity: Literal["low", "medium", "high", "unknown"] = "unknown"
    subjective_impact: str = Field(default="", max_length=600)
    structured_payload: dict[str, Any] = Field(default_factory=dict)
    active_mode: Literal["guest", "member", "practitioner", "research"] | None = None


class MonthlyReviewRequest(BaseModel):
    period_key: str = Field(min_length=7, max_length=7)
    temporal_snapshot_id: str = Field(min_length=1, max_length=180)
    evidence_refs: list[str] = Field(default_factory=list)
    verdict: Literal[
        "supported",
        "partially_supported",
        "not_observed",
        "contradicted",
        "insufficient_evidence",
    ]
    user_note: str = Field(default="", max_length=800)


class CaseRevisionCommitRequest(BaseModel):
    candidate_id: str = Field(min_length=1, max_length=180)


def _cognitive_failure_message(stage: str) -> str:
    return {
        "chart_compilation": "命盘事实没有完整建立。请检查出生信息后重新开始。",
        "baseline_cognition": "本轮没有形成足够可靠的整盘基线。命盘事实仍然保留，但系统不会用套话补成结论。",
        "formal_insight_validation": "整盘初步认知没有通过事实引用与版本检查，因此没有写入长期案例。",
        "pattern_hypothesis": "第一眼判断没有通过命盘事实检查，因此本轮已经停止，没有拿错误结论继续推演。",
        "work_path": "主作用路径没有通过一致性检查，因此本轮已经停止。已经形成的第一眼候选仍会保留在任务记录中。",
        "ziwei_lens": "八字与紫微的本轮参看没有完整完成，因此不会强行合并结论。",
        "prior_probe": "整盘判断没有形成可验证的现实问题，因此本轮已经停止。",
        "career_domain": "事业专题没有通过事实与证据检查，因此不会输出不完整判断。",
        "wealth_domain": "财富专题没有通过事实与证据检查，因此不会输出不完整判断。",
        "epistemic_review": "最终事实与证据检查没有通过，因此本轮结果不会作为完整测算展示。",
    }.get(stage, "本次深度认知没有完成。已经形成的阶段结果会保留，但不会冒充完整判断。")


def create_agent_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    agent: MingliAgent | None = None,
    case_store: AgentCaseStore | None = None,
    job_store: AgentJobStore | None = None,
) -> APIRouter:
    router = APIRouter(prefix=AGENT_API_PREFIX, tags=["mingli-agent"])
    injected_agent = agent is not None
    agent = agent or MingliAgent()
    case_store = case_store or build_agent_case_store()
    job_store = job_store or build_agent_job_store()
    recovered_interrupted_jobs = job_store.recover_interrupted()
    job_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="v50-cognitive-job")
    progressive_lock = threading.Lock()
    intake_agent = agent if injected_agent else MingliAgent(
        OllamaCognitiveModel(
            base_url=os.getenv("V50_MINGLI_AGENT_BASE_URL", "http://dblife.com:11888"),
            model=os.getenv("V50_ABU_INTAKE_MODEL", "qwen3:8b"),
            timeout_seconds=int(os.getenv("V50_ABU_INTAKE_TIMEOUT_SECONDS", "45")),
            num_ctx=8192,
        )
    )
    probe_planner = ProbePlanner()
    capability_registry = AbuCapabilityRegistry()

    def account_for(request: Request) -> dict[str, object] | None:
        token = request.cookies.get(session_cookie, "")
        return product_store.account_for_token(token) if token else None

    def load_case(case_id: str, request: Request) -> tuple[dict[str, Any], dict[str, object] | None]:
        account = account_for(request)
        row = case_store.get(case_id=case_id, user_id=str(account["user_id"]) if account else None)
        if row is None:
            raise HTTPException(status_code=404, detail="mingli_case_not_found")
        return row, account

    def mode_for(account: dict[str, object] | None, requested: str | None = None) -> str:
        role = str((account or {}).get("account_role") or "guest")
        allowed = {
            "guest": {"guest"},
            "member": {"member"},
            "practitioner": {"practitioner"},
            "research_master": {"research"},
            "admin": {"guest", "member", "practitioner", "research"},
        }.get(role, {"member"})
        defaults = {
            "guest": "guest",
            "member": "member",
            "practitioner": "practitioner",
            "research_master": "research",
            "admin": "member",
        }
        selected = requested or defaults.get(role, "member")
        if selected not in allowed:
            raise HTTPException(status_code=403, detail="product_mode_not_allowed")
        return selected

    def workspace_for(row: dict[str, Any], record: MingliCognitiveRecord) -> CaseCognitiveWorkspace:
        payload = row.get("case_belief_state") or row.get("workspace")
        return CaseCognitiveWorkspace.model_validate(payload) if payload else build_case_workspace(record)

    def workspace_state_for(
        row: dict[str, Any],
        *,
        case_id: str,
        active_mode: str = "member",
    ) -> WorkspaceState:
        payload = row.get("workspace_state")
        workspace_state = (
            WorkspaceState.model_validate(payload)
            if payload
            else build_workspace_state(case_id=case_id, active_mode=active_mode)
        )
        return (
            workspace_state.model_copy(update={"active_mode": active_mode})
            if workspace_state.active_mode != active_mode
            else workspace_state
        )

    def life_case_for(row: dict[str, Any], *, write: bool = False) -> LifeCase:
        payload = row.get("life_case")
        if not payload:
            raise HTTPException(status_code=409, detail="formal_life_case_not_available")
        life_case = LifeCase.model_validate(payload)
        if write and (life_case.status != "active" or not life_case.chart_version.active):
            raise HTTPException(status_code=409, detail="life_case_read_only")
        return life_case

    def save_case_row(
        *,
        case_id: str,
        row: dict[str, Any],
        account: dict[str, object] | None,
    ) -> None:
        row.pop("workspace", None)
        case_store.save(
            case_id=case_id,
            user_id=str(account["user_id"]) if account else row.get("user_id"),
            profile_id=row.get("profile_id"),
            payload=row,
        )

    def append_job_event(
        *,
        job_id: str,
        event_type: str,
        payload: dict[str, Any],
        epistemic_status: str,
        job_status: str | None = None,
    ) -> None:
        job_store.append_event(
            job_id=job_id,
            event={
                "event_type": event_type,
                "epistemic_status": epistemic_status,
                "payload": payload,
            },
            status=job_status,
        )

    def run_progressive_case(
        *,
        job_id: str,
        case_id: str,
        reading_id: str,
        birth_input: BirthInputCanonical,
        profile: dict[str, object] | None,
        user_id: str | None,
        active_mode: str,
    ) -> None:
        current_stage = "chart_compilation"
        try:
            with progressive_lock:
                world = compile_chart_world(reading_id=reading_id, birth_input=birth_input)
                append_job_event(
                    job_id=job_id,
                    event_type="chart_ready",
                    epistemic_status="accepted",
                    job_status="running",
                    payload={
                        "pillars": world.pillars,
                        "world_id": world.world_id,
                        "profile_id": str(profile.get("profile_id")) if profile else None,
                        "ziwei": {
                            "status": world.ziwei_profile.get("status", "unavailable"),
                            "reasoning_ready": bool(world.ziwei_profile.get("reasoning_ready")),
                            "calculator": world.ziwei_profile.get("calculator"),
                            "life_palace": world.ziwei_profile.get("life_palace"),
                            "body_palace": world.ziwei_profile.get("body_palace"),
                            "warnings": list(world.ziwei_profile.get("warnings") or []),
                        },
                    },
                )
                current_stage = "baseline_cognition"

                def on_stage(event_type: str, stage_payload: dict[str, Any]) -> None:
                    nonlocal current_stage
                    append_job_event(
                        job_id=job_id,
                        event_type=event_type,
                        epistemic_status=(
                            "provisional"
                            if event_type in {
                                "baseline_preview_ready",
                                "baseline_draft_ready",
                                "formal_insight_draft_ready",
                                "pattern_candidates_ready",
                            }
                            else "accepted"
                        ),
                        payload=stage_payload,
                    )
                    current_stage = {
                        "baseline_preview_ready": "baseline_cognition",
                        "baseline_draft_ready": "formal_insight_validation",
                        "baseline_validated": "formal_insight_validation",
                        "pattern_preview_ready": "pattern_hypothesis",
                        "pattern_candidates_ready": "work_path",
                        "work_path_ready": "ziwei_lens",
                        "work_path_unavailable": "ziwei_lens",
                        "ziwei_lens_ready": "prior_probe",
                        "ziwei_unavailable": "prior_probe",
                        "prior_probe_ready": "epistemic_review",
                        "whole_chart_ready": "epistemic_review",
                    }.get(event_type, current_stage)

                record = agent.first_baseline_reading(case_id=case_id, world=world, on_stage=on_stage)
                insight_draft = build_baseline_insight(record=record, world=world)
                append_job_event(
                    job_id=job_id,
                    event_type="formal_insight_draft_ready",
                    epistemic_status="provisional",
                    payload={
                        "status": "draft",
                        "insight_id": insight_draft.insight_id,
                        "claim": insight_draft.claim,
                        "persisted": False,
                    },
                )
                current_stage = "formal_insight_validation"
                workspace = build_case_workspace(record)
                if not record.review.commit_eligible:
                    validation = validate_formal_insight(insight=insight_draft, world=world)
                    row = {
                        "case_id": case_id,
                        "profile_id": str(profile.get("profile_id")) if profile else None,
                        "birth_input": birth_input.model_dump(mode="json"),
                        "world": world.model_dump(mode="json"),
                        "record": record.model_dump(mode="json"),
                        "case_belief_state": workspace.model_dump(mode="json"),
                        "workspace_state": build_workspace_state(
                            case_id=case_id,
                            active_mode=active_mode,
                        ).model_dump(mode="json"),
                        "life_case": None,
                        "insight_validation": validation.model_dump(mode="json"),
                        "first_run": {
                            "protocol": "single_call_baseline_v1",
                            "blocking_core_llm_calls": len(record.stage_receipts),
                            "unselected_domains_precomputed": False,
                        },
                        "status": record.review.disposition,
                    }
                    case_store.save(
                        case_id=case_id,
                        user_id=user_id,
                        profile_id=row["profile_id"],
                        payload=row,
                    )
                    outcome = _reliability_outcome_payload(world=world, record=record)
                    payload: dict[str, Any] = {
                        "outcome": outcome,
                        "validation": validation.model_dump(mode="json"),
                        "persisted_as_formal_insight": False,
                    }
                    if record.review.disposition == "competing":
                        payload["reading"] = _public_reading_view(
                            world=world,
                            record=record,
                            workspace=workspace,
                            probe_plan=probe_planner.plan(record=record, role_mode=active_mode),
                        )
                    append_job_event(
                        job_id=job_id,
                        event_type=(
                            "baseline_competing"
                            if record.review.disposition == "competing"
                            else "baseline_blocked"
                        ),
                        epistemic_status=record.review.disposition,
                        job_status="completed",
                        payload=payload,
                    )
                    return
                life_case, validation = commit_baseline_life_case(
                    insight=insight_draft,
                    world=world,
                    profile_id=str(profile.get("profile_id")) if profile else None,
                )
                append_job_event(
                    job_id=job_id,
                    event_type="baseline_validated",
                    epistemic_status="accepted",
                    payload={
                        "status": "validated",
                        "validation": validation.model_dump(mode="json"),
                        "persisted": False,
                    },
                )
                row = {
                    "case_id": case_id,
                    "profile_id": str(profile.get("profile_id")) if profile else None,
                    "birth_input": birth_input.model_dump(mode="json"),
                    "world": world.model_dump(mode="json"),
                    "record": record.model_dump(mode="json"),
                    "case_belief_state": workspace.model_dump(mode="json"),
                    "workspace_state": build_workspace_state(
                        case_id=case_id,
                        active_mode=active_mode,
                    ).model_dump(mode="json"),
                    "life_case": life_case.model_dump(mode="json"),
                    "insight_validation": validation.model_dump(mode="json"),
                    "first_run": {
                        "protocol": "single_call_baseline_v1",
                        "blocking_core_llm_calls": len(record.stage_receipts),
                        "unselected_domains_precomputed": False,
                    },
                    "status": "active",
                }
                case_store.save(
                    case_id=case_id,
                    user_id=user_id,
                    profile_id=row["profile_id"],
                    payload=row,
                )
                reading = _public_reading_view(
                    world=world,
                    record=record,
                    workspace=workspace,
                    probe_plan=probe_planner.plan(record=record, role_mode=active_mode),
                    life_case=life_case,
                )
                append_job_event(
                    job_id=job_id,
                    event_type="baseline_committed",
                    epistemic_status="completed",
                    job_status="completed",
                    payload={
                        "reading": reading,
                        "life_case_id": life_case.life_case_id,
                        "insight_id": life_case.baseline_insight.insight_id,
                        "blocking_core_llm_calls": len(record.stage_receipts),
                    },
                )
        except Exception as exc:  # noqa: BLE001 - the partial cognition remains visible and recoverable.
            LOGGER.exception("progressive_mingli_cognition_failed job_id=%s case_id=%s", job_id, case_id)
            append_job_event(
                job_id=job_id,
                event_type="reading_failed",
                epistemic_status="failed",
                job_status="failed",
                payload={
                    "failure_code": f"mingli_cognition_failed:{type(exc).__name__}",
                    "failure_stage": current_stage,
                    "message": _cognitive_failure_message(current_stage),
                },
            )

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
            "production_first_run_protocol": "single_call_baseline_v1",
            "first_run_blocking_core_llm_call_budget": 1,
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
            job_executor.submit(
                run_progressive_case,
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
            world = compile_chart_world(reading_id=reading_id, birth_input=birth_input)
            record = agent.first_baseline_reading(case_id=case_id, world=world)
        except Exception as exc:  # noqa: BLE001 - cognition failure must not become a template fallback.
            raise HTTPException(status_code=503, detail=f"mingli_cognition_failed:{type(exc).__name__}:{exc}") from exc
        insight_draft = build_baseline_insight(record=record, world=world)
        workspace = build_case_workspace(record)
        if not record.review.commit_eligible:
            validation = validate_formal_insight(insight=insight_draft, world=world)
            row = {
                "case_id": case_id,
                "profile_id": str(profile.get("profile_id")) if profile else None,
                "birth_input": birth_input.model_dump(mode="json"),
                "world": world.model_dump(mode="json"),
                "record": record.model_dump(mode="json"),
                "case_belief_state": workspace.model_dump(mode="json"),
                "workspace_state": build_workspace_state(
                    case_id=case_id,
                    active_mode=active_mode,
                ).model_dump(mode="json"),
                "life_case": None,
                "insight_validation": validation.model_dump(mode="json"),
                "first_run": {
                    "protocol": "single_call_baseline_v1",
                    "blocking_core_llm_calls": len(record.stage_receipts),
                    "unselected_domains_precomputed": False,
                },
                "status": record.review.disposition,
            }
            case_store.save(
                case_id=case_id,
                user_id=str(account["user_id"]) if account else None,
                profile_id=row["profile_id"],
                payload=row,
            )
            response: dict[str, Any] = {
                "status": f"baseline_{record.review.disposition}",
                "case_id": case_id,
                "saved": account is not None,
                "profile": profile,
                "outcome": _reliability_outcome_payload(world=world, record=record),
            }
            if record.review.disposition == "competing":
                response["reading"] = _public_reading_view(
                    world=world,
                    record=record,
                    workspace=workspace,
                    probe_plan=probe_planner.plan(record=record, role_mode=active_mode),
                )
            return response
        life_case, validation = commit_baseline_life_case(
            insight=insight_draft,
            world=world,
            profile_id=str(profile.get("profile_id")) if profile else None,
        )
        row = {
            "case_id": case_id,
            "profile_id": str(profile.get("profile_id")) if profile else None,
            "birth_input": birth_input.model_dump(mode="json"),
            "world": world.model_dump(mode="json"),
            "record": record.model_dump(mode="json"),
            "case_belief_state": workspace.model_dump(mode="json"),
            "workspace_state": build_workspace_state(
                case_id=case_id,
                active_mode=active_mode,
            ).model_dump(mode="json"),
            "life_case": life_case.model_dump(mode="json"),
            "insight_validation": validation.model_dump(mode="json"),
            "first_run": {
                "protocol": "single_call_baseline_v1",
                "blocking_core_llm_calls": len(record.stage_receipts),
                "unselected_domains_precomputed": False,
            },
            "status": "active",
        }
        case_store.save(
            case_id=case_id,
            user_id=str(account["user_id"]) if account else None,
            profile_id=row["profile_id"],
            payload=row,
        )
        return {
            "status": "first_reading_ready",
            "case_id": case_id,
            "saved": account is not None,
            "profile": profile,
            "reading": _public_reading_view(
                world=world,
                record=record,
                workspace=workspace,
                probe_plan=probe_planner.plan(record=record, role_mode=active_mode),
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
        row.pop("workspace", None)
        case_store.save(
            case_id=case_id,
            user_id=str(account["user_id"]),
            profile_id=row.get("profile_id"),
            payload=row,
        )
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
        row.pop("workspace", None)
        case_store.save(
            case_id=case_id,
            user_id=str(account["user_id"]),
            profile_id=row.get("profile_id"),
            payload=row,
        )
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
        world = ChartWorldInstance.model_validate(row["world"])
        record = MingliCognitiveRecord.model_validate(row["record"])
        if not _is_domain_eligible(row):
            raise HTTPException(status_code=409, detail="cognitive_record_requires_recompute")
        workspace = workspace_for(row, record)
        active_mode = mode_for(account, payload.active_mode)
        workspace_state = workspace_state_for(row, case_id=case_id, active_mode=active_mode).model_copy(update={
            "active_domain": domain.value,
            "active_mode": active_mode,
            "conversation_focus": f"domain:{domain.value}",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        row["workspace_state"] = workspace_state.model_dump(mode="json")
        if not domain_access_allowed(domain, role_mode=active_mode):
            raise HTTPException(status_code=403, detail="domain_not_available_for_product_mode")
        previous_exploration = record.domain_explorations.get(domain)
        life_case = LifeCase.model_validate(row["life_case"])
        try:
            exploration = agent.explore_domain(
                world=world,
                record=record,
                domain=domain,
                user_question=payload.user_question,
                baseline_insight_id=life_case.baseline_insight.insight_id,
                baseline_case_version=life_case.case_version,
                chart_version_id=life_case.chart_version.version_id,
                temporal_scope=(
                    workspace_state_for(row, case_id=case_id, active_mode=active_mode).selected_period
                    if domain is LifeDomain.LIFE_TIMING
                    else "current"
                ),
                on_stage=on_stage,
            )
        except Exception as exc:  # noqa: BLE001 - failed reasoning is visible and never replaced by a template.
            raise HTTPException(status_code=503, detail=f"domain_reasoning_failed:{type(exc).__name__}:{exc}") from exc
        if not exploration.review.commit_eligible or exploration.case_revision_candidate:
            pending = dict(row.get("pending_domain_explorations") or {})
            pending[domain.value] = exploration.model_dump(mode="json")
            row["pending_domain_explorations"] = pending
            if exploration.case_revision_candidate:
                row["case_revision_candidates"] = [
                    *(row.get("case_revision_candidates") or []),
                    exploration.case_revision_candidate,
                ]
            case_store.save(
                case_id=case_id,
                user_id=str(account["user_id"]) if account else row.get("user_id"),
                profile_id=row.get("profile_id"),
                payload=row,
            )
            return {
                "status": (
                    "case_revision_candidate"
                    if exploration.case_revision_candidate
                    else f"domain_{exploration.review.disposition}"
                ),
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
                        {"code": item.code, "message": item.message, "category": item.category}
                        for item in exploration.review.issues
                    ],
                },
                "reading": _public_reading_view(
                    world=world,
                    record=record,
                    workspace=workspace,
                    probe_plan=probe_planner.plan(record=record, role_mode=active_mode),
                    active_domain=LifeDomain.WHOLE_CHART,
                    life_case=life_case,
                    workspace_state=workspace_state,
                ),
            }
        record = record.model_copy(update={
            "domain_explorations": {**record.domain_explorations, domain: exploration},
            "revisions": [
                *record.revisions,
                {
                    "kind": "domain_exploration",
                    "domain": domain.value,
                    "user_question": payload.user_question,
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
            life_case, domain_validation = commit_domain_insight(
                life_case=life_case,
                insight=domain_insight,
                world=world,
            )
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=f"domain_insight_validation_failed:{exc}") from exc
        row["life_case"] = life_case.model_dump(mode="json")
        case_store.save(
            case_id=case_id,
            user_id=str(account["user_id"]) if account else row.get("user_id"),
            profile_id=row.get("profile_id"),
            payload=row,
        )
        return {
            "status": "domain_exploration_ready",
            "case_id": case_id,
            "domain": domain.value,
            "cache_hit": bool(previous_exploration and exploration.generated_at == previous_exploration.generated_at),
            "formal_insight": {
                "insight_id": domain_insight.insight_id,
                "status": "committed",
                "validation": domain_validation.model_dump(mode="json"),
            },
            "reading": _public_reading_view(
                world=world,
                record=record,
                workspace=workspace,
                probe_plan=probe_planner.plan(
                    record=record,
                    role_mode=active_mode,
                    scenario="timing" if domain is LifeDomain.LIFE_TIMING else "domain",
                    domain=domain,
                ),
                active_domain=domain,
                life_case=life_case,
                workspace_state=workspace_state,
            ),
        }

    def run_progressive_domain(
        *,
        job_id: str,
        case_id: str,
        domain: LifeDomain,
        payload: DomainExploreRequest,
        row: dict[str, Any],
        account: dict[str, object] | None,
    ) -> None:
        try:
            with progressive_lock:
                def on_stage(event_type: str, stage_payload: dict[str, Any]) -> None:
                    append_job_event(
                        job_id=job_id,
                        event_type=event_type,
                        epistemic_status="provisional" if event_type == "domain_preview_ready" else "accepted",
                        payload=stage_payload,
                        job_status="running",
                    )

                result = execute_domain_exploration(
                    case_id=case_id,
                    domain=domain,
                    payload=payload,
                    row=row,
                    account=account,
                    on_stage=on_stage,
                )
                event_type = {
                    "domain_exploration_ready": "domain_committed",
                    "domain_competing": "domain_competing",
                    "domain_blocked": "domain_blocked",
                    "case_revision_candidate": "domain_revision_candidate",
                }.get(result["status"], "domain_completed")
                append_job_event(
                    job_id=job_id,
                    event_type=event_type,
                    epistemic_status=(
                        "completed" if result["status"] == "domain_exploration_ready"
                        else (result.get("domain_outcome") or {}).get("state", "unresolved")
                    ),
                    payload=result,
                    job_status="completed",
                )
        except Exception as exc:  # noqa: BLE001 - a domain failure must remain visible.
            LOGGER.exception("progressive_domain_failed job_id=%s case_id=%s domain=%s", job_id, case_id, domain.value)
            detail = exc.detail if isinstance(exc, HTTPException) else f"{type(exc).__name__}:{exc}"
            append_job_event(
                job_id=job_id,
                event_type="domain_failed",
                epistemic_status="failed",
                payload={
                    "domain": domain.value,
                    "message": "本轮专题没有形成可靠结果，整盘基线仍然保留。",
                    "detail": str(detail),
                },
                job_status="failed",
            )

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
            job_executor.submit(
                run_progressive_domain,
                job_id=job_id,
                case_id=case_id,
                domain=domain,
                payload=payload,
                row=row,
                account=account,
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
        case_store.save(
            case_id=case_id,
            user_id=str(account["user_id"]) if account else row.get("user_id"),
            profile_id=row.get("profile_id"),
            payload=row,
        )
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
        case_store.save(
            case_id=case_id,
            user_id=str(account["user_id"]) if account else row.get("user_id"),
            profile_id=row.get("profile_id"),
            payload=row,
        )
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
        workspace_state = select_workspace_period(
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
        case_store.save(case_id=case_id, user_id=str(account["user_id"]), profile_id=profile_id, payload=row)
        return {"status": "case_claimed", "case_id": case_id, "profile_id": profile_id, "profile": profile}

    return router


def _public_reading_view(
    *,
    world: ChartWorldInstance,
    record: MingliCognitiveRecord,
    workspace: CaseCognitiveWorkspace,
    probe_plan: ProbePlan,
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART,
    life_case: LifeCase | dict[str, Any] | None = None,
    workspace_state: WorkspaceState | dict[str, Any] | None = None,
) -> dict[str, Any]:
    parsed_life_case = (
        life_case
        if isinstance(life_case, LifeCase)
        else LifeCase.model_validate(life_case)
        if life_case is not None
        else None
    )
    if parsed_life_case is not None:
        record = formal_projection_record(life_case=parsed_life_case, fallback_record=record)
    cognition = record.cognition
    primary = next((item for item in cognition.hypotheses if item.hypothesis_id == cognition.selected_hypothesis_id), cognition.hypotheses[0])
    hypothesis_beliefs = {item.hypothesis_id: item for item in workspace.hypothesis_beliefs}
    consumed = (
        probe_plan.source_probe_id in workspace.answered_probe_ids
        or any(item.source_probe_id == probe_plan.source_probe_id for item in workspace.probe_history)
    )
    latest_revision = next((item for item in reversed(record.revisions) if item.get("kind") == "probe_revision"), None)
    professional_mode = probe_plan.role_mode in {"practitioner", "research"}
    deliberation = build_deliberation_view(
        record=record,
        workspace=workspace,
        role_mode=probe_plan.role_mode,
        active_domain=active_domain,
    ).model_dump(mode="json") if professional_mode else None
    active_hypothesis_id = workspace.active_hypothesis_id if professional_mode else cognition.selected_hypothesis_id
    active_deliberation = {
        item.stage_key: item
        for item in workspace.deliberation_selections
        if item.active and item.action != "research_fork"
    }
    parsed_workspace_state = (
        workspace_state
        if isinstance(workspace_state, WorkspaceState)
        else WorkspaceState.model_validate(workspace_state)
        if workspace_state is not None
        else build_workspace_state(case_id=record.case_id, active_mode=probe_plan.role_mode)
    )
    selected_snapshot = (
        next(
            (
                item
                for item in reversed(parsed_life_case.temporal_snapshots)
                if item.period_key == parsed_workspace_state.selected_period and item.status == "active"
            ),
            None,
        )
        if parsed_life_case is not None
        else None
    )
    output = {
        "version": "deepbazi.living_reading.v1",
        "experience_mode": probe_plan.role_mode,
        "pillars": world.pillars,
        "first_look": cognition.first_look,
        "whole_chart_thesis": cognition.whole_chart_thesis,
        "lenses_available": {
            "bazi": True,
            "ziwei": bool(world.ziwei_profile.get("reasoning_ready")),
            "integrated": cognition.dual_lens is not None,
        },
        "ziwei_profile": world.ziwei_profile,
        "temporal_state": {
            "analysis_year": world.timing_context.get("analysis_year"),
            "annual_pillar": world.timing_context.get("annual_pillar"),
            "luck_pillar": world.timing_context.get("luck_pillar"),
            "luck_year_range": world.timing_context.get("luck_year_range"),
            "calculation_status": "ready",
            "interpretation_status": "not_generated",
            "system_period": parsed_workspace_state.system_period,
            "selected_period": parsed_workspace_state.selected_period,
            "selected_snapshot": selected_snapshot.model_dump(mode="json") if selected_snapshot else None,
        },
        "dual_lens": cognition.dual_lens.model_dump(mode="json") if cognition.dual_lens else None,
        "confidence": primary.confidence,
        "salient_phenomena": [item.model_dump(mode="json") for item in cognition.salient_phenomena],
        "hypotheses": [
            {
                **item.model_dump(mode="json"),
                "case_belief_direction": hypothesis_beliefs.get(item.hypothesis_id).current_direction if hypothesis_beliefs.get(item.hypothesis_id) else "unchanged",
                "professionally_selected": active_hypothesis_id == item.hypothesis_id and active_hypothesis_id != cognition.selected_hypothesis_id,
            }
            for item in cognition.hypotheses
        ],
        "selected_hypothesis_id": active_hypothesis_id,
        "system_selected_hypothesis_id": cognition.selected_hypothesis_id,
        "work_path": cognition.work_path.model_dump(mode="json"),
        "useful_god_reasoning": [item.model_dump(mode="json") for item in cognition.useful_god_reasoning],
        "portrait": [item.model_dump(mode="json") for item in cognition.portrait],
        "career": cognition.career.model_dump(mode="json") if cognition.career else None,
        "wealth": cognition.wealth.model_dump(mode="json") if cognition.wealth else None,
        "life_domains": domain_manifest(),
        "domain_explorations": {
            domain.value: _project_domain_exploration(exploration, role_mode=probe_plan.role_mode)
            for domain, exploration in record.domain_explorations.items()
            if domain_access_allowed(domain, role_mode=probe_plan.role_mode)
        },
        "prior_predictions": [item.model_dump(mode="json") for item in cognition.prior_predictions],
        "next_probe": cognition.next_probe.model_dump(mode="json"),
        "probe_plan": None if consumed else probe_plan.model_dump(mode="json"),
        "latest_revision": _public_revision(latest_revision) if latest_revision else None,
        "deliberation": deliberation,
        "latest_deliberation_revision": workspace.deliberation_revisions[-1].model_dump(mode="json") if professional_mode and workspace.deliberation_revisions else None,
        "workspace": {
            "active_hypothesis_id": workspace.active_hypothesis_id,
            "hypothesis_beliefs": [item.model_dump(mode="json") for item in workspace.hypothesis_beliefs],
            "assertion_beliefs": [item.model_dump(mode="json") for item in workspace.assertion_beliefs],
            "hidden_attribute_beliefs": [
                item.model_dump(mode="json")
                for item in workspace.hidden_attribute_beliefs
            ] if probe_plan.role_mode in {"practitioner", "research"} else [
                {
                    "attribute_id": item.attribute_id,
                    "lifecycle": item.lifecycle,
                    "confidence": item.confidence,
                }
                for item in workspace.hidden_attribute_beliefs
            ],
            "probe_response_count": len(workspace.probe_history),
            "revision_count": workspace.revision_count,
            "chart_facts_locked": workspace.chart_facts_locked,
            "global_update_allowed": workspace.global_update_allowed,
            "active_deliberation": {
                key: value.model_dump(mode="json")
                for key, value in active_deliberation.items()
            } if professional_mode else {},
        },
        "workspace_state": parsed_workspace_state.model_dump(mode="json"),
        "unresolved_questions": cognition.unresolved_questions,
        "review": record.review.model_dump(mode="json"),
        "reliability": {
            "state": record.reliability_disposition,
            "commit_eligible": record.review.commit_eligible,
            "semantic_signature": record.reliability_signature,
            "gate_version": record.review.gate_version,
            "hard_failure_codes": record.review.hard_failure_codes,
        },
        "revision_count": len(record.revisions),
        "cognitive_run": {
            "stage_count": len(record.stage_receipts),
            "context_count": len(record.context_manifest),
        },
    }
    if parsed_life_case is not None:
        output["life_case"] = project_life_case(parsed_life_case, role_mode=probe_plan.role_mode)
    sanitized = sanitize_public_mingli_payload(output)
    return project_living_reading(sanitized, mode=probe_plan.role_mode)


def _reliability_outcome_payload(
    *,
    world: ChartWorldInstance,
    record: MingliCognitiveRecord,
) -> dict[str, Any]:
    primary = next(
        (item for item in record.cognition.hypotheses if item.hypothesis_id == record.cognition.selected_hypothesis_id),
        record.cognition.hypotheses[0] if record.cognition.hypotheses else None,
    )
    alternatives = [
        {
            "hypothesis_id": item.hypothesis_id,
            "name": item.name,
            "thesis": item.thesis,
            "confidence": item.confidence,
            "supporting_evidence_refs": item.supporting_evidence_refs,
            "counter_evidence_refs": item.counter_evidence_refs,
            "success_conditions": item.success_conditions,
            "failure_conditions": item.failure_conditions,
        }
        for item in record.cognition.hypotheses
        if primary is None or item.hypothesis_id != primary.hypothesis_id
    ]
    return {
        "version": "deepbazi.mingli_reliability_outcome.v1",
        "state": record.reliability_disposition,
        "formal_insight_committed": False,
        "pillars": world.pillars,
        "world_id": world.world_id,
        "chart_facts_available": True,
        "primary_explanation": (
            {
                "hypothesis_id": primary.hypothesis_id,
                "name": primary.name,
                "thesis": primary.thesis,
                "confidence": primary.confidence,
                "success_conditions": primary.success_conditions,
                "failure_conditions": primary.failure_conditions,
            }
            if primary
            else None
        ),
        "competing_explanations": alternatives if record.reliability_disposition == "competing" else [],
        "uncertainties": record.cognition.unresolved_questions,
        "review": {
            "gate_version": record.review.gate_version,
            "hard_failure_codes": record.review.hard_failure_codes,
            "issues": [
                {
                    "code": item.code,
                    "message": item.message,
                    "category": item.category,
                    "blocks_commit": item.blocks_commit,
                }
                for item in record.review.issues
            ],
        },
    }


def _probe_revision_request(*, plan: ProbePlan, option_label: str, evidence: dict[str, Any], workspace: CaseCognitiveWorkspace) -> str:
    return f"""
[结构化案例证据复审]
这不是让你重新排盘，也不是让你迎合用户。请比较封存的先验命局认知与下面的新证据，只修正受影响的案例判断。

Probe 目标：{plan.purpose}
用户选择：{option_label}
证据：{evidence}
案例 Belief：{workspace.model_dump(mode='json')}

要求：
- interaction_type 必须是 feedback_revision；
- abu_message 简洁说明现在更倾向哪种理解；
- interpretation 明确什么改变、什么没有改变；
- changed_assertions 只包含真正受影响的案例断言；
- 不修改四柱、十神、时序计算或全局理论；
- 不重复用户原问题和完整回答；
- 若证据不足，明确保留两种解释，不假装已经确定；
- next_probe 只有在能显著区分剩余假设时才提供一个。
""".strip()


def _fallback_probe_revision(*, plan: ProbePlan, option_label: str) -> CaseTurnDraft:
    selected = next((item for item in plan.options if item.label == option_label), None)
    return CaseTurnDraft(
        interaction_type="feedback_revision",
        abu_message="这条现实线索已进入当前命盘的案例理解，但还不足以单独推翻整盘判断。",
        canvas_focus="overview",
        interpretation=f"当前只修正 {plan.domain.value} 范围内的表现方式；四柱、原局结构和全局理论保持不变。",
        hypothesis_updates=selected.hypothesis_updates if selected else {},
        changed_assertions=[],
        retained_assertion_ids=plan.target_assertion_ids,
        next_probe=None,
        suggested_actions=[],
        evidence_refs=[],
    )


def _public_revision(revision: dict[str, Any] | None) -> dict[str, Any] | None:
    if not revision:
        return None
    turn = revision.get("turn") or {}
    return {
        "revision_id": revision.get("evidence_id"),
        "summary": turn.get("abu_message") or "当前案例理解已修正。",
        "interpretation": turn.get("interpretation") or "原局事实保持不变。",
        "changed_assertions": [
            {
                "assertion_id": item.get("assertion_id"),
                "domain": item.get("domain"),
                "claim": item.get("claim"),
                "epistemic_status": item.get("epistemic_status"),
            }
            for item in turn.get("changed_assertions", [])
        ],
        "affected_hidden_attributes": revision.get("affected_hidden_attributes", []),
        "chart_facts_modified": False,
    }


def _project_domain_exploration(exploration, *, role_mode: str) -> dict[str, Any]:
    definition = domain_definition(exploration.domain)
    reading = exploration.reading.model_dump(mode="json")
    base = {
        "domain": exploration.domain.value,
        "name_zh": definition.name_zh,
        "readiness": definition.readiness.value,
        "public_depth": exploration.reasoning_protocol.get("public_depth"),
        "boundary": definition.boundary,
        "generated_at": exploration.generated_at,
        "reliability_state": exploration.reliability_disposition,
        "baseline_inheritance": {
            "baseline_insight_id": exploration.baseline_insight_id,
            "baseline_record_id": exploration.baseline_record_id,
            "case_version": exploration.baseline_case_version,
            "semantic_signature": exploration.baseline_semantic_signature,
        },
        "reading": reading,
    }
    if role_mode == "guest":
        base["reading"] = {
            "domain": reading["domain"],
            "core_question": reading["core_question"],
            "causal_chain": reading["causal_chain"],
            "stable_tendencies": reading["stable_tendencies"][:1],
            "opportunity_conditions": reading["opportunity_conditions"][:1],
            "risk_conditions": reading["risk_conditions"][:1],
            "timing_note": reading["timing_note"],
            "prior_directions": reading["prior_directions"][:1],
            "unknowns": reading["unknowns"][:1],
        }
    elif role_mode == "member":
        for assertion in base["reading"].get("assertions", []):
            assertion.pop("evidence_refs", None)
            assertion.pop("counter_evidence_refs", None)
    elif role_mode == "practitioner":
        base["review_summary"] = {
            "issue_count": len(exploration.review.issues),
            "fact_traceability_rate": exploration.review.fact_traceability_rate,
        }
        base["reasoning_protocol"] = exploration.reasoning_protocol
    else:
        base["review"] = exploration.review.model_dump(mode="json")
        base["reasoning_protocol"] = exploration.reasoning_protocol
        base["context_manifest"] = exploration.context_manifest
    return base


def _case_summary(row: dict[str, Any]) -> dict[str, Any]:
    record = MingliCognitiveRecord.model_validate(row["record"])
    birth = row.get("birth_input", {})
    life_case = LifeCase.model_validate(row["life_case"]) if row.get("life_case") else None
    first_look = life_case.baseline_insight.claim if life_case else record.cognition.first_look
    return {
        "case_id": row["case_id"],
        "profile_id": row.get("profile_id"),
        "display_name": birth.get("name") or "命理档案",
        "pillars": [birth.get("year_pillar"), birth.get("month_pillar"), birth.get("day_pillar"), birth.get("hour_pillar")],
        "first_look": first_look,
        "revision_count": len(life_case.revisions) if life_case else len(record.revisions),
        "reliability_state": record.reliability_disposition,
        "life_case_status": life_case.status if life_case else "uncommitted",
        "case_version": life_case.case_version if life_case else "",
        "read_only": bool(life_case and (life_case.status != "active" or not life_case.chart_version.active)),
    }


def _is_current_cognitive_record(row: dict[str, Any]) -> bool:
    record = row.get("record") or {}
    if not isinstance(record, dict) or record.get("version") not in {
        "deepbazi.mingli_cognitive_record.v2",
        "deepbazi.mingli_cognitive_record.v3",
    }:
        return False
    review = record.get("review") or {}
    if review.get("gate_version") != "mingli_reliability_gate_v1":
        return False
    disposition = record.get("reliability_disposition") or review.get("disposition")
    life_case_payload = row.get("life_case")
    if isinstance(life_case_payload, dict):
        try:
            life_case = LifeCase.model_validate(life_case_payload)
        except Exception:  # noqa: BLE001 - malformed stored contract is not current.
            return False
        if life_case.status != "active" or not life_case.chart_version.active:
            return False
    if disposition in {"blocked", "competing"}:
        return True
    receipts = record.get("stage_receipts") if isinstance(record, dict) else None
    required_stages = {"pattern_hypothesis", "work_path_portrait", "prediction_probe"}
    if record.get("version") == "deepbazi.mingli_cognitive_record.v2":
        required_stages.update({"career_reasoning", "wealth_reasoning"})
    completed = {
        str(item.get("stage"))
        for item in (receipts or [])
        if isinstance(item, dict) and item.get("status") == "completed"
    }
    if "baseline_cognition" in completed:
        life_case = row.get("life_case") or {}
        baseline = life_case.get("baseline_insight") if isinstance(life_case, dict) else None
        return bool(isinstance(baseline, dict) and baseline.get("status") == "committed")
    return required_stages.issubset(completed)


def _is_domain_eligible(row: dict[str, Any]) -> bool:
    if not _is_current_cognitive_record(row):
        return False
    record = row.get("record") or {}
    review = record.get("review") or {}
    if record.get("reliability_disposition") != "reliable" or not review.get("commit_eligible"):
        return False
    life_case = row.get("life_case") or {}
    baseline = life_case.get("baseline_insight") if isinstance(life_case, dict) else None
    return bool(
        isinstance(baseline, dict)
        and baseline.get("status") == "committed"
        and life_case.get("status") == "active"
        and (life_case.get("chart_version") or {}).get("active") is True
    )


def _is_historical_life_case(row: dict[str, Any]) -> bool:
    payload = row.get("life_case")
    if not isinstance(payload, dict):
        return False
    try:
        life_case = LifeCase.model_validate(payload)
    except Exception:  # noqa: BLE001 - malformed legacy rows are not formal history.
        return False
    return life_case.status in {"superseded", "archived"} or not life_case.chart_version.active
