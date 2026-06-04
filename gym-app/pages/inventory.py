import streamlit as st
import pandas as pd
import io
from datetime import date
import database as db
import styles


def render(gym_id, role):
    styles.page_header("📦", "Stock & Inventory",
                       "Point of Sale — Manage supplements, equipment & daily sales")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    tab_stock, tab_pos, tab_reports, tab_add = st.tabs([
        "📋 Stock List", "🛒 Point of Sale", "📊 Sales Report", "➕ Add Item"
    ])

    # ── Gym selector ───────────────────────────────────────────────────────────
    def gym_selector(key_suffix):
        if gym_id:
            st.text_input("Gym", value=next((g.name for g in gyms if g.id == gym_id), ""),
                          disabled=True, key=f"inv_gym_display_{key_suffix}")
            return gym_id
        else:
            opts = {g.name: g.id for g in gyms}
            chosen = st.selectbox("Gym", list(opts.keys()), key=f"inv_gym_{key_suffix}")
            return opts[chosen]

    # ── Stock List ─────────────────────────────────────────────────────────────
    with tab_stock:
        sc1, sc2 = st.columns([3, 1])
        with sc1:
            sel_gid = gym_selector("stock")
        with sc2:
            st.write("")
            st.write("")
            low_only = st.checkbox("⚠️ Low Stock Only", key="inv_low_only")

        items = db.get_stock_items(gym_id=sel_gid, low_stock_only=low_only)

        if not items:
            st.info("No inventory items found. Add items in the 'Add Item' tab.")
        else:
            low_count = sum(1 for i in items if i.quantity <= i.min_quantity)
            kc1, kc2, kc3, kc4 = st.columns(4)
            kc1.markdown(styles.metric_card("Total Items", len(items), "SKUs", "blue"),
                         unsafe_allow_html=True)
            kc2.markdown(styles.metric_card("Low Stock Alerts", low_count,
                                            "Below min level", "red"), unsafe_allow_html=True)
            total_stock_val = sum(i.purchase_price * i.quantity for i in items)
            kc3.markdown(styles.metric_card("Stock Value", f"PKR {total_stock_val:,.0f}",
                                            "At purchase price", "amber"), unsafe_allow_html=True)
            total_pot = sum(i.sale_price * i.quantity for i in items)
            kc4.markdown(styles.metric_card("Potential Revenue", f"PKR {total_pot:,.0f}",
                                            "At sale price", "green"), unsafe_allow_html=True)

            st.divider()
            rows = []
            for i in items:
                gname = next((g.name for g in gyms if g.id == i.gym_id), "—")
                alert = "🔴 Low Stock" if i.quantity <= i.min_quantity else ("🟡 Watch" if i.quantity <= i.min_quantity * 2 else "🟢 OK")
                profit = i.sale_price - i.purchase_price
                rows.append({
                    "Item": i.item_name,
                    "Category": i.category,
                    "Gym": gname,
                    "Purchase (PKR)": f"{i.purchase_price:,.2f}",
                    "Sale (PKR)": f"{i.sale_price:,.2f}",
                    "Profit/Unit": f"{profit:,.2f}",
                    "Qty": i.quantity,
                    "Min Qty": i.min_quantity,
                    "Status": alert,
                    "_id": i.id,
                })
            df = pd.DataFrame(rows)
            st.dataframe(df.drop(columns=["_id"]), use_container_width=True,
                         hide_index=True, height=380)

            # Edit / Delete
            if role == "admin":
                st.divider()
                st.markdown("**✏️ Edit Stock Item**")
                item_opts = {f"{i.item_name} (Qty: {i.quantity})": i.id for i in items}
                sel_item_label = st.selectbox("Select item", list(item_opts.keys()),
                                              key="inv_edit_sel")
                sel_item = next((i for i in items if i.id == item_opts[sel_item_label]), None)
                if sel_item:
                    with st.form(f"edit_stock_{sel_item.id}"):
                        ec1, ec2, ec3 = st.columns(3)
                        with ec1:
                            new_name = st.text_input("Item Name", value=sel_item.item_name,
                                                     key=f"es_name_{sel_item.id}")
                            new_cat = st.selectbox("Category", db.STOCK_CATEGORIES,
                                                   index=db.STOCK_CATEGORIES.index(sel_item.category)
                                                   if sel_item.category in db.STOCK_CATEGORIES else 0,
                                                   key=f"es_cat_{sel_item.id}")
                        with ec2:
                            new_buy = st.number_input("Purchase Price (PKR)",
                                                       value=float(sel_item.purchase_price),
                                                       min_value=0.0, step=1.0,
                                                       key=f"es_buy_{sel_item.id}")
                            new_sell = st.number_input("Sale Price (PKR)",
                                                        value=float(sel_item.sale_price),
                                                        min_value=0.0, step=1.0,
                                                        key=f"es_sell_{sel_item.id}")
                        with ec3:
                            new_qty = st.number_input("Quantity", value=int(sel_item.quantity),
                                                       min_value=0, step=1,
                                                       key=f"es_qty_{sel_item.id}")
                            new_min = st.number_input("Min Alert Qty",
                                                       value=int(sel_item.min_quantity),
                                                       min_value=0, step=1,
                                                       key=f"es_min_{sel_item.id}")
                        es1, es2 = st.columns(2)
                        if es1.form_submit_button("💾 Update", type="primary"):
                            db.update_stock_item(sel_item.id, item_name=new_name,
                                                 category=new_cat, purchase_price=new_buy,
                                                 sale_price=new_sell, quantity=new_qty,
                                                 min_quantity=new_min)
                            st.success("Item updated.")
                            st.rerun()
                        if es2.form_submit_button("🗑️ Delete Item"):
                            db.delete_stock_item(sel_item.id)
                            st.success("Deleted.")
                            st.rerun()

    # ── Point of Sale ──────────────────────────────────────────────────────────
    with tab_pos:
        st.markdown("**🛒 Point of Sale — Sell Items to Members**")
        sel_gid_pos = gym_selector("pos")

        items_pos = db.get_stock_items(gym_id=sel_gid_pos)
        if not items_pos:
            st.info("No stock items available.")
        else:
            with st.form("pos_form", clear_on_submit=True):
                pc1, pc2 = st.columns(2)
                with pc1:
                    item_opts_pos = {f"{i.item_name} — PKR {i.sale_price:.0f} (Qty: {i.quantity})": i.id
                                     for i in items_pos if i.quantity > 0}
                    if not item_opts_pos:
                        st.warning("All items are out of stock.")
                        st.stop()
                    sel_pos_label = st.selectbox("Select Item *", list(item_opts_pos.keys()),
                                                 key="pos_item_sel")
                    sel_pos_id = item_opts_pos[sel_pos_label]
                    sel_pos_item = next((i for i in items_pos if i.id == sel_pos_id), None)

                    qty_to_sell = st.number_input("Quantity", min_value=1,
                                                   max_value=sel_pos_item.quantity if sel_pos_item else 1,
                                                   step=1, value=1, key="pos_qty")
                    custom_price = st.number_input(
                        "Override Sale Price (PKR)",
                        value=float(sel_pos_item.sale_price) if sel_pos_item else 0.0,
                        min_value=0.0, step=1.0, key="pos_price",
                    )
                with pc2:
                    members_pos = db.get_members(gym_id=sel_gid_pos, status="Active")
                    mem_opts_pos = {"Walk-in (No Member)": None} | {
                        f"{m.serial_number} — {m.full_name}": m.id for m in members_pos
                    }
                    mem_sel_pos = st.selectbox("Member", list(mem_opts_pos.keys()),
                                               key="pos_member_sel")
                    pos_member_id = mem_opts_pos[mem_sel_pos]
                    sale_date_pos = st.date_input("Sale Date", value=date.today(), key="pos_date")
                    pos_notes = st.text_input("Notes / Reference", key="pos_notes")

                if sel_pos_item:
                    total_preview = qty_to_sell * custom_price
                    st.info(f"💰 Total: **PKR {total_preview:,.2f}** "
                            f"({qty_to_sell} × PKR {custom_price:.2f})")

                if st.form_submit_button("✅ Process Sale", type="primary",
                                         use_container_width=True):
                    current_user = st.session_state.get("username", "staff")
                    ok, msg = db.sell_stock_item(
                        stock_item_id=sel_pos_id,
                        gym_id=sel_gid_pos,
                        member_id=pos_member_id,
                        quantity_sold=qty_to_sell,
                        sale_price=custom_price,
                        sold_by=current_user,
                        sale_date=sale_date_pos,
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(msg)

    # ── Sales Report ───────────────────────────────────────────────────────────
    with tab_reports:
        st.markdown("**📊 Sales Report — Inventory Revenue**")
        rc1, rc2, rc3 = st.columns([2, 1, 1])
        with rc1:
            sel_gid_rep = gym_selector("rep")
        with rc2:
            rep_from = st.date_input("From", value=date.today().replace(day=1), key="inv_from")
        with rc3:
            rep_to = st.date_input("To", value=date.today(), key="inv_to")
        export_rep = st.button("⬇️ Export CSV", key="inv_export", use_container_width=True)

        sales = db.get_stock_sales(gym_id=sel_gid_rep, date_from=rep_from, date_to=rep_to)
        if not sales:
            st.info("No sales in this period.")
        else:
            total_revenue = sum(s.total_amount for s in sales)
            items_map = {i.id: i for i in db.get_stock_items()}
            members_map = {m.id: m for m in db.get_members()}

            # Profit calculation
            total_profit = 0.0
            rows = []
            for s in sales:
                item = items_map.get(s.stock_item_id)
                mem = members_map.get(s.member_id) if s.member_id else None
                profit = (s.sale_price - (item.purchase_price if item else 0)) * s.quantity_sold
                total_profit += profit
                rows.append({
                    "Date": s.sale_date,
                    "Item": item.item_name if item else "—",
                    "Category": item.category if item else "—",
                    "Qty": s.quantity_sold,
                    "Sale Price (PKR)": f"{s.sale_price:,.2f}",
                    "Total (PKR)": f"{s.total_amount:,.2f}",
                    "Profit (PKR)": f"{profit:,.2f}",
                    "Member": mem.full_name if mem else "Walk-in",
                    "Sold By": s.sold_by or "—",
                })

            rc1, rc2, rc3 = st.columns(3)
            rc1.markdown(styles.metric_card("Total Sales", f"PKR {total_revenue:,.0f}",
                                            f"{len(sales)} transactions", "green"), unsafe_allow_html=True)
            rc2.markdown(styles.metric_card("Total Profit", f"PKR {total_profit:,.0f}",
                                            "Revenue - Cost", "blue"), unsafe_allow_html=True)
            margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            rc3.markdown(styles.metric_card("Profit Margin", f"{margin:.1f}%",
                                            "On inventory sales", "purple"), unsafe_allow_html=True)

            st.divider()
            df_sales = pd.DataFrame(rows)
            st.dataframe(df_sales, use_container_width=True, hide_index=True, height=350)

            if export_rep:
                buf = io.StringIO()
                df_sales.to_csv(buf, index=False)
                st.download_button("📥 Download", data=buf.getvalue().encode(),
                                   file_name=f"inventory_sales_{rep_from}_{rep_to}.csv",
                                   mime="text/csv", key="inv_download")

    # ── Add Item ───────────────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add New Stock Item")
        sel_gid_add = gym_selector("add")

        with st.form("add_stock_form", clear_on_submit=True):
            ac1, ac2 = st.columns(2)
            with ac1:
                item_name = st.text_input("Item Name *", placeholder="e.g. Whey Protein 1kg",
                                          key="as_name")
                category = st.selectbox("Category *", db.STOCK_CATEGORIES, key="as_category")
                purchase_price = st.number_input("Purchase Price (PKR) *",
                                                  min_value=0.0, step=1.0, key="as_buy")
            with ac2:
                sale_price = st.number_input("Sale Price (PKR) *",
                                              min_value=0.0, step=1.0, key="as_sell")
                quantity = st.number_input("Initial Quantity *", min_value=0, step=1, key="as_qty")
                min_qty = st.number_input("Low Stock Alert Threshold",
                                          min_value=0, step=1, value=5, key="as_min")

            if st.form_submit_button("✅ Add to Inventory", type="primary",
                                     use_container_width=True):
                if not item_name.strip():
                    st.error("Item name is required.")
                elif sale_price < purchase_price:
                    st.warning("⚠️ Sale price is less than purchase price — you'll be selling at a loss.")
                    ok, msg = db.add_stock_item(sel_gid_add, item_name, category,
                                                purchase_price, sale_price, quantity, min_qty)
                    st.success(msg) if ok else st.error(msg)
                else:
                    ok, msg = db.add_stock_item(sel_gid_add, item_name, category,
                                                purchase_price, sale_price, quantity, min_qty)
                    st.success(msg) if ok else st.error(msg)
