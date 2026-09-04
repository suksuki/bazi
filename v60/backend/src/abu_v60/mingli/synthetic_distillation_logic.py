from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from abu_v60.mingli.agent_contracts import MingliAgentCasePacket
from abu_v60.mingli.agent_method_cards import method_card_catalog
from abu_v60.mingli.agent_method_distillation import (
    bound_method_context,
    distilled_check_guidance,
)
from abu_v60.mingli.agent_root_gate import packet_root_candidate_assessments
from abu_v60.mingli.synthetic_coordinate_discipline import (
    month_command_coordinate_violations,
)
from abu_v60.mingli.synthetic_distillation_contracts import (
    MINGLI_SYNTHETIC_DISTILLATION_EVALUATOR_VERSION,
    DistillationCandidateAssembly,
    DistillationCandidateOutput,
    DistillationCertaintyAssembly,
    DistillationCertaintyOutput,
    DistillationEvaluationCheck,
    DistillationRegimeOutput,
    SyntheticDistillationEvaluation,
)
from abu_v60.mingli.synthetic_experiment_gold import synthetic_experiment_dev_gold

_RULING_VALUES = {"SUPPORTS", "CONDITIONAL", "OPPOSES", "UNRESOLVED"}
_ADJUDICATION_RANK = {
    "BROKEN": 0,
    "UNRESOLVED": 1,
    "CONDITIONAL": 2,
    "SUPPORTED": 3,
}


def distillation_regime_context(packet: MingliAgentCasePacket) -> dict[str, Any]:
    """Project only the facts and method needed for weak-vs-follow judgment."""

    prompt_view = packet.model_prompt_view()
    professional = prompt_view["professional_adjudication"]
    return {
        "task": "REGIME_ONLY",
        "chart": prompt_view["chart"],
        "day_master_support": prompt_view["day_master_support"],
        "natal_relations": prompt_view["natal_relations"],
        "source_contexts": prompt_view["source_contexts"],
        "seasonal_context": professional["seasonal_context"],
        "support_order": professional["support_order"],
        "regime_method": professional["day_master_regime_method"],
        "allowed_output_scaffold": professional["output_field_contract"]["regime_decision"],
        "natal_evidence": _natal_evidence(packet),
    }


def distillation_candidate_context(
    packet: MingliAgentCasePacket,
    *,
    regime_output: DistillationRegimeOutput,
) -> dict[str, Any]:
    """Project candidate cards without life domains, timing, or Gold."""

    cards = method_card_catalog(packet.mechanism_observations)
    occurrences = _ten_god_occurrences(packet)
    observations = {item.evidence_id: item for item in packet.mechanism_observations}
    candidate_cards = []
    for candidate_ref in _candidate_universe(packet):
        card = cards[candidate_ref]
        observation = observations[candidate_ref]
        required = tuple(str(item) for item in card["required_checks"])
        candidate_cards.append(
            {
                "method_card_ref": candidate_ref,
                "label": observation.label,
                "structural_statement": observation.structural_statement,
                "role_summary": observation.role_summary,
                "observed_blocker_codes": observation.blocker_codes,
                "required_checks_in_exact_order": required,
                "blocking_checks": card["blocking_checks"],
                "conditioning_checks": card["conditioning_checks"],
                "check_guidance": distilled_check_guidance(
                    observation.pattern_ref,
                    required,
                    compact=True,
                ),
                "bound_context": bound_method_context(
                    pattern_ref=observation.pattern_ref,
                    ten_god_occurrences=occurrences,
                    root_candidates=packet.day_master_support.same_element_hidden_support,
                    visible_peers=packet.day_master_support.visible_peer_support,
                    hidden_resources=packet.day_master_support.resource_support,
                ),
            }
        )
    return {
        "task": "COMPARE_TWO_CANDIDATES_ONLY",
        "chart": {
            "day_master_stem": packet.day_master_stem,
            "month_command_branch": packet.month_command_branch,
            "pillars": tuple(
                {
                    "slot": item.slot,
                    "pillar": item.pillar,
                    "visible_ten_god": item.visible_ten_god,
                    "hidden": tuple(zip(item.hidden_stems, item.hidden_ten_gods, strict=True)),
                    "evidence_id": item.evidence_id,
                }
                for item in packet.pillars
            ),
        },
        "locally_locked_regime_pass": regime_output.model_dump(mode="json"),
        "candidate_universe": _candidate_universe(packet),
        "candidate_partition_rule": (
            "主解释与备选必须是两个不同候选；排除集合必须精确等于全集减去这两个候选。"
        ),
        "candidate_cards": tuple(candidate_cards),
        "natal_evidence": _natal_evidence(packet),
    }


def assemble_candidate_output(
    packet: MingliAgentCasePacket,
    output: DistillationCandidateOutput,
) -> DistillationCandidateAssembly:
    """Recompute candidate closure and aggregates without trusting model summaries."""

    universe = _candidate_universe(packet)
    if len(universe) < 2:
        raise ValueError("mingli_distillation_two_candidates_required")
    issues: set[str] = set()
    raw_pair = (
        output.primary_method_card_ref,
        output.alternative_method_card_ref,
    )
    if len(set(raw_pair)) == 2 and set(raw_pair).issubset(universe):
        primary_ref, alternative_ref = raw_pair
    else:
        primary_ref, alternative_ref = universe[:2]
        issues.add("CANDIDATE_ROLE_BINDING_REPAIRED")

    assessment_by_ref = {item.method_card_ref: item for item in output.assessments}
    cards = method_card_catalog(packet.mechanism_observations)
    natal_evidence_ids = _natal_evidence_ids(packet)
    aggregates: dict[str, str] = {}
    for role, candidate_ref in (
        ("PRIMARY", primary_ref),
        ("ALTERNATIVE", alternative_ref),
    ):
        assessment = assessment_by_ref.get(candidate_ref)
        card = cards[candidate_ref]
        required = tuple(str(item) for item in card["required_checks"])
        if assessment is None:
            issues.add(f"{role}_ASSESSMENT_MISSING")
            aggregates[candidate_ref] = "UNRESOLVED"
            continue
        actual_codes = tuple(item.check_code for item in assessment.rulings)
        if actual_codes != required:
            issues.add(f"{role}_RULING_IDENTITY_INVALID")
        evidence_valid = all(
            set(item.evidence_ids).issubset(natal_evidence_ids) for item in assessment.rulings
        )
        if not evidence_valid:
            issues.add(f"{role}_EVIDENCE_INVALID")
        if actual_codes != required or not evidence_valid:
            aggregates[candidate_ref] = "UNRESOLVED"
            continue
        values = {item.check_code: item.ruling for item in assessment.rulings}
        aggregates[candidate_ref] = _aggregate_rulings(
            values,
            blocking_checks=tuple(str(item) for item in card["blocking_checks"]),
            required_checks=required,
        )

    if (
        _ADJUDICATION_RANK[aggregates[primary_ref]]
        < _ADJUDICATION_RANK[aggregates[alternative_ref]]
    ):
        primary_ref, alternative_ref = alternative_ref, primary_ref
        issues.add("PRIMARY_SELECTION_REPAIRED")
    expected_excluded = tuple(
        item for item in universe if item not in {primary_ref, alternative_ref}
    )
    if output.excluded_method_card_refs != expected_excluded:
        issues.add("CANDIDATE_PARTITION_REPAIRED")

    return DistillationCandidateAssembly(
        universe=universe,
        primary_method_card_ref=primary_ref,
        alternative_method_card_ref=alternative_ref,
        excluded_method_card_refs=expected_excluded,
        primary_adjudication=aggregates[primary_ref],
        alternative_adjudication=aggregates[alternative_ref],
        issue_keys=tuple(sorted(issues)),
    )


def distillation_certainty_context(
    *,
    assembly: DistillationCandidateAssembly,
) -> dict[str, Any]:
    """Ask only for evidence-strength labels after local aggregate calculation."""

    return {
        "task": "CERTAINTY_MAPPING_ONLY",
        "locally_compiled_roles": {
            "primary": {
                "method_card_ref": assembly.primary_method_card_ref,
                "adjudication": assembly.primary_adjudication,
            },
            "alternative": {
                "method_card_ref": assembly.alternative_method_card_ref,
                "adjudication": assembly.alternative_adjudication,
            },
        },
        "mapping_table": {
            "primary": {
                "SUPPORTED": "SUPPORTED",
                "CONDITIONAL": "WORKS_IF",
                "BROKEN": "BLOCKED",
                "UNRESOLVED": "COMPETING",
            },
            "alternative": {
                "SUPPORTED": "SUPPORTED",
                "CONDITIONAL": "PARTIAL",
                "BROKEN": "BLOCKED",
                "UNRESOLVED": "COMPETING",
            },
            "work_path_closure_from_primary": {
                "SUPPORTED": "CLOSED",
                "CONDITIONAL": "CONDITIONAL",
                "BROKEN": "BROKEN",
                "UNRESOLVED": "UNCERTAIN",
            },
        },
        "instruction": "只按表映射，不重新推盘，不提高结论强度。",
    }


def assemble_certainty(
    assembly: DistillationCandidateAssembly,
) -> DistillationCertaintyAssembly:
    primary = assembly.primary_adjudication
    alternative = assembly.alternative_adjudication
    return DistillationCertaintyAssembly(
        primary_judgment={
            "SUPPORTED": "SUPPORTED",
            "CONDITIONAL": "WORKS_IF",
            "BROKEN": "BLOCKED",
            "UNRESOLVED": "COMPETING",
        }[primary],
        alternative_judgment={
            "SUPPORTED": "SUPPORTED",
            "CONDITIONAL": "PARTIAL",
            "BROKEN": "BLOCKED",
            "UNRESOLVED": "COMPETING",
        }[alternative],
        work_path_closure={
            "SUPPORTED": "CLOSED",
            "CONDITIONAL": "CONDITIONAL",
            "BROKEN": "BROKEN",
            "UNRESOLVED": "UNCERTAIN",
        }[primary],
        confidence_ceiling=("MEDIUM" if primary == "SUPPORTED" else "LOW"),
    )


def evaluate_distillation_outputs(
    *,
    experiment_ref: str,
    variant: str,
    packet: MingliAgentCasePacket,
    regime_output: DistillationRegimeOutput,
    candidate_output: DistillationCandidateOutput,
    certainty_output: DistillationCertaintyOutput,
    raw_outputs: Sequence[Mapping[str, Any]],
) -> SyntheticDistillationEvaluation:
    candidate_assembly = assemble_candidate_output(packet, candidate_output)
    certainty_assembly = assemble_certainty(candidate_assembly)
    checks: list[DistillationEvaluationCheck] = []

    def add(check_ref: str, passed: bool, statement: str, details: dict[str, Any]) -> None:
        checks.append(
            DistillationEvaluationCheck(
                check_ref=check_ref,
                status="PASS" if passed else "FAIL",
                statement=statement,
                details=details,
            )
        )

    packet_regime = _packet_regime_coherence(packet, regime_output)
    add(
        "REGIME_PACKET_COHERENT",
        bool(packet_regime["valid"]),
        "判型必须遵守根候选、最低根门、印比竞争和日主状态的本地事实边界。",
        packet_regime,
    )
    gold_regime = _gold_regime_coherence(
        experiment_ref=experiment_ref,
        variant=variant,
        regime_output=regime_output,
    )
    add(
        "REGIME_DEV_GOLD_BOUND",
        bool(gold_regime["valid"]),
        "DEV 判型必须落在冻结 Gold 允许的结果集合，Gold 从不进入模型上下文。",
        gold_regime,
    )
    add(
        "CANDIDATE_LOCAL_RECOMPILATION",
        not candidate_assembly.issue_keys,
        "候选主次、方法检查、证据与排除集合必须由本地系统重算后保持闭合。",
        candidate_assembly.model_dump(mode="json"),
    )
    certainty_actual = {
        "primary_judgment": certainty_output.primary_judgment,
        "alternative_judgment": certainty_output.alternative_judgment,
        "work_path_closure": certainty_output.work_path_closure,
        "confidence": certainty_output.confidence,
    }
    certainty_expected = certainty_assembly.model_dump(mode="json")
    certainty_valid = bool(
        certainty_output.primary_judgment == certainty_assembly.primary_judgment
        and certainty_output.alternative_judgment == certainty_assembly.alternative_judgment
        and certainty_output.work_path_closure == certainty_assembly.work_path_closure
        and (
            certainty_assembly.confidence_ceiling == "MEDIUM"
            or certainty_output.confidence == "LOW"
        )
    )
    add(
        "CERTAINTY_LOCALLY_COHERENT",
        certainty_valid,
        "最终判断强度与路径闭合度不得高于本地重算的方法裁决。",
        {"expected": certainty_expected, "actual": certainty_actual},
    )
    coordinate_violations = tuple(
        violation
        for raw in raw_outputs
        for violation in month_command_coordinate_violations(raw, packet=packet)
    )
    add(
        "MONTH_COMMAND_COORDINATES_SEPARATED",
        not coordinate_violations,
        "三段原文都不得把月干十神直接写成月令。",
        {"violations": coordinate_violations},
    )
    issue_keys = tuple(sorted(item.check_ref for item in checks if item.status == "FAIL"))
    return SyntheticDistillationEvaluation(
        evaluator_version=MINGLI_SYNTHETIC_DISTILLATION_EVALUATOR_VERSION,
        checks=tuple(checks),
        candidate_assembly=candidate_assembly,
        certainty_assembly=certainty_assembly,
        outcome="DEV_PASS" if not issue_keys else "DEV_REVIEW_REQUIRED",
        model_independence="PASS" if not issue_keys else "FAIL",
        issue_keys=issue_keys,
        qualification_effect="DEV_TRAINING_ONLY_NOT_QUALIFICATION",
    )


def _candidate_universe(packet: MingliAgentCasePacket) -> tuple[str, ...]:
    return tuple(item.evidence_id for item in packet.mechanism_observations)


def _aggregate_rulings(
    values: Mapping[str, str],
    *,
    blocking_checks: tuple[str, ...],
    required_checks: tuple[str, ...],
) -> str:
    if any(values.get(item) not in _RULING_VALUES for item in required_checks):
        return "UNRESOLVED"
    blocking = tuple(values[item] for item in blocking_checks)
    if "OPPOSES" in blocking:
        return "BROKEN"
    if "UNRESOLVED" in blocking:
        return "UNRESOLVED"
    all_values = tuple(values[item] for item in required_checks)
    if any(item in {"UNRESOLVED", "CONDITIONAL", "OPPOSES"} for item in all_values):
        return "CONDITIONAL"
    return "SUPPORTED"


def _packet_regime_coherence(
    packet: MingliAgentCasePacket,
    output: DistillationRegimeOutput,
) -> dict[str, Any]:
    regime = output.regime_decision
    support = packet.day_master_support
    assessments = packet_root_candidate_assessments(packet)
    candidates = tuple(support.same_element_hidden_support)
    minimum_roots = tuple(
        str(item["coordinate"])
        for item in assessments
        if item["minimum_anti_follow_gate"] == "PRESENT"
    )
    issues: list[str] = []
    if minimum_roots:
        if (
            regime.effective_root_status != "PRESENT"
            or regime.effective_root_coordinates != minimum_roots
        ):
            issues.append("MINIMUM_ROOT_NOT_APPLIED")
    elif not candidates:
        if regime.effective_root_status != "ABSENT" or regime.effective_root_coordinates:
            issues.append("ROOT_ABSENCE_NOT_PRESERVED")
    elif regime.effective_root_status == "PRESENT":
        if not regime.effective_root_coordinates or not set(
            regime.effective_root_coordinates
        ).issubset(candidates):
            issues.append("ROOT_COORDINATES_OUTSIDE_CANDIDATES")
    elif regime.effective_root_status != "UNRESOLVED":
        issues.append("ROOT_CANDIDATE_DISCARDED")

    if not support.visible_peer_support and regime.rooted_visible_support_status != "ABSENT":
        issues.append("VISIBLE_SUPPORT_INVENTED")
    expected_competition: set[str] = set()
    if support.resource_support:
        expected_competition.add("HIDDEN_RESOURCE")
    if support.visible_peer_support:
        expected_competition.add("VISIBLE_PEER")
    if not expected_competition.issubset(regime.competition_kinds):
        issues.append("COMPETITION_OMITTED")
    if not set(regime.evidence_ids).issubset(_natal_evidence_ids(packet)):
        issues.append("REGIME_EVIDENCE_OUTSIDE_PACKET")
    if support.evidence_id not in regime.evidence_ids:
        issues.append("REGIME_SUPPORT_EVIDENCE_MISSING")
    allowed_states = {
        "ORDINARY_WEAK": {"WEAK"},
        "FOLLOW_TREND": {"FOLLOWING_TENDENCY"},
        "FALSE_FOLLOW_COMPETITION": {"WEAK", "UNCERTAIN"},
        "UNRESOLVED": {"WEAK", "UNCERTAIN"},
        "NON_WEAK_OUTSIDE_SCOPE": {
            "STRONG",
            "BALANCED",
            "SPECIALIZED_TENDENCY",
        },
    }[regime.classification]
    if output.day_master_state not in allowed_states:
        issues.append("DAY_MASTER_STATE_REGIME_MISMATCH")
    return {
        "valid": not issues,
        "issues": tuple(issues),
        "minimum_roots": minimum_roots,
        "candidate_roots": candidates,
        "actual": output.model_dump(mode="json"),
    }


def _gold_regime_coherence(
    *,
    experiment_ref: str,
    variant: str,
    regime_output: DistillationRegimeOutput,
) -> dict[str, Any]:
    gold, gold_hash = synthetic_experiment_dev_gold(experiment_ref)
    prefix = f"{variant}_"
    required_keys = (
        f"{prefix}required_effective_root_status",
        f"{prefix}required_effective_root_coordinates",
        f"{prefix}required_rooted_visible_support_status",
        f"{prefix}required_competition_kinds",
        f"{prefix}allowed_regime_classifications",
    )
    missing = tuple(item for item in required_keys if item not in gold)
    regime = regime_output.regime_decision
    valid = not missing and bool(
        regime.effective_root_status == gold.get(required_keys[0])
        and regime.effective_root_coordinates == gold.get(required_keys[1])
        and regime.rooted_visible_support_status == gold.get(required_keys[2])
        and regime.competition_kinds == gold.get(required_keys[3])
        and regime.classification in gold.get(required_keys[4], ())
    )
    return {
        "valid": valid,
        "gold_hash": gold_hash,
        "missing_contract_keys": missing,
        "allowed_classifications": gold.get(required_keys[4], ()),
        "actual": regime.model_dump(mode="json"),
    }


def _natal_evidence(packet: MingliAgentCasePacket) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "evidence_id": item.evidence_id,
            "kind": item.kind,
            "statement": item.statement,
        }
        for item in packet.evidence_catalog
        if item.kind != "TIMING"
    )


def _natal_evidence_ids(packet: MingliAgentCasePacket) -> set[str]:
    return {item.evidence_id for item in packet.evidence_catalog if item.kind != "TIMING"}


def _ten_god_occurrences(packet: MingliAgentCasePacket) -> dict[str, tuple[str, ...]]:
    values: dict[str, list[str]] = {}
    for pillar in packet.pillars:
        values.setdefault(pillar.visible_ten_god, []).append(f"{pillar.slot}干{pillar.stem}")
        for stem, ten_god in zip(
            pillar.hidden_stems,
            pillar.hidden_ten_gods,
            strict=True,
        ):
            values.setdefault(ten_god, []).append(f"{pillar.slot}支藏{stem}")
    return {key: tuple(value) for key, value in values.items()}
