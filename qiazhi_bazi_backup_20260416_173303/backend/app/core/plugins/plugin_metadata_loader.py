"""从各插件 `skill_manifest.json` 的 `plugin_manifest` 块合并卡片元数据（裁决五维子集）。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

_MANIFEST_FILES: Dict[str, Path] = {
    "classical.blind_school.v1": Path(__file__).resolve().parents[2] / "plugins" / "blind_school" / "skill_manifest.json",
    "base.chronos": Path(__file__).resolve().parents[2] / "plugins" / "chronos" / "skill_manifest.json",
    "classical.wangshuai.v1": Path(__file__).resolve().parents[2] / "plugins" / "wangshuai" / "skill_manifest.json",
    "modern.wealth_risk.v1": Path(__file__).resolve().parents[2] / "plugins" / "modern_wealth_risk" / "skill_manifest.json",
}

_OPERATOR_CARD_PATH = (
    Path(__file__).resolve().parents[2] / "plugins" / "base_physics" / "manifests" / "l1_operator_card_profiles.json"
)


@lru_cache(maxsize=1)
def _operator_card_profiles() -> Dict[str, Any]:
    if not _OPERATOR_CARD_PATH.is_file():
        return {}
    data = json.loads(_OPERATOR_CARD_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def plugin_manifest_for_operator_card(operator_plugin_id: str) -> Dict[str, Any]:
    prof = _operator_card_profiles().get(operator_plugin_id)
    return dict(prof) if isinstance(prof, dict) else {}


def _read_manifest(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def plugin_manifest_for_registry_plugin(plugin_id: str) -> Dict[str, Any]:
    path = _MANIFEST_FILES.get(str(plugin_id))
    if not path:
        return {}
    root = _read_manifest(path)
    block = root.get("plugin_manifest")
    return dict(block) if isinstance(block, dict) else {}


def merge_plugin_manifest_into_metadata(metadata: Dict[str, Any], plugin_id: str) -> None:
    block = plugin_manifest_for_registry_plugin(plugin_id)
    for key in (
        "display_name",
        "use_case",
        "detailed_description",
        "physical_impact",
        "governance_notes",
        "recommendation_logic",
    ):
        if key in block and block[key] is not None:
            metadata[key] = block[key]
