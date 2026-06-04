"""QR code generation for member identity cards.

Generates a PNG of the member's `serial_number` (already unique per gym
and human-readable, e.g. PF-00001). Used by the membership card, public
profile, and the QR-scan attendance flow.
"""
from __future__ import annotations
import io
import qrcode
from qrcode.constants import ERROR_CORRECT_M


def member_qr_png(payload: str, box_size: int = 8, border: int = 2) -> bytes:
    """Return a PNG byte string encoding `payload` as a QR code.

    `payload` is the member's serial_number — that's what a USB scanner
    will type into the Daily Attendance input. Error correction is set
    to M (~15%) so the code remains readable when reprinted at small
    sizes on a membership card.
    """
    qr = qrcode.QRCode(
        version=None,                  # auto-fit smallest version
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(payload or "")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
