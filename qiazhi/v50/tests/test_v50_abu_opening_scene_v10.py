from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v10-opening-scene"


def test_opening_scene_is_an_icon_free_hd_delivery_asset() -> None:
    manifest = json.loads((ASSET_ROOT / "manifest.json").read_text(encoding="utf-8"))
    video = ASSET_ROOT / manifest["delivery"]["video"]
    poster = ASSET_ROOT / manifest["delivery"]["poster"]

    assert manifest["version"] == "v10"
    assert manifest["source"]["designer_icon_removed"] is True
    assert manifest["delivery"]["source_resolution"] == [1280, 720]
    assert manifest["delivery"]["delivery_resolution"] == [1920, 1080]
    assert manifest["delivery"]["written_frame_count"] == 240
    assert manifest["delivery"]["duration_seconds"] == 10.0
    assert video.stat().st_size > 6_000_000
    assert video.read_bytes()[4:8] == b"ftyp"
    assert Image.open(poster).size == (1920, 1080)


def test_opening_transition_has_a_clean_background_and_transparent_character() -> None:
    background = Image.open(ASSET_ROOT / "transition/abu_opening_background_v10.webp")
    character = Image.open(ASSET_ROOT / "transition/abu_opening_character_v10.png")

    assert background.size == (1672, 941)
    assert character.size == (556, 839)
    assert character.mode == "RGBA"
    assert character.getchannel("A").getextrema() == (0, 255)
    assert character.getchannel("A").getbbox() is not None


def test_opening_scene_hands_the_character_to_the_existing_abu_surface() -> None:
    html = (ROOT / "apps/product/static/l5/index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "apps/product/static/l5/app.js").read_text(encoding="utf-8")
    stylesheet = (ROOT / "apps/product/static/l5/styles.css").read_text(encoding="utf-8")

    assert 'id="openingSceneVideo"' in html
    assert 'id="openingAbuFlight"' in html
    assert "abu_opening_scene_v10.mp4" in html
    assert "20260717-thinking-chart-v1" in html
    assert 'const OPENING_SCENE_SESSION_KEY = "deepbazi.opening_scene_v10.seen"' in javascript
    assert 'get("opening") === "1"' in javascript
    assert "function openingDestinationRect()" in javascript
    assert 'el("abuStage")?.getBoundingClientRect()' in javascript
    assert 'setAbuSurface("peek"' in javascript
    assert javascript.count('setAbuSurface("peek", { persist: false, message: "你好，我是阿布。我们从你的出生信息开始。" })') == 2
    assert "flight.animate(" in javascript
    assert ".opening-scene-video" in stylesheet
    assert "object-fit: cover" in stylesheet
    assert "opening-scene-mobile-pan" in stylesheet
    assert "width: 175vw;" in stylesheet
    assert "object-fit: contain;" in stylesheet
    assert "mask-image: linear-gradient" in stylesheet
    assert "30% { transform: translate(-58%, -50%); }" in stylesheet
    assert "const renderedWidth = viewportWidth * 1.75;" in javascript
    assert "viewportWidth * .5 - renderedWidth * .52" in javascript
    assert ".opening-scene.is-revealing" in stylesheet


def test_opening_builder_uses_content_aware_repair_instead_of_a_cover_patch() -> None:
    builder = (ROOT / "tools/build_abu_opening_scene_v10.py").read_text(encoding="utf-8")

    assert "cv2.xphoto.INPAINT_FSR_BEST" in builder
    assert "ICON_DIAMOND" in builder
    assert '"scale=1920:1080:flags=lanczos' in builder
    assert '"-crf",' in builder
    assert '"+faststart"' in builder
