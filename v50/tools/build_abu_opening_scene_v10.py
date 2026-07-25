#!/usr/bin/env python3
"""Build the HD, icon-free Abu opening scene from the designer video."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


SCENE_VERSION = "v10"
ICON_CROP = (1070, 520, 160, 160)
ICON_DIAMOND = np.array([[86, 54], [113, 87], [86, 120], [59, 87]], dtype=np.int32)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_icon(frame: np.ndarray) -> np.ndarray:
    x, y, width, height = ICON_CROP
    crop = frame[y : y + height, x : x + width]
    if crop.shape[:2] != (height, width):
        raise ValueError("The source frame no longer matches the approved 1280x720 crop contract")

    valid_mask = np.full((height, width), 255, dtype=np.uint8)
    cv2.fillConvexPoly(valid_mask, ICON_DIAMOND, 0)
    valid_mask = cv2.erode(valid_mask, np.ones((3, 3), dtype=np.uint8), iterations=1)
    repaired = np.empty_like(crop)
    cv2.xphoto.inpaint(crop, valid_mask, repaired, cv2.xphoto.INPAINT_FSR_BEST)

    output = frame.copy()
    output[y : y + height, x : x + width] = repaired
    return output


def encode(source: Path, output: Path, poster: Path) -> dict[str, object]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required")

    capture = cv2.VideoCapture(str(source))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if (width, height) != (1280, 720) or not (23.9 <= fps <= 24.1):
        raise ValueError(f"Unexpected source contract: {width}x{height} at {fps:.3f}fps")

    output.parent.mkdir(parents=True, exist_ok=True)
    poster.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_suffix(".building.mp4")
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pixel_format",
        "bgr24",
        "-video_size",
        f"{width}x{height}",
        "-framerate",
        f"{fps:.6f}",
        "-i",
        "pipe:0",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "1:a?",
        "-vf",
        "scale=1920:1080:flags=lanczos,unsharp=5:5:0.32:3:3:0.12",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-movflags",
        "+faststart",
        str(temporary_output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    last_frame: np.ndarray | None = None
    written = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            cleaned = clean_icon(frame)
            process.stdin.write(cleaned.tobytes())
            last_frame = cleaned
            written += 1
    finally:
        capture.release()
        if process.stdin:
            process.stdin.close()
    return_code = process.wait()
    if return_code != 0:
        temporary_output.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg failed with exit code {return_code}")
    temporary_output.replace(output)

    if last_frame is None:
        raise RuntimeError("No video frames were decoded")
    poster_image = Image.fromarray(cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB))
    poster_image = poster_image.resize((1920, 1080), Image.Resampling.LANCZOS)
    poster_image.save(poster, "WEBP", quality=92, method=6)

    return {
        "source_resolution": [width, height],
        "delivery_resolution": [1920, 1080],
        "fps": round(fps, 3),
        "source_frame_count": frame_count,
        "written_frame_count": written,
        "duration_seconds": round(written / fps, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--asset-dir", type=Path, required=True)
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    asset_dir = args.asset_dir.resolve()
    output = asset_dir / "web" / "abu_opening_scene_v10.mp4"
    poster = asset_dir / "posters" / "abu_opening_scene_v10.webp"
    metadata = encode(source, output, poster)
    manifest = {
        "asset_pack": "ABU Opening Scene",
        "version": SCENE_VERSION,
        "source": {
            "filename": source.name,
            "sha256": sha256(source),
            "designer_icon_removed": True,
        },
        "delivery": {
            **metadata,
            "video": "web/abu_opening_scene_v10.mp4",
            "video_sha256": sha256(output),
            "poster": "posters/abu_opening_scene_v10.webp",
            "poster_sha256": sha256(poster),
            "quality_note": "1080p delivery enhanced from the approved 720p source; no synthetic detail claim.",
        },
        "transition": {
            "background": "transition/abu_opening_background_v10.webp",
            "character": "transition/abu_opening_character_v10.png",
            "destination": "#abuStage",
        },
    }
    (asset_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
