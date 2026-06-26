from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from v30.contracts import RoleKey
from v30.diagnosis.contracts import (
    DiagnosisClaim,
    DiagnosisDomain,
    DiagnosisGraph,
    DiagnosisMode,
    DiagnosisPath,
    DiagnosisPortrait,
    DiagnosisRouteDecision,
)


DIAGNOSIS_ROUTER_VERSION = "v30.real_bazi_diagnosis.router.v1"

MODE_DOMAIN: dict[DiagnosisMode, DiagnosisDomain] = {
    "overview": "structure",
    "career": "career",
    "wealth": "wealth",
    "relationship": "relationship",
    "health": "health",
    "timing": "timing",
    "hidden_factor_calibration": "hidden_factor",
    "practitioner_diagnostic": "structure",
}

ROLE_DENSITY: dict[str, str] = {
    "guest": "compact",
    "user": "standard",
    "practitioner": "dense",
    "analyst": "diagnostic",
    "admin": "diagnostic",
    "lab": "diagnostic",
}


def route_real_bazi_diagnosis(
    *,
    reading_id: str,
    role_key: RoleKey,
    graph: DiagnosisGraph,
    claims: Sequence[DiagnosisClaim],
    paths: Sequence[DiagnosisPath],
    portraits: Sequence[DiagnosisPortrait],
    requested_mode: DiagnosisMode = "overview",
    requested_domain: DiagnosisDomain | None = None,
    selected_question_id: str | None = None,
    limit: int | None = None,
) -> DiagnosisRouteDecision:
    selected_domain = requested_domain or MODE_DOMAIN.get(requested_mode, "structure")
    selected_claims = _select_claims(claims, selected_domain=selected_domain, mode=requested_mode, role_key=role_key, limit=limit)
    if not selected_claims and selected_domain != "structure":
        selected_domain = "structure"
        selected_claims = _select_claims(claims, selected_domain=selected_domain, mode=requested_mode, role_key=role_key, limit=limit)
    selected_paths = _select_paths(paths, selected_domain, selected_claims)
    selected_portraits = _select_portraits(portraits, selected_domain, selected_claims)
    followup_required = any(claim.needs_user_calibration for claim in selected_claims)
    safeguards = _safeguards(selected_claims, graph)
    return DiagnosisRouteDecision(
        route_id=f"{reading_id}:real-bazi-diagnosis-route:{requested_mode}:{selected_domain}",
        reading_id=reading_id,
        role_key=role_key,
        diagnosis_mode=requested_mode,
        selected_domain=selected_domain,
        selected_claim_ids=[claim.claim_id for claim in selected_claims],
        selected_path_ids=[path.path_id for path in selected_paths],
        selected_portrait_ids=[portrait.portrait_id for portrait in selected_portraits],
        followup_required=followup_required,
        followup_reason=_followup_reason(selected_claims, selected_question_id),
        expression_density=ROLE_DENSITY.get(str(role_key), "standard"),
        safeguards=safeguards,
        training_routes=_training_routes(selected_claims, selected_domain),
        central_brain_generated_facts=False,
    )


def summarize_diagnosis_route(route: DiagnosisRouteDecision) -> dict[str, Any]:
    return {
        "version": DIAGNOSIS_ROUTER_VERSION,
        "route_id": route.route_id,
        "reading_id": route.reading_id,
        "role_key": route.role_key,
        "diagnosis_mode": route.diagnosis_mode,
        "selected_domain": route.selected_domain,
        "selected_claim_count": len(route.selected_claim_ids),
        "selected_path_count": len(route.selected_path_ids),
        "selected_portrait_count": len(route.selected_portrait_ids),
        "followup_required": route.followup_required,
        "expression_density": route.expression_density,
        "training_routes": route.training_routes,
        "safeguards": route.safeguards,
        "boundary": "diagnosis_route_summary_selects_claims_not_facts",
    }


def _select_claims(
    claims: Sequence[DiagnosisClaim],
    *,
    selected_domain: DiagnosisDomain,
    mode: DiagnosisMode,
    role_key: RoleKey,
    limit: int | None,
) -> list[DiagnosisClaim]:
    pool = [claim for claim in claims if _claim_matches(claim, selected_domain, mode)]
    if mode == "overview":
        pool.extend(claim for claim in claims if claim.claim_level == "fact")
        pool.extend(claim for claim in claims if claim.domain in {"wealth", "career", "relationship", "health"} and claim.claim_level == "domain")
    pool = _dedupe_claims(pool)
    pool.sort(key=lambda row: (-_claim_score(row, selected_domain), _level_rank(row.claim_level), row.claim_id))
    default_limit = 8 if str(role_key) in {"practitioner", "analyst", "admin", "lab"} else 5
    return pool[: limit or default_limit]


def _select_paths(
    paths: Sequence[DiagnosisPath],
    domain: DiagnosisDomain,
    claims: Sequence[DiagnosisClaim],
) -> list[DiagnosisPath]:
    claim_path_ids = {path_id for claim in claims for path_id in claim.path_ids}
    rows = [path for path in paths if path.path_id in claim_path_ids or domain in path.domain_targets]
    rows.sort(key=lambda row: (-row.score, row.path_id))
    return rows[:6]


def _select_portraits(
    portraits: Sequence[DiagnosisPortrait],
    domain: DiagnosisDomain,
    claims: Sequence[DiagnosisClaim],
) -> list[DiagnosisPortrait]:
    claim_portrait_ids = {portrait_id for claim in claims for portrait_id in claim.portrait_ids}
    rows = [portrait for portrait in portraits if portrait.portrait_id in claim_portrait_ids or portrait.domain == domain]
    rows.sort(key=lambda row: (_band_rank(row.confidence_band), row.portrait_id))
    return rows[:6]


def _claim_matches(claim: DiagnosisClaim, domain: DiagnosisDomain, mode: DiagnosisMode) -> bool:
    if mode == "practitioner_diagnostic":
        return claim.domain in {"structure", "useful_god", "timing", "wealth", "career"}
    if mode == "hidden_factor_calibration":
        return claim.domain in {"hidden_factor", "useful_god"} or claim.needs_user_calibration
    if mode == "timing":
        return claim.domain == "timing" or claim.claim_level == "timing"
    return claim.domain == domain


def _claim_score(claim: DiagnosisClaim, selected_domain: DiagnosisDomain) -> float:
    score = {"high": 1.0, "medium": 0.68, "low": 0.36}.get(claim.confidence_band, 0.5)
    if claim.domain == selected_domain:
        score += 0.18
    if claim.claim_level == "domain":
        score += 0.2
    if claim.claim_level == "path":
        score += 0.12
    if claim.claim_level == "timing":
        score += 0.1
    if claim.needs_user_calibration:
        score -= 0.08
    if claim.blocked_overclaim:
        score -= 0.03
    return score


def _safeguards(claims: Sequence[DiagnosisClaim], graph: DiagnosisGraph) -> list[str]:
    rows = [
        "central_brain_selects_claims_not_facts",
        "diagnosis_graph_edges_must_reference_existing_nodes",
        "llm_expression_only_after_claim_selection",
    ]
    if any(claim.blocked_overclaim for claim in claims):
        rows.append("preserve_blocked_overclaim_boundaries")
    if any(claim.needs_user_calibration for claim in claims):
        rows.append("route_calibration_to_question_loop")
    if graph.top_claim_ids:
        rows.append("use_graph_top_claims_as_selection_prior")
    return rows


def _training_routes(claims: Sequence[DiagnosisClaim], selected_domain: DiagnosisDomain) -> list[str]:
    routes = ["real_bazi_diagnosis_route_quality", f"domain_claim_quality:{selected_domain}"]
    if any(claim.needs_user_calibration for claim in claims):
        routes.append("question_strategy_calibration")
    if any(claim.claim_level == "timing" for claim in claims):
        routes.append("timing_activation_claim_quality")
    if selected_domain == "hidden_factor" or any(claim.domain == "hidden_factor" for claim in claims):
        routes.append("hidden_factor_boundary_quality")
    return _dedupe(routes)


def _followup_reason(claims: Sequence[DiagnosisClaim], selected_question_id: str | None) -> str:
    if not any(claim.needs_user_calibration for claim in claims):
        return ""
    prefix = f"selected_question:{selected_question_id}; " if selected_question_id else ""
    domains = _dedupe([claim.domain for claim in claims if claim.needs_user_calibration])
    return f"{prefix}calibration_required_for:{','.join(domains)}"


def _dedupe_claims(claims: Sequence[DiagnosisClaim]) -> list[DiagnosisClaim]:
    seen: set[str] = set()
    out: list[DiagnosisClaim] = []
    for claim in claims:
        if claim.claim_id in seen:
            continue
        seen.add(claim.claim_id)
        out.append(claim)
    return out


def _dedupe(values: Sequence[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value and value not in out:
            out.append(value)
    return out


def _level_rank(value: str) -> int:
    order = ["domain", "path", "timing", "portrait", "feature", "question", "fact"]
    return order.index(value) if value in order else 99


def _band_rank(value: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(value, 3)
