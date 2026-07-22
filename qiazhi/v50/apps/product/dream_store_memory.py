from __future__ import annotations

from experience.dream import DreamSceneGrant, DreamVisit, DreamVisitState
from product.dream_store_contracts import DreamStoreConflict


class MemoryDreamStore:
    persistent = False
    storage_name = "memory_only"

    def __init__(self) -> None:
        self._visits: dict[str, DreamVisit] = {}
        self._grants: dict[str, DreamSceneGrant] = {}

    def create_visit(self, visit: DreamVisit) -> DreamVisit:
        if visit.visit_id in self._visits:
            raise DreamStoreConflict("dream_visit_already_exists")
        self._visits[visit.visit_id] = visit
        return visit

    def update_visit(self, visit: DreamVisit, *, expected_row_version: int) -> DreamVisit:
        current = self._visits.get(visit.visit_id)
        if current is None:
            raise DreamStoreConflict("dream_visit_not_found")
        if current.row_version != expected_row_version:
            raise DreamStoreConflict("dream_visit_version_conflict")
        self._visits[visit.visit_id] = visit
        return visit

    def get_visit(self, *, visit_id: str, owner_user_id: str) -> DreamVisit | None:
        visit = self._visits.get(visit_id)
        return visit if visit and visit.owner_user_id == owner_user_id else None

    def find_resumable_visit(self, *, owner_user_id: str) -> DreamVisit | None:
        values = [
            visit
            for visit in self._visits.values()
            if visit.owner_user_id == owner_user_id
            and visit.state != DreamVisitState.COMPLETED
        ]
        return max(values, key=lambda item: item.updated_at, default=None)

    def save_grant(self, grant: DreamSceneGrant) -> DreamSceneGrant:
        existing = self._grants.get(grant.public_scene_ref)
        if existing and existing.grant_id != grant.grant_id:
            raise DreamStoreConflict("dream_public_scene_ref_conflict")
        self._grants[grant.public_scene_ref] = grant
        return grant

    def get_grant(self, *, public_scene_ref: str) -> DreamSceneGrant | None:
        return self._grants.get(public_scene_ref)

    def list_grants(self) -> list[DreamSceneGrant]:
        return list(self._grants.values())


__all__ = ["MemoryDreamStore"]
