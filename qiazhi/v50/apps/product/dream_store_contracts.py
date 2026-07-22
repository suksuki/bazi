from __future__ import annotations

from typing import Protocol

from experience.dream import DreamSceneGrant, DreamVisit


class DreamStoreConflict(RuntimeError):
    pass


class DreamStore(Protocol):
    persistent: bool
    storage_name: str

    def create_visit(self, visit: DreamVisit) -> DreamVisit: ...
    def update_visit(self, visit: DreamVisit, *, expected_row_version: int) -> DreamVisit: ...
    def get_visit(self, *, visit_id: str, owner_user_id: str) -> DreamVisit | None: ...
    def find_resumable_visit(self, *, owner_user_id: str) -> DreamVisit | None: ...
    def save_grant(self, grant: DreamSceneGrant) -> DreamSceneGrant: ...
    def get_grant(self, *, public_scene_ref: str) -> DreamSceneGrant | None: ...
    def list_grants(self) -> list[DreamSceneGrant]: ...


__all__ = ["DreamStore", "DreamStoreConflict"]
