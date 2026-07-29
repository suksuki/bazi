from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

PROJECT_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_PATH = PROJECT_ROOT / "assets" / "registry.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_verified_assets() -> list[dict[str, object]]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if registry["policy"]["runtime_reads_v50_paths"]:
        raise RuntimeError("V60 asset registry cannot read V50 paths at runtime")

    verified: list[dict[str, object]] = []
    for asset in registry["assets"]:
        runtime_path = PROJECT_ROOT / str(asset["runtime_path"])
        if not runtime_path.is_file():
            raise FileNotFoundError(runtime_path)
        actual_hash = sha256_file(runtime_path)
        if actual_hash != asset["sha256"]:
            raise RuntimeError(
                f"Hash mismatch for {asset['asset_ref']}: "
                f"expected {asset['sha256']}, got {actual_hash}"
            )
        verified.append(asset)
    return verified


def sync_assets(engine: Engine) -> int:
    assets = load_verified_assets()
    statement = text(
        """
        INSERT INTO media.asset_versions (
            asset_ref,
            asset_version,
            runtime_path,
            sha256,
            media_type,
            source_manifest_ref,
            source_status,
            v60_role
        )
        VALUES (
            :asset_ref,
            :asset_version,
            :runtime_path,
            :sha256,
            :media_type,
            :source_manifest_ref,
            :source_status,
            :v60_role
        )
        ON CONFLICT (asset_ref, asset_version) DO UPDATE SET
            runtime_path = EXCLUDED.runtime_path,
            sha256 = EXCLUDED.sha256,
            media_type = EXCLUDED.media_type,
            source_manifest_ref = EXCLUDED.source_manifest_ref,
            source_status = EXCLUDED.source_status,
            v60_role = EXCLUDED.v60_role
        """
    )
    with engine.begin() as connection:
        for asset in assets:
            connection.execute(statement, asset)
    return len(assets)
