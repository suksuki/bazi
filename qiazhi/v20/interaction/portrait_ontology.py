from __future__ import annotations

from v20.interaction.portrait_schema import PORTRAIT_SOURCE_POLICY
from v20.measurement.dimensions import bazi_dimension_manifest


def portrait_ontology_manifest() -> dict[str, object]:
    return {
        "version": "v20.portrait_ontology_manifest.v1",
        "status": "ready",
        "source_policy": PORTRAIT_SOURCE_POLICY,
        "axis_source": "runtime_rule_decision_domain",
        "dimension_model": bazi_dimension_manifest()["version"],
        "portrait_layers": {
            "micro": "日主、十神、五行、地支等命局内部结构画像。",
            "decision": "格局、用神、强弱等需要裁决的路径画像。",
            "macro": "财富、事业、关系、健康边界等主题投影画像。",
            "time": "大运流年与原局互动形成的时间触发画像。",
        },
        "knowledge_role": "reviewed_knowledge_units_provide_language_boundaries_and_evidence_prompts",
        "calibration_role": "append_only_feedback_signal_for_later_review",
        "allowed_knowledge_usage": [
            "axis_label_support",
            "evidence_boundary_text",
            "calibration_prompt_context",
            "coverage_gap_detection",
        ],
        "forbidden_knowledge_usage": [
            "direct_personality_verdict",
            "question_ranking_bias",
            "answer_conclusion_driver",
            "rule_activation",
        ],
        "allowed_feedback_signals": [
            "confirm",
            "reject",
            "needs_review",
            "evidence_gap",
        ],
        "guardrails": [
            "PORTRAIT_ONTOLOGY_IS_CONTRACT_ONLY",
            "RULE_DECISION_REMAINS_SOURCE_OF_TRUTH",
            "REVIEWED_KNOWLEDGE_REQUIRED_FOR_RUNTIME_LANGUAGE",
            "NO_RUNTIME_MUTATION",
        ],
        "runtime_mutation": False,
    }
