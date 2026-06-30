from __future__ import annotations

import json
from pathlib import Path

from v40.contracts.base import Topic
from v40.contracts.chart import SyntheticCaseSeed
from v40.contracts.evaluation import EvaluationCaseSpec, ExpectedAdvice, ExpectedSignal, ExpectedVerdict, ForbiddenAssertion


def load_synthetic_seeds(path: str | Path) -> list[SyntheticCaseSeed]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("seeds", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("synthetic seed artifact must be a list or {'seeds': [...]}")
    return [SyntheticCaseSeed.model_validate(row) for row in rows]


def build_evaluation_cases_from_seeds(seeds: list[SyntheticCaseSeed]) -> list[EvaluationCaseSpec]:
    return [build_evaluation_case_from_seed(seed) for seed in seeds]


def build_evaluation_case_from_seed(seed: SyntheticCaseSeed) -> EvaluationCaseSpec:
    topic = _topic(seed.topic)
    return EvaluationCaseSpec(
        case_id=f"synthetic.{seed.seed_id}",
        case_type="synthetic",
        user_question=seed.question,
        topic=topic,
        known_reality={
            "synthetic": True,
            "chart_id": seed.chart_facts.chart_id,
            "pillars": seed.chart_facts.pillars_text,
        },
        expert_notes=[
            "Synthetic case only validates output structure and forbidden assertions.",
            "It must not be treated as real-world truth.",
        ],
        expected_signals=[
            ExpectedSignal(topic=Topic.STRUCTURE, claim_keywords=[seed.chart_facts.day_stem], min_confidence=0.4),
            ExpectedSignal(topic=Topic.USEFUL_GOD, claim_keywords=["用神"], min_confidence=0.4),
        ],
        expected_verdicts=[
            ExpectedVerdict(topic=topic, expected_keywords=seed.expected_keywords, min_evidence_count=1)
        ],
        expected_advice=[
            ExpectedAdvice(topic=topic, must_include_any=["校准", "反馈"], requires_action=True, requires_avoid=True)
        ],
        forbidden_assertions=[
            ForbiddenAssertion(text=text, severity="high", reason="synthetic_overclaim_guard")
            for text in seed.forbidden_assertions
        ],
    )


def _topic(value: str) -> Topic:
    normalized = value.strip().lower()
    aliases = {
        "career": Topic.CAREER,
        "事业": Topic.CAREER,
        "wealth": Topic.WEALTH,
        "财运": Topic.WEALTH,
        "relationship": Topic.RELATIONSHIP,
        "感情": Topic.RELATIONSHIP,
        "health": Topic.HEALTH,
        "健康": Topic.HEALTH,
        "timing": Topic.TIMING,
        "时运": Topic.TIMING,
        "useful_god": Topic.USEFUL_GOD,
        "用神": Topic.USEFUL_GOD,
        "overview": Topic.OVERVIEW,
    }
    return aliases.get(normalized, Topic.UNKNOWN)
