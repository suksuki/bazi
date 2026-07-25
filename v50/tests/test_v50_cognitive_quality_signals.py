from __future__ import annotations

from core.mingli_agent.contracts import ChartWorldInstance, WorldFact
from core.mingli_agent.quality import compare_cognitive_distinction, evaluate_cognitive_quality


def _world() -> ChartWorldInstance:
    facts = [
        WorldFact(fact_id="F1", kind="fact", category="pillar", statement="丁巳 乙巳 乙丑 乙酉", source_refs=[]),
        WorldFact(fact_id="F2", kind="derived_observation", category="graph_relation", statement="巳酉丑存在三合关系", source_refs=["F1"], authority="neutral_relation"),
    ]
    return ChartWorldInstance(
        world_id="world.test",
        reading_id="reading.test",
        pillars=["丁巳", "乙巳", "乙丑", "乙酉"],
        birth_profile={},
        facts=facts,
        knowledge=[],
        allowed_evidence_refs=["F1", "F2"],
    )


def _specific_payload() -> dict:
    return {
        "first_look": "丁巳、乙巳与乙酉之间的输出和金局压力构成主要矛盾。",
        "whole_chart_thesis": "乙木通过丁火输出，再面对巳酉丑金势的承载问题。",
        "hypotheses": [
            {"name": "输出制约", "thesis": "丁火输出制约金势", "failure_conditions": ["现实中长期不表达"], "counter_evidence_refs": [], "supporting_evidence_refs": ["F1", "F2"]},
            {"name": "受压不出", "thesis": "金势使乙木收缩", "failure_conditions": ["高压时反而持续主动输出"], "counter_evidence_refs": ["F1"], "supporting_evidence_refs": ["F2"]},
        ],
        "work_path": {
            "source": ["乙木"], "transformations": ["丁火输出"], "target": ["巳酉丑金势"],
            "body_function_relation": "以输出承接压力", "success_conditions": ["表达可落地"],
            "failure_conditions": ["输出通道受阻"], "evidence_refs": ["F1", "F2"],
        },
        "useful_god_reasoning": [{"candidate": "火", "role": "输出", "lens": "work_path", "evidence_refs": ["F1"]}],
        "portrait": [{"claim": "高压下倾向用表达解决问题", "falsifiers": ["现实中持续回避表达"], "evidence_refs": ["F1"]}],
        "prior_predictions": [{"claim": "更可能先形成输出再取得承载", "disconfirming_answer": "长期只等待外部安排", "evidence_refs": ["F2"]}],
    }


def test_quality_signals_reward_chart_anchors_and_falsifiers_without_claiming_correctness() -> None:
    signals = evaluate_cognitive_quality(_specific_payload(), world=_world())
    assert signals.status == "diagnostic_only"
    assert signals.structural_specificity >= 0.75
    assert signals.falsifiability >= 0.8
    assert signals.causal_completeness == 1.0
    assert signals.fact_traceability == 1.0
    assert "不判断命理结论正确与否" in signals.interpretation_boundary


def test_quality_signals_expose_generic_and_unfalsifiable_output() -> None:
    generic = {
        "first_look": "有机会也有挑战，保持积极心态。",
        "hypotheses": [{"name": "平衡", "thesis": "平衡就好", "supporting_evidence_refs": []}],
        "work_path": {"source": [], "transformations": [], "target": [], "evidence_refs": []},
        "portrait": [{"claim": "相信自己", "evidence_refs": []}],
        "prior_predictions": [],
    }
    signals = evaluate_cognitive_quality(generic, world=_world())
    assert signals.generic_language_risk >= 0.7
    assert signals.falsifiability == 0.0
    assert signals.causal_completeness < 0.3
    assert signals.warnings


def test_quality_signals_separate_traceability_from_deterministic_fact_consistency() -> None:
    world = ChartWorldInstance(
        world_id="world.fact.consistency",
        reading_id="reading.fact.consistency",
        pillars=["壬辰", "戊申", "丙午", "丁丑"],
        birth_profile={},
        facts=[
            WorldFact(
                fact_id="F007",
                kind="fact",
                category="root_strength",
                statement="root_strength",
                payload={"day_stem": "丙", "has_root": True},
            ),
            WorldFact(
                fact_id="F008",
                kind="fact",
                category="branch_relations",
                statement="branch_relations",
                payload={"relations": []},
            ),
        ],
        knowledge=[],
        allowed_evidence_refs=["F1", "F2", "F007", "F008"],
    )
    payload = _specific_payload()
    payload["first_look"] = "日主地支无根，午火与申金暗合。"
    payload["hypotheses"][0]["supporting_evidence_refs"] = ["F007", "F008"]

    signals = evaluate_cognitive_quality(payload, world=world)

    assert signals.fact_traceability == 1.0
    assert signals.deterministic_fact_consistency == 0.0
    assert any("根气事实冲突" in item for item in signals.factual_conflict_hits)
    assert any("午申暗合" in item for item in signals.unsupported_fact_claim_hits)


def test_contrastive_signal_detects_cross_chart_copying() -> None:
    left = _specific_payload()
    copied = dict(left)
    distinct = _specific_payload()
    distinct["first_look"] = "壬水在申子辰水势中先形成流动，再由戊土界定边界。"
    distinct["whole_chart_thesis"] = "水势与土堤的张力是全盘重心。"
    distinct["hypotheses"] = [{"name": "水势成流", "thesis": "申子辰聚水，以戊土定界"}]
    distinct["work_path"] = {"source": ["壬水"], "transformations": ["申子辰聚水"], "target": ["戊土"], "body_function_relation": "以土定水", "success_conditions": ["土有根"], "failure_conditions": ["土虚"], "evidence_refs": []}
    distinct["useful_god_reasoning"] = [{"candidate": "土", "role": "定界", "lens": "repair"}]

    copied_signal = compare_cognitive_distinction(left, copied)
    distinct_signal = compare_cognitive_distinction(left, distinct)
    assert copied_signal.portable_template_risk == 1.0
    assert distinct_signal.contrastive_distinction > copied_signal.contrastive_distinction
    assert "代理指标" in copied_signal.interpretation_boundary
