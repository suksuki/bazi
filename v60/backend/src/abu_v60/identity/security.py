from __future__ import annotations

import hashlib
import hmac

PBKDF2_SHA256_310K = "pbkdf2_sha256_310000_v50_compat"


def verify_password(*, password: str, scheme: str, expected_hash: str, salt: str) -> bool:
    if scheme != PBKDF2_SHA256_310K:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        310_000,
    ).hex()
    return hmac.compare_digest(candidate, expected_hash)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
