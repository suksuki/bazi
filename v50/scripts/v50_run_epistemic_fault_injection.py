from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.contracts import BirthInputCanonical
from core.life_domains import LifeDomain
from core.mingli_agent import MingliContextCompiler, compile_chart_world
from core.mingli_agent.contracts import CognitiveHypothesis, PatternHypothesisDraft, SalientPhenomenon
from core.mingli_agent.reasoner import (
    _citation_allowed,
    _forbidden_domain_tokens,
    _review_hypothesis_space,
    _semantic_text_errors,
)


ROOT = Path(__file__).resolve().parents[1]


def run_fault_injection() -> dict[str, Any]:
    world = compile_chart_world(reading_id="fault-injection", birth_input=_birth())
    context = MingliContextCompiler().compile(world=world, stage="pattern")
    first_ref = context.fact_refs[0]

    base = _pattern(first_ref=first_ref)
    duplicate = base.model_copy(
        update={"hypotheses": [
            base.hypotheses[0],
            base.hypotheses[1].model_copy(
                update={"name": base.hypotheses[0].name, "thesis": base.hypotheses[0].thesis}
            ),
        ]}
    )
    selected_non_primary = base.model_copy(update={"selected_hypothesis_id": "h2"})
    omitted_salient = base.model_copy(
        update={
            "salient_phenomena": [
                SalientPhenomenon(
                    phenomenon_id="s-omitted",
                    observation="关键关系",
                    why_it_matters="应进入假设比较",
                    evidence_refs=["F-NOT-EXPLAINED"],
                )
            ]
        }
    )

    probes: list[tuple[str, Callable[[], list[str]], str]] = [
        ("wrong_element_relation", lambda: _semantic_text_errors(text="此处木生金并形成主线。", world=world), "错误五行关系"),
        ("engineering_leak", lambda: _semantic_text_errors(text="根据 V50 runtime schema 得出结论。", world=world), "内部工程信息泄漏"),
        ("overconfident_claim", lambda: _semantic_text_errors(text="这件事必然发生。", world=world), "过度确定断言"),
        ("fabricated_branch_relation", lambda: _semantic_text_errors(text="子午冲决定全局。", world=world), "地支关系冲突"),
        (
            "unknown_evidence_ref",
            lambda: [] if _citation_allowed(ref="evidence.does.not.exist", allowed=set(world.allowed_evidence_refs)) else ["未知证据引用"],
            "未知证据引用",
        ),
        ("duplicate_hypothesis", lambda: _review_hypothesis_space(pattern=duplicate, context=context).issues, "因果签名重复"),
        (
            "selected_non_primary",
            lambda: _review_hypothesis_space(pattern=selected_non_primary, context=context).issues,
            "必须指向唯一 primary",
        ),
        (
            "salient_omission",
            lambda: _review_hypothesis_space(pattern=omitted_salient, context=context).issues,
            "盘面重心证据未进入假设比较",
        ),
        (
            "unsupported_health_assertion",
            lambda: [token for token in _forbidden_domain_tokens(LifeDomain.HEALTH_VITALITY) if token in "命主患有心脏病"],
            "心脏病",
        ),
        (
            "unsupported_relationship_assertion",
            lambda: [token for token in _forbidden_domain_tokens(LifeDomain.RELATIONSHIP) if token in "明年一定离婚"],
            "一定离婚",
        ),
    ]
    results = []
    for fault_id, detector, expected in probes:
        observed = detector()
        detected = any(expected in item for item in observed)
        results.append(
            {
                "fault_id": fault_id,
                "status": "passed" if detected else "failed",
                "expected_detector": expected,
                "observed_issues": observed,
            }
        )

    failures = [item["fault_id"] for item in results if item["status"] != "passed"]
    return {
        "version": "deepbazi.epistemic_fault_injection.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not failures else "failed",
        "observed_data": {
            "fault_count": len(results),
            "detected_count": len(results) - len(failures),
            "undetected_faults": failures,
        },
        "fault_results": results,
        "interpretation": "The review system detects injected fact, evidence, hypothesis, boundary, and leakage faults; it does not judge a unique Mingli truth.",
        "boundary_status": {
            "llm_used": False,
            "runtime_rules_modified_during_run": False,
            "verifier_relaxed": False,
            "automatic_repair_applied": False,
        },
    }


def _pattern(*, first_ref: str) -> PatternHypothesisDraft:
    return PatternHypothesisDraft(
        first_look="先比较两个结构解释。",
        whole_chart_thesis="以事实和反证选择主线。",
        salient_phenomena=[
            SalientPhenomenon(
                phenomenon_id="s1",
                observation="关键事实",
                why_it_matters="决定候选解释",
                evidence_refs=[first_ref],
            )
        ],
        hypotheses=[
            CognitiveHypothesis(
                hypothesis_id="h1",
                name="主动转化候选",
                thesis="可见节点形成主动转化路径。",
                rank=1,
                status="primary",
                supporting_evidence_refs=[first_ref],
                failure_conditions=["关键节点失效"],
                confidence="medium",
            ),
            CognitiveHypothesis(
                hypothesis_id="h2",
                name="环境承载候选",
                thesis="环境力量主导，主动路径只作辅助。",
                rank=2,
                status="alternative",
                supporting_evidence_refs=[first_ref],
                failure_conditions=["环境主导证据不足"],
                rejection_reason="当前仍有主动路径事实。",
                confidence="low",
            ),
        ],
        selected_hypothesis_id="h1",
        evidence_refs=[first_ref],
    )


def _birth() -> BirthInputCanonical:
    return BirthInputCanonical.model_validate(
        {
            "birth_input_id": "fault-injection-birth",
            "name": "故障注入",
            "gender": "male",
            "calendar_type": "solar",
            "birth_date": "1987-05-12",
            "birth_time": "18:00",
            "birth_location": "上海",
            "timezone": "Asia/Shanghai",
            "year_pillar": "丁巳",
            "month_pillar": "乙巳",
            "day_pillar": "乙丑",
            "hour_pillar": "乙酉",
            "input_quality": "explicit_pillars",
        }
    )


def _write(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "epistemic_fault_injection_v1.json"
    md_path = output_dir / "epistemic_fault_injection_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Epistemic Fault Injection v1",
        "",
        f"- Status: `{report['status']}`",
        f"- Detected: `{report['observed_data']['detected_count']}/{report['observed_data']['fault_count']}`",
        "",
    ]
    lines.extend(
        f"- `{item['fault_id']}`: **{item['status']}** — {', '.join(item['observed_issues'])}"
        for item in report["fault_results"]
    )
    lines.extend(["", "## Boundaries", "", "```json", json.dumps(report["boundary_status"], ensure_ascii=False, indent=2), "```", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject known faults into V50 epistemic reviewers.")
    parser.add_argument("--output-dir", default=str(ROOT / "reports/epistemic-review/fault-injection-v1"))
    args = parser.parse_args()
    report = run_fault_injection()
    paths = _write(report, Path(args.output_dir))
    print(json.dumps({"status": report["status"], "reports": [str(path) for path in paths]}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
