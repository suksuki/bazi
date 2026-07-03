from __future__ import annotations

from v30.brain.practitioner_interaction import (
    ADMIN_INTELLIGENCE_REPLAY_VERSION,
    build_admin_intelligence_replay,
    build_practitioner_selection_record,
    find_option_set,
)
from v30.presentation.thinking import build_thinking_projection
from v30.runtime import create_smoke_runtime


STAGE_OPTION_INTELLIGENCE_REPLAY_VERSION = "v30.stage_option_intelligence_replay.v1"


def run_stage_option_intelligence_replay(reading_id: str = "stage-option-intelligence-replay") -> dict[str, object]:
    runtime = create_smoke_runtime(reading_id=reading_id, locale="zh")
    thinking = build_thinking_projection(runtime)
    selection = _synthetic_selection(thinking)
    selections = [selection] if selection else []
    replay = build_admin_intelligence_replay(reading_id, thinking, selections)
    checks = [
        {
            "check_id": "admin_replay_contract_present",
            "passed": replay["version"] == ADMIN_INTELLIGENCE_REPLAY_VERSION and bool(replay["stages"]),
            "observed": {"stage_count": replay["stage_count"]},
        },
        {
            "check_id": "stage_point_candidate_selected_discarded_visible",
            "passed": all("stage_point_replay" in row for row in replay["stages"])
            and replay["summary"]["stage_point_candidate_count"] >= replay["summary"]["stage_point_selected_count"] >= 1,
            "observed": replay["summary"],
        },
        {
            "check_id": "text_option_extracted_discarded_visible",
            "passed": all("text_option_replay" in row for row in replay["stages"])
            and replay["summary"]["option_set_count"] >= 1,
            "observed": replay["summary"],
        },
        {
            "check_id": "practitioner_selection_distribution_visible",
            "passed": replay["summary"]["practitioner_selection_count"] == len(selections)
            and replay["practitioner_selection_summary"]["chart_fact_mutation_allowed"] is False,
            "observed": replay["practitioner_selection_summary"],
        },
        {
            "check_id": "replay_is_read_only",
            "passed": replay["chart_fact_mutation_allowed"] is False,
            "observed": {"boundary": replay["boundary"]},
        },
    ]
    ready = all(row["passed"] for row in checks)
    return {
        "version": STAGE_OPTION_INTELLIGENCE_REPLAY_VERSION,
        "status": "completed" if ready else "blocked",
        "reading_id": reading_id,
        "replay": replay,
        "checks": checks,
        "decision": {
            "stage_option_replay_ready": ready,
            "admin_observability_ready": ready,
            "chart_fact_mutation_allowed": False,
        },
        "boundary": "stage_option_intelligence_replay_validates_admin_observability_without_mutating_chart_facts",
    }


def _synthetic_selection(thinking: dict[str, object]) -> dict[str, object] | None:
    for step in thinking.get("steps", []):
        if not isinstance(step, dict):
            continue
        option_sets = step.get("stage_point_set", {}).get("option_sets", [])
        if not isinstance(option_sets, list) or not option_sets:
            continue
        option_set_id = str(option_sets[0].get("option_set_id") or "")
        option_set = find_option_set(thinking, option_set_id, role_key="practitioner")
        if not option_set:
            continue
        options = option_set.get("options", [])
        if not isinstance(options, list) or not options:
            continue
        return build_practitioner_selection_record(
            option_set,
            selected_option_ids=[str(options[0].get("option_id") or "")],
            action="select",
            confidence=0.78,
            actor_id="synthetic-admin-replay",
        )
    return None
