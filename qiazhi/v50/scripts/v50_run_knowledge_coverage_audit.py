#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


V50_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = V50_ROOT / "data" / "validation" / "reports"
JSON_REPORT = REPORT_DIR / "knowledge_coverage_audit_v1.json"
MD_REPORT = REPORT_DIR / "knowledge_coverage_audit_v1.md"

STATUS_SCORE = {
    "missing": 0.0,
    "partial": 0.5,
    "implemented": 0.75,
    "tested": 1.0,
}


def run_audit() -> dict[str, Any]:
    items = _audit_items()
    scores = _coverage_scores(items)
    conclusion = _conclusion(scores=scores, items=items)
    report = {
        "version": "v50.knowledge_coverage_audit.v1",
        "scope": [
            "Bazi Engine",
            "Ziwei Engine",
            "Fusion / Cross-engine mapping",
            "Topic mapping",
            "Evidence rule coverage",
        ],
        "summary": _summary(items),
        "coverage_scores": scores,
        "items": items,
        "final_conclusion": conclusion,
        "hard_boundary": {
            "audit_only": True,
            "rules_added": False,
            "weights_modified": False,
            "llm_used": False,
            "production_write": False,
        },
    }
    _write_reports(report)
    return report


def _audit_items() -> list[dict[str, Any]]:
    fixture_text = _fixture_corpus()
    rows: list[dict[str, Any]] = []

    def add(
        domain: str,
        knowledge_item: str,
        status: str,
        *,
        source_file: str = "",
        used_by_pipeline: bool = False,
        covered_by_fixture: bool | None = None,
        risk_level: str = "medium",
        recommended_action: str = "",
        fixture_tokens: list[str] | None = None,
    ) -> None:
        if covered_by_fixture is None:
            covered_by_fixture = any(token in fixture_text for token in (fixture_tokens or [knowledge_item]))
        rows.append(
            {
                "domain": domain,
                "knowledge_item": knowledge_item,
                "status": status,
                "source_file": source_file,
                "used_by_pipeline": used_by_pipeline,
                "covered_by_fixture": covered_by_fixture,
                "risk_level": risk_level,
                "recommended_action": recommended_action or _default_action(status),
            }
        )

    bazi_knowledge = "packages/core/engines/bazi/knowledge.py"
    bazi_engine = "packages/core/engines/bazi/material_engine.py"
    ziwei_knowledge = "packages/core/engines/ziwei/knowledge.py"
    ziwei_engine = "packages/core/engines/ziwei/material_engine.py"
    ziwei_builder = "packages/core/engines/ziwei/chart_builder.py"
    ziwei_dynamic = "packages/core/engines/ziwei/dynamic_evidence.py"
    flow_model = "packages/core/flows/model.py"
    mechanism_model = "packages/core/cognitive/mechanism_model.py"
    domain_model = "packages/core/cognitive/domain_mapping_model.py"
    decision_policy = "packages/core/brain/decision_policy.py"

    # Bazi foundation
    add("Bazi Foundation Coverage", "天干", "tested", source_file=bazi_knowledge, used_by_pipeline=True, risk_level="low", fixture_tokens=["year_pillar", "month_pillar"])
    add("Bazi Foundation Coverage", "地支", "tested", source_file=bazi_knowledge, used_by_pipeline=True, risk_level="low", fixture_tokens=["day_pillar", "hour_pillar"])
    add("Bazi Foundation Coverage", "藏干", "tested", source_file=bazi_knowledge, used_by_pipeline=True, risk_level="low", fixture_tokens=["hidden"])
    add("Bazi Foundation Coverage", "十神", "tested", source_file=bazi_engine, used_by_pipeline=True, risk_level="low", fixture_tokens=["ten_god", "shi_shen", "shang_guan"])
    add("Bazi Foundation Coverage", "五行", "tested", source_file=bazi_knowledge, used_by_pipeline=True, risk_level="low", fixture_tokens=["element_balance"])
    add("Bazi Foundation Coverage", "阴阳", "implemented", source_file=bazi_knowledge, used_by_pipeline=True, covered_by_fixture=False, risk_level="medium", recommended_action="Add fixture assertions for polarity-sensitive rules.")
    add("Bazi Foundation Coverage", "生克制化", "partial", source_file=bazi_knowledge, used_by_pipeline=True, covered_by_fixture=True, risk_level="medium", fixture_tokens=["output_to_wealth", "output_controls_pressure"])
    add("Bazi Foundation Coverage", "合冲刑害破", "partial", source_file=bazi_knowledge, used_by_pipeline=True, covered_by_fixture=False, risk_level="high", recommended_action="Only six clash / six harmony baseline exists; add 刑害破 coverage before relation-heavy judgments.")
    add("Bazi Foundation Coverage", "三合 / 三会 / 六合", "partial", source_file=bazi_knowledge, used_by_pipeline=False, covered_by_fixture=False, risk_level="high", recommended_action="六合 baseline exists; 三合 / 三会 are missing from runtime.")
    add("Bazi Foundation Coverage", "空亡", "missing", risk_level="medium")
    add("Bazi Foundation Coverage", "墓库", "missing", risk_level="high", recommended_action="Required before 财星入库 and storage-related wealth judgments.")
    add("Bazi Foundation Coverage", "旺衰 / 得令 / 通根 / 透干", "partial", source_file=bazi_engine, used_by_pipeline=True, covered_by_fixture=True, risk_level="high", fixture_tokens=["root_profile", "strength"])

    # Bazi mechanisms
    add("Bazi Mechanism Coverage", "食伤生财", "tested", source_file=flow_model, used_by_pipeline=True, risk_level="low", fixture_tokens=["output_to_wealth"])
    add("Bazi Mechanism Coverage", "食伤制杀", "tested", source_file=flow_model, used_by_pipeline=True, risk_level="low", fixture_tokens=["output_controls_pressure"])
    add("Bazi Mechanism Coverage", "杀印相生", "missing", risk_level="high")
    add("Bazi Mechanism Coverage", "财官相生", "missing", risk_level="high")
    add("Bazi Mechanism Coverage", "伤官见官", "partial", source_file=flow_model, used_by_pipeline=True, covered_by_fixture=False, risk_level="high", recommended_action="Current output_controls_pressure can approximate pressure; it is not a dedicated 伤官见官 rule.")
    add("Bazi Mechanism Coverage", "官杀混杂", "missing", risk_level="high")
    add("Bazi Mechanism Coverage", "比劫夺财", "tested", source_file=flow_model, used_by_pipeline=True, risk_level="low", fixture_tokens=["peer_competes_for_wealth"])
    add("Bazi Mechanism Coverage", "财星入库", "missing", risk_level="high")
    add("Bazi Mechanism Coverage", "印旺身强", "missing", risk_level="medium")
    add("Bazi Mechanism Coverage", "身弱财旺", "missing", risk_level="high")
    add("Bazi Mechanism Coverage", "身旺财弱", "missing", risk_level="high")
    add("Bazi Mechanism Coverage", "羊刃驾杀", "missing", risk_level="medium")
    add("Bazi Mechanism Coverage", "从格 / 假从", "missing", risk_level="medium")
    add("Bazi Mechanism Coverage", "调候", "missing", risk_level="high")
    add("Bazi Mechanism Coverage", "做功流通", "partial", source_file=mechanism_model, used_by_pipeline=True, covered_by_fixture=True, risk_level="high", fixture_tokens=["mechanism_v1", "output_to_wealth"])
    add("Bazi Mechanism Coverage", "体用", "missing", risk_level="high")
    add("Bazi Mechanism Coverage", "家里 / 家外", "missing", risk_level="medium")
    add("Bazi Mechanism Coverage", "主线条 / 轨迹", "missing", risk_level="high")

    # Bazi luck-year
    add("Bazi Luck-Year Coverage", "大运介入", "missing", risk_level="high")
    add("Bazi Luck-Year Coverage", "流年触发", "missing", risk_level="high")
    add("Bazi Luck-Year Coverage", "冲合引动", "missing", risk_level="high")
    add("Bazi Luck-Year Coverage", "运年叠加", "missing", risk_level="high")
    add("Bazi Luck-Year Coverage", "阶段主题变化", "missing", risk_level="high")
    add("Bazi Luck-Year Coverage", "远近 / 宫位 / 原局优先级", "missing", risk_level="high")
    add("Bazi Luck-Year Coverage", "原局、大运、流年三层证据关系", "missing", risk_level="high")

    # Topic mapping
    add("Bazi Topic Mapping Coverage", "事业", "tested", source_file=domain_model, used_by_pipeline=True, risk_level="low", fixture_tokens=["career"])
    add("Bazi Topic Mapping Coverage", "财富", "tested", source_file=domain_model, used_by_pipeline=True, risk_level="low", fixture_tokens=["wealth"])
    add("Bazi Topic Mapping Coverage", "感情", "missing", risk_level="high")
    add("Bazi Topic Mapping Coverage", "健康", "missing", risk_level="high")
    add("Bazi Topic Mapping Coverage", "学业", "missing", risk_level="medium")
    add("Bazi Topic Mapping Coverage", "家庭", "missing", risk_level="medium")
    add("Bazi Topic Mapping Coverage", "性格画像", "partial", source_file="packages/core/portrait", used_by_pipeline=False, covered_by_fixture=False, risk_level="medium", recommended_action="Portrait exists as a boundary layer but is not driven by current Brain outputs in validation.")
    add("Bazi Topic Mapping Coverage", "风险", "partial", source_file=domain_model, used_by_pipeline=True, covered_by_fixture=True, risk_level="medium", fixture_tokens=["pressure", "competition"])
    add("Bazi Topic Mapping Coverage", "阶段建议", "partial", source_file="packages/core/expression/experience_layer.py", used_by_pipeline=True, covered_by_fixture=True, risk_level="medium", fixture_tokens=["one_action"])

    # Ziwei foundation
    add("Ziwei Foundation Coverage", "十二宫", "tested", source_file=ziwei_builder, used_by_pipeline=True, risk_level="low", fixture_tokens=["palace"])
    add("Ziwei Foundation Coverage", "主星", "implemented", source_file=ziwei_knowledge, used_by_pipeline=True, covered_by_fixture=True, risk_level="medium", fixture_tokens=["major_star", "ziwei"])
    add("Ziwei Foundation Coverage", "辅星", "implemented", source_file=ziwei_knowledge, used_by_pipeline=True, covered_by_fixture=False, risk_level="medium")
    add("Ziwei Foundation Coverage", "四化", "tested", source_file=ziwei_knowledge, used_by_pipeline=True, risk_level="low", fixture_tokens=["transformation", "hua_ji"])
    add("Ziwei Foundation Coverage", "三方四正", "implemented", source_file=ziwei_builder, used_by_pipeline=True, covered_by_fixture=False, risk_level="medium")
    add("Ziwei Foundation Coverage", "宫干", "missing", risk_level="high")
    add("Ziwei Foundation Coverage", "命身宫", "tested", source_file=ziwei_engine, used_by_pipeline=True, risk_level="low", fixture_tokens=["life_palace", "body_palace"])
    add("Ziwei Foundation Coverage", "大限", "tested", source_file=ziwei_builder, used_by_pipeline=True, risk_level="medium", fixture_tokens=["major_cycle"])
    add("Ziwei Foundation Coverage", "流年", "tested", source_file=ziwei_builder, used_by_pipeline=True, risk_level="medium", fixture_tokens=["annual_cycle"])
    add("Ziwei Foundation Coverage", "流月", "missing", risk_level="medium")

    # Ziwei mechanisms
    add("Ziwei Mechanism Coverage", "命宫画像", "partial", source_file=ziwei_engine, used_by_pipeline=False, covered_by_fixture=False, risk_level="medium")
    add("Ziwei Mechanism Coverage", "官禄事业", "tested", source_file=ziwei_dynamic, used_by_pipeline=True, risk_level="low", fixture_tokens=["career_timing_activation"])
    add("Ziwei Mechanism Coverage", "财帛财富", "tested", source_file=ziwei_dynamic, used_by_pipeline=True, risk_level="low", fixture_tokens=["wealth_timing_activation"])
    add("Ziwei Mechanism Coverage", "夫妻关系", "tested", source_file=ziwei_dynamic, used_by_pipeline=True, risk_level="medium", fixture_tokens=["relationship_timing_activation"])
    add("Ziwei Mechanism Coverage", "疾厄健康", "tested", source_file=ziwei_dynamic, used_by_pipeline=True, risk_level="medium", fixture_tokens=["health_timing_activation"])
    add("Ziwei Mechanism Coverage", "迁移外部机会", "tested", source_file=ziwei_dynamic, used_by_pipeline=True, risk_level="medium", fixture_tokens=["migration_timing_activation"])
    add("Ziwei Mechanism Coverage", "福德心理状态", "missing", risk_level="medium")
    add("Ziwei Mechanism Coverage", "田宅资产", "missing", risk_level="medium")
    add("Ziwei Mechanism Coverage", "父母 / 子女 / 兄弟", "missing", risk_level="medium")
    add("Ziwei Mechanism Coverage", "大限主题", "partial", source_file=ziwei_dynamic, used_by_pipeline=True, covered_by_fixture=True, risk_level="medium", fixture_tokens=["major_cycle"])
    add("Ziwei Mechanism Coverage", "流年触发", "partial", source_file=ziwei_dynamic, used_by_pipeline=True, covered_by_fixture=True, risk_level="medium", fixture_tokens=["annual_cycle"])

    # Fusion and evidence
    add("Ziwei Time Coverage", "紫微短期压力", "tested", source_file=ziwei_dynamic, used_by_pipeline=True, risk_level="low", fixture_tokens=["short_term_pressure", "hua_ji"])
    add("Ziwei Time Coverage", "紫微主题激活", "tested", source_file=ziwei_dynamic, used_by_pipeline=True, risk_level="low", fixture_tokens=["timing_activation"])
    add("Ziwei Time Coverage", "紫微大限/流年并看", "partial", source_file=ziwei_dynamic, used_by_pipeline=True, covered_by_fixture=True, risk_level="medium", fixture_tokens=["major_cycle", "annual_cycle"])
    add("Fusion Coverage", "八字长期结构 vs 紫微阶段压力", "tested", source_file=decision_policy, used_by_pipeline=True, risk_level="low", fixture_tokens=["bazi_long_term_ziwei_short_term_conflict"])
    add("Fusion Coverage", "八字财富路径 vs 紫微财帛宫", "tested", source_file=decision_policy, used_by_pipeline=True, risk_level="low", fixture_tokens=["wealth_timing_activation"])
    add("Fusion Coverage", "八字事业压力 vs 紫微官禄宫", "tested", source_file=decision_policy, used_by_pipeline=True, risk_level="low", fixture_tokens=["career_timing_activation"])
    add("Fusion Coverage", "八字关系结构 vs 紫微夫妻宫", "partial", source_file=decision_policy, used_by_pipeline=True, covered_by_fixture=False, risk_level="high")
    add("Fusion Coverage", "冲突时如何保留双证据", "tested", source_file=decision_policy, used_by_pipeline=True, risk_level="low", fixture_tokens=["conflict_topics"])
    add("Fusion Coverage", "一致时如何提升 confidence", "tested", source_file=decision_policy, used_by_pipeline=True, risk_level="low", fixture_tokens=["alignment_bonus", "confidence_changes"])
    add("Evidence Coverage", "material_refs", "tested", source_file="packages/core/contracts/reasoning.py", used_by_pipeline=True, risk_level="low", fixture_tokens=["material_refs"])
    add("Evidence Coverage", "structure_refs", "tested", source_file="packages/core/contracts/reasoning.py", used_by_pipeline=True, risk_level="low", fixture_tokens=["structure_refs"])
    add("Evidence Coverage", "flow_refs", "tested", source_file="packages/core/contracts/reasoning.py", used_by_pipeline=True, risk_level="low", fixture_tokens=["flow_refs"])
    add("Evidence Coverage", "evidence_refs", "tested", source_file="packages/core/cognitive/contracts.py", used_by_pipeline=True, risk_level="low", fixture_tokens=["evidence_refs"])
    add("Evidence Coverage", "must_not_say", "tested", source_file="packages/core/judgment/model.py", used_by_pipeline=True, risk_level="low", fixture_tokens=["must_not_say"])
    add("Evidence Coverage", "user-facing verifier", "tested", source_file="packages/core/expression/verifier.py", used_by_pipeline=True, risk_level="low", fixture_tokens=["verifier"])

    return rows


def _fixture_corpus() -> str:
    fixture_dir = V50_ROOT / "data" / "validation" / "fixtures"
    chunks: list[str] = []
    for path in sorted(fixture_dir.glob("*.json")):
        chunks.append(path.name)
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _coverage_scores(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    domains = sorted({item["domain"] for item in items})
    scores: dict[str, dict[str, Any]] = {}
    for domain in domains:
        domain_items = [item for item in items if item["domain"] == domain]
        score = sum(STATUS_SCORE[item["status"]] for item in domain_items) / max(1, len(domain_items))
        status_counts = Counter(item["status"] for item in domain_items)
        scores[domain] = {
            "score": round(score, 3),
            "item_count": len(domain_items),
            "status_counts": dict(sorted(status_counts.items())),
            "high_risk_missing": [
                item["knowledge_item"]
                for item in domain_items
                if item["risk_level"] == "high" and item["status"] in {"missing", "partial"}
            ],
        }
    return scores


def _summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(item["status"] for item in items)
    return {
        "total_items": len(items),
        "status_counts": dict(sorted(status_counts.items())),
        "runtime_used_items": sum(1 for item in items if item["used_by_pipeline"]),
        "fixture_covered_items": sum(1 for item in items if item["covered_by_fixture"]),
        "high_risk_gaps": [
            item["knowledge_item"]
            for item in items
            if item["risk_level"] == "high" and item["status"] in {"missing", "partial"}
        ][:20],
    }


def _conclusion(*, scores: dict[str, dict[str, Any]], items: list[dict[str, Any]]) -> dict[str, Any]:
    bazi_mechanism = scores["Bazi Mechanism Coverage"]["score"]
    bazi_topic = scores["Bazi Topic Mapping Coverage"]["score"]
    ziwei_mechanism = scores["Ziwei Mechanism Coverage"]["score"]
    fusion = scores["Fusion Coverage"]["score"]
    evidence = scores["Evidence Coverage"]["score"]
    ready = "partial" if evidence >= 0.8 and fusion >= 0.6 and bazi_mechanism >= 0.2 and bazi_topic >= 0.3 else "no"
    blocked = ["relationship", "health", "family", "education"]
    allowed = ["wealth", "career"] if ready == "partial" else []
    gaps = [
        item["knowledge_item"]
        for item in items
        if item["risk_level"] == "high" and item["status"] in {"missing", "partial"}
    ]
    return {
        "ready_for_llm_synthetic_validation": ready,
        "allowed_topics": allowed,
        "blocked_topics": blocked,
        "must_fill_knowledge_gaps": gaps[:18],
        "risk_note": (
            "LLM Synthetic Validation can start only for currently supported wealth / career slices. "
            "It must be used to expose missing knowledge, not to compensate for missing knowledge."
        ),
        "next_recommended_phase": "LLM Synthetic Validation v1 with topic restrictions and visible blocked-topic reporting.",
        "score_drivers": {
            "bazi_mechanism": bazi_mechanism,
            "bazi_topic_mapping": bazi_topic,
            "ziwei_mechanism": ziwei_mechanism,
            "fusion": fusion,
            "evidence": evidence,
        },
    }


def _write_reports(report: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    MD_REPORT.write_text(_markdown_report(report), encoding="utf-8")


def _markdown_report(report: dict[str, Any]) -> str:
    conclusion = report["final_conclusion"]
    lines = [
        "# Knowledge Coverage Audit v1",
        "",
        "## Final Conclusion",
        "",
        f"- Ready for LLM Synthetic Validation: **{conclusion['ready_for_llm_synthetic_validation']}**",
        f"- Allowed topics: {', '.join(conclusion['allowed_topics']) or 'none'}",
        f"- Blocked topics: {', '.join(conclusion['blocked_topics']) or 'none'}",
        f"- Next recommended phase: {conclusion['next_recommended_phase']}",
        "",
        "## Coverage Scores",
        "",
        "| Domain | Score | Items | Status | High-risk gaps |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for domain, payload in report["coverage_scores"].items():
        status = ", ".join(f"{key}:{value}" for key, value in payload["status_counts"].items())
        gaps = ", ".join(payload["high_risk_missing"][:6])
        lines.append(f"| {domain} | {payload['score']} | {payload['item_count']} | {status} | {gaps} |")
    lines.extend(
        [
            "",
            "## Must-fill Knowledge Gaps",
            "",
            *[f"- {gap}" for gap in conclusion["must_fill_knowledge_gaps"]],
            "",
            "## Audit Items",
            "",
            "| Domain | Knowledge Item | Status | Runtime | Fixture | Risk | Source | Action |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["items"]:
        lines.append(
            "| {domain} | {knowledge_item} | {status} | {runtime} | {fixture} | {risk} | {source} | {action} |".format(
                domain=item["domain"],
                knowledge_item=item["knowledge_item"],
                status=item["status"],
                runtime="yes" if item["used_by_pipeline"] else "no",
                fixture="yes" if item["covered_by_fixture"] else "no",
                risk=item["risk_level"],
                source=item["source_file"] or "-",
                action=item["recommended_action"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def _default_action(status: str) -> str:
    if status == "missing":
        return "Add knowledge model, runtime hook, and validation fixture before user-facing use."
    if status == "partial":
        return "Complete runtime semantics and add focused fixtures."
    if status == "implemented":
        return "Add validation fixture coverage."
    return "Keep covered by regression."


def main() -> None:
    report = run_audit()
    conclusion = report["final_conclusion"]
    print(
        json.dumps(
            {
                "report": str(JSON_REPORT),
                "markdown": str(MD_REPORT),
                "ready_for_llm_synthetic_validation": conclusion["ready_for_llm_synthetic_validation"],
                "allowed_topics": conclusion["allowed_topics"],
                "blocked_topics": conclusion["blocked_topics"],
                "must_fill_knowledge_gaps": conclusion["must_fill_knowledge_gaps"][:8],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

