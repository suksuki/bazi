"""Bridge 层：按需从 legacy 抽取与映射数据。"""
from __future__ import annotations

from typing import Any, Dict, List

from core.config import config
from qiazhi_core.schemas.protocol import BaziMetadata, BasicInfo, EnergyProfile


def legacy_config_version() -> str:
    return getattr(config, "version", "unknown")


def get_vault_params_snapshot() -> Dict[str, Any]:
    v = config.vault
    return {
        "threshold": v.threshold,
        "sealed_damping": v.sealed_damping,
        "open_bonus": v.open_bonus,
        "collapse_penalty": v.collapse_penalty,
    }


def build_metadata_from_legacy_payload(payload: Dict[str, Any]) -> BaziMetadata:
    """将 legacy 侧常见数据结构映射为 BaziMetadata（MVP 映射版）。"""
    basic = BasicInfo(
        pillars=payload.get("pillars") or {},
        gender=payload.get("gender"),
        longitude=payload.get("longitude"),
        latitude=payload.get("latitude"),
    )
    energy = EnergyProfile(
        labels=(payload.get("energy_labels") or {}),
        raw_scores=(payload.get("energy_scores") or {}),
    )
    return BaziMetadata(
        basic_info=basic,
        energy_profile=energy,
        clash_combinations=(payload.get("clash_combinations") or []),
        semantic_refs=["@legacy.payload"],
    )
