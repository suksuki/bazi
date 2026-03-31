#!/usr/bin/env python3
"""
第 045 号指令：从 registry/config 下的 manifest 灌入 SQLite pattern_definitions。
TMM 与审计师签发的古典修正版一致（法典一致性锁）。
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
        p = ROOT / "registry" / "holographic_pattern" / pid / f"{pid}_manifest.json"
    return p if p.exists() else None


def seed_registry(registry_db_path: Path) -> int:
    """从 QGA 注册的 A-01~A-10 对应 manifest 写入 pattern_definitions。返回写入条数。"""
    qga_path = ROOT / "registry" / "qga_manifest.json"
    if not qga_path.exists():
        entries = [{"pattern_id": f"A-{i:02d}"} for i in range(1, 11)]
    else:
        with open(qga_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = (data.get("topics") or {}).get("holographic_pattern") or []

    registry = FDSRegistry(registry_db_path)
    count = 0
    for ent in entries:
        pid = ent.get("pattern_id")
        if not pid:
            continue
        path = _manifest_path(pid)
        if not path:
            print(f"⚠️ 未找到 manifest: {pid}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        meta = manifest.get("meta_info") or {}
        tmm = manifest.get("tensor_mapping_matrix") or {}
        ten_gods = tmm.get("ten_gods") or []
        weights = tmm.get("weights") or {}
        if not ten_gods or not weights:
            print(f"⚠️ {pid} 无 TMM，跳过")
            continue
        chinese_name = meta.get("chinese_name") or pid
        display_name = meta.get("display_name") or chinese_name
        category = meta.get("category") or ""
        source_ref = meta.get("source_ref") or ""
        registry.upsert_pattern(
            pattern_id=pid,
            chinese_name=chinese_name,
            tmm_ten_gods=ten_gods,
            tmm_weights=weights,
            display_name=display_name,
            category=category,
            sop_status="ENFORCED",
            source_ref=source_ref,
        )
        count += 1
        print(f"✅ {pid} {chinese_name}")
    registry.close()
    return count


def main():
    print("第 045 号：Manifest → SQLite pattern_definitions（法典一致性锁）")
    print(f"  输出: {REGISTRY_DB}")
    n = seed_registry(REGISTRY_DB)
    print(f"  写入 {n} 条格局定义")
    sys.exit(0)


if __name__ == "__main__":
    main()
