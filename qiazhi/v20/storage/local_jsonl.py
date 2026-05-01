from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.ops.config import load_runtime_config_from_env


@dataclass(frozen=True)
class LocalJsonlStore:
    runtime_dir: Path

    def append_record(self, ledger_name: str, payload: dict[str, object]) -> dict[str, object]:
        if "/" in ledger_name or ledger_name.startswith("."):
            raise ValueError(f"Invalid ledger name: {ledger_name}")
        directory = self.runtime_dir / "ledger"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{ledger_name}.jsonl"
        record = _record_payload(ledger_name, payload)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return {
            "version": "v20.local_jsonl_append_result.v1",
            "ledger_name": ledger_name,
            "record_id": record["record_id"],
            "relative_path": str(path.relative_to(self.runtime_dir)),
            "runtime_mutation": True,
            "guardrails": [
                "LOCAL_JSONL_APPEND_ONLY",
                "RUNTIME_DIR_LOCAL_TO_PROFILE",
                "NO_RAW_PRIVATE_FEEDBACK",
            ],
        }

    def status(self) -> dict[str, object]:
        ledger_dir = self.runtime_dir / "ledger"
        ledgers = []
        if ledger_dir.exists():
            for path in sorted(ledger_dir.glob("*.jsonl")):
                ledgers.append({"ledger_name": path.stem, "relative_path": str(path.relative_to(self.runtime_dir)), "bytes": path.stat().st_size})
        return {
            "version": "v20.local_jsonl_store_status.v1",
            "runtime_dir": str(self.runtime_dir),
            "ledger_count": len(ledgers),
            "ledgers": ledgers,
            "runtime_mutation": False,
            "guardrails": ["LOCAL_STORE_STATUS_ONLY", "NO_FILE_CONTENT_RENDERED"],
        }


def local_jsonl_store_from_env() -> LocalJsonlStore:
    config = load_runtime_config_from_env()
    profile = config.profile(config.active_profile)
    runtime_dir = Path(profile.runtime_dir)
    if not runtime_dir.is_absolute():
        runtime_dir = Path(__file__).resolve().parents[2] / runtime_dir
    return LocalJsonlStore(runtime_dir=runtime_dir)


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
