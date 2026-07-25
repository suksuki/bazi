from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    os.environ.get(
        "V50_ABU_DREAM_STANDARD_SOURCE",
        str(
            Path.home()
            / "Downloads/这一版阿布更可爱，来一个透明背景的，阿布坐着开始的标准视频，.mp4"
        ),
    )
).expanduser()
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v12-actor-pass"
ARTIFACT_ROOT = ROOT / "artifacts/abu-actor-pass-v1"
LIBRARY = ASSET_ROOT / "library.json"
INVENTORY = ASSET_ROOT / "video-inventory.json"
GLOBAL_REGISTRY = ROOT / "config/media_asset_registry_v1.json"
MOTION_REGISTRY = ASSET_ROOT.parent / "motion-registry.js"
FPS = 15
CANVAS = (960, 720)
BOTTOM_ANCHOR = 710
SOURCE_CROP_WIDTH = 1040
KEY_FILTER = (
    f"fps={FPS},crop={SOURCE_CROP_WIDTH}:720:0:0,format=rgba,"
    "colorkey=0x009e42:0.14:0.06,"
    "despill=type=green:mix=0.5:expand=0.05,format=rgba"
)


@dataclass(frozen=True)
class MotionSpec:
    directory: str
    action_id: str
    motion: str
    start: float
    end: float
    label_zh: str
    description_zh: str
    action_family: str
    product_role: str
    loop_mode: str
    gaze_target: str
    recommended_contexts: tuple[str, ...]
    do_not_use_for: tuple[str, ...]
    display_scale: float = 1.0
    stage_profile: str = "standard"
    category: str = "guidance"


MOTIONS = (
    MotionSpec(
        directory="dream-standard-cycle",
        action_id="abu_dream_standard_cycle_v1",
        motion="dream_standard_cycle",
        start=0.0,
        end=10.0,
        label_zh="默认阿布标准循环",
        description_zh="新版圆脸阿布从安静坐姿开始，观察四周、起身回应并自然回坐，作为统一产品中的默认陪伴形象。",
        action_family="default_companion",
        product_role="default_companion_presence",
        loop_mode="loop",
        gaze_target="semantic_world",
        recommended_contexts=(
            "workspace_companion",
            "dream_world_companion",
            "theater_finale_idle",
        ),
        do_not_use_for=("专业结论宣判", "命运吉凶暗示", "忙碌计算状态"),
    ),
    MotionSpec(
        directory="dream-seated-observe",
        action_id="abu_dream_seated_observe_v1",
        motion="dream_seated_observe",
        start=0.0,
        end=6.25,
        label_zh="坐姿观察与倾听",
        description_zh="阿布保持完整坐姿，轻微眨眼、抬头和转头，适合安静等待、倾听与观察梦境对象。",
        action_family="companion_idle",
        product_role="quiet_companion_presence",
        loop_mode="loop",
        gaze_target="semantic_world",
        recommended_contexts=("dream_gate_wait", "tree_observation", "quiet_companion"),
        do_not_use_for=("指向具体节点", "忙碌计算状态", "严重错误反馈"),
    ),
    MotionSpec(
        directory="dream-stand-and-return",
        action_id="abu_dream_stand_and_return_v1",
        motion="dream_stand_and_return",
        start=6.25,
        end=10.0,
        label_zh="起身回应并回坐",
        description_zh="阿布由坐姿自然起身、短暂停留并带着轻松表情回到坐姿，用于一次克制的确认或相遇回应。",
        action_family="companion_reaction",
        product_role="gentle_acknowledgement",
        loop_mode="one_shot",
        gaze_target="audience",
        recommended_contexts=("dream_encounter_acknowledgement", "gentle_confirmation"),
        do_not_use_for=("专业判断成立", "吉凶结果反馈", "语义指向"),
    ),
)


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    frames = [Image.open(path).convert("RGBA") for path in sorted(output_dir.glob("frame-*.png"))]
    if len(frames) != 150:
        raise RuntimeError(f"expected 150 keyed frames, got {len(frames)}")
    return frames


def union_box(frames: list[Image.Image]) -> tuple[int, int, int, int]:
    boxes = [frame.getchannel("A").getbbox() for frame in frames]
    boxes = [box for box in boxes if box]
    if not boxes:
        raise RuntimeError("green-screen extraction produced no visible Abu pixels")
    left = min(box[0] for box in boxes)
    top = min(box[1] for box in boxes)
    right = max(box[2] for box in boxes)
    bottom = max(box[3] for box in boxes)
    if right >= SOURCE_CROP_WIDTH - 8:
        raise RuntimeError("Abu touches the source isolation boundary")
    padding = 14
    return (
        max(0, left - padding),
        max(0, top - padding),
        min(SOURCE_CROP_WIDTH, right + padding),
        min(720, bottom + padding),
    )


def normalize_frames(
    frames: list[Image.Image], crop_box: tuple[int, int, int, int]
) -> list[Image.Image]:
    crop_width = crop_box[2] - crop_box[0]
    crop_height = crop_box[3] - crop_box[1]
    scale = min(620 / crop_width, 680 / crop_height)
    size = (round(crop_width * scale), round(crop_height * scale))
    normalized = []
    for frame in frames:
        actor = frame.crop(crop_box).resize(size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        x = (CANVAS[0] - actor.width) // 2
        y = BOTTOM_ANCHOR - actor.height
        canvas.alpha_composite(actor, (x, y))
        normalized.append(canvas)
    return normalized


def checkerboard(size: tuple[int, int], cell: int = 20) -> Image.Image:
    image = Image.new("RGBA", size, "#eef1ed")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill="#d7ddd8")
    return image


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
        sheet.paste(background.convert("RGB"), ((slot % columns) * tile[0], (slot // columns) * tile[1]))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=94, optimize=True)


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


def build_action(
    spec: MotionSpec,
    all_frames: list[Image.Image],
    crop_box: tuple[int, int, int, int],
) -> tuple[dict[str, object], dict[str, object]]:
    start = round(spec.start * FPS)
    end = min(len(all_frames), round(spec.end * FPS))
    frames = all_frames[start:end]
    if len(frames) < 2:
        raise RuntimeError(f"{spec.action_id} has too few frames")

    action_root = ASSET_ROOT / spec.directory
    web_dir = action_root / "web"
    poster_dir = action_root / "posters"
    contact_dir = action_root / "contact-sheets"
    for directory in (web_dir, poster_dir, contact_dir):
        directory.mkdir(parents=True, exist_ok=True)

    webp = web_dir / f"{spec.action_id}.webp"
    webm = web_dir / f"{spec.action_id}.webm"
    poster = poster_dir / f"{spec.action_id}.png"
    contact = contact_dir / f"{spec.action_id}_contact_sheet.png"
    frames[0].save(
        webp,
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / FPS),
        loop=0 if spec.loop_mode == "loop" else 1,
        quality=92,
        method=3,
        minimize_size=False,
    )
    save_webm(frames, webm)
    frames[0].save(poster, optimize=True)
    save_contact_sheet(frames, contact)

    duration_ms = round(len(frames) / FPS * 1000)
    manifest = {
        "version": "v50.abu.green_screen_motion.v1",
        "status": "production",
        "motion": spec.motion,
        "action_id": spec.action_id,
        "action_family": spec.action_family,
        "product_role": spec.product_role,
        "source_type": "designer_green_screen_video",
        "source": {
            "filename": SOURCE.name,
            "archived_filename": "abu_dream_standard_green_source.mp4",
            "sha256": sha256(SOURCE),
            "frame_count": 240,
            "fps": FPS,
            "segment_seconds": [spec.start, spec.end],
        },
        "canvas": list(CANVAS),
        "anchor": [0.5, BOTTOM_ANCHOR / CANVAS[1]],
        "actor_contract": {
            "facing": "front",
            "gaze_target": spec.gaze_target,
            "safe_crop": "full_body",
            "background": "transparent",
            "flip_horizontal": False,
            "loop_mode": spec.loop_mode,
            "recommended_contexts": list(spec.recommended_contexts),
        },
        "source_size": [1280, 720],
        "source_isolation_box": [0, 0, SOURCE_CROP_WIDTH, 720],
        "character_crop_box": list(crop_box),
        "transparent_background": True,
        "fixed_character_scale": True,
        "watermark_removed": True,
        "removed_regions": [
            {
                "name": "source_green_sparkle_mark",
                "method": "green_screen_key_and_character_isolation",
            }
        ],
        "alpha_matte": {
            "key_color": "#009e42",
            "similarity": 0.14,
            "blend": 0.06,
            "despill": {"type": "green", "mix": 0.5, "expand": 0.05},
        },
        "character_style": {
            "status": "owner_approved_default",
            "traits": ["round_face", "short_muzzle", "compact_body", "soft_eye_placement"],
        },
        "runtime_display": {
            "scale": spec.display_scale,
            "stage_profile": spec.stage_profile,
            "playback": spec.loop_mode,
            "category": spec.category,
        },
        "animation": f"web/{webp.name}",
        "video": f"web/{webm.name}",
        "poster": f"posters/{poster.name}",
        "contact_sheet": f"contact-sheets/{contact.name}",
        "frame_count": len(frames),
        "duration_ms": duration_ms,
        "delivery_bytes": {"webp": webp.stat().st_size, "webm": webm.stat().st_size},
        "usage": list(spec.recommended_contexts),
        "boundaries": {
            "creates_mingli_claim": False,
            "changes_case_state": False,
            "do_not_use_for": list(spec.do_not_use_for),
        },
    }
    (action_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    library_action = {
        "action_id": spec.action_id,
        "action_family": spec.action_family,
        "status": "production",
        "label_zh": spec.label_zh,
        "description_zh": spec.description_zh,
        "product_role": spec.product_role,
        "do_not_use_for": list(spec.do_not_use_for),
        "manifest": f"{spec.directory}/manifest.json",
        "video": f"{spec.directory}/web/{spec.action_id}.webm",
        "animation": f"{spec.directory}/web/{spec.action_id}.webp",
        "poster": f"{spec.directory}/posters/{spec.action_id}.png",
        "contact_sheet": f"{spec.directory}/contact-sheets/{spec.action_id}_contact_sheet.png",
        "duration_ms": duration_ms,
        "display_scale": spec.display_scale,
        "loop_mode": spec.loop_mode,
        "facing": "front",
        "gaze_target": spec.gaze_target,
        "safe_crop": "full_body",
        "recommended_contexts": list(spec.recommended_contexts),
    }
    return manifest, library_action


def update_inventory() -> None:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    inventory["sources"] = [
        item for item in inventory["sources"] if item["source_id"] != "dream_standard_cute_green"
    ]
    inventory["sources"].append(
        {
            "source_id": "dream_standard_cute_green",
            "filename": SOURCE.name,
            "archived_source": "artifacts/abu-actor-pass-v1/source-videos/abu_dream_standard_green_source.mp4",
            "sha256": sha256(SOURCE),
            "background": "green_screen",
            "actions": ["sit", "blink", "look_up", "head_turn", "stand", "smile", "return_sit"],
            "selected_ranges": [
                {"seconds": [spec.start, spec.end], "action_id": spec.action_id}
                for spec in MOTIONS
            ],
            "quality": "owner_approved_default_character_motion",
            "notes": [
                "Owner promoted this round-faced dream-world Abu as the default character on 2026-07-22.",
                "Previous default remains traceable as a retired action.",
            ],
            "removed_regions": ["green_screen", "source_green_sparkle_mark"],
        }
    )
    INVENTORY.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def update_library(actions: list[dict[str, object]]) -> None:
    library = json.loads(LIBRARY.read_text(encoding="utf-8"))
    new_ids = {action["action_id"] for action in actions}
    retained = []
    for action in library["actions"]:
        if action["action_id"] in new_ids:
            continue
        if action["action_id"] == "abu_quiet_sit_reaction_v1":
            action["status"] = "retired"
            action["product_role"] = "retired_previous_default_companion"
            action["superseded_by"] = "abu_dream_standard_cycle_v1"
        retained.append(action)
    library["actions"] = retained + actions
    library["governance"]["default_action_id"] = "abu_dream_standard_cycle_v1"
    library["governance"]["default_character_source_id"] = "dream_standard_cute_green"
    LIBRARY.write_text(
        json.dumps(library, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def update_global_registry() -> None:
    registry = json.loads(GLOBAL_REGISTRY.read_text(encoding="utf-8"))
    registry["abu_motion"]["sha256"] = sha256(MOTION_REGISTRY)
    registry["abu_motion"]["library"] = str(LIBRARY.relative_to(ROOT))
    registry["abu_motion"]["library_sha256"] = sha256(LIBRARY)
    registry["abu_motion"]["source_inventory"] = str(INVENTORY.relative_to(ROOT))
    registry["abu_motion"]["source_inventory_sha256"] = sha256(INVENTORY)
    registry["abu_motion"]["default_action_id"] = "abu_dream_standard_cycle_v1"
    GLOBAL_REGISTRY.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_source_review() -> None:
    archive = ARTIFACT_ROOT / "source-videos/abu_dream_standard_green_source.mp4"
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, archive)
    review_dir = ARTIFACT_ROOT / "source-contact-sheets/dream-standard-v15"
    review_dir.mkdir(parents=True, exist_ok=True)
    run(
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(SOURCE),
        "-vf",
        "fps=2,scale=320:-1,tile=5x4",
        "-frames:v",
        "1",
        str(review_dir / "source-contact-sheet.png"),
    )
    (review_dir / "source-review.json").write_text(
        json.dumps(
            {
                "version": "v50.abu.dream_standard_source_review.v1",
                "source_sha256": sha256(SOURCE),
                "decision": "owner_approved_default_character_motion",
                "action_ids": [spec.action_id for spec in MOTIONS],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"missing Abu source video: {SOURCE}")
    build_source_review()
    with tempfile.TemporaryDirectory(prefix="abu-dream-standard-v15-") as temp_name:
        keyed = extract_keyed_frames(Path(temp_name))
        crop_box = union_box(keyed)
        normalized = normalize_frames(keyed, crop_box)
        built = [build_action(spec, normalized, crop_box) for spec in MOTIONS]
    update_inventory()
    update_library([item[1] for item in built])
    update_global_registry()
    print(
        json.dumps(
            {
                "status": "promoted_default",
                "default_action_id": "abu_dream_standard_cycle_v1",
                "actions": [item[0]["action_id"] for item in built],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
