"""V9.0 Admin：冲突法典 API。"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.api.v1.admin.conflict import router as conflict_admin_router


@pytest.fixture()
def admin_client() -> TestClient:
    app = FastAPI()
    app.include_router(conflict_admin_router, prefix="/api")
    return TestClient(app)


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    return {"X-Admin-Token": os.getenv("QIAZHI_ADMIN_TOKEN", "").strip() or "local-dev-qiazhi-admin"}


@pytest.fixture()
def tmp_conflict_manifest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    src = Path(__file__).resolve().parents[2] / "app" / "plugins" / "classical" / "conflict_manifest.json"
    dst = tmp_path / "conflict_manifest.json"
    shutil.copyfile(src, dst)
    monkeypatch.setenv("QIAZHI_CONFLICT_MANIFEST_PATH", str(dst))
    return dst


def test_admin_conflict_manifest_get_put(admin_client: TestClient, admin_headers: dict[str, str], tmp_conflict_manifest: Path) -> None:
    r0 = admin_client.get("/api/v1/admin/conflict/manifest", headers=admin_headers)
    assert r0.status_code == 200
    body0 = r0.json()
    doc = dict(body0["manifest"])
    kinds = doc.setdefault("KIND_LINEAR", {})
    if isinstance(kinds.get("clash"), dict):
        kinds["clash"]["linear_multiplier"] = 0.87
    r1 = admin_client.put(
        "/api/v1/admin/conflict/update",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"manifest": doc},
    )
    assert r1.status_code == 200
    j1 = r1.json()
    assert j1.get("ok") is True
    assert re.match(r"^conflict_manifest\.\d{8}_\d{6}\.json\.bak$", Path(str(j1["backup_path"])).name)
    assert (tmp_conflict_manifest.with_suffix(".sha256")).is_file()
    disk = json.loads(tmp_conflict_manifest.read_text(encoding="utf-8"))
    from app.services import conflict_manifest_admin as cfma

    assert cfma.manifest_sha256(disk) == j1["sha256"]
