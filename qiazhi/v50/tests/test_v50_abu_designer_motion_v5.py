from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v5-designer-welcome"


def test_designer_welcome_wave_is_a_clean_production_asset() -> None:
    manifest = json.loads((ASSET_ROOT / "manifest.json").read_text(encoding="utf-8"))
    animation = ASSET_ROOT / manifest["animation"]
    poster = ASSET_ROOT / manifest["poster"]

    assert manifest["status"] == "production"
    assert manifest["motion"] == "welcome_wave"
    assert manifest["source"]["sha256"] == "cd8ddfe46839cbc7082daf9f0a0be93372e01141546adf3189f532b937c00e1d"
    assert manifest["transparent_background"] is True
    assert manifest["watermark_removed"] is True
    assert manifest["removed_regions"] == [
        {"name": "source_right_side_color_mark", "method": "excluded_before_alpha_extraction"}
    ]
    assert manifest["canvas"] == [720, 720]
    assert manifest["webp"] == {"quality": 93, "method": 6}
    assert manifest["frame_count"] == 37
    assert animation.stat().st_size > 1_000_000
    assert animation.read_bytes()[:4] == b"RIFF"
    assert animation.read_bytes()[8:12] == b"WEBP"
    assert poster.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_welcome_state_uses_designer_motion_without_reusing_completion_motion() -> None:
    registry = (ROOT / "apps/product/static/l5/assets/abu/motion-registry.js").read_text(encoding="utf-8")
    javascript = (ROOT / "apps/product/static/l5/app.js").read_text(encoding="utf-8")

    assert 'welcome: "welcome_wave"' in registry
    assert 'completed: "happy_tail"' in registry
    assert 'confidence_up: "happy_tail"' in registry
    assert "/assets/abu/v5-designer-welcome/web/abu_welcome_wave_v5.webp" in registry
    assert 'return path.startsWith("/") ? path' in javascript
    assert 'setAbuState("welcome", state.reading ? "又见面了" : "准备听你说")' in javascript


def test_designer_motion_builder_is_reusable_for_followup_deliveries() -> None:
    builder = (ROOT / "tools/build_abu_designer_motion.py").read_text(encoding="utf-8")

    assert 'parser.add_argument("--motion", required=True)' in builder
    assert 'parser.add_argument("--start", type=float, required=True)' in builder
    assert 'parser.add_argument("--end", type=float, required=True)' in builder
    assert 'parser.add_argument("--display-scale", type=float, default=1.0)' in builder
    assert 'parser.add_argument("--playback", choices=("loop", "hold", "one_shot"), default="loop")' in builder
    assert 'parser.add_argument("--loop-count", type=int, default=0)' in builder
    assert '"emotion_tracks_workflow_not_fate": True' in builder


def test_product_server_registers_webp_content_type_for_ubuntu() -> None:
    product_surface = (ROOT / "apps/product/product_surface.py").read_text(encoding="utf-8")

    assert 'mimetypes.add_type("image/webp", ".webp")' in product_surface
