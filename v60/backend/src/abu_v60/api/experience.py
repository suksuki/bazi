from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from abu_v60.api.identity import SessionDependency
from abu_v60.db import engine
from abu_v60.decision import (
    DecisionNotFinal,
    ReasonerProviderError,
    ReasonerRuntimeUnavailable,
)
from abu_v60.experience.home import (
    HomeExperienceService,
    HomeExperienceUnavailableError,
)
from abu_v60.mingli import (
    MechanismComparisonUnavailableError,
    RelationEffectEvidenceMaterialConflictError,
    RelationEffectEvidenceMaterialError,
    RelationEffectEvidenceMaterialRequest,
    RelationEffectEvidencePreparationRequest,
    RelationEffectEvidenceRequestConflictError,
    RelationEffectEvidenceRequestError,
)

router = APIRouter(prefix="/api/v60/experience", tags=["experience"])
service = HomeExperienceService(engine)


@router.get("/home")
def home_experience(session: SessionDependency) -> dict[str, Any]:
    try:
        return service.snapshot(account_ref=session.account.account_ref)
    except HomeExperienceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/home/mechanism-comparison")
def compare_home_mechanisms(session: SessionDependency) -> dict[str, Any]:
    try:
        return service.compare_mechanisms(
            account_ref=session.account.account_ref,
        )
    except HomeExperienceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except MechanismComparisonUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ReasonerRuntimeUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ReasonerProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except DecisionNotFinal as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/home/relation-effect-evidence-request")
def request_relation_effect_evidence(
    payload: RelationEffectEvidencePreparationRequest,
    session: SessionDependency,
) -> dict[str, Any]:
    try:
        receipt = service.request_relation_effect_evidence(
            account_ref=session.account.account_ref,
            request=payload,
        )
    except (
        HomeExperienceUnavailableError,
        RelationEffectEvidenceRequestConflictError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except RelationEffectEvidenceRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return receipt.model_dump(mode="json")


@router.post("/home/relation-effect-evidence-material")
def register_relation_effect_evidence_material(
    payload: RelationEffectEvidenceMaterialRequest,
    session: SessionDependency,
) -> dict[str, Any]:
    try:
        record = service.register_relation_effect_evidence_material(
            account_ref=session.account.account_ref,
            request=payload,
        )
    except (
        HomeExperienceUnavailableError,
        RelationEffectEvidenceMaterialConflictError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except RelationEffectEvidenceMaterialError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return record.model_dump(mode="json")
