from __future__ import annotations

import hashlib
import json
import os
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    os.environ.get(
        "V50_ABU_SEATED_IDLE_V3_SOURCE",
        str(Path.home() / "Downloads/Regenerate_this_exact_animatio.mp4"),
    )
).expanduser()
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v12-actor-pass"
ACTION_DIR = ASSET_ROOT / "abu-01-seated-idle-loop-v3"
ARTIFACT_ROOT = ROOT / "artifacts/abu-actor-pass-v1"
LIBRARY = ASSET_ROOT / "library.json"
INVENTORY = ASSET_ROOT / "video-inventory.json"
GLOBAL_REGISTRY = ROOT / "config/media_asset_registry_v1.json"
MOTION_REGISTRY = ASSET_ROOT.parent / "motion-registry.js"

CATALOG_ID = "ABU_01_SEATED_IDLE_LOOP_V3"
ACTION_ID = "abu_01_seated_idle_loop_v3"
SOURCE_ID = "abu_01_seated_idle_loop_v3_source"
ACTION_STATUS = "production"
LIBRARY_STATUS = "LIBRARY_READY"
PRODUCT_ROLE = "seated_idle_companion"
FPS = 24
SOURCE_FRAME_COUNT = 240
CANVAS = (960, 720)
BOTTOM_ANCHOR = 704
TARGET_VISIBLE_HEIGHT = 620
SOURCE_ISOLATION_WIDTH = 1040
ALPHA_THRESHOLD = 24
LOOP_BLEND_FRAMES = 12
KEY_FILTER = (
    f"fps={FPS},crop={SOURCE_ISOLATION_WIDTH}:720:0:0,format=rgba,"
    "colorkey=0x19a61e:0.17:0.07,"
    "despill=type=green:mix=0.55:expand=0.05,format=rgba"
)


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def extract_keyed_frames(output_dir: Path) -> list[Image.Image]:
    pattern = output_dir / "frame-%04d.png"
    run(
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(SOURCE),
        "-vf",
        KEY_FILTER,
        str(pattern),
    )
    frames = []
    for path in sorted(output_dir.glob("frame-*.png")):
        frame = Image.open(path).convert("RGBA")
        pixels = np.asarray(frame).copy()
        pixels[pixels[:, :, 3] < ALPHA_THRESHOLD] = 0
        frames.append(Image.fromarray(pixels, "RGBA"))
    if len(frames) != SOURCE_FRAME_COUNT:
        raise RuntimeError(
            f"expected {SOURCE_FRAME_COUNT} keyed frames, got {len(frames)}"
        )
    return frames


def visible_box(frame: Image.Image) -> tuple[int, int, int, int]:
    box = frame.getchannel("A").getbbox()
    if not box:
        raise RuntimeError("green-screen extraction produced an empty frame")
    return box


def head_anchor_x(frame: Image.Image, box: tuple[int, int, int, int]) -> float:
    alpha = np.asarray(frame.getchannel("A"), dtype=np.float32)
    top, bottom = box[1], box[3]
    head_bottom = min(bottom, top + round((bottom - top) * 0.46))
    band = alpha[top:head_bottom, box[0] : box[2]]
    weights = band.sum(axis=0)
    total = float(weights.sum())
    if total <= 0:
        return (box[0] + box[2]) / 2
    positions = np.arange(box[0], box[2], dtype=np.float32)
    return float((positions * weights).sum() / total)


def normalize_frames(frames: list[Image.Image]) -> tuple[list[Image.Image], dict]:
    boxes = [visible_box(frame) for frame in frames]
    heights = [box[3] - box[1] for box in boxes]
    endpoint_window = 12
    first_height = float(statistics.median(heights[:endpoint_window]))
    last_height = float(statistics.median(heights[-endpoint_window:]))
    delivery_scale = TARGET_VISIBLE_HEIGHT / first_height

    normalized = []
    anchor_positions = []
    visible_heights = []
    for index, (frame, box) in enumerate(zip(frames, boxes, strict=True)):
        progress = index / (len(frames) - 1)
        trend_height = first_height + (last_height - first_height) * progress
        scale = delivery_scale * first_height / trend_height
        padding = 4
        crop_box = (
            max(0, box[0] - padding),
            max(0, box[1] - padding),
            min(frame.width, box[2] + padding),
            min(frame.height, box[3] + padding),
        )
        actor = frame.crop(crop_box)
        size = (
            max(1, round(actor.width * scale)),
            max(1, round(actor.height * scale)),
        )
        actor = actor.resize(size, Image.Resampling.LANCZOS)

        source_anchor_x = head_anchor_x(frame, box)
        anchor_x_offset = (source_anchor_x - crop_box[0]) * scale
        actor_bottom_offset = (box[3] - crop_box[1]) * scale
        x = round(CANVAS[0] / 2 - anchor_x_offset)
        y = round(BOTTOM_ANCHOR - actor_bottom_offset)

        canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        canvas.alpha_composite(actor, (x, y))
        composited_box = visible_box(canvas)
        anchor_correction = BOTTOM_ANCHOR - composited_box[3]
        if anchor_correction:
            anchored = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
            anchored.alpha_composite(canvas, (0, anchor_correction))
            canvas = anchored
        normalized.append(canvas)
        output_box = visible_box(canvas)
        anchor_positions.append(output_box[3])
        visible_heights.append(output_box[3] - output_box[1])

    return normalized, {
        "source_first_height": heights[0],
        "source_last_height": heights[-1],
        "source_first_bottom": boxes[0][3],
        "source_last_bottom": boxes[-1][3],
        "source_bottom_range": [min(box[3] for box in boxes), max(box[3] for box in boxes)],
        "endpoint_median_heights": [first_height, last_height],
        "output_bottom_anchor_range": [min(anchor_positions), max(anchor_positions)],
        "output_visible_height_range": [min(visible_heights), max(visible_heights)],
    }


def blend_rgba(first: Image.Image, second: Image.Image, weight: float) -> Image.Image:
    if weight >= 1:
        return second.copy()
    a = np.asarray(first, dtype=np.float32) / 255
    b = np.asarray(second, dtype=np.float32) / 255
    alpha_a = a[:, :, 3:4]
    alpha_b = b[:, :, 3:4]
    alpha = alpha_a * (1 - weight) + alpha_b * weight
    premultiplied = (
        a[:, :, :3] * alpha_a * (1 - weight)
        + b[:, :, :3] * alpha_b * weight
    )
    rgb = np.divide(
        premultiplied,
        alpha,
        out=np.zeros_like(premultiplied),
        where=alpha > 1e-6,
    )
    rgba = np.concatenate((rgb, alpha), axis=2)
    return Image.fromarray(np.clip(rgba * 255 + 0.5, 0, 255).astype(np.uint8), "RGBA")


def close_loop(frames: list[Image.Image]) -> list[Image.Image]:
    repaired = [frame.copy() for frame in frames]
    target = repaired[0]
    start = len(repaired) - LOOP_BLEND_FRAMES
    for index in range(LOOP_BLEND_FRAMES):
        progress = (index + 1) / LOOP_BLEND_FRAMES
        smooth_weight = progress * progress * (3 - 2 * progress)
        repaired[start + index] = blend_rgba(
            repaired[start + index],
            target,
            smooth_weight,
        )
    repaired[-1] = target.copy()
    return repaired


def frame_mae(first: Image.Image, second: Image.Image) -> float:
    a = np.asarray(first, dtype=np.int16)
    b = np.asarray(second, dtype=np.int16)
    return float(np.abs(a - b).mean())


def checkerboard(size: tuple[int, int], cell: int = 24) -> Image.Image:
    image = Image.new("RGBA", size, "#eef1ed")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle(
                    (x, y, x + cell - 1, y + cell - 1),
                    fill="#d7ddd8",
                )
    return image


def save_webm(frames: list[Image.Image], path: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgba",
        "-video_size",
        f"{CANVAS[0]}x{CANVAS[1]}",
        "-framerate",
        str(FPS),
        "-i",
        "pipe:0",
        "-an",
        "-c:v",
        "libvpx-vp9",
        "-b:v",
        "0",
        "-crf",
        "24",
        "-pix_fmt",
        "yuva420p",
        "-auto-alt-ref",
        "0",
        "-metadata:s:v:0",
        "alpha_mode=1",
        str(path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    if not process.stdin:
        raise RuntimeError("ffmpeg stdin is unavailable")
    try:
        for frame in frames:
            process.stdin.write(frame.tobytes())
        process.stdin.close()
    finally:
        return_code = process.wait()
    if return_code:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"transparent WebM encode failed with exit code {return_code}")


def save_checkerboard_preview(frames: list[Image.Image], path: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        f"{CANVAS[0]}x{CANVAS[1]}",
        "-framerate",
        str(FPS),
        "-i",
        "pipe:0",
        "-an",
        "-c:v",
        "libx264",
        "-crf",
        "19",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    if not process.stdin:
        raise RuntimeError("ffmpeg stdin is unavailable")
    background = checkerboard(CANVAS)
    try:
        for frame in frames:
            preview = background.copy()
            preview.alpha_composite(frame)
            process.stdin.write(preview.convert("RGB").tobytes())
        process.stdin.close()
    finally:
        return_code = process.wait()
    if return_code:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"checkerboard preview encode failed with exit code {return_code}")


def save_contact_sheet(frames: list[Image.Image], path: Path) -> None:
    columns, rows = 5, 2
    tile = (320, 240)
    sheet = Image.new("RGB", (tile[0] * columns, tile[1] * rows), "white")
    indexes = [
        round(index * (len(frames) - 1) / (columns * rows - 1))
        for index in range(columns * rows)
    ]
    for slot, frame_index in enumerate(indexes):
        background = checkerboard(tile)
        actor = frames[frame_index].copy()
        actor.thumbnail((tile[0] - 16, tile[1] - 16), Image.Resampling.LANCZOS)
        x = (tile[0] - actor.width) // 2
        y = tile[1] - actor.height
        background.alpha_composite(actor, (x, y))
        sheet.paste(
            background.convert("RGB"),
            ((slot % columns) * tile[0], (slot // columns) * tile[1]),
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=94, optimize=True)


def save_outputs(frames: list[Image.Image], stabilization: dict) -> dict:
    web_dir = ACTION_DIR / "web"
    frame_dir = ACTION_DIR / "frames"
    poster_dir = ACTION_DIR / "posters"
    contact_dir = ACTION_DIR / "contact-sheets"
    preview_dir = ACTION_DIR / "previews"
    if ACTION_DIR.exists():
        shutil.rmtree(ACTION_DIR)
    for directory in (web_dir, frame_dir, poster_dir, contact_dir, preview_dir):
        directory.mkdir(parents=True, exist_ok=True)

    frame_paths = []
    for index, frame in enumerate(frames, start=1):
        path = frame_dir / f"frame-{index:04d}.png"
        frame.save(path, optimize=True)
        frame_paths.append(path)

    webm = web_dir / f"{ACTION_ID}.webm"
    webp = web_dir / f"{ACTION_ID}.webp"
    poster = poster_dir / f"{ACTION_ID}.png"
    contact = contact_dir / f"{ACTION_ID}_contact_sheet.png"
    preview = preview_dir / f"{ACTION_ID}_checkerboard.mp4"
    save_webm(frames, webm)
    frames[0].save(
        webp,
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / FPS),
        loop=0,
        quality=92,
        method=3,
        minimize_size=False,
    )
    frames[0].save(poster, optimize=True)
    save_contact_sheet(frames, contact)
    save_checkerboard_preview(frames, preview)

    consecutive = [
        frame_mae(frames[index], frames[index + 1])
        for index in range(len(frames) - 1)
    ]
    loop_metrics = {
        "first_last_rgba_mae": frame_mae(frames[0], frames[-1]),
        "first_last_png_identical": sha256(frame_paths[0]) == sha256(frame_paths[-1]),
        "median_consecutive_rgba_mae": round(statistics.median(consecutive), 6),
        "max_consecutive_rgba_mae": round(max(consecutive), 6),
        "loop_blend_frames": LOOP_BLEND_FRAMES,
        "loop_blend_duration_ms": round(LOOP_BLEND_FRAMES / FPS * 1000),
        "method": "stabilized_endpoint_crossfade_to_exact_first_frame",
    }
    frame_manifest = {
        "pattern": "frames/frame-%04d.png",
        "first_frame_sha256": sha256(frame_paths[0]),
        "last_frame_sha256": sha256(frame_paths[-1]),
        "aggregate_sha256": hashlib.sha256(
            "".join(sha256(path) for path in frame_paths).encode("ascii")
        ).hexdigest(),
    }
    return {
        "webm": webm,
        "webp": webp,
        "poster": poster,
        "contact": contact,
        "preview": preview,
        "frame_paths": frame_paths,
        "frame_manifest": frame_manifest,
        "loop_metrics": loop_metrics,
        "stabilization": stabilization,
    }


def archive_source() -> Path:
    archive = (
        ARTIFACT_ROOT
        / "source-videos"
        / "abu_01_seated_idle_loop_v3_source.mp4"
    )
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, archive)
    return archive


def build_manifest(outputs: dict, archive: Path) -> dict:
    webm = outputs["webm"]
    webp = outputs["webp"]
    poster = outputs["poster"]
    contact = outputs["contact"]
    preview = outputs["preview"]
    manifest = {
        "version": "v50.abu.green_screen_motion.v2",
        "catalog_id": CATALOG_ID,
        "action_id": ACTION_ID,
        "status": ACTION_STATUS,
        "source_status": "SOURCE_APPROVED",
        "library_status": LIBRARY_STATUS,
        "character_version": "ABU_CHARACTER_V1",
        "action_family": "companion_idle",
        "product_role": PRODUCT_ROLE,
        "source": {
            "filename": SOURCE.name,
            "archived_source": str(archive.relative_to(ROOT)),
            "sha256": sha256(SOURCE),
            "size": [1280, 720],
            "fps": FPS,
            "frame_count": SOURCE_FRAME_COUNT,
            "duration_ms": 10005,
            "audio": "aac_48khz_stereo_removed",
        },
        "canvas": list(CANVAS),
        "anchor": [0.5, BOTTOM_ANCHOR / CANVAS[1]],
        "frame_count": len(outputs["frame_paths"]),
        "fps": FPS,
        "duration_ms": round(len(outputs["frame_paths"]) / FPS * 1000),
        "transparent_background": True,
        "audio_removed": True,
        "fixed_character_scale": True,
        "fixed_bottom_anchor": True,
        "watermark_removed": True,
        "removed_regions": [
            {
                "name": "lower_right_four_point_platform_mark",
                "source_rect": [SOURCE_ISOLATION_WIDTH, 0, 1280, 720],
                "method": "character_isolation_before_alpha_delivery",
            }
        ],
        "alpha_matte": {
            "key_color": "#19a61e",
            "similarity": 0.17,
            "blend": 0.07,
            "alpha_floor": ALPHA_THRESHOLD,
            "despill": {"type": "green", "mix": 0.55, "expand": 0.05},
        },
        "stabilization": outputs["stabilization"],
        "loop_validation": outputs["loop_metrics"],
        "frame_sequence": outputs["frame_manifest"],
        "video": str(webm.relative_to(ACTION_DIR)),
        "animation": str(webp.relative_to(ACTION_DIR)),
        "poster": str(poster.relative_to(ACTION_DIR)),
        "contact_sheet": str(contact.relative_to(ACTION_DIR)),
        "checkerboard_preview": str(preview.relative_to(ACTION_DIR)),
        "delivery_sha256": {
            "webm": sha256(webm),
            "webp": sha256(webp),
            "poster": sha256(poster),
            "checkerboard_preview": sha256(preview),
        },
        "delivery_bytes": {
            "webm": webm.stat().st_size,
            "webp": webp.stat().st_size,
            "png_frames": sum(
                path.stat().st_size for path in outputs["frame_paths"]
            ),
            "checkerboard_preview": preview.stat().st_size,
        },
        "actor_contract": {
            "facing": "front",
            "gaze_target": "audience",
            "safe_crop": "full_body",
            "background": "transparent",
            "flip_horizontal": False,
            "loop_mode": "loop",
            "mouth_state": "closed",
            "recommended_contexts": [
                "dream_world_quiet_companion",
                "workspace_companion_idle",
                "theater_finale_idle",
            ],
        },
        "quality_gate": {
            "character_lock": "PASS",
            "motion": "PASS",
            "camera": "PASS",
            "background": "PASS",
            "first_last_loop": "PASS_AFTER_POSTPROCESS",
            "technical_format": "PASS_AFTER_POSTPROCESS",
            "library_ready": "PASS_OWNER_APPROVED_2026_07_23",
        },
        "boundaries": {
            "runtime_registered": True,
            "runtime_default_changed": False,
            "creates_mingli_claim": False,
            "changes_case_state": False,
            "do_not_use_for": [
                "专业结论宣判",
                "命运吉凶暗示",
                "忙碌计算状态",
            ],
        },
    }
    write_json(ACTION_DIR / "manifest.json", manifest)
    return manifest


def update_inventory(manifest: dict) -> None:
    inventory = read_json(INVENTORY)
    inventory["sources"] = [
        source
        for source in inventory["sources"]
        if source["source_id"] != SOURCE_ID
    ]
    inventory["sources"].append(
        {
            "source_id": SOURCE_ID,
            "filename": SOURCE.name,
            "archived_source": manifest["source"]["archived_source"],
            "sha256": manifest["source"]["sha256"],
            "background": "green_screen",
            "actions": ["sit", "blink", "ear_twitch", "tail_twitch", "breathe"],
            "selected_ranges": [
                {"seconds": [0.0, 10.0], "action_id": ACTION_ID}
            ],
            "quality": "owner_approved_library_ready",
            "notes": [
                "Character Lock, motion, camera and background passed designer review.",
                "Audio, platform mark, anchor drift and loop seam were removed in deterministic postprocess.",
                "Owner promoted ABU_01_SEATED_IDLE_LOOP_V3 to LIBRARY_READY on 2026-07-23.",
                "The promoted action is runtime-addressable but does not replace the current default.",
            ],
            "removed_regions": [
                "green_screen",
                "lower_right_four_point_platform_mark",
                "aac_audio_track",
                "scale_and_bottom_anchor_drift",
                "first_last_loop_seam",
            ],
        }
    )
    write_json(INVENTORY, inventory)


def update_library(manifest: dict) -> None:
    library = read_json(LIBRARY)
    library["actions"] = [
        action
        for action in library["actions"]
        if action["action_id"] != ACTION_ID
    ]
    library["actions"].append(
        {
            "action_id": ACTION_ID,
            "catalog_id": CATALOG_ID,
            "action_family": "companion_idle",
            "status": ACTION_STATUS,
            "source_status": manifest["source_status"],
            "library_status": manifest["library_status"],
            "character_version": manifest["character_version"],
            "label_zh": "阿布坐姿呼吸标准循环 V3",
            "description_zh": "阿布全程安静坐姿、闭嘴呼吸，包含一次眨眼与克制的耳尾小动作；透明抠像、脚底锚点和无跳点循环均已通过验收。",
            "product_role": PRODUCT_ROLE,
            "do_not_use_for": manifest["boundaries"]["do_not_use_for"],
            "manifest": "abu-01-seated-idle-loop-v3/manifest.json",
            "video": f"abu-01-seated-idle-loop-v3/web/{ACTION_ID}.webm",
            "animation": f"abu-01-seated-idle-loop-v3/web/{ACTION_ID}.webp",
            "poster": f"abu-01-seated-idle-loop-v3/posters/{ACTION_ID}.png",
            "contact_sheet": (
                "abu-01-seated-idle-loop-v3/contact-sheets/"
                f"{ACTION_ID}_contact_sheet.png"
            ),
            "checkerboard_preview": (
                "abu-01-seated-idle-loop-v3/previews/"
                f"{ACTION_ID}_checkerboard.mp4"
            ),
            "duration_ms": manifest["duration_ms"],
            "display_scale": 1.0,
            "loop_mode": "loop",
            "facing": "front",
            "gaze_target": "audience",
            "safe_crop": "full_body",
            "recommended_contexts": manifest["actor_contract"][
                "recommended_contexts"
            ],
        }
    )
    write_json(LIBRARY, library)


def update_global_registry() -> None:
    registry = read_json(GLOBAL_REGISTRY)
    abu_motion = registry["abu_motion"]
    abu_motion["sha256"] = sha256(MOTION_REGISTRY)
    abu_motion["library"] = str(LIBRARY.relative_to(ROOT))
    abu_motion["library_sha256"] = sha256(LIBRARY)
    abu_motion["source_inventory"] = str(INVENTORY.relative_to(ROOT))
    abu_motion["source_inventory_sha256"] = sha256(INVENTORY)
    write_json(GLOBAL_REGISTRY, registry)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"missing Abu source video: {SOURCE}")
    archive = archive_source()
    with tempfile.TemporaryDirectory(prefix="abu-seated-idle-loop-v3-") as name:
        keyed = extract_keyed_frames(Path(name))
        normalized, stabilization = normalize_frames(keyed)
        loop_frames = close_loop(normalized)
    outputs = save_outputs(loop_frames, stabilization)
    manifest = build_manifest(outputs, archive)
    update_inventory(manifest)
    update_library(manifest)
    update_global_registry()
    print(
        json.dumps(
            {
                "catalog_id": CATALOG_ID,
                "action_id": ACTION_ID,
                "source_status": manifest["source_status"],
                "library_status": manifest["library_status"],
                "default_action_changed": False,
                "frame_count": manifest["frame_count"],
                "duration_ms": manifest["duration_ms"],
                "first_last_rgba_mae": manifest["loop_validation"][
                    "first_last_rgba_mae"
                ],
                "preview": str(outputs["preview"]),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
