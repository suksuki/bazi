from __future__ import annotations

import json

from abu_v60.media import PROJECT_ROOT, load_verified_assets


def test_registry_assets_exist_and_match_hashes() -> None:
    assets = load_verified_assets()

    assert len(assets) == 30
    assert {asset["asset_ref"] for asset in assets} == {
        "dream.grove.clean.v1",
        "dream.v60.life-world.clean.v1",
        "brand.abuknows-v60.logo.transparent.v1",
        "abu.seated.idle.v1",
        "abu.seated.idle.poster.v1",
        "abu.seated.idle.webp.v1",
        "abu.v60.seated.poster.v1",
        "abu.v60.seated.idle.v1",
        "abu.v60.seated.idle.webp.v1",
        "abu.v60.seated.idle.poster.v1",
        "abu.v60.guide-left.v1",
        "abu.v60.guide-left.webp.v1",
        "abu.v60.guide-left.poster.v1",
        "dodo.v108.idle.v1",
        "dodo.v108.idle.webp.v1",
        "dodo.v108.idle.poster.v1",
        "abu.follow.walk.v1",
        "abu.follow.walk.webp.v1",
        "abu.follow.walk.poster.v1",
        "audio.morning-glints.opening.mp3.v1",
        "audio.morning-glints.opening.opus.v1",
        "dream.semantic-tree.base.v1",
        "dream.semantic-tree.leaf-world.v1",
        "dream.semantic-tree.leaf-structure.v1",
        "dream.semantic-tree.branch.v1",
        "dream.semantic-tree.energy.v1",
        "dream.semantic-tree.flower-bud.v1",
        "dream.semantic-tree.flower-open.v1",
        "dream.semantic-tree.fruit.v1",
        "dream.semantic-tree.foreground.v1",
    }


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
