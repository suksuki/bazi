#!/usr/bin/env python3
"""
FDS SOP V5.7：A-14～A-20 海选流水线 Phase 1 & 2
================================================
Phase 1: 遍历 518k 样本，应用 L1 逻辑，输出丰度报告。
Phase 2: 审计熔断（单格占比 ≤ 5%）；超则退出并提示回滚。
数据源：data/holographic_universe_518k.jsonl 或 data_local/ 下同名文件。
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
    p = argparse.ArgumentParser(description="V5.7 海选 Phase 1+2：丰度扫描与审计熔断")
    p.add_argument("--data", type=Path, default=None, help="518k jsonl 路径")
    p.add_argument("--out", type=Path, default=None, help="丰度报告输出路径，默认 audit_logs/v57_batch_1_abundance.json")
    p.add_argument("--threshold-pct", type=float, default=5.0, help="单格占比熔断阈值（默认 5%%）")
    p.add_argument("--limit", type=int, default=None, help="最多扫描行数（测试用）")
    args = p.parse_args()

    data_path = args.data or _data_path()
    if not data_path.exists():
        print(f"❌ 未找到数据文件: {data_path}")
        print("  请放置 data/holographic_universe_518k.jsonl 或 data_local/ 下同名文件。")
        sys.exit(1)

    from pattern_scanner_v57 import l1_match_a14_through_a20

    pattern_ids = [f"A-{i:02d}" for i in range(14, 21)]
    counts = {pid: 0 for pid in pattern_ids}
    total = 0
    no_bazi = 0

    print(f"📂 数据: {data_path}")
    print("⏳ Phase 1: 丰度扫描（L1 过滤器）...")

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
            matched = l1_match_a14_through_a20(case)
            for pid in matched:
                if pid in counts:
                    counts[pid] += 1
            if total % 100000 == 0 and total > 0:
                print(f"   已扫描 {total:,} 行…")

    print(f"\n✅ 扫描完成: 总行 {total:,}，无 bazi 跳过 {no_bazi:,}")

    # 丰度报告
    report = {
        "schema": "FDS_V57_batch_1_abundance",
        "data_path": str(data_path),
        "total_scanned": total,
        "pattern_results": [],
    }
    threshold = args.threshold_pct / 100.0
    melt = False
    for pid in pattern_ids:
        c = counts[pid]
        pct = (c / total * 100) if total else 0
        report["pattern_results"].append({
            "pattern_id": pid,
            "match_count": c,
            "percentage": f"{pct:.2f}%",
            "ratio": round(c / total, 6) if total else 0,
        })
        if total and (c / total) > threshold:
            melt = True
            print(f"⚠️ 熔断: {pid} 占比 {pct:.2f}% 超过 {args.threshold_pct}%")

    out_path = args.out or (ROOT / "audit_logs" / "v57_batch_1_abundance.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📄 丰度报告已写入: {out_path}")

    # Phase 2: 审计熔断
    if melt:
        print("\n❌ 审计熔断：存在格局超过阈值，请检查 L1 逻辑后回滚再跑。")
        sys.exit(2)

    print("\n✅ Phase 2 通过：未触发熔断。可进行 Phase 3 质心校准与迁库。")
    sys.exit(0)


if __name__ == "__main__":
    main()
