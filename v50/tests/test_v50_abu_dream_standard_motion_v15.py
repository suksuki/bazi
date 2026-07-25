from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v12-actor-pass"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_owner_approved_dream_abu_is_the_single_default_action() -> None:
    library = _json(ASSET_ROOT / "library.json")
    actions = {item["action_id"]: item for item in library["actions"]}

    assert library["governance"]["default_action_id"] == "abu_dream_standard_cycle_v1"
    assert library["governance"]["default_character_source_id"] == "dream_standard_cute_green"
    assert actions["abu_dream_standard_cycle_v1"]["status"] == "production"
    assert actions["abu_dream_standard_cycle_v1"]["product_role"] == "default_companion_presence"
    assert actions["abu_quiet_sit_reaction_v1"]["status"] == "retired"
    assert actions["abu_quiet_sit_reaction_v1"]["superseded_by"] == "abu_dream_standard_cycle_v1"


def test_green_screen_source_and_three_transparent_derivatives_are_traceable() -> None:
    inventory = _json(ASSET_ROOT / "video-inventory.json")
    source = next(item for item in inventory["sources"] if item["source_id"] == "dream_standard_cute_green")
    archived = ROOT / source["archived_source"]

    assert source["sha256"] == "0e70d5e6dfe3dd929f6c3f961f4d532c960b709ff3d94e701595e2b221ecaf45"
    assert _sha256(archived) == source["sha256"]
    assert source["background"] == "green_screen"

    expected_frames = {
        "dream-standard-cycle": 150,
        "dream-seated-observe": 94,
        "dream-stand-and-return": 56,
    }
    for directory, frame_count in expected_frames.items():
        manifest = _json(ASSET_ROOT / directory / "manifest.json")
        assert manifest["status"] == "production"
        assert manifest["transparent_background"] is True
        assert manifest["watermark_removed"] is True
        assert manifest["frame_count"] == frame_count
        assert manifest["character_style"]["status"] == "owner_approved_default"
        assert manifest["actor_contract"]["safe_crop"] == "full_body"
        webp = ASSET_ROOT / directory / manifest["animation"]
        webm = ASSET_ROOT / directory / manifest["video"]
        poster = ASSET_ROOT / directory / manifest["poster"]
        assert Image.open(webp).n_frames == frame_count
        assert Image.open(poster).convert("RGBA").getchannel("A").getextrema() == (0, 255)
        assert webm.read_bytes()[:4] == b"\x1aE\xdf\xa3"


def test_default_runtime_and_media_registry_reference_the_promoted_action() -> None:
    runtime = (ASSET_ROOT.parent / "motion-registry.js").read_text(encoding="utf-8")
    media = _json(ROOT / "config/media_asset_registry_v1.json")["abu_motion"]

    assert 'idle: "dream_standard_cycle"' in runtime
    assert 'quiet_companion: "dream_seated_observe"' in runtime
    assert 'confirming: "dream_stand_and_return"' in runtime
    assert media["default_action_id"] == "abu_dream_standard_cycle_v1"
    assert media["sha256"] == _sha256(ROOT / media["registry"])
    assert media["library_sha256"] == _sha256(ROOT / media["library"])
    assert media["source_inventory_sha256"] == _sha256(ROOT / media["source_inventory"])
