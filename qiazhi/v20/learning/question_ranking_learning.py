from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from v20.api.runtime import run_runtime_from_pillars
from v20.interaction.question_ranker import (
    SHADOW_POLICY_PATH_SUFFIX,
    QuestionRankingPolicy,
    default_question_ranking_policy,
)
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.learning.dynamic_decision_training import (
    DynamicDecisionTrainingCase,
    MANUAL_DECISION_TRAINING_CASES,
)
from v20.decision.questions import QUESTION_KEY_BY_DOMAIN


TOP_K_DEFAULT = 8
MAX_CASE_DEFAULT = 48
MISSING_RANK_PENALTY = TOP_K_DEFAULT + 4


def build_question_ranking_learning_report(
    cases: tuple[DynamicDecisionTrainingCase, ...] | None = None,
    *,
    top_k: int = TOP_K_DEFAULT,
    max_cases: int = MAX_CASE_DEFAULT,
    use_shadow_prefix: bool = True,
    collect_quality_findings: bool = False,
) -> dict[str, object]:
    pool = tuple(cases or MANUAL_DECISION_TRAINING_CASES)
    if not pool:
        return {
            "version": "v20.question_ranking_shadow_training_report.v1",
            "status": "blocked",
            "message": "no_cases_for_training",
            "case_count": 0,
            "runtime_mutation": False,
            "guardrails": ["OFFLINE_LEARNING_ONLY", "NO_RULE_MUTATION"],
        }

    selected_cases = tuple(pool[:max_cases])
    domain_positions: dict[str, list[float]] = {}
    rule_prefix_positions: dict[str, list[float]] = {}
    case_reports: list[dict[str, object]] = []
    quality_findings: list[str] = []

    for case in selected_cases:
        runtime = run_runtime_from_pillars(
            *case.pillar_displays,
            input_id=f"v20.question-ranking.train.{case.case_id}",
            question_key=case.question_key,
            user_text=case.user_text,
            flow_year_pillar=case.flow_year_pillar,
            luck_pillar=case.luck_pillar,
            flow_month_pillar=case.flow_month_pillar,
        )
        questions = tuple(runtime.get("questions", ()))
        question_positions = _question_positions(questions)
        found_keys: list[str] = []
        expected_positions: list[float] = []
        for expected_key in case.expected_question_keys:
            rank = _find_question_rank(question_positions, expected_key)
            if rank is None:
                position = float(top_k + MISSING_RANK_PENALTY)
                if collect_quality_findings and top_k:
                    # keep training report stable while preserving visibility in the detailed case row.
                    quality_findings.append(f"expected_question_not_found:{case.case_id}:{expected_key}")
            else:
                position = float(rank)
                found_keys.append(expected_key)
                expected_positions.append(position)
                domain = QUESTION_KEY_BY_DOMAIN.get(expected_key, "")
                if domain:
                    domain_positions.setdefault(domain, []).append(position)
                source_row = questions[rank - 1]
                rule_key = str(source_row.get("source_rule_key", ""))
                status = str(source_row.get("source_decision_status", "")) or str(source_row.get("status", ""))
                if use_shadow_prefix:
                    prefix = _rule_prefix(rule_key)
                    rule_prefix_positions.setdefault(prefix, []).append(position)
                if status:
                    # weakly reinforce confirmed/strong candidates, discourage noisy review states
                    if status in {"requires_review", "countered", "blocked", "mixed", "volatile"}:
                        # slight penalty
                        pass
        case_reports.append({
            "case_id": case.case_id,
            "found_expected": tuple(found_keys),
            "expected_rank_positions": tuple(expected_positions),
            "found_count": len(found_keys),
            "expected_count": len(case.expected_question_keys),
            "question_count": len(questions),
            "selected_domain": str(runtime.get("selected_question", {}).get("domain", "")),
        })

    if not domain_positions:
        return {
            "version": "v20.question_ranking_shadow_training_report.v1",
            "status": "ready_for_review",
            "message": "no_expected_domain_mapped",
            "case_count": len(selected_cases),
            "runtime_mutation": False,
            "guardrails": ["QUESTION_KEY_MUST_MAP_DOMAIN", "RANKING_SIGNAL_NEEDS_COVERAGE_ENRICHMENT"],
        }

    all_positions = [pos for values in domain_positions.values() for pos in values]
    global_mean = float(mean(all_positions)) if all_positions else float(top_k)

    domain_weights = {
        domain: _clamp((global_mean - mean(positions)) / max(1.0, top_k), -0.12, 0.12)
        for domain, positions in sorted(domain_positions.items())
        if positions
    }
    stage_weights = {}
    status_weights = {
        "confirmed": 0.06,
        "chain_review": 0.04,
        "candidate": 0.02,
        "weak_candidate": 0.0,
        "requires_review": -0.03,
        "countered": -0.04,
        "blocked": -0.06,
    }
    question_key_weights = {}
    rule_prefix_weights = {}
    if use_shadow_prefix and rule_prefix_positions:
        for prefix, positions in sorted(rule_prefix_positions.items()):
            if len(positions) >= 2:
                rule_prefix_weights[prefix] = _clamp((global_mean - mean(positions)) / max(1.0, top_k + 1), -0.08, 0.08)
    for domain, positions in domain_positions.items():
        if len(positions) >= 3:
            for key in _domain_question_keys(domain):
                if key not in question_key_weights:
                    question_key_weights[key] = 0.02

    policy = QuestionRankingPolicy(
        policy_id="v20.question_ranking.shadow.v1",
        domain_weights=domain_weights,
        stage_weights=stage_weights,
        status_weights=status_weights,
        question_key_weights=question_key_weights,
        rule_prefix_weights=rule_prefix_weights,
        feature_count_weight=0.004,
        max_feature_count=6,
        alignment_weight=0.16,
        max_adjustment=0.12,
        source="shadow_candidate",
        status="candidate",
        guardrails=(
            "OFFLINE_GENERATED",
            "NO_RULE_TRUTH_MUTATION",
            "SHADOW_APPLY_REQUIRES_REVIEW",
        ),
    )
    return {
        "version": "v20.question_ranking_shadow_training_report.v1",
        "status": "ready_for_review" if quality_findings else "ready",
        "runtime_mutation": False,
        "message": "question_ranking_shadow_policy_ready",
        "top_k": top_k,
        "case_count": len(selected_cases),
        "quality_finding_count": len(quality_findings),
        "quality_findings": tuple(quality_findings),
        "case_reports": tuple(case_reports),
        "global_mean_position": global_mean,
        "domain_position_stats": {
            domain: round(mean(positions), 3)
            for domain, positions in sorted(domain_positions.items())
            if positions
        },
        "shadow_policy": asdict(policy),
        "runtime_mutation": False,
        "guardrails": [
            "OFFLINE_LEARNING_ONLY",
            "NO_FEATURE_CREATION",
            "SHADOW_POLICY_REQUIRES_REVIEW",
        ],
    }


def write_question_ranking_learning_artifact(
    *,
    cases: tuple[DynamicDecisionTrainingCase, ...] | None = None,
    output_dir: Path | None = None,
    top_k: int = TOP_K_DEFAULT,
    max_cases: int = MAX_CASE_DEFAULT,
) -> dict[str, object]:
    report = build_question_ranking_learning_report(
        cases,
        top_k=top_k,
        max_cases=max_cases,
        collect_quality_findings=True,
    )
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or (runtime_dir / "training" / "question_ranking")
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"question_ranking_training_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.question_ranking_training_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "policy_path": str(latest_path),
        "report_status": report.get("status"),
        "case_count": report.get("case_count", 0),
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "SHADOW_APPLY_REQUIRES_REVIEW",
        ],
    }


def read_question_ranking_learning_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "question_ranking") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.question_ranking_training_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _question_positions(questions: tuple[dict[str, object], ...]) -> dict[str, list[int]]:
    positions: dict[str, list[int]] = {}
    for index, question in enumerate(questions):
        positions.setdefault(str(question.get("question_key", "")), []).append(index + 1)
    return positions


def _find_question_rank(position_map: dict[str, list[int]], question_key: str) -> int | None:
    ranks = position_map.get(question_key, [])
    return min(ranks) if ranks else None


def _rule_prefix(rule_key: str) -> str:
    parts = str(rule_key).split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return str(rule_key)


def _clamp(value: float, min_value: float, max_value: float) -> float:
    if value < min_value:
        return float(min_value)
    if value > max_value:
        return float(max_value)
    return float(value)


def _domain_question_keys(domain: str) -> tuple[str, ...]:
    return tuple(key for key, row_domain in QUESTION_KEY_BY_DOMAIN.items() if row_domain == domain)
