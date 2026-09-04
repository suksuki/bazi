from __future__ import annotations

from types import SimpleNamespace

import pytest
from abu_v60.api import public_experience
from fastapi import Response


def test_home_response_is_private_and_not_cacheable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        public_experience.service,
        "snapshot",
        lambda *, account_ref: {"account_ref": account_ref},
    )
    monkeypatch.setattr(
        public_experience,
        "public_home_projection",
        lambda snapshot: snapshot,
    )
    response = Response()
    session = SimpleNamespace(account=SimpleNamespace(account_ref="account-private"))

    payload = public_experience.public_home_experience(  # type: ignore[arg-type]
        response,
        session,
    )

    assert payload == {"account_ref": "account-private"}
    assert response.headers["Cache-Control"] == "private, no-store"
