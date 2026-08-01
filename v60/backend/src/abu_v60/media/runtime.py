from __future__ import annotations

from functools import lru_cache
from typing import Any

from abu_v60.media.catalog import load_verified_media_catalog
from abu_v60.media.registry import load_verified_assets

RUNTIME_ASSET_BINDINGS = {
    "brand_logo": "brand.abuknows-v60.logo.transparent.v1",
    "grove_background": "dream.grove.clean.v1",
    "life_world_background": "dream.v60.life-world.clean.v1",
    "home_day_background": "experience.v108.home.day-background.v1",
    "home_night_background": "experience.v108.home.night-background.v1",
    "home_day_logo": "experience.v108.home.day-logo.v1",
    "home_night_logo": "experience.v108.home.night-logo.v1",
    "home_profile_leaf": "experience.v108.home.profile-leaf.v1",
    "home_lab_flower": "experience.v108.home.lab-flower.v1",
}
RUNTIME_CUE_BINDINGS = {
    "abu_idle": "cue.dream.abu-idle.v1",
    "abu_guide_left": "cue.dream.abu-guide-left.v1",
    "dodo_idle": "cue.mingli.dodo-idle.v1",
}


class RuntimeMediaError(ValueError):
    pass


def _public_url(runtime_path: str) -> str:
    prefix = "web/public/"
    if not runtime_path.startswith(prefix):
        raise RuntimeMediaError(f"asset_not_public_runtime_delivery:{runtime_path}")
    return f"/{runtime_path.removeprefix(prefix)}"


def _project_asset(asset: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_ref": str(asset["asset_ref"]),
        "asset_version": str(asset["asset_version"]),
        "url": _public_url(str(asset["runtime_path"])),
        "media_type": str(asset["media_type"]),
        "sha256": str(asset["sha256"]),
    }


@lru_cache(maxsize=1)
def runtime_media_manifest() -> dict[str, Any]:
    catalog = load_verified_media_catalog()
    assets = {str(asset["asset_ref"]): dict(asset) for asset in load_verified_assets()}
    items = {str(item["media_ref"]): item for item in catalog["items"]}
    cues = {str(cue["cue_ref"]): cue for cue in catalog["cue_bundles"]}

    runtime_assets: dict[str, dict[str, Any]] = {}
    for binding, asset_ref in RUNTIME_ASSET_BINDINGS.items():
        asset = assets.get(asset_ref)
        if asset is None:
            raise RuntimeMediaError(f"runtime_asset_binding_missing:{binding}")
        runtime_assets[binding] = _project_asset(asset)

    runtime_cues: dict[str, dict[str, Any]] = {}
    for binding, cue_ref in RUNTIME_CUE_BINDINGS.items():
        cue = cues.get(cue_ref)
        if cue is None or cue["status"] != "RUNTIME_REGISTERED":
            raise RuntimeMediaError(f"runtime_cue_not_admitted:{binding}")
        media = items.get(str(cue["visual_media_ref"]))
        if media is None or media["library_status"] != "RUNTIME_REGISTERED":
            raise RuntimeMediaError(f"runtime_cue_visual_not_admitted:{binding}")
        deliveries = {
            str(delivery["role"]): _project_asset(assets[str(delivery["asset_ref"])])
            for delivery in media["deliveries"]
        }
        required_roles = {"VP9_ALPHA_WEBM", "REDUCED_MOTION_POSTER"}
        if not required_roles.issubset(deliveries):
            raise RuntimeMediaError(f"runtime_cue_delivery_incomplete:{binding}")
        runtime_cues[binding] = {
            "cue_ref": cue_ref,
            "version": str(cue["version"]),
            "trigger": str(cue["trigger"]),
            "playback": str(media["runtime_contract"]["playback"]),
            "interruptible": bool(media["runtime_contract"].get("interruptible", False)),
            "deliveries": deliveries,
        }

    return {
        "registry_version": "v60.runtime-media-registry.003",
        "catalog_version": str(catalog["schema_version"]),
        "assets": runtime_assets,
        "cues": runtime_cues,
    }
