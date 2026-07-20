from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu"
PACK = ASSET_ROOT / "v11-designer-sad-tears"


def test_sad_tears_is_a_transparent_hd_failure_motion() -> None:
    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    animation = PACK / str(manifest["animation"])
    poster = PACK / str(manifest["poster"])

    assert manifest["status"] == "production"
    assert manifest["motion"] == "sad_tears"
    assert manifest["source"]["sha256"] == "69655a4f4bd04b6d7a3a95fdc0f2b8bd54e55ad72330c7daf501b6d78b899ed4"
    assert manifest["canvas"] == [960, 720]
    assert manifest["anchor"] == [0.5, 700 / 720]
    assert manifest["frame_count"] == 150
    assert manifest["duration_ms"] == 10000
    assert manifest["transparent_background"] is True
    assert manifest["watermark_removed"] is True
    assert manifest["runtime_display"] == {
        "scale": 1.1,
        "stage_profile": "wide",
        "playback": "hold",
        "category": "workflow",
    }
    assert animation.stat().st_size > 10_000_000
    assert Image.open(animation).info.get("loop") == 1

    poster_image = Image.open(poster).convert("RGBA")
    alpha_box = poster_image.getchannel("A").getbbox()
    assert alpha_box is not None
    assert alpha_box[2] <= 840
    apparent_height = (alpha_box[3] - alpha_box[1]) * min(164 / 960, 106 / 720) * 1.1
    assert 72 <= apparent_height <= 102


def test_hard_failures_use_sadness_without_recasting_uncertainty_as_failure() -> None:
    registry = (ASSET_ROOT / "motion-registry.js").read_text(encoding="utf-8")
    javascript = (ROOT / "apps/product/static/l5/app.js").read_text(encoding="utf-8")
    html = (ROOT / "apps/product/static/l5/index.html").read_text(encoding="utf-8")
    stylesheet = (ROOT / "apps/product/static/l5/styles.css").read_text(encoding="utf-8")

    assert 'sad: "sad_tears"' in registry
    assert 'playback: "hold"' in registry
    assert 'setAbuState("sad", "这次没能形成可靠判断")' in javascript
    assert 'event.event_type === "domain_blocked" ? "sad" : "caution"' in javascript
    assert 'setAbuState("sad", "这个专题暂时没有完成")' in javascript
    assert 'setAbuState("sad", "这次看盘没有完成")' in javascript
    assert 'setAbuState("sad", "上次判断没有通过检查")' in javascript
    assert 'setAbuState("caution", "两种解释仍在竞争")' in javascript
    assert 'data-abu-motion="sad_tears"' in html
    assert ".app-shell.abu-panel-collapsed .abu-stage:focus-visible" in stylesheet
    assert "url('/assets/valley_sunrise.jpg')" in stylesheet
