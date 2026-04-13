"""Admin：冲突法典 ``conflict_manifest.json`` 读写、备份与 SHA256 指纹。"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.plugins.classical.conflict_auditor_v1 import get_conflict_manifest_path


def read_conflict_manifest_from_disk() -> Dict[str, Any]:
    path = get_conflict_manifest_path()
    if not path.is_file():
        raise HTTPException(
            status_code=503,
            detail={"status": "MANIFEST_MISSING", "detail": "conflict_manifest_file_missing", "path": str(path)},
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail=f"conflict_manifest_read_error:{exc}") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=503, detail="conflict_manifest_must_be_object")
    return data


def _stable_json_bytes(data: Dict[str, Any]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def manifest_sha256(data: Dict[str, Any]) -> str:
    return hashlib.sha256(_stable_json_bytes(data)).hexdigest()


def validate_conflict_manifest_minimal(data: Any) -> None:
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="manifest_must_be_object")
    if not isinstance(data.get("ENGINE"), dict):
        raise HTTPException(status_code=400, detail="conflict_manifest_missing_ENGINE")
    kinds = data.get("KIND_LINEAR")
    if not isinstance(kinds, dict) or not kinds:
        raise HTTPException(status_code=400, detail="conflict_manifest_KIND_LINEAR_required")


_BACKUP_NAME_RE = re.compile(r"^conflict_manifest\.\d{8}_\d{6}\.json\.bak$")


def list_timestamped_manifest_backups(limit: int = 80) -> List[Dict[str, Any]]:
    path = get_conflict_manifest_path()
    parent = path.parent
    if not parent.is_dir():
        return []
    rows: List[tuple[float, Path]] = []
    for p in parent.iterdir():
        if not p.is_file():
            continue
        if not _BACKUP_NAME_RE.match(p.name):
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        rows.append((float(st.st_mtime_ns), p))
    rows.sort(key=lambda x: -x[0])
    out: List[Dict[str, Any]] = []
    for _ns, p in rows[: max(1, min(200, int(limit)))]:
        try:
            st = p.stat()
        except OSError:
            continue
        out.append({"filename": p.name, "path": str(p), "size": int(st.st_size), "mtime_ns": int(st.st_mtime_ns)})
    return out


def _timestamp_backup_name() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"conflict_manifest.{stamp}.json.bak"


def _write_sidecar_sha256(path: Path, canonical_hex: str) -> None:
    path.with_suffix(".sha256").write_text(canonical_hex.lower() + "\n", encoding="utf-8")


def write_conflict_manifest_with_backup(data: Dict[str, Any]) -> Dict[str, Any]:
    validate_conflict_manifest_minimal(data)
    path = get_conflict_manifest_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"manifest_dir_error:{exc}") from exc
    backup_path: Optional[Path] = None
    if path.is_file():
        backup_path = path.parent / _timestamp_backup_name()
        shutil.copy2(path, backup_path)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"manifest_write_error:{exc}") from exc
    sha = manifest_sha256(data)
    try:
        _write_sidecar_sha256(path, sha)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"sha256_sidecar_write_error:{exc}") from exc
    return {"path": str(path), "backup_path": str(backup_path) if backup_path else None, "sha256": sha}


def restore_latest_manifest_backup() -> Dict[str, Any]:
    backups = list_timestamped_manifest_backups(limit=200)
    if not backups:
        raise HTTPException(status_code=404, detail="no_timestamped_conflict_manifest_backups")
    src = Path(str(backups[0]["path"]))
    if not src.is_file():
        raise HTTPException(status_code=404, detail="backup_file_missing")
    path = get_conflict_manifest_path()
    pre_backup: Optional[Path] = None
    if path.is_file():
        pre_backup = path.parent / _timestamp_backup_name()
        shutil.copy2(path, pre_backup)
    shutil.copy2(src, path)
    data = read_conflict_manifest_from_disk()
    sha = manifest_sha256(data)
    _write_sidecar_sha256(path, sha)
    return {
        "ok": True,
        "restored_from": str(src),
        "pre_restore_backup": str(pre_backup) if pre_backup else None,
        "sha256": sha,
    }
