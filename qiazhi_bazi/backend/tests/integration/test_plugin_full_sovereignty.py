"""
0.17 因果闭环集成测试：三合协议审计 + 枢纽防御多重叠加 + 从格主权纠偏持久契约。

依赖 `DATABASE_URL` 指向可连 PostgreSQL；持久化用例在库不可写时自动 skip。
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List

import pytest
from sqlalchemy.exc import OperationalError

from app.api.contracts import AnalyzeClashRequest, PhysicsConfig
from app.core.config.physics_settings import DEFAULT_PHYSICS_SETTINGS
from app.schemas.bazi_metadata import FourPillars, StemBranchPair
from app.services.analysis_service import analyze_clash_flow

FULL_STACK_PLUGINS = [
    "base.chronos",
    "classical.blind_school.v1",
    "classical.wangshuai.v1",
]


def _pillars(
    ys: str,
    yb: str,
    ms: str,
    mb: str,
    ds: str,
    db: str,
    hs: str,
    hb: str,
) -> FourPillars:
    return FourPillars(
        year=StemBranchPair(stem=ys, branch=yb),
        month=StemBranchPair(stem=ms, branch=mb),
        day=StemBranchPair(stem=ds, branch=db),
        hour=StemBranchPair(stem=hs, branch=hb),
    )


def _require_database_url() -> None:
    if not (os.getenv("DATABASE_URL") or "").strip():
        pytest.skip("需要 DATABASE_URL")


def _sanhe_skip_rows(audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = audit.get("sanhe_protocol_audits")
    if not isinstance(rows, list):
        return []
    return [x for x in rows if isinstance(x, dict) and str(x.get("status") or "") == "SKIPPED_BY_PROTOCOL"]


@pytest.mark.integration
def test_scene_1_sanhe_incomplete_triad_emits_skipped_by_protocol_in_audit_log() -> None:
    """旺支门控开启：申子辰缺「子」时，audit_log 须含 SKIPPED_BY_PROTOCOL（INCOMPLETE_TRIAD）。"""
    _require_database_url()

    async def _body() -> None:
        complete = _pillars("庚", "申", "丙", "子", "戊", "辰", "癸", "巳")
        incomplete = _pillars("庚", "申", "丙", "寅", "戊", "辰", "癸", "巳")
        cfg = PhysicsConfig(SUB_BRANCH_SANHE_REQ_WANG_ZHI=1.0)
        out_ok = await analyze_clash_flow(
            AnalyzeClashRequest(pillars=complete, physics_config=cfg, enabled_plugins=list(FULL_STACK_PLUGINS))
        )
        audit_ok = (out_ok.get("physics_tensor") or {}).get("audit_log") or {}
        skips_ok = _sanhe_skip_rows(audit_ok if isinstance(audit_ok, dict) else {})
        assert not any(r.get("reason") == "INCOMPLETE_TRIAD" for r in skips_ok), "三支齐且门控通过时不应有 INCOMPLETE 跳过"

        out_bad = await analyze_clash_flow(
            AnalyzeClashRequest(pillars=incomplete, physics_config=cfg, enabled_plugins=list(FULL_STACK_PLUGINS))
        )
        audit = (out_bad.get("physics_tensor") or {}).get("audit_log") or {}
        assert isinstance(audit, dict)
        skips = _sanhe_skip_rows(audit)
        assert skips, f"期望 sanhe_protocol_audits 含 SKIPPED_BY_PROTOCOL，实际 audit_log keys={list(audit.keys())}"
        assert any(str(s.get("reason") or "") == "INCOMPLETE_TRIAD" for s in skips), skips

    asyncio.run(_body())


@pytest.mark.integration
def test_scene_1_persisted_wang_zhi_registry_used_without_request_override() -> None:
    """将 SUB_BRANCH_SANHE_REQ_WANG_ZHI 持久化到 registry 后，无 PhysicsConfig 覆盖时仍走门控；缺支仍 SKIPPED。"""
    _require_database_url()
    try:
        from app.core.physics.settings_manager import bump_physics_settings_cache, persist_physics_registry_updates
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"settings_manager 不可用: {exc}")

    key = "SUB_BRANCH_SANHE_REQ_WANG_ZHI"
    prev = float(DEFAULT_PHYSICS_SETTINGS[key])
    try:
        persist_physics_registry_updates([(key, 1.0)])
    except OperationalError as exc:
        pytest.skip(f"physics_settings_registry 不可写: {exc}")
    bump_physics_settings_cache()

    try:

        async def _body() -> None:
            incomplete = _pillars("庚", "申", "丙", "寅", "戊", "辰", "癸", "巳")
            out = await analyze_clash_flow(
                AnalyzeClashRequest(pillars=incomplete, enabled_plugins=list(FULL_STACK_PLUGINS))
            )
            audit = (out.get("physics_tensor") or {}).get("audit_log") or {}
            skips = _sanhe_skip_rows(audit if isinstance(audit, dict) else {})
            assert any(str(s.get("reason") or "") == "INCOMPLETE_TRIAD" for s in skips), skips

        asyncio.run(_body())
    finally:
        try:
            persist_physics_registry_updates([(key, prev)])
            bump_physics_settings_cache()
        except OperationalError:
            pass


@pytest.mark.integration
def test_scene_2_pivot_defense_dual_threats_and_work_score_damping() -> None:
    """伤官见官 + 枭神夺食（官杀枢纽叠加）累计 severity；做功加权总分受物理场压缩。"""
    _require_database_url()

    async def _body() -> None:
        p = _pillars("癸", "卯", "丁", "酉", "庚", "辰", "壬", "午")
        body = AnalyzeClashRequest(
            pillars=p,
            physics_config=PhysicsConfig(WS_PIVOT_SELF_WEAK_THRESHOLD=12.0),
            enabled_plugins=list(FULL_STACK_PLUGINS),
        )
        out = await analyze_clash_flow(body)
        meta = (out.get("physics_tensor") or {}).get("meta") or {}
        pv = meta.get("pivot_defense_v1") or {}
        threats = list(pv.get("threats") or [])
        codes = [str(t.get("code") or "") for t in threats]
        assert pv.get("target_pivot") in {"正官", "七杀"}
        assert "L1_SGJG" in codes
        assert "L1_XSDS_OFFICER_PIVOT" in codes
        assert float(pv.get("threat_severity_sum") or 0.0) >= 1.15

        jf = meta.get("l1_junction_flags") or {}
        assert jf.get("SHANG_GUAN_JIAN_GUAN") and jf.get("XIAO_SHEN_DUO_SHI"), "须同时具备伤官见官与枭神夺食结构位"
        assert meta.get("l1_owl_food_v1"), "须存在枭神夺食 L1 记账（与 pivot 叠加威胁同源）"
        assert float(pv.get("threat_severity_sum") or 0.0) >= 1.5, "双重 L1 威胁 severity 与泛威胁累计应抬高危机合成"

        wa = meta.get("work_audit_v1") or {}
        items = list(wa.get("items") or [])
        totals = wa.get("totals") or {}
        exp_sum = float(totals.get("expected_work_sum") or 0.0)
        w_sum = float(totals.get("weighted_work_score_sum") or 0.0)
        assert exp_sum > 1e-3 and w_sum > 1e-3
        zg_scores = [float(it.get("work_score") or 0.0) for it in items if str(it.get("controller_deity") or "") == "正官"]
        assert zg_scores and sum(zg_scores) > 1.0, "官杀为控制方的做功 score 聚合应反映物理场下的有效做功记账"

    asyncio.run(_body())


@pytest.mark.integration
def test_scene_3_cong_wealth_robber_sovereignty_alloc_zero_and_protection_meta() -> None:
    """从财（从土）极端集中度 + 劫财见财：alloc_loss_effective=0 且 meta 记录 PATTERN_SOVEREIGNTY_PROTECTION。"""
    _require_database_url()

    async def _body() -> None:
        p = _pillars("己", "丑", "甲", "戌", "甲", "子", "乙", "丑")
        out = await analyze_clash_flow(
            AnalyzeClashRequest(
                pillars=p,
                physics_config=PhysicsConfig(PATTERN_CONG_DOMINANCE=0.32),
                enabled_plugins=list(FULL_STACK_PLUGINS),
            )
        )
        meta = (out.get("physics_tensor") or {}).get("meta") or {}
        pp = meta.get("pattern_profile") or {}
        assert str(pp.get("pattern_kind") or "").startswith("cong_")
        assert pp.get("sovereignty_priority") is True
        rw = meta.get("l1_robber_wealth_v1") or {}
        assert rw.get("alloc_loss_effective") == 0.0
        assert rw.get("sovereignty_gain") is True
        prot = meta.get("PATTERN_SOVEREIGNTY_PROTECTION") or {}
        assert prot.get("active") is True
        assert str(prot.get("scope") or "") == "l1_robber_wealth_alloc"

    asyncio.run(_body())
