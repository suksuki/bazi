from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from v20.api.runtime import run_runtime_from_pillars
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.validation.golden import GOLDEN_CASES
from v20.validation.rule_synthetic import RULE_SYNTHETIC_CASES, SyntheticRuleCase
from v20.validation.synthetic_schema import SyntheticCase

ProgressCallback = Callable[[str], None]

TECHNICAL_USER_TERMS = (
    "feature.",
    "rule.",
    "decision.",
    "候选路径",
    "裁决",
    "材料",
    "边界",
    "结构通道",
    "触发边界",
    "原局结构",
    "显式时间层",
    "证据门槛",
)

FORBIDDEN_ANSWER_TEXT = ("一定", "必然", "发财", "破财", "疾病", "应期")
FORBIDDEN_INTERNAL_TEXT = (
    "arbitration:",
    "borderline_capacity",
    "supported_capacity",
    "capacity_needs_support",
    "feature.",
    "rule.",
    "decision.",
)
OLD_RUNTIME_FIELDS = (
    "feature_discovery",
    "portrait_projection",
    "portrait_intelligence",
    "rule_candidate_support",
)


@dataclass(frozen=True)
class DynamicDecisionTrainingCase:
    case_id: str
    pillar_displays: tuple[str, str, str, str]
    user_text: str = ""
    question_key: str = ""
    flow_year_pillar: str = ""
    luck_pillar: str = ""
    flow_month_pillar: str = ""
    expected_decision_domains: tuple[str, ...] = ()
    expected_rule_keys: tuple[str, ...] = ()
    expected_portrait_domains: tuple[str, ...] = ()
    expected_question_keys: tuple[str, ...] = ()
    expected_control_keys: tuple[str, ...] = ()
    expected_selected_domains: tuple[str, ...] = ()
    source: str = "manual"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


MANUAL_DECISION_TRAINING_CASES: tuple[DynamicDecisionTrainingCase, ...] = (
    DynamicDecisionTrainingCase(
        case_id="v20.dynamic.training.career_shang_guan_jian_guan",
        pillar_displays=("壬寅", "甲辰", "丙子", "甲午"),
        user_text="我想看事业和财运",
        expected_decision_domains=("career", "ten_god", "strength"),
        expected_rule_keys=("rule.ten_god.shang_guan_jian_guan",),
        expected_portrait_domains=("career", "ten_god", "strength"),
        expected_question_keys=("q_career_structure", "q_hidden_stem_role"),
        expected_control_keys=("control.shang_guan_jian_guan",),
        expected_selected_domains=("career",),
        source="manual_dynamic_decision",
        notes="验证伤官见官从当前盘动态裁决进入画像与推荐问题，而不是从静态画像进入。",
    ),
    DynamicDecisionTrainingCase(
        case_id="v20.dynamic.training.wealth_capacity",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        user_text="我想看财运和收入稳定",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
        expected_decision_domains=("wealth", "time", "strength"),
        expected_rule_keys=("rule.wealth.material", "rule.time.trigger"),
        expected_portrait_domains=("wealth", "time", "strength"),
        expected_question_keys=("q_income_stability", "q_time_layer_context"),
        expected_selected_domains=("wealth",),
        source="manual_dynamic_decision",
        notes="验证财星显现、承载门槛和时间层触发能形成当前盘主线。",
    ),
    DynamicDecisionTrainingCase(
        case_id="v20.dynamic.training.branch_collision",
        pillar_displays=("甲子", "戊辰", "甲午", "辛酉"),
        user_text="我想知道这个盘结构上先看什么",
        expected_decision_domains=("branch", "strength"),
        expected_rule_keys=("rule.branch.relations",),
        expected_portrait_domains=("branch", "strength"),
        expected_question_keys=("q_branch_relation_detail", "q_strength_assessment"),
        expected_selected_domains=("branch", "strength"),
        source="manual_dynamic_decision",
        notes="验证地支互动能进入动态画像和问题入口。",
    ),
)


def default_dynamic_decision_training_cases() -> tuple[DynamicDecisionTrainingCase, ...]:
    rows = [_from_rule_case(row) for row in RULE_SYNTHETIC_CASES]
    rows.extend(_from_golden_case(row) for row in GOLDEN_CASES)
    rows.extend(MANUAL_DECISION_TRAINING_CASES)
    return tuple({row.case_id: row for row in rows}.values())


def run_dynamic_decision_training_batch(
    *,
    cases: tuple[DynamicDecisionTrainingCase, ...] | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    selected_cases = cases or default_dynamic_decision_training_cases()
    _emit(progress, f"dynamic decision cases: {len(selected_cases)}")
    case_results = [
        _evaluate_training_case(case, index=index + 1, total=len(selected_cases), progress=progress)
        for index, case in enumerate(selected_cases)
    ]
    failures = [failure for row in case_results for failure in row["failures"]]
    quality_findings = [finding for row in case_results for finding in row["quality_findings"]]
    return {
        "version": "v20.dynamic_decision_training_batch.v1",
        "status": "pass" if not failures else "fail",
        "quality_status": "needs_review" if quality_findings else "clean",
        "ok": not failures,
        "case_count": len(case_results),
        "failure_count": len(failures),
        "quality_finding_count": len(quality_findings),
        "case_results": case_results,
        "coverage_summary": _coverage_summary(case_results),
        "training_proposals": _training_proposals(case_results),
        "training_targets": (
            "knowledge_base",
            "rule_library",
            "portrait_library",
            "decision_parameters",
            "question_seed_ranking",
        ),
        "runtime_mutation": False,
        "guardrails": [
            "DYNAMIC_DECISION_TRAINING_IS_OFFLINE_ONLY",
            "RUNTIME_PORTRAIT_COMES_FROM_CURRENT_CHART_DECISIONS",
            "FULL_CORPUS_IS_NOT_PORTRAIT_TRUTH",
            "LLM_CAN_EXPLAIN_BUT_NOT_PROMOTE_RULE_TRUTH",
            "NO_POSTGRES_WRITE",
        ],
    }


def write_dynamic_decision_training_artifact(
    *,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    report = run_dynamic_decision_training_batch(progress=progress)
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "dynamic_decision"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"dynamic_decision_training_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.dynamic_decision_training_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "quality_status": report["quality_status"],
        "case_count": report["case_count"],
        "failure_count": report["failure_count"],
        "quality_finding_count": report["quality_finding_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_DECISION_PROMOTION",
        ],
    }


def read_dynamic_decision_training_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "dynamic_decision") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.dynamic_decision_training_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _evaluate_training_case(
    case: DynamicDecisionTrainingCase,
    *,
    index: int,
    total: int,
    progress: ProgressCallback | None,
) -> dict[str, object]:
    _emit(progress, f"evaluate {index}/{total}: {case.case_id}")
    runtime = run_runtime_from_pillars(
        *case.pillar_displays,
        input_id=case.case_id,
        question_key=case.question_key,
        user_text=case.user_text,
        flow_year_pillar=case.flow_year_pillar,
        luck_pillar=case.luck_pillar,
        flow_month_pillar=case.flow_month_pillar,
    )
    decisions = _rows(runtime.get("decision_report", {}).get("decisions", ()))
    hits = _rows(runtime.get("decision_report", {}).get("hits", ()))
    portrait_axes = _rows(runtime.get("decision_report", {}).get("portrait_projection", {}).get("axes", ()))
    questions = _rows(runtime.get("questions", ()))
    controls = _rows(runtime.get("decision_report", {}).get("practitioner_controls", ()))
    answer_text = str(runtime.get("answer_text", ""))

    decision_domains = _values(decisions, "domain")
    portrait_domains = _values(portrait_axes, "domain")
    question_keys = _values(questions, "question_key")
    question_domains = _values(questions, "domain")
    rule_keys = _values(decisions, "rule_key")
    hit_rule_keys = _values(hits, "rule_key")
    control_keys = _values(controls, "control_key")
    selected = runtime.get("selected_question", {})
    selected_domain = str(selected.get("domain", "")) if isinstance(selected, dict) else ""

    failures = []
    failures.extend(_missing("decision_domain", case.case_id, case.expected_decision_domains, decision_domains))
    failures.extend(_missing("rule_key", case.case_id, case.expected_rule_keys, (*rule_keys, *hit_rule_keys)))
    failures.extend(_missing("portrait_domain", case.case_id, case.expected_portrait_domains, portrait_domains))
    failures.extend(_missing("question_key", case.case_id, case.expected_question_keys, question_keys))
    failures.extend(_missing("practitioner_control", case.case_id, case.expected_control_keys, control_keys))
    if case.expected_selected_domains and selected_domain not in set(case.expected_selected_domains):
        failures.append(f"selected_question_domain_mismatch:{case.case_id}:{selected_domain}")
    if not decisions:
        failures.append(f"no_rule_decisions:{case.case_id}")
    if not portrait_axes:
        failures.append(f"no_portrait_projection:{case.case_id}")
    if not questions:
        failures.append(f"no_recommended_questions:{case.case_id}")
    if runtime.get("decision_validation", {}).get("ok") is not True:
        failures.append(f"decision_validation_failed:{case.case_id}")
    if selected_domain and selected_domain not in (*decision_domains, *question_domains):
        failures.append(f"selected_question_not_decision_aligned:{case.case_id}:{selected_domain}")
    for text in FORBIDDEN_ANSWER_TEXT:
        if text and text in answer_text:
            failures.append(f"forbidden_answer_text:{case.case_id}:{text}")
    for text in FORBIDDEN_INTERNAL_TEXT:
        if text and text in answer_text:
            failures.append(f"internal_answer_text_leak:{case.case_id}:{text}")
    for field in OLD_RUNTIME_FIELDS:
        if field in runtime:
            failures.append(f"old_runtime_field_present:{case.case_id}:{field}")

    quality_findings = []
    quality_findings.extend(_question_language_findings(case.case_id, questions))
    quality_findings.extend(_portrait_language_findings(case.case_id, portrait_axes))
    quality_findings.extend(_domain_alignment_findings(case.case_id, decision_domains, portrait_domains, question_domains))

    return {
        "version": "v20.dynamic_decision_training_case_result.v1",
        "case_id": case.case_id,
        "source": case.source,
        "ok": not failures,
        "status": "pass" if not failures else "fail",
        "quality_status": "needs_review" if quality_findings else "clean",
        "failures": failures,
        "quality_findings": quality_findings,
        "pillar_displays": case.pillar_displays,
        "selected_question_key": str(selected.get("question_key", "")) if isinstance(selected, dict) else "",
        "selected_question_title": str(selected.get("title", "")) if isinstance(selected, dict) else "",
        "decision_domains": decision_domains,
        "decision_keys": _values(decisions, "decision_key"),
        "rule_keys": tuple(dict.fromkeys((*rule_keys, *hit_rule_keys))),
        "portrait_domains": portrait_domains,
        "portrait_labels": _values(portrait_axes, "label"),
        "question_keys": question_keys,
        "question_titles": _values(questions, "title"),
        "question_domains": question_domains,
        "practitioner_control_keys": control_keys,
        "decision_count": len(decisions),
        "hit_count": len(hits),
        "portrait_axis_count": len(portrait_axes),
        "question_count": len(questions),
        "runtime_mutation": False,
        "notes": case.notes,
    }


def _coverage_summary(case_results: list[dict[str, object]]) -> dict[str, object]:
    return {
        "version": "v20.dynamic_decision_training_coverage.v1",
        "decision_domains": _sorted_union(case_results, "decision_domains"),
        "rule_keys": _sorted_union(case_results, "rule_keys"),
        "portrait_domains": _sorted_union(case_results, "portrait_domains"),
        "question_keys": _sorted_union(case_results, "question_keys"),
        "practitioner_control_keys": _sorted_union(case_results, "practitioner_control_keys"),
        "passing_case_count": sum(1 for row in case_results if row.get("ok") is True),
        "cases_needing_language_review": sum(1 for row in case_results if row.get("quality_status") == "needs_review"),
        "runtime_mutation": False,
    }


def _training_proposals(case_results: list[dict[str, object]]) -> list[dict[str, object]]:
    proposals: list[dict[str, object]] = []
    for row in case_results:
        case_id = str(row.get("case_id", ""))
        for failure in row.get("failures", ()):
            text = str(failure)
            proposals.append({
                "case_id": case_id,
                "target": _proposal_target(text),
                "issue": text,
                "action": _proposal_action(text),
                "runtime_allowed": True,
            })
        for finding in row.get("quality_findings", ()):
            text = str(finding)
            proposals.append({
                "case_id": case_id,
                "target": _proposal_target(text),
                "issue": text,
                "action": _proposal_action(text),
                "runtime_allowed": True,
            })
    return proposals


def _proposal_target(issue: str) -> str:
    if "question" in issue:
        return "question_seed_ranking"
    if "portrait" in issue:
        return "portrait_library"
    if "rule_key" in issue or "decision_domain" in issue or "rule_decisions" in issue:
        return "decision_parameters"
    if "forbidden_answer_text" in issue:
        return "llm_answer_guardrail"
    return "rule_library"


def _proposal_action(issue: str) -> str:
    if "technical_language" in issue:
        return "rewrite_user_visible_question_or_portrait_label"
    if "missing_expected_question" in issue:
        return "add_or_boost_question_seed_for_matching_decision"
    if "missing_expected_portrait_domain" in issue:
        return "add_portrait_projection_mapping_for_decision_domain"
    if "missing_expected_rule_key" in issue:
        return "add_synthetic_counterexample_or_rule_atom_for_current_chart"
    if "missing_expected_decision_domain" in issue:
        return "calibrate_decision_domain_weight_and_trigger"
    if "forbidden_answer_text" in issue:
        return "tighten_answer_text_guard"
    return "review_offline_then_promote_through_synthetic_gate"


def _question_language_findings(case_id: str, questions: list[dict[str, object]]) -> list[str]:
    findings = []
    for row in questions:
        title = str(row.get("title", ""))
        if any(term in title for term in TECHNICAL_USER_TERMS):
            findings.append(f"question_technical_language:{case_id}:{row.get('question_key', '')}:{title}")
    return findings


def _portrait_language_findings(case_id: str, portrait_tags: list[dict[str, object]]) -> list[str]:
    findings = []
    for row in portrait_tags:
        label = str(row.get("label", ""))
        summary = str(row.get("summary", ""))
        if any(term in label or term in summary for term in TECHNICAL_USER_TERMS[:3]):
            findings.append(f"portrait_technical_language:{case_id}:{row.get('tag_key', '')}:{label}")
    return findings


def _domain_alignment_findings(
    case_id: str,
    decision_domains: tuple[str, ...],
    portrait_domains: tuple[str, ...],
    question_domains: tuple[str, ...],
) -> list[str]:
    findings = []
    if not set(portrait_domains) & set(decision_domains):
        findings.append(f"portrait_not_decision_domain_aligned:{case_id}")
    if not set(question_domains) & set(decision_domains):
        findings.append(f"question_not_decision_domain_aligned:{case_id}")
    return findings


def _from_rule_case(case: SyntheticRuleCase) -> DynamicDecisionTrainingCase:
    return DynamicDecisionTrainingCase(
        case_id=f"{case.case_id}.dynamic",
        pillar_displays=case.pillar_displays,
        question_key=case.question_key,
        flow_year_pillar=case.flow_year_pillar,
        luck_pillar=case.luck_pillar,
        flow_month_pillar=case.flow_month_pillar,
        expected_decision_domains=case.expected_rule_domains,
        expected_portrait_domains=case.expected_rule_domains,
        expected_question_keys=case.expected_question_keys,
        source="rule_synthetic",
        notes=case.notes,
    )


def _from_golden_case(case: SyntheticCase) -> DynamicDecisionTrainingCase:
    return DynamicDecisionTrainingCase(
        case_id=f"{case.case_id}.dynamic",
        pillar_displays=case.pillar_displays,
        expected_decision_domains=case.expected_rule_candidate_domains,
        expected_portrait_domains=case.expected_rule_candidate_domains,
        expected_question_keys=case.expected_question_keys,
        source="golden",
    )


def _rows(value: object) -> list[dict[str, object]]:
    if isinstance(value, list | tuple):
        return [row for row in value if isinstance(row, dict)]
    return []


def _values(rows: list[dict[str, object]], key: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(row.get(key, "")) for row in rows if row.get(key)))


def _missing(kind: str, case_id: str, expected: tuple[str, ...], actual: tuple[str, ...]) -> list[str]:
    actual_set = set(actual)
    return [f"missing_expected_{kind}:{case_id}:{item}" for item in expected if item not in actual_set]


def _sorted_union(rows: list[dict[str, object]], key: str) -> tuple[str, ...]:
    values = {
        str(item)
        for row in rows
        for item in row.get(key, ())
        if str(item)
    }
    return tuple(sorted(values))


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
