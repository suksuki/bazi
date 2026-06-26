from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import Field

from v30.config import load_settings
from v30.contracts import AnswerContext, AnswerResult, V30Model
from v30.llm import V30LLMProviderConfig, call_llm_answer_draft, load_v30_llm_provider_config_from_env
from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime


class LLMLiveSmokeResult(V30Model):
    version: str = "v30.llm_live_smoke.v1"
    run_id: str
    status: str
    passed: bool
    summary: dict[str, Any] = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list)
    artifact_uri: str = ""
    boundary: str = "llm_live_smoke_observes_expression_layer_not_chart_facts"


LLMCall = Callable[[AnswerContext, AnswerResult, dict[str, object], V30LLMProviderConfig], dict[str, object]]


def run_llm_live_smoke(
    *,
    reading_id: str = "v30-llm-live-smoke",
    config: V30LLMProviderConfig | None = None,
    write_artifact: bool = True,
    llm_call: LLMCall | None = None,
) -> LLMLiveSmokeResult:
    started_at = datetime.now(timezone.utc)
    runtime = create_smoke_runtime(reading_id)
    if runtime.answer_context is None or runtime.answer_result is None:
        return _result(
            started_at=started_at,
            status="failed",
            failures=["runtime_missing_answer_context"],
            summary={},
            write_artifact=write_artifact,
        )
    cfg = config or load_v30_llm_provider_config_from_env()
    user_view = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    before = _mutation_snapshot(runtime)
    call = (llm_call or _default_llm_call)(runtime.answer_context, runtime.answer_result, user_view.get("reading_surface", {}), cfg)
    after = _mutation_snapshot(runtime)
    mutation = _mutation_proof(before, after)
    readiness = call.get("readiness", {}) if isinstance(call.get("readiness"), dict) else {}
    smoke_status = _smoke_status(call, readiness)
    drift = call.get("drift_check", {}) if isinstance(call.get("drift_check"), dict) else {}
    failures: list[str] = []
    if mutation["chart_facts_unchanged"] is not True:
        failures.append("llm_mutated_chart_facts")
    if mutation["ranked_decisions_unchanged"] is not True:
        failures.append("llm_mutated_ranked_decisions")
    if mutation["model_signal_unchanged"] is not True:
        failures.append("llm_mutated_model_signal")
    if mutation["interaction_state_unchanged"] is not True:
        failures.append("llm_mutated_interaction_state")
    if smoke_status == "accepted" and drift.get("passed") is not True:
        failures.append("llm_accepted_without_passing_drift_check")
    if call.get("status") == "accepted" and call.get("boundary") != "llm_answer_draft_expression_only_no_chart_fact_mutation":
        failures.append("llm_accepted_with_wrong_boundary")
    if call.get("status") == "fallback" and call.get("boundary") != "llm_fallback_keeps_rule_answer_and_does_not_mutate_chart_facts":
        failures.append("llm_fallback_with_wrong_boundary")
    summary = {
        "configured": bool(readiness.get("ready_for_connection")),
        "enabled": bool(readiness.get("enabled")),
        "execute_llm": bool(readiness.get("execute_llm")),
        "provider": str(readiness.get("provider") or cfg.provider),
        "model": str(readiness.get("model") or cfg.model),
        "config_source": str(readiness.get("config_source") or cfg.config_source),
        "call_status": str(call.get("status") or ""),
        "smoke_status": smoke_status,
        "executed": bool(call.get("executed")),
        "fallback_reason": str(call.get("fallback_reason") or ""),
        "drift_passed": drift.get("passed") if isinstance(drift, dict) else None,
        "drift_failures": drift.get("failures", []) if isinstance(drift, dict) else [],
        "no_chart_fact_mutation_proof": mutation,
        "text_present": bool(str(call.get("text") or "").strip()),
        "readiness": readiness,
        "boundary": "llm_live_smoke_summary_trains_expression_observability_not_chart_facts",
    }
    return _result(
        started_at=started_at,
        status="passed" if not failures else "failed",
        failures=failures,
        summary=summary,
        write_artifact=write_artifact,
    )


def _default_llm_call(
    answer_context: AnswerContext,
    rule_answer: AnswerResult,
    reading_surface: dict[str, object],
    config: V30LLMProviderConfig,
) -> dict[str, object]:
    return call_llm_answer_draft(
        answer_context,
        rule_answer,
        reading_surface=reading_surface,
        config=config,
    )


def _smoke_status(call: dict[str, object], readiness: dict[str, object]) -> str:
    if readiness.get("ready_for_connection") is not True:
        return "unconfigured"
    if readiness.get("execute_llm") is not True:
        return "configured_not_executed"
    if call.get("status") == "accepted":
        return "accepted"
    if call.get("fallback_reason") == "drift_check_failed":
        return "drift_rejected"
    return "fallback"


def _mutation_snapshot(runtime: Any) -> dict[str, object]:
    policy_effect = runtime.question_plan.policy_effect
    return {
        "day_master": runtime.chart_context.day_master,
        "day_master_element": runtime.chart_context.day_master_element,
        "natal_pillars": runtime.chart_context.natal_pillars,
        "time_layers": runtime.chart_context.time_layers,
        "ranked_decisions": policy_effect.get("ranked_decisions", {}),
        "model_signal_summary": policy_effect.get("model_signal_summary", {}),
        "interaction_state": policy_effect.get("interaction_state", {}),
    }


def _mutation_proof(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    return {
        "version": "v30.llm_no_mutation_proof.v1",
        "chart_facts_unchanged": {
            "day_master": before.get("day_master"),
            "day_master_element": before.get("day_master_element"),
            "natal_pillars": before.get("natal_pillars"),
            "time_layers": before.get("time_layers"),
        } == {
            "day_master": after.get("day_master"),
            "day_master_element": after.get("day_master_element"),
            "natal_pillars": after.get("natal_pillars"),
            "time_layers": after.get("time_layers"),
        },
        "ranked_decisions_unchanged": before.get("ranked_decisions") == after.get("ranked_decisions"),
        "model_signal_unchanged": before.get("model_signal_summary") == after.get("model_signal_summary"),
        "interaction_state_unchanged": before.get("interaction_state") == after.get("interaction_state"),
        "boundary": "llm_smoke_proves_expression_call_did_not_mutate_runtime_state",
    }


def _result(
    *,
    started_at: datetime,
    status: str,
    failures: list[str],
    summary: dict[str, Any],
    write_artifact: bool,
) -> LLMLiveSmokeResult:
    run_id = f"v30.llm_live_smoke.{started_at.strftime('%Y%m%d%H%M%S%f')}"
    payload = LLMLiveSmokeResult(
        run_id=run_id,
        status=status,
        passed=status == "passed",
        summary=summary,
        failures=failures,
    )
    if not write_artifact:
        return payload
    artifact_uri = _write_artifact(payload)
    return payload.model_copy(update={"artifact_uri": artifact_uri})


def _write_artifact(result: LLMLiveSmokeResult) -> str:
    settings = load_settings()
    root = settings.runtime_dir / "validation" / "llm_live_smoke"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{result.run_id}.json"
    path.write_text(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    latest = root / "latest.json"
    latest.write_text(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(Path(path).resolve())
