from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from product.agent_case_store import AgentCaseStore
from product.agent_runtime import AgentRuntimeServices, WorkspaceBaselineStartError
from product.product_store import ProductStore
from product.workspace_bootstrap import WorkspaceBootstrapError, WorkspaceBootstrapService


WORKSPACE_API_PREFIX = "/api/v50/experience/workspace"


class WorkspaceBootstrapRequest(BaseModel):
    profile_id: str = Field(default="", max_length=180)
    case_id: str = Field(default="", max_length=180)


def create_workspace_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    case_store: AgentCaseStore,
    agent_runtime: AgentRuntimeServices,
) -> APIRouter:
    router = APIRouter(prefix=WORKSPACE_API_PREFIX, tags=["case-workspace"])
    bootstrap_service = WorkspaceBootstrapService(
        product_store=product_store,
        case_store=case_store,
    )

    def authenticated_account(request: Request) -> dict[str, object]:
        token = request.cookies.get(session_cookie, "")
        account = product_store.account_for_token(token) if token else None
        if not account:
            raise HTTPException(status_code=401, detail="authentication_required")
        return account

    @router.post("/bootstrap")
    def workspace_bootstrap(
        payload: WorkspaceBootstrapRequest,
        request: Request,
    ) -> dict[str, object]:
        account = authenticated_account(request)
        try:
            response = bootstrap_service.issue(
                account=account,
                requested_profile_id=payload.profile_id,
                requested_case_id=payload.case_id,
            )
        except WorkspaceBootstrapError as exc:
            detail = str(exc)
            status = 404 if detail in {
                "workspace_case_not_found",
                "workspace_profile_not_found",
            } else 422
            raise HTTPException(status_code=status, detail=detail) from exc
        return response.model_dump(mode="json")

    @router.post("/cases/{case_id}/baseline")
    def start_workspace_baseline(case_id: str, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        try:
            return agent_runtime.workspace_baseline.start(
                case_id=case_id,
                account=account,
            )
        except WorkspaceBaselineStartError as exc:
            detail = str(exc)
            status = 404 if detail == "mingli_case_not_found" else (
                503 if detail == "baseline_job_create_failed" else 409
            )
            raise HTTPException(status_code=status, detail=detail) from exc

    @router.get("/jobs/{job_id}")
    def workspace_cognitive_job(job_id: str, request: Request) -> dict[str, object]:
        account = authenticated_account(request)
        job = agent_runtime.context.job_store.get(
            job_id=job_id,
            user_id=str(account["user_id"]),
        )
        if job is None:
            raise HTTPException(status_code=404, detail="cognitive_job_not_found")
        return {
            "status": str(job.get("status") or "queued"),
            "job_id": job_id,
            "case_id": str(job.get("case_id") or ""),
        }

    return router


__all__ = ["WORKSPACE_API_PREFIX", "create_workspace_router"]
