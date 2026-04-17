#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test"))
os.environ.setdefault("QIAZHI_SKIP_DISSENT_LEDGER_PERSIST", "1")

from app.api.contracts import AnalyzeClashRequest
from app.services.analysis_service import analyze_clash_flow
from tests.unit.test_metadata_projector_v12 import _sample_bundle_1990_06_14_zhengguan


async def main() -> int:
    sample = _sample_bundle_1990_06_14_zhengguan()
    md = sample.get("metadata") if isinstance(sample, dict) else {}
    pillars = (md or {}).get("pillars") if isinstance(md, dict) else {}
    req = AnalyzeClashRequest(
        pillars=pillars,
        enabled_plugins=["classical.blind_school.v1"],
        lang="ZH",
    )
    out = await analyze_clash_flow(req)
    first = out.get("first_observation_llm") if isinstance(out, dict) else {}
    msgs = first.get("messages") if isinstance(first, dict) else []
    msg_chars = len(str(msgs))
    tree = out.get("assertion_tree") if isinstance(out, dict) else {}
    nodes = tree.get("nodes") if isinstance(tree, dict) else []
    node_rows = []
    for n in nodes if isinstance(nodes, list) else []:
        if not isinstance(n, dict):
            continue
        node_rows.append(
            {
                "node_id": str(n.get("node_id") or ""),
                "node_type": str(n.get("node_type") or ""),
                "payload_chars": len(str(n.get("text") or "")),
            }
        )
    report_lines = [
        "# ARCH PURITY REPORT",
        "",
        "## v12.3-alpha 样本",
        "",
        "- 样本：1990-06-14（庚午/壬午/庚子/丙子）",
        f"- Round:first_observation messages chars: {msg_chars}",
        f"- Payload overload threshold(800): {'VIOLATION' if msg_chars > 800 else 'PASS'}",
        "",
        "## AssertionTree 节点 Payload",
        "",
        "| Node_ID | Node_Type | Payload_Chars | <300 |",
        "|---|---:|---:|---:|",
    ]
    for r in node_rows:
        report_lines.append(
            f"| {r['node_id']} | {r['node_type']} | {r['payload_chars']} | {'PASS' if r['payload_chars'] < 300 else 'VIOLATION'} |"
        )
    report_lines.extend(
        [
            "",
            "## 结论",
            "",
            f"- Debug 预期红闪判定：{'无红闪（PASS）' if msg_chars <= 800 else '存在红闪（VIOLATION）'}",
            f"- FACT_NODE 覆盖：{len(node_rows)} 个",
        ]
    )
    out_path = _BACKEND_ROOT.parent / "ARCH_PURITY_REPORT.md"
    out_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"report_written={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
