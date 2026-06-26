from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.interaction.question_atoms import QUESTION_ATOMS, QuestionSessionState, build_next_question_plan, question_atom_by_id
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


NEXT_QUESTION_SYNTHETIC_VERSION = "v20.next_question_synthetic_validation_report.v1"
NEXT_QUESTION_SYNTHETIC_ARTIFACT_VERSION = "v20.next_question_synthetic_validation_artifact_write.v1"


@dataclass(frozen=True)
class NextQuestionSyntheticCase:
    case_id: str
    role_key: str
    session_state: QuestionSessionState
    primary_domain: str
    primary_stage: str
    has_time_context: bool
    expected_atom_ids: tuple[str, ...] = ()
    suppressed_question_keys: tuple[str, ...] = ()
    expected_stage_in_top: str = ""
    expected_topic_in_top: str = ""
    expected_followup_target: str = ""


NEXT_QUESTION_SYNTHETIC_CASES: tuple[NextQuestionSyntheticCase, ...] = (
    NextQuestionSyntheticCase(
        case_id="guest_entry_no_time",
        role_key="guest",
        session_state=QuestionSessionState(),
        primary_domain="structure",
        primary_stage="entry",
        has_time_context=False,
        expected_atom_ids=("atom.guest.entry.overview",),
        expected_stage_in_top="entry",
        expected_topic_in_top="structure_dynamics",
    ),
    NextQuestionSyntheticCase(
        case_id="user_answered_career_prefers_timing",
        role_key="user",
        session_state=QuestionSessionState(
            answered_question_keys=("q_career_structure",),
            last_question_key="q_career_structure",
            last_domain="career",
            last_stage="focus",
            topic_depth={"career_structure": 1},
        ),
        primary_domain="career",
        primary_stage="focus",
        has_time_context=True,
        expected_atom_ids=("atom.user.timing.trigger",),
        suppressed_question_keys=("q_career_structure",),
        expected_stage_in_top="timing",
        expected_topic_in_top="timing_trigger",
        expected_followup_target="atom.user.timing.trigger",
    ),
    NextQuestionSyntheticCase(
        case_id="guest_health_entry_without_time",
        role_key="guest",
        session_state=QuestionSessionState(last_domain="health", last_stage="entry"),
        primary_domain="health",
        primary_stage="entry",
        has_time_context=False,
        expected_atom_ids=("atom.guest.entry.health",),
        expected_stage_in_top="entry",
        expected_topic_in_top="health_balance",
    ),
    NextQuestionSyntheticCase(
        case_id="user_relationship_timing_with_time",
        role_key="user",
        session_state=QuestionSessionState(
            answered_question_keys=("q_relationship_structure",),
            last_question_key="q_relationship_structure",
            last_domain="relationship",
            last_stage="focus",
            topic_depth={"relationship_pattern": 1},
        ),
        primary_domain="relationship",
        primary_stage="focus",
        has_time_context=True,
        expected_atom_ids=("atom.user.timing.relationship_window",),
        suppressed_question_keys=("q_relationship_structure",),
        expected_stage_in_top="timing",
        expected_topic_in_top="relationship_pattern",
        expected_followup_target="atom.user.timing.relationship_window",
    ),
    NextQuestionSyntheticCase(
        case_id="user_useful_god_after_strength",
        role_key="user",
        session_state=QuestionSessionState(
            answered_question_keys=("q_strength_assessment",),
            last_question_key="q_strength_assessment",
            last_domain="strength",
            last_stage="structure",
            topic_depth={"day_master_strength": 1},
        ),
        primary_domain="useful_god",
        primary_stage="focus",
        has_time_context=False,
        expected_atom_ids=("atom.user.focus.useful_god",),
        suppressed_question_keys=("q_strength_assessment",),
        expected_stage_in_top="focus",
        expected_topic_in_top="useful_god",
    ),
    NextQuestionSyntheticCase(
        case_id="analyst_structure_review_path",
        role_key="analyst",
        session_state=QuestionSessionState(last_domain="pattern", last_stage="structure"),
        primary_domain="structure",
        primary_stage="structure",
        has_time_context=False,
        expected_atom_ids=("atom.analyst.structure.primary_chain", "atom.analyst.review.counter_evidence"),
        expected_stage_in_top="structure",
        expected_topic_in_top="structure_dynamics",
    ),
    NextQuestionSyntheticCase(
        case_id="admin_observe_chain",
        role_key="admin",
        session_state=QuestionSessionState(last_domain="system", last_stage="observe"),
        primary_domain="structure",
        primary_stage="observe",
        has_time_context=True,
        expected_atom_ids=("atom.admin.observe.source", "atom.admin.observe.scoring"),
        expected_stage_in_top="observe",
        expected_topic_in_top="admin_observe",
    ),
)


def build_next_question_synthetic_validation_report(
    cases: tuple[NextQuestionSyntheticCase, ...] | None = None,
) -> dict[str, Any]:
    rows = []
    stage_hits: dict[str, int] = {}
    topic_hits: dict[str, int] = {}
    failures: list[str] = []
    followup_validation = validate_question_atom_followup_targets()
    failures.extend(f"followup_target:{item}" for item in followup_validation.get("missing_targets", ()) if str(item))
    for case in cases or NEXT_QUESTION_SYNTHETIC_CASES:
        plan = build_next_question_plan(
            role_key=case.role_key,
            session_state=case.session_state,
            primary_domain=case.primary_domain,
            primary_stage=case.primary_stage,
            has_time_context=case.has_time_context,
            runtime_policy={},
        )
        recommended = tuple(row for row in plan.get("recommended_atoms", ()) if isinstance(row, dict))
        suppressed = tuple(row for row in plan.get("suppressed_atoms", ()) if isinstance(row, dict))
        atom_ids = tuple(str(row.get("atom_id", "")) for row in recommended)
        suppressed_keys = tuple(str(row.get("question_key", "")) for row in suppressed)
        top_stages = tuple(str(row.get("stage", "")) for row in recommended[:3])
        top_topics = tuple(str(row.get("topic", "")) for row in recommended[:3])
        active_followup_targets = tuple(str(row) for row in plan.get("active_followup_targets", ()) if str(row))
        case_failures = []
        for atom_id in case.expected_atom_ids:
            if atom_id not in atom_ids:
                case_failures.append(f"missing_expected_atom:{atom_id}")
        for question_key in case.suppressed_question_keys:
            if question_key not in suppressed_keys:
                case_failures.append(f"missing_suppression:{question_key}")
        if case.expected_stage_in_top and case.expected_stage_in_top not in top_stages:
            case_failures.append(f"stage_not_in_top3:{case.expected_stage_in_top}")
        if case.expected_topic_in_top and case.expected_topic_in_top not in top_topics:
            case_failures.append(f"topic_not_in_top3:{case.expected_topic_in_top}")
        if case.expected_followup_target and case.expected_followup_target not in active_followup_targets:
            case_failures.append(f"followup_target_not_active:{case.expected_followup_target}")
        if case_failures:
            failures.extend(f"{case.case_id}:{failure}" for failure in case_failures)
        for stage in top_stages:
            if stage:
                stage_hits[stage] = stage_hits.get(stage, 0) + 1
        for topic in top_topics:
            if topic:
                topic_hits[topic] = topic_hits.get(topic, 0) + 1
        rows.append(
            {
                "case_id": case.case_id,
                "role_key": case.role_key,
                "status": "pass" if not case_failures else "fail",
                "failures": tuple(case_failures),
                "top_atom_ids": atom_ids[:5],
                "top_stages": top_stages,
                "top_topics": top_topics,
                "active_followup_targets": active_followup_targets,
                "followup_edges": tuple(plan.get("followup_edges", ())),
                "suppressed_question_keys": suppressed_keys,
                "has_time_context": case.has_time_context,
            }
        )
    policy = _candidate_policy(stage_hits=stage_hits, topic_hits=topic_hits, failures=failures)
    return {
        "version": NEXT_QUESTION_SYNTHETIC_VERSION,
        "status": "ready" if not failures and rows else "failed" if rows else "empty",
        "case_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "pass"),
        "failure_count": len(failures),
        "failures": tuple(failures),
        "case_results": tuple(rows),
        "candidate_policy": policy,
        "followup_target_validation": followup_validation,
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_VALIDATION_ONLY",
            "NEXT_QUESTION_POLICY_REORDERS_EXISTING_CANDIDATES",
            "ANSWERED_SUPPRESSION_MUST_PASS",
            "TIME_CONTEXT_BOOST_MUST_PASS",
        ],
    }


def write_next_question_synthetic_validation_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_next_question_synthetic_validation_report()
    directory = output_dir or storage.runtime_dir / "training" / "next_question_synthetic"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"next_question_synthetic_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": NEXT_QUESTION_SYNTHETIC_ARTIFACT_VERSION,
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "case_count": report["case_count"],
        "failure_count": report["failure_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "POINTER_ACTIVATION_IS_SEPARATE",
        ],
    }


def read_next_question_synthetic_validation_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "next_question_synthetic") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.next_question_synthetic_validation_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def validate_question_atom_followup_targets() -> dict[str, object]:
    atom_index = question_atom_by_id()
    missing = []
    stage_edges = []
    for atom in QUESTION_ATOMS:
        for target_id in atom.followup_targets:
            target = atom_index.get(target_id)
            if target is None:
                missing.append(f"{atom.atom_id}->{target_id}")
                continue
            stage_edges.append(
                {
                    "from_atom_id": atom.atom_id,
                    "from_stage": atom.stage,
                    "to_atom_id": target.atom_id,
                    "to_stage": target.stage,
                    "same_topic": atom.topic == target.topic,
                }
            )
    return {
        "version": "v20.question_atom_followup_target_validation.v1",
        "status": "pass" if not missing else "fail",
        "atom_count": len(QUESTION_ATOMS),
        "edge_count": len(stage_edges),
        "missing_target_count": len(missing),
        "missing_targets": tuple(missing),
        "stage_edges": tuple(stage_edges),
        "runtime_mutation": False,
        "guardrails": [
            "FOLLOWUP_TARGETS_MUST_REFERENCE_EXISTING_ATOMS",
            "FOLLOWUP_GRAPH_IS_INTERACTION_LAYER_ONLY",
            "NO_FACT_GENERATION",
        ],
    }


def _candidate_policy(*, stage_hits: dict[str, int], topic_hits: dict[str, int], failures: list[str]) -> dict[str, object]:
    if failures:
        return {
            "version": "v20.next_question_plan_candidate_policy.v1",
            "status": "blocked",
            "blocking_gate": "next_question_synthetic_failures",
            "runtime_mutation": False,
        }
    return {
        "version": "v20.next_question_plan_candidate_policy.v1",
        "status": "ready",
        "policy_key": "next_question_plan_policy",
        "stage_boosts": _boosts(stage_hits, base=0.015, cap=0.06),
        "topic_boosts": _boosts(topic_hits, base=0.01, cap=0.05),
        "source": "next_question_synthetic_validation",
        "runtime_mutation": False,
        "guardrails": [
            "BOOSTS_ONLY",
            "NO_NEW_ATOMS",
            "NO_FACT_GENERATION",
        ],
    }


def _boosts(counts: dict[str, int], *, base: float, cap: float) -> dict[str, float]:
    return {
        key: round(min(cap, base * max(1, count)), 4)
        for key, count in sorted(counts.items())
        if key
    }
