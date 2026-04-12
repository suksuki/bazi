"""
0.165 全量插件集成审计套件 (Integrated Causal Audit)

覆盖：L1 流水线顺序、地理场与天干五合锁共存、从格主权下劫财见财纠偏、枢纽防御累计、
性能与 meta 结构稳定性。详细报告见 `print_full_stack_plugin_report`。
"""
from __future__ import annotations

import asyncio
import statistics
import time
from typing import Any, Dict, List, Optional, Tuple
import pytest

from app.api.contracts import AnalyzeClashRequest, AnalyzeSeedRequest, PhysicsConfig
from app.llm.client import QwenClient
from app.schemas.bazi_metadata import FourPillars, StemBranchPair
from app.services.analysis_service import analyze_clash_flow, analyze_seed_flow
from app.services.helpers import interaction_pipeline as interaction_pipeline_mod

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


FULL_STACK_PLUGINS = [
    "base.chronos",
    "classical.blind_school.v1",
    "classical.wangshuai.v1",
]

_STEM_CYCLE = "甲乙丙丁戊己庚辛壬癸"


def _step_index(steps: List[Dict[str, Any]], *, op_id: str) -> Optional[int]:
    for i, s in enumerate(steps):
        if s.get("l1_operator_id") == op_id:
            return i
        lids = s.get("l1_operator_ids") or []
        if op_id in lids:
            return i
    return None


def _step_index_plugin(steps: List[Dict[str, Any]], *, plugin: str) -> Optional[int]:
    for i, s in enumerate(steps):
        if str(s.get("plugin") or "") == plugin:
            return i
    return None


def _sum_deity_abs(tensor: Dict[str, Any]) -> float:
    axes = tensor.get("deity_energy_axes") or {}
    if not isinstance(axes, dict):
        return 0.0
    s = 0.0
    for v in axes.values():
        if isinstance(v, dict):
            s += float(v.get("absolute_energy") or 0.0)
    return s


def _marks_have_tag(meta: Dict[str, Any], needle: str) -> bool:
    marks = meta.get("interaction_marks_per_deity") or {}
    if not isinstance(marks, dict):
        return False
    for v in marks.values():
        if isinstance(v, list) and any(needle in str(x) for x in v):
            return True
    return False


def _p95(latencies_ms: List[float]) -> float:
    if not latencies_ms:
        return 0.0
    s = sorted(latencies_ms)
    idx = max(0, min(len(s) - 1, int(round(0.95 * (len(s) - 1)))))
    return float(s[idx])


def print_full_stack_plugin_report(
    *,
    sections: List[Tuple[str, str]],
    race_risks: List[str],
) -> None:
    print("\n========== Full_Stack_Plugin_Report (0.165) ==========")
    for title, body in sections:
        print(f"\n--- {title} ---\n{body}")
    print("\n--- 逻辑竞争 / 潜在竞态 (Logic Race Conditions) ---")
    for i, line in enumerate(race_risks, 1):
        print(f"  {i}. {line}")
    print("========== End Full_Stack_Plugin_Report ==========\n")


def test_execution_order_status_before_conflict_and_geography_before_fusion() -> None:
    """L1_OP_STATUS 早于核心冲突算子；地理算子早于天干五合（与 interaction_pipeline 编排一致）。"""

    async def _body() -> None:
        p_rob = _pillars("乙", "卯", "甲", "申", "庚", "酉", "辛", "巳")
        body_rob = AnalyzeClashRequest(
            pillars=p_rob,
            enabled_plugins=list(FULL_STACK_PLUGINS),
            physics_config=PhysicsConfig(user_target_direction="南"),
        )
        out_rob = await analyze_clash_flow(body_rob)
        steps_rob = ((out_rob.get("physics_tensor") or {}).get("l1_atomic_pipeline") or {}).get("steps") or []
        i_status = _step_index(steps_rob, op_id="L1_OP_STATUS")
        i_robber = _step_index(steps_rob, op_id="L1_OP_ROBBER_WEALTH")
        assert i_status is not None, "期望流水线含 L1_OP_STATUS"
        assert i_robber is not None, "期望本盘触发劫财见财算子以便顺序断言"
        assert i_status < i_robber, "op_status（长生）必须先于核心冲突族（含 op_robber_wealth）"

        p_fuse = _pillars("己", "丑", "甲", "寅", "丙", "午", "戊", "戌")
        body_fuse = AnalyzeClashRequest(
            pillars=p_fuse,
            enabled_plugins=list(FULL_STACK_PLUGINS),
            physics_config=PhysicsConfig(user_target_direction="南"),
        )
        out_fuse = await analyze_clash_flow(body_fuse)
        steps_fuse = ((out_fuse.get("physics_tensor") or {}).get("l1_atomic_pipeline") or {}).get("steps") or []
        i_geo = _step_index(steps_fuse, op_id="L1_OP_GEOGRAPHY")
        i_fusion = _step_index_plugin(steps_fuse, plugin="base.stem_fusion")
        assert i_geo is not None and i_fusion is not None
        assert i_geo < i_fusion, "op_geography 必须在 op_stem_fusion 之前执行（避免误读为地理覆盖合化锁）"

        tr = out_rob.get("physics_tensor") or {}
        meta = tr.get("meta") if isinstance(tr.get("meta"), dict) else {}
        assert meta.get("l1_status_v1"), "长生状态应已写入 meta.l1_status_v1（供后续 L2 与 pivot）"
        assert meta.get("work_audit_v1") is not None or isinstance(meta.get("blind_school_features"), dict)

    asyncio.run(_body())


def test_geography_does_not_clear_stem_fusion_lock() -> None:
    """地理方位补丁与 stem_fusion_v1 锁死状态可并存。"""

    async def _body() -> None:
        p = _pillars("己", "未", "甲", "寅", "丙", "午", "丁", "巳")
        body = AnalyzeClashRequest(
            pillars=p,
            enabled_plugins=list(FULL_STACK_PLUGINS),
            physics_config=PhysicsConfig(user_target_direction="南"),
        )
        out = await analyze_clash_flow(body)
        meta = (out.get("physics_tensor") or {}).get("meta") or {}
        sf = meta.get("stem_fusion_v1") or {}
        geo = meta.get("geography_field_patch_v1")
        assert sf.get("is_locked") is True
        assert isinstance(geo, dict) and geo.get("direction") == "南"
        assert "stem_fusion_v1" in meta and meta["stem_fusion_v1"] is sf

    asyncio.run(_body())


def test_pattern_sovereignty_reconciles_robber_wealth_alloc() -> None:
    """从格主权定型后：对 op_robber_wealth 的 Abs 损耗做纠偏，并标记 sovereignty_gain。"""

    async def _body() -> None:
        p_rob = _pillars("己", "丑", "甲", "戌", "甲", "子", "乙", "丑")
        body0 = AnalyzeClashRequest(pillars=p_rob, enabled_plugins=list(FULL_STACK_PLUGINS))
        out0 = await analyze_clash_flow(body0)
        tensor0 = out0["physics_tensor"]
        meta0 = tensor0.get("meta") if isinstance(tensor0.get("meta"), dict) else {}
        assert meta0.get("l1_robber_wealth_v1"), "期望本盘触发 l1_robber_wealth_v1"
        before_abs = float(((tensor0.get("deity_energy_axes") or {}).get("正财") or {}).get("absolute_energy") or 0.0)

        pp = {
            "pattern_kind": "cong_fire",
            "pattern_name_zh": "从火格（测试注入）",
            "sovereignty_priority": True,
            "dominant_element": "fire",
            "dominance_ratio": 0.55,
            "favorable_deities": ["食神", "伤官"],
            "eta_flip_gain": 1.12,
        }
        meta0["pattern_profile"] = pp
        interaction_pipeline_mod._reconcile_robber_wealth_under_pattern_sovereignty(tensor0)
        rw = (tensor0.get("meta") or {}).get("l1_robber_wealth_v1") or {}
        assert rw.get("sovereignty_gain") is True
        assert rw.get("alloc_loss_effective") == 0.0
        prot = meta0.get("PATTERN_SOVEREIGNTY_PROTECTION") or {}
        assert prot.get("active") is True
        assert str(prot.get("scope") or "") == "l1_robber_wealth_alloc"
        after_abs = float(((tensor0.get("deity_energy_axes") or {}).get("正财") or {}).get("absolute_energy") or 0.0)
        assert after_abs >= before_abs * 0.999, "纠偏后正财 Abs 不应低于纠偏前（损耗被撤销）"

        p_cong = _pillars("丙", "寅", "甲", "午", "甲", "戌", "乙", "丑")
        body1 = AnalyzeClashRequest(
            pillars=p_cong,
            physics_config=PhysicsConfig(PATTERN_CONG_DOMINANCE=0.32),
            enabled_plugins=list(FULL_STACK_PLUGINS),
        )
        out1 = await analyze_clash_flow(body1)
        meta1 = (out1["physics_tensor"].get("meta") or {})
        pp1 = meta1.get("pattern_profile") or {}
        assert pp1.get("sovereignty_priority") is True
        assert str(pp1.get("pattern_kind") or "").startswith("cong_")

    asyncio.run(_body())


def test_pivot_defense_accumulates_severity_and_crisis_gate() -> None:
    """pivot_defense_v1：多 L1 威胁 severity 累计，并在门槛上触发 PIVOT_CRISIS。"""

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
        sev_sum = float(pv.get("threat_severity_sum") or 0.0)
        codes = [str(t.get("code") or "") for t in threats]
        assert len(threats) >= 2, f"期望多重威胁条目，实际 threats={threats}"
        assert "L1_SGJG" in codes, f"期望伤官见官威胁码，实际 codes={codes}"
        assert "L1_XSDS_OFFICER_PIVOT" in codes, f"期望枭神夺食与官杀枢纽叠加威胁码，实际 codes={codes}"
        assert sev_sum >= 1.15, f"期望 threat 累计接近危机阈 1.2，实际 sum={sev_sum}"
        assert pv.get("pivot_crisis") is True
        tags = list(pv.get("llm_assertion_tags") or [])
        assert "PIVOT_CRISIS" in tags

    asyncio.run(_body())


def test_performance_fifty_seeds_meta_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    """50 次种子流（LLM 打桩）：physics 链 latency 与 meta 结构稳定。"""

    async def _fake_chat(self: Any, *args: Any, **kwargs: Any) -> Tuple[str, Dict[str, float]]:
        return ("stub", {"elapsed_ms": 0.0, "approx_tokens": 0.0})

    monkeypatch.setattr(QwenClient, "chat_with_telemetry", _fake_chat)

    latencies_ms: List[float] = []
    meta_keys_samples: List[List[str]] = []

    async def _one(i: int) -> None:
        hs = _STEM_CYCLE[i % 10]
        pillars = _pillars("己", "未", "甲", "寅", "丙", "午", hs, "巳")
        body = AnalyzeSeedRequest(
            date="1990-01-15",
            time="10:30",
            calendar="solar",
            gender="male",
            reference_year=2000 + i,
            physics_config=PhysicsConfig(user_target_direction="南", PATTERN_CONG_DOMINANCE=0.42),
            enabled_plugins=list(FULL_STACK_PLUGINS),
        )

        def get_bazi(date: str, time: str, calendar: str) -> FourPillars:
            del date, time, calendar
            return pillars

        def get_timeline_snapshot(
            date: str,
            time: str,
            calendar: str,
            gender_flag: int,
            reference_year: int,
        ) -> Dict[str, Any]:
            del date, time, calendar, gender_flag, reference_year
            return {"liunian": "甲子", "dayun": "乙丑"}

        t0 = time.perf_counter()
        out = await analyze_seed_flow(body, get_bazi, get_timeline_snapshot, "2026-04-11T00:00:00Z")
        dt_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(dt_ms)
        pt = out.get("physics_tensor") or {}
        meta = pt.get("meta")
        assert isinstance(meta, dict), "physics_tensor.meta 必须为 dict"
        for k in ("stem_fusion_v1", "causal_routing", "l1_status_v1"):
            if k in meta:
                assert not isinstance(meta[k], str), f"meta.{k} 不应被覆盖为 str"
        meta_keys_samples.append(sorted(meta.keys())[:24])

    async def _run_all() -> None:
        for i in range(50):
            await _one(i)

    asyncio.run(_run_all())

    median = float(statistics.median(latencies_ms)) if latencies_ms else 0.0
    p95v = _p95(latencies_ms)
    assert median < 320.0, f"physics+插件链 median={median:.1f}ms 期望 <320ms（打桩 LLM 后）"
    assert p95v < 800.0, f"p95={p95v:.1f}ms 期望 <800ms"

    if len(meta_keys_samples) >= 2:
        a = set(meta_keys_samples[0])
        b = set(meta_keys_samples[-1])
        assert len(a & b) >= 8, "meta 键集合不应在批量请求中漂移丢失"


def test_print_full_stack_plugin_report_race_notes(capsys: pytest.CaptureFixture[str]) -> None:
    """打印审计报告（含竞态提示），供 CI 日志人工复核。"""
    sections = [
        (
            "流水线编排 (interaction_pipeline)",
            "顺序: atomic_pool → op_status → core_conflict(含 op_geography) → op_stem_fusion → op_sub_branch_interaction → "
            "junction/flow/pattern →（可选）robber 纠偏。L2 Hook: chronos → blind(op_work_logic) → wangshuai(pivot)。",
        ),
        (
            "格局 vs L1 算子",
            "pattern_profile 在 L1 冲突算子之后才定型；劫财见财的 Abs 纠偏在 evaluate_pattern_profile 之后执行（见 _reconcile_robber_wealth_under_pattern_sovereignty）。",
        ),
        (
            "路由 merged_eta_flip",
            "CausalRouter.apply_pattern_override 仅作用于 merged_impact，不自动回写 deity_energy_axes；与 physics 域纠偏分属两层。",
        ),
    ]
    race_risks = [
        "pattern_profile 与 l1_robber_wealth_v1 的时序：若将格局识别前移到冲突算子之前，需同步调整纠偏钩子位置。",
        "盲派 op_work_logic 与旺衰 pivot 均依赖 l1_status_v1；若 status 算子失败静默，下游将出现伪稳定枢纽。",
        "geography 修改 vector/normalized 与 stem_fusion 修改 axes 的顺序依赖：若重排为 fusion 先于 geography，则「锁态共存」断言需重写。",
        "enabled_plugins 为空与为全量时 chronos 去重逻辑不同（registry._chronos_registry_runner），合并审计时注意重复 chronos_audit_items。",
        "LLM 首包观测未打桩时，性能断言与全栈审计不可混用同一阈值。",
    ]
    print_full_stack_plugin_report(sections=sections, race_risks=race_risks)
    captured = capsys.readouterr()
    assert "Full_Stack_Plugin_Report" in captured.out


def test_sub_branch_banhe_abs_scales_with_abs_boost() -> None:
    """半合存在时：提高 SUB_BRANCH_BANHE_ABS_BOOST 应改变十神 Abs 总和（与 op_sub_branch 乘子一致）。"""

    async def _body() -> None:
        p = _pillars("甲", "子", "丙", "寅", "戊", "午", "庚", "申")
        body_lo = AnalyzeClashRequest(
            pillars=p,
            enabled_plugins=list(FULL_STACK_PLUGINS),
            physics_config=PhysicsConfig(SUB_BRANCH_BANHE_ABS_BOOST=0.02),
        )
        body_hi = AnalyzeClashRequest(
            pillars=p,
            enabled_plugins=list(FULL_STACK_PLUGINS),
            physics_config=PhysicsConfig(SUB_BRANCH_BANHE_ABS_BOOST=0.22),
        )
        out_lo = await analyze_clash_flow(body_lo)
        out_hi = await analyze_clash_flow(body_hi)
        pt_lo = out_lo.get("physics_tensor") or {}
        meta_lo = pt_lo.get("meta") if isinstance(pt_lo.get("meta"), dict) else {}
        iv2 = meta_lo.get("interaction_v2") or {}
        assert list(iv2.get("banhe") or []), "期望本盘含半合以便 Abs 对比"
        a_lo = _sum_deity_abs(out_lo["physics_tensor"] or {})
        a_hi = _sum_deity_abs(out_hi["physics_tensor"] or {})
        assert abs(a_hi - a_lo) > 1e-4, f"期望半合 Abs 总随 BANHE_ABS_BOOST 变化，lo={a_lo} hi={a_hi}"

    asyncio.run(_body())


def test_liuhai_marks_off_when_liuhai_disabled() -> None:
    """子未六害：SUB_BRANCH_LIUHAI_ENABLE=0 时不应出现害类 interaction 标。"""

    async def _body() -> None:
        p = _pillars("甲", "子", "乙", "午", "丙", "寅", "丁", "未")
        body_on = AnalyzeClashRequest(
            pillars=p,
            enabled_plugins=list(FULL_STACK_PLUGINS),
            physics_config=PhysicsConfig(SUB_BRANCH_LIUHAI_ENABLE=1.0),
        )
        body_off = AnalyzeClashRequest(
            pillars=p,
            enabled_plugins=list(FULL_STACK_PLUGINS),
            physics_config=PhysicsConfig(SUB_BRANCH_LIUHAI_ENABLE=0.0),
        )
        out_on = await analyze_clash_flow(body_on)
        out_off = await analyze_clash_flow(body_off)
        meta_on = (out_on.get("physics_tensor") or {}).get("meta") or {}
        meta_off = (out_off.get("physics_tensor") or {}).get("meta") or {}
        assert _marks_have_tag(meta_on, "hai"), "开启六害时期望 interaction 标含 hai"
        assert not _marks_have_tag(meta_off, "hai"), "关闭六害时期望无 hai 标"

    asyncio.run(_body())


def test_complex_chart_structural_signals() -> None:
    """复杂盘：至少同时命中多项结构信号（三合、伤官见官、合化/羁绊、枭神夺食等）。"""

    async def _body() -> None:
        p = _pillars("己", "丑", "甲", "寅", "丙", "午", "戊", "戌")
        body = AnalyzeClashRequest(
            pillars=p,
            enabled_plugins=list(FULL_STACK_PLUGINS),
            physics_config=PhysicsConfig(user_target_direction="南"),
        )
        out = await analyze_clash_flow(body)
        tensor = out["physics_tensor"] or {}
        meta = tensor.get("meta") if isinstance(tensor.get("meta"), dict) else {}
        comp = tensor.get("composite_field_impact") or {}
        sanhe_n = len(comp.get("sanhe_clusters") or [])
        jf = meta.get("l1_junction_flags") or {}
        sf = meta.get("stem_fusion_v1") or {}
        assert sanhe_n >= 1
        assert jf.get("SHANG_GUAN_JIAN_GUAN")
        assert isinstance(sf.get("cases"), list) and len(sf["cases"]) >= 1
        assert meta.get("l1_owl_food_v1") or meta.get("l1_blade_clash_v1") or meta.get("l1_gov_kill_mix_v1")

    asyncio.run(_body())
