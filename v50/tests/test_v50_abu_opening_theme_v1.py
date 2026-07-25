from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO_ROOT = ROOT / "apps/product/static/l5/assets/audio/abu"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_owner_supplied_opening_theme_is_archived_and_registered() -> None:
    library = _json(AUDIO_ROOT / "library.json")
    item = library["assets"][0]
    manifest_path = ROOT / item["manifest"]
    manifest = _json(manifest_path)
    source = ROOT / manifest["source"]["archived_path"]

    assert library["default_opening_theme_asset_id"] == "abu_mingli_opening_theme_morning_glints_v1"
    assert item["manifest_sha256"] == _sha256(manifest_path)
    assert manifest["product_role"] == "website_opening_theme"
    assert manifest["source"]["sha256"] == "d48faa4f0a79b7b4b61c05230cb789f0d1b178866f38f18b3ee1c45859e06908"
    assert _sha256(source) == manifest["source"]["sha256"]
    assert manifest["source"]["use_authorization"] == "owner_approved_for_abu_website_opening_music"


def test_web_variants_and_global_registry_are_hash_locked() -> None:
    registry = _json(ROOT / "config/media_asset_registry_v1.json")["abu_audio"]
    library = ROOT / registry["library"]
    manifest = _json(ROOT / registry["manifest"])
    builder = (ROOT / "scripts/v50_register_abu_opening_theme_v1.py").read_text(encoding="utf-8")

    assert registry["library_sha256"] == _sha256(library)
    assert registry["manifest_sha256"] == _sha256(ROOT / registry["manifest"])
    assert registry["runtime_mp3_sha256"] == _sha256(ROOT / registry["runtime_mp3"])
    assert registry["runtime_opus_sha256"] == _sha256(ROOT / registry["runtime_opus"])
    assert (ROOT / registry["runtime_mp3"]).read_bytes()[:3] in {b"ID3", b"\xff\xfb\x90"}
    assert (ROOT / registry["runtime_opus"]).read_bytes()[:4] == b"OggS"
    assert '"+bitexact"' in builder
    assert '"-serial_offset"' in builder
    assert manifest["playback_policy"] == {
        "audible_autoplay": False,
        "start_after_first_user_gesture": True,
        "play_once_per_browser_session": True,
        "loop": False,
        "default_volume": 0.52,
        "user_control_required": True,
        "narration_priority": True,
    }


def test_workspace_uses_gesture_safe_once_per_session_music_control() -> None:
    source = (ROOT / "apps/product/experience_shell/src/opening_music.ts").read_text(encoding="utf-8")
    main = (ROOT / "apps/product/experience_shell/src/main.ts").read_text(encoding="utf-8")
    components = (ROOT / "apps/product/experience_shell/src/components.ts").read_text(encoding="utf-8")

    assert "start_after_first_user_gesture" not in source
    assert "pointerdown" in source
    assert "SESSION_PLAYED_KEY" in source
    assert "this.audio.loop = false" in source
    assert "pauseForNarration" in source
    assert "document.documentElement.dataset.openingMusicState" in source
    assert 'command === "toggle-opening-music"' in main
    assert "openingMusic.pauseForNarration()" in main
    assert "syncOpeningMusicControls();\n  openingMusic.arm();" in main
    assert "data-opening-music-control" in components
