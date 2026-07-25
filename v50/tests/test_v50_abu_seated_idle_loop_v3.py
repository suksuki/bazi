from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v12-actor-pass"
ACTION_ROOT = ASSET_ROOT / "abu-01-seated-idle-loop-v3"
ACTION_ID = "abu_01_seated_idle_loop_v3"
SOURCE_SHA256 = "d5b3c64ad82aed464a201cd9e90e879e8f2cbe6abfe4fd78c08c0e8359697196"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_seated_idle_v3_is_library_ready_without_default_change() -> None:
    library = _json(ASSET_ROOT / "library.json")
    actions = {item["action_id"]: item for item in library["actions"]}
    action = actions[ACTION_ID]

    assert library["governance"]["default_action_id"] == "abu_dream_standard_cycle_v1"
    assert action["catalog_id"] == "ABU_01_SEATED_IDLE_LOOP_V3"
    assert action["status"] == "production"
    assert action["source_status"] == "SOURCE_APPROVED"
    assert action["library_status"] == "LIBRARY_READY"
    assert action["loop_mode"] == "loop"


def test_source_and_postprocess_are_traceable() -> None:
    inventory = _json(ASSET_ROOT / "video-inventory.json")
    source = next(
        item
        for item in inventory["sources"]
        if item["source_id"] == "abu_01_seated_idle_loop_v3_source"
    )
    archive = ROOT / source["archived_source"]
    manifest = _json(ACTION_ROOT / "manifest.json")

    assert source["sha256"] == SOURCE_SHA256
    assert _sha256(archive) == SOURCE_SHA256
    assert manifest["source"]["sha256"] == SOURCE_SHA256
    assert manifest["transparent_background"] is True
    assert manifest["audio_removed"] is True
    assert manifest["watermark_removed"] is True
    assert manifest["fixed_character_scale"] is True
    assert manifest["fixed_bottom_anchor"] is True
    assert manifest["quality_gate"]["first_last_loop"] == "PASS_AFTER_POSTPROCESS"
    assert (
        manifest["quality_gate"]["library_ready"]
        == "PASS_OWNER_APPROVED_2026_07_23"
    )
    assert manifest["boundaries"]["runtime_default_changed"] is False
    assert manifest["boundaries"]["runtime_registered"] is True


def test_png_sequence_is_transparent_anchored_and_exactly_loop_closed() -> None:
    manifest = _json(ACTION_ROOT / "manifest.json")
    frames = sorted((ACTION_ROOT / "frames").glob("frame-*.png"))

    assert len(frames) == manifest["frame_count"] == 240
    assert _sha256(frames[0]) == _sha256(frames[-1])
    assert manifest["loop_validation"]["first_last_rgba_mae"] == 0
    assert manifest["loop_validation"]["first_last_png_identical"] is True
    assert manifest["stabilization"]["output_bottom_anchor_range"] == [704, 704]

    sample = Image.open(frames[120]).convert("RGBA")
    assert sample.size == (960, 720)
    assert sample.getchannel("A").getextrema() == (0, 255)


def test_web_delivery_has_alpha_metadata_and_no_audio_stream() -> None:
    manifest = _json(ACTION_ROOT / "manifest.json")
    webm = ACTION_ROOT / manifest["video"]
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type:stream_tags=ALPHA_MODE",
            "-of",
            "json",
            str(webm),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(probe.stdout)
    streams = payload["streams"]

    assert [stream["codec_type"] for stream in streams] == ["video"]
    assert streams[0]["tags"]["ALPHA_MODE"] == "1"
    assert _sha256(webm) == manifest["delivery_sha256"]["webm"]
    assert Image.open(ACTION_ROOT / manifest["animation"]).n_frames == 240


def test_media_registry_hashes_include_library_ready_action_without_defaulting_it() -> None:
    media = _json(ROOT / "config/media_asset_registry_v1.json")["abu_motion"]
    runtime = (ASSET_ROOT.parent / "motion-registry.js").read_text(encoding="utf-8")

    assert media["default_action_id"] == "abu_dream_standard_cycle_v1"
    assert 'seated_idle_loop_v3: Object.freeze({' in runtime
    assert 'actionId: "abu_01_seated_idle_loop_v3"' in runtime
    assert 'idle: "dream_standard_cycle"' in runtime
    assert media["sha256"] == _sha256(ROOT / media["registry"])
    assert media["library_sha256"] == _sha256(ROOT / media["library"])
    assert media["source_inventory_sha256"] == _sha256(
        ROOT / media["source_inventory"]
    )
