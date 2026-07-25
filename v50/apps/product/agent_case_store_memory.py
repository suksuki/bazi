from __future__ import annotations

from typing import Any

from product.agent_case_payload import canonical_case_payload, compatibility_case_row


class MemoryAgentCaseStore:
    persistent = False
    storage_name = "memory_only"

    def __init__(self) -> None:
        self._cases: dict[str, dict[str, Any]] = {}

    def save(self, *, case_id: str, user_id: str | None, profile_id: str | None, payload: dict[str, Any]) -> None:
        canonical = canonical_case_payload(payload)
        self._cases[case_id] = {**canonical, "case_id": case_id, "user_id": user_id, "profile_id": profile_id}

    def get(self, *, case_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        row = self._cases.get(case_id)
        if row is None or (user_id is not None and row.get("user_id") not in {None, user_id}):
            return None
        return compatibility_case_row(row)

    def list_for_user(self, *, user_id: str) -> list[dict[str, Any]]:
        return [compatibility_case_row(row) for row in self._cases.values() if row.get("user_id") == user_id]
