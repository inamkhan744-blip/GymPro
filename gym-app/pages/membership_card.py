import streamlit as st
import base64
import os
from datetime import date
import database as db
import styles

UPLOAD_DIR = "gym-app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

STATUS_COLORS = {
    "Active":    ("#064E3B", "#34D399"),
    "Inactive":  ("#450A0A", "#F87171"),
    "Suspended": ("#451A03", "#FBBF24"),
    "Frozen":    ("#0C1A3A", "#60A5FA"),
}

def _photo_b64(photo_field: str, serial_number: str = "") -> str | None:
    # 1. Pehle database ka direct path check karein agar valid hai
    if photo_field:
        photo_str = str(photo_field).strip()
        if "<div" not in photo_str and "style=" not in photo_str and "border-top" not in photo_str:
            filename = os.path.basename(photo_str)
            paths_to_check = [
                os.path.join(UPLOAD_DIR, filename),
                os.path.join("gym-app/uploads", filename),
                photo_str
            ]
            for path in paths_to_check:
                if path and os.path.exists(path) and os.path.isfile(path):
                    try:
                        with open(path, "rb") as f:
                            return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
                    except Exception:
                        pass

    # 2. SERIAL MATCHING LOGIC (For new and properly named images)
    if serial_number:
        clean_serial = str(serial_number).strip().replace("-", "").lower()
        if os.path.exists(UPLOAD_DIR):
            for file_name in os.listdir(UPLOAD_DIR):
                if clean_serial in file_name.lower().replace("_", "").replace("-", ""):
                    path = os.path.join(UPLOAD_DIR, file_name)
                    if os.path.isfile(path):
                        try:
                            with open(path, "rb") as f:
                                return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
                        except Exception:
                            pass
    return None

def render_card_html(member, gym_name: str) -> str:
    bg_clr, badge_clr = STATUS_COLORS.get(member.status, ("#1E293B", "#94A3B8"))
    photo_src = _photo_b64(member.photo_path, member.serial_number)

    if photo_src:
        photo_html = f'<img src="{photo_src}" style="width:90px;height:90px;object-fit:cover;border-radius:50%;border:3px solid #7C3AED;display:block;margin:0 auto 0.5rem;" />'
    else:
        photo_html = '<div style="width:90px;height:90px;background:#334155;border-radius:50%;border:3px solid #7C3AED;display:flex;align-items:center;justify-content:center;margin:0 auto 0.5rem;font-size:2.5rem;color:#ffffff;">👤</div>'

    expiry_str = member.expiry_date or "—"
    try:
        exp_d = date.fromisoformat(str(member.expiry_date))
        days_left = (exp_d - date.today()).days
        expiry_note = f"({days_left}d left)" if days_left >= 0 else "(EXPIRED)"
        exp_color = "#34D399" if days_left > 7 else "#FBBF24" if days_left >= 0 else "#F87171"
    except Exception:
        expiry_note = ""
        exp_color = "#94A3B8"

    phone_html = f"<div style='text-align:center;font-size:0.75rem;color:#64748B;margin-bottom:0.5rem;'>📞 {member.phone}</div>" if member.phone else ""

    return f"""
    <div style="background:linear-gradient(135deg,#1E293B 0%,#0F172A 100%);border:1px solid #334155;border-radius:16px;padding:1.5rem;max-width:380px;margin:0 auto;box-shadow:0 20px 40px rgba(0,0,0,0.5);position:relative;overflow:hidden;font-family:sans-serif;">
        <div style="position:absolute;top:0;left:0;right:0;height:5px;background:linear-gradient(90deg,#7C3AED,#A78BFA,#7C3AED);"></div>
        <div style="text-align:center;margin-bottom:1rem;">
            <div style="font-size:0.65rem;color:#64748B;letter-spacing:0.15em;text-transform:uppercase;">GymPro — Multi-Gym Management</div>
            <div style="font-size:1.1rem;font-weight:800;color:#A78BFA;margin-top:0.2rem;">{gym_name}</div>
        </div>
        {photo_html}
        <div style="text-align:center;margin-bottom:1rem;">
            <div style="font-size:1.1rem;font-weight:800;color:#E2E8F0;">{member.full_name}</div>
            <div style="font-size:0.8rem;color:#7C3AED;font-weight:700;letter-spacing:0.08em;font-family:monospace;">{member.serial_number}</div>
        </div>
        <div style="text-align:center;margin-bottom:1rem;">
            <span style="background:{bg_clr};color:{badge_clr};padding:0.25rem 1rem;border-radius:9999px;font-size:0.75rem;font-weight:700;letter-spacing:0.05em;">● {member.status.upper()}</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;margin-bottom:0.75rem;">
            <div style="background:#0F172A;border-radius:8px;padding:0.5rem;">
                <div style="font-size:0.6rem;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;">Membership</div>
                <div style="font-size:0.85rem;font-weight:600;color:#E2E8F0;">{member.membership_type}</div>
            </div>
            <div style="background:#0F172A;border-radius:8px;padding:0.5rem;">
                <div style="font-size:0.6rem;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;">Fee / Month</div>
                <div style="font-size:0.85rem;font-weight:600;color:#34D399;">PKR {(member.fee_amount or 0):,.0f}</div>
            </div>
            <div style="background:#0F172A;border-radius:8px;padding:0.5rem;">
                <div style="font-size:0.6rem;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;">Join Date</div>
                <div style="font-size:0.8rem;font-weight:600;color:#E2E8F0;">{member.join_date}</div>
            </div>
            <div style="background:#0F172A;border-radius:8px;padding:0.5rem;">
                <div style="font-size:0.6rem;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;">Expiry Date</div>
                <div style="font-size:0.8rem;font-weight:600;color:{exp_color};">{expiry_str} <span style="font-size:0.65rem;">{expiry_note}</span></div>
            </div>
        </div>
        {phone_html}
    </div>
    """

def render(gym_id, role):
    styles.page_header("🪪", "Membership Cards", "Digital Identity Verification — Member Photo ID Preview")
    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        if gym_id:
            sel_gid = gym_id
            st.text_input("Gym", value=next((g.name for g in gyms if g.id == gym_id), ""), disabled=True)
        else:
            opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen = st.selectbox("Gym Location", list(opts.keys()))
            sel_gid = opts[chosen]
            
    with fc2:
        search = st.text_input("🔍 Search Member", placeholder="Name, serial, phone…")
    with fc3:
        status_f = st.selectbox("Status", ["All", "Active", "Inactive", "Suspended", "Frozen"])

    members = db.get_members(gym_id=sel_gid, status=status_f, search=search)
    if not members:
        st.info("No members match your filters.")
        return

    st.markdown(f"**{len(members)} member card(s)**")
    st.divider()

    mem_opts = {f"{m.serial_number} — {m.full_name}": m.id for m in members}
    selected_label = st.selectbox("Select member to preview card", list(mem_opts.keys()))
    selected_mid = mem_opts[selected_label]
    selected_m = next((m for m in members if m.id == selected_mid), None)

    if not selected_m:
        return

    gym_name = next((g.name for g in gyms if g.id == selected_m.gym_id), "GymPro")
    col_card, col_info = st.columns([1, 1])

    with col_card:
        st.markdown("**🪪 Membership Card Preview**")
        st.components.v1.html(render_card_html(selected_m, gym_name), height=450, scrolling=False)

    with col_info:
        st.markdown("**📋 Digital Identity Details**")
        st.markdown(f"""
| Field | Value |
|-------|-------|
| **Full Name** | {selected_m.full_name} |
| **Serial No.** | `{selected_m.serial_number}` |
| **Membership** | {selected_m.membership_type} |
| **Status** | {selected_m.status} |
        """)

        st.markdown("**📤 Update Identity Image**")
        new_photo = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png", "webp"], key=f"upload_{selected_m.id}")
        
        if new_photo:
            ext = os.path.splitext(new_photo.name)[-1].lower()
            # File name ab direct member ke serial number par save hoga
            clean_s = str(selected_m.serial_number).strip().replace("-", "").lower()
            new_filename = f"{clean_s}{ext}"
            path = os.path.join(UPLOAD_DIR, new_filename)
            with open(path, "wb") as fp:
                fp.write(new_photo.getbuffer())
                
            db.update_member(
                selected_m.id,
                photo_path=f"gym-app/uploads/{new_filename}",
                full_name=selected_m.full_name,
                phone=selected_m.phone or "",
                email=selected_m.email or "",
                gender=selected_m.gender or "",
                dob=selected_m.dob or "",
                membership_type=selected_m.membership_type,
                fee_amount=selected_m.fee_amount or 0,
                join_date=selected_m.join_date,
                expiry_date=selected_m.expiry_date or "",
                status=selected_m.status,
                notes=selected_m.notes or "",
            )
            st.success("✅ Photo updated perfectly!")
            st.rerun()

    # --- 👥 ASLI GALLERY VIEW LOOP WITH EXPANDER ---
    st.write("") 
    with st.expander(f"👥 View All {len(members)} Cards (Gallery View)", expanded=False):
        g_cols = st.columns(3) 
        for idx, m in enumerate(members):
            m_gym = next((g.name for g in gyms if g.id == m.gym_id), "GymPro")
            card_html = render_card_html(m, m_gym)
            with g_cols[idx % 3]:
                st.components.v1.html(card_html, height=460, scrolling=False)
