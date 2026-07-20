from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from experience.contracts import MingliExperienceEnvelope
from product.agent_case_store import AgentCaseStore
from product.canvas_projection import (
    ReadOnlyCanvasUnavailable,
    ReadOnlySixPillarCanvasService,
)
from product.legacy_usage import LegacyUsageStore
from product.onecanvas_structural import (
    OneCanvasStructuralError,
    compile_target_draft,
    compile_structural_variant,
    selection_catalog_payload,
)
from product.product_store import ProductStore
from product.theater_envelope import ProductExperienceEnvelopePort


EXPERIENCE_API_PREFIX = "/api/v50/experience"


class OneCanvasStructuralCompileRequest(BaseModel):
    selected_pillars: list[str] = Field(min_length=4, max_length=4)
    baseline_pillars: list[str] = Field(min_length=4, max_length=4)
    baseline_relations: list[dict[str, Any]]
    formal_path: dict[str, Any]
    baseline_timing: dict[str, Any]
    analysis_year: int = Field(ge=1800, le=2400)
    gender: Literal["male", "female", "unknown"]
    birth_year_hint: int | None = Field(default=None, ge=1900, le=2100)


class OneCanvasTargetPillars(BaseModel):
    year: str = Field(min_length=2, max_length=2)
    month: str = Field(min_length=2, max_length=2)
    day: str = Field(min_length=2, max_length=2)
    hour: str = Field(min_length=2, max_length=2)


class OneCanvasTargetConstraint(BaseModel):
    pillar: str = Field(default="", max_length=2)
    stem: str = Field(default="", max_length=1)
    branch: str = Field(default="", max_length=1)


class OneCanvasTargetDraftPillars(BaseModel):
    year: OneCanvasTargetConstraint = Field(default_factory=OneCanvasTargetConstraint)
    month: OneCanvasTargetConstraint = Field(default_factory=OneCanvasTargetConstraint)
    day: OneCanvasTargetConstraint = Field(default_factory=OneCanvasTargetConstraint)
    hour: OneCanvasTargetConstraint = Field(default_factory=OneCanvasTargetConstraint)


class OneCanvasTargetCompileRequest(BaseModel):
    target_draft_id: str = Field(default="", max_length=160)
    desired: OneCanvasTargetPillars | None = None
    target_draft: OneCanvasTargetDraftPillars | None = None
    selected_variant_id: str = Field(default="", max_length=160)
    baseline_pillars: list[str] = Field(min_length=4, max_length=4)
    baseline_relations: list[dict[str, Any]]
    formal_path: dict[str, Any]
    baseline_timing: dict[str, Any]
    analysis_year: int = Field(ge=1900, le=2100)
    gender: Literal["male", "female", "unknown"]
    cycle_year_anchor: int | None = Field(default=None, ge=1900, le=2100)

    @model_validator(mode="after")
    def _one_target_shape(self) -> "OneCanvasTargetCompileRequest":
        if (self.desired is None) == (self.target_draft is None):
            raise ValueError("onecanvas_exactly_one_target_shape_required")
        return self


def create_experience_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    case_store: AgentCaseStore,
    legacy_usage_store: LegacyUsageStore,
) -> APIRouter:
    router = APIRouter(prefix=EXPERIENCE_API_PREFIX, tags=["mingli-experience"])
    envelope_port = ProductExperienceEnvelopePort(case_store=case_store)
    canvas_service = ReadOnlySixPillarCanvasService(case_store=case_store)

    def authenticated_account(request: Request) -> dict[str, object]:
        token = request.cookies.get(session_cookie, "")
        account = product_store.account_for_token(token) if token else None
        if not account:
            raise HTTPException(status_code=401, detail="authentication_required")
        return account

    @router.get("/cases")
    def list_experience_cases(request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        rows = case_store.list_for_user(user_id=str(account["user_id"]))
        cases: list[dict[str, Any]] = []
        seen_profiles: set[str] = set()
        for row in rows:
            case_id = str(row.get("case_id") or "")
            life_case = row.get("life_case") if isinstance(row.get("life_case"), dict) else {}
            chart_version = life_case.get("chart_version") if isinstance(life_case.get("chart_version"), dict) else {}
            baseline = life_case.get("baseline_insight") if isinstance(life_case.get("baseline_insight"), dict) else {}
            if (
                not case_id
                or life_case.get("status") != "active"
                or not chart_version.get("active")
                or baseline.get("status") != "committed"
            ):
                continue
            profile_id = str(row.get("profile_id") or "")
            profile_key = profile_id or case_id
            if profile_key in seen_profiles:
                continue
            seen_profiles.add(profile_key)
            profile = (
                product_store.get_profile(user_id=str(account["user_id"]), profile_id=profile_id)
                if profile_id
                else None
            )
            cases.append({
                "case_id": case_id,
                "profile_id": profile_id or None,
                "display_name": str((profile or {}).get("display_name") or "当前命盘"),
                "case_version": str(life_case.get("case_version") or ""),
                "status": str(life_case.get("status") or row.get("status") or "unavailable"),
                "baseline_available": bool(life_case.get("baseline_insight")),
                "experience_url": f"/experience?case={case_id}",
            })
        return {
            "status": "experience_cases_ready",
            "cases": cases,
            "cognition_source": "LifeCase",
            "legacy_report_used": False,
        }

    @router.get(
        "/cases/{case_id}/baseline",
        response_model=MingliExperienceEnvelope,
    )
    def baseline_experience(case_id: str, request: Request) -> MingliExperienceEnvelope:
        account = authenticated_account(request)
        try:
            return envelope_port.issue_envelope(
                participant_id=str(account["user_id"]),
                topic_id="whole-chart-baseline",
                topic_version="experience-next-v1",
                disclosure_level="approved_insights",
                case_id=case_id,
                permitted_capabilities=[
                    "narrated_workspace",
                    "four_pillar_stage",
                    "reasoning_path_stage",
                ],
            )
        except ValueError as exc:
            detail = str(exc)
            status = 404 if detail == "experience_case_not_found" else 409
            raise HTTPException(status_code=status, detail=detail) from exc

    @router.get("/cases/{case_id}/canvas")
    def read_only_canvas(case_id: str, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        try:
            return canvas_service.issue(
                case_id=case_id,
                participant_id=str(account["user_id"]),
                account_role=str(account.get("role") or "member"),
            )
        except ReadOnlyCanvasUnavailable as exc:
            detail = str(exc)
            status = 404 if detail == "experience_case_not_found" else 409
            raise HTTPException(status_code=status, detail=detail) from exc

    @router.get("/cases/{case_id}/canvas/context")
    def read_only_canvas_context(
        case_id: str,
        request: Request,
        stage: str,
        selected: str,
        layer: str,
    ) -> dict[str, object]:
        account = authenticated_account(request)
        try:
            context = canvas_service.issue_context(
                case_id=case_id,
                participant_id=str(account["user_id"]),
                account_role=str(account.get("role") or "member"),
                stage=stage,
                selected_object_ref=selected,
                visible_layer=layer,
            )
            return {
                "status": "canvas_context_ready",
                "context": context.model_dump(mode="json"),
                "llm_used": False,
                "formal_state_writes": False,
            }
        except ReadOnlyCanvasUnavailable as exc:
            detail = str(exc)
            status = 404 if detail in {"experience_case_not_found", "canvas_object_not_disclosed"} else 409
            raise HTTPException(status_code=status, detail=detail) from exc

    @router.get("/onecanvas/selection-catalog")
    def onecanvas_selection_catalog(request: Request) -> dict[str, object]:
        authenticated_account(request)
        return {
            "status": "onecanvas_selection_catalog_ready",
            "catalog": selection_catalog_payload(),
            "llm_used": False,
            "formal_state_writes": False,
        }

    @router.post("/onecanvas/structural-compile")
    def onecanvas_structural_compile(
        payload: OneCanvasStructuralCompileRequest,
        request: Request,
    ) -> dict[str, object]:
        authenticated_account(request)
        try:
            variant = compile_structural_variant(**payload.model_dump(mode="python"))
        except OneCanvasStructuralError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "status": "onecanvas_structural_variant_ready",
            "variant": variant,
            "llm_used": False,
            "formal_state_writes": False,
            "life_case_writes": False,
        }

    @router.post("/onecanvas/target-compile")
    def onecanvas_target_compile(
        payload: OneCanvasTargetCompileRequest,
        request: Request,
    ) -> dict[str, object]:
        authenticated_account(request)
        try:
            values = payload.model_dump(mode="python")
            desired = values.pop("desired")
            target_draft = values.pop("target_draft")
            compiled = compile_target_draft(
                desired=target_draft if target_draft is not None else desired,
                **values,
            )
        except OneCanvasStructuralError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "status": "onecanvas_target_resolved",
            **compiled,
            "llm_used": False,
            "formal_state_writes": False,
            "life_case_writes": False,
        }

    @router.get("/admin/legacy-usage")
    def legacy_usage_report(request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        if str(account.get("role") or "") != "admin":
            raise HTTPException(status_code=403, detail="admin_required")
        return {
            "status": "legacy_usage_ready",
            "records": legacy_usage_store.snapshot(),
            "raw_birth_data_logged": False,
            "raw_conversation_logged": False,
        }

    return router
