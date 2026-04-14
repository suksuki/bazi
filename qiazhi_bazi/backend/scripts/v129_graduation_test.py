#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"graduation_report={out_path}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
