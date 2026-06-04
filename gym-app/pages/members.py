import streamlit as st
import pandas as pd
import os
import uuid
from PIL import Image
from datetime import date, timedelta
import database as db
import styles
from qr_utils import member_qr_png

# Purani pictures ka seedha path set kar diya gaya hai
UPLOAD_DIR = "gym-app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

GENDERS = ["Male", "Female", "Other", "Prefer not to say"]
STATUSES = ["Active", "Inactive", "Suspended", "Frozen"]


def save_photo(f):
    ext = os.path.splitext(f.name)[-1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as fp:
        fp.write(f.getbuffer())
    return filename


def show_photo(photo_field, w=100):
    if photo_field:
        filename = os.path.basename(photo_field)
        path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(path):
            try:
                st.image(Image.open(path), width=w)
                return
            except Exception:
                pass
    st.markdown("👤", unsafe_allow_html=True)


def render(gym_id, role):
    styles.page_header("👥", "Members", "Register, search and manage gym members")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym in **Gym Setup** first.")
        return

    # --- TABS KI JAGAH CHANGE KAR DI (Register Member Pehle) ---
    tab_add, tab_list = st.tabs(["➕ Register Member", "📋 Member List"])

    # --- REGISTER MEMBER TAB (Ab Yeh Pehle Open Hoga) ---
    with tab_add:
        _register_form(gyms, gym_id, role)

    # --- MEMBER LIST TAB (Ab Yeh Baad Mein Open Hoga) ---
    with tab_list:
        f1, f2, f3, f4 = st.columns([2, 2, 1, 1])
        gym_opts = {g.name: g.id for g in gyms}

        with f1:
            if gym_id:
                chosen_gym_name = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)
                st.text_input("Gym", value=chosen_gym_name, disabled=True, key="ml_gym_display")
                selected_gid = gym_id
            else:
                opts = {"All Gyms": None} | gym_opts
                chosen = st.selectbox("Gym", list(opts.keys()), key="ml_gym")
                selected_gid = opts[chosen]
        with f2:
            search = st.text_input("🔍 Search", placeholder="Name, serial, phone…", key="ml_search")
        with f3:
            status_f = st.selectbox("Status", ["All"] + STATUSES, key="ml_status")
        with f4:
            st.write("")
            st.write("")
            st.button("🔄 Refresh", use_container_width=True, key="ml_refresh")

        members = db.get_members(gym_id=selected_gid, status=status_f, search=search)

        active_c = sum(1 for m in members if m.status == "Active")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Found", len(members))
        mc2.metric("Active", active_c)
        mc3.metric("Inactive / Other", len(members) - active_c)

        st.divider()

        if not members:
            st.info("No members match your filters.")
        else:
            rows = []
            for m in members:
                gym_name = next((g.name for g in gyms if g.id == m.gym_id), "—")
                rows.append({
                    "Serial": m.serial_number,
                    "Name": m.full_name,
                    "Gym": gym_name,
                    "Membership": m.membership_type,
                    "Phone": m.phone or "—",
                    "Fee/Month": f"PKR {m.fee_amount:,.0f}",
                    "Joined": m.join_date,
                    "Expires": m.expiry_date or "—",
                    "Status": m.status,
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True, height=300)

            st.divider()
            st.markdown("**Member Details**")
            selected_serial = st.selectbox(
                "Select member to view/edit",
                [m.serial_number for m in members],
                format_func=lambda s: next(
                    (f"{m.serial_number} — {m.full_name}" for m in members if m.serial_number == s), s
                ),
                key="ml_select_member",
            )
            selected_m = next((m for m in members if m.serial_number == selected_serial), None)
            if selected_m:
                _member_detail(selected_m, gyms, role)


def _member_detail(m, gyms, role):
    col_photo, col_info = st.columns([1, 4])
    with col_photo:
        show_photo(m.photo_path, w=120)
    with col_info:
        gym_name = next((g.name for g in gyms if g.id == m.gym_id), "—")
        status_color = {"Active": "green", "Inactive": "red", "Suspended": "amber", "Frozen": "blue"}.get(m.status, "gray")
        st.markdown(
            f"**{m.full_name}** &nbsp; {styles.badge(m.status, status_color)} &nbsp; `{m.serial_number}`",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**Gym:** {gym_name}  \n**Type:** {m.membership_type}  \n**Fee:** PKR {m.fee_amount:,.0f}")
        c2.markdown(f"**Phone:** {m.phone or '—'}  \n**Email:** {m.email or '—'}  \n**Gender:** {m.gender or '—'}")
        c3.markdown(f"**Joined:** {m.join_date}  \n**Expires:** {m.expiry_date or '—'}  \n**DOB:** {m.dob or '—'}")
        if m.notes:
            st.caption(f"📝 {m.notes}")

    with st.expander("📱 Member QR Code"):
        qc1, qc2 = st.columns([1, 2])
        with qc1:
            png = member_qr_png(m.serial_number, box_size=8, border=2)
            st.image(png, width=200, caption=m.serial_number)
        with qc2:
            st.markdown("Print this on the membership card.")
            st.download_button(
                "⬇️ Download QR PNG",
                data=png,
                file_name=f"{m.serial_number}_qr.png",
                mime="image/png",
                key=f"qr_dl_{m.id}",
            )

    if role in ("admin", "staff"):
        with st.expander("✏️ Edit Member"):
            _edit_form(m, gyms)
        if role == "admin":
            if st.button("🗑️ Delete Member", key=f"del_m_{m.id}"):
                st.session_state[f"confirm_del_m_{m.id}"] = True
            if st.session_state.get(f"confirm_del_m_{m.id}"):
                st.warning("Permanently delete this member?")
                cc, cx = st.columns(2)
                if cc.button("✅ Yes, Delete", key=f"cdy_{m.id}", type="primary"):
                    db.delete_member(m.id)
                    st.success("Deleted.")
                    st.session_state.pop(f"confirm_del_m_{m.id}", None)
                    st.rerun()
                if cx.button("Cancel", key=f"cdn_{m.id}"):
                    st.session_state.pop(f"confirm_del_m_{m.id}", None)
                    st.rerun()


def _register_form(gyms, gym_id, role):
    st.subheader("Register New Member")
    gym_opts = {g.name: g.id for g in gyms}
    default_name = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)

    with st.form("reg_member_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            gym_sel = st.selectbox("Gym *", list(gym_opts.keys()),
                                   index=list(gym_opts.keys()).index(default_name),
                                   key="reg_gym_sel")
            full_name = st.text_input("Full Name *", key="reg_full_name")
            phone = st.text_input("Phone", placeholder="+92 300-0000000", key="reg_phone")
            email = st.text_input("Email", key="reg_email")
            gender = st.selectbox("Gender", GENDERS, key="reg_gender")
            dob = st.date_input("Date of Birth", value=None,
                                min_value=date(1920, 1, 1), max_value=date.today(),
                                key="reg_dob")
        with c2:
            mem_type = st.selectbox("Membership Type *", db.MEMBERSHIP_TYPES, key="reg_mem_type")
            fee_amount = st.number_input("Monthly Fee (PKR)", min_value=0.0, step=5.0, format="%.2f", key="reg_fee")
            join_date = st.date_input("Join Date *", value=date.today(), key="reg_join")
            expiry_date = st.date_input("Expiry Date", value=date.today() + timedelta(days=30), key="reg_expiry")
            status = st.selectbox("Status", STATUSES, key="reg_status")
            notes = st.text_area("Notes", height=80, key="reg_notes")
            photo = st.file_uploader("📷 Member Photo", type=["jpg", "jpeg", "png", "webp"],
                                     key="reg_photo")

        if photo:
            st.image(photo, width=100, caption="Preview")

        if st.form_submit_button("✅ Register Member", type="primary", use_container_width=True):
            if not full_name.strip():
                st.error("Full name is required.")
            else:
                photo_path = save_photo(photo) if photo else None
                ok, msg, serial = db.add_member(
                    gym_id=gym_opts[gym_sel],
                    full_name=full_name, phone=phone, email=email,
                    gender=gender, dob=str(dob) if dob else "",
                    membership_type=mem_type, fee_amount=fee_amount,
                    join_date=str(join_date),
                    expiry_date=str(expiry_date) if expiry_date else None,
                    photo_path=photo_path, status=status, notes=notes,
                )
                if ok:
                    st.success(f"🎉 {msg}")
                else:
                    st.error(msg)


def _edit_form(m, gyms):
    gym_opts = {g.name: g.id for g in gyms}
    cur_gym = next((g.name for g in gyms if g.id == m.gym_id), gyms[0].name)

    with st.form(f"edit_member_form_{m.id}"):
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("Full Name *", value=m.full_name, key=f"ef_name_{m.id}")
            phone = st.text_input("Phone", value=m.phone or "", key=f"ef_phone_{m.id}")
            email = st.text_input("Email", value=m.email or "", key=f"ef_email_{m.id}")
            gender_i = GENDERS.index(m.gender) if m.gender in GENDERS else 0
            gender = st.selectbox("Gender", GENDERS, index=gender_i, key=f"ef_gender_{m.id}")
            dob_val = None
            if m.dob:
                try:
                    dob_val = date.fromisoformat(m.dob)
                except Exception:
                    pass
            dob = st.date_input("DOB", value=dob_val, min_value=date(1920, 1, 1),
                                max_value=date.today(), key=f"ef_dob_{m.id}")
        with c2:
            mi = db.MEMBERSHIP_TYPES.index(m.membership_type) if m.membership_type in db.MEMBERSHIP_TYPES else 0
            mem_type = st.selectbox("Membership Type *", db.MEMBERSHIP_TYPES, index=mi, key=f"ef_mtype_{m.id}")
            fee_amount = st.number_input("Fee (PKR)", value=float(m.fee_amount or 0),
                                         min_value=0.0, step=5.0, key=f"ef_fee_{m.id}")
            join_date = st.date_input("Join Date *", value=date.fromisoformat(m.join_date),
                                      key=f"ef_join_{m.id}")
            exp_val = date.fromisoformat(m.expiry_date) if m.expiry_date else date.today() + timedelta(days=30)
            expiry_date = st.date_input("Expiry Date", value=exp_val, key=f"ef_expiry_{m.id}")
            si = STATUSES.index(m.status) if m.status in STATUSES else 0
            status = st.selectbox("Status", STATUSES, index=si, key=f"ef_status_{m.id}")
            notes = st.text_area("Notes", value=m.notes or "", height=70, key=f"ef_notes_{m.id}")
            photo = st.file_uploader("Replace Photo", type=["jpg", "jpeg", "png", "webp"],
                                     key=f"ef_photo_{m.id}")

        cs, cc = st.columns(2)
        save = cs.form_submit_button("💾 Save", type="primary")
        cancel = cc.form_submit_button("Cancel")

        if cancel:
            st.rerun()
        if save:
            photo_path = m.photo_path
            if photo:
                photo_path = save_photo(photo)
            ok, msg = db.update_member(
                m.id, full_name=full_name, phone=phone, email=email,
                gender=gender, dob=str(dob) if dob else "",
                membership_type=mem_type, fee_amount=fee_amount,
                join_date=str(join_date), expiry_date=str(expiry_date),
                photo_path=photo_path, status=status, notes=notes,
            )
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
