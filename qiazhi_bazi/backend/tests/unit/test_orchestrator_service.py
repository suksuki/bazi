"""OrchestratorService：无 LLM 内部闭环单测。"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

from unittest.mock import patch

from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, ConflictPoint, FlowState, FourPillars, StemBranchPair
from app.services.orchestrator_service import OrchestratorService, run_internal_loop
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
