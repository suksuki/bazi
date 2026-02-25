#!/usr/bin/env python3
"""
FDS 格局扫描器（SOP V4.0 海选 + 全量索引）
==========================================
按 SOP V4.0 预处理与 Step 5.5：对指定格局执行「海选」并构建全量 .npz 点阵索引。
支持 A-01、A-02；可直接跳过少量样本阶段，利用全量 518k 跑出索引。

用法:
  python scripts/fds_pattern_scanner.py --target A-02
  python scripts/fds_pattern_scanner.py --target A-02 --census   # 先跑 SOP 海选再建索引
  python scripts/fds_pattern_scanner.py --target A-01 --data ./data/holographic_universe_518k.jsonl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def resolve_manifest(target: str) -> Path:
    t = target.strip().upper()
    if t != "A-01":
        p = ROOT / "registry" / "holographic_pattern" / t / f"{t}_manifest.json"
        if p.exists():
            return p
    return ROOT / "config" / "patterns" / "manifest_A01.json"


def run_census(pattern_id: str) -> bool:
    """运行 SOP 海选（KnowledgeDrivenCensus），返回是否成功。"""
    try:
        from core.logic_compiler import get_knowledge_census
        engine = get_knowledge_census()
        res = engine.request_census(pattern_id, limit=None, include_tensor=True)
        print(f"✅ 海选完成: {res['matched_count']:,} / {res['total_scanned']:,} (丰度: {res['abundance']:.6f})")
        return True
    except Exception as e:
        print(f"⚠️ 海选跳过或失败: {e}")
        return False


def run_full_index(pattern_id: str, data_path: Path | None, out_dir: Path, limit: int | None) -> bool:
    """运行全量索引构建，返回是否成功。"""
    try:
        from build_a01_full_index import (
            resolve_manifest_for_pattern,
            build_full_index,
            ROOT as _ROOT,
        )
        manifest_path = resolve_manifest_for_pattern(pattern_id)
        if not manifest_path.exists():
            print(f"❌ 未找到 manifest: {manifest_path}")
            return False
        data = data_path or _ROOT / "data" / "holographic_universe_518k.jsonl"
        if not data.exists():
            data = _ROOT / "data_local" / "holographic_universe_518k.jsonl"
        if not data.exists():
            print(f"❌ 未找到数据: {data}")
            return False
        n, _, _ = build_full_index(data, manifest_path, out_dir, limit=limit, pattern_id=pattern_id)
        return n >= 0
    except Exception as e:
        print(f"❌ 全量索引构建失败: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="FDS 格局扫描器（SOP V4.0）")
    parser.add_argument("--target", type=str, required=True, help="格局 ID，如 A-01、A-02")
    parser.add_argument("--census", action="store_true", help="先执行 SOP 海选再建全量索引")
    parser.add_argument("--data", type=Path, default=None, help="518k jsonl 路径")
    parser.add_argument("--out", type=Path, default=None, help="输出目录，默认 data_local")
    parser.add_argument("--limit", type=int, default=None, help="全量索引最多样本数（测试用）")
    args = parser.parse_args()

    pattern_id = args.target.strip().upper()
    manifest_path = resolve_manifest(pattern_id)
    if not manifest_path.exists():
        print(f"❌ 未找到格局 manifest: {manifest_path}")
        sys.exit(1)
    print(f"📜 法理已锚定: {manifest_path}")

    if args.census:
        print("--- Phase I: SOP 海选 ---")
        run_census(pattern_id)

    print("--- Phase II: 全量索引构建 ---")
    out_dir = args.out or ROOT / "data_local"
    run_full_index(pattern_id, args.data, out_dir, args.limit)
    labels = {"A-01": "正官格", "A-02": "七杀格", "A-03": "偏财格", "A-04": "正财格", "A-05": "枭神格", "A-06": "食神格", "A-07": "伤官格", "A-08": "正印格", "A-09": "建禄格", "A-10": "阳刃格", "A-11": "从财格", "A-12": "从杀格", "A-13": "专旺格"}
    name = labels.get(pattern_id, pattern_id)
    print(f"🎯 {pattern_id} {name} 格局扫描完成。")


if __name__ == "__main__":
    main()
