#!/usr/bin/env python3
"""V12 压力内测：10 个极端样本反应式大脑闭环回归 + REJECT 稳定性报表。"""

from __future__ import annotations

import copy
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test"))
os.environ.setdefault("QIAZHI_SKIP_DISSENT_LEDGER_PERSIST", "1")

from app.logic.brain.assertion_tree import build_assertion_tree
from app.logic.brain.hub import BrainHub
from app.schemas.bazi_metadata import FourPillars, StemBranchPair
from tests.unit.test_metadata_projector_v12 import _sample_bundle_1990_06_14_zhengguan


@dataclass
class StressCase:
    case_id: str
    label: str
    pillars: FourPillars


def _p(stem: str, branch: str) -> StemBranchPair:
    return StemBranchPair(stem=stem, branch=branch)


CASES: List[StressCase] = [
    StressCase("C01", "从强倾向（金水寒凝）", FourPillars(year=_p("庚", "申"), month=_p("辛", "酉"), day=_p("庚", "申"), hour=_p("壬", "子"))),
    StressCase("C02", "从弱倾向（木火重压）", FourPillars(year=_p("甲", "寅"), month=_p("丙", "午"), day=_p("辛", "丑"), hour=_p("丁", "巳"))),
    StressCase("C03", "五行中和（平衡盘）", FourPillars(year=_p("己", "亥"), month=_p("甲", "寅"), day=_p("丙", "午"), hour=_p("庚", "申"))),
    StressCase("C04", "官杀混杂（高冲突）", FourPillars(year=_p("癸", "酉"), month=_p("庚", "午"), day=_p("乙", "卯"), hour=_p("辛", "酉"))),
    StressCase("C05", "财多身弱（负载测试）", FourPillars(year=_p("戊", "辰"), month=_p("己", "未"), day=_p("甲", "子"), hour=_p("戊", "戌"))),
    StressCase("C06", "印旺比劫（守成偏好）", FourPillars(year=_p("壬", "子"), month=_p("癸", "亥"), day=_p("甲", "寅"), hour=_p("乙", "卯"))),
    StressCase("C07", "子午冲显性（情感宫波动）", FourPillars(year=_p("庚", "午"), month=_p("壬", "午"), day=_p("庚", "子"), hour=_p("丙", "子"))),
    StressCase("C08", "辰戌冲（土库冲开）", FourPillars(year=_p("戊", "辰"), month=_p("壬", "戌"), day=_p("乙", "丑"), hour=_p("辛", "未"))),
    StressCase("C09", "三合趋向（木局候选）", FourPillars(year=_p("甲", "寅"), month=_p("乙", "卯"), day=_p("丙", "戌"), hour=_p("丁", "亥"))),
    StressCase("C10", "金木交战（极端对冲）", FourPillars(year=_p("辛", "酉"), month=_p("甲", "寅"), day=_p("庚", "午"), hour=_p("乙", "卯"))),
]


def _report_path() -> Path:
    return Path(__file__).resolve().parents[2] / "docs" / "architecture" / "V12_SYSTEM_LOGIC_STABILITY_REPORT.md"


def run_case(case: StressCase) -> Dict[str, Any]:
    bundle = _sample_bundle_1990_06_14_zhengguan()
    metadata = copy.deepcopy(bundle["metadata"])
    physics_tensor = copy.deepcopy(bundle["physics_tensor"])
    metadata["pillars"] = case.pillars.model_dump()
    hub = BrainHub()
    ctx = hub.build_context(metadata=metadata, physics_tensor=physics_tensor, user_intention="seek_fame")
    hallucination = "此盘财官双美，近期财源广进、大发横财，可放手投机暴富。"
    audit = hub.audit(hallucination, ctx.psv_list)
    reject_count = 1 if str(audit.audit_state).upper() == "REJECT" else 0
    tree = build_assertion_tree(
        version_id=f"stress-{case.case_id}",
        assertions=[
            {"assertion_id": "f1", "text": f"{case.label}：结构冲突需复核。", "evidence_refs": ["pillars.day_branch"]},
            {"assertion_id": "f2", "text": "若财轴负向，不得输出暴富叙事。", "evidence_refs": ["rule:psv.robber_wealth_pierce_ratio"]},
        ],
        psv_list=ctx.psv_list,
        user_intention_id="seek_fame",
    )
    return {
        "case_id": case.case_id,
        "label": case.label,
        "audit_state": str(audit.audit_state),
        "reason_code": str(audit.reason_code),
        "reject_count": reject_count,
        "assertion_nodes": len((tree.get("nodes") or [])),
    }


def write_report(rows: List[Dict[str, Any]]) -> Path:
    now = datetime.now(timezone.utc).isoformat()
    total_reject = sum(int(r.get("reject_count") or 0) for r in rows)
    path = _report_path()
    lines = [
        "# V12 系统逻辑稳定性报表",
        "",
        f"- 生成时间: `{now}`",
        f"- 样本数: `{len(rows)}`",
        f"- REJECT 总次数: `{total_reject}`",
        "",
        "## 逐案明细",
        "",
        "| Case | 标签 | AuditState | ReasonCode | REJECT | AssertionNodes |",
        "|---|---|---|---|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['case_id']} | {r['label']} | {r['audit_state']} | {r['reason_code']} | {r['reject_count']} | {r['assertion_nodes']} |"
        )
    lines.extend(
        [
            "",
            "## 结论",
            "",
            "- 全链路已跑通：`BrainHub.build_context -> SemanticAuditor(REJECT 计数) -> AssertionTree`。",
            "- 本报表可作为 V12.1 稳定核心的内测基线输入。",
            "",
            "## 原始 JSON",
            "",
            "```json",
            json.dumps(rows, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    print("=== V12 压力内测启动 ===")
    results: List[Dict[str, Any]] = []
    for case in CASES:
        row = run_case(case)
        results.append(row)
        print(f"[{case.case_id}] {case.label} -> audit={row['audit_state']} reason={row['reason_code']} rejects={row['reject_count']}")
    out = write_report(results)
    print(f"=== 完成：报表已写入 {out} ===")


if __name__ == "__main__":
    main()
