from __future__ import annotations

from pydantic import Field

from v30.contracts import FeatureEvidence, V30Model


class KnowledgeRulePortraitSignal(V30Model):
    signal_id: str
    signal_type: str
    source_id: str
    domain: str
    label: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float
    boundary: str


SEED_KNOWLEDGE_RULE_PORTRAIT = {
    "ten_god_visibility": {
        "signal_type": "knowledge",
        "source_id": "v30.knowledge.ten_god.visibility",
        "label": "Visible ten-god signals are context markers, not user verdicts.",
        "boundary": "knowledge_support_only_no_personality_verdict",
    },
    "useful_god_candidate_question": {
        "signal_type": "rule",
        "source_id": "v30.rule.useful_god.candidate_gate",
        "label": "Useful-god stays as candidate path until evidence review is complete.",
        "boundary": "rule_blocks_fixed_useful_god_without_review",
    },
    "rule_hidden_factor_dialogue_boundary": {
        "signal_type": "rule",
        "source_id": "v30.rule.hidden_factor.requires_dialogue",
        "label": "Hidden-factor amplification is blocked until dialogue feedback calibrates it.",
        "boundary": "rule_blocks_deterministic_hidden_factor_claim",
    },
    "hidden_stem_context": {
        "signal_type": "portrait",
        "source_id": "v30.portrait.hidden_stem.dialogue_probe",
        "label": "Hidden-stem portrait signals require dialogue calibration.",
        "boundary": "portrait_hypothesis_requires_user_feedback",
    },
}


def build_knowledge_rule_portrait_signals(
    evidence: list[FeatureEvidence],
) -> list[KnowledgeRulePortraitSignal]:
    rows: list[KnowledgeRulePortraitSignal] = []
    for key, seed in SEED_KNOWLEDGE_RULE_PORTRAIT.items():
        matched = [row for row in evidence if key in row.supports]
        if not matched:
            continue
        rows.append(
            KnowledgeRulePortraitSignal(
                signal_id=f"{seed['source_id']}:signal",
                signal_type=str(seed["signal_type"]),
                source_id=str(seed["source_id"]),
                domain=matched[0].domain,
                label=str(seed["label"]),
                evidence_ids=[row.evidence_id for row in matched],
                confidence=round(sum(row.confidence for row in matched) / len(matched), 3),
                boundary=str(seed["boundary"]),
            )
        )
    return rows
