from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.config import V30Settings, load_settings
from v30.validation.production_replay_intake import (
    PRODUCTION_REPLAY_INTAKE_VERSION,
    summarize_production_replay_intake,
)


PRODUCTION_REPLAY_STORE_VERSION = "v30.production_replay_store.v1"
PRODUCTION_REPLAY_SEARCH_VERSION = "v30.production_replay_search.v1"

_FORBIDDEN_STORE_KEYS = {
    "answer",
    "birth_date",
    "birth_time",
    "date",
    "datetime",
    "email",
    "free_text",
    "message",
    "name",
    "phone",
    "raw_payload",
    "text",
    "user_answer",
    "user_text",
}


class ProductionReplayIntakeStore:
    def __init__(self, settings: V30Settings | None = None, root: Path | None = None):
        self._settings = settings or load_settings()
        self._root = root or self._settings.runtime_dir / "validation" / "production_replay_intake"
        self._rows_dir = self._root / "rows"
        self._index_path = self._root / "index.json"

    def upsert_batch(self, batch: dict[str, Any]) -> dict[str, Any]:
        rows = [
            self._sanitize_row(row)
            for row in batch.get("rows", [])
            if isinstance(row, dict) and row.get("version") == PRODUCTION_REPLAY_INTAKE_VERSION
        ]
        rows = [row for row in rows if row]
        self._rows_dir.mkdir(parents=True, exist_ok=True)
        existing = self._load_index_rows()
        by_id = {str(row.get("intake_id") or ""): row for row in existing if row.get("intake_id")}
        for row in rows:
            row["stored_at"] = datetime.now(timezone.utc).isoformat()
            by_id[str(row["intake_id"])] = row
            row_path = self._rows_dir / f"{_safe_id(str(row['intake_id']))}.json"
            row_path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
        all_rows = sorted(by_id.values(), key=lambda row: str(row.get("intake_id") or ""))
        payload = {
            "version": PRODUCTION_REPLAY_STORE_VERSION,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "row_count": len(all_rows),
            "rows": all_rows,
            "summary": summarize_production_replay_intake(all_rows),
            "privacy_boundary": "production_replay_store_persists_metadata_only_without_private_content_or_chart_fact_import",
        }
        self._root.mkdir(parents=True, exist_ok=True)
        self._index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "version": "v30.production_replay_store_write.v1",
            "stored_count": len(rows),
            "total_count": len(all_rows),
            "index_uri": str(self._index_path),
            "summary": payload["summary"],
            "boundary": "production_replay_store_write_does_not_promote_policy_or_import_chart_facts",
        }

    def search(
        self,
        *,
        selection_status: str = "",
        calendar_type: str = "",
        boundary_tag: str = "",
        module_ready: str = "",
        source_artifact_family: str = "",
        limit: int = 50,
    ) -> dict[str, Any]:
        rows = self._load_index_rows()
        filtered = [
            row for row in rows
            if _matches(row, selection_status=selection_status, calendar_type=calendar_type, boundary_tag=boundary_tag, module_ready=module_ready, source_artifact_family=source_artifact_family)
        ]
        clean_limit = max(1, min(int(limit), 200))
        filtered = filtered[:clean_limit]
        return {
            "version": PRODUCTION_REPLAY_SEARCH_VERSION,
            "backend": "json_fallback",
            "searchable": self._index_path.exists(),
            "count": len(filtered),
            "filters": {
                "selection_status": selection_status,
                "calendar_type": calendar_type,
                "boundary_tag": boundary_tag,
                "module_ready": module_ready,
                "source_artifact_family": source_artifact_family,
                "limit": clean_limit,
            },
            "summary": summarize_production_replay_intake(filtered),
            "rows": filtered,
            "index_uri": str(self._index_path),
            "boundary": "production_replay_search_returns_metadata_only_rows_not_chart_facts",
        }

    def _load_index_rows(self) -> list[dict[str, Any]]:
        if not self._index_path.exists():
            return []
        try:
            payload = json.loads(self._index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        rows = payload.get("rows", []) if isinstance(payload, dict) else []
        return [row for row in rows if isinstance(row, dict)]

    def _sanitize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        if _contains_forbidden_keys(row):
            return {}
        allowed = {
            "version",
            "intake_id",
            "case_id",
            "source",
            "source_artifact",
            "chart_status",
            "calendar_type",
            "boundary_tags",
            "readiness_tags",
            "module_contract_tags",
            "module_readiness",
            "selection_status",
            "calibration_candidate",
            "hold_reasons",
            "privacy_guard",
            "fact_import_policy",
            "boundary",
        }
        clean = {key: value for key, value in row.items() if key in allowed}
        if clean.get("version") != PRODUCTION_REPLAY_INTAKE_VERSION:
            return {}
        clean["storage_guard"] = {
            "metadata_only": True,
            "no_private_user_content": True,
            "no_chart_fact_import": True,
            "forbidden_key_scan_passed": not _contains_forbidden_keys(clean),
        }
        return clean


def build_production_replay_store(settings: V30Settings | None = None) -> ProductionReplayIntakeStore:
    return ProductionReplayIntakeStore(settings=settings)


def _matches(
    row: dict[str, Any],
    *,
    selection_status: str,
    calendar_type: str,
    boundary_tag: str,
    module_ready: str,
    source_artifact_family: str,
) -> bool:
    if selection_status and row.get("selection_status") != selection_status:
        return False
    if calendar_type and row.get("calendar_type") != calendar_type:
        return False
    if boundary_tag:
        tags = row.get("boundary_tags", [])
        if not isinstance(tags, list) or boundary_tag not in tags:
            return False
    if module_ready:
        readiness = row.get("module_readiness", {})
        if not isinstance(readiness, dict) or readiness.get(module_ready) is not True:
            return False
    if source_artifact_family:
        source = row.get("source_artifact", {})
        if not isinstance(source, dict) or source.get("family") != source_artifact_family:
            return False
    return True


def _contains_forbidden_keys(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key) in _FORBIDDEN_STORE_KEYS:
                return True
            if _contains_forbidden_keys(nested):
                return True
    if isinstance(value, list):
        return any(_contains_forbidden_keys(row) for row in value)
    return False


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value)[:180]
