from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path("/Users/liujin/Downloads")
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v12-actor-pass"
ACTION_ROOT = ASSET_ROOT / "ninja-disappear-throw"
ARTIFACT_ROOT = ROOT / "artifacts/abu-actor-pass-v1"

SOURCES = {
    "sitting_full_body": DOWNLOADS / "对不起，应该是初始帧为阿布坐立的全身像.mp4",
    "standing_full_body": DOWNLOADS / "不错，但是有个问题，初始帧的阿布，站着的阿布改为站立全身像.mp4",
    "half_body": DOWNLOADS / "来一段阿布忍者形象的视频，设计为忍者消失，扔飞镖，记得视频开.mp4",
}

ARCHIVE_NAMES = {
    "sitting_full_body": "abu_ninja_sitting_start_source.mp4",
    "standing_full_body": "abu_ninja_standing_start_source.mp4",
    "half_body": "abu_ninja_half_body_start_source.mp4",
}

ACTION_ID = "abu_ninja_disappear_throw_v1"
FPS = 15
CANVAS = (960, 720)
FRAME_DURATION_MS = round(1000 / FPS)
FILTER = (
    "fps=15,"
    "crop=1120:720:80:0,"
    "drawbox=x=1005:y=485:w=115:h=165:color=black:t=fill,"
    "colorkey=black:0.018:0.06,"
    "format=rgba,"
    "scale=960:617:flags=lanczos,"
    "pad=960:720:0:103:color=0x00000000"
)


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_sources() -> None:
    missing = [str(path) for path in SOURCES.values() if not path.exists()]
    if missing:
        raise SystemExit(f"missing Abu source videos: {missing}")


def archive_sources() -> None:
    source_dir = ARTIFACT_ROOT / "source-videos"
    source_dir.mkdir(parents=True, exist_ok=True)
    for variant, source in SOURCES.items():
        shutil.copy2(source, source_dir / ARCHIVE_NAMES[variant])


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


def build_variant_review() -> None:
    review_dir = ARTIFACT_ROOT / "source-contact-sheets/ninja"
    review_dir.mkdir(parents=True, exist_ok=True)
    for variant, source in SOURCES.items():
        contact_sheet_from_source(source, review_dir / f"{variant}.jpg")
    review = {
        "version": "v50.abu.ninja_source_review.v1",
        "selected_variant": "sitting_full_body",
        "variants": [
            {
                "variant": "sitting_full_body",
                "source_sha256": sha256(SOURCES["sitting_full_body"]),
                "status": "selected_for_production",
                "reason": "完整坐姿保持 Abu 的可爱体态，避免片尾以双脚直立形象突兀开场。",
            },
            {
                "variant": "standing_full_body",
                "source_sha256": sha256(SOURCES["standing_full_body"]),
                "status": "candidate_pose_hold",
                "reason": "双脚直立形象改变了 Abu 的常规体态，片尾第一眼过于突兀。",
            },
            {
                "variant": "half_body",
                "source_sha256": sha256(SOURCES["half_body"]),
                "status": "candidate_framing_hold",
                "reason": "开场为半身近景，无法与片尾全身角色无缝衔接。",
            },
        ],
    }
    (review_dir / "variant-review.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def checkerboard(size: tuple[int, int], cell: int = 16) -> Image.Image:
    image = Image.new("RGBA", size, (239, 239, 234, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if ((x // cell) + (y // cell)) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(214, 220, 215, 255))
    return image


def build_contact_sheet(frames: list[Image.Image], output: Path) -> None:
    columns, rows = 5, 2
    thumb_size = (320, 240)
    sheet = Image.new("RGB", (thumb_size[0] * columns, thumb_size[1] * rows), "white")
    selected = [round(index * (len(frames) - 1) / (columns * rows - 1)) for index in range(columns * rows)]
    for position, frame_index in enumerate(selected):
        background = checkerboard(thumb_size)
        actor = frames[frame_index].copy()
        actor.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        x = (thumb_size[0] - actor.width) // 2
        y = thumb_size[1] - actor.height
        background.alpha_composite(actor, (x, y))
        sheet.paste(background.convert("RGB"), ((position % columns) * thumb_size[0], (position // columns) * thumb_size[1]))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92, optimize=True)


def build_action() -> None:
    source = SOURCES["sitting_full_body"]
    web_dir = ACTION_ROOT / "web"
    poster_dir = ACTION_ROOT / "posters"
    contact_dir = ACTION_ROOT / "contact-sheets"
    for directory in (web_dir, poster_dir, contact_dir):
        directory.mkdir(parents=True, exist_ok=True)

    webm = web_dir / "abu_ninja_disappear_throw_v1.webm"
    webp = web_dir / "abu_ninja_disappear_throw_v1.webp"
    poster = poster_dir / "abu_ninja_disappear_throw_v1.png"
    contact_sheet = contact_dir / "abu_ninja_disappear_throw_v1_contact_sheet.png"

    with tempfile.TemporaryDirectory(prefix="abu-ninja-v13-") as temp_name:
        temp_dir = Path(temp_name)
        frame_pattern = temp_dir / "frame-%04d.png"
        run(
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-vf",
            FILTER,
            str(frame_pattern),
        )
        frame_paths = sorted(temp_dir.glob("frame-*.png"))
        frames = [Image.open(path).convert("RGBA") for path in frame_paths]
        if len(frames) < 140:
            raise RuntimeError(f"unexpected ninja frame count: {len(frames)}")

        frames[0].save(poster, optimize=True)
        frames[0].save(
            webp,
            save_all=True,
            append_images=frames[1:],
            duration=FRAME_DURATION_MS,
            loop=1,
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
        str(source),
        "-vf",
        FILTER,
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
        "motion": "ninja_disappear_throw",
        "action_id": ACTION_ID,
        "action_family": "playful_transition",
        "source_type": "extracted_video",
        "source": {
            "filename": source.name,
            "archived_filename": ARCHIVE_NAMES["sitting_full_body"],
            "sha256": sha256(source),
            "frame_count": 240,
            "fps": FPS,
            "segment_seconds": [0.0, 10.0],
            "selected_variant": "sitting_full_body",
        },
        "canvas": list(CANVAS),
        "anchor": [0.5, 0.9861111111111112],
        "actor_contract": {
            "facing": "front",
            "gaze_target": "audience",
            "safe_crop": "full_body_wide_action",
            "background": "transparent",
            "flip_horizontal": False,
            "loop_mode": "one_shot",
            "recommended_contexts": ["theater_finale", "ambient_ip_moment", "scene_transition_cameo"],
        },
        "source_size": [1280, 720],
        "character_crop_box": [80, 0, 1120, 720],
        "transparent_background": True,
        "fixed_character_scale": True,
        "watermark_removed": True,
        "removed_regions": [
            {
                "name": "source_lower_right_sparkle_mark",
                "method": "excluded_before_alpha_extraction",
            }
        ],
        "alpha_matte": {"similarity": 0.018, "blend": 0.06},
        "webp": {"quality": 92, "method": 3, "loop_count": 1},
        "runtime_display": {
            "scale": 1.16,
            "stage_profile": "wide",
            "playback": "one_shot",
            "category": "ambient",
        },
        "animation": "web/abu_ninja_disappear_throw_v1.webp",
        "video": "web/abu_ninja_disappear_throw_v1.webm",
        "poster": "posters/abu_ninja_disappear_throw_v1.png",
        "contact_sheet": "contact-sheets/abu_ninja_disappear_throw_v1_contact_sheet.png",
        "frame_count": frame_count,
        "duration_ms": duration_ms,
        "delivery_bytes": {"webp": webp.stat().st_size, "webm": webm.stat().st_size},
        "usage": ["theater_finale", "ambient_ip_moment", "scene_transition_cameo"],
        "boundaries": {
            "playful_ip_action_only": True,
            "creates_mingli_claim": False,
            "changes_case_state": False,
            "must_not_interrupt_professional_explanation": True,
        },
    }
    (ACTION_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ensure_sources()
    archive_sources()
    build_variant_review()
    build_action()
    print(json.dumps({"action_id": ACTION_ID, "output": str(ACTION_ROOT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
