from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from abu_v60.system_manifest import (
    DECISION_POLICY_VERSION,
    DREAM_GAME_ENGINE_VERSION,
    FOUNDATION_VERSION,
    MINGLI_ENGINE_VERSION,
    PRODUCT_ID,
    STORY_ENGINE_VERSION,
    WORLD_ENGINE_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = REPO_ROOT / ".runtime"
EXPECTED_ENGINES = {
    "decision": DECISION_POLICY_VERSION,
    "game": DREAM_GAME_ENGINE_VERSION,
    "world": WORLD_ENGINE_VERSION,
    "mingli": MINGLI_ENGINE_VERSION,
    "story": STORY_ENGINE_VERSION,
}
EXPECTED_FOUNDATION_VERSION = FOUNDATION_VERSION
LOCAL_REASONER_DEFAULTS = {
    "V60_REASONER_ENABLED": "true",
    "V60_REASONER_PROVIDER": "ollama-generate",
    "V60_REASONER_MODEL": "gemma4:latest",
    "V60_REASONER_PROFILE_REF": "v60.model-serving.gemma4-structured-decision.001",
    "V60_REASONER_BASE_URL": "http://dblife.com:11888",
    "V60_REASONER_TIMEOUT_SECONDS": "180",
    "V60_REASONER_THINK": "false",
    "V60_REASONER_TEMPERATURE": "0",
    "V60_REASONER_TOP_P": "0.95",
    "V60_REASONER_TOP_K": "64",
    "V60_REASONER_NUM_CTX": "32768",
    "V60_REASONER_NUM_PREDICT": "1200",
    "V60_REASONER_KEEP_ALIVE": "30m",
}
LOCAL_MINGLI_AGENT_DEFAULTS = {
    "V60_MINGLI_AGENT_ENABLED": "true",
    "V60_MINGLI_AGENT_PROVIDER": "ollama-generate",
    "V60_MINGLI_AGENT_MODEL": "gemma4:latest",
    "V60_MINGLI_AGENT_MODEL_DIGEST": (
        "c6eb396dbd5992bbe3f5cdb947e8bbc0ee413d7c17e2beaae69f5d569cf982eb"
    ),
    "V60_MINGLI_AGENT_PROFILE_REF": (
        "v60.model-serving.gemma4-mingli-agent.002"
    ),
    "V60_MINGLI_AGENT_BASE_URL": "http://dblife.com:11888",
    "V60_MINGLI_AGENT_TIMEOUT_SECONDS": "420",
    "V60_MINGLI_AGENT_THINK": "false",
    "V60_MINGLI_AGENT_TEMPERATURE": "0",
    "V60_MINGLI_AGENT_TOP_P": "0.95",
    "V60_MINGLI_AGENT_TOP_K": "64",
    "V60_MINGLI_AGENT_NUM_CTX": "32768",
    "V60_MINGLI_AGENT_NUM_PREDICT": "5200",
    "V60_MINGLI_AGENT_KEEP_ALIVE": "30m",
}
LOCAL_TTS_DEFAULTS = {
    "V60_TTS_ENABLED": "true",
    "V60_TTS_URL": "https://dblife.com/abu-tts/tts",
    "V60_TTS_PROVIDER_PROFILE_REF": "v60.qwen3-tts-proxy.001",
    "V60_TTS_PROVIDER_DEPLOYMENT_REF": "dblife-public-proxy",
    "V60_TTS_MODEL": "Qwen3-TTS",
    "V60_TTS_ABU_VOICE": "Dylan",
    "V60_TTS_DUODUO_VOICE": "Vivian",
    "V60_TTS_TIMEOUT_SECONDS": "45",
}


class LocalRuntimeError(RuntimeError):
    pass


def _paths(port: int) -> tuple[Path, Path]:
    return (
        RUNTIME_DIR / f"abu-v60-{port}.pid.json",
        RUNTIME_DIR / f"abu-v60-{port}.log",
    )


def _read_json(url: str, *, timeout: float = 1.0) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (
        json.JSONDecodeError,
        OSError,
        urllib.error.HTTPError,
        urllib.error.URLError,
    ):
        return None


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(0.4)
        return client.connect_ex((host, port)) == 0


def _process_command(pid: int) -> str | None:
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        check=False,
        capture_output=True,
        text=True,
    )
    command = result.stdout.strip()
    return command or None


def _read_pid_record(port: int) -> dict[str, Any] | None:
    pid_path, _ = _paths(port)
    try:
        return json.loads(pid_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _owned_pid(port: int) -> int | None:
    record = _read_pid_record(port)
    if record is None:
        return None
    pid = int(record.get("pid", 0))
    command = _process_command(pid)
    expected_fragment = f"abu_v60.main:app --host {record['host']} --port {port}"
    if command is None or expected_fragment not in command:
        return None
    return pid


def _runtime_probe(host: str, port: int) -> dict[str, Any]:
    base_url = f"http://{host}:{port}"
    health = _read_json(f"{base_url}/api/v60/health")
    manifest = _read_json(f"{base_url}/api/v60/system/manifest")
    status = _read_json(f"{base_url}/api/v60/system/runtime-status")
    return {
        "base_url": base_url,
        "health": health,
        "manifest": manifest,
        "runtime_status": status,
    }


def _assert_ready(host: str, port: int) -> dict[str, Any]:
    probe = _runtime_probe(host, port)
    manifest = probe["manifest"]
    status = probe["runtime_status"]
    if manifest is None or manifest.get("product_id") != PRODUCT_ID:
        raise LocalRuntimeError("local_runtime_manifest_unavailable")
    actual_engines = manifest.get("engines", {})
    mismatches = {
        engine: {
            "actual": actual_engines.get(engine),
            "expected": expected_version,
        }
        for engine, expected_version in EXPECTED_ENGINES.items()
        if actual_engines.get(engine) != expected_version
    }
    if mismatches:
        raise LocalRuntimeError(
            "local_runtime_version_mismatch:"
            f"{json.dumps(mismatches, sort_keys=True)}"
        )
    if status is None or status.get("status") != "READY":
        raise LocalRuntimeError("local_runtime_integrity_not_ready")
    health = probe["health"]
    database = health.get("database", {}) if health is not None else {}
    if (
        health is None
        or health.get("status") != "ready"
        or database.get("foundation_version") != EXPECTED_FOUNDATION_VERSION
    ):
        raise LocalRuntimeError(
            "local_runtime_database_foundation_mismatch:"
            f"actual={database.get('foundation_version')},"
            f"expected={EXPECTED_FOUNDATION_VERSION}"
        )
    return probe


def start(host: str, port: int) -> dict[str, Any]:
    existing_pid = _owned_pid(port)
    if existing_pid is not None:
        return {
            "action": "already_running",
            "pid": existing_pid,
            **_assert_ready(host, port),
        }

    if _port_open(host, port):
        probe = _runtime_probe(host, port)
        manifest = probe["manifest"]
        if manifest and manifest.get("product_id") == PRODUCT_ID:
            actual_versions = manifest.get("engines", {})
            raise LocalRuntimeError(
                "unmanaged_v60_process_on_port:"
                f"actual={actual_versions},expected={EXPECTED_ENGINES}"
            )
        raise LocalRuntimeError("foreign_process_on_v60_port")

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    pid_path, log_path = _paths(port)
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "abu_v60.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    with log_path.open("ab", buffering=0) as log:
        runtime_environment = {
            **LOCAL_REASONER_DEFAULTS,
            **LOCAL_MINGLI_AGENT_DEFAULTS,
            **LOCAL_TTS_DEFAULTS,
            **os.environ,
        }
        process = subprocess.Popen(
            command,
            cwd=REPO_ROOT,
            env={**runtime_environment, "PYTHONUNBUFFERED": "1"},
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    pid_path.write_text(
        json.dumps(
            {
                "pid": process.pid,
                "host": host,
                "port": port,
                "repo_root": str(REPO_ROOT),
                "started_at_unix": int(time.time()),
                "expected_engines": EXPECTED_ENGINES,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    deadline = time.monotonic() + 20
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pid_path.unlink(missing_ok=True)
            raise LocalRuntimeError(
                f"local_runtime_exited_during_start:{process.returncode}"
            )
        try:
            return {
                "action": "started",
                "pid": process.pid,
                "log_path": str(log_path),
                **_assert_ready(host, port),
            }
        except LocalRuntimeError as exc:
            last_error = exc
            time.sleep(0.25)

    stop(host, port)
    raise LocalRuntimeError(f"local_runtime_start_timeout:{last_error}")


def stop(host: str, port: int) -> dict[str, Any]:
    pid_path, _ = _paths(port)
    pid = _owned_pid(port)
    if pid is None:
        if _port_open(host, port):
            raise LocalRuntimeError("refusing_to_stop_unmanaged_process")
        pid_path.unlink(missing_ok=True)
        return {"action": "already_stopped"}

    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and _process_command(pid) is not None:
        time.sleep(0.1)
    if _process_command(pid) is not None:
        os.kill(pid, signal.SIGKILL)
    pid_path.unlink(missing_ok=True)
    return {"action": "stopped", "pid": pid}


def status(host: str, port: int) -> dict[str, Any]:
    pid = _owned_pid(port)
    probe = _runtime_probe(host, port)
    return {
        "action": "status",
        "managed": pid is not None,
        "pid": pid,
        "port_open": _port_open(host, port),
        **probe,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the local Abu Knows V60 runtime.")
    parser.add_argument("action", choices=("start", "stop", "restart", "status", "check"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8060, type=int)
    args = parser.parse_args()

    try:
        if args.action == "start":
            result = start(args.host, args.port)
        elif args.action == "stop":
            result = stop(args.host, args.port)
        elif args.action == "restart":
            stop(args.host, args.port)
            result = start(args.host, args.port)
        elif args.action == "check":
            result = {"action": "check", **_assert_ready(args.host, args.port)}
        else:
            result = status(args.host, args.port)
    except LocalRuntimeError as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)}, indent=2))
        raise SystemExit(1) from exc

    print(json.dumps({"status": "OK", **result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
