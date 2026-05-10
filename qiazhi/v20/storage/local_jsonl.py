from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.ops.config import load_runtime_config_from_env


@dataclass(frozen=True)
class LocalJsonlStore:
    runtime_dir: Path
    max_ledger_bytes: int = 10 * 1024 * 1024

    def append_record(self, ledger_name: str, payload: dict[str, object]) -> dict[str, object]:
        if "/" in ledger_name or ledger_name.startswith("."):
            raise ValueError(f"Invalid ledger name: {ledger_name}")
        directory = self.runtime_dir / "ledger"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{ledger_name}.jsonl"
        record = _record_payload(ledger_name, payload)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        rotated_path = _rotate_if_needed(path, incoming_bytes=len(line.encode("utf-8")), max_bytes=self.max_ledger_bytes)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
        return {
            "version": "v20.local_jsonl_append_result.v1",
            "ledger_name": ledger_name,
            "record_id": record["record_id"],
            "relative_path": str(path.relative_to(self.runtime_dir)),
            "rotated": rotated_path is not None,
            "rotated_relative_path": str(rotated_path.relative_to(self.runtime_dir)) if rotated_path else "",
            "max_ledger_bytes": self.max_ledger_bytes,
            "runtime_mutation": True,
            "guardrails": [
                "LOCAL_JSONL_APPEND_ONLY",
                "LOCAL_JSONL_SIZE_BOUNDED",
                "RUNTIME_DIR_LOCAL_TO_PROFILE",
                "NO_RAW_PRIVATE_FEEDBACK",
            ],
        }

    def status(self) -> dict[str, object]:
        ledger_dir = self.runtime_dir / "ledger"
        ledgers = []
        if ledger_dir.exists():
            for path in sorted(ledger_dir.glob("*.jsonl")):
                ledgers.append({
                    "ledger_name": path.stem,
                    "relative_path": str(path.relative_to(self.runtime_dir)),
                    "bytes": path.stat().st_size,
                })
        return {
            "version": "v20.local_jsonl_store_status.v1",
            "runtime_dir": str(self.runtime_dir),
            "max_ledger_bytes": self.max_ledger_bytes,
            "ledger_count": len(ledgers),
            "ledgers": ledgers,
            "runtime_mutation": False,
            "guardrails": ["LOCAL_STORE_STATUS_ONLY", "NO_FILE_CONTENT_RENDERED", "LOCAL_JSONL_SIZE_BOUNDED"],
        }


def local_jsonl_store_from_env() -> LocalJsonlStore:
    config = load_runtime_config_from_env()
    profile = config.profile(config.active_profile)
    runtime_dir = Path(profile.runtime_dir)
    if not runtime_dir.is_absolute():
        runtime_dir = Path(__file__).resolve().parents[2] / runtime_dir
    return LocalJsonlStore(runtime_dir=runtime_dir, max_ledger_bytes=_max_ledger_bytes_from_env())


def _record_payload(ledger_name: str, payload: dict[str, object]) -> dict[str, object]:
    created_at = datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return {
        "version": "v20.local_jsonl_record.v1",
        "record_id": f"{ledger_name}.{digest}",
        "ledger_name": ledger_name,
        "created_at": created_at,
        "payload": payload,
        "guardrails": ["APPEND_ONLY_RECORD", "PAYLOAD_MUST_BE_ALREADY_REDACTED"],
    }


def _rotate_if_needed(path: Path, *, incoming_bytes: int, max_bytes: int) -> Path | None:
    if max_bytes <= 0 or not path.exists():
        return None
    if path.stat().st_size + incoming_bytes <= max_bytes:
        return None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rotated = path.with_name(f"{path.stem}.{timestamp}.jsonl")
    suffix = 1
    while rotated.exists():
        rotated = path.with_name(f"{path.stem}.{timestamp}.{suffix}.jsonl")
        suffix += 1
    path.rename(rotated)
    return rotated


def _max_ledger_bytes_from_env() -> int:
    try:
        return max(1024, int(os.getenv("V20_LOCAL_JSONL_MAX_BYTES", str(10 * 1024 * 1024))))
    except ValueError:
        return 10 * 1024 * 1024
