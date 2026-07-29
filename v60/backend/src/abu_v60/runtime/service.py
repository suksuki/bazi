from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.db import engine
from abu_v60.dream.service import DreamService
from abu_v60.settings import settings
from abu_v60.system_manifest import PRIMARY_WORLD_ID
from abu_v60.world import WorldContinuityEngine, WorldPulse

logger = logging.getLogger(__name__)

# Stable signed bigint namespace for the one canonical V60 world pulse.
WORLD_RUNTIME_ADVISORY_LOCK = 6_000_060_001


@dataclass(frozen=True)
class RuntimePulse:
    lease_acquired: bool
    world: WorldPulse | None
    synchronized_encounters: int


class WorldRuntimeCoordinator:
    """Host-level orchestration around existing World and Dream owners."""

    def __init__(
        self,
        database: Engine,
        *,
        world: WorldContinuityEngine | None = None,
        dream: DreamService | None = None,
    ) -> None:
        self._database = database
        self._world = world or WorldContinuityEngine()
        self._dream = dream or DreamService(database)

    def pulse(self, *, observed_at: datetime | None = None) -> RuntimePulse:
        with self._database.begin() as connection:
            lease_acquired = bool(
                connection.execute(
                    text("SELECT pg_try_advisory_xact_lock(:lock_key)"),
                    {"lock_key": WORLD_RUNTIME_ADVISORY_LOCK},
                ).scalar_one()
            )
            if not lease_acquired:
                return RuntimePulse(
                    lease_acquired=False,
                    world=None,
                    synchronized_encounters=0,
                )
            world_pulse = self._world.pulse(
                connection=connection,
                world_ref=PRIMARY_WORLD_ID,
                observed_at=observed_at,
            )

        synchronized = self._dream.synchronize_settled_world_events()
        return RuntimePulse(
            lease_acquired=True,
            world=world_pulse,
            synchronized_encounters=synchronized,
        )


class WorldRuntimeWorker:
    """Small resilient loop; PostgreSQL remains the clock and lease authority."""

    def __init__(
        self,
        coordinator: WorldRuntimeCoordinator,
        *,
        enabled: bool,
        poll_seconds: float,
    ) -> None:
        self._coordinator = coordinator
        self._enabled = enabled
        self._poll_seconds = poll_seconds
        self._stop_event: asyncio.Event | None = None
        self._task: asyncio.Task[None] | None = None
        self._state_lock = Lock()
        self._state: dict[str, Any] = {
            "status": "DISABLED" if not enabled else "CONFIGURED",
            "enabled": enabled,
            "poll_seconds": poll_seconds,
            "pulse_count": 0,
            "settled_event_count": 0,
            "synchronized_encounter_count": 0,
            "last_tick": None,
            "last_pulse_at": None,
            "last_error": None,
        }

    async def start(self) -> None:
        if not self._enabled or self._task is not None:
            return
        self._stop_event = asyncio.Event()
        with self._state_lock:
            self._state["status"] = "STARTING"
        self._task = asyncio.create_task(
            self._run(),
            name="v60-world-runtime",
        )

    async def stop(self) -> None:
        if self._task is None or self._stop_event is None:
            return
        self._stop_event.set()
        await self._task
        self._task = None
        self._stop_event = None
        with self._state_lock:
            self._state["status"] = "STOPPED"

    def status(self) -> dict[str, Any]:
        with self._state_lock:
            return dict(self._state)

    async def _run(self) -> None:
        assert self._stop_event is not None
        while not self._stop_event.is_set():
            try:
                pulse = await asyncio.to_thread(self._coordinator.pulse)
                now = datetime.now(UTC).isoformat()
                with self._state_lock:
                    self._state["status"] = "READY" if pulse.lease_acquired else "STANDBY"
                    self._state["pulse_count"] += 1
                    self._state["last_pulse_at"] = now
                    self._state["last_error"] = None
                    if pulse.world is not None:
                        self._state["last_tick"] = pulse.world.current_tick
                        self._state["settled_event_count"] += len(pulse.world.settled_event_refs)
                    self._state["synchronized_encounter_count"] += pulse.synchronized_encounters
            except Exception as exc:  # The worker must survive a transient DB outage.
                logger.exception("V60 world runtime pulse failed")
                with self._state_lock:
                    self._state["status"] = "DEGRADED"
                    self._state["last_pulse_at"] = datetime.now(UTC).isoformat()
                    self._state["last_error"] = type(exc).__name__

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._poll_seconds,
                )
            except TimeoutError:
                pass


world_runtime_worker = WorldRuntimeWorker(
    WorldRuntimeCoordinator(engine),
    enabled=settings.world_runtime_enabled,
    poll_seconds=settings.world_runtime_poll_seconds,
)
