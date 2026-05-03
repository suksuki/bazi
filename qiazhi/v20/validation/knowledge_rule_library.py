from __future__ import annotations

from collections import Counter
from typing import Any

from v20.corpus.artifacts import read_corpus_training_artifacts
from v20.knowledge.rule_library import build_knowledge_rule_library, validate_knowledge_rule_library
from v20.validation.rule_synthetic import build_rule_synthetic_training_report


def build_knowledge_rule_validation_report(domain: str = "", *, limit: int = 0) -> dict[str, object]:
    library = build_knowledge_rule_library(domain, limit=limit)
    library_validation = validate_knowledge_rule_library(domain, limit=limit)
    synthetic_training = build_rule_synthetic_training_report()
    corpus_training = read_corpus_training_artifacts()
    synthetic_by_domain = _synthetic_training_by_domain(synthetic_training)
    synthetic_by_rule = _synthetic_training_by_rule(synthetic_training)
    corpus_by_source = _corpus_training_by_source(corpus_training)
    rows = [
        _validate_definition(
            definition,
            synthetic_by_domain=synthetic_by_domain,
            synthetic_by_rule=synthetic_by_rule,
            corpus_by_source=corpus_by_source,
        )
        for definition in library.get("definitions", ())
        if isinstance(definition, dict)
    ]
    state_counts = Counter(str(row["validation_state"]) for row in rows)
    iteration_actions = Counter(str(row["next_iteration_action"]) for row in rows)
    hard_failures = [
        failure
        for row in rows
        for failure in row.get("hard_failures", ())
        if isinstance(failure, str)
    ]
    hard_failures.extend(str(row) for row in library_validation.get("failures", ()) if str(row))
    return {
        "version": "v20.knowledge_rule_library_validation_report.v1",
        "status": "active_ready" if rows else "empty",
        "ok": not hard_failures,
        "domain": domain.strip(),
        "definition_count": len(rows),
        "synthetic_covered_count": sum(1 for row in rows if row["synthetic_state"] != "missing_synthetic_case"),
        "missing_synthetic_count": sum(1 for row in rows if row["synthetic_state"] == "missing_synthetic_case"),
        "corpus_signal_count": sum(1 for row in rows if row["corpus_signal_state"] != "corpus_not_built"),
        "runtime_allowed_count": sum(1 for row in rows if row.get("runtime_allowed") is True),
        "state_counts": dict(sorted(state_counts.items())),
        "iteration_actions": dict(sorted(iteration_actions.items())),
        "definitions": rows,
        "hard_failures": hard_failures,
        "upstream": {
            "library_status": library.get("status", ""),
            "library_validation_status": library_validation.get("status", ""),
            "synthetic_training_status": synthetic_training.get("status", ""),
            "synthetic_case_count": synthetic_training.get("case_count", 0),
            "corpus_training_status": corpus_training.get("status", ""),
            "corpus_training_run_id": corpus_training.get("run_id", ""),
        },
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_RULE_VALIDATION_FEEDS_ACTIVE_ITERATION",
            "SYNTHETIC_CASES_VALIDATE_RULE_COLLISIONS",
            "CORPUS_SUPPORT_IS_PRIOR_NOT_RULE_TRUTH",
            "ACTIVE_RULE_ITERATION",
        ],
    }


def _validate_definition(
    definition: dict[str, object],
    *,
    synthetic_by_domain: dict[str, dict[str, object]],
    synthetic_by_rule: dict[str, dict[str, object]],
    corpus_by_source: dict[str, dict[str, object]],
) -> dict[str, object]:
    domain = str(definition.get("domain", ""))
    source_id = str(definition.get("source_knowledge_id", ""))
    synthetic = synthetic_by_domain.get(domain, {})
    rule_key = str(definition.get("rule_key", ""))
    if rule_key:
        synthetic = synthetic_by_rule.get(rule_key, synthetic)
    corpus = corpus_by_source.get(source_id, {})
    hard_failures: list[str] = []
    alignment = definition.get("bazi_alignment", {})
    if not isinstance(alignment, dict) or alignment.get("ok") is not True:
        hard_failures.append(f"bazi_alignment_failed:{definition.get('rule_key', '')}")
    synthetic_state = _synthetic_state(synthetic)
    corpus_state = _corpus_state(corpus)
    validation_state = _validation_state(synthetic_state, corpus_state, hard_failures)
    return {
        "version": "v20.knowledge_rule_definition_validation.v1",
        "rule_key": definition.get("rule_key", ""),
        "domain": domain,
        "source_knowledge_id": source_id,
        "title": definition.get("title", ""),
        "portrait": _first_value(definition.get("portrait_outputs", ()), "label"),
        "question": _first_value(definition.get("question_outputs", ()), "title"),
        "atom_count": len(definition.get("condition_atoms", ())),
        "synthetic_state": synthetic_state,
        "synthetic_case_count": int(synthetic.get("case_count", 0) or 0),
        "synthetic_confidence": float(synthetic.get("synthetic_confidence", 0.0) or 0.0),
        "synthetic_case_ids": tuple(str(row) for row in synthetic.get("case_ids", ()) if str(row)),
        "corpus_signal_state": corpus_state,
        "support_count": int(corpus.get("support_count", 0) or 0),
        "support_ratio": float(corpus.get("support_ratio", 0.0) or 0.0),
        "support_quality": str(corpus.get("support_quality", "")),
        "top_matched_feature_ids": _top_feature_ids(corpus),
        "validation_state": validation_state,
        "next_iteration_action": _next_iteration_action(validation_state),
        "runtime_allowed": True,
        "hard_failures": hard_failures,
        "guardrails": [
            "DEFINITION_VALIDATION_ONLY",
            "MISSING_SYNTHETIC_CASE_FEEDS_ITERATION",
            "TOO_BROAD_CORPUS_SUPPORT_FEEDS_SUBCONDITIONS",
        ],
    }


def _synthetic_training_by_domain(report: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = {}
    for row in report.get("rule_domain_training", ()):
        if isinstance(row, dict) and row.get("domain"):
            rows[str(row["domain"])] = row
    return rows


def _synthetic_training_by_rule(report: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = {}
    for row in report.get("rule_training", ()):
        if not isinstance(row, dict):
            continue
        rule_key = str(row.get("rule_key", ""))
        if rule_key:
            rows[rule_key] = row
    return rows


def _corpus_training_by_source(report: dict[str, object]) -> dict[str, dict[str, object]]:
    training = report.get("rule_proposal_training", {})
    if not isinstance(training, dict):
        return {}
    rows = {}
    for row in training.get("proposals", ()):
        if isinstance(row, dict) and row.get("source_knowledge_id"):
            rows[str(row["source_knowledge_id"])] = row
    return rows


def _synthetic_state(row: dict[str, object]) -> str:
    if not row:
        return "missing_synthetic_case"
    if int(row.get("fail_count", 0) or 0) > 0:
        return "synthetic_failed"
    if float(row.get("synthetic_confidence", 0.0) or 0.0) >= 1.0:
        return "synthetic_passed"
    return "synthetic_incomplete"


def _corpus_state(row: dict[str, object]) -> str:
    if not row:
        return "corpus_not_built"
    quality = str(row.get("support_quality", ""))
    if quality == "too_broad_needs_subconditions":
        return "corpus_too_broad"
    if quality:
        return quality
    return "corpus_signal_available"


def _validation_state(synthetic_state: str, corpus_state: str, hard_failures: list[str]) -> str:
    if hard_failures:
        return "blocked_by_contract_failure"
    if synthetic_state == "missing_synthetic_case":
        return "needs_synthetic_case"
    if synthetic_state == "synthetic_failed":
        return "needs_rule_or_case_fix"
    if corpus_state == "corpus_too_broad":
        return "synthetic_passed_needs_subconditions"
    if corpus_state == "corpus_not_built":
        # 无语料时仍推进可学习子条件，保持规则主线可继续迭代；
        # 语料作为优化先验，不作为规则真值门槛。
        return "synthetic_passed_fallback_ready"
    return "validated_active_ready"


def _next_iteration_action(validation_state: str) -> str:
    actions = {
        "blocked_by_contract_failure": "fix_rule_contract",
        "needs_synthetic_case": "add_domain_synthetic_case",
        "needs_rule_or_case_fix": "repair_rule_atoms_or_expected_case",
        "synthetic_passed_needs_subconditions": "split_by_exact_feature_signature_and_counterexamples",
        "synthetic_passed_fallback_ready": "split_by_exact_feature_signature_and_activate_replay_eval",
        "validated_active_ready": "activate_weight_or_parameter_iteration",
    }
    return actions.get(validation_state, "manual_review")


def _top_feature_ids(row: dict[str, object]) -> tuple[str, ...]:
    values = []
    for item in row.get("top_matched_feature_ids", ()):
        if isinstance(item, dict) and item.get("value"):
            values.append(str(item["value"]))
        elif isinstance(item, str):
            values.append(item)
    return tuple(values[:8])


def _first_value(rows: object, key: str) -> str:
    if not isinstance(rows, (list, tuple)) or not rows:
        return ""
    first = rows[0]
    if not isinstance(first, dict):
        return ""
    return str(first.get(key, ""))
