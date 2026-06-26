from __future__ import annotations

import pytest

from v30.config import _validate_database_url


def test_v30_database_url_allows_v30_database() -> None:
    _validate_database_url("postgresql://user:pass@localhost:5432/qiazhi_v30")


def test_v30_database_url_rejects_v20_database() -> None:
    with pytest.raises(ValueError, match="V20 database"):
        _validate_database_url("postgresql://user:pass@localhost:5432/qiazhi_v20")


def test_v30_database_url_allows_unset() -> None:
    _validate_database_url(None)
