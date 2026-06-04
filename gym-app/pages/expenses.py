import streamlit as st
import pandas as pd
import io
from datetime import date
import database as db
import styles


def render(gym_id, role, current_user):
    styles.page_header("📉", "Daily Expenses", "Track and export all gym operational costs")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    tab_list, tab_add = st.tabs(["📋 Records", "➕ Add Expense"])

    # ── Records ────────────────────────────────────────────────────────────────
    with tab_list:
        f1, f2, f3, f4, f5 = st.columns([2, 1, 1, 1, 1])
        with f1:
            if gym_id:
                sel_gid = gym_id
                st.text_input("Gym", value=next((g.name for g in gyms if g.id == gym_id), ""),
                              disabled=True, key="exp_gym_display")
            else:
                opts = {"All Gyms": None} | {g.name: g.id for g in gyms}
                chosen = st.selectbox("Gym", list(opts.keys()), key="exp_gym")
                sel_gid = opts[chosen]
        with f2:
            cat_filter = st.selectbox("Category", ["All"] + db.EXPENSE_CATEGORIES, key="exp_cat")
        with f3:
            date_from = st.date_input("From", value=date.today().replace(day=1), key="exp_from")
        with f4:
            date_to = st.date_input("To", value=date.today(), key="exp_to")
        with f5:
            st.write("")
            st.write("")
            export = st.button("⬇️ Export CSV", use_container_width=True, key="exp_export")

        expenses = db.get_expenses(gym_id=sel_gid, category=cat_filter,
                                   date_from=date_from, date_to=date_to)
        total = sum(e.amount for e in expenses)

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Records", len(expenses))
        mc2.metric("Total Spent", f"PKR {total:,.2f}")
        mc3.metric("Average", f"PKR {(total / len(expenses)):,.2f}" if expenses else "PKR 0.00")
        st.divider()

        if expenses:
            rows = []
            for e in expenses:
                gym_name = next((g.name for g in gyms if g.id == e.gym_id), "—")
                rows.append({
                    "Date": e.expense_date,
                    "Gym": gym_name,
                    "Category": e.category,
                    "Description": e.description or "—",
                    "Amount": f"PKR {e.amount:,.2f}",
                    "Staff": e.staff_name or "—",
                    "ID": e.id,
                })
            df = pd.DataFrame(rows)
            display_df = df.drop(columns=["ID"])
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=350)

            if export:
                csv_buf = io.StringIO()
                display_df.to_csv(csv_buf, index=False)
                st.download_button(
                    "📥 Download CSV",
                    data=csv_buf.getvalue().encode(),
                    file_name=f"expenses_{date_from}_{date_to}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="exp_download",
                )

            st.divider()
            st.markdown("**📊 Breakdown by Category**")
            cat_totals = {}
            for e in expenses:
                cat_totals[e.category] = cat_totals.get(e.category, 0) + e.amount
            chart_df = pd.DataFrame(
                {"Category": list(cat_totals.keys()), "Amount (PKR)": list(cat_totals.values())}
            ).set_index("Category")
            st.bar_chart(chart_df, color="#F87171")

            if role == "admin":
                st.divider()
                st.markdown("**🗑️ Delete an Expense**")
                exp_opts = {
                    f"#{e.id} | {e.expense_date} | {e.category} | PKR {e.amount:.2f}": e.id
                    for e in expenses
                }
                sel_exp_label = st.selectbox("Select expense", list(exp_opts.keys()),
                                             key="exp_del_select")
                if st.button("Delete Selected", type="secondary", key="exp_del_btn"):
                    st.session_state["confirm_del_exp"] = exp_opts[sel_exp_label]
                if st.session_state.get("confirm_del_exp"):
                    st.warning("Delete this expense record?")
                    cc, cx = st.columns(2)
                    if cc.button("✅ Confirm", type="primary", key="exp_del_confirm"):
                        db.delete_expense(st.session_state["confirm_del_exp"])
                        st.success("Deleted.")
                        st.session_state.pop("confirm_del_exp", None)
                        st.rerun()
                    if cx.button("Cancel", key="exp_del_cancel"):
                        st.session_state.pop("confirm_del_exp", None)
                        st.rerun()
        else:
            st.info("No expenses match your filters.")

    # ── Add Expense ────────────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Record New Expense")
        gym_opts = {g.name: g.id for g in gyms}
        default_gym = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)

        with st.form("add_expense_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                gym_sel = st.selectbox("Gym *", list(gym_opts.keys()),
                                       index=list(gym_opts.keys()).index(default_gym),
                                       key="ae_gym_sel")
                amount = st.number_input("Amount (PKR) *", min_value=0.01, step=1.0,
                                         format="%.2f", key="ae_amount")
                category = st.selectbox("Category *", db.EXPENSE_CATEGORIES, key="ae_category")
            with c2:
                expense_date = st.date_input("Date *", value=date.today(), key="ae_date")
                description = st.text_area("Description", height=120, key="ae_description",
                                           placeholder="What was this expense for?")

            if st.form_submit_button("✅ Record Expense", type="primary", use_container_width=True):
                ok, msg = db.add_expense(
                    gym_id=gym_opts[gym_sel],
                    amount=amount, category=category,
                    description=description,
                    expense_date=expense_date,
                    staff_name=current_user,
                )
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(msg)
