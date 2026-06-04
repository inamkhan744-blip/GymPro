"""
Stateless HMAC tokens for public member-profile links.

Goal: prevent anonymous enumeration of `/profile?<id>` by requiring an
unguessable token tied to the member id. Uses the existing SESSION_SECRET so
no schema migration is needed.

Token format:  "<member_id>.<hmac16>"
e.g.           "42.9f3a1c8b2d4e5f60"
"""

from __future__ import annotations

import hashlib
import hmac
import os

_TOKEN_LEN = 16  # hex chars; 64 bits — far beyond what's enumerable


def _secret() -> bytes:
    """Return the signing secret. Fails closed if SESSION_SECRET is missing —
    a hardcoded fallback would let anyone forge valid public-profile tokens
    offline and re-enable anonymous member enumeration.
    """
    s = os.environ.get("SESSION_SECRET")
    if not s:
        raise RuntimeError(
            "SESSION_SECRET is not set. Public member-profile links require a "
            "server-side secret to prevent token forgery."
        )
    return s.encode()


def make_token(member_id: int) -> str:
    """Return an opaque token for the given member id."""
    sig = hmac.new(_secret(), str(int(member_id)).encode(), hashlib.sha256).hexdigest()
    return f"{int(member_id)}.{sig[:_TOKEN_LEN]}"


def parse_token(token: str) -> int | None:
    """Validate `token` and return the member id, or None if invalid."""
    if not token or "." not in token:
        return None
    raw_id, _, sig = token.partition(".")
    try:
        mid = int(raw_id)
    except (TypeError, ValueError):
        return None
    expected = hmac.new(_secret(), str(mid).encode(), hashlib.sha256).hexdigest()[:_TOKEN_LEN]
    if not hmac.compare_digest(sig, expected):
        return None
    return mid
