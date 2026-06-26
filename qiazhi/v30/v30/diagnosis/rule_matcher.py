from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.contracts import FeatureEvidence, StructureState
from v30.diagnosis.contracts import DiagnosisDomain, MatchedRule
from v30.knowledge import match_krp_library_units


RULE_MATCHER_VERSION = "v30.real_bazi_diagnosis.rule_matcher.v1"

DOMAIN_MAP = {
    "chart": "overview",
    "element": "structure",
    "foundation": "overview",
    "ten_god": "structure",
    "branch_relation": "structure",
    "time_context": "timing",
    "structure_pattern": "structure",
    "structure_dynamic": "structure",
    "useful_god": "useful_god",
    "domain_rule": "overview",
    "wealth": "wealth",
    "career": "career",
    "relationship": "relationship",
    "romance": "relationship",
    "health": "health",
    "hidden_factor": "hidden_factor",
    "rule_counterevidence": "overview",
}

DOMAIN_PATH_SCORE_KEYS = {
    "wealth": "dynamic_wealth_path_count",
    "career": "dynamic_career_path_count",
    "relationship": "dynamic_relationship_path_count",
    "health": "dynamic_health_review_path_count",
    "useful_god": "dynamic_useful_god_candidate_path_count",
    "structure": "dynamic_path_count",
    "timing": "dynamic_path_count",
    "overview": "dynamic_path_count",
    "hidden_factor": "dynamic_path_count",
}

FIXED_EVENT_BLOCKERS = {
    "timing_claim",
    "special_year_claim",
    "flow_month_claim_without_context",
}
MUTATION_BLOCKERS = {
    "chart_fact_mutation",
    "llm_chart_fact_generation",
    "training_chart_fact_generation",
}
OUTCOME_BLOCKERS = {
    "fixed_bazi_verdict",
    "fixed_strength_verdict",
    "fixed_geju_verdict",
    "fixed_useful_god_verdict",
    "fixed_wealth_outcome_claim",
    "fixed_career_outcome_claim",
    "fixed_relationship_outcome_claim",
    "fixed_health_outcome_claim",
    "private_relationship_fact_claim",
    "medical_diagnosis",
    "disease_prediction",
}


def match_real_bazi_rules(
    *,
    feature_evidence: Sequence[FeatureEvidence],
    structure_state: StructureState | None = None,
    model_signal_summary: Mapping[str, Any] | None = None,
    krp_units: Sequence[Mapping[str, Any]] | None = None,
    question_policy: Mapping[str, Any] | None = None,
    limit: int | None = None,
) -> list[MatchedRule]:
    units = list(krp_units) if krp_units is not None else match_krp_library_units(
        list(feature_evidence),
        dict(question_policy or {}),
    )
    supports_by_id = _evidence_support_index(feature_evidence)
    matches: list[MatchedRule] = []
    for unit in units:
        if str(unit.get("unit_type") or "") != "rule":
            continue
        matched = _string_list(unit.get("matched_supports"))
        if not matched:
            continue
        domain_targets = _domain_targets(str(unit.get("domain") or "overview"))
        evidence_ids = _evidence_ids_for_unit(matched, supports_by_id)
        if not evidence_ids:
            continue
        blocked_claims = _blocked_claims(unit)
        score = _match_strength(
            unit=unit,
            matched=matched,
            domain_targets=domain_targets,
            structure_state=structure_state,
            model_signal_summary=model_signal_summary or {},
        )
        matches.append(
            MatchedRule(
                rule_match_id=f"rbd.match:{unit.get('unit_id')}",
                rule_id=str(unit.get("unit_id") or ""),
                source_family_ids=_string_list(unit.get("source_family_ids")),
                domain_targets=domain_targets,
                match_strength=score,
                required_context_hit=[row for row in matched if not row.startswith("weakens:")],
                counter_context_hit=_counter_context(unit, matched),
                missing_context=_missing_context(unit, matched),
                claim_templates=_claim_templates(unit),
                blocked_claims=blocked_claims,
                evidence_ids=evidence_ids,
                path_ids=_path_ids(domain_targets, structure_state),
                can_generate_claim=_can_generate_claim(blocked_claims, score),
                requires_user_calibration=_requires_user_calibration(unit, matched),
            )
        )
    matches.sort(key=lambda row: (-row.match_strength, row.rule_id))
    if limit is not None:
        return matches[:limit]
    return matches


def summarize_rule_matches(matches: Sequence[MatchedRule]) -> dict[str, Any]:
    by_domain: dict[str, int] = {}
    blocked: dict[str, int] = {}
    for row in matches:
        for domain in row.domain_targets:
            by_domain[domain] = by_domain.get(domain, 0) + 1
        for blocker in row.blocked_claims:
            blocked[blocker] = blocked.get(blocker, 0) + 1
    return {
        "version": RULE_MATCHER_VERSION,
        "match_count": len(matches),
        "claim_ready_count": sum(1 for row in matches if row.can_generate_claim),
        "requires_calibration_count": sum(1 for row in matches if row.requires_user_calibration),
        "domain_counts": dict(sorted(by_domain.items())),
        "blocked_claim_counts": dict(sorted(blocked.items())),
        "top_rule_ids": [row.rule_id for row in list(matches)[:8]],
        "boundary": "rule_match_summary_is_diagnostic_not_public_verdict",
    }


def _evidence_support_index(evidence: Sequence[FeatureEvidence]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for row in evidence:
        tokens = [*row.supports, *[f"weakens:{item}" for item in row.weakens]]
        for token in tokens:
            index.setdefault(str(token), []).append(row.evidence_id)
    return index


def _evidence_ids_for_unit(matched: Sequence[str], index: Mapping[str, list[str]]) -> list[str]:
    ids: set[str] = set()
    for token in matched:
        ids.update(index.get(str(token), []))
    return sorted(ids)


def _domain_targets(domain: str) -> list[DiagnosisDomain]:
    mapped = DOMAIN_MAP.get(domain, "overview")
    if domain == "domain_rule":
        return ["wealth", "career", "relationship", "health"]
    return [mapped]  # type: ignore[list-item]


def _blocked_claims(unit: Mapping[str, Any]) -> list[str]:
    blocked = set(_string_list(unit.get("condition_weakens")))
    blocked.update(_string_list(unit.get("matched_weakens")))
    boundary = str(unit.get("boundary") or "")
    if "not_event" in boundary or "event" in boundary:
        blocked.update(FIXED_EVENT_BLOCKERS)
    if "not_medical" in boundary or "medical" in boundary:
        blocked.update({"medical_diagnosis", "disease_prediction"})
    if "not_outcome" in boundary or "outcome" in boundary:
        blocked.update(OUTCOME_BLOCKERS & {
            "fixed_wealth_outcome_claim",
            "fixed_career_outcome_claim",
            "fixed_relationship_outcome_claim",
            "fixed_health_outcome_claim",
        })
    blocked.update(item for item in _string_list(unit.get("score_reasons")) if item.startswith("blocked:"))
    return sorted(blocked)


def _counter_context(unit: Mapping[str, Any], matched: Sequence[str]) -> list[str]:
    rows = set(_string_list(unit.get("matched_weakens")))
    rows.update(token.removeprefix("weakens:") for token in matched if token.startswith("weakens:"))
    return sorted(rows)


def _missing_context(unit: Mapping[str, Any], matched: Sequence[str]) -> list[str]:
    required = set(_string_list(unit.get("required_context")))
    if not required:
        return []
    matched_set = set(matched)
    return sorted(item for item in required if item not in matched_set)


def _claim_templates(unit: Mapping[str, Any]) -> list[str]:
    guidance = _string_list(unit.get("answer_guidance"))
    if guidance:
        return guidance
    title = str(unit.get("title") or "")
    return [title] if title else []


def _path_ids(domain_targets: Sequence[DiagnosisDomain], structure_state: StructureState | None) -> list[str]:
    if structure_state is None:
        return []
    rows: list[str] = []
    for node in structure_state.graph_nodes:
        if not isinstance(node, dict) or node.get("kind") != "dynamic_path":
            continue
        node_id = str(node.get("node_id") or "")
        if not node_id:
            continue
        domain_tags = _path_domain_tags(node)
        if not domain_tags or set(domain_targets) & domain_tags:
            rows.append(node_id)
    return rows[:8]


def _path_domain_tags(node: Mapping[str, Any]) -> set[str]:
    out: set[str] = set()
    families = node.get("family_chain", [])
    families = families if isinstance(families, list) else []
    chain = {str(item) for item in families}
    if "wealth" in chain:
        out.add("wealth")
    if "authority" in chain:
        out.add("career")
        out.add("relationship")
    if node.get("conflict_families"):
        out.add("relationship")
        out.add("health")
    if node.get("resolution_families"):
        out.add("structure")
        out.add("useful_god")
    return out


def _match_strength(
    *,
    unit: Mapping[str, Any],
    matched: Sequence[str],
    domain_targets: Sequence[DiagnosisDomain],
    structure_state: StructureState | None,
    model_signal_summary: Mapping[str, Any],
) -> float:
    base = float(unit.get("score", 0.0) or 0.0)
    required_context_score = min(0.16, len([row for row in matched if not row.startswith("weakens:")]) * 0.025)
    counter_penalty = min(0.22, len(_counter_context(unit, matched)) * 0.055)
    missing_penalty = min(0.18, len(_missing_context(unit, matched)) * 0.045)
    path_support = _path_support(domain_targets, structure_state)
    model_support = _model_signal_support(model_signal_summary)
    score = base + required_context_score + path_support + model_support - counter_penalty - missing_penalty
    return round(max(0.01, min(1.0, score)), 3)


def _path_support(domain_targets: Sequence[DiagnosisDomain], structure_state: StructureState | None) -> float:
    if structure_state is None:
        return 0.0
    scores = structure_state.path_scores or {}
    support = 0.0
    for domain in domain_targets:
        key = DOMAIN_PATH_SCORE_KEYS.get(domain, "dynamic_path_count")
        count = float(scores.get(key, 0.0) or 0.0)
        if count:
            support += min(0.08, count * 0.008)
    if float(scores.get("dynamic_path_resolution_family_count", 0.0) or 0.0):
        support += 0.025
    return round(min(0.14, support), 3)


def _model_signal_support(model_signal_summary: Mapping[str, Any]) -> float:
    if not model_signal_summary:
        return 0.0
    if model_signal_summary.get("status") == "ready" or model_signal_summary.get("summary_id"):
        return 0.03
    return 0.0


def _can_generate_claim(blocked_claims: Sequence[str], score: float) -> bool:
    if score < 0.35:
        return False
    if set(blocked_claims) & MUTATION_BLOCKERS:
        return False
    return True


def _requires_user_calibration(unit: Mapping[str, Any], matched: Sequence[str]) -> bool:
    domain = str(unit.get("domain") or "")
    boundary = str(unit.get("boundary") or "")
    if domain in {"hidden_factor", "time_context"}:
        return True
    if "requires_dialogue" in boundary or "requires_user" in boundary:
        return True
    if any(token in {"rule_time_boundary", "hidden_stem_context"} for token in matched):
        return True
    return bool(_missing_context(unit, matched))


def _string_list(value: Any) -> list[str]:
    return [str(row) for row in value] if isinstance(value, list) else []
