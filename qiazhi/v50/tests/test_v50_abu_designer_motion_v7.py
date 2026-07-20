from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v7-designer-run-jump"


def test_run_jump_is_a_high_definition_transparent_product_motion() -> None:
    manifest = json.loads((ASSET_ROOT / "manifest.json").read_text(encoding="utf-8"))
    animation = ASSET_ROOT / str(manifest["animation"])
    poster = ASSET_ROOT / str(manifest["poster"])

    assert manifest["status"] == "production"
    assert manifest["motion"] == "run_jump"
    assert manifest["source"]["sha256"] == "ce349b8ce06fcebc695dd325775a21e530a756fa74fd9fac27fc8595d70a22b1"
    assert manifest["canvas"] == [960, 640]
    assert manifest["webp"] == {"quality": 94, "method": 6}
    assert manifest["transparent_background"] is True
    assert manifest["watermark_removed"] is True
    assert manifest["frame_count"] == 107
    assert manifest["duration_ms"] == 7133
    assert animation.stat().st_size > 5_000_000
    assert animation.read_bytes()[:4] == b"RIFF"
    assert animation.read_bytes()[8:12] == b"WEBP"
    assert poster.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_run_jump_is_random_ambient_motion_with_a_wider_stage() -> None:
    javascript = (ROOT / "apps/product/static/l5/app.js").read_text(encoding="utf-8")
    registry = (ROOT / "apps/product/static/l5/assets/abu/motion-registry.js").read_text(encoding="utf-8")
    stylesheet = (ROOT / "apps/product/static/l5/styles.css").read_text(encoding="utf-8")

    assert 'adventure: "run_jump"' in registry
    assert "/assets/abu/v7-designer-run-jump/web/abu_run_jump_v7.webp" in registry
    assert "function chooseAbuAmbientMoment()" in javascript
    assert "const moment = chooseAbuAmbientMoment()" in javascript
    assert ".abu-stage { width: 164px; height: 106px; flex: 0 0 164px; }" in stylesheet
    assert ".workspace { grid-template-columns: minmax(400px, 430px) minmax(0, 1fr); }" in stylesheet
