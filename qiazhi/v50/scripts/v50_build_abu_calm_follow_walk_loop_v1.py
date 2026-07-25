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
        "V50_ABU_CALM_FOLLOW_WALK_SOURCE",
        str(Path.home() / "Downloads/Create_a_second_green_scree.mp4"),
    )
).expanduser()
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v12-actor-pass"
ACTION_DIR = ASSET_ROOT / "abu-02-calm-follow-walk-loop-v1"
ARTIFACT_ROOT = ROOT / "artifacts/abu-actor-pass-v1"
LIBRARY = ASSET_ROOT / "library.json"
INVENTORY = ASSET_ROOT / "video-inventory.json"
GLOBAL_REGISTRY = ROOT / "config/media_asset_registry_v1.json"
MOTION_REGISTRY = ASSET_ROOT.parent / "motion-registry.js"

CATALOG_ID = "ABU_02_CALM_FOLLOW_WALK_LOOP_V1"
ACTION_ID = "abu_02_calm_follow_walk_loop_v1"
SOURCE_ID = "abu_02_calm_follow_walk_loop_v1_source"
ACTION_STATUS = "production"
LIBRARY_STATUS = "LIBRARY_READY"
FPS = 24
SOURCE_FRAME_COUNT = 240
LOOP_START_FRAME = 6
LOOP_END_EXCLUSIVE = 60
MATCHED_ENDPOINT_FRAME = 60
CANVAS = (960, 720)
BOTTOM_ANCHOR = 704
TARGET_VISIBLE_HEIGHT = 620
SOURCE_ISOLATION_WIDTH = 1040
ALPHA_THRESHOLD = 24
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
        pixels = np.asarray(Image.open(path).convert("RGBA")).copy()
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


def upper_body_anchor_x(
    frame: Image.Image,
    box: tuple[int, int, int, int],
) -> float:
    alpha = np.asarray(frame.getchannel("A"), dtype=np.float32)
    upper_bottom = box[1] + round((box[3] - box[1]) * 0.67)
    band = alpha[box[1] : upper_bottom, box[0] : box[2]]
    weights = band.sum(axis=0)
    total = float(weights.sum())
    if total <= 0:
        return (box[0] + box[2]) / 2
    positions = np.arange(box[0], box[2], dtype=np.float32)
    return float((positions * weights).sum() / total)


def normalize_cycle(
    frames: list[Image.Image],
) -> tuple[list[Image.Image], Image.Image, dict]:
    boxes = [visible_box(frame) for frame in frames]
    anchors = [
        upper_body_anchor_x(frame, box)
        for frame, box in zip(frames, boxes, strict=True)
    ]
    selected_heights = [
        boxes[index][3] - boxes[index][1]
        for index in range(LOOP_START_FRAME, LOOP_END_EXCLUSIVE)
    ]
    fixed_scale = TARGET_VISIBLE_HEIGHT / statistics.median(selected_heights)
    start_anchor = anchors[LOOP_START_FRAME]
    end_anchor = anchors[MATCHED_ENDPOINT_FRAME]

    def compose(source_index: int, progress: float) -> Image.Image:
        frame = frames[source_index]
        box = boxes[source_index]
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
                max(1, round(actor.width * fixed_scale)),
                max(1, round(actor.height * fixed_scale)),
            ),
            Image.Resampling.LANCZOS,
        )

        drift_baseline = start_anchor + (end_anchor - start_anchor) * progress
        baseline_offset = (drift_baseline - crop_box[0]) * fixed_scale
        actor_bottom_offset = (box[3] - crop_box[1]) * fixed_scale
        x = round(CANVAS[0] / 2 - baseline_offset)
        y = round(BOTTOM_ANCHOR - actor_bottom_offset)
        canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        canvas.alpha_composite(actor, (x, y))

        pixels = np.asarray(canvas).copy()
        pixels[pixels[:, :, 3] < ALPHA_THRESHOLD] = 0
        canvas = Image.fromarray(pixels, "RGBA")
        output_box = visible_box(canvas)
        if output_box[3] != BOTTOM_ANCHOR:
            anchored = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
            anchored.alpha_composite(canvas, (0, BOTTOM_ANCHOR - output_box[3]))
            canvas = anchored
        return canvas

    output = []
    frame_count = LOOP_END_EXCLUSIVE - LOOP_START_FRAME
    for offset, source_index in enumerate(
        range(LOOP_START_FRAME, LOOP_END_EXCLUSIVE)
    ):
        output.append(compose(source_index, offset / frame_count))
    matched_endpoint = compose(MATCHED_ENDPOINT_FRAME, 1.0)
    output_boxes = [visible_box(frame) for frame in output]
    return output, matched_endpoint, {
        "method": "constant_scale_bottom_anchor_with_linear_drift_removal",
        "fixed_scale": round(fixed_scale, 8),
        "source_actor_box_range": [
            min(box[0] for box in boxes),
            min(box[1] for box in boxes),
            max(box[2] for box in boxes),
            max(box[3] for box in boxes),
        ],
        "selected_source_height_range": [
            min(selected_heights),
            max(selected_heights),
        ],
        "source_upper_body_anchor": {
            "start": round(start_anchor, 6),
            "matched_endpoint": round(end_anchor, 6),
            "linear_drift_removed": round(end_anchor - start_anchor, 6),
        },
        "output_bottom_anchor_range": [
            min(box[3] for box in output_boxes),
            max(box[3] for box in output_boxes),
        ],
        "output_actor_union_box": [
            min(box[0] for box in output_boxes),
            min(box[1] for box in output_boxes),
            max(box[2] for box in output_boxes),
            max(box[3] for box in output_boxes),
        ],
        "output_visible_height_range": [
            min(box[3] - box[1] for box in output_boxes),
            max(box[3] - box[1] for box in output_boxes),
        ],
        "natural_vertical_bob_preserved": True,
    }


def frame_mae(first: Image.Image, second: Image.Image) -> float:
    a = np.asarray(first, dtype=np.int16)
    b = np.asarray(second, dtype=np.int16)
    mask = (a[:, :, 3] > ALPHA_THRESHOLD) | (b[:, :, 3] > ALPHA_THRESHOLD)
    return float(np.abs(a.astype(np.int32) - b.astype(np.int32))[mask].mean())


def alpha_iou(first: Image.Image, second: Image.Image) -> float:
    a = np.asarray(first.getchannel("A")) > ALPHA_THRESHOLD
    b = np.asarray(second.getchannel("A")) > ALPHA_THRESHOLD
    return float((a & b).sum() / max(1, (a | b).sum()))


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


def save_raw_video(
    frames: list[Image.Image],
    path: Path,
    *,
    checkerboard_background: bool,
    repeats: int = 1,
) -> None:
    pixel_format = "rgb24" if checkerboard_background else "rgba"
    codec_args = (
        [
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
        ]
        if checkerboard_background
        else [
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
        ]
    )
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pixel_format",
        pixel_format,
        "-video_size",
        f"{CANVAS[0]}x{CANVAS[1]}",
        "-framerate",
        str(FPS),
        "-i",
        "pipe:0",
        "-an",
        *codec_args,
        str(path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    if not process.stdin:
        raise RuntimeError("ffmpeg stdin is unavailable")
    background = checkerboard(CANVAS)
    try:
        for _ in range(repeats):
            for frame in frames:
                if checkerboard_background:
                    preview = background.copy()
                    preview.alpha_composite(frame)
                    process.stdin.write(preview.convert("RGB").tobytes())
                else:
                    process.stdin.write(frame.tobytes())
        process.stdin.close()
    finally:
        return_code = process.wait()
    if return_code:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"video encode failed with exit code {return_code}")


def save_contact_sheet(frames: list[Image.Image], path: Path) -> None:
    columns, rows = 6, 2
    tile = (280, 210)
    sheet = Image.new("RGB", (tile[0] * columns, tile[1] * rows), "white")
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
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=94, optimize=True)


def save_outputs(
    frames: list[Image.Image],
    matched_endpoint: Image.Image,
    stabilization: dict,
) -> dict:
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
    save_raw_video(frames, webm, checkerboard_background=False)
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
    save_raw_video(
        frames,
        preview,
        checkerboard_background=True,
        repeats=3,
    )

    consecutive = [
        frame_mae(frames[index], frames[index + 1])
        for index in range(len(frames) - 1)
    ]
    seam_mae = frame_mae(frames[-1], frames[0])
    natural_endpoint_mae = frame_mae(frames[-1], matched_endpoint)
    loop_metrics = {
        "source_start_frame_inclusive": LOOP_START_FRAME,
        "source_end_frame_exclusive": LOOP_END_EXCLUSIVE,
        "source_output_frames_inclusive": [
            LOOP_START_FRAME,
            LOOP_END_EXCLUSIVE - 1,
        ],
        "matched_endpoint_frame_not_delivered": MATCHED_ENDPOINT_FRAME,
        "matched_endpoint_rgba_mae": round(
            frame_mae(frames[0], matched_endpoint),
            6,
        ),
        "matched_endpoint_alpha_iou": round(
            alpha_iou(frames[0], matched_endpoint),
            8,
        ),
        "seam_step_rgba_mae": round(seam_mae, 6),
        "natural_endpoint_step_rgba_mae": round(natural_endpoint_mae, 6),
        "seam_vs_natural_step_delta": round(
            abs(seam_mae - natural_endpoint_mae),
            6,
        ),
        "median_consecutive_rgba_mae": round(
            statistics.median(consecutive),
            6,
        ),
        "max_consecutive_rgba_mae": round(max(consecutive), 6),
        "crossfade_frames": 0,
        "duplicate_endpoint_frame": False,
        "method": "matched_gait_phase_boundary_without_crossfade",
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
        / "abu_02_calm_follow_walk_loop_v1_source.mp4"
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
        "semantic_state": "LOCOMOTION_FOLLOW",
        "action_type": "LOOP",
        "action_family": "locomotion",
        "product_role": "calm_follow_walk",
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
        "selected_loop": {
            "source_frame_start_inclusive": LOOP_START_FRAME,
            "source_frame_end_exclusive": LOOP_END_EXCLUSIVE,
            "matched_endpoint_frame": MATCHED_ENDPOINT_FRAME,
            "source_time_seconds": [
                LOOP_START_FRAME / FPS,
                LOOP_END_EXCLUSIVE / FPS,
            ],
            "selection_basis": (
                "best alpha-phase match with natural seam continuity "
                "inside the approved first gait cycle"
            ),
        },
        "canvas": list(CANVAS),
        "anchor": {
            "name": "bottom_center",
            "normalized": [0.5, BOTTOM_ANCHOR / CANVAS[1]],
            "pixels": [CANVAS[0] // 2, BOTTOM_ANCHOR],
        },
        "bounding_box": outputs["stabilization"]["output_actor_union_box"],
        "frame_count": len(outputs["frame_paths"]),
        "fps": FPS,
        "duration_ms": round(len(outputs["frame_paths"]) / FPS * 1000),
        "transparent_background": True,
        "audio_removed": True,
        "watermark_removed": True,
        "fixed_character_scale": True,
        "fixed_bottom_anchor": True,
        "natural_vertical_bob_preserved": True,
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
        "checkerboard_preview_repeats": 3,
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
        "runtime_contract": {
            "trigger": "canonical_abu_follow_distance_exceeded",
            "duration_ms": round(len(outputs["frame_paths"]) / FPS * 1000),
            "playback": "loop_while_container_is_moving",
            "interruptible": True,
            "return_action": "approved_idle_or_observe_action",
            "cooldown_ms": 0,
            "fallback": "reduced_motion_poster",
            "anchor": "bottom_center",
            "preferred_screen_side": "left_or_trailing_side",
            "mobile_suitability": "full_body_small_actor",
            "container_motion_owner": "dream_runtime",
            "actor_has_embedded_horizontal_translation": False,
        },
        "actor_contract": {
            "facing": "right",
            "gaze_target": "travel_direction",
            "safe_crop": "full_body",
            "background": "transparent",
            "flip_horizontal": False,
            "loop_mode": "loop",
            "mouth_state": "closed",
            "recommended_contexts": [
                "dream_world_delayed_follow",
                "tree_world_guide_transition",
                "workspace_companion_reposition",
                "studio_transparent_actor_composite",
            ],
        },
        "quality_gate": {
            "character_lock": "PASS",
            "motion": "PASS",
            "camera": "PASS",
            "background": "PASS",
            "first_last_loop": "PASS_AFTER_PHASE_MATCH_POSTPROCESS",
            "technical_format": "PASS_AFTER_POSTPROCESS",
            "library_ready": "PASS_OWNER_APPROVED",
        },
        "boundaries": {
            "runtime_registered": True,
            "runtime_default_changed": False,
            "creates_mingli_claim": False,
            "changes_case_state": False,
            "no_crossfade_or_frame_blending": True,
            "do_not_use_for": [
                "独立命理推理",
                "命理结论生成",
                "角色瞬移或位置结算",
                "静止等待状态",
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
            "actions": ["calm_walk_in_place", "breathe", "tail_follow_through"],
            "selected_ranges": [
                {
                    "frames": [
                        LOOP_START_FRAME,
                        LOOP_END_EXCLUSIVE - 1,
                    ],
                    "seconds": [
                        LOOP_START_FRAME / FPS,
                        LOOP_END_EXCLUSIVE / FPS,
                    ],
                    "action_id": ACTION_ID,
                }
            ],
            "quality": "library_ready_owner_approved",
            "notes": [
                "Character Lock, motion, camera and background passed designer review.",
                "Frames 6-59 form the delivered cycle; frame 60 is the matched endpoint and is not duplicated.",
                "No crossfade, frame blending or horizontal actor translation was introduced.",
                "Owner approved runtime use for canonical Abu follow locomotion.",
            ],
            "removed_regions": [
                "green_screen",
                "lower_right_four_point_platform_mark",
                "aac_audio_track",
                "linear_anchor_drift",
                "non_matching_source_tail",
            ],
        }
    )
    write_json(INVENTORY, inventory)


def update_library(manifest: dict) -> None:
    library = read_json(LIBRARY)
    library["version"] = "v50.abu.motion_library.actor_pass_v2"
    library["actions"] = [
        action
        for action in library["actions"]
        if action["action_id"] != ACTION_ID
    ]
    library["actions"].append(
        {
            "action_id": ACTION_ID,
            "catalog_id": CATALOG_ID,
            "action_family": "locomotion",
            "semantic_state": "LOCOMOTION_FOLLOW",
            "action_type": "LOOP",
            "status": ACTION_STATUS,
            "source_status": manifest["source_status"],
            "library_status": manifest["library_status"],
            "character_version": manifest["character_version"],
            "label_zh": "阿布平静跟随行走循环 V1",
            "description_zh": (
                "阿布闭嘴、平静原地行走的透明循环；由运行时移动角色容器，"
                "本素材只表达连续步态。"
            ),
            "product_role": "calm_follow_walk",
            "do_not_use_for": manifest["boundaries"]["do_not_use_for"],
            "manifest": "abu-02-calm-follow-walk-loop-v1/manifest.json",
            "video": (
                "abu-02-calm-follow-walk-loop-v1/web/"
                f"{ACTION_ID}.webm"
            ),
            "animation": (
                "abu-02-calm-follow-walk-loop-v1/web/"
                f"{ACTION_ID}.webp"
            ),
            "poster": (
                "abu-02-calm-follow-walk-loop-v1/posters/"
                f"{ACTION_ID}.png"
            ),
            "contact_sheet": (
                "abu-02-calm-follow-walk-loop-v1/contact-sheets/"
                f"{ACTION_ID}_contact_sheet.png"
            ),
            "checkerboard_preview": (
                "abu-02-calm-follow-walk-loop-v1/previews/"
                f"{ACTION_ID}_checkerboard.mp4"
            ),
            "duration_ms": manifest["duration_ms"],
            "display_scale": 1.0,
            "loop_mode": "loop",
            "facing": "right",
            "gaze_target": "travel_direction",
            "safe_crop": "full_body",
            "runtime_registered": True,
            "recommended_contexts": manifest["actor_contract"][
                "recommended_contexts"
            ],
        }
    )
    library["review_candidates"] = [
        action
        for action in library.get("review_candidates", [])
        if action["action_id"] != ACTION_ID
    ]
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
    with tempfile.TemporaryDirectory(prefix="abu-calm-follow-walk-v1-") as name:
        keyed = extract_keyed_frames(Path(name))
        frames, matched_endpoint, stabilization = normalize_cycle(keyed)
    outputs = save_outputs(frames, matched_endpoint, stabilization)
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
                "runtime_registered": True,
                "default_action_changed": False,
                "source_frames": [
                    LOOP_START_FRAME,
                    LOOP_END_EXCLUSIVE - 1,
                ],
                "frame_count": manifest["frame_count"],
                "duration_ms": manifest["duration_ms"],
                "matched_endpoint_alpha_iou": manifest["loop_validation"][
                    "matched_endpoint_alpha_iou"
                ],
                "seam_vs_natural_step_delta": manifest["loop_validation"][
                    "seam_vs_natural_step_delta"
                ],
                "preview": str(outputs["preview"]),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
