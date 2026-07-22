from __future__ import annotations

from typing import Any

from core.contracts.professional_review import ProfessionalReviewOverlay
from core.life_case import LifeCase, formal_projection_record, project_life_case
from core.life_domains import (
    LifeDomain,
    domain_access_allowed,
    domain_definition,
    domain_manifest,
)
from core.mingli_agent import (
    CaseBeliefState,
    ChartWorldInstance,
    MingliCognitiveRecord,
    ProbePlan,
    build_deliberation_view,
)
from core.mingli_agent.reasoner import sanitize_public_mingli_payload
from experience.workspace import CaseWorkspaceState, build_case_workspace_state
from product.agent_probe_support import public_revision
from product.reading_projection import project_living_reading


def public_reading_view(
    *,
    world: ChartWorldInstance,
    record: MingliCognitiveRecord,
    workspace: CaseBeliefState,
    probe_plan: ProbePlan,
    active_domain: LifeDomain = LifeDomain.WHOLE_CHART,
    life_case: LifeCase | dict[str, Any] | None = None,
    workspace_state: CaseWorkspaceState | dict[str, Any] | None = None,
) -> dict[str, Any]:
    parsed_life_case = (
        life_case
        if isinstance(life_case, LifeCase)
        else LifeCase.model_validate(life_case)
        if life_case is not None
        else None
    )
    if parsed_life_case is not None:
        record = formal_projection_record(life_case=parsed_life_case, fallback_record=record)
    cognition = record.cognition
    primary = next(
        (
            item
            for item in cognition.hypotheses
            if item.hypothesis_id == cognition.selected_hypothesis_id
        ),
        cognition.hypotheses[0],
    )
    hypothesis_beliefs = {item.hypothesis_id: item for item in workspace.hypothesis_beliefs}
    consumed = (
        probe_plan.source_probe_id in workspace.answered_probe_ids
        or any(item.source_probe_id == probe_plan.source_probe_id for item in workspace.probe_history)
    )
    latest_revision = next(
        (item for item in reversed(record.revisions) if item.get("kind") == "probe_revision"),
        None,
    )
    professional_mode = probe_plan.role_mode in {"practitioner", "research"}
    deliberation = (
        build_deliberation_view(
            record=record,
            workspace=workspace,
            role_mode=probe_plan.role_mode,
            active_domain=active_domain,
        ).model_dump(mode="json")
        if professional_mode
        else None
    )
    active_hypothesis_id = (
        workspace.active_hypothesis_id
        if professional_mode
        else cognition.selected_hypothesis_id
    )
    active_deliberation = {
        item.stage_key: item
        for item in workspace.deliberation_selections
        if item.active and item.action != "research_fork"
    }
    parsed_workspace_state = (
        workspace_state
        if isinstance(workspace_state, CaseWorkspaceState)
        else CaseWorkspaceState.model_validate(workspace_state)
        if workspace_state is not None
        else build_case_workspace_state(
            case_id=record.case_id,
            active_mode=probe_plan.role_mode,
        )
    )
    selected_snapshot = (
        next(
            (
                item
                for item in reversed(parsed_life_case.temporal_snapshots)
                if item.period_key == parsed_workspace_state.selected_period
                and item.status == "active"
            ),
            None,
        )
        if parsed_life_case is not None
        else None
    )
    output = {
        "version": "deepbazi.living_reading.v1",
        "experience_mode": probe_plan.role_mode,
        "pillars": world.pillars,
        "first_look": cognition.first_look,
        "whole_chart_thesis": cognition.whole_chart_thesis,
        "lenses_available": {
            "bazi": True,
            "ziwei": bool(world.ziwei_profile.get("reasoning_ready")),
            "integrated": cognition.dual_lens is not None,
        },
        "ziwei_profile": world.ziwei_profile,
        "temporal_state": {
            "analysis_year": world.timing_context.get("analysis_year"),
            "annual_pillar": world.timing_context.get("annual_pillar"),
            "luck_pillar": world.timing_context.get("luck_pillar"),
            "luck_year_range": world.timing_context.get("luck_year_range"),
            "calculation_status": "ready",
            "interpretation_status": "not_generated",
            "system_period": parsed_workspace_state.system_period,
            "selected_period": parsed_workspace_state.selected_period,
            "selected_snapshot": (
                selected_snapshot.model_dump(mode="json") if selected_snapshot else None
            ),
        },
        "dual_lens": cognition.dual_lens.model_dump(mode="json") if cognition.dual_lens else None,
        "confidence": primary.confidence,
        "salient_phenomena": [
            item.model_dump(mode="json") for item in cognition.salient_phenomena
        ],
        "hypotheses": [
            {
                **item.model_dump(mode="json"),
                "case_belief_direction": (
                    hypothesis_beliefs[item.hypothesis_id].current_direction
                    if item.hypothesis_id in hypothesis_beliefs
                    else "unchanged"
                ),
                "professionally_selected": (
                    active_hypothesis_id == item.hypothesis_id
                    and active_hypothesis_id != cognition.selected_hypothesis_id
                ),
            }
            for item in cognition.hypotheses
        ],
        "selected_hypothesis_id": active_hypothesis_id,
        "system_selected_hypothesis_id": cognition.selected_hypothesis_id,
        "work_path": cognition.work_path.model_dump(mode="json"),
        "useful_god_reasoning": [
            item.model_dump(mode="json") for item in cognition.useful_god_reasoning
        ],
        "portrait": [item.model_dump(mode="json") for item in cognition.portrait],
        "career": cognition.career.model_dump(mode="json") if cognition.career else None,
        "wealth": cognition.wealth.model_dump(mode="json") if cognition.wealth else None,
        "life_domains": domain_manifest(),
        "domain_explorations": {
            domain.value: project_domain_exploration(
                exploration,
                role_mode=probe_plan.role_mode,
            )
            for domain, exploration in record.domain_explorations.items()
            if domain_access_allowed(domain, role_mode=probe_plan.role_mode)
        },
        "prior_predictions": [
            item.model_dump(mode="json") for item in cognition.prior_predictions
        ],
        "next_probe": cognition.next_probe.model_dump(mode="json"),
        "probe_plan": None if consumed else probe_plan.model_dump(mode="json"),
        "latest_revision": public_revision(latest_revision) if latest_revision else None,
        "deliberation": deliberation,
        "latest_deliberation_revision": (
            workspace.deliberation_revisions[-1].model_dump(mode="json")
            if professional_mode and workspace.deliberation_revisions
            else None
        ),
        "workspace": {
            "active_hypothesis_id": workspace.active_hypothesis_id,
            "hypothesis_beliefs": [
                item.model_dump(mode="json") for item in workspace.hypothesis_beliefs
            ],
            "assertion_beliefs": [
                item.model_dump(mode="json") for item in workspace.assertion_beliefs
            ],
            "hidden_attribute_beliefs": (
                [item.model_dump(mode="json") for item in workspace.hidden_attribute_beliefs]
                if probe_plan.role_mode in {"practitioner", "research"}
                else [
                    {
                        "attribute_id": item.attribute_id,
                        "lifecycle": item.lifecycle,
                        "confidence": item.confidence,
                    }
                    for item in workspace.hidden_attribute_beliefs
                ]
            ),
            "probe_response_count": len(workspace.probe_history),
            "revision_count": workspace.revision_count,
            "chart_facts_locked": workspace.chart_facts_locked,
            "global_update_allowed": workspace.global_update_allowed,
            "active_deliberation": (
                {
                    key: value.model_dump(mode="json")
                    for key, value in active_deliberation.items()
                }
                if professional_mode
                else {}
            ),
        },
        "workspace_state": parsed_workspace_state.model_dump(mode="json"),
        "unresolved_questions": cognition.unresolved_questions,
        "review": record.review.model_dump(mode="json"),
        "reliability": {
            "state": record.reliability_disposition,
            "commit_eligible": record.review.commit_eligible,
            "semantic_signature": record.reliability_signature,
            "gate_version": record.review.gate_version,
            "hard_failure_codes": record.review.hard_failure_codes,
        },
        "revision_count": len(record.revisions),
        "cognitive_run": {
            "stage_count": len(record.stage_receipts),
            "context_count": len(record.context_manifest),
        },
    }
    if parsed_life_case is not None:
        output["life_case"] = project_life_case(
            parsed_life_case,
            role_mode=probe_plan.role_mode,
        )
    sanitized = sanitize_public_mingli_payload(output)
    return project_living_reading(sanitized, mode=probe_plan.role_mode)


def reliability_outcome_payload(
    *,
    world: ChartWorldInstance,
    record: MingliCognitiveRecord,
    professional_review: ProfessionalReviewOverlay | None = None,
) -> dict[str, Any]:
    professionally_blocked = bool(
        professional_review is not None
        and professional_review.professional_release_status == "blocked"
    )
    primary = next(
        (
            item
            for item in record.cognition.hypotheses
            if item.hypothesis_id == record.cognition.selected_hypothesis_id
        ),
        record.cognition.hypotheses[0] if record.cognition.hypotheses else None,
    )
    alternatives = [
        {
            "hypothesis_id": item.hypothesis_id,
            "name": item.name,
            "thesis": item.thesis,
            "confidence": item.confidence,
            "supporting_evidence_refs": item.supporting_evidence_refs,
            "counter_evidence_refs": item.counter_evidence_refs,
            "success_conditions": item.success_conditions,
            "failure_conditions": item.failure_conditions,
        }
        for item in record.cognition.hypotheses
        if primary is None or item.hypothesis_id != primary.hypothesis_id
    ]
    return {
        "version": "deepbazi.mingli_reliability_outcome.v1",
        "state": "professional_blocked" if professionally_blocked else record.reliability_disposition,
        "formal_insight_committed": False,
        "pillars": world.pillars,
        "world_id": world.world_id,
        "chart_facts_available": True,
        "primary_explanation": (
            {
                "hypothesis_id": primary.hypothesis_id,
                "name": primary.name,
                "thesis": primary.thesis,
                "confidence": primary.confidence,
                "success_conditions": primary.success_conditions,
                "failure_conditions": primary.failure_conditions,
            }
            if primary and not professionally_blocked
            else None
        ),
        "competing_explanations": (
            alternatives
            if record.reliability_disposition == "competing" and not professionally_blocked
            else []
        ),
        "uncertainties": [] if professionally_blocked else record.cognition.unresolved_questions,
        "professional_release": (
            {
                "status": professional_review.professional_release_status,
                "review_version": professional_review.review_version,
                "hard_error_count": professional_review.hard_error_count,
                "major_error_count": professional_review.major_error_count,
                "blocked_scopes": [item.scope for item in professional_review.scope_blocks],
            }
            if professional_review is not None
            else {"status": "unreviewed"}
        ),
        "review": {
            "gate_version": record.review.gate_version,
            "hard_failure_codes": record.review.hard_failure_codes,
            "issues": [
                {
                    "code": item.code,
                    "message": item.message,
                    "category": item.category,
                    "blocks_commit": item.blocks_commit,
                }
                for item in record.review.issues
            ],
        },
    }


def project_domain_exploration(exploration: Any, *, role_mode: str) -> dict[str, Any]:
    definition = domain_definition(exploration.domain)
    reading = exploration.reading.model_dump(mode="json")
    base = {
        "domain": exploration.domain.value,
        "name_zh": definition.name_zh,
        "readiness": definition.readiness.value,
        "public_depth": exploration.reasoning_protocol.get("public_depth"),
        "boundary": definition.boundary,
        "generated_at": exploration.generated_at,
        "reliability_state": exploration.reliability_disposition,
        "baseline_inheritance": {
            "baseline_insight_id": exploration.baseline_insight_id,
            "baseline_record_id": exploration.baseline_record_id,
            "case_version": exploration.baseline_case_version,
            "semantic_signature": exploration.baseline_semantic_signature,
        },
        "reading": reading,
    }
    if role_mode == "guest":
        base["reading"] = {
            "domain": reading["domain"],
            "core_question": reading["core_question"],
            "causal_chain": reading["causal_chain"],
            "stable_tendencies": reading["stable_tendencies"][:1],
            "opportunity_conditions": reading["opportunity_conditions"][:1],
            "risk_conditions": reading["risk_conditions"][:1],
            "timing_note": reading["timing_note"],
            "prior_directions": reading["prior_directions"][:1],
            "unknowns": reading["unknowns"][:1],
        }
    elif role_mode == "member":
        for assertion in base["reading"].get("assertions", []):
            assertion.pop("evidence_refs", None)
            assertion.pop("counter_evidence_refs", None)
    elif role_mode == "practitioner":
        base["review_summary"] = {
            "issue_count": len(exploration.review.issues),
            "fact_traceability_rate": exploration.review.fact_traceability_rate,
        }
        base["reasoning_protocol"] = exploration.reasoning_protocol
    else:
        base["review"] = exploration.review.model_dump(mode="json")
        base["reasoning_protocol"] = exploration.reasoning_protocol
        base["context_manifest"] = exploration.context_manifest
    return base
