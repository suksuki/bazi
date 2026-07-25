from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request

from core.life_case import LifeCase
from core.mingli_agent import (
    CaseBeliefState,
    MingliCognitiveRecord,
    build_case_belief_state,
)
from experience.workspace import (
    CaseWorkspaceState,
    build_case_workspace_state,
)
from product.agent_case_store import AgentCaseStore
from product.agent_job_store import AgentJobStore
from product.product_store import ProductStore


@dataclass(frozen=True)
class AgentApiContext:
    """HTTP authority boundary for identity, role checks, and Case persistence."""

    product_store: ProductStore
    case_store: AgentCaseStore
    job_store: AgentJobStore
    session_cookie: str

    def account_for(self, request: Request) -> dict[str, object] | None:
        token = request.cookies.get(self.session_cookie, "")
        return self.product_store.account_for_token(token) if token else None

    def load_case(
        self,
        case_id: str,
        request: Request,
    ) -> tuple[dict[str, Any], dict[str, object] | None]:
        account = self.account_for(request)
        row = self.case_store.get(
            case_id=case_id,
            user_id=str(account["user_id"]) if account else None,
        )
        if row is None:
            raise HTTPException(status_code=404, detail="mingli_case_not_found")
        return row, account

    def mode_for(
        self,
        account: dict[str, object] | None,
        requested: str | None = None,
    ) -> str:
        role = str((account or {}).get("account_role") or "guest")
        allowed = {
            "guest": {"guest"},
            "member": {"member"},
            "practitioner": {"practitioner"},
            "research_master": {"research"},
            "admin": {"guest", "member", "practitioner", "research"},
        }.get(role, {"member"})
        defaults = {
            "guest": "guest",
            "member": "member",
            "practitioner": "practitioner",
            "research_master": "research",
            "admin": "member",
        }
        selected = requested or defaults.get(role, "member")
        if selected not in allowed:
            raise HTTPException(status_code=403, detail="product_mode_not_allowed")
        return selected

    @staticmethod
    def workspace_for(
        row: dict[str, Any],
        record: MingliCognitiveRecord,
    ) -> CaseBeliefState:
        payload = row.get("case_belief_state") or row.get("workspace")
        return CaseBeliefState.model_validate(payload) if payload else build_case_belief_state(record)

    @staticmethod
    def workspace_state_for(
        row: dict[str, Any],
        *,
        case_id: str,
        active_mode: str = "member",
    ) -> CaseWorkspaceState:
        payload = row.get("workspace_state")
        workspace_state = (
            CaseWorkspaceState.model_validate(payload)
            if payload
            else build_case_workspace_state(case_id=case_id, active_mode=active_mode)
        )
        return (
            workspace_state.model_copy(update={"active_mode": active_mode})
            if workspace_state.active_mode != active_mode
            else workspace_state
        )

    @staticmethod
    def life_case_for(row: dict[str, Any], *, write: bool = False) -> LifeCase:
        payload = row.get("life_case")
        if not payload:
            raise HTTPException(status_code=409, detail="formal_life_case_not_available")
        life_case = LifeCase.model_validate(payload)
        if write and (life_case.status != "active" or not life_case.chart_version.active):
            raise HTTPException(status_code=409, detail="life_case_read_only")
        return life_case

    def save_case_row(
        self,
        *,
        case_id: str,
        row: dict[str, Any],
        account: dict[str, object] | None,
    ) -> None:
        row.pop("workspace", None)
        self.case_store.save(
            case_id=case_id,
            user_id=str(account["user_id"]) if account else row.get("user_id"),
            profile_id=row.get("profile_id"),
            payload=row,
        )

    def append_job_event(
        self,
        *,
        job_id: str,
        event_type: str,
        payload: dict[str, Any],
        epistemic_status: str,
        job_status: str | None = None,
    ) -> None:
        self.job_store.append_event(
            job_id=job_id,
            event={
                "event_type": event_type,
                "epistemic_status": epistemic_status,
                "payload": payload,
            },
            status=job_status,
        )
