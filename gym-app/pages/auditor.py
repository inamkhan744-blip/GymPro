import streamlit as st
import pandas as pd
import os
from datetime import date
import database as db
import styles

def render(gym_id, role, username):
    styles.page_header("🔍", "Independent Audit Module",
                       "Cross-Verification Log — Staff aur Auditor ka Data Milana")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    tab_headcount, tab_verify, tab_log, tab_summary = st.tabs([
        "👥 Headcount Verification",
        "✍️ Cross-Verification Log",
        "📋 Audit Log",
        "⚠️ Dispute / Discrepancy Flag",
    ])

    # ── Headcount Verification ─────────────────────────────────────────────────
    with tab_headcount:
        st.markdown("**Bando Ki Tadaad Check Karna** — Physical headcount aur system records verify karein.")

        # Gym selection
        gym_opts = {g.name: g.id for g in gyms}
        hsel_gid = gym_id if gym_id else gym_opts[st.selectbox("Switch Gym Location", list(gym_opts.keys()), key="hc_gym")]

        st.divider()
        st.markdown("### 🤳 Active Members List")

        # Function fetch karein
        active_members = db.get_active_members(hsel_gid)

        if active_members:
            for member in active_members:
                # Column design
                col_img, col_info, col_btn = st.columns([1, 4, 1.5])
                
                with col_img:
                    if member.photo_path:
                        # Path structure: /home/runner/workspace/gym-app/uploads/filename
                        base_path = os.path.join(os.getcwd(), "gym-app", "uploads")
                        filename = os.path.basename(member.photo_path)
                        full_path = os.path.join(base_path, filename)
                        
                        if os.path.exists(full_path):
                            st.image(full_path, width=50)
                        else:
                            st.write("👤")
                    else:
                        st.write("👤")
                
                with col_info:
                    st.write(f"**{member.full_name}**")
                    st.caption(f"ID: {member.id}")
                
                with col_btn:
                    if st.button("✅ Present", key=f"btn_{member.id}"):
                        # 1. Mark Attendance
                        ok, msg = db.mark_member_present(member.id, hsel_gid, date.today())
                        
                        # 2. Update Discrepancy
                        db.update_audit_by_member(member.id, "Verified")
                        
                        if ok:
                            st.toast(f"{member.full_name} Marked!")
                            st.rerun() # Refresh taake member list se hat jaye
                        else:
                            st.error(msg)
        else:
            st.success("🎉 Sab members verify ho chuke hain!")


    # ── Cross-Verification Log ─────────────────────────────────────────────────
    with tab_verify:
        st.markdown("**✍️ Cross-Verification Log** — Independent observation aur discrepancies check karein.")

        gym_opts2 = {g.name: g.id for g in gyms}
        sel_gid = gym_id if gym_id else gym_opts2[st.selectbox("Switch Gym Location", list(gym_opts2.keys()), key="cv_gym")]

        entry_type = st.radio("Entry Type", ["Fee Collection", "Expense"], horizontal=True, key="cv_entry_type")

        # --- Fee Collection Logic ---
        if entry_type == "Fee Collection":
            # 1. Fetch & Filter: Sirf wo records jo abhi tak verify nahi huye
            all_records = db.get_fee_records(gym_id=sel_gid)
            records = [r for r in all_records if not db.is_record_verified(r.id)]

            if not records:
                st.success("🎉 Sab fee records verify ho chuke hain!")
                st.stop()

            # 2. Selectbox
            selected_record = st.selectbox(
                "Select Fee Record to Audit", 
                records, 
                format_func=lambda x: f"#{x.id} | {(x.member.full_name if x.member else 'Unknown')} | PKR {x.amount:,.2f}"
            )
            
            ref_id, expected, member = selected_record.id, selected_record.amount, selected_record.member
            
            # --- Comparison Area ---
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown("### Comparison")
                st.metric("Staff Recorded Amount", f"PKR {expected:,.2f}")
            with c2:
                if member and hasattr(member, 'photo_path') and member.photo_path:
                    filename = os.path.basename(member.photo_path)
                    full_path = os.path.join("gym-app", "uploads", filename)
                    if os.path.exists(full_path):
                        st.image(full_path, width=100, caption=member.full_name)
                    else:
                        st.write("👤 No Photo")
                else:
                    st.write("👤 No Photo")

            # --- Verification Form ---
            with st.form("cross_verification_form", clear_on_submit=True):
                actual = st.number_input("Actual Amount Observed (PKR)", min_value=0.0, format="%.2f")
                description = st.text_input("Description / Notes")
                
                if st.form_submit_button("✅ Submit Cross-Verification", type="primary", use_container_width=True):
                    # Database submission call
                    status, msg = db.add_audit_entry(
                        gym_id=sel_gid, 
                        entry_type="fee", 
                        reference_id=ref_id,
                        expected_amount=expected, 
                        actual_amount=actual,
                        description=description, 
                        entry_date=str(date.today()),
                        verified_by=st.session_state.get("username", "Unknown") # <--- Yahan change karein
                    )
                    
                    if status:
                        if actual != expected:
                            st.error(f"⚠️ DISCREPANCY: Auditor observed {actual}, Staff recorded {expected}!")
                        else:
                            st.success("✅ MATCHED: Records are accurate.")
                        st.rerun() # Page refresh taake list update ho jaye
                    else:
                        st.error(f"Error: {msg}")

        else: # Expense Section
            st.info("Expense verification module under development.")





    # ── Audit Log ───────────────────────────────────────
    with tab_log:
        st.markdown("**Full Cross-Verification Log — Tamam Audit Entries**")

        # Filters
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        with f1:
            opts2 = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen2 = st.selectbox("Gym", list(opts2.keys()), key="log_gym")
            log_gid = opts2[chosen2]
        with f2:
            status_f = st.selectbox("Audit Status", ["All", "Verified", "Discrepancy", "Pending"], key="log_status")
        with f3:
            df_from = st.date_input("From", value=date.today().replace(day=1), key="log_from")
        with f4:
            df_to = st.date_input("To", value=date.today(), key="log_to")

        entries = db.get_audit_entries(gym_id=log_gid, status=status_f, date_from=df_from, date_to=df_to)

        # Stats
        v_count = sum(1 for e in entries if e.status == "Verified")
        d_count = sum(1 for e in entries if e.status == "Discrepancy")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Total", len(entries))
        mc2.metric("✅ Verified", v_count)
        mc3.metric("⚠️ Disputes", d_count)
        mc4.metric("🕐 Pending", len(entries) - v_count - d_count)

        st.divider()

        # Display Logs with Expandable Details
        if entries:
            for e in entries:
                # 1. Safe calculation
                diff = (e.actual_amount or 0) - (e.expected_amount or 0)
                status_color = "🟢" if e.status == "Verified" else "🔴" if e.status == "Discrepancy" else "🟡"

                # 2. Member data safely fetch karein
                member_info = None
                if e.entry_type == 'fee' and e.reference_id:
                    member_info = db.get_member_by_id(e.reference_id)

                # 3. Dynamic Title
                display_name = member_info.full_name if member_info else f"Ref: {e.reference_id}"

                with st.expander(f"{status_color} {e.entry_date} | {display_name} | Diff: {diff:+.2f} PKR"):

                    c_img, c_det = st.columns([1, 3])

                    with c_img:
                        if member_info and member_info.photo_path:
                            # Path logic
                            filename = os.path.basename(member_info.photo_path)
                            full_path = os.path.join(os.getcwd(), "gym-app", "uploads", filename)
                            if os.path.exists(full_path):
                                st.image(full_path, width=80)
                            else:
                                st.write("👤 No Image")
                        else:
                            st.write("👤 No Member")

                    with c_det:
                        st.write(f"**Member:** {member_info.full_name if member_info else 'Unknown Member'}")
                        st.write(f"**Expected:** {e.expected_amount:,.2f} | **Actual:** {e.actual_amount:,.2f}")
                        st.write(f"**Verified By:** {e.verified_by} | **Status:** {e.status}")

                    st.info(f"Notes: {e.description or 'No notes provided'}")

                    if e.status == "Discrepancy":
                        if st.button(f"✅ Mark as Resolved (ID: {e.id})", key=f"res_{e.id}"):
                            db.update_audit_status(e.id, "Resolved")
                            st.rerun()
        else:
            st.info("No audit entries found.")




    # ── Dispute / Discrepancy Flag ─────────────────────────────────────────────
    with tab_summary:
        st.markdown("### ⚠️ Dispute / Discrepancy Control Center")

        # 1. Financial Discrepancies
        st.subheader("💰 Financial Discrepancies")
        all_disc = [e for e in db.get_audit_entries(gym_id=gym_id, status="Discrepancy") if e.entry_type in ("fee", "expense")]

        if not all_disc:
            st.success("✅ Financial records clear!")
        else:
            total_var = sum(abs(e.actual_amount - e.expected_amount) for e in all_disc)
            st.metric("Total Financial Variance", f"PKR {total_var:,.2f}", delta=f"{len(all_disc)} Open Issues", delta_color="inverse")

            for e in all_disc:
                # Color coding: +ve profit/extra, -ve loss/shortage
                diff = e.actual_amount - e.expected_amount
                color = "🔴" if diff < 0 else "🟢"

                with st.expander(f"{color} {e.entry_date} | {e.entry_type.upper()} | Var: {diff:+,.2f} PKR"):
                    col1, col2 = st.columns(2)
                    col1.write(f"**Expected:** {e.expected_amount:,.2f}")
                    col1.write(f"**Observed:** {e.actual_amount:,.2f}")
                    col2.write(f"**Staff:** {e.verified_by}")
                    col2.write(f"**Notes:** {e.description or 'None'}")

                    # Action Buttons with Unique Keys
                    c1, c2 = st.columns(2)
                    if c1.button(f"✅ Mark Resolved (ID: {e.id})", key=f"dis_res_{e.id}"):
                        db.update_audit_status(e.id, "Resolved")
                        st.rerun()
                    if c2.button(f"🚩 Flag to Manager (ID: {e.id})", key=f"dis_flag_{e.id}"):
                        db.update_audit_status(e.id, "Manager Review")
                        st.rerun()

        st.divider()

        # 2. Headcount Discrepancies
        st.subheader("👥 Headcount Discrepancies")
        hc_disc = [e for e in db.get_audit_entries(gym_id=gym_id, status="Discrepancy") if "headcount" in e.entry_type]

        if not hc_disc:
            st.success("✅ Headcount is accurate!")
        else:
            for e in hc_disc:
                diff = int(e.actual_amount - e.expected_amount)
                st.warning(f"⚠️ **{e.entry_date}**: {e.entry_type.replace('_', ' ').title()} - Difference: {diff:+d}")
                # Headcount button with unique key
                if st.button(f"Resolve Headcount Issue {e.id}", key=f"hc_res_{e.id}"):
                    db.update_audit_status(e.id, "Resolved")
                    st.rerun()
