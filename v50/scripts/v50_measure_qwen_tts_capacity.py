from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SYNTHETIC_PROFILES = {
    "short_10s": "先看整盘重心。这张命盘更擅长把复杂经验整理成可以持续输出的方法。",
    "standard_30s": (
        "先看整盘重心。这张命盘的优势不只在拥有想法，而在于能否把经验转化为持续输出。"
        "主路径已经出现，但它成立仍依赖稳定反馈与现实承接。如果环境长期封闭，这条路径就会减弱。"
    ),
    "long_60s": (
        "先看整盘重心。这张命盘反复面对的，并不是能力有没有，而是能力怎样被现实承接。"
        "当输出、反馈和资源形成连续路径时，原有压力可以转化为行动；当其中一环中断，思考就容易停留在内部。"
        "因此当前判断不是让你盲目推进，而是先确认承接条件，再决定扩大投入。"
        "这里仍保留另一种解释：如果现实中长期没有稳定输出，主路径的优先级需要下降。"
    ),
    "mingli_terms": (
        "八字的年柱、月柱、日柱和时柱共同构成原局。这里要区分月令、藏干、十神、体用、调候与制化，"
        "也要区分原局事实、大运激活和流年候选。食伤制杀、印星承接与通关路径都只能在各自条件成立时使用。"
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure Qwen TTS capacity with synthetic Mingli text.")
    parser.add_argument("--base-url", default=os.getenv("V50_TTS_BASE_URL", "http://127.0.0.1:17860"))
    parser.add_argument("--speaker", default=os.getenv("V50_ABU_TTS_SPEAKER", "Eric"))
    parser.add_argument(
        "--instruction",
        default=os.getenv(
            "V50_ABU_TTS_INSTRUCT",
            "声音亲切沉稳，像一位可靠的年轻命理师；自然停顿，不要播音腔。",
        ),
    )
    parser.add_argument("--api-key", default=os.getenv("V50_TTS_API_KEY", ""))
    parser.add_argument("--concurrency", default="1,2,4,8")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--output-dir", default="reports/qwen-tts-capacity-v2")
    args = parser.parse_args()

    concurrencies = sorted({max(1, int(item)) for item in args.concurrency.split(",") if item.strip()})
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    for concurrency in concurrencies:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(
                    synthesize,
                    base_url=args.base_url,
                    speaker=args.speaker,
                    instruction=args.instruction,
                    api_key=args.api_key,
                    timeout=args.timeout,
                    profile=profile,
                    text=text,
                    concurrency=concurrency,
                ): profile
                for profile, text in SYNTHETIC_PROFILES.items()
            }
            for future in as_completed(futures):
                rows.append(future.result())

    report = build_report(
        rows=rows,
        base_url=args.base_url,
        speaker=args.speaker,
        started=started,
        finished=datetime.now(timezone.utc),
    )
    (output_dir / "qwen_tts_capacity_v2.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "QWEN_TTS_CAPACITY_V2.md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0 if report["summary"]["error_count"] == 0 else 1


def synthesize(
    *,
    base_url: str,
    speaker: str,
    instruction: str,
    api_key: str,
    timeout: float,
    profile: str,
    text: str,
    concurrency: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    payload = json.dumps(
        {"text": text, "speaker": speaker, "instruct": instruction, "language": "Chinese"},
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/tts",
        data=payload,
        headers=headers,
        method="POST",
    )
    row: dict[str, Any] = {
        "profile": profile,
        "concurrency": concurrency,
        "text_length": len(text),
        "status": "failed",
    }
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            headers_seconds = time.perf_counter() - started
            first = response.read(64 * 1024)
            first_packet_seconds = time.perf_counter() - started
            wav_bytes = first + response.read()
            server_generation = response.headers.get("X-Gen-Seconds")
        total_seconds = time.perf_counter() - started
        duration_seconds, sample_rate = wav_metadata(wav_bytes)
        server_generation_seconds = float(server_generation) if server_generation else None
        opus_size = opus_size_bytes(wav_bytes)
        row.update(
            {
                "status": "passed",
                "headers_seconds": round(headers_seconds, 4),
                "first_packet_seconds": round(first_packet_seconds, 4),
                "total_seconds": round(total_seconds, 4),
                "server_generation_seconds": server_generation_seconds,
                "queue_and_transport_estimate_seconds": (
                    round(max(0.0, headers_seconds - server_generation_seconds), 4)
                    if server_generation_seconds is not None
                    else None
                ),
                "audio_duration_seconds": round(duration_seconds, 4),
                "sample_rate": sample_rate,
                "rtf": round(total_seconds / duration_seconds, 4),
                "size_bytes": len(wav_bytes),
                "bytes_per_audio_minute": round(len(wav_bytes) / duration_seconds * 60),
                "opus_size_bytes": opus_size,
                "opus_bytes_per_audio_minute": (
                    round(opus_size / duration_seconds * 60) if opus_size else None
                ),
                "opus_compression_ratio": round(opus_size / len(wav_bytes), 4) if opus_size else None,
            }
        )
    except (urllib.error.URLError, TimeoutError, wave.Error, EOFError, ValueError) as exc:
        row["error"] = f"{type(exc).__name__}:{exc}"
        row["total_seconds"] = round(time.perf_counter() - started, 4)
    return row


def wav_metadata(wav_bytes: bytes) -> tuple[float, int]:
    if not wav_bytes.startswith(b"RIFF") or b"WAVE" not in wav_bytes[:16]:
        raise ValueError("response_is_not_wav")
    with wave.open(io.BytesIO(wav_bytes), "rb") as reader:
        sample_rate = reader.getframerate()
        duration = reader.getnframes() / sample_rate
    if duration <= 0:
        raise ValueError("empty_wav")
    return duration, sample_rate


def build_report(
    *,
    rows: list[dict[str, Any]],
    base_url: str,
    speaker: str,
    started: datetime,
    finished: datetime,
) -> dict[str, Any]:
    passed = [row for row in rows if row["status"] == "passed"]
    rtfs = [row["rtf"] for row in passed]
    first_packets = [row["first_packet_seconds"] for row in passed]
    by_concurrency: dict[str, Any] = {}
    for concurrency in sorted({row["concurrency"] for row in rows}):
        lane = [row for row in rows if row["concurrency"] == concurrency]
        lane_passed = [row for row in lane if row["status"] == "passed"]
        by_concurrency[str(concurrency)] = {
            "requests": len(lane),
            "passed": len(lane_passed),
            "failure_rate": round((len(lane) - len(lane_passed)) / max(1, len(lane)), 4),
            "rtf_p50": percentile([row["rtf"] for row in lane_passed], 0.50),
            "rtf_p95": percentile([row["rtf"] for row in lane_passed], 0.95),
            "first_packet_p95_seconds": percentile(
                [row["first_packet_seconds"] for row in lane_passed], 0.95
            ),
            "complete_p95_seconds": percentile(
                [row["total_seconds"] for row in lane_passed], 0.95
            ),
            "queue_and_transport_p95_seconds": percentile(
                [
                    row["queue_and_transport_estimate_seconds"]
                    for row in lane_passed
                    if row.get("queue_and_transport_estimate_seconds") is not None
                ],
                0.95,
            ),
        }
    totals = [row["total_seconds"] for row in passed]
    queue_estimates = [
        row["queue_and_transport_estimate_seconds"]
        for row in passed
        if row.get("queue_and_transport_estimate_seconds") is not None
    ]
    opus_minutes = [
        row["opus_bytes_per_audio_minute"]
        for row in passed
        if row.get("opus_bytes_per_audio_minute") is not None
    ]
    return {
        "version": "deepbazi.qwen_tts_capacity_report.v2",
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "base_url": base_url,
        "speaker": speaker,
        "input_data": "synthetic_non_user_mingli_text",
        "summary": {
            "request_count": len(rows),
            "passed_count": len(passed),
            "error_count": len(rows) - len(passed),
            "rtf_p50": percentile(rtfs, 0.50),
            "rtf_p95": percentile(rtfs, 0.95),
            "first_packet_p50_seconds": percentile(first_packets, 0.50),
            "first_packet_p95_seconds": percentile(first_packets, 0.95),
            "complete_p50_seconds": percentile(totals, 0.50),
            "complete_p95_seconds": percentile(totals, 0.95),
            "queue_and_transport_p50_seconds": percentile(queue_estimates, 0.50),
            "queue_and_transport_p95_seconds": percentile(queue_estimates, 0.95),
            "failure_rate": round((len(rows) - len(passed)) / max(1, len(rows)), 4),
            "opus_bytes_per_audio_minute_p50": percentile(opus_minutes, 0.50),
        },
        "by_concurrency": by_concurrency,
        "observations": {
            "gpu_memory": "not_observable_through_current_http_contract",
            "voice_consistency": "requires_manual_listening_review",
            "mingli_pronunciation": "requires_manual_listening_review",
            "cache_hit_rate": "measured_at_narrated_workspace_not_raw_tts_endpoint",
            "queue_wait": "estimate_only_without_server_queue_header",
        },
        "rows": sorted(rows, key=lambda item: (item["concurrency"], item["profile"])),
    }


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 4)
    index = (len(ordered) - 1) * quantile
    lower = int(index)
    upper = min(len(ordered) - 1, lower + 1)
    value = ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)
    return round(value, 4)


def opus_size_bytes(wav_bytes: bytes) -> int | None:
    binary = shutil.which(os.getenv("V50_FFMPEG_BINARY", "ffmpeg"))
    if not binary:
        return None
    completed = subprocess.run(
        [
            binary,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "wav",
            "-i",
            "pipe:0",
            "-map_metadata",
            "-1",
            "-c:a",
            "libopus",
            "-application",
            "voip",
            "-b:a",
            "48k",
            "-vbr",
            "on",
            "-f",
            "ogg",
            "pipe:1",
        ],
        input=wav_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return len(completed.stdout) if completed.returncode == 0 and completed.stdout.startswith(b"OggS") else None


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Qwen TTS Capacity v2",
        "",
        f"- Endpoint: `{report['base_url']}`",
        f"- Voice: `{report['speaker']}`",
        f"- Requests: `{summary['request_count']}`",
        f"- Passed / errors: `{summary['passed_count']} / {summary['error_count']}`",
        f"- RTF p50 / p95: `{summary['rtf_p50']} / {summary['rtf_p95']}`",
        f"- First packet p50 / p95: `{summary['first_packet_p50_seconds']}s / {summary['first_packet_p95_seconds']}s`",
        f"- Complete p50 / p95: `{summary['complete_p50_seconds']}s / {summary['complete_p95_seconds']}s`",
        f"- Queue + transport estimate p50 / p95: `{summary['queue_and_transport_p50_seconds']}s / {summary['queue_and_transport_p95_seconds']}s`",
        f"- Opus bytes per audio minute p50: `{summary['opus_bytes_per_audio_minute_p50']}`",
        "",
        "## Concurrency",
        "",
        "| 并发 | 通过 | 失败率 | RTF p50 | RTF p95 | 首包 p95 | 完成 p95 | 排队估算 p95 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for concurrency, lane in report["by_concurrency"].items():
        lines.append(
            f"| {concurrency} | {lane['passed']}/{lane['requests']} | {lane['failure_rate']} | {lane['rtf_p50']} | {lane['rtf_p95']} | {lane['first_packet_p95_seconds']}s | {lane['complete_p95_seconds']}s | {lane['queue_and_transport_p95_seconds']}s |"
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- 本次只使用合成命理文本，不包含用户命盘或私人内容。",
            "- HTTP 服务当前整段返回 WAV；`first_packet` 主要反映服务生成后开始响应的时间，不等同于真正流式 TTS 首帧。",
            "- GPU 显存、音色一致性与干支术语发音仍需服务器观测和人工听审。",
            "- 缓存命中率属于 Narrated Workspace 指标；直接 TTS 压测不会伪造缓存命中。",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
