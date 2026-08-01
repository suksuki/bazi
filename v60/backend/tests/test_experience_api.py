from __future__ import annotations

from types import SimpleNamespace

import pytest
from abu_v60.api import experience
from fastapi import Response


def test_home_response_is_private_and_not_cacheable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        experience.service,
        "snapshot",
        lambda *, account_ref: {"account_ref": account_ref},
    )
    response = Response()
    session = SimpleNamespace(account=SimpleNamespace(account_ref="account-private"))

    payload = experience.home_experience(response, session)  # type: ignore[arg-type]

    assert payload == {"account_ref": "account-private"}
    assert response.headers["Cache-Control"] == "private, no-store"
