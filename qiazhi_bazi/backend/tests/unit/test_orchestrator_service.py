"""OrchestratorService：无 LLM 内部闭环单测。"""
from __future__ import annotations

import asyncio
import os

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

from unittest.mock import patch

from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, ConflictPoint, FlowState, FourPillars, StemBranchPair
from app.services.orchestrator_service import OrchestratorService, run_full_cycle, run_internal_loop
from app.skills import physics_engine as physics_engine_module


class _FakePhysicsSkill:
    def consume(self, payload):
        return payload

    def get_interaction_params(self):
        from app.skills.physics_rules import DEFAULT_INTERACTION_PARAMS

        return dict(DEFAULT_INTERACTION_PARAMS)

    def produce(self, consumed):
        md = consumed.get("metadata")
        pillars = md.pillars if hasattr(md, "pillars") else None
        yb = pillars.year.branch if pillars else "子"
        return {
            "normalized": {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2},
            "deity_scores": {"比肩": 1.0},
            "meta": {"params": {}},
            "audit_log": {"param_version_id": "orch-test"},
            "by_pillar": {yb: {"raw_energy": 1.0}},
        }


def _pillars() -> FourPillars:
    return FourPillars(
        year=StemBranchPair(stem="甲", branch="子"),
        month=StemBranchPair(stem="丙", branch="寅"),
        day=StemBranchPair(stem="戊", branch="辰"),
        hour=StemBranchPair(stem="庚", branch="午"),
    )


def test_run_internal_loop_no_llm_returns_physics_and_vf_bundle():
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(
            points=[ConflictPoint(kind="clash", positions=["year_branch", "day_branch"], detail="子午冲")]
        ),
        flow_state=FlowState.UNKNOWN,
    )
    with patch.object(physics_engine_module.PhysicsInferenceSkill, "instance", return_value=_FakePhysicsSkill()):
        out = run_internal_loop(
            metadata_obj=md,
            enabled_plugins=[],
            blind_school_features={},
            physics_config={},
            session_id=None,
            dayun=None,
            liunian=None,
        )
    assert out["metadata"].pillars == md.pillars
    pt = out["physics_tensor"]
    assert isinstance(pt, dict)
    assert "normalized" in pt
    assert isinstance(out["plugin_outputs"], dict)
    meta = pt.get("meta")
    assert isinstance(meta, dict)
    assert isinstance(meta.get("semantic_label_bundle_v1"), (dict, type(None)))
    assert isinstance(out.get("verified_fact_lines"), list)
    assert "verdict_skeleton" in out
    assert "### 核心气象 (物理预判)" in (out.get("verdict_skeleton") or "")
    assert "### 风险预警 (意志对垒)" in (out.get("verdict_skeleton") or "")
    assert out["metadata"].verdict_anchor_layer.verdict_skeleton == out.get("verdict_skeleton")


def test_run_internal_loop_emit_records_physics_vf_and_audit():
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(
            points=[ConflictPoint(kind="clash", positions=["year_branch", "day_branch"], detail="子午冲")]
        ),
        flow_state=FlowState.UNKNOWN,
    )
    events: list[tuple[str, object]] = []

    def emit(ev: str, data: object) -> None:
        events.append((ev, data))

    with patch.object(physics_engine_module.PhysicsInferenceSkill, "instance", return_value=_FakePhysicsSkill()):
        run_internal_loop(
            metadata_obj=md,
            enabled_plugins=["classical.pattern_detector.v2"],
            blind_school_features={},
            physics_config={},
            emit=emit,
        )
    kinds = [e[0] for e in events]
    assert kinds.count("physics_update") >= 1
    assert "vf_discovered" in kinds
    phys_updates = [d for ev, d in events if ev == "physics_update" and isinstance(d, dict)]
    assert phys_updates, "expected physics_update payloads"
    phys_first = phys_updates[0]
    assert "deity_scores" in phys_first
    assert isinstance(phys_first.get("pattern_thresholds"), list)
    assert phys_first.get("pattern_thresholds_status") == "EMPTY_NO_DATA"
    phys_last = phys_updates[-1]
    assert isinstance(phys_last.get("pattern_thresholds"), list)
    assert phys_last.get("pattern_thresholds_status") == "OK"
    rows = phys_last["pattern_thresholds"]
    assert rows, "with L2 strict rows, pattern_thresholds must be non-empty"
    assert all(
        isinstance(x, dict)
        and str(x.get("engine_v") or "") == "MANIFEST_V5.8_STRICT"
        and "name" in x
        and "progress" in x
        and "stability" in x
        for x in rows
    )


class _FakePhysicsSkillFull:
    """含完整十神与月令，供 L2 manifest 写出 strict 行（V8.2 格局常驻）。"""

    def consume(self, payload):
        return payload

    def get_interaction_params(self):
        from app.skills.physics_rules import DEFAULT_INTERACTION_PARAMS

        return dict(DEFAULT_INTERACTION_PARAMS)

    def produce(self, consumed):
        md = consumed.get("metadata")
        pillars = md.pillars if hasattr(md, "pillars") else None
        yb = pillars.year.branch if pillars else "子"
        return {
            "normalized": {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2},
            "deity_scores": {
                "正印": 4.0,
                "偏印": 4.0,
                "食神": 30.0,
                "伤官": 30.0,
                "比肩": 6.0,
                "劫财": 6.0,
                "偏财": 6.0,
                "正财": 6.0,
                "七杀": 4.0,
                "正官": 4.0,
            },
            "meta": {"params": {}, "month_branch": "午", "active_structures": []},
            "audit_log": {"param_version_id": "orch-v82"},
            "by_pillar": {yb: {"raw_energy": 1.0}},
        }


def test_run_internal_loop_pattern_l2_runs_when_enabled_list_omits_pattern_id_v82():
    """V8.2：Registry 白名单强制 ``classical.pattern_detector.v2``；仅盲派在名单时仍须写出 manifest 水位。"""
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(
            points=[ConflictPoint(kind="clash", positions=["year_branch", "day_branch"], detail="子午冲")]
        ),
        flow_state=FlowState.UNKNOWN,
    )
    events: list[tuple[str, object]] = []

    def emit(ev: str, data: object) -> None:
        events.append((ev, data))

    with patch.object(physics_engine_module.PhysicsInferenceSkill, "instance", return_value=_FakePhysicsSkillFull()):
        out = run_internal_loop(
            metadata_obj=md,
            enabled_plugins=["classical.blind_school.v1"],
            blind_school_features={},
            physics_config={},
            emit=emit,
        )
    meta = (out.get("physics_tensor") or {}).get("meta") or {}
    assert isinstance(meta, dict)
    assert meta.get("pattern_thresholds_engine") == "universal_manifest_v1"
    assert meta.get("pattern_thresholds_status") == "OK"
    rows = meta.get("pattern_thresholds")
    assert isinstance(rows, list) and len(rows) >= 1
    po = out.get("plugin_outputs") or {}
    assert "classical.pattern_detector.v2" in po
    phys_updates = [d for ev, d in events if ev == "physics_update" and isinstance(d, dict)]
    assert phys_updates
    assert phys_updates[-1].get("pattern_thresholds_status") == "OK"
    assert len(phys_updates[-1].get("pattern_thresholds") or []) >= 1


def test_run_internal_loop_structural_preview_prepends_vf_line():
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.UNKNOWN,
    )
    events: list[tuple[str, object]] = []

    def emit(ev: str, data: object) -> None:
        events.append((ev, data))

    with patch.object(physics_engine_module.PhysicsInferenceSkill, "instance", return_value=_FakePhysicsSkill()):
        out = run_internal_loop(
            metadata_obj=md,
            enabled_plugins=[],
            blind_school_features={},
            physics_config={},
            emit=emit,
            is_preview=True,
            structural_preview={"kind": "L1_STRUCTURE", "label": "测试三合局", "card_id": "inbox-sanhe-test"},
        )
    vf = [e for e in events if e[0] == "vf_discovered"]
    assert vf, "expected vf_discovered events"
    first = vf[0][1]
    assert isinstance(first, dict)
    assert str(first.get("line") or "").startswith("[PREVIEW]")
    assert "测试三合局" in str(first.get("line") or "")
    assert out.get("is_preview") is True
    assert isinstance(out.get("preview_pattern_alert"), str)


def test_run_internal_loop_is_preview_skips_narrative_refresh_flag():
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.UNKNOWN,
    )
    with patch.object(physics_engine_module.PhysicsInferenceSkill, "instance", return_value=_FakePhysicsSkill()):
        out = run_internal_loop(
            metadata_obj=md,
            enabled_plugins=[],
            blind_school_features={},
            physics_config={},
            is_preview=True,
        )
    assert out.get("is_preview") is True
    assert out.get("requires_narrative_refresh") is False


def test_run_full_cycle_async_generator_ends_with_complete():
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.UNKNOWN,
    )

    async def collect() -> list:
        out = []
        async for item in run_full_cycle(
            metadata_obj=md,
            enabled_plugins=[],
            blind_school_features={},
            physics_config={},
        ):
            out.append(item)
        return out

    items = asyncio.run(collect())
    assert items[-1]["event"] == "complete"
    assert "metadata" in items[-1]["data"]
    assert "physics_tensor" in items[-1]["data"]


def test_orchestrator_service_class_alias():
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.UNKNOWN,
    )
    with patch.object(physics_engine_module.PhysicsInferenceSkill, "instance", return_value=_FakePhysicsSkill()):
        a = OrchestratorService.run_internal_loop(
            metadata_obj=md,
            enabled_plugins=[],
            blind_school_features={},
            physics_config={},
        )
        b = run_internal_loop(
            metadata_obj=md,
            enabled_plugins=[],
            blind_school_features={},
            physics_config={},
        )
    assert a["physics_tensor"].keys() == b["physics_tensor"].keys()
