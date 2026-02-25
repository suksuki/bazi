#!/usr/bin/env python3
"""
FDS SOP V4.1 Step 5.6：古典知识库（HKB）语义对齐
==================================================
将 manifest 中的 semantic_core_dimensions 同步到 config/hkb/hkb_params.json，
使 ai_engine 可调用结构化 HKB；含古典原文引用（古籍印证）。

用法:
  python scripts/sync_pattern_hkb.py                    # 同步所有已存在 manifest 的格局
  python scripts/sync_pattern_hkb.py --pattern_id A-03
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
HKB_PATH = ROOT / "config" / "hkb" / "hkb_params.json"

# 格局 → 古籍引用（审计师/分析师提供，可扩展）
CLASSICAL_REFS: Dict[str, Dict[str, str]] = {
    "A-02": {
        "A_stress_transform": "《渊海子平》：「杀重身轻，终身有损。」「杀印相生，威镇边疆。」",
        "B_order_rebuild": "《三命通会》：「七杀有制，聪明伶俐。」",
        "C_eruption_kinetic": "《子平真诠》：「杀官混杂，贫夭；制伏得宜，暴发。」",
    },
    "A-03": {
        "A_resource_expansion": "《渊海子平》：「偏财乃众人之财，宜露不宜藏。」「偏财身强发福。」",
        "B_speculation_kinetic": "《三命通会》：「偏财喜动，动则生财。」",
        "C_wealth_retention": "《子平真诠》：「财宜藏，官宜露。」偏财格需身强方能留财。",
    },
    "A-04": {
        "A_stability": "《渊海子平》：「正财乃己身之财，宜藏不宜露。」稳健积累。",
        "B_pragmatism": "《三命通会》：「正财主务实、守成。」",
        "C_risk_aversion": "《子平真诠》：「正财格不喜杀旺，杀旺则破财。」应力宜低。",
    },
    "A-05": {
        "A_intuition": "《渊海子平》：「偏印主灵悟、直觉。」",
        "B_esoteric": "《三命通会》：「偏印多涉偏门、玄学。」",
        "C_solitude": "《子平真诠》：「偏印夺食，喜静恶动。」孤独研究。",
    },
}


def load_hkb() -> Dict[str, Any]:
    if not HKB_PATH.exists():
        return {"schema_version": "1.0", "hkb": {}}
    with open(HKB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_hkb(data: Dict[str, Any]) -> None:
    HKB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HKB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def manifest_semantic_to_hkb_core(
    pattern_id: str,
    semantic_core_dimensions: Dict[str, Any],
    classical_refs: Dict[str, str],
) -> Dict[str, Any]:
    """将 manifest 的 semantic_core_dimensions 转为 HKB 可用的 semantic_core 结构（含古典引用）。"""
    core: Dict[str, Any] = {}
    for key, d in semantic_core_dimensions.items():
        if not isinstance(d, dict):
            continue
        name = d.get("name", key)
        mapping = d.get("physical_mapping", "")
        classical = d.get("classical_by_gemini", d.get("definition", ""))
        ref = classical_refs.get(key, "")
        core[key] = {
            "name": name,
            "physical_mapping": mapping,
            "definition": classical,
            "classical_ref": ref,
        }
    return core


def sync_pattern(pattern_id: str, manifest_path: Path) -> bool:
    if not manifest_path.exists():
        return False
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    dimensions = manifest.get("semantic_core_dimensions") or {}
    if not dimensions:
        return False
    refs = CLASSICAL_REFS.get(pattern_id, {})
    core = manifest_semantic_to_hkb_core(pattern_id, dimensions, refs)
    if not core:
        return False
    hkb = load_hkb()
    hkb.setdefault("hkb", {})
    key = f"{pattern_id.lower().replace('-', '')}_semantic_core"
    hkb["hkb"][key] = core
    save_hkb(hkb)
    return True


def main():
    parser = argparse.ArgumentParser(description="SOP V4.1 Step 5.6：格局 HKB 语义同步")
    parser.add_argument("--pattern_id", type=str, default=None, help="仅同步指定格局；缺省则同步 A-02、A-03")
    parser.add_argument("--hkb_path", type=Path, default=None, help="HKB 输出路径，默认 config/hkb/hkb_params.json")
    args = parser.parse_args()
    global HKB_PATH
    if args.hkb_path is not None:
        HKB_PATH = args.hkb_path

    patterns = [args.pattern_id] if args.pattern_id else ["A-02", "A-03", "A-04", "A-05"]
    synced = 0
    for pid in patterns:
        pid = pid.strip().upper()
        manifest_path = ROOT / "registry" / "holographic_pattern" / pid / f"{pid}_manifest.json"
        if sync_pattern(pid, manifest_path):
            print(f"  ✅ {pid} 语义已同步至 HKB")
            synced += 1
        else:
            if manifest_path.exists():
                print(f"  ⚠️ {pid} manifest 无 semantic_core_dimensions，跳过")
            else:
                print(f"  ⚠️ {pid} manifest 不存在，跳过")
    print(f"🎯 HKB 同步完成：{synced} 个格局 → {HKB_PATH}")


if __name__ == "__main__":
    main()
