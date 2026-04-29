from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v17_rebirth.backend.api import v18_1_predictive as api_module
from v17_rebirth.backend.api.app import app
from v17_rebirth.backend.services import core_bazi_feature_layer as feature_layer
from v17_rebirth.backend.services import core_bazi_strength_model as strength_model


def _chart(year: str, month: str, day: str, hour: str) -> dict:
    return {
        "chart_snapshot": {
            "chart_id": f"chart-{year}-{month}-{day}-{hour}",
            "four_pillars": {
                "year": year,
                "month": month,
                "day": day,
                "hour": hour,
            },
        }
    }


def _bundle(year: str, month: str, day: str, hour: str) -> dict:
    return feature_layer.extract_core_bazi_features(_chart(year, month, day, hour))


def _balanced_core_bundle() -> dict:
    return {
        "bundle_id": "core_feature_bundle_balanced_fixture",
        "chart_id": "chart-balanced-fixture",
        "version": "core_bazi_layer_v1",
        "features": {
            "day_master": {"feature_id": "core.day_master", "output": {"day_master": {"stem": "乙"}}},
            "hidden_stems": {"feature_id": "core.hidden_stems", "output": {"hidden_stems": {}}},
            "ten_god_mapping": {
                "feature_id": "core.ten_god_mapping",
                "output": {
                    "ten_gods": {
                        "visible": {
                            "year_stem": {"ten_god": "食神", "ten_god_group": "output"},
                            "month_stem": {"ten_god": "比肩", "ten_god_group": "peer"},
                            "day_stem": {"ten_god": "日主", "ten_god_group": "self"},
                            "hour_stem": {"ten_god": "正官", "ten_god_group": "officer"},
                        }
                    }
                },
            },
            "root_strength": {
                "feature_id": "core.root_strength",
                "output": {
                    "rootedness": {
                        "day_master": {"root_score": 0.48, "root_count": 1},
                        "ten_god_roots": {
                            "peer": {"root_score": 0.42},
                            "resource": {"root_score": 0.26},
                            "output": {"root_score": 0.34},
                            "wealth": {"root_score": 0.36},
                            "officer": {"root_score": 0.38},
                        },
                    }
                },
            },
            "month_command": {
                "feature_id": "core.month_command",
                "output": {
                    "month_command": {
                        "season_support": {
                            "day_master": {"support": "medium", "season_multiplier": 1.8},
                            "peer": {"support": "medium", "season_multiplier": 1.8},
                            "resource": {"support": "weak", "season_multiplier": 1.0},
                            "output": {"support": "medium", "season_multiplier": 1.8},
                            "wealth": {"support": "weak", "season_multiplier": 1.0},
                            "officer": {"support": "medium", "season_multiplier": 1.8},
                        }
                    }
                },
            },
        },
    }


def test_strength_model_detects_strong_day_master_tendency() -> None:
    bundle = _bundle("甲寅", "甲寅", "甲寅", "癸亥")
    strength = strength_model.evaluate_core_strength({"core_feature_bundle": bundle})

    day = strength["day_master_strength"]
    assert day["tendency"] in {"strong", "leaning_strong"}
    assert day["support_score"] > day["pressure_score"]
    assert strength["guardrails"]["no_domain_conclusion"] is True
    assert strength["guardrails"]["no_use_god_verdict"] is True


def test_strength_model_detects_weak_day_master_tendency() -> None:
    bundle = _bundle("辛酉", "庚申", "乙丑", "己丑")
    strength = strength_model.evaluate_core_strength({"core_feature_bundle": bundle})

    day = strength["day_master_strength"]
    assert day["tendency"] in {"weak", "leaning_weak"}
    assert day["pressure_score"] > day["support_score"]


def test_strength_model_detects_balanced_fixture() -> None:
    strength = strength_model.evaluate_core_strength({"core_feature_bundle": _balanced_core_bundle()})

    day = strength["day_master_strength"]
    assert day["tendency"] == "balanced"
    assert abs(day["support_score"] - day["pressure_score"]) < 0.1


def test_strength_model_outputs_ten_god_strengths_and_evidence_refs() -> None:
    strength = strength_model.evaluate_core_strength({"core_feature_bundle": _bundle("丁巳", "乙酉", "乙丑", "乙卯")})

    ten_gods = strength["ten_god_strengths"]
    assert {"wealth", "officer_killing", "output", "seal", "peer"} == set(ten_gods)
    assert all(0.0 <= item["score"] <= 1.0 for item in ten_gods.values())
    assert all(item["evidence_refs"] for item in ten_gods.values())
    assert strength["evidence_refs"] == [
        "core.day_master",
        "core.ten_god_mapping",
        "core.hidden_stems",
        "core.root_strength",
        "core.month_command",
    ]


def test_strength_store_has_no_prediction_or_narrative_side_effects(tmp_path: Path) -> None:
    store = strength_model.CoreBaziStrengthStore(tmp_path / "strength.json")
    strength = store.evaluate_and_store({"core_feature_bundle": _bundle("丁巳", "乙酉", "乙丑", "乙卯")})
    loaded = store.get_bundle(strength["strength_bundle_id"])

    forbidden = {"prediction_id", "ledger", "conclusion", "conclusions", "narrative", "pattern_verdict", "use_god_verdict"}
    found: list[str] = []

    def walk(value, path: str = "") -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in forbidden:
                    found.append(f"{path}/{key}")
                walk(nested, f"{path}/{key}")
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                walk(nested, f"{path}[{index}]")

    walk(loaded)

    assert loaded["guardrails"]["no_prediction_id"] is True
    assert loaded["guardrails"]["no_ledger_write"] is True
    assert found == []


def test_strength_api_evaluate_and_get_round_trip(tmp_path: Path, monkeypatch) -> None:
    store = strength_model.CoreBaziStrengthStore(tmp_path / "api_strength.json")
    monkeypatch.setattr(api_module, "core_bazi_strength_service", store)

    client = TestClient(app)
    core_bundle = _bundle("丁巳", "乙酉", "乙丑", "乙卯")
    evaluate_resp = client.post("/api/v18.1/core-bazi/strength/evaluate", json={"core_feature_bundle": core_bundle})

    assert evaluate_resp.status_code == 200
    payload = evaluate_resp.json()
    assert payload["ok"] is True
    strength_bundle_id = payload["data"]["strength_bundle_id"]

    get_resp = client.get(f"/api/v18.1/core-bazi/strength/{strength_bundle_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["strength_bundle_id"] == strength_bundle_id
