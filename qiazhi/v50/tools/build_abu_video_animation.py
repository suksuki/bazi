from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


CANVAS_SIZE = 512
CHARACTER_MAX_SIZE = 456
BOTTOM_ANCHOR = 494
FPS = 15

SEGMENTS = {
    "idle_blink": (0.0, 2.05),
    "head_tilt": (2.0, 4.7),
    "caution_ears": (4.65, 6.7),
    "happy_tail": (6.65, 9.05),
}


def build(
    *,
    frames_dir: Path,
    output_dir: Path,
    canvas_size: int = CANVAS_SIZE,
    character_max_size: int = CHARACTER_MAX_SIZE,
    bottom_anchor: int = BOTTOM_ANCHOR,
    quality: int = 86,
    method: int = 3,
) -> dict[str, object]:
    frame_paths = sorted(frames_dir.glob("frame_*.png"))
    if len(frame_paths) < 2:
        raise ValueError("at least two extracted frames are required")

    source_frames = [Image.open(path).convert("RGB") for path in frame_paths]
    crop_box = _character_union_box(source_frames)
    transparent_frames = [
        _transparent_canvas(
            frame,
            crop_box=crop_box,
            canvas_width=canvas_size,
            canvas_height=canvas_size,
            character_max_width=character_max_size,
            character_max_height=character_max_size,
            bottom_anchor=bottom_anchor,
        )
        for frame in source_frames
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    web_dir = output_dir / "web"
    poster_dir = output_dir / "posters"
    web_dir.mkdir(exist_ok=True)
    poster_dir.mkdir(exist_ok=True)

    assets: dict[str, dict[str, object]] = {}
    for state, (start_seconds, end_seconds) in SEGMENTS.items():
        start = max(0, round(start_seconds * FPS))
        end = min(len(transparent_frames), round(end_seconds * FPS) + 1)
        frames = transparent_frames[start:end]
        if len(frames) < 2:
            raise ValueError(f"segment {state} has too few frames")
        web_path = web_dir / f"abu_{state}_v4.webp"
        poster_path = poster_dir / f"abu_{state}_v4.png"
        _save_animated_webp(frames, web_path, quality=quality, method=method)
        frames[0].save(poster_path, optimize=True)
        assets[state] = {
            "animation": f"web/{web_path.name}",
            "poster": f"posters/{poster_path.name}",
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "frame_count": len(frames),
            "duration_ms": round(len(frames) * 1000 / FPS),
            "bytes": web_path.stat().st_size,
        }

    sample_indexes = [0, len(transparent_frames) // 3, 2 * len(transparent_frames) // 3, len(transparent_frames) - 1]
    for index in sample_indexes:
        transparent_frames[index].save(output_dir / f"sample_{index:03d}.png", optimize=True)

    manifest: dict[str, object] = {
        "version": "v50.abu.video_derived_animation_pack.v4",
        "status": "production_candidate",
        "source_frame_count": len(source_frames),
        "source_fps": FPS,
        "canvas": [canvas_size, canvas_size],
        "anchor": [0.5, bottom_anchor / canvas_size],
        "webp": {"quality": quality, "method": method},
        "transparent_background": True,
        "watermark_removed": True,
        "watermark_removal_method": "fixed character isolation before alpha extraction",
        "crop_box": list(crop_box),
        "assets": assets,
        "state_mapping": {
            "idle": "idle_blink",
            "thinking": "head_tilt",
            "caution": "caution_ears",
            "wave": "happy_tail",
            "confidence_up": "happy_tail",
        },
        "boundaries": {
            "creates_mingli_claim": False,
            "changes_case_state": False,
            "calls_llm": False,
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def _character_union_box(frames: list[Image.Image]) -> tuple[int, int, int, int]:
    min_x, min_y = frames[0].width, frames[0].height
    max_x = max_y = 0
    character_limit = round(frames[0].width * 0.82)
    for frame in frames:
        pixels = np.asarray(frame)
        brightness = pixels.max(axis=2)
        mask = brightness > 12
        mask[:, character_limit:] = False
        ys, xs = np.where(mask)
        if not len(xs):
            continue
        min_x = min(min_x, int(xs.min()))
        min_y = min(min_y, int(ys.min()))
        max_x = max(max_x, int(xs.max()) + 1)
        max_y = max(max_y, int(ys.max()) + 1)
    if max_x <= min_x or max_y <= min_y:
        raise ValueError("character could not be isolated from the video background")
    padding = 24
    return (
        max(0, min_x - padding),
        max(0, min_y - padding),
        min(frames[0].width, max_x + padding),
        min(frames[0].height, max_y + padding),
    )


def _transparent_canvas(
    frame: Image.Image,
    *,
    crop_box: tuple[int, int, int, int],
    alpha_low: float = 9.0,
    alpha_high: float = 29.0,
    canvas_width: int = CANVAS_SIZE,
    canvas_height: int = CANVAS_SIZE,
    character_max_width: int = CHARACTER_MAX_SIZE,
    character_max_height: int = CHARACTER_MAX_SIZE,
    bottom_anchor: int = BOTTOM_ANCHOR,
) -> Image.Image:
    rgb = np.asarray(frame.crop(crop_box)).astype(np.uint8)
    brightness = rgb.max(axis=2).astype(np.float32)
    alpha = np.clip((brightness - alpha_low) * (255.0 / (alpha_high - alpha_low)), 0, 255).astype(np.uint8)
    alpha[brightness <= alpha_low] = 0
    alpha[brightness >= alpha_high] = 255
    rgba = np.dstack([rgb, alpha])
    character = Image.fromarray(rgba, mode="RGBA")
    scale = min(character_max_width / character.width, character_max_height / character.height)
    size = (max(1, round(character.width * scale)), max(1, round(character.height * scale)))
    character = character.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    x = (canvas_width - character.width) // 2
    y = bottom_anchor - character.height
    canvas.alpha_composite(character, (x, y))
    return canvas


def _save_animated_webp(
    frames: list[Image.Image],
    path: Path,
    *,
    quality: int = 86,
    method: int = 3,
    loop_count: int = 0,
) -> None:
    duration = round(1000 / FPS)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=loop_count,
        format="WEBP",
        quality=quality,
        method=method,
        minimize_size=False,
    )
    probe = Image.open(path)
    if getattr(probe, "n_frames", 1) != len(frames):
        raise ValueError(f"animated WebP frame mismatch for {path.name}")
    probe.seek(len(frames) // 2)
    if probe.convert("RGBA").getextrema()[3][0] != 0:
        raise ValueError(f"animated WebP lost transparency for {path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build transparent Abu state animations from extracted video frames.")
    parser.add_argument("frames_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--canvas-size", type=int, default=CANVAS_SIZE)
    parser.add_argument("--character-max-size", type=int, default=CHARACTER_MAX_SIZE)
    parser.add_argument("--bottom-anchor", type=int, default=BOTTOM_ANCHOR)
    parser.add_argument("--quality", type=int, default=86)
    parser.add_argument("--method", type=int, default=3)
    args = parser.parse_args()
    manifest = build(
        frames_dir=args.frames_dir,
        output_dir=args.output_dir,
        canvas_size=args.canvas_size,
        character_max_size=args.character_max_size,
        bottom_anchor=args.bottom_anchor,
        quality=args.quality,
        method=args.method,
    )
    print(json.dumps({"status": "built", "output": str(args.output_dir), "assets": manifest["assets"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
