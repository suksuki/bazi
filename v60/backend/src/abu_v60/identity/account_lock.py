from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def lock_account_transaction(
    connection: Connection,
    *,
    account_ref: str,
) -> None:
    """Serialize account-current reads and writes within one transaction."""

    if not account_ref:
        raise ValueError("account_transaction_lock_ref_required")
    connection.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:account_ref))"),
        {"account_ref": account_ref},
    )
