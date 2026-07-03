from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from v30.brain.contracts import DecisionCandidate, DecisionConflict


DECISION_CONFLICT_RESOLVER_VERSION = "v30.decision_conflict_resolver.v1"


def resolve_decision_conflicts(
    candidates: list[DecisionCandidate],
    *,
    mode: str = "compatibility",
) -> dict[str, object]:
    conflicts: list[DecisionConflict] = []
    audits: list[dict[str, object]] = []
    by_domain: dict[str, list[DecisionCandidate]] = defaultdict(list)
    for candidate in candidates:
        by_domain[candidate.domain].append(candidate)

    for domain, rows in sorted(by_domain.items()):
        domain_rows = sorted(rows, key=lambda row: (-row.confidence, row.candidate_id))
        if not domain_rows:
            continue
        top = domain_rows[0]
        runner_up = domain_rows[1] if len(domain_rows) > 1 else None
        domain_conflicts = _domain_conflicts(domain, top, runner_up)
        conflicts.extend(domain_conflicts)
        audits.append(_domain_audit(domain, domain_rows, domain_conflicts))

    deduped_conflicts = _dedupe_conflicts(conflicts)
    return {
        "version": DECISION_CONFLICT_RESOLVER_VERSION,
        "mode": mode,
        "conflicts": [row.model_dump(mode="json") for row in deduped_conflicts],
        "summary": _summary(candidates, deduped_conflicts, by_domain, mode=mode),
        "audit": audits,
        "score_mutation_allowed": False,
        "verdict_mutation_allowed": False,
        "boundary": "conflict_resolver_explains_branch_uncertainty_without_mutating_candidate_scores_or_verdicts",
    }


def _domain_conflicts(
    domain: str,
    top: DecisionCandidate,
    runner_up: DecisionCandidate | None,
) -> list[DecisionConflict]:
    conflicts: list[DecisionConflict] = []
    if runner_up and abs(top.confidence - runner_up.confidence) <= 0.15:
        conflicts.append(
            DecisionConflict(
                conflict_id=f"conflict:{domain}:branch_probability",
                domain=domain,
                conflict_type="close_branch_probability",
                branch_a_id=top.candidate_id,
                branch_b_id=runner_up.candidate_id,
                evidence_for_a=top.evidence_refs[:4],
                evidence_for_b=runner_up.evidence_refs[:4],
                resolution_policy="keep_both_branches_until_decision_engine_or_practitioner_calibration_separates_weight",
                needed_question=_question_for_domain(domain),
            )
        )
    if top.requires_calibration:
        conflicts.append(
            DecisionConflict(
                conflict_id=f"conflict:{domain}:calibration_needed",
                domain=domain,
                conflict_type="requires_calibration",
                branch_a_id=top.candidate_id,
                evidence_for_a=top.evidence_refs[:4],
                resolution_policy="ask_only_if_value_of_information_exceeds_user_cost",
                needed_question=_question_for_domain(domain),
            )
        )
    counter_weight = _float(top.score_components.get("counter_evidence"), 0.0)
    if counter_weight >= 0.25:
        conflicts.append(
            DecisionConflict(
                conflict_id=f"conflict:{domain}:counter_evidence",
                domain=domain,
                conflict_type="counter_evidence_present",
                branch_a_id=top.candidate_id,
                evidence_for_a=top.evidence_refs[:4],
                resolution_policy="downgrade_assertion_level_unless_counter_evidence_is_resolved",
                needed_question=_question_for_domain(domain),
            )
        )
    return conflicts


def _summary(
    candidates: list[DecisionCandidate],
    conflicts: list[DecisionConflict],
    by_domain: dict[str, list[DecisionCandidate]],
    *,
    mode: str,
) -> dict[str, object]:
    conflict_types = Counter(row.conflict_type for row in conflicts)
    signal_bound_candidate_count = sum(1 for row in candidates if row.source_signal_ids)
    return {
        "version": "v30.decision_conflict_resolver_summary.v1",
        "resolver_version": DECISION_CONFLICT_RESOLVER_VERSION,
        "mode": mode,
        "candidate_count": len(candidates),
        "conflict_count": len(conflicts),
        "domain_count": len(by_domain),
        "conflict_type_counts": dict(sorted(conflict_types.items())),
        "signal_bound_candidate_count": signal_bound_candidate_count,
        "candidate_signal_count": sum(len(row.source_signal_ids) for row in candidates),
        "domains_with_conflicts": _sorted_unique([row.domain for row in conflicts]),
        "score_mutation_allowed": False,
        "score_mutated": False,
        "verdict_mutation_allowed": False,
        "verdict_mutated": False,
        "boundary": "conflict_resolver_summary_is_audit_and_training_signal_not_score_or_verdict_authority",
    }


def _domain_audit(
    domain: str,
    rows: list[DecisionCandidate],
    conflicts: list[DecisionConflict],
) -> dict[str, object]:
    top = rows[0]
    runner_up = rows[1] if len(rows) > 1 else None
    source_type_counts = Counter()
    source_module_counts = Counter()
    for candidate in rows:
        source_type_counts.update(_int_counts(candidate.signal_source_summary.get("source_type_counts")))
        source_module_counts.update(_int_counts(candidate.signal_source_summary.get("source_module_counts")))
    return {
        "version": "v30.decision_conflict_domain_audit.v1",
        "resolver_version": DECISION_CONFLICT_RESOLVER_VERSION,
        "domain": domain,
        "candidate_count": len(rows),
        "top_candidate_id": top.candidate_id,
        "top_claim_id": top.claim_id,
        "top_confidence": top.confidence,
        "runner_up_candidate_id": runner_up.candidate_id if runner_up else "",
        "runner_up_claim_id": runner_up.claim_id if runner_up else "",
        "runner_up_confidence": runner_up.confidence if runner_up else 0.0,
        "confidence_gap": round(abs(top.confidence - runner_up.confidence), 3) if runner_up else 1.0,
        "signal_bound_candidate_count": sum(1 for row in rows if row.source_signal_ids),
        "top_source_signal_count": len(top.source_signal_ids),
        "candidate_signal_count": sum(len(row.source_signal_ids) for row in rows),
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "source_module_counts": dict(sorted(source_module_counts.items())),
        "conflict_count": len(conflicts),
        "conflict_types": [row.conflict_type for row in conflicts],
        "resolution_policy": _policy_summary(conflicts),
        "needed_question": next((row.needed_question for row in conflicts if row.needed_question), ""),
        "score_mutation_allowed": False,
        "verdict_mutation_allowed": False,
        "boundary": "domain_conflict_audit_explains_why_branch_or_question_exists_without_changing_verdict",
    }


def _policy_summary(conflicts: list[DecisionConflict]) -> str:
    policies = _sorted_unique([row.resolution_policy for row in conflicts if row.resolution_policy])
    if not policies:
        return "no_conflict_no_extra_question"
    return ";".join(policies)


def _question_for_domain(domain: str) -> str:
    return {
        "career": "事业更像稳定承接职责，还是已经出现转型触发？",
        "wealth": "当前财务更需要主动争取、合作分配，还是保守积累？",
        "relationship": "关系里最反复的是表达冲突、距离边界，还是承诺节奏？",
        "health": "最近更明显的是压力消耗、作息紊乱，还是身体反馈？",
        "timing": "哪一年或哪段时间的变化最明显？",
        "structure": "当前更能印证身强、身弱，还是中和待复核？",
        "useful_god": "现实反馈更支持承接扶助，还是疏通泄化？",
        "hidden_factor": "是否有反复出现但命盘表层不容易直接解释的经历？",
    }.get(domain, "这个判断最需要补充哪个现实背景？")


def _dedupe_conflicts(conflicts: list[DecisionConflict]) -> list[DecisionConflict]:
    seen: set[str] = set()
    rows: list[DecisionConflict] = []
    for conflict in conflicts:
        if conflict.conflict_id in seen:
            continue
        seen.add(conflict.conflict_id)
        rows.append(conflict)
    return rows


def _int_counts(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    counts: dict[str, int] = {}
    for key, raw_count in value.items():
        if not str(key):
            continue
        counts[str(key)] = int(_float(raw_count, 0.0))
    return counts


def _sorted_unique(values: list[str] | object) -> list[str]:
    if isinstance(values, list):
        iterable = values
    else:
        iterable = list(values) if values is not None else []
    return sorted({str(row) for row in iterable if str(row)})


def _float(value: object, default: float) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default
