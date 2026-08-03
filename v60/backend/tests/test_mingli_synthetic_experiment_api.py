from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from abu_v60.api import mingli_synthetic_lab
from abu_v60.main import app
from abu_v60.mingli.synthetic_experiment_service import SyntheticExperimentError
from fastapi import HTTPException, Response
from httpx import ASGITransport, AsyncClient


class _ReadOnlySyntheticService:
    def __init__(self) -> None:
        self.catalog_calls = 0
        self.snapshot_calls: list[tuple[str, str, str | None]] = []

    def catalog(self) -> dict[str, Any]:
        self.catalog_calls += 1
        return {
            "experiments": [
                {
                    "experiment_ref": "experiment:sealed",
                    "latest_run_ref": "run:sealed",
                }
            ],
            "browser_generation_allowed": False,
            "read_only": True,
        }

    def snapshot(
        self,
        *,
        experiment_ref: str,
        variant: str,
        run_ref: str | None,
    ) -> dict[str, Any]:
        self.snapshot_calls.append((experiment_ref, variant, run_ref))
        return {
            "experiment_ref": experiment_ref,
            "run_ref": run_ref,
            "selected_variant": variant,
            "browser_generation_allowed": False,
            "read_only": True,
        }


def test_catalog_and_snapshot_are_authenticated_read_only_gets(monkeypatch: Any) -> None:
    stub = _ReadOnlySyntheticService()
    monkeypatch.setattr(mingli_synthetic_lab, "service", stub)
    session = SimpleNamespace(
        account=SimpleNamespace(account_ref="owner", account_role="admin")
    )
    catalog_response = Response()
    snapshot_response = Response()

    catalog = mingli_synthetic_lab.synthetic_experiment_catalog(
        catalog_response,
        session,  # type: ignore[arg-type]
    )
    snapshot = mingli_synthetic_lab.synthetic_experiment_snapshot(
        "experiment:sealed",
        snapshot_response,
        session,  # type: ignore[arg-type]
        variant="B",
        run_ref="run:sealed",
    )

    assert catalog["browser_generation_allowed"] is False
    assert snapshot["selected_variant"] == "B"
    assert stub.catalog_calls == 1
    assert stub.snapshot_calls == [("experiment:sealed", "B", "run:sealed")]
    assert catalog_response.headers["Cache-Control"] == "private, no-store"
    assert snapshot_response.headers["Cache-Control"] == "private, no-store"


def test_snapshot_maps_missing_and_drift_without_running_model(monkeypatch: Any) -> None:
    class _FailingService(_ReadOnlySyntheticService):
        def snapshot(
            self,
            *,
            experiment_ref: str,
            variant: str,
            run_ref: str | None,
        ) -> dict[str, Any]:
            del experiment_ref, variant, run_ref
            raise SyntheticExperimentError("mingli_synthetic_experiment_definition_drift")

    monkeypatch.setattr(mingli_synthetic_lab, "service", _FailingService())
    session = SimpleNamespace(
        account=SimpleNamespace(account_ref="owner", account_role="admin")
    )

    with pytest.raises(HTTPException) as caught:
        mingli_synthetic_lab.synthetic_experiment_snapshot(
            "experiment:sealed",
            Response(),
            session,  # type: ignore[arg-type]
            variant="A",
            run_ref="run:sealed",
        )
    assert caught.value.status_code == 409
    assert caught.value.detail == "mingli_synthetic_experiment_definition_drift"


def test_synthetic_lab_rejects_non_reviewer_session(monkeypatch: Any) -> None:
    stub = _ReadOnlySyntheticService()
    monkeypatch.setattr(mingli_synthetic_lab, "service", stub)
    session = SimpleNamespace(
        account=SimpleNamespace(account_ref="member", account_role="member")
    )

    with pytest.raises(HTTPException) as caught:
        mingli_synthetic_lab.synthetic_experiment_catalog(
            Response(),
            session,  # type: ignore[arg-type]
        )

    assert caught.value.status_code == 403
    assert caught.value.detail == "mingli_synthetic_lab_reviewer_required"
    assert stub.catalog_calls == 0


def test_synthetic_lab_api_requires_session() -> None:
    async def request() -> tuple[int, int]:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://v60.test",
        ) as client:
            catalog = await client.get("/api/v60/mingli/lab/synthetic-experiments")
            snapshot = await client.get(
                "/api/v60/mingli/lab/synthetic-experiments/unknown/snapshot"
            )
            return catalog.status_code, snapshot.status_code

    assert asyncio.run(request()) == (401, 401)
