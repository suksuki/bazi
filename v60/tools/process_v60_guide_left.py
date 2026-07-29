from __future__ import annotations

import hashlib
import os
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from process_v60_seated_idle import (
    checkerboard,
    frame_mae,
    head_anchor_x,
    read_json,
    run,
    sha256_file,
    visible_box,
    write_json,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEDIA_ID = "ABU_V60_05_GUIDE_LEFT_ONCE_V1"
MEDIA_REF = "media.abu.v60.guide-left.v1"
REVISION = "v1"
CHARACTER_VERSION = "ABU_CHARACTER_V60_V1"
SOURCE = Path(
    os.environ.get(
        "ABU_V60_GUIDE_LEFT_SOURCE",
        PROJECT_ROOT / "media" / "sources" / MEDIA_ID / REVISION / "source.mp4",
    )
)

FPS = 24
SOURCE_FRAME_COUNT = 240
SOURCE_START_FRAME = 12
SOURCE_END_FRAME_EXCLUSIVE = 116
SOURCE_PEAK_FRAME = 60
SOURCE_ISOLATION_WIDTH = 950
CANVAS = (960, 720)
BOTTOM_ANCHOR = 704
TARGET_VISIBLE_HEIGHT = 620
ALPHA_THRESHOLD = 18
KEY_FILTER = (
    f"fps={FPS},crop={SOURCE_ISOLATION_WIDTH}:720:0:0,format=rgba,"
    "colorkey=0x00bd14:0.20:0.08,"
    "despill=type=green:mix=0.60:expand=0.04,format=rgba"
)

MASTER_DIR = PROJECT_ROOT / "media" / "masters" / MEDIA_ID / REVISION
REVIEW_DIR = PROJECT_ROOT / "media" / "review" / MEDIA_ID / REVISION
DELIVERY_DIR = (
    PROJECT_ROOT
    / "web"
    / "public"
    / "assets"
    / "abu"
    / "v60"
    / "abu-v60-guide-left-once-v1"
)
MANIFEST_PATH = PROJECT_ROOT / "media" / "manifests" / f"{MEDIA_ID}.v1.json"
CATALOG_PATH = PROJECT_ROOT / "media" / "catalog.json"
REGISTRY_PATH = PROJECT_ROOT / "assets" / "registry.json"


def extract_keyed_frames(output_dir: Path) -> list[Image.Image]:
    run(
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(SOURCE),
        "-vf",
        KEY_FILTER,
        str(output_dir / "frame-%04d.png"),
    )
    frames: list[Image.Image] = []
    for path in sorted(output_dir.glob("frame-*.png")):
        pixels = np.asarray(Image.open(path).convert("RGBA")).copy()
        pixels[pixels[:, :, 3] < ALPHA_THRESHOLD] = 0
        frames.append(Image.fromarray(pixels, "RGBA"))
    if len(frames) != SOURCE_FRAME_COUNT:
        raise RuntimeError(
            f"expected {SOURCE_FRAME_COUNT} source frames, got {len(frames)}"
        )
    return frames


def normalize_frames(
    frames: list[Image.Image],
) -> tuple[list[Image.Image], dict[str, Any]]:
    boxes = [visible_box(frame) for frame in frames]
    if max(box[2] for box in boxes) >= SOURCE_ISOLATION_WIDTH - 8:
        raise RuntimeError("guide actor touches the source-window exclusion boundary")

    crop_padding = 6
    crop_box = (
        max(0, min(box[0] for box in boxes) - crop_padding),
        max(0, min(box[1] for box in boxes) - crop_padding),
        min(frames[0].width, max(box[2] for box in boxes) + crop_padding),
        min(frames[0].height, max(box[3] for box in boxes) + crop_padding),
    )
    neutral_window = min(12, len(frames))
    neutral_heights = [boxes[index][3] - boxes[index][1] for index in range(neutral_window)]
    scale = TARGET_VISIBLE_HEIGHT / statistics.median(neutral_heights)
    neutral_head_x = statistics.median(
        head_anchor_x(frames[index], boxes[index]) for index in range(neutral_window)
    )
    x = round(CANVAS[0] / 2 - (neutral_head_x - crop_box[0]) * scale)

    normalized: list[Image.Image] = []
    source_heights: list[int] = []
    output_heights: list[int] = []
    output_bottoms: list[int] = []
    output_boxes: list[tuple[int, int, int, int]] = []
    for frame, source_box in zip(frames, boxes, strict=True):
        actor = frame.crop(crop_box)
        actor = actor.resize(
            (
                max(1, round(actor.width * scale)),
                max(1, round(actor.height * scale)),
            ),
            Image.Resampling.LANCZOS,
        )
        source_bottom_offset = (source_box[3] - crop_box[1]) * scale
        y = round(BOTTOM_ANCHOR - source_bottom_offset)
        canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        canvas.alpha_composite(actor, (x, y))

        output_box = visible_box(canvas)
        correction = BOTTOM_ANCHOR - output_box[3]
        if correction:
            anchored = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
            anchored.alpha_composite(canvas, (0, correction))
            canvas = anchored
            output_box = visible_box(canvas)

        normalized.append(canvas)
        output_boxes.append(output_box)
        source_heights.append(source_box[3] - source_box[1])
        output_heights.append(output_box[3] - output_box[1])
        output_bottoms.append(output_box[3])

    return normalized, {
        "source_actor_bbox_union": [
            min(box[0] for box in boxes),
            min(box[1] for box in boxes),
            max(box[2] for box in boxes),
            max(box[3] for box in boxes),
        ],
        "source_visible_height_range": [min(source_heights), max(source_heights)],
        "normalization_crop": list(crop_box),
        "constant_scale": round(scale, 8),
        "output_bbox_union": [
            min(box[0] for box in output_boxes),
            min(box[1] for box in output_boxes),
            max(box[2] for box in output_boxes),
            max(box[3] for box in output_boxes),
        ],
        "output_visible_height_range": [min(output_heights), max(output_heights)],
        "output_bottom_anchor_range": [min(output_bottoms), max(output_bottoms)],
    }


def encode_webm(frames: list[Image.Image], path: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
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
    if process.stdin is None:
        raise RuntimeError("ffmpeg stdin is unavailable")
    for frame in frames:
        process.stdin.write(frame.tobytes())
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("VP9 alpha encode failed")


def encode_checkerboard(frames: list[Image.Image], path: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
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
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    if process.stdin is None:
        raise RuntimeError("ffmpeg stdin is unavailable")
    background = checkerboard(CANVAS)
    for frame in frames:
        preview = background.copy()
        preview.alpha_composite(frame)
        process.stdin.write(preview.convert("RGB").tobytes())
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("checkerboard encode failed")


def save_contact_sheet(frames: list[Image.Image], path: Path) -> None:
    columns, rows = 4, 3
    tile = (320, 240)
    sheet = Image.new("RGB", (columns * tile[0], rows * tile[1]), "white")
    indexes = [
        round(index * (len(frames) - 1) / (columns * rows - 1))
        for index in range(columns * rows)
    ]
    for slot, frame_index in enumerate(indexes):
        background = checkerboard(tile)
        actor = frames[frame_index].copy()
        actor.thumbnail((tile[0] - 16, tile[1] - 16), Image.Resampling.LANCZOS)
        background.alpha_composite(
            actor,
            ((tile[0] - actor.width) // 2, tile[1] - actor.height),
        )
        sheet.paste(
            background.convert("RGB"),
            ((slot % columns) * tile[0], (slot // columns) * tile[1]),
        )
    sheet.save(path, optimize=True)


def build_outputs(frames: list[Image.Image]) -> dict[str, Path]:
    for directory in (MASTER_DIR, REVIEW_DIR, DELIVERY_DIR):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)

    frame_dir = MASTER_DIR / "frames"
    frame_dir.mkdir()
    for index, frame in enumerate(frames):
        frame.save(frame_dir / f"frame-{index:04d}.png", optimize=True)

    webm = DELIVERY_DIR / "actor.webm"
    webp = DELIVERY_DIR / "actor.webp"
    poster = DELIVERY_DIR / "poster.png"
    checkerboard_path = REVIEW_DIR / "checkerboard.mp4"
    contact_sheet = REVIEW_DIR / "contact-sheet.png"

    encode_webm(frames, webm)
    frames[0].save(
        webp,
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / FPS),
        loop=1,
        quality=92,
        method=3,
        minimize_size=False,
    )
    frames[SOURCE_PEAK_FRAME - SOURCE_START_FRAME].save(poster, optimize=True)
    encode_checkerboard(frames, checkerboard_path)
    save_contact_sheet(frames, contact_sheet)
    return {
        "webm": webm,
        "webp": webp,
        "poster": poster,
        "checkerboard": checkerboard_path,
        "contact_sheet": contact_sheet,
        "frame_dir": frame_dir,
    }


def relative(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def write_manifest(
    *,
    outputs: dict[str, Path],
    stabilization: dict[str, Any],
) -> dict[str, Any]:
    source_receipt = read_json(SOURCE.parent / "ingest-receipt.json")
    frame_paths = sorted(outputs["frame_dir"].glob("frame-*.png"))
    consecutive_mae = [
        frame_mae(
            Image.open(frame_paths[index]).convert("RGBA"),
            Image.open(frame_paths[index + 1]).convert("RGBA"),
        )
        for index in range(len(frame_paths) - 1)
    ]
    manifest = {
        "schema_version": "v60.actor-motion-process.001",
        "asset_id": MEDIA_ID,
        "revision": REVISION,
        "character_version": CHARACTER_VERSION,
        "source": {
            "path": relative(SOURCE),
            "sha256": sha256_file(SOURCE),
            "original_filename": source_receipt["original_filename"],
            "video": {
                "size": [1280, 720],
                "fps": FPS,
                "frames": SOURCE_FRAME_COUNT,
                "duration_ms": 10005,
            },
            "audio": "AAC_48KHZ_STEREO_REMOVED",
        },
        "owner_decision": {
            "status": "OWNER_APPROVED_FOR_GUIDE_LEFT_POSTPROCESS",
            "selected_identity_use": "V60_GUIDE_LEFT_ONCE",
        },
        "identity_provenance": {
            "character_reference_asset_id": "ABU_V60_CHARACTER_REFERENCE_V1",
            "transparent_poster_asset_id": "ABU_V60_SEATED_TRANSPARENT_V1",
            "character_version": CHARACTER_VERSION,
            "mirror_safe": False,
        },
        "selection": {
            "source_start_frame_inclusive": SOURCE_START_FRAME,
            "source_end_frame_exclusive": SOURCE_END_FRAME_EXCLUSIVE,
            "source_peak_frame": SOURCE_PEAK_FRAME,
            "delivery_frame_count": len(frame_paths),
            "duration_ms": round(len(frame_paths) / FPS * 1000),
            "excluded_source_reason": (
                "The later source section repeats the guide gesture and is not "
                "part of the admitted single invitation."
            ),
            "crossfade_frames": 0,
        },
        "action_phases": {
            "neutral_lead_source_frames": [12, 29],
            "turn_and_lift_source_frames": [30, 51],
            "open_paw_invitation_source_frames": [52, 75],
            "return_source_frames": [76, 95],
            "neutral_hold_source_frames": [96, 115],
        },
        "alpha_matte": {
            "source_key_sample": "#00bd14",
            "similarity": 0.20,
            "blend": 0.08,
            "alpha_floor": ALPHA_THRESHOLD,
            "despill": {"type": "green", "mix": 0.60, "expand": 0.04},
        },
        "watermark_and_window": {
            "removed": True,
            "method": "exclude_before_alpha_delivery",
            "retained_source_rect": [0, 0, SOURCE_ISOLATION_WIDTH, 720],
            "excluded_source_rect": [SOURCE_ISOLATION_WIDTH, 0, 1280, 720],
            "source_actor_rightmost_pixel": stabilization["source_actor_bbox_union"][2],
            "clearance_pixels": (
                SOURCE_ISOLATION_WIDTH - stabilization["source_actor_bbox_union"][2]
            ),
        },
        "canvas": list(CANVAS),
        "fps": FPS,
        "frame_count": len(frame_paths),
        "duration_ms": round(len(frame_paths) / FPS * 1000),
        "anchor": {
            "type": "BOTTOM_CENTER",
            "pixel": [CANVAS[0] // 2, BOTTOM_ANCHOR],
            "normalized": [0.5, round(BOTTOM_ANCHOR / CANVAS[1], 8)],
            "observed_range": stabilization["output_bottom_anchor_range"],
        },
        "stabilization": stabilization,
        "motion_contract": {
            "semantic_state": "GUIDE_LEFT",
            "direction": "SCREEN_LEFT",
            "gesture_count": 1,
            "source_mouth_motion": "NO_SPEECH_OR_REACTION_IN_RETAINED_SEGMENT",
            "head_turn_and_open_paw_preserved": True,
            "runtime_owns_actor_container_translation": True,
        },
        "one_shot_validation": {
            "median_consecutive_rgba_mae": round(statistics.median(consecutive_mae), 6),
            "max_consecutive_rgba_mae": round(max(consecutive_mae), 6),
            "crossfade_frames": 0,
            "repeated_source_gesture_excluded": True,
        },
        "masters": {
            "png_frame_pattern": relative(outputs["frame_dir"] / "frame-%04d.png"),
            "aggregate_sha256": hashlib.sha256(
                "".join(sha256_file(path) for path in frame_paths).encode("ascii")
            ).hexdigest(),
        },
        "deliveries": {
            key: {"path": relative(path), "sha256": sha256_file(path)}
            for key, path in outputs.items()
            if key in {"webm", "webp", "poster", "checkerboard", "contact_sheet"}
        },
        "runtime_contract": {
            "trigger": "ABU_GUIDES_TO_DESTINATION_ON_SCREEN_LEFT",
            "playback": "PLAY_ONCE",
            "interruptible": True,
            "return_action": "media.abu.v60.seated-idle.v1",
            "cooldown_ms": 1800,
            "anchor": "BOTTOM_CENTER",
            "preferred_screen_side": "RIGHT",
            "direction": "SCREEN_LEFT",
            "mirror_safe": False,
            "mobile_suitability": True,
            "reduced_motion_asset_ref": "abu.v60.guide-left.poster.v1",
        },
    }
    write_json(MANIFEST_PATH, manifest)
    return manifest


def upsert_runtime_records(manifest: dict[str, Any]) -> None:
    catalog = read_json(CATALOG_PATH)
    catalog["items"] = [
        item for item in catalog["items"] if item["media_ref"] != MEDIA_REF
    ]
    deliveries = [
        {
            "asset_ref": "abu.v60.guide-left.v1",
            "asset_version": MEDIA_ID,
            "role": "VP9_ALPHA_WEBM",
            "path": manifest["deliveries"]["webm"]["path"],
            "sha256": manifest["deliveries"]["webm"]["sha256"],
            "alpha": True,
        },
        {
            "asset_ref": "abu.v60.guide-left.webp.v1",
            "asset_version": MEDIA_ID,
            "role": "ANIMATED_WEBP",
            "path": manifest["deliveries"]["webp"]["path"],
            "sha256": manifest["deliveries"]["webp"]["sha256"],
            "alpha": True,
        },
        {
            "asset_ref": "abu.v60.guide-left.poster.v1",
            "asset_version": MEDIA_ID,
            "role": "REDUCED_MOTION_POSTER",
            "path": manifest["deliveries"]["poster"]["path"],
            "sha256": manifest["deliveries"]["poster"]["sha256"],
            "alpha": True,
        },
    ]
    catalog["items"].append(
        {
            "media_ref": MEDIA_REF,
            "asset_id": MEDIA_ID,
            "revision": REVISION,
            "media_kind": "ACTOR_MOTION",
            "character_version": CHARACTER_VERSION,
            "semantic_role": "GUIDE_LEFT",
            "action_type": "ONE_SHOT",
            "library_status": "RUNTIME_REGISTERED",
            "source": {
                "path": relative(SOURCE),
                "original_filename": manifest["source"]["original_filename"],
                "sha256": manifest["source"]["sha256"],
                "generator": "Gemini",
                "prompt_ref": "V60_GEMINI_ABU_ACTOR_PROMPTS_V1",
                "prompt_status": "OWNER_SUPPLIED_GENERATION_RESULT",
                "authorization": "OWNER_APPROVED_FOR_POSTPROCESS_AND_GUIDE_LEFT_USE",
            },
            "process_manifest_path": relative(MANIFEST_PATH),
            "process_manifest_sha256": sha256_file(MANIFEST_PATH),
            "deliveries": deliveries,
            "review_artifacts": [
                {
                    "role": "CHECKERBOARD_PREVIEW",
                    "path": manifest["deliveries"]["checkerboard"]["path"],
                    "sha256": manifest["deliveries"]["checkerboard"]["sha256"],
                },
                {
                    "role": "CONTACT_SHEET",
                    "path": manifest["deliveries"]["contact_sheet"]["path"],
                    "sha256": manifest["deliveries"]["contact_sheet"]["sha256"],
                },
            ],
            "runtime_contract": manifest["runtime_contract"],
        }
    )
    for identity in catalog["character_identities"]:
        if identity["character_version"] == CHARACTER_VERSION:
            identity["motion_media_refs"] = sorted(
                {*identity["motion_media_refs"], MEDIA_REF}
            )
    write_json(CATALOG_PATH, catalog)

    registry = read_json(REGISTRY_PATH)
    asset_refs = {delivery["asset_ref"] for delivery in deliveries}
    registry["assets"] = [
        asset for asset in registry["assets"] if asset["asset_ref"] not in asset_refs
    ]
    role_by_ref = {
        "abu.v60.guide-left.v1": ("video/webm", "abu_v60_guide_left_once"),
        "abu.v60.guide-left.webp.v1": (
            "image/webp",
            "abu_v60_guide_left_animation_fallback",
        ),
        "abu.v60.guide-left.poster.v1": (
            "image/png",
            "abu_v60_guide_left_reduced_motion",
        ),
    }
    for delivery in deliveries:
        media_type, role = role_by_ref[delivery["asset_ref"]]
        registry["assets"].append(
            {
                "asset_ref": delivery["asset_ref"],
                "asset_version": MEDIA_ID,
                "runtime_path": delivery["path"],
                "sha256": delivery["sha256"],
                "media_type": media_type,
                "source_manifest_ref": relative(MANIFEST_PATH),
                "source_status": "OWNER_APPROVED",
                "v60_role": role,
            }
        )
    write_json(REGISTRY_PATH, registry)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"missing immutable source: {SOURCE}")
    with tempfile.TemporaryDirectory(prefix="abu-v60-guide-left-") as temp:
        keyed_frames = extract_keyed_frames(Path(temp))
        selected_frames = keyed_frames[SOURCE_START_FRAME:SOURCE_END_FRAME_EXCLUSIVE]
        normalized_frames, stabilization = normalize_frames(selected_frames)
    outputs = build_outputs(normalized_frames)
    manifest = write_manifest(outputs=outputs, stabilization=stabilization)
    upsert_runtime_records(manifest)
    print(
        f"{MEDIA_ID}: {manifest['frame_count']} frames, "
        f"{manifest['duration_ms']} ms, source={manifest['source']['sha256']}"
    )


if __name__ == "__main__":
    main()
