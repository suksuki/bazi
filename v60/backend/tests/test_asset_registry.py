from __future__ import annotations

import json

from abu_v60.media import PROJECT_ROOT, load_verified_assets
from abu_v60.system_manifest import ASSET_REGISTRY_VERSION


def test_registry_assets_exist_and_match_hashes() -> None:
    assets = load_verified_assets()

    assert len(assets) == 26
    assert {asset["asset_ref"] for asset in assets} == {
        "experience.v60.login-life-tree-background.v1",
        "brand.abuknows-v60.logo.transparent.v1",
        "abu.v60.seated.poster.v1",
        "abu.v60.seated.idle.v1",
        "abu.v60.seated.idle.webp.v1",
        "abu.v60.seated.idle.poster.v1",
        "dodo.v108.idle.v1",
        "dodo.v108.idle.webp.v1",
        "dodo.v108.idle.poster.v1",
        "experience.v108.home.day-background.v1",
        "experience.v108.home.night-background.v1",
        "experience.v108.home.day-logo.v1",
        "experience.v108.home.night-logo.v1",
        "experience.v108.home.profile-leaf.v1",
        "experience.v108.home.lab-flower.v1",
        "experience.v108.mingli-branch.day-video.v1",
        "experience.v108.mingli-branch.day-start.v1",
        "experience.v108.mingli-branch.day-poster.v1",
        "experience.v108.mingli-branch.night-video.v1",
        "experience.v108.mingli-branch.night-start.v1",
        "experience.v108.mingli-branch.night-poster.v1",
        "experience.v128.mingli-branch.day-video.v1",
        "experience.v128.mingli-branch.day-start.v1",
        "experience.v128.mingli-branch.day-poster.v1",
        "experience.v131.mingli-lab.day-background.v1",
        "experience.v131.mingli-lab.night-background.v1",
    }


def test_registry_schema_matches_runtime_manifest() -> None:
    registry_path = PROJECT_ROOT / "assets" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    assert registry["schema_version"] == ASSET_REGISTRY_VERSION


def test_registry_never_reads_v50_at_runtime() -> None:
    registry_path = PROJECT_ROOT / "assets" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    assert registry["policy"]["runtime_reads_v50_paths"] is False
    assert all(not str(asset["runtime_path"]).startswith("v50/") for asset in registry["assets"])


def test_web_runtime_does_not_hardcode_registered_asset_paths() -> None:
    web_source = PROJECT_ROOT / "web" / "src"
    offenders: list[str] = []
    for path in web_source.rglob("*"):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        if '"/assets/' in path.read_text(encoding="utf-8"):
            offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert offenders == []
