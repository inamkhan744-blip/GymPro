import streamlit as st
import pandas as pd
from datetime import date
import database as db
import styles
import urllib.parse


def make_wa_link(phone: str, message: str) -> str:
    clean = "".join(c for c in phone if c.isdigit() or c == "+")
    if clean.startswith("0"):
        clean = "+92" + clean[1:]
    return f"https://wa.me/{clean}?text={urllib.parse.quote(message)}"


def render(gym_id, role):
    styles.page_header("📏", "Member Progress Tracker",
                       "Monthly weight & body measurements with progress graphs")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    tab_record, tab_view = st.tabs(["📝 Record Measurements", "📈 Progress Graph"])

    # ── Record ─────────────────────────────────────────────────────────────────
    with tab_record:
        fc1, fc2 = st.columns([2, 2])
        with fc1:
            if gym_id:
                sel_gid = gym_id
                st.text_input("Gym", value=next((g.name for g in gyms if g.id == gym_id), ""),
                              disabled=True, key="pr_gym_display")
            else:
                opts = {g.name: g.id for g in gyms}
                chosen = st.selectbox("Gym", list(opts.keys()), key="pr_gym")
                sel_gid = opts[chosen]
        with fc2:
            members = db.get_members(gym_id=sel_gid, status="Active")
            if not members:
                st.info("No active members.")
                st.stop()
            mem_opts = {f"{m.serial_number} — {m.full_name}": m.id for m in members}
            sel_label = st.selectbox("Member", list(mem_opts.keys()), key="pr_member")
            sel_mid = mem_opts[sel_label]
            sel_m = next((m for m in members if m.id == sel_mid), None)

        if not sel_m:
            st.stop()

        # Show latest record for reference
        records = db.get_body_measurements(sel_mid)
        if records:
            latest = records[-1]
            st.markdown(
                f"**Last recorded:** {latest.recorded_date} — "
                f"Weight: **{latest.weight_kg} kg** | "
                f"Waist: **{latest.waist_cm or '—'} cm** | "
                f"Chest: **{latest.chest_cm or '—'} cm**"
            )

        st.divider()
        with st.form("progress_record_form", clear_on_submit=True):
            st.markdown("**Enter New Measurements**")
            r1, r2, r3 = st.columns(3)
            with r1:
                rec_date = st.date_input("Date", value=date.today(), key="pr_date")
                weight = st.number_input("Weight (kg)", min_value=0.0, max_value=300.0,
                                          step=0.1, format="%.1f", key="pr_weight")
                body_fat = st.number_input("Body Fat %", min_value=0.0, max_value=60.0,
                                            step=0.1, format="%.1f", value=0.0, key="pr_bodyfat")
            with r2:
                chest = st.number_input("Chest (cm)", min_value=0.0, max_value=200.0,
                                         step=0.5, format="%.1f", value=0.0, key="pr_chest")
                waist = st.number_input("Waist (cm)", min_value=0.0, max_value=200.0,
                                         step=0.5, format="%.1f", value=0.0, key="pr_waist")
            with r3:
                hips = st.number_input("Hips (cm)", min_value=0.0, max_value=200.0,
                                        step=0.5, format="%.1f", value=0.0, key="pr_hips")
                bicep = st.number_input("Bicep (cm)", min_value=0.0, max_value=100.0,
                                         step=0.5, format="%.1f", value=0.0, key="pr_bicep")
            notes = st.text_area("Notes", height=70, key="pr_notes",
                                  placeholder="Observations, diet notes, trainer remarks…")

            if st.form_submit_button("💾 Save Measurements", type="primary",
                                     use_container_width=True):
                ok, msg = db.add_body_measurement(
                    member_id=sel_mid,
                    recorded_date=rec_date,
                    weight_kg=weight,
                    chest_cm=chest or None,
                    waist_cm=waist or None,
                    hips_cm=hips or None,
                    bicep_cm=bicep or None,
                    body_fat_pct=body_fat or None,
                    notes=notes,
                )
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(msg)

        # Past records table
        if records:
            st.divider()
            st.markdown(f"**📋 All Measurements for {sel_m.full_name}**")
            rows = [{
                "Date": r.recorded_date,
                "Weight (kg)": r.weight_kg,
                "Chest (cm)": r.chest_cm or "—",
                "Waist (cm)": r.waist_cm or "—",
                "Hips (cm)": r.hips_cm or "—",
                "Bicep (cm)": r.bicep_cm or "—",
                "Body Fat %": r.body_fat_pct or "—",
                "Notes": r.notes or "—",
                "_id": r.id,
            } for r in reversed(records)]
            df = pd.DataFrame(rows)
            st.dataframe(df.drop(columns=["_id"]), use_container_width=True, hide_index=True)

            if role == "admin":
                del_opts = {f"{r['Date']} — {r['Weight (kg)']} kg": r["_id"] for r in rows}
                sel_del = st.selectbox("Select record to delete", list(del_opts.keys()),
                                       key="pr_del_sel")
                if st.button("🗑️ Delete Record", key="pr_del_btn"):
                    db.delete_body_measurement(del_opts[sel_del])
                    st.success("Deleted.")
                    st.rerun()

    # ── Progress Graph ──────────────────────────────────────────────────────────
    with tab_view:
        fc3, fc4 = st.columns([2, 2])
        with fc3:
            if gym_id:
                sel_gid2 = gym_id
                st.text_input("Gym ", value=next((g.name for g in gyms if g.id == gym_id), ""),
                              disabled=True, key="pg_gym_display")
            else:
                opts2 = {g.name: g.id for g in gyms}
                chosen2 = st.selectbox("Gym ", list(opts2.keys()), key="pg_gym")
                sel_gid2 = opts2[chosen2]
        with fc4:
            members2 = db.get_members(gym_id=sel_gid2)
            if not members2:
                st.info("No members.")
                st.stop()
            mem_opts2 = {f"{m.serial_number} — {m.full_name}": m.id for m in members2}
            sel_label2 = st.selectbox("Member ", list(mem_opts2.keys()), key="pg_member")
            sel_mid2 = mem_opts2[sel_label2]

        recs = db.get_body_measurements(sel_mid2)
        sel_m2 = next((m for m in members2 if m.id == sel_mid2), None)

        if not recs:
            st.info("No measurements recorded yet. Add records in the Record tab.")
        else:
            df_g = pd.DataFrame([{
                "Date": r.recorded_date,
                "Weight (kg)": r.weight_kg,
                "Chest (cm)": r.chest_cm,
                "Waist (cm)": r.waist_cm,
                "Hips (cm)": r.hips_cm,
                "Bicep (cm)": r.bicep_cm,
                "Body Fat %": r.body_fat_pct,
            } for r in recs]).set_index("Date")

            # Weight change summary
            first_w = recs[0].weight_kg
            last_w = recs[-1].weight_kg
            delta_w = last_w - first_w
            sign = "▼" if delta_w < 0 else "▲"
            color = "green" if delta_w <= 0 else "red"

            kc1, kc2, kc3 = st.columns(3)
            kc1.markdown(styles.metric_card("Starting Weight", f"{first_w} kg",
                                            recs[0].recorded_date, "blue"), unsafe_allow_html=True)
            kc2.markdown(styles.metric_card("Current Weight", f"{last_w} kg",
                                            recs[-1].recorded_date, color), unsafe_allow_html=True)
            kc3.markdown(styles.metric_card("Total Change", f"{sign} {abs(delta_w):.1f} kg",
                                            f"Over {len(recs)} session(s)", color), unsafe_allow_html=True)

            st.divider()
            metric = st.selectbox("Show graph for",
                                  ["Weight (kg)", "Chest (cm)", "Waist (cm)", "Hips (cm)",
                                   "Bicep (cm)", "Body Fat %"],
                                  key="pg_metric")
            chart_df = df_g[[metric]].dropna()
            if not chart_df.empty:
                st.line_chart(chart_df, color="#7C3AED")
            else:
                st.info(f"No {metric} data recorded.")

            # WhatsApp progress share
            if sel_m2 and sel_m2.phone:
                st.divider()
                st.markdown("**📱 Share Progress via WhatsApp**")
                tip = db.get_health_tip(sel_mid2)
                gym_name = next((g.name for g in gyms if g.id == (sel_m2.gym_id)), "GymPro")
                change_str = f"lost {abs(delta_w):.1f} kg" if delta_w < 0 else f"gained {abs(delta_w):.1f} kg"
                msg = (
                    f"Hi {sel_m2.full_name}! 🏋️ Here's your progress update from {gym_name}:\n\n"
                    f"Starting weight: {first_w} kg\n"
                    f"Current weight: {last_w} kg\n"
                    f"You have {change_str} — keep it up!\n\n"
                    f"{tip}\n\n"
                    f"See you at the gym! 💪"
                )
                wa_link = make_wa_link(sel_m2.phone, msg)
                st.markdown(
                    f'<a href="{wa_link}" target="_blank" style="display:inline-block;'
                    f'background:#25D366;color:white;padding:0.5rem 1.5rem;'
                    f'border-radius:8px;font-weight:700;text-decoration:none;">💬 Send Progress on WhatsApp</a>',
                    unsafe_allow_html=True,
                )
