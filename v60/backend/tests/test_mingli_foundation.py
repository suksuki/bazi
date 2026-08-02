from datetime import date, time

import pytest
from abu_v60.mingli.calendar import BirthInput, resolve_four_pillars
from abu_v60.mingli.compiler import compile_birth_case, compile_case


def owner_birth_input() -> BirthInput:
    return BirthInput(
        calendar_type="solar",
        birth_date=date(1977, 5, 8),
        birth_time=time(17, 30),
        timezone="Asia/Shanghai",
        true_solar_time_policy="not_applied",
    )


def test_v60_recomputes_owner_chart_without_v50_runtime() -> None:
    chart = resolve_four_pillars(owner_birth_input())
    assert chart.ordered() == ["丁巳", "乙巳", "乙丑", "乙酉"]


def test_bounded_case_compilation_keeps_professional_unknowns_unresolved() -> None:
    birth_input = owner_birth_input()
    compiled = compile_birth_case(
        case_ref="v60-test-case-owner",
        birth_input=birth_input,
    )

    assert len(compiled.facts) == 22
    assert "strength" in compiled.life_case_payload["unresolved"]
    assert "effective_work" in compiled.life_case_payload["unresolved"]
    assert all(fact["fact_type"] != "strength" for fact in compiled.facts)
    assert compiled.scene_payload["tree_phenotype"]["semantic_status"] == "VISUAL_METAPHOR_ONLY"


def test_visual_phenotype_depends_on_chart_facts_not_case_identity() -> None:
    birth_input = owner_birth_input()
    first = compile_birth_case(case_ref="v60-case-a", birth_input=birth_input)
    second = compile_birth_case(case_ref="v60-case-b", birth_input=birth_input)

    assert first.scene_payload["tree_phenotype"] == second.scene_payload["tree_phenotype"]
    assert first.scene_ref != second.scene_ref


def test_birth_compiler_matches_verified_compatibility_entrypoint() -> None:
    birth_input = owner_birth_input()
    case_ref = "v60-case-calendar-equivalence"

    direct = compile_birth_case(case_ref=case_ref, birth_input=birth_input)
    verified = compile_case(
        case_ref=case_ref,
        birth_input=birth_input,
        chart=resolve_four_pillars(birth_input),
    )

    assert direct == verified


def test_product_case_rejects_chart_that_did_not_come_from_birth_input() -> None:
    birth_input = owner_birth_input()
    chart = resolve_four_pillars(birth_input).model_copy(update={"hour": "甲子"})

    with pytest.raises(ValueError, match="birth_chart_mismatch"):
        compile_case(
            case_ref="v60-case-calendar-drift",
            birth_input=birth_input,
            chart=chart,
        )
