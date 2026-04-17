#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import copy
import json
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# 允许在无真实 DATABASE_URL 的 CI / 本地环境下导入 app.db.session（引擎惰性连库；本脚本烟测不访问真实 PG）
if not (os.getenv("DATABASE_URL") or os.getenv("QIAZHI_BAZI_DB_URL")):
    os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:65432/postgres"

from app.core.scanner import Scanner
from app.logic.brain.hub import BrainHub
from app.schemas.bazi_metadata import FourPillars, StemBranchPair
from tests.unit.test_metadata_projector_v12 import _sample_bundle_1990_06_14_zhengguan


@dataclass
class Case:
    case_id: str
    label: str
    pillars: FourPillars


def _p(stem: str, branch: str) -> StemBranchPair:
    return StemBranchPair(stem=stem, branch=branch)


CASES: List[Case] = [
    Case("C01", "高能闭锁样本", FourPillars(year=_p("庚", "午"), month=_p("壬", "午"), day=_p("庚", "子"), hour=_p("丙", "子"))),
    Case("C02", "子午冲显性", FourPillars(year=_p("甲", "子"), month=_p("丁", "午"), day=_p("庚", "子"), hour=_p("丙", "午"))),
    Case("C03", "寅巳穿害倾向", FourPillars(year=_p("甲", "寅"), month=_p("辛", "巳"), day=_p("丙", "寅"), hour=_p("癸", "酉"))),
    Case("C04", "平衡盘", FourPillars(year=_p("己", "亥"), month=_p("甲", "寅"), day=_p("丙", "午"), hour=_p("庚", "申"))),
    Case("C05", "官杀混杂", FourPillars(year=_p("癸", "酉"), month=_p("庚", "午"), day=_p("乙", "卯"), hour=_p("辛", "酉"))),
    Case("C06", "财多身弱", FourPillars(year=_p("戊", "辰"), month=_p("己", "未"), day=_p("甲", "子"), hour=_p("戊", "戌"))),
    Case("C07", "从强倾向", FourPillars(year=_p("庚", "申"), month=_p("辛", "酉"), day=_p("庚", "申"), hour=_p("壬", "子"))),
    Case("C08", "木火偏盛", FourPillars(year=_p("甲", "寅"), month=_p("丙", "午"), day=_p("辛", "丑"), hour=_p("丁", "巳"))),
    Case("C09", "辰戌冲", FourPillars(year=_p("戊", "辰"), month=_p("壬", "戌"), day=_p("乙", "丑"), hour=_p("辛", "未"))),
    Case("C10", "金木交战", FourPillars(year=_p("辛", "酉"), month=_p("甲", "寅"), day=_p("庚", "午"), hour=_p("乙", "卯"))),
]


def _run_case(case: Case) -> Dict[str, object]:
    bundle = _sample_bundle_1990_06_14_zhengguan()
    md = copy.deepcopy(bundle["metadata"])
    pt = copy.deepcopy(bundle["physics_tensor"])
    md["pillars"] = case.pillars.model_dump()
    points = Scanner().scan(case.pillars).points
    cp = [{"kind": str(p.kind), "detail": str(p.detail)} for p in points]
    hub = BrainHub()
    out = hub.orchestrate(
        conflict_points=cp,
        verified_facts=["VF01", "VF02"],
        user_confirmed=False,
        self_abs=0.95 if case.case_id == "C01" else 0.5,
        output_vector_present=False if case.case_id == "C01" else True,
    )
    lineage_ok = str((out.htn_plan or {}).get("lineage") or "") == "HTN_DRIVEN"
    has_conflict = bool(out.seed_short)
    probe_ok = (out.flow_state == "PROBE_WAITING") if has_conflict else True
    return {
        "case_id": case.case_id,
        "label": case.label,
        "seed_short": out.seed_short,
        "flow_state": out.flow_state,
        "lineage": (out.htn_plan or {}).get("lineage"),
        "lineage_ok": lineage_ok,
        "probe_ok": probe_ok,
    }


def _v1295_analyze_out_stub(tag: str) -> Dict[str, object]:
    """构造接近 analyze-clash 的负载，用于 V12.95 静默仲裁审计烟测。"""
    return {
        "metadata": {
            "flow_state": "probe_waiting",
            "conflict_matrix": {"points": [{"kind": "clash", "detail": f"伤官见官逻辑冲突-{tag}"}]},
            "verdict_anchor_layer": {},
        },
        "physics_tensor": {
            "meta": {
                "global_entropy": {"value": 0.35, "metrics": {"m_clash": 0.12}},
                "semantic_label_bundle_v1": {
                    "verified_fact_lines": ["VF:七杀透干与印星牵制", "VF:官星得根于月令"],
                },
                "decision_inbox_v1": {
                    "match_scores": [
                        {"plugin_id": "plugin.alpha", "score": 0.91},
                        {"plugin_id": "plugin.beta", "score": 0.905},
                    ]
                },
            },
            "deity_scores": {"正官": 0.42, "七杀": 0.38},
        },
        "assertion_tree": {"protocol": "assertion_tree.v1", "root_id": "root", "nodes": [], "edges": []},
        "active_probing": {
            "reason_code": "M3_HIGH_TENSION_PENDING",
            "interrupt": {"interrupt_id": f"int-{tag}"},
            "block_mode": True,
        },
        "interrupt_request": {"state": "pending"},
    }


async def run_v1295_audit_smoke() -> Tuple[bool, List[str]]:
    """两次静默仲裁：校验 conflict_context 含物理证据字段，并写入 meta 审计 feed。"""
    from app.services.helpers import v1294_silent_arbiter as v4

    captured: List[str] = []

    async def fake_invoke(**kwargs: object) -> Dict[str, object]:
        ctx = kwargs.get("conflict_context") or {}
        captured.append(json.dumps(ctx, ensure_ascii=False))
        return {
            "decision": "plugin.alpha",
            "reason": "stub-arbiter",
            "audit": {
                "prompt_messages": [{"role": "user", "content": "stub"}],
                "raw_response": '{"decision":"plugin.alpha","reason":"stub-arbiter"}',
                "conflict_context": ctx,
            },
        }

    @contextmanager
    def fake_scope():
        class _DummySession:
            pass

        yield _DummySession()

    lines: List[str] = []
    with patch.object(v4, "invoke_conflict_arbiter_llm", new=fake_invoke):
        with patch.object(v4, "load_gold_arbiter_matching", return_value=({"伤官"}, "Based on GOLD Set #1 (HTN snapshot #7)")):
            with patch.object(v4, "persist_arbitration_log_to_snapshot", return_value=1):
                with patch("app.db.session.session_scope", fake_scope):
                    out1 = await v4.maybe_apply_v1294_silent_arbiter_to_analyze_clash(
                        out=copy.deepcopy(_v1295_analyze_out_stub("A")),
                        session_id=1,
                        lang="zh",
                        client=object(),
                    )
                    out2 = await v4.maybe_apply_v1294_silent_arbiter_to_analyze_clash(
                        out=copy.deepcopy(_v1295_analyze_out_stub("B")),
                        session_id=1,
                        lang="zh",
                        client=object(),
                    )

    pt1 = out1.get("physics_tensor") if isinstance(out1.get("physics_tensor"), dict) else {}
    meta1 = pt1.get("meta") if isinstance(pt1.get("meta"), dict) else {}
    feed1 = meta1.get("arbitration_audit_feed_v1")
    pt2 = out2.get("physics_tensor") if isinstance(out2.get("physics_tensor"), dict) else {}
    meta2 = pt2.get("meta") if isinstance(pt2.get("meta"), dict) else {}
    feed2 = meta2.get("arbitration_audit_feed_v1")
    ok_len = isinstance(feed1, list) and len(feed1) >= 1 and isinstance(feed2, list) and len(feed2) >= 1
    ok_phys = len(captured) >= 2 and all(
        ("global_entropy" in blob and "verified_fact_lines_excerpt" in blob and "deity_scores_excerpt" in blob)
        for blob in captured
    )

    lines.append(f"- arbitration_runs: {len(captured)}")
    lines.append(f"- meta_feed_entries_run1: {len(feed1) if isinstance(feed1, list) else 0}")
    lines.append(f"- meta_feed_entries_run2: {len(feed2) if isinstance(feed2, list) else 0}")
    lines.append(f"- physics_context_has_entropy_vf_deity: {ok_phys}")

    ok = bool(ok_len and ok_phys)
    lines.append(f"- v1295_smoke: {'PASS' if ok else 'FAIL'}")
    return ok, lines


def main() -> int:
    rows = [_run_case(c) for c in CASES]
    ok = all(bool(r["lineage_ok"]) and bool(r["probe_ok"]) for r in rows)
    out_path = Path(__file__).resolve().parents[2] / "docs" / "architecture" / "V129_GRADUATION_REPORT.md"
    lines = [
        "# V12.92 毕业测试报告",
        "",
        "| Case | Label | seed_short | flow_state | lineage | lineage_ok | probe_ok |",
        "|---|---|---|---|---|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['case_id']} | {r['label']} | {r['seed_short']} | {r['flow_state']} | {r['lineage']} | {r['lineage_ok']} | {r['probe_ok']} |"
        )
    lines.append("")
    lines.append(f"- overall: {'PASS' if ok else 'FAIL'}")
    audit_ok, audit_lines = asyncio.run(run_v1295_audit_smoke())
    lines.append("")
    lines.append("## V12.95 LLM 裁决审计烟测（Debug 透明化 / BrainHtnSnapshot.arbitration_logs）")
    lines.extend(audit_lines)
    lines.append(f"- graduation_total: {'PASS' if ok and audit_ok else 'FAIL'}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"graduation_report={out_path}")
    return 0 if ok and audit_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
