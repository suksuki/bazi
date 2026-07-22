from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import ChartWorldInstance, MingliAgent, ProbePlanner
from product.agent_api_context import AgentApiContext
from product.agent_case_store import AgentCaseStore
from product.agent_command_service import (
    BaselineAssertionReconciliationService,
    BaselineCaseCommandService,
    DomainExplorationCommandService,
)
from product.agent_job_store import AgentJobStore
from product.agent_jobs import AgentJobRunner
from product.formal_insight_state import cognition_background
from product.product_store import ProductStore


class WorkspaceBaselineStartError(ValueError):
    pass


@dataclass(frozen=True)
class AgentRuntimeServices:
    context: AgentApiContext
    agent: MingliAgent
    probe_planner: ProbePlanner
    baseline_commands: BaselineCaseCommandService
    domain_commands: DomainExplorationCommandService
    jobs: AgentJobRunner
    workspace_baseline: "WorkspaceBaselineCoordinator"


class WorkspaceBaselineCoordinator:
    """Start or locally reconcile one missing Workspace baseline."""

    def __init__(
        self,
        *,
        context: AgentApiContext,
        jobs: AgentJobRunner,
    ) -> None:
        self._context = context
        self._jobs = jobs
        self._reconciler = BaselineAssertionReconciliationService()

    def start(
        self,
        *,
        case_id: str,
        account: dict[str, object],
    ) -> dict[str, Any]:
        user_id = str(account["user_id"])
        row = self._context.case_store.get(case_id=case_id, user_id=user_id)
        if row is None:
            raise WorkspaceBaselineStartError("mingli_case_not_found")
        if _has_committed_baseline(row):
            return _result("baseline_cache_reused", case_id)

        background = row.get("background_cognition")
        background = background if isinstance(background, dict) else {}
        existing_job_id = str(background.get("job_id") or "")
        if existing_job_id:
            existing_job = self._context.job_store.get(
                job_id=existing_job_id,
                user_id=user_id,
            )
            job_status = str((existing_job or {}).get("status") or background.get("status") or "")
            if job_status in {"queued", "running"}:
                return _result(
                    "baseline_preparing",
                    case_id,
                    job_id=existing_job_id,
                )

        if row.get("record"):
            reconciled = self._reconciler.reconcile(
                row=row,
                profile_id=str(row.get("profile_id") or "") or None,
            )
            self._context.save_case_row(
                case_id=case_id,
                row=reconciled.row,
                account=account,
            )
            return _result(
                "baseline_reconciled" if reconciled.committed else "baseline_partial",
                case_id,
                isolated_assertion_count=reconciled.isolated_assertion_count,
            )

        if existing_job_id or int(background.get("attempt_count") or 0) > 0:
            return _result(
                "baseline_unavailable",
                case_id,
                job_id=existing_job_id,
            )

        try:
            birth_input = BirthInputCanonical.model_validate(row["birth_input"])
            world = ChartWorldInstance.model_validate(row["world"])
        except Exception as exc:  # noqa: BLE001 - persisted boundary is explicit.
            raise WorkspaceBaselineStartError("workspace_chart_case_invalid") from exc

        profile_id = str(row.get("profile_id") or "")
        profile = (
            self._context.product_store.get_profile(
                user_id=user_id,
                profile_id=profile_id,
            )
            if profile_id
            else None
        )
        job_id = "cognitive-job-" + hashlib.sha256(
            f"flow-slim-baseline-v1|{case_id}|{world.world_id}".encode("utf-8")
        ).hexdigest()[:20]
        try:
            self._context.job_store.create(
                job_id=job_id,
                case_id=case_id,
                user_id=user_id,
                payload={
                    "version": "deepbazi.progressive_cognitive_job.v1",
                    "reading_id": world.reading_id,
                    "active_mode": self._context.mode_for(account),
                    "profile_id": profile_id,
                    "entry_protocol": "flow_slim_background_baseline_v1",
                },
            )
        except Exception as exc:  # noqa: BLE001 - stable ID deduplicates concurrent starts.
            existing = self._context.job_store.get(job_id=job_id, user_id=user_id)
            if existing is None:
                raise WorkspaceBaselineStartError("baseline_job_create_failed") from exc
            return _result("baseline_preparing", case_id, job_id=job_id)

        row["background_cognition"] = cognition_background(
            background,
            operational_status="queued",
            insight_status="draft",
            attempt_count=1,
            job_id=job_id,
            reason="valid_baseline_missing",
        )
        self._context.save_case_row(case_id=case_id, row=row, account=account)
        self._jobs.submit_baseline(
            job_id=job_id,
            case_id=case_id,
            reading_id=world.reading_id,
            birth_input=birth_input,
            profile=profile,
            user_id=user_id,
            active_mode=self._context.mode_for(account),
            world=world,
        )
        return _result(
            "baseline_preparing",
            case_id,
            job_id=job_id,
            llm_calls_started=1,
        )


def build_agent_runtime(
    *,
    product_store: ProductStore,
    session_cookie: str,
    agent: MingliAgent,
    case_store: AgentCaseStore,
    job_store: AgentJobStore,
) -> AgentRuntimeServices:
    context = AgentApiContext(
        product_store=product_store,
        case_store=case_store,
        job_store=job_store,
        session_cookie=session_cookie,
    )
    probe_planner = ProbePlanner()
    baseline_commands = BaselineCaseCommandService(agent=agent, case_store=case_store)
    domain_commands = DomainExplorationCommandService(agent=agent, case_store=case_store)
    jobs = AgentJobRunner(
        context=context,
        baseline_commands=baseline_commands,
        probe_planner=probe_planner,
    )
    return AgentRuntimeServices(
        context=context,
        agent=agent,
        probe_planner=probe_planner,
        baseline_commands=baseline_commands,
        domain_commands=domain_commands,
        jobs=jobs,
        workspace_baseline=WorkspaceBaselineCoordinator(context=context, jobs=jobs),
    )


def _has_committed_baseline(row: dict[str, Any]) -> bool:
    life_case = row.get("life_case")
    if not isinstance(life_case, dict):
        return False
    baseline = life_case.get("baseline_insight")
    chart_version = life_case.get("chart_version")
    return bool(
        life_case.get("status") == "active"
        and isinstance(chart_version, dict)
        and chart_version.get("active") is True
        and isinstance(baseline, dict)
        and baseline.get("status") == "committed"
        and isinstance(baseline.get("professional_review_overlay"), dict)
        and baseline.get("professional_release_status") in {"passed", "partially_blocked"}
    )


def _result(
    status: str,
    case_id: str,
    *,
    job_id: str = "",
    llm_calls_started: int = 0,
    isolated_assertion_count: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "case_id": case_id,
        "job_id": job_id,
        "llm_calls_started": llm_calls_started,
    }
    if isolated_assertion_count is not None:
        payload["isolated_assertion_count"] = isolated_assertion_count
    return payload


__all__ = [
    "AgentRuntimeServices",
    "WorkspaceBaselineCoordinator",
    "WorkspaceBaselineStartError",
    "build_agent_runtime",
]
