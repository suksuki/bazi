from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from typing import Any


SIGNAL_AWARE_CANDIDATE_BUILDER_VERSION = "v30.signal_aware_candidate_builder.v1"


def build_signal_candidate_support(
    *,
    claim_scores: list[dict[str, object]],
    claims: dict[str, dict[str, object]],
    signal_registry: Mapping[str, Any] | None = None,
    mode: str = "compatibility",
) -> dict[str, object]:
    registry = dict(signal_registry or {})
    signals = [
        dict(row)
        for row in registry.get("signals", [])
        if isinstance(row, Mapping)
    ]
    signals_by_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
    signals_by_evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for signal in signals:
        source_ref = str(signal.get("source_ref") or "")
        if source_ref:
            signals_by_ref[source_ref].append(signal)
        for ref in _string_list(signal.get("evidence_refs")):
            signals_by_evidence[ref].append(signal)
        branch_ref = str(signal.get("branch_group_id") or "")
        if branch_ref:
            signals_by_ref[branch_ref].append(signal)
    support_by_claim: dict[str, dict[str, object]] = {}
    bound_signals_by_id: dict[str, dict[str, Any]] = {}
    for score in claim_scores:
        claim_id = str(score.get("claim_id") or "")
        if not claim_id:
            continue
        claim = claims.get(claim_id, {})
        refs = _claim_refs(claim_id, claim, score)
        related = _dedupe_signals([
            *signals_by_ref.get(claim_id, []),
            *[
                signal
                for ref in refs
                for signal in signals_by_ref.get(ref, [])
            ],
            *[
                signal
                for ref in refs
                for signal in signals_by_evidence.get(ref, [])
            ],
        ])
        source_types = Counter(str(row.get("source_type") or "") for row in related if row.get("source_type"))
        source_modules = Counter(str(row.get("source_module") or "") for row in related if row.get("source_module"))
        for signal in related:
            signal_id = str(signal.get("signal_id") or "")
            if signal_id:
                bound_signals_by_id.setdefault(signal_id, signal)
        direct_claim_signal = next(
            (
                row for row in related
                if str(row.get("source_type") or "") == "diagnosis_claim"
                and str(row.get("source_ref") or "") == claim_id
            ),
            {},
        )
        support_by_claim[claim_id] = {
            "version": SIGNAL_AWARE_CANDIDATE_BUILDER_VERSION,
            "mode": mode,
            "claim_id": claim_id,
            "source_signal_ids": [str(row.get("signal_id")) for row in related if row.get("signal_id")],
            "direct_claim_signal_id": str(direct_claim_signal.get("signal_id") or ""),
            "signal_count": len(related),
            "source_type_counts": dict(sorted(source_types.items())),
            "source_module_counts": dict(sorted(source_modules.items())),
            "evidence_bound_signal_count": sum(1 for row in related if _string_list(row.get("evidence_refs"))),
            "score_mutation_allowed": False,
            "score_mutated": False,
            "candidate_confidence_source": "claim_scores",
            "boundary": "signal_candidate_support_is_compatibility_binding_not_score_mutation",
        }
    return {
        "version": SIGNAL_AWARE_CANDIDATE_BUILDER_VERSION,
        "mode": mode,
        "registry_id": str(registry.get("registry_id") or ""),
        "registry_signal_count": len(signals),
        "claim_support_count": len(support_by_claim),
        "claims_with_direct_signal_count": sum(1 for row in support_by_claim.values() if row.get("direct_claim_signal_id")),
        "claims_with_any_signal_count": sum(1 for row in support_by_claim.values() if int(row.get("signal_count") or 0) > 0),
        "source_type_counts": _source_counts(bound_signals_by_id.values(), "source_type"),
        "source_module_counts": _source_counts(bound_signals_by_id.values(), "source_module"),
        "score_mutation_allowed": False,
        "score_mutated": False,
        "support_by_claim_id": support_by_claim,
        "boundary": "candidate_builder_summary_binds_signals_without_changing_decision_result",
    }


def _claim_refs(claim_id: str, claim: dict[str, object], score: dict[str, object]) -> set[str]:
    refs = {claim_id}
    for key in ("evidence_ids", "rule_ids", "path_ids", "portrait_ids"):
        refs.update(_string_list(claim.get(key)))
    graph = score.get("graph_metrics")
    if isinstance(graph, Mapping):
        refs.update(_string_list(graph.get("claim_refs")))
    return {ref for ref in refs if ref}


def _dedupe_signals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        signal_id = str(row.get("signal_id") or "")
        if not signal_id or signal_id in seen:
            continue
        seen.add(signal_id)
        out.append(row)
    return out


def _source_counts(rows, key: str) -> dict[str, int]:
    counts = Counter(str(row.get(key) or "") for row in rows if row.get(key))
    return dict(sorted(counts.items()))


def _string_list(value: object) -> list[str]:
    if isinstance(value, list | tuple | set):
        return [str(row) for row in value if str(row)]
    return []
