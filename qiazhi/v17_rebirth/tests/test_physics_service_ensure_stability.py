"""单元：PhysicsService.ensure_stability（无 HTTP）。"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from v17_rebirth.backend.services import physics_service
from v17_rebirth.backend.services.physics_service import DataSovereigntyError, PhysicsService


def _stable_tensor() -> dict:
    return {
        "four_pillars": {"year": "甲子", "month": "甲子", "day": "甲子", "hour": "甲子"},
        "luck_pillar": "乙丑",
        "flow_pillar": "丙寅",
        "meta": {"v17_physics_stable": True},
    }


def test_ensure_stability_ok_after_bind() -> None:
    sid = "pytest-ensure-stability-ok"
    try:
        PhysicsService.bind_session_tensor(sid, _stable_tensor())
        asyncio.run(PhysicsService.ensure_stability(sid, wait_sec=1.0, poll_sec=0.02))
    finally:
        PhysicsService.release_session(sid)


def test_ensure_stability_raises_when_unbound() -> None:
    sid = "pytest-ensure-stability-missing"
    PhysicsService.release_session(sid)
    with pytest.raises(DataSovereigntyError, match="physics_metadata_unstable"):
        asyncio.run(PhysicsService.ensure_stability(sid, wait_sec=0.35, poll_sec=0.05))


class _MissingBackend:
    async def get_physics(self, _session_id: str) -> dict[str, Any]:
        return {}

    async def delete_physics(self, _session_id: str) -> None:
        return None


def test_ensure_stability_forces_pass_when_local_tensor_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    sid = "pytest-ensure-stability-local-fallback"
    monkeypatch.setattr(physics_service, "get_state_backend", lambda: _MissingBackend())
    PhysicsService.release_session(sid)
    asyncio.run(
        PhysicsService.ensure_stability(
            sid,
            wait_sec=0.5,
            poll_sec=0.05,
            local_physics=_stable_tensor(),
        )
    )
