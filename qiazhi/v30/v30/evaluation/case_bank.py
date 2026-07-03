from __future__ import annotations

from v30.evaluation.contracts import (
    EvaluationCaseSpec,
    ExpectedAdvice,
    ExpectedProbe,
    ExpectedSignal,
    ExpectedVerdict,
    ForbiddenAssertion,
)
from v30.training.mingli_phase2 import load_phase2_ziwei_golden_cases
from v30.training.mingli_training import MingliGoldenCase, load_phase1_mingli_golden_cases


def evaluation_case_from_mingli_case(case: MingliGoldenCase) -> EvaluationCaseSpec:
    domains = case.expected_verdict_domains or case.target_domains or ["overview"]
    expected_signals = [
        ExpectedSignal(
            source_type="ziwei_signal",
            source_module="ziwei_domain_lens",
            domain=domain,
            claim_key="",
            min_confidence=0.0,
            required=True,
        )
        for domain in domains
        if case.ziwei_matched_rule_ids
    ]
    expected_probes = [
        ExpectedProbe(
            domain=domain,
            target=f"{domain}_manifestation",
            hidden_attribute_key=f"{domain}_reality_probe",
            expected_keywords=list(case.expected_advice_directions[:3]),
            required=bool(case.reality_probe_answers),
        )
        for domain in case.target_domains
        if case.reality_probe_answers or "reality_probe" in {engine.value for engine in case.required_engines}
    ]
    return EvaluationCaseSpec(
        case_id=f"eval:{case.case_id}",
        case_type="golden",
        linked_case_id=case.case_id,
        user_question=case.user_question,
        topic=domains[0] if domains else "overview",
        time_scope="current_year" if "今年" in case.user_question else "natal",
        known_reality={
            "reality_probe_answers": case.reality_probe_answers,
            "required_engines": [engine.value for engine in case.required_engines],
        },
        expert_notes=list(case.notes),
        expected_signals=expected_signals,
        expected_verdicts=[
            ExpectedVerdict(
                domain=domain,
                expected_keywords=list(case.expected_advice_directions),
                allowed_assertions=list(case.expected_advice_directions),
                forbidden_assertions=list(case.forbidden_assertions),
                requires_conflict_handling=domain in {"wealth", "relationship", "timing", "useful_god"},
            )
            for domain in domains
        ],
        expected_advice=[
            ExpectedAdvice(
                domain=domain,
                source_verdict_domain=domain,
                must_include_any=list(case.expected_advice_directions),
                requires_action=True,
                requires_avoid=domain in {"wealth", "relationship", "health"},
                requires_condition=domain in {"wealth", "timing", "career"},
            )
            for domain in domains
        ],
        expected_probes=expected_probes,
        allowed_assertions=list(case.expected_advice_directions),
        forbidden_assertions=[
            ForbiddenAssertion(text=text, severity="critical" if any(token in text for token in ("必然", "一定", "保证", "绝对")) else "high")
            for text in case.forbidden_assertions
        ],
        evaluation_tags=sorted({*case.target_domains, *case.expected_verdict_domains, "mingli", "phase1" if "phase1" in case.case_id else "phase2"}),
    )


def load_phase1_evaluation_cases() -> list[EvaluationCaseSpec]:
    return [evaluation_case_from_mingli_case(case) for case in load_phase1_mingli_golden_cases()]


def load_phase2_evaluation_cases() -> list[EvaluationCaseSpec]:
    return [evaluation_case_from_mingli_case(case) for case in load_phase2_ziwei_golden_cases()]
