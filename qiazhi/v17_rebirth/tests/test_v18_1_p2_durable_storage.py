from __future__ import annotations

from pathlib import Path

import pytest

from v17_rebirth.backend.services import v18_1_predictive_engine as engine


class FakePostgresAdapter(engine.V18StorageAdapter):
    backend_name = "postgres"

    def __init__(self):
        self.snapshot = {}
        self.save_count = 0

    def load_snapshot(self):
        return engine.json.loads(engine.json.dumps(self.snapshot, ensure_ascii=False)) if self.snapshot else {}

    def save_snapshot(self, snapshot):
        self.save_count += 1
        self.snapshot = engine.json.loads(engine.json.dumps(snapshot, ensure_ascii=False))


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.deleted = []
        self.block_locks = set()

    def get_json(self, key):
        return self.values.get(key)

    def set_json(self, key, value, ttl_seconds=300):
        self.values[key] = value

    def delete(self, *keys):
        self.deleted.extend(keys)
        for key in keys:
            self.values.pop(key, None)

    def acquire_lock(self, key, ttl_seconds=30):
        return key not in self.block_locks

    def release_lock(self, key):
        return None

    def idempotency_get(self, key):
        return self.values.get(f"idempotency:{key}")

    def idempotency_set(self, key, value, ttl_seconds=86400):
        self.values[f"idempotency:{key}"] = value


def _durable_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    service._redis = FakeRedis()
    facade = engine.RuleRuntimeFacade(service)
    return service, facade


@pytest.fixture()
def durable_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    return _durable_runtime(tmp_path, monkeypatch)


def _rule_payload(rule_id="durable.rule", owner_plugin="plugin.durable"):
    return {
        "rule_id": rule_id,
        "theory_family": "durable",
        "condition": {"durable_visible": True},
        "effect": {"wealth": 0.7},
        "priority": 0.8,
        "evidence_strength": 0.9,
        "conflict_policy": "merge",
        "version": "v1",
        "owner_plugin": owner_plugin,
        "status": "experimental",
        "effect_scope": ["wealth"],
        "allowed_topics": ["wealth"],
    }


def _activate(service: engine.V18PredictiveStore):
    service.register_rule(_rule_payload(), actor_role="manager", actor_user_id=1)
    service.update_rule_status("durable.rule", "validated", actor_role="manager", actor_user_id=1, version="v1")
    service.activate_rule(rule_id="durable.rule", target_version="v1", actor_role="manager", actor_user_id=1)
    return service.get_rule("durable.rule")


def _prediction(service: engine.V18PredictiveStore, facade: engine.RuleRuntimeFacade, prediction_id="pred-durable"):
    rule = service.get_rule("durable.rule")
    return facade.run_prediction_contract_pipeline(
        {
            "prediction_id": prediction_id,
            "request_id": f"req-{prediction_id}",
            "user_query": "durable prediction",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": "plugin.durable", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {"matched_facts": ["durable_visible"], "four_pillars": {"year": "甲子"}},
        },
        "system",
        0,
    )


def test_json_and_postgres_adapter_snapshots_are_consistent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _ = _durable_runtime(tmp_path, monkeypatch)
    _activate(service)
    snapshot = service._snapshot()
    adapter = FakePostgresAdapter()
    adapter.save_snapshot(snapshot)
    monkeypatch.setattr(engine, "V18_STORAGE_BACKEND", "postgres")
    monkeypatch.setattr(engine, "_make_storage_adapter", lambda _backend, _dsn: adapter)

    pg_service = engine.V18PredictiveStore()

    assert pg_service.get_rule("durable.rule").content_hash == service.get_rule("durable.rule").content_hash
    assert pg_service._storage_backend == "postgres"


def test_json_to_postgres_migration_is_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _ = _durable_runtime(tmp_path, monkeypatch)
    _activate(service)
    adapter = FakePostgresAdapter()
    monkeypatch.setattr(engine, "PostgresStorageAdapter", lambda _dsn: adapter)

    first = service.migrate_json_to_postgres("postgres://fake")
    second = service.migrate_json_to_postgres("postgres://fake")

    assert first["rule_count"] == second["rule_count"] == 1
    assert adapter.save_count == 2
    assert adapter.load_snapshot()["rules"]


def test_audit_event_append_only_and_hash_chain_detection(durable_runtime) -> None:
    service, _ = durable_runtime
    _activate(service)

    assert service.verify_audit_hash_chain()["ok"] is True
    with pytest.raises(engine.PredictiveServiceError) as update_error:
        service.update_audit_event("anything")
    assert update_error.value.code == "AUDIT_APPEND_ONLY"

    service._rule_audit_events[0].message = "tampered"
    broken = service.verify_audit_hash_chain()
    assert broken["ok"] is False
    assert broken["broken"]


def test_transaction_rollback_restores_state(durable_runtime) -> None:
    service, _ = durable_runtime

    with pytest.raises(RuntimeError):
        with service.transaction("rollback-test"):
            service.register_rule(_rule_payload("rollback.rule", "plugin.rollback"), actor_role="manager", actor_user_id=1)
            raise RuntimeError("boom")

    with pytest.raises(engine.PredictiveServiceError):
        service.get_rule("rollback.rule", allow_inactive=True)


def test_feedback_missing_prediction_fails_and_idempotency_prevents_duplicate(durable_runtime) -> None:
    service, facade = durable_runtime
    _activate(service)
    _prediction(service, facade)
    conclusion_ref = service.get_ledger("pred-durable")["conclusion_refs"][0]

    with pytest.raises(engine.PredictiveServiceError) as missing:
        service.append_prediction_feedback("missing", {"feedback_type": "miss"})
    assert missing.value.code == "LEDGER_NOT_FOUND"

    first = service.append_prediction_feedback("pred-durable", {"request_id": "fb-1", "conclusion_ref": conclusion_ref, "feedback_type": "hit"})
    second = service.append_prediction_feedback("pred-durable", {"request_id": "fb-1", "conclusion_ref": conclusion_ref, "feedback_type": "hit"})

    assert first == second
    assert service.query_feedback(prediction_id="pred-durable")["total_matched"] == 1
    assert "cache:rule_quality_scores" in service._redis.deleted


def test_redis_lock_blocks_rule_activation(durable_runtime) -> None:
    service, _ = durable_runtime
    service.register_rule(_rule_payload("locked.rule", "plugin.locked"), actor_role="manager", actor_user_id=1)
    service.update_rule_status("locked.rule", "validated", actor_role="manager", actor_user_id=1, version="v1")
    service._redis.block_locks.add("lock:rule:locked.rule")

    with pytest.raises(engine.PredictiveServiceError) as locked:
        service.activate_rule(rule_id="locked.rule", target_version="v1", actor_role="manager", actor_user_id=1)
    assert locked.value.code == "LOCK_BUSY"
