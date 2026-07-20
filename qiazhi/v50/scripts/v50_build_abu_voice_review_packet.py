from __future__ import annotations

import argparse
import io
import json
import os
import wave
from datetime import datetime, timezone
from pathlib import Path

from product.narrated_workspace import FfmpegOpusTranscoder
from product.theater_performance import QwenTheaterTTS


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the private Abu voice listening packet.")
    parser.add_argument("--profile", default=str(ROOT / "data/voice/abu_voice_profile_v1.json"))
    parser.add_argument("--corpus", default=str(ROOT / "data/voice/abu_voice_corpus_v1.json"))
    parser.add_argument("--base-url", default=os.getenv("V50_TTS_BASE_URL", "http://127.0.0.1:17860"))
    parser.add_argument("--api-key", default=os.getenv("V50_TTS_API_KEY", ""))
    parser.add_argument("--output-dir", default=str(ROOT / "reports/abu-voice-review-v1"))
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    items = list(corpus["items"])
    if args.limit > 0:
        items = items[: args.limit]
    output_dir = Path(args.output_dir)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    transcoder = FfmpegOpusTranscoder(os.getenv("V50_FFMPEG_BINARY", "ffmpeg"))
    rows: list[dict[str, object]] = []
    for item in items:
        scene_instruction = profile["scene_instructions"][item["scene"]]
        instruction = f"{profile['base_instruction']} {scene_instruction}"
        tts = QwenTheaterTTS(
            base_url=args.base_url,
            speaker=profile["voice_id"],
            instruction=instruction,
            api_key=args.api_key,
        )
        row: dict[str, object] = {
            **item,
            "voice_version": tts.voice_version,
            "status": "failed",
            "human_review": {
                "pronunciation": None,
                "stress": None,
                "pause_naturalness": None,
                "certainty_tone": None,
                "broadcast_voice_risk": None,
                "child_voice_risk": None,
                "two_minute_listening_fit": None,
                "notes": ""
            },
        }
        try:
            speech = tts.synthesize(item["text"])
            opus = transcoder.transcode(speech.wav_bytes)
            wav_path = audio_dir / f"{item['id']}.wav"
            opus_path = audio_dir / f"{item['id']}.opus"
            wav_path.write_bytes(speech.wav_bytes)
            opus_path.write_bytes(opus)
            duration_ms, sample_rate = wav_metadata(speech.wav_bytes)
            row.update(
                {
                    "status": "ready_for_human_review",
                    "wav_path": str(wav_path.relative_to(output_dir)),
                    "opus_path": str(opus_path.relative_to(output_dir)),
                    "duration_ms": duration_ms,
                    "sample_rate": sample_rate,
                    "generation_seconds": speech.generation_seconds,
                    "wav_size_bytes": len(speech.wav_bytes),
                    "opus_size_bytes": len(opus),
                    "compression_ratio": round(len(opus) / len(speech.wav_bytes), 4),
                }
            )
        except Exception as exc:  # Packet generation must retain the failed item for review.
            row["error"] = f"{type(exc).__name__}:{exc}"
        rows.append(row)

    report = {
        "schema_version": "deepbazi.abu_voice_review_packet.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile_version": profile["profile_version"],
        "corpus_version": corpus["corpus_version"],
        "voice_id": profile["voice_id"],
        "status": "awaiting_human_review",
        "human_review_performed": False,
        "items": rows,
    }
    (output_dir / "abu_voice_review_packet_v1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "ABU_VOICE_REVIEW_PACKET_V1.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    print(json.dumps({"items": len(rows), "ready": sum(row["status"] == "ready_for_human_review" for row in rows)}, ensure_ascii=False))
    return 0 if all(row["status"] == "ready_for_human_review" for row in rows) else 1


def wav_metadata(payload: bytes) -> tuple[int, int]:
    with wave.open(io.BytesIO(payload), "rb") as reader:
        return round(reader.getnframes() / reader.getframerate() * 1000), reader.getframerate()


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Abu Voice Review Packet v1",
        "",
        f"- Candidate voice: `{report['voice_id']}`",
        f"- Profile: `{report['profile_version']}`",
        f"- Status: `{report['status']}`",
        "- 当前文件只证明音频已生成，不代表声线或发音已经通过人工审听。",
        "",
        "## Listening Order",
        "",
        "| ID | 场景 | 时长 | Opus / WAV | 人工结论 |",
        "|---|---|---:|---|---|",
    ]
    for row in report["items"]:
        audio = f"[{row.get('opus_path', '缺失')}]({row.get('opus_path', '')}) / [{row.get('wav_path', '缺失')}]({row.get('wav_path', '')})" if row["status"] == "ready_for_human_review" else "生成失败"
        lines.append(
            f"| `{row['id']}` | {row['scene']} | {round((row.get('duration_ms') or 0) / 1000, 1)}s | {audio} | 待审听 |"
        )
    lines.extend(
        [
            "",
            "## Review Dimensions",
            "",
            "每条分别评估：发音、重音、停顿、确定性等级、播音腔风险、儿童腔风险、连续听两分钟的适配度。",
            "",
            "冻结 `Abu Voice ID / Prompt / Lexicon / Voice Version` 前，所有项目必须完成人工记录。",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
