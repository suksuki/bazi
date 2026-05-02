from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from v20.api.runtime import run_runtime_from_pillars
from v20.knowledge.rule_extraction import build_rule_extraction_report, validate_rule_extraction_report
from v20.measurement.domain_alignment import ALLOWED_BAZI_DOMAINS, is_allowed_bazi_domain
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.validation.golden import GOLDEN_CASES
from v20.validation.rule_synthetic import RULE_SYNTHETIC_CASES, SyntheticRuleCase
from v20.validation.synthetic_schema import SyntheticCase

ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class RulePortraitBatchCase:
    case_id: str
    pillar_displays: tuple[str, str, str, str]
    question_key: str = ""
    flow_year_pillar: str = ""
    luck_pillar: str = ""
    flow_month_pillar: str = ""
    expected_feature_domains: tuple[str, ...] = ()
    expected_question_keys: tuple[str, ...] = ()
    expected_rule_domains: tuple[str, ...] = ()
    source: str = "manual"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


REPRESENTATIVE_BATCH_CASES: tuple[RulePortraitBatchCase, ...] = (
    RulePortraitBatchCase(
        case_id="v20.batch.representative.wealth_time",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        question_key="q_income_stability",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
        expected_feature_domains=("wealth", "ten_god", "time", "strength"),
        expected_question_keys=("q_income_stability", "q_time_layer_context"),
        expected_rule_domains=("wealth", "ten_god"),
        source="representative",
    ),
    RulePortraitBatchCase(
        case_id="v20.batch.representative.element_useful_god",
        pillar_displays=("壬寅", "甲辰", "丙子", "甲午"),
        question_key="q_element_balance",
        expected_feature_domains=("element", "useful_god", "ten_god", "strength"),
        expected_question_keys=("q_element_balance", "q_useful_god_candidates"),
        expected_rule_domains=("element",),
        source="representative",
    ),
)


def default_rule_portrait_batch_cases() -> tuple[RulePortraitBatchCase, ...]:
    rows = [_from_rule_case(row) for row in RULE_SYNTHETIC_CASES]
    rows.extend(_from_golden_case(row) for row in GOLDEN_CASES)
    rows.extend(REPRESENTATIVE_BATCH_CASES)
    by_id = {row.case_id: row for row in rows}
    return tuple(by_id.values())


def run_rule_portrait_batch(
    *,
    cases: tuple[RulePortraitBatchCase, ...] | None = None,
    domains: tuple[str, ...] = ALLOWED_BAZI_DOMAINS,
    domain_limit: int = 4,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    selected_cases = cases or default_rule_portrait_batch_cases()
    selected_domains = tuple(domain for domain in domains if is_allowed_bazi_domain(domain))
    _emit(progress, f"rule domains: {len(selected_domains)}")
    rule_rows = [_rule_domain_generation(domain, domain_limit=domain_limit, progress=progress) for domain in selected_domains]
    _emit(progress, f"runtime cases: {len(selected_cases)}")
    case_rows = [
        _evaluate_batch_case(case, index=index + 1, total=len(selected_cases), progress=progress)
        for index, case in enumerate(selected_cases)
    ]
    failures = [
        failure
        for row in (*rule_rows, *case_rows)
        for failure in row.get("failures", ())
        if isinstance(failure, str)
    ]
    return {
        "version": "v20.rule_portrait_batch_report.v1",
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "domain_count": len(rule_rows),
        "case_count": len(case_rows),
        "failure_count": len(failures),
        "rule_generation": rule_rows,
        "case_results": case_rows,
        "coverage_summary": _coverage_summary(rule_rows, case_rows),
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "BATCH_GENERATION_AND_VALIDATION_ONLY",
            "RULE_EXTRACTION_FEEDS_ACTIVE_RUNTIME",
            "PORTRAITS_COME_FROM_RUNTIME_RULE_DECISIONS",
            "QUESTIONS_REQUIRE_BAZI_DOMAIN_ALIGNMENT",
            "NO_POSTGRES_WRITE",
            "RUNTIME_RULES_ACTIVE_WITH_TRACE",
        ],
    }


def write_rule_portrait_batch_artifact(
    *,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    report = run_rule_portrait_batch(progress=progress)
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "rule_portrait_batch"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"rule_portrait_batch_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.rule_portrait_batch_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "domain_count": report["domain_count"],
        "case_count": report["case_count"],
        "failure_count": report["failure_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RULE_OR_PORTRAIT_PROMOTION",
        ],
    }


def read_rule_portrait_batch_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "rule_portrait_batch") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.rule_portrait_batch_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _rule_domain_generation(domain: str, *, domain_limit: int, progress: ProgressCallback | None) -> dict[str, object]:
    _emit(progress, f"generate rules: {domain}")
    report = build_rule_extraction_report(domain, limit=domain_limit)
    validation = validate_rule_extraction_report(domain, limit=domain_limit)
    candidates = [row for row in report.get("candidates", ()) if isinstance(row, dict)]
    failures = []
    if validation.get("ok") is not True:
        failures.extend(str(row) for row in validation.get("failures", ()) if str(row))
    for candidate in candidates:
        rule_id = str(candidate.get("rule_id", ""))
        alignment = candidate.get("bazi_alignment", {})
        if not isinstance(alignment, dict) or alignment.get("ok") is not True:
            failures.append(f"rule_candidate_alignment_failed:{rule_id}")
        if candidate.get("runtime_allowed") is not True:
            failures.append(f"rule_candidate_runtime_blocked:{rule_id}")
    return {
        "version": "v20.rule_generation_batch_domain.v1",
        "domain": domain,
        "status": "pass" if not failures else "fail",
        "ok": not failures,
        "candidate_count": len(candidates),
        "atom_count": report.get("atom_count", 0),
        "aligned_candidate_count": sum(
            1
            for candidate in candidates
            if isinstance(candidate.get("bazi_alignment"), dict) and candidate["bazi_alignment"].get("ok") is True
        ),
        "validation_status": validation.get("status", ""),
        "failures": failures,
        "runtime_mutation": False,
    }


def _evaluate_batch_case(
    case: RulePortraitBatchCase,
    *,
    index: int,
    total: int,
    progress: ProgressCallback | None,
) -> dict[str, object]:
    _emit(progress, f"validate case {index}/{total}: {case.case_id}")
    runtime = run_runtime_from_pillars(
        *case.pillar_displays,
        input_id=case.case_id,
        question_key=case.question_key,
        flow_year_pillar=case.flow_year_pillar,
        luck_pillar=case.luck_pillar,
        flow_month_pillar=case.flow_month_pillar,
    )
    features = [row for row in runtime.get("feature_layer", {}).get("features", ()) if isinstance(row, dict)]
    questions = [row for row in runtime.get("questions", ()) if isinstance(row, dict)]
    decisions = [
        row for row in runtime.get("decision_report", {}).get("decisions", ()) if isinstance(row, dict)
    ]
    portrait_axes = [
        row
        for row in runtime.get("decision_report", {}).get("portrait_projection", {}).get("axes", ())
        if isinstance(row, dict)
    ]
    feature_domains = tuple(sorted({str(row.get("domain", "")) for row in features if row.get("domain")}))
    question_keys = tuple(str(row.get("question_key", "")) for row in questions if row.get("question_key"))
    rule_domains = _decision_domains(decisions)
    portrait_domains = tuple(dict.fromkeys(
        str(row.get("domain", ""))
        for row in portrait_axes
        if row.get("domain")
    ))
    failures = []
    failures.extend(_missing("feature_domain", case.case_id, case.expected_feature_domains, feature_domains))
    failures.extend(_missing("question_key", case.case_id, case.expected_question_keys, question_keys))
    failures.extend(_missing("rule_domain", case.case_id, case.expected_rule_domains, rule_domains))
    if not questions:
        failures.append(f"no_questions:{case.case_id}")
    if not portrait_axes:
        failures.append(f"no_portrait_projection_axes:{case.case_id}")
    if not decisions:
        failures.append(f"no_rule_decisions:{case.case_id}")
    failures.extend(_alignment_failures("question", case.case_id, questions, "alignment_status"))
    if runtime.get("decision_validation", {}).get("ok") is not True:
        failures.append(f"decision_validation_failed:{case.case_id}")
    return {
        "version": "v20.rule_portrait_batch_case_result.v1",
        "case_id": case.case_id,
        "source": case.source,
        "ok": not failures,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "pillar_displays": case.pillar_displays,
        "selected_question_key": runtime.get("selected_question", {}).get("question_key", ""),
        "feature_domains": feature_domains,
        "question_keys": question_keys[:16],
        "question_alignment_statuses": tuple(
            dict.fromkeys(str(row.get("alignment_status", "")) for row in questions if row.get("alignment_status"))
        ),
        "portrait_domains": portrait_domains,
        "decision_domains": rule_domains,
        "decision_statuses": tuple(dict.fromkeys(str(row.get("status", "")) for row in decisions if row.get("status"))),
        "feature_count": len(features),
        "question_count": len(questions),
        "portrait_axis_count": len(portrait_axes),
        "decision_count": len(decisions),
        "runtime_mutation": False,
    }


def _coverage_summary(rule_rows: list[dict[str, object]], case_rows: list[dict[str, object]]) -> dict[str, object]:
    rule_domains = sorted(str(row.get("domain", "")) for row in rule_rows if row.get("domain"))
    portrait_domains = sorted(
        {
            str(domain)
            for row in case_rows
            for domain in row.get("portrait_domains", ())
            if str(domain)
        }
    )
    question_domains = sorted(
        {
            str(domain)
            for row in case_rows
            for domain in row.get("feature_domains", ())
            if str(domain)
        }
    )
    return {
        "version": "v20.rule_portrait_batch_coverage.v1",
        "rule_domains": rule_domains,
        "portrait_domains": portrait_domains,
        "feature_domains_seen": question_domains,
        "decision_domains_seen": sorted(
            {
                str(domain)
                for row in case_rows
                for domain in row.get("decision_domains", ())
                if str(domain)
            }
        ),
        "aligned_rule_domain_count": sum(1 for row in rule_rows if row.get("ok") is True),
        "passing_case_count": sum(1 for row in case_rows if row.get("ok") is True),
        "runtime_mutation": False,
    }


def _from_rule_case(case: SyntheticRuleCase) -> RulePortraitBatchCase:
    return RulePortraitBatchCase(
        case_id=f"{case.case_id}.batch",
        pillar_displays=case.pillar_displays,
        question_key=case.question_key,
        flow_year_pillar=case.flow_year_pillar,
        luck_pillar=case.luck_pillar,
        flow_month_pillar=case.flow_month_pillar,
        expected_question_keys=case.expected_question_keys,
        expected_rule_domains=case.expected_rule_domains,
        source="rule_synthetic",
    )


def _from_golden_case(case: SyntheticCase) -> RulePortraitBatchCase:
    return RulePortraitBatchCase(
        case_id=f"{case.case_id}.batch",
        pillar_displays=case.pillar_displays,
        expected_feature_domains=case.expected_feature_domains,
        expected_question_keys=case.expected_question_keys,
        expected_rule_domains=case.expected_rule_candidate_domains,
        source="golden",
    )


def _missing(kind: str, case_id: str, expected: tuple[str, ...], actual: tuple[str, ...]) -> list[str]:
    actual_set = set(actual)
    return [f"missing_expected_{kind}:{case_id}:{item}" for item in expected if item not in actual_set]


def _alignment_failures(
    kind: str,
    case_id: str,
    rows: list[dict[str, object]],
    key: str,
    *,
    allow_missing: bool = False,
) -> list[str]:
    failures = []
    for row in rows:
        status = str(row.get(key, ""))
        if allow_missing and not status:
            continue
        if status not in {"bazi_core_aligned", "bazi_projection_aligned"}:
            row_id = str(row.get("question_key") or row.get("axis_id") or row.get("domain") or "")
            failures.append(f"{kind}_alignment_failed:{case_id}:{row_id}:{status}")
    return failures


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)


def _decision_domains(rows: list[dict[str, object]]) -> tuple[str, ...]:
    domains: list[str] = []
    for row in rows:
        domains.append(str(row.get("domain", "")))
        rule_key = str(row.get("rule_key", ""))
        for marker, domain in (
            (".ten_god.", "ten_god"),
            (".wealth.", "wealth"),
            (".strength.", "strength"),
            (".branch.", "branch"),
            (".time.", "time"),
            (".element.", "element"),
            (".useful_god.", "useful_god"),
            (".pattern.", "pattern"),
        ):
            if marker in rule_key:
                domains.append(domain)
    return tuple(dict.fromkeys(domain for domain in domains if domain))
