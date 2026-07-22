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
SOURCE_ROOT = Path(
    os.environ.get("V50_ABU_SOURCE_DIR", str(Path.home() / "Downloads"))
).expanduser()
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v12-actor-pass"
ARTIFACT_ROOT = ROOT / "artifacts/abu-actor-pass-v1"
FPS = 15
CANVAS = (960, 720)
FRAME_DURATION_MS = round(1000 / FPS)


@dataclass(frozen=True)
class MotionSpec:
    source: Path
    archived_filename: str
    directory: str
    action_id: str
    motion: str
    action_family: str
    product_role: str
    loop_mode: str
    gaze_target: str
    safe_crop: str
    display_scale: float
    stage_profile: str
    category: str
    recommended_contexts: tuple[str, ...]
    do_not_use_for: tuple[str, ...]
    content_note: str = ""
    drop_initial_frames: int = 0


MOTIONS = (
    MotionSpec(
        source=SOURCE_ROOT / "这个阿布脸太尖了，不是以前那个，应该是可爱一点的.mp4",
        archived_filename="abu_quiet_sit_reaction_source.mp4",
        directory="quiet-sit-reaction",
        action_id="abu_quiet_sit_reaction_v1",
        motion="quiet_sit_reaction",
        action_family="companion_idle",
        product_role="default_companion_presence",
        loop_mode="loop",
        gaze_target="audience",
        safe_crop="full_body",
        display_scale=1.45,
        stage_profile="standard",
        category="guidance",
        recommended_contexts=("abu_dock_idle", "theater_finale_idle", "workspace_companion"),
        do_not_use_for=("busy_processing", "hard_failure", "semantic_pointing"),
    ),
    MotionSpec(
        source=SOURCE_ROOT / "来一个阿布打棒球的视频，初始帧为阿布坐着，我给你阿布坐着的图.mp4",
        archived_filename="abu_baseball_swing_source.mp4",
        directory="baseball-swing",
        action_id="abu_baseball_swing_v1",
        motion="baseball_swing",
        action_family="playful_activity",
        product_role="ambient_active_interlude",
        loop_mode="one_shot",
        gaze_target="activity_object",
        safe_crop="full_body_wide_action",
        display_scale=1.08,
        stage_profile="wide",
        category="ambient",
        recommended_contexts=("life_world_ambient", "theater_finale", "social_ip_moment"),
        do_not_use_for=("professional_explanation", "reading_success", "favorable_result_signal"),
        drop_initial_frames=1,
    ),
    MotionSpec(
        source=SOURCE_ROOT / "来一个阿布打日本pachinko_，获得大奖视频，和以前一样.mp4",
        archived_filename="abu_pachinko_jackpot_source.mp4",
        directory="pachinko-jackpot",
        action_id="abu_pachinko_jackpot_v1",
        motion="pachinko_jackpot",
        action_family="playful_arcade_cameo",
        product_role="rare_finale_arcade_easter_egg",
        loop_mode="one_shot",
        gaze_target="activity_object",
        safe_crop="full_body_with_machine",
        display_scale=1.04,
        stage_profile="extra_wide",
        category="ambient_restricted",
        recommended_contexts=("theater_finale_rare", "internal_motion_gallery", "social_ip_easter_egg"),
        do_not_use_for=(
            "wealth_or_fortune_reading",
            "reading_success",
            "payment_or_reward_prompt",
            "professional_explanation",
            "default_child_facing_scene",
        ),
        content_note="Arcade-style pachinko imagery; never bind this action to a user's fortune or outcome.",
    ),
)


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def filter_for(spec: MotionSpec) -> str:
    trim = (
        f"trim=start_frame={spec.drop_initial_frames},setpts=PTS-STARTPTS,"
        if spec.drop_initial_frames
        else ""
    )
    return (
        f"fps={FPS},{trim}"
        "crop=1120:720:80:0,"
        "drawbox=x=1005:y=485:w=115:h=165:color=black:t=fill,"
        "colorkey=black:0.018:0.06,"
        "format=rgba,"
        "scale=960:617:flags=lanczos,"
        "pad=960:720:0:103:color=0x00000000"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_sources() -> None:
    missing = [str(spec.source) for spec in MOTIONS if not spec.source.exists()]
    if missing:
        raise SystemExit(f"missing Abu source videos: {missing}")


def archive_sources() -> None:
    source_dir = ARTIFACT_ROOT / "source-videos"
    source_dir.mkdir(parents=True, exist_ok=True)
    for spec in MOTIONS:
        shutil.copy2(spec.source, source_dir / spec.archived_filename)


def contact_sheet_from_source(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        "fps=1,scale=320:-1,tile=5x2",
        "-frames:v",
        "1",
        str(output),
    )


def build_source_review() -> None:
    review_dir = ARTIFACT_ROOT / "source-contact-sheets/playful-v14"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_items = []
    for spec in MOTIONS:
        contact_sheet_from_source(spec.source, review_dir / f"{spec.motion}.jpg")
        review_items.append(
            {
                "action_id": spec.action_id,
                "source_filename": spec.source.name,
                "source_sha256": sha256(spec.source),
                "status": "selected_for_production",
                "product_role": spec.product_role,
                "do_not_use_for": list(spec.do_not_use_for),
                "content_note": spec.content_note,
            }
        )
    review = {
        "version": "v50.abu.playful_motion_source_review.v1",
        "sources": review_items,
    }
    (review_dir / "source-review.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def checkerboard(size: tuple[int, int], cell: int = 16) -> Image.Image:
    image = Image.new("RGBA", size, (239, 239, 234, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if ((x // cell) + (y // cell)) % 2:
                draw.rectangle(
                    (x, y, x + cell - 1, y + cell - 1),
                    fill=(214, 220, 215, 255),
                )
    return image


def build_contact_sheet(frames: list[Image.Image], output: Path) -> None:
    columns, rows = 5, 2
    thumb_size = (320, 240)
    sheet = Image.new("RGB", (thumb_size[0] * columns, thumb_size[1] * rows), "white")
    selected = [
        round(index * (len(frames) - 1) / (columns * rows - 1))
        for index in range(columns * rows)
    ]
    for position, frame_index in enumerate(selected):
        background = checkerboard(thumb_size)
        actor = frames[frame_index].copy()
        actor.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        x = (thumb_size[0] - actor.width) // 2
        y = thumb_size[1] - actor.height
        background.alpha_composite(actor, (x, y))
        sheet.paste(
            background.convert("RGB"),
            ((position % columns) * thumb_size[0], (position // columns) * thumb_size[1]),
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92, optimize=True)


def build_action(spec: MotionSpec) -> dict[str, object]:
    action_root = ASSET_ROOT / spec.directory
    web_dir = action_root / "web"
    poster_dir = action_root / "posters"
    contact_dir = action_root / "contact-sheets"
    for directory in (web_dir, poster_dir, contact_dir):
        directory.mkdir(parents=True, exist_ok=True)

    webm = web_dir / f"{spec.action_id}.webm"
    webp = web_dir / f"{spec.action_id}.webp"
    poster = poster_dir / f"{spec.action_id}.png"
    contact_sheet = contact_dir / f"{spec.action_id}_contact_sheet.png"

    with tempfile.TemporaryDirectory(prefix=f"{spec.motion}-") as temp_name:
        temp_dir = Path(temp_name)
        frame_pattern = temp_dir / "frame-%04d.png"
        run(
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(spec.source),
            "-vf",
            filter_for(spec),
            str(frame_pattern),
        )
        frame_paths = sorted(temp_dir.glob("frame-*.png"))
        frames = [Image.open(path).convert("RGBA") for path in frame_paths]
        if len(frames) < 140:
            raise RuntimeError(f"unexpected {spec.motion} frame count: {len(frames)}")

        frames[0].save(poster, optimize=True)
        frames[0].save(
            webp,
            save_all=True,
            append_images=frames[1:],
            duration=FRAME_DURATION_MS,
            loop=0 if spec.loop_mode == "loop" else 1,
            quality=92,
            method=3,
        )
        build_contact_sheet(frames, contact_sheet)

    run(
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(spec.source),
        "-vf",
        filter_for(spec),
        "-an",
        "-c:v",
        "libvpx-vp9",
        "-b:v",
        "0",
        "-crf",
        "25",
        "-pix_fmt",
        "yuva420p",
        "-auto-alt-ref",
        "0",
        str(webm),
    )

    frame_count = len(frames)
    duration_ms = round(frame_count / FPS * 1000)
    manifest = {
        "version": "v50.abu.designer_motion.v1",
        "status": "production",
        "motion": spec.motion,
        "action_id": spec.action_id,
        "action_family": spec.action_family,
        "product_role": spec.product_role,
        "source_type": "designer_video",
        "source": {
            "filename": spec.source.name,
            "archived_filename": spec.archived_filename,
            "sha256": sha256(spec.source),
            "frame_count": 240,
            "fps": FPS,
            "segment_seconds": [round(spec.drop_initial_frames / FPS, 3), 10.0],
            "dropped_initial_frames": spec.drop_initial_frames,
        },
        "canvas": list(CANVAS),
        "anchor": [0.5, 0.9861111111111112],
        "actor_contract": {
            "facing": "front",
            "gaze_target": spec.gaze_target,
            "safe_crop": spec.safe_crop,
            "background": "transparent",
            "flip_horizontal": False,
            "loop_mode": spec.loop_mode,
            "recommended_contexts": list(spec.recommended_contexts),
        },
        "source_size": [1280, 720],
        "character_crop_box": [80, 0, 1120, 720],
        "transparent_background": True,
        "fixed_character_scale": True,
        "watermark_removed": True,
        "removed_regions": [
            {
                "name": "source_lower_right_sparkle_mark",
                "method": "painted_black_before_alpha_extraction",
                "post_crop_box": [1005, 485, 1120, 650],
            }
        ],
        "alpha_matte": {"similarity": 0.018, "blend": 0.06},
        "webp": {
            "quality": 92,
            "method": 3,
            "loop_count": 0 if spec.loop_mode == "loop" else 1,
        },
        "runtime_display": {
            "scale": spec.display_scale,
            "stage_profile": spec.stage_profile,
            "playback": spec.loop_mode,
            "category": spec.category,
        },
        "animation": f"web/{spec.action_id}.webp",
        "video": f"web/{spec.action_id}.webm",
        "poster": f"posters/{spec.action_id}.png",
        "contact_sheet": f"contact-sheets/{spec.action_id}_contact_sheet.png",
        "frame_count": frame_count,
        "duration_ms": duration_ms,
        "delivery_bytes": {"webp": webp.stat().st_size, "webm": webm.stat().st_size},
        "usage": list(spec.recommended_contexts),
        "content_note": spec.content_note,
        "boundaries": {
            "creates_mingli_claim": False,
            "changes_case_state": False,
            "must_not_interrupt_professional_explanation": spec.action_family != "companion_idle",
            "do_not_use_for": list(spec.do_not_use_for),
        },
    }
    (action_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "action_id": spec.action_id,
        "output": str(action_root),
        "duration_ms": duration_ms,
    }


def main() -> None:
    ensure_sources()
    archive_sources()
    build_source_review()
    outputs = [build_action(spec) for spec in MOTIONS]
    print(json.dumps({"actions": outputs}, ensure_ascii=False))


if __name__ == "__main__":
    main()
