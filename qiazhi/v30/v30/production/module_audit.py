from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from v30.production.contracts import (
    ModuleAuditEntry,
    ModuleOutputStatus,
    ProductionAuditSummary,
    SignalRegistry,
    SignalUsageAudit,
    SourceModule,
)


def build_usage_audit(
    registry: SignalRegistry,
    *,
    decision_result: Mapping[str, Any] | None = None,
    final_synthesis: Mapping[str, Any] | None = None,
    reading_surface: Mapping[str, Any] | None = None,
    thinking_projection: Mapping[str, Any] | None = None,
    training_artifacts: Sequence[Mapping[str, Any]] | None = None,
) -> list[SignalUsageAudit]:
    decision_payload = _dict(decision_result)
    verdict_payload = _list(decision_payload.get("verdicts"))
    if not verdict_payload and isinstance(decision_payload.get("decision_verdicts"), list):
        verdict_payload = _list(decision_payload.get("decision_verdicts"))
    final_payload = _dict(final_synthesis)
    surface_payload = _dict(reading_surface)
    thinking_payload = _dict(thinking_projection)
    training_payload = list(training_artifacts or [])

    decision_refs = _all_refs(decision_payload)
    verdict_refs = _all_refs(verdict_payload)
    advice_refs = _all_refs(_advice_payloads(decision_payload, final_payload))
    ui_refs = _all_refs(surface_payload) | _all_refs(thinking_payload)
    training_refs = _all_refs(training_payload)

    rows: list[SignalUsageAudit] = []
    for signal in registry.signals:
        refs = _signal_refs(signal.model_dump(mode="json"))
        consumed_by_decision = bool(refs & decision_refs)
        consumed_by_verdict = bool(refs & verdict_refs)
        consumed_by_advice = bool(refs & advice_refs)
        consumed_by_ui = bool(refs & ui_refs)
        consumed_by_training = bool(refs & training_refs)
        consumers = []
        if consumed_by_decision:
            consumers.append("decision_result")
        if consumed_by_verdict:
            consumers.append("decision_verdict")
        if consumed_by_advice:
            consumers.append("advice_or_final_synthesis")
        if consumed_by_ui:
            consumers.append("reading_surface_or_thinking_projection")
        if consumed_by_training:
            consumers.append("training_artifacts")
        output_bound = consumed_by_verdict or consumed_by_advice or consumed_by_ui
        status = _signal_status(
            output_bound=output_bound,
            consumed_by_decision=consumed_by_decision,
            consumed_by_training=consumed_by_training,
            source_module=signal.source_module,
        )
        rows.append(
            SignalUsageAudit(
                signal_id=signal.signal_id,
                consumed_by_decision=consumed_by_decision,
                consumed_by_verdict=consumed_by_verdict,
                consumed_by_advice=consumed_by_advice,
                consumed_by_ui=consumed_by_ui,
                consumed_by_training=consumed_by_training,
                indirect_consumers=consumers,
                output_bound=output_bound,
                status=status,
                notes=_usage_notes(signal.source_module.value, consumers, output_bound),
            )
        )
    return rows


def build_module_audit(
    registry: SignalRegistry,
    usage_audit: Sequence[SignalUsageAudit],
) -> list[ModuleAuditEntry]:
    usage_by_signal = {row.signal_id: row for row in usage_audit}
    signals_by_module: dict[SourceModule, list[dict[str, Any]]] = defaultdict(list)
    for signal in registry.signals:
        signals_by_module[signal.source_module].append(signal.model_dump(mode="json"))
    entries: list[ModuleAuditEntry] = []
    for module_name, signals in sorted(signals_by_module.items(), key=lambda item: item[0].value):
        usages = [usage_by_signal.get(str(signal.get("signal_id"))) for signal in signals]
        source_types = sorted(
            {str(signal.get("source_type")) for signal in signals if str(signal.get("source_type"))}
        )
        missing_fields = sorted(
            {
                field
                for issue in registry.validation_issues
                if _issue_signal_id(issue) in {str(signal.get("signal_id")) for signal in signals}
                for field in _issue_missing_fields(issue)
            }
        )
        output_bound_count = sum(1 for usage in usages if usage is not None and usage.output_bound)
        consumed_by_decision_count = sum(1 for usage in usages if usage is not None and usage.consumed_by_decision)
        consumed_by_verdict_count = sum(1 for usage in usages if usage is not None and usage.consumed_by_verdict)
        consumed_by_advice_count = sum(1 for usage in usages if usage is not None and usage.consumed_by_advice)
        consumed_by_ui_count = sum(1 for usage in usages if usage is not None and usage.consumed_by_ui)
        consumed_by_training_count = sum(1 for usage in usages if usage is not None and usage.consumed_by_training)
        status = _module_status(
            module_name,
            signal_count=len(signals),
            output_bound_count=output_bound_count,
            decision_count=consumed_by_decision_count,
            training_count=consumed_by_training_count,
        )
        entries.append(
            ModuleAuditEntry(
                module_name=module_name,
                source_types=source_types,  # type: ignore[arg-type]
                produced_count=len(signals),
                signal_count=len(signals),
                consumed_by_decision_count=consumed_by_decision_count,
                consumed_by_verdict_count=consumed_by_verdict_count,
                consumed_by_advice_count=consumed_by_advice_count,
                consumed_by_ui_count=consumed_by_ui_count,
                consumed_by_training_count=consumed_by_training_count,
                output_bound_count=output_bound_count,
                status=status,
                example_signal_ids=[str(signal.get("signal_id")) for signal in signals[:5]],
                missing_fields=missing_fields,
                recommended_action=_recommended_action(module_name, status, output_bound_count, missing_fields),
            )
        )
    return entries


def summarize_production_audit(
    *,
    reading_id: str,
    registry: SignalRegistry,
    usage_audit: Sequence[SignalUsageAudit],
    module_audit: Sequence[ModuleAuditEntry],
) -> ProductionAuditSummary:
    status_counts = Counter(row.status.value for row in module_audit)
    top_output_bound_modules = [
        row.module_name.value
        for row in sorted(module_audit, key=lambda item: (-item.output_bound_count, item.module_name.value))
        if row.output_bound_count
    ][:8]
    return ProductionAuditSummary(
        reading_id=reading_id,
        signal_count=len(registry.signals),
        module_count=len(module_audit),
        output_bound_signal_count=sum(1 for row in usage_audit if row.output_bound),
        decision_consumed_signal_count=sum(1 for row in usage_audit if row.consumed_by_decision),
        verdict_consumed_signal_count=sum(1 for row in usage_audit if row.consumed_by_verdict),
        advice_consumed_signal_count=sum(1 for row in usage_audit if row.consumed_by_advice),
        ui_consumed_signal_count=sum(1 for row in usage_audit if row.consumed_by_ui),
        training_consumed_signal_count=sum(1 for row in usage_audit if row.consumed_by_training),
        status_counts=dict(sorted(status_counts.items())),
        validation_issue_count=len(registry.validation_issues),
        top_output_bound_modules=top_output_bound_modules,
        candidate_module_count=status_counts.get(ModuleOutputStatus.CANDIDATE.value, 0),
        orphan_module_count=status_counts.get(ModuleOutputStatus.ORPHAN.value, 0),
    )


def _signal_status(
    *,
    output_bound: bool,
    consumed_by_decision: bool,
    consumed_by_training: bool,
    source_module: SourceModule,
) -> ModuleOutputStatus:
    if output_bound:
        return ModuleOutputStatus.OUTPUT_BOUND
    if consumed_by_decision:
        return ModuleOutputStatus.RUNTIME_USED
    if consumed_by_training:
        return ModuleOutputStatus.TRAIN_ONLY
    if source_module == SourceModule.STAGE_POINT:
        return ModuleOutputStatus.DEBUG_ONLY
    return ModuleOutputStatus.CANDIDATE


def _module_status(
    module_name: SourceModule,
    *,
    signal_count: int,
    output_bound_count: int,
    decision_count: int,
    training_count: int,
) -> ModuleOutputStatus:
    if signal_count <= 0:
        return ModuleOutputStatus.ORPHAN
    if output_bound_count > 0:
        return ModuleOutputStatus.OUTPUT_BOUND
    if decision_count > 0:
        return ModuleOutputStatus.RUNTIME_USED
    if training_count > 0:
        return ModuleOutputStatus.TRAIN_ONLY
    if module_name == SourceModule.STAGE_POINT:
        return ModuleOutputStatus.DEBUG_ONLY
    return ModuleOutputStatus.CANDIDATE


def _recommended_action(
    module_name: SourceModule,
    status: ModuleOutputStatus,
    output_bound_count: int,
    missing_fields: list[str],
) -> str:
    if missing_fields:
        return "补齐 signal source_ref / claim_key / evidence_refs / boundary 后再扩大消费范围。"
    if module_name == SourceModule.STAGE_POINT:
        return "保持 presentation/sidebar 审计，不作为 Decision Engine 输入。"
    if status == ModuleOutputStatus.OUTPUT_BOUND:
        return "已进入产出链，下一阶段可评估是否接入 signal-based candidate builder。"
    if status == ModuleOutputStatus.RUNTIME_USED:
        return "已被运行链路消费，但未直接绑定用户产出；下一阶段检查是否应进入 Verdict 或 AdvicePlan。"
    if status == ModuleOutputStatus.CANDIDATE and output_bound_count == 0:
        return "有候选产出但未绑定用户结果；保留为 DCA-15 candidate builder 候选来源。"
    if status == ModuleOutputStatus.ORPHAN:
        return "未发现下游消费；需要接入、降级或删除。"
    return "保留审计观察。"


def _usage_notes(module_name: str, consumers: list[str], output_bound: bool) -> list[str]:
    notes: list[str] = []
    if not consumers:
        notes.append("no_downstream_reference_detected")
    if output_bound:
        notes.append("output_bound_by_existing_runtime_payload")
    if module_name == SourceModule.STAGE_POINT.value:
        notes.append("presentation_only_do_not_feed_decision_v1")
    return notes


def _advice_payloads(decision_result: dict[str, Any], final_synthesis: dict[str, Any]) -> list[object]:
    payloads: list[object] = []
    payloads.append(final_synthesis.get("advice", ""))
    payloads.append(final_synthesis.get("synthesis_blueprint", {}))
    payloads.extend(_list(final_synthesis.get("decision_verdicts")))
    payloads.extend(_list(decision_result.get("verdicts")))
    return payloads


def _signal_refs(signal: dict[str, Any]) -> set[str]:
    refs = {
        str(signal.get("signal_id") or ""),
        str(signal.get("source_ref") or ""),
        str(signal.get("claim_key") or ""),
        str(signal.get("branch_group_id") or ""),
        str(signal.get("conflict_group_id") or ""),
    }
    refs.update(str(row) for row in signal.get("evidence_refs", []) if row)
    refs.update(str(row) for row in signal.get("counter_evidence_refs", []) if row)
    return {ref for ref in refs if ref}


def _all_refs(value: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        for key, row in value.items():
            if isinstance(key, str) and _reference_like(key):
                refs.add(key)
            refs.update(_all_refs(row))
        return refs
    if isinstance(value, list | tuple | set):
        for row in value:
            refs.update(_all_refs(row))
        return refs
    if isinstance(value, str):
        if _reference_like(value):
            refs.add(value)
        return refs
    return refs


def _reference_like(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if len(text) > 180:
        return False
    tokens = (
        "claim",
        "feature",
        "path",
        "portrait",
        "rule",
        "evidence",
        "decision",
        "verdict",
        "signal",
        "rbd.",
        "v30.",
        ":",
    )
    return any(token in text for token in tokens)


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[dict[str, Any]]:
    return [dict(row) for row in value if isinstance(row, Mapping)] if isinstance(value, list) else []


def _issue_signal_id(issue: object) -> str:
    return str(issue.get("signal_id") or "") if isinstance(issue, Mapping) else ""


def _issue_missing_fields(issue: object) -> list[str]:
    if not isinstance(issue, Mapping):
        return []
    value = issue.get("missing_fields")
    return [str(row) for row in value if row] if isinstance(value, list) else []
