from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from v30.api.app import AnswerRequest, LLMAnswerEnhancementRequest, ReadingRequest, create_app
from v30.llm.acceptance import validate_bazi_llm_output_payload
from v30.presentation.client_model import build_presentation_model
from v30.runtime import attach_question_outcome, create_smoke_runtime


RUNTIME_ANSWER_INTEGRATION_DELTA_REVIEW_VERSION = "v30.runtime_answer_integration_delta_review.v1"

QUALITY_TOKENS = (
    "庚",
    "日主",
    "命盘",
    "官杀",
    "印星",
    "官印相生",
    "结构",
    "路径",
    "画像",
    "特征",
    "事业",
    "时运",
)
FORBIDDEN_CUSTOMER_TOKENS = (
    "policy_effect",
    "raw_runtime",
    "prompt_contract_id",
    "context_pack_id",
    "diagnostics",
    "llm_bazi_answer_draft · LLM accepted",
    "基础判断：",
    "路径复核：",
    "特征画像：",
    "证据数=",
)


def run_runtime_answer_integration_delta_review(
    *,
    reading_id: str = "core-evidence-5-runtime-answer-integration",
) -> dict[str, Any]:
    runtime_row = _runtime_row(reading_id=f"{reading_id}-runtime")
    api_rows = _api_rows(reading_id=f"{reading_id}-api")
    return build_runtime_answer_integration_delta_review(
        integration_rows=[runtime_row, *api_rows],
        reading_id=reading_id,
    )


def build_runtime_answer_integration_delta_review(
    *,
    integration_rows: Sequence[Mapping[str, Any]],
    reading_id: str = "core-evidence-5-runtime-answer-integration",
) -> dict[str, Any]:
    rows = [dict(row) for row in integration_rows]
    summary = _summary(rows)
    decision = _decision(summary, rows)
    return {
        "version": RUNTIME_ANSWER_INTEGRATION_DELTA_REVIEW_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["runtime_answer_integration_ready"] else "blocked",
        "reading_id": reading_id,
        "decision": decision,
        "quality_summary": summary,
        "integration_rows": rows,
        "core_scope": {
            "task_id": "CORE-EVIDENCE-5",
            "title": "Runtime Answer Integration Delta Review",
            "acceptance_target": (
                "runtime answer panels, API answer refresh, and optional LLM enhancement must expose "
                "Bazi-specific customer text, safe LLM metadata, and non-mutating chart facts"
            ),
        },
        "policy_boundary": {
            "live_llm_execution_performed": False,
            "mock_provider_used_for_llm_success_path": True,
            "chart_fact_mutation_allowed": False,
            "full_pytest_run_by_default": False,
            "boundary": "core_evidence_5_uses_temp_repository_and_mock_llm_only",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "runtime_answer_integration_delta_review_validates_end_to_end_answer_surface",
    }


def _runtime_row(*, reading_id: str) -> dict[str, Any]:
    runtime = create_smoke_runtime(
        reading_id,
        day_master="庚",
        day_master_element="metal",
        luck_pillar="戊寅",
        flow_year_pillar="庚子",
    )
    refreshed = attach_question_outcome(
        runtime,
        "q_v30_user_career_direction",
        {
            "answer": "我想先看事业方向。",
            "selected_option": "career:pressure",
            "confidence": 0.8,
            "feedback_tags": ["career"],
        },
    )
    view = build_presentation_model(refreshed, role_key="user", locale="zh", client="web").model_dump(mode="json")
    return _view_row(
        row_id="runtime_answer_panel_after_question_outcome",
        view=view,
        chart_before=runtime.chart_context.model_dump(mode="json"),
        chart_after=refreshed.chart_context.model_dump(mode="json"),
        expected_statuses={"accepted", "fallback", "deferred"},
    )


def _api_rows(*, reading_id: str) -> list[dict[str, Any]]:
    previous_env = {key: os.environ.get(key) for key in _API_ENV_KEYS}
    previous_provider = None
    with tempfile.TemporaryDirectory(prefix="v30-core-evidence-5-") as temp_root:
        try:
            os.environ["V30_REPOSITORY"] = "local_json"
            os.environ["V30_RUNTIME_DIR"] = str(Path(temp_root) / ".runtime")
            os.environ.pop("V30_REDIS_URL", None)
            os.environ["V30_LLM_ENABLED"] = "true"
            os.environ["V30_LLM_EXECUTE"] = "true"
            os.environ["V30_LLM_PROVIDER"] = "ollama_native"
            os.environ["V30_LLM_BASE_URL"] = "http://127.0.0.1:11434/v1"
            os.environ["V30_LLM_MODEL"] = "qwen-test"
            os.environ["V30_LLM_HTTP_TIMEOUT_SEC"] = "0.1"
            os.environ["V30_LLM_MAX_TOKENS"] = "160"

            from v30.llm import client as client_module

            previous_provider = client_module._post_ollama_native_completion
            client_module._post_ollama_native_completion = _mock_provider

            app = create_app()
            create_route = _route_endpoint(app, "/api/v30/readings")
            answer_route = _route_endpoint(app, "/api/v30/readings/{reading_id}/questions/{question_id}/answer")
            llm_route = _route_endpoint(app, "/api/v30/readings/{reading_id}/questions/{question_id}/answer/llm")
            view_route = _route_endpoint(app, "/api/v30/readings/{reading_id}/view")
            created = create_route(
                ReadingRequest(
                    reading_id=reading_id,
                    locale="zh",
                    target_year=2030,
                    actor_id="core-evidence-5-user",
                    session_id="core-evidence-5-session",
                    day_master="庚",
                    day_master_element="metal",
                    birth_input={
                        "input_id": f"{reading_id}-input",
                        "calendar_type": "solar",
                        "birth_date": "1990-02-04",
                        "birth_time": "23:30",
                        "timezone": "Asia/Shanghai",
                        "gender": "female",
                    },
                )
            )
            initial_view = view_route(reading_id, role="user", locale="zh", client="web")
            question_id = _next_question_id(initial_view) or "q_v30_user_career_direction"
            answer = answer_route(
                reading_id,
                question_id,
                AnswerRequest(
                    answer="我想先看事业方向，近几年一直有职责压力。",
                    role="user",
                    locale="zh",
                    client="web",
                    outcome_status="answered",
                    selected_option="career:pressure",
                    confidence=0.8,
                    feedback_tags=["career"],
                ),
            )
            answer_row = _view_row(
                row_id="api_answer_refresh_panel",
                view=_mapping(answer.get("view")),
                chart_before=_chart_from_view(initial_view),
                chart_after=_chart_from_view(_mapping(answer.get("view"))),
                expected_statuses={"accepted", "fallback", "deferred"},
                extra_checks={"api_answer_accepted": answer.get("accepted") is True},
            )
            enhanced = llm_route(
                reading_id,
                question_id,
                LLMAnswerEnhancementRequest(
                    role="user",
                    locale="zh",
                    client="web",
                    task_type="domain_followup",
                    domain="career",
                ),
            )
            enhanced_row = _view_row(
                row_id="api_llm_enhancement_accepted_panel",
                view=_mapping(enhanced.get("view")),
                chart_before=_chart_from_view(initial_view),
                chart_after=_chart_from_view(_mapping(enhanced.get("view"))),
                expected_statuses={"accepted"},
                extra_checks={
                    "llm_enhancement_accepted": enhanced.get("accepted") is True,
                    "llm_executed": enhanced.get("llm_executed") is True,
                },
            )
            enhanced_row["created_status"] = created.get("status")
            return [answer_row, enhanced_row]
        except Exception as exc:  # pragma: no cover - summarized as a failed validation row.
            return [
                {
                    "row_id": "api_runtime_answer_integration_exception",
                    "integration_ready": False,
                    "checks": {"api_journey_no_exception": False},
                    "failed_check_ids": ["api_journey_no_exception"],
                    "exception": f"{type(exc).__name__}:{exc}",
                }
            ]
        finally:
            if previous_provider is not None:
                from v30.llm import client as client_module

                client_module._post_ollama_native_completion = previous_provider
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def _view_row(
    *,
    row_id: str,
    view: Mapping[str, Any],
    chart_before: Mapping[str, Any],
    chart_after: Mapping[str, Any],
    expected_statuses: set[str],
    extra_checks: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    answer_panel = _mapping(view.get("answer_panel"))
    text = str(answer_panel.get("text") or "")
    llm = _mapping(answer_panel.get("llm_metadata"))
    context_summary = _mapping(llm.get("context_pack_summary"))
    checks = {
        "answer_panel_present": bool(answer_panel),
        "answer_text_is_bazi_specific": _bazi_quality_text(text),
        "answer_text_no_customer_leak": not any(token in text for token in FORBIDDEN_CUSTOMER_TOKENS),
        "llm_status_is_expected": str(llm.get("status") or "") in expected_statuses,
        "llm_metadata_is_customer_safe": not _metadata_has_forbidden_customer_keys(llm),
        "context_summary_has_product_layers": {"domain_card", "bazi_features", "bazi_portraits", "bazi_paths"} <= set(
            context_summary.get("layers", []) if isinstance(context_summary.get("layers"), list) else []
        ),
        "chart_facts_stable": dict(chart_before) == dict(chart_after),
        "answer_boundary_non_mutating": str(answer_panel.get("boundary") or "") in {
            "rule_bound_answer_no_llm_fact_mutation",
            "bounded_llm_answer_no_chart_fact_mutation",
        },
    }
    if extra_checks:
        checks.update(dict(extra_checks))
    failed = [check_id for check_id, passed in checks.items() if not passed]
    return {
        "row_id": row_id,
        "integration_ready": not failed,
        "checks": checks,
        "failed_check_ids": failed,
        "answer_source": str(answer_panel.get("source") or ""),
        "llm_status": str(llm.get("status") or ""),
        "answer_text": text,
        "context_layers": context_summary.get("layers", []) if isinstance(context_summary.get("layers"), list) else [],
        "boundary": "runtime_answer_panel_integration_row",
    }


def _summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ready_rows = [row for row in rows if row.get("integration_ready") is True]
    return {
        "row_count": len(rows),
        "ready_row_count": len(ready_rows),
        "failed_row_count": len(rows) - len(ready_rows),
        "ready_ratio": round(len(ready_rows) / max(1, len(rows)), 3),
        "row_ids": [str(row.get("row_id") or "") for row in rows],
    }


def _decision(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    failed_rows = [row for row in rows if row.get("failed_check_ids")]
    blockers: list[str] = []
    if failed_rows:
        blockers.append("runtime_answer_integration_rows_failed")
    if int(summary.get("row_count", 0) or 0) < 3:
        blockers.append("runtime_answer_integration_coverage_below_minimum")
    ready = not blockers
    return {
        "runtime_answer_integration_ready": ready,
        "decision_status": "core_evidence_5_runtime_answer_integration_ready"
        if ready
        else "core_evidence_5_runtime_answer_integration_blocked",
        "check_count": sum(len(_mapping(row.get("checks"))) for row in rows),
        "passed_check_count": sum(1 for row in rows for passed in _mapping(row.get("checks")).values() if passed),
        "failed_check_ids": sorted(
            {
                str(check_id)
                for row in rows
                for check_id in _list(row.get("failed_check_ids"))
                if check_id
            }
        ),
        "failed_row_ids": [str(row.get("row_id") or "") for row in failed_rows],
        "blockers": blockers,
        "live_llm_execution_performed": False,
        "full_pytest_required": False,
        "next_action": "continue_to_core_evidence_closeout"
        if ready
        else "repair_runtime_answer_panel_api_integration",
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("runtime_answer_integration_ready") is True:
        return {
            "task_id": "CORE-EVIDENCE-6",
            "title": "Core Evidence Closeout And Documentation Sync",
            "rationale": "Runtime answer integration is ready; next close the CORE-EVIDENCE chain and update module completion status.",
            "full_pytest_required_before_start": False,
        }
    return {
        "task_id": "CORE-EVIDENCE-5A",
        "title": "Runtime Answer Integration Hardening",
        "rationale": "Runtime/API answer panel failed text quality, metadata safety, or non-mutation checks.",
        "full_pytest_required_before_start": False,
    }


def _mock_provider(prompt: Mapping[str, Any], config: object) -> dict[str, Any]:
    return {
        "domain": "career",
        "answer_text": (
            "事业追问以庚日主的官杀压力和印星承接为核心，重点看职责、资质和平台能否形成官印相生路径。"
            "这里使用已知反馈和结构特征说明，不新增年份或固定结论。"
        ),
        "used_user_signals": ["career"],
        "boundaries": ["rule_bound_answer_no_llm_fact_mutation"],
    }


def _bazi_quality_text(text: str) -> bool:
    return (
        len(text) >= 40
        and any(token in text for token in ("庚", "日主", "命盘"))
        and any(token in text for token in ("官杀", "印星", "财星", "官印相生", "十神"))
        and any(token in text for token in ("事业", "时运", "结构", "路径", "画像", "特征"))
    )


def _metadata_has_forbidden_customer_keys(metadata: Mapping[str, Any]) -> bool:
    forbidden = {"prompt_request", "prompt_contract_id", "context_pack_id", "raw_runtime_payload", "diagnostics"}
    return bool(set(metadata) & forbidden)


def _route_endpoint(app: Any, path: str) -> Any:
    return next(route.endpoint for route in app.routes if getattr(route, "path", "") == path)


def _next_question_id(view: Mapping[str, Any]) -> str:
    surface = _mapping(view.get("reading_surface"))
    next_question = _mapping(surface.get("next_question"))
    return str(next_question.get("question_id") or "")


def _chart_from_view(view: Mapping[str, Any]) -> dict[str, Any]:
    surface = _mapping(view.get("reading_surface"))
    core = _mapping(surface.get("core_bazi_reading"))
    chart = _mapping(core.get("chart"))
    return {
        "four_pillars": core.get("four_pillars"),
        "day_master": core.get("day_master"),
        "chart": chart,
    }


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


_API_ENV_KEYS = (
    "V30_REPOSITORY",
    "V30_RUNTIME_DIR",
    "V30_REDIS_URL",
    "V30_LLM_ENABLED",
    "V30_LLM_EXECUTE",
    "V30_LLM_PROVIDER",
    "V30_LLM_BASE_URL",
    "V30_LLM_MODEL",
    "V30_LLM_HTTP_TIMEOUT_SEC",
    "V30_LLM_MAX_TOKENS",
)
