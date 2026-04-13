"""V8.3 Admin：调候法典 API（manifest / reload / update / 备份 / 回滚）。"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.api.v1.admin.climate import router as climate_admin_router


@pytest.fixture()
def admin_client() -> TestClient:
    app = FastAPI()
    app.include_router(climate_admin_router, prefix="/api")
    return TestClient(app)


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    return {"X-Admin-Token": os.getenv("QIAZHI_ADMIN_TOKEN", "").strip() or "local-dev-qiazhi-admin"}


@pytest.fixture()
def tmp_climate_manifest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    src = Path(__file__).resolve().parents[2] / "app" / "plugins" / "classical" / "climate_manifest.json"
    dst = tmp_path / "climate_manifest.json"
    shutil.copyfile(src, dst)
    monkeypatch.setenv("QIAZHI_CLIMATE_MANIFEST_PATH", str(dst))
    return dst


def test_admin_climate_manifest_requires_token(admin_client: TestClient) -> None:
    r = admin_client.get("/api/v1/admin/climate/manifest")
    assert r.status_code == 401


def test_admin_climate_manifest_reload_update_writes_sha256_sidecar(
    admin_client: TestClient,
    admin_headers: dict[str, str],
    tmp_climate_manifest: Path,
) -> None:
    r0 = admin_client.get("/api/v1/admin/climate/manifest", headers=admin_headers)
    assert r0.status_code == 200
    body0 = r0.json()
    assert body0.get("ok") is True
    assert isinstance(body0.get("manifest"), dict)
    assert body0.get("sha256")

    r1 = admin_client.post("/api/v1/admin/climate/reload", headers=admin_headers)
    assert r1.status_code == 200

    doc = dict(body0["manifest"])
    table = doc.get("TABLE")
    assert isinstance(table, list)
    for row in table:
        if isinstance(row, dict) and str(row.get("month_branch")) == "未":
            row["earth_mod"] = float(row.get("earth_mod", 1.1)) + 0.05
            break
    r2 = admin_client.put(
        "/api/v1/admin/climate/update",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"manifest": doc},
    )
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2.get("ok") is True
    assert j2.get("backup_path")
    assert re.match(r"^climate_manifest\.\d{8}_\d{6}\.json\.bak$", Path(str(j2["backup_path"])).name)

    sig = tmp_climate_manifest.with_suffix(".sha256")
    assert sig.is_file()
    line = sig.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    assert len(line) == 64
    disk = json.loads(tmp_climate_manifest.read_text(encoding="utf-8"))
    from app.services import climate_manifest_admin as cma

    assert cma.manifest_sha256(disk) == line
