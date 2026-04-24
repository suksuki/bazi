from __future__ import annotations

import math
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from v17_rebirth.backend.logic.plugin_discovery import iter_all_plugin_specs
from v17_rebirth.backend.services.plugin_governance import classify_plugin_governance
from v17_rebirth.testing.auto_learning_loop import run_auto_learning_cycle
from v17_rebirth.testing.parameter_candidate_runner import build_parameter_experiments_from_report
from v17_rebirth.testing.practitioner_benchmarks import (
    PRACTITIONER_BENCHMARK_CASES,
    practitioner_dynamic_families,
    practitioner_relation_families,
    run_practitioner_case,
)
from v17_rebirth.testing.synthetic_batch_lab import DEFAULT_SYNTHETIC_BATCH_CASES, build_synthetic_batch_report
from v17_rebirth.testing.synthetic_lab import (
    SYNTHETIC_AUTHORITY_CASES,
    SYNTHETIC_CASES,
    SYNTHETIC_CORE_CASES,
    SYNTHETIC_PATTERN_CASES,
    SYNTHETIC_RISK_CASES,
    pattern_case_fact,
    pattern_fact,
    run_authority_case,
    run_case,
    run_core_case,
    run_pattern_case,
    run_risk_case,
)


LEARNING_CAMPAIGN_VERSION = "v17.learning_campaign.v1"
DEFAULT_LEARNING_BUDGET_SECONDS = 3 * 60 * 60


@dataclass(frozen=True)
class LearningCampaignConfig:
    max_duration_seconds: int = DEFAULT_LEARNING_BUDGET_SECONDS
    include_extended_synthetic: bool = True
    include_practitioner_benchmarks: bool = True
    include_auto_learning_loop: bool = True
    request_llm_review: bool = False
    max_extended_cases: int | None = None


@dataclass(frozen=True)
class LearningFinding:
    source: str
    case_id: str
    severity: str
    message: str
    parameter_family: str
    reviewer: str = "codex"
    needs_analyst_feedback: bool = False
    needs_llm_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "case_id": self.case_id,
            "severity": self.severity,
            "message": self.message,
            "parameter_family": self.parameter_family,
            "reviewer": self.reviewer,
            "needs_analyst_feedback": bool(self.needs_analyst_feedback),
            "needs_llm_review": bool(self.needs_llm_review),
        }


ProgressCallback = Callable[[dict[str, Any]], None]
StopPredicate = Callable[[], bool]


def run_learning_campaign(
    config: LearningCampaignConfig | None = None,
    *,
    progress_callback: ProgressCallback | None = None,
    should_stop: StopPredicate | None = None,
) -> dict[str, Any]:
    config = config or LearningCampaignConfig()
    started = time.monotonic()
    findings: list[LearningFinding] = []
    interrupted = False

    _emit_progress(progress_callback, "plugin_governance", "插件治理覆盖", 8, started, config)
    governance = build_plugin_governance_coverage()
    if _should_stop(should_stop):
        interrupted = True

    _emit_progress(progress_callback, "synthetic_batch", "批量合成样盘", 22, started, config)
    batch_report = build_synthetic_batch_report(DEFAULT_SYNTHETIC_BATCH_CASES)
    findings.extend(_findings_from_batch_report(batch_report))

    extended_report = {"state": "skipped", "case_count": 0, "passed_count": 0, "failed_count": 0, "findings": []}
    if config.include_extended_synthetic and not interrupted and not _budget_exceeded(started, config):
        _emit_progress(progress_callback, "extended_synthetic", "完整 Synthetic Lab", 42, started, config)
        extended_report = audit_extended_synthetic_catalog(max_cases=config.max_extended_cases)
        findings.extend(_findings_from_dicts(extended_report.get("findings")))
        interrupted = _should_stop(should_stop)

    practitioner_report = {"state": "skipped", "case_count": 0, "passed_count": 0, "failed_count": 0, "findings": []}
    if config.include_practitioner_benchmarks and not interrupted and not _budget_exceeded(started, config):
        _emit_progress(progress_callback, "practitioner_benchmark", "真实命盘 Benchmark", 62, started, config)
        practitioner_report = audit_practitioner_benchmarks()
        findings.extend(_findings_from_dicts(practitioner_report.get("findings")))
        interrupted = _should_stop(should_stop)

    auto_loop = {"state": "skipped"}
    if config.include_auto_learning_loop and not interrupted and not _budget_exceeded(started, config):
        _emit_progress(progress_callback, "auto_learning_loop", "影子调参与反馈包", 78, started, config)
        auto_loop = run_auto_learning_cycle()
        findings.extend(_findings_from_auto_loop(auto_loop))
        interrupted = _should_stop(should_stop)

    _emit_progress(progress_callback, "scorecard", "汇总报告", 92, started, config)
    parameter_family_counts = Counter(
        finding.parameter_family
        for finding in findings
        if finding.parameter_family and finding.parameter_family != "none"
    )
    experiment_report = {
        "protocol": "v17.learning_campaign.parameter_review.v1",
        "parameter_family_counts": dict(parameter_family_counts),
        "audits": [
            {"case_id": finding.case_id, "source": finding.source}
            for finding in findings
        ],
    }
    parameter_experiments = build_parameter_experiments_from_report(experiment_report)
    scorecard = _scorecard(
        batch_report=batch_report,
        extended_report=extended_report,
        practitioner_report=practitioner_report,
        findings=findings,
        parameter_experiment_count=len(parameter_experiments),
        interrupted=interrupted,
    )
    llm_review_package = _llm_review_package(
        findings=findings,
        parameter_experiments=parameter_experiments,
        requested=bool(config.request_llm_review),
    )
    learning_insights = build_learning_insights(
        extended_report=extended_report,
        practitioner_report=practitioner_report,
        batch_report=batch_report,
        findings=findings,
        parameter_experiments=parameter_experiments,
    )
    elapsed = time.monotonic() - started

    report = {
        "protocol": LEARNING_CAMPAIGN_VERSION,
        "primary_reviewer": "codex",
        "secondary_reviewer": "analyst",
        "config": {
            "max_duration_seconds": int(config.max_duration_seconds),
            "include_extended_synthetic": bool(config.include_extended_synthetic),
            "include_practitioner_benchmarks": bool(config.include_practitioner_benchmarks),
            "include_auto_learning_loop": bool(config.include_auto_learning_loop),
            "request_llm_review": bool(config.request_llm_review),
            "max_extended_cases": config.max_extended_cases,
        },
        "budget": {
            "max_duration_seconds": int(config.max_duration_seconds),
            "elapsed_seconds": round(float(elapsed), 4),
            "within_budget": bool(elapsed <= max(1, int(config.max_duration_seconds))),
            "target_window": "under_3_hours",
        },
        "interrupted": bool(interrupted),
        "scorecard": scorecard,
        "plugin_governance_coverage": governance,
        "synthetic_batch": _compact_batch_report(batch_report),
        "extended_synthetic": extended_report,
        "practitioner_benchmarks": practitioner_report,
        "auto_learning_loop": auto_loop,
        "learning_insights": learning_insights,
        "parameter_family_counts": dict(parameter_family_counts),
        "parameter_experiments": parameter_experiments,
        "analyst_feedback_items": [
            finding.to_dict()
            for finding in findings
            if finding.needs_analyst_feedback
        ],
        "llm_review_package": llm_review_package,
        "findings": [finding.to_dict() for finding in findings],
        "can_auto_apply": False,
        "safety_gates": (
            "sandbox_only",
            "do_not_write_real_config",
            "codex_primary_review_required",
            "analyst_review_for_uncertain_or_conflicting_cases",
            "manual_approval_required_before_apply",
        ),
    }
    _emit_progress(progress_callback, "completed", "完成", 100, started, config)
    return report


def build_plugin_governance_coverage() -> dict[str, Any]:
    profiles: list[dict[str, Any]] = []
    for spec in iter_all_plugin_specs():
        profiles.append(
            classify_plugin_governance(
                plugin_id=str(spec.plugin_id),
                causal_tier=int(getattr(spec, "causal_tier", 3) or 3),
            )
        )
    governance_counts = Counter(str(row.get("governance_class") or "unknown") for row in profiles)
    authority_counts = Counter(str(row.get("authority_level") or "unknown") for row in profiles)
    learning_counts = Counter(str(row.get("learning_family") or "unknown") for row in profiles)
    unclassified = [
        str(row.get("plugin_id") or "")
        for row in profiles
        if str(row.get("governance_class") or "") in {"general_fact_plugin", "unknown"}
    ]
    return {
        "protocol": "v17.learning_campaign.plugin_governance_coverage.v1",
        "plugin_count": len(profiles),
        "governance_class_counts": dict(sorted(governance_counts.items())),
        "authority_level_counts": dict(sorted(authority_counts.items())),
        "learning_family_counts": dict(sorted(learning_counts.items())),
        "unclassified_count": len(unclassified),
        "unclassified_plugin_ids": unclassified[:32],
    }


def audit_extended_synthetic_catalog(max_cases: int | None = None) -> dict[str, Any]:
    findings: list[LearningFinding] = []
    signals: list[dict[str, Any]] = []
    relation_counter: Counter[str] = Counter()
    dynamic_counter: Counter[str] = Counter()
    climate_buckets: Counter[str] = Counter()
    base_cases = list(SYNTHETIC_CASES)
    if max_cases is not None:
        base_cases = base_cases[: max(0, int(max_cases))]
    passed = 0
    for case in base_cases:
        before = len(findings)
        try:
            run = run_case(case)
        except Exception as exc:
            findings.append(
                LearningFinding(
                    source="synthetic_catalog",
                    case_id=case.case_id,
                    severity="P0",
                    message=f"runtime crash: {exc}",
                    parameter_family="runtime.stability",
                    needs_analyst_feedback=True,
                )
            )
            continue
        _audit_basic_run(case.case_id, run.total, run.top, findings)
        relation_families = {
            str(row.get("family_key") or "")
            for row in (run.meta.get("relation_formation_summary") or [])
            if isinstance(row, dict)
        }
        dynamic_families = {
            str(row.get("family_key") or "")
            for row in (run.meta.get("relation_dynamics_summary") or [])
            if isinstance(row, dict)
        }
        climate_field = run.meta.get("climate_field") if isinstance(run.meta.get("climate_field"), dict) else {}
        climate_label = _climate_label(climate_field)
        relation_counter.update(family for family in relation_families if family)
        dynamic_counter.update(family for family in dynamic_families if family)
        if climate_label:
            climate_buckets[climate_label] += 1
        signals.append(
            {
                "case_id": case.case_id,
                "layer": case.layer,
                "tags": list(case.tags),
                "top": list(run.top[:4]),
                "total": round(float(run.total or 0.0), 3),
                "relation_families": sorted(relation_families),
                "dynamic_families": sorted(dynamic_families),
                "climate_label": climate_label,
            }
        )
        for family_key in case.expected_relation_families:
            if family_key not in relation_families:
                findings.append(
                    LearningFinding(
                        source="synthetic_catalog",
                        case_id=case.case_id,
                        severity="P1",
                        message=f"missing expected relation family: {family_key}",
                        parameter_family=f"relation_formation.{family_key}",
                    )
                )
        for family_key in case.expected_dynamic_families:
            if family_key not in dynamic_families:
                findings.append(
                    LearningFinding(
                        source="synthetic_catalog",
                        case_id=case.case_id,
                        severity="P1",
                        message=f"missing expected dynamic family: {family_key}",
                        parameter_family=f"relation_dynamics.{family_key}",
                    )
                )
        if not isinstance(run.meta.get("climate_field"), dict):
            findings.append(
                LearningFinding(
                    source="synthetic_catalog",
                    case_id=case.case_id,
                    severity="P2",
                    message="missing climate field metadata",
                    parameter_family="climate_field",
                )
            )
        if len(findings) == before:
            passed += 1

    risk_summary = _audit_risk_cases(findings)
    authority_summary = _audit_authority_cases(findings)
    pattern_summary = _audit_pattern_cases(findings)
    core_summary = _audit_core_cases(findings)
    case_count = len(base_cases) + risk_summary["case_count"] + authority_summary["case_count"] + pattern_summary["case_count"] + core_summary["case_count"]
    failed_case_ids = {finding.case_id for finding in findings}
    return {
        "protocol": "v17.learning_campaign.extended_synthetic_audit.v1",
        "state": "green" if not findings else "needs_review",
        "case_count": case_count,
        "passed_count": max(0, case_count - len(failed_case_ids)),
        "failed_count": len(failed_case_ids),
        "catalog_groups": {
            "base": len(base_cases),
            "risk": risk_summary["case_count"],
            "authority": authority_summary["case_count"],
            "pattern": pattern_summary["case_count"],
            "core": core_summary["case_count"],
        },
        "signals": signals[:64],
        "relation_family_counts": dict(sorted(relation_counter.items())),
        "dynamic_family_counts": dict(sorted(dynamic_counter.items())),
        "climate_bucket_counts": dict(sorted(climate_buckets.items())),
        "topic_signal_counts": {
            "risk_patterns": risk_summary.get("signal_count", 0),
            "authority_routes": authority_summary.get("signal_count", 0),
            "pattern_routes": pattern_summary.get("signal_count", 0),
            "core_routes": core_summary.get("signal_count", 0),
        },
        "findings": [finding.to_dict() for finding in findings],
    }


def audit_practitioner_benchmarks() -> dict[str, Any]:
    findings: list[LearningFinding] = []
    signals: list[dict[str, Any]] = []
    passed = 0
    for case in PRACTITIONER_BENCHMARK_CASES:
        before = len(findings)
        try:
            run = run_practitioner_case(case)
        except Exception as exc:
            findings.append(
                LearningFinding(
                    source="practitioner_benchmark",
                    case_id=case.case_id,
                    severity="P0",
                    message=f"runtime crash: {exc}",
                    parameter_family="runtime.stability",
                    needs_analyst_feedback=True,
                )
            )
            continue
        _audit_basic_run(case.case_id, run.total, run.top, findings, source="practitioner_benchmark")
        relation_families = practitioner_relation_families(run)
        dynamic_families = practitioner_dynamic_families(run)
        signals.append(
            {
                "case_id": case.case_id,
                "description": case.description,
                "audit_focus": list(case.audit_focus),
                "expected_leader": case.expected_leader,
                "top": list(run.top[:6]),
                "relation_families": sorted(relation_families),
                "dynamic_families": sorted(dynamic_families),
                "reviewer_note": case.reviewer_note,
            }
        )
        for family_key in case.expected_relation_families:
            if family_key not in relation_families:
                findings.append(
                    LearningFinding(
                        source="practitioner_benchmark",
                        case_id=case.case_id,
                        severity="P1",
                        message=f"missing expected relation family: {family_key}",
                        parameter_family=f"relation_formation.{family_key}",
                    )
                )
        for family_key in case.expected_dynamic_families:
            if family_key not in dynamic_families:
                findings.append(
                    LearningFinding(
                        source="practitioner_benchmark",
                        case_id=case.case_id,
                        severity="P1",
                        message=f"missing expected dynamic family: {family_key}",
                        parameter_family=f"relation_dynamics.{family_key}",
                    )
                )
        for family_key in case.forbidden_relation_families:
            if family_key in relation_families or family_key in dynamic_families:
                findings.append(
                    LearningFinding(
                        source="practitioner_benchmark",
                        case_id=case.case_id,
                        severity="P1",
                        message=f"forbidden family present: {family_key}",
                        parameter_family=f"relation_gate.{family_key}",
                        needs_analyst_feedback=True,
                    )
                )
        for god in case.expected_top_contains:
            if god not in run.top:
                findings.append(
                    LearningFinding(
                        source="practitioner_benchmark",
                        case_id=case.case_id,
                        severity="P1",
                        message=f"expected top axis missing: {god}",
                        parameter_family="authority.leader_axis",
                    )
                )
        if case.expected_leader and (not run.top or run.top[0] != case.expected_leader):
            findings.append(
                LearningFinding(
                    source="practitioner_benchmark",
                    case_id=case.case_id,
                    severity="P1",
                    message=f"leader mismatch: expected {case.expected_leader}, got {run.top[0] if run.top else '—'}",
                    parameter_family="authority.leader_axis",
                )
            )
        if len(findings) == before:
            passed += 1
    return {
        "protocol": "v17.learning_campaign.practitioner_audit.v1",
        "state": "green" if not findings else "needs_review",
        "case_count": len(PRACTITIONER_BENCHMARK_CASES),
        "passed_count": passed,
        "failed_count": len({finding.case_id for finding in findings}),
        "signals": signals,
        "findings": [finding.to_dict() for finding in findings],
    }


def build_learning_insights(
    *,
    extended_report: dict[str, Any],
    practitioner_report: dict[str, Any],
    batch_report: dict[str, Any],
    findings: list[LearningFinding],
    parameter_experiments: list[dict[str, Any]],
) -> dict[str, Any]:
    relation_counts = (
        extended_report.get("relation_family_counts")
        if isinstance(extended_report.get("relation_family_counts"), dict)
        else {}
    )
    dynamic_counts = (
        extended_report.get("dynamic_family_counts")
        if isinstance(extended_report.get("dynamic_family_counts"), dict)
        else {}
    )
    climate_counts = (
        extended_report.get("climate_bucket_counts")
        if isinstance(extended_report.get("climate_bucket_counts"), dict)
        else {}
    )
    topic_counts = (
        extended_report.get("topic_signal_counts")
        if isinstance(extended_report.get("topic_signal_counts"), dict)
        else {}
    )
    validated_families = {
        *(f"relation_formation.{key}" for key, count in relation_counts.items() if int(count or 0) > 0),
        *(f"relation_dynamics.{key}" for key, count in dynamic_counts.items() if int(count or 0) > 0),
    }
    if climate_counts:
        validated_families.add("climate_field")
    if int(topic_counts.get("authority_routes") or 0) > 0:
        validated_families.add("authority.core")
    if int(topic_counts.get("pattern_routes") or 0) > 0:
        validated_families.add("pattern_specialization")
    if int(topic_counts.get("risk_patterns") or 0) > 0:
        validated_families.add("risk_matrix")
    if int(topic_counts.get("core_routes") or 0) > 0:
        validated_families.add("work_authority_core")

    top_signals: list[dict[str, Any]] = []
    synthetic_signals = sorted(
        [signal for signal in (extended_report.get("signals") or []) if isinstance(signal, dict)],
        key=_signal_weight,
        reverse=True,
    )
    for signal in synthetic_signals[:8]:
        if not isinstance(signal, dict):
            continue
        families = _dedupe_preserve_order([*list(signal.get("relation_families") or []), *list(signal.get("dynamic_families") or [])])
        top_signals.append(
            {
                "case_id": signal.get("case_id"),
                "signal_type": "synthetic",
                "summary": f"top={ '/'.join(str(item) for item in (signal.get('top') or [])[:3]) or '—' }；families={','.join(str(item) for item in families[:4]) or '—'}；climate={signal.get('climate_label') or '—'}",
                "parameter_family": _primary_parameter_family_from_signal(signal),
            }
        )
    for signal in (practitioner_report.get("signals") or [])[:4]:
        if not isinstance(signal, dict):
            continue
        top_signals.append(
            {
                "case_id": signal.get("case_id"),
                "signal_type": "practitioner",
                "summary": f"top={ '/'.join(str(item) for item in (signal.get('top') or [])[:4]) or '—' }；focus={ ' / '.join(str(item) for item in (signal.get('audit_focus') or [])[:3]) }",
                "parameter_family": "practitioner_benchmark",
            }
        )

    blind_spots = _learning_blind_spots(
        relation_counts=relation_counts,
        dynamic_counts=dynamic_counts,
        topic_counts=topic_counts,
        practitioner_report=practitioner_report,
        findings=findings,
    )
    total_cases = int(batch_report.get("case_count") or 0) + int(extended_report.get("case_count") or 0) + int(
        practitioner_report.get("case_count") or 0
    )
    signal_count = len(top_signals) + len(validated_families)
    learning_density = round(signal_count / max(1, total_cases), 3)
    if findings or parameter_experiments:
        learning_value = "actionable"
    elif learning_density >= 0.45:
        learning_value = "baseline_validated"
    else:
        learning_value = "low_signal_green"

    return {
        "protocol": "v17.learning_insights.v1",
        "learning_value": learning_value,
        "learning_density": learning_density,
        "validated_parameter_families": sorted(validated_families),
        "top_learning_signals": top_signals[:12],
        "blind_spots": blind_spots,
        "recommended_next_cases": _recommended_next_cases(blind_spots=blind_spots, findings=findings),
    }


def _primary_parameter_family_from_signal(signal: dict[str, Any]) -> str:
    relation_families = [str(item) for item in (signal.get("relation_families") or []) if str(item)]
    dynamic_families = [str(item) for item in (signal.get("dynamic_families") or []) if str(item)]
    if relation_families:
        return f"relation_formation.{relation_families[0]}"
    if dynamic_families:
        return f"relation_dynamics.{dynamic_families[0]}"
    if signal.get("climate_label"):
        return "climate_field"
    layer = str(signal.get("layer") or "").strip()
    return f"synthetic.{layer}" if layer else "synthetic.general"


def _signal_weight(signal: dict[str, Any]) -> int:
    tags = {str(item) for item in (signal.get("tags") or [])}
    relation_families = {str(item) for item in (signal.get("relation_families") or []) if str(item)}
    dynamic_families = {str(item) for item in (signal.get("dynamic_families") or []) if str(item)}
    score = len(relation_families) * 2 + len(dynamic_families) * 2
    high_value_tags = {
        "relation",
        "runtime",
        "authority",
        "pattern",
        "climate",
        "sanhui",
        "sanhe",
        "stem_fusion",
        "interrupt",
        "resonance",
    }
    score += sum(2 for tag in tags if tag in high_value_tags)
    if signal.get("climate_label"):
        score += 1
    if str(signal.get("layer") or "").startswith(("L1", "L2", "MASTER")):
        score += 2
    return score


def _dedupe_preserve_order(values: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _learning_blind_spots(
    *,
    relation_counts: dict[str, Any],
    dynamic_counts: dict[str, Any],
    topic_counts: dict[str, Any],
    practitioner_report: dict[str, Any],
    findings: list[LearningFinding],
) -> list[str]:
    relation_keys = {str(key) for key, count in relation_counts.items() if int(count or 0) > 0}
    dynamic_keys = {str(key) for key, count in dynamic_counts.items() if int(count or 0) > 0}
    blind_spots: list[str] = []

    relation_groups = {
        "sanhe": {"sanhe"},
        "sanhui": {"sanhui"},
        "banhe": {"banhe", "banhe_shengwang", "banhe_muwang"},
        "gonghe": {"gonghe"},
        "liuhe": {"liuhe"},
        "anhe": {"anhe"},
        "stem_fusion": {"stem_fusion", "stem_fusion_transform"},
    }
    missing_relation = sorted(
        group_name
        for group_name, aliases in relation_groups.items()
        if not (relation_keys & aliases or dynamic_keys & aliases)
    )
    if missing_relation:
        blind_spots.append("关系家族覆盖仍缺：" + " / ".join(missing_relation))

    expected_dynamic = {"chong", "xing", "hai", "po", "ke"}
    missing_dynamic = sorted(expected_dynamic - dynamic_keys)
    if missing_dynamic:
        blind_spots.append("动力学扰动覆盖仍缺：" + " / ".join(missing_dynamic))

    if int(topic_counts.get("core_routes") or 0) < 4:
        blind_spots.append("做功/authority core 的路径样盘仍偏少，需要增加通关、制化、过制边界。")
    if int(topic_counts.get("pattern_routes") or 0) < 4:
        blind_spots.append("格局/专题样盘仍偏少，需要增加调候破格、格局互斥和混合格局。")

    practitioner_count = int(practitioner_report.get("case_count") or 0)
    if practitioner_count < 8:
        blind_spots.append(f"真实校盘基准仍偏薄：当前 {practitioner_count} 例，尚不足以代表命理师审盘分歧。")

    if findings:
        families = sorted({finding.parameter_family for finding in findings if finding.parameter_family})
        blind_spots.append("本轮异常集中参数族：" + " / ".join(families[:8]))

    if not blind_spots:
        blind_spots.append("本轮基础矩阵全绿，但仍缺主动挑战型样盘：极端气候、双体抢权、soft-bias 越权防线。")
    return blind_spots[:8]


def _recommended_next_cases(*, blind_spots: list[str], findings: list[LearningFinding]) -> list[str]:
    if findings:
        out: list[str] = []
        for family in sorted({finding.parameter_family for finding in findings if finding.parameter_family})[:6]:
            out.append(f"围绕 `{family}` 自动生成边界样盘，并与对应 practitioner benchmark 做 A/B 审计。")
        return out

    recommendations = [
        "构造“食伤制杀 vs 食伤生财”双主线抢权样盘，验证盲派体用与子平 authority 是否一致。",
        "构造寒湿、炎燥两组极端调候样盘，验证 climate_field 是否只影响效率/稳定/优先级，不回写 L0 base。",
        "构造 Level 3 soft bias 试图推翻 Level 1 hard constraint 的越权样盘，验证 authority gate。",
    ]
    if any("关系家族" in spot for spot in blind_spots):
        recommendations.append("补齐缺失关系家族的最小单变量样盘，每组只改一个地支或天干。")
    if any("真实校盘" in spot for spot in blind_spots):
        recommendations.append("新增 5 张命理师校盘基准，覆盖官杀混杂、财印交战、强弱与结构流通分歧。")
    return recommendations[:6]


def _climate_label(climate_field: dict[str, Any]) -> str:
    if not climate_field:
        return ""
    state = str(climate_field.get("climate_state") or climate_field.get("state") or "").strip()
    thermal = _safe_float(climate_field.get("thermal_index"))
    moisture = _safe_float(climate_field.get("moisture_index"))
    if not state:
        if thermal >= 0.45 and moisture <= -0.25:
            state = "炎燥"
        elif thermal >= 0.45 and moisture >= 0.25:
            state = "炎湿"
        elif thermal <= -0.45 and moisture >= 0.25:
            state = "寒湿"
        elif thermal <= -0.45 and moisture <= -0.25:
            state = "寒燥"
        elif thermal >= 0.25:
            state = "偏暖"
        elif thermal <= -0.25:
            state = "偏寒"
        elif moisture >= 0.25:
            state = "偏湿"
        elif moisture <= -0.25:
            state = "偏燥"
        else:
            state = "中和"
    return f"{state}(thermal={thermal:.2f}, moisture={moisture:.2f})"


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def render_learning_campaign_markdown(report: dict[str, Any]) -> str:
    scorecard = report.get("scorecard") if isinstance(report.get("scorecard"), dict) else {}
    coverage = report.get("plugin_governance_coverage") if isinstance(report.get("plugin_governance_coverage"), dict) else {}
    batch = report.get("synthetic_batch") if isinstance(report.get("synthetic_batch"), dict) else {}
    extended = report.get("extended_synthetic") if isinstance(report.get("extended_synthetic"), dict) else {}
    practitioner = report.get("practitioner_benchmarks") if isinstance(report.get("practitioner_benchmarks"), dict) else {}
    governance_counts = coverage.get("governance_class_counts") if isinstance(coverage.get("governance_class_counts"), dict) else {}
    authority_counts = coverage.get("authority_level_counts") if isinstance(coverage.get("authority_level_counts"), dict) else {}
    learning_counts = coverage.get("learning_family_counts") if isinstance(coverage.get("learning_family_counts"), dict) else {}
    extended_groups = extended.get("catalog_groups") if isinstance(extended.get("catalog_groups"), dict) else {}
    insights = report.get("learning_insights") if isinstance(report.get("learning_insights"), dict) else {}
    findings = report.get("findings") if isinstance(report.get("findings"), list) else []
    experiments = report.get("parameter_experiments") if isinstance(report.get("parameter_experiments"), list) else []
    llm_pkg = report.get("llm_review_package") if isinstance(report.get("llm_review_package"), dict) else {}
    feedback = report.get("analyst_feedback_items") if isinstance(report.get("analyst_feedback_items"), list) else []
    state = str(scorecard.get("state") or "unknown")
    codex_judgement = (
        "当前学习活动全绿，建议保持参数冻结，不生成调参候选。"
        if state == "green" and not findings and not experiments
        else "当前学习活动存在待审计项，建议先由 Codex 复核参数族与失败样盘，再交给分析师裁决。"
    )
    analyst_judgement = "无需分析师介入；没有 gate / 法理 / 语义冲突项。" if not feedback else "存在需要分析师复核的不确定项，请优先看 Analyst Feedback Items。"
    llm_judgement = "无需调用 LLM；本轮没有需要语义裁决的异常。" if not llm_pkg.get("should_request_llm_review") else "可以调用 LLM 做只读复核，但禁止直接输出配置补丁。"
    lines = [
        "# V17 Auto Learning Campaign Report",
        "",
        "日期：2026-04-23",
        "",
        f"- 协议：`{report.get('protocol')}`",
        f"- 主审：`{report.get('primary_reviewer')}`",
        f"- 复核：`{report.get('secondary_reviewer')}`",
        f"- 总状态：`{scorecard.get('state')}`",
        f"- 可自动应用参数：`{report.get('can_auto_apply')}`",
        f"- 运行预算：`{(report.get('budget') or {}).get('target_window', 'under_3_hours')}`",
        "",
        "## Executive Review",
        f"- Codex 主审结论：{codex_judgement}",
        f"- 分析师复核建议：{analyst_judgement}",
        f"- LLM 复核建议：{llm_judgement}",
        f"- 安全状态：`can_auto_apply={report.get('can_auto_apply')}`，所有参数候选仍为 review-only。",
        "",
        "## Learning Value",
        f"- 本轮学习价值：`{insights.get('learning_value', 'unknown')}`",
        f"- 学习密度：`{insights.get('learning_density', 0)}`",
        f"- 已验证参数族：{', '.join(str(item) for item in (insights.get('validated_parameter_families') or [])) or '—'}",
        f"- 主要盲区：{'; '.join(str(item) for item in (insights.get('blind_spots') or [])) or '—'}",
        "",
        "## Scorecard",
        f"- Synthetic Batch：{batch.get('passed_count', 0)}/{batch.get('case_count', 0)} passed",
        f"- Extended Synthetic：{extended.get('passed_count', 0)}/{extended.get('case_count', 0)} passed",
        f"- Practitioner Benchmark：{practitioner.get('passed_count', 0)}/{practitioner.get('case_count', 0)} passed",
        f"- Findings：{scorecard.get('finding_count', 0)}",
        f"- High Priority Findings：{scorecard.get('high_priority_finding_count', 0)}",
        f"- Parameter Experiments：{scorecard.get('parameter_experiment_count', 0)}",
        "",
        "## Coverage Matrix",
        f"- Synthetic Batch 覆盖：代表性关系、运流、冲害、调候场，共 {batch.get('case_count', 0)} 例。",
        f"- Extended Synthetic 覆盖：base={extended_groups.get('base', 0)} / risk={extended_groups.get('risk', 0)} / authority={extended_groups.get('authority', 0)} / pattern={extended_groups.get('pattern', 0)} / core={extended_groups.get('core', 0)}。",
        f"- Practitioner Benchmark 覆盖：真实复杂盘 {practitioner.get('case_count', 0)} 例。",
        "",
        "## Learning Signals",
    ]
    signals = insights.get("top_learning_signals") if isinstance(insights.get("top_learning_signals"), list) else []
    if signals:
        for item in signals[:12]:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('case_id')}` · {item.get('signal_type')} · {item.get('summary')} · 参数族：`{item.get('parameter_family')}`"
            )
    else:
        lines.append("- （无）")
    lines.extend(["", "## Next Hard Cases"])
    next_cases = insights.get("recommended_next_cases") if isinstance(insights.get("recommended_next_cases"), list) else []
    if next_cases:
        for item in next_cases:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无新增建议。")
    lines.extend([
        "",
        "## Plugin Governance Coverage",
        f"- 插件数：{coverage.get('plugin_count', 0)}",
        f"- 未分类插件：{coverage.get('unclassified_count', 0)}",
        "- Governance Class：",
    ])
    if governance_counts:
        for key, count in sorted(governance_counts.items()):
            lines.append(f"  - `{key}`：{count}")
    else:
        lines.append("  - （无）")
    lines.append("- Authority Level：")
    if authority_counts:
        for key, count in sorted(authority_counts.items()):
            lines.append(f"  - `{key}`：{count}")
    else:
        lines.append("  - （无）")
    lines.append("- Learning Family Top：")
    if learning_counts:
        for key, count in sorted(learning_counts.items(), key=lambda item: (-int(item[1]), str(item[0])))[:12]:
            lines.append(f"  - `{key}`：{count}")
    else:
        lines.append("  - （无）")

    lines.extend(["", "## Parameter Health"])
    families = report.get("parameter_family_counts") if isinstance(report.get("parameter_family_counts"), dict) else {}
    if not families:
        lines.append("- 当前没有触发参数族异常，不建议为了“学习感”而调参。")
        lines.append("- 本轮结论：冻结当前参数，继续积累更难的 synthetic / benchmark 样盘。")
    else:
        for family, count in sorted(families.items()):
            lines.append(f"- `{family}`：{count}")

    lines.extend(["", "## Parameter Experiments"])
    if not experiments:
        lines.append("- 当前没有生成影子参数实验。")
    else:
        for item in experiments:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('experiment_id')}` · {item.get('parameter_family')} · {item.get('application_mode')}"
            )

    lines.extend(["", "## Analyst Feedback Items"])
    if not feedback:
        lines.append("- （无）")
    else:
        for item in feedback:
            if not isinstance(item, dict):
                continue
            lines.append(f"- `{item.get('case_id')}` · {item.get('parameter_family')} · {item.get('message')}")

    lines.extend(["", "## System Feedback Package"])
    if not findings:
        lines.append("- 系统反馈：无异常，无需生成新的参数族调优任务。")
    else:
        for item in findings:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('source')}` / `{item.get('case_id')}` · {item.get('parameter_family')} · {item.get('message')}"
            )

    lines.extend(["", "## LLM Review Package"])
    lines.append(f"- 建议调用 LLM：`{llm_pkg.get('should_request_llm_review')}`")
    lines.append(f"- Payload Policy：`{llm_pkg.get('payload_policy', 'summarized_findings_only_no_raw_large_metadata')}`")
    lines.append(f"- Forbidden Output：`{', '.join(str(item) for item in (llm_pkg.get('forbidden_output') or []))}`")
    for item in llm_pkg.get("review_questions") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Safety Gates"])
    for gate in report.get("safety_gates") or []:
        lines.append(f"- `{gate}`")
    lines.append("")
    return "\n".join(lines)


def _audit_basic_run(
    case_id: str,
    total: float,
    top: Iterable[str],
    findings: list[LearningFinding],
    *,
    source: str = "synthetic_catalog",
) -> None:
    top_list = list(top or [])
    if not top_list:
        findings.append(LearningFinding(source, case_id, "P1", "top axis is empty", "ten_gods.calibration"))
    if not math.isfinite(float(total or 0.0)) or float(total or 0.0) <= 0.0:
        findings.append(LearningFinding(source, case_id, "P1", f"invalid total: {total}", "ten_gods.calibration"))


def _audit_risk_cases(findings: list[LearningFinding]) -> dict[str, Any]:
    signal_count = 0
    for case in SYNTHETIC_RISK_CASES:
        before = len(findings)
        run = run_risk_case(case)
        if not run.facts:
            findings.append(LearningFinding("synthetic_risk", case.case_id, "P1", "no risk facts emitted", "risk_matrix"))
            continue
        signal_count += len(run.facts)
        patterns = {
            str((fact.meta or {}).get("pattern_candidate") or "")
            for fact in run.facts
            if isinstance(fact.meta, dict)
        }
        for pattern_name in case.expected_patterns:
            if pattern_name not in patterns:
                findings.append(
                    LearningFinding(
                        "synthetic_risk",
                        case.case_id,
                        "P1",
                        f"missing expected risk pattern: {pattern_name}",
                        "risk_matrix",
                    )
                )
        if len(findings) == before:
            pass
    return {"case_count": len(SYNTHETIC_RISK_CASES), "signal_count": signal_count}


def _audit_authority_cases(findings: list[LearningFinding]) -> dict[str, Any]:
    signal_count = 0
    for case in SYNTHETIC_AUTHORITY_CASES:
        run = run_authority_case(case)
        if not run.facts:
            findings.append(LearningFinding("synthetic_authority", case.case_id, "P1", "no authority facts emitted", "authority.layer_protocol"))
            continue
        signal_count += len(run.facts)
        if run.authority.get("source") != "classical.ziping.god_ring_resolver.v1":
            findings.append(LearningFinding("synthetic_authority", case.case_id, "P1", "authority source mismatch", "authority.layer_protocol"))
        if run.resolved.get("display_mode") != "authority":
            findings.append(LearningFinding("synthetic_authority", case.case_id, "P1", "resolved authority payload missing", "authority.layer_protocol"))
    return {"case_count": len(SYNTHETIC_AUTHORITY_CASES), "signal_count": signal_count}


def _audit_pattern_cases(findings: list[LearningFinding]) -> dict[str, Any]:
    signal_count = 0
    for case in SYNTHETIC_PATTERN_CASES:
        run = run_pattern_case(case)
        fact = pattern_case_fact(run)
        if fact is None:
            findings.append(LearningFinding("synthetic_pattern", case.case_id, "P1", "no pattern fact emitted", "pattern_specialization"))
            continue
        signal_count += 1
        if fact.meta.get("pattern_candidate") != case.expected_pattern:
            findings.append(LearningFinding("synthetic_pattern", case.case_id, "P1", "pattern candidate mismatch", "pattern_specialization"))
        if fact.meta.get("target_god") != case.expected_target_god:
            findings.append(LearningFinding("synthetic_pattern", case.case_id, "P1", "target god mismatch", "pattern_specialization"))
        if not run.authority.get("judgement_bias_entries"):
            findings.append(LearningFinding("synthetic_pattern", case.case_id, "P1", "pattern did not route into authority", "authority.layer_protocol"))
    return {"case_count": len(SYNTHETIC_PATTERN_CASES), "signal_count": signal_count}


def _audit_core_cases(findings: list[LearningFinding]) -> dict[str, Any]:
    signal_count = 0
    for case in SYNTHETIC_CORE_CASES:
        run = run_core_case(case)
        result = run.result
        signal_count += 1 if result else 0
        if not isinstance(result.get("effect_scores"), dict):
            findings.append(LearningFinding("synthetic_core", case.case_id, "P1", "missing effect scores", "authority.core_path"))
        if not result.get("use_candidates"):
            findings.append(LearningFinding("synthetic_core", case.case_id, "P1", "missing use candidates", "authority.core_path"))
        if not result.get("taboo_candidates"):
            findings.append(LearningFinding("synthetic_core", case.case_id, "P1", "missing taboo candidates", "authority.core_path"))
        if str(result.get("mode") or "") != "six_pillar_spacetime_core":
            findings.append(LearningFinding("synthetic_core", case.case_id, "P1", "core mode mismatch", "authority.core_path"))
    return {"case_count": len(SYNTHETIC_CORE_CASES), "signal_count": signal_count}


def _findings_from_batch_report(report: dict[str, Any]) -> list[LearningFinding]:
    out: list[LearningFinding] = []
    for row in report.get("anomalies") or []:
        if not isinstance(row, dict):
            continue
        out.append(
            LearningFinding(
                source="synthetic_batch",
                case_id=str(row.get("case_id") or ""),
                severity="P1",
                message=str(row.get("message") or row.get("anomaly_type") or ""),
                parameter_family=str(row.get("parameter_family") or "unknown"),
                needs_analyst_feedback=str(row.get("parameter_family") or "").startswith("relation_gate."),
            )
        )
    return out


def _findings_from_auto_loop(report: dict[str, Any]) -> list[LearningFinding]:
    out: list[LearningFinding] = []
    for row in report.get("analyst_feedback_items") or []:
        if not isinstance(row, dict):
            continue
        out.append(
            LearningFinding(
                source="auto_learning_loop",
                case_id=str(row.get("experiment_id") or ""),
                severity="P2",
                message=str(row.get("requested_feedback") or row.get("reason") or ""),
                parameter_family=str(row.get("parameter_family") or "unknown"),
                needs_analyst_feedback=True,
            )
        )
    return out


def _findings_from_dicts(rows: Any) -> list[LearningFinding]:
    out: list[LearningFinding] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        out.append(
            LearningFinding(
                source=str(row.get("source") or ""),
                case_id=str(row.get("case_id") or ""),
                severity=str(row.get("severity") or "P2"),
                message=str(row.get("message") or ""),
                parameter_family=str(row.get("parameter_family") or "unknown"),
                reviewer=str(row.get("reviewer") or "codex"),
                needs_analyst_feedback=bool(row.get("needs_analyst_feedback")),
                needs_llm_review=bool(row.get("needs_llm_review")),
            )
        )
    return out


def _compact_batch_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocol": report.get("protocol"),
        "case_count": int(report.get("case_count") or 0),
        "passed_count": int(report.get("passed_count") or 0),
        "failed_count": int(report.get("failed_count") or 0),
        "learning_loop_state": report.get("learning_loop_state"),
        "parameter_family_counts": dict(report.get("parameter_family_counts") or {}),
    }


def _scorecard(
    *,
    batch_report: dict[str, Any],
    extended_report: dict[str, Any],
    practitioner_report: dict[str, Any],
    findings: list[LearningFinding],
    parameter_experiment_count: int,
    interrupted: bool = False,
) -> dict[str, Any]:
    finding_count = len(findings)
    p0_p1_count = sum(1 for finding in findings if finding.severity in {"P0", "P1"})
    state = "paused" if interrupted else "green"
    if p0_p1_count:
        state = "needs_codex_review"
    if any(finding.needs_analyst_feedback for finding in findings):
        state = "needs_analyst_feedback"
    return {
        "state": state,
        "finding_count": finding_count,
        "high_priority_finding_count": p0_p1_count,
        "parameter_experiment_count": int(parameter_experiment_count),
        "batch_failed_count": int(batch_report.get("failed_count") or 0),
        "extended_failed_count": int(extended_report.get("failed_count") or 0),
        "practitioner_failed_count": int(practitioner_report.get("failed_count") or 0),
    }


def _llm_review_package(
    *,
    findings: list[LearningFinding],
    parameter_experiments: list[dict[str, Any]],
    requested: bool,
) -> dict[str, Any]:
    review_questions: list[str] = []
    if findings:
        families = sorted({finding.parameter_family for finding in findings if finding.parameter_family})
        review_questions.append(
            "请审阅这些参数族是否属于数值可调、规则 gate 错误，还是命理定义冲突：" + ", ".join(families)
        )
    if parameter_experiments:
        review_questions.append("请按命理口径评估候选参数实验的方向是否合理，禁止直接建议上线。")
    should_request = bool(requested and (findings or parameter_experiments))
    return {
        "protocol": "v17.learning_campaign.llm_review_package.v1",
        "requested": bool(requested),
        "should_request_llm_review": should_request,
        "review_questions": review_questions,
        "payload_policy": "summarized_findings_only_no_raw_large_metadata",
        "allowed_output": ("evaluation", "risk_notes", "parameter_family_comments", "analyst_questions"),
        "forbidden_output": ("direct_config_patch", "authority_override", "l0_l1_mutation"),
    }


def _budget_exceeded(started: float, config: LearningCampaignConfig) -> bool:
    return (time.monotonic() - started) >= max(1, int(config.max_duration_seconds))


def _should_stop(predicate: StopPredicate | None) -> bool:
    if predicate is None:
        return False
    try:
        return bool(predicate())
    except Exception:
        return False


def _emit_progress(
    callback: ProgressCallback | None,
    step_key: str,
    step_label: str,
    progress_percent: int,
    started: float,
    config: LearningCampaignConfig,
) -> None:
    if callback is None:
        return
    elapsed = max(0.0, time.monotonic() - started)
    budget = max(1, int(config.max_duration_seconds))
    remaining = max(0.0, min(float(budget), float(budget) - elapsed))
    try:
        callback(
            {
                "step_key": step_key,
                "step_label": step_label,
                "progress_percent": max(0, min(100, int(progress_percent))),
                "elapsed_seconds": round(elapsed, 3),
                "estimated_remaining_seconds": round(remaining, 3),
            }
        )
    except Exception:
        return
