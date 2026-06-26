from __future__ import annotations

from v20.decision.question_sources import question_source_manifest
from v20.graph.schema import QuestionSourcePath


QUESTION_SOURCE_GRAPH_VERSION = "v20.question_source_graph.v1"

PHASE_WEIGHT = {
    "runtime": 0.22,
    "decision": 0.2,
    "portrait": 0.16,
    "feature": 0.15,
    "time": 0.13,
    "seed": 0.1,
    "interaction": 0.24,
    "fallback": 0.02,
}

CONFLICT_TAGS = {
    "fallback": ("fallback_only_when_no_candidates",),
    "seed_registry": ("seed_must_not_override_chart_specific_candidates",),
}

LEARNING_TAGS = {
    "practitioner_refresh": ("practitioner_feedback", "session_rerank_only"),
    "latent_event": ("latent_event_feedback", "experience_signal_only"),
    "seed_registry": ("seed_fit_policy",),
    "mainline": ("mainline_arbitration_weight_policy",),
}

QUALITY_TAGS = {
    "mainline": ("policy_candidate_quality",),
    "seed_registry": ("seed_fit_quality",),
    "practitioner_refresh": ("interaction_quality",),
    "latent_event": ("interaction_quality",),
}

QUALITY_SIGNAL_KEYS = {
    "mainline": ("mainline_arbitration_weight_policy",),
    "seed_registry": ("question_focus_policy",),
    "practitioner_refresh": ("role_interaction_policy", "question_review_policy"),
    "latent_event": ("brain_memory_policy", "role_interaction_policy"),
}

CONFLICT_PENALTY = {
    "fallback_only_when_no_candidates": 0.18,
    "seed_must_not_override_chart_specific_candidates": 0.05,
}

LEARNING_BOOST = {
    "practitioner_feedback": 0.08,
    "latent_event_feedback": 0.06,
    "seed_fit_policy": 0.03,
    "mainline_arbitration_weight_policy": 0.04,
}

PHASE_PROPAGATION = {
    "runtime": ("decision", "feature"),
    "decision": ("portrait", "feature"),
    "portrait": ("decision",),
    "feature": ("decision",),
    "time": ("decision", "runtime"),
    "seed": ("decision",),
    "interaction": ("decision", "runtime"),
    "fallback": (),
}


def build_question_source_paths(
    *,
    quality_signal: dict[str, object] | None = None,
) -> tuple[QuestionSourcePath, ...]:
    manifest = tuple(question_source_manifest())
    phase_counts: dict[str, int] = {}
    for row in manifest:
        phase = str(row.get("phase", ""))
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
    paths = []
    for row in manifest:
        source_key = str(row.get("source_key", ""))
        phase = str(row.get("phase", ""))
        order = int(row.get("order", 0) or 0)
        base_weight = PHASE_WEIGHT.get(phase, 0.08)
        conflict_tags = CONFLICT_TAGS.get(source_key, ())
        learning_tags = LEARNING_TAGS.get(source_key, ())
        quality_tags = QUALITY_TAGS.get(source_key, ())
        propagated_weight = _propagated_weight(phase, phase_counts)
        conflict_penalty = _conflict_penalty(conflict_tags)
        learning_boost = _learning_boost(learning_tags)
        quality_boost = _quality_boost(source_key, quality_signal or {})
        order_penalty = min(0.18, order / 1000)
        score = round(
            max(0.01, base_weight + propagated_weight + learning_boost + quality_boost - conflict_penalty - order_penalty),
            3,
        )
        paths.append(
            QuestionSourcePath(
                path_id=f"question_source.{source_key}",
                source_key=source_key,
                phase=phase,
                order=order,
                base_weight=base_weight,
                score=score,
                propagated_weight=propagated_weight,
                conflict_penalty=conflict_penalty,
                learning_boost=learning_boost,
                quality_boost=quality_boost,
                conflict_tags=conflict_tags,
                learning_tags=learning_tags,
                quality_tags=quality_tags,
                arbitration_notes=_arbitration_notes(propagated_weight, conflict_penalty, learning_boost, quality_boost),
            )
        )
    return tuple(paths)


def arbitrate_question_source_paths(
    *,
    quality_signal: dict[str, object] | None = None,
    limit: int = 12,
) -> dict[str, object]:
    paths = build_question_source_paths(quality_signal=quality_signal)
    ordered = tuple(sorted(paths, key=lambda row: (row.score, -row.order, row.source_key), reverse=True))
    selected = tuple(row for row in ordered if row.source_key != "fallback")[:limit]
    fallback = tuple(row for row in paths if row.source_key == "fallback")
    return {
        "version": QUESTION_SOURCE_GRAPH_VERSION,
        "status": "ready",
        "algorithm": "phase_weighted_question_source_graph_phase1",
        "selected_paths": tuple(row.to_dict() for row in selected),
        "fallback_paths": tuple(row.to_dict() for row in fallback),
        "conflict_summary": _conflict_summary(paths),
        "learning_summary": _learning_summary(paths),
        "quality_summary": _quality_summary(paths),
        "path_count": len(paths),
        "runtime_mutation": False,
        "guardrails": (
            "QUESTION_SOURCE_GRAPH_RERANKS_ONLY",
            "NO_NEW_QUESTION_GENERATION",
            "FALLBACK_CANNOT_OVERRIDE_EVIDENCE_CANDIDATES",
            "LEARNING_TAGS_ARE_POLICY_INPUTS_ONLY",
            "QUALITY_SIGNALS_RERANK_ONLY",
        ),
    }


def _propagated_weight(phase: str, phase_counts: dict[str, int]) -> float:
    linked_count = sum(phase_counts.get(linked_phase, 0) for linked_phase in PHASE_PROPAGATION.get(phase, ()))
    return round(min(0.06, linked_count * 0.012), 3)


def _conflict_penalty(tags: tuple[str, ...]) -> float:
    return round(min(0.24, sum(CONFLICT_PENALTY.get(tag, 0.0) for tag in tags)), 3)


def _learning_boost(tags: tuple[str, ...]) -> float:
    return round(min(0.12, sum(LEARNING_BOOST.get(tag, 0.0) for tag in tags)), 3)


def _quality_boost(source_key: str, quality_signal: dict[str, object]) -> float:
    if not quality_signal:
        return 0.0
    source_scores = quality_signal.get("source_quality_scores", {})
    if isinstance(source_scores, dict) and source_key in source_scores:
        return _quality_score_to_boost(float(source_scores.get(source_key, 0.0) or 0.0))
    candidate_scores = []
    for candidate in quality_signal.get("candidates", ()):
        if not isinstance(candidate, dict):
            continue
        candidate_type = str(candidate.get("candidate_type", ""))
        if candidate_type not in QUALITY_SIGNAL_KEYS.get(source_key, ()):
            continue
        candidate_scores.append(float(candidate.get("quality_score", 0.0) or 0.0))
    if not candidate_scores:
        return 0.0
    return _quality_score_to_boost(max(candidate_scores))


def _quality_score_to_boost(score: float) -> float:
    return round(max(0.0, min(0.1, score * 0.1)), 3)


def _arbitration_notes(
    propagated_weight: float,
    conflict_penalty: float,
    learning_boost: float,
    quality_boost: float,
) -> tuple[str, ...]:
    notes = []
    if propagated_weight:
        notes.append(f"path_propagation:+{propagated_weight:.3f}")
    if learning_boost:
        notes.append(f"learning_boost:+{learning_boost:.3f}")
    if quality_boost:
        notes.append(f"quality_boost:+{quality_boost:.3f}")
    if conflict_penalty:
        notes.append(f"conflict_penalty:-{conflict_penalty:.3f}")
    return tuple(notes)


def _conflict_summary(paths: tuple[QuestionSourcePath, ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "source_key": row.source_key,
            "conflict_tags": row.conflict_tags,
            "conflict_penalty": row.conflict_penalty,
        }
        for row in paths
        if row.conflict_tags
    )


def _learning_summary(paths: tuple[QuestionSourcePath, ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "source_key": row.source_key,
            "learning_tags": row.learning_tags,
            "learning_boost": row.learning_boost,
        }
        for row in paths
        if row.learning_tags
    )


def _quality_summary(paths: tuple[QuestionSourcePath, ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "source_key": row.source_key,
            "quality_tags": row.quality_tags,
            "quality_boost": row.quality_boost,
        }
        for row in paths
        if row.quality_tags or row.quality_boost
    )
