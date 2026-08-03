from __future__ import annotations

import re
from typing import Any

MINGLI_AGENT_NORMALIZATION_ISSUE_FIELD = "_server_normalization_issue_keys"


def repair_output_form(value: Any) -> Any:
    """Remove schema labels from copy while retaining typed enum fields."""

    if not isinstance(value, dict):
        return value
    value = dict(value)
    first_look = value.get("first_look")
    if isinstance(first_look, str):
        value["first_look"] = re.sub(
            r"^(?:PRIMARY|ALTERNATIVE|H1|H2)\s*[:：·-]\s*",
            "",
            first_look,
            flags=re.IGNORECASE,
        )
    hypotheses = value.get("hypotheses")
    names: dict[str, str] = {}
    if isinstance(hypotheses, list):
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict):
                continue
            name = hypothesis.get("name")
            if isinstance(name, str):
                repaired = re.sub(
                    r"\s*[（(](?:PRIMARY|ALTERNATIVE|H1|H2)[）)]\s*$",
                    "",
                    name,
                    flags=re.IGNORECASE,
                ).strip()
                hypothesis["name"] = repaired
                hypothesis_id = hypothesis.get("hypothesis_id")
                if isinstance(hypothesis_id, str):
                    names[hypothesis_id] = repaired
    decision = value.get("hypothesis_decision")
    if isinstance(decision, dict):
        for key in ("winner", "loser"):
            side = decision.get(key)
            if isinstance(side, dict) and isinstance(side.get("rationale"), str):
                side["rationale"] = _repair_decision_copy(side["rationale"], names)
        reversal = decision.get("reversal")
        if isinstance(reversal, dict):
            for key in ("question", "winner_signal", "loser_signal"):
                if isinstance(reversal.get(key), str):
                    reversal[key] = _repair_decision_copy(reversal[key], names)
    return _repair_nested_copy(value, names=names)


def _repair_decision_copy(value: str, names: dict[str, str]) -> str:
    for hypothesis_id, name in names.items():
        value = re.sub(
            rf"(?<![A-Za-z0-9]){hypothesis_id}(?![A-Za-z0-9])",
            name,
            value,
        )
    value = re.sub(
        r"(?:SUPPORTS|CONDITIONAL|OPPOSES|UNRESOLVED)\s*[:：]\s*",
        "",
        value,
    )
    return (
        value.replace("UNRESOLVED", "尚需校准")
        .replace("BLOCKED", "路径受阻")
        .replace("PRIMARY", "主解释")
        .replace("ALTERNATIVE", "替代解释")
    )


_NON_PROSE_FIELDS = {
    MINGLI_AGENT_NORMALIZATION_ISSUE_FIELD,
    "adjudication",
    "check_code",
    "classification",
    "closure",
    "competition_kinds",
    "confidence",
    "coordinate_evidence_id",
    "day_master_state",
    "dominant_chain_status",
    "effective_root_coordinates",
    "effective_root_status",
    "evidence_ids",
    "hypothesis_id",
    "judgment",
    "loser_id",
    "mechanism_evidence_ids",
    "method_card_ref",
    "method_asset_ref",
    "natal_evidence_ids",
    "relation_evidence_ids",
    "role",
    "root_status",
    "rooted_visible_support_status",
    "ruling",
    "selected_hypothesis_id",
    "status",
    "transformation_codes",
    "winner_id",
}


def _repair_nested_copy(value: Any, *, names: dict[str, str], field: str = "") -> Any:
    if isinstance(value, dict):
        return {
            key: _repair_nested_copy(item, names=names, field=key) for key, item in value.items()
        }
    if isinstance(value, list):
        return [_repair_nested_copy(item, names=names, field=field) for item in value]
    if isinstance(value, str) and field not in _NON_PROSE_FIELDS:
        return _repair_decision_copy(value, names)
    return value
