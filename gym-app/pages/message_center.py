"""
Admin-only Message Center.

Shows today's transactions (new member registrations + fee collections) so the
admin can personally verify each one and send the WhatsApp message from their
own phone via wa.me. Used as a fraud-control checkpoint: staff cannot send
messages on behalf of the business — only the admin can.

Receipt timestamps come from FeeRecord.created_at (the moment staff hit
"Record Payment" — set automatically by the SQLAlchemy default).
"""

import os
import streamlit as st
import urllib.parse
from datetime import date
import database as db
import styles


def _public_base_url() -> str:
    """Public HTTPS origin to embed in the WhatsApp message profile link.
    Prefers the production domain (REPLIT_DOMAINS, comma-separated), falls
    back to the dev domain, then localhost as a last resort.
    """
    prod = os.environ.get("REPLIT_DOMAINS", "")
    if prod:
        host = prod.split(",")[0].strip()
        if host:
            return f"https://{host}"
    dev = os.environ.get("REPLIT_DEV_DOMAIN", "")
    if dev:
        return f"https://{dev}"
    return "/"


def _profile_url(member_id: int) -> str:
    from profile_token import make_token
    return f"{_public_base_url()}/?profile={make_token(member_id)}"


def _build_receipt_message(member, gym_name: str, amount: float,
                           paid_at_str: str, expiry: str, profile_url: str) -> str:
    """Professional receipt template (used by 'Send Receipt' on fee rows)."""
    return (
        "--- 🧾 OFFICIAL GYM RECEIPT ---\n"
        f"Hello {member.full_name}!\n"
        f"Welcome to {gym_name}. Your payment has been received.\n\n"
        f"💰 Amount: PKR {amount:,.2f}\n"
        f"📅 Date/Time: {paid_at_str}\n"
        f"⏳ Expiry Date: {expiry}\n\n"
        f"🔗 View Digital Member Card: {profile_url}\n\n"
        "Stay fit and keep grinding! 💪\n"
        "----------------------------------"
    )


def _build_welcome_message(member, gym_name: str, profile_url: str) -> str:
    """Welcome template for newly-registered members. Includes the joining
    fee captured at registration (Member.fee_amount)."""
    fee = float(getattr(member, "fee_amount", 0) or 0)
    amount_str = f"PKR {fee:,.2f}" if fee > 0 else "—"
    return (
        "--- 🏋️ WELCOME TO THE GYM ---\n"
        f"Hello {member.full_name}!\n"
        f"Welcome to {gym_name}. Your membership is now active.\n\n"
        f"🆔 Member ID: {member.serial_number}\n"
        f"📦 Membership: {member.membership_type}\n"
        f"💰 Amount Paid: {amount_str}\n"
        f"⏳ Expiry Date: {member.expiry_date or '—'}\n\n"
        f"🔗 View Digital Member Card: {profile_url}\n\n"
        "Stay fit and keep grinding! 💪\n"
        "----------------------------------"
    )


# ── Helpers ───────────────────────────────────────────────────────────────────
def _format_pk_phone(raw) -> str:
    """Normalize a phone to digits-only with PK 92 country code.
    Returns '' if the input cannot be coerced into a valid PK mobile number.
    Valid shapes (after digit-only stripping): 03XXXXXXXXX, 3XXXXXXXXX,
    92XXXXXXXXXX, 0092XXXXXXXXXX.
    """
    if not raw:
        return ""
    digits = "".join(c for c in str(raw) if c.isdigit())
    if not digits:
        return ""
    if digits.startswith("0092"):       # 0092 300... → 92 300...
        digits = digits[2:]
    elif digits.startswith("0"):        # 0300...     → 92300...
        digits = "92" + digits[1:]
    elif digits.startswith("92"):       # already prefixed
        pass
    elif digits.startswith("3") and len(digits) == 10:  # 3001234567 → 923001234567
        digits = "92" + digits
    else:
        return ""                       # unknown shape — don't fabricate a link
    # PK mobile = 92 + 3XXXXXXXXX  (total 12 digits, must start with "923")
    if len(digits) != 12 or not digits.startswith("923"):
        return ""
    return digits


def _wa_link(phone: str, message: str) -> str:
    return f"https://wa.me/{_format_pk_phone(phone)}?text={urllib.parse.quote(message)}"


def _wa_action(phone: str, message: str, on_mark, key: str):
    """Render WhatsApp link button + 'Mark as Sent' button side-by-side.

    • `st.link_button` opens WhatsApp directly in a new tab (real anchor —
      no popup blocking on mobile or desktop).
    • `st.button("Mark as Sent")` runs `on_mark()` to flip whatsapp_sent=True
      in the DB and triggers a rerun so the row drops off the Pending list.

    Suppresses both buttons when the phone is invalid.
    """
    normalized = _format_pk_phone(phone)
    if not normalized:
        st.caption("⚠️ Invalid phone")
        return
    link = f"https://wa.me/{normalized}?text={urllib.parse.quote(message)}"
    a, b = st.columns([1, 1])
    with a:
        st.link_button("💬 Send WhatsApp", link, use_container_width=True)
    with b:
        if st.button("✓ Mark as Sent", key=key, use_container_width=True,
                     type="primary"):
            try:
                ok = on_mark()
            except Exception as e:
                st.error(f"Could not mark as sent: {e}")
                return
            if not ok:
                st.toast("Already marked as sent.", icon="ℹ️")
            st.rerun()


# ── Page ──────────────────────────────────────────────────────────────────────
def render(gym_id, role):
    if role != "admin":
        st.error("🚫 Message Center is restricted to administrators.")
        return

    styles.page_header(
        "📨", "Message Center",
        "Admin-only · Verify today's transactions and send WhatsApp messages from your own phone",
    )

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    today = date.today()
    today_str = str(today)
    gyms_by_id = {g.id: g for g in gyms}

    # ── Filter ────────────────────────────────────────────────────────────────
    f1, f2 = st.columns([2, 1])
    with f1:
        opts = {"🌐 All Gyms": None} | {f"🏋️ {g.name}": g.id for g in gyms}
        cur_label = next((f"🏋️ {g.name}" for g in gyms if g.id == gym_id), "🌐 All Gyms")
        chosen = st.selectbox(
            "Gym filter", list(opts.keys()),
            index=list(opts.keys()).index(cur_label),
            key="mc_gym_filter",
        )
        sel_gid = opts[chosen]
    with f2:
        st.metric("Date", today_str)

    # ── Today's data ──────────────────────────────────────────────────────────
    all_members = db.get_members(gym_id=sel_gid)
    # Only Pending rows: registered today AND not yet WhatsApp'd.
    today_members = [
        m for m in all_members
        if (m.join_date or "") == today_str and not getattr(m, "whatsapp_sent", False)
    ]

    # Use record-creation timestamp (when staff hit Record Payment) rather
    # than the form's payment_date — keeps backdated entries from hiding
    # from the admin's review window.
    today_fees = db.get_fee_records_created_today(gym_id=sel_gid)

    # ── Summary metrics ───────────────────────────────────────────────────────
    total_collected = sum(r.amount for r in today_fees)
    m1, m2, m3 = st.columns(3)
    m1.metric("New Members Today", len(today_members))
    m2.metric("Fees Collected Today", len(today_fees))
    m3.metric("Total Today", f"PKR {total_collected:,.2f}")

    st.divider()

    # ── Today's Fee Collections ───────────────────────────────────────────────
    st.subheader("💰 Today's Fee Collections")
    if not today_fees:
        st.info("No fees collected today yet.")
    else:
        # Clean 3-column layout: Member · Amount · Actions
        h = st.columns([2.5, 1.5, 3])
        for col, label in zip(h, ["Member", "Amount", "Actions"]):
            col.markdown(f"**{label}**")
        st.divider()

        for r in today_fees:
            mem = db.get_member(r.member_id)
            gym = gyms_by_id.get(r.gym_id)
            gym_name = gym.name if gym else "—"

            c = st.columns([2.5, 1.5, 3])
            with c[0]:
                st.write(f"**{mem.full_name if mem else '—'}**")
                st.caption(f"{gym_name} · Receipt {r.receipt_number or '—'}")
            with c[1]:
                st.write(f"**PKR {r.amount:,.2f}**")
            with c[2]:
                if mem and mem.phone:
                    paid_at_str = (
                        r.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                        if r.created_at else (r.payment_date or "—")
                    )
                    msg = _build_receipt_message(
                        member=mem,
                        gym_name=gym_name,
                        amount=r.amount,
                        paid_at_str=paid_at_str,
                        expiry=r.period_end or mem.expiry_date or "—",
                        profile_url=_profile_url(mem.id),
                    )
                    _wa_action(mem.phone, msg,
                               on_mark=lambda fid=r.id: db.mark_fee_whatsapp_sent(fid),
                               key=f"mc_fee_{r.id}")
                else:
                    st.caption("⚠️ No phone")
            st.divider()

    st.divider()

    # ── Today's New Members ───────────────────────────────────────────────────
    st.subheader("👥 Today's New Members")
    if not today_members:
        st.info("No new members registered today.")
    else:
        h = st.columns([2.5, 1.5, 3])
        for col, label in zip(h, ["Member", "Joining Fee", "Actions"]):
            col.markdown(f"**{label}**")
        st.divider()

        for m in today_members:
            gym = gyms_by_id.get(m.gym_id)
            gym_name = gym.name if gym else "—"

            c = st.columns([2.5, 1.5, 3])
            with c[0]:
                st.write(f"**{m.full_name}**")
                st.caption(f"{gym_name} · {m.membership_type} · {m.serial_number}")
            with c[1]:
                fee = float(m.fee_amount or 0)
                st.write(f"**PKR {fee:,.2f}**" if fee > 0 else "—")
            with c[2]:
                if m.phone:
                    msg = _build_welcome_message(
                        member=m,
                        gym_name=gym_name,
                        profile_url=_profile_url(m.id),
                    )
                    _wa_action(m.phone, msg,
                               on_mark=lambda mid=m.id: db.mark_member_whatsapp_sent(mid),
                               key=f"mc_mem_{m.id}")
                else:
                    st.caption("⚠️ No phone")
            st.divider()

    st.divider()
    st.caption(
        "🔒 **Fraud control:** Staff can only save data. All outbound WhatsApp "
        "messages are sent from the admin's phone via this page, after you "
        "personally verify each row."
    )
