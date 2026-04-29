from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v17_rebirth.backend.api import v18_1_predictive as api_module
from v17_rebirth.backend.api.app import app
from v17_rebirth.backend.services import core_bazi_feature_layer as core_layer


def _sample_chart() -> dict:
    return {
        "chart_snapshot": {
            "chart_id": "chart-core-v1",
            "four_pillars": {
                "year": "丁巳",
                "month": "乙酉",
                "day": "乙丑",
                "hour": "乙卯",
            },
            "luck_pillar": "壬子",
            "flow_pillar": "己未",
        }
    }


def test_core_feature_extracts_day_master_ten_gods_and_hidden_stems() -> None:
    bundle = core_layer.extract_core_bazi_features(_sample_chart())
    features = bundle["features"]

    assert features["day_master"]["feature_id"] == "core.day_master"
    assert features["day_master"]["output"]["day_master"]["stem"] == "乙"
    assert features["day_master"]["output"]["day_master"]["element"] == "wood"
    assert features["day_master"]["output"]["day_master"]["polarity"] == "yin"

    visible = features["ten_god_mapping"]["output"]["ten_gods"]["visible"]
    assert visible["year_stem"]["stem"] == "丁"
    assert visible["year_stem"]["ten_god"] == "食神"
    assert visible["month_stem"]["ten_god"] == "比肩"
    assert visible["day_stem"]["ten_god"] == "日主"

    hidden = features["hidden_stems"]["output"]["hidden_stems"]
    assert hidden["巳"][0]["stem"] == "丙"
    assert hidden["巳"][0]["weight"] == "primary"
    assert hidden["丑"][0]["stem"] == "己"


def test_core_feature_extracts_root_and_month_command_evidence_only() -> None:
    bundle = core_layer.extract_core_bazi_features(_sample_chart())
    features = bundle["features"]

    rootedness = features["root_strength"]["output"]["rootedness"]
    assert rootedness["day_master"]["root_count"] >= 1
    assert 0.0 <= rootedness["day_master"]["root_score"] <= 1.0
    assert "wealth" in rootedness["ten_god_roots"]

    month_command = features["month_command"]["output"]["month_command"]
    assert month_command["branch"] == "酉"
    assert month_command["season_element"] == "metal"
    assert month_command["dominant_hidden_stem"] == "辛"
    assert month_command["day_master_season_relation"] == "officer"
    assert "wealth" in month_command["season_support"]

    assert features["root_strength"]["boundary"] == "root_evidence_only_no_body_strength_judgement"
    assert "conclusion" not in bundle
    assert "prediction_id" not in bundle


def test_core_feature_extracts_relation_hits_without_good_bad_judgement() -> None:
    bundle = core_layer.extract_core_bazi_features(_sample_chart())
    relations = bundle["features"]["relation_hits"]["output"]["relations"]
    relation_types = {item["relation_type"] for item in relations}

    assert "three_harmony" in relation_types
    assert "six_harmony" in relation_types
    assert "clash" in relation_types
    assert any(
        item["relation_type"] == "three_harmony"
        and item["branches"] == ["巳", "酉", "丑"]
        and item["target_element"] == "metal"
        and item["scope"] == "natal"
        for item in relations
    )
    assert any(
        item["relation_type"] == "clash"
        and set(item["branches"]) == {"丑", "未"}
        and item["scope"] == "flow_to_natal"
        for item in relations
    )
    assert bundle["features"]["relation_hits"]["boundary"] == "geometry_only_no_good_bad_judgement"


def test_core_feature_store_round_trip_and_no_prediction_side_effects(tmp_path: Path) -> None:
    store = core_layer.CoreBaziFeatureStore(tmp_path / "bundles.json")
    bundle = store.extract_and_store(_sample_chart())
    loaded = store.get_bundle(bundle["bundle_id"])

    assert loaded["bundle_id"] == bundle["bundle_id"]
    assert loaded["guardrails"]["fact_layer_only"] is True
    assert loaded["guardrails"]["no_ledger_write"] is True
    assert "prediction_id" not in loaded
    assert "ledger" not in loaded
    assert "conclusions" not in loaded


def test_core_bazi_feature_api_extract_and_get(tmp_path: Path, monkeypatch) -> None:
    store = core_layer.CoreBaziFeatureStore(tmp_path / "api_bundles.json")
    monkeypatch.setattr(api_module, "core_bazi_feature_service", store)

    client = TestClient(app)
    extract_resp = client.post("/api/v18.1/core-bazi/features/extract", json=_sample_chart())

    assert extract_resp.status_code == 200
    payload = extract_resp.json()
    assert payload["ok"] is True
    bundle_id = payload["data"]["bundle_id"]

    get_resp = client.get(f"/api/v18.1/core-bazi/features/{bundle_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["bundle_id"] == bundle_id
