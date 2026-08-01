from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from abu_v60.media import PROJECT_ROOT, load_verified_media_catalog
from abu_v60.provenance import canonical_json


def probe(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise RuntimeError("ffprobe is required for V60 media technical audit")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def main() -> None:
    catalog = load_verified_media_catalog()
    audited_deliveries = 0
    alpha_videos = 0
    audio_deliveries = 0

    for item in catalog["items"]:
        for delivery in item.get("deliveries", []):
            role = str(delivery["role"])
            path = PROJECT_ROOT / str(delivery["path"])
            streams = probe(path)["streams"]
            video_streams = [
                stream for stream in streams if stream["codec_type"] == "video"
            ]
            audio_streams = [
                stream for stream in streams if stream["codec_type"] == "audio"
            ]

            if role == "VP9_ALPHA_WEBM":
                if len(video_streams) != 1 or audio_streams:
                    raise RuntimeError(f"{path} must contain one video stream and no audio")
                video = video_streams[0]
                tags = {
                    str(key).upper(): str(value)
                    for key, value in video.get("tags", {}).items()
                }
                alpha_mode = tags.get("ALPHA_MODE", "0")
                if video["codec_name"] != "vp9" or alpha_mode != "1":
                    raise RuntimeError(f"{path} is not a VP9 alpha delivery")
                alpha_videos += 1

            if role.startswith("WEB_AUDIO_"):
                if not audio_streams or video_streams:
                    raise RuntimeError(f"{path} must contain audio and no video")
                audio_deliveries += 1

            audited_deliveries += 1

    print(
        canonical_json(
            {
                "audited_deliveries": audited_deliveries,
                "vp9_alpha_video_deliveries": alpha_videos,
                "audio_only_deliveries": audio_deliveries,
                "status": "PASS",
            }
        )
    )


if __name__ == "__main__":
    main()
