from __future__ import annotations

from typing import Any, Protocol


class LegacyFormalWriteBlocked(ValueError):
    """Raised when a retired representation attempts to become case authority."""


class AgentCaseStore(Protocol):
    persistent: bool
    storage_name: str

    def save(self, *, case_id: str, user_id: str | None, profile_id: str | None, payload: dict[str, Any]) -> None: ...
    def get(self, *, case_id: str, user_id: str | None = None) -> dict[str, Any] | None: ...
    def list_for_user(self, *, user_id: str) -> list[dict[str, Any]]: ...
