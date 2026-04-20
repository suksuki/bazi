from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator


def test_snapshot_frame_contract_stable_smoke() -> None:
    raw_physics = {
        "ten_gods_base_l0": {"伤官": 10.0, "食神": 8.0},
        "ten_gods_runtime": {"伤官": 10.0, "食神": 8.0},
        "four_pillars": {"year": "丁", "month": "乙", "day": "乙", "hour": "乙"},
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "facts": [],
        "total_energy_index": 18.0,
    }

    with patch(
        "v17_rebirth.backend.services.verdict_orchestrator.AutoScanner.ensure_loaded",
        return_value=None,
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.hydrate_v17_physics_tensor",
        return_value=None,
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.six_pillars_tensor_complete",
        return_value=True,
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.PhysicsAdapter.read_deity_scores",
        return_value={"伤官": 10.0, "食神": 8.0},
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.read_runtime_scores",
        return_value={"伤官": 10.0, "食神": 8.0},
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.read_base_scores",
        return_value={"伤官": 5.0, "食神": 4.0},
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.build_narrative_scores",
        return_value={"伤官": 10.0, "食神": 8.0},
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.logic_pd.collect_all_spec_facts_and_record",
        return_value=[],
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.build_decision_arbitration",
        return_value={
            "manual_decisions": [],
            "auto_resolutions": [],
            "llm_arbitration_context": [],
            "auto_arbitration": [],
            "pending_decisions": [],
            "manual_inbox": [],
        },
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.build_decision_batches",
        return_value={"prompt_lines": []},
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.build_snapshot_payload",
        return_value={"snapshot_kind": "physics"},
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.build_claim_conflict_graph",
        return_value={"graph_version": "v17.claim_graph.1", "nodes": [], "edges": [], "conflicts": []},
    ), patch(
        "v17_rebirth.backend.services.snapshot_intel.build_snapshot_plan_trace_index",
        return_value={"contract": "v17.decision.trace_index.v1", "items": []},
    ):
        snap = VerdictOrchestrator().snapshot_frame(raw_physics=raw_physics)

    assert snap["layer"] == "SNAPSHOT"
    assert snap["payload"]["snapshot_kind"] == "physics"


def test_narrator_frames_routes_to_narrative() -> None:
    raw_physics = {
        "ten_gods_base_l0": {"伤官": 10.0, "食神": 8.0},
        "ten_gods_runtime": {"伤官": 10.0, "食神": 8.0},
        "four_pillars": {"year": "丁", "month": "乙", "day": "乙", "hour": "乙"},
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "facts": [],
        "total_energy_index": 18.0,
    }

    async def _fake_frames(*_args, **_kwargs):
        yield {"layer": "NARRATOR", "payload": {"render_text": "ok", "llm_meta": {"elapsed_ms": 1}}}

    with patch(
        "v17_rebirth.backend.services.verdict_orchestrator.hydrate_v17_physics_tensor",
        return_value=None,
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.six_pillars_tensor_complete",
        return_value=True,
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.PhysicsAdapter.read_deity_scores",
        return_value={"伤官": 10.0, "食神": 8.0},
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.build_narrative_scores",
        return_value={"伤官": 10.0, "食神": 8.0},
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.logic_pd.collect_all_spec_facts_and_record",
        return_value=[],
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.build_decision_arbitration",
        return_value={
            "manual_decisions": [],
            "auto_resolutions": [],
            "llm_arbitration_context": [],
            "auto_arbitration": [],
            "pending_decisions": [],
            "manual_inbox": [],
            "suggestions": [],
        },
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.build_decision_batches",
        return_value={"prompt_lines": []},
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.build_fact_fragments",
        return_value=[],
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.get_realtime_pipeline",
        return_value=AsyncMock(),
    ), patch(
        "v17_rebirth.backend.services.verdict_orchestrator.V17LlmBridge",
        return_value=Mock(resolve=Mock(return_value={"model": "test"})),
        ), patch(
            "v17_rebirth.backend.services.verdict_orchestrator.run_narrator_frames",
            _fake_frames,
        ):
        async def _collect() -> list[dict]:
            collected: list[dict] = []
            async for frame in VerdictOrchestrator().narrator_frames(
                raw_physics=raw_physics,
                facts=[],
                will_proxy="stable",
                decisions=[],
                session_id="s1",
                stability_checked=True,
            ):
                collected.append(frame)
            return collected

        collected = asyncio.run(_collect())

    assert len(collected) == 1
    assert collected[0]["payload"]["render_text"] == "ok"
