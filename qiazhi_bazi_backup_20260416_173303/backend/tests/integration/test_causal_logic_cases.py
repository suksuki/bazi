"""
0.16 因果逻辑全路径自动化测试 (Auto-Verdict-Test)

通过 analyze_clash_flow 串联：物理张量 → L1 Junction → 旺衰枢纽 → 流通审计 → 格局识别 → CausalRouter。
部分断言使用 PhysicsConfig 注入合法阈值（符合「常数仅从配置读取」），用于在固定四柱下稳定复现极端象意。
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple

import pytest

from app.api.contracts import AnalyzeClashRequest, PhysicsConfig
from app.schemas.bazi_metadata import FourPillars, StemBranchPair
from app.services.analysis_service import analyze_clash_flow

pytestmark = pytest.mark.slow


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


def _logic_trace(case_id: str, physics_tensor: Dict[str, Any], metadata: Dict[str, Any]) -> None:
    """每次用例结束后打印 Logic_Trace，便于 CI 日志人工复核。"""
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    norm = physics_tensor.get("normalized") if isinstance(physics_tensor.get("normalized"), dict) else {}
    piv = meta.get("pivot_defense_v1") or {}
    flow = meta.get("energy_flow_audit") or {}
    pp = meta.get("pattern_profile") or {}
    wa = meta.get("work_audit_v1") or {}
    jf = meta.get("l1_junction_flags") or {}
    cr = meta.get("causal_routing") or {}
    pillars = (metadata or {}).get("pillars") or {}
    day = pillars.get("day") or {}
    print(f"\n========== Logic_Trace / {case_id} ==========")
    print(f"日主: {day.get('stem', '?')}{day.get('branch', '?')}")
    print(f"归一化场强: {norm}")
    print(f"枢纽 pivot_defense_v1: target_pivot={piv.get('target_pivot')} crisis={piv.get('pivot_crisis')} threats={piv.get('threats')}")
    print(f"L1_Junction: SHANG_GUAN_JIAN_GUAN={jf.get('SHANG_GUAN_JIAN_GUAN')} CAI_XING_PO_YIN={jf.get('CAI_XING_PO_YIN')} sgjg_severity={jf.get('sgjg_severity')}")
    print(f"流通 energy_flow_audit: break_count={flow.get('break_count')} segments={len(flow.get('segments') or [])}")
    print(f"格局 pattern_profile: kind={pp.get('pattern_kind')} ratio={pp.get('dominance_ratio')} sovereignty={pp.get('sovereignty_priority')}")
    print(f"做功 work_audit_v1 items={len((wa.get('items') or []))} totals={wa.get('totals')}")
    print(f"路由 pattern_router_applied={meta.get('pattern_router_applied')} pattern_kw={cr.get('pattern_assertion_keywords')}")
    print("========== End Logic_Trace ==========\n")


def _fail(layer: str, detail: str) -> None:
    pytest.fail(f"[{layer}] {detail}")


async def _run_clash(
    pillars: FourPillars,
    *,
    physics_config: Optional[PhysicsConfig] = None,
    liunian: Optional[str] = None,
    dayun: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    body = AnalyzeClashRequest(
        pillars=pillars,
        physics_config=physics_config,
        liunian=liunian,
        dayun=dayun,
    )
    out = await analyze_clash_flow(body)
    return out.get("physics_tensor") or {}, out.get("metadata") or {}


def test_case_01_tan_cai_huai_yin_pivot_and_work() -> None:
    """
    Case_01: 贪财坏印（枢纽防御 + 财星破印 L1）

    四柱：丙午 甲午 壬子 辛丑 — 火旺财局，壬日主，时干辛金正印；子午冲抬升熵。
    通过提高 WS_PIVOT_SELF_WEAK_THRESHOLD 将用神池切到印比侧，使枢纽落在「正印」，
    从而与 meta.l1_wealth_seal_v1 / CAI_XING_PO_YIN 对齐。
    """

    async def _body() -> None:
        pillars = _pillars("丙", "午", "甲", "午", "壬", "子", "辛", "丑")
        physics_config = PhysicsConfig(WS_PIVOT_SELF_WEAK_THRESHOLD=12.0)
        tensor, metadata = await _run_clash(pillars, physics_config=physics_config)
        meta = tensor.get("meta") if isinstance(tensor.get("meta"), dict) else {}
        _logic_trace("Case_01", tensor, metadata)

        piv = meta.get("pivot_defense_v1") or {}
        tp = str(piv.get("target_pivot") or "")
        if tp not in {"正印", "偏印"}:
            _fail("逻辑层(枢纽)", f"期望枢纽为印绶(正印/偏印)，实际 target_pivot={tp!r}")

        threats = list(piv.get("threats") or [])
        sev_sum = float(piv.get("threat_severity_sum") or 0.0)
        has_wealth_seal_threat = any(str(t.get("code")) == "L1_WEALTH_SEAL" for t in threats)
        if not piv.get("pivot_crisis"):
            if not (has_wealth_seal_threat and sev_sum >= 1.1):
                _fail(
                    "逻辑层(危机)",
                    f"期望 pivot_crisis 或 (L1_WEALTH_SEAL 威胁且 severity 和≥1.1)，实际 crisis={piv.get('pivot_crisis')} sum={sev_sum} threats={threats}",
                )

        wa = meta.get("work_audit_v1") or {}
        items: List[Dict[str, Any]] = list(wa.get("items") or [])
        cai_yin_scores = [
            float(it.get("work_score") or 0.0)
            for it in items
            if str(it.get("controller_deity")) in {"正财", "偏财"} and str(it.get("controlled_deity")) in {"正印", "偏印"}
        ]
        if not cai_yin_scores:
            _fail("物理层(做功)", "work_audit_v1 中未找到「财制印」向量条目")
        best = max(cai_yin_scores)
        if best <= 1.2:
            _fail("物理层(做功)", f"财克印的 work_score 期望 >1.2，实际 max={best}")

        if not meta.get("l1_wealth_seal_v1") and not (meta.get("l1_junction_flags") or {}).get("CAI_XING_PO_YIN"):
            _fail("物理层(L1)", "期望存在 l1_wealth_seal_v1 或 CAI_XING_PO_YIN 标志")

    asyncio.run(_body())


def test_case_02_shang_guan_jian_guan_flow_gate_and_liunian() -> None:
    """
    Case_02: 伤官见官 + 通关（逻辑门 + 流年引动）

    四柱：癸卯 丁酉 庚辰 壬午。
    Step A: 提高 FLOW_AUDITOR_ABS_THRESHOLD → 流通审计多段 BROKEN。
    Step B: 流年壬子 + 默认阈值 → 全链 FLOWING；伤官见官结构信号仍由 L1_Junction 提供。
    """

    async def _body() -> None:
        pillars = _pillars("癸", "卯", "丁", "酉", "庚", "辰", "壬", "午")
        strict = PhysicsConfig(FLOW_AUDITOR_ABS_THRESHOLD=0.35)
        loose = PhysicsConfig(FLOW_AUDITOR_ABS_THRESHOLD=0.06)

        tensor_a, meta_a = await _run_clash(pillars, physics_config=strict)
        _logic_trace("Case_02_StepA", tensor_a, meta_a)
        jf_a = (tensor_a.get("meta") or {}).get("l1_junction_flags") or {}
        if not jf_a.get("SHANG_GUAN_JIAN_GUAN"):
            _fail("逻辑层(L1)", "Step A 期望 SHANG_GUAN_JIAN_GUAN=True（伤官见官）")
        breaks_a = int(((tensor_a.get("meta") or {}).get("energy_flow_audit") or {}).get("break_count") or 0)
        if breaks_a < 3:
            _fail("物理层(流通)", f"Step A 期望多数相生段 BROKEN，实际 break_count={breaks_a}")

        tensor_b, meta_b = await _run_clash(pillars, physics_config=loose, liunian="壬子")
        _logic_trace("Case_02_StepB", tensor_b, meta_b)
        flow_b = (tensor_b.get("meta") or {}).get("energy_flow_audit") or {}
        breaks_b = int(flow_b.get("break_count") or 0)
        if breaks_b != 0:
            _fail("物理层(流通)", f"Step B 期望全链 FLOWING（break_count=0），实际 break_count={breaks_b}")
        segs = list(flow_b.get("segments") or [])
        if not all(str(s.get("state")) == "FLOWING" for s in segs):
            _fail("物理层(流通)", "Step B 存在非 FLOWING 的相邻五行段")

        jf_b = (tensor_b.get("meta") or {}).get("l1_junction_flags") or {}
        if not jf_b.get("SHANG_GUAN_JIAN_GUAN"):
            _fail("逻辑层(L1)", "Step B 仍应保留伤官见官结构位（SHANG_GUAN_JIAN_GUAN）")

        if jf_b.get("sgjg_severity") == "MINOR_INTERFERENCE" and jf_a.get("sgjg_severity") == "CRITICAL":
            ctrl_a = float(jf_a.get("control_energy") or 0.0)
            ctrl_b = float(jf_b.get("control_energy") or 0.0)
            assert ctrl_b <= ctrl_a * 1.05, "severity 降级时期望 control_energy 未显著高于 StepA"

    asyncio.run(_body())


def test_case_03_cong_fire_routing_and_temporal_revoke() -> None:
    """
    Case_03: 从火格 + 流年破格

    四柱：丙寅 甲午 辛巳 丁酉；降低 PATTERN_CONG_DOMINANCE 稳定命中 cong_fire。
    路由：pattern_router_applied.merged_eta_flip。
    流年：己丑 / 戊辰 → pattern_kind 回到 none。
    """

    async def _body() -> None:
        pillars = _pillars("丙", "寅", "甲", "午", "辛", "巳", "丁", "酉")
        cfg = PhysicsConfig(PATTERN_CONG_DOMINANCE=0.45)

        tensor0, meta0 = await _run_clash(pillars, physics_config=cfg)
        _logic_trace("Case_03_Base", tensor0, meta0)
        meta = tensor0.get("meta") if isinstance(tensor0.get("meta"), dict) else {}
        pp = meta.get("pattern_profile") or {}
        pk = str(pp.get("pattern_kind") or "")
        if pk != "cong_fire" and not pk.startswith("cong_"):
            _fail("格局路由", f"期望从势类 pattern_kind=cong_*，实际 {pk!r}")
        if not pp.get("sovereignty_priority"):
            _fail("格局路由", "期望 pattern_profile.sovereignty_priority=True")

        router = meta.get("pattern_router_applied") or {}
        if not router.get("merged_eta_flip"):
            _fail("格局路由", "期望 CausalRouter 写入 pattern_router_applied.merged_eta_flip=True")

        for liu in ("己丑", "戊辰"):
            tensor_w, meta_w = await _run_clash(pillars, physics_config=cfg, liunian=liu)
            _logic_trace(f"Case_03_Liunian_{liu}", tensor_w, meta_w)
            pp_w = (tensor_w.get("meta") or {}).get("pattern_profile") or {}
            if str(pp_w.get("pattern_kind") or "none") == "cong_fire":
                _fail("时空引动", f"流年 {liu} 期望撤销从火格(pattern_kind≠cong_fire)，实际仍为 cong_fire")

    asyncio.run(_body())


def test_half_combination_shen_zi_water_patch() -> None:
    """申子半合（无辰）：interaction_v2.banhe 记水局 Phi，并向量化水场强补丁 + branch_interaction_audit。"""

    async def _body() -> None:
        pillars = _pillars("甲", "子", "丙", "寅", "戊", "午", "庚", "申")
        tensor, metadata = await _run_clash(pillars)
        meta = tensor.get("meta") if isinstance(tensor.get("meta"), dict) else {}
        _logic_trace("HalfBanhe", tensor, metadata)
        iv2 = meta.get("interaction_v2") or {}
        banhe = list(iv2.get("banhe") or [])
        assert banhe, "期望 interaction_v2.banhe 非空（申子半合）"
        assert any(str(h.get("element")) == "water" for h in banhe), f"期望半合化水，实际 banhe={banhe}"
        assert all(float(h.get("phi") or 0) > 0.55 for h in banhe), "期望半合 Phi≈配置 SUB_BRANCH_BANHE_PHI"
        audit = (tensor.get("audit_log") or {}).get("branch_interaction_audit") or []
        assert any(str(x.get("type")) == "BANHE" for x in audit), "期望 audit_log.branch_interaction_audit 含 BANHE"
        vec = tensor.get("vector") if isinstance(tensor.get("vector"), dict) else {}
        assert float(vec.get("water") or 0) > 0, "期望 vector.water 存在正向水能量"

    asyncio.run(_body())


def test_stem_fusion_stuck_zeros_merged_attack_route() -> None:
    """邻柱五合不化 → stem_fusion_v1 STUCK；CausalRouter 将 locked 十神 merged_impact 置零。"""

    async def _body() -> None:
        pillars = _pillars("己", "未", "甲", "寅", "丙", "午", "丁", "巳")
        tensor, metadata = await _run_clash(pillars)
        meta = tensor.get("meta") if isinstance(tensor.get("meta"), dict) else {}
        _logic_trace("StemStuck", tensor, metadata)
        sf = meta.get("stem_fusion_v1") or {}
        assert sf.get("is_locked") is True
        assert sf.get("has_stuck") is True
        assert any(str(c.get("mode")) == "stuck" for c in (sf.get("cases") or []))
        locked = [str(d) for d in (sf.get("locked_deities") or []) if str(d).strip()]
        assert locked, "期望 locked_deities 非空"
        cr = meta.get("causal_routing") or {}
        merged = cr.get("merged_impact") if isinstance(cr.get("merged_impact"), dict) else {}
        touched = [d for d in locked if d in merged]
        assert touched, f"期望至少一名锁定十神出现在 merged_impact 中以便验证置零，locked={locked} merged_keys={list(merged.keys())}"
        for d in touched:
            assert abs(float(merged.get(d) or 0.0)) < 1e-9, f"期望 merged[{d}]≈0，实际 {merged.get(d)}"

    asyncio.run(_body())
