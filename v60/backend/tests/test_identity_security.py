import hashlib

from abu_v60.identity.security import PBKDF2_SHA256_310K, verify_password


def test_v50_compatible_password_verifier_is_explicitly_bounded() -> None:
    password = "local-test-password"
    salt = "00112233445566778899aabbccddeeff"
    expected_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt),
        310_000,
    ).hex()

    assert verify_password(
        password=password,
        scheme=PBKDF2_SHA256_310K,
        expected_hash=expected_hash,
        salt=salt,
    )
    assert not verify_password(
        password="wrong",
        scheme=PBKDF2_SHA256_310K,
        expected_hash=expected_hash,
        salt=salt,
    )
    assert not verify_password(
        password=password,
        scheme="unknown",
        expected_hash=expected_hash,
        salt=salt,
    )
