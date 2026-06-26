from __future__ import annotations

from v20.interaction.question_seed_registry import question_seed_registry_manifest
from v20.learning.role_question_click_training import build_role_question_click_training_report
from v20.learning.role_view_policy_candidates import build_role_view_policy_candidate_report
from v20.learning.role_view_policy_replay import build_role_view_policy_replay_report
from v20.role_view.runtime_pointer import build_role_view_runtime_pointer
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


ROLE_VIEW_COMPLETION_VERSION = "v20.role_view_mainline_completion.v1"


def build_role_view_completion_report(*, store: LocalJsonlStore | None = None) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    seed_manifest = question_seed_registry_manifest()
    clicks = build_role_question_click_training_report(store=storage)
    candidates = build_role_view_policy_candidate_report(click_training_report=clicks)
    replay = build_role_view_policy_replay_report(policy_candidate_report=candidates)
    pointer = build_role_view_runtime_pointer(store=storage)
    phases = _phases(seed_manifest, clicks, candidates, replay, pointer)
    complete_count = sum(1 for phase in phases if phase["status"] == "complete")
    return {
        "version": ROLE_VIEW_COMPLETION_VERSION,
        "status": "complete" if complete_count == len(phases) else "partial",
        "completion_percent": round(complete_count / len(phases) * 100),
        "phase_count": len(phases),
        "complete_phase_count": complete_count,
        "phases": phases,
        "data_state": {
            "click_count": clicks.get("click_count", 0),
            "seed_count": seed_manifest.get("seed_count", 0),
            "candidate_count": candidates.get("candidate_count", 0),
            "comparison_count": replay.get("comparison_count", 0),
            "runtime_applied": pointer.get("runtime_applied", False),
            "runtime_effect": pointer.get("runtime_effect", ""),
        },
        "runtime_scope": [
            "role_question_ordering",
            "role_question_group_priority",
            "role_question_domain_priority",
            "role_question_strategy_priority",
            "role_seed_question_priority",
        ],
        "non_goals": [
            "no_chart_fact_mutation",
            "no_core_inference_mutation",
            "no_decision_report_mutation",
            "no_raw_user_text_learning",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_VIEW_MAINLINE_COMPLETION_IS_OBSERVABILITY_ONLY",
            "ROLE_VIEW_RUNTIME_POLICY_ONLY_REORDERS_VIEW_QUESTIONS",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
            "NO_RAW_USER_TEXT_IN_ROLE_LEARNING",
        ],
    }


def _phases(
    seed_manifest: dict[str, object],
    clicks: dict[str, object],
    candidates: dict[str, object],
    replay: dict[str, object],
    pointer: dict[str, object],
) -> list[dict[str, object]]:
    return [
        _phase("P1", "role_view_projection", True, "role_view module projects portrait/question view"),
        _phase("P2", "role_answer_profile", True, "non-stream and stream answers use role answer profile"),
        _phase("P3", "role_question_ui", True, "frontend renders role-aware question profiles and groups"),
        _phase("P4", "role_click_learning", "seed_question_role_fit" in tuple(clicks.get("training_targets", ())), "click ledger aggregates role/group/domain/strategy/seed"),
        _phase("P5", "seed_registry", int(seed_manifest.get("seed_count", 0) or 0) >= 20, "seed registry has broad cold-start coverage"),
        _phase("P6", "candidate_replay_pointer", replay.get("version") == "v20.role_view_policy_replay_report.v1" and pointer.get("version") == "v20.role_view_runtime_pointer.v1", "candidate, replay and pointer contracts are available"),
        _phase("P7", "runtime_promotion_gate", "promotion_gate" in pointer, "runtime pointer exposes read-only promotion gate for replay-ready candidates"),
    ]


def _phase(phase_key: str, name: str, complete: bool, summary: str) -> dict[str, object]:
    return {
        "phase_key": phase_key,
        "name": name,
        "status": "complete" if complete else "pending_data",
        "summary": summary,
    }
