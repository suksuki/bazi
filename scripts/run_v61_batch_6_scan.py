#!/usr/bin/env python3
"""
FDS SOP V6.1：第六梯队（A-46～A-60）Batch 6 海选
=================================================
验收位：A-48（六甲趋乾）丰度若 > 0.2% 则熔断，需将「地支亥≥2」升至≥3。
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
    p = argparse.ArgumentParser(description="V6.1 第六梯队海选：A-46～A-60 丰度扫描")
    p.add_argument("--tier", type=int, default=6, help="固定为 6 表示 A-46～A-60")
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--out", type=Path, default=None, help="默认 audit_logs/v61_batch_6_abundance.json")
    p.add_argument("--threshold-a48-pct", type=float, default=0.2, help="A-48 六甲趋乾熔断阈值（默认 0.2%%）")
    p.add_argument("--limit", type=int, default=None, help="最多扫描行数（测试用）")
    args = p.parse_args()

    data_path = args.data or _data_path()
    if not data_path.exists():
        print(f"❌ 未找到数据文件: {data_path}")
        sys.exit(1)

    from pattern_scanner_v61 import l1_match_a46_through_a60

    pattern_ids = [f"A-{i}" for i in range(46, 61)]
    counts = {pid: 0 for pid in pattern_ids}
    total = 0
    no_bazi = 0

    print(f"📂 数据: {data_path}")
    print("⏳ Batch 6: A-46～A-60 丰度扫描...")

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
            matched = l1_match_a46_through_a60(case)
            for pid in matched:
                if pid in counts:
                    counts[pid] += 1
            if total % 100000 == 0 and total > 0:
                print(f"   已扫描 {total:,} 行…")

    print(f"\n✅ 扫描完成: 总行 {total:,}，无 bazi 跳过 {no_bazi:,}")

    report = {
        "schema": "FDS_V61_batch_6_abundance",
        "data_path": str(data_path),
        "total_scanned": total,
        "pattern_results": [],
    }
    threshold_a48 = args.threshold_a48_pct / 100.0
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
        if total and pid == "A-48" and ratio > threshold_a48:
            melt = True
            print(f"⚠️ 熔断: A-48（六甲趋乾）占比 {pct:.2f}% 超过阈值 {args.threshold_a48_pct}%")

    out_path = args.out or (ROOT / "audit_logs" / "v61_batch_6_abundance.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📄 丰度报告已写入: {out_path}")

    if melt:
        print("\n❌ 审计熔断：请将 A-48「地支亥≥2」升至≥3 后回滚再跑。")
        sys.exit(2)

    print("\n✅ 未触发熔断。")
    sys.exit(0)


if __name__ == "__main__":
    main()
