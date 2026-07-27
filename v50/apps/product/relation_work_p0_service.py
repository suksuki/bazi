from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from threading import RLock
from typing import Any

from core.graph import counterfactual_remove_node, counterfactual_remove_relation
from experience.compiler import canonical_hash
from experience.contracts import TopicExploration
from experience.life_tree_questions import (
    LifeTreeQuestionInstance,
    exploration_from_life_tree_answer,
    select_life_tree_questions,
)
from experience.relation_work_projection import (
    RelationFactProjectionItem,
    RelationWorkProjectionView,
    WorkPathProjectionItem,
    project_relation_work_for_consumer,
)
from experience.store import TheaterStore
from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner, CanonicalSceneUnavailable
from product.canvas_projection import (
    ReadOnlyCanvasUnavailable,
    ReadOnlySixPillarCanvasService,
)
from product.life_tree_question_blueprints import (
    PRIMARY_REALITY_FLOWER_BLUEPRINT_ID,
    load_life_tree_question_blueprints,
    load_relation_lab_question_blueprints,
)
from product.relation_work_case_projection import (
    RealRelationWorkContext,
    compile_real_relation_work_context,
)
from product.relation_work_p0_scenario import (
    P0_FIXTURE_ID,
    P0RelationWorkFixture,
    build_p0_relation_work_fixture,
    build_p0_temporal_relation_work_fixture,
)


class RelationWorkP0Unavailable(ValueError):
    pass


class RelationWorkP0Conflict(ValueError):
    pass


@dataclass(frozen=True)
class RelationWorkP0FeaturePolicy:
    enabled: bool = False
    canonical_enabled: bool = True

    @classmethod
    def from_environment(cls) -> "RelationWorkP0FeaturePolicy":
        canonical_value = os.environ.get(
            "V50_CANONICAL_RELATION_WORK_ENABLED",
            "1",
        ).strip().lower()
        return cls(
            enabled=os.environ.get("V50_RGM_WPM_P0_ENABLED", "").strip().lower()
            in {"1", "true", "yes", "on"},
            canonical_enabled=canonical_value not in {"0", "false", "no", "off"},
        )


class MemoryRelationWorkP0Store:
    def __init__(self) -> None:
        self._lock = RLock()
        self._explorations: dict[tuple[str, str], TopicExploration] = {}

    def save_answer(
        self,
        *,
        participant_run_id: str,
        question_instance_id: str,
        exploration: TopicExploration,
    ) -> TopicExploration:
        key = (participant_run_id, question_instance_id)
        with self._lock:
            existing = self._explorations.get(key)
            if existing is not None:
                if existing.responses != exploration.responses:
                    raise RelationWorkP0Conflict(
                        "life_tree_question_answer_already_recorded"
                    )
                return existing
            self._explorations[key] = exploration
            return exploration

    def list_for_run(self, participant_run_id: str) -> list[TopicExploration]:
        with self._lock:
            return sorted(
                (
                    item
                    for (run_id, _), item in self._explorations.items()
                    if run_id == participant_run_id
                ),
                key=lambda item: item.created_at,
            )


@dataclass(frozen=True)
class RealCaseRelationWorkRuntime:
    context: RealRelationWorkContext
    dream_projection: RelationWorkProjectionView
    lab_projection: RelationWorkProjectionView
    questions: tuple[LifeTreeQuestionInstance, ...]
    lab_questions: tuple[LifeTreeQuestionInstance, ...]
    canonical_canvas: dict[str, Any]
    canonical_projection_hash: str


class RelationWorkP0Service:
    def __init__(
        self,
        *,
        feature_policy: RelationWorkP0FeaturePolicy | None = None,
        store: MemoryRelationWorkP0Store | None = None,
        fixture: P0RelationWorkFixture | None = None,
        case_store: AgentCaseStore | None = None,
        theater_store: TheaterStore | None = None,
    ) -> None:
        self.feature_policy = (
            feature_policy or RelationWorkP0FeaturePolicy.from_environment()
        )
        self.store = store or MemoryRelationWorkP0Store()
        self.life_blueprints = load_life_tree_question_blueprints()
        self.lab_blueprints = load_relation_lab_question_blueprints()
        # Isolated P0 keeps the original structural question surface.
        self.blueprints = self.lab_blueprints
        self.fixture = (
            fixture or build_p0_relation_work_fixture()
            if self.feature_policy.enabled or fixture is not None
            else None
        )
        self.temporal_fixture = (
            build_p0_temporal_relation_work_fixture()
            if self.feature_policy.enabled
            else None
        )
        self.dream_projection = (
            project_relation_work_for_consumer(
                self.fixture.projection,
                audience="dream",
            )
            if self.fixture is not None
            else None
        )
        self.lab_projection = (
            project_relation_work_for_consumer(
                self.fixture.projection,
                audience="lab",
            )
            if self.fixture is not None
            else None
        )
        self.questions = (
            select_life_tree_questions(
                projection=self.dream_projection,
                blueprints=self.lab_blueprints,
            )
            if self.dream_projection is not None
            else []
        )
        self._question_by_id = {
            item.instance_id: item for item in self.questions
        }
        self.case_store = case_store
        self.theater_store = theater_store
        self.scene_owner = (
            CanonicalSceneOwner(case_store=case_store) if case_store else None
        )
        self.canvas_service = (
            ReadOnlySixPillarCanvasService(case_store=case_store)
            if case_store
            else None
        )
        self._real_case_cache: dict[
            tuple[str, str, str, str],
            RealCaseRelationWorkRuntime,
        ] = {}

    def bootstrap(self, *, participant_run_id: str) -> dict[str, object]:
        self._require_enabled()
        _validate_run_id(participant_run_id)
        explorations = self.store.list_for_run(participant_run_id)
        return {
            "schema_version": "deepbazi.relation-work-p0-bootstrap.v1",
            "fixture_id": P0_FIXTURE_ID,
            "participant_run_id": participant_run_id,
            "source": self.dream_projection.source.model_dump(mode="json"),
            "foundation_ref": self.dream_projection.foundation_ref,
            "foundation_hash": self.dream_projection.foundation_content_hash,
            "question_bank_version": (
                self.questions[0].blueprint_version if self.questions else ""
            ),
            "question_count": len(self.questions),
            "questions": [
                item.model_dump(mode="json") for item in self.questions
            ],
            "explorations": [
                item.model_dump(mode="json") for item in explorations
            ],
            "professional_state": {
                "resolved_count": len(
                    self.dream_projection.professionally_resolved_view
                ),
                "message": "当前没有已获专业准入的有效做功。",
                "main_work_declared": False,
            },
            "write_boundary": {
                "owner": "TopicExploration",
                "writes_life_case": False,
                "upgrades_relation_effect": False,
                "upgrades_work_path": False,
                "declares_main_work": False,
            },
        }

    def answer(
        self,
        *,
        participant_run_id: str,
        question_instance_id: str,
        selected_option_id: str,
        now: datetime | None = None,
    ) -> TopicExploration:
        self._require_enabled()
        _validate_run_id(participant_run_id)
        question = self._question_by_id.get(question_instance_id)
        if question is None:
            raise RelationWorkP0Unavailable(
                "life_tree_question_not_available_for_current_tree"
            )
        exploration = exploration_from_life_tree_answer(
            question=question,
            participant_run_id=participant_run_id,
            selected_option_id=selected_option_id,
            created_at=now or datetime.now(timezone.utc),
        )
        return self.store.save_answer(
            participant_run_id=participant_run_id,
            question_instance_id=question_instance_id,
            exploration=exploration,
        )

    def question(self, question_instance_id: str) -> LifeTreeQuestionInstance:
        self._require_enabled()
        question = self._question_by_id.get(question_instance_id)
        if question is None:
            raise RelationWorkP0Unavailable(
                "life_tree_question_not_available_for_current_tree"
            )
        return question

    def lab_view(self) -> RelationWorkProjectionView:
        self._require_enabled()
        return self.lab_projection

    def lab_bootstrap(self) -> dict[str, object]:
        self._require_enabled()
        natal = project_relation_work_for_consumer(
            self.temporal_fixture.natal.projection,
            audience="lab",
        )
        timing = project_relation_work_for_consumer(
            self.temporal_fixture.timing.projection,
            audience="lab",
        )
        return {
            "schema_version": "deepbazi.mingli-lab-relation-work-p0.v1",
            "fixture_id": P0_FIXTURE_ID,
            "views": {
                "natal": natal.model_dump(mode="json"),
                "timing": timing.model_dump(mode="json"),
            },
            "temporal_delta": self.temporal_fixture.delta.model_dump(mode="json"),
            "layout": {
                "coordinate_system": "six-pillar-twelve-node",
                "columns": [
                    {"id": "year", "label": "年柱", "scope": "natal"},
                    {"id": "month", "label": "月柱", "scope": "natal"},
                    {"id": "day", "label": "日柱", "scope": "natal"},
                    {"id": "hour", "label": "时柱", "scope": "natal"},
                    {"id": "luck", "label": "大运", "scope": "luck"},
                    {"id": "2028", "label": "2028 流年", "scope": "year"},
                ],
                "levels": [
                    {"id": "stem", "label": "干"},
                    {"id": "branch", "label": "支"},
                ],
            },
            "professional_state": {
                "resolved_count": len(
                    timing.professionally_resolved_view
                ),
                "message": "当前没有已获专业准入的有效做功。",
                "main_work_declared": False,
                "fail_closed": True,
            },
            "diagnostic_contract": {
                "counterfactual_is_professional_authority": False,
                "temporal_delta_is_professional_authority": False,
                "line_prominence_is_professional_importance": False,
                "frontend_inference_allowed": False,
                "writes_life_case": False,
            },
        }

    def lab_counterfactual(
        self,
        *,
        temporal_view: str,
        removal_type: str,
        removed_ref: str,
    ) -> dict[str, object]:
        self._require_enabled()
        fixture = (
            self.temporal_fixture.natal
            if temporal_view == "natal"
            else self.temporal_fixture.timing
            if temporal_view == "timing"
            else None
        )
        if fixture is None:
            raise RelationWorkP0Unavailable("unknown_lab_temporal_view")
        if removal_type == "node":
            known_refs = {
                participant.node_ref
                for fact in fixture.relation_facts
                for participant in fact.fact_key.participant_refs
            }
            if removed_ref not in known_refs:
                raise RelationWorkP0Unavailable(
                    "counterfactual_node_not_in_current_projection"
                )
            result = counterfactual_remove_node(
                candidates=list(fixture.work_path_candidates),
                node_ref=removed_ref,
            )
        elif removal_type == "relation_fact":
            known_refs = {
                fact.revision_ref for fact in fixture.relation_facts
            }
            if removed_ref not in known_refs:
                raise RelationWorkP0Unavailable(
                    "counterfactual_relation_not_in_current_projection"
                )
            result = counterfactual_remove_relation(
                candidates=list(fixture.work_path_candidates),
                relation_fact_revision_ref=removed_ref,
            )
        else:
            raise RelationWorkP0Unavailable(
                "unknown_counterfactual_removal_type"
            )
        return {
            "schema_version": "deepbazi.mingli-lab-counterfactual-p0.v1",
            "temporal_view": temporal_view,
            "source_foundation_ref": fixture.projection.foundation_ref,
            "source_foundation_hash": fixture.projection.content_hash,
            "counterfactual": result.model_dump(mode="json"),
            "diagnostic_only": True,
            "professional_effect_changed": False,
            "writes_life_case": False,
        }

    def case_bootstrap(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
    ) -> dict[str, object]:
        runtime = self._real_case_runtime(
            case_id=case_id,
            participant_id=participant_id,
            account_role=account_role,
        )
        participant_run_id = _real_participant_run_id(
            participant_id=participant_id,
            case_id=case_id,
            foundation_hash=runtime.dream_projection.foundation_content_hash,
        )
        all_explorations = self._list_real_explorations(participant_run_id)
        current_question_refs = {
            item.instance_id for item in runtime.questions
        }
        explorations = [
            item
            for item in all_explorations
            if item.experiment_kind == "life_tree_relation_work_question"
            and current_question_refs.intersection(item.responses)
        ]
        tree_visual_profile = _tree_visual_profile(runtime.context)
        tree_scene = _tree_scene_state(
            projection=runtime.dream_projection,
            questions=runtime.questions,
            explorations=explorations,
        )
        return {
            "schema_version": "deepbazi.relation-work-lifecase-bootstrap.p1.v1",
            "data_source": "CURRENT_REAL_LIFECASE",
            "case_id": case_id,
            "participant_run_id": participant_run_id,
            "source": runtime.dream_projection.source.model_dump(mode="json"),
            "foundation_ref": runtime.dream_projection.foundation_ref,
            "foundation_hash": (
                runtime.dream_projection.foundation_content_hash
            ),
            "question_bank_version": (
                runtime.questions[0].blueprint_version
                if runtime.questions
                else ""
            ),
            "question_count": len(runtime.questions),
            "questions": [
                item.model_dump(mode="json") for item in runtime.questions
            ],
            "explorations": [
                item.model_dump(mode="json") for item in explorations
            ],
            "abu_conversation": {
                "turns": _abu_observation_history(all_explorations),
                "llm_used": False,
                "writes_life_case": False,
                "professional_judgment_allowed": False,
            },
            "tree_scene": tree_scene,
            "tree_visual_profile": tree_visual_profile,
            "canonical_timing": _canonical_timing_summary(
                runtime.canonical_canvas
            ),
            "empty_state": (
                ""
                if runtime.questions
                else "这棵树暂时没有开放新的命题"
            ),
            "professional_state": _professional_state(
                runtime.dream_projection
            ),
            "write_boundary": _write_boundary(),
        }

    def dream_tree_visual_profile(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
        expected_life_case_version: str = "",
    ) -> dict[str, object]:
        runtime = self._real_case_runtime(
            case_id=case_id,
            participant_id=participant_id,
            account_role=account_role,
        )
        if expected_life_case_version:
            self._require_life_case_version(
                runtime=runtime,
                expected_life_case_version=expected_life_case_version,
            )
        return _tree_visual_profile(runtime.context)

    def dream_reality_question_view(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
        encounter_set_id: str,
        round_id: str,
        expected_life_case_version: str,
    ) -> dict[str, object]:
        runtime = self._real_case_runtime(
            case_id=case_id,
            participant_id=participant_id,
            account_role=account_role,
        )
        self._require_life_case_version(
            runtime=runtime,
            expected_life_case_version=expected_life_case_version,
        )
        participant_run_id = _dream_real_participant_run_id(
            participant_id=participant_id,
            encounter_set_id=encounter_set_id,
            round_id=round_id,
            case_id=case_id,
            life_case_version=expected_life_case_version,
        )
        question = _primary_reality_question(runtime.questions)
        explorations = self._list_real_explorations(participant_run_id)
        existing = (
            next(
                (
                    item
                    for item in explorations
                    if question is not None
                    and item.experiment_kind
                    == "dream_reality_question_answer"
                    and question.instance_id in item.responses
                ),
                None,
            )
            if question is not None
            else None
        )
        return _dream_reality_question_payload(
            question=question,
            exploration=existing,
            profile=_tree_visual_profile(runtime.context),
            expected_life_case_version=expected_life_case_version,
        )

    def answer_dream_reality_question(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
        encounter_set_id: str,
        round_id: str,
        expected_life_case_version: str,
        question_instance_id: str,
        selected_option_id: str,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> dict[str, object]:
        runtime = self._real_case_runtime(
            case_id=case_id,
            participant_id=participant_id,
            account_role=account_role,
        )
        self._require_life_case_version(
            runtime=runtime,
            expected_life_case_version=expected_life_case_version,
        )
        question = _primary_reality_question(runtime.questions)
        if question is None or question.instance_id != question_instance_id:
            raise RelationWorkP0Unavailable(
                "dream_reality_question_not_available_for_current_tree"
            )
        participant_run_id = _dream_real_participant_run_id(
            participant_id=participant_id,
            encounter_set_id=encounter_set_id,
            round_id=round_id,
            case_id=case_id,
            life_case_version=expected_life_case_version,
        )
        existing = next(
            (
                item
                for item in self._list_real_explorations(participant_run_id)
                if item.experiment_kind == "dream_reality_question_answer"
                and question.instance_id in item.responses
            ),
            None,
        )
        if existing is not None:
            if (
                existing.responses.get(question.instance_id)
                != selected_option_id
            ):
                raise RelationWorkP0Conflict(
                    "dream_reality_question_answer_already_sealed"
                )
            return _dream_reality_question_payload(
                question=question,
                exploration=existing,
                profile=_tree_visual_profile(runtime.context),
                expected_life_case_version=expected_life_case_version,
            )
        if not idempotency_key or len(idempotency_key) > 180:
            raise RelationWorkP0Unavailable(
                "dream_reality_question_idempotency_key_invalid"
            )
        exploration = exploration_from_life_tree_answer(
            question=question,
            participant_run_id=participant_run_id,
            selected_option_id=selected_option_id,
            created_at=now or datetime.now(timezone.utc),
        )
        exploration_identity = {
            "participant_run_id": participant_run_id,
            "question_instance_id": question.instance_id,
        }
        exploration = exploration.model_copy(update={
            "exploration_id": (
                f"exploration:{canonical_hash(exploration_identity)}"
            ),
            "responses": {
                question.instance_id: selected_option_id,
                "_encounter_set_id": encounter_set_id,
                "_case_id": case_id,
                "_life_case_version": expected_life_case_version,
                "_blueprint_id": question.blueprint_id,
                "_blueprint_version": question.blueprint_version,
                "_idempotency_key": idempotency_key,
                "_reveal_status": "WAITING_REALITY_EVIDENCE",
            },
            "observations": [
                *exploration.observations,
                f"encounter_set_id:{encounter_set_id}",
                f"round_id:{round_id}",
                f"life_case_version:{expected_life_case_version}",
                "reveal_status:WAITING_REALITY_EVIDENCE",
                "answer_is_immutable:true",
            ],
            "experiment_kind": "dream_reality_question_answer",
            "life_case_version_observed": expected_life_case_version,
        })
        if self.theater_store is None:
            raise RelationWorkP0Unavailable(
                "real_lifecase_exploration_store_unavailable"
            )
        self.theater_store.save_exploration(exploration)
        return _dream_reality_question_payload(
            question=question,
            exploration=exploration,
            profile=_tree_visual_profile(runtime.context),
            expected_life_case_version=expected_life_case_version,
        )

    def answer_case_question(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
        question_instance_id: str,
        selected_option_id: str,
        now: datetime | None = None,
    ) -> TopicExploration:
        runtime = self._real_case_runtime(
            case_id=case_id,
            participant_id=participant_id,
            account_role=account_role,
        )
        question = next(
            (
                item
                for item in runtime.questions
                if item.instance_id == question_instance_id
            ),
            None,
        )
        if question is None:
            raise RelationWorkP0Unavailable(
                "life_tree_question_not_available_for_current_tree"
            )
        participant_run_id = _real_participant_run_id(
            participant_id=participant_id,
            case_id=case_id,
            foundation_hash=runtime.dream_projection.foundation_content_hash,
        )
        existing = next(
            (
                item
                for item in self._list_real_explorations(participant_run_id)
                if question_instance_id in item.responses
            ),
            None,
        )
        if existing is not None:
            if existing.responses.get(question_instance_id) != selected_option_id:
                raise RelationWorkP0Conflict(
                    "life_tree_question_answer_already_recorded"
                )
            return existing
        exploration = exploration_from_life_tree_answer(
            question=question,
            participant_run_id=participant_run_id,
            selected_option_id=selected_option_id,
            created_at=now or datetime.now(timezone.utc),
        )
        if self.theater_store is None:
            raise RelationWorkP0Unavailable(
                "real_lifecase_exploration_store_unavailable"
            )
        self.theater_store.save_exploration(exploration)
        return exploration

    @staticmethod
    def _require_life_case_version(
        *,
        runtime: RealCaseRelationWorkRuntime,
        expected_life_case_version: str,
    ) -> None:
        source = runtime.context.metadata.get("source")
        current_version = (
            str(source.get("life_case_version") or "")
            if isinstance(source, dict)
            else ""
        )
        if (
            not expected_life_case_version
            or current_version != expected_life_case_version
        ):
            raise RelationWorkP0Conflict(
                "dream_reality_question_lifecase_version_changed"
            )

    def case_abu_observation_turn(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
        question_instance_id: str,
        request_id: str,
        message: str,
        now: datetime | None = None,
    ) -> dict[str, object]:
        runtime = self._real_case_runtime(
            case_id=case_id,
            participant_id=participant_id,
            account_role=account_role,
        )
        question = next(
            (
                item
                for item in runtime.questions
                if item.instance_id == question_instance_id
            ),
            None,
        )
        if question is None:
            raise RelationWorkP0Unavailable(
                "life_tree_question_not_available_for_current_tree"
            )
        _validate_request_id(request_id)
        normalized_message = " ".join(message.strip().split())
        if not normalized_message or len(normalized_message) > 300:
            raise RelationWorkP0Unavailable("invalid_abu_observation_message")
        participant_run_id = _real_participant_run_id(
            participant_id=participant_id,
            case_id=case_id,
            foundation_hash=runtime.dream_projection.foundation_content_hash,
        )
        explorations = self._list_real_explorations(participant_run_id)
        answered = any(
            item.experiment_kind == "life_tree_relation_work_question"
            and question_instance_id in item.responses
            for item in explorations
        )
        if not answered:
            raise RelationWorkP0Conflict(
                "life_tree_question_observation_required_before_abu_turn"
            )
        identity = {
            "participant_run_id": participant_run_id,
            "question_instance_id": question_instance_id,
            "request_id": request_id,
        }
        exploration_id = f"exploration:{canonical_hash(identity)}"
        existing = next(
            (
                item
                for item in explorations
                if item.exploration_id == exploration_id
            ),
            None,
        )
        if existing is not None:
            if existing.responses.get("user_message") != normalized_message:
                raise RelationWorkP0Conflict(
                    "abu_observation_turn_request_conflict"
                )
            return {
                "turn": _abu_observation_turn_payload(existing),
                "history": _abu_observation_history(explorations),
                "boundaries": _abu_observation_boundaries(),
            }
        classification, reply = _abu_observation_reply(
            question=question,
            message=normalized_message,
        )
        exploration = TopicExploration(
            exploration_id=exploration_id,
            participant_run_id=participant_run_id,
            topic_id=f"abu:{question.blueprint_id}",
            responses={
                "request_id": request_id,
                "question_instance_id": question_instance_id,
                "user_message": normalized_message,
                "abu_message": reply,
                "classification": classification,
            },
            capsule_message="阿布只整理当前证据边界，不替你或系统作出命理判断。",
            experiment_kind="life_tree_abu_observation_turn",
            scene_id=question.source_foundation_ref,
            scene_source_hash=question.source_foundation_hash,
            base_snapshot_ref=question.source_foundation_ref,
            base_snapshot_hash=question.source_foundation_hash,
            sandbox_result_refs=[
                *question.relation_fact_revision_refs,
                *question.work_path_candidate_refs,
            ],
            observations=[
                "user_statement_not_lifecase_truth",
                f"abu_classification:{classification}",
            ],
            open_question=question.prompt,
            restored_original=True,
            capability_trace=["deterministic_structure"],
            life_case_version_observed=question.blueprint_version,
            case_local_only=True,
            created_at=now or datetime.now(timezone.utc),
        )
        if self.theater_store is None:
            raise RelationWorkP0Unavailable(
                "real_lifecase_exploration_store_unavailable"
            )
        self.theater_store.save_exploration(exploration)
        current = [*explorations, exploration]
        return {
            "turn": _abu_observation_turn_payload(exploration),
            "history": _abu_observation_history(current),
            "boundaries": _abu_observation_boundaries(),
        }

    def case_lab_bootstrap(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
    ) -> dict[str, object]:
        runtime = self._real_case_runtime(
            case_id=case_id,
            participant_id=participant_id,
            account_role=account_role,
        )
        relation_audit = _relation_lab_audit(runtime.lab_projection)
        path_focus = _relation_path_focus(runtime.lab_projection)
        return {
            "schema_version": "deepbazi.mingli-lab-lifecase.p1.v1",
            "data_source": "CURRENT_REAL_LIFECASE",
            "case_id": case_id,
            "relation_work": runtime.lab_projection.model_dump(mode="json"),
            "relation_audit": relation_audit,
            "path_focus": path_focus,
            "canonical_canvas": runtime.canonical_canvas,
            "canonical_timing": _canonical_timing_summary(
                runtime.canonical_canvas
            ),
            "learning_questions": [
                item.model_dump(mode="json")
                for item in runtime.lab_questions
            ],
            "professional_state": _professional_state(
                runtime.lab_projection
            ),
            "diagnostic_contract": {
                "counterfactual_is_professional_authority": False,
                "temporal_delta_is_professional_authority": False,
                "line_prominence_is_professional_importance": False,
                "frontend_inference_allowed": False,
                "writes_life_case": False,
            },
        }

    def case_lab_counterfactual(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
        removal_type: str,
        removed_ref: str,
    ) -> dict[str, object]:
        runtime = self._real_case_runtime(
            case_id=case_id,
            participant_id=participant_id,
            account_role=account_role,
        )
        context = runtime.context
        if removal_type == "node":
            known_refs = {
                participant.node_ref
                for fact in context.relation_facts
                for participant in fact.fact_key.participant_refs
            }
            if removed_ref not in known_refs:
                raise RelationWorkP0Unavailable(
                    "counterfactual_node_not_in_current_projection"
                )
            result = counterfactual_remove_node(
                candidates=list(context.work_path_candidates),
                node_ref=removed_ref,
            )
        elif removal_type == "relation_fact":
            known_refs = {item.revision_ref for item in context.relation_facts}
            if removed_ref not in known_refs:
                raise RelationWorkP0Unavailable(
                    "counterfactual_relation_not_in_current_projection"
                )
            result = counterfactual_remove_relation(
                candidates=list(context.work_path_candidates),
                relation_fact_revision_ref=removed_ref,
            )
        else:
            raise RelationWorkP0Unavailable(
                "unknown_counterfactual_removal_type"
            )
        return {
            "schema_version": "deepbazi.mingli-lab-counterfactual-p1.v1",
            "case_id": case_id,
            "source_foundation_ref": context.projection.foundation_ref,
            "source_foundation_hash": context.projection.content_hash,
            "counterfactual": result.model_dump(mode="json"),
            "diagnostic_only": True,
            "professional_effect_changed": False,
            "writes_life_case": False,
        }

    def _real_case_runtime(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
    ) -> RealCaseRelationWorkRuntime:
        self._require_canonical_enabled()
        if (
            self.case_store is None
            or self.scene_owner is None
            or self.canvas_service is None
        ):
            raise RelationWorkP0Unavailable(
                "real_lifecase_projection_unavailable"
            )
        row = self.case_store.get(
            case_id=case_id,
            user_id=participant_id,
        )
        if row is None:
            raise RelationWorkP0Unavailable("experience_case_not_found")
        try:
            canonical_projection = self.scene_owner.issue_projection(
                case_id=case_id,
                participant_id=participant_id,
                account_role=account_role,
                projection_kind="onecanvas",
            )
            cache_key = (
                case_id,
                participant_id,
                account_role,
                canonical_projection.projection_hash,
            )
            cached = self._real_case_cache.get(cache_key)
            if cached is not None:
                return cached
            context = compile_real_relation_work_context(
                case_id=case_id,
                row=row,
                canonical_projection_payload=canonical_projection.payload,
            )
            canonical_canvas = self.canvas_service.issue(
                case_id=case_id,
                participant_id=participant_id,
                account_role=account_role,
            )
        except (CanonicalSceneUnavailable, ReadOnlyCanvasUnavailable, ValueError) as exc:
            raise RelationWorkP0Unavailable(str(exc)) from exc
        dream_projection = project_relation_work_for_consumer(
            context.projection,
            audience="dream",
        )
        lab_projection = project_relation_work_for_consumer(
            context.projection,
            audience="lab",
        )
        runtime = RealCaseRelationWorkRuntime(
            context=context,
            dream_projection=dream_projection,
            lab_projection=lab_projection,
            questions=tuple(
                select_life_tree_questions(
                    projection=dream_projection,
                    blueprints=self.life_blueprints,
                    limit=5,
                )
            ),
            lab_questions=tuple(
                select_life_tree_questions(
                    projection=dream_projection,
                    blueprints=self.lab_blueprints,
                    limit=6,
                )
            ),
            canonical_canvas=canonical_canvas,
            canonical_projection_hash=canonical_projection.projection_hash,
        )
        for key in list(self._real_case_cache):
            if key[:3] == cache_key[:3] and key != cache_key:
                self._real_case_cache.pop(key, None)
        if len(self._real_case_cache) >= 64:
            self._real_case_cache.clear()
        self._real_case_cache[cache_key] = runtime
        return runtime

    def _list_real_explorations(
        self,
        participant_run_id: str,
    ) -> list[TopicExploration]:
        if self.theater_store is None:
            raise RelationWorkP0Unavailable(
                "real_lifecase_exploration_store_unavailable"
            )
        return sorted(
            self.theater_store.list_explorations(participant_run_id),
            key=lambda item: item.created_at,
        )

    def _require_enabled(self) -> None:
        if not self.feature_policy.enabled:
            raise RelationWorkP0Unavailable("relation_work_p0_feature_disabled")

    def _require_canonical_enabled(self) -> None:
        if not self.feature_policy.canonical_enabled:
            raise RelationWorkP0Unavailable(
                "canonical_relation_work_feature_disabled"
            )


def _relation_lab_audit(
    projection: RelationWorkProjectionView,
) -> dict[str, object]:
    facts = projection.factual_view
    class_counts = Counter(item.legality_class for item in facts)
    quarantined = [
        _relation_audit_fact(item)
        for item in facts
        if item.provenance_status in {"quarantined", "illegal", "incomplete"}
    ]
    return {
        "schema_version": "deepbazi.relation-legality-audit.v1",
        "policy_version": (
            facts[0].legality_policy_version if facts else ""
        ),
        "total_relation_facts": len(facts),
        "legal_direct_edges": class_counts["legal_direct"],
        "legal_mediated_relations": class_counts["legal_mediated"],
        "containment_edges": class_counts["containment"],
        "positional_edges": class_counts["positional"],
        "unsupported_edges": class_counts["unsupported"],
        "illegal_cross_layer_edges": class_counts["illegal_cross_layer"],
        "missing_rule_id": sum(
            "rule_id" in item.missing_requirements for item in facts
        ),
        "missing_provenance": sum(
            item.provenance_status == "incomplete" for item in facts
        ),
        "missing_participant_constraints": sum(
            any(
                requirement in {
                    "manifestation_or_mediation_evidence",
                    "registered_cross_layer_mediator",
                    "branch_to_hidden_stem_containment_shape",
                    "same_column_stem_branch_position_shape",
                    "branch_relation_requires_branch_participants",
                }
                for requirement in item.missing_requirements
            )
            for item in facts
        ),
        "visible_inventory_fact_refs": [
            item.fact_revision_ref for item in facts if item.inventory_visible
        ],
        "quarantined_fact_count": len(quarantined),
        "quarantined_facts": quarantined,
        "illegal_facts": [
            item
            for item in quarantined
            if item["legality_class"] == "illegal_cross_layer"
        ],
        "default_paths_consume_quarantine": False,
    }


def _relation_path_focus(
    projection: RelationWorkProjectionView,
) -> dict[str, object]:
    eligible_fact_refs = {
        item.fact_revision_ref
        for item in projection.factual_view
        if item.default_path_eligible
    }
    all_paths = list(projection.candidate_path_view)
    eligible_paths = [
        path
        for path in all_paths
        if path.ordered_fact_revision_refs
        and all(
            fact_ref in eligible_fact_refs
            for fact_ref in path.ordered_fact_revision_refs
        )
    ]
    competition_group_counts = Counter(
        path.competing_path_group_ref
        for path in eligible_paths
        if path.competing_path_group_ref
    )
    paths = sorted(
        eligible_paths,
        key=lambda path: _path_focus_sort_key(
            path,
            competition_group_counts=competition_group_counts,
        ),
    )
    primary = paths[0] if paths else None
    competition = None
    if primary and primary.competing_path_group_ref:
        competition = next(
            (
                item
                for item in paths[1:]
                if item.competing_path_group_ref
                == primary.competing_path_group_ref
            ),
            None,
        )
    visible = [
        item
        for item in (primary, competition)
        if item is not None
    ]
    return {
        "schema_version": "deepbazi.lab-path-focus.v1",
        "selection_policy": "diagnostic_structural_focus.v2",
        "selection_is_professional_ranking": False,
        "main_work_declared": False,
        "primary_path_ref": (
            primary.work_path_candidate_ref if primary else ""
        ),
        "competition_path_ref": (
            competition.work_path_candidate_ref if competition else ""
        ),
        "visible_path_refs": [
            item.work_path_candidate_ref for item in visible
        ],
        "hidden_candidate_count": max(0, len(all_paths) - len(visible)),
        "primary_shape": (
            "single_segment_candidate"
            if primary and len(primary.ordered_fact_revision_refs) == 1
            else "multi_segment_candidate"
            if primary
            else "none"
        ),
        "key_blocker": _key_path_blocker(primary),
        "empty_state": (
            ""
            if primary
            else "当前盘没有通过直连与溯源校验的结构候选。"
        ),
    }


def _path_focus_sort_key(
    path: WorkPathProjectionItem,
    *,
    competition_group_counts: Counter[str],
) -> tuple[int, int, int, int, int, str]:
    coordinates = path.participant_coordinates
    slot_order = {
        "year": 0,
        "month": 1,
        "day": 2,
        "hour": 3,
        "luck": 4,
    }
    indices = [
        slot_order[item.get("slot", "")]
        for item in coordinates
        if item.get("slot", "") in slot_order
    ]
    span = max(indices) - min(indices) if indices else 99
    return (
        0
        if competition_group_counts[path.competing_path_group_ref] >= 2
        else 1,
        0 if path.competing_path_group_ref else 1,
        -len(path.ordered_fact_revision_refs),
        len(path.blocker_types),
        span,
        path.work_path_candidate_ref,
    )


def _key_path_blocker(
    path: WorkPathProjectionItem | None,
) -> dict[str, str]:
    if path is None:
        return {
            "blocker_type": "no_legal_candidate",
            "message": "没有合格直连事实，不能构造候选路径。",
        }
    blocker = path.blocker_types[0] if path.blocker_types else (
        "professional_effect_not_admitted"
    )
    return {
        "blocker_type": blocker,
        "message": {
            "capacity_unresolved": "承载容量尚未核证。",
            "effect_unresolved": "实际作用尚未获专业核证。",
            "usability_unresolved": "现实可用性尚未核证。",
            "professional_effect_not_admitted": "尚未通过专业作用准入。",
        }.get(blocker, "仍有结构条件需要核证。"),
    }


def _relation_audit_fact(
    fact: RelationFactProjectionItem,
) -> dict[str, object]:
    return {
        "relation_fact_id": fact.relation_fact_id,
        "relation_kind": fact.relation_kind,
        "participant_refs": fact.participant_refs,
        "participant_kinds": fact.participant_kinds,
        "legality_class": fact.legality_class,
        "provenance_status": fact.provenance_status,
        "missing_requirements": fact.missing_requirements,
    }


def _primary_reality_question(
    questions: tuple[LifeTreeQuestionInstance, ...],
) -> LifeTreeQuestionInstance | None:
    return next(
        (
            item
            for item in questions
            if item.blueprint_id == PRIMARY_REALITY_FLOWER_BLUEPRINT_ID
            and item.purpose == "life_observation"
            and item.reveal_policy == "REALITY_FEEDBACK"
        ),
        None,
    )


def _dream_real_participant_run_id(
    *,
    participant_id: str,
    encounter_set_id: str,
    round_id: str,
    case_id: str,
    life_case_version: str,
) -> str:
    identity = {
        "participant_id": participant_id,
        "encounter_set_id": encounter_set_id,
        "round_id": round_id,
        "case_id": case_id,
        "life_case_version": life_case_version,
    }
    return f"dream-real:{canonical_hash(identity)}"


def _dream_reality_question_payload(
    *,
    question: LifeTreeQuestionInstance | None,
    exploration: TopicExploration | None,
    profile: dict[str, object],
    expected_life_case_version: str,
) -> dict[str, object]:
    if question is None:
        return {
            "schema_version": "deepbazi.dream-reality-question-view.v1",
            "available": False,
            "empty_state": "这棵树暂时没有开放新的命题",
            "question": None,
            "sealed": False,
            "selected_option_id": "",
            "sealed_at": None,
            "reveal_status": "NOT_STARTED",
            "fruit_state": "NONE",
            "tree_visual_profile": profile,
            "source_life_case_version": expected_life_case_version,
            "write_owner": "TopicExploration",
            "writes_life_case": False,
        }
    selected_option_id = (
        exploration.responses.get(question.instance_id, "")
        if exploration is not None
        else ""
    )
    return {
        "schema_version": "deepbazi.dream-reality-question-view.v1",
        "available": True,
        "empty_state": "",
        "question": {
            "question_instance_id": question.instance_id,
            "blueprint_id": question.blueprint_id,
            "blueprint_version": question.blueprint_version,
            "title": question.title,
            "prompt": question.prompt,
            "options": [
                {
                    "option_id": item.option_id,
                    "label": item.label_template,
                }
                for item in question.options
            ],
            "why_this_question": question.why_this_question,
            "observation_window": question.observation_window,
            "reveal_policy": question.reveal_policy,
        },
        "sealed": exploration is not None,
        "selected_option_id": selected_option_id,
        "sealed_at": (
            exploration.created_at.isoformat()
            if exploration is not None
            else None
        ),
        "reveal_status": (
            exploration.responses.get(
                "_reveal_status",
                "WAITING_REALITY_EVIDENCE",
            )
            if exploration is not None
            else "NOT_STARTED"
        ),
        "fruit_state": (
            "PENDING_REALITY_EVIDENCE"
            if exploration is not None
            else "FLOWER_OPEN"
        ),
        "tree_visual_profile": profile,
        "source_life_case_version": expected_life_case_version,
        "write_owner": "TopicExploration",
        "writes_life_case": False,
    }


def _validate_run_id(value: str) -> None:
    if not value or len(value) > 120:
        raise RelationWorkP0Unavailable("invalid_participant_run_id")
    if any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_:." for character in value):
        raise RelationWorkP0Unavailable("invalid_participant_run_id")


def _validate_request_id(value: str) -> None:
    if not value or len(value) > 120:
        raise RelationWorkP0Unavailable("invalid_abu_observation_request_id")
    if any(
        character
        not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_:."
        for character in value
    ):
        raise RelationWorkP0Unavailable("invalid_abu_observation_request_id")


def _real_participant_run_id(
    *,
    participant_id: str,
    case_id: str,
    foundation_hash: str,
) -> str:
    return (
        "life-tree-real:"
        + canonical_hash(
            {
                "participant_id": participant_id,
                "case_id": case_id,
                "foundation_hash": foundation_hash,
            }
        )
    )


def _canonical_timing_summary(
    canvas: dict[str, Any],
) -> dict[str, Any]:
    stages = canvas.get("stages")
    stages = stages if isinstance(stages, dict) else {}
    return {
        "source": "CANONICAL_ONECANVAS",
        "default_stage": canvas.get("default_stage"),
        "stage_order": canvas.get("stage_order"),
        "stages": {
            stage_id: {
                "title": stage.get("title"),
                "summary": stage.get("summary"),
                "diff_hash": canonical_hash(stage.get("diff") or {}),
            }
            for stage_id, stage in stages.items()
            if isinstance(stage, dict)
        },
        "frontend_inference_allowed": False,
    }


def _professional_state(
    projection: RelationWorkProjectionView,
) -> dict[str, object]:
    resolved_count = len(projection.professionally_resolved_view)
    return {
        "resolved_count": resolved_count,
        "message": (
            "当前已有获准展示的有界专业作用。"
            if resolved_count
            else "当前没有已获专业准入的有效做功。"
        ),
        "main_work_declared": False,
        "fail_closed": True,
    }


def _write_boundary() -> dict[str, object]:
    return {
        "owner": "TopicExploration",
        "writes_life_case": False,
        "upgrades_relation_effect": False,
        "upgrades_work_path": False,
        "declares_main_work": False,
    }


def _abu_observation_reply(
    *,
    question: LifeTreeQuestionInstance,
    message: str,
) -> tuple[str, str]:
    compact = message.lower()
    hypotheses = "、".join(dict.fromkeys(question.distinguished_hypotheses))
    if any(token in compact for token in ("确定", "主线", "有效", "结论", "就是")):
        return (
            "unresolved_professional_boundary",
            "这里还没有获专业准入的有效做功。我们可以比较"
            f"{hypotheses}的证据，却不能把一次偏好说成主线。",
        )
    if any(token in compact for token in ("依据", "证据", "为什么", "凭什么")):
        return (
            "bounded_evidence",
            f"这道题只沿着当前投影已有的关系事实和候选看：{question.why_this_question}",
        )
    if any(token in compact for token in ("下一", "还看", "继续", "再看")):
        return (
            "next_observation",
            "先看哪一条证据会让这些候选真正分开。没有新的权威证据时，"
            "保持未决比替它们排座次更准确。",
        )
    return (
        "user_observation",
        "我把这句话留作你的观察。它可以帮助继续比较"
        f"{hypotheses}，但不会改写命盘，也不会替代专业判定。",
    )


def _abu_observation_boundaries() -> dict[str, object]:
    return {
        "facts_are_server_projection_only": True,
        "candidates_are_not_professional_effects": True,
        "user_statement_is_not_lifecase_truth": True,
        "llm_used": False,
        "writes_life_case": False,
    }


def _abu_observation_turn_payload(
    exploration: TopicExploration,
) -> dict[str, object]:
    return {
        "turn_id": exploration.exploration_id,
        "question_instance_id": exploration.responses.get(
            "question_instance_id",
            "",
        ),
        "user_message": exploration.responses.get("user_message", ""),
        "abu_message": exploration.responses.get("abu_message", ""),
        "classification": exploration.responses.get("classification", ""),
        "created_at": exploration.created_at.isoformat(),
    }


def _abu_observation_history(
    explorations: list[TopicExploration],
) -> list[dict[str, object]]:
    return [
        _abu_observation_turn_payload(item)
        for item in sorted(explorations, key=lambda entry: entry.created_at)
        if item.experiment_kind == "life_tree_abu_observation_turn"
    ]


def _tree_visual_profile(
    context: RealRelationWorkContext,
) -> dict[str, object]:
    graph = context.metadata["_authoritative_graph"]
    nodes = [
        item
        for item in graph.nodes
        if item.element in {"wood", "fire", "earth", "metal", "water"}
    ]
    counts = Counter(item.element for item in nodes)
    total = max(1, len(nodes))
    ratios = {
        element: round(counts[element] / total, 4)
        for element in ("wood", "fire", "earth", "metal", "water")
    }
    highest = max(counts.values(), default=0)
    lowest = min((counts[element] for element in ratios), default=0)
    balance = 1.0 if highest == 0 else 1.0 - ((highest - lowest) / highest)
    relation_counts = Counter(
        item.fact_key.relation_family for item in context.relation_facts
    )
    directional_total = max(
        1,
        relation_counts["generates"]
        + relation_counts["controls"]
        + relation_counts["same_element_support"]
        + relation_counts["clashes"],
    )
    tension = _bounded_metric(
        0.25
        + (relation_counts["controls"] / directional_total) * 0.4
        + min(0.1, relation_counts["clashes"] * 0.05)
        + (1.0 - balance) * 0.2
    )
    density = _bounded_metric(
        0.32
        + max(0, len(nodes) - 12) * 0.04
        + max(0, len(context.relation_facts) - 60) * 0.002
    )
    moisture = _bounded_metric(ratios["water"])
    light = _bounded_metric(ratios["fire"] + ratios["wood"] * 0.18)
    growth = _bounded_metric(
        0.2
        + ratios["wood"] * 1.4
        + ratios["water"] * 0.45
        + min(0.16, len(context.work_path_candidates) * 0.04)
    )
    if moisture >= 0.18 and growth >= 0.55:
        form = "wide_flowing"
    elif balance >= 0.65:
        form = "wide_balanced"
    elif tension >= 0.52:
        form = "tall_tensed"
    else:
        form = "compact_grounded"
    if moisture >= 0.14:
        material = "dew_fed"
    elif light >= 0.25:
        material = "sun_warmed"
    else:
        material = "mineral_cool"
    scale_x = {
        "wide_flowing": 1.16,
        "wide_balanced": 1.14,
        "tall_tensed": 0.86,
        "compact_grounded": 0.99,
    }[form]
    scale_y = {
        "wide_flowing": 0.95,
        "wide_balanced": 0.96,
        "tall_tensed": 1.06,
        "compact_grounded": 1.0,
    }[form]
    dominant_element = max(ratios, key=ratios.get)
    hue_rotate = {
        "wood": 72.0,
        "fire": -12.0,
        "earth": 0.0,
        "metal": 52.0,
        "water": 148.0,
    }[dominant_element] + {
        "dew_fed": 4.0,
        "sun_warmed": -4.0,
        "mineral_cool": 0.0,
    }[material]
    rotation = -1.2 if relation_counts["controls"] >= relation_counts["generates"] else 0.7
    identity = {
        "foundation_hash": context.projection.content_hash,
        "element_counts": dict(sorted(counts.items())),
        "relation_counts": dict(sorted(relation_counts.items())),
        "dominant_element": dominant_element,
        "form": form,
        "material": material,
    }
    return {
        "schema_version": "deepbazi.life-tree-visual-profile.p1.v1",
        "profile_id": f"tree-visual:{canonical_hash(identity)}",
        "source": "SERVER_DERIVED_CURRENT_LIFECASE_GRAPH",
        "form": form,
        "material": material,
        "metrics": {
            "density": round(density, 3),
            "tension": round(tension, 3),
            "moisture": round(moisture, 3),
            "light": round(light, 3),
            "growth": round(growth, 3),
            "balance": round(balance, 3),
        },
        "element_distribution": ratios,
        "render_tokens": {
            "scale_x": scale_x,
            "scale_y": scale_y,
            "rotation_deg": rotation,
            "hue_rotate_deg": hue_rotate,
            "saturation": round(0.82 + density * 0.18, 3),
            "brightness": round(0.94 + light * 0.16, 3),
            "canopy_echo_opacity": round(0.08 + density * 0.24, 3),
            "ground_sheen_opacity": round(0.04 + moisture * 2.1, 3),
        },
        "visual_metaphor_only": True,
        "professional_judgment": False,
        "frontend_metric_inference_allowed": False,
    }


def _bounded_metric(value: float) -> float:
    return max(0.0, min(1.0, value))


def _tree_scene_state(
    *,
    projection: RelationWorkProjectionView,
    questions: tuple[LifeTreeQuestionInstance, ...],
    explorations: list[TopicExploration],
) -> dict[str, object]:
    questions_by_category: dict[str, list[LifeTreeQuestionInstance]] = {}
    for question in questions:
        questions_by_category.setdefault(question.category, []).append(question)
    answered_refs = {
        question_ref
        for exploration in explorations
        for question_ref in exploration.responses
    }
    life_questions = questions_by_category.get("life_observation", [])
    flower_unlocked = bool(life_questions)
    definitions = (("flower-question", "FLOWER", "life_observation"),)
    nodes = []
    for node_id, organ, category in definitions:
        items = questions_by_category.get(category, [])
        answered_count = sum(
            item.instance_id in answered_refs for item in items
        )
        if not items:
            status = "unavailable"
        elif category == "life_observation" and not flower_unlocked:
            status = "locked"
        elif answered_count == len(items):
            status = "explored"
        else:
            status = "available"
        nodes.append(
            {
                "node_id": node_id,
                "organ": organ,
                "category": category,
                "status": status,
                "question_refs": [item.instance_id for item in items],
                "projection_ref": projection.foundation_ref,
                "visual_truth_authority": False,
            }
        )
    return {
        "schema_version": "deepbazi.real-life-tree-scene.p1.v1",
        "scene_id": f"life-tree-scene:{projection.foundation_content_hash}",
        "foundation_ref": projection.foundation_ref,
        "foundation_hash": projection.foundation_content_hash,
        "nodes": nodes,
        "flower_unlocked": flower_unlocked,
        "fruit": {
            "visible": False,
            "reason": "blindround_not_bound",
        },
        "persistent_source": "TopicExploration",
        "frontend_truth_inference_allowed": False,
    }


__all__ = [
    "MemoryRelationWorkP0Store",
    "RelationWorkP0Conflict",
    "RelationWorkP0FeaturePolicy",
    "RelationWorkP0Service",
    "RelationWorkP0Unavailable",
]
