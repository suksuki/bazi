from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu"
STAGE = (164, 106)


def _manifest(directory: str) -> dict[str, object]:
    return json.loads((ASSET_ROOT / directory / "manifest.json").read_text(encoding="utf-8"))


def test_taoist_and_breakdance_are_transparent_hd_production_assets() -> None:
    expected = {
        "v9-designer-taoist-divination": {
            "motion": "taoist_divination",
            "hash": "a626bba26e911443c8a211642fc2e254e9453006ec858f3c8dbd1b894da84783",
            "minimum_bytes": 9_000_000,
            "playback": "loop",
            "loop_count": 0,
            "category": "workflow",
        },
        "v9-designer-breakdance": {
            "motion": "breakdance",
            "hash": "04adff7578bf784582aa2285888870414c2aee528a650b5f3e97943df1c6e6d7",
            "minimum_bytes": 7_000_000,
            "playback": "one_shot",
            "loop_count": 1,
            "category": "ambient",
        },
    }
    for directory, contract in expected.items():
        manifest = _manifest(directory)
        animation = ASSET_ROOT / directory / str(manifest["animation"])
        poster = ASSET_ROOT / directory / str(manifest["poster"])

        assert manifest["status"] == "production"
        assert manifest["motion"] == contract["motion"]
        assert manifest["source"]["sha256"] == contract["hash"]
        assert manifest["canvas"] == [960, 720]
        assert manifest["anchor"] == [0.5, 700 / 720]
        assert manifest["frame_count"] == 150
        assert manifest["duration_ms"] == 10000
        assert manifest["transparent_background"] is True
        assert manifest["watermark_removed"] is True
        assert manifest["webp"] == {"quality": 94, "method": 6, "loop_count": contract["loop_count"]}
        assert manifest["runtime_display"]["playback"] == contract["playback"]
        assert manifest["runtime_display"]["category"] == contract["category"]
        assert animation.stat().st_size > contract["minimum_bytes"]
        assert animation.read_bytes()[:4] == b"RIFF"
        assert animation.read_bytes()[8:12] == b"WEBP"
        assert poster.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        animated = Image.open(animation)
        assert animated.info.get("loop") == contract["loop_count"]


def _apparent_size(path: Path, display_scale: float) -> tuple[float, float]:
    image = Image.open(path).convert("RGBA")
    box = image.getchannel("A").getbbox()
    assert box is not None
    contain = min(STAGE[0] / image.width, STAGE[1] / image.height)
    return (
        (box[2] - box[0]) * contain * display_scale,
        (box[3] - box[1]) * contain * display_scale,
    )


def test_runtime_visual_scale_is_normalized_by_visible_character_not_canvas() -> None:
    posters = {
        "idle": ("v4-video-derived/posters/abu_idle_blink_v4.png", 0.96),
        "listen": ("v4-video-derived/posters/abu_head_tilt_v4.png", 0.94),
        "boundary": ("v4-video-derived/posters/abu_caution_ears_v4.png", 1.02),
        "complete": ("v4-video-derived/posters/abu_happy_tail_v4.png", 0.95),
        "welcome": ("v5-designer-welcome/posters/abu_welcome_wave_v5.png", 0.94),
        "butterfly": ("v6-designer-play/posters/abu_butterfly_play_v6.png", 0.98),
        "run": ("v7-designer-run-jump/posters/abu_run_jump_v7.png", 1.14),
        "classic": ("v8-designer-divination/posters/abu_divination_v8.png", 1.06),
        "taoist": ("v9-designer-taoist-divination/posters/abu_taoist_divination_v9.png", 1.15),
        "dance": ("v9-designer-breakdance/posters/abu_breakdance_v9.png", 1.12),
    }
    for motion, (relative_path, display_scale) in posters.items():
        _, height = _apparent_size(ASSET_ROOT / relative_path, display_scale)
        assert 72 <= height <= 102, f"{motion} apparent height is {height:.1f}px"

    sleep_width, _ = _apparent_size(
        ASSET_ROOT / "v6-designer-sleep/posters/abu_sleep_breathe_v6.png",
        1.12,
    )
    assert 80 <= sleep_width <= 110


def test_product_keeps_one_motion_registry_after_l5_runtime_retirement() -> None:
    registry = (ASSET_ROOT / "motion-registry.js").read_text(encoding="utf-8")
    surface = (ROOT / "apps/product/product_surface.py").read_text(encoding="utf-8")

    assert 'scaleBasis: "visible character bounds rather than source canvas size"' in registry
    assert 'thinking: "taoist_divination"' in registry
    assert 'celebration: "breakdance"' in registry
    assert 'label: "偷偷跳一小段舞"' in registry
    assert 'label: "发现了一只蝴蝶", weight: 5' in registry
    assert 'label: "偷偷跳一小段舞", weight: 3' in registry
    assert 'app.mount("/assets"' in surface
    assert 'FileResponse(MEDIA_DIR / "app.js"' not in surface
