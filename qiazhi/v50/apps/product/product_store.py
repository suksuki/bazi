from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import uuid4

from core.contracts import BirthInputCanonical
from product.database_schema import check_product_database_schema


ACCOUNT_ROLES = {"member", "practitioner", "research_master"}
PASSWORD_ITERATIONS = 310_000


class ProductStoreError(ValueError):
    pass


class ProductStore(Protocol):
    persistent: bool
    storage_name: str

    def register_account(self, *, email: str, password: str, display_name: str, role: str) -> dict[str, object]: ...
    def authenticate(self, *, email: str, password: str) -> dict[str, object] | None: ...
    def ensure_admin_account(self, *, email: str, password: str, display_name: str) -> dict[str, object]: ...
    def create_session(self, *, user_id: str) -> str: ...
    def account_for_token(self, token: str) -> dict[str, object] | None: ...
    def revoke_session(self, token: str) -> None: ...
    def save_profile(self, *, user_id: str, birth_input: BirthInputCanonical, profile_id: str | None = None) -> dict[str, object]: ...
    def list_profiles(self, *, user_id: str) -> list[dict[str, object]]: ...
    def get_profile(self, *, user_id: str, profile_id: str) -> dict[str, object] | None: ...
    def delete_profile(self, *, user_id: str, profile_id: str) -> bool: ...


class MemoryProductStore:
    persistent = False
    storage_name = "memory_only"

    def __init__(self) -> None:
        self._accounts: dict[str, dict[str, object]] = {}
        self._accounts_by_email: dict[str, str] = {}
        self._sessions: dict[str, str] = {}
        self._profiles: dict[str, dict[str, dict[str, object]]] = {}

    def register_account(self, *, email: str, password: str, display_name: str, role: str) -> dict[str, object]:
        clean_email, clean_name, clean_role = _validate_registration(email, password, display_name, role)
        if clean_email in self._accounts_by_email:
            raise ProductStoreError("email_already_registered")
        user_id = f"v50-user-{uuid4().hex[:20]}"
        salt, password_hash = _hash_password(password)
        internal = {
            **_public_account(user_id=user_id, email=clean_email, display_name=clean_name, role=clean_role),
            "password_salt": salt,
            "password_hash": password_hash,
        }
        self._accounts[user_id] = internal
        self._accounts_by_email[clean_email] = user_id
        return _strip_password(internal)

    def authenticate(self, *, email: str, password: str) -> dict[str, object] | None:
        user_id = self._accounts_by_email.get(email.strip().lower())
        account = self._accounts.get(user_id or "")
        if not account or not _verify_password(password, str(account["password_salt"]), str(account["password_hash"])):
            return None
        return _strip_password(account)

    def ensure_admin_account(self, *, email: str, password: str, display_name: str) -> dict[str, object]:
        clean_email, clean_name = _validate_admin(email, password, display_name)
        for account in self._accounts.values():
            if account.get("account_role") == "admin" and account.get("email") != clean_email:
                account["active"] = False
        user_id = self._accounts_by_email.get(clean_email) or "v50-admin-primary"
        salt, password_hash = _hash_password(password)
        internal = {
            **_public_account(user_id=user_id, email=clean_email, display_name=clean_name, role="admin"),
            "password_salt": salt,
            "password_hash": password_hash,
        }
        self._accounts[user_id] = internal
        self._accounts_by_email[clean_email] = user_id
        return _strip_password(internal)

    def create_session(self, *, user_id: str) -> str:
        token = secrets.token_urlsafe(36)
        self._sessions[_token_hash(token)] = user_id
        return token

    def account_for_token(self, token: str) -> dict[str, object] | None:
        account = self._accounts.get(self._sessions.get(_token_hash(token), ""))
        return _strip_password(account) if account else None

    def revoke_session(self, token: str) -> None:
        self._sessions.pop(_token_hash(token), None)

    def save_profile(self, *, user_id: str, birth_input: BirthInputCanonical, profile_id: str | None = None) -> dict[str, object]:
        profiles = self._profiles.setdefault(user_id, {})
        if profile_id and profile_id not in profiles:
            raise ProductStoreError("profile_not_found")
        profile = _account_profile_payload(
            user_id=user_id,
            birth_input=birth_input,
            profile_id=profile_id,
            persisted=False,
        )
        if not profile_id:
            candidate_name = str(profile.get("display_name") or "").strip().casefold()
            existing = next(
                (
                    item
                    for item in profiles.values()
                    if not item.get("deleted")
                    and item.get("profile_fingerprint") == profile["profile_fingerprint"]
                    and str(item.get("display_name") or "").strip().casefold() == candidate_name
                ),
                None,
            )
            if existing:
                profile["profile_id"] = existing["profile_id"]
        for existing in profiles.values():
            existing["is_default"] = False
        profiles[str(profile["profile_id"])] = profile
        return dict(profile)

    def list_profiles(self, *, user_id: str) -> list[dict[str, object]]:
        values = [dict(value) for value in self._profiles.get(user_id, {}).values() if not value.get("deleted")]
        values.sort(key=lambda item: (not bool(item.get("is_default")), str(item.get("display_name"))))
        return _deduplicate_profile_archive(values)

    def get_profile(self, *, user_id: str, profile_id: str) -> dict[str, object] | None:
        value = self._profiles.get(user_id, {}).get(profile_id)
        return dict(value) if value and not value.get("deleted") else None

    def delete_profile(self, *, user_id: str, profile_id: str) -> bool:
        profile = self._profiles.get(user_id, {}).get(profile_id)
        if not profile:
            return False
        profile["deleted"] = True
        return True


class PostgresProductStore:
    persistent = True
    storage_name = "v50_postgresql"

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        check_product_database_schema(database_url)

    def _connect(self):
        import psycopg
        return psycopg.connect(self._database_url)

    def register_account(self, *, email: str, password: str, display_name: str, role: str) -> dict[str, object]:
        from psycopg import errors
        from psycopg.types.json import Jsonb

        clean_email, clean_name, clean_role = _validate_registration(email, password, display_name, role)
        user_id = f"v50-user-{uuid4().hex[:20]}"
        salt, password_hash = _hash_password(password)
        account = _public_account(user_id=user_id, email=clean_email, display_name=clean_name, role=clean_role)
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO v50_user_accounts (
                            user_id, email, display_name, account_role, password_hash, password_salt,
                            role_status, active, account_json
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, true, %s)
                        """,
                        (user_id, clean_email, clean_name, clean_role, password_hash, salt, account["role_status"], Jsonb(account)),
                    )
        except errors.UniqueViolation as exc:
            raise ProductStoreError("email_already_registered") from exc
        return _strip_password(account)

    def authenticate(self, *, email: str, password: str) -> dict[str, object] | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT account_json, password_hash, password_salt
                    FROM v50_user_accounts WHERE email = %s AND active = true LIMIT 1
                    """,
                    (email.strip().lower(),),
                )
                row = cur.fetchone()
        if not row or not _verify_password(password, row["password_salt"], row["password_hash"]):
            return None
        return _strip_password(dict(row["account_json"]))

    def ensure_admin_account(self, *, email: str, password: str, display_name: str) -> dict[str, object]:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        clean_email, clean_name = _validate_admin(email, password, display_name)
        salt, password_hash = _hash_password(password)
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT user_id FROM v50_user_accounts WHERE email = %s LIMIT 1", (clean_email,))
                existing = cur.fetchone()
                user_id = str(existing["user_id"]) if existing else "v50-admin-primary"
                if not existing:
                    cur.execute("SELECT 1 FROM v50_user_accounts WHERE user_id = %s", (user_id,))
                    if cur.fetchone():
                        user_id = f"v50-admin-{uuid4().hex[:20]}"
                account = _public_account(
                    user_id=user_id,
                    email=clean_email,
                    display_name=clean_name,
                    role="admin",
                )
                cur.execute(
                    """
                    UPDATE v50_user_accounts
                    SET active = false, updated_at = now()
                    WHERE account_role = 'admin' AND email <> %s
                    """,
                    (clean_email,),
                )
                cur.execute(
                    """
                    INSERT INTO v50_user_accounts (
                        user_id, email, display_name, account_role, password_hash, password_salt,
                        role_status, active, account_json
                    ) VALUES (%s, %s, %s, 'admin', %s, %s, 'system_admin', true, %s)
                    ON CONFLICT (email) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        account_role = 'admin',
                        password_hash = EXCLUDED.password_hash,
                        password_salt = EXCLUDED.password_salt,
                        role_status = 'system_admin',
                        active = true,
                        account_json = EXCLUDED.account_json,
                        updated_at = now()
                    """,
                    (user_id, clean_email, clean_name, password_hash, salt, Jsonb(account)),
                )
        return _strip_password(account)

    def create_session(self, *, user_id: str) -> str:
        token = secrets.token_urlsafe(36)
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v50_user_sessions (session_id, user_id, token_hash, expires_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (f"v50-session-{uuid4().hex[:20]}", user_id, _token_hash(token), expires_at),
                )
        return token

    def account_for_token(self, token: str) -> dict[str, object] | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT a.account_json
                    FROM v50_user_sessions s
                    JOIN v50_user_accounts a ON a.user_id = s.user_id
                    WHERE s.token_hash = %s AND s.revoked = false AND s.expires_at > now() AND a.active = true
                    LIMIT 1
                    """,
                    (_token_hash(token),),
                )
                row = cur.fetchone()
        return _strip_password(dict(row["account_json"])) if row else None

    def revoke_session(self, token: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE v50_user_sessions SET revoked = true, updated_at = now() WHERE token_hash = %s",
                    (_token_hash(token),),
                )

    def save_profile(self, *, user_id: str, birth_input: BirthInputCanonical, profile_id: str | None = None) -> dict[str, object]:
        from psycopg.types.json import Jsonb

        if profile_id and self.get_profile(user_id=user_id, profile_id=profile_id) is None:
            raise ProductStoreError("profile_not_found")
        profile = _account_profile_payload(
            user_id=user_id,
            birth_input=birth_input,
            profile_id=profile_id,
            persisted=True,
        )
        with self._connect() as conn:
            with conn.cursor() as cur:
                if not profile_id:
                    cur.execute(
                        """
                        SELECT profile_id FROM v50_bazi_profiles
                        WHERE user_id = %s
                          AND profile_fingerprint = %s
                          AND lower(trim(display_name)) = lower(trim(%s))
                          AND deleted = false
                        ORDER BY updated_at DESC LIMIT 1
                        """,
                        (user_id, profile["profile_fingerprint"], profile["display_name"]),
                    )
                    existing = cur.fetchone()
                    if existing:
                        profile["profile_id"] = str(existing[0])
                cur.execute("UPDATE v50_bazi_profiles SET is_default = false WHERE user_id = %s AND deleted = false", (user_id,))
                cur.execute(
                    """
                    INSERT INTO v50_bazi_profiles (
                        profile_id, identity_ref, user_id, profile_fingerprint, display_name, gender,
                        calendar_type, birth_date, birth_time, birth_location, timezone, pillars,
                        is_default, deleted, profile_json, updated_at
                    ) VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true, false, %s, now())
                    ON CONFLICT (profile_id) DO UPDATE SET
                        profile_fingerprint = EXCLUDED.profile_fingerprint,
                        display_name = EXCLUDED.display_name,
                        gender = EXCLUDED.gender,
                        calendar_type = EXCLUDED.calendar_type,
                        birth_date = EXCLUDED.birth_date,
                        birth_time = EXCLUDED.birth_time,
                        birth_location = EXCLUDED.birth_location,
                        timezone = EXCLUDED.timezone,
                        pillars = EXCLUDED.pillars,
                        is_default = true,
                        deleted = false,
                        profile_json = EXCLUDED.profile_json,
                        updated_at = now()
                    """,
                    (
                        profile["profile_id"], user_id, profile["profile_fingerprint"], profile["display_name"],
                        profile["gender"], profile["calendar_type"], profile["birth_date"], profile["birth_time"],
                        profile["birth_location"], profile["timezone"], Jsonb(profile["pillars"]), Jsonb(profile),
                    ),
                )
        return profile

    def list_profiles(self, *, user_id: str) -> list[dict[str, object]]:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT profile_json, is_default FROM v50_bazi_profiles
                    WHERE user_id = %s AND deleted = false
                    ORDER BY is_default DESC, updated_at DESC LIMIT 200
                    """,
                    (user_id,),
                )
                rows = cur.fetchall()
        return _deduplicate_profile_archive(
            [{**dict(row["profile_json"]), "is_default": bool(row["is_default"])} for row in rows]
        )

    def get_profile(self, *, user_id: str, profile_id: str) -> dict[str, object] | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT profile_json, is_default FROM v50_bazi_profiles
                    WHERE user_id = %s AND profile_id = %s AND deleted = false LIMIT 1
                    """,
                    (user_id, profile_id),
                )
                row = cur.fetchone()
        return {**dict(row["profile_json"]), "is_default": bool(row["is_default"])} if row else None

    def delete_profile(self, *, user_id: str, profile_id: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE v50_bazi_profiles SET deleted = true, is_default = false, updated_at = now()
                    WHERE user_id = %s AND profile_id = %s AND deleted = false
                    """,
                    (user_id, profile_id),
                )
                return cur.rowcount > 0


def build_product_store() -> ProductStore:
    database_url = os.environ.get("V50_DATABASE_URL", "").strip()
    if not database_url:
        return MemoryProductStore()
    return PostgresProductStore(database_url)


def birth_input_from_profile(profile: dict[str, object]) -> BirthInputCanonical:
    pillars = list(profile.get("pillars") or ["", "", "", ""])
    pillars.extend([""] * (4 - len(pillars)))
    return BirthInputCanonical(
        birth_input_id=str(profile.get("birth_input_id") or f"profile:{profile['profile_id']}"),
        name=str(profile["display_name"]),
        gender=str(profile.get("gender") or "unknown"),
        calendar_type=str(profile.get("calendar_type") or "solar"),
        birth_date=str(profile["birth_date"]),
        birth_time=str(profile["birth_time"]),
        birth_location=str(profile.get("birth_location") or ""),
        timezone=str(profile["timezone"]),
        lunar_leap_month=profile.get("lunar_leap_month"),
        true_solar_time_policy=str(profile.get("true_solar_time_policy") or "not_applied"),
        year_pillar=str(pillars[0]),
        month_pillar=str(pillars[1]),
        day_pillar=str(pillars[2]),
        hour_pillar=str(pillars[3]),
        input_quality=str(profile.get("input_quality") or "profile_archive"),
        warnings=list(profile.get("warnings") or []),
    )


def _validate_registration(email: str, password: str, display_name: str, role: str) -> tuple[str, str, str]:
    clean_email = email.strip().lower()
    clean_name = display_name.strip()
    clean_role = role.strip().lower()
    if "@" not in clean_email or clean_email.startswith("@") or clean_email.endswith("@"):
        raise ProductStoreError("invalid_email")
    if len(password) < 8:
        raise ProductStoreError("password_too_short")
    if not clean_name:
        raise ProductStoreError("display_name_required")
    if clean_role not in ACCOUNT_ROLES:
        raise ProductStoreError("unsupported_account_role")
    return clean_email, clean_name, clean_role


def _validate_admin(email: str, password: str, display_name: str) -> tuple[str, str]:
    clean_email = email.strip().lower()
    clean_name = display_name.strip()
    if "@" not in clean_email or clean_email.startswith("@") or clean_email.endswith("@"):
        raise ProductStoreError("invalid_email")
    if len(password) < 8:
        raise ProductStoreError("password_too_short")
    if not clean_name:
        raise ProductStoreError("display_name_required")
    return clean_email, clean_name


def _public_account(*, user_id: str, email: str, display_name: str, role: str) -> dict[str, object]:
    return {
        "user_id": user_id,
        "email": email,
        "display_name": display_name,
        "account_role": role,
        "role_status": "system_admin" if role == "admin" else "active" if role == "member" else "self_declared",
        "active": True,
        "storage": "v50_product_account",
        "boundary": "account_role_controls_workspace_access_not_mingli_judgment",
    }


def _hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PASSWORD_ITERATIONS)
    return salt, digest.hex()


def _verify_password(password: str, salt: str, expected_hash: str) -> bool:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PASSWORD_ITERATIONS).hex()
    return hmac.compare_digest(digest, expected_hash)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _strip_password(account: dict[str, object] | None) -> dict[str, object]:
    if not account:
        return {}
    projected = {
        key: value
        for key, value in account.items()
        if key not in {"password_hash", "password_salt"}
    }
    projected["role"] = str(projected.get("account_role") or "")
    return projected


def _account_profile_payload(
    *,
    user_id: str,
    birth_input: BirthInputCanonical,
    profile_id: str | None,
    persisted: bool,
) -> dict[str, object]:
    fingerprint_payload = {
        "gender": birth_input.gender.value,
        "calendar_type": birth_input.calendar_type.value,
        "birth_date": birth_input.birth_date,
        "birth_time": birth_input.birth_time,
        "birth_location": birth_input.birth_location.strip(),
        "timezone": birth_input.timezone,
        "lunar_leap_month": birth_input.lunar_leap_month,
    }
    fingerprint = hashlib.sha256(json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]
    resolved_id = profile_id or f"v50-profile-{uuid4().hex[:20]}"
    return {
        "profile_id": resolved_id,
        "user_id": user_id,
        "birth_input_id": birth_input.birth_input_id,
        "profile_fingerprint": fingerprint,
        "display_name": birth_input.name.strip(),
        "gender": birth_input.gender.value,
        "calendar_type": birth_input.calendar_type.value,
        "birth_date": birth_input.birth_date,
        "birth_time": birth_input.birth_time,
        "birth_location": birth_input.birth_location.strip(),
        "timezone": birth_input.timezone,
        "lunar_leap_month": birth_input.lunar_leap_month,
        "true_solar_time_policy": birth_input.true_solar_time_policy,
        "input_quality": birth_input.input_quality,
        "warnings": list(birth_input.warnings),
        "pillars": [birth_input.year_pillar, birth_input.month_pillar, birth_input.day_pillar, birth_input.hour_pillar],
        "is_default": True,
        "deleted": False,
        "persisted": persisted,
        "storage": "v50_postgresql" if persisted else "memory_only",
        "boundary": "profile_is_user_owned_birth_material_not_training_or_global_policy",
    }


def _deduplicate_profile_archive(values: list[dict[str, object]]) -> list[dict[str, object]]:
    """Hide old retry-created duplicates without deleting case-referenced rows."""

    unique: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for item in values:
        fingerprint = str(item.get("profile_fingerprint") or item.get("profile_id") or "")
        display_name = str(item.get("display_name") or "").strip().casefold()
        key = (fingerprint, display_name)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
