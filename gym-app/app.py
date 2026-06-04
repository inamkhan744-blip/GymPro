import streamlit as st
import sqlite3
import sys
import os

# Path setting
sys.path.insert(0, os.path.dirname(__file__))


import database as db
import auth
import styles
from pages import (admin_dashboard, setup, members, attendance, fee_collection, expenses, 
                   whatsapp, auditor, user_management, reports, membership_card, progress, 
                   inventory, complaints, message_center,
)





# Page Config (Sabse pehle)
st.set_page_config(page_title="GymPro", page_icon="🏋️", layout="wide")
db.init_db()
styles.inject_css()

# ── Auth Gate ──
if not auth.require_login():
    auth.login_page()
    st.stop()
# ya naya code ha bd ma sagid delete karna par jaye
# Sahi tareeka:
st.markdown("""
    <link rel="manifest" href="manifest.json">
    <script>
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/service-worker.js');
    }
    </script>
""", unsafe_allow_html=True)


# (Yahan woh import lines aur baki logic rakhein jo aapne pehle likha tha)
# Sahi tareeqa: Har module ka naam likhein
from pages import (
    admin_dashboard, 
    setup, 
    members, 
    attendance, 
    fee_collection, 
    expenses, 
    whatsapp, 
    auditor, 
    user_management, 
    reports, 
    membership_card, 
    progress, 
    inventory, 
    complaints, 
    message_center,
    ai_assistant,
)




# ── Public profile route (no login required) ──────────────────────────────────
# Triggered by ?profile=<token> where <token> is an HMAC-signed reference to
# the member id. Prevents anonymous enumeration of the member roster.
_profile_param = st.query_params.get("profile")
if _profile_param:
    from pages import public_profile
    from profile_token import parse_token
    _mid = parse_token(_profile_param)
    public_profile.render(_mid if _mid is not None else -1)
    st.stop()

# ── Auth gate ──────────────────────────────────────────────────────────────────
if not auth.require_login():
    auth.login_page()
    st.stop()

# ── Lazy-import pages ──────────────────────────────────────────────────────────
from pages import (
    admin_dashboard,
    setup,
    members,
    attendance,
    fee_collection,
    expenses,
    whatsapp,
    auditor,
    user_management,
    reports,
    membership_card,
    progress,
    inventory,
    complaints,
    message_center,
    ai_assistant,
)

role        = st.session_state.get("role", "staff")
full_name   = st.session_state.get("full_name", "User")
username    = st.session_state.get("username", "")
user_id     = st.session_state.get("user_id")
gym_id      = st.session_state.get("selected_gym_id")
user_gym_id = st.session_state.get("user_gym_id")

gyms = db.get_all_gyms()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0.5rem 0.5rem;text-align:center;">
        <div style="font-size:2rem;">🏋️</div>
        <div style="font-size:1.2rem;font-weight:800;color:#A78BFA;letter-spacing:0.05em;">GymPro</div>
        <div style="font-size:0.7rem;color:#475569;letter-spacing:0.1em;text-transform:uppercase;">Multi-Gym Control Panel</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    role_icon = auth.ROLE_ICONS.get(role, "👤")
    role_label = {"admin": "Administrator", "staff": "Staff Member",
                  "auditor": "Independent Auditor"}.get(role, role.upper())
    st.markdown(f"""
    <div style="background:#1E293B;border-radius:10px;padding:0.75rem;margin-bottom:0.75rem;">
        <div style="font-size:0.65rem;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;">Signed in as</div>
        <div style="font-weight:700;color:#E2E8F0;">{role_icon} {full_name}</div>
        <div style="font-size:0.72rem;color:#7C3AED;font-weight:600;">{role_label}</div>
    </div>
    """, unsafe_allow_html=True)

    # Switch Gym Location
    if role == "admin" and gyms:
        st.markdown("""<div style="font-size:0.65rem;color:#64748B;text-transform:uppercase;
            letter-spacing:0.08em;margin-bottom:0.3rem;">Switch Gym Location</div>""",
                    unsafe_allow_html=True)
        gym_options = {"🌐 All Gyms": None} | {f"🏋️ {g.name}": g.id for g in gyms}
        cur_gym_key = next((f"🏋️ {g.name}" for g in gyms if g.id == gym_id), "🌐 All Gyms")
        chosen_gym = st.selectbox(
            "Switch Gym Location", 
            list(gym_options.keys()),
            index=list(gym_options.keys()).index(cur_gym_key),
            label_visibility="collapsed",
            key="main_gym_selector"  # <--- Yeh line error khatam kar degi
        )

        st.session_state["selected_gym_id"] = gym_options[chosen_gym]
        gym_id = st.session_state["selected_gym_id"]
        st.markdown(f"""<div style="font-size:0.7rem;color:#64748B;text-align:right;
            margin-top:-0.3rem;margin-bottom:0.3rem;">{len(gyms)} gym(s) registered</div>""",
                    unsafe_allow_html=True)
    elif user_gym_id and gyms:
        gym_name = next((g.name for g in gyms if g.id == user_gym_id), "Your Gym")
        st.markdown(f"""<div style="background:#1E293B;border-radius:8px;padding:0.5rem 0.75rem;
            margin-bottom:0.5rem;font-size:0.85rem;">🏋️ <strong>{gym_name}</strong><br>
            <span style="font-size:0.65rem;color:#64748B;">Assigned Gym</span></div>""",
                    unsafe_allow_html=True)
        st.session_state["selected_gym_id"] = user_gym_id
        gym_id = user_gym_id

    st.divider()

    # Navigation
    # Navigation
    allowed = auth.allowed_pages()
    nav_sections = {
        "AI & Support": {
            "AI Assistant":      ("🤖", "AI Assistant"),
        },
        "General Management": {
            "Dashboard":         ("📊", "Dashboard"),
            "Gym Setup":         ("⚙️", "Gym Setup"),
        },
        "Member & Identity": {
            "Members":           ("👥", "Members"),
            "Membership Cards":  ("🪪", "Membership Cards"),
            "Attendance":        ("📅", "Attendance"),
            "Progress Tracker":  ("📏", "Progress Tracker"),
        },
        "Fees & Finance": {
            "Fee Collection":    ("💰", "Fee Collection"),
            "Expenses":          ("📉", "Expenses"),
            "Inventory":         ("📦", "Inventory"),
            "Reports":           ("📈", "Reports"),
        },
        "Communication": {
            "Message Center":    ("📨", "Message Center"),
            "WhatsApp":          ("💬", "WhatsApp"),
            "Complaints":        ("📣", "Complaints"),
        },
        "Audit & Access": {
            "Audit":             ("🔍", "Audit"),
            "User Management":   ("🔐", "User Management"),

        },
    }



    current_page = st.session_state.get("page", "Dashboard")
    for section_label, pages in nav_sections.items():
        visible = [k for k in pages if k in allowed]
        if not visible:
            continue
        st.markdown(
            f'<div style="font-size:0.6rem;color:#475569;text-transform:uppercase;'
            f'letter-spacing:0.1em;padding:0.4rem 0 0.2rem;">{section_label}</div>',
            unsafe_allow_html=True,
        )
        for page_key in visible:
            icon, label = pages[page_key]
            is_active = current_page == page_key
            btn_style = "nav-btn-active" if is_active else "nav-btn"
            st.markdown(f'<div class="{btn_style}">', unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=f"nav_{page_key}", use_container_width=True):
                st.session_state["page"] = page_key
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Alerts summary
    try:
        bdays = db.get_birthday_members(days_ahead=1, gym_id=gym_id)
        absent = db.get_absent_members(days=3, gym_id=gym_id)
        low_s = db.get_stock_items(gym_id=gym_id, low_stock_only=True)
        if bdays:
            st.markdown(f'<div style="background:#1E3A1E;border-radius:6px;padding:0.4rem 0.6rem;'
                        f'font-size:0.75rem;color:#34D399;margin-bottom:0.3rem;">🎂 {len(bdays)} birthday today</div>',
                        unsafe_allow_html=True)
        if absent:
            st.markdown(f'<div style="background:#3A1E1E;border-radius:6px;padding:0.4rem 0.6rem;'
                        f'font-size:0.75rem;color:#F87171;margin-bottom:0.3rem;">🚶 {len(absent)} absent 3+ days</div>',
                        unsafe_allow_html=True)
        if low_s:
            st.markdown(f'<div style="background:#3A2A1E;border-radius:6px;padding:0.4rem 0.6rem;'
                        f'font-size:0.75rem;color:#FBBF24;margin-bottom:0.3rem;">📦 {len(low_s)} low stock items</div>',
                        unsafe_allow_html=True)
    except Exception:
        pass

    stats = db.get_stats(gym_id)
    st.markdown("""<div style="font-size:0.65rem;color:#64748B;text-transform:uppercase;
        letter-spacing:0.08em;margin:0.5rem 0 0.3rem;">Revenue Analytics</div>""",
                unsafe_allow_html=True)
    st.markdown(styles.metric_card("Members", stats["total_members"],
                                   f"{stats['active_members']} active", "purple"),
                unsafe_allow_html=True)
    st.markdown(styles.metric_card("Month Revenue", f"PKR {stats['month_revenue']:,.0f}",
                                   "", "green"), unsafe_allow_html=True)
    st.markdown(styles.metric_card("Month Expenses", f"PKR {stats['month_expenses']:,.0f}",
                                   "", "red"), unsafe_allow_html=True)





    st.divider()
    if st.button("🚪 Sign Out", use_container_width=True):
        auth.logout()



# ── Page Router ────────────────────────────────────────────────────────────────
page = st.session_state.get("page", "Dashboard")

if not auth.can_access(page):
    st.error("🚫 You don't have permission to access this page.")
    st.stop()

gid = st.session_state.get("selected_gym_id")

if   page == "Dashboard":
    admin_dashboard.render(gid, role,)


elif page == "Gym Setup":        setup.render()
elif page == "Members":          members.render(gid, role)
elif page == "Membership Cards": membership_card.render(gid, role)
elif page == "Attendance":       attendance.render(gid, role, username)
elif page == "Progress Tracker": progress.render(gid, role)
elif page == "Fee Collection":   fee_collection.render(gid, role, username)
elif page == "Expenses":         expenses.render(gid, role, username)
elif page == "Inventory":        inventory.render(gid, role)
elif page == "Reports":          reports.render(gid, role)
elif page == "Message Center":   message_center.render(gid, role)
elif page == "WhatsApp":         whatsapp.render(gid, role)
elif page == "Complaints":       complaints.render(gid, role)
elif page == "Audit":            auditor.render(gid, role, username)
elif page == "User Management":  user_management.render(user_id)
elif page == "AI Assistant":
    from pages import ai_assistant
    ai_assistant.render(gid, role)

