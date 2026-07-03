from __future__ import annotations

from v30.brain.practitioner_interaction import (
    build_practitioner_interaction_state,
    build_practitioner_selection_record,
    find_option_set,
)
from v30.brain.text_options import (
    OPTION_SET_VERSION,
    PRACTITIONER_SELECTION_VERSION,
    TEXT_OPTION_PROJECTION_VERSION,
    build_response_option_set_for_question,
    build_text_option_projection_from_stage_points,
    extract_text_semantic_units,
)
from v30.presentation import build_presentation_model
from v30.presentation.thinking import build_thinking_projection
from v30.runtime import create_smoke_runtime


TEXT_OPTION_SYNTHETIC_VALIDATION_VERSION = "v30.text_option_synthetic_validation.v1"


def run_text_option_synthetic_validation(reading_id: str = "toi-synthetic-validation") -> dict[str, object]:
    runtime = create_smoke_runtime(reading_id=reading_id, locale="zh")
    thinking = build_thinking_projection(runtime)
    presentation = build_presentation_model(runtime, role_key="practitioner", locale="zh", client="web").model_dump(mode="json")
    useful_projection = build_text_option_projection_from_stage_points(
        [
            {
                "point_id": "stage.useful_god.synthetic.001",
                "stage_id": "useful_god_arbitration",
                "text": "用神候选先看土与火，土负责承接，火负责温煦，但火过旺会加重燥性。",
                "bazi_terms": ["用神", "土", "火"],
                "evidence_refs": ["synthetic.useful_god.earth", "synthetic.useful_god.fire"],
            }
        ],
        stage_id="useful_god_arbitration",
    )
    internal_extraction = extract_text_semantic_units(
        "JSON required key context_id v30.metadata schema is valid.",
        source_type="llm",
        source_id="internal-noise",
        stage_id="rule_matching",
    )
    turn = presentation["reading_surface"]["current_dialogue_turn"]
    question = turn["question"]
    response_option_set = turn["response_option_set"]
    hidden_option_set = build_response_option_set_for_question(
        {
            "question_id": "q_hidden_synthetic",
            "topic": "hidden_factor",
            "label": "这里需要补一个隐藏线索",
            "answer_constraints": {
                "constraint_type": "structured_hidden_factor",
                "allowed_state_tags": [
                    {"value": "career_pressure", "label": "事业压力"},
                    {"value": "wealth_fluctuation", "label": "财务波动"},
                ],
            },
        },
        stage_id="question_followup",
        role_key="user",
    )
    first_option_set = _first_stage_option_set(thinking) or useful_projection["option_sets"][0]
    first_option_id = str(first_option_set["options"][0]["option_id"])
    selection = build_practitioner_selection_record(
        first_option_set,
        selected_option_ids=[first_option_id],
        action="select",
        confidence=0.82,
        actor_id="synthetic-practitioner",
    )
    practitioner_state = build_practitioner_interaction_state(reading_id, thinking, [selection], role_key="practitioner")
    cases = [
        _case(
            "SPI-7A",
            "stage_point_synthetic_tier",
            bool(_first_stage_point_set(thinking).get("selected_points")),
            {
                "stage_point_set_version": _first_stage_point_set(thinking).get("version"),
                "selected_count": len(_first_stage_point_set(thinking).get("selected_points", [])),
            },
        ),
        _case(
            "TOI-7B",
            "text_to_option_extraction_tier",
            useful_projection["version"] == TEXT_OPTION_PROJECTION_VERSION
            and useful_projection["option_sets"]
            and useful_projection["option_sets"][0]["version"] == OPTION_SET_VERSION
            and not internal_extraction["semantic_units"],
            {
                "useful_option_count": len(useful_projection["option_sets"][0]["options"]),
                "internal_noise_discarded": bool(internal_extraction["discarded_units"]),
            },
        ),
        _case(
            "TOI-7C",
            "practitioner_selection_alignment_tier",
            selection["version"] == PRACTITIONER_SELECTION_VERSION
            and selection["effect"]["chart_fact_mutation_allowed"] is False
            and practitioner_state["selection_count"] == 1,
            {
                "selection_action": selection["action"],
                "belief_delta": selection["effect"]["belief_delta"],
                "forbidden_effect_targets": selection["forbidden_effect_targets"],
            },
        ),
        _case(
            "HF-TOI-A",
            "hidden_factor_option_set_tier",
            hidden_option_set["topic"] == "hidden_factor"
            and hidden_option_set["selection_mode"] == "structured_hidden_factor"
            and hidden_option_set["visibility"]["user"] == "interactive",
            {
                "hidden_factor_option_count": len(hidden_option_set["options"]),
                "boundary": hidden_option_set["boundary"],
            },
        ),
        _case(
            "VAL-518K-A",
            "stage_option_distribution_observation",
            bool(thinking.get("steps"))
            and sum(len(step.get("stage_point_set", {}).get("option_sets", [])) for step in thinking["steps"]) >= 1,
            {
                "stage_count": len(thinking.get("steps", [])),
                "stage_option_set_count": sum(len(step.get("stage_point_set", {}).get("option_sets", [])) for step in thinking["steps"]),
                "sample_mode": "smoke_distribution_observation_not_full_518k",
            },
        ),
        _case(
            "DIALOGUE-ONE",
            "current_dialogue_single_question_contract",
            turn["ui_policy"]["max_visible_questions"] == 1
            and question["response_option_set"]["option_set_id"] == response_option_set["option_set_id"],
            {
                "question_id": question["question_id"],
                "response_option_set_version": response_option_set["version"],
            },
        ),
    ]
    ready = all(row["passed"] for row in cases)
    return {
        "version": TEXT_OPTION_SYNTHETIC_VALIDATION_VERSION,
        "status": "completed" if ready else "blocked",
        "case_count": len(cases),
        "passed_count": sum(1 for row in cases if row["passed"]),
        "failed_case_ids": [str(row["case_id"]) for row in cases if not row["passed"]],
        "cases": cases,
        "decision": {
            "text_option_synthetic_ready": ready,
            "stage_point_synthetic_ready": ready,
            "practitioner_selection_alignment_ready": ready,
            "chart_fact_mutation_allowed": False,
            "full_518k_run_performed": False,
        },
        "boundary": "text_option_synthetic_validation_checks_interaction_intelligence_without_mutating_chart_facts",
    }


def _first_stage_point_set(thinking: dict[str, object]) -> dict[str, object]:
    for step in thinking.get("steps", []):
        if isinstance(step, dict) and isinstance(step.get("stage_point_set"), dict):
            return step["stage_point_set"]
    return {}


def _first_stage_option_set(thinking: dict[str, object]) -> dict[str, object] | None:
    for step in thinking.get("steps", []):
        if not isinstance(step, dict):
            continue
        option_sets = step.get("stage_point_set", {}).get("option_sets", [])
        if isinstance(option_sets, list) and option_sets:
            found = find_option_set(thinking, str(option_sets[0].get("option_set_id") or ""), role_key="practitioner")
            return found or option_sets[0]
    return None


def _case(case_id: str, title: str, passed: bool, observed: dict[str, object]) -> dict[str, object]:
    return {
        "case_id": case_id,
        "title": title,
        "passed": bool(passed),
        "observed": observed,
    }
