from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v4-video-derived"


def test_abu_v4_animation_pack_is_transparent_watermark_free_and_complete() -> None:
    manifest = json.loads((ASSET_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["transparent_background"] is True
    assert manifest["watermark_removed"] is True
    assert manifest["canvas"] == [640, 640]
    assert manifest["webp"] == {"quality": 92, "method": 5}
    assert set(manifest["assets"]) == {"idle_blink", "head_tilt", "caution_ears", "happy_tail"}
    for payload in manifest["assets"].values():
        animation = ASSET_ROOT / payload["animation"]
        poster = ASSET_ROOT / payload["poster"]
        assert animation.stat().st_size > 500_000
        assert poster.stat().st_size > 100_000
        assert animation.read_bytes()[:4] == b"RIFF"
        assert animation.read_bytes()[8:12] == b"WEBP"
        assert poster.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_public_product_uses_state_driven_abu_v4_assets() -> None:
    index = (ROOT / "apps/product/static/l5/index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "apps/product/static/l5/app.js").read_text(encoding="utf-8")
    registry = (ROOT / "apps/product/static/l5/assets/abu/motion-registry.js").read_text(encoding="utf-8")

    assert "id=\"abuMotionFrame\"" in index
    assert "/assets/abu/v4-video-derived/web/abu_idle_blink_v4.webp" in index
    assert "ABU_STATE_MOTION" in javascript
    assert 'thinking: "taoist_divination"' in registry
    assert 'caution: "caution_ears"' in registry
    assert 'wave: "happy_tail"' in registry
    assert "prefers-reduced-motion: reduce" in javascript
    assert 'const ABU_MOTION_ROOT = "/assets/abu/v4-video-derived"' in javascript
