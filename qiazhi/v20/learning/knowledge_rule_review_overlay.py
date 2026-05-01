from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.decision.knowledge_bridge import build_knowledge_rule_review_overlay
from v20.storage.local_jsonl import local_jsonl_store_from_env

ProgressCallback = Callable[[str], None]


def write_knowledge_rule_review_overlay_artifact(
    *,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    _emit(progress, "building knowledge rule review overlay")
    report = build_knowledge_rule_review_overlay()
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "knowledge_rule_review_overlay"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"knowledge_rule_review_overlay_{stamp}.json"
    payload = report | {
        "artifact_id": f"v20.knowledge_rule_review_overlay.{stamp}",
        "artifact_type": "knowledge_rule_review_overlay",
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.knowledge_rule_review_overlay_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "artifact_id": payload["artifact_id"],
        "report_status": report["status"],
        "rule_count": report["rule_count"],
        "shadow_weight_candidate_count": report["shadow_weight_candidate_count"],
        "runtime_promotion_candidate_count": report["runtime_promotion_candidate_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_RULE_PROMOTION",
            "RUNTIME_MAY_CONSUME_ONLY_LOCKED_ARTIFACT_VERSION",
        ],
    }


def read_knowledge_rule_review_overlay_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "knowledge_rule_review_overlay") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.knowledge_rule_review_overlay_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {
        "latest_path": str(latest_path),
        "runtime_mutation": False,
    }


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
