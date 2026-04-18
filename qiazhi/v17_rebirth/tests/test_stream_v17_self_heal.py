from __future__ import annotations

import asyncio
import json

from v17_rebirth.backend.api import stream_v17
from v17_rebirth.backend.services import physics_service
from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator


class _FakeBackend:
    def __init__(self) -> None:
        self.physics: dict[str, dict] = {}

    async def get_physics(self, session_id: str) -> dict:
        return dict(self.physics.get(session_id) or {})

    async def set_physics(self, session_id: str, tensor: dict) -> bool:
        self.physics[session_id] = dict(tensor)
        return True


def test_self_heal_physics_if_missing_rebuilds_backend_tensor(monkeypatch) -> None:
    backend = _FakeBackend()

    async def _fake_hydrate(pl: dict) -> None:
        pl["meta"] = {"v17_physics_stable": True}

    monkeypatch.setattr(stream_v17, "get_state_backend", lambda: backend)
    monkeypatch.setattr(physics_service, "get_state_backend", lambda: backend)
    monkeypatch.setattr(
        stream_v17,
        "_run_v17_physics_core",
        lambda **_: {
            "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊辰",
            "flow_pillar": "己巳",
            "flow_year": 2026,
            "gender": "female",
            "birth_time": "2026-04-18T00:00:00",
        },
    )
    monkeypatch.setattr(stream_v17, "_hydrate_physics_atomically", _fake_hydrate)

    payload = {"session_id": "heal-case", "facts": ["before-heal"]}
    healed = asyncio.run(stream_v17._self_heal_physics_if_missing("heal-case", payload))

    assert healed is True
    assert backend.physics["heal-case"]["four_pillars"]["year"] == "甲子"
    assert payload["meta"]["v17_physics_stable"] is True


def test_snapshot_frame_marks_local_memory_anchor(monkeypatch) -> None:
    monkeypatch.setattr("v17_rebirth.backend.services.verdict_orchestrator.AutoScanner.ensure_loaded", lambda: None)
    monkeypatch.setattr(
        "v17_rebirth.backend.services.verdict_orchestrator.hydrate_v17_physics_tensor",
        lambda payload: payload.setdefault("meta", {"v17_physics_stable": True}),
    )
    monkeypatch.setattr(
        "v17_rebirth.backend.services.verdict_orchestrator.logic_pd.collect_all_spec_facts_and_record",
        lambda _pt: [],
    )

    class _FakeAdapter:
        def __init__(self, **_kwargs) -> None:
            pass

        def read_deity_scores(self, _payload: dict) -> dict:
            return {"正官": 42.0, "食神": 18.0, "比肩": 8.0}

    monkeypatch.setattr("v17_rebirth.backend.services.verdict_orchestrator.PhysicsAdapter", _FakeAdapter)

    frame = VerdictOrchestrator().snapshot_frame(
        raw_physics={
            "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
            "luck_pillar": "戊辰",
            "flow_pillar": "己巳",
            "flow_year": 2026,
            "facts": ["即时显影"],
        },
        session_id="unused-session",
        causal_anchor="local_memory",
    )

    assert frame["payload"]["causal_anchor"] == "local_memory"
    assert frame["payload"]["four_pillars"]["year"] == "甲子"
    assert frame["payload"]["physics_fingerprint"]


def test_stream_frames_emits_terminal_error_frame_on_unhandled_narrator_exception(monkeypatch) -> None:
    class _FakeBackend:
        async def ping(self) -> bool:
            return True

        async def set_physics(self, _session_id: str, _tensor: dict) -> bool:
            return True

        async def get_physics(self, _session_id: str) -> dict:
            return {}

        async def delete_physics(self, _session_id: str) -> None:
            return None

        async def get_physics_keys(self, _session_id: str) -> list[str]:
            return []

        def subscribe_actions(self, _session_id: str):
            class _Ctx:
                async def __aenter__(self):
                    return asyncio.Queue()

                async def __aexit__(self, exc_type, exc, tb):
                    return False

            return _Ctx()

    monkeypatch.setattr(stream_v17, "get_state_backend", lambda: _FakeBackend())
    monkeypatch.setattr(stream_v17, "_hydrate_physics_atomically", lambda _pl: asyncio.sleep(0))
    monkeypatch.setattr(stream_v17.PhysicsService, "prime_local_tensor", lambda *_a, **_k: None)
    monkeypatch.setattr(stream_v17.PhysicsService, "abind_session_tensor", lambda *_a, **_k: asyncio.sleep(0))
    monkeypatch.setattr(stream_v17.PhysicsService, "ensure_stability", lambda *_a, **_k: asyncio.sleep(0))
    monkeypatch.setattr(VerdictOrchestrator, "assert_six_pillars_physics", lambda *_a, **_k: None)
    monkeypatch.setattr(
        VerdictOrchestrator,
        "snapshot_frame",
        lambda *_a, **_k: {"timestamp": "t0", "layer": "SNAPSHOT", "payload": {"snapshot_kind": "physics"}},
    )

    async def _boom(*_args, **_kwargs):
        yield {"timestamp": "t1", "layer": "SNAPSHOT", "payload": {"snapshot_kind": "llm_audit_dispatch"}}
        raise RuntimeError("boom")

    monkeypatch.setattr(VerdictOrchestrator, "narrator_frames", _boom)

    async def _collect() -> list[dict]:
        rows: list[dict] = []
        async for chunk in stream_v17._stream_frames(
            will_proxy="stable",
            payload={
                "session_id": "sid",
                "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
                "luck_pillar": "戊辰",
                "flow_pillar": "己巳",
                "flow_year": 2026,
            },
        ):
            rows.append(json.loads(chunk.decode("utf-8").strip()))
        return rows

    frames = asyncio.run(_collect())
    final = frames[-1]
    assert final["layer"] == "NARRATOR"
    assert final["payload"]["llm_meta"]["engine_state"] == "orchestrator_runtime_error"
    assert "llm_audit_dispatch" in final["payload"]["llm_meta"]["step_position"]
