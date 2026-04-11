from __future__ import annotations

from app.plugins.chronos.temporal_v2 import append_temporal_trigger_audits
from app.schemas.bazi_metadata import BaziMetadata, FourPillars, StemBranchPair


def test_temporal_trigger_clash_audit() -> None:
    pillars = FourPillars(
        year=StemBranchPair(stem="甲", branch="子"),
        month=StemBranchPair(stem="丙", branch="寅"),
        day=StemBranchPair(stem="戊", branch="辰"),
        hour=StemBranchPair(stem="庚", branch="午"),
    )
    md = BaziMetadata(
        pillars=pillars,
        temporal_context={"liunian_ganzhi": "丙午", "dayun_ganzhi": "甲子", "reference_year": 2026},
    )
    tensor: dict = {"meta": {}, "audit_log": {}}
    rows = append_temporal_trigger_audits(
        physics_tensor=tensor,
        metadata=md,
        branches={"year": "子", "month": "寅", "day": "辰", "hour": "午"},
        settings={"CHRONOS_V2_TEMPORAL_ENABLE": 1.0},
    )
    assert any(r.get("payload", {}).get("type") == "TEMPORAL_TRIGGER" for r in rows)
    kinds = {r.get("payload", {}).get("kind") for r in rows}
    assert "CLASH" in kinds
    meta = tensor.get("meta") or {}
    assert (meta.get("chronos_v2_temporal") or {}).get("triggers")
