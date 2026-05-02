from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.learning.self_evolution import read_self_evolution_artifact, run_self_evolution_cycle
from v20.storage.local_jsonl import local_jsonl_store_from_env


def build_active_package(
    manifest: dict[str, object] | None = None,
    *,
    include_rule_batch: bool = False,
    corpus_preview_limit: int = 0,
) -> dict[str, object]:
    source = manifest or run_self_evolution_cycle(
        write=False,
        include_rule_batch=include_rule_batch,
        corpus_preview_limit=corpus_preview_limit,
    )
    request_pack = source.get("active_item_requests", {})
    requests = _requests(request_pack)
    active_items = tuple(_active_item_from_request(row, source) for row in requests)
    kind_counts = Counter(str(row["active_item_type"]) for row in active_items)
    gate_counts = Counter(str(row["next_gate"]) for row in active_items)
    return {
        "version": "v20.active_package.v1",
        "package_id": _package_id(source),
        "source_run_id": source.get("run_id", ""),
        "source_manifest_status": source.get("status", ""),
        "status": "active" if active_items else "empty",
        "active_item_count": len(active_items),
        "active_item_type_counts": dict(sorted(kind_counts.items())),
        "next_gate_counts": dict(sorted(gate_counts.items())),
        "active_items": active_items,
        "validation_plan": _validation_plan(active_items),
        "activation_policy": {
            "runtime_activation_allowed": True,
            "active_package_can_promote": True,
            "requires_decision_registry": False,
            "required_final_status": "active",
        },
        "runtime_mutation": False,
        "guardrails": (
            "ACTIVE_PACKAGE_CAN_FEED_RUNTIME",
            "SYNTHETIC_AND_REPLAY_EVAL_ARE_CONTINUOUS_TUNING_SIGNALS",
            "LLM_OUTPUT_IS_DRAFT_NOT_CORE_TRUTH",
            "CORE_FACTS_STILL_REQUIRE_DETERMINISTIC_RUNTIME",
        ),
    }


def write_active_package_artifact(
    package: dict[str, object] | None = None,
    *,
    output_dir: Path | None = None,
) -> dict[str, object]:
    payload = package or build_active_package()
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    root = output_dir or runtime_dir / "training" / "active_packages"
    root.mkdir(parents=True, exist_ok=True)
    package_id = str(payload.get("package_id", _package_id(payload)))
    run_dir = root / _safe(package_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "latest.json"
    package_path = run_dir / "active_package.json"
    stored = payload | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(stored, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    package_path.write_text(json.dumps(stored, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.active_package_artifact_write.v1",
        "status": "written",
        "package_status": payload.get("status", ""),
        "active_item_count": payload.get("active_item_count", 0),
        "latest_path": str(latest_path),
        "package_path": str(package_path),
        "runtime_mutation": True,
        "guardrails": (
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "ACTIVE_PACKAGE_OUTPUT_ALLOWED",
        ),
    }


def read_active_package_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "active_packages") / "latest.json"
    if not latest_path.exists():
        latest_manifest = read_self_evolution_artifact()
        return {
            "version": "v20.active_package_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "upstream_self_evolution_status": latest_manifest.get("status", "not_built"),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {
        "latest_path": str(latest_path),
        "runtime_mutation": False,
    }


def _active_item_from_request(request: dict[str, object], manifest: dict[str, object]) -> dict[str, object]:
    active_item_type = str(request.get("request_type", "active_item"))
    target = str(request.get("target", ""))
    action = str(request.get("recommended_action", "review_active_item"))
    active_item_id = _active_item_id(active_item_type, target, action, str(manifest.get("run_id", "")))
    return {
        "version": "v20.learning_active_item.v1",
        "active_item_id": active_item_id,
        "active_item_type": active_item_type,
        "target": target,
        "title": _title(active_item_type, target, action),
        "source_artifact": request.get("source_artifact", ""),
        "source_action": action,
        "evidence": request.get("evidence", {}),
        "active_item_status": "active",
        "next_gate": _next_gate(active_item_type, action),
        "validation_requirements": _validation_requirements(active_item_type),
        "llm_role": _llm_role(active_item_type),
        "draft_contract": _draft_contract(active_item_type),
        "runtime_allowed": True,
        "risk": _risk(active_item_type, target, action),
        "guardrails": (
            "ACTIVE_ITEM_IS_ACTIVE_ITERATION_UNIT",
            "EVIDENCE_PACK_REQUIRED",
            "SYNTHETIC_AND_REPLAY_VALIDATION_REFINE_OUTPUTS",
        ),
    }


def _requests(request_pack: object) -> list[dict[str, object]]:
    if not isinstance(request_pack, dict):
        return []
    rows: list[dict[str, object]] = []
    for key in (
        "rule_active_item_requests",
        "portrait_active_item_requests",
        "feature_active_item_requests",
        "question_active_item_requests",
        "synthetic_case_requests",
    ):
        value = request_pack.get(key, ())
        if isinstance(value, (list, tuple)):
            rows.extend(row for row in value if isinstance(row, dict))
    return rows


def _validation_plan(active_items: tuple[dict[str, object], ...]) -> dict[str, object]:
    gates = tuple(dict.fromkeys(str(row["next_gate"]) for row in active_items if row.get("next_gate")))
    return {
        "version": "v20.active_item_validation_plan.v1",
        "status": "active" if active_items else "empty",
        "required_gates": gates,
        "batch_order": (
            "contract_validation",
            "synthetic_case_materialization",
            "runtime_replay",
            "runtime_replay_eval",
            "decision_registry_iteration",
        ),
        "blocked_runtime_outputs": (
            "llm_direct_decision_override",
            "llm_direct_chart_fact_generation",
        ),
    }


def _validation_requirements(active_item_type: str) -> tuple[str, ...]:
    common = ("contract_validation", "evidence_pack_link", "decision_registry_record")
    if active_item_type == "rule_active_item":
        return (*common, "positive_synthetic_case", "negative_synthetic_case", "counterexample_case", "runtime_replay_eval")
    if active_item_type == "portrait_active_item":
        return (*common, "rule_decision_mapping", "topic_projection_check", "language_safety_check")
    if active_item_type == "feature_active_item":
        return (*common, "chart_fact_trace", "counterevidence_trace", "topic_projection_check")
    if active_item_type == "question_active_item":
        return (*common, "question_intent_binding", "ranking_runtime_replay_eval", "answer_plan_alignment")
    if active_item_type == "synthetic_case":
        return ("case_contract_validation", "expected_feature_assertions", "forbidden_text_assertions")
    return common


def _next_gate(active_item_type: str, action: str) -> str:
    if active_item_type == "synthetic_case":
        return "synthetic_case_materialization"
    if active_item_type == "rule_active_item" and "activate" in action:
        return "active_rule_runtime_replay"
    if active_item_type == "rule_active_item":
        return "synthetic_validation"
    if active_item_type == "portrait_active_item":
        return "portrait_projection_batch"
    if active_item_type == "feature_active_item":
        return "feature_trace_validation"
    if active_item_type == "question_active_item":
        return "active_question_ranking_replay"
    return "contract_validation"


def _llm_role(active_item_type: str) -> str:
    roles = {
        "rule_active_item": "rule_drafter",
        "portrait_active_item": "feature_assistant",
        "feature_active_item": "feature_assistant",
        "question_active_item": "question_designer",
        "synthetic_case": "safety_reviewer",
    }
    return roles.get(active_item_type, "safety_reviewer")


def _draft_contract(active_item_type: str) -> dict[str, object]:
    if active_item_type == "rule_active_item":
        return {
            "outputs": ("RuleCondition[]", "RuleCounterEvidence[]", "RuleProjection[]"),
            "forbidden": ("fortune_verdict", "untraced_condition"),
        }
    if active_item_type == "portrait_active_item":
        return {
            "outputs": ("PortraitAxisActive", "TopicProjectionActive"),
            "forbidden": ("personality_label_without_evidence", "fixed_life_judgment"),
        }
    if active_item_type == "feature_active_item":
        return {
            "outputs": ("BaziFeatureActive", "TraceNodeActive"),
            "forbidden": ("feature_without_chart_fact", "feature_without_counterevidence_boundary"),
        }
    if active_item_type == "question_active_item":
        return {
            "outputs": ("QuestionActive", "QuestionIntentBinding"),
            "forbidden": ("generic_question_without_current_chart_anchor",),
        }
    return {
        "outputs": ("SyntheticCaseProposal",),
        "forbidden": ("destiny_truth_label", "event_outcome_label"),
    }


def _risk(active_item_type: str, target: str, action: str) -> str:
    if target in {"health", "relationship"}:
        return "medium"
    if active_item_type == "rule_active_item" and "activate" in action:
        return "medium_high"
    if active_item_type == "synthetic_case":
        return "low"
    return "medium_low"


def _title(active_item_type: str, target: str, action: str) -> str:
    labels = {
        "rule_active_item": "规则候选",
        "portrait_active_item": "画像候选",
        "feature_active_item": "八字特征候选",
        "question_active_item": "智能问题候选",
        "synthetic_case": "合成八字候选",
    }
    return f"{labels.get(active_item_type, '候选')} · {target or 'unknown'} · {action}"


def _package_id(source: dict[str, object]) -> str:
    raw = json.dumps(
        {
            "run_id": source.get("run_id", ""),
            "status": source.get("status", ""),
            "active_item_requests": source.get("active_item_requests", {}),
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return f"v20.active_package.{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def _active_item_id(active_item_type: str, target: str, action: str, run_id: str) -> str:
    raw = "|".join((active_item_type, target, action, run_id))
    return f"v20.active_item.{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value.strip())
