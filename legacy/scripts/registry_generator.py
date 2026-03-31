#!/usr/bin/env python3
"""
FDS SOP V5.7 工业化版：镜像立法注册器
======================================
输入：审计师签发的 JSON 块（含 pattern_id, chinese_name, classical_anchor, centroid_5d, l1_constraint）。
输出：config/patterns/manifest_{id}.json、SQLite pattern_definitions、DuckDB 种子点（TMM_SEED）。
严禁改动审计师给出的 TMM（centroid_5d）数值。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 标准十神顺序（与 V4/TMM 一致，仅用于满足 schema，投影不用于化气/魁罡/金神）
TEN_GODS_ORDER = ["ZG", "PG", "ZR", "PR", "ZS", "PS", "ZC", "PC", "ZB", "PB"]


def _minimal_tmm() -> dict:
    """满足 pattern_definitions 与 manifest 结构的最小 TMM（零权，质心由 centroid_5d 单独存）。"""
    return {
        "ten_gods": TEN_GODS_ORDER,
        "weights": {g: [0.0, 0.0, 0.0, 0.0, 0.0] for g in TEN_GODS_ORDER},
    }


def build_manifest(entry: dict) -> dict:
    """从签发条目生成单格局 manifest（与 upsert_pattern_meta 可读格式兼容）。"""
    pid = (entry.get("pattern_id") or "").strip().upper()
    name = entry.get("chinese_name") or pid
    anchor = entry.get("classical_anchor") or ""
    centroid = entry.get("centroid_5d")
    l1 = entry.get("l1_constraint") or ""
    if not centroid or len(centroid) != 5:
        raise ValueError(f"{pid}: centroid_5d 必须为长度 5 的数组")
    tmm = _minimal_tmm()
    return {
        "pattern_id": pid,
        "version": "SOP_V5.7",
        "meta_info": {
            "chinese_name": name,
            "display_name": name,
            "category": "化气/魁罡/金神",
            "source_ref": anchor,
            "l1_constraint": l1,
        },
        "tensor_mapping_matrix": tmm,
        "centroid_5d": centroid,
    }


def write_manifest(manifest: dict, out_dir: Path) -> Path:
    """写入 config/patterns/manifest_A14.json 等（与 upsert_pattern_meta 查找一致）。"""
    pid = (manifest.get("pattern_id") or "UNKNOWN").strip().upper()
    num = pid.replace("A-", "").replace("-", "")
    path = out_dir / f"manifest_A{num}.json"
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return path


def upsert_sqlite(registry, manifest: dict) -> None:
    """将 manifest 写入 SQLite pattern_definitions（含 centroid_json）。"""
    pid = (manifest.get("pattern_id") or "").strip().upper()
    meta = manifest.get("meta_info") or {}
    tmm = manifest.get("tensor_mapping_matrix") or _minimal_tmm()
    ten_gods = tmm.get("ten_gods") or TEN_GODS_ORDER
    weights = tmm.get("weights") or {g: [0.0] * 5 for g in ten_gods}
    centroid = manifest.get("centroid_5d")
    centroid_json = json.dumps(centroid, ensure_ascii=False) if centroid else None
    registry.upsert_pattern(
        pattern_id=pid,
        chinese_name=meta.get("chinese_name") or pid,
        tmm_ten_gods=ten_gods,
        tmm_weights=weights,
        display_name=meta.get("display_name") or meta.get("chinese_name"),
        category=meta.get("category") or "",
        sop_status="ENFORCED",
        source_ref=meta.get("source_ref") or "",
        centroid_json=centroid_json,
    )


def seed_duckdb(physics, pattern_id: str, centroid_5d: list) -> None:
    """向 DuckDB pattern_points 插入一条种子点，使 get_centroid 返回签发质心。"""
    import numpy as np
    pid = pattern_id.strip().upper()
    arr = np.array([[float(centroid_5d[0]), float(centroid_5d[1]), float(centroid_5d[2]), float(centroid_5d[3]), float(centroid_5d[4])]], dtype=np.float64)
    physics.insert_points(pid, ["TMM_SEED"], [0], arr, replace=True, commit=True)


def main():
    import argparse
    p = argparse.ArgumentParser(description="SOP V5.7 镜像立法：签发 JSON → manifest + SQLite + DuckDB 种子")
    p.add_argument("--input", type=Path, default=None, help="签发 JSON 文件；默认 config/patterns/sop_v57_A14_A20_signed.json")
    p.add_argument("--dry-run", action="store_true", help="仅生成 manifest 文件，不写 SQLite/DuckDB")
    args = p.parse_args()

    input_path = args.input or (ROOT / "config" / "patterns" / "sop_v57_A14_A20_signed.json")
    input_path = input_path if input_path.is_absolute() else (ROOT / input_path)
    if not input_path.exists():
        print(f"❌ 未找到签发文件: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = (data.get("patterns") or []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    if not entries:
        print("❌ 签发文件中无 patterns 数组")
        sys.exit(1)

    out_dir = ROOT / "config" / "patterns"
    generated = []
    for entry in entries:
        pid = (entry.get("pattern_id") or "").strip().upper()
        try:
            manifest = build_manifest(entry)
            path = write_manifest(manifest, out_dir)
            generated.append((pid, manifest, path))
            print(f"✅ {pid} manifest → {path.name}")
        except Exception as e:
            print(f"⚠️ {pid} 跳过: {e}")

    if args.dry_run:
        print("  [dry-run] 未写入 SQLite/DuckDB")
        sys.exit(0)

    from core.database import REGISTRY_DB, PHYSICS_DB
    from core.database.fds_registry import FDSRegistry
    from core.database.fds_physics import FDSPhysics

    registry = FDSRegistry(REGISTRY_DB)
    for pid, manifest, _ in generated:
        try:
            upsert_sqlite(registry, manifest)
            print(f"✅ {pid} SQLite 已写入")
        except Exception as e:
            print(f"⚠️ {pid} SQLite 失败: {e}")
    registry.close()

    physics = FDSPhysics(PHYSICS_DB)
    for pid, manifest, _ in generated:
        centroid = manifest.get("centroid_5d")
        if not centroid:
            continue
        try:
            seed_duckdb(physics, pid, centroid)
            print(f"✅ {pid} DuckDB 种子点已写入")
        except Exception as e:
            print(f"⚠️ {pid} DuckDB 失败: {e}")
    physics.close()

    print(f"  完成 {len(generated)} 条镜像入库（SOP V5.7）。")
    sys.exit(0)


if __name__ == "__main__":
    main()
