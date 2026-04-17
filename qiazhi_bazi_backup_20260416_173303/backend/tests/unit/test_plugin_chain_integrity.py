"""V6.9：全量中枢路径须触发 UniversalPatternEngine.evaluate，且 manifest 指纹与磁盘一致。"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

from app.logic.patterns.engine import UniversalPatternEngine, get_pattern_manifest_path
from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, ConflictPoint, FlowState, FourPillars, StemBranchPair
from app.services.orchestrator_service import run_internal_loop
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
            "audit_log": {"param_version_id": "plugin-chain-test"},
            "by_pillar": {yb: {"raw_energy": 1.0}},
        }


def _pillars() -> FourPillars:
    return FourPillars(
        year=StemBranchPair(stem="甲", branch="子"),
        month=StemBranchPair(stem="丙", branch="寅"),
        day=StemBranchPair(stem="戊", branch="辰"),
        hour=StemBranchPair(stem="庚", branch="午"),
    )


def test_full_internal_loop_invokes_evaluate_and_manifest_sha_matches_disk() -> None:
    mp = get_pattern_manifest_path()
    assert isinstance(mp, Path) and mp.is_file(), "pattern manifest path must be readable"
    disk_sha = hashlib.sha256(mp.read_bytes()).hexdigest()

    calls = {"n": 0}
    orig_eval = UniversalPatternEngine.evaluate

    def _counting_evaluate(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        calls["n"] += 1
        return orig_eval(self, *args, **kwargs)

    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(
            points=[ConflictPoint(kind="clash", positions=["year_branch", "day_branch"], detail="子午冲")]
        ),
        flow_state=FlowState.UNKNOWN,
    )

    with patch.object(UniversalPatternEngine, "evaluate", _counting_evaluate):
        with patch.object(physics_engine_module.PhysicsInferenceSkill, "instance", return_value=_FakePhysicsSkill()):
            out = run_internal_loop(
                metadata_obj=md,
                enabled_plugins=["classical.pattern_detector.v2"],
                blind_school_features={},
                physics_config={},
            )

    assert calls["n"] >= 1, "UniversalPatternEngine.evaluate must run at least once in L2 path"
    pt = out.get("physics_tensor") or {}
    assert isinstance(pt, dict)
    meta = pt.get("meta") or {}
    assert isinstance(meta, dict)
    assert meta.get("pattern_manifest_file_sha256") == disk_sha
    assert meta.get("pattern_thresholds_engine") == "universal_manifest_v1"
    cfc = meta.get("climate_field_correction_v1")
    assert isinstance(cfc, dict) and cfc.get("month_branch") == "午"
    assert isinstance(cfc.get("element_mods"), dict) and float(cfc["element_mods"].get("fire", 0.0)) > 1.0
    rows = meta.get("pattern_thresholds")
    assert isinstance(rows, list) and len(rows) >= 1
    assert all(str(r.get("engine_v") or "") == "MANIFEST_V5.8_STRICT" for r in rows if isinstance(r, dict))
