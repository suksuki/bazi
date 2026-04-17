"""V6.6–V6.7 Admin：格局法典 API（manifest / reload / update / preview / 备份 / 回滚）。"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.api.v1.admin.patterns import router as patterns_admin_router


@pytest.fixture()
def admin_client() -> TestClient:
    app = FastAPI()
    app.include_router(patterns_admin_router, prefix="/api")
    return TestClient(app)


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    return {"X-Admin-Token": os.getenv("QIAZHI_ADMIN_TOKEN", "").strip() or "local-dev-qiazhi-admin"}


@pytest.fixture()
def tmp_manifest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    src = Path(__file__).resolve().parents[2] / "app" / "logic" / "patterns" / "pattern_manifest.json"
    dst = tmp_path / "pattern_manifest.json"
    shutil.copyfile(src, dst)
    monkeypatch.setenv("QIAZHI_PATTERN_MANIFEST_PATH", str(dst))
    return dst


def test_admin_patterns_manifest_requires_token(admin_client: TestClient) -> None:
    r = admin_client.get("/api/v1/admin/patterns/manifest")
    assert r.status_code == 401


def test_admin_patterns_manifest_reload_preview_update(
    admin_client: TestClient,
    admin_headers: dict[str, str],
    tmp_manifest: Path,
) -> None:
    r0 = admin_client.get("/api/v1/admin/patterns/manifest", headers=admin_headers)
    assert r0.status_code == 200
    body0 = r0.json()
    assert body0.get("ok") is True
    assert isinstance(body0.get("manifest"), dict)
    assert body0.get("sha256")

    r1 = admin_client.post("/api/v1/admin/patterns/reload", headers=admin_headers)
    assert r1.status_code == 200
    assert r1.json().get("ok") is True

    tensor = {
        "deity_scores": {
            "正印": 2.0,
            "偏印": 2.0,
            "食神": 30.0,
            "伤官": 30.0,
            "比肩": 8.0,
            "劫财": 8.0,
            "偏财": 6.0,
            "正财": 6.0,
            "七杀": 4.0,
            "正官": 4.0,
        },
        "meta": {"month_branch": "午", "active_structures": []},
    }
    r2 = admin_client.post(
        "/api/v1/admin/patterns/preview",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"physics_tensor": tensor, "metadata": {}},
    )
    assert r2.status_code == 200
    rows = r2.json().get("rows") or []
    fc = next(x for x in rows if x.get("pattern_id") == "FOLLOW_CHILD")
    assert fc.get("exclusion_hit") is True

    doc = dict(body0["manifest"])
    doc["SPECIAL_PATTERNS"]["FOLLOW_CHILD"]["exclusions"]["Seal_Axis"] = 0.05
    r3 = admin_client.put(
        "/api/v1/admin/patterns/update",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"manifest": doc},
    )
    assert r3.status_code == 200
    j3 = r3.json()
    assert j3.get("ok") is True
    assert j3.get("backup_path"), "应写入时间戳 .json.bak 备份路径"
    assert re.match(r"^pattern_manifest\.\d{8}_\d{6}\.json\.bak$", Path(str(j3["backup_path"])).name)
    bak = Path(str(j3["backup_path"]))
    assert bak.is_file()

    r4 = admin_client.post(
        "/api/v1/admin/patterns/preview",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"physics_tensor": tensor, "metadata": {}},
    )
    assert r4.status_code == 200
    fc2 = next(x for x in r4.json().get("rows") or [] if x.get("pattern_id") == "FOLLOW_CHILD")
    assert fc2.get("exclusion_hit") is False

    doc["SPECIAL_PATTERNS"]["FOLLOW_CHILD"]["exclusions"]["Seal_Axis"] = 0.03
    admin_client.put(
        "/api/v1/admin/patterns/update",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"manifest": doc},
    )


def test_admin_patterns_restore_latest_roundtrip(
    admin_client: TestClient,
    admin_headers: dict[str, str],
    tmp_manifest: Path,
) -> None:
    r0 = admin_client.get("/api/v1/admin/patterns/manifest", headers=admin_headers)
    orig = r0.json()["manifest"]
    doc = dict(orig)
    doc["SPECIAL_PATTERNS"]["FOLLOW_CHILD"]["exclusions"]["Seal_Axis"] = 0.99
    admin_client.put(
        "/api/v1/admin/patterns/update",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"manifest": doc},
    )
    r1 = admin_client.get("/api/v1/admin/patterns/manifest", headers=admin_headers)
    assert float(r1.json()["manifest"]["SPECIAL_PATTERNS"]["FOLLOW_CHILD"]["exclusions"]["Seal_Axis"]) == pytest.approx(0.99)
    r2 = admin_client.post("/api/v1/admin/patterns/restore-latest", headers=admin_headers)
    assert r2.status_code == 200
    assert r2.json().get("ok") is True
    r3 = admin_client.get("/api/v1/admin/patterns/manifest", headers=admin_headers)
    assert float(r3.json()["manifest"]["SPECIAL_PATTERNS"]["FOLLOW_CHILD"]["exclusions"]["Seal_Axis"]) == pytest.approx(
        float(orig["SPECIAL_PATTERNS"]["FOLLOW_CHILD"]["exclusions"]["Seal_Axis"])
    )


def test_admin_patterns_collision_preview_returns_physics_and_axis_energy(
    admin_client: TestClient,
    admin_headers: dict[str, str],
    tmp_manifest: Path,
) -> None:
    """collision-preview：排盘 + 物理引擎 + 格局行（含主轴能量，供 Admin 可视化）。"""
    r = admin_client.post(
        "/api/v1/admin/patterns/collision-preview",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={
            "date": "1977-05-08",
            "time": "18:00",
            "calendar": "solar",
            "gender": "male",
            "reference_year": 2024,
            "enabled_plugins": [],
        },
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("ok") is True
    rows = j.get("rows") or []
    assert isinstance(rows, list) and len(rows) >= 1
    pt = j.get("physics_tensor") or {}
    assert isinstance(pt, dict) and pt.get("deity_scores")
    any_row = rows[0]
    assert "primary_axis_energy" in any_row
    assert "exclusion_axis_snapshots" in any_row
    assert isinstance(any_row["exclusion_axis_snapshots"], list)


def test_admin_patterns_update_rejects_non_object(admin_client: TestClient, admin_headers: dict[str, str], tmp_manifest: Path) -> None:
    r = admin_client.put(
        "/api/v1/admin/patterns/update",
        headers={**admin_headers, "Content-Type": "application/json"},
        json={"manifest": []},
    )
    assert r.status_code in (400, 422)
