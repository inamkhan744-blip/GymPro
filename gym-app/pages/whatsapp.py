import streamlit as st
import pandas as pd
import io
from datetime import date
import urllib.parse
import database as db
import styles


DEFAULT_TEMPLATE = (
    "Hello {name}, this is a reminder from {gym} that your membership expires on {expiry}. "
    "Please renew to continue enjoying our services. Thank you!"
)


def make_wa_link(phone: str, message: str) -> str:
    clean = "".join(c for c in phone if c.isdigit() or c == "+")
    if clean.startswith("0"):
        clean = "+92" + clean[1:]
    return f"https://wa.me/{clean}?text={urllib.parse.quote(message)}"


def wa_button(link: str, label: str = "💬 Send WhatsApp") -> str:
    return (
        f'<a href="{link}" target="_blank" style="display:inline-block;'
        f'background:#25D366;color:white;padding:0.4rem 1rem;border-radius:8px;'
        f'font-weight:700;text-decoration:none;font-size:0.85rem;">{label}</a>'
    )


def render(gym_id, role):
    styles.page_header("💬", "WhatsApp Automation",
                       "Fee reminders · Absentee alerts · Birthdays · Streak warnings")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    tab_expiry, tab_absent, tab_birthday, tab_streak = st.tabs([
        "⏰ Fee Expiry Reminders",
        "🚶 Absentee Alerts",
        "🎂 Birthday Wishes",
        "🔥 Streak Warnings",
    ])

    # ── Shared gym selector ────────────────────────────────────────────────────
    def gym_selector(tab_key):
        if gym_id:
            return gym_id
        else:
            opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen = st.selectbox("Gym", list(opts.keys()), key=f"wa_gym_{tab_key}")
            return opts[chosen]

    # ── Settings in sidebar-style expander ─────────────────────────────────────
    with st.expander("⚙️ WhatsApp Message Settings", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            days_threshold = st.number_input(
                "Send 5-Day Advance Reminder — days ahead",
                min_value=1, max_value=60, value=5, step=1, key="wa_days_threshold",
            )
            absent_days = st.number_input(
                "Absentee alert after (days)",
                min_value=1, max_value=30, value=3, step=1, key="wa_absent_days",
            )
        with c2:
            template = st.text_area(
                "Fee Reminder Template",
                value=DEFAULT_TEMPLATE, height=100, key="wa_template",
                help="Placeholders: {name} {gym} {expiry} {days}",
            )
        st.caption("💡 Note: WhatsApp links open WhatsApp Web/App for one-click sending from your device.")

    st.divider()

    # ── Tab 1: Fee Expiry Reminders ────────────────────────────────────────────
    with tab_expiry:
        sel_gid_exp = gym_selector("expiry")
        expiring = db.get_expiring_members(days=int(days_threshold), gym_id=sel_gid_exp)

        if not expiring:
            st.success(f"✅ No members expiring within {int(days_threshold)} days!")
        else:
            urgent = sum(1 for _, d in expiring if d <= 2)
            ac1, ac2, ac3 = st.columns(3)
            ac1.metric("To Notify", len(expiring))
            ac2.metric("Urgent (≤ 2 days)", urgent)
            ac3.metric("Upcoming", len(expiring) - urgent)
            st.divider()

            rows = []
            for idx, (m, days_left) in enumerate(sorted(expiring, key=lambda x: x[1])):
                gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                tip = db.get_health_tip(m.id)
                msg = template.format(name=m.full_name, gym=gym_name,
                                      expiry=m.expiry_date, days=days_left)
                full_msg = f"{msg}\n\n{tip}"
                phone = m.phone or ""
                urgency = "🔴" if days_left <= 2 else "🟡" if days_left <= 4 else "🟢"
                wa_link = make_wa_link(phone, full_msg) if phone else None

                with st.expander(
                    f"{urgency} {m.full_name} — {days_left} day(s) left | {gym_name}",
                    expanded=days_left <= 2,
                ):
                    e1, e2 = st.columns([3, 1])
                    with e1:
                        st.markdown(f"**Serial:** `{m.serial_number}` · **Phone:** {phone or '—'}")
                        st.markdown(f"**Membership:** {m.membership_type} · **Fee:** PKR {m.fee_amount:,.0f}")
                        st.info(full_msg)
                    with e2:
                        if wa_link:
                            st.markdown(wa_button(wa_link, "💬 Send via WhatsApp"),
                                        unsafe_allow_html=True)
                        else:
                            st.warning("No phone")

                rows.append({
                    "Urgency": urgency, "Name": m.full_name,
                    "Phone": phone or "—", "Gym": gym_name,
                    "Expires": m.expiry_date, "Days Left": days_left,
                })

            st.divider()
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            buf = io.StringIO(); df.to_csv(buf, index=False)
            st.download_button("⬇️ Export List", data=buf.getvalue().encode(),
                               file_name=f"fee_reminders_{date.today()}.csv",
                               mime="text/csv", key="wa_exp_export")

    # ── Tab 2: Absentee Alerts ─────────────────────────────────────────────────
    with tab_absent:
        sel_gid_abs = gym_selector("absent")
        st.markdown(f"**Members absent for more than {int(absent_days)} consecutive days**")
        absent_members = db.get_absent_members(days=int(absent_days), gym_id=sel_gid_abs)

        if not absent_members:
            st.success(f"✅ All active members attended within the last {int(absent_days)} days!")
        else:
            st.warning(f"⚠️ {len(absent_members)} member(s) have not checked in recently")
            st.divider()
            for idx, m in enumerate(absent_members):
                gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                tip = db.get_health_tip(m.id + 3)
                phone = m.phone or ""
                msg = (
                    f"Hi {m.full_name}! 🌟 We miss you at {gym_name}!\n\n"
                    f"It's been a few days since we saw you — your fitness journey matters to us. "
                    f"Come back and keep up the great work! 💪\n\n"
                    f"{tip}\n\n"
                    f"We're here to support you. See you soon! 🏋️"
                )
                wa_link = make_wa_link(phone, msg) if phone else None
                with st.expander(f"🚶 {m.full_name} — {gym_name} | {phone or 'No phone'}"):
                    ab1, ab2 = st.columns([3, 1])
                    with ab1:
                        st.markdown(f"**Serial:** `{m.serial_number}` · **Membership:** {m.membership_type}")
                        st.info(msg)
                    with ab2:
                        if wa_link:
                            st.markdown(wa_button(wa_link, "💬 Send Absentee Alert"),
                                        unsafe_allow_html=True)
                        else:
                            st.warning("No phone")

    # ── Tab 3: Birthday Wishes ─────────────────────────────────────────────────
    with tab_birthday:
        sel_gid_bday = gym_selector("birthday")
        bday_ahead = st.number_input("Show birthdays within (days)", min_value=1,
                                      max_value=30, value=7, step=1, key="wa_bday_days")
        birthday_members = db.get_birthday_members(days_ahead=int(bday_ahead),
                                                    gym_id=sel_gid_bday)

        if not birthday_members:
            st.info(f"No birthdays in the next {int(bday_ahead)} days.")
        else:
            st.success(f"🎂 {len(birthday_members)} birthday(s) upcoming!")
            st.divider()
            for m, days_to_bday in birthday_members:
                gym_name = next((g.name for g in gyms if g.id == m.gym_id), "Gym")
                phone = m.phone or ""
                bday_label = "Today! 🎉" if days_to_bday == 0 else f"in {days_to_bday} day(s)"
                msg = (
                    f"🎂 Happy Birthday {m.full_name}! 🎉\n\n"
                    f"The entire {gym_name} family wishes you a wonderful birthday! "
                    f"As a special gift, please come in for a complimentary session today.\n\n"
                    f"🎁 Special Offer: Show this message for your birthday discount!\n\n"
                    f"Keep staying fit and healthy — you inspire us all! 💪🌟\n\n"
                    f"With love,\n{gym_name} Team 🏋️"
                )
                wa_link = make_wa_link(phone, msg) if phone else None
                with st.expander(
                    f"🎂 {m.full_name} — Birthday {bday_label} | DOB: {m.dob}",
                    expanded=days_to_bday == 0,
                ):
                    bd1, bd2 = st.columns([3, 1])
                    with bd1:
                        st.markdown(f"**Serial:** `{m.serial_number}` · **Gym:** {gym_name}")
                        st.info(msg)
                    with bd2:
                        if wa_link:
                            st.markdown(wa_button(wa_link, "🎂 Send Birthday Wish"),
                                        unsafe_allow_html=True)
                        else:
                            st.warning("No phone")

    # ── Tab 4: Streak Warnings ─────────────────────────────────────────────────
    with tab_streak:
        sel_gid_str = gym_selector("streak")
        st.markdown("**Workout Streak Leaderboard & Streak Break Warnings**")

        leaderboard = db.get_attendance_leaderboard(gym_id=sel_gid_str, limit=20)

        if not leaderboard:
            st.info("No attendance data yet.")
        else:
            # Top members
            lb_rows = []
            for rank, entry in enumerate(leaderboard, 1):
                m = entry["member"]
                streak = entry["streak"]
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                lb_rows.append({
                    "Rank": medal,
                    "Name": m.full_name,
                    "Serial": m.serial_number,
                    "This Month": entry["count"],
                    "Current Streak": f"🔥 {streak}" if streak >= 3 else streak,
                    "Status": m.status,
                })
            st.dataframe(pd.DataFrame(lb_rows), use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("**🔥 Send Streak Encouragement / Warning**")
            members_all = db.get_members(gym_id=sel_gid_str, status="Active")
            if members_all:
                mem_opts_str = {f"{m.serial_number} — {m.full_name}": m for m in members_all}
                sel_str_label = st.selectbox("Select member", list(mem_opts_str.keys()),
                                             key="str_member_sel")
                sel_str_m = mem_opts_str[sel_str_label]
                streak_count = db.get_member_streak(sel_str_m.id)
                gym_name = next((g.name for g in gyms if g.id == sel_str_m.gym_id), "Gym")
                tip = db.get_health_tip(sel_str_m.id + 7)
                phone = sel_str_m.phone or ""

                if streak_count >= 7:
                    msg = (
                        f"🔥 Amazing {sel_str_m.full_name}! You have a {streak_count}-day workout streak!\n\n"
                        f"You're absolutely crushing it at {gym_name}! Don't stop now — "
                        f"you're building a habit that will change your life! 🏆\n\n"
                        f"{tip}\n\n"
                        f"Keep going — your {gym_name} team is rooting for you! 💪"
                    )
                    label = "🔥 Send Streak Celebration"
                elif streak_count >= 3:
                    msg = (
                        f"💪 Great work {sel_str_m.full_name}! You're on a {streak_count}-day streak!\n\n"
                        f"You're doing fantastic at {gym_name}. Keep this momentum going — "
                        f"consistency is the key to transformation! 🎯\n\n"
                        f"{tip}\n\n"
                        f"See you tomorrow! 🏋️"
                    )
                    label = "💪 Send Streak Encouragement"
                else:
                    msg = (
                        f"Hi {sel_str_m.full_name}! ⚠️ Your workout streak is at risk!\n\n"
                        f"Don't let your progress slip — you've worked so hard at {gym_name}. "
                        f"Come in today and restart your streak! Every champion shows up even "
                        f"when they don't feel like it. 🦁\n\n"
                        f"{tip}\n\n"
                        f"We're waiting for you! 🏋️"
                    )
                    label = "⚠️ Send Streak Warning"

                st.markdown(
                    styles.metric_card("Current Streak", f"🔥 {streak_count} days",
                                       sel_str_m.full_name, "purple"),
                    unsafe_allow_html=True,
                )
                st.info(msg)
                if phone:
                    wa_link = make_wa_link(phone, msg)
                    st.markdown(wa_button(wa_link, label), unsafe_allow_html=True)
                else:
                    st.warning("No phone number on file.")

        # Bulk leaderboard WhatsApp (all members)
        if leaderboard and len(leaderboard) >= 3:
            st.divider()
            st.markdown("**📢 Share Weekly Leaderboard with All Members**")
            gym_name_lb = next((g.name for g in gyms if g.id == sel_gid_str), "GymPro")
            lb_text = f"🏆 *{gym_name_lb} — Monthly Attendance Leaderboard* 🏆\n\n"
            for rank, entry in enumerate(leaderboard[:5], 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                lb_text += (f"{medal} {entry['member'].full_name} — "
                            f"{entry['count']} sessions | 🔥 {entry['streak']} day streak\n")
            lb_text += f"\nKeep pushing — consistency is everything! 💪 #{gym_name_lb.replace(' ', '')}"

            st.code(lb_text, language=None)
            st.caption("Copy the text above and paste into a WhatsApp group for your gym members.")
