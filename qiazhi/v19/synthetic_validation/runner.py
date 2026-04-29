from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping

from v19.core import evaluate_core, validate_inference_bundle
from v19.domain_adapters import build_domain_adapter_input, validate_domain_adapter_input
from v19.mapping_registry import MappingRegistry
from v19.synthetic_validation.schema import SyntheticCase


SYNTHETIC_VALIDATION_VERSION = "v19.synthetic_validation.v1"

DEFAULT_FLOW_CYCLE = {
    ("seal", "peer", "support"),
    ("peer", "output", "drain"),
    ("output", "wealth", "generate"),
    ("wealth", "officer", "generate"),
    ("officer", "seal", "generate"),
}


def _stable_hash(payload: Mapping[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _coerce_case(case: SyntheticCase | Mapping[str, Any]) -> SyntheticCase:
    if isinstance(case, SyntheticCase):
        return case
    return SyntheticCase.from_mapping(case)


def _get_path(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if isinstance(current, Mapping):
            if part not in current:
                return None
            current = current[part]
            continue
        if isinstance(current, list):
            next_values = []
            for item in current:
                if isinstance(item, Mapping) and part in item:
                    next_values.append(item[part])
            current = next_values
            continue
        return None
    return current


def _contains_item(actual: Any, expected_item: Mapping[str, Any]) -> bool:
    if not isinstance(actual, list):
        return False
    for item in actual:
        if not isinstance(item, Mapping):
            continue
        if all(item.get(key) == value for key, value in expected_item.items()):
            return True
    return False


def _match(actual: Any, expected: Any) -> bool:
    if isinstance(expected, Mapping):
        if "equals" in expected:
            return actual == expected["equals"]
        if "in" in expected:
            return actual in set(expected["in"])
        if "contains" in expected:
            if isinstance(actual, list):
                return expected["contains"] in actual
            if isinstance(actual, str):
                return str(expected["contains"]) in actual
            return False
        if "contains_any" in expected:
            wanted = set(expected["contains_any"])
            if isinstance(actual, list):
                return bool(wanted & set(actual))
            return actual in wanted
        if "not_contains" in expected:
            if isinstance(actual, list):
                return expected["not_contains"] not in actual
            if isinstance(actual, str):
                return str(expected["not_contains"]) not in actual
            return True
        if "contains_item" in expected:
            return _contains_item(actual, expected["contains_item"])
        if "exists" in expected:
            return (actual is not None) is bool(expected["exists"])
    if isinstance(actual, list):
        return expected in actual
    return actual == expected


def _expectation_failures(payload: Mapping[str, Any], expectations: Mapping[str, Any], scope: str) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []
    for path, expected in expectations.items():
        actual = _get_path(payload, path)
        if not _match(actual, expected):
            failures.append(
                {
                    "scope": scope,
                    "path": path,
                    "expected": expected,
                    "actual": actual,
                    "failure_type": "expectation_mismatch",
                }
            )
    return failures


def _walk_keys(payload: Any) -> Iterable[str]:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            yield str(key)
            yield from _walk_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _walk_keys(item)


def _forbidden_failures(forbidden_outputs: List[str], inference: Mapping[str, Any], adapter_input: Mapping[str, Any]) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []
    scoped = {"inference": inference, "domain_adapter": adapter_input}
    inference_keys = set(_walk_keys(inference))
    adapter_keys = set(_walk_keys(adapter_input))
    for forbidden in forbidden_outputs:
        if "." in forbidden:
            root, _, remainder = forbidden.partition(".")
            if root in scoped and _get_path(scoped[root], remainder) is not None:
                failures.append({"scope": root, "path": remainder, "failure_type": "forbidden_output_present"})
            continue
        if forbidden in inference_keys:
            failures.append({"scope": "inference", "path": forbidden, "failure_type": "forbidden_output_present"})
        if forbidden in adapter_keys:
            failures.append({"scope": "domain_adapter", "path": forbidden, "failure_type": "forbidden_output_present"})
    return failures


def _forced_failures(inference: Mapping[str, Any], adapter_input: Mapping[str, Any]) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []
    validation = validate_inference_bundle(inference)
    if not validation["valid"]:
        failures.append({"scope": "inference", "failure_type": "schema_invalid", "errors": validation["errors"]})

    adapter_validation = validate_domain_adapter_input(adapter_input, inference)
    if not adapter_validation["valid"]:
        failures.append({"scope": "domain_adapter", "failure_type": "adapter_invalid", "errors": adapter_validation["errors"]})

    flows = {
        (str(row.get("from")), str(row.get("to")), str(row.get("type")))
        for row in inference.get("energy_flow", [])
        if isinstance(row, Mapping)
    }
    if DEFAULT_FLOW_CYCLE <= flows:
        failures.append({"scope": "inference.energy_flow", "failure_type": "default_closed_loop_detected"})

    for conflict in inference.get("internal_conflicts", []):
        if isinstance(conflict, Mapping) and not conflict.get("direction"):
            failures.append({"scope": "inference.internal_conflicts", "failure_type": "missing_conflict_direction"})
    return failures


def _run_case(case: SyntheticCase, mapping_registry: MappingRegistry | None = None) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    try:
        core_result = evaluate_core(case.chart)
        inference = core_result["inference"]
        adapter_input = build_domain_adapter_input(inference, domain="wealth", mapping_registry=mapping_registry)
    except Exception as exc:
        return {
            "case_id": case.case_id,
            "status": "fail",
            "tags": list(case.tags),
            "failures": [{"scope": "runner", "failure_type": "exception", "message": str(exc)}],
            "warnings": [],
        }

    failures.extend(_forced_failures(inference, adapter_input))
    failures.extend(_expectation_failures(inference, case.expected_inference_signals, "inference"))
    failures.extend(_expectation_failures(adapter_input, case.expected_domain_adapter_outputs, "domain_adapter"))
    failures.extend(_forbidden_failures(case.forbidden_outputs, inference, adapter_input))

    status = "fail" if failures else "warning" if warnings else "pass"
    return {
        "case_id": case.case_id,
        "status": status,
        "tags": list(case.tags),
        "failures": failures,
        "warnings": warnings,
    }


def run_synthetic_validation(
    cases: Iterable[SyntheticCase | Mapping[str, Any]],
    mapping_registry: MappingRegistry | None = None,
) -> Dict[str, Any]:
    normalized_cases = [_coerce_case(case) for case in cases]
    case_results = [_run_case(case, mapping_registry=mapping_registry) for case in normalized_cases]
    failures = [result for result in case_results if result["status"] == "fail"]
    warnings = [result for result in case_results if result["status"] == "warning"]
    payload = {"version": SYNTHETIC_VALIDATION_VERSION, "case_ids": [case.case_id for case in normalized_cases]}
    return {
        "version": SYNTHETIC_VALIDATION_VERSION,
        "validation_run": "synthetic_run_" + _stable_hash(payload),
        "status": "fail" if failures else "warning" if warnings else "pass",
        "summary": {
            "total": len(case_results),
            "passed": sum(1 for result in case_results if result["status"] == "pass"),
            "failed": len(failures),
            "warnings": len(warnings),
        },
        "cases": case_results,
        "drift_report": {
            "drift_count": sum(len(result["failures"]) for result in failures),
            "items": [
                {"case_id": result["case_id"], "failures": result["failures"]}
                for result in failures
            ],
        },
        "regression_report": {
            "regression_count": len(failures),
            "items": [
                {"case_id": result["case_id"], "tags": result["tags"], "status": result["status"]}
                for result in failures
            ],
        },
        "boundaries": [
            "SYNTHETIC_VALIDATION_ONLY",
            "DOES_NOT_PROVE_REAL_WORLD_ACCURACY",
            "NO_RULE_ACTIVATION",
            "NO_PRODUCTION_PATH",
        ],
    }
