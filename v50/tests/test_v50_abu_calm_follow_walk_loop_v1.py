from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v12-actor-pass"
ACTION_ROOT = ASSET_ROOT / "abu-02-calm-follow-walk-loop-v1"
ACTION_ID = "abu_02_calm_follow_walk_loop_v1"
SOURCE_SHA256 = "993c6d111903f7f995b23c6f5a0653f9f893b21cb678d1cea60b9475f6fbdfa8"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_calm_follow_walk_is_owner_approved_and_runtime_registered() -> None:
    library = _json(ASSET_ROOT / "library.json")
    actions = {item["action_id"]: item for item in library["actions"]}
    action = actions[ACTION_ID]

    assert library["governance"]["default_action_id"] == "abu_dream_standard_cycle_v1"
    assert action["catalog_id"] == "ABU_02_CALM_FOLLOW_WALK_LOOP_V1"
    assert action["status"] == "production"
    assert action["source_status"] == "SOURCE_APPROVED"
    assert (
        action["library_status"]
        == "LIBRARY_READY"
    )
    assert action["semantic_state"] == "LOCOMOTION_FOLLOW"
    assert action["action_type"] == "LOOP"
    assert action["runtime_registered"] is True
    assert ACTION_ID not in {
        item["action_id"] for item in library.get("review_candidates", [])
    }


def test_source_loop_boundary_and_postprocess_are_traceable() -> None:
    inventory = _json(ASSET_ROOT / "video-inventory.json")
    source = next(
        item
        for item in inventory["sources"]
        if item["source_id"] == "abu_02_calm_follow_walk_loop_v1_source"
    )
    archive = ROOT / source["archived_source"]
    manifest = _json(ACTION_ROOT / "manifest.json")

    assert source["sha256"] == SOURCE_SHA256
    assert _sha256(archive) == SOURCE_SHA256
    assert manifest["source"]["sha256"] == SOURCE_SHA256
    assert manifest["selected_loop"] == {
        "source_frame_start_inclusive": 6,
        "source_frame_end_exclusive": 60,
        "matched_endpoint_frame": 60,
        "source_time_seconds": [0.25, 2.5],
        "selection_basis": (
            "best alpha-phase match with natural seam continuity "
            "inside the approved first gait cycle"
        ),
    }
    assert manifest["transparent_background"] is True
    assert manifest["audio_removed"] is True
    assert manifest["watermark_removed"] is True
    assert manifest["natural_vertical_bob_preserved"] is True


def test_png_masters_are_transparent_anchored_and_naturally_looped() -> None:
    manifest = _json(ACTION_ROOT / "manifest.json")
    frames = sorted((ACTION_ROOT / "frames").glob("frame-*.png"))
    loop = manifest["loop_validation"]

    assert len(frames) == manifest["frame_count"] == 54
    assert manifest["duration_ms"] == 2250
    assert manifest["stabilization"]["output_bottom_anchor_range"] == [704, 704]
    assert loop["source_output_frames_inclusive"] == [6, 59]
    assert loop["matched_endpoint_frame_not_delivered"] == 60
    assert loop["matched_endpoint_alpha_iou"] >= 0.96
    assert loop["seam_vs_natural_step_delta"] <= 1.1
    assert loop["crossfade_frames"] == 0
    assert loop["duplicate_endpoint_frame"] is False
    assert loop["method"] == "matched_gait_phase_boundary_without_crossfade"
    assert _sha256(frames[0]) != _sha256(frames[-1])

    sample = Image.open(frames[27]).convert("RGBA")
    assert sample.size == (960, 720)
    assert sample.getchannel("A").getextrema() == (0, 255)


def test_delivery_has_alpha_no_audio_and_three_cycle_review_preview() -> None:
    manifest = _json(ACTION_ROOT / "manifest.json")
    webm = ACTION_ROOT / manifest["video"]
    preview = ACTION_ROOT / manifest["checkerboard_preview"]
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,nb_frames:stream_tags=ALPHA_MODE",
            "-of",
            "json",
            str(webm),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    preview_probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "json",
            str(preview),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    streams = json.loads(probe.stdout)["streams"]
    preview_stream = json.loads(preview_probe.stdout)["streams"][0]

    assert [stream["codec_type"] for stream in streams] == ["video"]
    assert streams[0]["tags"]["ALPHA_MODE"] == "1"
    assert int(preview_stream["nb_read_frames"]) == 54 * 3
    assert _sha256(webm) == manifest["delivery_sha256"]["webm"]
    assert Image.open(ACTION_ROOT / manifest["animation"]).n_frames == 54
    poster = Image.open(ACTION_ROOT / manifest["poster"]).convert("RGBA")
    assert poster.getchannel("A").getextrema() == (0, 255)


def test_media_registry_hashes_track_approved_runtime_mapping() -> None:
    media = _json(ROOT / "config/media_asset_registry_v1.json")["abu_motion"]
    runtime = (ASSET_ROOT.parent / "motion-registry.js").read_text(encoding="utf-8")

    assert media["default_action_id"] == "abu_dream_standard_cycle_v1"
    assert ACTION_ID in runtime
    assert 'following: "calm_follow_walk"' in runtime
    assert media["sha256"] == _sha256(ROOT / media["registry"])
    assert media["library_sha256"] == _sha256(ROOT / media["library"])
    assert media["source_inventory_sha256"] == _sha256(
        ROOT / media["source_inventory"]
    )


def test_gallery_and_dream_runtime_use_the_approved_follow_action() -> None:
    gallery = (
        ROOT
        / "apps/product/static/experience/internal-tools/abu-motion-gallery-v1/app.js"
    ).read_text(encoding="utf-8")
    template = (
        ROOT
        / "apps/product/static/experience/internal-tools/abu-motion-gallery-v1/index.html"
    ).read_text(encoding="utf-8")
    shell = ROOT / "apps/product/experience_shell/src"
    dream_runtime = (shell / "dream_runtime.ts").read_text(encoding="utf-8")
    dream_assets = (shell / "dream_asset_registry.ts").read_text(encoding="utf-8")

    assert "library.actions.forEach" in gallery
    assert "已审核 · 系统可用" in gallery
    assert 'class="approval"' in template
    assert 'styles.css?v=actor-pass-v2' in template
    assert 'app.js?v=actor-pass-v2' in template
    assert 'const ABU_V12 = "/assets/abu/v12-actor-pass"' in dream_assets
    assert (
        "abu-02-calm-follow-walk-loop-v1/web/"
        "abu_02_calm_follow_walk_loop_v1.webp"
    ) in dream_assets
    assert "DREAM_RUNTIME_ASSETS.abuWalk.fallback" in dream_runtime
