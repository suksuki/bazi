from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from v40.contracts.base import RoleKey
from v40.contracts.user import UserAccountInternal, UserSessionRecord


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str, *, salt: str | None = None) -> tuple[str, str]:
    clean_password = password.strip()
    if len(clean_password) < 6:
        raise ValueError("Password must be at least 6 characters")
    chosen_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", clean_password.encode("utf-8"), chosen_salt.encode("utf-8"), 120_000)
    return digest.hex(), chosen_salt


def verify_password(password: str, *, password_hash: str, password_salt: str) -> bool:
    candidate_hash, _salt = hash_password(password, salt=password_salt)
    return hmac.compare_digest(candidate_hash, password_hash)


def build_user_account(
    *,
    email: str,
    password: str,
    display_name: str = "",
    role_key: RoleKey = "user",
) -> UserAccountInternal:
    if role_key not in {"user", "practitioner"}:
        raise ValueError("User app registration only supports user or practitioner")
    clean_email = normalize_email(email)
    if "@" not in clean_email:
        raise ValueError("Registration requires a valid email")
    password_hash, password_salt = hash_password(password)
    user_id = f"user:{secrets.token_urlsafe(18)}"
    return UserAccountInternal(
        user_id=user_id,
        email=clean_email,
        display_name=display_name.strip() or clean_email.split("@", 1)[0],
        role_key=role_key,
        active=True,
        password_hash=password_hash,
        password_salt=password_salt,
    )


def build_user_session(*, user_id: str, role_key: RoleKey) -> UserSessionRecord:
    if role_key not in {"user", "practitioner"}:
        raise ValueError("User app session only supports user or practitioner")
    now = datetime.now(timezone.utc)
    return UserSessionRecord(
        session_id=f"sess:{secrets.token_urlsafe(24)}",
        user_id=user_id,
        role_key=role_key,
        created_at=now,
        expires_at=now + timedelta(days=30),
        revoked=False,
    )

