from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Callable
from uuid import uuid4

from experience.canonical_scene import CanonicalScene
from experience.dream import (
    DREAM_PILOT_CONSENT_VERSION,
    DREAM_PRIVACY_POLICY_VERSION,
    DREAM_PROJECTION_VERSION,
    DREAM_SELECTION_POLICY_VERSION,
    DreamAuditEvent,
    DreamConsentStatus,
    DreamEncounterProjection,
    DreamFeatureStatus,
    DreamMirrorProjection,
    DreamSceneGrant,
    DreamTreeProjection,
    DreamVisit,
    DreamVisitState,
    EncounterSet,
    transition_visit,
    visit_view,
)
from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner, CanonicalSceneUnavailable
from product.canvas_projection import ReadOnlyCanvasUnavailable, ReadOnlySixPillarCanvasService
from product.dream_feature import DreamFeaturePolicy
from product.dream_pilot import (
    CANONICAL_NPC_IDS,
    ensure_authorized_human_projection_life_case,
)
from product.dream_projection import DreamProjectionCompiler, eligibility_snapshot
from product.dream_store_contracts import DreamStore, DreamStoreConflict


class DreamBridgeError(ValueError):
    pass


class DreamTruthAdapter:
    """Read formal V50 sources through their existing application owners."""

    def __init__(self, *, case_store: AgentCaseStore) -> None:
        self.case_store = case_store
        self.scene_owner = CanonicalSceneOwner(case_store=case_store)
        self.canvas_owner = ReadOnlySixPillarCanvasService(case_store=case_store)

    def scene(self, grant: DreamSceneGrant) -> CanonicalScene:
        return self.scene_owner.issue_authorized_scene(
            case_id=grant.case_id,
            authorization_ref=grant.grant_id,
            account_role="member",
        )

    def canvas(self, grant: DreamSceneGrant) -> dict[str, object]:
        return self.canvas_owner.issue_authorized(
            case_id=grant.case_id,
            authorization_ref=grant.grant_id,
            account_role="member",
        )

    def canvas_context(
        self,
        grant: DreamSceneGrant,
        *,
        stage: str,
        selected_object_ref: str,
        visible_layer: str,
    ) -> dict[str, object]:
        context = self.canvas_owner.issue_authorized_context(
            case_id=grant.case_id,
            authorization_ref=grant.grant_id,
            account_role="member",
            stage=stage,
            selected_object_ref=selected_object_ref,
            visible_layer=visible_layer,
        )
        return context.model_dump(mode="json")


class DreamEligibilityService:
    def __init__(
        self,
        *,
        store: DreamStore,
        truth: DreamTruthAdapter,
        clock: Callable[[], datetime],
    ) -> None:
        self.store = store
        self.truth = truth
        self.clock = clock

    def eligible(self) -> tuple[list[tuple[DreamSceneGrant, CanonicalScene]], dict[str, int]]:
        now = self.clock()
        accepted: list[tuple[DreamSceneGrant, CanonicalScene]] = []
        reasons: dict[str, int] = {}
        seen_public: set[str] = set()
        seen_sources: set[str] = set()
        for grant in self.store.list_grants():
            reason = ""
            if not grant.is_active_at(now):
                reason = "grant_inactive"
            elif grant.purpose != "dream_bridge_v1":
                reason = "purpose_not_allowed"
            elif grant.anonymization_policy_version != DREAM_PRIVACY_POLICY_VERSION:
                reason = "privacy_policy_mismatch"
            elif grant.public_scene_ref in seen_public:
                reason = "public_scene_ref_duplicate"
            elif not self._subject_boundary_valid(grant):
                reason = "scene_subject_boundary_invalid"
            if reason:
                reasons[reason] = reasons.get(reason, 0) + 1
                continue
            try:
                scene = self.truth.scene(grant)
                self.truth.canvas(grant)
            except (CanonicalSceneUnavailable, ReadOnlyCanvasUnavailable, ValueError):
                reasons["canonical_source_unavailable"] = (
                    reasons.get("canonical_source_unavailable", 0) + 1
                )
                continue
            if scene.identity.source_hash != grant.authorized_source_hash:
                reasons["authorized_source_version_changed"] = (
                    reasons.get("authorized_source_version_changed", 0) + 1
                )
                continue
            if scene.identity.source_hash in seen_sources:
                reasons["canonical_scene_duplicate"] = (
                    reasons.get("canonical_scene_duplicate", 0) + 1
                )
                continue
            if len(scene.chart_facts) != 4:
                reasons["canonical_chart_incomplete"] = (
                    reasons.get("canonical_chart_incomplete", 0) + 1
                )
                continue
            seen_public.add(grant.public_scene_ref)
            seen_sources.add(scene.identity.source_hash)
            accepted.append((grant, scene))
        return accepted, reasons

    def pilot_composition(
        self,
        *,
        user_id: str,
        human_case_id: str = "",
    ) -> tuple[list[tuple[DreamSceneGrant, CanonicalScene]], bool, int]:
        eligible, _ = self.eligible()
        human = [
            item
            for item in eligible
            if item[0].subject_kind == "authorized_human"
            and item[0].authorized_by_ref == user_id
            and (not human_case_id or item[0].case_id == human_case_id)
        ]
        human.sort(key=lambda item: (item[0].updated_at, item[0].grant_id), reverse=True)
        npc_by_id = {
            item[0].subject_ref: item
            for item in eligible
            if item[0].subject_kind == "canonical_npc"
            and item[0].subject_ref in CANONICAL_NPC_IDS
        }
        npcs = [npc_by_id[npc_id] for npc_id in sorted(CANONICAL_NPC_IDS) if npc_id in npc_by_id]
        selected = [*human[:1], *npcs]
        return selected, bool(human), len(npcs)

    def _subject_boundary_valid(self, grant: DreamSceneGrant) -> bool:
        row = self.truth.case_store.get(case_id=grant.case_id)
        if row is None:
            return False
        if grant.subject_kind == "authorized_human":
            return bool(
                grant.subject_ref
                and row.get("user_id") == grant.authorized_by_ref
            )
        if grant.subject_kind == "canonical_npc":
            npc = row.get("canonical_npc") if isinstance(row.get("canonical_npc"), dict) else {}
            return bool(
                row.get("user_id") is None
                and grant.subject_ref in CANONICAL_NPC_IDS
                and npc.get("npc_id") == grant.subject_ref
                and npc.get("identity_class") == "canonical_npc"
                and npc.get("not_human") is True
                and npc.get("not_reality_evidence") is True
                and npc.get("canonical_lifecase_ref")
            )
        return False


class DreamJourneyService:
    def __init__(
        self,
        *,
        case_store: AgentCaseStore,
        dream_store: DreamStore,
        feature_policy: DreamFeaturePolicy,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.case_store = case_store
        self.store = dream_store
        self.feature_policy = feature_policy
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.truth = DreamTruthAdapter(case_store=case_store)
        self.eligibility = DreamEligibilityService(
            store=dream_store,
            truth=self.truth,
            clock=self.clock,
        )
        self.projection = DreamProjectionCompiler()

    def feature_status(self, *, user_id: str, case_id: str = "") -> DreamFeatureStatus:
        enabled = self.feature_policy.allows(user_id)
        if not enabled:
            return DreamFeatureStatus(
                enabled=False,
                available=False,
                resumable=False,
                eligible_scene_count=0,
                reason_code="dream_feature_disabled",
            )
        consent = self._consent_status(user_id=user_id, case_id=case_id)
        composition, human_ready, npc_count = self.eligibility.pilot_composition(
            user_id=user_id,
            human_case_id=case_id,
        )
        available = human_ready and npc_count == 2 and len(composition) == 3
        resumable = False
        current = self.store.find_resumable_visit(owner_user_id=user_id)
        if current is not None and available and self._visit_matches(current, composition):
            try:
                self._validate_visit_grants(current)
                resumable = True
            except DreamBridgeError:
                resumable = False
        return DreamFeatureStatus(
            enabled=True,
            available=available,
            resumable=resumable,
            eligible_scene_count=len(composition),
            reason_code=(
                "dream_ready"
                if available
                else "dream_npc_bootstrap_incomplete"
                if npc_count != 2
                else "dream_human_consent_required"
            ),
            consent_state=consent.state,
            human_scene_eligible=human_ready,
            canonical_npc_scene_count=npc_count,
            composition_ready=available,
        )

    def consent_status(self, *, user_id: str, case_id: str) -> DreamConsentStatus:
        self._require_feature(user_id)
        return self._consent_status(user_id=user_id, case_id=case_id)

    def grant_consent(self, *, user_id: str, case_id: str) -> DreamConsentStatus:
        self._require_feature(user_id)
        row = self._owned_human_case(user_id=user_id, case_id=case_id)
        try:
            ensure_authorized_human_projection_life_case(
                case_store=self.case_store,
                case_id=case_id,
                user_id=user_id,
            )
        except ValueError as exc:
            raise DreamBridgeError("dream_human_scene_not_formally_available") from exc
        grant_id, public_scene_ref, subject_ref = _human_grant_identity(
            user_id=user_id,
            case_id=case_id,
        )
        try:
            scene = self.truth.scene_owner.issue_authorized_scene(
                case_id=case_id,
                authorization_ref=grant_id,
                account_role="member",
            )
            self.truth.canvas_owner.issue_authorized(
                case_id=case_id,
                authorization_ref=grant_id,
                account_role="member",
            )
        except (CanonicalSceneUnavailable, ReadOnlyCanvasUnavailable, ValueError) as exc:
            raise DreamBridgeError("dream_human_scene_not_formally_available") from exc
        existing = self.store.get_grant(public_scene_ref=public_scene_ref)
        if existing is not None and (
            existing.case_id != case_id
            or existing.authorized_by_ref != user_id
            or existing.subject_kind != "authorized_human"
            or existing.subject_ref != subject_ref
        ):
            raise DreamBridgeError("dream_human_consent_identity_conflict")
        if (
            existing is not None
            and existing.is_active_at(self.clock())
            and existing.authorized_source_hash == scene.identity.source_hash
        ):
            return self._consent_status(user_id=user_id, case_id=case_id)
        now = self.clock()
        sequence = (existing.authorization_sequence + 1) if existing is not None else 1
        self.store.save_grant(DreamSceneGrant(
            grant_id=grant_id,
            case_id=case_id,
            public_scene_ref=public_scene_ref,
            authorization_basis="explicit_in_product_dream_pilot_consent",
            authorized_by_ref=user_id,
            authorization_version=f"{DREAM_PILOT_CONSENT_VERSION}.r{sequence}",
            authorization_sequence=sequence,
            subject_kind="authorized_human",
            subject_ref=subject_ref,
            anonymization_policy_version=DREAM_PRIVACY_POLICY_VERSION,
            authorized_source_hash=scene.identity.source_hash,
            valid_from=now,
            valid_until=None,
            withdrawn_at=None,
            status="active",
            created_at=existing.created_at if existing is not None else now,
            updated_at=now,
        ))
        _ = row
        return self._consent_status(user_id=user_id, case_id=case_id)

    def withdraw_consent(self, *, user_id: str, case_id: str) -> DreamConsentStatus:
        self._require_feature(user_id)
        self._owned_human_case(user_id=user_id, case_id=case_id)
        _, public_scene_ref, _ = _human_grant_identity(user_id=user_id, case_id=case_id)
        grant = self.store.get_grant(public_scene_ref=public_scene_ref)
        if grant is None:
            return self._consent_status(user_id=user_id, case_id=case_id)
        if grant.authorized_by_ref != user_id or grant.subject_kind != "authorized_human":
            raise DreamBridgeError("dream_human_consent_identity_conflict")
        if grant.status == "active":
            now = self.clock()
            self.store.save_grant(grant.model_copy(update={
                "status": "withdrawn",
                "withdrawn_at": now,
                "updated_at": now,
            }))
        return self._consent_status(user_id=user_id, case_id=case_id)

    def create_or_resume_visit(
        self,
        *,
        user_id: str,
        home_case_id: str = "",
    ) -> DreamVisit:
        self._require_feature(user_id)
        composition, human_ready, npc_count = self.eligibility.pilot_composition(
            user_id=user_id,
            human_case_id=home_case_id,
        )
        if not human_ready or npc_count != 2 or len(composition) != 3:
            raise DreamBridgeError("DREAM_ENCOUNTER_UNAVAILABLE")
        current = self.store.find_resumable_visit(owner_user_id=user_id)
        if current is not None and self._visit_matches(current, composition):
            try:
                self._validate_visit_grants(current)
                return current
            except DreamBridgeError:
                pass
        human_case_id = next(
            grant.case_id for grant, _ in composition if grant.subject_kind == "authorized_human"
        )
        home_ref = self._home_life_case_ref(
            user_id=user_id,
            requested_case_id=home_case_id or human_case_id,
        )
        selected = sorted(
            composition,
            key=lambda item: hashlib.sha256(
                f"{user_id}|{DREAM_SELECTION_POLICY_VERSION}|{item[0].public_scene_ref}".encode()
            ).hexdigest(),
        )[:3]
        now = self.clock()
        visit_id = f"dream-visit-{uuid4().hex}"
        encounter = EncounterSet(
            encounter_set_id=f"dream-encounter-{uuid4().hex}",
            visit_id=visit_id,
            scene_refs=[grant.public_scene_ref for grant, _ in selected],
            eligibility_snapshot=[
                eligibility_snapshot(grant=grant, scene=scene)
                for grant, scene in selected
            ],
            created_at=now,
        )
        visit = DreamVisit(
            visit_id=visit_id,
            owner_user_id=user_id,
            home_life_case_ref=home_ref,
            encounter_set=encounter,
            created_at=now,
            updated_at=now,
            audit_events=[DreamAuditEvent(
                event_code="dream_visit_created",
                occurred_at=now,
            )],
        )
        return self.store.create_visit(visit)

    def get_visit(self, *, user_id: str, visit_id: str) -> DreamVisit:
        self._require_feature(user_id)
        visit = self.store.get_visit(visit_id=visit_id, owner_user_id=user_id)
        if visit is None:
            raise DreamBridgeError("dream_visit_not_found")
        return visit

    def enter(self, *, user_id: str, visit_id: str) -> DreamVisit:
        visit = self.get_visit(user_id=user_id, visit_id=visit_id)
        self._validate_visit_grants(visit)
        if visit.state in {
            DreamVisitState.ENCOUNTER_READY,
            DreamVisitState.TREE_SELECTED,
            DreamVisitState.TREE_OBSERVING,
            DreamVisitState.MIRROR_OPEN,
        }:
            return visit
        if visit.state == DreamVisitState.COMPLETED:
            raise DreamBridgeError("dream_visit_completed")
        original_version = visit.row_version
        now = self.clock()
        for target in (
            DreamVisitState.PATH_OFFERED,
            DreamVisitState.DREAM_ENTERING,
            DreamVisitState.ENCOUNTER_READY,
        ):
            if visit.state == target:
                continue
            visit = transition_visit(visit, target, at=now)
        visit = visit.model_copy(update={
            "audit_events": [
                *visit.audit_events,
                DreamAuditEvent(event_code="dream_entry_accepted", occurred_at=now),
            ]
        })
        return self._save(visit, expected_row_version=original_version)

    def encounter(
        self,
        *,
        user_id: str,
        visit_id: str,
    ) -> DreamEncounterProjection:
        visit = self.get_visit(user_id=user_id, visit_id=visit_id)
        if visit.state not in {
            DreamVisitState.ENCOUNTER_READY,
            DreamVisitState.TREE_SELECTED,
            DreamVisitState.TREE_OBSERVING,
            DreamVisitState.MIRROR_OPEN,
        }:
            raise DreamBridgeError("dream_encounter_not_ready")
        scenes = self._validate_visit_grants(visit)
        return self.projection.encounter(visit=visit, scenes=scenes)

    def select_tree(
        self,
        *,
        user_id: str,
        visit_id: str,
        public_scene_ref: str,
    ) -> DreamVisit:
        visit = self.get_visit(user_id=user_id, visit_id=visit_id)
        self._validate_visit_grants(visit)
        if public_scene_ref not in visit.encounter_set.scene_refs:
            raise DreamBridgeError("dream_scene_not_in_encounter")
        if visit.selected_scene_ref:
            if visit.selected_scene_ref != public_scene_ref:
                raise DreamBridgeError("dream_tree_selection_locked")
            return visit
        if visit.state != DreamVisitState.ENCOUNTER_READY:
            raise DreamBridgeError("dream_tree_selection_not_allowed")
        original_version = visit.row_version
        now = self.clock()
        visit = visit.model_copy(update={"selected_scene_ref": public_scene_ref})
        visit = transition_visit(visit, DreamVisitState.TREE_SELECTED, at=now)
        visit = transition_visit(visit, DreamVisitState.TREE_OBSERVING, at=now)
        visit = visit.model_copy(update={
            "audit_events": [
                *visit.audit_events,
                DreamAuditEvent(event_code="dream_tree_selected", occurred_at=now),
            ]
        })
        return self._save(visit, expected_row_version=original_version)

    def tree_projection(
        self,
        *,
        user_id: str,
        visit_id: str,
        public_scene_ref: str,
    ) -> DreamTreeProjection:
        visit = self.get_visit(user_id=user_id, visit_id=visit_id)
        grant, scene = self._selected_scene(
            visit=visit,
            public_scene_ref=public_scene_ref,
        )
        return self.projection.tree(grant=grant, scene=scene)

    def mirror_projection(
        self,
        *,
        user_id: str,
        visit_id: str,
        public_scene_ref: str,
    ) -> DreamMirrorProjection:
        visit = self.get_visit(user_id=user_id, visit_id=visit_id)
        if visit.state != DreamVisitState.MIRROR_OPEN:
            raise DreamBridgeError("dream_mirror_not_open")
        grant, scene = self._selected_scene(
            visit=visit,
            public_scene_ref=public_scene_ref,
        )
        canvas = self.truth.canvas(grant)
        return self.projection.mirror(
            grant=grant,
            scene=scene,
            canvas=canvas,
        )

    def open_mirror(self, *, user_id: str, visit_id: str) -> DreamVisit:
        visit = self.get_visit(user_id=user_id, visit_id=visit_id)
        self._validate_visit_grants(visit)
        if visit.state == DreamVisitState.MIRROR_OPEN:
            return visit
        if visit.state != DreamVisitState.TREE_OBSERVING:
            raise DreamBridgeError("dream_mirror_open_not_allowed")
        original_version = visit.row_version
        now = self.clock()
        visit = transition_visit(visit, DreamVisitState.MIRROR_OPEN, at=now)
        visit = visit.model_copy(update={
            "audit_events": [
                *visit.audit_events,
                DreamAuditEvent(event_code="dream_mirror_opened", occurred_at=now),
            ]
        })
        return self._save(visit, expected_row_version=original_version)

    def close_mirror(self, *, user_id: str, visit_id: str) -> DreamVisit:
        visit = self.get_visit(user_id=user_id, visit_id=visit_id)
        self._validate_visit_grants(visit)
        if visit.state == DreamVisitState.TREE_OBSERVING:
            return visit
        if visit.state != DreamVisitState.MIRROR_OPEN:
            raise DreamBridgeError("dream_mirror_close_not_allowed")
        original_version = visit.row_version
        visit = transition_visit(visit, DreamVisitState.TREE_OBSERVING, at=self.clock())
        return self._save(visit, expected_row_version=original_version)

    def mirror_context(
        self,
        *,
        user_id: str,
        visit_id: str,
        public_scene_ref: str,
        stage: str,
        selected_object_ref: str,
        visible_layer: str,
    ) -> dict[str, object]:
        visit = self.get_visit(user_id=user_id, visit_id=visit_id)
        if visit.state != DreamVisitState.MIRROR_OPEN:
            raise DreamBridgeError("dream_mirror_not_open")
        grant, scene = self._selected_scene(
            visit=visit,
            public_scene_ref=public_scene_ref,
        )
        canvas = self.truth.canvas(grant)
        selected_object_ref = self.projection.resolve_canvas_ref(
            grant=grant,
            canvas=canvas,
            public_ref=selected_object_ref,
        )
        context = self.truth.canvas_context(
            grant,
            stage=stage,
            selected_object_ref=selected_object_ref,
            visible_layer=visible_layer,
        )
        return self.projection.context(grant=grant, scene=scene, context=context)

    def _selected_scene(
        self,
        *,
        visit: DreamVisit,
        public_scene_ref: str,
    ) -> tuple[DreamSceneGrant, CanonicalScene]:
        if not visit.selected_scene_ref or visit.selected_scene_ref != public_scene_ref:
            raise DreamBridgeError("dream_scene_not_selected")
        scenes = self._validate_visit_grants(visit)
        return scenes[public_scene_ref]

    def _validate_visit_grants(
        self,
        visit: DreamVisit,
    ) -> dict[str, tuple[DreamSceneGrant, CanonicalScene]]:
        now = self.clock()
        output: dict[str, tuple[DreamSceneGrant, CanonicalScene]] = {}
        snapshots = {
            item.public_scene_ref: item
            for item in visit.encounter_set.eligibility_snapshot
        }
        for public_ref in visit.encounter_set.scene_refs:
            grant = self.store.get_grant(public_scene_ref=public_ref)
            snapshot = snapshots.get(public_ref)
            if grant is None or snapshot is None or not grant.is_active_at(now):
                raise DreamBridgeError("dream_scene_authorization_unavailable")
            try:
                scene = self.truth.scene(grant)
            except (CanonicalSceneUnavailable, ValueError) as exc:
                raise DreamBridgeError("dream_scene_authorization_unavailable") from exc
            if (
                scene.identity.source_hash != snapshot.source_hash
                or scene.identity.source_hash != grant.authorized_source_hash
                or grant.grant_id != snapshot.grant_ref
                or grant.authorization_version != snapshot.authorization_version
                or grant.anonymization_policy_version != snapshot.privacy_policy_version
                or grant.subject_kind != snapshot.subject_kind
                or grant.subject_ref != snapshot.subject_ref
            ):
                raise DreamBridgeError("dream_scene_source_version_changed")
            output[public_ref] = (grant, scene)
        humans = [
            grant
            for grant, _ in output.values()
            if grant.subject_kind == "authorized_human"
            and grant.authorized_by_ref == visit.owner_user_id
        ]
        npc_ids = {
            grant.subject_ref
            for grant, _ in output.values()
            if grant.subject_kind == "canonical_npc"
        }
        if len(humans) != 1 or npc_ids != CANONICAL_NPC_IDS:
            raise DreamBridgeError("dream_pilot_composition_invalid")
        return output

    def _consent_status(self, *, user_id: str, case_id: str) -> DreamConsentStatus:
        if not case_id:
            grants = [
                item
                for item in self.store.list_grants()
                if item.subject_kind == "authorized_human" and item.authorized_by_ref == user_id
            ]
            grants.sort(key=lambda item: (item.updated_at, item.grant_id), reverse=True)
            case_id = grants[0].case_id if grants else "no-active-case"
        try:
            self._owned_human_case(user_id=user_id, case_id=case_id)
        except DreamBridgeError:
            return DreamConsentStatus(
                case_id=case_id,
                state="case_unavailable",
                can_grant=False,
                can_withdraw=False,
            )
        _, public_scene_ref, _ = _human_grant_identity(user_id=user_id, case_id=case_id)
        grant = self.store.get_grant(public_scene_ref=public_scene_ref)
        if grant is None:
            return DreamConsentStatus(
                case_id=case_id,
                state="not_granted",
                can_grant=True,
                can_withdraw=False,
            )
        if grant.status != "active" or grant.withdrawn_at is not None:
            return DreamConsentStatus(
                case_id=case_id,
                state="withdrawn",
                can_grant=True,
                can_withdraw=False,
            )
        try:
            scene = self.truth.scene(grant)
        except (CanonicalSceneUnavailable, ValueError):
            return DreamConsentStatus(
                case_id=case_id,
                state="source_changed",
                can_grant=True,
                can_withdraw=True,
            )
        changed = scene.identity.source_hash != grant.authorized_source_hash
        return DreamConsentStatus(
            case_id=case_id,
            state="source_changed" if changed else "active",
            can_grant=changed,
            can_withdraw=True,
        )

    def _owned_human_case(self, *, user_id: str, case_id: str) -> dict[str, object]:
        row = self.case_store.get(case_id=case_id)
        if row is None or row.get("user_id") != user_id:
            raise DreamBridgeError("dream_human_case_not_owned")
        return row

    @staticmethod
    def _visit_matches(
        visit: DreamVisit,
        composition: list[tuple[DreamSceneGrant, CanonicalScene]],
    ) -> bool:
        return set(visit.encounter_set.scene_refs) == {
            grant.public_scene_ref for grant, _ in composition
        }

    def _home_life_case_ref(self, *, user_id: str, requested_case_id: str) -> str:
        rows = (
            [self.case_store.get(case_id=requested_case_id, user_id=user_id)]
            if requested_case_id
            else self.case_store.list_for_user(user_id=user_id)
        )
        row = next((item for item in rows if isinstance(item, dict)), None)
        if row is None:
            raise DreamBridgeError("dream_home_case_required")
        life_case = row.get("life_case") if isinstance(row.get("life_case"), dict) else {}
        return str(life_case.get("life_case_id") or row.get("case_id") or requested_case_id)

    def _require_feature(self, user_id: str) -> None:
        if not self.feature_policy.allows(user_id):
            raise DreamBridgeError("dream_feature_disabled")

    def _save(self, visit: DreamVisit, *, expected_row_version: int) -> DreamVisit:
        try:
            return self.store.update_visit(
                visit,
                expected_row_version=expected_row_version,
            )
        except DreamStoreConflict as exc:
            raise DreamBridgeError(str(exc)) from exc


__all__ = [
    "DreamBridgeError",
    "DreamEligibilityService",
    "DreamJourneyService",
    "DreamTruthAdapter",
]


def _human_grant_identity(*, user_id: str, case_id: str) -> tuple[str, str, str]:
    digest = hashlib.sha256(
        f"dream-pilot-human|{user_id}|{case_id}".encode()
    ).hexdigest()
    return (
        f"dream-human-grant-{digest[:24]}",
        f"dream-scene-human-{digest[:32]}",
        f"authorized-human-{digest[32:56]}",
    )
