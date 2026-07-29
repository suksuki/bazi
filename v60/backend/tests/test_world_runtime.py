from __future__ import annotations

import asyncio

from abu_v60.runtime import RuntimePulse, WorldRuntimeWorker
from abu_v60.world import WorldPulse


class _Coordinator:
    def pulse(self) -> RuntimePulse:
        return RuntimePulse(
            lease_acquired=True,
            world=WorldPulse(
                world_ref="world:test",
                previous_tick=4,
                current_tick=5,
                epoch=2,
                settled_event_refs=("event:due",),
            ),
            synchronized_encounters=1,
        )


def test_world_runtime_worker_pulses_and_stops_cleanly() -> None:
    async def scenario() -> dict[str, object]:
        worker = WorldRuntimeWorker(
            _Coordinator(),  # type: ignore[arg-type]
            enabled=True,
            poll_seconds=0.01,
        )
        await worker.start()
        for _ in range(50):
            if worker.status()["pulse_count"]:
                break
            await asyncio.sleep(0.002)
        await worker.stop()
        return worker.status()

    status = asyncio.run(scenario())

    assert status["status"] == "STOPPED"
    assert status["pulse_count"] >= 1
    assert status["last_tick"] == 5
    assert status["settled_event_count"] >= 1
    assert status["synchronized_encounter_count"] >= 1
    assert status["last_error"] is None


def test_disabled_world_runtime_never_starts() -> None:
    async def scenario() -> dict[str, object]:
        worker = WorldRuntimeWorker(
            _Coordinator(),  # type: ignore[arg-type]
            enabled=False,
            poll_seconds=1,
        )
        await worker.start()
        await worker.stop()
        return worker.status()

    status = asyncio.run(scenario())

    assert status["status"] == "DISABLED"
    assert status["pulse_count"] == 0
