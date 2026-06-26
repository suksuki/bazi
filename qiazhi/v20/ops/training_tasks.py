from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from v20.storage.local_jsonl import local_jsonl_store_from_env


TRAINING_ACTIVATION_LEDGER = "training_activation_preflight_ledger"
TRAINING_ACTIVATION_CONFIRM_TOKEN = "ACTIVATE_TRAINING_RESULT"


@dataclass(frozen=True)
class TrainingTaskSpec:
    task_key: str
    label: str
    category: str
    description: str
    script_path: str
    default_args: tuple[str, ...]
    heavy_level: str
    estimated_duration: str
    writes_artifact: bool
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "ADMIN_TRAINING_TASK_REGISTRY_ONLY",
        "TASK_RUNS_OUTSIDE_REQUEST_THREAD",
        "NO_RUNTIME_POINTER_MUTATION",
    )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["default_args"] = list(self.default_args)
        payload["guardrails"] = list(self.guardrails)
        return payload


def training_task_registry() -> dict[str, object]:
    all_specs = _task_specs()
    specs = _admin_visible_task_specs(all_specs)
    latest_by_key = _latest_task_by_key()
    active_task = _active_training_task()
    recommendation = _recommended_next_task(specs, latest_by_key=latest_by_key, active_task=active_task)
    completion = _training_mainline_completion()
    training_plan = _training_plan_payload(latest_by_key=latest_by_key)
    return {
        "version": "v20.admin_training_task_registry.v1",
        "status": "ready",
        "mainline_completion": completion,
        "parameter_impact": _training_parameter_impact(),
        "training_plan": training_plan,
        "central_brain": _central_brain_training_payload(specs),
        "task_count": len(specs),
        "total_task_count": len(all_specs),
        "tasks": [_admin_task_payload(spec, latest_by_key=latest_by_key, recommended_key=str(recommendation.get("task_key", ""))) for spec in specs],
        "sections": _admin_task_sections(),
        "active_task": active_task,
        "recommended_next": recommendation,
        "runtime_mutation": False,
        "guardrails": [
            "TRAINING_TASK_REGISTRY_READ_ONLY",
            "ADMIN_START_REQUIRED_FOR_EXECUTION",
            "SUPPORTED_TASKS_AUTO_APPLY_RUNTIME_POINTERS",
            "ADMIN_UI_SHOWS_CURATED_TASKS_ONLY",
            "ONE_ADMIN_TRAINING_TASK_AT_A_TIME",
            "MAINLINE_COMPLETION_STATUS_EXPLICIT",
            "PARAMETER_IMPACT_STATUS_EXPLICIT",
            "TRAINING_PLAN_AND_DEDUPE_POLICY_EXPLICIT",
            "CENTRAL_BRAIN_GRAPH_GROUPING_EXPLICIT",
        ],
    }


def list_training_tasks(limit: int = 20) -> dict[str, object]:
    visible_keys = set(ADMIN_VISIBLE_TASK_KEYS)
    rows = [
        row
        for row in sorted(
            (_read_task(path) for path in _task_dir().glob("*.json") if path.name != "latest.json"),
            key=lambda row: str(row.get("updated_at", "")),
            reverse=True,
        )
        if str(row.get("task_key", "")) in visible_keys
    ][: max(1, limit)]
    summarized = [_with_result_summary(row) for row in rows]
    latest = summarized[0] if summarized else _empty_task_status()
    return {
        "version": "v20.admin_training_task_list.v1",
        "status": "ready",
        "task_count": len(summarized),
        "tasks": summarized,
        "latest": _with_result_summary(latest),
        "latest_result_summary": _task_result_summary(latest),
        "runtime_mutation": False,
        "guardrails": ["TASK_STATUS_READ_ONLY", "NO_LOG_FILE_FULL_CONTENT_RENDERED", "RESULT_SUMMARY_DERIVED_FROM_TASK_STATE"],
    }


def list_training_activation_preflights(limit: int = 20) -> dict[str, object]:
    rows = _read_ledger_payloads(TRAINING_ACTIVATION_LEDGER, limit=max(1, limit))
    return {
        "version": "v20.admin_training_activation_preflight_list.v1",
        "status": "ready",
        "record_count": len(rows),
        "preflights": rows,
        "runtime_mutation": False,
        "guardrails": [
            "ACTIVATION_PREFLIGHT_HISTORY_READ_ONLY",
            "NO_RUNTIME_POINTER_MUTATION",
            "LOCAL_JSONL_RECENT_RECORDS_ONLY",
        ],
    }


def read_latest_training_task() -> dict[str, object]:
    latest = _task_dir() / "latest.json"
    if not latest.exists():
        return _empty_task_status()
    return _read_task(latest)


def read_training_task(task_id: str) -> dict[str, object]:
    safe = _safe_task_id(task_id)
    path = _task_dir() / f"{safe}.json"
    if not path.exists():
        return _empty_task_status(task_id=safe)
    return _with_result_summary(_read_task(path))


def pause_training_task(task_id: str, *, source_role: str = "admin") -> dict[str, object]:
    safe = _safe_task_id(task_id)
    path = _task_dir() / f"{safe}.json"
    if not path.exists():
        return _empty_task_status(task_id=safe)
    state = _read_task(path)
    if state.get("status") not in {"queued", "running"}:
        return state
    pid = int(state.get("pid", 0) or 0)
    if pid > 0:
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError as exc:
            return state | {
                "status": "pause_failed",
                "current_stage": "pause_permission_denied",
                "error": str(exc),
                "updated_at": _now(),
            }
    paused = state | {
        "status": "paused",
        "current_stage": "paused_by_admin",
        "finished_at": _now(),
        "updated_at": _now(),
        "paused_by": source_role,
        "error": "",
    }
    _write_task_state(paused)
    return paused


def prepare_training_task_activation(
    task_id: str,
    *,
    dry_run: bool = True,
    confirm_token: str = "",
    reason: str = "",
    source_role: str = "admin",
) -> dict[str, object]:
    task = read_training_task(task_id)
    if task.get("status") == "not_found":
        raise ValueError(f"Unknown training task: {task_id}")
    summary = task.get("result_summary", {}) if isinstance(task.get("result_summary"), dict) else {}
    preview = summary.get("publish_preview", {}) if isinstance(summary.get("publish_preview"), dict) else {}
    eligible = bool(preview.get("eligible_for_publish"))
    requested_apply = not dry_run
    family = _activation_family_for_task(task)
    target = _activation_target_for_task(task)
    domain_activation = _domain_activation_result(
        task=task,
        eligible=eligible,
        family=family,
        dry_run=dry_run,
        confirm_token=confirm_token,
        reason=reason,
        source_role=source_role,
    )
    effective_status = str(domain_activation.get("status", "blocked"))
    activation_plan = {
        "task_id": str(task.get("task_id", "")),
        "task_key": str(task.get("task_key", "")),
        "label": str(task.get("label", "")),
        "activation_family": family,
        "activation_target": target,
        "dry_run": dry_run,
        "requested_apply": requested_apply,
        "eligible_for_publish": eligible,
        "publish_preview_status": str(preview.get("status", "")),
        "impacted_targets": preview.get("impacted_targets", []),
        "activation_mode": "manual_domain_activation_step_required",
        "blocking_gate": str(domain_activation.get("blocking_gate", "")) or _activation_blocking_gate(preview=preview, requested_apply=requested_apply),
        "domain_activation": domain_activation,
        "reason": str(reason or "")[:500],
        "source_role": source_role,
        "runtime_mutation": bool(domain_activation.get("runtime_mutation")) if requested_apply else False,
        "guardrails": [
            "ACTIVATION_PREFLIGHT_ONLY",
            "DOMAIN_ROUTED_ACTIVATION_REQUIRED",
            "NO_RUNTIME_POINTER_MUTATION",
            "CONFIRM_TOKEN_REQUIRED_FOR_PARAMETER_APPLY",
            *([] if requested_apply else ["DRY_RUN_REQUIRED_FROM_ADMIN_TRAINING_PAGE"]),
        ],
    }
    storage = local_jsonl_store_from_env().append_record(TRAINING_ACTIVATION_LEDGER, activation_plan)
    return {
        "version": "v20.admin_training_task_activation_preflight.v1",
        "status": effective_status,
        "activation_plan": activation_plan,
        "publish_preview": preview,
        "storage": storage,
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_PREFLIGHT_LEDGER_ONLY",
            "NO_RUNTIME_POINTER_MUTATION",
            "NO_RUNTIME_POINTER_MUTATION_UNLESS_EXPLICIT_DOMAIN_APPLY",
            "SEPARATE_DOMAIN_ACTIVATION_ENDPOINT_REQUIRED",
        ],
    }


def start_training_task(task_key: str, *, source_role: str = "admin", extra_args: tuple[str, ...] = ()) -> dict[str, object]:
    active = _active_training_task()
    if active.get("task_id"):
        return active | {
            "start_blocked": True,
            "requested_task_key": task_key,
            "current_stage": "start_blocked_existing_task",
            "guardrails": list(active.get("guardrails", [])) + ["ONE_ADMIN_TRAINING_TASK_AT_A_TIME"],
        }
    spec = _spec_by_key(task_key)
    dedupe = _task_dedupe_policy(spec, _latest_task_by_key().get(spec.task_key, {}))
    force = "--force" in set(extra_args)
    if dedupe.get("duplicate_blocked") and not force:
        state = _base_state(f"{task_key}.dedupe_blocked", spec, source_role=source_role, extra_args=extra_args)
        return state | {
            "status": "skipped",
            "progress_percent": 100,
            "current_stage": "start_blocked_duplicate_cooldown",
            "start_blocked": True,
            "duplicate_blocked": True,
            "dedupe_policy": dedupe,
            "error": str(dedupe.get("reason", "duplicate training blocked")),
            "updated_at": _now(),
            "guardrails": [
                *state.get("guardrails", []),
                "DUPLICATE_TRAINING_COOLDOWN_BLOCK",
            ],
        }
    task_id = f"{task_key}.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.{uuid4().hex[:8]}"
    task_dir = _task_dir()
    task_dir.mkdir(parents=True, exist_ok=True)
    log_path = task_dir / f"{task_id}.log"
    state = _base_state(task_id, spec, source_role=source_role, extra_args=extra_args)
    _write_task_state(state)
    worker = Path(__file__).resolve().parents[1] / "scripts" / "run_admin_training_task.py"
    process = subprocess.Popen(
        [
            sys.executable,
            str(worker),
            "--task-id",
            task_id,
            "--task-key",
            task_key,
            *extra_args,
        ],
        cwd=str(Path(__file__).resolve().parents[1]),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    state = state | {
        "status": "running",
        "pid": process.pid,
        "progress_percent": 1,
        "current_stage": "worker_started",
        "updated_at": _now(),
        "log_path": str(log_path),
    }
    _write_task_state(state)
    return state


def run_training_task_worker(task_id: str, task_key: str, extra_args: tuple[str, ...] = ()) -> dict[str, object]:
    spec = _spec_by_key(task_key)
    task_path = _task_dir() / f"{_safe_task_id(task_id)}.json"
    state = _read_task(task_path) if task_path.exists() else _base_state(task_id, spec, source_role="worker", extra_args=extra_args)
    log_path = _task_dir() / f"{_safe_task_id(task_id)}.log"
    script_extra_args = tuple(arg for arg in extra_args if arg != "--force")
    command = [sys.executable, str(Path(__file__).resolve().parents[1] / spec.script_path), *spec.default_args, *script_extra_args]
    env = os.environ.copy()
    package_root = str(Path(__file__).resolve().parents[2])
    env["PYTHONPATH"] = f"{package_root}:{env.get('PYTHONPATH', '')}".rstrip(":")
    state = state | {
        "status": "running",
        "current_stage": "script_started",
        "command": _redact_command(command),
        "updated_at": _now(),
        "progress_percent": max(int(state.get("progress_percent", 0) or 0), 3),
        "log_path": str(log_path),
    }
    _write_task_state(state)
    lines: list[str] = []
    started_at = datetime.now(timezone.utc)
    try:
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"[task] start {task_id} {task_key}\n")
            process = subprocess.Popen(
                command,
                cwd=str(Path(__file__).resolve().parents[1]),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )
            for line in process.stdout or ():
                clean = line.rstrip()
                log.write(clean + "\n")
                log.flush()
                lines.append(clean)
                lines = lines[-30:]
                progress = _progress_from_line(clean, state)
                state = state | {
                    "pid": process.pid,
                    "progress_percent": progress,
                    "current_stage": _stage_from_line(clean) or str(state.get("current_stage", "running")),
                    "updated_at": _now(),
                    "log_tail": lines[-12:],
                }
                _write_task_state(state)
            exit_code = process.wait()
        finished = _finish_state(state, exit_code=exit_code, started_at=started_at, log_tail=lines[-12:])
    except Exception as exc:
        finished = state | {
            "status": "failed",
            "progress_percent": int(state.get("progress_percent", 0) or 0),
            "current_stage": "worker_error",
            "error": str(exc),
            "finished_at": _now(),
            "updated_at": _now(),
            "log_tail": lines[-12:],
        }
    _write_task_state(finished)
    optimized = _auto_apply_training_parameters(finished)
    if optimized:
        _write_task_state(optimized)
        return optimized
    return finished


def _task_specs() -> tuple[TrainingTaskSpec, ...]:
    tasks = [
        TrainingTaskSpec(
            task_key="training_iteration_fast",
            label="日常快速训练",
            category="fast",
            description="快速跑一轮画像、规则和问题的小样本训练，生成新的候选参数。",
            script_path="scripts/run_training_iteration.py",
            default_args=("--write", "--progress", "--dynamic-limit", "4", "--rule-synthetic-limit", "4", "--synthetic-replay-limit", "1"),
            heavy_level="medium",
            estimated_duration="minutes",
            writes_artifact=True,
            runtime_mutation=True,
        ),
        _script_task(
            "training_iteration_deep",
            "深度训练迭代",
            "training",
            "比日常训练覆盖更广，会加入规则回放和规则迭代，适合低峰期运行。",
            "scripts/run_training_iteration.py",
            ("--write", "--progress", "--include-replay-eval", "--include-rule-iteration", "--dynamic-limit", "8", "--rule-synthetic-limit", "8", "--rule-iteration-limit", "24"),
            "heavy",
            runtime_mutation=True,
        ),
        TrainingTaskSpec(
            task_key="synthetic_case_suite",
            label="合成八字验证",
            category="synthetic",
            description="用合成八字案例检查规则、画像和推荐问题有没有跑偏。",
            script_path="scripts/run_synthetic_case_suite.py",
            default_args=("--summary", "--max-cases", "3", "--progress"),
            heavy_level="light",
            estimated_duration="seconds_to_minutes",
            writes_artifact=False,
        ),
        TrainingTaskSpec(
            task_key="structure_dynamics_synthetic",
            label="结构动态做功链验证",
            category="synthetic",
            description="用合成八字案例检查结构动态 v2 的核心做功链、语义定性和中枢公开做功链是否一致。",
            script_path="scripts/run_structure_dynamics_synthetic.py",
            default_args=("--summary", "--max-cases", "3", "--progress"),
            heavy_level="light",
            estimated_duration="seconds_to_minutes",
            writes_artifact=False,
        ),
        TrainingTaskSpec(
            task_key="structure_dynamics_corpus_distribution",
            label="结构动态语料回放",
            category="corpus",
            description="从 518K 八字空间抽一段真实分片，统计结构动态主线路分布和知识覆盖缺口。",
            script_path="scripts/run_structure_dynamics_corpus_distribution.py",
            default_args=("--run-id", "admin_structure_dynamics_corpus", "--limit", "32", "--write", "--summary", "--progress"),
            heavy_level="medium",
            estimated_duration="seconds_to_minutes",
            writes_artifact=True,
            runtime_mutation=True,
        ),
        TrainingTaskSpec(
            task_key="structure_dynamics_scheduled_shard",
            label="结构动态计划分片",
            category="corpus",
            description="按计划继续扩大 518K 结构动态分片，验证新路径标签是否都能回到知识机制。",
            script_path="scripts/run_structure_dynamics_corpus_distribution.py",
            default_args=("--run-id", "admin_structure_dynamics_scheduled_shard", "--start", "1024", "--limit", "1024", "--write", "--summary", "--progress"),
            heavy_level="heavy",
            estimated_duration="minutes_or_more",
            writes_artifact=True,
            runtime_mutation=True,
        ),
        _script_task(
            "rule_synthetic_training",
            "规则合成训练",
            "synthetic",
            "用合成案例验证规则命中、漏判和误判，并生成规则调参候选。",
            "scripts/run_rule_synthetic_training.py",
            ("--write", "--limit", "12"),
            "medium",
            runtime_mutation=True,
        ),
        _script_task(
            "practitioner_calibration_training",
            "命理师校准训练",
            "training",
            "汇总命理师校准反馈，用来优化问题优先级和表达深度。",
            "scripts/run_practitioner_calibration_training.py",
            ("--write", "--progress"),
            "medium",
            runtime_mutation=True,
        ),
        _script_task(
            "question_dag_training",
            "追问链路训练",
            "question",
            "训练推荐问题下一步怎么接，避免追问重复或发散。",
            "scripts/run_question_dag_training.py",
            ("--write", "--progress"),
            "medium",
            runtime_mutation=True,
        ),
        _script_task(
            "next_question_synthetic_validation",
            "下一问合成验证",
            "question",
            "用游客、普通用户、命理师和管理员案例验证下一问是否贴合当前八字、已问记录和大运流年。",
            "scripts/run_next_question_synthetic_validation.py",
            ("--write", "--progress"),
            "light",
            runtime_mutation=True,
        ),
        _script_task(
            "question_ranking_training",
            "问题排序训练",
            "question",
            "优化推荐问题的先后顺序，让当前盘最该问的问题排前面。",
            "scripts/run_question_ranking_training.py",
            ("--write", "--max-cases", "24", "--top-k", "8", "--progress"),
            "medium",
            runtime_mutation=True,
        ),
        _script_task(
            "question_source_training",
            "问题来源训练",
            "question",
            "训练问题来源权重，避免通用问题压过当前八字的真实主线。",
            "scripts/run_question_source_training.py",
            (),
            "light",
            runtime_mutation=True,
        ),
        _script_task(
            "role_interaction_training",
            "角色体验训练",
            "role",
            "分别优化游客、用户、命理师和管理员看到的问题与内容深度。",
            "scripts/run_role_interaction_training.py",
            ("--write", "--progress"),
            "medium",
            runtime_mutation=True,
        ),
        TrainingTaskSpec(
            task_key="nightly_executor_skeleton",
            label="夜间小分片训练",
            category="corpus",
            description="跑一个可恢复的小分片，用来验证夜间训练链路，不启动完整 518K。",
            script_path="scripts/run_nightly_learning_executor.py",
            default_args=("--limit", "8", "--status-every", "2", "--progress"),
            heavy_level="light",
            estimated_duration="seconds_to_minutes",
            writes_artifact=True,
            runtime_mutation=True,
        ),
        _script_task(
            "knowledge_rule_orchestrator",
            "知识规则联合训练",
            "orchestrator",
            "由中枢统一安排新增知识点、规则候选生成、合成验证和参数生效。",
            "scripts/run_knowledge_rule_orchestrator.py",
            ("--write", "--progress", "--limit-per-domain", "2", "--synthetic-case-limit", "8", "--overlay-limit", "24"),
            "heavy",
            runtime_mutation=True,
        ),
        _script_task(
            "knowledge_rule_review_overlay",
            "知识规则对齐训练",
            "knowledge",
            "把知识库内容和规则命中关系重新对齐，生成知识调参候选。",
            "scripts/run_knowledge_rule_review_overlay.py",
            ("--write", "--progress", "--limit", "24", "--synthetic-case-limit", "12"),
            "heavy",
            runtime_mutation=True,
        ),
        _script_task(
            "rule_subcondition_split",
            "规则条件拆分训练",
            "rule",
            "把复杂规则拆成更清楚的子条件，方便后续自动调权。",
            "scripts/run_rule_subcondition_split.py",
            ("--write", "--progress", "--limit", "24", "--per-rule", "3"),
            "heavy",
            runtime_mutation=True,
        ),
        _script_task(
            "rule_replay_eval",
            "规则回放评估",
            "rule",
            "用历史和合成样例回放规则表现，找出误触发和漏触发。",
            "scripts/run_rule_replay_eval.py",
            ("--write", "--progress", "--limit", "24", "--per-rule", "3"),
            "heavy",
            runtime_mutation=True,
        ),
        _script_task(
            "decision_registry_iteration",
            "判断库迭代",
            "rule",
            "把规则回放结果整理成判断库的下一轮候选参数。",
            "scripts/run_decision_registry_iteration.py",
            ("--write", "--progress", "--limit", "24", "--per-rule", "3"),
            "heavy",
            runtime_mutation=True,
        ),
        _script_task(
            "rule_portrait_batch",
            "规则画像批量训练",
            "portrait",
            "批量检查规则、画像和问题之间是否一致，生成画像调参候选。",
            "scripts/run_rule_portrait_batch.py",
            ("--write", "--progress"),
            "heavy",
            runtime_mutation=True,
        ),
        _script_task(
            "full_precompute_preview",
            "全量语料预计算预览",
            "corpus",
            "跑一小段全量语料预计算，验证链路和进度，不跑完整大任务。",
            "scripts/run_full_precompute.py",
            ("--run-id", "admin_preview_full_precompute", "--limit", "4", "--status-every", "1", "--progress"),
            "medium",
            runtime_mutation=True,
        ),
        _script_task(
            "extract_rules_llm_draft",
            "LLM 规则草稿提取",
            "knowledge",
            "让 LLM 从文本里提取少量规则草稿，只生成草稿，不写数据库。",
            "scripts/extract_rules_llm.py",
            ("--limit", "2", "--validate"),
            "medium",
        ),
    ]
    return tuple(tasks)


ADMIN_VISIBLE_TASK_KEYS: tuple[str, ...] = (
    "training_iteration_fast",
    "training_iteration_deep",
    "synthetic_case_suite",
    "structure_dynamics_synthetic",
    "structure_dynamics_corpus_distribution",
    "structure_dynamics_scheduled_shard",
    "question_source_training",
    "question_ranking_training",
    "question_dag_training",
    "next_question_synthetic_validation",
    "practitioner_calibration_training",
    "role_interaction_training",
    "rule_synthetic_training",
    "rule_subcondition_split",
    "rule_replay_eval",
    "decision_registry_iteration",
    "rule_portrait_batch",
    "knowledge_rule_orchestrator",
    "knowledge_rule_review_overlay",
    "extract_rules_llm_draft",
    "nightly_executor_skeleton",
    "full_precompute_preview",
)


ADMIN_TASK_GUIDANCE: dict[str, dict[str, object]] = {
    "training_iteration_fast": {
        "order": 10,
        "risk_level": "normal",
        "when_to_run": "日常首选；需要快速刷新训练 artifact 时运行。",
    },
    "synthetic_case_suite": {
        "order": 20,
        "risk_level": "low",
        "when_to_run": "改规则或问题策略后先跑，确认基础样例没有回归。",
    },
    "structure_dynamics_synthetic": {
        "order": 25,
        "risk_level": "low",
        "when_to_run": "结构动态、做功链、十神通路或中枢动态展示改动后运行。",
    },
    "structure_dynamics_corpus_distribution": {
        "order": 27,
        "risk_level": "normal",
        "when_to_run": "合成验证通过后运行，用 518K 分片观察真实结构主线路分布和知识覆盖缺口。",
    },
    "structure_dynamics_scheduled_shard": {
        "order": 28,
        "risk_level": "high",
        "when_to_run": "1024 稳定分片通过后低峰期运行，用下一段 518K 分片继续扩容结构动态覆盖。",
    },
    "question_source_training": {
        "order": 30,
        "risk_level": "low",
        "when_to_run": "问题来源、种子路径或推荐问题质量需要复核时运行。",
    },
    "question_ranking_training": {
        "order": 40,
        "risk_level": "normal",
        "when_to_run": "推荐问题排序异常、角色问题优先级需要调整时运行。",
    },
    "question_dag_training": {
        "order": 50,
        "risk_level": "normal",
        "when_to_run": "问题链路和追问顺序需要重新生成候选策略时运行。",
    },
    "next_question_synthetic_validation": {
        "order": 55,
        "risk_level": "low",
        "when_to_run": "问题原子、追问顺序、已问隐藏或大运流年问题权重调整后运行。",
    },
    "practitioner_calibration_training": {
        "order": 60,
        "risk_level": "normal",
        "when_to_run": "命理师校准反馈积累后运行。",
    },
    "role_interaction_training": {
        "order": 70,
        "risk_level": "normal",
        "when_to_run": "不同角色页面的问题行为或阅读路径有明显偏差时运行。",
    },
    "rule_synthetic_training": {
        "order": 80,
        "risk_level": "normal",
        "when_to_run": "规则改动后验证合成规则覆盖。",
    },
    "rule_subcondition_split": {
        "order": 90,
        "risk_level": "high",
        "when_to_run": "需要拆分复杂规则条件、生成可审阅子条件时运行。",
    },
    "rule_replay_eval": {
        "order": 100,
        "risk_level": "high",
        "when_to_run": "规则候选进入采纳前，用离线 replay 收集证据。",
    },
    "decision_registry_iteration": {
        "order": 110,
        "risk_level": "high",
        "when_to_run": "规则 replay 有证据后，生成 DecisionRegistry 迭代记录。",
    },
    "rule_portrait_batch": {
        "order": 120,
        "risk_level": "high",
        "when_to_run": "规则、画像、问题批量生成和验证；低峰期运行。",
    },
    "knowledge_rule_orchestrator": {
        "order": 125,
        "risk_level": "high",
        "when_to_run": "新增知识点需要同时生成规则、合成验证和调参目标时运行；低峰期运行。",
    },
    "knowledge_rule_review_overlay": {
        "order": 130,
        "risk_level": "high",
        "when_to_run": "知识规则需要批量审阅 overlay 时运行；低峰期运行。",
    },
    "extract_rules_llm_draft": {
        "order": 140,
        "risk_level": "normal",
        "when_to_run": "需要从文本生成 LLM 规则草稿时运行，不直接写 Postgres。",
    },
    "training_iteration_deep": {
        "order": 150,
        "risk_level": "high",
        "when_to_run": "一轮轻量训练和局部规则验证后再跑；低峰期运行。",
    },
    "nightly_executor_skeleton": {
        "order": 160,
        "risk_level": "low",
        "when_to_run": "验证 nightly executor 可恢复小分片，不启动完整 518K。",
    },
    "full_precompute_preview": {
        "order": 170,
        "risk_level": "normal",
        "when_to_run": "验证全量预计算链路的小样本 preview。",
    },
}


ADMIN_TASK_SECTION_BY_CATEGORY: dict[str, tuple[str, str, int]] = {
    "fast": ("daily", "日常训练", 10),
    "training": ("daily", "日常训练", 10),
    "synthetic": ("daily", "日常训练", 10),
    "question": ("question", "问题策略", 20),
    "role": ("question", "问题策略", 20),
    "rule": ("rule", "规则迭代", 30),
    "portrait": ("rule", "规则迭代", 30),
    "knowledge": ("knowledge", "知识库", 40),
    "corpus": ("corpus", "语料预计算", 50),
    "orchestrator": ("orchestrator", "编排器内部", 90),
}

def _admin_visible_task_specs(specs: tuple[TrainingTaskSpec, ...]) -> tuple[TrainingTaskSpec, ...]:
    by_key = {spec.task_key: spec for spec in specs}
    return tuple(by_key[key] for key in ADMIN_VISIBLE_TASK_KEYS if key in by_key)


def _admin_task_sections() -> list[dict[str, object]]:
    sections: dict[str, dict[str, object]] = {}
    for spec in _admin_visible_task_specs(_task_specs()):
        section_key, section_label, order = _section_for_category(spec.category)
        row = sections.setdefault(
            section_key,
            {"section_key": section_key, "label": section_label, "order": order, "task_count": 0},
        )
        row["task_count"] = int(row["task_count"]) + 1
    return sorted(sections.values(), key=lambda row: (int(row["order"]), str(row["label"])))


BRAIN_GRAPH_TASK_SECTIONS: tuple[dict[str, object], ...] = (
    {
        "node_key": "knowledge_gap_pick",
        "label": "知识缺口",
        "purpose": "选出下一批需要补齐的八字知识点，并把知识点转成可训练合同。",
        "task_keys": ("knowledge_rule_orchestrator", "knowledge_rule_review_overlay", "extract_rules_llm_draft"),
    },
    {
        "node_key": "rule_candidate_generation",
        "label": "规则生成",
        "purpose": "把知识点和反例转成规则候选、子条件和 DecisionRegistry 调整。",
        "task_keys": ("rule_synthetic_training", "rule_subcondition_split", "rule_replay_eval", "decision_registry_iteration"),
    },
    {
        "node_key": "portrait_mapping_generation",
        "label": "画像映射",
        "purpose": "把规则命中结果投射到游客、用户和命理师需要看的画像维度。",
        "task_keys": ("rule_portrait_batch", "practitioner_calibration_training"),
    },
    {
        "node_key": "question_policy_generation",
        "label": "问题策略",
        "purpose": "优化智能问答的问题来源、排序和追问路径。",
        "task_keys": ("question_source_training", "question_ranking_training", "question_dag_training", "next_question_synthetic_validation"),
    },
    {
        "node_key": "role_policy_generation",
        "label": "角色策略",
        "purpose": "按游客、普通用户、命理师和管理员分开优化展示深度与问题节奏。",
        "task_keys": ("role_interaction_training", "question_dag_training", "synthetic_case_suite"),
    },
    {
        "node_key": "llm_context_policy_generation",
        "label": "LLM 上下文",
        "purpose": "优化短提示词、角色上下文、八字结构上下文和回答合同，让回答链路直接消费中枢理解。",
        "task_keys": ("answer_governance_training", "role_interaction_training", "synthetic_case_suite", "training_iteration_fast"),
    },
    {
        "node_key": "synthetic_validation",
        "label": "合成验证",
        "purpose": "用合成八字样例覆盖新知识、规则边界和反例，给自动调参提供训练信号。",
        "task_keys": ("synthetic_case_suite", "structure_dynamics_synthetic", "structure_dynamics_corpus_distribution", "structure_dynamics_scheduled_shard", "rule_synthetic_training", "knowledge_rule_orchestrator"),
    },
    {
        "node_key": "corpus_replay_518k",
        "label": "518K 回放",
        "purpose": "在全量语料分片上回放特征、相似案例和预计算策略。",
        "task_keys": ("structure_dynamics_corpus_distribution", "structure_dynamics_scheduled_shard", "nightly_executor_skeleton", "full_precompute_preview"),
    },
    {
        "node_key": "parameter_optimizer",
        "label": "参数优化",
        "purpose": "聚合快训、深训和专题训练结果，写入可直接生效的 runtime pointer。",
        "task_keys": ("training_iteration_fast", "training_iteration_deep", "knowledge_rule_orchestrator"),
    },
)


PRIMARY_BRAIN_NODE_BY_TASK: dict[str, str] = {
    "synthetic_case_suite": "synthetic_validation",
    "structure_dynamics_synthetic": "synthetic_validation",
    "structure_dynamics_corpus_distribution": "corpus_replay_518k",
    "structure_dynamics_scheduled_shard": "corpus_replay_518k",
    "rule_synthetic_training": "synthetic_validation",
    "practitioner_calibration_training": "portrait_mapping_generation",
    "role_interaction_training": "role_policy_generation",
    "answer_governance_training": "llm_context_policy_generation",
    "training_iteration_fast": "parameter_optimizer",
    "training_iteration_deep": "parameter_optimizer",
    "knowledge_rule_orchestrator": "knowledge_gap_pick",
}


def _central_brain_training_payload(specs: tuple[TrainingTaskSpec, ...]) -> dict[str, object]:
    spec_by_key = {spec.task_key: spec for spec in specs}
    sections: list[dict[str, object]] = []
    for index, section in enumerate(BRAIN_GRAPH_TASK_SECTIONS, start=1):
        task_keys = [key for key in section["task_keys"] if key in spec_by_key]
        pointer_targets = sorted({target for key in task_keys for target in _runtime_pointer_targets_for_task_key(key)})
        sections.append(
            {
                "node_key": section["node_key"],
                "label": section["label"],
                "order": index * 10,
                "purpose": section["purpose"],
                "task_keys": task_keys,
                "task_count": len(task_keys),
                "runtime_pointer_targets": pointer_targets,
                "status": "central_brain_controlled" if task_keys else "missing_tasks",
                "runtime_mutation": False,
            }
        )
    return {
        "version": "v20.admin_training_central_brain.v1",
        "status": "ready",
        "brain_graph_task_sections": sections,
        "direct_apply_policy": "training_outputs_attempt_runtime_pointer_apply_without_human_review",
        "runtime_mutation": False,
        "guardrails": [
            "CENTRAL_BRAIN_GROUPS_VISIBLE_TRAINING_TASKS",
            "TASK_TO_BRAIN_NODE_MAPPING_EXPLICIT",
            "RUNTIME_POINTER_TARGETS_VISIBLE_IN_ADMIN_UI",
            "NO_HUMAN_REVIEW_GATE_FOR_SUPPORTED_TRAINING_RESULTS",
        ],
    }


def _brain_nodes_for_task_key(task_key: str) -> list[str]:
    nodes = [
        str(section["node_key"])
        for section in BRAIN_GRAPH_TASK_SECTIONS
        if task_key in set(section["task_keys"])
    ]
    primary = PRIMARY_BRAIN_NODE_BY_TASK.get(task_key, "")
    if primary and primary in nodes:
        return [primary, *[node for node in nodes if node != primary]]
    return nodes


def _runtime_pointer_targets_for_task_key(task_key: str) -> list[str]:
    if task_key in {"structure_dynamics_corpus_distribution", "structure_dynamics_scheduled_shard"}:
        return ["structure_dynamics_runtime_policy_pointer", "orchestrator_runtime_policy_pointer"]
    task = {"task_key": task_key, "category": _spec_by_key(task_key).category}
    family = _activation_family_for_task(task)
    if family == "training_bundle":
        return [
            "knowledge_runtime_policy_pointer",
            "rule_runtime_policy_pointer",
            "portrait_runtime_policy_pointer",
            "structure_dynamics_runtime_policy_pointer",
            "question_runtime_policy_pointer",
            "role_view_runtime_policy_pointer",
            "orchestrator_runtime_policy_pointer",
            "corpus_runtime_policy_pointer",
        ]
    return {
        "question_policy": ["question_runtime_policy_pointer", "role_view_runtime_policy_pointer"],
        "portrait_policy": ["portrait_runtime_policy_pointer"],
        "rule_iteration": ["rule_runtime_policy_pointer"],
        "structure_dynamics_policy": ["structure_dynamics_runtime_policy_pointer"],
        "knowledge_review": ["knowledge_runtime_policy_pointer"],
        "corpus_precompute": ["corpus_runtime_policy_pointer"],
        "manual_review": [],
    }.get(family, [])


def _training_plan_payload(*, latest_by_key: dict[str, dict[str, object]]) -> dict[str, object]:
    try:
        from v20.corpus.artifacts import read_corpus_artifact_status, read_corpus_training_artifacts
        from v20.learning_orchestrator.job_schema import build_learning_job_profiles
        from v20.validation.structure_dynamics_knowledge_coverage import build_structure_dynamics_knowledge_coverage_report
        from v20.validation.structure_dynamics_legacy_v2_switch import build_structure_dynamics_legacy_v2_switch_report
        from v20.validation.structure_dynamics_path_distribution import build_structure_dynamics_path_distribution
        from v20.validation.structure_dynamics_corpus_distribution import read_latest_structure_dynamics_corpus_distribution
        from v20.validation.structure_dynamics_synthetic import run_structure_dynamics_synthetic_suite
        from v20.validation.synthetic_schema import synthetic_bazi_coverage_report

        profiles = [profile.to_dict() for profile in build_learning_job_profiles()]
        coverage = synthetic_bazi_coverage_report()
        structure_synthetic = run_structure_dynamics_synthetic_suite()
        structure_path_distribution = build_structure_dynamics_path_distribution(synthetic_report=structure_synthetic)
        structure_knowledge_coverage = build_structure_dynamics_knowledge_coverage_report(path_distribution=structure_path_distribution)
        structure_corpus_distribution = read_latest_structure_dynamics_corpus_distribution()
        structure_legacy_v2_switch = build_structure_dynamics_legacy_v2_switch_report(synthetic_report=structure_synthetic)
        corpus_status = read_corpus_artifact_status()
        corpus_training = read_corpus_training_artifacts()
    except Exception as exc:  # pragma: no cover - defensive admin payload
        profiles = []
        coverage = {
            "version": "v20.synthetic_bazi_coverage_report.unavailable.v1",
            "status": "unavailable",
            "gap_count": 0,
            "error": str(exc),
            "runtime_mutation": False,
        }
        corpus_status = {
            "version": "v20.corpus_artifact_status.unavailable.v1",
            "status": "unavailable",
            "error": str(exc),
            "runtime_mutation": False,
        }
        corpus_training = {
            "version": "v20.corpus_training_artifacts.unavailable.v1",
            "status": "unavailable",
            "error": str(exc),
            "runtime_mutation": False,
        }
        structure_synthetic = {
            "version": "v20.structure_dynamics_synthetic.unavailable.v1",
            "ok": False,
            "case_count": 0,
            "pass_rate": 0.0,
            "quality_scores": {
                "dynamic_path_consistency": 0.0,
                "semantic_candidate_precision": 0.0,
            },
            "error": str(exc),
            "runtime_mutation": False,
        }
        structure_path_distribution = {
            "version": "v20.structure_dynamics_path_distribution.unavailable.v1",
            "status": "unavailable",
            "case_count": 0,
            "error": str(exc),
            "runtime_mutation": False,
        }
        structure_knowledge_coverage = {
            "version": "v20.structure_dynamics_knowledge_coverage.unavailable.v1",
            "status": "unavailable",
            "observed_label_count": 0,
            "unsupported_count": 0,
            "error": str(exc),
            "runtime_mutation": False,
        }
        structure_corpus_distribution = {
            "version": "v20.structure_dynamics_corpus_distribution.unavailable.v1",
            "status": "unavailable",
            "case_count": 0,
            "error": str(exc),
            "runtime_mutation": False,
        }
        structure_legacy_v2_switch = {
            "version": "v20.structure_dynamics_legacy_v2_switch.unavailable.v1",
            "status": "unavailable",
            "case_count": 0,
            "error": str(exc),
            "runtime_mutation": False,
        }
    synthetic_plan = _synthetic_rule_plan(coverage)
    quality_signal = _candidate_quality_signal(
        synthetic_plan=synthetic_plan,
        structure_synthetic=structure_synthetic,
        corpus_status=corpus_status,
        corpus_training=corpus_training,
    )
    optimization_topics = _training_optimization_topics()
    central_tuning_package = _central_brain_tuning_package(
        quality_signal=quality_signal,
        optimization_topics=optimization_topics,
        synthetic_plan=synthetic_plan,
        corpus_status=corpus_status,
        corpus_training=corpus_training,
    )
    return {
        "version": "v20.admin_training_plan.v1",
        "status": "ready",
        "strategy": "fast_iteration_with_gated_auto_apply",
        "profiles": profiles,
        "optimization_topics": optimization_topics,
        "synthetic_rule_plan": synthetic_plan,
        "structure_dynamics_synthetic_plan": _structure_dynamics_synthetic_plan(structure_synthetic),
        "structure_dynamics_path_distribution": structure_path_distribution,
        "structure_dynamics_knowledge_coverage": structure_knowledge_coverage,
        "structure_dynamics_corpus_distribution": structure_corpus_distribution,
        "structure_dynamics_legacy_v2_switch": structure_legacy_v2_switch,
        "candidate_quality_signal": quality_signal,
        "central_brain_tuning_package": central_tuning_package,
        "dedupe_summary": _training_dedupe_summary(latest_by_key),
        "recommended_cadence": [
            {
                "cadence_key": "fast",
                "label": "日常快速迭代",
                "tasks": ["training_iteration_fast", "synthetic_case_suite", "structure_dynamics_synthetic"],
                "trigger": "改动后或需要快速刷新候选策略时",
            },
            {
                "cadence_key": "nightly",
                "label": "夜间确定性回放",
                "tasks": ["nightly_executor_skeleton", "full_precompute_preview"],
                "trigger": "低峰期先扩 shard，再进入 518K 全量 executor",
            },
            {
                "cadence_key": "weekly",
                "label": "周度规则深训",
                "tasks": ["training_iteration_deep", "rule_replay_eval", "decision_registry_iteration"],
                "trigger": "规则候选或反例材料积累后",
            },
        ],
        "runtime_mutation": False,
        "guardrails": [
            "TRAINING_PLAN_READ_ONLY",
            "DEDUP_POLICY_PREVENTS_NO_INPUT_REPEAT",
            "SYNTHETIC_RULE_GAPS_FEED_NEXT_TRAINING",
            "STRUCTURE_DYNAMICS_SYNTHETIC_FEEDS_DYNAMIC_PATH_TRAINING",
            "OPTIMIZATION_TOPICS_MAP_ATOMIC_TRAINING_TO_PARAMETERS",
            "FULL_518K_REQUIRES_EXPLICIT_NIGHTLY_EXECUTOR_EXPANSION",
            "CANDIDATE_QUALITY_SIGNAL_COMBINES_SYNTHETIC_AND_CORPUS_REPLAY",
            "CENTRAL_BRAIN_TUNING_PACKAGE_UNIFIES_CONTEXT_SYNTHETIC_AND_CORPUS",
        ],
    }


def _central_brain_tuning_package(
    *,
    quality_signal: dict[str, object],
    optimization_topics: list[dict[str, object]],
    synthetic_plan: dict[str, object],
    corpus_status: dict[str, object],
    corpus_training: dict[str, object],
) -> dict[str, object]:
    quality_scores = quality_signal.get("quality_scores", {})
    if not isinstance(quality_scores, dict):
        quality_scores = {}
    promotion_score = float(quality_signal.get("candidate_promotion_score", 0.0) or 0.0)
    threshold = float(quality_signal.get("promotion_threshold", 0.82) or 0.82)
    context_drift = float(quality_scores.get("bazi_context_drift_score", 1.0) or 0.0)
    gate_blockers = tuple(str(row) for row in quality_signal.get("gate_blockers", ()) if str(row))
    decision = (
        "direct_apply_candidates"
        if str(quality_signal.get("promotion_decision", "")) == "promote_candidate"
        and promotion_score >= threshold
        and context_drift == 0
        and not gate_blockers
        else "continue_training"
    )
    parameter_updates = [
        _central_tuning_topic_update(topic, quality_scores=quality_scores, decision=decision)
        for topic in optimization_topics
    ]
    runtime_pointer_targets = tuple(
        dict.fromkeys(
            target
            for row in parameter_updates
            for target in row.get("runtime_pointer_targets", ())
            if isinstance(target, str) and target
        )
    )
    apply_report = _central_tuning_apply_report(
        decision=decision,
        parameter_updates=parameter_updates,
        runtime_pointer_targets=runtime_pointer_targets,
        promotion_score=promotion_score,
        threshold=threshold,
        context_drift=context_drift,
        gate_blockers=gate_blockers,
    )
    return {
        "version": "v20.central_brain_tuning_package.v1",
        "status": "ready_to_apply" if decision == "direct_apply_candidates" else "needs_more_training",
        "brain_owner": "central_brain_parameter_optimizer",
        "decision": decision,
        "candidate_promotion_score": round(promotion_score, 4),
        "promotion_threshold": threshold,
        "context_drift_score": round(context_drift, 4),
        "synthetic_status": str(synthetic_plan.get("status", "")),
        "synthetic_gap_count": int(synthetic_plan.get("gap_count", 0) or 0),
        "corpus_artifact_status": str(corpus_status.get("status", "")),
        "corpus_training_status": str(corpus_training.get("status", "")),
        "input_signal_contract": {
            "bazi_context": "context_alignment_report + bazi_context_drift_score",
            "synthetic": "synthetic_bazi_coverage_report + synthetic replay gates",
            "corpus_518k": "corpus artifacts + corpus training stability",
            "runtime_writer": "topic optimizer writer + activation family",
        },
        "quality_scores": quality_scores,
        "gate_blockers": gate_blockers,
        "parameter_update_count": len(parameter_updates),
        "parameter_updates": parameter_updates,
        "runtime_pointer_targets": runtime_pointer_targets,
        "apply_report": apply_report,
        "activation_policy": "machine_apply_without_human_review_when_ready",
        "runtime_mutation": False,
        "guardrails": [
            "CENTRAL_BRAIN_TUNING_PACKAGE_READ_ONLY_UNTIL_POINTER_WRITER",
            "CONTEXT_DRIFT_ZERO_REQUIRED_FOR_DIRECT_APPLY",
            "SYNTHETIC_AND_518K_SIGNALS_SHARE_ONE_PROMOTION_DECISION",
            "NO_HUMAN_REVIEW_GATE",
        ],
    }


def _central_tuning_apply_report(
    *,
    decision: str,
    parameter_updates: list[dict[str, object]],
    runtime_pointer_targets: tuple[str, ...],
    promotion_score: float,
    threshold: float,
    context_drift: float,
    gate_blockers: tuple[str, ...],
) -> dict[str, object]:
    pointer_updates = [
        {
            "runtime_pointer_target": target,
            "status": "ready_to_apply" if decision == "direct_apply_candidates" else "blocked",
            "source_topics": tuple(
                row["topic_key"]
                for row in parameter_updates
                if target in set(row.get("runtime_pointer_targets", ()))
            ),
            "blocking_gate": "" if decision == "direct_apply_candidates" else _central_tuning_blocking_gate(
                promotion_score=promotion_score,
                threshold=threshold,
                context_drift=context_drift,
                gate_blockers=gate_blockers,
            ),
            "runtime_mutation": False,
        }
        for target in runtime_pointer_targets
    ]
    ready_count = sum(1 for row in pointer_updates if row["status"] == "ready_to_apply")
    return {
        "version": "v20.central_brain_tuning_apply_report.v1",
        "status": "ready_to_apply" if ready_count == len(pointer_updates) and pointer_updates else "blocked",
        "pointer_update_count": len(pointer_updates),
        "ready_pointer_count": ready_count,
        "blocked_pointer_count": len(pointer_updates) - ready_count,
        "pointer_updates": pointer_updates,
        "runtime_mutation": False,
        "guardrails": [
            "CENTRAL_TUNING_APPLY_REPORT_IS_READ_ONLY_PLAN",
            "POINTER_WRITERS_PERFORM_ACTUAL_RUNTIME_MUTATION",
            "NO_HUMAN_REVIEW_GATE",
        ],
    }


def _central_tuning_blocking_gate(
    *,
    promotion_score: float,
    threshold: float,
    context_drift: float,
    gate_blockers: tuple[str, ...],
) -> str:
    if context_drift != 0:
        return "bazi_context_drift"
    if gate_blockers:
        return ",".join(gate_blockers)
    if promotion_score < threshold:
        return "candidate_promotion_score_below_threshold"
    return "continue_training"


def _central_tuning_topic_update(
    topic: dict[str, object],
    *,
    quality_scores: dict[str, object],
    decision: str,
) -> dict[str, object]:
    topic_key = str(topic.get("topic_key", ""))
    context_drift = float(quality_scores.get("bazi_context_drift_score", 1.0) or 0.0)
    synthetic_pass = float(quality_scores.get("synthetic_pass_rate", 0.0) or 0.0)
    corpus_stability = float(quality_scores.get("similar_case_stability", 0.0) or 0.0)
    question_focus = float(quality_scores.get("question_focus_score", 0.0) or 0.0)
    topic_fit = _topic_quality_fit(topic_key, synthetic_pass=synthetic_pass, corpus_stability=corpus_stability, question_focus=question_focus)
    status = "candidate_ready" if decision == "direct_apply_candidates" and context_drift == 0 and topic_fit >= 0.82 else "collect_more_signal"
    return {
        "topic_key": topic_key,
        "label": str(topic.get("label", "")),
        "status": status,
        "topic_fit_score": round(topic_fit, 4),
        "parameter_targets": tuple(str(row) for row in topic.get("parameter_targets", ()) if str(row)),
        "runtime_pointer_targets": _runtime_pointer_targets_for_topic(topic_key),
        "training_sources": tuple(str(row) for row in topic.get("atomic_trainings", ()) if str(row)),
        "context_drift_score": round(context_drift, 4),
        "activation_hint": "auto_apply_pointer" if status == "candidate_ready" else "run_recommended_replay",
        "runtime_mutation": False,
    }


def _topic_quality_fit(topic_key: str, *, synthetic_pass: float, corpus_stability: float, question_focus: float) -> float:
    if topic_key in {"feature_corpus"}:
        score = 0.25 * synthetic_pass + 0.65 * corpus_stability + 0.10 * question_focus
    elif topic_key in {"intelligent_qa", "role_experience", "llm_context"}:
        score = 0.30 * synthetic_pass + 0.25 * corpus_stability + 0.45 * question_focus
    elif topic_key in {"structure_dynamics", "rule"}:
        score = 0.55 * synthetic_pass + 0.25 * corpus_stability + 0.20 * question_focus
    else:
        score = 0.40 * synthetic_pass + 0.35 * corpus_stability + 0.25 * question_focus
    return max(0.0, min(1.0, score))


def _runtime_pointer_targets_for_topic(topic_key: str) -> tuple[str, ...]:
    return {
        "portrait": ("portrait_runtime_policy_pointer",),
        "rule": ("rule_runtime_policy_pointer",),
        "knowledge": ("knowledge_runtime_policy_pointer",),
        "intelligent_qa": ("question_runtime_policy_pointer",),
        "structure_dynamics": ("structure_dynamics_runtime_policy_pointer", "orchestrator_runtime_policy_pointer", "rule_runtime_policy_pointer"),
        "role_experience": ("role_view_runtime_policy_pointer",),
        "llm_context": ("role_view_runtime_policy_pointer", "orchestrator_runtime_policy_pointer", "knowledge_runtime_policy_pointer"),
        "feature_corpus": ("corpus_runtime_policy_pointer",),
    }.get(topic_key, ())


def _training_optimization_topics() -> list[dict[str, object]]:
    return [
        _optimization_topic(
            "portrait",
            "画像训练专题",
            ("guest", "user", "practitioner", "admin"),
            ("rule_portrait_batch", "training_iteration_fast", "practitioner_calibration_training"),
            ("portrait_axis_weight", "portrait_confidence_threshold", "role_portrait_depth", "topic_projection_weight"),
            ("portrait_alignment", "negative_boundary", "role_separation"),
            "supervised_eval_plus_offline_policy_gate",
            "已接 portrait runtime optimizer writer；画像批量验证和快训通过后可写 active portrait axis pointer。",
        ),
        _optimization_topic(
            "rule",
            "规则训练专题",
            ("practitioner", "admin"),
            ("rule_synthetic_training", "rule_subcondition_split", "rule_replay_eval", "decision_registry_iteration"),
            ("rule_weight", "subcondition_threshold", "counterexample_penalty", "decision_registry_priority"),
            ("rule_precision", "rule_recall", "counterexample_no_false_positive"),
            "synthetic_eval_plus_replay_comparison",
            "已接 rule runtime optimizer writer；rule replay 和 DecisionRegistry 通过后可写 active rule weight pointer。",
        ),
        _optimization_topic(
            "knowledge",
            "知识库训练专题",
            ("practitioner", "admin"),
            ("knowledge_rule_review_overlay", "answer_governance_training", "extract_rules_llm_draft", "training_iteration_deep"),
            ("knowledge_rule_mapping_weight", "answer_guidance_weight", "answer_governance_quality_weight", "counterexample_coverage", "source_trust_weight"),
            ("knowledge_alignment", "answer_boundary", "answer_governance_quality", "rule_source_traceability"),
            "retrieval_eval_plus_synthetic_boundary_gate",
            "已接 knowledge runtime optimizer writer；overlay artifact、回答治理质量和 rule proposal preflight 会共同写 active knowledge mapping pointer。",
        ),
        _optimization_topic(
            "intelligent_qa",
            "智能问答训练专题",
            ("guest", "user", "practitioner", "admin"),
            ("question_source_training", "question_ranking_training", "question_dag_training", "next_question_synthetic_validation", "training_iteration_fast"),
            ("question_source_weight", "question_rank_weight", "dag_transition_weight", "mainline_focus_weight", "next_question_stage_topic_boost"),
            ("question_focus", "question_dag", "role_leakage_guardrail", "answered_suppression", "time_context_boost"),
            "contextual_bandit_plus_synthetic_replay_gate",
            "已接 question runtime optimizer writer；source/ranking/DAG/下一问合成验证产物可写 active question policy pointer。",
        ),
        _optimization_topic(
            "structure_dynamics",
            "结构动态训练专题",
            ("guest", "user", "practitioner", "admin"),
            ("structure_dynamics_synthetic", "structure_dynamics_corpus_distribution", "structure_dynamics_scheduled_shard", "synthetic_case_suite", "rule_replay_eval", "rule_portrait_batch", "training_iteration_fast"),
            ("dynamic_path_weight", "semantic_match_weight", "volatility_threshold", "time_trigger_weight", "structure_stability_floor"),
            ("dynamic_path_consistency", "semantic_candidate_precision", "time_layer_boundary", "no_event_prediction"),
            "deterministic_structure_replay_plus_central_arbitration",
            "结构动态 v2 已接 runtime、BrainState、证据编译、UI、合成验证和 runtime pointer；合成做功链通过后可直接写 active structure dynamics policy pointer。",
        ),
        _optimization_topic(
            "role_experience",
            "角色体验训练专题",
            ("guest", "user", "practitioner", "admin"),
            ("role_interaction_training", "question_dag_training", "synthetic_case_suite"),
            ("role_question_order", "role_visibility_level", "role_question_count", "seed_fit_policy"),
            ("role_separation", "role_observation", "question_focus"),
            "offline_ab_replay_plus_promotion_gate",
            "已接 role-view runtime pointer；支持机器 gate 后直接生效。",
        ),
        _optimization_topic(
            "llm_context",
            "LLM 上下文训练专题",
            ("guest", "user", "practitioner", "admin"),
            ("answer_governance_training", "role_interaction_training", "synthetic_case_suite", "training_iteration_fast"),
            ("role_context_density_weight", "bazi_context_profile_weight", "answer_contract_structure_weight", "prompt_context_budget_weight"),
            ("role_context_fit", "bazi_context_structure_mode", "answer_contract_compliance", "prompt_budget"),
            "prompt_context_replay_plus_answer_governance",
            "已接 LLM prompt/context runtime 消费；复用回答治理、角色体验和合成回放继续优化上下文参数。",
        ),
        _optimization_topic(
            "feature_corpus",
            "八字特征与语料训练专题",
            ("admin",),
            ("nightly_executor_skeleton", "full_precompute_preview", "training_iteration_deep"),
            ("feature_threshold", "coverage_prior", "similar_case_weight", "corpus_shard_quality"),
            ("core_feature", "full_518k_distribution", "negative_boundary"),
            "deterministic_replay_plus_distribution_eval",
            "已接 corpus runtime optimizer writer；完整 corpus artifacts 通过后可写 active corpus policy pointer。",
        ),
    ]


def _optimization_topic(
    key: str,
    label: str,
    roles: tuple[str, ...],
    atomic_trainings: tuple[str, ...],
    parameter_targets: tuple[str, ...],
    synthetic_gates: tuple[str, ...],
    model_pattern: str,
    current_gap: str,
) -> dict[str, object]:
    writer_ready = key in {
        "role_experience",
        "rule",
        "portrait",
        "knowledge",
        "intelligent_qa",
        "structure_dynamics",
        "llm_context",
        "feature_corpus",
    }
    return {
        "topic_key": key,
        "label": label,
        "roles": list(roles),
        "training_groups": _topic_training_groups(key),
        "atomic_trainings": list(atomic_trainings),
        "parameter_targets": list(parameter_targets),
        "synthetic_gates": list(synthetic_gates),
        "model_pattern": model_pattern,
        "optimizer_writer_status": "ready" if writer_ready else "missing_or_partial",
        "current_gap": current_gap,
        "runtime_mutation": False,
        "guardrails": [
            "TOPIC_PLAN_ONLY",
            "ATOMIC_TRAINING_MUST_WRITE_ARTIFACT_OR_POINTER",
            "SYNTHETIC_GATE_REQUIRED_BEFORE_RUNTIME_APPLY",
            "TRAINING_GROUPS_MAP_TOPIC_TO_ATOMIC_SCRIPTS_AND_POINTERS",
        ],
    }


def _topic_training_groups(key: str) -> list[dict[str, object]]:
    groups = {
        "structure_dynamics": (
            ("dynamic_path_validation", "做功链合成验证", ("structure_dynamics_synthetic", "synthetic_case_suite"), ("dynamic_path_weight", "semantic_match_weight"), ("structure_dynamics_runtime_policy_pointer", "orchestrator_runtime_policy_pointer", "rule_runtime_policy_pointer")),
            ("corpus_path_distribution", "518K 做功链分布", ("structure_dynamics_corpus_distribution", "structure_dynamics_scheduled_shard", "nightly_executor_skeleton", "full_precompute_preview"), ("structure_stability_floor", "semantic_match_weight"), ("structure_dynamics_runtime_policy_pointer", "orchestrator_runtime_policy_pointer")),
            ("time_trigger_replay", "岁运引动回放", ("structure_dynamics_synthetic", "rule_replay_eval"), ("time_trigger_weight", "volatility_threshold"), ("structure_dynamics_runtime_policy_pointer", "orchestrator_runtime_policy_pointer", "rule_runtime_policy_pointer")),
            ("dynamic_chain_stability", "结构链稳定性", ("rule_portrait_batch", "training_iteration_fast"), ("dynamic_path_weight", "structure_stability_floor"), ("structure_dynamics_runtime_policy_pointer", "orchestrator_runtime_policy_pointer")),
        ),
        "portrait": (
            ("axis_weighting", "画像轴权重", ("rule_portrait_batch",), ("portrait_axis_weight", "portrait_confidence_threshold"), ("portrait_runtime_policy_pointer",)),
            ("role_portrait_projection", "角色画像投射", ("practitioner_calibration_training", "training_iteration_fast"), ("role_portrait_depth", "topic_projection_weight"), ("portrait_runtime_policy_pointer", "role_view_runtime_policy_pointer")),
        ),
        "intelligent_qa": (
            ("source_ranking", "问题来源排序", ("question_source_training", "question_ranking_training"), ("question_source_weight", "question_rank_weight"), ("question_runtime_policy_pointer",)),
            ("dag_mainline", "问题链路与主线", ("question_dag_training", "next_question_synthetic_validation", "training_iteration_fast"), ("dag_transition_weight", "mainline_focus_weight", "next_question_stage_topic_boost"), ("question_runtime_policy_pointer", "orchestrator_runtime_policy_pointer")),
        ),
        "role_experience": (
            ("role_ordering", "角色问题顺序", ("role_interaction_training",), ("role_question_order", "role_question_count"), ("role_view_runtime_policy_pointer",)),
            ("role_visibility", "角色可见层", ("question_dag_training", "synthetic_case_suite"), ("role_visibility_level", "seed_fit_policy"), ("role_view_runtime_policy_pointer",)),
        ),
        "llm_context": (
            ("answer_contract", "回答合同", ("answer_governance_training",), ("answer_contract_structure_weight", "prompt_context_budget_weight"), ("role_view_runtime_policy_pointer", "orchestrator_runtime_policy_pointer")),
            ("bazi_context_profile", "八字上下文摘要", ("role_interaction_training", "synthetic_case_suite"), ("bazi_context_profile_weight", "role_context_density_weight"), ("knowledge_runtime_policy_pointer", "orchestrator_runtime_policy_pointer")),
        ),
        "feature_corpus": (
            ("corpus_shard_replay", "518K 分片回放", ("nightly_executor_skeleton", "full_precompute_preview"), ("corpus_shard_quality", "similar_case_weight"), ("corpus_runtime_policy_pointer",)),
            ("feature_distribution", "特征分布校准", ("training_iteration_deep",), ("feature_threshold", "coverage_prior"), ("corpus_runtime_policy_pointer",)),
        ),
        "rule": (
            ("synthetic_rule_boundary", "合成规则边界", ("rule_synthetic_training", "rule_subcondition_split"), ("rule_weight", "counterexample_weight"), ("rule_runtime_policy_pointer",)),
            ("rule_replay_activation", "规则回放生效", ("rule_replay_eval", "decision_registry_iteration"), ("rule_activation_weight", "subcondition_weight"), ("rule_runtime_policy_pointer",)),
        ),
        "knowledge": (
            ("knowledge_rule_mapping", "知识规则映射", ("knowledge_rule_orchestrator", "knowledge_rule_review_overlay"), ("knowledge_rule_mapping_weight", "source_trust_weight"), ("knowledge_runtime_policy_pointer",)),
            ("answer_boundary", "回答边界", ("answer_governance_training", "synthetic_case_suite"), ("answer_guidance_weight", "counterexample_coverage"), ("knowledge_runtime_policy_pointer",)),
        ),
    }.get(key, ())
    return [
        {
            "group_key": group_key,
            "label": label,
            "atomic_trainings": atomic,
            "parameter_targets": params,
            "runtime_pointer_targets": pointers,
            "runtime_mutation": False,
        }
        for group_key, label, atomic, params, pointers in groups
    ]


def _synthetic_rule_plan(coverage: dict[str, object]) -> dict[str, object]:
    missing_domains = [str(row) for row in coverage.get("missing_domains", [])]
    missing_stages = [str(row) for row in coverage.get("missing_stages", [])]
    missing_capabilities = [str(row) for row in coverage.get("missing_capabilities", [])]
    next_cases = [
        {"gap_type": "domain", "key": key, "recommended_task": "rule_synthetic_training"}
        for key in missing_domains
    ] + [
        {"gap_type": "dag_stage", "key": key, "recommended_task": "question_dag_training"}
        for key in missing_stages
    ] + [
        {"gap_type": "capability", "key": key, "recommended_task": "synthetic_case_suite"}
        for key in missing_capabilities
    ]
    return {
        "version": "v20.admin_synthetic_rule_training_plan.v1",
        "status": "needs_expansion" if next_cases else "covered",
        "case_count": int(coverage.get("case_count", 0) or 0),
        "gap_count": len(next_cases),
        "coverage_status": str(coverage.get("status", "")),
        "next_cases": next_cases[:12],
        "source_report": coverage,
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_PLAN_FROM_COVERAGE_REPORT",
            "NO_RULE_TRUTH_GENERATED_BY_PLAN",
            "NEXT_CASES_ARE_TRAINING_FIXTURE_REQUESTS",
        ],
    }


def _structure_dynamics_synthetic_plan(report: dict[str, object]) -> dict[str, object]:
    quality_scores = report.get("quality_scores", {}) if isinstance(report.get("quality_scores"), dict) else {}
    ok = bool(report.get("ok"))
    next_cases = []
    if not ok:
        next_cases.append(
            {
                "gap_type": "structure_dynamics_v2",
                "key": "dynamic_path_or_semantic_precision",
                "recommended_task": "structure_dynamics_synthetic",
            }
        )
    return {
        "version": "v20.admin_structure_dynamics_synthetic_plan.v1",
        "status": "covered" if ok else "needs_expansion",
        "case_count": int(report.get("case_count", 0) or 0),
        "pass_rate": float(report.get("pass_rate", 0.0) or 0.0),
        "dynamic_path_consistency": float(quality_scores.get("dynamic_path_consistency", 0.0) or 0.0),
        "semantic_candidate_precision": float(quality_scores.get("semantic_candidate_precision", 0.0) or 0.0),
        "next_cases": next_cases,
        "source_report": report,
        "runtime_mutation": False,
        "guardrails": [
            "SDE_V2_SYNTHETIC_PLAN_FROM_STRUCTURE_DYNAMICS_REPORT",
            "NO_RUNTIME_POINTER_MUTATION",
            "DYNAMIC_PATH_VALIDATION_REQUIRED_BEFORE_LEGACY_SWITCH",
        ],
    }


def _candidate_quality_signal(
    *,
    synthetic_plan: dict[str, object],
    structure_synthetic: dict[str, object],
    corpus_status: dict[str, object],
    corpus_training: dict[str, object],
) -> dict[str, object]:
    synthetic_gap_count = int(synthetic_plan.get("gap_count", 0) or 0)
    synthetic_ready = str(synthetic_plan.get("status", "")) == "covered" and synthetic_gap_count == 0
    corpus_artifact_status = str(corpus_status.get("status", ""))
    corpus_training_status = str(corpus_training.get("status", ""))
    corpus_ready = corpus_artifact_status in {"ready", "complete", "completed"} and corpus_training_status == "ready"
    blockers: list[str] = []
    if not synthetic_ready:
        blockers.append("synthetic_coverage_needs_expansion")
    structure_ready = bool(structure_synthetic.get("ok"))
    if not structure_ready:
        blockers.append("structure_dynamics_synthetic_not_ready")
    if not corpus_ready:
        blockers.append("corpus_518k_replay_artifacts_not_ready")
    recommended_tasks = []
    if not synthetic_ready:
        recommended_tasks.append("synthetic_case_suite")
        recommended_tasks.append("rule_synthetic_training")
    if not structure_ready:
        recommended_tasks.append("structure_dynamics_synthetic")
    if not corpus_ready:
        recommended_tasks.append("nightly_executor_skeleton")
        recommended_tasks.append("full_precompute_preview")
    quality_scores = _candidate_quality_scores(
        synthetic_plan=synthetic_plan,
        structure_synthetic=structure_synthetic,
        synthetic_ready=synthetic_ready,
        structure_ready=structure_ready,
        corpus_ready=corpus_ready,
        corpus_status=corpus_status,
        corpus_training=corpus_training,
    )
    if float(quality_scores.get("bazi_context_drift_score", 1.0)) > 0:
        blockers.append("bazi_context_alignment_drift")
    promotion_score = _candidate_promotion_score(quality_scores)
    promotion_threshold = 0.82
    return {
        "version": "v20.admin_candidate_quality_signal.v1",
        "status": "ready_for_candidate_apply" if not blockers and promotion_score >= promotion_threshold else "needs_more_replay",
        "synthetic_status": str(synthetic_plan.get("status", "")),
        "structure_dynamics_synthetic_status": "covered" if structure_ready else "needs_expansion",
        "synthetic_gap_count": synthetic_gap_count,
        "structure_dynamics_synthetic_case_count": int(structure_synthetic.get("case_count", 0) or 0),
        "corpus_artifact_status": corpus_artifact_status,
        "corpus_training_status": corpus_training_status,
        "corpus_run_id": str(corpus_training.get("run_id") or corpus_status.get("run_id") or ""),
        "quality_scores": quality_scores,
        "candidate_promotion_score": promotion_score,
        "promotion_threshold": promotion_threshold,
        "promotion_decision": "promote_candidate" if not blockers and promotion_score >= promotion_threshold else "run_recommended_replay",
        "gate_blockers": blockers,
        "recommended_tasks": tuple(dict.fromkeys(recommended_tasks)),
        "candidate_gate_note": (
            f"合成验证和 518K 回放评分达到 {promotion_score:.2f}，训练候选更容易直接进入 candidate_active。"
            if not blockers and promotion_score >= promotion_threshold
            else f"候选参数评分 {promotion_score:.2f}，仍可能被 machine gate 阻断；先补合成覆盖和 518K 小分片回放。"
        ),
        "runtime_mutation": False,
        "guardrails": [
            "QUALITY_SIGNAL_READ_ONLY",
            "SYNTHETIC_AND_CORPUS_REPLAY_FEED_MACHINE_GATE",
            "BAZI_CONTEXT_DRIFT_FEEDS_MACHINE_GATE",
            "PROMOTION_SCORE_COMBINES_SYNTHETIC_AND_518K_REPLAY",
            "NO_HUMAN_REVIEW_GATE",
            "NO_POINTER_WRITE_FROM_PLAN",
        ],
    }


def _candidate_quality_scores(
    *,
    synthetic_plan: dict[str, object],
    structure_synthetic: dict[str, object],
    synthetic_ready: bool,
    structure_ready: bool,
    corpus_ready: bool,
    corpus_status: dict[str, object],
    corpus_training: dict[str, object],
) -> dict[str, float]:
    synthetic_gap_count = int(synthetic_plan.get("gap_count", 0) or 0)
    synthetic_case_count = max(0, int(synthetic_plan.get("case_count", 0) or 0))
    synthetic_pass_rate = 1.0 if synthetic_ready else max(0.0, 1.0 - synthetic_gap_count / max(1, synthetic_case_count + synthetic_gap_count))
    rule_false_positive_rate = 0.0 if synthetic_ready else min(1.0, synthetic_gap_count / max(1, synthetic_case_count))
    portrait_drift_score = 1.0 - _corpus_artifact_stability(corpus_training, "portrait_axis_training", corpus_ready=corpus_ready)
    corpus_distribution_shift = 1.0 - _corpus_status_stability(corpus_status, corpus_training, corpus_ready=corpus_ready)
    similar_case_stability = _corpus_artifact_stability(corpus_training, "similarity_manifest", corpus_ready=corpus_ready)
    question_focus_score = 1.0 if synthetic_ready else synthetic_pass_rate
    bazi_context_drift_score = 0.0 if synthetic_ready else min(1.0, rule_false_positive_rate)
    structure_scores = structure_synthetic.get("quality_scores", {}) if isinstance(structure_synthetic.get("quality_scores"), dict) else {}
    dynamic_path_consistency = float(structure_scores.get("dynamic_path_consistency", 0.0) or 0.0)
    semantic_candidate_precision = float(structure_scores.get("semantic_candidate_precision", 0.0) or 0.0)
    return {
        "synthetic_pass_rate": round(synthetic_pass_rate, 4),
        "structure_dynamic_path_consistency": round(dynamic_path_consistency if structure_ready else min(dynamic_path_consistency, 0.81), 4),
        "structure_semantic_candidate_precision": round(semantic_candidate_precision if structure_ready else min(semantic_candidate_precision, 0.81), 4),
        "rule_false_positive_rate": round(rule_false_positive_rate, 4),
        "portrait_drift_score": round(portrait_drift_score, 4),
        "question_focus_score": round(question_focus_score, 4),
        "corpus_distribution_shift": round(corpus_distribution_shift, 4),
        "similar_case_stability": round(similar_case_stability, 4),
        "bazi_context_drift_score": round(bazi_context_drift_score, 4),
    }


def _candidate_promotion_score(scores: dict[str, float]) -> float:
    positive = (
        0.22 * float(scores.get("synthetic_pass_rate", 0.0))
        + 0.08 * float(scores.get("structure_dynamic_path_consistency", 0.0))
        + 0.06 * float(scores.get("structure_semantic_candidate_precision", 0.0))
        + 0.18 * (1.0 - float(scores.get("rule_false_positive_rate", 1.0)))
        + 0.12 * (1.0 - float(scores.get("portrait_drift_score", 1.0)))
        + 0.14 * float(scores.get("question_focus_score", 0.0))
        + 0.08 * (1.0 - float(scores.get("corpus_distribution_shift", 1.0)))
        + 0.08 * float(scores.get("similar_case_stability", 0.0))
        + 0.04 * (1.0 - float(scores.get("bazi_context_drift_score", 1.0)))
    )
    return round(max(0.0, min(1.0, positive)), 4)


def _corpus_artifact_stability(corpus_training: dict[str, object], key: str, *, corpus_ready: bool) -> float:
    artifact = corpus_training.get(key)
    if not corpus_ready or not isinstance(artifact, dict):
        return 0.0
    if artifact.get("status") != "ready":
        return 0.0
    case_count = int(artifact.get("case_count", 0) or 0)
    if case_count <= 0:
        return 0.0
    return min(1.0, case_count / 512.0)


def _corpus_status_stability(
    corpus_status: dict[str, object],
    corpus_training: dict[str, object],
    *,
    corpus_ready: bool,
) -> float:
    if not corpus_ready:
        return 0.0
    status_case_count = int(corpus_status.get("processed_count", corpus_status.get("case_count", 0)) or 0)
    training_case_count = max(
        int(_dict_value(corpus_training.get("portrait_axis_training")).get("case_count", 0) or 0),
        int(_dict_value(corpus_training.get("rule_proposal_training")).get("case_count", 0) or 0),
    )
    case_count = max(status_case_count, training_case_count)
    if case_count <= 0:
        return 0.0
    return min(1.0, case_count / 512.0)


def _dict_value(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _training_dedupe_summary(latest_by_key: dict[str, dict[str, object]]) -> dict[str, object]:
    specs = _admin_visible_task_specs(_task_specs())
    rows = [_task_dedupe_policy(spec, latest_by_key.get(spec.task_key, {})) for spec in specs]
    blocked = [row for row in rows if row.get("duplicate_blocked")]
    return {
        "version": "v20.admin_training_dedupe_summary.v1",
        "status": "active",
        "tracked_task_count": len(rows),
        "cooldown_blocked_count": len(blocked),
        "blocked_task_keys": [str(row.get("task_key", "")) for row in blocked],
        "runtime_mutation": False,
        "guardrails": [
            "DEDUP_SUMMARY_READ_ONLY",
            "COOLDOWN_ONLY_BLOCKS_IDENTICAL_SUCCESSFUL_RUNS",
            "FAILED_OR_PAUSED_TASKS_CAN_RERUN",
        ],
    }


def _task_dedupe_policy(spec: TrainingTaskSpec, latest: dict[str, object]) -> dict[str, object]:
    cooldown_hours = _cooldown_hours_for_spec(spec)
    last_status = str(latest.get("status", ""))
    last_updated = str(latest.get("updated_at", ""))
    age_seconds = _age_seconds(last_updated)
    duplicate_blocked = last_status == "succeeded" and age_seconds is not None and age_seconds < cooldown_hours * 3600
    remaining_seconds = max(0, int(cooldown_hours * 3600 - age_seconds)) if duplicate_blocked and age_seconds is not None else 0
    return {
        "version": "v20.admin_training_task_dedupe_policy.v1",
        "task_key": spec.task_key,
        "fingerprint": _task_fingerprint(spec),
        "cooldown_hours": cooldown_hours,
        "last_status": last_status,
        "last_updated_at": last_updated,
        "age_seconds": int(age_seconds) if age_seconds is not None else None,
        "duplicate_blocked": duplicate_blocked,
        "remaining_cooldown_seconds": remaining_seconds,
        "blocking_gate": "duplicate_success_cooldown" if duplicate_blocked else "",
        "reason": "同一脚本和参数已在冷却期内成功运行；避免无输入变化的重复训练。" if duplicate_blocked else "可运行；没有命中重复训练冷却。",
        "runtime_mutation": False,
        "guardrails": [
            "TASK_DEDUPE_USES_LATEST_SUCCESS_STATUS",
            "FAILED_TASKS_ARE_NOT_DEDUP_BLOCKED",
            "COOLDOWN_IS_PER_TASK_FINGERPRINT",
        ],
    }


def _cooldown_hours_for_spec(spec: TrainingTaskSpec) -> int:
    if spec.heavy_level == "heavy":
        return 24
    if spec.heavy_level == "medium":
        return 6
    return 1


def _task_fingerprint(spec: TrainingTaskSpec) -> str:
    payload = json.dumps(
        {
            "task_key": spec.task_key,
            "script_path": spec.script_path,
            "default_args": list(spec.default_args),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    import hashlib

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _age_seconds(value: str) -> float | None:
    parsed = _parse_datetime(value)
    if parsed is None:
        return None
    return max(0.0, (datetime.now(timezone.utc) - parsed).total_seconds())


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _training_mainline_completion() -> dict[str, object]:
    completed = _admin_training_completed_items()
    components = _training_mainline_components()
    remaining = [
        str(row["key"])
        for row in components
        if not bool(row.get("complete"))
    ]
    percent = int(round(sum(int(row.get("percent", 0) or 0) for row in components) / max(1, len(components))))
    return {
        "version": "v20.admin_training_mainline_completion.v1",
        "status": "complete" if not remaining else "needs_work",
        "percent": percent,
        "component_count": len(components),
        "components": components,
        "completed_count": len(completed),
        "remaining_count": len(remaining),
        "completed_items": completed,
        "remaining_items": remaining,
        "runtime_mutation": False,
        "guardrails": [
            "COMPLETION_STATUS_READ_ONLY",
            "NO_RUNTIME_POINTER_MUTATION",
            "COMPLETION_USES_LIGHTWEIGHT_COMPONENT_SNAPSHOT",
            "DOMAIN_APPLY_REQUIRES_EXPLICIT_CONFIRM_TOKEN",
        ],
    }


def _training_parameter_impact() -> dict[str, object]:
    rows = [
        _parameter_impact_row(
            "training_bundle",
            "orchestrator runtime policy payload",
            "auto_gated_active_pointer",
            "training_iteration_fast/deep can produce candidate policy versions; successful runs auto-apply through the machine gate.",
        ),
        _parameter_impact_row(
            "question_policy",
            "role-view question ordering policy",
            "auto_gated_active_pointer",
            "role_interaction_training uses role-view pointer; question source/ranking/DAG training uses question runtime pointer.",
        ),
        _parameter_impact_row(
            "rule_iteration",
            "rule replay and DecisionRegistry iteration signals",
            "auto_gated_active_pointer",
            "rule_iteration can activate rule weight policy automatically after replay and DecisionRegistry machine gate.",
        ),
        _parameter_impact_row(
            "portrait_policy",
            "portrait axis weighting and role portrait depth hints",
            "auto_gated_active_pointer",
            "rule_portrait_batch can activate portrait axis weight policy automatically after synthetic portrait alignment passes.",
        ),
        _parameter_impact_row(
            "knowledge_review",
            "knowledge review queue and rule proposal preflights",
            "auto_gated_active_pointer",
            "knowledge_rule_review_overlay can activate knowledge-rule mapping policy automatically after machine preflight passes.",
        ),
        _parameter_impact_row(
            "corpus_precompute",
            "offline corpus artifact indexes",
            "auto_gated_active_pointer",
            "completed corpus artifacts can activate feature thresholds, coverage priors, and similarity weights through a versioned pointer.",
        ),
    ]
    return {
        "version": "v20.admin_training_parameter_impact.v1",
        "status": "ready",
        "auto_parameter_optimization": True,
        "runtime_parameter_change_requires_activation": True,
        "families": rows,
        "impactful_family_count": sum(1 for row in rows if row["impact_mode"] == "auto_gated_active_pointer"),
        "optimizer_writer_missing_count": sum(1 for row in rows if row["impact_mode"] == "optimizer_writer_missing"),
        "artifact_only_count": sum(1 for row in rows if row["impact_mode"] == "artifact_only"),
        "runtime_mutation": False,
        "guardrails": [
            "SUPPORTED_TRAINING_AUTO_TUNES_THROUGH_MACHINE_GATE",
            "PARAMETER_CHANGES_REQUIRE_GATED_POINTER",
            "MISSING_OPTIMIZER_WRITERS_ARE_EXPLICIT",
        ],
    }


def _parameter_impact_row(family: str, target: str, impact_mode: str, note: str) -> dict[str, object]:
    return {
        "family": family,
        "target": target,
        "impact_mode": impact_mode,
        "note": note,
    }


def _admin_training_completed_items() -> list[str]:
    return [
        "curated_training_script_registry",
        "background_task_execution",
        "single_active_task_guard",
        "progress_pause_and_history",
        "result_summary_contract",
        "machine_gate_and_direct_apply",
        "publish_preview",
        "activation_family_router",
        "activation_preflight_history",
        "domain_gated_activation_adapter",
    ]


def _training_mainline_components() -> list[dict[str, object]]:
    try:
        from v20.ops.config import load_runtime_config_from_env
        from v20.ops.profiles import validate_runtime_config

        ops = validate_runtime_config(load_runtime_config_from_env())
    except Exception as exc:
        return [
            _completion_component("admin_training_page", 100, True, "admin training page contract complete"),
            _completion_component("system_components", 0, False, f"component status unavailable: {exc}"),
        ]
    return [
        _completion_component("admin_training_page", 100, True, "admin training page contract complete"),
        _completion_component(
            "knowledge_mainline",
            100,
            True,
            "knowledge optimizer writer is connected to gated active pointer",
        ),
        _completion_component(
            "rule_iteration",
            100,
            True,
            "rule replay and DecisionRegistry optimizer writer is connected",
        ),
        _completion_component(
            "corpus_precompute",
            100,
            True,
            "corpus optimizer writer is connected; missing artifacts block through machine gate",
        ),
        _completion_component(
            "ops_validation",
            100 if ops.get("ok") else 50,
            bool(ops.get("ok")),
            "ok" if ops.get("ok") else "degraded",
        ),
    ]


def _completion_component(key: str, percent: int, complete: bool, reason: str) -> dict[str, object]:
    return {
        "key": key,
        "percent": max(0, min(100, percent)),
        "complete": complete,
        "reason": reason,
    }


def _admin_task_payload(
    spec: TrainingTaskSpec,
    *,
    latest_by_key: dict[str, dict[str, object]] | None = None,
    recommended_key: str = "",
) -> dict[str, object]:
    section_key, section_label, section_order = _section_for_category(spec.category)
    guidance = ADMIN_TASK_GUIDANCE.get(spec.task_key, {})
    latest = (latest_by_key or {}).get(spec.task_key, {})
    dedupe = _task_dedupe_policy(spec, latest)
    brain_nodes = _brain_nodes_for_task_key(spec.task_key)
    return spec.to_dict() | {
        "section_key": section_key,
        "section_label": section_label,
        "section_order": section_order,
        "brain_nodes": brain_nodes,
        "primary_brain_node": brain_nodes[0] if brain_nodes else "",
        "runtime_pointer_targets": _runtime_pointer_targets_for_task_key(spec.task_key),
        "admin_visible": True,
        "recommended_order": int(guidance.get("order", 999)),
        "risk_level": str(guidance.get("risk_level", "normal")),
        "when_to_run": str(guidance.get("when_to_run", "")),
        "is_recommended_next": spec.task_key == recommended_key,
        "last_status": latest.get("status", ""),
        "last_updated_at": latest.get("updated_at", ""),
        "dedupe_policy": dedupe,
        "start_allowed": not bool(dedupe.get("duplicate_blocked")),
        "start_blocking_gate": str(dedupe.get("blocking_gate", "")),
    }


def _section_for_category(category: str) -> tuple[str, str, int]:
    return ADMIN_TASK_SECTION_BY_CATEGORY.get(category, ("other", "其他", 100))


def _latest_task_by_key() -> dict[str, dict[str, object]]:
    latest: dict[str, dict[str, object]] = {}
    rows = sorted(
        (_read_task(path) for path in _task_dir().glob("*.json") if path.name != "latest.json"),
        key=lambda row: str(row.get("updated_at", "")),
        reverse=True,
    )
    for row in rows:
        key = str(row.get("task_key", ""))
        if key and key not in latest:
            latest[key] = row
    return latest


def _active_training_task() -> dict[str, object]:
    visible_keys = set(ADMIN_VISIBLE_TASK_KEYS)
    rows = sorted(
        (_read_task(path) for path in _task_dir().glob("*.json") if path.name != "latest.json"),
        key=lambda row: str(row.get("updated_at", "")),
        reverse=True,
    )
    for row in rows:
        if str(row.get("task_key", "")) not in visible_keys:
            continue
        if _task_is_active(row):
            return row
    return {}


def _task_is_active(task: dict[str, object]) -> bool:
    status = str(task.get("status", ""))
    if status not in {"queued", "running"}:
        return False
    pid = int(task.get("pid", 0) or 0)
    if pid <= 0:
        return status == "queued"
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _recommended_next_task(
    specs: tuple[TrainingTaskSpec, ...],
    *,
    latest_by_key: dict[str, dict[str, object]],
    active_task: dict[str, object],
) -> dict[str, object]:
    if active_task.get("task_id"):
        return {
            "task_key": active_task.get("task_key", ""),
            "label": active_task.get("label", ""),
            "status": active_task.get("status", ""),
            "reason": "当前已有后台训练在运行；先等待完成或暂停。",
            "blocked_by_active_task": True,
        }
    ordered = sorted(specs, key=lambda spec: int(ADMIN_TASK_GUIDANCE.get(spec.task_key, {}).get("order", 999)))
    fast = next((spec for spec in ordered if spec.task_key == "training_iteration_fast"), ordered[0] if ordered else None)
    if fast is not None:
        fast_latest = latest_by_key.get(fast.task_key, {})
        if fast_latest.get("status") not in {"running", "queued"}:
            return _recommendation_payload(fast, fast_latest, reason="主线默认入口；优先运行日常轻量训练，再按专题补跑子任务。")
    for spec in ordered:
        latest = latest_by_key.get(spec.task_key, {})
        if latest.get("status") not in {"succeeded", "running", "queued"}:
            return _recommendation_payload(spec, latest, reason="该任务尚未成功运行，是当前最小下一步。")
    if fast is None:
        return {}
    return _recommendation_payload(fast, latest_by_key.get(fast.task_key, {}), reason="全部可见任务已有成功记录；回到日常轻量训练。")


def _recommendation_payload(spec: TrainingTaskSpec, latest: dict[str, object], *, reason: str) -> dict[str, object]:
    guidance = ADMIN_TASK_GUIDANCE.get(spec.task_key, {})
    return {
        "task_key": spec.task_key,
        "label": spec.label,
        "section": _section_for_category(spec.category)[1],
        "risk_level": str(guidance.get("risk_level", "normal")),
        "when_to_run": str(guidance.get("when_to_run", "")),
        "last_status": latest.get("status", "not_run"),
        "last_updated_at": latest.get("updated_at", ""),
        "reason": reason,
        "blocked_by_active_task": False,
    }


def _script_task(
    task_key: str,
    label: str,
    category: str,
    description: str,
    script_path: str,
    default_args: tuple[str, ...],
    heavy_level: str,
    *,
    runtime_mutation: bool = False,
) -> TrainingTaskSpec:
    return TrainingTaskSpec(
        task_key=task_key,
        label=label,
        category=category,
        description=description,
        script_path=script_path,
        default_args=default_args,
        heavy_level=heavy_level,
        estimated_duration="seconds_to_minutes" if heavy_level != "heavy" else "minutes_or_more",
        writes_artifact=runtime_mutation,
        runtime_mutation=runtime_mutation,
    )


def _spec_by_key(task_key: str) -> TrainingTaskSpec:
    for spec in _task_specs():
        if spec.task_key == task_key:
            return spec
    raise ValueError(f"Unknown training task: {task_key}")


def _base_state(task_id: str, spec: TrainingTaskSpec, *, source_role: str, extra_args: tuple[str, ...]) -> dict[str, object]:
    now = _now()
    return {
        "version": "v20.admin_training_task_state.v1",
        "task_id": _safe_task_id(task_id),
        "task_key": spec.task_key,
        "label": spec.label,
        "category": spec.category,
        "status": "queued",
        "progress_percent": 0,
        "current_stage": "queued",
        "source_role": source_role,
        "created_at": now,
        "started_at": now,
        "updated_at": now,
        "finished_at": "",
        "pid": 0,
        "extra_args": list(extra_args),
        "log_tail": [],
        "artifact_outputs": [],
        "error": "",
        "runtime_mutation": spec.runtime_mutation,
        "guardrails": [
            "TASK_STATUS_PERSISTED_TO_RUNTIME_DIR",
            "TASK_RUNS_IN_BACKGROUND_PROCESS",
            "NO_RUNTIME_POINTER_MUTATION_FROM_TASK",
        ],
    }


def _finish_state(state: dict[str, object], *, exit_code: int, started_at: datetime, log_tail: list[str]) -> dict[str, object]:
    status = "succeeded" if exit_code == 0 else "failed"
    return state | {
        "status": status,
        "exit_code": exit_code,
        "progress_percent": 100 if exit_code == 0 else int(state.get("progress_percent", 0) or 0),
        "current_stage": "completed" if exit_code == 0 else "failed",
        "finished_at": _now(),
        "updated_at": _now(),
        "elapsed_seconds": int((datetime.now(timezone.utc) - started_at).total_seconds()),
        "log_tail": log_tail,
    }


def _task_dir() -> Path:
    return local_jsonl_store_from_env().runtime_dir / "training" / "tasks"


def _write_task_state(state: dict[str, object]) -> None:
    directory = _task_dir()
    directory.mkdir(parents=True, exist_ok=True)
    task_id = _safe_task_id(str(state.get("task_id", "")))
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
    (directory / f"{task_id}.json").write_text(payload, encoding="utf-8")
    (directory / "latest.json").write_text(payload, encoding="utf-8")


def _read_task(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else _empty_task_status()
    except (OSError, json.JSONDecodeError):
        return _empty_task_status(task_id=path.stem)


def _empty_task_status(task_id: str = "") -> dict[str, object]:
    return {
        "version": "v20.admin_training_task_state.v1",
        "task_id": task_id,
        "status": "not_found",
        "progress_percent": 0,
        "current_stage": "",
        "runtime_mutation": False,
        "guardrails": ["TASK_STATUS_READ_ONLY"],
    }


def _with_result_summary(task: dict[str, object]) -> dict[str, object]:
    return task | {"result_summary": _task_result_summary(task)}


def _task_result_summary(task: dict[str, object]) -> dict[str, object]:
    status = str(task.get("status") or "not_found")
    payload = _contract_payload_from_log_tail(task)
    payload_status = str(payload.get("status") or "")
    risk = _result_risk(status=status, payload_status=payload_status, task=task)
    artifact_written = status == "succeeded" and (
        bool(task.get("runtime_mutation")) or _task_has_runtime_optimizer_evidence(task=task, payload=payload)
    )
    context_quality = _training_context_quality_signal(payload=payload, artifact_written=artifact_written)
    machine_gate = _machine_gate(
        status=status,
        risk=risk,
        artifact_written=artifact_written,
        payload=payload,
        context_quality=context_quality,
    )
    publish_preview = _publish_preview(
        task=task,
        machine_gate=machine_gate,
        artifact_written=artifact_written,
        payload=payload,
    )
    return {
        "version": "v20.admin_training_task_result_summary.v1",
        "status": status,
        "outcome": _result_outcome(status=status, payload_status=payload_status),
        "risk_level": risk,
        "recommended_action": _result_recommended_action(status=status, risk=risk),
        "artifact_written": artifact_written,
        "machine_gate": machine_gate,
        "context_quality_signal": context_quality,
        "publish_preview": publish_preview,
        "elapsed_seconds": int(task.get("elapsed_seconds", 0) or 0),
        "exit_code": task.get("exit_code", ""),
        "contract_status": payload_status,
        "contract_version": str(payload.get("version") or ""),
        "contract_script": str(payload.get("script_path") or payload.get("contract_command") or ""),
        "key_counts": _contract_key_counts(payload),
        "error": str(task.get("error") or payload.get("error") or ""),
        "guardrails": [
            "RESULT_SUMMARY_DERIVED_FROM_TASK_STATE",
            "LOG_TAIL_ONLY_NO_FULL_LOG_RENDER",
            "SUPPORTED_ARTIFACTS_AUTO_APPLY_THROUGH_OPTIMIZER",
            "TRAINING_CONTEXT_DRIFT_SIGNAL_EXPLICIT",
            "MACHINE_OPTIMIZATION_GATE_DOES_NOT_MUTATE_RUNTIME",
            "PUBLISH_PREVIEW_DOES_NOT_MUTATE_RUNTIME",
        ],
    }


def _contract_payload_from_log_tail(task: dict[str, object]) -> dict[str, object]:
    lines = task.get("log_tail", [])
    if not isinstance(lines, list):
        return {}
    log_path = Path(str(task.get("log_path", "")))
    if log_path.exists():
        try:
            file_lines = log_path.read_text(encoding="utf-8").splitlines()[-240:]
        except OSError:
            file_lines = []
        payload = _json_payload_from_lines(file_lines)
        if payload:
            return payload
    return _json_payload_from_lines([str(line) for line in lines])


def _json_payload_from_lines(lines: list[str]) -> dict[str, object]:
    text_lines = [str(line).strip() for line in lines]
    for index in range(len(text_lines)):
        if text_lines[index] != "{":
            continue
        try:
            payload = json.loads("\n".join(text_lines[index:]))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    for line in reversed(lines):
        text = str(line).strip()
        if not text.startswith("{"):
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _contract_key_counts(payload: dict[str, object]) -> dict[str, int]:
    keys = (
        "recommendations",
        "training_targets",
        "training_proposals",
        "candidate_policy",
        "cases",
        "case_results",
        "risk_count",
        "guardrails",
    )
    counts: dict[str, int] = {}
    for key in keys:
        value = payload.get(key)
        if isinstance(value, (list, tuple, dict)):
            counts[key] = len(value)
        elif isinstance(value, int):
            counts[key] = value
    return counts


def _result_outcome(*, status: str, payload_status: str) -> str:
    if status in {"queued", "running"}:
        return "运行中"
    if status == "paused":
        return "已暂停"
    if status == "succeeded":
        if payload_status in {"fail", "failed", "error"}:
            return "脚本完成但结果有风险"
        return "训练完成"
    if status == "failed":
        return "执行失败"
    return "暂无结果"


def _result_risk(*, status: str, payload_status: str, task: dict[str, object]) -> str:
    if status in {"failed", "pause_failed"} or payload_status in {"fail", "failed", "error"} or task.get("error"):
        return "high"
    if status in {"queued", "running", "paused"}:
        return "pending"
    return "low" if status == "succeeded" else "unknown"


def _result_recommended_action(*, status: str, risk: str) -> str:
    if status in {"queued", "running"}:
        return "等待任务完成；必要时使用暂停。"
    if status == "paused":
        return "确认是否需要重新运行推荐任务。"
    if risk == "high":
        return "查看日志尾巴和 artifact；本轮不会生效。"
    if status == "succeeded":
        return "机器优化 gate 已处理；有 runtime writer 的结果会直接尝试生效。"
    return "运行推荐下一步任务。"


def _machine_gate(
    *,
    status: str,
    risk: str,
    artifact_written: bool,
    payload: dict[str, object],
    context_quality: dict[str, object],
) -> dict[str, object]:
    if status in {"queued", "running"}:
        return _machine_gate_payload("pending", False, "任务仍在运行，等待完成后进入机器优化 gate。")
    if status == "paused":
        return _machine_gate_payload("paused", False, "任务已暂停，本轮结果不生效。")
    if status != "succeeded":
        return _machine_gate_payload("blocked", False, "任务未成功完成，不生效。")
    if risk == "high":
        return _machine_gate_payload("blocked", False, "结果摘要标记为高风险，不生效。")
    if not artifact_written:
        return _machine_gate_payload("observe_only", False, "本任务不写训练 artifact，仅作为验证。")
    if str(context_quality.get("status", "")) == "drifted":
        return _machine_gate_payload("blocked", False, "训练结果偏离当前八字上下文，不生效。")
    if _contract_payload_has_training_evidence(payload):
        return _machine_gate_payload("machine_ready", True, "机器 gate 通过；如果存在 runtime optimizer writer，会直接尝试生效。")
    return _machine_gate_payload("machine_ready", True, "脚本成功且写入训练 artifact；如果存在 runtime optimizer writer，会直接尝试生效。")


def _training_context_quality_signal(*, payload: dict[str, object], artifact_written: bool) -> dict[str, object]:
    alignment = payload.get("context_alignment_report")
    if isinstance(alignment, dict):
        drift_score = float(alignment.get("drift_score", 1.0) or 0.0)
        return {
            "version": "v20.training_context_quality_signal.v1",
            "status": "aligned" if drift_score == 0 else "drifted",
            "bazi_context_drift_score": round(max(0.0, min(1.0, drift_score)), 4),
            "context_id": str(alignment.get("context_id", "")),
            "aligned_count": int(alignment.get("aligned_count", 0) or 0),
            "module_count": int(alignment.get("module_count", 0) or 0),
            "source": "runtime_context_alignment_report",
            "runtime_mutation": False,
            "guardrails": [
                "TRAINING_RESULT_MUST_STAY_BOUND_TO_CURRENT_BAZI_CONTEXT",
                "CONTEXT_DRIFT_BLOCKS_PARAMETER_APPLY",
            ],
        }
    return {
        "version": "v20.training_context_quality_signal.v1",
        "status": "not_declared" if artifact_written else "observe_only",
        "bazi_context_drift_score": 0.0,
        "context_id": "",
        "aligned_count": 0,
        "module_count": 0,
        "source": "training_payload_has_no_runtime_context_report",
        "runtime_mutation": False,
        "guardrails": [
            "TRAINING_CONTEXT_SIGNAL_DEFAULTS_TO_NON_BLOCKING_FOR_LEGACY_ARTIFACTS",
            "NEW_CONTEXT_AWARE_TRAINING_SHOULD_EMIT_CONTEXT_ALIGNMENT_REPORT",
        ],
    }


def _machine_gate_payload(status: str, can_apply: bool, reason: str) -> dict[str, object]:
    return {
        "version": "v20.admin_training_task_machine_gate.v1",
        "status": status,
        "can_apply_parameters": can_apply,
        "reason": reason,
        "guardrails": [
            "MACHINE_OPTIMIZATION_GATE_READ_ONLY",
            "NO_RUNTIME_POINTER_MUTATION",
            "NO_HUMAN_REVIEW_REQUIRED_FOR_SUPPORTED_OPTIMIZERS",
        ],
    }


def _contract_payload_has_training_evidence(payload: dict[str, object]) -> bool:
    for key in ("recommendations", "training_proposals", "candidate_policy", "artifact_path", "latest_path", "run_path"):
        value = payload.get(key)
        if isinstance(value, (list, tuple, dict)) and len(value) > 0:
            return True
        if isinstance(value, str) and value:
            return True
    return False


def _task_has_runtime_optimizer_evidence(*, task: dict[str, object], payload: dict[str, object]) -> bool:
    task_key = str(task.get("task_key", ""))
    if task_key == "structure_dynamics_synthetic":
        quality = payload.get("quality_scores", {}) if isinstance(payload.get("quality_scores"), dict) else {}
        return (
            payload.get("version") == "v20.structure_dynamics_synthetic.v1"
            and payload.get("ok") is True
            and int(payload.get("case_count", 0) or 0) >= 1
            and "dynamic_path_consistency" in quality
            and "semantic_candidate_precision" in quality
        )
    if task_key in {"structure_dynamics_corpus_distribution", "structure_dynamics_scheduled_shard"}:
        return (
            payload.get("version") == "v20.structure_dynamics_corpus_distribution.v1"
            and str(payload.get("status", "")) in {"completed", "completed_with_findings"}
            and int(payload.get("limit", payload.get("case_count", 0)) or 0) >= 1
            and int(payload.get("unsupported_label_count", 0) or 0) == 0
        )
    return False


def _read_ledger_payloads(ledger_name: str, *, limit: int) -> list[dict[str, object]]:
    path = local_jsonl_store_from_env().runtime_dir / "ledger" / f"{ledger_name}.jsonl"
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[dict[str, object]] = []
    for line in reversed(lines[-500:]):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        rows.append(payload | {
            "record_id": str(row.get("record_id", "")),
            "created_at": str(row.get("created_at", "")),
        })
        if len(rows) >= limit:
            break
    return rows


def _publish_preview(
    *,
    task: dict[str, object],
    machine_gate: dict[str, object],
    artifact_written: bool,
    payload: dict[str, object],
) -> dict[str, object]:
    status = str(task.get("status") or "")
    auto_policy = _auto_optimization_policy(task=task, machine_gate=machine_gate, status=status)
    if status in {"queued", "running"}:
        preview_status = "pending"
        eligible = False
        reason = "任务仍在运行，完成后自动进入机器优化 gate。"
    elif not bool(machine_gate.get("can_apply_parameters")):
        preview_status = "blocked"
        eligible = False
        reason = f"机器 gate 未通过：{machine_gate.get('reason') or '不可生效'}"
    elif not bool(auto_policy.get("parameter_apply_supported")):
        preview_status = "optimizer_missing"
        eligible = False
        reason = "训练产物已生成，但这个原子脚本还没有 runtime optimizer writer；需要补 writer 后才能直接优化系统。"
    else:
        preview_status = "ready"
        eligible = True
        reason = "已通过机器优化 gate；训练完成后会直接尝试生效，可手动重试。"
    return {
        "version": "v20.admin_training_task_publish_preview.v1",
        "status": preview_status,
        "eligible_for_publish": eligible,
        "reason": reason,
        "artifact_written": artifact_written,
        "activation_family": _activation_family_for_task(task),
        "activation_target": _activation_target_for_task(task),
        "auto_optimization": auto_policy,
        "impacted_targets": _publish_preview_targets(task=task, payload=payload),
        "runtime_mutation": False,
        "guardrails": [
            "PUBLISH_PREVIEW_READ_ONLY",
            "DOMAIN_ROUTED_ACTIVATION_REQUIRED",
            "NO_RUNTIME_POINTER_MUTATION",
            "SUPPORTED_OPTIMIZERS_AUTO_APPLY_AFTER_TRAINING",
        ],
    }


def _publish_preview_targets(*, task: dict[str, object], payload: dict[str, object]) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    for key in ("artifact_path", "latest_path", "run_path", "output_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            targets.append({"target_type": "artifact", "key": key, "value": value})
    if not targets:
        targets.append(
            {
                "target_type": "task_result",
                "key": str(task.get("task_key") or "training_task"),
                "value": str(task.get("log_path") or task.get("task_id") or "result_summary"),
            }
        )
    return targets[:5]


def _auto_apply_training_parameters(task: dict[str, object]) -> dict[str, object] | None:
    if task.get("status") != "succeeded":
        return None
    if not _parameter_apply_supported_for_task(task):
        return None
    if task.get("auto_parameter_apply"):
        return None
    task_id = str(task.get("task_id", ""))
    if not task_id:
        return None
    try:
        result = prepare_training_task_activation(
            task_id,
            dry_run=False,
            confirm_token=TRAINING_ACTIVATION_CONFIRM_TOKEN,
            reason="system auto parameter apply after training success",
            source_role="system",
        )
    except Exception as exc:
        result = {
            "version": "v20.admin_training_auto_parameter_apply_error.v1",
            "status": "failed",
            "error": str(exc),
            "runtime_mutation": False,
        }
    return task | {
        "auto_parameter_apply": result,
        "auto_parameter_apply_status": str(result.get("status", "failed")),
        "runtime_mutation": bool(task.get("runtime_mutation")) or bool(result.get("runtime_mutation")),
        "updated_at": _now(),
        "guardrails": list(task.get("guardrails", [])) + ["AUTO_PARAMETER_APPLY_USES_DOMAIN_GATE"],
    }


def _auto_optimization_policy(*, task: dict[str, object], machine_gate: dict[str, object], status: str) -> dict[str, object]:
    family = _activation_family_for_task(task)
    supported = _parameter_apply_supported_for_task(task)
    candidate = status == "succeeded" and supported and bool(machine_gate.get("can_apply_parameters"))
    return {
        "version": "v20.admin_training_auto_optimization_policy.v1",
        "enabled": True,
        "parameter_apply_supported": supported,
        "auto_apply_candidate": candidate,
        "activation_family": family,
        "optimizer_writer": _optimizer_writer_for_task(task),
        "mode": "auto_gate_then_apply" if supported else "optimizer_writer_missing",
        "reason": "supported task uses gated pointer apply and does not require human review" if supported else "task still lacks a runtime optimizer writer",
        "runtime_mutation": False,
        "guardrails": [
            "AUTO_OPTIMIZATION_REPLACES_MANUAL_REVIEW_FOR_SUPPORTED_OPTIMIZERS",
            "DOMAIN_GATE_STILL_REQUIRED",
            "NO_RUNTIME_WRITE_WHEN_GATE_BLOCKS",
        ],
    }


def _activation_blocking_gate(*, preview: dict[str, object], requested_apply: bool) -> str:
    if requested_apply:
        return "admin_training_page_dry_run_only"
    if not bool(preview.get("eligible_for_publish")):
        return str(preview.get("status") or "publish_preview_not_ready")
    return ""


def _domain_activation_result(
    *,
    task: dict[str, object],
    eligible: bool,
    family: str,
    dry_run: bool,
    confirm_token: str,
    reason: str,
    source_role: str,
) -> dict[str, object]:
    requested_apply = not dry_run
    if not eligible:
        return _domain_activation_payload("blocked", family, "publish_preview_not_eligible", runtime_mutation=False)
    if not requested_apply:
        return _domain_activation_payload("ready", family, "", runtime_mutation=False)
    if confirm_token != TRAINING_ACTIVATION_CONFIRM_TOKEN:
        return _domain_activation_payload("blocked", family, "activation_confirm_token_required", runtime_mutation=False)
    task_key = str(task.get("task_key", ""))
    if family == "question_policy" and task_key == "role_interaction_training":
        from v20.role_view.runtime_pointer import write_role_view_runtime_pointer_activate_candidate

        result = write_role_view_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)
        return _domain_activation_payload(
            str(result.get("status", "blocked")),
            family,
            "" if result.get("runtime_mutation") else str(result.get("status", "blocked")),
            runtime_mutation=bool(result.get("runtime_mutation")),
            result=result,
        )
    if family == "question_policy":
        from v20.learning.question_runtime_pointer import write_question_runtime_pointer_activate_candidate

        result = write_question_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)
        return _domain_activation_payload(
            str(result.get("status", "blocked")),
            family,
            "" if result.get("runtime_mutation") else str(result.get("status", "blocked")),
            runtime_mutation=bool(result.get("runtime_mutation")),
            result=result,
        )
    if family == "training_bundle":
        result = _activate_training_bundle(source_role=source_role, reason=reason)
        return _domain_activation_payload(
            str(result.get("status", "blocked")),
            family,
            "" if result.get("runtime_mutation") else str(result.get("blocking_gate") or result.get("status", "blocked")),
            runtime_mutation=bool(result.get("runtime_mutation")),
            result=result,
        )
    if family == "rule_iteration":
        from v20.learning.rule_runtime_pointer import write_rule_runtime_pointer_activate_candidate

        result = write_rule_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)
        return _domain_activation_payload(
            str(result.get("status", "blocked")),
            family,
            "" if result.get("runtime_mutation") else str(result.get("status", "blocked")),
            runtime_mutation=bool(result.get("runtime_mutation")),
            result=result,
        )
    if family == "portrait_policy":
        from v20.learning.portrait_runtime_pointer import write_portrait_runtime_pointer_activate_candidate

        result = write_portrait_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)
        return _domain_activation_payload(
            str(result.get("status", "blocked")),
            family,
            "" if result.get("runtime_mutation") else str(result.get("status", "blocked")),
            runtime_mutation=bool(result.get("runtime_mutation")),
            result=result,
        )
    if family == "structure_dynamics_policy":
        from v20.learning.structure_dynamics_runtime_pointer import write_structure_dynamics_runtime_pointer_activate_candidate

        result = write_structure_dynamics_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)
        return _domain_activation_payload(
            str(result.get("status", "blocked")),
            family,
            "" if result.get("runtime_mutation") else str(result.get("status", "blocked")),
            runtime_mutation=bool(result.get("runtime_mutation")),
            result=result,
        )
    if family == "knowledge_review":
        from v20.learning.knowledge_runtime_pointer import write_knowledge_runtime_pointer_activate_candidate

        result = write_knowledge_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)
        return _domain_activation_payload(
            str(result.get("status", "blocked")),
            family,
            "" if result.get("runtime_mutation") else str(result.get("status", "blocked")),
            runtime_mutation=bool(result.get("runtime_mutation")),
            result=result,
        )
    if family == "corpus_precompute":
        from v20.learning.corpus_runtime_pointer import write_corpus_runtime_pointer_activate_candidate

        result = write_corpus_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)
        return _domain_activation_payload(
            str(result.get("status", "blocked")),
            family,
            "" if result.get("runtime_mutation") else str(result.get("status", "blocked")),
            runtime_mutation=bool(result.get("runtime_mutation")),
            result=result,
        )
    return _optimizer_writer_missing_result(family=family, task_key=task_key)


def _optimizer_writer_missing_result(*, family: str, task_key: str) -> dict[str, object]:
    return _domain_activation_payload(
        "blocked",
        family,
        f"{family}_optimizer_writer_missing",
        runtime_mutation=False,
        result={
            "version": "v20.admin_training_optimizer_writer_missing.v1",
            "status": "blocked",
            "task_key": task_key,
            "activation_family": family,
            "reason": "该原子训练脚本还没有 runtime optimizer writer；必须补 writer 后才能直接生效。",
            "runtime_mutation": False,
            "guardrails": [
                "MISSING_OPTIMIZER_WRITER_EXPLICIT",
                "NO_HUMAN_REVIEW_FALLBACK",
                "NO_RUNTIME_WRITE_WITHOUT_POINTER_WRITER",
            ],
        },
    )


def _activate_training_bundle(*, source_role: str, reason: str) -> dict[str, object]:
    writer_specs = (
        ("orchestrator_policy", _activate_orchestrator_policy),
        ("question_policy", _activate_question_policy),
        ("role_view_policy", _activate_role_view_policy),
        ("rule_policy", _activate_rule_policy),
        ("portrait_policy", _activate_portrait_policy),
        ("structure_dynamics_policy", _activate_structure_dynamics_policy),
        ("knowledge_policy", _activate_knowledge_policy),
        ("corpus_policy", _activate_corpus_policy),
    )
    results: list[dict[str, object]] = []
    for writer_key, writer in writer_specs:
        try:
            result = writer(source_role=source_role, reason=reason)
        except Exception as exc:
            result = {
                "version": "v20.training_bundle_writer_error.v1",
                "status": "failed",
                "error": str(exc),
                "runtime_mutation": False,
            }
        results.append(
            {
                "writer_key": writer_key,
                "status": str(result.get("status", "")),
                "runtime_mutation": bool(result.get("runtime_mutation")),
                "active_policy_version": str(result.get("active_policy_version", "")),
                "blocking_gate": str(result.get("blocking_gate", "")) or ("" if result.get("runtime_mutation") else str(result.get("status", ""))),
                "domain_result": result,
            }
        )
    activated = [row for row in results if bool(row.get("runtime_mutation"))]
    blocked = [row for row in results if not bool(row.get("runtime_mutation"))]
    status = "bundle_active" if activated else "blocked_by_machine_gate"
    apply_report = _training_bundle_apply_report(results)
    return {
        "version": "v20.training_bundle_activation_result.v1",
        "status": status,
        "activated_writer_count": len(activated),
        "blocked_writer_count": len(blocked),
        "writer_count": len(results),
        "writer_results": results,
        "apply_report": apply_report,
        "blocking_gate": "" if activated else "all_training_bundle_writers_blocked",
        "runtime_mutation": bool(activated),
        "guardrails": [
            "TRAINING_BUNDLE_AUTO_APPLIES_EACH_SUPPORTED_POINTER",
            "TRAINING_BUNDLE_EMITS_UNIFIED_APPLY_REPORT",
            "FAILED_POINTER_GATE_DOES_NOT_BLOCK_OTHER_POINTERS",
            "NO_HUMAN_REVIEW_GATE",
            "ROLLBACK_REMAINS_POINTER_BASED",
        ],
    }


def _training_bundle_apply_report(results: list[dict[str, object]]) -> dict[str, object]:
    rows = []
    for row in results:
        writer_key = str(row.get("writer_key", ""))
        rows.append(
            {
                "writer_key": writer_key,
                "runtime_pointer_target": _runtime_pointer_target_for_writer(writer_key),
                "status": "applied" if bool(row.get("runtime_mutation")) else "blocked",
                "active_policy_version": str(row.get("active_policy_version", "")),
                "blocking_gate": str(row.get("blocking_gate", "")),
                "runtime_mutation": False,
            }
        )
    applied = [row for row in rows if row["status"] == "applied"]
    return {
        "version": "v20.training_bundle_apply_report.v1",
        "status": "partial_applied" if applied and len(applied) < len(rows) else ("applied" if applied else "blocked"),
        "applied_pointer_count": len(applied),
        "blocked_pointer_count": len(rows) - len(applied),
        "pointer_count": len(rows),
        "pointer_results": rows,
        "runtime_mutation": False,
        "guardrails": [
            "APPLY_REPORT_SUMMARIZES_POINTER_WRITER_RESULTS",
            "FAILED_POINTER_DOES_NOT_HIDE_SUCCESSFUL_POINTERS",
            "NO_HUMAN_REVIEW_GATE",
        ],
    }


def _runtime_pointer_target_for_writer(writer_key: str) -> str:
    return {
        "orchestrator_policy": "orchestrator_runtime_policy_pointer",
        "question_policy": "question_runtime_policy_pointer",
        "role_view_policy": "role_view_runtime_policy_pointer",
        "rule_policy": "rule_runtime_policy_pointer",
        "portrait_policy": "portrait_runtime_policy_pointer",
        "structure_dynamics_policy": "structure_dynamics_runtime_policy_pointer",
        "knowledge_policy": "knowledge_runtime_policy_pointer",
        "corpus_policy": "corpus_runtime_policy_pointer",
    }.get(writer_key, "")


def _activate_orchestrator_policy(*, source_role: str, reason: str) -> dict[str, object]:
    from v20.orchestrator.runtime_policy import write_runtime_policy_activate_latest_candidate

    return write_runtime_policy_activate_latest_candidate(source_role=source_role, reason=reason)


def _activate_question_policy(*, source_role: str, reason: str) -> dict[str, object]:
    from v20.learning.question_runtime_pointer import write_question_runtime_pointer_activate_candidate

    return write_question_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)


def _activate_role_view_policy(*, source_role: str, reason: str) -> dict[str, object]:
    from v20.role_view.runtime_pointer import write_role_view_runtime_pointer_activate_candidate

    return write_role_view_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)


def _activate_rule_policy(*, source_role: str, reason: str) -> dict[str, object]:
    from v20.learning.rule_runtime_pointer import write_rule_runtime_pointer_activate_candidate

    return write_rule_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)


def _activate_portrait_policy(*, source_role: str, reason: str) -> dict[str, object]:
    from v20.learning.portrait_runtime_pointer import write_portrait_runtime_pointer_activate_candidate

    return write_portrait_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)


def _activate_structure_dynamics_policy(*, source_role: str, reason: str) -> dict[str, object]:
    from v20.learning.structure_dynamics_runtime_pointer import write_structure_dynamics_runtime_pointer_activate_candidate

    return write_structure_dynamics_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)


def _activate_knowledge_policy(*, source_role: str, reason: str) -> dict[str, object]:
    from v20.learning.knowledge_runtime_pointer import write_knowledge_runtime_pointer_activate_candidate

    return write_knowledge_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)


def _activate_corpus_policy(*, source_role: str, reason: str) -> dict[str, object]:
    from v20.learning.corpus_runtime_pointer import write_corpus_runtime_pointer_activate_candidate

    return write_corpus_runtime_pointer_activate_candidate(source_role=source_role, reason=reason)


def _rule_iteration_reviewer_result() -> dict[str, object]:
    from v20.learning.decision_registry_iteration import read_decision_registry_iteration_artifact
    from v20.learning.rule_replay_eval import read_rule_replay_eval_artifact

    replay = read_rule_replay_eval_artifact()
    registry = read_decision_registry_iteration_artifact()
    replay_ready = replay.get("status") == "ready" and int(replay.get("runtime_activation_count", 0) or 0) > 0
    registry_ready = registry.get("status") == "ready" and int(registry.get("runtime_activation_count", 0) or 0) > 0
    if not replay_ready or not registry_ready:
        return _domain_activation_payload(
            "blocked",
            "rule_iteration",
            "rule_replay_or_decision_registry_artifact_missing",
            runtime_mutation=False,
            result={
                "version": "v20.admin_rule_iteration_reviewer.v1",
                "status": "blocked",
                "replay_status": replay.get("status", "not_built"),
                "registry_status": registry.get("status", "not_built"),
                "runtime_mutation": False,
            },
        )
    return _domain_activation_payload(
        "review_ready",
        "rule_iteration",
        "",
        runtime_mutation=False,
        result={
            "version": "v20.admin_rule_iteration_reviewer.v1",
            "status": "review_ready",
            "replay_status": replay.get("status", ""),
            "registry_status": registry.get("status", ""),
            "replay_runtime_activation_count": replay.get("runtime_activation_count", 0),
            "registry_runtime_activation_count": registry.get("runtime_activation_count", 0),
            "runtime_effect": "rule_iteration_review_ready_no_pointer_write",
            "runtime_mutation": False,
            "guardrails": [
                "RULE_ITERATION_REVIEWER_READS_ARTIFACTS_ONLY",
                "NO_RUNTIME_POINTER_MUTATION",
                "DECISION_REGISTRY_ARTIFACT_REQUIRED",
            ],
        },
    )


def _knowledge_review_reviewer_result() -> dict[str, object]:
    from v20.knowledge.approval import build_first_wave_approval_preflight
    from v20.knowledge.review_queue import build_knowledge_review_queue
    from v20.knowledge.rule_proposal import build_first_wave_rule_proposal_preflight

    queue = build_knowledge_review_queue(limit_per_domain=3)
    approval = build_first_wave_approval_preflight()
    proposal = build_first_wave_rule_proposal_preflight(limit_per_domain=1)
    queue_ready = queue.get("status") == "ready" and int(queue.get("candidate_count", 0) or 0) > 0
    approval_ready = approval.get("status") == "ready_for_decision_review" and bool(approval.get("ok"))
    proposal_ready = proposal.get("status") == "active_ready" and bool(proposal.get("ok"))
    if not queue_ready or not approval_ready or not proposal_ready:
        blockers = []
        if not queue_ready:
            blockers.append("knowledge_review_queue_not_ready")
        if not approval_ready:
            blockers.append("first_wave_approval_preflight_blocked")
        if not proposal_ready:
            blockers.append("rule_proposal_preflight_blocked")
        return _domain_activation_payload(
            "blocked",
            "knowledge_review",
            ",".join(blockers),
            runtime_mutation=False,
            result={
                "version": "v20.admin_knowledge_review_reviewer.v1",
                "status": "blocked",
                "queue_status": queue.get("status", "empty"),
                "queue_candidate_count": queue.get("candidate_count", 0),
                "approval_status": approval.get("status", ""),
                "approval_blocked_domain_count": approval.get("blocked_domain_count", 0),
                "proposal_status": proposal.get("status", ""),
                "proposal_blocked_domain_count": proposal.get("blocked_domain_count", 0),
                "runtime_mutation": False,
            },
        )
    return _domain_activation_payload(
        "review_ready",
        "knowledge_review",
        "",
        runtime_mutation=False,
        result={
            "version": "v20.admin_knowledge_review_reviewer.v1",
            "status": "review_ready",
            "queue_candidate_count": queue.get("candidate_count", 0),
            "approval_domain_count": approval.get("domain_count", 0),
            "proposal_count": proposal.get("proposal_count", 0),
            "runtime_effect": "knowledge_review_ready_no_runtime_activation",
            "runtime_mutation": False,
            "guardrails": [
                "KNOWLEDGE_REVIEWER_READS_PREFLIGHTS_ONLY",
                "NO_RUNTIME_KNOWLEDGE_ACTIVATION",
                "DECISION_REVIEW_REQUIRED_BEFORE_RELEASE",
            ],
        },
    )


def _domain_activation_payload(
    status: str,
    family: str,
    blocking_gate: str,
    *,
    runtime_mutation: bool,
    result: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "version": "v20.admin_training_domain_activation_result.v1",
        "status": status,
        "activation_family": family,
        "blocking_gate": blocking_gate,
        "domain_result": result or {},
        "runtime_mutation": runtime_mutation,
        "guardrails": [
            "DOMAIN_ACTIVATION_GATE_REQUIRED",
            "CONFIRM_TOKEN_REQUIRED_FOR_APPLY",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
        ],
    }


def _activation_family_for_task(task: dict[str, object]) -> str:
    task_key = str(task.get("task_key", ""))
    category = str(task.get("category", ""))
    if task_key == "knowledge_rule_orchestrator":
        return "training_bundle"
    if task_key in {"question_source_training", "question_ranking_training", "question_dag_training", "role_interaction_training"}:
        return "question_policy"
    if task_key == "structure_dynamics_synthetic":
        return "structure_dynamics_policy"
    if task_key in {"structure_dynamics_corpus_distribution", "structure_dynamics_scheduled_shard"}:
        return "structure_dynamics_policy"
    if category == "portrait" or task_key == "rule_portrait_batch":
        return "portrait_policy"
    if category in {"rule", "synthetic"} or task_key == "rule_synthetic_training":
        return "rule_iteration"
    if category == "knowledge" or task_key == "extract_rules_llm_draft":
        return "knowledge_review"
    if category == "corpus" or task_key in {"nightly_executor_skeleton", "full_precompute_preview"}:
        return "corpus_precompute"
    if category in {"fast", "training"} or task_key.startswith("training_iteration_"):
        return "training_bundle"
    return "manual_review"


def _activation_target_for_task(task: dict[str, object]) -> str:
    family = _activation_family_for_task(task)
    return {
        "question_policy": "question_runtime_policy_pointer",
        "portrait_policy": "portrait_axis_weight_pointer",
        "structure_dynamics_policy": "structure_dynamics_runtime_policy_pointer",
        "rule_iteration": "rule_validation_and_decision_registry",
        "knowledge_review": "knowledge_rule_mapping_pointer",
        "corpus_precompute": "corpus_runtime_policy_pointer",
        "training_bundle": "multi_artifact_training_bundle",
        "manual_review": "manual_activation_review",
    }.get(family, "manual_activation_review")


def _parameter_apply_supported_for_task(task: dict[str, object]) -> bool:
    family = _activation_family_for_task(task)
    return family in {
        "training_bundle",
        "question_policy",
        "rule_iteration",
        "structure_dynamics_policy",
        "portrait_policy",
        "knowledge_review",
        "corpus_precompute",
    }


def _optimizer_writer_for_task(task: dict[str, object]) -> str:
    family = _activation_family_for_task(task)
    task_key = str(task.get("task_key", ""))
    if family == "training_bundle":
        return "training_bundle_multi_pointer_writer"
    if family == "question_policy" and task_key != "role_interaction_training":
        return "question_runtime_policy_pointer"
    if family == "rule_iteration":
        return "rule_runtime_policy_pointer"
    if family == "portrait_policy":
        return "portrait_runtime_policy_pointer"
    if family == "structure_dynamics_policy":
        return "structure_dynamics_runtime_policy_pointer"
    if family == "knowledge_review":
        return "knowledge_runtime_policy_pointer"
    if family == "corpus_precompute":
        return "corpus_runtime_policy_pointer"
    if task_key == "role_interaction_training":
        return "role_view_runtime_policy_pointer"
    return ""


def _safe_task_id(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]", "_", str(value or "task"))
    return clean[:160] or "task"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact_command(command: list[str]) -> list[str]:
    redacted: list[str] = []
    skip_next = False
    for value in command:
        if skip_next:
            redacted.append("REDACTED")
            skip_next = False
            continue
        redacted.append(value)
        if value in {"--password", "--api-key", "--token", "--secret"}:
            skip_next = True
    return redacted


def _progress_from_line(line: str, state: dict[str, object]) -> int:
    match = re.search(r"\[(\d+)/(\d+)\]", line)
    if match:
        current = int(match.group(1))
        total = max(1, int(match.group(2)))
        return min(98, max(3, int(current / total * 98)))
    if "running replay" in line:
        return max(int(state.get("progress_percent", 0) or 0), 35)
    if line.startswith("{") or '"status"' in line:
        return max(int(state.get("progress_percent", 0) or 0), 90)
    return max(int(state.get("progress_percent", 0) or 0), 5)


def _stage_from_line(line: str) -> str:
    match = re.search(r"\[\d+/\d+\]\s+([^:]+)", line)
    if match:
        return match.group(1).strip()
    if "running replay" in line:
        return "synthetic_replay"
    if "error" in line.lower():
        return "error"
    return ""
