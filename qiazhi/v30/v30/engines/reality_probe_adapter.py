from __future__ import annotations

from typing import Any

from v30.contracts import CoreRuntimeResult
from v30.engines.contracts import EngineKey, EngineRunRequest, EngineRunResult, EngineRunStatus


REALITY_PROBE_ENGINE_ADAPTER_VERSION = "v30.reality_probe_engine_adapter.v1"


def run_reality_probe_engine(request: EngineRunRequest, *, runtime: CoreRuntimeResult | None = None) -> EngineRunResult:
    context = request.engine_context
    probe_candidates = _list(context.get("probe_candidates"))
    diagnostics: dict[str, Any] = {
        "source": "engine_context",
        "answer_signal_count": len(_list(context.get("answer_signals"))),
    }
    if runtime is not None:
        policy_effect = runtime.question_plan.policy_effect
        probe_candidates = [
            *probe_candidates,
            *_list(runtime.question_plan.hidden_factor_probes),
            *_dialogue_probe_candidates(_dict(policy_effect.get("question_dialogue_graph"))),
        ]
        diagnostics.update(
            {
                "source": "runtime_policy_effect",
                "question_outcome_count": len(_list(policy_effect.get("question_outcomes"))),
                "known_user_signal_count": len(_list(policy_effect.get("known_user_signals"))),
            }
        )
    unique_candidates = _dedupe_probe_candidates(probe_candidates)
    return EngineRunResult(
        result_id=f"{request.reading_id}:engine:reality_probe:{request.mode.value}",
        reading_id=request.reading_id,
        engine=EngineKey.REALITY_PROBE,
        mode=request.mode,
        status=EngineRunStatus.READY if unique_candidates else EngineRunStatus.PARTIAL,
        engine_version=REALITY_PROBE_ENGINE_ADAPTER_VERSION,
        standard_version="v30.reality_probe_calibration_engine.v1",
        facts=[],
        features=[],
        signals=[],
        probe_candidates=unique_candidates,
        diagnostics={
            **diagnostics,
            "probe_candidate_count": len(unique_candidates),
            "reality_probe_affects_manifestation_not_chart_facts": True,
        },
        warnings=[] if unique_candidates else ["reality_probe_has_no_probe_candidates_yet"],
        decision_weight=0.4,
        boundary="reality_probe_engine_calibrates_manifestation_and_hidden_attributes_without_mutating_chart_facts",
    )


def _dialogue_probe_candidates(graph: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = _list(graph.get("nodes"))
    candidates = []
    for node in nodes:
        question = str(node.get("question") or node.get("label") or "").strip()
        if not question:
            continue
        candidates.append(
            {
                "probe_id": str(node.get("node_id") or node.get("question_id") or question[:40]),
                "question": question,
                "source": "question_dialogue_graph",
                "boundary": "dialogue_graph_probe_candidate_not_chart_fact",
            }
        )
    return candidates[:8]


def _dedupe_probe_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        key = str(row.get("probe_id") or row.get("question") or row.get("question_id") or row)[:120]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []
