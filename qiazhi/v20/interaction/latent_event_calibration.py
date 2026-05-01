from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

from v20.learning.latent_factor_calibration import latent_factor_calibration_manifest
from v20.learning.ledger import LedgerEntry
from v20.learning.proposal import LearningProposal
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env

YEAR_OPTIONS = ("unknown", "birth_to_12", "13_to_18", "19_to_24", "25_to_30", "31_to_36", "37_to_42", "43_to_48", "49_to_54", "55_plus")
INTENSITY_OPTIONS = ("none", "mild", "clear", "strong")
CONFIDENCE_OPTIONS = ("low", "medium", "high")
RESULT_OPTIONS = {
    "wealth_change": ("no_clear_change", "income_up", "income_down", "resource_gain", "resource_pressure", "mixed"),
    "career_transition": ("no_clear_change", "role_up", "role_down", "platform_change", "responsibility_change", "mixed"),
    "relationship_shift": ("no_clear_change", "relationship_stabilized", "relationship_changed", "relationship_pressure", "family_focus_shift", "mixed"),
    "relocation_environment": ("no_clear_change", "city_change", "work_environment_change", "home_environment_change", "travel_or_mobility_up", "mixed"),
    "stress_recovery": ("stable", "recovered_fast", "recovered_slow", "repeated_pressure", "support_helped", "mixed"),
    "action_result": ("not_observed", "result_fast", "result_slow", "needs_repeated_attempts", "external_help_decisive", "mixed"),
}


@dataclass(frozen=True)
class LatentCalibrationScenario:
    scenario_id: str
    domain: str
    prompt: str
    event_type: str
    factor_ids: tuple[str, ...]
    result_options: tuple[str, ...]
    year_options: tuple[str, ...] = YEAR_OPTIONS
    intensity_options: tuple[str, ...] = INTENSITY_OPTIONS
    confidence_options: tuple[str, ...] = CONFIDENCE_OPTIONS

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LatentCalibrationAnswer:
    scenario_id: str
    year_option: str
    result_option: str
    intensity: str
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def latent_calibration_scenarios() -> tuple[LatentCalibrationScenario, ...]:
    return (
        _scenario(
            "latent.wealth_change",
            "wealth",
            "哪一段时间里，收入、资源或财务压力最容易出现明显变化？",
            "wealth_change",
            ("wealth_amplifier", "timing_sensitivity", "resource_support"),
        ),
        _scenario(
            "latent.career_transition",
            "career",
            "哪一段时间里，职业角色、平台或责任最容易出现明显变化？",
            "career_transition",
            ("career_amplifier", "resource_support", "opportunity_access"),
        ),
        _scenario(
            "latent.relationship_shift",
            "relationship",
            "哪一段时间里，关系重心或家庭责任最容易出现明显变化？",
            "relationship_shift",
            ("relationship_sensitivity", "timing_sensitivity", "stress_recovery_capacity"),
        ),
        _scenario(
            "latent.relocation_environment",
            "relocation",
            "哪一段时间里，居住地、工作城市或长期环境变化最明显？",
            "relocation_environment",
            ("relocation_mobility", "opportunity_access", "baseline_amplifier"),
        ),
        _scenario(
            "latent.stress_recovery",
            "stress",
            "压力较大的阶段里，你的恢复方式更接近哪一种？",
            "stress_recovery",
            ("stress_recovery_capacity", "risk_tolerance", "health_safety_modifier"),
        ),
        _scenario(
            "latent.action_result",
            "global",
            "你投入行动之后，结果通常更接近哪一种节奏？",
            "action_result",
            ("action_efficiency", "baseline_amplifier", "resource_support"),
        ),
    )


def latent_event_calibration_manifest() -> dict[str, object]:
    return {
        "version": "v20.latent_event_calibration_manifest.v1",
        "status": "ready",
        "factor_manifest": latent_factor_calibration_manifest()["version"],
        "scenario_count": len(latent_calibration_scenarios()),
        "scenarios": [row.to_dict() for row in latent_calibration_scenarios()],
        "input_policy": {
            "free_text_allowed": False,
            "year_selection": "single_bucket_or_unknown",
            "result_selection": "single_controlled_option",
            "intensity_selection": INTENSITY_OPTIONS,
            "confidence_selection": CONFIDENCE_OPTIONS,
        },
        "runtime_mutation": False,
        "guardrails": [
            "STRUCTURED_CHOICES_ONLY",
            "USER_EVENTS_CALIBRATE_PERSONAL_FACTORS_ONLY",
            "NO_RULE_TRUTH_UPDATE",
            "NO_USER_VISIBLE_PROBABILITY_SCORE",
        ],
    }


def analyze_latent_event_calibration(
    *,
    input_id: str,
    source_role: str,
    answers: tuple[LatentCalibrationAnswer, ...],
    locale: str = "zh",
) -> dict[str, object]:
    _validate_source_role(source_role)
    if not answers:
        raise ValueError("At least one latent calibration answer is required.")
    scenario_map = {row.scenario_id: row for row in latent_calibration_scenarios()}
    for answer in answers:
        _validate_answer(answer, scenario_map)
    factor_updates = _factor_update_signals(answers, scenario_map)
    source_hash = _source_hash(
        input_id,
        source_role,
        locale,
        *(f"{row.scenario_id}:{row.year_option}:{row.result_option}:{row.intensity}:{row.confidence}" for row in answers),
    )
    proposal = LearningProposal(
        proposal_id=f"v20.latent.event.calibration.proposal.{source_hash}",
        proposal_type="personal_hidden_setting_and_amplifier_review",
        summary=f"Review {len(answers)} structured life-node calibration answer(s).",
        risk="medium",
    )
    ledger = LedgerEntry(
        run_id=f"v20.latent.event.calibration.run.{source_hash}",
        source="latent_event_calibration_analyzer",
        input_hash=source_hash,
        artifact_hash=_source_hash(*(str(row) for row in factor_updates)),
    )
    return {
        "version": "v20.latent_event_calibration_report.v1",
        "source_hash": source_hash,
        "source_role": source_role,
        "answer_count": len(answers),
        "answers": [row.to_dict() for row in answers],
        "factor_update_signals": factor_updates,
        "learning_proposal": proposal.to_dict(),
        "ledger_entry": ledger.to_dict(),
        "runtime_mutation": False,
        "guardrails": [
            "STRUCTURED_LIFE_NODE_CHOICES_ONLY",
            "FACTOR_UPDATES_ARE_POSTERIOR_SIGNALS_ONLY",
            "NO_RUNTIME_RULE_OR_ANSWER_MUTATION",
            "VALIDATION_REQUIRED_BEFORE_ROUTE_RERANK_USE",
        ],
    }


def record_latent_event_calibration(
    *,
    input_id: str,
    source_role: str,
    answers: tuple[LatentCalibrationAnswer, ...],
    locale: str = "zh",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    analysis = analyze_latent_event_calibration(
        input_id=input_id,
        source_role=source_role,
        answers=answers,
        locale=locale,
    )
    storage = (store or local_jsonl_store_from_env()).append_record(
        "latent_event_calibration_ledger",
        _persistable_payload(analysis),
    )
    return {
        "version": "v20.latent_event_calibration_record_result.v1",
        "analysis": analysis,
        "storage": storage,
        "runtime_mutation": True,
        "guardrails": [
            "APPEND_ONLY_LATENT_EVENT_CALIBRATION",
            "NO_RUNTIME_RULE_MUTATION",
            "NO_USER_VISIBLE_SCORE_MUTATION",
        ],
    }


def _scenario(scenario_id: str, domain: str, prompt: str, event_type: str, factor_ids: tuple[str, ...]) -> LatentCalibrationScenario:
    return LatentCalibrationScenario(
        scenario_id=scenario_id,
        domain=domain,
        prompt=prompt,
        event_type=event_type,
        factor_ids=factor_ids,
        result_options=RESULT_OPTIONS[event_type],
    )


def _validate_source_role(source_role: str) -> None:
    if source_role not in {"user", "analyst", "admin", "practitioner"}:
        raise ValueError(f"Unsupported latent calibration source role: {source_role}")


def _validate_answer(answer: LatentCalibrationAnswer, scenario_map: dict[str, LatentCalibrationScenario]) -> None:
    scenario = scenario_map.get(answer.scenario_id)
    if scenario is None:
        raise ValueError(f"Unsupported latent calibration scenario: {answer.scenario_id}")
    if answer.year_option not in scenario.year_options:
        raise ValueError(f"Unsupported year option: {answer.year_option}")
    if answer.result_option not in scenario.result_options:
        raise ValueError(f"Unsupported result option: {answer.result_option}")
    if answer.intensity not in scenario.intensity_options:
        raise ValueError(f"Unsupported intensity option: {answer.intensity}")
    if answer.confidence not in scenario.confidence_options:
        raise ValueError(f"Unsupported confidence option: {answer.confidence}")


def _factor_update_signals(
    answers: tuple[LatentCalibrationAnswer, ...],
    scenario_map: dict[str, LatentCalibrationScenario],
) -> list[dict[str, object]]:
    rows = []
    for answer in answers:
        scenario = scenario_map[answer.scenario_id]
        evidence_strength = _evidence_strength(answer)
        for factor_id in scenario.factor_ids:
            rows.append(
                {
                    "factor_id": factor_id,
                    "scenario_id": answer.scenario_id,
                    "domain": scenario.domain,
                    "event_type": scenario.event_type,
                    "year_option": answer.year_option,
                    "result_option": answer.result_option,
                    "evidence_strength": evidence_strength,
                    "signal_direction": _signal_direction(answer.result_option),
                    "allowed_use": "personal_calibration_only",
                    "runtime_allowed": False,
                    "guardrails": [
                        "POSTERIOR_SIGNAL_ONLY",
                        "NO_RULE_TRUTH_UPDATE",
                        "NO_DETERMINISTIC_PREDICTION",
                    ],
                }
            )
    return rows


def _evidence_strength(answer: LatentCalibrationAnswer) -> float:
    intensity = {"none": 0.0, "mild": 0.35, "clear": 0.7, "strong": 1.0}[answer.intensity]
    confidence = {"low": 0.45, "medium": 0.7, "high": 0.92}[answer.confidence]
    if answer.year_option == "unknown" or answer.result_option in {"no_clear_change", "not_observed"}:
        return round(min(0.25, intensity * confidence), 3)
    return round(intensity * confidence, 3)


def _signal_direction(result_option: str) -> str:
    if result_option in {"income_down", "resource_pressure", "role_down", "relationship_pressure", "recovered_slow", "repeated_pressure"}:
        return "pressure_or_constraint"
    if result_option in {"no_clear_change", "not_observed", "stable"}:
        return "low_observed_change"
    if result_option == "mixed":
        return "mixed"
    return "activation_or_support"


def _persistable_payload(analysis: dict[str, object]) -> dict[str, object]:
    return {
        "version": analysis["version"],
        "source_hash": analysis["source_hash"],
        "source_role": analysis["source_role"],
        "answer_count": analysis["answer_count"],
        "answers": analysis["answers"],
        "factor_update_signals": analysis["factor_update_signals"],
        "learning_proposal": analysis["learning_proposal"],
        "ledger_entry": analysis["ledger_entry"],
        "runtime_mutation": False,
    }


def _source_hash(*values: str) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:16]
