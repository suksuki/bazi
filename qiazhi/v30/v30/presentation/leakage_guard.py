from __future__ import annotations

import re
from collections.abc import Iterator


LEAKAGE_SCAN_VERSION = "v30.product_projection_leakage_scan.v1"

USER_VISIBLE_ROLES = {"guest", "user"}

FORBIDDEN_EXACT_TOKENS = {
    "keep_both_branches_until_decision_engine_or_practitioner_calibration_separates_weight",
    "ask_only_if_value_of_information_exceeds_user_cost",
    "downgrade_assertion_level_unless_counter_evidence_is_resolved",
    "value_of_information",
    "training_target",
    "claim_key",
    "conflict_group_id",
    "policy_key",
    "runtime_debug",
    "llm_executed",
    "fallback_reason",
    "FeedbackOverlay",
    "SignalRegistry",
    "DecisionEngine",
}

FORBIDDEN_ENGINEERING_PHRASES = {
    "model_probe_failed",
    "readiness",
    "diagnostic_trace",
    "raw_signal",
    "score mutation",
    "verdict mutation",
}

SNAKE_CASE_PATTERN = re.compile(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+){2,}\b")

METADATA_PATH_PARTS = {
    "version",
    "boundary",
    "card_id",
    "branch_card_id",
    "verdict_id",
    "source_verdict_id",
    "source_conflict_id",
    "source_candidate_ids",
    "option_set_id",
    "question_id",
    "submit_contract",
    "selection_endpoint",
    "role_key",
    "contract_version",
    "output_runtime_contract",
}

SNAKE_CASE_VALUE_ALLOWLIST = {
    "customer_summary",
    "practitioner_calibration",
    "needs_calibration",
    "product_projection",
}


def scan_product_payload(payload: object, *, role_key: str) -> dict[str, object]:
    """Scan user-facing product payload text for internal runtime leakage."""

    role = role_key if role_key in {"guest", "user", "practitioner", "analyst", "admin", "lab"} else "user"
    strict = role in USER_VISIBLE_ROLES
    findings: list[dict[str, object]] = []
    for path, text in _iter_strings(payload):
        if _metadata_path(path):
            continue
        lowered = text.lower()
        for token in sorted(FORBIDDEN_EXACT_TOKENS):
            if token in text:
                findings.append(_finding(path, token=token, category="exact_internal_token"))
        for phrase in sorted(FORBIDDEN_ENGINEERING_PHRASES):
            if phrase.lower() in lowered:
                findings.append(_finding(path, token=phrase, category="engineering_phrase"))
        if strict:
            for match in SNAKE_CASE_PATTERN.findall(text):
                if match not in SNAKE_CASE_VALUE_ALLOWLIST:
                    findings.append(_finding(path, token=match, category="snake_case_runtime_value"))

    exact_hits = sorted({row["token"] for row in findings if row["category"] == "exact_internal_token"})
    snake_hits = sorted({row["token"] for row in findings if row["category"] == "snake_case_runtime_value"})
    return {
        "version": LEAKAGE_SCAN_VERSION,
        "role_key": role,
        "strict_user_surface": strict,
        "passed": not findings,
        "finding_count": len(findings),
        "findings": findings[:20],
        "forbidden_token_hits": exact_hits,
        "snake_case_hits": snake_hits,
        "role_policy": (
            "guest_user_projection_must_not_expose_internal_runtime_language"
            if strict
            else "diagnostic_roles_may_receive_more_depth_but_product_cards_still_avoid_raw_policy_keys"
        ),
        "boundary": "leakage_guard_scans_product_projection_text_without_mutating_runtime_facts",
    }


def assert_product_payload_clean(payload: object, *, role_key: str) -> dict[str, object]:
    scan = scan_product_payload(payload, role_key=role_key)
    if not scan["passed"]:
        raise ValueError(f"product projection leakage detected: {scan['findings']}")
    return scan


def _iter_strings(value: object, path: str = "$") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
        return
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield from _iter_strings(child, child_path)
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _iter_strings(child, f"{path}[{index}]")


def _metadata_path(path: str) -> bool:
    parts = {part.strip("[]") for part in re.split(r"[.\[\]]+", path) if part}
    return bool(parts & METADATA_PATH_PARTS)


def _finding(path: str, *, token: str, category: str) -> dict[str, object]:
    return {
        "path": path,
        "token": token,
        "category": category,
    }
