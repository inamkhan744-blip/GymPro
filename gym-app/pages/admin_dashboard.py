import streamlit as st
import pandas as pd
from datetime import date
import database as db
import styles


def render(gym_id, role):
    styles.page_header("📊", "Dashboard", "Real-time overview across all operations")

    gyms = db.get_all_gyms()
    if not gyms and role == "admin":
        st.info("👋 Welcome! Head to **Gym Setup** to create your first gym.")
        return

    stats = db.get_stats(gym_id)

    # ── KPI Row ────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(styles.metric_card("Total Members", stats["total_members"],
                                       "All registered", "purple"), unsafe_allow_html=True)
    with c2:
        st.markdown(styles.metric_card("Active Members", stats["active_members"],
                                       f"{stats['total_members'] - stats['active_members']} inactive",
                                       "green"), unsafe_allow_html=True)
    with c3:
        st.markdown(styles.metric_card("Month Revenue", f"PKR {stats['month_revenue']:,.0f}",
                                       f"Total: PKR {stats['total_revenue']:,.0f}", "blue"),
                    unsafe_allow_html=True)
    with c4:
        net = stats["month_revenue"] - stats["month_expenses"]
        color = "green" if net >= 0 else "red"
        st.markdown(styles.metric_card("Month Net P/L", f"PKR {net:,.0f}",
                                       f"Exp: PKR {stats['month_expenses']:,.0f}", color),
                    unsafe_allow_html=True)
    with c5:
        inv_rev = stats.get("inventory_revenue", 0)
        st.markdown(styles.metric_card("Inventory Sales", f"PKR {inv_rev:,.0f}",
                                       "From POS", "amber"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Birthday + Expiry Alerts ───────────────────────────────────────────────
    bday_members = db.get_birthday_members(days_ahead=3, gym_id=gym_id)
    expiring_now = db.get_expiring_members(days=3, gym_id=gym_id)
    absent_alert = db.get_absent_members(days=3, gym_id=gym_id)
    low_stock = db.get_stock_items(gym_id=gym_id, low_stock_only=True)

    if bday_members or expiring_now or absent_alert or low_stock:
        alerts = []
        for m, d_left in bday_members:
            label = "Today! 🎉" if d_left == 0 else f"in {d_left} day(s)"
            alerts.append(f"🎂 **{m.full_name}** birthday {label}")
        for m, d_left in expiring_now[:3]:
            alerts.append(f"⏰ **{m.full_name}** membership expires in {d_left} day(s)")
        for m in absent_alert[:3]:
            alerts.append(f"🚶 **{m.full_name}** absent 3+ days")
        for item in low_stock[:3]:
            alerts.append(f"📦 **{item.item_name}** stock low ({item.quantity} left)")

        if alerts:
            st.warning("**🔔 Attention Required:**  " + "  ·  ".join(alerts[:6]))

    st.divider()

    # ── Charts Row ─────────────────────────────────────────────────────────────
    col_rev, col_exp = st.columns(2)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    year = date.today().year

    with col_rev:
        st.markdown("**💰 Monthly Revenue (PKR)**")
        rev = db.get_monthly_revenue(gym_id=gym_id, year=year)
        rev_df = pd.DataFrame({"Month": month_names,
                                "Revenue (PKR)": [rev[i] for i in range(1, 13)]}).set_index("Month")
        st.bar_chart(rev_df, color="#7C3AED")

    with col_exp:
        st.markdown("**📉 Monthly Expenses (PKR)**")
        expenses = db.get_expenses(gym_id=gym_id)
        monthly_exp = {i: 0.0 for i in range(1, 13)}
        for e in expenses:
            try:
                d = date.fromisoformat(e.expense_date)
                if d.year == year:
                    monthly_exp[d.month] += e.amount
            except Exception:
                pass
        exp_df = pd.DataFrame({"Month": month_names,
                                "Expenses (PKR)": [monthly_exp[i] for i in range(1, 13)]}).set_index("Month")
        st.bar_chart(exp_df, color="#F87171")

    st.divider()

    # ── Peak Hour Analytics ────────────────────────────────────────────────────
    st.markdown("**⏰ Peak Hour Analytics — Busiest Times (by Attendance Record Time)**")
    hour_data = db.get_attendance_by_hour(gym_id=gym_id)
    if any(hour_data.values()):
        peak_hour = max(hour_data, key=lambda h: hour_data[h])
        peak_count = hour_data[peak_hour]
        ph1, ph2 = st.columns([3, 1])
        with ph1:
            hour_labels = [f"{h:02d}:00" for h in range(24)]
            ph_df = pd.DataFrame({
                "Hour": hour_labels,
                "Entries": [hour_data[h] for h in range(24)],
            }).set_index("Hour")
            st.bar_chart(ph_df, color="#34D399")
        with ph2:
            am_pm = f"{'AM' if peak_hour < 12 else 'PM'}"
            hour_12 = peak_hour if peak_hour <= 12 else peak_hour - 12
            st.markdown(styles.metric_card(
                "Peak Hour", f"{hour_12}:00 {am_pm}",
                f"{peak_count} check-ins", "green"
            ), unsafe_allow_html=True)
            total_att = sum(hour_data.values())
            st.markdown(styles.metric_card(
                "Total Logged", total_att, "all-time entries", "blue"
            ), unsafe_allow_html=True)
    else:
        st.info("No attendance records yet — peak hour data will appear as members check in.")

    st.divider()

    # ── Attendance Leaderboard ──────────────────────────────────────────────────
    st.markdown("**🏆 Monthly Attendance Leaderboard + Streak Counter**")
    leaderboard = db.get_attendance_leaderboard(gym_id=gym_id, limit=10)
    if leaderboard:
        lb_rows = []
        for rank, entry in enumerate(leaderboard, 1):
            m = entry["member"]
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            lb_rows.append({
                "Rank": medal,
                "Name": m.full_name,
                "Serial": m.serial_number,
                "Sessions This Month": entry["count"],
                "Streak": f"🔥 {entry['streak']} days" if entry["streak"] >= 3 else f"{entry['streak']} days",
            })
        st.dataframe(pd.DataFrame(lb_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No attendance data yet.")

    st.divider()

    # ── Recent Scan-Ins (live log from QR attendance kiosk) ───────────────────
    st.markdown("**🎯 Recent Scan-Ins (Today)** — live from the QR attendance scanner")
    scans = db.get_recent_scans(gym_id=gym_id, limit=10, today_only=True)
    if scans:
        scan_rows = [{
            "Time":      s["time"],
            "Member":    s["name"],
            "Serial":    s["serial"],
            "Gym":       s["gym"],
            "Marked By": s["marked_by"],
        } for s in scans]
        st.dataframe(pd.DataFrame(scan_rows), use_container_width=True, hide_index=True)
    else:
        st.caption("No QR check-ins yet today.")

    st.divider()


    # ── Recent Activity ─────────────────────────────────────────────────────────
    col_mem, col_fee = st.columns(2)

    with col_mem:
        st.markdown("**👥 Recent Registrations**")
        members = db.get_members(gym_id=gym_id)[:8]
        # Sabhi fee records fetch kar lein taake status check ho sake
        all_fees = db.get_fee_records(gym_id=gym_id)
        paid_member_ids = {f.member_id for f in all_fees} 

        if members:
            rows = [{
                "Serial": m.serial_number,
                "Name": m.full_name,
                "Status": "✅ Paid" if m.id in paid_member_ids else "❌ Pending",
                "Type": m.membership_type,
                "Joined": m.join_date,
            } for m in members]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No members yet.")

    with col_fee:
        st.markdown("**🧾 Recent Fee Collections**")
        fees = db.get_fee_records(gym_id=gym_id)[:8]
        if fees:
            rows = []
            for f in fees:
                mem = db.get_member(f.member_id)
                rows.append({
                    "Receipt": f.receipt_number,
                    "Member": mem.full_name if mem else "—",
                    "Amount": f"PKR {f.amount:,.2f}",
                    "Method": f.payment_method,
                    "Date": f.payment_date,
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No fee records yet.")

    

    # ── Expiring Memberships Alert ─────────────────────────────────────────────
    expiring = db.get_expiring_members(days=7, gym_id=gym_id)
    if expiring:
        st.markdown(f"**⚠️ {len(expiring)} Membership(s) Expiring in 7 Days**")
        rows = [{
            "Serial": m.serial_number,
            "Name": m.full_name,
            "Phone": m.phone or "—",
            "Expires": m.expiry_date,
            "Days Left": days_left,
        } for m, days_left in expiring]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Per-Gym Summary ────────────────────────────────────────────────────────
    if role == "admin" and not gym_id and len(gyms) > 1:
        st.divider()
        st.markdown("**🏢 Multi-Gym Control Panel — Per-Gym Summary**")
        gym_rows = []
        for g in gyms:
            gs = db.get_stats(g.id)
            gym_rows.append({
                "Gym": g.name,
                "Members": gs["total_members"],
                "Active": gs["active_members"],
                "Revenue": f"PKR {gs['total_revenue']:,.0f}",
                "Expenses": f"PKR {gs['total_expenses']:,.0f}",
                "Net P/L": f"PKR {gs['net_profit']:,.0f}",
                "Inventory": f"PKR {gs.get('inventory_revenue', 0):,.0f}",
            })
        st.dataframe(pd.DataFrame(gym_rows), use_container_width=True, hide_index=True)