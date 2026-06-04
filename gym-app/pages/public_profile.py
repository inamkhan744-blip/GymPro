"""
Public Member Profile — accessible without login.

Reached via `?profile=<member_id>` in the URL. Renders a card-style digital
membership view (photo, name, gym, type, join/expiry, status). Sensitive
fields (phone, email, internal notes) are intentionally NOT shown.
"""

import html
import os
import streamlit as st
import database as db
import styles


def _esc(s) -> str:
    """Escape user-controlled text before embedding in unsafe_allow_html blocks."""
    return html.escape(str(s)) if s is not None else ""


def render(member_id: int):
    styles.inject_css()
    m = db.get_member(member_id) if member_id and member_id > 0 else None
    if not m:
        _not_found()
        return

    gym = next((g for g in db.get_all_gyms() if g.id == m.gym_id), None)
    gym_name = _esc(gym.name) if gym else "—"
    safe_full_name = _esc(m.full_name)
    safe_serial    = _esc(m.serial_number)
    safe_status    = _esc(m.status or "Active")
    safe_mtype     = _esc(m.membership_type or "—")
    safe_join      = _esc(m.join_date or "—")
    safe_expiry    = _esc(m.expiry_date or "—")

    # Status colour
    status = (m.status or "Active").lower()
    status_colors = {"active": "#10B981", "inactive": "#64748B",
                     "suspended": "#EF4444", "frozen": "#3B82F6"}
    chip_bg = status_colors.get(status, "#7C3AED")

    # Centered card layout
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            f"""
            <div style="background:linear-gradient(160deg,#1E293B 0%,#0F172A 100%);
                        border:1px solid #334155;border-radius:18px;padding:1.8rem;
                        box-shadow:0 25px 50px rgba(0,0,0,0.45);margin-top:2rem;">
              <div style="text-align:center;margin-bottom:0.5rem;">
                <div style="font-size:0.7rem;color:#7C3AED;letter-spacing:0.18em;
                            text-transform:uppercase;font-weight:700;">
                  🏋️ Digital Membership Card
                </div>
                <div style="font-size:1.05rem;color:#A78BFA;font-weight:700;
                            margin-top:0.2rem;">{gym_name}</div>
              </div>
            """,
            unsafe_allow_html=True,
        )

        # Photo
        photo_path = m.photo_path
        if photo_path and not os.path.isabs(photo_path):
            photo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                      photo_path) if not os.path.exists(photo_path) else photo_path
        if photo_path and os.path.exists(photo_path):
            pc1, pc2, pc3 = st.columns([1, 2, 1])
            with pc2:
                st.image(photo_path, width=220)
        else:
            st.markdown(
                """<div style="text-align:center;font-size:5rem;margin:1rem 0;">👤</div>""",
                unsafe_allow_html=True,
            )

        # Name + serial + status
        st.markdown(
            f"""
            <div style="text-align:center;margin-top:0.5rem;">
              <div style="font-size:1.6rem;font-weight:800;color:#F1F5F9;">
                {safe_full_name}
              </div>
              <div style="font-family:monospace;color:#94A3B8;font-size:0.95rem;
                          margin-top:0.2rem;">{safe_serial}</div>
              <div style="margin-top:0.6rem;">
                <span style="background:{chip_bg};color:white;padding:0.25rem 0.85rem;
                             border-radius:999px;font-size:0.75rem;font-weight:700;
                             text-transform:uppercase;letter-spacing:0.08em;">
                  {safe_status}
                </span>
              </div>
            </div>
            <hr style="border-color:#334155;margin:1.4rem 0 1rem;">
            """,
            unsafe_allow_html=True,
        )

        # QR code — same one used by the gym's attendance scanner.
        try:
            from qr_utils import member_qr_png
            qr_png = member_qr_png(m.serial_number, box_size=6, border=2)
            qc1, qc2, qc3 = st.columns([1, 2, 1])
            with qc2:
                st.image(qr_png, width=180,
                         caption=f"Show at gate · {m.serial_number}")
        except Exception:
            pass

        # Detail rows
        rows = [
            ("Membership Type", safe_mtype),
            ("Member Since",    safe_join),
            ("Valid Until",     safe_expiry),
        ]
        for label, value in rows:
            st.markdown(
                f"""<div style="display:flex;justify-content:space-between;
                              padding:0.45rem 0;border-bottom:1px solid #1E293B;">
                  <span style="color:#94A3B8;font-size:0.85rem;">{label}</span>
                  <span style="color:#F1F5F9;font-weight:600;">{value}</span>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown(
            """
              <div style="text-align:center;margin-top:1.4rem;color:#64748B;
                          font-size:0.7rem;letter-spacing:0.1em;text-transform:uppercase;">
                Verified by GymPro · Keep grinding 💪
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _not_found():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            """
            <div style="text-align:center;margin-top:5rem;padding:2rem;
                        background:#1E293B;border-radius:14px;border:1px solid #334155;">
              <div style="font-size:3rem;">🔍</div>
              <div style="font-size:1.3rem;font-weight:700;color:#F1F5F9;margin-top:0.5rem;">
                Member Not Found
              </div>
              <div style="color:#94A3B8;margin-top:0.5rem;">
                This profile link is invalid or the member has been removed.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
