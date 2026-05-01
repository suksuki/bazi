from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

from v20.learning.ledger import LedgerEntry
from v20.learning.proposal import LearningProposal
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env

CONTROL_OPTIONS: dict[str, tuple[str, ...]] = {
    "control.day_master_strength": ("偏强", "中和偏强", "中和", "中和偏弱", "偏弱", "待复核"),
    "control.shang_guan_jian_guan": ("成立", "候选", "被印化", "被财通关", "不成立", "待复核"),
    "control.wealth_capacity": ("可承接", "需扶身", "走通关", "看大运", "证据不足"),
    "control.pattern_status": ("成格", "破格", "候选", "不取格", "待复核"),
}


@dataclass(frozen=True)
class PractitionerControlSelection:
    control_key: str
    option: str
    source_decision_keys: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_practitioner_calibration(
    *,
    input_id: str,
    source_role: str,
    selections: tuple[PractitionerControlSelection, ...],
    locale: str = "zh",
) -> dict[str, object]:
    _validate_source_role(source_role)
    if not selections:
        raise ValueError("At least one practitioner control selection is required.")
    for selection in selections:
        _validate_selection(selection)
    source_hash = _source_hash(
        input_id,
        source_role,
        locale,
        *(
            f"{selection.control_key}={selection.option}:{','.join(selection.source_decision_keys)}"
            for selection in selections
        ),
    )
    signals = [
        {
            "control_key": selection.control_key,
            "option": selection.option,
            "source_decision_keys": selection.source_decision_keys,
            "target": _target_for_control(selection.control_key),
            "signal_role": "structured_practitioner_decision_parameter_feedback",
            "runtime_allowed": False,
            "guardrails": [
                "STRUCTURED_SELECTION_ONLY",
                "NO_RUNTIME_RULE_MUTATION",
                "PROMOTION_REQUIRES_BATCH_VALIDATION",
            ],
        }
        for selection in selections
    ]
    proposal = LearningProposal(
        proposal_id=f"v20.practitioner.calibration.proposal.{source_hash}",
        proposal_type="practitioner_decision_parameter_review",
        summary=f"Review {len(selections)} structured practitioner control selection(s).",
        risk="medium" if any(selection.option in {"成立", "成格", "偏强", "偏弱"} for selection in selections) else "low",
    )
    ledger = LedgerEntry(
        run_id=f"v20.practitioner.calibration.run.{source_hash}",
        source="practitioner_calibration_analyzer",
        input_hash=source_hash,
        artifact_hash=_source_hash(*(str(signal) for signal in signals)),
    )
    return {
        "version": "v20.practitioner_calibration_report.v1",
        "source_hash": source_hash,
        "source_role": source_role,
        "selection_count": len(selections),
        "selections": [selection.to_dict() for selection in selections],
        "training_signals": signals,
        "learning_proposal": proposal.to_dict(),
        "ledger_entry": ledger.to_dict(),
        "runtime_mutation": False,
        "guardrails": [
            "PRACTITIONER_CALIBRATION_SIGNAL_ONLY",
            "BUTTON_OR_SELECT_ONLY",
            "NO_FREE_TEXT_CORE_DECISION",
            "NO_RUNTIME_DECISION_MUTATION",
            "VALIDATION_REQUIRED_BEFORE_POLICY_USE",
        ],
    }


def record_practitioner_calibration(
    *,
    input_id: str,
    source_role: str,
    selections: tuple[PractitionerControlSelection, ...],
    locale: str = "zh",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    analysis = analyze_practitioner_calibration(
        input_id=input_id,
        source_role=source_role,
        selections=selections,
        locale=locale,
    )
    storage = (store or local_jsonl_store_from_env()).append_record(
        "practitioner_calibration_ledger",
        _persistable_payload(analysis),
    )
    return {
        "version": "v20.practitioner_calibration_record_result.v1",
        "analysis": analysis,
        "storage": storage,
        "runtime_mutation": True,
        "guardrails": [
            "APPEND_ONLY_PRACTITIONER_CALIBRATION",
            "NO_RUNTIME_RULE_MUTATION",
            "NO_USER_VISIBLE_VERDICT_MUTATION",
        ],
    }


def _persistable_payload(analysis: dict[str, object]) -> dict[str, object]:
    return {
        "version": analysis["version"],
        "source_hash": analysis["source_hash"],
        "source_role": analysis["source_role"],
        "selection_count": analysis["selection_count"],
        "selections": analysis["selections"],
        "training_signals": analysis["training_signals"],
        "learning_proposal": analysis["learning_proposal"],
        "ledger_entry": analysis["ledger_entry"],
        "runtime_mutation": False,
    }


def _validate_source_role(source_role: str) -> None:
    if source_role not in {"analyst", "admin", "practitioner"}:
        raise ValueError(f"Unsupported practitioner calibration source role: {source_role}")


def _validate_selection(selection: PractitionerControlSelection) -> None:
    options = CONTROL_OPTIONS.get(selection.control_key)
    if not options:
        raise ValueError(f"Unsupported practitioner control: {selection.control_key}")
    if selection.option not in options:
        raise ValueError(f"Unsupported option {selection.option} for {selection.control_key}")
    if any(not key.startswith("decision.") for key in selection.source_decision_keys):
        raise ValueError("source_decision_keys must reference decision.* keys")


def _target_for_control(control_key: str) -> str:
    return {
        "control.day_master_strength": "decision_parameters.strength_capacity",
        "control.shang_guan_jian_guan": "decision_parameters.ten_god_collision",
        "control.wealth_capacity": "decision_parameters.wealth_capacity",
        "control.pattern_status": "decision_parameters.pattern_status",
    }.get(control_key, "decision_parameters")


def _source_hash(*values: str) -> str:
    raw = "|".join(values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
