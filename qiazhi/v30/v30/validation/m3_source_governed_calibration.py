from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.knowledge.source_registry import SOURCE_FAMILIES
from v30.validation.corpus_518k import Corpus518KValidationResult
from v30.validation.synthetic_case import SyntheticValidationSuiteResult


M3_SOURCE_GOVERNED_CALIBRATION_VERSION = "v30.m3_source_governed_calibration.v1"


CORE_DOMAIN_FAMILIES = {
    "career",
    "wealth",
    "relationship",
    "health",
    "structure_dynamic",
    "structure_pattern",
    "useful_god",
    "ten_god",
}


def build_m3_source_governed_calibration(
    *,
    krp_units: list[dict[str, object]],
    rule_specs: list[dict[str, object]],
    portrait_assets: list[dict[str, object]],
    synthetic: SyntheticValidationSuiteResult,
    validation_518k: Corpus518KValidationResult | None = None,
    artifact_dir: str | Path | None = None,
) -> dict[str, object]:
    """Build the M3-G1 calibration tag layer.

    The payload is intentionally observational. It maps sources, rules, portrait
    density, synthetic evidence, and 518K distribution into calibration tags
    without changing chart facts, rule outcomes, or active policy pointers.
    """

    real_case_tags = _real_case_calibration_tags(synthetic)
    domain_depth = _domain_rule_depth_expansion(krp_units=krp_units, rule_specs=rule_specs, portrait_assets=portrait_assets)
    training_distribution = _training_synthetic_distribution(synthetic=synthetic, domain_depth=domain_depth)
    source_queue = _source_extraction_queue(krp_units=krp_units, rule_specs=rule_specs, domain_depth=domain_depth)
    distribution_518k = _distribution_518k_summary(validation_518k)
    tag_groups = {
        "real_case_calibration_tags": real_case_tags,
        "domain_rule_depth_expansion": domain_depth,
        "training_synthetic_distribution": training_distribution,
        "source_extraction_queue": source_queue,
        "distribution_518k_summary": distribution_518k,
    }
    payload: dict[str, object] = {
        "version": M3_SOURCE_GOVERNED_CALIBRATION_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "ready",
        "tag_groups": tag_groups,
        "coverage": {
            "tag_group_count": len(tag_groups),
            "real_case_tag_count": len(real_case_tags),
            "domain_depth_tag_count": len(domain_depth),
            "training_tag_count": len(training_distribution),
            "source_queue_count": len(source_queue),
            "has_518k_distribution": bool(distribution_518k.get("included")),
        },
        "decision_boundary": {
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "training_scope": [
                "source_coverage_weights",
                "rule_path_priority",
                "portrait_density_review",
                "dynamic_structure_path_review",
                "question_strategy",
            ],
            "forbidden_training_scope": [
                "four_pillars",
                "luck_cycle_facts",
                "flow_year_facts",
                "flow_month_facts",
                "fixed_useful_god_verdict",
                "fixed_structure_verdict",
            ],
        },
        "boundary": "m3_g1_tags_are_observational_calibration_evidence_not_chart_facts_or_pointer_promotion",
    }
    if artifact_dir is not None:
        path = _write_artifact(payload, Path(artifact_dir))
        payload["artifact_uri"] = str(path)
    return payload


def _real_case_calibration_tags(synthetic: SyntheticValidationSuiteResult) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for result in synthetic.results:
        observed = result.observed
        rule_states = observed.get("rule_states_by_kind", {})
        path_scores = observed.get("structure_path_scores", {})
        krp_summary = observed.get("krp_library_summary", {})
        portrait_domains = observed.get("macro_portrait_domains", [])
        rows.append(
            {
                "tag_id": f"m3.real_case_calibration_tags.{result.case_id}",
                "case_id": result.case_id,
                "case_passed": result.passed,
                "mapped_krp_domains": sorted(_mapping_keys(krp_summary.get("by_domain") if isinstance(krp_summary, dict) else {})),
                "mapped_rule_states": sorted(_flatten_rule_states(rule_states).items()),
                "dynamic_path_count": _int_from_mapping(path_scores, "dynamic_path_count"),
                "portrait_domain_count": len(portrait_domains) if isinstance(portrait_domains, list) else 0,
                "calibration_state": "stable_observation" if result.passed else "needs_m3_review",
                "target_modules": ["M3"],
                "boundary": "real_case_calibration_tag_routes_m3_review_without_changing_chart_facts",
            }
        )
    return rows


def _domain_rule_depth_expansion(
    *,
    krp_units: list[dict[str, object]],
    rule_specs: list[dict[str, object]],
    portrait_assets: list[dict[str, object]],
) -> list[dict[str, object]]:
    krp_by_domain = Counter(str(row.get("domain") or "") for row in krp_units)
    rule_by_domain = Counter(str(row.get("domain") or "") for row in rule_specs)
    portrait_by_domain = Counter(str(row.get("domain") or "") for row in portrait_assets)
    domains = sorted(CORE_DOMAIN_FAMILIES | set(krp_by_domain) | set(rule_by_domain) | set(portrait_by_domain))
    rows: list[dict[str, object]] = []
    for domain in domains:
        if not domain:
            continue
        krp_count = krp_by_domain.get(domain, 0)
        rule_count = rule_by_domain.get(domain, 0) + (rule_by_domain.get("domain_rule", 0) if domain in {"career", "wealth", "relationship", "health"} else 0)
        portrait_count = portrait_by_domain.get(domain, 0)
        depth_score = round(min(1.0, krp_count / 3 * 0.45 + rule_count / 2 * 0.35 + portrait_count / 1 * 0.2), 3)
        rows.append(
            {
                "tag_id": f"m3.domain_rule_depth_expansion.{domain}",
                "domain": domain,
                "krp_unit_count": krp_count,
                "rule_spec_count": rule_count,
                "portrait_asset_count": portrait_count,
                "depth_score": depth_score,
                "depth_state": "calibrated_depth" if depth_score >= 0.7 else "growth_candidate",
                "recommended_action": _domain_action(domain, depth_score),
                "boundary": "domain_depth_tag_expands_rule_evidence_not_fixed_life_outcome_claims",
            }
        )
    return rows


def _training_synthetic_distribution(
    *,
    synthetic: SyntheticValidationSuiteResult,
    domain_depth: list[dict[str, object]],
) -> list[dict[str, object]]:
    growth_domains = [
        str(row.get("domain"))
        for row in domain_depth
        if row.get("depth_state") == "growth_candidate"
    ]
    return [
        {
            "tag_id": "m3.training_synthetic_distribution.m3_core_spine",
            "suite_id": synthetic.suite_id,
            "case_count": synthetic.case_count,
            "passed_count": synthetic.passed_count,
            "failed_count": synthetic.failed_count,
            "growth_candidate_domains": growth_domains,
            "training_candidate_scope": [
                "source_family_coverage",
                "rule_state_distribution",
                "dynamic_path_distribution",
                "portrait_density_distribution",
            ],
            "chart_fact_mutation_allowed": False,
            "boundary": "training_distribution_tags_tune_m3_coverage_not_chart_facts",
        }
    ]


def _source_extraction_queue(
    *,
    krp_units: list[dict[str, object]],
    rule_specs: list[dict[str, object]],
    domain_depth: list[dict[str, object]],
) -> list[dict[str, object]]:
    unit_source_ids = {
        str(source_id)
        for unit in krp_units
        for source_id in (unit.get("source_family_ids") if isinstance(unit.get("source_family_ids"), list) else [])
        if source_id
    }
    rule_domains = {str(row.get("domain") or "") for row in rule_specs}
    growth_domains = [
        str(row.get("domain"))
        for row in domain_depth
        if row.get("depth_state") == "growth_candidate"
    ]
    rows: list[dict[str, object]] = []
    for source in SOURCE_FAMILIES:
        source_id = source.source_family_id
        rows.append(
            {
                "tag_id": f"m3.source_extraction_queue.{source_id}",
                "source_family_id": source_id,
                "already_referenced": source_id in unit_source_ids,
                "target_domains": growth_domains[:6] or sorted(rule_domains),
                "queue_state": "continue_extracting" if source_id in unit_source_ids else "needs_initial_mapping",
                "runtime_import_allowed": False,
                "boundary": "source_queue_allows_source_governed_extraction_not_v20_runtime_import",
            }
        )
    return rows


def _distribution_518k_summary(validation_518k: Corpus518KValidationResult | None) -> dict[str, object]:
    if validation_518k is None:
        return {
            "tag_id": "m3.518k_distribution_summary.not_requested",
            "included": False,
            "reason": "not_requested",
            "boundary": "518k_distribution_summary_is_optional_for_routine_m3_g1_validation",
        }
    return {
        "tag_id": f"m3.518k_distribution_summary.{validation_518k.run_id}",
        "included": True,
        "run_id": validation_518k.run_id,
        "mode": validation_518k.mode,
        "case_count": validation_518k.case_count,
        "promotion_signal": validation_518k.promotion_signal,
        "coverage_metrics": validation_518k.coverage_metrics,
        "drift_metrics": validation_518k.drift_metrics,
        "artifact_record_id": validation_518k.artifact_record_id,
        "artifact_search_backend": validation_518k.artifact_search_backend,
        "boundary": "518k_distribution_evidence_guides_m3_coverage_without_full_corpus_default",
    }


def _domain_action(domain: str, depth_score: float) -> str:
    if depth_score >= 0.7:
        return "watch_with_real_case_replay"
    if domain in {"career", "wealth", "relationship", "health"}:
        return "expand_domain_subfamily_rules_with_source_tags"
    if domain in {"structure_dynamic", "structure_pattern", "useful_god"}:
        return "expand_counter_evidence_and_dynamic_path_tags"
    return "add_source_mapped_krp_or_portrait_units"


def _mapping_keys(value: object) -> set[str]:
    if not isinstance(value, dict):
        return set()
    return {str(key) for key in value if key}


def _flatten_rule_states(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    counts: Counter[str] = Counter()
    for states in value.values():
        rows = states if isinstance(states, list) else [states]
        for state in rows:
            if state:
                counts[str(state)] += 1
    return dict(counts)


def _int_from_mapping(value: object, key: str) -> int:
    if not isinstance(value, dict):
        return 0
    raw = value.get(key, 0)
    return raw if isinstance(raw, int) else 0


def _write_artifact(payload: dict[str, object], artifact_dir: Path) -> Path:
    import json

    artifact_dir.mkdir(parents=True, exist_ok=True)
    created = str(payload.get("created_at") or "").replace(":", "").replace("-", "")
    path = artifact_dir / f"v30.m3.g1.source_governed_calibration.{created}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
