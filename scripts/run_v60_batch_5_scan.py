#!/usr/bin/env python3
"""
FDS SOP V6.0：第五梯队（A-41～A-50）深空格局全量海选
======================================================
Phase 1: 遍历 518k，应用 pattern_scanner_v60 L1，产出《深空格局稀有度清单》。
Phase 2: 审计熔断 — A-41/A-43 < 0.1%，A-44 < 5%。
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
    p = argparse.ArgumentParser(description="V6.0 第五梯队海选：A-41～A-50 丰度扫描与审计熔断")
    p.add_argument("--tier", type=int, default=5, help="固定为 5 表示 A-41～A-50")
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--out", type=Path, default=None, help="默认 audit_logs/v60_batch_5_abundance.json")
    p.add_argument("--threshold-rare-pct", type=float, default=0.1, help="A-41/A-43 奇格熔断阈值（默认 0.1%%）")
    p.add_argument("--threshold-a44-pct", type=float, default=5.0, help="A-44 杂气财官熔断阈值（默认 5%%）")
    p.add_argument("--limit", type=int, default=None, help="最多扫描行数（测试用）")
    args = p.parse_args()

    data_path = args.data or _data_path()
    if not data_path.exists():
        print(f"❌ 未找到数据文件: {data_path}")
        sys.exit(1)

    from pattern_scanner_v60 import l1_match_a41_through_a50

    pattern_ids = [f"A-{i}" for i in range(41, 51)]
    counts = {pid: 0 for pid in pattern_ids}
    total = 0
    no_bazi = 0

    print(f"📂 数据: {data_path}")
    print("⏳ Phase 1: 第五梯队深空丰度扫描（A-41～A-50 L1 过滤器）...")

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
            matched = l1_match_a41_through_a50(case)
            for pid in matched:
                if pid in counts:
                    counts[pid] += 1
            if total % 100000 == 0 and total > 0:
                print(f"   已扫描 {total:,} 行…")

    print(f"\n✅ 扫描完成: 总行 {total:,}，无 bazi 跳过 {no_bazi:,}")

    report = {
        "schema": "FDS_V60_batch_5_abundance",
        "description": "深空格局稀有度清单",
        "data_path": str(data_path),
        "total_scanned": total,
        "pattern_results": [],
    }
    threshold_rare = args.threshold_rare_pct / 100.0
    threshold_a44 = args.threshold_a44_pct / 100.0
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
            if pid in ("A-41", "A-43") and ratio >= threshold_rare:
                melt = True
                print(f"⚠️ 熔断: {pid} 占比 {pct:.2f}% 超过奇格阈值 {args.threshold_rare_pct}%")
            if pid == "A-44" and ratio >= threshold_a44:
                melt = True
                print(f"⚠️ 熔断: A-44（杂气财官）占比 {pct:.2f}% 超过阈值 {args.threshold_a44_pct}%")

    out_path = args.out or (ROOT / "audit_logs" / "v60_batch_5_abundance.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📄 《深空格局稀有度清单》已写入: {out_path}")

    if melt:
        print("\n❌ 审计熔断：请收紧 L1 或调整阈值后回滚再跑。")
        sys.exit(2)

    print("\n✅ Phase 2 通过：未触发熔断。")
    sys.exit(0)


if __name__ == "__main__":
    main()
