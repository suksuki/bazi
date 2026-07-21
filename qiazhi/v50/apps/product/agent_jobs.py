from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from fastapi import HTTPException

from core.contracts import BirthInputCanonical
from core.life_domains import LifeDomain
from core.mingli_agent import ProbePlanner
from product.agent_api_context import AgentApiContext
from product.agent_command_service import BaselineCaseCommand, BaselineCaseCommandService
from product.agent_reading_projection import public_reading_view, reliability_outcome_payload


LOGGER = logging.getLogger(__name__)
DomainExecution = Callable[[Callable[[str, dict[str, Any]], None] | None], dict[str, Any]]


class AgentJobRunner:
    """Single background executor for the same commands used by synchronous APIs."""

    def __init__(
        self,
        *,
        context: AgentApiContext,
        baseline_commands: BaselineCaseCommandService,
        probe_planner: ProbePlanner,
    ) -> None:
        self._context = context
        self._baseline_commands = baseline_commands
        self._probe_planner = probe_planner
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="v50-cognitive-job",
        )
        self._lock = threading.Lock()
        self.recovered_interrupted_jobs = context.job_store.recover_interrupted()

    def submit_baseline(
        self,
        *,
        job_id: str,
        case_id: str,
        reading_id: str,
        birth_input: BirthInputCanonical,
        profile: dict[str, object] | None,
        user_id: str | None,
        active_mode: str,
    ) -> None:
        self._executor.submit(
            self._run_baseline,
            job_id=job_id,
            case_id=case_id,
            reading_id=reading_id,
            birth_input=birth_input,
            profile=profile,
            user_id=user_id,
            active_mode=active_mode,
        )

    def submit_domain(
        self,
        *,
        job_id: str,
        case_id: str,
        domain: LifeDomain,
        execute: DomainExecution,
    ) -> None:
        self._executor.submit(
            self._run_domain,
            job_id=job_id,
            case_id=case_id,
            domain=domain,
            execute=execute,
        )

    def _run_baseline(
        self,
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
            with self._lock:
                def on_command_event(
                    event_type: str,
                    stage_payload: dict[str, Any],
                ) -> None:
                    nonlocal current_stage
                    self._context.append_job_event(
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
                        job_status="running" if event_type == "chart_ready" else None,
                    )
                    current_stage = {
                        "chart_ready": "baseline_cognition",
                        "baseline_preview_ready": "baseline_cognition",
                        "baseline_draft_ready": "formal_insight_validation",
                        "formal_insight_draft_ready": "formal_insight_validation",
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

                result = self._baseline_commands.execute(
                    BaselineCaseCommand(
                        case_id=case_id,
                        reading_id=reading_id,
                        birth_input=birth_input,
                        profile_id=str(profile.get("profile_id")) if profile else None,
                        user_id=user_id,
                        active_mode=active_mode,
                    ),
                    on_event=on_command_event,
                )
                if not result.committed:
                    payload: dict[str, Any] = {
                        "outcome": reliability_outcome_payload(
                            world=result.world,
                            record=result.record,
                        ),
                        "validation": result.validation.model_dump(mode="json"),
                        "persisted_as_formal_insight": False,
                    }
                    if result.record.review.disposition == "competing":
                        payload["reading"] = public_reading_view(
                            world=result.world,
                            record=result.record,
                            workspace=result.workspace,
                            probe_plan=self._probe_planner.plan(
                                record=result.record,
                                role_mode=active_mode,
                            ),
                        )
                    self._context.append_job_event(
                        job_id=job_id,
                        event_type=(
                            "baseline_competing"
                            if result.record.review.disposition == "competing"
                            else "baseline_blocked"
                        ),
                        epistemic_status=result.record.review.disposition,
                        job_status="completed",
                        payload=payload,
                    )
                    return
                life_case = result.life_case
                assert life_case is not None
                reading = public_reading_view(
                    world=result.world,
                    record=result.record,
                    workspace=result.workspace,
                    probe_plan=self._probe_planner.plan(
                        record=result.record,
                        role_mode=active_mode,
                    ),
                    life_case=life_case,
                )
                self._context.append_job_event(
                    job_id=job_id,
                    event_type="baseline_committed",
                    epistemic_status="completed",
                    job_status="completed",
                    payload={
                        "reading": reading,
                        "life_case_id": life_case.life_case_id,
                        "insight_id": life_case.baseline_insight.insight_id,
                        "blocking_core_llm_calls": len(result.record.stage_receipts),
                    },
                )
        except Exception as exc:  # noqa: BLE001 - partial cognition remains recoverable.
            LOGGER.exception(
                "progressive_mingli_cognition_failed job_id=%s case_id=%s",
                job_id,
                case_id,
            )
            self._context.append_job_event(
                job_id=job_id,
                event_type="reading_failed",
                epistemic_status="failed",
                job_status="failed",
                payload={
                    "failure_code": f"mingli_cognition_failed:{type(exc).__name__}",
                    "failure_stage": current_stage,
                    "message": cognitive_failure_message(current_stage),
                },
            )

    def _run_domain(
        self,
        *,
        job_id: str,
        case_id: str,
        domain: LifeDomain,
        execute: DomainExecution,
    ) -> None:
        try:
            with self._lock:
                def on_stage(event_type: str, stage_payload: dict[str, Any]) -> None:
                    self._context.append_job_event(
                        job_id=job_id,
                        event_type=event_type,
                        epistemic_status=(
                            "provisional" if event_type == "domain_preview_ready" else "accepted"
                        ),
                        payload=stage_payload,
                        job_status="running",
                    )

                result = execute(on_stage)
                event_type = {
                    "domain_exploration_ready": "domain_committed",
                    "domain_competing": "domain_competing",
                    "domain_blocked": "domain_blocked",
                    "case_revision_candidate": "domain_revision_candidate",
                }.get(result["status"], "domain_completed")
                self._context.append_job_event(
                    job_id=job_id,
                    event_type=event_type,
                    epistemic_status=(
                        "completed"
                        if result["status"] == "domain_exploration_ready"
                        else (result.get("domain_outcome") or {}).get("state", "unresolved")
                    ),
                    payload=result,
                    job_status="completed",
                )
        except Exception as exc:  # noqa: BLE001 - a domain failure must remain visible.
            LOGGER.exception(
                "progressive_domain_failed job_id=%s case_id=%s domain=%s",
                job_id,
                case_id,
                domain.value,
            )
            detail = exc.detail if isinstance(exc, HTTPException) else f"{type(exc).__name__}:{exc}"
            self._context.append_job_event(
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


def cognitive_failure_message(stage: str) -> str:
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
