from __future__ import annotations

from v20.graph.question_source_graph import arbitrate_question_source_paths
from v20.interaction.questions import QuestionCandidate


QUESTION_SOURCE_RANKING_REPORT_VERSION = "v20.question_source_ranking_report.v1"

STRATEGY_SOURCE_MAP = {
    "runtime_fusion": "runtime_fusion",
    "mainline": "mainline",
    "mainline_candidate": "mainline",
    "mainline_focus": "mainline",
    "mainline_focus_selected": "mainline",
    "portrait_axis": "portrait_axis",
    "decision_hit": "decision_hit",
    "feature_hook": "feature_hook",
    "feature_context": "feature_hook",
    "secondary": "decision_loop",
    "knowledge_output": "decision_loop",
    "time_context": "time_context",
    "seed_registry": "seed_registry",
    "practitioner_refresh": "practitioner_refresh",
    "latent_event": "latent_event",
    "fallback": "fallback",
}


def build_question_source_ranking_report(
    questions: tuple[QuestionCandidate, ...],
    *,
    quality_signal: dict[str, object] | None = None,
) -> dict[str, object]:
    graph = arbitrate_question_source_paths(quality_signal=quality_signal or {})
    path_by_source = {
        str(row.get("source_key", "")): row
        for row in (
            *tuple(graph.get("selected_paths", ())),
            *tuple(graph.get("fallback_paths", ())),
        )
        if isinstance(row, dict)
    }
    rows = []
    missing_sources = []
    for rank, question in enumerate(questions, start=1):
        source_key = _source_key_for_question(question)
        path = path_by_source.get(source_key, {})
        if not path:
            missing_sources.append(source_key)
        rows.append(
            {
                "rank": rank,
                "question_id": question.question_id or question.question_key,
                "question_key": question.question_key,
                "domain": question.domain,
                "question_strategy": question.question_strategy,
                "source_key": source_key,
                "source_graph_score": float(path.get("score", 0.0) or 0.0) if isinstance(path, dict) else 0.0,
                "question_score": float(question.score or 0.0),
                "arbitration_notes": tuple(path.get("arbitration_notes", ())) if isinstance(path, dict) else (),
            }
        )
    return {
        "version": QUESTION_SOURCE_RANKING_REPORT_VERSION,
        "status": "ready" if rows else "empty",
        "source": "Questions+QuestionSourceGraph",
        "question_count": len(rows),
        "source_path_count": int(graph.get("path_count", 0) or 0),
        "rows": tuple(rows),
        "missing_source_keys": tuple(sorted(set(row for row in missing_sources if row))),
        "question_source_graph": {
            "version": graph.get("version", ""),
            "status": graph.get("status", ""),
            "selected_path_count": len(graph.get("selected_paths", ())),
            "fallback_path_count": len(graph.get("fallback_paths", ())),
            "conflict_summary": graph.get("conflict_summary", ()),
            "learning_summary": graph.get("learning_summary", ()),
            "quality_summary": graph.get("quality_summary", ()),
        },
        "runtime_mutation": False,
        "guardrails": (
            "QUESTION_SOURCE_REPORT_IS_READ_ONLY",
            "QUESTION_SOURCE_GRAPH_RERANK_EXPLANATION_ONLY",
            "NO_NEW_QUESTION_GENERATION",
            "NO_QUESTION_ORDER_MUTATION",
        ),
    }


def _source_key_for_question(question: QuestionCandidate) -> str:
    strategy = question.question_strategy or ""
    if strategy in STRATEGY_SOURCE_MAP:
        return STRATEGY_SOURCE_MAP[strategy]
    if strategy.startswith("seed_"):
        return "seed_registry"
    if strategy.startswith("mainline"):
        return "mainline"
    if strategy.startswith("feature_"):
        return "feature_hook"
    return "decision_loop"
