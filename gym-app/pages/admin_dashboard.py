import streamlit as st
import pandas as pd
from datetime import date
import database as db
import styles

def render(gym_id, role):
    # Custom 3D CSS for modern look
    st.markdown("""
    <style>
    /* 3D Glass Card Effect */
    .glass-card-3d {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9));
        backdrop-filter: blur(12px);
        border-radius: 24px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 20px 35px -12px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .glass-card-3d:hover {
        transform: translateY(-4px);
        box-shadow: 0 25px 40px -15px rgba(0,0,0,0.5);
        border-color: rgba(255,255,255,0.2);
    }
    .metric-value-3d {
        font-size: 38px;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF, #A78BFA);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        letter-spacing: -1px;
    }
    .metric-label-3d {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #94A3B8;
    }
    .alert-box-critical {
        background: rgba(239, 68, 68, 0.12);
        border-left: 4px solid #EF4444;
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
    }
    .alert-box-urgent {
        background: rgba(245, 158, 11, 0.12);
        border-left: 4px solid #F59E0B;
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
    }
    .alert-box-absent {
        background: rgba(59, 130, 246, 0.12);
        border-left: 4px solid #3B82F6;
        border-radius: 16px;
        padding: 16px;
        margin: 8px 0;
    }
    .badge-paid {
        background: #10B981;
        color: white;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-partial {
        background: #F59E0B;
        color: white;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-unpaid {
        background: #EF4444;
        color: white;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    styles.page_header("📊", "Dashboard", "Real-time overview across all operations")

    gyms = db.get_all_gyms()
    if not gyms and role == "admin":
        st.info("👋 Welcome! Head to **Gym Setup** to create your first gym.")
        return

    stats = db.get_stats(gym_id)

    # ── 5 KPI Cards (3D Glass) ────────────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.markdown(f"""
        <div class="glass-card-3d" style="text-align:center;">
            <div class="metric-label-3d">👥 TOTAL MEMBERS</div>
            <div class="metric-value-3d">{stats['total_members']}</div>
            <div style="font-size:11px; color:#475569;">All registered</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div class="glass-card-3d" style="text-align:center;">
            <div class="metric-label-3d">✅ ACTIVE MEMBERS</div>
            <div class="metric-value-3d">{stats['active_members']}</div>
            <div style="font-size:11px; color:#475569;">{stats['total_members'] - stats['active_members']} inactive</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c3:
        st.markdown(f"""
        <div class="glass-card-3d" style="text-align:center;">
            <div class="metric-label-3d">💰 MONTH REVENUE</div>
            <div class="metric-value-3d">PKR {stats['month_revenue']:,.0f}</div>
            <div style="font-size:11px; color:#475569;">Total: PKR {stats['total_revenue']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c4:
        net = stats["month_revenue"] - stats["month_expenses"]
        color_net = "#10B981" if net >= 0 else "#EF4444"
        st.markdown(f"""
        <div class="glass-card-3d" style="text-align:center;">
            <div class="metric-label-3d">📈 MONTH NET P/L</div>
            <div class="metric-value-3d" style="background:linear-gradient(135deg, #FFF, {color_net}); -webkit-background-clip:text; background-clip:text;">PKR {net:,.0f}</div>
            <div style="font-size:11px; color:#475569;">Exp: PKR {stats['month_expenses']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c5:
        inv_rev = stats.get("inventory_revenue", 0)
        st.markdown(f"""
        <div class="glass-card-3d" style="text-align:center;">
            <div class="metric-label-3d">📦 INVENTORY SALES</div>
            <div class="metric-value-3d">PKR {inv_rev:,.0f}</div>
            <div style="font-size:11px; color:#475569;">From POS</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── ALERTS SECTION (Categorized: Critical/Urgent/Absent) ──────────────────
    bday_members = db.get_birthday_members(days_ahead=3, gym_id=gym_id)
    expiring_now = db.get_expiring_members(days=7, gym_id=gym_id)  # Get all expiring
    absent_alert = db.get_absent_members(days=3, gym_id=gym_id)
    low_stock = db.get_stock_items(gym_id=gym_id, low_stock_only=True)

    # Categorize expiring
    critical = [(m, d) for m, d in expiring_now if d <= 1]
    urgent = [(m, d) for m, d in expiring_now if 2 <= d <= 3]
    
    st.markdown("### ⚠️ ATTENTION REQUIRED")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.markdown('<div class="alert-box-critical"><strong>🔴 CRITICAL (0-1 din)</strong></div>', unsafe_allow_html=True)
        if critical:
            for m, d in critical[:5]:
                st.write(f"• **{m.full_name}** — {d} day(s) left")
        else:
            st.write("✅ No critical expiries")
    
    with col_b:
        st.markdown('<div class="alert-box-urgent"><strong>🟠 URGENT (2-3 din)</strong></div>', unsafe_allow_html=True)
        if urgent:
            for m, d in urgent[:5]:
                st.write(f"• **{m.full_name}** — {d} days left")
        else:
            st.write("✅ No urgent expiries")
    
    with col_c:
        st.markdown('<div class="alert-box-absent"><strong>🔵 ABSENT 3+ DAYS</strong></div>', unsafe_allow_html=True)
        if absent_alert:
            for m in absent_alert[:5]:
                st.write(f"• **{m.full_name}**")
        else:
            st.write("✅ Everyone active")
    
    # Birthday + Low Stock as small notes
    if bday_members:
        bday_text = "🎂 " + ", ".join([f"{m.full_name} ({d} day(s))" for m, d in bday_members[:3]])
        st.info(bday_text)
    if low_stock:
        stock_text = "📦 Low stock: " + ", ".join([f"{i.item_name} ({i.quantity} left)" for i in low_stock[:3]])
        st.warning(stock_text)

    st.markdown("---")

    # ── LEADERBOARD + PEAK HOUR (No Graphs) ───────────────────────────────────
    col_lb, col_ph = st.columns(2)
    
    with col_lb:
        st.markdown("### 🏆 Monthly Attendance Leaderboard")
        leaderboard = db.get_attendance_leaderboard(gym_id=gym_id, limit=5)
        if leaderboard:
            for rank, entry in enumerate(leaderboard[:5], 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #334155;">
                    <span style="font-weight:700; color:#A78BFA;">{medal}</span>
                    <span style="flex:1; margin-left:12px;"><strong>{entry['member'].full_name}</strong></span>
                    <span style="color:#94A3B8;">{entry['count']} sessions</span>
                    <span style="color:#F59E0B;">🔥 {entry['streak']}d</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No attendance data yet.")
    
    with col_ph:
        st.markdown("### ⏰ Peak Hour")
        hour_data = db.get_attendance_by_hour(gym_id=gym_id)
        if any(hour_data.values()):
            peak_hour = max(hour_data, key=lambda h: hour_data[h])
            peak_count = hour_data[peak_hour]
            am_pm = "AM" if peak_hour < 12 else "PM"
            hour_12 = peak_hour if peak_hour <= 12 else peak_hour - 12
            total_att = sum(hour_data.values())
            
            st.markdown(f"""
            <div class="glass-card-3d" style="text-align:center;">
                <div style="font-size:48px; font-weight:800; background:linear-gradient(135deg,#FFF,#A78BFA); -webkit-background-clip:text; background-clip:text; color:transparent;">
                    {hour_12}:00 {am_pm}
                </div>
                <div style="font-size:14px; color:#94A3B8;">🔥 {peak_count} check-ins at this hour</div>
                <div style="margin-top:12px; padding-top:12px; border-top:1px solid #334155;">
                    <div style="font-size:11px; color:#475569;">📊 Total Logged: {total_att} all-time entries</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No attendance records yet.")
    
    st.markdown("---")
    
    # ── RECENT SCAN-INS ───────────────────────────────────────────────────────
    st.markdown("### 🎯 Recent Scan-Ins (Today)")
    scans = db.get_recent_scans(gym_id=gym_id, limit=10, today_only=True)
    if scans:
        scan_df = pd.DataFrame([{
            "Time": s["time"],
            "Member": s["name"],
            "Serial": s["serial"],
            "Marked By": s["marked_by"],
        } for s in scans])
        st.dataframe(scan_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No QR check-ins yet today.")
    
    st.markdown("---")
    
    # ── MEMBERS & FEE STATUS TABLE ─────────────────────────────────────────────
    st.markdown("### 👥 Members & Fee Status")
    st.caption("Recent registrations + fee status ek hi jagah")
    
    all_members = db.get_members(gym_id=gym_id)
    all_fees = db.get_fee_records(gym_id=gym_id)
    
    member_paid = {}
    for f in all_fees:
        member_paid[f.member_id] = member_paid.get(f.member_id, 0) + f.amount
    
    unified_rows = []
    for m in all_members:
        expected_fee = getattr(m, "fee_amount", 0) or 0
        paid = member_paid.get(m.id, 0)
        pending = max(expected_fee - paid, 0)
        
        if expected_fee == 0 and paid == 0:
            status_badge = '<span class="badge-paid">⚪ No Fee</span>'
            status_key = "none"
        elif paid >= expected_fee and expected_fee > 0:
            status_badge = '<span class="badge-paid">🟢 PAID</span>'
            status_key = "paid"
        elif paid > 0 and paid < expected_fee:
            status_badge = '<span class="badge-partial">🟡 PARTIAL</span>'
            status_key = "partial"
        else:
            status_badge = '<span class="badge-unpaid">🔴 UNPAID</span>'
            status_key = "unpaid"
        
        unified_rows.append({
            "Serial": m.serial_number,
            "Name": m.full_name,
            "Phone": m.phone or "—",
            "Type": m.membership_type,
            "Fee": f"PKR {expected_fee:,.0f}",
            "Paid": f"PKR {paid:,.0f}",
            "Pending": f"PKR {pending:,.0f}",
            "Status": status_badge,
            "_status_key": status_key,
        })
    
    # Stats cards
    total_count = len(unified_rows)
    paid_count = sum(1 for r in unified_rows if r["_status_key"] == "paid")
    unpaid_count = sum(1 for r in unified_rows if r["_status_key"] == "unpaid")
    partial_count = sum(1 for r in unified_rows if r["_status_key"] == "partial")
    
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(styles.metric_card("Total Members", total_count, "All registered", "purple"), unsafe_allow_html=True)
    with s2:
        st.markdown(styles.metric_card("🟢 Paid", paid_count, "Fee cleared", "green"), unsafe_allow_html=True)
    with s3:
        st.markdown(styles.metric_card("🟡 Partial", partial_count, "Some pending", "amber"), unsafe_allow_html=True)
    with s4:
        st.markdown(styles.metric_card("🔴 Unpaid", unpaid_count, "Need to collect", "red"), unsafe_allow_html=True)
    
    # Filter buttons
    if "fee_filter" not in st.session_state:
        st.session_state.fee_filter = "all"
    
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        if st.button(f"All ({total_count})", use_container_width=True,
                     type="primary" if st.session_state.fee_filter == "all" else "secondary"):
            st.session_state.fee_filter = "all"
            st.rerun()
    with fc2:
        if st.button(f"🟢 Paid ({paid_count})", use_container_width=True,
                     type="primary" if st.session_state.fee_filter == "paid" else "secondary"):
            st.session_state.fee_filter = "paid"
            st.rerun()
    with fc3:
        if st.button(f"🟡 Partial ({partial_count})", use_container_width=True,
                     type="primary" if st.session_state.fee_filter == "partial" else "secondary"):
            st.session_state.fee_filter = "partial"
            st.rerun()
    with fc4:
        if st.button(f"🔴 Unpaid ({unpaid_count})", use_container_width=True,
                     type="primary" if st.session_state.fee_filter == "unpaid" else "secondary"):
            st.session_state.fee_filter = "unpaid"
            st.rerun()
    
    search_query = st.text_input("🔍 Search by Name / Serial / Phone", placeholder="Type to search...")
    
    filtered_rows = [r for r in unified_rows if st.session_state.fee_filter == "all" or r["_status_key"] == st.session_state.fee_filter]
    if search_query:
        q = search_query.lower()
        filtered_rows = [r for r in filtered_rows if q in r["Name"].lower() or q in r["Serial"].lower()]
    
    if filtered_rows:
        display_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in filtered_rows[:25]]
        st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
        st.caption(f"📋 Showing {len(display_rows)} of {len(filtered_rows)} members")
    
    st.markdown("---")
    
    # ── EXPIRING MEMBERSHIPS (Enhanced) ───────────────────────────────────────
    expiring = db.get_expiring_members(days=7, gym_id=gym_id)
    if expiring:
        st.markdown(f"### ⚠️ {len(expiring)} Membership(s) Expiring in 7 Days")
        
        critical = [x for x in expiring if x[1] <= 1]
        urgent = [x for x in expiring if 2 <= x[1] <= 3]
        soon = [x for x in expiring if x[1] >= 4]
        
        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown(styles.metric_card("🔴 Critical", len(critical), "Aaj ya kal expire", "red"), unsafe_allow_html=True)
        with e2:
            st.markdown(styles.metric_card("🟠 Urgent", len(urgent), "2-3 din mein", "amber"), unsafe_allow_html=True)
        with e3:
            st.markdown(styles.metric_card("🟡 Soon", len(soon), "4-7 din mein", "blue"), unsafe_allow_html=True)
        
        exp_rows = []
        for m, days_left in expiring[:20]:
            urgency = "🔴 Critical" if days_left <= 1 else "🟠 Urgent" if days_left <= 3 else "🟡 Soon"
            exp_rows.append({
                "Urgency": urgency,
                "Name": m.full_name,
                "Serial": m.serial_number,
                "Phone": m.phone or "—",
                "Expires On": m.expiry_date,
                "Days Left": "TODAY!" if days_left == 0 else f"{days_left} day(s)",
            })
        st.dataframe(pd.DataFrame(exp_rows), use_container_width=True, hide_index=True)
        st.info("💡 **Tip:** Critical members ko foran WhatsApp/Call karein renewal ke liye!")
    
    st.markdown("---")
    st.caption("✨ Simplified dashboard · No graphs · Clean 3D design · Just what matters")