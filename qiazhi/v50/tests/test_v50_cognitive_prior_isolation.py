from __future__ import annotations

import json
from pathlib import Path

from core.contracts import BirthInputCanonical
from core.mingli_agent import MingliContextCompiler, compile_chart_world
from core.mingli_agent.reasoner import _pattern_hypothesis_prompt


ROOT = Path(__file__).resolve().parents[1]


def _fixture_birth() -> BirthInputCanonical:
    taxonomy = json.loads(
        (ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v1.json").read_text(encoding="utf-8")
    )
    payload = dict(taxonomy["cases"][0]["birth_input"])
    payload["birth_time"] = "08:30"
    return BirthInputCanonical.model_validate(payload)


def test_production_world_excludes_synthetic_expected_contract_by_default() -> None:
    world = compile_chart_world(reading_id="prior-isolation.default", birth_input=_fixture_birth())

    assert all(item.category != "research_fixture_prior" for item in world.facts)


def test_context_never_exposes_expected_contract_even_for_research_world() -> None:
    world = compile_chart_world(
        reading_id="prior-isolation.explicit-research",
        birth_input=_fixture_birth(),
        include_research_fixture_prior=True,
    )
    assert any(item.category == "research_fixture_prior" for item in world.facts)

    context = MingliContextCompiler().compile(world=world, stage="pattern")
    encoded = json.dumps(context.payload, ensure_ascii=False)

    assert "expert_structure_prior" not in context.payload
    assert "research_fixture_prior" not in encoded
    assert "expected_path" not in encoded


def test_pattern_prompt_is_generic_and_contains_no_fixture_answer() -> None:
    world = compile_chart_world(reading_id="prior-isolation.prompt", birth_input=_fixture_birth())
    prompt = _pattern_hypothesis_prompt(world)

    assert "expert_structure_prior" not in prompt
    assert "research_fixture_prior" not in prompt
    assert "expected_path" not in prompt
    assert "output_controls_pressure" not in prompt
    assert "乙木生丁火" not in prompt
    assert "巳酉丑" not in prompt
