from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    os.environ.get(
        "V50_ABU_OPENING_THEME_SOURCE",
        str(Path.home() / "Downloads/Morning_Glints_In_The_Grove.mp3"),
    )
).expanduser()
SOURCE_ARCHIVE = ROOT / "artifacts/abu-audio/source/morning-glints-in-the-grove-source.mp3"
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/audio/abu"
TRACK_ROOT = ASSET_ROOT / "morning-glints-in-the-grove-v1"
LIBRARY = ASSET_ROOT / "library.json"
MANIFEST = TRACK_ROOT / "manifest.json"
MP3 = TRACK_ROOT / "morning-glints-in-the-grove-opening-v1.mp3"
OPUS = TRACK_ROOT / "morning-glints-in-the-grove-opening-v1.opus"
GLOBAL_REGISTRY = ROOT / "config/media_asset_registry_v1.json"
EXPECTED_SOURCE_SHA256 = "d48faa4f0a79b7b4b61c05230cb789f0d1b178866f38f18b3ee1c45859e06908"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def probe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        (
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:stream=codec_name,sample_rate,channels,channel_layout",
            "-of",
            "json",
            str(path),
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build_web_variants(duration_seconds: float) -> None:
    TRACK_ROOT.mkdir(parents=True, exist_ok=True)
    fade_out_start = max(0.0, duration_seconds - 2.6)
    audio_filter = (
        "loudnorm=I=-20:TP=-2:LRA=7,"
        "afade=t=in:st=0:d=1.2,"
        f"afade=t=out:st={fade_out_start:.3f}:d=2.6"
    )
    common = (
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(SOURCE_ARCHIVE),
        "-vn",
        "-af",
        audio_filter,
        "-ar",
        "48000",
        "-ac",
        "2",
        "-fflags",
        "+bitexact",
        "-map_metadata",
        "-1",
    )
    run(
        *common,
        "-c:a",
        "libmp3lame",
        "-b:a",
        "192k",
        "-flags:a",
        "+bitexact",
        str(MP3),
    )
    run(
        *common,
        "-c:a",
        "libopus",
        "-b:a",
        "112k",
        "-vbr",
        "on",
        "-flags:a",
        "+bitexact",
        "-serial_offset",
        "0",
        str(OPUS),
    )


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"missing opening theme source: {SOURCE}")
    source_hash = sha256(SOURCE)
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise SystemExit(
            f"unexpected opening theme source hash: {source_hash} != {EXPECTED_SOURCE_SHA256}"
        )

    SOURCE_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, SOURCE_ARCHIVE)
    source_probe = probe(SOURCE_ARCHIVE)
    source_duration = float(source_probe["format"]["duration"])
    build_web_variants(source_duration)

    asset_id = "abu_mingli_opening_theme_morning_glints_v1"
    manifest = {
        "schema_version": "deepbazi.abu_audio_asset.v1",
        "asset_id": asset_id,
        "title": "Morning Glints In The Grove",
        "label_zh": "林间晨光",
        "status": "production_local",
        "product_role": "website_opening_theme",
        "registered_at": "2026-07-22",
        "source": {
            "original_filename": SOURCE.name,
            "archived_path": relative(SOURCE_ARCHIVE),
            "sha256": source_hash,
            "origin": "owner_supplied_analyst_designed",
            "use_authorization": "owner_approved_for_abu_website_opening_music",
            "technical": source_probe,
        },
        "web_variants": [
            {
                "format": "mp3",
                "mime_type": "audio/mpeg",
                "path": relative(MP3),
                "sha256": sha256(MP3),
                "technical": probe(MP3),
            },
            {
                "format": "opus",
                "mime_type": "audio/ogg; codecs=opus",
                "path": relative(OPUS),
                "sha256": sha256(OPUS),
                "technical": probe(OPUS),
            },
        ],
        "web_mastering": {
            "integrated_loudness_target_lufs": -20,
            "true_peak_ceiling_dbtp": -2,
            "fade_in_seconds": 1.2,
            "fade_out_seconds": 2.6,
            "sample_rate_hz": 48000,
        },
        "playback_policy": {
            "audible_autoplay": False,
            "start_after_first_user_gesture": True,
            "play_once_per_browser_session": True,
            "loop": False,
            "default_volume": 0.52,
            "user_control_required": True,
            "narration_priority": True,
        },
    }
    write_json(MANIFEST, manifest)

    library = {
        "schema_version": "deepbazi.abu_audio_library.v1",
        "updated_at": "2026-07-22",
        "default_opening_theme_asset_id": asset_id,
        "assets": [
            {
                "asset_id": asset_id,
                "title": manifest["title"],
                "label_zh": manifest["label_zh"],
                "status": manifest["status"],
                "product_role": manifest["product_role"],
                "manifest": relative(MANIFEST),
                "manifest_sha256": sha256(MANIFEST),
            }
        ],
    }
    write_json(LIBRARY, library)

    registry = json.loads(GLOBAL_REGISTRY.read_text(encoding="utf-8"))
    registry["abu_audio"] = {
        "library": relative(LIBRARY),
        "library_sha256": sha256(LIBRARY),
        "default_opening_theme_asset_id": asset_id,
        "manifest": relative(MANIFEST),
        "manifest_sha256": sha256(MANIFEST),
        "runtime_mp3": relative(MP3),
        "runtime_mp3_sha256": sha256(MP3),
        "runtime_opus": relative(OPUS),
        "runtime_opus_sha256": sha256(OPUS),
    }
    write_json(GLOBAL_REGISTRY, registry)

    print(
        json.dumps(
            {
                "status": "registered",
                "asset_id": asset_id,
                "duration_seconds": round(source_duration, 3),
                "source_sha256": source_hash,
                "library": relative(LIBRARY),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
