from pathlib import Path
import importlib.util

from fastapi.testclient import TestClient

from app.core import runtime_config
from app.db.session import init_db

_BACKEND_MAIN = Path(__file__).resolve().parents[2] / "main.py"
_spec = importlib.util.spec_from_file_location("qiazhi_bazi_backend_main", _BACKEND_MAIN)
assert _spec and _spec.loader
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
app = _module.app


def test_admin_runtime_config_roundtrip(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    client = TestClient(app)
    put_r = client.put(
        "/api/admin/runtime-config",
        json={
            "llm": {
                "base_url": "http://192.168.0.10:11434/v1",
                "api_key": "ollama",
                "model": "qwen2.5:3b",
            }
        },
    )
    assert put_r.status_code == 200
    get_r = client.get("/api/admin/runtime-config")
    assert get_r.status_code == 200
    assert get_r.json()["config"]["llm"]["model"] == "qwen2.5:3b"


def test_analyze_clash_returns_atomic_points_without_llm(monkeypatch, tmp_path: Path):
    # 回归：即使 LLM 不可达，接口也应返回 metadata 与引导文案，而非 502
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    runtime_config.set_runtime_config(
        {
            "llm": {
                "base_url": "http://127.0.0.1:9/v1",  # force unreachable
                "api_key": "x",
                "model": "x",
            }
        }
    )
    client = TestClient(app)
    r = client.post(
        "/api/v1/analyze_clash",
        json={
            "pillars": {
                "year": {"stem": "甲", "branch": "申"},
                "month": {"stem": "丙", "branch": "寅"},
                "day": {"stem": "戊", "branch": "午"},
                "hour": {"stem": "庚", "branch": "子"},
            }
        },
    )
    assert r.status_code == 200
    data = r.json()
    details = [p["detail"] for p in data["metadata"]["conflict_matrix"]["points"]]
    assert "寅申冲" in details
    assert "子午冲" in details
    assert "是否需要深入分析这个局部" in data["llm_prompt"]


def test_regression_decision_step_write(monkeypatch, tmp_path: Path):
    # 回归：关键路径“记录过程”写入接口可用
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    init_db()
    client = TestClient(app)
    c = client.post("/api/consultations", json={"subject_ref": "reg-1", "input_meta": {"seed": True}})
    assert c.status_code == 200
    cid = c.json()["id"]
    s = client.post(
        "/api/decision-steps",
        json={
            "consultation_id": cid,
            "step_type": "atomic-ziwu",
            "raw_data": {"conflict": "子午冲"},
            "human_choice": {"checked": True},
        },
    )
    assert s.status_code == 200
    assert isinstance(s.json()["id"], int)


def test_regression_rollback_event_write(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    init_db()
    client = TestClient(app)
    c = client.post("/api/consultations", json={"subject_ref": "reg-rb-1", "input_meta": {"seed": True}})
    assert c.status_code == 200
    cid = c.json()["id"]
    s = client.post(
        "/api/decision-steps",
        json={
            "consultation_id": cid,
            "step_type": "atomic-zichou",
            "raw_data": {"conflict": "子丑合"},
            "human_choice": {"action": "execute"},
        },
    )
    assert s.status_code == 200
    target_id = s.json()["id"]
    rb = client.post("/api/decision-steps/rollback", json={"target_step_id": target_id, "reason": "test rollback"})
    assert rb.status_code == 200
    assert rb.json()["target_step_id"] == target_id


def test_analyze_seed_end_to_end(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    runtime_config.set_runtime_config(
        {"llm": {"base_url": "http://127.0.0.1:9/v1", "api_key": "x", "model": "x"}}
    )
    client = TestClient(app)
    r = client.post("/api/v1/analyze-seed", json={"date": "1977-05-08", "time": "18:00", "calendar": "solar"})
    assert r.status_code == 200
    data = r.json()
    assert data["metadata"]["pillars"]["year"]["stem"] in "甲乙丙丁戊己庚辛壬癸"
    assert "llm_prompt" in data
