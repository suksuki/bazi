from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(
    os.environ.get("V50_DREAM_REFERENCE_SOURCE_DIR", str(Path.home() / "Downloads"))
).expanduser()
ASSET_ROOT = (
    ROOT
    / "artifacts/abu-dream-world/director-reference/dream-encounter-01/v1"
)
GLOBAL_REGISTRY = ROOT / "config/media_asset_registry_v1.json"
WATERMARK_MASK = ASSET_ROOT / "processing/gemini-watermark-mask.png"


@dataclass(frozen=True)
class SegmentSpec:
    segment_id: str
    start_seconds: float
    end_seconds: float
    purpose: str


@dataclass(frozen=True)
class ReferenceSpec:
    reference_id: str
    source_filename: str
    archived_filename: str
    clean_filename: str
    label_zh: str
    director_role: str
    recommended_use: tuple[str, ...]
    do_not_use_for: tuple[str, ...]
    segments: tuple[SegmentSpec, ...]


REFERENCES = (
    ReferenceSpec(
        reference_id="dream_ref_life_tree_growth_v1",
        source_filename="1000056879.mp4",
        archived_filename="01-life-tree-growth-source-with-watermark.mp4",
        clean_filename="01-life-tree-growth-clean.mp4",
        label_zh="生命树生长与阶段变化",
        director_role="tree_lifecycle_motion_language",
        recommended_use=("tree_growth_rhythm", "root_light_language", "tree_breathing_reference"),
        do_not_use_for=("shot_01_direct_runtime", "formal_life_prediction", "canonical_path_claim"),
        segments=(
            SegmentSpec("root_awaken_and_sprout", 0.0, 2.5, "根系苏醒与萌芽节奏"),
            SegmentSpec("tree_emerges_abu_arrives", 2.5, 5.0, "树体显现与阿布进入构图"),
            SegmentSpec("question_fruit_appears", 5.0, 7.5, "问题意象出现的运动参考"),
            SegmentSpec("flowering_settles", 7.5, 10.0, "开花与画面安定节奏"),
        ),
    ),
    ReferenceSpec(
        reference_id="dream_ref_fog_gate_three_trees_v1",
        source_filename="1000056881.mp4",
        archived_filename="02-abu-fog-gate-three-trees-source-with-watermark.mp4",
        clean_filename="02-abu-fog-gate-three-trees-clean.mp4",
        label_zh="阿布穿雾与三树显影",
        director_role="shot_01_02_fog_gate_and_spatial_reveal",
        recommended_use=("fog_gate_camera", "abu_wait_turn_walk", "three_tree_depth_composition"),
        do_not_use_for=("three_equal_choice_ui", "automatic_tree_selection", "final_runtime_video"),
        segments=(
            SegmentSpec("abu_waits", 0.0, 3.5, "阿布等待与入口停顿"),
            SegmentSpec("abu_turns_and_enters_fog", 3.5, 5.5, "阿布转身并进入雾层"),
            SegmentSpec("fog_boundary_opens", 5.5, 7.0, "无实体门框的雾界展开"),
            SegmentSpec("three_trees_revealed", 7.0, 10.0, "三树纵深构图与观察节奏"),
        ),
    ),
    ReferenceSpec(
        reference_id="dream_ref_tree_structure_response_v1",
        source_filename="1000056885.mp4",
        archived_filename="03-tree-structure-response-source-with-watermark.mp4",
        clean_filename="03-tree-structure-response-clean.mp4",
        label_zh="生命树结构回应",
        director_role="tree_touch_response_motion_language",
        recommended_use=("restrained_structure_response", "light_travel_timing", "abu_observation_pose"),
        do_not_use_for=("unverified_path_projection", "multi_symbol_response", "canonical_mingli_assertion"),
        segments=(
            SegmentSpec("abu_observes_tree", 0.0, 2.5, "阿布观察与树的静息状态"),
            SegmentSpec("structure_light_traverses", 2.5, 5.0, "结构光沿树体移动的节奏"),
            SegmentSpec("flower_response", 5.0, 7.5, "单一花朵回应的视觉参考"),
            SegmentSpec("fruit_and_mirror_settle", 7.5, 10.0, "复合象征收束，仅供反例审阅"),
        ),
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


def ensure_sources() -> None:
    missing = [str(SOURCE_ROOT / item.source_filename) for item in REFERENCES if not (SOURCE_ROOT / item.source_filename).is_file()]
    if missing:
        raise SystemExit(f"missing Dream reference videos: {missing}")


def create_watermark_mask() -> None:
    WATERMARK_MASK.parent.mkdir(parents=True, exist_ok=True)
    mask = Image.new("L", (1280, 720), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(
        [
            (1168, 558),
            (1181, 584),
            (1210, 599),
            (1181, 614),
            (1168, 642),
            (1155, 614),
            (1126, 599),
            (1155, 584),
        ],
        fill=255,
    )
    mask.filter(ImageFilter.MaxFilter(7)).save(WATERMARK_MASK)


def clean_master(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        f"removelogo=f={WATERMARK_MASK}",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "17",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output),
    )


def split_segment(master: Path, output: Path, segment: SegmentSpec) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{segment.start_seconds:.3f}",
        "-to",
        f"{segment.end_seconds:.3f}",
        "-i",
        str(master),
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "17",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output),
    )


def render_contact_sheet(master: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(master),
        "-vf",
        "fps=2,scale=320:-1,tile=5x4",
        "-frames:v",
        "1",
        str(output),
    )


def render_keyframe(master: Path, output: Path, at_seconds: float) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{at_seconds:.3f}",
        "-i",
        str(master),
        "-frames:v",
        "1",
        str(output),
    )


def probe(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def build_reference(spec: ReferenceSpec) -> dict[str, Any]:
    source = SOURCE_ROOT / spec.source_filename
    archived = ASSET_ROOT / "sources" / spec.archived_filename
    master = ASSET_ROOT / "clean-masters" / spec.clean_filename
    archived.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, archived)
    clean_master(archived, master)

    segment_rows = []
    for index, segment in enumerate(spec.segments, start=1):
        filename = f"{index:02d}-{segment.segment_id}.mp4"
        segment_path = ASSET_ROOT / "segments" / spec.reference_id / filename
        keyframe_path = ASSET_ROOT / "keyframes" / spec.reference_id / f"{index:02d}-{segment.segment_id}.png"
        split_segment(master, segment_path, segment)
        render_keyframe(master, keyframe_path, (segment.start_seconds + segment.end_seconds) / 2)
        segment_rows.append(
            {
                "segment_id": segment.segment_id,
                "seconds": [segment.start_seconds, segment.end_seconds],
                "purpose": segment.purpose,
                "video": str(segment_path.relative_to(ASSET_ROOT)),
                "video_sha256": sha256(segment_path),
                "keyframe": str(keyframe_path.relative_to(ASSET_ROOT)),
                "keyframe_sha256": sha256(keyframe_path),
            }
        )

    contact_sheet = ASSET_ROOT / "contact-sheets" / f"{spec.reference_id}.png"
    render_contact_sheet(master, contact_sheet)
    return {
        "reference_id": spec.reference_id,
        "label_zh": spec.label_zh,
        "status": "director_reference_registered",
        "director_role": spec.director_role,
        "source": {
            "original_filename": spec.source_filename,
            "archived_file": str(archived.relative_to(ASSET_ROOT)),
            "sha256": sha256(archived),
            "watermark_present": True,
        },
        "clean_master": {
            "file": str(master.relative_to(ASSET_ROOT)),
            "sha256": sha256(master),
            "watermark_removed": True,
            "probe": probe(master),
        },
        "contact_sheet": {
            "file": str(contact_sheet.relative_to(ASSET_ROOT)),
            "sha256": sha256(contact_sheet),
        },
        "segments": segment_rows,
        "recommended_use": list(spec.recommended_use),
        "do_not_use_for": list(spec.do_not_use_for),
    }


def update_global_registry(registry_path: Path) -> None:
    registry = json.loads(GLOBAL_REGISTRY.read_text(encoding="utf-8"))
    registry["dream_director_reference"] = {
        "registry": str(registry_path.relative_to(ROOT)),
        "sha256": sha256(registry_path),
        "status": "reference_only_not_runtime",
        "runtime_authorized": False,
    }
    GLOBAL_REGISTRY.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ensure_sources()
    create_watermark_mask()
    references = [build_reference(spec) for spec in REFERENCES]
    registry = {
        "schema_version": "deepbazi.dream_director_reference.v1",
        "collection_id": "dream-encounter-01-director-reference-v1",
        "status": "registered_reference_only",
        "source_type": "gemini_concept_video",
        "abu_character_reference": {
            "status": "candidate_not_canonical",
            "preferred_reference_id": "dream_ref_fog_gate_three_trees_v1",
            "traits": [
                "round_face",
                "short_muzzle",
                "compact_body",
                "soft_eye_placement",
                "red_scarf",
            ],
            "note_zh": "梦境版阿布候选造型参考；尚未替代正式角色模型表。",
        },
        "references": references,
        "boundaries": {
            "runtime_authorized": False,
            "creates_mingli_claim": False,
            "changes_canonical_scene": False,
            "creates_path_assertion": False,
            "final_product_video": False,
            "use_as_animation_spec_reference": True,
        },
    }
    registry_path = ASSET_ROOT / "registry.json"
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    update_global_registry(registry_path)
    print(
        json.dumps(
            {
                "status": registry["status"],
                "references": len(references),
                "segments": sum(len(item["segments"]) for item in references),
                "registry": str(registry_path),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
