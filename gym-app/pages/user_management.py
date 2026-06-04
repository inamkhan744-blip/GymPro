import streamlit as st
import pandas as pd
import database as db
import styles

ROLES = ["admin", "staff", "auditor"]


def render(current_user_id):
    styles.page_header("🔐", "User Management", "Manage system accounts and role-based access")

    users = db.get_all_users()
    gyms = db.get_all_gyms()
    gym_opts = {"All Gyms (Admin)": None} | {g.name: g.id for g in gyms}

    # ── Add User ───────────────────────────────────────────────────────────────
    with st.expander("➕ Add New User", expanded=False):
        with st.form("add_user_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                username = st.text_input("Username *", placeholder="jsmith", key="au_username")
                full_name = st.text_input("Full Name *", placeholder="John Smith", key="au_fullname")
                password = st.text_input("Password *", type="password", key="au_password")
            with c2:
                role = st.selectbox("Role *", ROLES, key="au_role")
                gym_sel = st.selectbox("Assigned Gym", list(gym_opts.keys()), key="au_gym")
                st.caption("Admins see all gyms. Staff/Auditors are scoped to a gym.")

            if st.form_submit_button("✅ Create User", type="primary", use_container_width=True):
                if not username.strip() or not full_name.strip() or not password:
                    st.error("Username, full name, and password are required.")
                else:
                    ok, msg = db.add_user(
                        username=username.strip(),
                        full_name=full_name.strip(),
                        password=password,
                        role=role,
                        gym_id=gym_opts[gym_sel],
                    )
                    st.success(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()

    st.divider()

    # ── User List ──────────────────────────────────────────────────────────────
    st.markdown(f"**{len(users)} User(s)**")

    role_icons = {"admin": "👑", "staff": "🧑‍💼", "auditor": "🔍"}

    rows = []
    for u in users:
        gym_name = next((g.name for g in gyms if g.id == u.gym_id), "All Gyms")
        rows.append({
            "Role": f"{role_icons.get(u.role, '')} {u.role.capitalize()}",
            "Username": u.username,
            "Full Name": u.full_name,
            "Gym": gym_name,
            "Active": "✅" if u.is_active else "❌",
            "Created": u.created_at.strftime("%Y-%m-%d") if u.created_at else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()

    # ── Edit / Delete ──────────────────────────────────────────────────────────
    st.markdown("**Edit or Remove a User**")
    user_opts = {f"{u.username} ({u.role})": u.id for u in users if u.id != current_user_id}

    if not user_opts:
        st.info("No other users to manage.")
        return

    sel_label = st.selectbox("Select user", list(user_opts.keys()), key="um_sel_user")
    sel_uid = user_opts[sel_label]
    sel_user = next((u for u in users if u.id == sel_uid), None)

    if not sel_user:
        return

    with st.form(f"edit_user_form_{sel_uid}"):
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("Full Name *", value=sel_user.full_name,
                                     key=f"eu_name_{sel_uid}")
            new_role = st.selectbox("Role *", ROLES, index=ROLES.index(sel_user.role),
                                    key=f"eu_role_{sel_uid}")
            new_pw = st.text_input("New Password (leave blank to keep)", type="password",
                                   key=f"eu_pw_{sel_uid}")
        with c2:
            gym_keys = list(gym_opts.keys())
            cur_gym_name = next((g.name for g in gyms if g.id == sel_user.gym_id), "All Gyms (Admin)")
            gym_idx = gym_keys.index(cur_gym_name) if cur_gym_name in gym_keys else 0
            new_gym = st.selectbox("Assigned Gym", gym_keys, index=gym_idx,
                                   key=f"eu_gym_{sel_uid}")
            is_active = st.checkbox("Active Account", value=sel_user.is_active,
                                    key=f"eu_active_{sel_uid}")

        cs, cd = st.columns(2)
        save = cs.form_submit_button("💾 Save Changes", type="primary")
        delete = cd.form_submit_button("🗑️ Delete User")

        if save:
            ok, msg = db.update_user(
                user_id=sel_uid,
                full_name=new_name,
                role=new_role,
                gym_id=gym_opts[new_gym],
                is_active=is_active,
                new_password=new_pw or None,
            )
            st.success(msg) if ok else st.error(msg)
            if ok:
                st.rerun()

        if delete:
            st.session_state["confirm_del_user"] = sel_uid

    if st.session_state.get("confirm_del_user") == sel_uid:
        st.warning(f"Permanently delete **{sel_user.username}**?")
        cc, cx = st.columns(2)
        if cc.button("✅ Yes, Delete", type="primary", key=f"cdu_yes_{sel_uid}"):
            db.delete_user(sel_uid)
            st.success("User deleted.")
            st.session_state.pop("confirm_del_user", None)
            st.rerun()
        if cx.button("Cancel", key=f"cdu_no_{sel_uid}"):
            st.session_state.pop("confirm_del_user", None)
            st.rerun()
