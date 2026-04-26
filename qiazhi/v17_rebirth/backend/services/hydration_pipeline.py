from __future__ import annotations

from collections import Counter
from typing import Any

from v17_rebirth.backend.services.plugin_governance import classify_plugin_governance


HYDRATION_PIPELINE_PROTOCOL = "v17.hydration_pipeline.v1"
ALGORITHM_EXECUTION_POLICY_PROTOCOL = "v17.algorithm_execution_policy.v1"
ALGORITHM_EXECUTION_TRACE_PROTOCOL = "v17.algorithm_execution_trace.v1"
ALGORITHM_EXECUTION_AUDIT_PROTOCOL = "v17.algorithm_execution_audit.v1"

EXPECTED_EXECUTION_STAGES: tuple[str, ...] = (
    "geometry_built",
    "base_runtime_ready",
    "plugin_manifest_ready",
    "plugin_scan_completed",
    "claims_compiled",
    "conflicts_routed",
    "modifier_settlement_completed",
    "decision_buckets_ready",
    "flow_applied",
    "runtime_synced",
    "meta_contract_built",
)

EXECUTION_STAGE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "stage": "geometry_built",
        "phase": "foundation",
        "label": "几何关系建模",
        "category": "physics",
        "critical": True,
        "requires": (),
        "sovereignty_sensitive": False,
    },
    {
        "stage": "base_runtime_ready",
        "phase": "foundation",
        "label": "基线与运行态就绪",
        "category": "physics",
        "critical": True,
        "requires": ("geometry_built",),
        "sovereignty_sensitive": False,
    },
    {
        "stage": "plugin_manifest_ready",
        "phase": "plugin_pipeline",
        "label": "插件治理清单就绪",
        "category": "governance",
        "critical": True,
        "requires": ("base_runtime_ready",),
        "sovereignty_sensitive": True,
    },
    {
        "stage": "plugin_scan_completed",
        "phase": "plugin_pipeline",
        "label": "插件扫描完成",
        "category": "plugin_scan",
        "critical": True,
        "requires": ("plugin_manifest_ready",),
        "sovereignty_sensitive": True,
    },
    {
        "stage": "claims_compiled",
        "phase": "reasoning",
        "label": "主张编译",
        "category": "claims",
        "critical": True,
        "requires": ("plugin_scan_completed",),
        "sovereignty_sensitive": True,
    },
    {
        "stage": "conflicts_routed",
        "phase": "reasoning",
        "label": "冲突路由",
        "category": "conflict",
        "critical": True,
        "requires": ("claims_compiled",),
        "sovereignty_sensitive": True,
    },
    {
        "stage": "modifier_settlement_completed",
        "phase": "settlement",
        "label": "统一结算完成",
        "category": "settlement",
        "critical": True,
        "requires": ("conflicts_routed",),
        "sovereignty_sensitive": True,
    },
    {
        "stage": "decision_buckets_ready",
        "phase": "settlement",
        "label": "决策分桶完成",
        "category": "decision",
        "critical": False,
        "requires": ("modifier_settlement_completed",),
        "sovereignty_sensitive": False,
    },
    {
        "stage": "flow_applied",
        "phase": "runtime",
        "label": "流转平衡完成",
        "category": "flow",
        "critical": True,
        "requires": ("modifier_settlement_completed",),
        "sovereignty_sensitive": False,
    },
    {
        "stage": "runtime_synced",
        "phase": "runtime",
        "label": "运行态同步",
        "category": "authority_gate",
        "critical": True,
        "requires": ("flow_applied",),
        "sovereignty_sensitive": True,
        "gate_stage": True,
    },
    {
        "stage": "meta_contract_built",
        "phase": "contract",
        "label": "元数据契约构建",
        "category": "contract",
        "critical": True,
        "requires": ("runtime_synced",),
        "sovereignty_sensitive": True,
    },
)

EXECUTION_STAGE_SPEC_BY_NAME: dict[str, dict[str, Any]] = {
    str(row["stage"]): dict(row) for row in EXECUTION_STAGE_SPECS
}


def build_algorithm_execution_policy() -> dict[str, Any]:
    return {
        "protocol": ALGORITHM_EXECUTION_POLICY_PROTOCOL,
        "expected_stages": list(EXPECTED_EXECUTION_STAGES),
        "critical_path": [
            str(row["stage"])
            for row in EXECUTION_STAGE_SPECS
            if bool(row.get("critical"))
        ],
        "gate_stages": [
            str(row["stage"])
            for row in EXECUTION_STAGE_SPECS
            if bool(row.get("gate_stage"))
        ],
        "stages": [dict(row) for row in EXECUTION_STAGE_SPECS],
    }


def build_plugin_governance_manifest(specs: list[Any]) -> dict[str, Any]:
    profiles: list[dict[str, Any]] = []
    for spec in specs or []:
        pid = str(getattr(spec, "plugin_id", "") or "").strip()
        if not pid:
            continue
        profiles.append(
            classify_plugin_governance(
                plugin_id=pid,
                layer=_layer_from_tier(int(getattr(spec, "causal_tier", 3) or 3)),
                causal_tier=int(getattr(spec, "causal_tier", 3) or 3),
                manifest={},
            )
        )
    class_counts = Counter(str(row.get("governance_class") or "") for row in profiles)
    authority_counts = Counter(str(row.get("authority_level") or "") for row in profiles)
    return {
        "protocol": HYDRATION_PIPELINE_PROTOCOL,
        "plugin_count": len(profiles),
        "governance_class_counts": dict(class_counts),
        "authority_level_counts": dict(authority_counts),
        "profiles": profiles,
    }


def bucket_decision_records(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [dict(row) for row in decisions or [] if isinstance(row, dict)]
    manual = [d for d in rows if str(d.get("arbiter_type") or "user") == "user"]
    system = [d for d in rows if str(d.get("arbiter_type") or "") == "system"]
    llm = [d for d in rows if str(d.get("arbiter_type") or "") == "llm"]
    return {
        "protocol": HYDRATION_PIPELINE_PROTOCOL,
        "manual_decisions": manual,
        "auto_resolutions": system,
        "llm_arbitration_context": llm,
        "manual_inbox": list(manual),
        "auto_decisions": [*system, *llm],
        "decision_inbox_contract": "v17.decision.inbox.v2",
        "bucket_counts": {
            "manual": len(manual),
            "system": len(system),
            "llm": len(llm),
            "total": len(rows),
        },
    }


def append_algorithm_execution_stage(
    meta: dict[str, Any],
    *,
    stage: str,
    label: str,
    detail: str = "",
    counts: dict[str, Any] | None = None,
    sovereignty: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = meta if isinstance(meta, dict) else {}
    stage_name = str(stage or "").strip()
    spec = EXECUTION_STAGE_SPEC_BY_NAME.get(stage_name, {})
    trace = source.get("algorithm_execution_trace")
    if not isinstance(trace, dict):
        trace = {
            "protocol": ALGORITHM_EXECUTION_TRACE_PROTOCOL,
            "expected_stages": list(EXPECTED_EXECUTION_STAGES),
            "policy_protocol": ALGORITHM_EXECUTION_POLICY_PROTOCOL,
            "stages": [],
        }
        source["algorithm_execution_trace"] = trace
    rows = trace.get("stages")
    if not isinstance(rows, list):
        rows = []
        trace["stages"] = rows
    rows.append(
        {
            "index": len(rows),
            "stage": stage_name,
            "label": str(label or spec.get("label") or "").strip(),
            "detail": str(detail or "").strip(),
            "phase": str(spec.get("phase") or "").strip(),
            "category": str(spec.get("category") or "").strip(),
            "critical": bool(spec.get("critical")),
            "requires": list(spec.get("requires") or ()),
            "sovereignty_sensitive": bool(spec.get("sovereignty_sensitive")),
            "counts": dict(counts or {}),
            "sovereignty": dict(sovereignty or {}),
        }
    )
    trace["completed_stage_count"] = len(rows)
    trace["completed_stages"] = [str(row.get("stage") or "").strip() for row in rows if str(row.get("stage") or "").strip()]
    return trace


def build_algorithm_execution_audit(trace_value: Any) -> dict[str, Any]:
    trace = trace_value if isinstance(trace_value, dict) else {}
    policy = build_algorithm_execution_policy()
    rows = trace.get("stages") if isinstance(trace.get("stages"), list) else []
    normalized_rows = [row for row in rows if isinstance(row, dict)]
    stage_names = [str(row.get("stage") or "").strip() for row in normalized_rows if str(row.get("stage") or "").strip()]
    first_seen: dict[str, int] = {}
    duplicates: list[str] = []
    for idx, stage in enumerate(stage_names):
        if stage in first_seen:
            duplicates.append(stage)
            continue
        first_seen[stage] = idx
    missing = [stage for stage in EXPECTED_EXECUTION_STAGES if stage not in first_seen]
    out_of_order_pairs: list[str] = []
    previous_idx = -1
    previous_stage = ""
    for stage in EXPECTED_EXECUTION_STAGES:
        idx = first_seen.get(stage)
        if idx is None:
            continue
        if idx < previous_idx and previous_stage:
            out_of_order_pairs.append(f"{previous_stage}->{stage}")
        previous_idx = idx
        previous_stage = stage
    dependency_violations: list[str] = []
    critical_dependency_violations: list[str] = []
    for spec in EXECUTION_STAGE_SPECS:
        stage_name = str(spec["stage"])
        stage_idx = first_seen.get(stage_name)
        if stage_idx is None:
            continue
        for required in (spec.get("requires") or ()):
            required_name = str(required)
            required_idx = first_seen.get(required_name)
            if required_idx is None or required_idx > stage_idx:
                edge = f"{required_name}->{stage_name}"
                dependency_violations.append(edge)
                if bool(spec.get("critical")):
                    critical_dependency_violations.append(edge)
    critical_missing = [
        str(spec["stage"])
        for spec in EXECUTION_STAGE_SPECS
        if bool(spec.get("critical")) and str(spec["stage"]) in missing
    ]
    phase_completion: dict[str, float] = {}
    phase_specs: dict[str, list[str]] = {}
    for spec in EXECUTION_STAGE_SPECS:
        phase = str(spec.get("phase") or "unknown")
        phase_specs.setdefault(phase, []).append(str(spec["stage"]))
    for phase, phase_stage_names in phase_specs.items():
        completed_count = sum(1 for stage in phase_stage_names if stage in first_seen)
        phase_completion[phase] = round(completed_count / max(1, len(phase_stage_names)), 3)
    sovereignty_rows = [row.get("sovereignty") for row in normalized_rows if isinstance(row.get("sovereignty"), dict)]

    def _flag(name: str) -> bool:
        return any(bool(row.get(name)) for row in sovereignty_rows)

    coverage = round(len({stage for stage in stage_names if stage in EXPECTED_EXECUTION_STAGES}) / max(1, len(EXPECTED_EXECUTION_STAGES)), 3)
    order_ok = not missing and not out_of_order_pairs
    settlement_seen = "modifier_settlement_completed" in first_seen
    authority_present = _flag("hard_authority_present")
    authority_gate_present = _flag("authority_layer_protocol_present")
    critical_path_ok = not critical_missing and not critical_dependency_violations
    gate_stage_ok = (
        "runtime_synced" in first_seen
        and settlement_seen
        and authority_gate_present
    )
    watch_stages = list(
        dict.fromkeys(
            [
                *missing,
                *[edge.split("->")[-1] for edge in dependency_violations],
                *([] if authority_gate_present else ["runtime_synced"]),
            ]
        )
    )
    validated_stages = [
        stage
        for stage in EXPECTED_EXECUTION_STAGES
        if stage in first_seen and stage not in watch_stages
    ]
    summary = "healthy"
    if not order_ok or not settlement_seen or not critical_path_ok or not gate_stage_ok:
        summary = "needs_review"
    elif coverage < 1.0 or not authority_present or not authority_gate_present:
        summary = "partial"
    return {
        "protocol": ALGORITHM_EXECUTION_AUDIT_PROTOCOL,
        "policy_protocol": policy["protocol"],
        "expected_stages": list(EXPECTED_EXECUTION_STAGES),
        "critical_path": list(policy["critical_path"]),
        "gate_stages": list(policy["gate_stages"]),
        "completed_stages": stage_names,
        "completed_stage_count": len(stage_names),
        "trace_coverage_ratio": coverage,
        "order_ok": bool(order_ok),
        "missing_stages": missing,
        "duplicate_stages": list(dict.fromkeys(duplicates)),
        "out_of_order_pairs": out_of_order_pairs,
        "dependency_violations": list(dict.fromkeys(dependency_violations)),
        "critical_missing_stages": critical_missing,
        "critical_dependency_violations": list(dict.fromkeys(critical_dependency_violations)),
        "critical_path_ok": bool(critical_path_ok),
        "gate_stage_ok": bool(gate_stage_ok),
        "validated_stages": validated_stages,
        "watch_stages": watch_stages,
        "phase_completion": phase_completion,
        "settlement_seen": settlement_seen,
        "flow_seen": "flow_applied" in first_seen,
        "meta_contract_seen": "meta_contract_built" in first_seen,
        "hard_authority_present": authority_present,
        "blind_theme_present": _flag("blind_theme_present"),
        "climate_theme_present": _flag("climate_theme_present"),
        "xiangfa_theme_present": _flag("xiangfa_theme_present"),
        "bazi_image_present": _flag("bazi_image_present"),
        "macro_theme_present": _flag("macro_theme_present"),
        "wealth_profile_present": _flag("wealth_profile_present"),
        "wealth_code_present": _flag("wealth_code_present"),
        "authority_layer_protocol_present": authority_gate_present,
        "summary": summary,
    }


def _layer_from_tier(causal_tier: int) -> str:
    # This is a fallback for specs without module metadata; plugin_id rules remain primary.
    if causal_tier >= 5:
        return "L0"
    if causal_tier == 4:
        return "L1"
    if causal_tier == 3:
        return "L2"
    if causal_tier == 2:
        return "L3"
    return "L4"
