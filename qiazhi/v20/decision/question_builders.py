from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.decision.question_config import QUESTION_KEY_BY_DOMAIN, QUESTION_STRATEGY
from v20.decision.question_titles import portrait_tag_question_title, runtime_decision_question_title


MakeQuestion = Callable[
    [str, str, str, float, FeatureLayer, dict[str, object] | None, str],
    QuestionCandidate,
]
AlignQuestion = Callable[[QuestionCandidate], QuestionCandidate | None]
ExplicitTitle = Callable[[str], str]


def runtime_decision_fusion_questions(
    runtime_decision_fusion: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    make_question: MakeQuestion,
    align_question: AlignQuestion,
    explicit_title: ExplicitTitle,
    max_per_domain: int = 2,
) -> list[QuestionCandidate]:
    if not runtime_decision_fusion:
        return []
    decisions = tuple(row for row in runtime_decision_fusion.get("decisions", ()) if isinstance(row, dict))
    by_domain: dict[str, list[dict[str, object]]] = defaultdict(list)
    for decision in decisions:
        by_domain[str(decision.get("domain", ""))].append(decision)

    rows: list[QuestionCandidate] = []
    for domain, domain_rows in by_domain.items():
        if not domain or domain not in QUESTION_KEY_BY_DOMAIN:
            continue
        ordered = sorted(
            (
                (
                    round(float(row.get("confidence", 0.0) or 0.0), 3),
                    float(row.get("score", 0.0) or 0.0),
                    int(row.get("score", 0.0) or 0) + int(_state_priority(str(row.get("structural_state", "")))),
                    row,
                )
                for row in domain_rows
            ),
            key=lambda item: (item[0], item[1], item[2]),
            reverse=True,
        )
        key = QUESTION_KEY_BY_DOMAIN[domain]
        for _, _, _, row in ordered[:max_per_domain]:
            decision = _runtime_decision_to_candidate_source(row)
            title = runtime_decision_question_title(
                domain,
                row,
                question_key=key,
                explicit_title=explicit_title,
            )
            score = round(float(row.get("confidence", 0.0) or 0.0) + 0.08, 3)
            candidate = make_question(
                key,
                title,
                domain,
                min(0.99, score),
                feature_layer,
                decision,
                QUESTION_STRATEGY["runtime_fusion"],
            )
            aligned = align_question(candidate)
            if aligned:
                rows.append(aligned)
    return rows


def portrait_tag_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    make_question: MakeQuestion,
    align_question: AlignQuestion,
    max_total: int = 10,
) -> list[QuestionCandidate]:
    rows: list[QuestionCandidate] = []
    projection = decision_report.get("portrait_projection", {})
    axes = tuple(projection.get("axes", ()) if isinstance(projection, dict) else ())
    for axis in axes:
        if not isinstance(axis, dict) or len(rows) >= max_total:
            continue
        domain = str(axis.get("domain", ""))
        key = QUESTION_KEY_BY_DOMAIN.get(domain)
        if not key:
            continue
        title = portrait_tag_question_title(axis)
        source = {
            "decision_key": str(axis.get("axis_id", "")),
            "rule_key": f"rule.{domain}.portrait_tag",
            "status": str(axis.get("axis_state", "")) or ("confirmed" if str(axis.get("attention_level", "")) == "high" else "candidate"),
            "label": str(axis.get("profile_tag", "")) or str(axis.get("label", "")),
            "score": float(axis.get("peak_confidence", 0.0) or 0.0),
            "anchor": str(axis.get("structural_anchor", "")),
            "feature_ids": tuple(str(row) for row in axis.get("feature_ids", ()) if str(row)),
        }
        candidate = make_question(
            key,
            title,
            domain,
            round(min(0.82, max(0.38, float(axis.get("peak_confidence", 0.0) or 0.0) - 0.16)), 3),
            feature_layer,
            source,
            QUESTION_STRATEGY["portrait_axis"],
        )
        aligned = align_question(candidate)
        if aligned is not None:
            rows.append(aligned)
    return rows


def _state_priority(state: str) -> int:
    if state in {"confirmed", "chain_review", "candidate", "weak_candidate"}:
        return 2
    if state in {"mixed", "volatile", "requires_review", "countered", "blocked"}:
        return 1
    return 0


def _runtime_decision_to_candidate_source(decision: dict[str, object]) -> dict[str, object]:
    return {
        "decision_key": str(decision.get("decision_key", "")),
        "rule_key": str(decision.get("source_rule_key", "")),
        "status": str(decision.get("structural_state", "")),
        "label": str(decision.get("user_facing_decision", "")),
        "score": float(decision.get("confidence", 0.0) or 0.0),
        "feature_ids": tuple(str(row) for row in decision.get("feature_ids", ()) if str(row)),
        "support": tuple(str(row) for row in decision.get("evidence_summary", ()) if str(row)),
        "counter_evidence": tuple(str(row) for row in decision.get("counter_evidence", ()) if str(row)),
    }
