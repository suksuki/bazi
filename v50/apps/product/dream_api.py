from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from experience.dream import DREAM_PILOT_CONSENT_VERSION
from experience.dream_navigation import (
    DreamControlCredential,
    DreamNavigationSample,
    DreamWorldPosition,
)
from product.agent_case_store import AgentCaseStore
from product.dream_feature import DreamFeaturePolicy
from product.dream_game_service import DreamGameError, DreamGameService
from product.dream_service import DreamBridgeError, DreamJourneyService
from product.dream_store_contracts import DreamStore
from product.product_store import ProductStore
from product.relation_work_p0_service import RelationWorkP0Service


DREAM_API_PREFIX = "/api/v50/dream"


class DreamVisitRequest(BaseModel):
    home_case_id: str = Field(default="", max_length=180)
    client_instance_id: str = Field(min_length=8, max_length=180)
    takeover: bool = False


class DreamControlTakeoverRequest(BaseModel):
    client_instance_id: str = Field(min_length=8, max_length=180)


class DreamTreeSelectionRequest(BaseModel):
    scene_ref: str = Field(min_length=16, max_length=180)


class DreamConsentRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=180)
    accepted: Literal[True]
    consent_version: Literal[DREAM_PILOT_CONSENT_VERSION] = DREAM_PILOT_CONSENT_VERSION


class DreamConsentWithdrawalRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=180)
    confirmed: Literal[True]


class DreamMirrorOpenRequest(BaseModel):
    onecanvas_view_ref: str = Field(min_length=32, max_length=180)
    navigation: DreamNavigationSample


class DreamRecoveryRequest(BaseModel):
    navigation: DreamNavigationSample
    recovery_sequence: int = Field(ge=1)


class DreamDepartureIntentRequest(BaseModel):
    active: bool


class DreamDepartureCommitRequest(BaseModel):
    trigger: Literal["SPATIAL_BOUNDARY", "SEMANTIC_EXIT"]
    navigation: DreamNavigationSample
    boundary_position: DreamWorldPosition | None = None
    commit_sequence: int = Field(ge=1)


class DreamGuestAnchorMigrationRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=180)
    guest_anchor_capability: str = Field(min_length=32, max_length=512)
    accepted: Literal[True]


class DreamGameDivinationRequest(BaseModel):
    explicit_user_intent: Literal[True]
    idempotency_key: str = Field(min_length=8, max_length=180)


class DreamGameLearningAnswerRequest(BaseModel):
    option_id: str = Field(min_length=1, max_length=180)
    idempotency_key: str = Field(min_length=8, max_length=180)


class DreamRealityQuestionAnswerRequest(BaseModel):
    question_instance_id: str = Field(min_length=1, max_length=180)
    option_id: str = Field(min_length=1, max_length=180)
    idempotency_key: str = Field(min_length=8, max_length=180)


class DreamGameJudgmentSealRequest(BaseModel):
    selected_outcome_option_id: Literal["yes", "no", "partial_or_unclear"]
    confidence_basis_points: int = Field(ge=0, le=10000)
    node_refs: list[str] = Field(default_factory=list, max_length=8)
    relation_refs: list[str] = Field(default_factory=list, max_length=8)
    interpretation: str = Field(default="", max_length=1200)
    evidence_refs: list[str] = Field(default_factory=list, max_length=24)
    strongest_alternative: str = Field(min_length=1, max_length=1000)
    disconfirmation_condition: str = Field(min_length=1, max_length=1000)
    idempotency_key: str = Field(min_length=8, max_length=180)
    confirmed: Literal[True]


class DreamGameRevealRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=180)


class DreamGameFlowerCloseRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=180)
    confirmed: Literal[True]


def create_dream_router(
    *,
    product_store: ProductStore,
    session_cookie: str,
    case_store: AgentCaseStore,
    dream_store: DreamStore,
    feature_policy: DreamFeaturePolicy,
    relation_work_service: RelationWorkP0Service | None = None,
) -> APIRouter:
    router = APIRouter(prefix=DREAM_API_PREFIX, tags=["abu-dream-bridge"])
    service = DreamJourneyService(
        case_store=case_store,
        dream_store=dream_store,
        feature_policy=feature_policy,
    )
    game_service = DreamGameService(
        journey=service,
        store=dream_store,
        relation_work_service=relation_work_service,
    )

    def user_id(request: Request) -> str:
        token = request.cookies.get(session_cookie, "")
        account = product_store.account_for_token(token) if token else None
        if not account:
            raise HTTPException(status_code=401, detail="authentication_required")
        return str(account["user_id"])

    def control_credential(request: Request) -> DreamControlCredential:
        try:
            return DreamControlCredential(
                client_instance_id=request.headers.get("x-dream-client-instance", ""),
                lease_id=request.headers.get("x-dream-lease-id", ""),
                lease_epoch=int(request.headers.get("x-dream-lease-epoch", "0")),
                fence_token=int(request.headers.get("x-dream-fence-token", "0")),
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=409, detail="dream_control_lease_required") from exc

    @router.get("/status")
    def feature_status(
        request: Request,
        case_id: str = Query(default="", max_length=180),
    ) -> dict[str, object]:
        return service.feature_status(
            user_id=user_id(request),
            case_id=case_id,
        ).model_dump(mode="json")

    @router.get("/consent")
    def consent_status(
        request: Request,
        case_id: str = Query(min_length=1, max_length=180),
    ) -> dict[str, object]:
        try:
            status = service.consent_status(user_id=user_id(request), case_id=case_id)
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return status.model_dump(mode="json")

    @router.post("/consent")
    def grant_consent(
        payload: DreamConsentRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            status = service.grant_consent(
                user_id=user_id(request),
                case_id=payload.case_id,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return status.model_dump(mode="json")

    @router.post("/consent/withdraw")
    def withdraw_consent(
        payload: DreamConsentWithdrawalRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            status = service.withdraw_consent(
                user_id=user_id(request),
                case_id=payload.case_id,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return status.model_dump(mode="json")

    @router.post("/visits")
    def create_visit(payload: DreamVisitRequest, request: Request) -> dict[str, object]:
        try:
            visit, lease = service.create_or_resume_visit(
                user_id=user_id(request),
                home_case_id=payload.home_case_id,
                client_instance_id=payload.client_instance_id,
                takeover=payload.takeover,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return service.session_view(visit=visit, lease=lease).model_dump(mode="json")

    @router.get("/visits/{visit_id}")
    def read_visit(visit_id: str, request: Request) -> dict[str, object]:
        try:
            credential = control_credential(request)
            visit = service.get_visit(
                user_id=user_id(request),
                visit_id=visit_id,
                credential=credential,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return service.session_view(
            visit=visit,
            credential=credential,
        ).model_dump(mode="json")

    @router.post("/visits/{visit_id}/control/takeover")
    def takeover_visit_control(
        visit_id: str,
        payload: DreamControlTakeoverRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            visit, lease = service.takeover_visit_control(
                user_id=user_id(request),
                visit_id=visit_id,
                client_instance_id=payload.client_instance_id,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return service.session_view(visit=visit, lease=lease).model_dump(mode="json")

    @router.post("/visits/{visit_id}/enter")
    def enter_visit(visit_id: str, request: Request) -> dict[str, object]:
        try:
            credential = control_credential(request)
            visit = service.enter(
                user_id=user_id(request),
                visit_id=visit_id,
                credential=credential,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return service.session_view(
            visit=visit,
            credential=credential,
        ).model_dump(mode="json")

    @router.get("/visits/{visit_id}/encounter")
    def encounter(visit_id: str, request: Request) -> dict[str, object]:
        try:
            projection = service.encounter(
                user_id=user_id(request),
                visit_id=visit_id,
                credential=control_credential(request),
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return projection.model_dump(mode="json")

    @router.post("/visits/{visit_id}/select-tree")
    def select_tree(
        visit_id: str,
        payload: DreamTreeSelectionRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            visit = service.select_tree(
                user_id=user_id(request),
                visit_id=visit_id,
                public_scene_ref=payload.scene_ref,
                credential=control_credential(request),
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return service.session_view(
            visit=visit,
            credential=control_credential(request),
        ).model_dump(mode="json")

    @router.get("/visits/{visit_id}/trees/{scene_ref}")
    def tree_projection(
        visit_id: str,
        scene_ref: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            projection = service.tree_projection(
                user_id=user_id(request),
                visit_id=visit_id,
                public_scene_ref=scene_ref,
                credential=control_credential(request),
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return projection.model_dump(mode="json")

    @router.get("/visits/{visit_id}/trees/{scene_ref}/mirror")
    def mirror_projection(
        visit_id: str,
        scene_ref: str,
        request: Request,
        view_ref: str = Query(min_length=32, max_length=180),
    ) -> dict[str, object]:
        try:
            projection = service.mirror_projection(
                user_id=user_id(request),
                visit_id=visit_id,
                public_scene_ref=scene_ref,
                onecanvas_view_ref=view_ref,
                credential=control_credential(request),
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return projection.model_dump(mode="json")

    @router.post("/visits/{visit_id}/trees/{scene_ref}/reveal")
    def reveal_tree(
        visit_id: str,
        scene_ref: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            projection = service.reveal_projection(
                user_id=user_id(request),
                visit_id=visit_id,
                public_scene_ref=scene_ref,
                credential=control_credential(request),
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return projection.model_dump(mode="json")

    @router.post("/visits/{visit_id}/mirror/open")
    def open_mirror(
        visit_id: str,
        payload: DreamMirrorOpenRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            visit = service.open_mirror(
                user_id=user_id(request),
                visit_id=visit_id,
                onecanvas_view_ref=payload.onecanvas_view_ref,
                navigation_sample=payload.navigation,
                credential=control_credential(request),
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return service.session_view(
            visit=visit,
            credential=control_credential(request),
        ).model_dump(mode="json")

    @router.post("/visits/{visit_id}/mirror/close")
    def close_mirror(visit_id: str, request: Request) -> dict[str, object]:
        try:
            credential = control_credential(request)
            visit = service.close_mirror(
                user_id=user_id(request),
                visit_id=visit_id,
                credential=credential,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return service.session_view(
            visit=visit,
            credential=credential,
        ).model_dump(mode="json")

    @router.get("/visits/{visit_id}/trees/{scene_ref}/mirror/context")
    def mirror_context(
        visit_id: str,
        scene_ref: str,
        request: Request,
        stage: str = Query(default="natal", max_length=40),
        selected: str = Query(default="", max_length=240),
        layer: str = Query(default="overview", max_length=80),
    ) -> dict[str, object]:
        try:
            return service.mirror_context(
                user_id=user_id(request),
                visit_id=visit_id,
                public_scene_ref=scene_ref,
                stage=stage,
                selected_object_ref=selected,
                visible_layer=layer,
                credential=control_credential(request),
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc

    @router.post("/visits/{visit_id}/control/heartbeat")
    def heartbeat(visit_id: str, request: Request) -> dict[str, object]:
        try:
            view = service.heartbeat(
                user_id=user_id(request),
                visit_id=visit_id,
                credential=control_credential(request),
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return view.model_dump(mode="json")

    @router.post("/visits/{visit_id}/recovery/checkpoint")
    def checkpoint(
        visit_id: str,
        payload: DreamRecoveryRequest,
        request: Request,
    ) -> dict[str, object]:
        credential = control_credential(request)
        try:
            visit, saved = service.checkpoint(
                user_id=user_id(request),
                visit_id=visit_id,
                sample=payload.navigation,
                recovery_sequence=payload.recovery_sequence,
                credential=credential,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return {
            "visit": service.session_view(
                visit=visit,
                credential=credential,
            ).model_dump(mode="json"),
            "checkpoint": saved.model_dump(mode="json"),
        }

    @router.post("/visits/{visit_id}/suspend")
    def suspend(
        visit_id: str,
        payload: DreamRecoveryRequest,
        request: Request,
    ) -> dict[str, object]:
        credential = control_credential(request)
        try:
            visit = service.suspend(
                user_id=user_id(request),
                visit_id=visit_id,
                sample=payload.navigation,
                recovery_sequence=payload.recovery_sequence,
                credential=credential,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return service.session_view(visit=visit, credential=credential).model_dump(mode="json")

    @router.post("/visits/{visit_id}/recover")
    def recover(visit_id: str, request: Request) -> dict[str, object]:
        credential = control_credential(request)
        try:
            visit = service.recover(
                user_id=user_id(request),
                visit_id=visit_id,
                credential=credential,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return service.session_view(visit=visit, credential=credential).model_dump(mode="json")

    @router.post("/visits/{visit_id}/departure/intent")
    def departure_intent(
        visit_id: str,
        payload: DreamDepartureIntentRequest,
        request: Request,
    ) -> dict[str, object]:
        credential = control_credential(request)
        try:
            visit = service.set_departure_intent(
                user_id=user_id(request),
                visit_id=visit_id,
                active=payload.active,
                credential=credential,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return service.session_view(visit=visit, credential=credential).model_dump(mode="json")

    @router.post("/visits/{visit_id}/departure/commit")
    def commit_departure(
        visit_id: str,
        payload: DreamDepartureCommitRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            result = service.commit_departure(
                user_id=user_id(request),
                visit_id=visit_id,
                trigger=payload.trigger,
                sample=payload.navigation,
                boundary_position=payload.boundary_position,
                commit_sequence=payload.commit_sequence,
                credential=control_credential(request),
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return result.model_dump(mode="json")

    @router.get("/visits/{visit_id}/departure/result")
    def departure_result(
        visit_id: str,
        request: Request,
        commit_sequence: int = Query(ge=1),
    ) -> dict[str, object]:
        try:
            result = service.departure_result(
                user_id=user_id(request),
                visit_id=visit_id,
                commit_sequence=commit_sequence,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return result.model_dump(mode="json")

    @router.post("/anchors/migrate-guest")
    def migrate_guest_anchor(
        payload: DreamGuestAnchorMigrationRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            result = service.migrate_guest_anchor(
                user_id=user_id(request),
                case_id=payload.case_id,
                capability=payload.guest_anchor_capability,
                accepted=payload.accepted,
            )
        except DreamBridgeError as exc:
            raise _http_error(exc) from exc
        return result.model_dump(mode="json")

    @router.get("/visits/{visit_id}/game/content-gate")
    def dream_game_content_gate(visit_id: str, request: Request) -> dict[str, object]:
        try:
            return game_service.content_gate(
                user_id=user_id(request),
                visit_id=visit_id,
                credential=control_credential(request),
            )
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.get("/visits/{visit_id}/game/rounds")
    def dream_game_rounds(visit_id: str, request: Request) -> list[dict[str, object]]:
        try:
            return [
                item.model_dump(mode="json")
                for item in game_service.round_cards(
                    user_id=user_id(request),
                    visit_id=visit_id,
                    credential=control_credential(request),
                )
            ]
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post("/visits/{visit_id}/game/rounds/{round_id}/start")
    def dream_game_start_round(
        visit_id: str,
        round_id: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.start_round(
                user_id=user_id(request),
                visit_id=visit_id,
                round_id=round_id,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.get(
        "/visits/{visit_id}/game/rounds/{round_id}/reality-question"
    )
    def dream_reality_question(
        visit_id: str,
        round_id: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.reality_question(
                user_id=user_id(request),
                visit_id=visit_id,
                round_id=round_id,
                credential=control_credential(request),
            )
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post(
        "/visits/{visit_id}/game/rounds/{round_id}/reality-question/answer"
    )
    def dream_reality_question_answer(
        visit_id: str,
        round_id: str,
        payload: DreamRealityQuestionAnswerRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.answer_reality_question(
                user_id=user_id(request),
                visit_id=visit_id,
                round_id=round_id,
                question_instance_id=payload.question_instance_id,
                selected_option_id=payload.option_id,
                idempotency_key=payload.idempotency_key,
                credential=control_credential(request),
            )
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.get("/visits/{visit_id}/game/attempts/{attempt_id}")
    def dream_game_read_attempt(
        visit_id: str,
        attempt_id: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.read_attempt(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post("/visits/{visit_id}/game/attempts/{attempt_id}/lenses/{lens}")
    def dream_game_observe_lens(
        visit_id: str,
        attempt_id: str,
        lens: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.observe_lens(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                lens=lens,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post("/visits/{visit_id}/game/attempts/{attempt_id}/question/open")
    def dream_game_open_question(
        visit_id: str,
        attempt_id: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.open_question(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post(
        "/visits/{visit_id}/game/attempts/{attempt_id}"
        "/learning/{question_id}/answer"
    )
    def dream_game_answer_learning_question(
        visit_id: str,
        attempt_id: str,
        question_id: str,
        payload: DreamGameLearningAnswerRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.answer_learning_question(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                question_id=question_id,
                option_id=payload.option_id,
                idempotency_key=payload.idempotency_key,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post("/visits/{visit_id}/game/attempts/{attempt_id}/divination")
    def dream_game_cast_divination(
        visit_id: str,
        attempt_id: str,
        payload: DreamGameDivinationRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.cast_divination(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                idempotency_key=payload.idempotency_key,
                explicit_user_intent=payload.explicit_user_intent,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post("/visits/{visit_id}/game/attempts/{attempt_id}/judgment/start")
    def dream_game_begin_judgment(
        visit_id: str,
        attempt_id: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.begin_judgment(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post("/visits/{visit_id}/game/attempts/{attempt_id}/judgment/seal")
    def dream_game_seal_judgment(
        visit_id: str,
        attempt_id: str,
        payload: DreamGameJudgmentSealRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.seal_judgment(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                selected_outcome_option_id=payload.selected_outcome_option_id,
                confidence_basis_points=payload.confidence_basis_points,
                node_refs=payload.node_refs,
                relation_refs=payload.relation_refs,
                interpretation=payload.interpretation,
                evidence_refs=payload.evidence_refs,
                strongest_alternative=payload.strongest_alternative,
                disconfirmation_condition=payload.disconfirmation_condition,
                idempotency_key=payload.idempotency_key,
                confirmed=payload.confirmed,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post("/visits/{visit_id}/game/attempts/{attempt_id}/reveal")
    def dream_game_reveal(
        visit_id: str,
        attempt_id: str,
        payload: DreamGameRevealRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.reveal(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                idempotency_key=payload.idempotency_key,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post("/visits/{visit_id}/game/attempts/{attempt_id}/flower/close")
    def dream_game_close_flower(
        visit_id: str,
        attempt_id: str,
        payload: DreamGameFlowerCloseRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.close_flower(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                idempotency_key=payload.idempotency_key,
                confirmed=payload.confirmed,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.get("/visits/{visit_id}/game/attempts/{attempt_id}/result")
    def dream_game_result(
        visit_id: str,
        attempt_id: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.read_result(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    @router.post("/visits/{visit_id}/game/attempts/{attempt_id}/complete")
    def dream_game_complete(
        visit_id: str,
        attempt_id: str,
        request: Request,
    ) -> dict[str, object]:
        try:
            return game_service.complete(
                user_id=user_id(request),
                visit_id=visit_id,
                attempt_id=attempt_id,
                credential=control_credential(request),
            ).model_dump(mode="json")
        except DreamGameError as exc:
            raise _game_http_error(exc) from exc

    return router


def _http_error(error: DreamBridgeError) -> HTTPException:
    detail = str(error)
    if detail == "dream_feature_disabled":
        return HTTPException(status_code=404, detail=detail)
    if detail in {"dream_visit_not_found", "dream_departure_result_not_found"}:
        return HTTPException(status_code=404, detail=detail)
    if detail in {
        "DREAM_ENCOUNTER_UNAVAILABLE",
        "dream_scene_authorization_unavailable",
        "dream_scene_source_version_changed",
        "dream_pilot_composition_invalid",
        "dream_human_consent_identity_conflict",
    }:
        return HTTPException(status_code=409, detail=detail)
    if detail in {
        "dream_human_case_not_owned",
        "dream_human_scene_not_formally_available",
    }:
        return HTTPException(status_code=422, detail=detail)
    if detail in {
        "dream_visit_version_conflict",
        "dream_tree_selection_locked",
        "dream_tree_selection_not_allowed",
        "dream_scene_not_selected",
        "dream_scene_not_in_encounter",
        "dream_encounter_not_ready",
        "dream_visit_completed",
        "dream_mirror_not_open",
        "dream_mirror_reference_invalid",
        "dream_tree_reveal_not_allowed",
        "dream_mirror_open_not_allowed",
        "dream_mirror_close_not_allowed",
        "dream_control_takeover_required",
        "dream_control_lease_required",
        "dream_control_lease_superseded",
        "dream_control_lease_stale",
        "dream_control_lease_expired",
        "dream_world_projection_required",
        "dream_world_projection_invalid",
        "dream_world_geometry_invalid",
        "dream_recovery_position_not_stable",
        "dream_recovery_sequence_stale",
        "dream_departure_intent_not_allowed",
        "dream_departure_requires_closed_mirror",
        "dream_spatial_departure_boundary_not_crossed",
        "dream_departure_sequence_stale",
        "dream_guest_anchor_unavailable",
    }:
        return HTTPException(status_code=409, detail=detail)
    if detail == "dream_guest_anchor_consent_required":
        return HTTPException(status_code=422, detail=detail)
    return HTTPException(status_code=422, detail=detail)


def _game_http_error(error: DreamGameError) -> HTTPException:
    detail = str(error)
    if detail in {"dream_game_round_not_found", "dream_game_attempt_not_found"}:
        return HTTPException(status_code=404, detail=detail)
    if detail in {
        "dream_game_content_revoked",
        "dream_game_projection_invalid",
        "dream_game_scene_source_changed",
        "dream_game_dual_seal_invalid",
        "dream_game_system_seal_invalid",
        "dream_game_evidence_not_revealable",
        "dream_game_attempt_version_conflict",
        "dream_game_record_conflict",
        "dream_game_learning_idempotency_conflict",
        "dream_game_outcome_not_revealable",
        "dream_game_answer_collection_closed",
        "dream_game_answer_already_sealed",
        "dream_game_flower_already_closed",
        "dream_game_flower_version_conflict",
        "dream_game_flower_answer_set_conflict",
        "dream_reality_question_answer_already_sealed",
        "dream_reality_question_lifecase_version_changed",
        "dream_control_takeover_required",
        "dream_control_lease_required",
        "dream_control_lease_superseded",
        "dream_control_lease_stale",
        "dream_control_lease_expired",
    }:
        return HTTPException(status_code=409, detail=detail)
    return HTTPException(status_code=422, detail=detail)


__all__ = ["DREAM_API_PREFIX", "create_dream_router"]
