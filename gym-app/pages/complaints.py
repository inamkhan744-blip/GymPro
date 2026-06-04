import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import database as db
import styles


PRIORITY_COLORS = {"Low": "blue", "Medium": "amber", "High": "red", "Urgent": "red"}
STATUS_ICONS = {"Open": "🟡", "In Progress": "🔵", "Resolved": "✅"}


def make_wa_link(phone: str, message: str) -> str:
    clean = "".join(c for c in phone if c.isdigit() or c == "+")
    if clean.startswith("0"):
        clean = "+92" + clean[1:]
    return f"https://wa.me/{clean}?text={urllib.parse.quote(message)}"


def render(gym_id, role):
    styles.page_header("📣", "Complaints & Feedback",
                       "Member complaints with WhatsApp resolution trigger")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    tab_list, tab_submit = st.tabs(["📋 All Complaints", "➕ Submit Complaint"])

    # ── All Complaints ─────────────────────────────────────────────────────────
    with tab_list:
        fc1, fc2, fc3 = st.columns([2, 1, 1])
        with fc1:
            if gym_id:
                sel_gid = gym_id
                st.text_input("Gym", value=next((g.name for g in gyms if g.id == gym_id), ""),
                              disabled=True, key="cmp_gym_display")
            else:
                opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
                chosen = st.selectbox("Gym", list(opts.keys()), key="cmp_gym")
                sel_gid = opts[chosen]
        with fc2:
            status_f = st.selectbox("Status", ["All"] + db.COMPLAINT_STATUSES, key="cmp_status")
        with fc3:
            priority_f = st.selectbox("Priority", ["All"] + db.COMPLAINT_PRIORITIES,
                                       key="cmp_priority")

        complaints = db.get_complaints(gym_id=sel_gid, status=status_f)
        if priority_f != "All":
            complaints = [c for c in complaints if c.priority == priority_f]

        if not complaints:
            st.info("No complaints found.")
        else:
            open_c = sum(1 for c in complaints if c.status == "Open")
            ip_c   = sum(1 for c in complaints if c.status == "In Progress")
            res_c  = sum(1 for c in complaints if c.status == "Resolved")

            kc1, kc2, kc3, kc4 = st.columns(4)
            kc1.metric("Total", len(complaints))
            kc2.metric("🟡 Open", open_c)
            kc3.metric("🔵 In Progress", ip_c)
            kc4.metric("✅ Resolved", res_c)

            st.divider()

            for c in complaints:
                gname = next((g.name for g in gyms if g.id == c.gym_id), "—")
                mem = db.get_member(c.member_id) if c.member_id else None
                icon = STATUS_ICONS.get(c.status, "❓")
                pcolor = PRIORITY_COLORS.get(c.priority, "gray")
                header = (f"{icon} **#{c.id}** — {c.subject} &nbsp; "
                          f"{styles.badge(c.priority, pcolor)} &nbsp; "
                          f"{styles.badge(c.status, 'green' if c.status == 'Resolved' else 'amber')}")

                with st.expander(f"#{c.id} — {c.subject} [{c.status}] | {gname}", expanded=False):
                    st.markdown(header, unsafe_allow_html=True)

                    cd1, cd2 = st.columns(2)
                    with cd1:
                        st.markdown(f"**Gym:** {gname}")
                        st.markdown(f"**Member:** {mem.full_name if mem else 'Non-member / Walk-in'}")
                        st.markdown(f"**Submitted By:** {c.submitted_by or '—'}")
                        st.markdown(f"**Date:** {c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else '—'}")
                    with cd2:
                        if c.resolved_by:
                            st.markdown(f"**Resolved By:** {c.resolved_by}")
                        if c.resolved_at:
                            st.markdown(f"**Resolved At:** {c.resolved_at.strftime('%Y-%m-%d %H:%M')}")

                    if c.description:
                        st.info(c.description)

                    # Status update (admin/staff)
                    if role in ("admin", "staff") and c.status != "Resolved":
                        st.divider()
                        with st.form(f"resolve_form_{c.id}"):
                            new_status = st.selectbox(
                                "Update Status",
                                [s for s in db.COMPLAINT_STATUSES if s != c.status],
                                key=f"cmp_new_status_{c.id}",
                            )
                            if st.form_submit_button("✅ Update Status", type="primary"):
                                current_user = st.session_state.get("username", "admin")
                                ok, msg = db.update_complaint_status(c.id, new_status, current_user)
                                if ok:
                                    st.success(msg)
                                    # WhatsApp trigger on Resolve
                                    if new_status == "Resolved" and mem and mem.phone:
                                        gym_name = next((g.name for g in gyms if g.id == c.gym_id), "GymPro")
                                        wa_msg = (
                                            f"Dear {mem.full_name},\n\n"
                                            f"Your complaint at {gym_name} has been *Resolved*! ✅\n\n"
                                            f"Subject: {c.subject}\n\n"
                                            f"We apologize for any inconvenience and thank you for your patience. "
                                            f"Please don't hesitate to contact us if you need further assistance.\n\n"
                                            f"Best regards,\n{gym_name} Team 🏋️"
                                        )
                                        wa_link = make_wa_link(mem.phone, wa_msg)
                                        st.markdown(
                                            f'<a href="{wa_link}" target="_blank" style="display:inline-block;'
                                            f'background:#25D366;color:white;padding:0.5rem 1.2rem;'
                                            f'border-radius:8px;font-weight:700;text-decoration:none;">'
                                            f'💬 Send Resolution via WhatsApp</a>',
                                            unsafe_allow_html=True,
                                        )
                                    st.rerun()
                                else:
                                    st.error(msg)

                    elif c.status == "Resolved" and mem and mem.phone and not c.wa_sent:
                        gym_name = next((g.name for g in gyms if g.id == c.gym_id), "GymPro")
                        wa_msg = (
                            f"Dear {mem.full_name},\n\n"
                            f"Your complaint at {gym_name} has been *Resolved*! ✅\n\n"
                            f"Subject: {c.subject}\n\n"
                            f"Thank you for your patience.\n\n"
                            f"Best regards,\n{gym_name} Team 🏋️"
                        )
                        wa_link = make_wa_link(mem.phone, wa_msg)
                        st.markdown(
                            f'<a href="{wa_link}" target="_blank" style="display:inline-block;'
                            f'background:#25D366;color:white;padding:0.4rem 1rem;'
                            f'border-radius:8px;font-weight:700;text-decoration:none;font-size:0.85rem;">'
                            f'💬 Send WhatsApp Notification</a>',
                            unsafe_allow_html=True,
                        )

    # ── Submit Complaint ───────────────────────────────────────────────────────
    with tab_submit:
        st.subheader("Submit New Complaint / Feedback")
        if gym_id:
            sel_gid_sub = gym_id
            st.text_input("Gym", value=next((g.name for g in gyms if g.id == gym_id), ""),
                          disabled=True, key="csub_gym_display")
        else:
            opts2 = {g.name: g.id for g in gyms}
            chosen2 = st.selectbox("Gym", list(opts2.keys()), key="csub_gym")
            sel_gid_sub = opts2[chosen2]

        with st.form("submit_complaint_form", clear_on_submit=True):
            sc1, sc2 = st.columns(2)
            with sc1:
                members_sub = db.get_members(gym_id=sel_gid_sub)
                mem_opts_sub = {"No Member (Staff/Walk-in)": None} | {
                    f"{m.serial_number} — {m.full_name}": m.id for m in members_sub
                }
                mem_sel_sub = st.selectbox("Related Member", list(mem_opts_sub.keys()),
                                           key="csub_member")
                subject = st.text_input("Subject *", placeholder="e.g. Equipment not working",
                                        key="csub_subject")
                priority = st.selectbox("Priority", db.COMPLAINT_PRIORITIES, index=1,
                                        key="csub_priority")
            with sc2:
                description = st.text_area("Description", height=140,
                                           placeholder="Describe the issue in detail…",
                                           key="csub_desc")

            if st.form_submit_button("📣 Submit Complaint", type="primary",
                                     use_container_width=True):
                if not subject.strip():
                    st.error("Subject is required.")
                else:
                    current_user = st.session_state.get("username", "staff")
                    ok, msg = db.add_complaint(
                        gym_id=sel_gid_sub,
                        subject=subject,
                        description=description,
                        priority=priority,
                        submitted_by=current_user,
                        member_id=mem_opts_sub[mem_sel_sub],
                    )
                    st.success(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()
