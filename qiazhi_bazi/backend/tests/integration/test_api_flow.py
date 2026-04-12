import asyncio
from contextlib import contextmanager
import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "postgresql://tester:tester@127.0.0.1/qiazhi_test")

import app.api.admin as admin_module
import app.api.router as router_module
from app.api.contracts import (
    AnalyzeClashRequest,
    AnalyzeSeedRequest,
    ConfirmStructureRequest,
    ConsultationCreate,
    DecisionRollbackRequest,
    DecisionStepCreate,
    RuntimeConfigRequest,
)
from app.core import runtime_config
from app.db.models import Consultation, DecisionStep, SessionConsensus
from app.schemas.bazi_metadata import FourPillars, StemBranchPair


class _FakeSession:
    def __init__(self):
        self.consultations = {}
        self.steps = {}
        self.consensus = {}
        self._next_consultation_id = 1
        self._next_step_id = 1
        self._next_consensus_id = 1

    def add(self, obj):
        if isinstance(obj, Consultation):
            if obj.id is None:
                obj.id = self._next_consultation_id
                self._next_consultation_id += 1
            self.consultations[obj.id] = obj
            return
        if isinstance(obj, DecisionStep):
            if obj.id is None:
                obj.id = self._next_step_id
                self._next_step_id += 1
            self.steps[obj.id] = obj
            return
        if isinstance(obj, SessionConsensus):
            if obj.id is None:
                obj.id = self._next_consensus_id
                self._next_consensus_id += 1
            self.consensus[obj.id] = obj
            return
        raise TypeError(f"unsupported object: {type(obj)!r}")

    def flush(self):
        return None

    def refresh(self, _obj):
        return None

    def get(self, model, obj_id):
        if model is Consultation:
            return self.consultations.get(obj_id)
        if model is DecisionStep:
            return self.steps.get(obj_id)
        return None

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        return None


def _patch_fake_session(monkeypatch) -> _FakeSession:
    fake = _FakeSession()

    @contextmanager
    def fake_scope():
        yield fake

    monkeypatch.setattr(router_module, "session_scope", fake_scope)
    return fake


def test_admin_runtime_config_roundtrip(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    put_r = admin_module.runtime_config_put(
        RuntimeConfigRequest(
            llm={
                "base_url": "http://127.0.0.1:11434/v1",
                "api_key": "",
                "model": "qwen2.5:3b",
            }
        )
    )
    assert put_r["ok"] is True
    get_r = admin_module.runtime_config_get()
    assert get_r["config"]["llm"]["model"] == "qwen2.5:3b"
    assert get_r["config"]["llm"].get("api_key") in ("", None)
    assert get_r["config"]["llm"].get("api_key_configured") is False


def test_admin_runtime_config_redacts_api_key(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    runtime_config.set_runtime_config({"llm": {"base_url": "http://127.0.0.1:1/v1", "api_key": "secret-key", "model": "m"}})
    get_r = admin_module.runtime_config_get()
    assert get_r["config"]["llm"].get("api_key") in ("", None)
    assert get_r["config"]["llm"].get("api_key_configured") is True
    disk = runtime_config.get_runtime_config()
    assert disk["llm"]["api_key"] == "secret-key"


def test_analyze_clash_returns_atomic_points_without_llm(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    runtime_config.set_runtime_config(
        {"llm": {"base_url": "http://127.0.0.1:9/v1", "api_key": "x", "model": "x"}}
    )
    result = asyncio.run(
        router_module.analyze_clash(
            AnalyzeClashRequest(
                pillars=FourPillars(
                    year=StemBranchPair(stem="甲", branch="申"),
                    month=StemBranchPair(stem="丙", branch="寅"),
                    day=StemBranchPair(stem="戊", branch="午"),
                    hour=StemBranchPair(stem="庚", branch="子"),
                )
            )
        )
    )
    details = [point["detail"] for point in result["metadata"]["conflict_matrix"]["points"]]
    assert "寅申冲" in details
    assert "子午冲" in details
    assert "是否需要深入分析这个局部" in result["llm_prompt"]


def test_regression_decision_step_write(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    _patch_fake_session(monkeypatch)

    consultation = router_module.create_consultation(ConsultationCreate(subject_ref="reg-1", input_meta={"seed": True}))
    step = router_module.create_decision_step(
        DecisionStepCreate(
            consultation_id=consultation["id"],
            step_type="atomic-ziwu",
            raw_data={"conflict": "子午冲"},
            human_choice={"checked": True},
        )
    )
    assert isinstance(step["id"], int)


def test_regression_rollback_event_write(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    _patch_fake_session(monkeypatch)

    consultation = router_module.create_consultation(ConsultationCreate(subject_ref="reg-rb-1", input_meta={"seed": True}))
    step = router_module.create_decision_step(
        DecisionStepCreate(
            consultation_id=consultation["id"],
            step_type="atomic-zichou",
            raw_data={"conflict": "子丑合"},
            human_choice={"action": "execute"},
        )
    )
    rollback = router_module.rollback_decision_step(
        DecisionRollbackRequest(target_step_id=step["id"], reason="test rollback")
    )
    assert rollback["target_step_id"] == step["id"]


def test_confirm_structure_roundtrip(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    fake = _patch_fake_session(monkeypatch)
    consultation = router_module.create_consultation(ConsultationCreate(subject_ref="reg-structure", input_meta={"seed": True}))

    response = router_module.confirm_structure(
        ConfirmStructureRequest(
            consultation_id=consultation["id"],
            structure_name="伤官配印",
            confidence=0.82,
            evidence="unit test",
        )
    )
    assert response["ok"] is True
    assert fake.consultations[consultation["id"]].input_meta["confirmed_structure"]["name"] == "伤官配印"


def test_analyze_seed_end_to_end(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", tmp_path / "runtime_config.json")
    runtime_config.set_runtime_config(
        {"llm": {"base_url": "http://127.0.0.1:9/v1", "api_key": "x", "model": "x"}}
    )
    result = asyncio.run(
        router_module.analyze_seed(
            AnalyzeSeedRequest(date="1977-05-08", time="18:00", calendar="solar", gender="male")
        )
    )
    assert result["metadata"]["pillars"]["year"]["stem"] in "甲乙丙丁戊己庚辛壬癸"
    assert "llm_prompt" in result
    assert isinstance(result.get("physics_tensor", {}).get("confidence"), float)
    assert isinstance(result.get("physics_tensor", {}).get("evidence"), list)
