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


def test_unified_product_keeps_v4_pack_and_uses_registered_standard_idle() -> None:
    components = (ROOT / "apps/product/experience_shell/src/components.ts").read_text(encoding="utf-8")
    registry = (ROOT / "apps/product/static/l5/assets/abu/motion-registry.js").read_text(encoding="utf-8")

    assert "/assets/abu/v12-actor-pass/quiet-sit-reaction/web/abu_quiet_sit_reaction_v1.webp" in components
    assert 'idle: "quiet_sit_reaction"' in registry
    assert 'thinking: "taoist_divination"' in registry
    assert 'caution: "caution_ears"' in registry
    assert 'wave: "happy_tail"' in registry
