from __future__ import annotations

from v30.contracts import FeatureEvidence, MainlineState, StructureState
from v30.knowledge import KnowledgeRulePortraitSignal


MAINLINE_SELECTOR_VERSION = "v30.mainline_selector.v1"


def select_mainline_state(
    structure: StructureState,
    evidence: list[FeatureEvidence],
    knowledge_rule_portrait_signals: list[KnowledgeRulePortraitSignal] | None = None,
) -> MainlineState:
    signals = knowledge_rule_portrait_signals or []
    domains = {row.domain for row in evidence}
    time_missing = any(row.domain == "time_context" and row.kind == "missing_requirement" for row in evidence)
    useful_gate = any(row.domain == "useful_god" and row.kind == "evidence_gate" for row in evidence)
    strength_pattern = any(row.domain == "structure_pattern" for row in evidence)
    domain_rule = any(row.domain == "domain_rule" for row in evidence)
    rule_evidence = [row for row in evidence if row.domain == "rule"]
    title = _title(structure, domains, time_missing, useful_gate, strength_pattern)
    quality_gate = "needs_time_context" if time_missing else "evidence_bound"
    return MainlineState(
        mainline_id=f"{structure.structure_id}:mainline",
        domain="core_structure",
        title=title,
        state="evidence_bound_review",
        score=round(structure.confidence, 3),
        primary_structure_id=structure.structure_id,
        evidence_ids=structure.evidence_ids,
        supporting_mainlines=_supporting(domains, signals, rule_evidence),
        rejected_mainlines=[],
        why_selected=_why_selected(structure, time_missing, useful_gate, strength_pattern, domain_rule, signals, rule_evidence),
        quality_gate=quality_gate,
    )


def _title(
    structure: StructureState,
    domains: set[str],
    time_missing: bool,
    useful_gate: bool,
    strength_pattern: bool,
) -> str:
    if time_missing:
        return "Current chart structure is evidence-bound; timing remains unconfirmed"
    if strength_pattern:
        return "Current chart supports strength and pattern candidate review"
    if "branch_relation" in domains:
        return "Current chart structure has dynamic branch relation evidence"
    if useful_gate:
        return "Current chart supports useful-god candidate review, not a fixed verdict"
    return "Current chart structure is evidence-bound"


def _supporting(
    domains: set[str],
    signals: list[KnowledgeRulePortraitSignal],
    rule_evidence: list[FeatureEvidence],
) -> list[str]:
    rows: list[str] = []
    if "ten_god" in domains:
        rows.append("ten_god_context")
    if "element" in domains:
        rows.append("element_distribution")
    if "branch_relation" in domains:
        rows.append("branch_relation_review")
    if "useful_god" in domains:
        rows.append("useful_god_candidate_gate")
    if "structure_pattern" in domains:
        rows.append("strength_pattern_candidate_review")
    if "domain_rule" in domains:
        rows.append("domain_rule_candidate_review")
    rows.extend(f"{signal.signal_type}_signal:{signal.source_id}" for signal in signals)
    rows.extend(f"rule_evidence:{row.kind}" for row in rule_evidence)
    return rows


def _why_selected(
    structure: StructureState,
    time_missing: bool,
    useful_gate: bool,
    strength_pattern: bool,
    domain_rule: bool,
    signals: list[KnowledgeRulePortraitSignal],
    rule_evidence: list[FeatureEvidence],
) -> str:
    reasons = [
        "Selected because the structure state is bound to the current ChartContext and compiled FeatureEvidence.",
        f"Structure state: {structure.state}.",
    ]
    if time_missing:
        reasons.append("Explicit luck or flow time layer is missing, so timing claims remain blocked.")
    if useful_gate:
        reasons.append("Useful-god remains a candidate path review, not a fixed favorable/unfavorable verdict.")
    if strength_pattern:
        reasons.append("Strength, 格局, and useful-god family signals remain candidate reviews rather than final verdicts.")
    if domain_rule:
        reasons.append("Wealth, career, relationship, and health domain rules remain review candidates, not life outcome verdicts.")
    if any(signal.signal_type == "rule" for signal in signals):
        reasons.append("Rule signals are bound and keep boundary conditions active.")
    if rule_evidence:
        reasons.append(f"Rule evidence is executed and bound: {len(rule_evidence)}.")
    countered_count = _rule_state_count(rule_evidence, "countered")
    if countered_count:
        reasons.append(f"Counter-evidence is present and blocks overconfident rule use: {countered_count}.")
    if any(signal.signal_type == "portrait" for signal in signals):
        reasons.append("Portrait signals remain hypotheses until user feedback or validation strengthens them.")
    mechanism_count = int(structure.path_scores.get("mechanism_path_count", 0.0))
    if mechanism_count:
        reasons.append(f"Mechanism paths are scored: {mechanism_count}.")
    dynamic_path_count = int(structure.path_scores.get("dynamic_path_count", 0.0))
    if dynamic_path_count:
        reasons.append(f"Dynamic graph v2 paths are extracted: {dynamic_path_count}.")
    resolution_count = int(structure.path_scores.get("dynamic_path_resolution_family_count", 0.0))
    if resolution_count:
        reasons.append(f"Path-resolution families are available for candidate review: {resolution_count}.")
    domain_path_count = int(
        structure.path_scores.get("dynamic_wealth_path_count", 0.0)
        + structure.path_scores.get("dynamic_career_path_count", 0.0)
        + structure.path_scores.get("dynamic_relationship_path_count", 0.0)
        + structure.path_scores.get("dynamic_health_review_path_count", 0.0)
    )
    if domain_path_count:
        reasons.append(f"Domain rule paths are available for bounded review: {domain_path_count}.")
    return " ".join(reasons)


def _rule_state_count(rule_evidence: list[FeatureEvidence], state: str) -> int:
    return sum(1 for row in rule_evidence if f"rule_decision_state:{state}" in row.supports)
