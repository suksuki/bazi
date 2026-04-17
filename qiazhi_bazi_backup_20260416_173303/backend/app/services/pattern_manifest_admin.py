"""Admin：格局法典 JSON 读写、时间戳备份与从备份回滚。"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.logic.patterns.engine import get_pattern_manifest_path


def read_pattern_manifest_from_disk() -> Dict[str, Any]:
    """经 ``load_pattern_manifest``（含签名校验容错）；失败时抛 HTTP 503 JSON。"""
    from app.logic.patterns.engine import load_pattern_manifest

    path = get_pattern_manifest_path()
    if not path.is_file():
        raise HTTPException(status_code=503, detail={"status": "SIGNATURE_ERROR", "detail": "manifest_file_missing", "path": str(path)})
    data = load_pattern_manifest(None)
    if isinstance(data, dict) and data.get("status") == "SIGNATURE_ERROR":
        raise HTTPException(status_code=503, detail=data)
    return data


def _stable_json_bytes(data: Dict[str, Any]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def manifest_sha256(data: Dict[str, Any]) -> str:
    return hashlib.sha256(_stable_json_bytes(data)).hexdigest()


def validate_manifest_minimal(data: Any) -> None:
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="manifest_must_be_object")
    if not any(k in data for k in ("STANDARD_OCTAD", "SPECIAL_PATTERNS", "ENGINE", "AXIS_REGISTRY")):
        raise HTTPException(status_code=400, detail="manifest_missing_core_sections")


_BACKUP_NAME_RE = re.compile(r"^pattern_manifest\.\d{8}_\d{6}\.json\.bak$")


def list_timestamped_manifest_backups(limit: int = 80) -> List[Dict[str, Any]]:
    """按 mtime 新→旧列出 `pattern_manifest.YYYYMMDD_HHMMSS.json.bak`。"""
    path = get_pattern_manifest_path()
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
        out.append(
            {
                "filename": p.name,
                "path": str(p),
                "size": int(st.st_size),
                "mtime_ns": int(st.st_mtime_ns),
            }
        )
    return out


def _timestamp_backup_name() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"pattern_manifest.{stamp}.json.bak"


def write_pattern_manifest_with_backup(data: Dict[str, Any]) -> Dict[str, Any]:
    """写入磁盘；若已有法典文件则先复制为带 UTC 时间戳的 `.json.bak`。"""
    validate_manifest_minimal(data)
    path = get_pattern_manifest_path()
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
    return {
        "path": str(path),
        "backup_path": str(backup_path) if backup_path is not None else None,
        "sha256": manifest_sha256(data),
    }


def restore_latest_manifest_backup() -> Dict[str, Any]:
    """将最新时间戳备份写回主法典（写回前再为当前主文件打一条时间戳备份）。"""
    backups = list_timestamped_manifest_backups(limit=200)
    if not backups:
        raise HTTPException(status_code=404, detail="no_timestamped_manifest_backups")
    src = Path(str(backups[0]["path"]))
    if not src.is_file():
        raise HTTPException(status_code=404, detail="backup_file_missing")
    path = get_pattern_manifest_path()
    pre_backup: Optional[Path] = None
    if path.is_file():
        pre_backup = path.parent / _timestamp_backup_name()
        shutil.copy2(path, pre_backup)
    shutil.copy2(src, path)
    data = read_pattern_manifest_from_disk()
    return {
        "ok": True,
        "restored_from": str(src),
        "pre_restore_backup": str(pre_backup) if pre_backup else None,
        "sha256": manifest_sha256(data),
    }


def preview_evaluate_rows(
    physics_tensor: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    from app.logic.patterns.engine import UniversalPatternEngine

    return UniversalPatternEngine().evaluate(physics_tensor, metadata or {})
