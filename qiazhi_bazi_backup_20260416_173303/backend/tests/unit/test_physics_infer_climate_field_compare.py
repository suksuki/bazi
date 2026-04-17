"""V8.3：物理推断 meta 含调候前后场强对比块。"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, FourPillars, StemBranchPair
from app.skills.physics_engine import PhysicsInferenceSkill


def _md() -> BaziMetadata:
    return BaziMetadata(
        pillars=FourPillars(
            year=StemBranchPair(stem="庚", branch="午", energy_value=100),
            month=StemBranchPair(stem="壬", branch="午", energy_value=100),
            day=StemBranchPair(stem="庚", branch="戌", energy_value=100),
            hour=StemBranchPair(stem="壬", branch="午", energy_value=100),
        ),
        conflict_matrix=ConflictMatrix(points=[]),
    )


def test_infer_includes_climate_manifest_field_compare_v1() -> None:
    skill = PhysicsInferenceSkill.instance()
    skill.refresh_cache()
    out = skill.infer(_md(), physics_config={})
    meta = out.get("meta") or {}
    cmp = meta.get("climate_manifest_field_compare_v1")
    assert isinstance(cmp, dict)
    pre = cmp.get("normalized_pre_manifest")
    post = cmp.get("normalized_post_manifest_pre_hard_climate")
    assert isinstance(pre, dict) and isinstance(post, dict)
    assert abs(sum(float(pre[k]) for k in ("wood", "fire", "earth", "metal", "water")) - 1.0) < 0.02
    assert abs(sum(float(post[k]) for k in ("wood", "fire", "earth", "metal", "water")) - 1.0) < 0.02
    assert pre != post
    ctv = meta.get("conflict_topology_v1")
    assert isinstance(ctv, dict)
    assert "aggregate_conflict_linear_factor" in ctv
