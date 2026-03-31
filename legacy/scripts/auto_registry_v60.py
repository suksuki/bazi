#!/usr/bin/env python3
"""
FDS SOP V6.0：全量自动化注册脚本
================================
一次性对第五梯队（A-41～A-50）执行：registry_generator 生成 manifest + SQLite + DuckDB 种子，
并更新 registry/qga_manifest.json 完成 QGA 并网。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    signed = ROOT / "config" / "patterns" / "sop_v60_A41_A50_signed.json"
    if not signed.exists():
        print(f"❌ 未找到签发文件: {signed}")
        sys.exit(1)

    # 1) 调用 registry_generator
    ret = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "registry_generator.py"), "--input", str(signed)],
        cwd=str(ROOT),
    )
    if ret.returncode != 0:
        print("❌ registry_generator 执行失败")
        sys.exit(ret.returncode)

    # 2) 更新 qga_manifest：追加 A-41～A-50（仅对签发文件中存在的 pattern）
    with open(signed, "r", encoding="utf-8") as f:
        data = json.load(f)
    patterns = data.get("patterns") or []
    pids = [str(p.get("pattern_id") or "").strip().upper() for p in patterns if p.get("pattern_id")]

    qga_path = ROOT / "registry" / "qga_manifest.json"
    if not qga_path.exists():
        print("❌ 未找到 registry/qga_manifest.json")
        sys.exit(1)
    with open(qga_path, "r", encoding="utf-8") as f:
        qga = json.load(f)
    entries = (qga.get("topics") or {}).get("holographic_pattern") or []
    existing = {e.get("pattern_id") for e in entries if e.get("pattern_id")}
    for pid in pids:
        if not pid or pid in existing:
            continue
        num = pid.replace("A-", "").replace("-", "").strip()
        entries.append({
            "pattern_id": pid,
            "topic": "holographic_pattern",
            "version": "6.0-SOP",
            "index_path": "",
            "manifest_ref": f"config/patterns/manifest_A{num}.json",
        })
        existing.add(pid)
    qga.setdefault("topics", {})["holographic_pattern"] = entries
    with open(qga_path, "w", encoding="utf-8") as f:
        json.dump(qga, f, ensure_ascii=False, indent=0)
    print(f"✅ QGA 并网: 已挂载 {len(pids)} 个格局 (A-41～A-50 中已签发者)。")
    sys.exit(0)


if __name__ == "__main__":
    main()
