from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from typing import Any, Callable
from uuid import uuid4

from experience.dream_game import (
    BlindRoundCard,
    BlindRoundDefinition,
    DREAM_GAME_EVALUATION_POLICY_VERSION,
    DREAM_GAME_V50_BANNER,
    DREAM_FLOWER_PROTOCOL_VERSION,
    DivinationRecord,
    DreamGameAttempt,
    DreamGameAttemptView,
    DreamLearningAnswerRecord,
    DreamLearningQuestionPublic,
    DreamGameRecordEnvelope,
    DreamGameResultProjection,
    DreamGameState,
    DreamQuestionAttemptProgress,
    DreamQuestionProgressItem,
    DreamQuestionSetProjection,
    EvaluationRecord,
    FlowerClosureRecord,
    FlowerLifecycle,
    FlowerLifecycleView,
    JudgmentEvaluation,
    JudgmentSubmission,
    KnowledgeSeed,
    OutcomeRevealRecord,
    PreOutcomeDreamProjection,
    PreOutcomeDreamProjectionView,
    SharedFruit,
    UserJudgmentSeal,
    UserPathHypothesis,
)
from experience.dream_navigation import DreamControlCredential
from product.dream_game_content import (
    SIX_LENSES,
    canonical_json_hash,
    compile_v50_canonical_encounter,
    immutable_model_hash,
)
from product.dream_service import DreamBridgeError, DreamJourneyService
from product.dream_store_contracts import DreamStore, DreamStoreConflict
from product.relation_work_p0_service import (
    RelationWorkP0Conflict,
    RelationWorkP0Service,
    RelationWorkP0Unavailable,
)


class DreamGameError(ValueError):
    pass


def _selection_whisper(event_family: str) -> str:
    return {
        "JOB_CHANGE": "这棵树，正停在一次去留之前。",
        "CONTRACT_SIGNING": "这棵树，守着一份尚未落定的约定。",
        "RELOCATION_OR_TRAVEL": "这棵树，记着一条还没有走完的路。",
        "V50_STRUCTURE_PATH": "先读懂叶与枝，问题花才会开放。",
    }.get(event_family, "这棵树，有一件事仍在等待回答。")


class DreamGameService:
    """Run sealed blind rounds inside the existing authorized Dream Visit."""

    def __init__(
        self,
        *,
        journey: DreamJourneyService,
        store: DreamStore,
        relation_work_service: RelationWorkP0Service | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.journey = journey
        self.store = store
        self.relation_work_service = relation_work_service
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def content_gate(
        self,
        *,
        user_id: str,
        visit_id: str,
        credential: DreamControlCredential,
    ) -> dict[str, Any]:
        rounds = self._ensure_v50_rounds(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        verified = self.store.verified_real_game_content_count()
        return {
            "schema_version": "deepbazi.dream_game_content_gate.v1",
            "development_content": "V50_CANONICAL_ONLY",
            "simulated_round_count": 0,
            "v50_canonical_round_count": len(rounds),
            "verified_real_content_count": verified,
            "verified_real_content_required": 3,
            "verified_real_content_gate": f"{verified}/3",
            "verified_real_launch": "LOCKED" if verified < 3 else "ELIGIBLE_FOR_REVIEW",
            "banner": DREAM_GAME_V50_BANNER,
        }

    def round_cards(
        self,
        *,
        user_id: str,
        visit_id: str,
        credential: DreamControlCredential,
    ) -> list[BlindRoundCard]:
        rounds = self._ensure_v50_rounds(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        _visit, scenes = self._context(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        cards: list[BlindRoundCard] = []
        for index, item in enumerate(rounds):
            tree_available, tree_visual_profile = self._tree_profile(
                user_id=user_id,
                round_definition=item,
                scenes=scenes,
            )
            cards.append(BlindRoundCard(
                round_id=item.round_id,
                resident_scene_ref=item.resident_scene_ref,
                resident_label=item.resident_label,
                anonymous_label=f"梦树{index + 1}",
                event_family=item.event_family,
                question_preview="完成树上的结构理解后，问题花才会开放。",
                selection_whisper=_selection_whisper(item.event_family),
                evidence_class=item.evidence_class,
                development_only=item.development_only,
                banner=self._banner_for(item),
                content_state=item.content_state,
                knowledge_cutoff=item.question.knowledge_cutoff,
                tree_available=tree_available,
                tree_visual_profile=tree_visual_profile,
            ))
        return cards

    def reality_question(
        self,
        *,
        user_id: str,
        visit_id: str,
        round_id: str,
        credential: DreamControlCredential,
    ) -> dict[str, object]:
        visit, scenes = self._context(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        self._ensure_v50_rounds(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        round_definition = self._round(round_id)
        self._validate_round_access(
            round_definition=round_definition,
            scenes=scenes,
        )
        source_snapshot = round_definition.source_snapshot
        if source_snapshot is None:
            raise DreamGameError("dream_reality_question_snapshot_missing")
        grant, _scene = scenes[round_definition.resident_scene_ref]
        service = self._require_relation_work_service()
        try:
            return service.dream_reality_question_view(
                case_id=grant.case_id,
                participant_id=user_id,
                account_role="member",
                encounter_set_id=visit.encounter_set.encounter_set_id,
                round_id=round_id,
                expected_life_case_version=(
                    source_snapshot.source_life_case_version
                ),
            )
        except (RelationWorkP0Conflict, RelationWorkP0Unavailable) as exc:
            raise DreamGameError(str(exc)) from exc

    def answer_reality_question(
        self,
        *,
        user_id: str,
        visit_id: str,
        round_id: str,
        question_instance_id: str,
        selected_option_id: str,
        idempotency_key: str,
        credential: DreamControlCredential,
    ) -> dict[str, object]:
        visit, scenes = self._context(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        self._ensure_v50_rounds(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        round_definition = self._round(round_id)
        self._validate_round_access(
            round_definition=round_definition,
            scenes=scenes,
        )
        source_snapshot = round_definition.source_snapshot
        if source_snapshot is None:
            raise DreamGameError("dream_reality_question_snapshot_missing")
        grant, _scene = scenes[round_definition.resident_scene_ref]
        service = self._require_relation_work_service()
        try:
            return service.answer_dream_reality_question(
                case_id=grant.case_id,
                participant_id=user_id,
                account_role="member",
                encounter_set_id=visit.encounter_set.encounter_set_id,
                round_id=round_id,
                expected_life_case_version=(
                    source_snapshot.source_life_case_version
                ),
                question_instance_id=question_instance_id,
                selected_option_id=selected_option_id,
                idempotency_key=idempotency_key,
                now=self.clock(),
            )
        except (RelationWorkP0Conflict, RelationWorkP0Unavailable) as exc:
            raise DreamGameError(str(exc)) from exc

    def start_round(
        self,
        *,
        user_id: str,
        visit_id: str,
        round_id: str,
        credential: DreamControlCredential,
    ) -> DreamGameAttemptView:
        visit, scenes = self._context(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        self._ensure_v50_rounds(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        round_definition = self._round(round_id)
        self._validate_round_access(round_definition=round_definition, scenes=scenes)
        self._refresh_flower(round_definition)
        existing = self.store.find_game_attempt(
            round_id=round_id,
            viewer_id=user_id,
            visit_id=visit_id,
        )
        if existing is not None:
            return self._attempt_view(self._validated_attempt(
                user_id=user_id,
                visit_id=visit_id,
                attempt_id=existing.attempt_id,
                credential=credential,
            ))
        grant, _ = scenes[round_definition.resident_scene_ref]
        now = self.clock()
        attempt_id = f"dream-game-attempt-{uuid4().hex}"
        projection_ref = f"dream-game-projection-{secrets.token_hex(32)}"
        projection_payload = {
            "projection_ref": projection_ref,
            "round_id": round_id,
            "attempt_id": attempt_id,
            "viewer_id": user_id,
            "visit_id": visit_id,
            "case_namespace": visit.case_namespace,
            "resident_scene_ref": round_definition.resident_scene_ref,
            "resident_label": round_definition.resident_label,
            "authorization_version": grant.authorization_version,
            "knowledge_cutoff": round_definition.question.knowledge_cutoff,
            "clock_domain": round_definition.question.clock_domain,
            "source_snapshot_id": round_definition.frozen_projection.source_snapshot_id,
            "cutoff_verification_status": (
                round_definition.frozen_projection.cutoff_verification_status
            ),
            "expires_at": now + timedelta(hours=4),
            "frozen_projection_hash": round_definition.frozen_projection.projection_hash,
            "question": round_definition.question,
            "canvas": round_definition.frozen_projection.canvas_snapshot,
            "allowed_nodes": round_definition.frozen_projection.allowed_nodes,
            "allowed_relations": round_definition.frozen_projection.allowed_relations,
            "available_lenses": SIX_LENSES,
            "evidence_class": round_definition.evidence_class,
            "development_only": round_definition.development_only,
            "banner": self._banner_for(round_definition),
        }
        projection_payload["viewer_projection_hash"] = canonical_json_hash(
            _jsonable(projection_payload)
        )
        projection = PreOutcomeDreamProjection.model_validate(projection_payload)
        if round_definition.question_set is None:
            raise DreamGameError("dream_game_question_set_missing")
        if (
            round_definition.evidence_class == "V50_CANONICAL"
            and round_definition.question_set.content_status != "ACTIVE"
        ):
            raise DreamGameError("dream_game_question_bundle_not_active")
        question_progress = DreamQuestionAttemptProgress(
            question_set_id=round_definition.question_set.question_set_id,
            items=[
                DreamQuestionProgressItem(
                    question_id=item.question_id,
                    kind=item.kind,
                )
                for item in round_definition.question_set.questions
            ],
            updated_at=now,
        )
        prior_seal = (
            self.store.find_game_answer_seal(round_id=round_id, viewer_id=user_id)
            if round_definition.flower_protocol_version == DREAM_FLOWER_PROTOCOL_VERSION
            else None
        )
        prior_attempt = (
            self.store.get_game_attempt(
                attempt_id=prior_seal.attempt_id,
                viewer_id=user_id,
            )
            if prior_seal is not None
            else None
        )
        attempt = DreamGameAttempt(
            attempt_id=attempt_id,
            round_id=round_id,
            viewer_id=user_id,
            visit_id=visit_id,
            case_namespace=visit.case_namespace,
            resident_scene_ref=round_definition.resident_scene_ref,
            state=(
                prior_attempt.state
                if prior_attempt is not None
                else DreamGameState.ROUND_OBSERVING
            ),
            projection=projection,
            question_set_ref=round_definition.question_set.question_set_id,
            question_progress=(
                prior_attempt.question_progress
                if prior_attempt is not None
                else question_progress
            ),
            observed_lenses=(
                list(prior_attempt.observed_lenses) if prior_attempt is not None else []
            ),
            divination_ref=prior_attempt.divination_ref if prior_attempt is not None else "",
            submission_ref=prior_seal.submission_ref if prior_seal is not None else "",
            user_seal_ref=prior_seal.seal_id if prior_seal is not None else "",
            answer_source_attempt_id=prior_seal.attempt_id if prior_seal is not None else "",
            reveal_ref=prior_attempt.reveal_ref if prior_attempt is not None else "",
            evaluation_ref=prior_attempt.evaluation_ref if prior_attempt is not None else "",
            knowledge_seed_ref=(
                prior_attempt.knowledge_seed_ref if prior_attempt is not None else ""
            ),
            created_at=now,
            updated_at=now,
            state_history=(
                list(prior_attempt.state_history)
                if prior_attempt is not None
                else [
                    DreamGameState.ROUND_ELIGIBILITY_CHECK,
                    DreamGameState.PROJECTION_ISSUING,
                    DreamGameState.ROUND_OBSERVING,
                ]
            ),
        )
        try:
            return self._attempt_view(self.store.create_game_attempt(attempt))
        except DreamStoreConflict as exc:
            repeated = self.store.find_game_attempt(
                round_id=round_id,
                viewer_id=user_id,
                visit_id=visit_id,
            )
            if repeated is not None:
                return self._attempt_view(repeated)
            raise DreamGameError(str(exc)) from exc

    def read_attempt(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        credential: DreamControlCredential,
    ) -> DreamGameAttemptView:
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        return self._attempt_view(attempt)

    def observe_lens(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        lens: str,
        credential: DreamControlCredential,
    ) -> DreamGameAttemptView:
        if lens not in SIX_LENSES:
            raise DreamGameError("dream_game_lens_not_allowed")
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        if attempt.state not in {
            DreamGameState.ROUND_OBSERVING,
            DreamGameState.QUESTION_FLOWER_OPEN,
            DreamGameState.OPTIONAL_DIVINATION,
            DreamGameState.JUDGMENT_DRAFTING,
        }:
            raise DreamGameError("dream_game_observation_closed")
        if lens in attempt.observed_lenses:
            return self._attempt_view(attempt)
        return self._attempt_view(self._advance(
            attempt,
            state=attempt.state,
            observed_lenses=[*attempt.observed_lenses, lens],
        ))

    def answer_learning_question(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        question_id: str,
        option_id: str,
        idempotency_key: str,
        credential: DreamControlCredential,
    ) -> DreamGameAttemptView:
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        if attempt.state != DreamGameState.ROUND_OBSERVING:
            raise DreamGameError("dream_game_learning_question_closed")
        round_definition = self._round(attempt.round_id)
        question_set = round_definition.question_set
        progress = attempt.question_progress
        if question_set is None or progress is None:
            raise DreamGameError("dream_game_question_set_missing")
        if (
            question_set.question_set_id != attempt.question_set_ref
            or question_set.source_snapshot_id != attempt.projection.source_snapshot_id
        ):
            raise DreamGameError("dream_game_question_set_binding_invalid")
        question = next(
            (item for item in question_set.questions if item.question_id == question_id),
            None,
        )
        if question is None:
            raise DreamGameError("dream_game_learning_question_not_found")
        current_item = next(
            (item for item in progress.items if item.question_id == question_id),
            None,
        )
        if current_item is None:
            raise DreamGameError("dream_game_learning_progress_invalid")
        if current_item.status == "COMPLETED":
            return self._attempt_view(attempt)
        if not self._question_dependencies_complete(question, progress):
            raise DreamGameError("dream_game_learning_prerequisites_incomplete")
        option = next(
            (item for item in question.options if item.option_id == option_id),
            None,
        )
        if option is None:
            raise DreamGameError("dream_game_learning_option_invalid")

        key_hash = canonical_json_hash({"idempotency_key": idempotency_key})
        answer_id = (
            "dream-learning-answer-"
            + canonical_json_hash({
                "attempt": attempt_id,
                "question": question_id,
                "key": key_hash,
            })[:32]
        )
        existing = self.store.get_game_record(record_id=answer_id)
        if existing is not None:
            stored = DreamLearningAnswerRecord.model_validate(existing.payload)
            if stored.selected_option_id != option_id:
                raise DreamGameError("dream_game_learning_idempotency_conflict")
            current = self.store.get_game_attempt(
                attempt_id=attempt_id,
                viewer_id=user_id,
            )
            if current is None:
                raise DreamGameError("dream_game_attempt_not_found")
            return self._attempt_view(current)

        now = self.clock()
        correct = option_id == question.correct_option_id
        next_items = []
        for item in progress.items:
            if item.question_id != question_id:
                next_items.append(item)
                continue
            next_items.append(item.model_copy(update={
                "status": "COMPLETED" if correct else "RETRY_REQUIRED",
                "attempts": item.attempts + 1,
                "last_selected_option_id": option_id,
                "feedback": (
                    question.success_message if correct else question.retry_message
                ),
                "resolved_answer_ref_kind": (
                    option.answer_ref_kind if correct else "none"
                ),
                "resolved_answer_ref": option.answer_ref if correct else "",
                "resolved_evidence_refs": (
                    list(question.evidence_refs) if correct else []
                ),
                "completed_at": now if correct else None,
            }))
        flower_unlocked = all(item.status == "COMPLETED" for item in next_items)
        next_progress = DreamQuestionAttemptProgress(
            question_set_id=progress.question_set_id,
            items=next_items,
            flower_unlocked=flower_unlocked,
            updated_at=now,
        )
        answer_payload = {
            "answer_id": answer_id,
            "attempt_id": attempt_id,
            "round_id": attempt.round_id,
            "viewer_id": user_id,
            "question_set_id": question_set.question_set_id,
            "question_id": question_id,
            "selected_option_id": option_id,
            "correct": correct,
            "resolved_evidence_refs": (
                list(question.evidence_refs) if correct else []
            ),
            "idempotency_key_hash": key_hash,
            "answered_at": now,
            "immutable_hash": "0" * 64,
        }
        answer_payload["immutable_hash"] = immutable_model_hash(answer_payload)
        answer = DreamLearningAnswerRecord.model_validate(answer_payload)
        next_attempt = self._next_attempt(
            attempt,
            state=DreamGameState.ROUND_OBSERVING,
            question_progress=next_progress,
        )
        try:
            self._commit_bundle(
                next_attempt,
                [self._record("learning_answer", answer, viewer_id=user_id)],
                expected_row_version=attempt.row_version,
            )
        except DreamGameError as exc:
            if str(exc) != "dream_game_attempt_version_conflict":
                raise
            repeated = self.store.get_game_record(record_id=answer_id)
            current = self.store.get_game_attempt(
                attempt_id=attempt_id,
                viewer_id=user_id,
            )
            if repeated is None or current is None:
                raise
            return self._attempt_view(current)
        return self._attempt_view(next_attempt)

    def open_question(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        credential: DreamControlCredential,
    ) -> DreamGameAttemptView:
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        if attempt.state == DreamGameState.QUESTION_FLOWER_OPEN:
            return self._attempt_view(attempt)
        if attempt.state != DreamGameState.ROUND_OBSERVING:
            raise DreamGameError("dream_game_question_not_available")
        if attempt.question_progress is None or not attempt.question_progress.flower_unlocked:
            raise DreamGameError("dream_game_flower_prerequisites_incomplete")
        return self._attempt_view(self._advance(
            attempt,
            state=DreamGameState.QUESTION_FLOWER_OPEN,
        ))

    def cast_divination(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        idempotency_key: str,
        explicit_user_intent: bool,
        credential: DreamControlCredential,
    ) -> DreamGameAttemptView:
        if explicit_user_intent is not True:
            raise DreamGameError("dream_game_divination_explicit_intent_required")
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        if attempt.state not in {
            DreamGameState.QUESTION_FLOWER_OPEN,
            DreamGameState.OPTIONAL_DIVINATION,
            DreamGameState.JUDGMENT_DRAFTING,
        }:
            raise DreamGameError("dream_game_divination_not_available")
        if not attempt.projection.question.liuyao_permitted:
            raise DreamGameError("dream_game_divination_not_permitted")
        if attempt.divination_ref:
            return self._attempt_view(attempt)
        key_hash = canonical_json_hash({"idempotency_key": idempotency_key})
        record_id = f"dream-divination-{canonical_json_hash({'attempt': attempt_id, 'key': key_hash})[:32]}"
        existing = self.store.get_game_record(record_id=record_id)
        if existing is not None:
            recovered = self._advance(
                attempt,
                state=DreamGameState.OPTIONAL_DIVINATION,
                divination_ref=record_id,
            )
            return self._attempt_view(recovered)
        now = self.clock()
        lines = [sum(secrets.choice((2, 3)) for _ in range(3)) for _ in range(6)]
        payload = {
            "divination_id": record_id,
            "attempt_id": attempt_id,
            "round_id": attempt.round_id,
            "viewer_id": user_id,
            "explicit_user_intent": True,
            "question_id": attempt.projection.question.question_id,
            "exact_question": attempt.projection.question.neutral_question_text,
            "subject_ref": attempt.resident_scene_ref,
            "server_timestamp": now,
            "divination_temporality": "RETROSPECTIVE_BLIND",
            "line_values_bottom_up": lines,
            "moving_line_indexes": [index + 1 for index, value in enumerate(lines) if value in {6, 9}],
            "authorization_ref": attempt.projection.authorization_version,
            "idempotency_key_hash": key_hash,
        }
        payload["immutable_hash"] = immutable_model_hash(_jsonable(payload))
        divination = DivinationRecord.model_validate(payload)
        next_attempt = self._next_attempt(
            attempt,
            state=DreamGameState.OPTIONAL_DIVINATION,
            divination_ref=divination.divination_id,
        )
        self._commit_bundle(
            next_attempt,
            [self._record("divination", divination, viewer_id=user_id)],
            expected_row_version=attempt.row_version,
        )
        return self._attempt_view(next_attempt)

    def begin_judgment(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        credential: DreamControlCredential,
    ) -> DreamGameAttemptView:
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        if attempt.state == DreamGameState.JUDGMENT_DRAFTING:
            return self._attempt_view(attempt)
        if attempt.state not in {
            DreamGameState.QUESTION_FLOWER_OPEN,
            DreamGameState.OPTIONAL_DIVINATION,
        }:
            raise DreamGameError("dream_game_judgment_not_available")
        return self._attempt_view(self._advance(
            attempt,
            state=DreamGameState.JUDGMENT_DRAFTING,
        ))

    def seal_judgment(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        selected_outcome_option_id: str,
        confidence_basis_points: int,
        node_refs: list[str],
        relation_refs: list[str],
        interpretation: str,
        strongest_alternative: str,
        disconfirmation_condition: str,
        evidence_refs: list[str],
        idempotency_key: str,
        confirmed: bool,
        credential: DreamControlCredential,
    ) -> DreamGameAttemptView:
        if confirmed is not True:
            raise DreamGameError("dream_game_seal_confirmation_required")
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        if attempt.user_seal_ref:
            return self._attempt_view(attempt)
        if attempt.state != DreamGameState.JUDGMENT_DRAFTING:
            raise DreamGameError("dream_game_judgment_not_drafting")
        round_definition = self._round(attempt.round_id)
        if round_definition.flower_protocol_version == DREAM_FLOWER_PROTOCOL_VERSION:
            flower = self._refresh_flower(round_definition)
            if flower is None or flower.state != "OPEN":
                raise DreamGameError("dream_game_answer_collection_closed")
        if selected_outcome_option_id not in attempt.projection.question.outcome_options:
            raise DreamGameError("dream_game_outcome_option_invalid")
        allowed_nodes = {item.node_ref for item in attempt.projection.allowed_nodes}
        allowed_relations = {item.relation_ref for item in attempt.projection.allowed_relations}
        if set(node_refs) - allowed_nodes:
            raise DreamGameError("dream_game_hypothesis_node_invalid")
        if set(relation_refs) - allowed_relations:
            raise DreamGameError("dream_game_hypothesis_relation_invalid")
        if set(evidence_refs) - (allowed_nodes | allowed_relations):
            raise DreamGameError("dream_game_evidence_ref_invalid")
        key_hash = canonical_json_hash({"idempotency_key": idempotency_key})
        submission_id = f"dream-submission-{canonical_json_hash({'attempt': attempt_id, 'key': key_hash})[:32]}"
        seal_id = f"dream-user-seal-{canonical_json_hash({'submission': submission_id})[:32]}"
        now = self.clock()
        hypothesis = UserPathHypothesis(
            hypothesis_id=f"dream-user-hypothesis-{canonical_json_hash({'submission': submission_id})[:32]}",
            node_refs=list(dict.fromkeys(node_refs)),
            relation_refs=list(dict.fromkeys(relation_refs)),
            interpretation=interpretation,
        )
        submission_payload = {
            "submission_id": submission_id,
            "attempt_id": attempt_id,
            "round_id": attempt.round_id,
            "viewer_id": user_id,
            "projection_hash": attempt.projection.viewer_projection_hash,
            "selected_outcome_option_id": selected_outcome_option_id,
            "confidence_basis_points": confidence_basis_points,
            "user_path_hypothesis": hypothesis,
            "evidence_refs": list(dict.fromkeys(evidence_refs)),
            "strongest_alternative": strongest_alternative,
            "disconfirmation_condition": disconfirmation_condition,
            "assistance_mode": (
                "ASSISTED"
                if (
                    attempt.question_progress is not None
                    and any(item.attempts > 1 for item in attempt.question_progress.items)
                )
                else "INDEPENDENT"
            ),
            "divination_ref": attempt.divination_ref,
            "created_at": now,
        }
        submission_payload["immutable_hash"] = immutable_model_hash(_jsonable(submission_payload))
        submission = JudgmentSubmission.model_validate(submission_payload)
        user_seal_payload = {
            "seal_id": seal_id,
            "round_id": attempt.round_id,
            "attempt_id": attempt_id,
            "viewer_id": user_id,
            "submission_ref": submission.submission_id,
            "projection_hash": attempt.projection.viewer_projection_hash,
            "submission_hash": submission.immutable_hash,
            "sealed_at": now,
        }
        user_seal_payload["immutable_hash"] = immutable_model_hash(_jsonable(user_seal_payload))
        user_seal = UserJudgmentSeal.model_validate(user_seal_payload)
        system_seal = self.store.get_game_system_seal(
            seal_id=round_definition.system_judgment_seal_ref,
        )
        if (
            system_seal is None
            or system_seal.immutable_hash != round_definition.system_judgment_commitment_hash
            or system_seal.projection_hash != attempt.projection.frozen_projection_hash
            or system_seal.sealed_at >= round_definition.published_at
        ):
            raise DreamGameError("dream_game_system_seal_invalid")
        multi_answer = (
            round_definition.flower_protocol_version == DREAM_FLOWER_PROTOCOL_VERSION
        )
        next_attempt = self._next_attempt(
            attempt,
            state=(
                DreamGameState.USER_JUDGMENT_SEALED
                if multi_answer
                else DreamGameState.OUTCOME_REVEALABLE
            ),
            submission_ref=submission.submission_id,
            user_seal_ref=user_seal.seal_id,
            answer_source_attempt_id=attempt.attempt_id,
            extra_history=(
                [DreamGameState.USER_JUDGMENT_SEALED]
                if multi_answer
                else [
                    DreamGameState.USER_JUDGMENT_SEALED,
                    DreamGameState.BOTH_JUDGMENTS_SEALED,
                    DreamGameState.OUTCOME_REVEALABLE,
                ]
            ),
        )
        records = [
            self._record("judgment_submission", submission, viewer_id=user_id),
            self._record("user_judgment_seal", user_seal, viewer_id=user_id),
        ]
        if multi_answer:
            try:
                self.store.commit_game_answer_bundle(
                    next_attempt,
                    records,
                    user_seal=user_seal,
                    submitted_at=now,
                    expected_row_version=attempt.row_version,
                )
            except DreamStoreConflict as exc:
                if str(exc) != "dream_game_answer_already_sealed":
                    raise DreamGameError(str(exc)) from exc
                existing = self.store.find_game_answer_seal(
                    round_id=attempt.round_id,
                    viewer_id=user_id,
                )
                if existing is None:
                    raise DreamGameError(str(exc)) from exc
                source = self.store.get_game_attempt(
                    attempt_id=existing.attempt_id,
                    viewer_id=user_id,
                )
                if source is None:
                    raise DreamGameError("dream_game_answer_source_missing") from exc
                return self._attempt_view(source)
        else:
            self._commit_bundle(
                next_attempt,
                records,
                expected_row_version=attempt.row_version,
            )
        return self._attempt_view(next_attempt)

    def close_flower(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        idempotency_key: str,
        confirmed: bool,
        credential: DreamControlCredential,
    ) -> DreamGameAttemptView:
        if confirmed is not True:
            raise DreamGameError("dream_game_flower_close_confirmation_required")
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        round_definition = self._round(attempt.round_id)
        if round_definition.flower_protocol_version != DREAM_FLOWER_PROTOCOL_VERSION:
            raise DreamGameError("dream_game_flower_close_not_supported")
        if user_id != round_definition.flower_owner_ref:
            raise DreamGameError("dream_game_flower_owner_required")
        flower = self._refresh_flower(round_definition)
        if flower is None:
            raise DreamGameError("dream_game_flower_not_found")
        if flower.state != "OPEN":
            return self._attempt_view(attempt)
        self._close_flower(
            round_definition=round_definition,
            reason="OWNER_CLOSED",
            trigger_kind="OWNER",
            trigger_ref=user_id,
            idempotency_key=idempotency_key,
        )
        current = self.store.get_game_attempt(
            attempt_id=attempt.attempt_id,
            viewer_id=user_id,
        )
        if current is None:
            raise DreamGameError("dream_game_attempt_not_found")
        return self._attempt_view(current)

    def reveal(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        idempotency_key: str,
        credential: DreamControlCredential,
    ) -> DreamGameResultProjection:
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        if attempt.reveal_ref:
            return self._result(attempt)
        round_definition = self._round(attempt.round_id)
        shared_fruit = None
        answer_attempt = attempt
        if round_definition.flower_protocol_version == DREAM_FLOWER_PROTOCOL_VERSION:
            flower = self._refresh_flower(round_definition)
            now = self.clock()
            if (
                flower is None
                or flower.state != "SHARED_FRUIT_FORMED"
                or not flower.shared_fruit_ref
                or now < flower.outcome_due_at
            ):
                raise DreamGameError("dream_game_outcome_not_revealable")
            shared_fruit = self._typed_record(flower.shared_fruit_ref, SharedFruit)
            answer_attempt = self._answer_source_attempt(attempt)
        elif attempt.state != DreamGameState.OUTCOME_REVEALABLE:
            raise DreamGameError("dream_game_outcome_not_revealable")
        pack = self.store.get_game_content_pack(pack_id=round_definition.pack_id)
        if pack is None or pack.content_state == "REVOKED" or pack.revoked_at is not None:
            raise DreamGameError("dream_game_content_revoked")
        submission = self._typed_record(attempt.submission_ref, JudgmentSubmission)
        user_seal = self._typed_record(attempt.user_seal_ref, UserJudgmentSeal)
        system_seal = self.store.get_game_system_seal(
            seal_id=round_definition.system_judgment_seal_ref,
        )
        outcome = self.store.find_game_outcome_evidence(round_id=attempt.round_id)
        if system_seal is None or outcome is None:
            raise DreamGameError("dream_game_evidence_unavailable")
        if outcome.verification_status in {"WITHDRAWN", "DISPUTED", "UNVERIFIED"}:
            raise DreamGameError("dream_game_evidence_not_revealable")
        if (
            user_seal.submission_hash != submission.immutable_hash
            or user_seal.projection_hash
            != answer_attempt.projection.viewer_projection_hash
            or system_seal.immutable_hash != round_definition.system_judgment_commitment_hash
            or system_seal.projection_hash != attempt.projection.frozen_projection_hash
        ):
            raise DreamGameError("dream_game_dual_seal_invalid")
        now = self.clock()
        key_hash = canonical_json_hash({"idempotency_key": idempotency_key})
        reveal_payload = {
            "reveal_id": f"dream-reveal-{canonical_json_hash({'attempt': attempt_id, 'key': key_hash})[:32]}",
            "attempt_id": attempt_id,
            "round_id": attempt.round_id,
            "viewer_id": user_id,
            "user_seal_ref": user_seal.seal_id,
            "system_seal_ref": system_seal.seal_id,
            "evidence_ref": outcome.evidence_id,
            "revealed_at": now,
            "idempotency_key_hash": key_hash,
        }
        reveal_payload["immutable_hash"] = immutable_model_hash(_jsonable(reveal_payload))
        reveal_record = OutcomeRevealRecord.model_validate(reveal_payload)
        evaluation = self._evaluate(
            attempt=attempt,
            submission=submission,
            system_seal=system_seal,
            outcome=outcome,
            reveal_record=reveal_record,
            now=now,
        )
        seed = self._knowledge_seed(
            attempt=attempt,
            submission=submission,
            system_seal=system_seal,
            outcome=outcome,
            evaluation=evaluation,
            now=now,
        )
        next_attempt = self._next_attempt(
            attempt,
            state=DreamGameState.KNOWLEDGE_SEED_ISSUED,
            reveal_ref=reveal_record.reveal_id,
            evaluation_ref=evaluation.evaluation_id,
            knowledge_seed_ref=seed.seed_id,
            extra_history=(
                [
                    DreamGameState.BOTH_JUDGMENTS_SEALED,
                    DreamGameState.OUTCOME_REVEALABLE,
                    DreamGameState.OUTCOME_REVEALED,
                    DreamGameState.EVALUATED,
                    DreamGameState.KNOWLEDGE_SEED_ISSUED,
                ]
                if round_definition.flower_protocol_version
                == DREAM_FLOWER_PROTOCOL_VERSION
                else [
                    DreamGameState.OUTCOME_REVEALED,
                    DreamGameState.EVALUATED,
                    DreamGameState.KNOWLEDGE_SEED_ISSUED,
                ]
            ),
        )
        self._commit_bundle(
            next_attempt,
            [
                self._record("outcome_reveal", reveal_record, viewer_id=user_id),
                self._record("evaluation", evaluation, viewer_id=user_id),
                self._record("knowledge_seed", seed, viewer_id=user_id),
            ],
            expected_row_version=attempt.row_version,
        )
        return DreamGameResultProjection(
            banner=self._banner_for(round_definition),
            evidence_class=round_definition.evidence_class,
            development_only=round_definition.development_only,
            submission=submission,
            user_seal=user_seal,
            shared_fruit=shared_fruit,
            system_seal=system_seal,
            outcome_evidence=outcome,
            reveal_record=reveal_record,
            evaluation=evaluation,
            knowledge_seed=seed,
        )

    def read_result(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        credential: DreamControlCredential,
    ) -> DreamGameResultProjection:
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        if not attempt.reveal_ref:
            raise DreamGameError("dream_game_outcome_not_revealed")
        return self._result(attempt)

    def complete(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        credential: DreamControlCredential,
    ) -> DreamGameAttemptView:
        attempt = self._validated_attempt(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=attempt_id,
            credential=credential,
        )
        if attempt.state == DreamGameState.ROUND_COMPLETE:
            return self._attempt_view(attempt)
        if attempt.state != DreamGameState.KNOWLEDGE_SEED_ISSUED:
            raise DreamGameError("dream_game_round_not_completeable")
        return self._attempt_view(self._advance(
            attempt,
            state=DreamGameState.ROUND_COMPLETE,
        ))

    def _tree_profile(
        self,
        *,
        user_id: str,
        round_definition: BlindRoundDefinition,
        scenes: dict[str, tuple[Any, Any]],
    ) -> tuple[bool, dict[str, object]]:
        if self.relation_work_service is None:
            return True, {}
        source_snapshot = round_definition.source_snapshot
        scene_entry = scenes.get(round_definition.resident_scene_ref)
        if source_snapshot is None or scene_entry is None:
            return False, {}
        grant, _scene = scene_entry
        try:
            profile = self.relation_work_service.dream_tree_visual_profile(
                case_id=grant.case_id,
                participant_id=user_id,
                account_role="member",
                expected_life_case_version=(
                    source_snapshot.source_life_case_version
                ),
            )
        except (RelationWorkP0Conflict, RelationWorkP0Unavailable):
            return False, {}
        return bool(profile.get("profile_id")), profile

    def _require_relation_work_service(self) -> RelationWorkP0Service:
        if self.relation_work_service is None:
            raise DreamGameError("dream_reality_question_service_unavailable")
        return self.relation_work_service

    def _ensure_v50_rounds(
        self,
        *,
        user_id: str,
        visit_id: str,
        credential: DreamControlCredential,
    ) -> list[BlindRoundDefinition]:
        visit, scenes = self._context(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        encounter = self.journey.encounter(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        labels = {item.scene_ref: item.resident_label for item in encounter.trees}
        entries = []
        for scene_ref in visit.encounter_set.scene_refs:
            grant, scene = scenes[scene_ref]
            entries.append((
                grant,
                scene,
                labels.get(scene_ref, "匿名生命树"),
                self.journey.truth.canvas(grant),
            ))
        packs, compiled = compile_v50_canonical_encounter(
            entries=entries,
            published_at=self.clock(),
        )
        for pack in packs:
            self.store.save_game_content_pack(pack)
        rounds: list[BlindRoundDefinition] = []
        for round_definition, system_seal, outcome in compiled:
            existing = self.store.get_game_round(round_id=round_definition.round_id)
            if existing is not None:
                if existing.flower_protocol_version == DREAM_FLOWER_PROTOCOL_VERSION:
                    self.store.save_game_flower(
                        self._new_flower_lifecycle(existing)
                    )
                rounds.append(existing)
                continue
            self.store.save_game_round(round_definition)
            self.store.save_game_system_seal(system_seal)
            self.store.save_game_outcome_evidence(outcome)
            if round_definition.flower_protocol_version == DREAM_FLOWER_PROTOCOL_VERSION:
                self.store.save_game_flower(
                    self._new_flower_lifecycle(round_definition)
                )
            rounds.append(round_definition)
        return rounds

    def _context(self, *, user_id: str, visit_id: str, credential: DreamControlCredential):
        try:
            return self.journey.game_context(
                user_id=user_id,
                visit_id=visit_id,
                credential=credential,
            )
        except DreamBridgeError as exc:
            raise DreamGameError(str(exc)) from exc

    def _validated_attempt(
        self,
        *,
        user_id: str,
        visit_id: str,
        attempt_id: str,
        credential: DreamControlCredential,
    ) -> DreamGameAttempt:
        _visit, scenes = self._context(
            user_id=user_id,
            visit_id=visit_id,
            credential=credential,
        )
        attempt = self.store.get_game_attempt(attempt_id=attempt_id, viewer_id=user_id)
        if attempt is None or attempt.visit_id != visit_id:
            raise DreamGameError("dream_game_attempt_not_found")
        round_definition = self._round(attempt.round_id)
        self._validate_round_access(round_definition=round_definition, scenes=scenes)
        grant, _ = scenes[attempt.resident_scene_ref]
        if (
            attempt.projection.authorization_version != grant.authorization_version
            or attempt.projection.frozen_projection_hash
            != round_definition.frozen_projection.projection_hash
            or attempt.projection.source_snapshot_id
            != round_definition.frozen_projection.source_snapshot_id
            or attempt.question_set_ref
            != (
                round_definition.question_set.question_set_id
                if round_definition.question_set is not None
                else ""
            )
        ):
            raise DreamGameError("dream_game_projection_invalid")
        now = self.clock()
        if now >= attempt.projection.expires_at:
            attempt = self._renew_projection_envelope(attempt=attempt, now=now)
        return attempt

    def _renew_projection_envelope(
        self,
        *,
        attempt: DreamGameAttempt,
        now: datetime,
    ) -> DreamGameAttempt:
        # The viewer hash seals the frozen content. Delivery refs and their short
        # expiry may rotate after current authorization has been revalidated.
        projection = attempt.projection.model_copy(update={
            "projection_ref": f"dream-game-projection-{secrets.token_hex(32)}",
            "expires_at": now + timedelta(hours=4),
        })
        renewed = self._next_attempt(
            attempt,
            state=attempt.state,
            projection=projection,
        )
        try:
            self._commit_bundle(
                renewed,
                [],
                expected_row_version=attempt.row_version,
            )
            return renewed
        except DreamGameError as exc:
            if str(exc) != "dream_game_attempt_version_conflict":
                raise
            current = self.store.get_game_attempt(
                attempt_id=attempt.attempt_id,
                viewer_id=attempt.viewer_id,
            )
            if (
                current is None
                or current.projection.expires_at <= now
                or current.projection.authorization_version
                != attempt.projection.authorization_version
                or current.projection.frozen_projection_hash
                != attempt.projection.frozen_projection_hash
            ):
                raise
            return current

    def _validate_round_access(self, *, round_definition: BlindRoundDefinition, scenes) -> None:
        pack = self.store.get_game_content_pack(pack_id=round_definition.pack_id)
        if pack is None or pack.content_state == "REVOKED" or pack.revoked_at is not None:
            raise DreamGameError("dream_game_content_revoked")
        if round_definition.content_state == "REVOKED":
            raise DreamGameError("dream_game_content_revoked")
        if round_definition.content_state != "PUBLISHABLE":
            raise DreamGameError("dream_game_content_not_publishable")
        if round_definition.resident_scene_ref not in scenes:
            raise DreamGameError("dream_game_scene_not_in_visit")
        grant, _ = scenes[round_definition.resident_scene_ref]
        if grant.authorized_source_hash != round_definition.frozen_projection.source_scene_hash:
            raise DreamGameError("dream_game_scene_source_changed")
        snapshot = round_definition.source_snapshot
        question_set = round_definition.question_set
        if (
            round_definition.evidence_class != "V50_CANONICAL"
            or snapshot is None
            or question_set is None
            or snapshot.cutoff_verification_status
            != "VERIFIED_AS_OF_SOURCE_VERSION"
            or round_definition.frozen_projection.cutoff_verification_status
            != "VERIFIED_AS_OF_SOURCE_VERSION"
            or snapshot.source_snapshot_id
            != round_definition.frozen_projection.source_snapshot_id
            or question_set.source_snapshot_id != snapshot.source_snapshot_id
            or question_set.source_hash != snapshot.source_hash
            or question_set.cutoff_at != snapshot.cutoff_at
        ):
            raise DreamGameError("dream_game_cutoff_unverifiable")

    def _round(self, round_id: str) -> BlindRoundDefinition:
        value = self.store.get_game_round(round_id=round_id)
        if value is None:
            raise DreamGameError("dream_game_round_not_found")
        return value

    @staticmethod
    def _new_flower_lifecycle(
        round_definition: BlindRoundDefinition,
    ) -> FlowerLifecycle:
        if (
            round_definition.answer_close_at is None
            or round_definition.outcome_due_at is None
        ):
            raise DreamGameError("dream_game_multi_answer_window_invalid")
        flower_id = (
            "dream-flower-"
            + canonical_json_hash({
                "round_id": round_definition.round_id,
                "protocol": DREAM_FLOWER_PROTOCOL_VERSION,
            })[:40]
        )
        return FlowerLifecycle(
            flower_id=flower_id,
            round_id=round_definition.round_id,
            owner_ref=round_definition.flower_owner_ref,
            question_seal_ref=round_definition.system_judgment_seal_ref,
            answer_close_at=round_definition.answer_close_at,
            outcome_due_at=round_definition.outcome_due_at,
            created_at=round_definition.published_at,
            updated_at=round_definition.published_at,
        )

    def _refresh_flower(
        self,
        round_definition: BlindRoundDefinition,
    ) -> FlowerLifecycle | None:
        if round_definition.flower_protocol_version != DREAM_FLOWER_PROTOCOL_VERSION:
            return None
        flower = self.store.get_game_flower(round_id=round_definition.round_id)
        if flower is None:
            flower = self.store.save_game_flower(
                self._new_flower_lifecycle(round_definition)
            )
        now = self.clock()
        if flower.state == "OPEN" and now >= flower.answer_close_at:
            reason = (
                "OUTCOME_CUTOFF"
                if now >= flower.outcome_due_at
                else "NATURAL_WITHER"
            )
            return self._close_flower(
                round_definition=round_definition,
                reason=reason,
                trigger_kind="SYSTEM",
                trigger_ref="dream-flower-scheduler",
                idempotency_key=(
                    f"auto:{reason}:{flower.answer_close_at.isoformat()}"
                ),
            )
        return flower

    def _close_flower(
        self,
        *,
        round_definition: BlindRoundDefinition,
        reason: str,
        trigger_kind: str,
        trigger_ref: str,
        idempotency_key: str,
    ) -> FlowerLifecycle:
        now = self.clock()
        if reason == "NATURAL_WITHER" and (
            round_definition.answer_close_at is None
            or now < round_definition.answer_close_at
            or (
                round_definition.outcome_due_at is not None
                and now >= round_definition.outcome_due_at
            )
        ):
            raise DreamGameError("dream_game_flower_close_reason_invalid")
        if reason == "OUTCOME_CUTOFF" and (
            round_definition.outcome_due_at is None
            or now < round_definition.outcome_due_at
        ):
            raise DreamGameError("dream_game_flower_close_reason_invalid")
        for _attempt in range(4):
            flower = self.store.get_game_flower(round_id=round_definition.round_id)
            if flower is None:
                flower = self.store.save_game_flower(
                    self._new_flower_lifecycle(round_definition)
                )
            if flower.state != "OPEN":
                return flower
            answer_seals = self.store.list_game_answer_seals(
                round_id=round_definition.round_id
            )
            answer_seals = sorted(answer_seals, key=lambda item: item.seal_id)
            answer_manifest = [
                {"seal_ref": item.seal_id, "immutable_hash": item.immutable_hash}
                for item in answer_seals
            ]
            answer_set_hash = canonical_json_hash(answer_manifest)
            key_hash = canonical_json_hash({"idempotency_key": idempotency_key})
            now = self.clock()
            closure_id = (
                "dream-flower-closure-"
                + canonical_json_hash({
                    "flower_id": flower.flower_id,
                    "idempotency_key_hash": key_hash,
                })[:36]
            )
            closure_payload = {
                "closure_id": closure_id,
                "flower_id": flower.flower_id,
                "round_id": flower.round_id,
                "question_seal_ref": flower.question_seal_ref,
                "closed_at": now,
                "close_reason": reason,
                "answer_seal_refs": [item.seal_id for item in answer_seals],
                "answer_count": len(answer_seals),
                "answer_set_hash": answer_set_hash,
                "trigger_kind": trigger_kind,
                "trigger_ref": trigger_ref,
                "idempotency_key_hash": key_hash,
                "immutable_hash": "0" * 64,
            }
            closure_payload["immutable_hash"] = immutable_model_hash(
                _jsonable(closure_payload)
            )
            closure = FlowerClosureRecord.model_validate(closure_payload)
            shared_fruit = None
            shared_fruit_ref = ""
            next_state = "CLOSED_NO_RESPONSE"
            records = [self._record("flower_closure", closure, viewer_id="")]
            if answer_seals:
                fruit_payload = {
                    "fruit_id": (
                        "dream-shared-fruit-"
                        + canonical_json_hash({
                            "flower_id": flower.flower_id,
                            "closure_ref": closure.closure_id,
                        })[:36]
                    ),
                    "flower_id": flower.flower_id,
                    "round_id": flower.round_id,
                    "question_seal_ref": flower.question_seal_ref,
                    "closure_ref": closure.closure_id,
                    "answer_set_hash": answer_set_hash,
                    "answer_count": len(answer_seals),
                    "visual_state": "MIST_WHITE",
                    "formed_at": now,
                    "outcome_due_at": flower.outcome_due_at,
                    "immutable_hash": "0" * 64,
                }
                fruit_payload["immutable_hash"] = immutable_model_hash(
                    _jsonable(fruit_payload)
                )
                shared_fruit = SharedFruit.model_validate(fruit_payload)
                shared_fruit_ref = shared_fruit.fruit_id
                next_state = "SHARED_FRUIT_FORMED"
                records.append(self._record("shared_fruit", shared_fruit, viewer_id=""))
            next_flower = flower.model_copy(update={
                "state": next_state,
                "answer_count": len(answer_seals),
                "closure_ref": closure.closure_id,
                "shared_fruit_ref": shared_fruit_ref,
                "updated_at": now,
                "row_version": flower.row_version + 1,
            })
            try:
                return self.store.commit_game_flower_closure(
                    next_flower,
                    closure,
                    shared_fruit,
                    records,
                    expected_row_version=flower.row_version,
                )
            except DreamStoreConflict as exc:
                if str(exc) not in {
                    "dream_game_flower_version_conflict",
                    "dream_game_flower_answer_set_conflict",
                    "dream_game_flower_already_closed",
                }:
                    raise DreamGameError(str(exc)) from exc
        raise DreamGameError("dream_game_flower_close_conflict")

    def _answer_source_attempt(self, attempt: DreamGameAttempt) -> DreamGameAttempt:
        source_attempt_id = attempt.answer_source_attempt_id or attempt.attempt_id
        source = self.store.get_game_attempt(
            attempt_id=source_attempt_id,
            viewer_id=attempt.viewer_id,
        )
        if (
            source is None
            or source.round_id != attempt.round_id
            or source.user_seal_ref != attempt.user_seal_ref
        ):
            raise DreamGameError("dream_game_answer_source_missing")
        return source

    def _flower_view(
        self,
        *,
        round_definition: BlindRoundDefinition,
        attempt: DreamGameAttempt,
    ) -> FlowerLifecycleView | None:
        flower = self._refresh_flower(round_definition)
        if flower is None:
            return None
        close_reason = None
        if flower.closure_ref:
            closure = self._typed_record(flower.closure_ref, FlowerClosureRecord)
            close_reason = closure.close_reason
        answer_count_visible = attempt.viewer_id == flower.owner_ref
        revealable = (
            flower.state == "SHARED_FRUIT_FORMED"
            and self.clock() >= flower.outcome_due_at
        )
        if flower.state == "OPEN" and attempt.user_seal_ref:
            message = "你的判断已经封入花心。花朵仍在等待其他独立回应。"
        elif flower.state == "OPEN":
            message = "问题花仍在开放。所有来访者的回答彼此不可见。"
        elif flower.state == "CLOSED_NO_RESPONSE":
            message = "花朵已经自然凋谢，本轮没有形成共同果实。"
        elif revealable:
            message = "共同果实已到揭盲时刻。"
        else:
            message = "答案集合已经封存，雾白果实正在等待现实反馈。"
        return FlowerLifecycleView(
            flower_id=flower.flower_id,
            state=flower.state,
            answer_close_at=flower.answer_close_at,
            outcome_due_at=flower.outcome_due_at,
            own_answer_sealed=bool(attempt.user_seal_ref),
            answer_count_visible=answer_count_visible,
            answer_count=flower.answer_count if answer_count_visible else None,
            close_reason=close_reason,
            shared_fruit_visible=flower.state == "SHARED_FRUIT_FORMED",
            revealable=revealable,
            neutral_message=message,
        )

    def _advance(self, attempt: DreamGameAttempt, *, state: DreamGameState, **changes) -> DreamGameAttempt:
        next_attempt = self._next_attempt(attempt, state=state, **changes)
        self._commit_bundle(next_attempt, [], expected_row_version=attempt.row_version)
        return next_attempt

    def _next_attempt(
        self,
        attempt: DreamGameAttempt,
        *,
        state: DreamGameState,
        extra_history: list[DreamGameState] | None = None,
        **changes,
    ) -> DreamGameAttempt:
        history = list(attempt.state_history)
        for item in extra_history or [state]:
            if not history or history[-1] != item:
                history.append(item)
        return attempt.model_copy(update={
            **changes,
            "state": state,
            "state_history": history,
            "updated_at": self.clock(),
            "row_version": attempt.row_version + 1,
        })

    def _commit_bundle(self, attempt, records, *, expected_row_version: int) -> None:
        try:
            self.store.commit_game_attempt_bundle(
                attempt,
                records,
                expected_row_version=expected_row_version,
            )
        except DreamStoreConflict as exc:
            raise DreamGameError(str(exc)) from exc

    def _attempt_view(self, attempt: DreamGameAttempt) -> DreamGameAttemptView:
        round_definition = self._round(attempt.round_id)
        flower_view = self._flower_view(
            round_definition=round_definition,
            attempt=attempt,
        )
        question_set = round_definition.question_set
        progress = attempt.question_progress
        if (
            question_set is None
            or progress is None
            or question_set.question_set_id != attempt.question_set_ref
        ):
            raise DreamGameError("dream_game_question_set_missing")
        divination = None
        if attempt.divination_ref:
            divination = self._typed_record(attempt.divination_ref, DivinationRecord)
        question_projection = DreamQuestionSetProjection(
            question_set_id=question_set.question_set_id,
            question_set_version=question_set.question_set_version,
            source_snapshot_id=question_set.source_snapshot_id,
            cutoff_at=question_set.cutoff_at,
            domain=question_set.domain,
            content_status=question_set.content_status,
            story_script_ref=question_set.story_script_ref,
            target_lens=question_set.target_lens,
            reveal_policy=question_set.reveal_policy,
            questions=[
                DreamLearningQuestionPublic(
                    question_id=item.question_id,
                    kind=item.kind,
                    title=item.title,
                    prompt=item.prompt,
                    target_lens=item.target_lens,
                    options=[
                        {"option_id": option.option_id, "label": option.label}
                        for option in item.options
                    ],
                    available=self._question_dependencies_complete(item, progress),
                    organ_role=item.organ_role,
                    depends_on=list(item.depends_on),
                    difficulty=item.difficulty,
                )
                for item in question_set.questions
            ],
        )
        internal_projection = attempt.projection
        public_projection_payload = {
            key: value
            for key, value in internal_projection.model_dump(mode="json").items()
            if key not in {
                "schema_version",
                "question",
                "viewer_id",
                "visit_id",
                "case_namespace",
            }
        }
        public_projection = PreOutcomeDreamProjectionView.model_validate(
            public_projection_payload
        )
        return DreamGameAttemptView(
            attempt_id=attempt.attempt_id,
            round_id=attempt.round_id,
            state=attempt.state,
            projection=public_projection,
            question_set=question_projection,
            question_progress=progress,
            flower_question=(
                round_definition.question
                if attempt.state != DreamGameState.ROUND_OBSERVING
                else None
            ),
            observed_lenses=attempt.observed_lenses,
            divination=divination,
            flower=flower_view,
            sealed=bool(attempt.user_seal_ref),
            revealable=(
                flower_view.revealable
                if flower_view is not None
                else attempt.state == DreamGameState.OUTCOME_REVEALABLE
            ),
            completed=attempt.state == DreamGameState.ROUND_COMPLETE,
            updated_at=attempt.updated_at,
        )

    def _record(self, kind: str, model, *, viewer_id: str) -> DreamGameRecordEnvelope:
        payload = model.model_dump(mode="json")
        return DreamGameRecordEnvelope(
            record_id=str(
                payload.get("divination_id")
                or payload.get("answer_id")
                or payload.get("submission_id")
                or payload.get("seal_id")
                or payload.get("closure_id")
                or payload.get("fruit_id")
                or payload.get("reveal_id")
                or payload.get("evaluation_id")
                or payload.get("seed_id")
            ),
            record_kind=kind,
            round_id=str(payload["round_id"]),
            viewer_id=viewer_id,
            immutable_hash=str(payload["immutable_hash"]),
            payload=payload,
            created_at=(
                getattr(model, "server_timestamp", None)
                or getattr(model, "created_at", None)
                or getattr(model, "sealed_at", None)
                or getattr(model, "revealed_at", None)
                or getattr(model, "evaluated_at", None)
                or getattr(model, "issued_at", None)
                or self.clock()
            ),
        )

    @staticmethod
    def _leaf_questions_complete(progress: DreamQuestionAttemptProgress) -> bool:
        leaf_items = [
            item for item in progress.items
            if item.kind in {"LEAF_BASIC_01", "LEAF_BASIC_02"}
        ]
        return len(leaf_items) == 2 and all(
            item.status == "COMPLETED" for item in leaf_items
        )

    @classmethod
    def _question_dependencies_complete(
        cls,
        question,
        progress: DreamQuestionAttemptProgress,
    ) -> bool:
        dependency_ids = list(question.depends_on)
        if not dependency_ids and question.kind == "TRUNK_BACKBONE_01":
            return cls._leaf_questions_complete(progress)
        if not dependency_ids:
            return True
        progress_by_id = {item.question_id: item for item in progress.items}
        return all(
            dependency_id in progress_by_id
            and progress_by_id[dependency_id].status == "COMPLETED"
            for dependency_id in dependency_ids
        )

    @staticmethod
    def _banner_for(round_definition: BlindRoundDefinition) -> str:
        if round_definition.evidence_class == "V50_CANONICAL":
            return DREAM_GAME_V50_BANNER
        return "非正式内容｜不得作为真人果实"

    def _typed_record(self, record_id: str, model):
        envelope = self.store.get_game_record(record_id=record_id)
        if envelope is None:
            raise DreamGameError("dream_game_record_not_found")
        return model.model_validate(envelope.payload)

    def _evaluate(self, *, attempt, submission, system_seal, outcome, reveal_record, now):
        bucket = lambda value: "low" if value < 4500 else ("medium" if value < 7500 else "high")
        selected_nodes = set(submission.user_path_hypothesis.node_refs)
        omitted = [
            item.node_ref for item in attempt.projection.allowed_nodes
            if item.node_ref not in selected_nodes
        ][:4]
        payload = {
            "evaluation_id": f"dream-evaluation-{canonical_json_hash({'reveal': reveal_record.reveal_id})[:32]}",
            "attempt_id": attempt.attempt_id,
            "round_id": attempt.round_id,
            "user_seal_ref": attempt.user_seal_ref,
            "system_seal_ref": system_seal.seal_id,
            "reveal_ref": reveal_record.reveal_id,
            "evaluation_policy_version": DREAM_GAME_EVALUATION_POLICY_VERSION,
            "user_result": JudgmentEvaluation(
                option_match=submission.selected_outcome_option_id == outcome.resolved_option_id,
                confidence_bucket=bucket(submission.confidence_basis_points),
                decisive_node_omissions=omitted,
                disconfirmation_condition_quality=(
                    "VALID" if len(submission.disconfirmation_condition.strip()) >= 8 else "INVALID"
                ),
            ),
            "system_result": JudgmentEvaluation(
                option_match=system_seal.selected_outcome_option_id == outcome.resolved_option_id,
                confidence_bucket=bucket(system_seal.confidence_basis_points),
                decisive_node_omissions=[],
                disconfirmation_condition_quality="VALID",
            ),
            "outcome_choice_differs": submission.selected_outcome_option_id != system_seal.selected_outcome_option_id,
            "confidence_gap_basis_points": abs(submission.confidence_basis_points - system_seal.confidence_basis_points),
            "limitations": [
                (
                    "V50 结构果实只核对冻结命盘快照，不构成真人现实验证证据。"
                    if outcome.evidence_class == "V50_CANONICAL"
                    else "模拟果实只验证盲局流程与推理可复盘性，不构成现实命理证据。"
                ),
                "用户路径是假说，不会写入正式 PathAssertion。",
                "结构引用质量留待专业审查，本轮只校验引用身份。",
            ],
            "evaluated_at": now,
        }
        payload["immutable_hash"] = immutable_model_hash(_jsonable(payload))
        return EvaluationRecord.model_validate(payload)

    def _knowledge_seed(self, *, attempt, submission, system_seal, outcome, evaluation, now):
        matched = submission.selected_outcome_option_id == outcome.resolved_option_id
        evidence_label = (
            "冻结 V50 结构快照"
            if outcome.evidence_class == "V50_CANONICAL"
            else "模拟结果"
        )
        payload = {
            "seed_id": f"dream-seed-{canonical_json_hash({'evaluation': evaluation.evaluation_id})[:32]}",
            "attempt_id": attempt.attempt_id,
            "round_id": attempt.round_id,
            "viewer_id": attempt.viewer_id,
            "evaluation_ref": evaluation.evaluation_id,
            "issued_calibration_summary": (
                f"你的事前判断与{evidence_label}一致。保留当时引用的依据，同时继续检查最强反证。"
                if matched
                else f"你的事前判断与{evidence_label}不同。先保留原判断，再比较被忽略的条件和反证。"
            ),
            "observation_kept": submission.evidence_refs[:4],
            "missed_or_overweighted": evaluation.user_result.decisive_node_omissions,
            "applicable_boundary": (
                "这是一条私人复盘记录，只适用于本次结构盲局；不会进入 LifeCase、"
                "PathAssertion、共享知识库或训练证据。"
            ),
            "issued_at": now,
        }
        payload["immutable_hash"] = immutable_model_hash(_jsonable(payload))
        return KnowledgeSeed.model_validate(payload)

    def _result(self, attempt: DreamGameAttempt) -> DreamGameResultProjection:
        round_definition = self._round(attempt.round_id)
        submission = self._typed_record(attempt.submission_ref, JudgmentSubmission)
        user_seal = self._typed_record(attempt.user_seal_ref, UserJudgmentSeal)
        system_seal = self.store.get_game_system_seal(
            seal_id=round_definition.system_judgment_seal_ref,
        )
        outcome = self.store.find_game_outcome_evidence(round_id=attempt.round_id)
        reveal_record = self._typed_record(attempt.reveal_ref, OutcomeRevealRecord)
        evaluation = self._typed_record(attempt.evaluation_ref, EvaluationRecord)
        seed = self._typed_record(attempt.knowledge_seed_ref, KnowledgeSeed)
        if system_seal is None or outcome is None:
            raise DreamGameError("dream_game_result_incomplete")
        shared_fruit = None
        if round_definition.flower_protocol_version == DREAM_FLOWER_PROTOCOL_VERSION:
            flower = self.store.get_game_flower(round_id=attempt.round_id)
            if flower is None or not flower.shared_fruit_ref:
                raise DreamGameError("dream_game_shared_fruit_missing")
            shared_fruit = self._typed_record(flower.shared_fruit_ref, SharedFruit)
        return DreamGameResultProjection(
            banner=self._banner_for(round_definition),
            evidence_class=round_definition.evidence_class,
            development_only=round_definition.development_only,
            submission=submission,
            user_seal=user_seal,
            shared_fruit=shared_fruit,
            system_seal=system_seal,
            outcome_evidence=outcome,
            reveal_record=reveal_record,
            evaluation=evaluation,
            knowledge_seed=seed,
        )


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


__all__ = ["DreamGameError", "DreamGameService"]
