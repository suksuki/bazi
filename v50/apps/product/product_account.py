from __future__ import annotations

import hashlib
import hmac
import secrets

from product.product_store_contracts import ProductStoreError


ACCOUNT_ROLES = {"member", "practitioner", "research_master"}
PASSWORD_ITERATIONS = 310_000


def validate_registration(email: str, password: str, display_name: str, role: str) -> tuple[str, str, str]:
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


def validate_admin(email: str, password: str, display_name: str) -> tuple[str, str]:
    clean_email = email.strip().lower()
    clean_name = display_name.strip()
    if "@" not in clean_email or clean_email.startswith("@") or clean_email.endswith("@"):
        raise ProductStoreError("invalid_email")
    if len(password) < 8:
        raise ProductStoreError("password_too_short")
    if not clean_name:
        raise ProductStoreError("display_name_required")
    return clean_email, clean_name


def public_account(*, user_id: str, email: str, display_name: str, role: str) -> dict[str, object]:
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


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PASSWORD_ITERATIONS)
    return salt, digest.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PASSWORD_ITERATIONS).hex()
    return hmac.compare_digest(digest, expected_hash)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def strip_password(account: dict[str, object] | None) -> dict[str, object]:
    if not account:
        return {}
    projected = {
        key: value
        for key, value in account.items()
        if key not in {"password_hash", "password_salt"}
    }
    projected["role"] = str(projected.get("account_role") or "")
    return projected
