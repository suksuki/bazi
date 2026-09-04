from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Response, status

from abu_v60.api.identity import SessionDependency
from abu_v60.db import engine
from abu_v60.experience.home import HomeExperienceService, HomeExperienceUnavailableError

router = APIRouter(prefix="/api/v60/experience", tags=["public-mingli-experience"])
service = HomeExperienceService(engine)


def public_home_projection(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Project the private Home onto the public life-tree reading shell."""

    return {
        "scope": "MINGLI_HOME",
        "profile": snapshot["profile"],
        "case": snapshot["case"],
        "case_options": [
            {
                key: item[key]
                for key in (
                    "case_ref",
                    "profile_ref",
                    "display_name",
                    "gender",
                    "calendar_type",
                    "birth_date",
                    "birth_time",
                    "birth_location",
                    "timezone",
                    "lunar_leap_month",
                    "status",
                    "pillars",
                    "active",
                    "stage_subject_id",
                    "subject_kind",
                    "identity_badge",
                    "birth_location_status",
                )
            }
            for item in snapshot["case_options"]
            if item["subject_kind"] in {"HUMAN_OWNER", "HUMAN_REFERENCE"}
        ],
        "chart": snapshot["chart"],
        "life_case": {
            key: snapshot["life_case"][key]
            for key in (
                "life_case_revision_ref",
                "revision",
                "status",
                "revision_hash",
            )
        },
        "tree": {
            key: snapshot["tree"][key]
            for key in (
                "tree_ref",
                "projection_version",
                "scene_ref",
                "phenotype",
                "read_only",
                "source_kind",
            )
        },
        "privacy": {"private_to_account": True},
    }


@router.get("/home")
def public_home_experience(
    response: Response,
    session: SessionDependency,
) -> dict[str, Any]:
    """Return only the data used by the public life-tree and reading shell."""

    try:
        snapshot = service.snapshot(account_ref=session.account.account_ref)
    except HomeExperienceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    response.headers["Cache-Control"] = "private, no-store"
    return public_home_projection(snapshot)
