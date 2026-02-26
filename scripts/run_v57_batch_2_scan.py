#!/usr/bin/env python3
"""
FDS SOP V5.7：A-21～A-30 第二梯队海选流水线 Phase 1 & 2
========================================================
Phase 1: 遍历 518k 样本，应用 L1 逻辑（从格/专旺/天地元气/两神成象），输出丰度报告。
Phase 2: 审计熔断
  - 单格占比 ≤ 5%（通用）；
  - A-29（天地元气格）≤ 0.1%（极苛刻格局）。
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
    p = argparse.ArgumentParser(description="V5.7 第二梯队海选 Phase 1+2：A-21～A-30 丰度扫描与审计熔断")
    p.add_argument("--tier", type=int, default=2, help="固定为 2 表示仅 A-21～A-30（保留兼容）")
    p.add_argument("--data", type=Path, default=None, help="518k jsonl 路径")
    p.add_argument("--out", type=Path, default=None, help="丰度报告输出路径，默认 audit_logs/v57_batch_2_abundance.json")
    p.add_argument("--threshold-pct", type=float, default=5.0, help="单格占比熔断阈值（默认 5%%）")
    p.add_argument("--threshold-a29-pct", type=float, default=0.1, help="A-29 天地元气格熔断阈值（默认 0.1%%）")
    p.add_argument("--strict-a29", action="store_true", help="A-29 采用「天地同流」严格判定（四干同且四支同）")
    p.add_argument("--limit", type=int, default=None, help="最多扫描行数（测试用）")
    args = p.parse_args()

    data_path = args.data or _data_path()
    if not data_path.exists():
        print(f"❌ 未找到数据文件: {data_path}")
        print("  请放置 data/holographic_universe_518k.jsonl 或 data_local/ 下同名文件。")
        sys.exit(1)

    from pattern_scanner_v57 import l1_match_a21_through_a30

    pattern_ids = [f"A-{i}" for i in range(21, 31)]
    counts = {pid: 0 for pid in pattern_ids}
    total = 0
    no_bazi = 0
    strict_a29 = getattr(args, "strict_a29", False)
    if strict_a29:
        print("🔒 A-29 严格模式：天地同流（四干同且四支同）")

    print(f"📂 数据: {data_path}")
    print("⏳ Phase 1: 第二梯队丰度扫描（A-21～A-30 L1 过滤器）...")

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
            matched = l1_match_a21_through_a30(case, strict_a29=strict_a29)
            for pid in matched:
                if pid in counts:
                    counts[pid] += 1
            if total % 100000 == 0 and total > 0:
                print(f"   已扫描 {total:,} 行…")

    print(f"\n✅ 扫描完成: 总行 {total:,}，无 bazi 跳过 {no_bazi:,}")

    # 丰度报告
    report = {
        "schema": "FDS_V57_batch_2_abundance",
        "data_path": str(data_path),
        "total_scanned": total,
        "pattern_results": [],
    }
    threshold = args.threshold_pct / 100.0
    threshold_a29 = args.threshold_a29_pct / 100.0
    melt = False
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
        if total:
            if ratio > threshold:
                melt = True
                print(f"⚠️ 熔断: {pid} 占比 {pct:.2f}% 超过通用阈值 {args.threshold_pct}%")
            if pid == "A-29" and ratio > threshold_a29:
                melt = True
                print(f"⚠️ 熔断: A-29（天地元气格）占比 {pct:.2f}% 超过苛刻阈值 {args.threshold_a29_pct}%")

    out_path = args.out or (ROOT / "audit_logs" / "v57_batch_2_abundance.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📄 丰度报告已写入: {out_path}")

    # Phase 2: 审计熔断
    if melt:
        print("\n❌ 审计熔断：存在格局超过阈值，请检查 L1 逻辑后回滚再跑。")
        sys.exit(2)

    print("\n✅ Phase 2 通过：未触发熔断。可进行第二梯队 Phase 3 迁库（若需）。")
    sys.exit(0)


if __name__ == "__main__":
    main()
