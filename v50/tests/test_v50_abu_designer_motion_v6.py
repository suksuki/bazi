from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu"


def _assert_motion(
    directory: str,
    motion: str,
    source_hash: str,
    alpha_matte: dict[str, float],
    frame_count: int,
    duration_ms: int,
    canvas: list[int],
) -> dict[str, object]:
    root = ASSET_ROOT / directory
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    animation = root / str(manifest["animation"])
    poster = root / str(manifest["poster"])

    assert manifest["status"] == "production"
    assert manifest["motion"] == motion
    assert manifest["source"]["sha256"] == source_hash
    assert manifest["transparent_background"] is True
    assert manifest["watermark_removed"] is True
    assert manifest["canvas"] == canvas
    assert manifest["alpha_matte"] == alpha_matte
    assert manifest["frame_count"] == frame_count
    assert manifest["duration_ms"] == duration_ms
    assert animation.stat().st_size > 1_500_000
    assert animation.read_bytes()[:4] == b"RIFF"
    assert animation.read_bytes()[8:12] == b"WEBP"
    assert poster.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    return manifest


def test_sleep_and_butterfly_designer_motions_are_production_assets() -> None:
    sleep = _assert_motion(
        "v6-designer-sleep",
        "sleep_breathe",
        "76333476f95210a0c807b7fa4dbe0f3c6c04f944b05eb856af096a9f7d658526",
        {"low": 30.0, "high": 56.0},
        58,
        3867,
        [720, 720],
    )
    play = _assert_motion(
        "v6-designer-play",
        "butterfly_play",
        "59b5064310d0b9b3689c0c8a695059dd302f1881a730c8044110b0295ce78515",
        {"low": 36.0, "high": 64.0},
        76,
        5067,
        [960, 640],
    )

    assert sleep["usage"] == ["idle_timeout", "quiet_waiting"]
    assert play["usage"] == ["awake_idle_random", "ambient_companion_moment"]
    assert play["character_crop_box"] == [70, 20, 1030, 700]
    assert sleep["webp"] == {"quality": 93, "method": 6}
    assert play["webp"] == {"quality": 93, "method": 6}


def test_sleep_and_play_motions_remain_registered_for_future_scene_consumers() -> None:
    registry = (ROOT / "apps/product/static/l5/assets/abu/motion-registry.js").read_text(encoding="utf-8")

    assert 'sleep: "sleep_breathe"' in registry
    assert 'playful: "butterfly_play"' in registry
    assert 'adventure: "run_jump"' in registry
    assert 'celebration: "breakdance"' in registry
    assert 'completed: "happy_tail"' in registry
    assert "/assets/abu/v6-designer-sleep/web/abu_sleep_breathe_v6.webp" in registry
    assert "/assets/abu/v6-designer-play/web/abu_butterfly_play_v6.webp" in registry


def test_motion_builder_supports_usage_alpha_matte_and_manual_crop() -> None:
    builder = (ROOT / "tools/build_abu_designer_motion.py").read_text(encoding="utf-8")
    extractor = (ROOT / "tools/extract_video_frames.swift").read_text(encoding="utf-8")

    assert 'parser.add_argument("--usage", nargs="*", default=[])' in builder
    assert 'parser.add_argument("--alpha-low", type=float, default=9.0)' in builder
    assert 'parser.add_argument("--crop-box", type=int, nargs=4)' in builder
    assert 'parser.add_argument("--canvas-width", type=int, default=CANVAS_SIZE)' in builder
    assert 'parser.add_argument("--quality", type=int, default=86)' in builder
    assert "AVAssetImageGenerator" in extractor
    assert 'String(format: "frame_%04d.png", index)' in extractor
