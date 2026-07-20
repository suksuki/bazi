from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from build_abu_video_animation import (
    BOTTOM_ANCHOR,
    CANVAS_SIZE,
    FPS,
    _character_union_box,
    _save_animated_webp,
    _transparent_canvas,
)


def build_motion(
    *,
    frames_dir: Path,
    output_dir: Path,
    source_video: Path,
    motion: str,
    start_seconds: float,
    end_seconds: float,
    version: str,
    usage: list[str] | None = None,
    alpha_low: float = 9.0,
    alpha_high: float = 29.0,
    crop_box_override: tuple[int, int, int, int] | None = None,
    canvas_width: int = CANVAS_SIZE,
    canvas_height: int = CANVAS_SIZE,
    character_max_width: int = 456,
    character_max_height: int = 456,
    bottom_anchor: int = BOTTOM_ANCHOR,
    quality: int = 86,
    method: int = 3,
    display_scale: float = 1.0,
    stage_profile: str = "standard",
    playback: str = "loop",
    category: str = "workflow",
    loop_count: int = 0,
    action_id: str | None = None,
    action_family: str = "guidance",
    facing: str = "front",
    gaze_target: str = "none",
    safe_crop: str = "full_body",
    flip_horizontal: bool = False,
) -> dict[str, object]:
    if alpha_high <= alpha_low:
        raise ValueError("alpha_high must be greater than alpha_low")
    frame_paths = sorted(frames_dir.glob("frame_*.png"))
    if len(frame_paths) < 2:
        raise ValueError("at least two extracted frames are required")

    source_frames = [Image.open(path).convert("RGB") for path in frame_paths]
    crop_box = crop_box_override or _character_union_box(source_frames)
    start = max(0, round(start_seconds * FPS))
    end = min(len(source_frames), round(end_seconds * FPS) + 1)
    selected = source_frames[start:end]
    if len(selected) < 2:
        raise ValueError("selected motion segment has too few frames")
    transparent_frames = [
        _transparent_canvas(
            frame,
            crop_box=crop_box,
            alpha_low=alpha_low,
            alpha_high=alpha_high,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            character_max_width=character_max_width,
            character_max_height=character_max_height,
            bottom_anchor=bottom_anchor,
        )
        for frame in selected
    ]
    if flip_horizontal:
        transparent_frames = [ImageOps.mirror(frame) for frame in transparent_frames]

    web_dir = output_dir / "web"
    poster_dir = output_dir / "posters"
    contact_sheet_dir = output_dir / "contact-sheets"
    web_dir.mkdir(parents=True, exist_ok=True)
    poster_dir.mkdir(parents=True, exist_ok=True)
    contact_sheet_dir.mkdir(parents=True, exist_ok=True)
    web_path = web_dir / f"abu_{motion}_{version}.webp"
    video_path = web_dir / f"abu_{motion}_{version}.webm"
    poster_path = poster_dir / f"abu_{motion}_{version}.png"
    contact_sheet_path = contact_sheet_dir / f"abu_{motion}_{version}_contact_sheet.png"
    _save_animated_webp(
        transparent_frames,
        web_path,
        quality=quality,
        method=method,
        loop_count=loop_count,
    )
    _save_transparent_webm(transparent_frames, video_path)
    _save_contact_sheet(transparent_frames, contact_sheet_path)
    transparent_frames[0].save(poster_path, optimize=True)

    source_hash = hashlib.sha256(source_video.read_bytes()).hexdigest()
    manifest: dict[str, object] = {
        "version": f"v50.abu.designer_motion.{version}",
        "status": "production",
        "motion": motion,
        "action_id": action_id or f"abu_{motion}_{version}",
        "action_family": action_family,
        "source_type": "extracted_video",
        "source": {
            "filename": source_video.name,
            "sha256": source_hash,
            "frame_count": len(source_frames),
            "fps": FPS,
            "segment_seconds": [start_seconds, end_seconds],
        },
        "canvas": [canvas_width, canvas_height],
        "anchor": [0.5, bottom_anchor / canvas_height],
        "actor_contract": {
            "facing": facing,
            "gaze_target": gaze_target,
            "safe_crop": safe_crop,
            "background": "transparent",
            "flip_horizontal": flip_horizontal,
            "loop_mode": playback,
            "recommended_contexts": usage or [],
        },
        "source_size": [source_frames[0].width, source_frames[0].height],
        "character_crop_box": list(crop_box),
        "transparent_background": True,
        "fixed_character_scale": True,
        "watermark_removed": True,
        "removed_regions": [
            {
                "name": "source_right_side_color_mark",
                "method": "excluded_before_alpha_extraction",
            }
        ],
        "alpha_matte": {"low": alpha_low, "high": alpha_high},
        "webp": {"quality": quality, "method": method, "loop_count": loop_count},
        "runtime_display": {
            "scale": display_scale,
            "stage_profile": stage_profile,
            "playback": playback,
            "category": category,
        },
        "animation": f"web/{web_path.name}",
        "video": f"web/{video_path.name}",
        "poster": f"posters/{poster_path.name}",
        "contact_sheet": f"contact-sheets/{contact_sheet_path.name}",
        "frame_count": len(transparent_frames),
        "duration_ms": round(len(transparent_frames) * 1000 / FPS),
        "bytes": web_path.stat().st_size,
        "delivery_bytes": {
            "webp": web_path.stat().st_size,
            "webm": video_path.stat().st_size,
        },
        "usage": usage or [],
        "boundaries": {
            "emotion_tracks_workflow_not_fate": True,
            "creates_mingli_claim": False,
            "changes_case_state": False,
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def _save_transparent_webm(frames: list[Image.Image], path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to build transparent WebM delivery")
    width, height = frames[0].size
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgba",
        "-video_size",
        f"{width}x{height}",
        "-framerate",
        str(FPS),
        "-i",
        "pipe:0",
        "-an",
        "-c:v",
        "libvpx-vp9",
        "-pix_fmt",
        "yuva420p",
        "-lossless",
        "1",
        "-auto-alt-ref",
        "0",
        "-row-mt",
        "1",
        "-metadata:s:v:0",
        "alpha_mode=1",
        str(path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        if not process.stdin:
            raise RuntimeError("ffmpeg stdin is unavailable")
        for frame in frames:
            process.stdin.write(frame.convert("RGBA").tobytes())
        process.stdin.close()
    finally:
        return_code = process.wait()
    if return_code != 0:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"transparent WebM encode failed with exit code {return_code}")


def _save_contact_sheet(frames: list[Image.Image], path: Path) -> None:
    columns, rows = 4, 2
    tile = 240
    sheet = Image.new("RGB", (columns * tile, rows * tile), "#dbe2dd")
    draw = ImageDraw.Draw(sheet)
    square = 20
    for y in range(0, sheet.height, square):
        for x in range(0, sheet.width, square):
            color = "#eef1ed" if (x // square + y // square) % 2 == 0 else "#d7ddd8"
            draw.rectangle((x, y, x + square, y + square), fill=color)
    indexes = [round(index * (len(frames) - 1) / (columns * rows - 1)) for index in range(columns * rows)]
    for slot, frame_index in enumerate(indexes):
        frame = frames[frame_index].convert("RGBA")
        frame.thumbnail((tile - 16, tile - 16), Image.Resampling.LANCZOS)
        x = (slot % columns) * tile + (tile - frame.width) // 2
        y = (slot // columns) * tile + (tile - frame.height) // 2
        sheet.paste(frame, (x, y), frame)
    sheet.save(path, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build one production Abu motion from a designer video.")
    parser.add_argument("frames_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("source_video", type=Path)
    parser.add_argument("--motion", required=True)
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--end", type=float, required=True)
    parser.add_argument("--version", default="v5")
    parser.add_argument("--usage", nargs="*", default=[])
    parser.add_argument("--alpha-low", type=float, default=9.0)
    parser.add_argument("--alpha-high", type=float, default=29.0)
    parser.add_argument("--crop-box", type=int, nargs=4)
    parser.add_argument("--canvas-width", type=int, default=CANVAS_SIZE)
    parser.add_argument("--canvas-height", type=int, default=CANVAS_SIZE)
    parser.add_argument("--character-max-width", type=int, default=456)
    parser.add_argument("--character-max-height", type=int, default=456)
    parser.add_argument("--bottom-anchor", type=int, default=BOTTOM_ANCHOR)
    parser.add_argument("--quality", type=int, default=86)
    parser.add_argument("--method", type=int, default=3)
    parser.add_argument("--display-scale", type=float, default=1.0)
    parser.add_argument("--stage-profile", default="standard")
    parser.add_argument("--playback", choices=("loop", "hold", "one_shot"), default="loop")
    parser.add_argument("--category", choices=("guidance", "workflow", "ambient", "rest"), default="workflow")
    parser.add_argument("--loop-count", type=int, default=0)
    parser.add_argument("--action-id")
    parser.add_argument("--action-family", default="guidance")
    parser.add_argument("--facing", choices=("left", "right", "front"), default="front")
    parser.add_argument("--gaze-target", default="none")
    parser.add_argument("--safe-crop", default="full_body")
    parser.add_argument("--flip-horizontal", action="store_true")
    args = parser.parse_args()
    manifest = build_motion(
        frames_dir=args.frames_dir,
        output_dir=args.output_dir,
        source_video=args.source_video,
        motion=args.motion,
        start_seconds=args.start,
        end_seconds=args.end,
        version=args.version,
        usage=args.usage,
        alpha_low=args.alpha_low,
        alpha_high=args.alpha_high,
        crop_box_override=tuple(args.crop_box) if args.crop_box else None,
        canvas_width=args.canvas_width,
        canvas_height=args.canvas_height,
        character_max_width=args.character_max_width,
        character_max_height=args.character_max_height,
        bottom_anchor=args.bottom_anchor,
        quality=args.quality,
        method=args.method,
        display_scale=args.display_scale,
        stage_profile=args.stage_profile,
        playback=args.playback,
        category=args.category,
        loop_count=args.loop_count,
        action_id=args.action_id,
        action_family=args.action_family,
        facing=args.facing,
        gaze_target=args.gaze_target,
        safe_crop=args.safe_crop,
        flip_horizontal=args.flip_horizontal,
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
