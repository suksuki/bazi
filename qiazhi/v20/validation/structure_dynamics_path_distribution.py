from __future__ import annotations

from collections import Counter
from typing import Any

from v20.validation.structure_dynamics_synthetic import run_structure_dynamics_synthetic_suite


STRUCTURE_DYNAMICS_PATH_DISTRIBUTION_VERSION = "v20.structure_dynamics_path_distribution.v1"


def build_structure_dynamics_path_distribution(*, synthetic_report: dict[str, Any] | None = None) -> dict[str, Any]:
    report = synthetic_report or run_structure_dynamics_synthetic_suite()
    rows = [row for row in report.get("results", ()) if isinstance(row, dict)]
    labels = Counter()
    states = Counter()
    semantic_labels = Counter()
    time_relation_types = Counter()
    for row in rows:
        observed = row.get("observed", {}) if isinstance(row.get("observed"), dict) else {}
        label = str(observed.get("label", ""))
        if label:
            labels[label] += 1
        brain_path = observed.get("brain_work_path", {}) if isinstance(observed.get("brain_work_path"), dict) else {}
        state = str(brain_path.get("state", ""))
        if state:
            states[state] += 1
        for semantic in observed.get("semantic_labels", ()):
            semantic_labels[str(semantic)] += 1
        for relation_type in observed.get("time_relation_blockers", ()):
            time_relation_types[str(relation_type)] += 1
    counterexample_labels = {"财破印", "比劫夺财", "印制食伤"}
    return {
        "version": STRUCTURE_DYNAMICS_PATH_DISTRIBUTION_VERSION,
        "status": "ready" if report.get("ok") else "blocked",
        "case_count": int(report.get("case_count", 0) or 0),
        "pass_rate": float(report.get("pass_rate", 0.0) or 0.0),
        "label_distribution": _counter_rows(labels),
        "state_distribution": _counter_rows(states),
        "semantic_distribution": _counter_rows(semantic_labels),
        "time_relation_distribution": _counter_rows(time_relation_types),
        "counterexample_coverage": {
            "required_labels": sorted(counterexample_labels),
            "covered_labels": sorted(label for label in counterexample_labels if semantic_labels.get(label, 0) > 0),
            "covered_count": sum(1 for label in counterexample_labels if semantic_labels.get(label, 0) > 0),
            "required_count": len(counterexample_labels),
            "status": "covered" if all(semantic_labels.get(label, 0) > 0 for label in counterexample_labels) else "needs_expansion",
        },
        "time_blocker_coverage": {
            "covered_types": sorted(key for key, count in time_relation_types.items() if count > 0),
            "covered_count": len([key for key, count in time_relation_types.items() if count > 0]),
            "status": "covered" if time_relation_types else "needs_expansion",
        },
        "runtime_mutation": False,
        "guardrails": [
            "PATH_DISTRIBUTION_IS_AGGREGATE_ONLY",
            "NO_RUNTIME_POINTER_MUTATION",
            "NO_SINGLE_CASE_TRUTH_FROM_DISTRIBUTION",
        ],
    }


def _counter_rows(counter: Counter[str]) -> list[dict[str, Any]]:
    total = sum(counter.values())
    return [
        {
            "key": key,
            "count": count,
            "ratio": round(count / max(1, total), 4),
        }
        for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]
