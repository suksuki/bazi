from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.decision.knowledge_bridge import build_knowledge_rule_review_overlay
from v20.knowledge.completeness_audit import build_knowledge_completeness_audit
from v20.knowledge.rule_proposal import build_first_wave_rule_proposal_preflight, build_first_wave_rule_proposals
from v20.learning.knowledge_rule_review_overlay import write_knowledge_rule_review_overlay_artifact
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.validation.rule_synthetic import (
    RULE_SYNTHETIC_CASES,
    build_rule_synthetic_training_report,
    write_rule_synthetic_training_artifact,
)


KNOWLEDGE_RULE_ORCHESTRATOR_VERSION = "v20.knowledge_rule_orchestrator_plan.v1"


def build_knowledge_rule_orchestrator_plan(
    *,
    limit_per_domain: int = 2,
    synthetic_case_limit: int = 8,
    overlay_limit: int = 24,
    run_validation: bool = False,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    _emit(progress, "knowledge_completeness")
    knowledge = build_knowledge_completeness_audit()
    _emit(progress, "rule_proposals")
    proposals = build_first_wave_rule_proposals(limit_per_domain=max(1, limit_per_domain))
    preflight = build_first_wave_rule_proposal_preflight(limit_per_domain=max(1, limit_per_domain))
    cases = _selected_synthetic_cases(synthetic_case_limit)
    if run_validation:
        _emit(progress, f"rule_synthetic cases={len(cases)}")
        synthetic = build_rule_synthetic_training_report(cases=cases)
        _emit(progress, f"knowledge_rule_overlay limit={max(0, overlay_limit)}")
        overlay = build_knowledge_rule_review_overlay(
            limit=max(0, overlay_limit),
            synthetic_case_limit=max(0, synthetic_case_limit),
        )
    else:
        synthetic = _scheduled_synthetic_validation(cases)
        overlay = _scheduled_knowledge_rule_overlay(overlay_limit=overlay_limit, synthetic_case_limit=synthetic_case_limit)
    blockers = _blockers(knowledge=knowledge, preflight=preflight, synthetic=synthetic, overlay=overlay)
    return {
        "version": KNOWLEDGE_RULE_ORCHESTRATOR_VERSION,
        "status": "active_ready" if not blockers else "needs_alignment",
        "completion_percent": 99 if not blockers else 94,
        "brain_owner": "central_orchestrator",
        "mainline_status": _mainline_summary(knowledge),
        "new_knowledge_point_contract": _new_knowledge_point_contract(),
        "next_topic_groups": _next_topic_groups(),
        "stages": _stages(),
        "rule_generation": {
            "status": proposals.get("status", ""),
            "domain_count": proposals.get("domain_count", 0),
            "proposal_count": proposals.get("proposal_count", 0),
            "preflight_status": preflight.get("status", ""),
            "preflight_ok": bool(preflight.get("ok")),
            "iteration_requirement_count": preflight.get("iteration_requirement_count", 0),
            "runtime_mutation": False,
        },
        "synthetic_validation": {
            "status": synthetic.get("status", ""),
            "suite_status": synthetic.get("suite_status", ""),
            "case_count": synthetic.get("case_count", 0),
            "failure_count": synthetic.get("failure_count", 0),
            "training_scope": synthetic.get("training_scope", ()),
            "runtime_mutation": False,
        },
        "knowledge_rule_overlay": {
            "status": overlay.get("status", ""),
            "definition_count": overlay.get("definition_count", 0),
            "overlay_count": overlay.get("overlay_count", overlay.get("rule_count", 0)),
            "synthetic_case_count": overlay.get("synthetic_case_count", 0),
            "runtime_mutation": False,
        },
        "parameter_targets": _parameter_targets(synthetic=synthetic, overlay=overlay),
        "activation_policy": {
            "mode": "direct_apply_after_machine_success",
            "human_review_gate": False,
            "validation_execution": "runs_in_background_training_task" if not run_validation else "executed",
            "runtime_pointer_targets": (
                "knowledge_runtime_policy_pointer",
                "rule_runtime_policy_pointer",
                "portrait_runtime_policy_pointer",
                "question_runtime_policy_pointer",
                "orchestrator_runtime_policy_pointer",
            ),
            "admin_task_activation_family": "training_bundle",
            "runtime_mutation": False,
        },
        "blockers": blockers,
        "next_actions": _next_actions(blockers),
        "runtime_mutation": False,
        "guardrails": [
            "CENTRAL_ORCHESTRATOR_OWNS_KNOWLEDGE_RULE_VALIDATION_LOOP",
            "NEW_KNOWLEDGE_MUST_BIND_RULES_SYNTHETIC_CASES_AND_ANSWER_GUIDANCE",
            "NO_HUMAN_REVIEW_GATE_FOR_TRAINING",
            "STATUS_PLAN_DOES_NOT_MUTATE_RUNTIME",
            "ADMIN_PLAN_IS_LIGHTWEIGHT_BACKGROUND_TASK_RUNS_VALIDATION",
        ],
    }


def write_knowledge_rule_orchestrator_artifact(
    *,
    limit_per_domain: int = 2,
    synthetic_case_limit: int = 8,
    overlay_limit: int = 24,
    output_dir: Path | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, object]:
    report = build_knowledge_rule_orchestrator_plan(
        limit_per_domain=limit_per_domain,
        synthetic_case_limit=synthetic_case_limit,
        overlay_limit=overlay_limit,
        run_validation=True,
        progress=progress,
    )
    cases = _selected_synthetic_cases(synthetic_case_limit)
    _emit(progress, "write_rule_synthetic_artifact")
    rule_synthetic_write = write_rule_synthetic_training_artifact(cases=cases)
    _emit(progress, "write_knowledge_overlay_artifact")
    overlay_write = write_knowledge_rule_review_overlay_artifact(
        limit=max(0, overlay_limit),
        synthetic_case_limit=max(0, synthetic_case_limit),
        progress=progress,
    )
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "knowledge_rule_orchestrator"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"knowledge_rule_orchestrator_{stamp}.json"
    payload = report | {
        "status": "written",
        "child_artifacts": {
            "rule_synthetic": rule_synthetic_write,
            "knowledge_rule_overlay": overlay_write,
        },
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.knowledge_rule_orchestrator_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report.get("status", ""),
        "completion_percent": report.get("completion_percent", 0),
        "parameter_targets": report.get("parameter_targets", {}),
        "child_artifacts": payload["child_artifacts"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "CHILD_TRAINING_ARTIFACTS_WRITTEN_FOR_POINTER_CONSUMERS",
            "NO_HUMAN_REVIEW_GATE_FOR_TRAINING",
        ],
    }


def read_knowledge_rule_orchestrator_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "knowledge_rule_orchestrator") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.knowledge_rule_orchestrator_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _selected_synthetic_cases(limit: int) -> tuple[object, ...]:
    clean_limit = max(0, limit)
    return RULE_SYNTHETIC_CASES[:clean_limit] if clean_limit else RULE_SYNTHETIC_CASES


def _scheduled_synthetic_validation(cases: tuple[object, ...]) -> dict[str, object]:
    return {
        "version": "v20.rule_synthetic_training_report.scheduled.v1",
        "status": "scheduled",
        "suite_status": "scheduled",
        "case_count": len(cases),
        "failure_count": 0,
        "training_scope": (
            "rule_atom_collision_validation",
            "synthetic_counterexample_gap_detection",
            "active_rule_weight_iteration",
        ),
        "runtime_mutation": False,
    }


def _scheduled_knowledge_rule_overlay(*, overlay_limit: int, synthetic_case_limit: int) -> dict[str, object]:
    return {
        "version": "v20.knowledge_rule_review_overlay.scheduled.v1",
        "status": "scheduled",
        "definition_count": max(0, overlay_limit),
        "overlay_count": max(0, overlay_limit),
        "synthetic_case_count": max(0, synthetic_case_limit),
        "runtime_mutation": False,
    }


def _mainline_summary(report: dict[str, object]) -> dict[str, object]:
    p0_gaps = report.get("p0_gaps", ()) if isinstance(report.get("p0_gaps", ()), list | tuple) else ()
    return {
        "status": "continuous_iteration_ready" if report.get("status") == "complete" and not p0_gaps else "needs_alignment",
        "completion_label": "99%+" if report.get("status") == "complete" and not p0_gaps else "94%",
        "blocker_count": len(p0_gaps),
        "training_outputs_apply_directly": True,
        "runtime_mutation": False,
    }


def _new_knowledge_point_contract() -> dict[str, object]:
    return {
        "required_fields": (
            "knowledge_id",
            "directory_node",
            "source_refs",
            "condition_atoms",
            "rule_path",
            "portrait_outputs",
            "question_outputs",
            "answer_guidance",
            "counterexamples",
            "synthetic_cases",
            "runtime_boundary",
        ),
        "generation_policy": "knowledge_point_and_rule_candidate_are_created_as_one_unit",
        "validation_policy": "synthetic_cases_and_counterexamples_are_required_iteration_signals",
        "activation_policy": "parameter_targets_apply_directly_through_runtime_pointers",
        "runtime_mutation": False,
    }


def _next_topic_groups() -> tuple[dict[str, object], ...]:
    return (
        _topic_group("ten_god_position", "十神位置细则", "L3", ("year_month_day_hour_position", "visible_hidden_mixed")),
        _topic_group("branch_arbitration", "地支关系仲裁", "L4", ("clash_combine_seen_together", "half_combine_arch_hidden_combine")),
        _topic_group("pattern_counterexample", "格局反例", "L5", ("false_following_pattern", "mixed_purity_break_pattern")),
        _topic_group("time_trigger_detail", "岁运触发细分", "L9", ("fuyin_fanyin", "tomb_storage_open_close")),
        _topic_group("palace_application", "宫位应用细分", "L7", ("spouse_palace", "career_environment", "hour_family_late_stage")),
    )


def _topic_group(topic_key: str, label: str, node_key: str, atoms: tuple[str, ...]) -> dict[str, object]:
    return {
        "topic_key": topic_key,
        "label": label,
        "node_key": node_key,
        "atomic_training_targets": atoms,
        "required_output": "knowledge_unit_rule_proposal_synthetic_case_parameter_target",
        "runtime_mutation": False,
    }


def _stages() -> tuple[dict[str, object], ...]:
    return (
        _stage("knowledge_gap_pick", "中枢根据知识完备度挑选下一批原子知识点。", "knowledge_topics"),
        _stage("knowledge_atom_contract", "每个知识点必须同时生成规则路径、反例、回答边界。", "knowledge_point_contract"),
        _stage("rule_candidate_generation", "从知识点生成可追踪规则候选，不生成无来源规则。", "rule_proposals"),
        _stage("synthetic_case_binding", "给每条规则候选绑定合成八字验证和禁止输出。", "synthetic_cases"),
        _stage("rule_synthetic_validation", "用合成案例验证命中、漏判、误判。", "rule_synthetic_training"),
        _stage("knowledge_rule_overlay", "把知识依据、规则命中和 synthetic 信号对齐。", "knowledge_rule_overlay"),
        _stage("runtime_parameter_apply", "训练成功后直接写入可用 runtime pointer。", "runtime_pointer_targets"),
    )


def _stage(stage_key: str, purpose: str, output: str) -> dict[str, object]:
    return {
        "stage_key": stage_key,
        "purpose": purpose,
        "output_artifact": output,
        "central_brain_owner": True,
        "runtime_mutation": False,
    }


def _parameter_targets(*, synthetic: dict[str, object], overlay: dict[str, object]) -> dict[str, object]:
    failure_count = int(synthetic.get("failure_count", 0) or 0)
    case_count = int(synthetic.get("case_count", 0) or 0)
    overlay_count = int(overlay.get("overlay_count", overlay.get("rule_count", 0)) or 0)
    synthetic_confidence = round(max(0, case_count - failure_count) / max(1, case_count), 4)
    return {
        "knowledge_rule_mapping_weight": 0.012 if overlay_count > 0 else 0.0,
        "rule_synthetic_confidence_weight": 0.01 if synthetic_confidence >= 0.95 else 0.004,
        "counterexample_gap_weight": 0.0 if failure_count == 0 else round(min(0.02, failure_count / max(1, case_count) * 0.02), 4),
        "orchestrator_knowledge_rule_loop_weight": 0.01,
        "synthetic_confidence": synthetic_confidence,
        "runtime_mutation": False,
    }


def _blockers(
    *,
    knowledge: dict[str, object],
    preflight: dict[str, object],
    synthetic: dict[str, object],
    overlay: dict[str, object],
) -> list[dict[str, object]]:
    blockers: list[dict[str, object]] = []
    if knowledge.get("status") != "complete":
        blockers.append({"area": "mainline", "reason": "mainline_not_ready"})
    if preflight.get("ok") is not True:
        blockers.append({"area": "rule_generation", "reason": "rule_proposal_static_contract_failed"})
    if int(synthetic.get("case_count", 0) or 0) <= 0:
        blockers.append({"area": "synthetic_validation", "reason": "no_synthetic_cases"})
    if str(overlay.get("status", "")) in {"fail", "error", "blocked"}:
        blockers.append({"area": "knowledge_rule_overlay", "reason": "overlay_failed"})
    return blockers


def _next_actions(blockers: list[dict[str, object]]) -> tuple[dict[str, object], ...]:
    if blockers:
        return tuple(
            {
                "area": str(row.get("area", "")),
                "action": str(row.get("reason", "")),
                "activation_policy": "fix_machine_path_then_apply_directly",
            }
            for row in blockers
        )
    return (
        {
            "area": "knowledge_growth",
            "action": "generate_next_atomic_knowledge_points_with_rules_and_synthetic_cases",
            "activation_policy": "direct_apply_without_human_review_gate",
        },
        {
            "area": "central_brain",
            "action": "schedule_knowledge_rule_orchestrator_before_deep_training",
            "activation_policy": "training_bundle_pointer_apply",
        },
    )


def _emit(progress: Callable[[str], None] | None, message: str) -> None:
    if progress:
        progress(message)
