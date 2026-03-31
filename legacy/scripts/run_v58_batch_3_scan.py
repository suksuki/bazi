#!/usr/bin/env python3
"""
FDS SOP V5.8：第三梯队（A-31～A-35）奇格异局海选流水线
========================================================
Phase 1: 遍历 518k，应用 pattern_scanner_v58 L1，输出丰度报告。
Phase 2: 审计熔断 — A-31～A-34 为极稀有奇格，丰度若超过 0.5% 立即报警。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def _data_path() -> Path:
    for p in [
        ROOT / "data" / "holographic_universe_518k.jsonl",
        ROOT / "data_local" / "holographic_universe_518k.jsonl",
    ]:
        if p.exists():
            return p
    return ROOT / "data" / "holographic_universe_518k.jsonl"


def main():
    import argparse
    p = argparse.ArgumentParser(description="V5.8 第三梯队海选：A-31～A-35 丰度扫描与审计熔断")
    p.add_argument("--tier", type=int, default=3, help="固定为 3 表示 A-31～A-35")
    p.add_argument("--data", type=Path, default=None, help="518k jsonl 路径")
    p.add_argument("--out", type=Path, default=None, help="丰度报告输出路径，默认 audit_logs/v58_batch_3_abundance.json")
    p.add_argument("--threshold-rare-pct", type=float, default=0.5, help="A-31～A-34 奇格熔断阈值（默认 0.5%%）")
    p.add_argument("--limit", type=int, default=None, help="最多扫描行数（测试用）")
    args = p.parse_args()

    data_path = args.data or _data_path()
    if not data_path.exists():
        print(f"❌ 未找到数据文件: {data_path}")
        sys.exit(1)

    from pattern_scanner_v58 import l1_match_a31_through_a35

    pattern_ids = [f"A-{i}" for i in range(31, 36)]
    counts = {pid: 0 for pid in pattern_ids}
    total = 0
    no_bazi = 0

    print(f"📂 数据: {data_path}")
    print("⏳ Phase 1: 第三梯队丰度扫描（A-31～A-35 奇格 L1 过滤器）...")

    with open(data_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            if args.limit and total >= args.limit:
                break
            total += 1
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not case.get("bazi"):
                no_bazi += 1
                continue
            matched = l1_match_a31_through_a35(case)
            for pid in matched:
                if pid in counts:
                    counts[pid] += 1
            if total % 100000 == 0 and total > 0:
                print(f"   已扫描 {total:,} 行…")

    print(f"\n✅ 扫描完成: 总行 {total:,}，无 bazi 跳过 {no_bazi:,}")

    report = {
        "schema": "FDS_V58_batch_3_abundance",
        "data_path": str(data_path),
        "total_scanned": total,
        "pattern_results": [],
    }
    threshold_rare = args.threshold_rare_pct / 100.0
    melt = False
    RARE_IDS = {"A-31", "A-32", "A-33", "A-34"}

    for pid in pattern_ids:
        c = counts[pid]
        pct = (c / total * 100) if total else 0
        ratio = (c / total) if total else 0
        report["pattern_results"].append({
            "pattern_id": pid,
            "match_count": c,
            "percentage": f"{pct:.2f}%",
            "ratio": round(ratio, 6),
        })
        if total and pid in RARE_IDS and ratio > threshold_rare:
            melt = True
            print(f"⚠️ 熔断: {pid}（奇格）占比 {pct:.2f}% 超过阈值 {args.threshold_rare_pct}%")

    out_path = args.out or (ROOT / "audit_logs" / "v58_batch_3_abundance.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📄 丰度报告已写入: {out_path}")

    if melt:
        print("\n❌ 审计熔断：A-31～A-34 中至少一格超过 0.5%，请检查 L1 逻辑后回滚再跑。")
        sys.exit(2)

    print("\n✅ Phase 2 通过：未触发熔断。第三梯队奇格丰度在控。")
    sys.exit(0)


if __name__ == "__main__":
    main()
