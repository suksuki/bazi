#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("/Users/liujin/Downloads/Create_an_second_cinematic_d.mp4")
ARTIFACT_ROOT = (
    ROOT
    / "artifacts/abu-dream-world/entry-transition/abu-03-dream-entry-transition-v1"
)
RUNTIME_ROOT = (
    ROOT
    / "apps/product/static/l5/assets/dream/entry-transition-v1"
)

SOURCE_ARCHIVE = ARTIFACT_ROOT / "source/Create_an_second_cinematic_d-source-with-watermark.mp4"
CLEAN_MASTER = ARTIFACT_ROOT / "clean-master/abu_03_dream_entry_transition_v1_clean_master.mp4"
RUNTIME_VIDEO = RUNTIME_ROOT / "abu_03_dream_entry_transition_v1_runtime_1080p.mp4"
FIRST_FRAME = RUNTIME_ROOT / "abu_03_dream_entry_transition_v1_first_frame.png"
LAST_FRAME = RUNTIME_ROOT / "abu_03_dream_entry_transition_v1_last_frame.png"
RUNTIME_MANIFEST = RUNTIME_ROOT / "manifest.json"
ARTIFACT_MANIFEST = ARTIFACT_ROOT / "manifest.json"

ASSET_ID = "ABU_03_DREAM_ENTRY_TRANSITION_V1"
RUNTIME_DURATION_SECONDS = 7.75
HANDOFF_START_SECONDS = 7.10
SOURCE_SAFE_CROP = "crop=1118:628:0:80"
CLEAN_MASTER_FILTER = f"{SOURCE_SAFE_CROP},scale=1280:720:flags=lanczos"
RUNTIME_FILTER = "scale=1920:1080:flags=lanczos,unsharp=5:5:0.20:5:5:0"


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def ffprobe(path: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,format_name",
            "-show_entries",
            "stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def build(source: Path) -> None:
    if not source.is_file():
        raise SystemExit(f"missing source video: {source}")

    for directory in {
        SOURCE_ARCHIVE.parent,
        CLEAN_MASTER.parent,
        RUNTIME_ROOT,
    }:
        directory.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source, SOURCE_ARCHIVE)

    run(
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        CLEAN_MASTER_FILTER,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "17",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(CLEAN_MASTER),
    )

    run(
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(CLEAN_MASTER),
        "-t",
        f"{RUNTIME_DURATION_SECONDS:.2f}",
        "-vf",
        RUNTIME_FILTER,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(RUNTIME_VIDEO),
    )

    run(
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        "0",
        "-i",
        str(RUNTIME_VIDEO),
        "-frames:v",
        "1",
        "-update",
        "1",
        str(FIRST_FRAME),
    )
    run(
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{RUNTIME_DURATION_SECONDS - 0.05:.2f}",
        "-i",
        str(RUNTIME_VIDEO),
        "-frames:v",
        "1",
        "-update",
        "1",
        str(LAST_FRAME),
    )

    source_probe = ffprobe(source)
    clean_probe = ffprobe(CLEAN_MASTER)
    runtime_probe = ffprobe(RUNTIME_VIDEO)
    manifest = {
        "schema_version": "deepbazi.dream.entry_transition_asset.v1",
        "asset_id": ASSET_ID,
        "character_version": "ABU_CHARACTER_V1",
        "source_status": "SOURCE_APPROVED",
        "library_status": "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW",
        "semantic_state": "DREAM_ENTRY_TRANSITION",
        "action_type": "ONE_SHOT",
        "runtime_role": (
            "home sleeping Abu to fog path; hand off to the real three-tree "
            "selection runtime"
        ),
        "source": {
            "input_filename": source.name,
            "archived_path": str(SOURCE_ARCHIVE.relative_to(ROOT)),
            "sha256": sha256(source),
            "probe": source_probe,
        },
        "postprocess": {
            "watermark_removed": True,
            "watermark_removal_method": "sixteen_by_nine_safe_crop",
            "source_safe_crop": {
                "width": 1118,
                "height": 628,
                "x": 0,
                "y": 80,
                "reason": (
                    "remove the lower-right platform mark without blur or "
                    "synthetic inpainting while retaining every Abu action"
                ),
            },
            "audio_removed": True,
            "clean_master_path": str(CLEAN_MASTER.relative_to(ROOT)),
            "clean_master_sha256": sha256(CLEAN_MASTER),
            "clean_master_probe": clean_probe,
        },
        "runtime": {
            "path": str(RUNTIME_VIDEO.relative_to(ROOT)),
            "sha256": sha256(RUNTIME_VIDEO),
            "probe": runtime_probe,
            "duration_seconds": RUNTIME_DURATION_SECONDS,
            "handoff_start_seconds": HANDOFF_START_SECONDS,
            "handoff_duration_seconds": round(
                RUNTIME_DURATION_SECONDS - HANDOFF_START_SECONDS,
                2,
            ),
            "first_frame": str(FIRST_FRAME.relative_to(ROOT)),
            "first_frame_sha256": sha256(FIRST_FRAME),
            "last_frame": str(LAST_FRAME.relative_to(ROOT)),
            "last_frame_sha256": sha256(LAST_FRAME),
            "left_lower_fog_handoff": True,
            "interactive_destination": "THREE_TREE_SELECTION",
            "video_is_not_interactive_selection": True,
        },
        "constraints": {
            "runtime_controls_tree_rotation": True,
            "final_video_seconds_are_not_used_as_interactive_ui": True,
            "center_tree_handoff_slot": 1,
            "center_tree_palette": "blue",
            "candidate_tree_positions_must_remain_stable": True,
            "audio_tracks_allowed": False,
        },
    }

    encoded = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    RUNTIME_MANIFEST.write_text(encoded, encoding="utf-8")
    ARTIFACT_MANIFEST.write_text(encoded, encoding="utf-8")


if __name__ == "__main__":
    build(Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_SOURCE)
