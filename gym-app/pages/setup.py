import streamlit as st
import database as db
import styles


def render():
    styles.page_header("⚙️", "Gym Setup", "Create and manage your gym locations")

    # ── Add New Gym ────────────────────────────────────────────────────────────
    with st.expander("➕ Add New Gym", expanded=False):
        with st.form("add_gym_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Gym Name *", placeholder="e.g. PowerFit Downtown")
                phone = st.text_input("Phone", placeholder="+1 555-0000")
            with c2:
                address = st.text_input("Address", placeholder="123 Main Street, City")
                email = st.text_input("Email", placeholder="info@gym.com")
            submitted = st.form_submit_button("Add Gym", type="primary", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("Gym name is required.")
                else:
                    ok, msg = db.add_gym(name, address, phone, email)
                    st.success(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()

    st.divider()

    gyms = db.get_all_gyms()
    st.markdown(f"**{len(gyms)} Gym(s) Configured**")

    if not gyms:
        st.info("No gyms yet. Use the form above to add your first gym.")
        return

    for g in gyms:
        stats = db.get_stats(g.id)
        with st.expander(f"🏋️ **{g.name}**  ·  {stats['active_members']} active members  ·  PKR {stats['total_revenue']:,.0f} revenue"):
            col_form, col_stats, col_danger = st.columns([3, 2, 1])

            with col_form:
                with st.form(f"edit_gym_{g.id}"):
                    st.markdown("**Edit Details**")
                    new_name = st.text_input("Name *", value=g.name, key=f"n_{g.id}")
                    new_addr = st.text_input("Address", value=g.address or "", key=f"a_{g.id}")
                    new_phone = st.text_input("Phone", value=g.phone or "", key=f"p_{g.id}")
                    new_email = st.text_input("Email", value=g.email or "", key=f"e_{g.id}")
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        if not new_name.strip():
                            st.error("Name required.")
                        else:
                            ok, msg = db.update_gym(g.id, new_name, new_addr, new_phone, new_email)
                            st.success(msg) if ok else st.error(msg)
                            if ok:
                                st.rerun()

            with col_stats:
                st.markdown("**Statistics**")
                st.markdown(styles.metric_card("Total Members", stats["total_members"], color="purple"), unsafe_allow_html=True)
                st.markdown(styles.metric_card("Active", stats["active_members"], color="green"), unsafe_allow_html=True)
                st.markdown(styles.metric_card("All-time Revenue", f"PKR {stats['total_revenue']:,.0f}", color="blue"), unsafe_allow_html=True)
                st.markdown(styles.metric_card("All-time Expenses", f"PKR {stats['total_expenses']:,.0f}", color="red"), unsafe_allow_html=True)

            with col_danger:
                st.markdown("**Danger Zone**")
                st.warning("Deleting removes ALL members & data.")
                if st.button("🗑️ Delete Gym", key=f"del_{g.id}"):
                    st.session_state[f"confirm_gym_{g.id}"] = True

                if st.session_state.get(f"confirm_gym_{g.id}"):
                    st.error(f"Permanently delete **{g.name}**?")
                    if st.button("✅ Confirm Delete", key=f"cyes_{g.id}", type="primary"):
                        db.delete_gym(g.id)
                        st.success("Gym deleted.")
                        st.session_state.pop(f"confirm_gym_{g.id}", None)
                        st.rerun()
                    if st.button("Cancel", key=f"cno_{g.id}"):
                        st.session_state.pop(f"confirm_gym_{g.id}", None)
                        st.rerun()
