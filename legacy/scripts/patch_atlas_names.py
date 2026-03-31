#!/usr/bin/env python3
"""
SOP V6.4 — 静态 Atlas 名片补全
==============================
遍历 static_atlas.json，若 chinese_name 仅含编号则从 qga_manifest / manifest 解析真名并永久固化回 atlas。
审计标准：API 返回中不出现 {"id": "A-xx", "name": "A-xx"} 的冗余。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATLAS_PATH = ROOT / "core" / "engine" / "static_atlas.json"
QGA_PATH = ROOT / "registry" / "qga_manifest.json"


def _load_qga_name_map() -> dict[str, str]:
    """从 qga_manifest 的 holographic_pattern 构建 pattern_id -> name_cn（仅当 name_cn 非编号时）."""
    out = {}
    if not QGA_PATH.exists():
        return out
    try:
        with open(QGA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return out
    entries = (data.get("topics") or {}).get("holographic_pattern") or []
    for e in entries:
        pid = (e.get("pattern_id") or "").strip()
        name = (e.get("name_cn") or "").strip()
        if pid and name and name != pid:
            out[pid] = name
    return out


def _name_from_manifest(pid: str, manifest_ref: str) -> str | None:
    """从 manifest 文件读取 meta_info.chinese_name。manifest_ref 相对项目根。"""
    path = ROOT / manifest_ref.replace("\\", "/").lstrip("/")
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    meta = data.get("meta_info") or {}
    name = (meta.get("chinese_name") or meta.get("display_name") or meta.get("name") or "").strip()
    return name if name and name != pid else None


def main() -> None:
    if not ATLAS_PATH.exists():
        print(f"❌ 未找到 {ATLAS_PATH}")
        sys.exit(1)

    with open(ATLAS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    patterns = data.get("patterns") or []
    if not patterns:
        print("⚠️ atlas 无 patterns 数组")
        sys.exit(0)

    qga_names = _load_qga_name_map()
    # 从 qga 取 manifest_ref 以便回退到 manifest 文件
    qga_entries = {}
    if QGA_PATH.exists():
        try:
            with open(QGA_PATH, "r", encoding="utf-8") as f:
                qga_data = json.load(f)
            for e in (qga_data.get("topics") or {}).get("holographic_pattern") or []:
                pid = (e.get("pattern_id") or "").strip()
                if pid:
                    qga_entries[pid] = e
        except Exception:
            pass

    updated = 0
    for p in patterns:
        pid = (p.get("pattern_id") or "").strip()
        if not pid:
            continue
        current = (p.get("chinese_name") or "").strip()
        if current and current != pid:
            continue

        resolved = None
        if pid in qga_names:
            resolved = qga_names[pid]
        if not resolved and pid in qga_entries:
            ref = (qga_entries[pid].get("manifest_ref") or "").strip()
            if ref:
                resolved = _name_from_manifest(pid, ref)
        if not resolved:
            # 无 manifest_ref 时尝试默认路径
            ref = f"registry/holographic_pattern/{pid}/{pid}_manifest.json"
            resolved = _name_from_manifest(pid, ref)
        if not resolved:
            num = pid.replace("A-", "").replace("-", "").strip()
            resolved = _name_from_manifest(pid, f"config/patterns/manifest_A{num}.json")

        if resolved and resolved != pid:
            p["chinese_name"] = resolved
            updated += 1
            print(f"   {pid}: {current or '(空)'} → {resolved}")

    if updated == 0:
        print("✅ 无需补全：所有格局 chinese_name 已非纯编号（或无可解析来源）")
        return

    with open(ATLAS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已固化 {updated} 个格局中文名至 {ATLAS_PATH}")


if __name__ == "__main__":
    main()
