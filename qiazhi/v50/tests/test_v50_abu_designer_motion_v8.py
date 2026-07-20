from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v8-designer-divination"


def test_divination_motion_is_high_definition_transparent_and_watermark_free() -> None:
    manifest = json.loads((ASSET_ROOT / "manifest.json").read_text(encoding="utf-8"))
    animation = ASSET_ROOT / str(manifest["animation"])
    poster = ASSET_ROOT / str(manifest["poster"])

    assert manifest["status"] == "production"
    assert manifest["motion"] == "divination"
    assert manifest["source"]["sha256"] == "2dd91480c1efab682751f0ffae8df56d270cf165bdda56aadeea4fbe046ca3ee"
    assert manifest["canvas"] == [960, 720]
    assert manifest["transparent_background"] is True
    assert manifest["watermark_removed"] is True
    assert manifest["frame_count"] == 150
    assert manifest["duration_ms"] == 10000
    assert animation.stat().st_size > 6_000_000
    assert animation.read_bytes()[:4] == b"RIFF"
    assert animation.read_bytes()[8:12] == b"WEBP"
    assert poster.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_divination_motion_drives_real_reasoning_wait_states() -> None:
    javascript = (ROOT / "apps/product/static/l5/app.js").read_text(encoding="utf-8")
    registry = (ROOT / "apps/product/static/l5/assets/abu/motion-registry.js").read_text(encoding="utf-8")
    html = (ROOT / "apps/product/static/l5/index.html").read_text(encoding="utf-8")

    assert 'divination_classic: Object.freeze({' in registry
    assert "/assets/abu/v8-designer-divination/web/abu_divination_v8.webp" in registry
    assert 'thinking: "taoist_divination"' in registry
    assert 'setAbuState(label.includes("出生信息") ? "parsing" : "thinking", label)' in javascript
    assert "function setAbuLoadingPeek" in javascript
    assert 'id="abuMotionFrame"' in html
    assert 'class="thinking-abu-loader"' not in html
    assert 'data-abu-motion="divination_classic"' not in html
