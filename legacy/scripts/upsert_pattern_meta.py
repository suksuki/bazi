#!/usr/bin/env python3
"""
FDS SOP V5.5：格局立法完成后一键注库 — 将 Manifest 写入 SQLite，并可选触发 RAG 古典原典同步。
「没进库，就不算集成。」
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.database import REGISTRY_DB
from core.database.fds_registry import FDSRegistry


def _manifest_path(pattern_id: str) -> Path | None:
    pid = pattern_id.strip().upper()
    if pid == "A-01":
        p = ROOT / "config" / "patterns" / "manifest_A01.json"
    else:
        # 优先 registry，否则 config/patterns（SOP V5.7 镜像立法）
        p = ROOT / "registry" / "holographic_pattern" / pid / f"{pid}_manifest.json"
        if not p.exists():
            num = pid.replace("-", "")
            p = ROOT / "config" / "patterns" / f"manifest_{num}.json"
        if not p.exists():
            p = ROOT / "config" / "patterns" / f"manifest_A{pid.replace('A-', '')}.json"
    return p if p.exists() else None


def upsert_one(registry: FDSRegistry, pattern_id: str) -> bool:
    """将指定格局 Manifest 写入 SQLite；返回是否成功。支持 centroid_5d（SOP V5.7）。"""
    path = _manifest_path(pattern_id)
    if not path:
        print(f"⚠️ 未找到 manifest: {pattern_id}")
        return False
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    meta = manifest.get("meta_info") or {}
    tmm = manifest.get("tensor_mapping_matrix") or {}
    ten_gods = tmm.get("ten_gods") or []
    weights = tmm.get("weights") or {}
    if not ten_gods or not weights:
        print(f"⚠️ {pattern_id} 无 TMM，跳过")
        return False
    centroid_5d = manifest.get("centroid_5d")
    centroid_json = json.dumps(centroid_5d, ensure_ascii=False) if centroid_5d and len(centroid_5d) == 5 else None
    registry.upsert_pattern(
        pattern_id=pattern_id,
        chinese_name=meta.get("chinese_name") or pattern_id,
        tmm_ten_gods=ten_gods,
        tmm_weights=weights,
        display_name=meta.get("display_name"),
        category=meta.get("category"),
        sop_status="ENFORCED",
        source_ref=meta.get("source_ref"),
        centroid_json=centroid_json,
    )
    return True


def main():
    import argparse
    p = argparse.ArgumentParser(description="V5.5 一键注库：Manifest → SQLite，可选 RAG 同步")
    p.add_argument("--pattern", type=str, default=None, help="格局 ID，不传则处理 QGA 内全部")
    p.add_argument("--rag", action="store_true", help="注库后执行 RAG 古典原典灌入（ingest_rag_classical_canon.py）")
    args = p.parse_args()
    registry = FDSRegistry(REGISTRY_DB)
    if args.pattern:
        ids = [args.pattern.strip().upper()]
    else:
        qga = ROOT / "registry" / "qga_manifest.json"
        if not qga.exists():
            ids = [f"A-{i:02d}" for i in range(1, 11)]
        else:
            with open(qga, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries = (data.get("topics") or {}).get("holographic_pattern") or []
            ids = [e.get("pattern_id") for e in entries if e.get("pattern_id")]
    n = 0
    for pid in ids:
        if upsert_one(registry, pid):
            n += 1
            print(f"✅ {pid}")
    registry.close()
    print(f"  写入 {n} 条至 {REGISTRY_DB}")
    if args.rag:
        print("  执行 RAG 古典原典同步...")
        try:
            from core.rag_canon import ingest_canon_from_config
            m = ingest_canon_from_config()
            print(f"  RAG 灌入 {m} 条")
        except Exception as e:
            print(f"  ⚠️ RAG 灌入失败: {e}")
    else:
        print("  提示：加 --rag 可同时执行 RAG 古典原典灌入（V5.5 建议封卷前必跑）")
    sys.exit(0)


if __name__ == "__main__":
    main()
