from __future__ import annotations

import hashlib
import json
from typing import Any

from v20.core.schemas import ChartFacts, TimeContext


BAZI_CONTEXT_FRAME_VERSION = "v20.bazi_context_frame.v1"
BAZI_CONTEXT_BINDING_VERSION = "v20.bazi_context_binding.v1"
BAZI_CONTEXT_ALIGNMENT_REPORT_VERSION = "v20.bazi_context_alignment_report.v1"


def build_bazi_context_frame(
    *,
    chart_facts: ChartFacts,
    time_context: TimeContext,
    input_id: str = "",
) -> dict[str, object]:
    chart_payload = chart_facts.to_dict()
    time_payload = time_context.to_dict()
    pillar_displays = _pillar_displays(chart_payload)
    time_layers = _time_layers(time_payload)
    context_seed = {
        "pillars": pillar_displays,
        "day_master": chart_payload.get("day_master", ""),
        "time_layers": time_layers,
    }
    context_id = "v20.bazi_context." + hashlib.sha256(
        json.dumps(context_seed, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "version": BAZI_CONTEXT_FRAME_VERSION,
        "status": "ready",
        "context_id": context_id,
        "request_input_id": input_id,
        "anchor_scope": "chart_facts+luck+flow_year+flow_month",
        "natal_pillars": pillar_displays,
        "day_master": chart_payload.get("day_master", ""),
        "day_master_element": chart_payload.get("day_master_element", ""),
        "time_context_status": time_payload.get("status", ""),
        "time_layers": time_layers,
        "time_relation_count": len(time_payload.get("relation_hits", ()) or ()),
        "required_consumers": [
            "structure_dynamics",
            "portrait_projection",
            "question_intent_model",
            "mainline_arbitration",
            "llm_context_pack",
        ],
        "binding_policy": {
            "fact_source": "current_measured_chart_only",
            "time_source": "explicit_luck_flow_year_flow_month_only",
            "role_policy": "role_changes_visibility_and_voice_not_facts",
            "llm_policy": "llm_consumes_locked_context_and_must_not_recalculate_chart",
            "drift_action": "drop_or_downrank_outputs_without_current_context_anchor",
        },
        "runtime_mutation": False,
        "guardrails": [
            "BAZI_CONTEXT_FRAME_IS_SINGLE_RUNTIME_FACT_ANCHOR",
            "NO_MODULE_OUTPUT_WITHOUT_CURRENT_CHART_CONTEXT",
            "LUCK_AND_FLOW_YEAR_ARE_EXPLICIT_TIME_CONTEXT_ONLY",
            "FUTURE_GEO_CONTEXT_MUST_EXTEND_THIS_FRAME_NOT_REPLACE_IT",
        ],
    }


def build_context_binding(
    frame: dict[str, object],
    *,
    module_key: str,
    evidence_domains: tuple[str, ...] = (),
    feature_ids: tuple[str, ...] = (),
    time_sensitive: bool = False,
) -> dict[str, object]:
    evidence_domains = tuple(row for row in evidence_domains if str(row))
    feature_ids = tuple(row for row in feature_ids if str(row))
    anchors = _evidence_anchors(
        module_key=module_key,
        evidence_domains=evidence_domains,
        feature_ids=feature_ids,
        time_sensitive=time_sensitive,
    )
    return {
        "version": BAZI_CONTEXT_BINDING_VERSION,
        "status": "bound" if frame.get("context_id") else "missing_context",
        "context_id": frame.get("context_id", ""),
        "module_key": module_key,
        "anchor_scope": frame.get("anchor_scope", ""),
        "natal_pillars": frame.get("natal_pillars", {}),
        "time_context_status": frame.get("time_context_status", ""),
        "time_layers": frame.get("time_layers", []),
        "time_sensitive": time_sensitive,
        "evidence_domains": list(dict.fromkeys(evidence_domains)),
        "feature_ids": list(dict.fromkeys(feature_ids))[:16],
        "evidence_anchor_count": len(anchors),
        "evidence_anchors": anchors,
        "drift_policy": "module_output_must_trace_to_context_id_or_be_downranked",
        "runtime_mutation": False,
    }


def attach_context_binding(
    payload: object,
    frame: dict[str, object],
    *,
    module_key: str,
    evidence_domains: tuple[str, ...] = (),
    feature_ids: tuple[str, ...] = (),
    time_sensitive: bool = False,
) -> object:
    if not isinstance(payload, dict):
        return payload
    payload["context_binding"] = build_context_binding(
        frame,
        module_key=module_key,
        evidence_domains=evidence_domains,
        feature_ids=feature_ids,
        time_sensitive=time_sensitive,
    )
    guardrails = list(payload.get("guardrails", ()) or ())
    if "OUTPUT_BOUND_TO_CURRENT_BAZI_CONTEXT" not in guardrails:
        guardrails.append("OUTPUT_BOUND_TO_CURRENT_BAZI_CONTEXT")
    payload["guardrails"] = guardrails
    return payload


def build_context_alignment_report(
    frame: dict[str, object],
    *,
    bindings: dict[str, object],
) -> dict[str, object]:
    expected_context_id = str(frame.get("context_id", ""))
    module_rows = []
    drift_count = 0
    missing_count = 0
    for module_key in frame.get("required_consumers", ()) or ():
        binding = bindings.get(str(module_key), {})
        if not isinstance(binding, dict):
            binding = {}
        bound_context_id = str(binding.get("context_id", ""))
        status = str(binding.get("status", "missing_context"))
        if not bound_context_id:
            alignment = "missing"
            missing_count += 1
        elif bound_context_id != expected_context_id:
            alignment = "drifted"
            drift_count += 1
        elif status == "bound":
            alignment = "aligned"
        else:
            alignment = status or "unknown"
        module_rows.append(
            {
                "module_key": module_key,
                "alignment": alignment,
                "status": status,
                "context_id": bound_context_id,
                "time_sensitive": bool(binding.get("time_sensitive", False)),
                "evidence_domains": list(binding.get("evidence_domains", ()) or ())[:8],
                "evidence_anchor_count": int(binding.get("evidence_anchor_count", 0) or 0),
            }
        )
    total = len(module_rows) or 1
    drift_score = round((drift_count + missing_count) / total, 4)
    aligned_count = sum(1 for row in module_rows if row["alignment"] == "aligned")
    return {
        "version": BAZI_CONTEXT_ALIGNMENT_REPORT_VERSION,
        "status": "aligned" if aligned_count == len(module_rows) else "needs_attention",
        "context_id": expected_context_id,
        "anchor_scope": frame.get("anchor_scope", ""),
        "drift_score": drift_score,
        "aligned_count": aligned_count,
        "missing_count": missing_count,
        "drift_count": drift_count,
        "module_count": len(module_rows),
        "modules": module_rows,
        "guardrails": [
            "CONTEXT_ALIGNMENT_REPORT_IS_RUNTIME_OBSERVABILITY",
            "DRIFT_SCORE_ZERO_MEANS_ALL_REQUIRED_MODULES_SHARE_CURRENT_CONTEXT",
        ],
        "runtime_mutation": False,
    }


def _pillar_displays(chart_payload: dict[str, Any]) -> dict[str, str]:
    pillars = chart_payload.get("pillars", {})
    if not isinstance(pillars, dict):
        return {}
    rows = {}
    for key in ("year", "month", "day", "hour"):
        pillar = pillars.get(key, {})
        if not isinstance(pillar, dict):
            continue
        rows[key] = f"{pillar.get('stem', '')}{pillar.get('branch', '')}"
    return rows


def _time_layers(time_payload: dict[str, Any]) -> list[dict[str, str]]:
    layers = []
    for row in time_payload.get("layers", ()) or ():
        if not isinstance(row, dict):
            continue
        pillar = row.get("pillar", {})
        ten_god = row.get("ten_god", {})
        if not isinstance(pillar, dict):
            pillar = {}
        if not isinstance(ten_god, dict):
            ten_god = {}
        layers.append(
            {
                "layer_key": str(row.get("layer_key", "")),
                "pillar": f"{pillar.get('stem', '')}{pillar.get('branch', '')}",
                "ten_god": str(ten_god.get("label", "")),
            }
        )
    return layers


def _evidence_anchors(
    *,
    module_key: str,
    evidence_domains: tuple[str, ...],
    feature_ids: tuple[str, ...],
    time_sensitive: bool,
) -> list[dict[str, str]]:
    anchors: list[dict[str, str]] = []
    for domain in dict.fromkeys(evidence_domains):
        anchors.append(
            {
                "anchor_type": "domain",
                "anchor_key": str(domain),
                "module_key": module_key,
            }
        )
    for feature_id in dict.fromkeys(feature_ids):
        if len(anchors) >= 18:
            break
        anchors.append(
            {
                "anchor_type": "feature",
                "anchor_key": str(feature_id),
                "module_key": module_key,
            }
        )
    if time_sensitive:
        anchors.append(
            {
                "anchor_type": "time_context",
                "anchor_key": "luck+flow_year+flow_month",
                "module_key": module_key,
            }
        )
    return anchors[:20]
