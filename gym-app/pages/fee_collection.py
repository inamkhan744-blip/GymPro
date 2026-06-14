import streamlit as st
import pandas as pd
import io
import os
import uuid
from datetime import date, timedelta
import database as db
import styles


def _generate_fee_receipt_html(receipt_number, member_name, serial, gym_name, amount, payment_method, period_end):
    """Thermal Printer ke liye fee collection ki slip ka HTML format"""
    today_str = date.today().strftime("%Y-%m-%d")

    html_code = f"""
    <html>
    <head>
        <style>
            @media print {{
                body {{ width: 80mm; margin: 0; padding: 5px; font-family: 'Courier New', Courier, monospace; font-size: 12px; }}
            }}
            .receipt-box {{ width: 100%; max-width: 300px; padding: 10px; border: 1px dashed #000; font-family: 'Courier New', Courier, monospace; color: #000; background: #fff; }}
            .text-center {{ text-align: center; }}
            .bold {{ font-weight: bold; }}
            .divider {{ border-top: 1px dashed #000; margin: 8px 0; }}
            .flex-space {{ display: flex; justify-content: space-between; }}
        </style>
    </head>
    <body>
        <div class="receipt-box">
            <div class="text-center bold" style="font-size: 16px;">{gym_name.upper()}</div>
            <div class="text-center" style="font-size: 10px;">FEE PAYMENT RECEIPT</div>
            <div class="divider"></div>
            <div class="flex-space"><span>Receipt No:</span><span class="bold">{receipt_number}</span></div>
            <div class="flex-space"><span>Date:</span><span>{today_str}</span></div>
            <div class="divider"></div>
            <div class="flex-space"><span>Member Serial:</span><span class="bold">{serial}</span></div>
            <div class="flex-space"><span>Name:</span><span class="bold">{member_name}</span></div>
            <div class="divider"></div>
            <div class="bold">PAYMENT DETAILS:</div>
            <div class="flex-space"><span>Fee Received:</span><span class="bold">PKR {amount:,.2f}</span></div>
            <div class="flex-space"><span>Method:</span><span>{payment_method}</span></div>
            <div class="flex-space"><span>Valid Till:</span><span class="bold">{period_end}</span></div>
            <div class="flex-space"><span>Status:</span><span class="bold">PAID ✅</span></div>
            <div class="divider"></div>
            <div class="text-center bold" style="margin-top: 10px;">Thank You For Your Payment! 🙏</div>
            <div class="text-center" style="font-size: 9px; color: #555; margin-top: 5px;">Software by Gym Master</div>
        </div>
        <script>
            window.print();
        </script>
    </body>
    </html>
    """
    return html_code


def get_member_payment_status(member):
    """Check if member's fee is paid or pending"""
    if not member or not hasattr(member, 'expiry_date') or not member.expiry_date:
        return "pending", "❌ No expiry date", "#ffc107", "black"
    
    try:
        expiry = pd.to_datetime(member.expiry_date).date()
        today = date.today()
        
        if expiry >= today:
            days_left = (expiry - today).days
            return "paid", f"✅ PAID ({days_left} days left)", "#28a745", "white"
        else:
            days_expired = (today - expiry).days
            return "pending", f"⏳ PENDING (Expired {days_expired} days ago)", "#dc3545", "white"
    except:
        return "pending", "⚠️ Invalid expiry date", "#ffc107", "black"


def render(gym_id, role, current_user):
    styles.page_header("💰", "Fee Collection", "Record, track, and manage membership fee payments")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    # ── SECTION 1: ADD NEW RECORD ──────────────────────────────────────────────
    st.markdown("### ➕ Collect Fee / Add New Payment Record")

    gym_opts = {g.name: g.id for g in gyms}
    default_gym = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)

    # ── GYM + SEARCH + MEMBER SELECTION (FORM SE BAHAR) ──
    c1, c2 = st.columns(2)

    with c1:
        gym_sel = st.selectbox(
            "Gym *",
            list(gym_opts.keys()),
            index=list(gym_opts.keys()).index(default_gym),
            key="cf_gym_sel"
        )
        sel_gym_id = gym_opts[gym_sel]
        members = db.get_members(gym_id=sel_gym_id)

        # 🔍 SEARCH BAR
        search_query = st.text_input(
            "🔍 Search Member (Name or Serial)",
            key="cf_search",
            placeholder="Type name or serial number..."
        )

        # Filter members
        if search_query:
            q = search_query.lower().strip()
            filtered_members = [
                m for m in members
                if q in m.full_name.lower() or q in str(m.serial_number).lower()
            ]
        else:
            filtered_members = members

        # 🆕 FILTER BY PAYMENT STATUS
        st.markdown("**Filter by Status:**")
        status_filter = st.radio(
            "",
            ["All Members", "✅ Paid Members Only", "⏳ Pending Members Only"],
            horizontal=True,
            key="status_filter"
        )
        
        # Apply status filter
        if status_filter == "✅ Paid Members Only":
            filtered_members = [
                m for m in filtered_members 
                if m.expiry_date and pd.to_datetime(m.expiry_date).date() >= date.today()
            ]
        elif status_filter == "⏳ Pending Members Only":
            filtered_members = [
                m for m in filtered_members 
                if not m.expiry_date or pd.to_datetime(m.expiry_date).date() < date.today()
            ]

        # 🆕 Create dropdown with status badges
        mem_opts = {}
        member_status_map = {}
        
        for m in filtered_members:
            status_type, status_text, bg_color, text_color = get_member_payment_status(m)
            # Format: Serial — Name [STATUS]
            label = f"{m.serial_number} — {m.full_name}  {status_text}"
            mem_opts[label] = m.id
            member_status_map[m.id] = {
                "status": status_type,
                "status_text": status_text,
                "expiry": m.expiry_date,
                "member": m
            }

        sel_mem = None
        member_id = None

        if not members:
            st.warning("No members in this gym.")
        elif not mem_opts:
            st.warning(f"No members match '{search_query}' or filter criteria. Try different keywords.")
        else:
            mem_sel = st.selectbox("Select Member *", list(mem_opts.keys()), key="cf_member_sel")
            member_id = mem_opts[mem_sel]
            sel_mem = next((m for m in filtered_members if m.id == member_id), None)

            if sel_mem:
                # 🖼️ MEMBER PICTURE & INFO with clear status
                pic_col, info_col = st.columns([1, 2])

                with pic_col:
                    member_photo = (
                        getattr(sel_mem, 'photo', None)
                        or getattr(sel_mem, 'photo_path', None)
                        or getattr(sel_mem, 'picture', None)
                        or getattr(sel_mem, 'image', None)
                        or getattr(sel_mem, 'photo_url', None)
                        or getattr(sel_mem, 'profile_picture', None)
                    )

                    photo_shown = False

                    if member_photo:
                        try:
                            if isinstance(member_photo, bytes):
                                st.image(member_photo, width=120)
                                photo_shown = True
                            elif isinstance(member_photo, str) and member_photo.strip():
                                if member_photo.startswith(('http://', 'https://', 'data:image')):
                                    st.image(member_photo, width=120)
                                    photo_shown = True
                                elif os.path.exists(member_photo):
                                    st.image(member_photo, width=120)
                                    photo_shown = True
                                else:
                                    for folder in ['', 'uploads/', 'photos/', 'static/', 'gym-app/uploads/', 'gym-app/photos/']:
                                        full_path = os.path.join(folder, member_photo)
                                        if os.path.exists(full_path):
                                            st.image(full_path, width=120)
                                            photo_shown = True
                                            break
                        except Exception:
                            photo_shown = False

                    if not photo_shown:
                        st.markdown(
                            "<div style='width:120px;height:120px;background:linear-gradient(135deg,#667eea,#764ba2);"
                            "border-radius:50%;display:flex;align-items:center;justify-content:center;"
                            "font-size:50px;color:white;box-shadow:0 4px 10px rgba(0,0,0,0.2);'>👤</div>",
                            unsafe_allow_html=True
                        )

                with info_col:
                    st.markdown(f"**👤 Name:** {sel_mem.full_name}")
                    st.markdown(f"**🔢 Serial:** {sel_mem.serial_number}")
                    st.caption(f"💵 Standard fee: **PKR {sel_mem.fee_amount:,.2f}**")
                    
                    # 🆕 BIG STATUS BADGE
                    status_type, status_text, bg_color, text_color = get_member_payment_status(sel_mem)
                    st.markdown(
                        f"<div style='background:{bg_color};color:{text_color};padding:8px 15px;border-radius:25px;"
                        f"display:inline-block;font-weight:bold;margin-top:5px;'>{status_text}</div>",
                        unsafe_allow_html=True
                    )
                    
                    if sel_mem.expiry_date:
                        try:
                            expiry = pd.to_datetime(sel_mem.expiry_date).date()
                            st.caption(f"📅 Current expiry: {expiry}")
                        except:
                            st.caption(f"📅 Current expiry: {sel_mem.expiry_date}")
                    else:
                        st.caption("📅 No expiry date set")

    # ── FORM (Payment details + Submit) ──
    with st.form("collect_fee_form", clear_on_submit=True):
        f_c1, f_c2 = st.columns(2)

        with f_c1:
            st.markdown("**Payment Details**")
            default_amount = float(sel_mem.fee_amount) if sel_mem and hasattr(sel_mem, 'fee_amount') else 0.01
            amount = st.number_input(
                "Amount (PKR) *",
                min_value=0.01,
                value=default_amount,
                step=5.0,
                format="%.2f",
                key="cf_amount"
            )
            payment_method = st.selectbox("Payment Method *", db.PAYMENT_METHODS, key="cf_method")

        with f_c2:
            st.markdown("**Period & Date**")
            payment_date = st.date_input("Payment Date *", value=date.today(), key="cf_date")
            period_start = st.date_input("Period Start", value=date.today(), key="cf_period_start")
            
            # Suggest period end based on payment (default 30 days)
            default_end = date.today() + timedelta(days=30)
            if sel_mem and sel_mem.expiry_date:
                try:
                    current_expiry = pd.to_datetime(sel_mem.expiry_date).date()
                    if current_expiry > date.today():
                        default_end = current_expiry + timedelta(days=30)
                except:
                    pass
            
            period_end = st.date_input("Period End", value=default_end, key="cf_period_end")

        notes = st.text_area("Notes (optional)", height=80, key="cf_notes")

        submitted = st.form_submit_button(
            "✅ Record Payment & Print Slip",
            type="primary",
            use_container_width=True
        )

        if submitted:
            if not member_id:
                st.error("Select a member first (use search above).")
            elif amount <= 0:
                st.error("Amount must be positive.")
            elif not sel_mem:
                st.error("Member details missing.")
            else:
                ok, msg = db.add_fee_record(
                    member_id=member_id, gym_id=sel_gym_id, amount=amount,
                    payment_method=payment_method, payment_date=payment_date,
                    period_start=period_start, period_end=period_end,
                    collected_by=current_user, notes=notes
                )

                if ok:
                    db.update_member(member_id, expiry_date=str(period_end), status="Active")

                    generated_rcp = f"RCP-{uuid.uuid4().hex[:6].upper()}"
                    receipt_html = _generate_fee_receipt_html(
                        receipt_number=generated_rcp,
                        member_name=sel_mem.full_name,
                        serial=sel_mem.serial_number,
                        gym_name=gym_sel,
                        amount=amount,
                        payment_method=payment_method,
                        period_end=str(period_end)
                    )

                    st.components.v1.html(f"""
                        <script>
                            var w = window.open('', '_blank');
                            w.document.write({repr(receipt_html)});
                            w.document.close();
                        </script>
                    """, height=0)

                    ai_link = "https://gympro-ai.replit.app"
                    whatsapp_msg = f"Salam {sel_mem.full_name}, aapki fees (PKR {amount:,.2f}) receive ho gayi hai. Shukriya! \n\nApni progress aur diet plan yahan check karein: {ai_link}"

                    st.success(f"✅ {msg} · Membership extended to {period_end}!")
                    
                    # Show WhatsApp message
                    with st.expander("📱 WhatsApp Message (Copy & Send)"):
                        st.code(whatsapp_msg, language="text")
                        st.caption("💡 Tip: Copy this message and paste on WhatsApp")
                    
                    st.toast("Printing Slip... Please wait.", icon="🖨️")
                    st.balloons()
                else:
                    st.error(msg)

    st.divider()

    # ── SECTION 2: VIEW RECORDS ──────────────────────────────────────────────
    st.markdown("### 📋 Payment History & Records")
    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
    with f1:
        if gym_id:
            sel_gid = gym_id
            st.text_input("Gym", value=next((g.name for g in gyms if g.id == gym_id), ""), disabled=True, key="fc_gym_display")
        else:
            opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
            chosen = st.selectbox("Select Gym", list(opts.keys()), key="fc_gym")
            sel_gid = opts[chosen]
    with f2:
        date_from = st.date_input("From Date", value=date.today().replace(day=1), key="fc_from")
    with f3:
        date_to = st.date_input("To Date", value=date.today(), key="fc_to")
    with f4:
        st.write("")
        st.write("")
        export = st.button("⬇️ Export CSV", use_container_width=True, key="fc_export")

    records = db.get_fee_records(gym_id=sel_gid, date_from=date_from, date_to=date_to)

    total = sum(r.amount for r in records)
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Total Records", len(records))
    mc2.metric("Total Collected", f"PKR {total:,.2f}")
    mc3.metric("Average Amount", f"PKR {(total / len(records)):,.2f}" if records else "PKR 0.00")

    if records:
        rows = []
        for r in records:
            mem = db.get_member(r.member_id)
            gym_name = next((g.name for g in gyms if g.id == r.gym_id), "—")
            
            # 🆕 Get current payment status for this member
            current_status = "—"
            if mem:
                status_type, status_text, _, _ = get_member_payment_status(mem)
                current_status = status_text
            
            rows.append({
                "Record_ID": r.id,
                "Receipt": r.receipt_number,
                "Member": mem.full_name if mem else "—",
                "Member_ID": r.member_id,
                "Serial": mem.serial_number if mem else "—",
                "Gym": gym_name,
                "Gym_ID": r.gym_id,
                "Amount": r.amount,
                "Method": r.payment_method,
                "Date": r.payment_date,
                "Period Start": r.period_start,
                "Period End": r.period_end,
                "Collected By": r.collected_by or "—",
                "Notes": r.notes or "",
                "Current Status": current_status  # 🆕 New column
            })
        df = pd.DataFrame(rows)

        # Display Table with status column
        display_df = df.copy()
        display_df["Amount"] = display_df["Amount"].apply(lambda x: f"PKR {x:,.2f}")
        display_df["Period"] = display_df.apply(lambda r: f"{r['Period Start'] or '—'} → {r['Period End'] or '—'}", axis=1)
        
        # 🆕 Show table with Current Status column
        st.dataframe(
            display_df[["Member", "Serial", "Amount", "Method", "Date", "Period", "Current Status"]], 
            use_container_width=True, 
            hide_index=True, 
            height=300
        )

        # ── SECTION 3: EDIT & DELETE ACTIONS (🔴 ONLY FOR ADMIN / OWNER) ──
        if str(role).lower() in ["admin", "owner"]:
            st.markdown("### 🛠️ Record Actions (Admin Only)")

            record_opts = {f"Receipt: {r['Receipt']} — {r['Member']} (PKR {r['Amount']})": r for r in rows}
            selected_label = st.selectbox("Select Record to Edit or Delete", list(record_opts.keys()), key="action_record_select")
            selected_record = record_opts[selected_label]

            act_tab1, act_tab2 = st.tabs(["✏️ Edit / Update Record", "🗑️ Delete Record"])

            # ── TAB 3.1: EDIT/UPDATE ENTRY ──
            with act_tab1:
                with st.form("edit_fee_form"):
                    st.write(f"Editing Receipt: **{selected_record['Receipt']}** for **{selected_record['Member']}**")
                    e_c1, e_c2 = st.columns(2)
                    with e_c1:
                        new_amount = st.number_input("Update Amount (PKR)", min_value=0.01, value=float(selected_record['Amount']), step=5.0, format="%.2f")
                        new_method = st.selectbox("Update Payment Method", db.PAYMENT_METHODS, index=db.PAYMENT_METHODS.index(selected_record['Method']) if selected_record['Method'] in db.PAYMENT_METHODS else 0)
                    with e_c2:
                        # Date conversion check
                        p_start_val = pd.to_datetime(selected_record['Period Start']).date() if selected_record['Period Start'] else date.today()
                        p_end_val = pd.to_datetime(selected_record['Period End']).date() if selected_record['Period End'] else date.today()

                        new_p_start = st.date_input("Update Period Start", value=p_start_val)
                        new_p_end = st.date_input("Update Period End", value=p_end_val)

                    new_notes = st.text_area("Update Notes", value=selected_record['Notes'])

                    if st.form_submit_button("💾 Save Changes (Update)", type="primary", use_container_width=True):
                        if hasattr(db, 'update_fee_record'):
                            ok, msg = db.update_fee_record(
                                selected_record['Record_ID'], 
                                new_amount, 
                                new_method, 
                                new_p_start, 
                                new_p_end, 
                                new_notes
                            )
                            
                            if ok:
                                db.update_member(selected_record['Member_ID'], expiry_date=str(new_p_end))
                                st.success("✅ Record updated successfully!")
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("⚠️ database.py mein 'update_fee_record' function nahi mila.")

            # ── TAB 3.2: DELETE ENTRY ──
            with act_tab2:
                st.warning(f"⚠️ Kya aap waqai Receipt **{selected_record['Receipt']}** ko hamesha ke liye delete karna chahte hain?")
                st.caption("Ye action undo nahi ho sakta.")
                if st.button("🚨 Confirm Permanent Delete", type="primary", use_container_width=True):
                    if hasattr(db, 'delete_fee_record'):
                        ok, msg = db.delete_fee_record(selected_record['Record_ID'])
                        if ok:
                            st.success("✅ Record successfully deleted!")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("⚠️ database.py mein 'delete_fee_record' function missing hai.")

        if export:
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False)
            st.download_button(
                "📥 Download CSV", 
                data=csv_buf.getvalue().encode(), 
                file_name=f"fee_collection_{date_from}_{date_to}.csv", 
                mime="text/csv", 
                use_container_width=True
            )
    else:
        st.info("📭 No records found for the selected filters.")

    # ── FOOTER: Summary of pending members ──
    st.divider()
    with st.expander("📊 Fee Collection Summary", expanded=False):
        all_members = db.get_members(gym_id=sel_gym_id) if sel_gym_id else []
        paid_count = 0
        pending_count = 0
        
        for member in all_members:
            status_type, _, _, _ = get_member_payment_status(member)
            if status_type == "paid":
                paid_count += 1
            else:
                pending_count += 1
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Members", len(all_members))
        col2.metric("✅ Paid Members", paid_count, delta=f"{paid_count - pending_count}" if all_members else None)
        col3.metric("⏳ Pending Members", pending_count, delta=f"-{pending_count}" if pending_count > 0 else None)
        
        if pending_count > 0:
            st.warning(f"⚠️ {pending_count} members ki fee pending hai! Inhe collect karein.")