from __future__ import annotations

import asyncio

from v17_rebirth.backend.services import narrative_flow, narrative_intel, snapshot_intel


def test_narrative_intel_build_fact_fragments_and_sorted_rows() -> None:
    facts = [
        {"fact": "低", "weight": 0.2},
        {"fact": "高", "weight": 0.9},
        {"fact": "中", "weight": 0.5},
    ]
    rows = narrative_intel.sorted_fact_rows(facts)
    assert [r["fact"] for r in rows[:2]] == ["高", "中"]

    deity_scores = {"伤官": 12.0, "正官": 30.0, "比肩": 8.0}
    fragments = narrative_intel.build_fact_fragments(deity_scores, facts, total_energy_index=123.4)
    assert any("Total Energy Index=123.40" in frag for frag in fragments)
    assert fragments[0].startswith("以下提供的 160 条事实")
    assert "正官偏强" in fragments[2]


def test_build_snapshot_payload_does_not_dupe_auto_decisions_and_has_gate() -> None:
    raw = {
        "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊辰",
        "flow_pillar": "己巳",
        "meta": {
            "plugin_execution_status": [{"id": "x"}],
            "plugin_claims": [{"claim_id": "c1", "label": "A"}],
            "god_ring_authority": {
                "use_gods": ["正官", "正印"],
                "taboo_gods": ["伤官", "劫财"],
                "source": "classical.ziping.god_ring_resolver.v1",
                "confidence": 0.82,
                "core_paths_preview": [{"target_god": "正官", "path_type": "sanhe", "net_effect": 0.66}],
                "core_graph_meta": {"positive_targets": {"正官": 0.88}},
            },
        },
    }
    raw_decision = {"id": "d1", "source": "p", "label": "重复", "target_god": "伤官"}
    arbitration = {
        "manual_decisions": [raw_decision],
        "auto_resolutions": [],
        "llm_arbitration_context": [],
    }
    payload = snapshot_intel.build_snapshot_payload(
        raw_physics=raw,
        ranked=[("正官", 18.0), ("伤官", 12.0)],
        scores={"正官": 18.0, "伤官": 12.0},
        base_scores={"正官": 10.0, "伤官": 10.0},
        narrative_scores={"正官": 20.0, "伤官": 11.0},
        tension=8.0,
        total_energy_index=70.0,
        arbitration=arbitration,
        decision_batches={"all": [{"id": "b1"}], "prompt_lines": ["p1"]},
        plugin_rows=[],
        plugin_hits=[],
        plugin_facts=[],
        sorted_fact_rows=[],
        claim_conflict_graph={"summary": {"x": 1}},
        causal_anchor="local_memory",
        trace_index_builder=lambda _pt: {"contract": "v17.decision.trace_index.v1", "plan_count": 0, "items": []},
    )

    assert payload["snapshot_contract"] == "v17.21_full_physics"
    assert "physics_report" in payload
    assert len(payload["all_decisions"]) == 1
    assert payload["plugins"]["claims"][0]["claim_id"] == "c1"
    assert payload["pillars"]["four_pillars"]["year"] == "甲子"
    assert payload["god_rings"]["god_of_use"] == ["正官", "正印"]
    assert payload["god_rings"]["god_of_taboo"] == ["伤官", "劫财"]
    assert payload["god_rings"]["display_mode"] == "authority"
    assert payload["god_rings"]["label_of_use"] == "USE"
    assert payload["god_rings"]["confidence"] == 0.82
    assert payload["god_rings"]["core_paths_preview"][0]["target_god"] == "正官"
    assert payload["god_rings"]["core_graph_meta"]["positive_targets"]["正官"] == 0.88


class _FakePipeline:
    def __init__(self) -> None:
        self.status_events = 0

    def compute_llm_audit_preview(self, **_kwargs) -> dict:
        return {
            "llm_request_messages": [1, 2, 3],
            "full_prompt_trace": {"raw_prompt": True},
            "llm_system_prompt": "system",
            "llm_user_prompt": "user",
        }

    async def run(
        self,
        *,
        on_llm_partial,
        status_callback,
        **_kwargs,
    ) -> dict:
        await on_llm_partial("[INTENSIFY:七杀]")
        if status_callback is not None:
            await status_callback({"status": "streaming", "chunk": "前文"})
            await status_callback({"status": "dispatched", "payload": {"messages": [1]}})
            await status_callback({"status": "connected", "latency": 15})
        await on_llm_partial("尾")
        return {
            "payload": {
                "render_text": "最终判词",
                "llm_meta": {"engine_state": "ok"},
                "source_facts": [],
            }
        }


class _EmptyRenderPipeline:
    def compute_llm_audit_preview(self, **_kwargs) -> dict:
        return {
            "llm_request_messages": [],
            "llm_system_prompt": "system",
            "llm_user_prompt": "user",
        }

    async def run(
        self,
        *,
        on_llm_partial,
        status_callback=None,
        **_kwargs,
    ) -> dict:
        await on_llm_partial("前")
        await on_llm_partial("文")
        return {"payload": {"render_text": "   ", "llm_meta": {"error": "timeout", "error_id": "T1", "engine_state": "empty"}}}


class _ErrorPipeline:
    def compute_llm_audit_preview(self, **_kwargs) -> dict:
        return {}

    async def run(
        self,
        *,
        on_llm_partial,
        **_kwargs,
    ) -> dict:
        await on_llm_partial("触发")
        raise RuntimeError("pipeline-broken")


def test_narrator_flow_emits_frames_and_calls_feedback_callback() -> None:
    pipeline = _FakePipeline()
    feedback_events: list[tuple[str, str]] = []

    async def _on_feedback(tag: str, el: str, _reason: str) -> None:
        feedback_events.append((tag, el))

    async def _collect() -> list[dict]:
        rows: list[dict] = []
        async for frame in narrative_flow.run_narrator_frames(
            raw_physics={"four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}},
            fragments=["片段A", "片段B"],
            narrative_scores={"伤官": 10.0},
            decision_batches={"all": [], "prompt_lines": []},
            will_proxy="stable",
            god_of_use=["伤官"],
            god_of_taboo=["正官"],
            decision_anchor="",
            user_message="给你一句",
            action_signal=False,
            role_style="weaver",
            session_id="sid",
            causal_anchor="redis_sync",
            action_queue=None,
            on_feedback_proposal=_on_feedback,
            model_hint="mock-llm",
            pipeline=pipeline,
        ):
            rows.append(frame)
        return rows

    rows = asyncio.run(_collect())
    assert rows
    assert rows[0]["layer"] == "SNAPSHOT"
    assert any(r["layer"] == "NARRATOR" for r in rows)
    assert feedback_events == [("INTENSIFY", "七杀")]


def test_narrator_flow_returns_empty_render_fallback_hint() -> None:
    pipeline = _EmptyRenderPipeline()
    async def _collect() -> list[dict]:
        frames: list[dict] = []
        async for frame in narrative_flow.run_narrator_frames(
            raw_physics={"four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}},
            fragments=["a"],
            narrative_scores={"伤官": 10.0},
            decision_batches={"all": [], "prompt_lines": []},
            will_proxy="stable",
            god_of_use=["伤官"],
            god_of_taboo=["正官"],
            decision_anchor="",
            user_message="给你一句",
            action_signal=False,
            role_style="weaver",
            session_id="sid",
            causal_anchor="redis_sync",
            action_queue=None,
            model_hint="mock-llm",
            pipeline=pipeline,
        ):
            frames.append(frame)
        return frames

    frames = asyncio.run(_collect())
    assert frames
    fallbacks = [x for x in frames if x["layer"] == "NARRATOR"]
    assert len(fallbacks) >= 1
    assert "叙事织机未产出可见正文" in str(fallbacks[-1]["payload"]["render_text"])
    assert fallbacks[-1]["payload"]["llm_meta"].get("ok") is False


def test_narrator_flow_rethrows_pipeline_error() -> None:
    pipeline = _ErrorPipeline()
    async def _collect() -> None:
        async for _frame in narrative_flow.run_narrator_frames(
            raw_physics={"four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}},
            fragments=["a"],
            narrative_scores={"伤官": 10.0},
            decision_batches={"all": [], "prompt_lines": []},
            will_proxy="stable",
            god_of_use=["伤官"],
            god_of_taboo=["正官"],
            decision_anchor="",
            user_message="给你一句",
            action_signal=False,
            role_style="weaver",
            session_id="sid",
            causal_anchor="redis_sync",
            action_queue=None,
            model_hint="mock-llm",
            pipeline=pipeline,
        ):
            pass

    try:
        asyncio.run(_collect())
    except RuntimeError as err:
        assert str(err) == "pipeline-broken"
    else:
        raise AssertionError("expected runtime error")


def test_build_snapshot_plan_trace_index() -> None:
    raw_physics = {
        "decision_brain_state": {
            "plan_queue": [
                {
                    "plan_id": "p1",
                    "anchor": "anchor-a",
                    "status": "COMMITTED",
                    "routing": "auto",
                    "updated_at": "2026-04-20T00:00:00Z",
                    "decision_ids": ["d1", "d2"],
                    "batch_ids": ["b1"],
                    "impact_summary": {"pos": 1},
                }
            ]
        }
    }

    idx = snapshot_intel.build_snapshot_plan_trace_index(raw_physics)
    assert idx["plan_count"] == 1
    assert idx["items"][0]["plan_id"] == "p1"
    assert idx["items"][0]["decision_count"] == 2
