from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.identity.contracts import AccountView, ProfileView, SessionView
from abu_v60.identity.security import hash_session_token, verify_password
from abu_v60.provenance import stable_ref

SESSION_TTL = timedelta(days=7)


class InvalidCredentialsError(ValueError):
    pass


class IdentityService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def login(self, *, email: str, password: str) -> tuple[str, SessionView]:
        normalized_email = email.strip().lower()
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    SELECT account_ref, email, display_name, account_role, active,
                           password_scheme, password_hash, password_salt
                    FROM identity.accounts
                    WHERE lower(email) = :email
                    """
                    ),
                    {"email": normalized_email},
                )
                .mappings()
                .one_or_none()
            )
            if row is None or not row["active"]:
                raise InvalidCredentialsError("invalid_credentials")
            if not verify_password(
                password=password,
                scheme=row["password_scheme"],
                expected_hash=row["password_hash"],
                salt=row["password_salt"],
            ):
                raise InvalidCredentialsError("invalid_credentials")

            token = secrets.token_urlsafe(40)
            token_hash = hash_session_token(token)
            session_ref = stable_ref("v60-session", token_hash)
            expires_at = datetime.now(UTC) + SESSION_TTL
            connection.execute(
                text(
                    """
                    INSERT INTO identity.sessions
                        (session_ref, account_ref, token_hash, expires_at)
                    VALUES
                        (:session_ref, :account_ref, :token_hash, :expires_at)
                    """
                ),
                {
                    "session_ref": session_ref,
                    "account_ref": row["account_ref"],
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                },
            )
        return token, self.session_for_token(token)

    def session_for_token(self, token: str) -> SessionView:
        token_hash = hash_session_token(token)
        with self._engine.connect() as connection:
            account = (
                connection.execute(
                    text(
                        """
                    SELECT a.account_ref, a.email, a.display_name, a.account_role
                    FROM identity.sessions AS s
                    JOIN identity.accounts AS a ON a.account_ref = s.account_ref
                    WHERE s.token_hash = :token_hash
                      AND s.revoked_at IS NULL
                      AND s.expires_at > now()
                      AND a.active = true
                    """
                    ),
                    {"token_hash": token_hash},
                )
                .mappings()
                .one_or_none()
            )
            if account is None:
                raise InvalidCredentialsError("invalid_session")
            profiles = (
                connection.execute(
                    text(
                        """
                    SELECT profile_ref, display_name, gender, calendar_type,
                           birth_date, birth_time, birth_location, timezone
                    FROM identity.profiles
                    WHERE account_ref = :account_ref AND active = true
                    ORDER BY created_at, profile_ref
                    """
                    ),
                    {"account_ref": account["account_ref"]},
                )
                .mappings()
                .all()
            )
        return SessionView(
            account=AccountView(**dict(account)),
            profiles=[ProfileView(**dict(profile)) for profile in profiles],
        )

    def logout(self, token: str) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE identity.sessions
                    SET revoked_at = COALESCE(revoked_at, now())
                    WHERE token_hash = :token_hash
                    """
                ),
                {"token_hash": hash_session_token(token)},
            )
