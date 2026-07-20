from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal


ExperienceMode = Literal["guest", "member", "practitioner", "research"]


_PUBLIC_BASE_FIELDS = {
    "version",
    "experience_mode",
    "pillars",
    "first_look",
    "whole_chart_thesis",
    "lenses_available",
    "confidence",
    "portrait",
    "prior_predictions",
    "probe_plan",
    "latest_revision",
    "dual_lens",
    "ziwei_profile",
    "life_domains",
    "domain_explorations",
    "revision_count",
    "workspace",
    "workspace_state",
    "life_case",
    "temporal_state",
    "reliability",
}

_PRACTITIONER_FIELDS = {
    *_PUBLIC_BASE_FIELDS,
    "salient_phenomena",
    "hypotheses",
    "selected_hypothesis_id",
    "system_selected_hypothesis_id",
    "work_path",
    "useful_god_reasoning",
    "career",
    "wealth",
    "next_probe",
    "deliberation",
    "latest_deliberation_revision",
    "unresolved_questions",
}

_PUBLIC_FORBIDDEN_RESEARCH_FIELDS = {
    "mechanism_ast",
    "unified_state",
    "theme_bundle",
    "decision_confidence_profile",
    "theory_refs",
    "context_manifest",
    "stage_receipts",
    "reasoning_protocol",
    "review",
}


def project_living_reading(payload: dict[str, Any], *, mode: ExperienceMode) -> dict[str, Any]:
    """Project one cognitive record into a role-specific server contract.

    This function may omit or simplify cognition. It never creates a new Mingli
    claim and never mutates the stored cognitive record.
    """

    source = deepcopy(payload)
    if mode in {"guest", "member"}:
        projected = {key: source[key] for key in _PUBLIC_BASE_FIELDS if key in source}
        projected["portrait"] = _public_assertions(source.get("portrait", []), member=mode == "member")
        projected["prior_predictions"] = _public_predictions(
            source.get("prior_predictions", []),
            member=mode == "member",
        )
        projected["dual_lens"] = _public_dual_lens(source.get("dual_lens"), member=mode == "member")
        projected["ziwei_profile"] = _public_ziwei_profile(source.get("ziwei_profile") or {})
        projected["workspace"] = _public_workspace(source.get("workspace") or {})
        projected["latest_revision"] = _public_revision(source.get("latest_revision"))
        projected["public_evidence"] = _public_evidence(source, member=mode == "member")
        projected["public_work_path"] = _public_work_path(source.get("work_path") or {})
        projected = _strip_public_research_fields(projected)
        contract = "GuestReadingProjection" if mode == "guest" else "MemberReadingProjection"
    elif mode == "practitioner":
        projected = {key: source[key] for key in _PRACTITIONER_FIELDS if key in source}
        projected["workspace"] = _practitioner_workspace(source.get("workspace") or {})
        projected["ziwei_profile"] = _practitioner_ziwei_profile(source.get("ziwei_profile") or {})
        contract = "PractitionerCognitiveProjection"
    else:
        projected = source
        contract = "ResearchAuditProjection"

    projected["version"] = "deepbazi.role_reading_projection.v1"
    projected["experience_mode"] = mode
    projected["projection_contract"] = {
        "name": contract,
        "mode": mode,
        "source": "LifeCaseRevision+CaseBeliefState+WorkspaceState",
        "new_mingli_claims_created": False,
        "server_side_enforced": True,
    }
    return projected


def _public_assertions(assertions: list[dict[str, Any]], *, member: bool) -> list[dict[str, Any]]:
    fields = {"assertion_id", "domain", "claim", "epistemic_status"}
    if member:
        fields.update({"conditions", "falsifiers"})
    return [{key: item[key] for key in fields if key in item} for item in assertions]


def _public_predictions(predictions: list[dict[str, Any]], *, member: bool) -> list[dict[str, Any]]:
    fields = {"prediction_id", "claim"}
    if member:
        fields.update({"why_predicted", "disconfirming_answer"})
    return [{key: item[key] for key in fields if key in item} for item in predictions]


def _public_dual_lens(dual_lens: dict[str, Any] | None, *, member: bool) -> dict[str, Any] | None:
    if not dual_lens:
        return None
    fields = {
        "ziwei_first_look",
        "identity_axis",
        "agreements",
        "tensions",
        "integrated_thesis",
        "current_stage_note",
        "uncertainties",
    }
    projected = {key: deepcopy(dual_lens[key]) for key in fields if key in dual_lens}
    projected["palace_observations"] = [
        {
            key: item[key]
            for key in ({"observation_id", "domain", "claim"} | ({"why_it_matters", "counter_conditions"} if member else set()))
            if key in item
        }
        for item in dual_lens.get("palace_observations", [])[:3]
    ]
    return projected


def _public_ziwei_profile(profile: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "status",
        "reasoning_ready",
        "input_quality",
        "life_palace",
        "body_palace",
        "five_elements_class",
        "warnings",
    }
    return {key: deepcopy(profile[key]) for key in fields if key in profile}


def _public_workspace(workspace: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "probe_response_count",
        "revision_count",
        "chart_facts_locked",
        "global_update_allowed",
    }
    return {key: deepcopy(workspace[key]) for key in fields if key in workspace}


def _public_revision(revision: dict[str, Any] | None) -> dict[str, Any] | None:
    if not revision:
        return None
    fields = {"revision_id", "summary", "interpretation", "changed_assertions", "chart_facts_modified"}
    return {key: deepcopy(revision[key]) for key in fields if key in revision}


def _public_evidence(source: dict[str, Any], *, member: bool) -> dict[str, Any]:
    """Expose readable reasoning depth without leaking the professional workbench."""

    selected_id = source.get("selected_hypothesis_id")
    hypotheses = source.get("hypotheses") or []
    primary = next((item for item in hypotheses if item.get("hypothesis_id") == selected_id), None)
    if primary is None and hypotheses:
        primary = hypotheses[0]
    alternatives = [item for item in hypotheses if item is not primary]

    hypothesis_fields = {"name", "thesis", "success_conditions", "failure_conditions"}
    if member:
        hypothesis_fields.add("rejection_reason")

    def project_hypothesis(item: dict[str, Any] | None) -> dict[str, Any] | None:
        if not item:
            return None
        return {key: deepcopy(item[key]) for key in hypothesis_fields if key in item}

    observation_limit = 3 if member else 1
    alternative_limit = 2 if member else 1
    uncertainty_limit = 3 if member else 1
    return {
        "observations": [
            {
                key: deepcopy(item[key])
                for key in {"observation", "why_it_matters"}
                if key in item
            }
            for item in (source.get("salient_phenomena") or [])[:observation_limit]
        ],
        "primary_explanation": project_hypothesis(primary),
        "alternative_explanations": [
            projected
            for item in alternatives[:alternative_limit]
            if (projected := project_hypothesis(item)) is not None
        ],
        "uncertainties": deepcopy((source.get("unresolved_questions") or [])[:uncertainty_limit]),
    }


def _public_work_path(work_path: dict[str, Any]) -> dict[str, Any]:
    """Project the approved path without exposing fact IDs or audit internals."""

    fields = {"path_statement", "transformations", "body_function_relation"}
    return {key: deepcopy(work_path[key]) for key in fields if key in work_path}


def _strip_public_research_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_public_research_fields(child)
            for key, child in value.items()
            if key not in _PUBLIC_FORBIDDEN_RESEARCH_FIELDS
        }
    if isinstance(value, list):
        return [_strip_public_research_fields(item) for item in value]
    return value


def _practitioner_workspace(workspace: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "active_hypothesis_id",
        "hypothesis_beliefs",
        "assertion_beliefs",
        "hidden_attribute_beliefs",
        "probe_response_count",
        "revision_count",
        "chart_facts_locked",
        "global_update_allowed",
        "active_deliberation",
    }
    return {key: deepcopy(workspace[key]) for key in fields if key in workspace}


def _practitioner_ziwei_profile(profile: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "status",
        "reasoning_ready",
        "calculator",
        "input_quality",
        "life_palace",
        "body_palace",
        "soul_star",
        "body_star",
        "five_elements_class",
        "four_transformations",
        "decade_palace",
        "annual_palace",
        "warnings",
    }
    return {key: deepcopy(profile[key]) for key in fields if key in profile}
