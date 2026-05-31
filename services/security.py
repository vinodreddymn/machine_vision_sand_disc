"""Security utilities: password hashing, JWT (HS256), and RBAC helpers.

Design goals:
- No breaking changes: auth is optional and disabled by default.
- No extra deps: uses stdlib crypto (pbkdf2 + hmac) for hashing and JWT signing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + pad).encode("ascii"))


def hash_password(password: str, *, rounds: int = 150_000) -> str:
    """Return a salted PBKDF2 hash string."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds, dklen=32)
    return f"pbkdf2_sha256${rounds}${_b64url_encode(salt)}${_b64url_encode(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds_s, salt_s, hash_s = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        rounds = int(rounds_s)
        salt = _b64url_decode(salt_s)
        expected = _b64url_decode(hash_s)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds, dklen=len(expected))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


@dataclass(frozen=True, slots=True)
class JwtConfig:
    secret: bytes
    issuer: str
    exp_minutes: int


def load_jwt_config(security_cfg: dict[str, Any]) -> JwtConfig:
    env_key = str(security_cfg.get("jwt_secret_env", "DISK_VISION_JWT_SECRET"))
    secret = os.getenv(env_key, "")
    if not secret:
        # Generate a process-local secret if not set. This keeps dev usable while
        # encouraging explicit config in production.
        secret = secrets.token_urlsafe(48)
    return JwtConfig(secret=secret.encode("utf-8"), issuer=str(security_cfg.get("jwt_issuer", "diskvision")), exp_minutes=int(security_cfg.get("jwt_exp_minutes", 720)))


def encode_jwt(payload: dict[str, Any], *, cfg: JwtConfig) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    body = dict(payload)
    body.setdefault("iat", now)
    body.setdefault("iss", cfg.issuer)
    body.setdefault("exp", now + int(cfg.exp_minutes) * 60)
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = hmac.new(cfg.secret, signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(sig)}"


def decode_jwt(token: str, *, cfg: JwtConfig) -> dict[str, Any] | None:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".", 2)
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        sig = _b64url_decode(sig_b64)
        expected = hmac.new(cfg.secret, signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        now = int(time.time())
        if payload.get("iss") != cfg.issuer:
            return None
        if int(payload.get("exp", 0)) < now:
            return None
        return payload
    except Exception:
        return None


ROLE_OPERATOR = "OPERATOR"
ROLE_SUPERVISOR = "SUPERVISOR"
ROLE_ADMIN = "ADMIN"


def role_allows(role: str, required: str) -> bool:
    order = {ROLE_OPERATOR: 1, ROLE_SUPERVISOR: 2, ROLE_ADMIN: 3}
    return order.get(role, 0) >= order.get(required, 99)

