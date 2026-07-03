from __future__ import annotations

from typing import Any

from v30.engines.contracts import EngineKey, EngineRunRequest, EngineRunResult, EngineRunStatus
from v30.ziwei.adapters import ziwei_signal_from_rule, ziwei_signal_to_bazi_signal
from v30.ziwei.domain_rules import load_ziwei_v1_domain_rules
from v30.ziwei.probe_mapping import mapping_for_claim_key, probe_mappings_by_domain
from v30.ziwei.standards import ZIWEI_DECISION_WEIGHT_V1, ZIWEI_SYSTEM_STANDARD_VERSION


ZIWEI_ENGINE_ADAPTER_VERSION = "v30.ziwei_engine_adapter.v1"


def run_ziwei_engine(request: EngineRunRequest) -> EngineRunResult:
    context = request.engine_context
    matched_rule_ids = _string_list(context.get("ziwei_matched_rule_ids"))
    domain = _ziwei_domain_from_request(request)
    rules = load_ziwei_v1_domain_rules()
    selected_rules = [
        rule for rule in rules
        if rule.rule_id in set(matched_rule_ids)
    ]
    ziwei_signals = [
        ziwei_signal_from_rule(
            reading_id=request.reading_id,
            rule=rule,
            source_ref=str(context.get("ziwei_chart_id") or rule.rule_id),
        )
        for rule in selected_rules
    ]
    bazi_signals = [ziwei_signal_to_bazi_signal(signal) for signal in ziwei_signals]
    probe_candidates = []
    for rule in selected_rules:
        mapping = mapping_for_claim_key(rule.claim_key)
        if mapping is not None:
            probe_candidates.append(mapping.model_dump(mode="json"))
    if not selected_rules and domain:
        probe_candidates = [
            row.model_dump(mode="json")
            for row in probe_mappings_by_domain(domain)
        ][:3]
    warnings = []
    status = EngineRunStatus.READY
    if not selected_rules:
        status = EngineRunStatus.PARTIAL
        warnings.append("ziwei_fact_layer_not_connected_no_matched_rule_signal_emitted")
    return EngineRunResult(
        result_id=f"{request.reading_id}:engine:ziwei:{request.mode.value}",
        reading_id=request.reading_id,
        engine=EngineKey.ZIWEI,
        mode=request.mode,
        status=status,
        engine_version=ZIWEI_ENGINE_ADAPTER_VERSION,
        standard_version=ZIWEI_SYSTEM_STANDARD_VERSION,
        facts=[],
        features=[],
        signals=bazi_signals,
        probe_candidates=probe_candidates,
        diagnostics={
            "matched_rule_count": len(selected_rules),
            "candidate_probe_count": len(probe_candidates),
            "decision_weight": ZIWEI_DECISION_WEIGHT_V1,
            "requires_fact_layer_before_runtime_use": True,
        },
        warnings=warnings,
        decision_weight=ZIWEI_DECISION_WEIGHT_V1,
        boundary="ziwei_engine_adapter_emits_domain_lens_sidecar_signals_only_when_rules_are_explicitly_matched",
    )


def _ziwei_domain_from_request(request: EngineRunRequest) -> str:
    aliases = {
        "wealth": "wealth",
        "career": "career",
        "relationship": "relationship",
        "health": "health_pressure",
        "mobility": "mobility",
        "location": "mobility",
        "property": "property",
        "timing": "mobility",
        "overview": "",
        "unknown": "",
    }
    return aliases.get(request.domain.value, aliases.get(request.topic.value, ""))


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(row).strip() for row in value if str(row).strip()]
    if isinstance(value, tuple | set):
        return [str(row).strip() for row in value if str(row).strip()]
    return []
