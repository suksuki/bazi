from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from core.contracts import BirthInputCanonical
from core.mingli_agent import MingliContextCompiler, ProbePlanner, apply_probe_response, build_case_belief_state, compile_chart_world
from core.mingli_agent.contracts import (
    CaseAssertion,
    CognitiveHypothesis,
    DiscriminatingProbe,
    DomainCausalReading,
    EpistemicReviewReceipt,
    MingliCognitiveDraft,
    MingliCognitiveRecord,
    PriorPrediction,
    SalientPhenomenon,
    UsefulGodReasoning,
    WorkPathReasoning,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline V50 cognitive architecture validation.")
    parser.add_argument("--output-dir", default=str(ROOT / "reports" / "mingli_agent" / "cognitive-system-v1"))
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    bridge_world = compile_chart_world(reading_id="validation-bridge", birth_input=_birth("乙酉", "bridge"))
    broken_world = compile_chart_world(reading_id="validation-broken", birth_input=_birth("乙亥", "broken"))
    compiler = MingliContextCompiler()
    pattern = compiler.compile(world=bridge_world, stage="pattern")
    prediction = compiler.compile(
        world=bridge_world,
        stage="prediction",
        cognitive_state={"selected_hypothesis_id": "h1"},
    )

    bridge_relations = _triple_relations(bridge_world)
    broken_relations = _triple_relations(broken_world)
    record = _record()
    planner = ProbePlanner()
    plans = {mode: planner.plan(record=record, role_mode=mode) for mode in ("guest", "member", "practitioner", "research")}
    workspace = build_case_belief_state(record)
    updated, update_receipt = apply_probe_response(
        workspace=workspace,
        plan=plans["member"],
        option_id=plans["member"].options[0].option_id,
    )

    checks = {
        "stage_context_hashes_distinct": pattern.content_hash != prediction.content_hash,
        "prediction_context_is_smaller": len(prediction.fact_refs) < len(pattern.fact_refs),
        "bridge_relation_present_in_base": len(bridge_relations) >= 3,
        "bridge_relation_disappears_in_controlled_variant": len(broken_relations) == 0,
        "four_role_questions_distinct": len({plan.question for plan in plans.values()}) == 4,
        "all_probes_target_competing_hypotheses": all(len(plan.target_hypothesis_ids) >= 2 for plan in plans.values()),
        "case_belief_updated": updated.revision_count == 1 and bool(update_receipt.updated_hypothesis_ids),
        "chart_facts_unchanged": update_receipt.chart_facts_modified is False,
        "global_policy_unchanged": update_receipt.global_policy_modified is False,
        "global_theory_update_forbidden": all("global_theory" in plan.forbidden_updates for plan in plans.values()),
    }
    status = "passed" if all(checks.values()) else "failed"
    report = {
        "run_id": "v50-cognitive-system-validation-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "observed_data": {
            "bridge_relation_count": len(bridge_relations),
            "broken_variant_bridge_relation_count": len(broken_relations),
            "pattern_fact_count": len(pattern.fact_refs),
            "prediction_fact_count": len(prediction.fact_refs),
            "pattern_knowledge_count": len(pattern.knowledge_refs),
            "prediction_knowledge_count": len(prediction.knowledge_refs),
            "role_probe_questions": {mode: plan.question for mode, plan in plans.items()},
            "updated_hypothesis_ids": update_receipt.updated_hypothesis_ids,
        },
        "checks": checks,
        "interpretation": [
            "Stage context is task-specific instead of a shared full-world prompt.",
            "The controlled hour-branch mutation removes the triple-combination observations that should disappear.",
            "One epistemic target is projected into four different user jobs.",
            "Probe feedback updates only the current case belief workspace.",
        ],
        "recommendation": "Use this offline suite as a merge gate; use reviewed live model cases separately for cognitive quality.",
        "boundary": {
            "training_performed": False,
            "weights_modified": False,
            "runtime_rules_modified": False,
            "brain_logic_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "llm_used": False,
            "global_policy_update_allowed": False,
            "audit_only": True,
        },
    }
    json_path = output_dir / "cognitive_system_validation_v1.json"
    md_path = output_dir / "cognitive_system_validation_v1.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"status": status, "json": str(json_path), "markdown": str(md_path)}, ensure_ascii=False))
    raise SystemExit(0 if status == "passed" else 1)


def _birth(hour_pillar: str, suffix: str) -> BirthInputCanonical:
    return BirthInputCanonical.model_validate({
        "birth_input_id": f"cognitive-validation-{suffix}",
        "name": suffix,
        "gender": "male",
        "calendar_type": "solar",
        "birth_date": "1980-05-01",
        "birth_time": "18:00",
        "birth_location": "Shanghai",
        "timezone": "Asia/Shanghai",
        "year_pillar": "丁巳",
        "month_pillar": "乙巳",
        "day_pillar": "乙丑",
        "hour_pillar": hour_pillar,
        "input_quality": "explicit_pillars",
    })


def _triple_relations(world) -> list[str]:
    return [item.statement for item in world.facts if item.category == "graph_relation" and "三合" in item.statement]


def _record() -> MingliCognitiveRecord:
    hypotheses = [
        CognitiveHypothesis(
            hypothesis_id="h1", name="输出制压", thesis="通过输出处理结构压力。", rank=1, status="primary",
            supporting_evidence_refs=["F001"], failure_conditions=["输出节点失效"], confidence="high",
        ),
        CognitiveHypothesis(
            hypothesis_id="h2", name="顺从压力", thesis="在输出失效时顺从外部结构。", rank=2, status="alternative",
            supporting_evidence_refs=["F001"], failure_conditions=["输出仍主动做功"], rejection_reason="当前输出节点可见。", confidence="low",
        ),
    ]
    assertion = CaseAssertion(
        assertion_id="a1", domain="portrait", claim="更常通过方法和产出处理压力。", rationale="主做功如此。",
        epistemic_status="supported", falsifiers=["长期只依附现成体系"], evidence_refs=["F001"],
    )
    domain = lambda name: DomainCausalReading(
        domain=name, core_question="价值如何形成？", causal_chain=["结构", "行为", "环境", "结果"],
        stable_tendencies=["主动拆解"], favorable_environments=["复杂问题"], adverse_environments=["低自主重复"],
        opportunity_conditions=["输出被承接"], risk_conditions=["承载不足"], timing_note="仅条件候选。",
        prior_directions=["研究", "架构"], assertions=[assertion.model_copy(update={"assertion_id": f"{name}-a1", "domain": name})], unknowns=["现实承接"],
    )
    predictions = [
        PriorPrediction(
            prediction_id=f"p{index}", claim=claim, why_predicted="来自主假设。", target_hypothesis_ref="h1",
            evidence_refs=["F001"], disconfirming_answer="长期呈现相反模式。",
        )
        for index, claim in enumerate(("主动拆解压力。", "复杂问题更能激活能力。", "资源依赖成果转化。"), start=1)
    ]
    cognition = MingliCognitiveDraft(
        first_look="先看输出如何作用于压力端。", whole_chart_thesis="主线是输出能否驾驭压力。",
        salient_phenomena=[SalientPhenomenon(phenomenon_id="s1", observation="桥接结构", why_it_matters="改变全局闭合", evidence_refs=["F001"])],
        hypotheses=hypotheses, selected_hypothesis_id="h1",
        work_path=WorkPathReasoning(
            path_statement="乙木生丁火，丁火制金。", source=["乙木"], transformations=["丁火输出"], target=["金局压力"],
            body_function_relation="乙为体，输出制压为用。", closure="conditional", success_conditions=["丁火可用"],
            failure_conditions=["丁火失效"], evidence_refs=["F001"],
        ),
        useful_god_reasoning=[UsefulGodReasoning(
            candidate="丁火", role="转化", why_useful="连接体与压力端。", when_harmful="泄身而不能制压。",
            applicable_conditions=["压力端成形"], invalidating_conditions=["输出失效"], evidence_refs=["F001"],
        )],
        portrait=[assertion], prior_predictions=predictions,
        next_probe=DiscriminatingProbe(
            probe_id="probe-1", question="面对强规则压力时，你通常如何处理？", purpose="区分输出制压与顺从压力。",
            distinguishes_hypothesis_refs=["h1", "h2"], options=["主动拆解并形成方案", "先依附现成体系", "两者都不像"],
            expected_updates={"主动拆解并形成方案": "h1 strengthen", "先依附现成体系": "h2 strengthen"},
        ),
        unresolved_questions=["现实环境是否承接"], evidence_refs=["F001"], career=domain("career"), wealth=domain("wealth"),
    )
    return MingliCognitiveRecord(
        record_id="validation-record", case_id="validation-case", world_id="validation-world",
        created_at=datetime.now(timezone.utc).isoformat(), model="fixture", cognition=cognition,
        review=EpistemicReviewReceipt(passed=True, fact_traceability_rate=1.0, model="fixture"),
    )


def _markdown(report: dict[str, object]) -> str:
    observed = report["observed_data"]
    checks = report["checks"]
    return "\n".join([
        "# V50 Cognitive System Validation v1",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Observed Data",
        "",
        f"- Bridge relations: `{observed['bridge_relation_count']}`; controlled variant: `{observed['broken_variant_bridge_relation_count']}`.",
        f"- Pattern facts: `{observed['pattern_fact_count']}`; prediction facts: `{observed['prediction_fact_count']}`.",
        f"- Updated case hypotheses: `{', '.join(observed['updated_hypothesis_ids'])}`.",
        "",
        "## Checks",
        "",
        *[f"- {'PASS' if value else 'FAIL'} `{key}`" for key, value in checks.items()],
        "",
        "## Boundary",
        "",
        "`training_performed=false`, `weights_modified=false`, `mingli_algorithm_modified=false`, `llm_used=false`.",
        "",
        "## Recommendation",
        "",
        str(report["recommendation"]),
        "",
    ])


if __name__ == "__main__":
    main()
