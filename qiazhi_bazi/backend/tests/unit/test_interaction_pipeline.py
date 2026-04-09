from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, ConflictPoint, FourPillars, StemBranchPair
from app.services.helpers.interaction_pipeline import evaluate_interactions
from app.core.rules.junction import EnergyVaultStatus


def _pillars_dingsi_yisi() -> FourPillars:
    return FourPillars(
        year=StemBranchPair(stem="丁", branch="巳"),
        month=StemBranchPair(stem="乙", branch="巳"),
        day=StemBranchPair(stem="乙", branch="酉"),
        hour=StemBranchPair(stem="辛", branch="丑"),
    )


def test_pipeline_sanhe_aggregated_lab01_shape():
    """巳酉丑全：composite 聚合态 + 与 Lab-01 同构的 cluster_abs 量级。"""
    pillars = _pillars_dingsi_yisi()
    meta = BaziMetadata(pillars=pillars, conflict_matrix=ConflictMatrix(points=[]))
    tensor = {
        "by_pillar": {
            "year": {"raw_energy": 50.0},
            "month": {"raw_energy": 50.0},
            "day": {"raw_energy": 60.0},
            "hour": {"raw_energy": 54.55},
        }
    }
    params = {
        "L1_PUNISH_FRICTION_SANXING": 0.2,
        "L1_PUNISH_FRICTION_ZIXING": 0.15,
        "L1_CLASH_INTENSITY": 1.0,
        "L1_COMBINE_LOCK_RATIO": 0.3,
        "L1_PIERCE_RATIO": 0.45,
    }
    evaluate_interactions(physics_tensor=tensor, metadata=meta, interaction_params=params, physics_config={})
    comp = tensor.get("composite_field_impact") or {}
    clusters = comp.get("sanhe_clusters") or []
    assert len(clusters) == 1
    assert clusters[0]["energy_vault_status"] == EnergyVaultStatus.AGGREGATED.value
    assert abs(clusters[0]["cluster_abs"] - 214.55) < 0.01
    # 乙木墓在未；此盘无未支，不应产生墓库插件步骤
    steps = (tensor.get("l1_atomic_pipeline") or {}).get("steps") or []
    assert not any(s.get("plugin") == "base.grave" for s in steps)


def test_pipeline_grave_locked_when_tomb_branch_present():
    pillars = FourPillars(
        year=StemBranchPair(stem="甲", branch="寅"),
        month=StemBranchPair(stem="甲", branch="卯"),
        day=StemBranchPair(stem="乙", branch="亥"),
        hour=StemBranchPair(stem="甲", branch="未"),
    )
    meta = BaziMetadata(pillars=pillars, conflict_matrix=ConflictMatrix(points=[]))
    tensor = {
        "by_pillar": {
            "year": {"raw_energy": 10.0},
            "month": {"raw_energy": 10.0},
            "day": {"raw_energy": 20.0},
            "hour": {"raw_energy": 80.0},
        }
    }
    evaluate_interactions(physics_tensor=tensor, metadata=meta, interaction_params={}, physics_config={"GRAVE_BURST_MULTIPLIER": 1.3})
    steps = (tensor.get("l1_atomic_pipeline") or {}).get("steps") or []
    grave_steps = [s for s in steps if s.get("plugin") == "base.grave"]
    assert len(grave_steps) == 1
    assert grave_steps[0]["delta"]["energy_vault_status"] == EnergyVaultStatus.LOCKED.value


def test_pipeline_clash_step():
    pillars = FourPillars(
        year=StemBranchPair(stem="甲", branch="子"),
        month=StemBranchPair(stem="甲", branch="午"),
        day=StemBranchPair(stem="甲", branch="寅"),
        hour=StemBranchPair(stem="甲", branch="卯"),
    )
    meta = BaziMetadata(
        pillars=pillars,
        conflict_matrix=ConflictMatrix(
            points=[
                ConflictPoint(kind="clash", positions=["year_branch", "month_branch"], detail="子午冲"),
            ]
        ),
    )
    tensor = {
        "by_pillar": {
            "year": {"raw_energy": 40.0},
            "month": {"raw_energy": 40.0},
            "day": {"raw_energy": 30.0},
            "hour": {"raw_energy": 30.0},
        }
    }
    evaluate_interactions(physics_tensor=tensor, metadata=meta, interaction_params={"L1_CLASH_INTENSITY": 1.0}, physics_config={})
    steps = (tensor.get("l1_atomic_pipeline") or {}).get("steps") or []
    clash = [s for s in steps if s.get("plugin") == "base.clash"]
    assert len(clash) == 1
    assert clash[0]["delta"]["effect"] == "clash"
