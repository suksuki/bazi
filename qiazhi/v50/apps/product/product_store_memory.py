from __future__ import annotations

import secrets
from uuid import uuid4

from core.contracts import BirthInputCanonical
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


class MemoryProductStore:
    persistent = False
    storage_name = "memory_only"

    def __init__(self) -> None:
        self._accounts: dict[str, dict[str, object]] = {}
        self._accounts_by_email: dict[str, str] = {}
        self._sessions: dict[str, str] = {}
        self._profiles: dict[str, dict[str, dict[str, object]]] = {}

    def register_account(self, *, email: str, password: str, display_name: str, role: str) -> dict[str, object]:
        clean_email, clean_name, clean_role = validate_registration(email, password, display_name, role)
        if clean_email in self._accounts_by_email:
            raise ProductStoreError("email_already_registered")
        user_id = f"v50-user-{uuid4().hex[:20]}"
        salt, password_hash = hash_password(password)
        internal = {
            **public_account(user_id=user_id, email=clean_email, display_name=clean_name, role=clean_role),
            "password_salt": salt,
            "password_hash": password_hash,
        }
        self._accounts[user_id] = internal
        self._accounts_by_email[clean_email] = user_id
        return strip_password(internal)

    def authenticate(self, *, email: str, password: str) -> dict[str, object] | None:
        user_id = self._accounts_by_email.get(email.strip().lower())
        account = self._accounts.get(user_id or "")
        if not account or not verify_password(password, str(account["password_salt"]), str(account["password_hash"])):
            return None
        return strip_password(account)

    def ensure_admin_account(self, *, email: str, password: str, display_name: str) -> dict[str, object]:
        clean_email, clean_name = validate_admin(email, password, display_name)
        for account in self._accounts.values():
            if account.get("account_role") == "admin" and account.get("email") != clean_email:
                account["active"] = False
        user_id = self._accounts_by_email.get(clean_email) or "v50-admin-primary"
        salt, password_hash = hash_password(password)
        internal = {
            **public_account(user_id=user_id, email=clean_email, display_name=clean_name, role="admin"),
            "password_salt": salt,
            "password_hash": password_hash,
        }
        self._accounts[user_id] = internal
        self._accounts_by_email[clean_email] = user_id
        return strip_password(internal)

    def create_session(self, *, user_id: str) -> str:
        token = secrets.token_urlsafe(36)
        self._sessions[token_hash(token)] = user_id
        return token

    def account_for_token(self, token: str) -> dict[str, object] | None:
        account = self._accounts.get(self._sessions.get(token_hash(token), ""))
        return strip_password(account) if account else None

    def revoke_session(self, token: str) -> None:
        self._sessions.pop(token_hash(token), None)

    def save_profile(self, *, user_id: str, birth_input: BirthInputCanonical, profile_id: str | None = None) -> dict[str, object]:
        profiles = self._profiles.setdefault(user_id, {})
        if profile_id and profile_id not in profiles:
            raise ProductStoreError("profile_not_found")
        profile = account_profile_payload(
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
        return deduplicate_profile_archive(values)

    def get_profile(self, *, user_id: str, profile_id: str) -> dict[str, object] | None:
        value = self._profiles.get(user_id, {}).get(profile_id)
        return dict(value) if value and not value.get("deleted") else None

    def delete_profile(self, *, user_id: str, profile_id: str) -> bool:
        profile = self._profiles.get(user_id, {}).get(profile_id)
        if not profile:
            return False
        profile["deleted"] = True
        return True
