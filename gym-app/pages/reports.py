import streamlit as st
import pandas as pd
import io
from datetime import date
import database as db
import styles


MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def render(gym_id, role):
    styles.page_header("📈", "Income vs Expenditure Report",
                       "Munafa aur Kharcha — Complete financial reconciliation")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    fc1, fc2, fc3 = st.columns([2, 1, 1])
    with fc1:
        if gym_id:
            sel_gid = gym_id
            gname = next((g.name for g in gyms if g.id == gym_id), "")
            st.text_input("Gym (Multi-Gym Control)", value=gname, disabled=True,
                          key="rpt_gym_display")
        else:
            opts = {"🌐 All Gyms": None} | {f"🏋️ {g.name}": g.id for g in gyms}
            chosen = st.selectbox("Gym Location / Switch Gym", list(opts.keys()),
                                  key="rpt_gym")
            sel_gid = opts[chosen]
    with fc2:
        year = st.selectbox("Year",
                            list(range(date.today().year, date.today().year - 5, -1)),
                            key="rpt_year")
    with fc3:
        st.write("")
        st.write("")
        export_all = st.button("⬇️ Export Full Report", use_container_width=True,
                               key="rpt_export_btn")

    st.divider()

    rev_monthly = db.get_monthly_revenue(gym_id=sel_gid, year=year)
    total_revenue = sum(rev_monthly.values())

    expenses = db.get_expenses(gym_id=sel_gid)
    exp_monthly: dict[int, float] = {i: 0.0 for i in range(1, 13)}
    for e in expenses:
        try:
            d = date.fromisoformat(e.expense_date)
            if d.year == year:
                exp_monthly[d.month] += e.amount
        except Exception:
            pass
    total_expenses = sum(exp_monthly.values())
    net_profit = total_revenue - total_expenses
    margin_pct = (net_profit / total_revenue * 100) if total_revenue > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(styles.metric_card("Total Revenue", f"PKR {total_revenue:,.0f}",
                                       f"Year {year}", "green"), unsafe_allow_html=True)
    with k2:
        st.markdown(styles.metric_card("Total Expenditure", f"PKR {total_expenses:,.0f}",
                                       f"Year {year}", "red"), unsafe_allow_html=True)
    with k3:
        color = "green" if net_profit >= 0 else "red"
        st.markdown(styles.metric_card("Net Profit / Loss", f"PKR {net_profit:,.0f}",
                                       "Munafa / Nuqsan", color), unsafe_allow_html=True)
    with k4:
        st.markdown(styles.metric_card("Profit Margin", f"{margin_pct:.1f}%",
                                       "Revenue retained", "blue"), unsafe_allow_html=True)

    st.divider()

    st.markdown("**📊 Monthly Income vs Expenditure — Comparison Chart**")
    chart_data = pd.DataFrame({
        "Month": MONTH_NAMES,
        "Revenue (PKR)": [rev_monthly[i] for i in range(1, 13)],
        "Expenses (PKR)": [exp_monthly[i] for i in range(1, 13)],
    }).set_index("Month")
    st.bar_chart(chart_data, color=["#34D399", "#F87171"])

    st.divider()

    st.markdown("**📋 Monthly Breakdown — Mahana Hissab**")
    table_rows = []
    for i in range(1, 13):
        rev = rev_monthly[i]
        exp = exp_monthly[i]
        net = rev - exp
        pct = (net / rev * 100) if rev > 0 else 0.0
        table_rows.append({
            "Month": MONTH_NAMES[i - 1],
            "Revenue (PKR)": f"{rev:,.2f}",
            "Expenses (PKR)": f"{exp:,.2f}",
            "Net Profit (PKR)": f"{net:,.2f}",
            "Profit Margin": f"{pct:.1f}%",
            "Status": "✅ Profit" if net >= 0 else "❌ Loss",
        })
    table_rows.append({
        "Month": "TOTAL",
        "Revenue (PKR)": f"{total_revenue:,.2f}",
        "Expenses (PKR)": f"{total_expenses:,.2f}",
        "Net Profit (PKR)": f"{net_profit:,.2f}",
        "Profit Margin": f"{margin_pct:.1f}%",
        "Status": "✅ Profit" if net_profit >= 0 else "❌ Loss",
    })

    df_table = pd.DataFrame(table_rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True, height=460)

    st.divider()

    st.markdown("**💸 Expenditure by Category — Kharche ka Hissab**")
    cat_data = db.get_expenses_by_category(sel_gid)
    if cat_data:
        cc1, cc2 = st.columns([2, 3])
        with cc1:
            cat_rows = [{"Category": r["category"], "Amount (PKR)": f"{r['total']:,.2f}"}
                        for r in cat_data]
            st.dataframe(pd.DataFrame(cat_rows), use_container_width=True, hide_index=True)
        with cc2:
            cat_chart = pd.DataFrame({
                "Category": [r["category"] for r in cat_data],
                "Amount": [r["total"] for r in cat_data],
            }).set_index("Category")
            st.bar_chart(cat_chart, color="#A78BFA")
    else:
        st.info("No expense data yet.")

    st.divider()

    if role == "admin" and not sel_gid and len(gyms) > 1:
        st.markdown("**🏢 Per-Gym Financial Summary — Har Gym ka Hissab**")
        gym_rows = []
        for g in gyms:
            rev = sum(db.get_monthly_revenue(gym_id=g.id, year=year).values())
            exp_list = db.get_expenses(gym_id=g.id)
            exp = sum(e.amount for e in exp_list if e.expense_date[:4] == str(year))
            net = rev - exp
            gym_rows.append({
                "Gym": g.name,
                "Revenue (PKR)": f"{rev:,.0f}",
                "Expenses (PKR)": f"{exp:,.0f}",
                "Net (PKR)": f"{net:,.0f}",
                "Status": "✅ Profit" if net >= 0 else "❌ Loss",
            })
        st.dataframe(pd.DataFrame(gym_rows), use_container_width=True, hide_index=True)

    if export_all:
        buf = io.StringIO()
        df_table.to_csv(buf, index=False)
        st.download_button(
            "📥 Download P&L Report CSV",
            data=buf.getvalue().encode(),
            file_name=f"income_expenditure_{year}_{sel_gid or 'all'}.csv",
            mime="text/csv",
            use_container_width=True,
            key="rpt_download_csv",
        )
