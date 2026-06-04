"""
WhatsApp Gateway — server-side, silent message sender.

Sends messages from a single configured admin WhatsApp number through a REST
gateway (Green-API by default). No `wa.me` links, no popups, no staff
intervention. The send happens in a background thread so the Streamlit UI is
never blocked.

Configuration (environment variables / Replit Secrets):
    GREEN_API_INSTANCE_ID   – your Green-API instance id (e.g. 1101234567)
    GREEN_API_TOKEN         – your Green-API API token

Optional override for any other gateway with the same shape:
    WHATSAPP_API_URL        – full URL template, must contain {instance} and
                              {token}, e.g.
                              "https://api.green-api.com/waInstance{instance}/sendMessage/{token}"

Usage:
    from whatsapp_gateway import send_background_whatsapp
    send_background_whatsapp("03001234567",
                             "Welcome Ali to PowerFit! ...")

The function returns immediately. Delivery is fire-and-forget; failures are
logged to the server console (and to the gym audit log if `database.add_audit`
is available) but never raised to the caller.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Optional

import requests

logger = logging.getLogger("whatsapp_gateway")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(_h)


# ── Phone normalization ────────────────────────────────────────────────────────
def _normalize_pk_phone(raw) -> str:
    """Return digits-only phone with Pakistan country code (92).
    Accepts any input; non-string / falsy values yield ''.
    """
    if not raw:
        return ""
    try:
        raw = str(raw)
    except Exception:
        return ""
    cleaned = "".join(c for c in raw if c.isdigit() or c == "+")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("00"):
        cleaned = cleaned[2:]
    if cleaned.startswith("0"):                    # 0300... → 92300...
        cleaned = "92" + cleaned[1:]
    elif cleaned.startswith("3") and len(cleaned) == 10:  # 300... → 92300...
        cleaned = "92" + cleaned
    elif not cleaned.startswith("92"):
        cleaned = "92" + cleaned
    return cleaned


# ── Gateway call ──────────────────────────────────────────────────────────────
def _send_via_green_api(phone: str, message: str) -> tuple[bool, str]:
    """POST to Green-API. Returns (ok, info). Never raises. Never leaks the token.

    Note on logging: `requests` exception strings frequently include the full
    request URL, which here contains the API token. We therefore log only the
    sanitized exception class name + a generic category — never `str(exc)`.
    """
    instance = os.environ.get("GREEN_API_INSTANCE_ID")
    token    = os.environ.get("GREEN_API_TOKEN")

    if not instance or not token:
        return False, "gateway not configured"

    url_tpl = os.environ.get(
        "WHATSAPP_API_URL",
        "https://api.green-api.com/waInstance{instance}/sendMessage/{token}",
    )
    try:
        url = url_tpl.format(instance=instance, token=token)
    except (KeyError, IndexError, ValueError):
        return False, "invalid WHATSAPP_API_URL template"

    payload = {
        "chatId": f"{phone}@c.us",   # Green-API chat-id format for personal numbers
        "message": message,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
    except requests.Timeout:
        return False, "network error: timeout"
    except requests.ConnectionError:
        return False, "network error: connection failed"
    except requests.RequestException as e:
        # Do NOT include str(e) — it can contain the URL with the token.
        return False, f"network error: {type(e).__name__}"
    except Exception as e:  # defensive — never let the worker thread crash
        return False, f"unexpected error: {type(e).__name__}"

    if r.status_code == 200:
        try:
            data = r.json()
            return True, f"sent (id={data.get('idMessage', '?')})"
        except ValueError:
            return True, "sent (no json body)"
    # Response body is from the API server, not from `requests`, so it does
    # not contain our outbound URL/token. Still trimmed defensively.
    body_snip = (r.text or "")[:200].replace(token, "***")
    return False, f"HTTP {r.status_code}: {body_snip}"


# ── Public API ────────────────────────────────────────────────────────────────
def send_background_whatsapp(number: str, message: str) -> None:
    """
    Fire-and-forget. Sends `message` to `number` from the server's configured
    admin WhatsApp account. Never raises, never blocks.

    Args:
        number:  Raw phone in any format; normalized to 92XXXXXXXXXX.
        message: Plain text WhatsApp message.
    """
    try:
        phone = _normalize_pk_phone(number)
        if not phone or len(phone) < 11:
            logger.warning("send_background_whatsapp: invalid phone (len=%d)", len(phone))
            return
        msg = "" if message is None else str(message)
    except Exception as e:
        logger.error("send_background_whatsapp: pre-flight error: %s", type(e).__name__)
        return

    def _worker() -> None:
        try:
            ok, info = _send_via_green_api(phone, msg)
            if ok:
                logger.info("WhatsApp → %s OK (%s)", phone, info)
            else:
                logger.error("WhatsApp → %s FAILED: %s", phone, info)
        except Exception as e:  # final safety net
            logger.error("WhatsApp → %s worker crashed: %s", phone, type(e).__name__)

    try:
        threading.Thread(target=_worker, daemon=True, name="wa-send").start()
    except Exception as e:
        logger.error("send_background_whatsapp: thread launch failed: %s", type(e).__name__)


def gateway_configured() -> bool:
    """True when the gateway env vars are present."""
    return bool(os.environ.get("GREEN_API_INSTANCE_ID") and os.environ.get("GREEN_API_TOKEN"))
