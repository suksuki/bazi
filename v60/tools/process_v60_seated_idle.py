from __future__ import annotations

import hashlib
import json
import os
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEDIA_ID = "ABU_V60_SEATED_IDLE_LOOP_V1"
MEDIA_REF = "media.abu.v60.seated-idle.v1"
REVISION = "v1"
CHARACTER_VERSION = "ABU_CHARACTER_V60_V1"
SOURCE = Path(
    os.environ.get(
        "ABU_V60_IDLE_SOURCE",
        PROJECT_ROOT / "media" / "sources" / MEDIA_ID / REVISION / "source.mp4",
    )
)

FPS = 24
SOURCE_FRAME_COUNT = 240
SOURCE_ISOLATION_WIDTH = 1050
SAFE_CLOSED_MOUTH_END = 95
MIN_LOOP_FRAMES = 48
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
    PROJECT_ROOT / "web" / "public" / "assets" / "abu" / "v60" / "abu-v60-seated-idle-loop-v1"
)
MANIFEST_PATH = PROJECT_ROOT / "media" / "manifests" / f"{MEDIA_ID}.v1.json"
CATALOG_PATH = PROJECT_ROOT / "media" / "catalog.json"
REGISTRY_PATH = PROJECT_ROOT / "assets" / "registry.json"


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def visible_box(frame: Image.Image) -> tuple[int, int, int, int]:
    box = frame.getchannel("A").getbbox()
    if box is None:
        raise RuntimeError("green-screen extraction produced an empty frame")
    return box


def head_anchor_x(frame: Image.Image, box: tuple[int, int, int, int]) -> float:
    alpha = np.asarray(frame.getchannel("A"), dtype=np.float32)
    head_bottom = min(box[3], box[1] + round((box[3] - box[1]) * 0.46))
    band = alpha[box[1] : head_bottom, box[0] : box[2]]
    weights = band.sum(axis=0)
    total = float(weights.sum())
    if total <= 0:
        return (box[0] + box[2]) / 2
    positions = np.arange(box[0], box[2], dtype=np.float32)
    return float((positions * weights).sum() / total)


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
        raise RuntimeError(f"expected {SOURCE_FRAME_COUNT} source frames, got {len(frames)}")
    return frames


def normalize_frames(frames: list[Image.Image]) -> tuple[list[Image.Image], dict[str, Any]]:
    boxes = [visible_box(frame) for frame in frames]
    heights = [box[3] - box[1] for box in boxes]
    endpoint_window = min(12, len(frames) // 3)
    first_height = float(statistics.median(heights[:endpoint_window]))
    last_height = float(statistics.median(heights[-endpoint_window:]))
    delivery_scale = TARGET_VISIBLE_HEIGHT / first_height

    normalized: list[Image.Image] = []
    anchor_positions: list[int] = []
    visible_heights: list[int] = []
    for index, (frame, box) in enumerate(zip(frames, boxes, strict=True)):
        progress = index / max(1, len(frames) - 1)
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
        actor = actor.resize(
            (
                max(1, round(actor.width * scale)),
                max(1, round(actor.height * scale)),
            ),
            Image.Resampling.LANCZOS,
        )
        anchor_x_offset = (head_anchor_x(frame, box) - crop_box[0]) * scale
        actor_bottom_offset = (box[3] - crop_box[1]) * scale
        x = round(CANVAS[0] / 2 - anchor_x_offset)
        y = round(BOTTOM_ANCHOR - actor_bottom_offset)

        canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        canvas.alpha_composite(actor, (x, y))
        composited_box = visible_box(canvas)
        correction = BOTTOM_ANCHOR - composited_box[3]
        if correction:
            anchored = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
            anchored.alpha_composite(canvas, (0, correction))
            canvas = anchored

        output_box = visible_box(canvas)
        normalized.append(canvas)
        anchor_positions.append(output_box[3])
        visible_heights.append(output_box[3] - output_box[1])

    return normalized, {
        "source_visible_height_range": [min(heights), max(heights)],
        "endpoint_median_heights": [first_height, last_height],
        "output_bottom_anchor_range": [min(anchor_positions), max(anchor_positions)],
        "output_visible_height_range": [min(visible_heights), max(visible_heights)],
    }


def alpha_iou(first: Image.Image, second: Image.Image) -> float:
    first_alpha = np.asarray(first.getchannel("A")) > 0
    second_alpha = np.asarray(second.getchannel("A")) > 0
    union = np.logical_or(first_alpha, second_alpha).sum()
    if union == 0:
        return 1.0
    return float(np.logical_and(first_alpha, second_alpha).sum() / union)


def frame_mae(first: Image.Image, second: Image.Image) -> float:
    first_array = np.asarray(first, dtype=np.int16)
    second_array = np.asarray(second, dtype=np.int16)
    union_alpha = np.logical_or(
        first_array[:, :, 3] > 0,
        second_array[:, :, 3] > 0,
    )
    if not union_alpha.any():
        return 0.0
    return float(np.abs(first_array - second_array)[union_alpha].mean())


def choose_loop(frames: list[Image.Image]) -> tuple[list[Image.Image], dict[str, Any]]:
    candidates: list[tuple[float, int, float, float]] = []
    first = frames[0]
    for endpoint in range(MIN_LOOP_FRAMES, min(SAFE_CLOSED_MOUTH_END, len(frames) - 1) + 1):
        mae = frame_mae(first, frames[endpoint])
        iou = alpha_iou(first, frames[endpoint])
        score = mae + (1 - iou) * 30
        candidates.append((score, endpoint, mae, iou))
    _, endpoint, endpoint_mae, endpoint_iou = min(candidates)

    # Endpoint is the natural next phase after the final retained source frame.
    selected = [frame.copy() for frame in frames[:endpoint]]
    selected.append(first.copy())
    return selected, {
        "source_start_frame_inclusive": 0,
        "source_phase_match_frame": endpoint,
        "source_end_frame_exclusive": endpoint,
        "delivery_frame_count": len(selected),
        "selection_window": [MIN_LOOP_FRAMES, SAFE_CLOSED_MOUTH_END],
        "endpoint_rgba_mae_before_exact_close": round(endpoint_mae, 6),
        "endpoint_alpha_iou": round(endpoint_iou, 8),
        "closure_method": "phase_matched_cut_then_exact_first_frame",
        "crossfade_frames": 0,
        "excluded_source_reason": (
            "Later source frames contain a mouth-open reaction and are not part "
            "of the Owner-approved quiet IDLE extraction."
        ),
    }


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
    columns, rows = 5, 2
    tile = (320, 240)
    sheet = Image.new("RGB", (columns * tile[0], rows * tile[1]), "white")
    indexes = [
        round(index * (len(frames) - 1) / (columns * rows - 1)) for index in range(columns * rows)
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
        loop=0,
        quality=92,
        method=3,
        minimize_size=False,
    )
    frames[0].save(poster, optimize=True)
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
    loop: dict[str, Any],
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
            "status": "OWNER_APPROVED_FOR_SEGMENTED_IDLE_POSTPROCESS",
            "whole_take_contract": "NOT_USED",
            "selected_identity_use": "V60_QUIET_COMPANION_IDLE",
        },
        "identity_provenance": {
            "character_reference_asset_id": "ABU_V60_CHARACTER_REFERENCE_V1",
            "transparent_poster_asset_id": "ABU_V60_SEATED_TRANSPARENT_V1",
            "character_version": CHARACTER_VERSION,
            "mirror_safe": False,
        },
        "selection": loop,
        "alpha_matte": {
            "source_key_sample": "#00bd14",
            "similarity": 0.20,
            "blend": 0.08,
            "alpha_floor": ALPHA_THRESHOLD,
            "despill": {"type": "green", "mix": 0.60, "expand": 0.04},
        },
        "watermark": {
            "removed": True,
            "method": "exclude_before_alpha_delivery",
            "retained_source_rect": [0, 0, SOURCE_ISOLATION_WIDTH, 720],
            "excluded_source_rect": [SOURCE_ISOLATION_WIDTH, 0, 1280, 720],
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
            "semantic_state": "QUIET_COMPANION_IDLE",
            "mouth_open_frames": 0,
            "blink_contract_enforced": False,
            "source_eye_motion_preserved": True,
            "natural_breathing_preserved": True,
            "head_or_body_translation_owned_by_runtime": False,
        },
        "loop_validation": {
            "first_last_rgba_mae": frame_mae(
                Image.open(frame_paths[0]).convert("RGBA"),
                Image.open(frame_paths[-1]).convert("RGBA"),
            ),
            "first_last_png_identical": (
                sha256_file(frame_paths[0]) == sha256_file(frame_paths[-1])
            ),
            "median_consecutive_rgba_mae": round(statistics.median(consecutive_mae), 6),
            "max_consecutive_rgba_mae": round(max(consecutive_mae), 6),
            "crossfade_frames": 0,
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
            "trigger": "ABU_VISIBLE_IN_QUIET_COMPANION_STATE",
            "playback": "LOOP",
            "interruptible": True,
            "return_action": "SELF",
            "anchor": "BOTTOM_CENTER",
            "reduced_motion_asset_ref": "abu.v60.seated.idle.poster.v1",
        },
    }
    write_json(MANIFEST_PATH, manifest)
    return manifest


def upsert_runtime_records(manifest: dict[str, Any]) -> None:
    catalog = read_json(CATALOG_PATH)
    catalog["items"] = [item for item in catalog["items"] if item["media_ref"] != MEDIA_REF]
    deliveries = [
        {
            "asset_ref": "abu.v60.seated.idle.v1",
            "asset_version": MEDIA_ID,
            "role": "VP9_ALPHA_WEBM",
            "path": manifest["deliveries"]["webm"]["path"],
            "sha256": manifest["deliveries"]["webm"]["sha256"],
            "alpha": True,
        },
        {
            "asset_ref": "abu.v60.seated.idle.webp.v1",
            "asset_version": MEDIA_ID,
            "role": "ANIMATED_WEBP",
            "path": manifest["deliveries"]["webp"]["path"],
            "sha256": manifest["deliveries"]["webp"]["sha256"],
            "alpha": True,
        },
        {
            "asset_ref": "abu.v60.seated.idle.poster.v1",
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
            "semantic_role": "QUIET_COMPANION_IDLE",
            "action_type": "LOOP",
            "library_status": "RUNTIME_REGISTERED",
            "source": {
                "path": relative(SOURCE),
                "original_filename": manifest["source"]["original_filename"],
                "sha256": manifest["source"]["sha256"],
                "generator": "Gemini",
                "prompt_ref": "OWNER_SUPPLIED_GEMINI_IDLE_SOURCE_2026-07-28",
                "prompt_status": "OWNER_SUPPLIED_WITHOUT_PROMPT_TRANSCRIPT",
                "authorization": "OWNER_APPROVED_FOR_POSTPROCESS_AND_IDLE_USE",
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
            identity["motion_media_refs"] = sorted({*identity["motion_media_refs"], MEDIA_REF})
    for cue in catalog["cue_bundles"]:
        if cue["cue_ref"] == "cue.mingli.abu-idle.v1":
            cue["visual_media_ref"] = MEDIA_REF
            cue["reduced_motion"]["visual_asset_ref"] = "abu.v60.seated.idle.poster.v1"
    write_json(CATALOG_PATH, catalog)

    registry = read_json(REGISTRY_PATH)
    asset_refs = {delivery["asset_ref"] for delivery in deliveries}
    registry["assets"] = [
        asset for asset in registry["assets"] if asset["asset_ref"] not in asset_refs
    ]
    role_by_ref = {
        "abu.v60.seated.idle.v1": ("video/webm", "abu_v60_quiet_companion_idle"),
        "abu.v60.seated.idle.webp.v1": (
            "image/webp",
            "abu_v60_quiet_companion_animation_fallback",
        ),
        "abu.v60.seated.idle.poster.v1": (
            "image/png",
            "abu_v60_quiet_companion_reduced_motion",
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
    with tempfile.TemporaryDirectory(prefix="abu-v60-idle-") as temp:
        keyed_frames = extract_keyed_frames(Path(temp))
        normalized_frames, stabilization = normalize_frames(
            keyed_frames[: SAFE_CLOSED_MOUTH_END + 1]
        )
        loop_frames, loop = choose_loop(normalized_frames)
    outputs = build_outputs(loop_frames)
    manifest = write_manifest(
        outputs=outputs,
        loop=loop,
        stabilization=stabilization,
    )
    upsert_runtime_records(manifest)
    print(
        json.dumps(
            {
                "asset_id": MEDIA_ID,
                "source_sha256": manifest["source"]["sha256"],
                "selected_source_frames": [
                    loop["source_start_frame_inclusive"],
                    loop["source_end_frame_exclusive"],
                ],
                "frame_count": manifest["frame_count"],
                "duration_ms": manifest["duration_ms"],
                "first_last_rgba_mae": manifest["loop_validation"]["first_last_rgba_mae"],
                "checkerboard": manifest["deliveries"]["checkerboard"]["path"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
