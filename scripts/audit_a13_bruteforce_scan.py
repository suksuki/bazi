#!/usr/bin/env python3
"""
A-13 专项抢救：月劫格「暴力扫描」
=================================
仅用基础定义「月支 == 日干劫财之禄」对 518k 做单一维度计数。
若 count > 0，说明当前 L1 附加约束过重或 A-13 无 manifest 导致零命中。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# 日干 → 劫财之禄（月支为劫财禄即月劫）
# 甲劫财乙禄卯、乙劫财甲禄寅、丙劫财丁禄午、丁劫财丙禄巳、
# 戊劫财己禄午、己劫财戊禄巳、庚劫财辛禄酉、辛劫财庚禄申、
# 壬劫财癸禄子、癸劫财壬禄亥
JIE_CAI_LU = {
    "甲": "卯", "乙": "寅", "丙": "午", "丁": "巳",
    "戊": "午", "己": "巳", "庚": "酉", "辛": "申",
    "壬": "子", "癸": "亥",
}


def _bazi_to_month_day(case: dict) -> tuple[str, str]:
    """从 case['bazi'] 取月支、日干。"""
    bazi = case.get("bazi")
    if not bazi or not isinstance(bazi, dict):
        return "", ""
    month_pillar = bazi.get("month")
    day_pillar = bazi.get("day")
    if isinstance(month_pillar, str) and len(month_pillar) >= 2:
        month_branch = month_pillar[1]
    elif isinstance(month_pillar, dict):
        month_branch = (month_pillar.get("zhi") or month_pillar.get("branch") or "")
    else:
        month_branch = ""
    if isinstance(day_pillar, str) and len(day_pillar) >= 1:
        day_master = day_pillar[0]
    elif isinstance(day_pillar, dict):
        day_master = (day_pillar.get("gan") or day_pillar.get("stem") or "")
    else:
        day_master = ""
    return month_branch, day_master


def is_yue_jie_basic(case: dict) -> bool:
    """仅判定：月支 == 日干劫财之禄（异性同五行）。"""
    month_branch, day_master = _bazi_to_month_day(case)
    if not day_master or not month_branch:
        return False
    lu = JIE_CAI_LU.get(day_master.strip())
    return lu == month_branch.strip()


def main():
    data_path = ROOT / "data_local" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        data_path = ROOT / "data" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        print("❌ 未找到 518k 数据，请放置 data_local/holographic_universe_518k.jsonl 或 data/ 下")
        sys.exit(1)

    count = 0
    total = 0
    no_bazi = 0
    sample_uids = []

    print("⏳ A-13 基础月劫（月支=劫财禄）暴力扫描...")
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total += 1
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not case.get("bazi"):
                no_bazi += 1
                continue
            if is_yue_jie_basic(case):
                count += 1
                if len(sample_uids) < 5:
                    sample_uids.append(case.get("uid") or case.get("id") or total)
            if total % 100000 == 0 and total > 0:
                print(f"   已扫描 {total:,} 行，当前基础月劫命中 {count:,}")

    print(f"\n✅ 扫描完成: 总行 {total:,}，无 bazi 跳过 {no_bazi:,}")
    print(f"   基础月劫命中数（仅 月支==日干劫财禄）: {count:,}")
    if sample_uids:
        print(f"   样例 uid: {sample_uids}")
    if count > 0:
        print("\n📌 结论: 基础定义有命中，当前 A-13 零命中来自 L1 附加约束过重或 A-13 无 manifest（回退 A-01 逻辑）。需松绑 L1 或补 A-13 manifest + 专用 L1。")
    else:
        print("\n📌 结论: 即使基础定义仍为 0，请检查 518k 中 bazi 结构（month/day 字段）是否与 _bazi_to_month_day 一致。")


if __name__ == "__main__":
    main()
