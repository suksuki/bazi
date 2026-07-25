from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request, WebSocket

from experience.runtime import TheaterRuntime
from experience.store import TheaterStore
from product.product_store import ProductStore
from product.theater_envelope import ProductExperienceEnvelopePort
from product.theater_experiment import ProductMingliExperimentPort
from product.theater_performance import TheaterPerformanceService


@dataclass(frozen=True)
class TheaterRouteContext:
    product_store: ProductStore
    session_cookie: str
    theater_store: TheaterStore
    runtime: TheaterRuntime
    envelope_port: ProductExperienceEnvelopePort
    experiment_port: ProductMingliExperimentPort
    performance_service: TheaterPerformanceService

    def account_for_request(self, request: Request):
        token = request.cookies.get(self.session_cookie, "")
        return self.product_store.account_for_token(token) if token else None

    def account_for_websocket(self, websocket: WebSocket):
        token = websocket.cookies.get(self.session_cookie, "")
        return self.product_store.account_for_token(token) if token else None

    def require_admin(self, request: Request):
        account = self.account_for_request(request)
        if not account or str(account.get("account_role") or "") != "admin":
            raise HTTPException(status_code=403, detail="theater_director_requires_admin")
        return account

    def authorize_run(self, *, participant_run_id: str, access_token: str, account) -> None:
        run = self.theater_store.get_participant(participant_run_id)
        if not run:
            raise HTTPException(status_code=404, detail="participant_run_not_found")
        account_matches = bool(account and str(account.get("user_id")) == run.participant_ref)
        token_matches = bool(
            access_token
            and run.access_token_hash
            and secrets.compare_digest(run.access_token_hash, token_hash(access_token))
        )
        if not account_matches and not token_matches:
            raise HTTPException(status_code=403, detail="participant_access_denied")


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def public_run(run: Any) -> dict[str, object]:
    payload = run.model_dump(mode="json")
    payload.pop("access_token_hash", None)
    return payload
