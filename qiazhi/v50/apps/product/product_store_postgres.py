from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from core.contracts import BirthInputCanonical
from product.database_schema import check_product_database_schema
from product.product_account import (
    hash_password,
    public_account,
    strip_password,
    token_hash,
    validate_admin,
    validate_registration,
    verify_password,
)
from product.product_profile import account_profile_payload, deduplicate_profile_archive
from product.product_store_contracts import ProductStoreError


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

        clean_email, clean_name, clean_role = validate_registration(email, password, display_name, role)
        user_id = f"v50-user-{uuid4().hex[:20]}"
        salt, password_hash = hash_password(password)
        account = public_account(user_id=user_id, email=clean_email, display_name=clean_name, role=clean_role)
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
        return strip_password(account)

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
        if not row or not verify_password(password, row["password_salt"], row["password_hash"]):
            return None
        return strip_password(dict(row["account_json"]))

    def ensure_admin_account(self, *, email: str, password: str, display_name: str) -> dict[str, object]:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        clean_email, clean_name = validate_admin(email, password, display_name)
        salt, password_hash = hash_password(password)
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT user_id FROM v50_user_accounts WHERE email = %s LIMIT 1", (clean_email,))
                existing = cur.fetchone()
                user_id = str(existing["user_id"]) if existing else "v50-admin-primary"
                if not existing:
                    cur.execute("SELECT 1 FROM v50_user_accounts WHERE user_id = %s", (user_id,))
                    if cur.fetchone():
                        user_id = f"v50-admin-{uuid4().hex[:20]}"
                account = public_account(
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
        return strip_password(account)

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
                    (f"v50-session-{uuid4().hex[:20]}", user_id, token_hash(token), expires_at),
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
                    (token_hash(token),),
                )
                row = cur.fetchone()
        return strip_password(dict(row["account_json"])) if row else None

    def revoke_session(self, token: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE v50_user_sessions SET revoked = true, updated_at = now() WHERE token_hash = %s",
                    (token_hash(token),),
                )

    def save_profile(self, *, user_id: str, birth_input: BirthInputCanonical, profile_id: str | None = None) -> dict[str, object]:
        from psycopg.types.json import Jsonb

        if profile_id and self.get_profile(user_id=user_id, profile_id=profile_id) is None:
            raise ProductStoreError("profile_not_found")
        profile = account_profile_payload(
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
        return deduplicate_profile_archive(
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
