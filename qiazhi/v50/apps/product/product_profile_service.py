from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from core.contracts import BirthInputCanonical
from core.engines import BirthCalendarResolutionError, resolve_birth_input_pillars
from core.life_case import LifeCase, LifeCaseRevision
from product.agent_case_store import AgentCaseStore


def supersede_profile_life_cases(
    *,
    case_store: AgentCaseStore,
    user_id: str,
    profile_id: str,
) -> int:
    changed = 0
    for row in case_store.list_for_user(user_id=user_id):
        if str(row.get("profile_id") or "") != profile_id or not row.get("life_case"):
            continue
        life_case = LifeCase.model_validate(row["life_case"])
        if life_case.status != "active":
            continue
        now = datetime.now(timezone.utc).isoformat()
        life_case = life_case.model_copy(update={
            "status": "superseded",
            "chart_version": life_case.chart_version.model_copy(update={"active": False}),
            "revisions": [
                *life_case.revisions,
                LifeCaseRevision(
                    revision_id=f"life-revision-{uuid4().hex[:16]}",
                    kind="chart_version_changed",
                    created_at=now,
                    summary="出生资料已修改；旧命盘版本及其洞察保留审计，但不再作为当前认知。",
                ),
            ],
            "updated_at": now,
        })
        row["life_case"] = life_case.model_dump(mode="json")
        case_store.save(
            case_id=str(row["case_id"]),
            user_id=user_id,
            profile_id=profile_id,
            payload=row,
        )
        changed += 1
    return changed


def resolve_profile_birth(birth_input: BirthInputCanonical) -> BirthInputCanonical:
    try:
        resolved = resolve_birth_input_pillars(birth_input)
    except BirthCalendarResolutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not all((resolved.year_pillar, resolved.month_pillar, resolved.day_pillar, resolved.hour_pillar)):
        raise HTTPException(status_code=422, detail="complete_pillars_required")
    return resolved
