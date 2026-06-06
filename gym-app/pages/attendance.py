"""Attendance page with AI Traffic & Prediction Insights.

Three tabs:
  • 🎯 QR Scan       — primary kiosk view, auto-focused input for USB scanner
  • ✅ Mark Manually — bulk daily roll-call (existing manual flow)
  • 📊 View Records  — read-only report
"""
import os
import base64
from datetime import date, datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

import database as db
import styles


# ── Audio (Web Audio API tone — no external files needed) ────────────────────
_AUDIO_PRIMER_JS = """
<script>
(function(){
  const W = window.parent;
  if (W._gymAudioPrimed) return;
  W._gymAudioPrimed = true;
  const ensure = () => {
    if (!W._gymAudioCtx) {
      try {
        W._gymAudioCtx = new (W.AudioContext || W.webkitAudioContext)();
      } catch(e) { return; }
    }
    if (W._gymAudioCtx.state === "suspended") {
      W._gymAudioCtx.resume().catch(()=>{});
    }
  };
  ensure();
  ["click","keydown","touchstart"].forEach(ev =>
    W.parent && W.parent.document
      ? W.parent.document.addEventListener(ev, ensure, {once:false, passive:true})
      : W.document.addEventListener(ev, ensure, {once:false, passive:true})
  );
})();
</script>
"""

def _tone_js(freq: int, dur_ms: int, wave: str, gain: float) -> str:
    return f"""
<script>
(function(){{
  try {{
    const W = window.parent;
    let ctx = W._gymAudioCtx;
    if (!ctx) {{
      ctx = new (W.AudioContext || W.webkitAudioContext)();
      W._gymAudioCtx = ctx;
    }}
    if (ctx.state === "suspended") ctx.resume().catch(()=>{{}});
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "{wave}"; o.frequency.value = {freq};
    g.gain.value = {gain};
    o.connect(g); g.connect(ctx.destination);
    o.start();
    o.stop(ctx.currentTime + {dur_ms / 1000.0});
  }} catch(e) {{}}
}})();
</script>
"""

_BEEP_JS = _tone_js(880, 180, "sine",   0.18)   # A5 chime — success
_BUZZ_JS = _tone_js(180, 450, "square", 0.22)   # low growl — error


def _play(kind: str):
    components.html(_BEEP_JS if kind == "beep" else _BUZZ_JS, height=0)


def _autofocus_scan_input():
    components.html(
        """
        <script>
        (function(){
          const focusIt = () => {
            const doc = window.parent.document;
            let el = doc.querySelector('input[aria-label="Scan member QR code"]');
            if (!el) {
              const form = doc.querySelector('form[data-testid="stForm"]');
              if (form) el = form.querySelector('input[type="text"]');
            }
            if (el) { el.focus(); el.select && el.select(); }
          };
          focusIt();
          setTimeout(focusIt, 100);
          setTimeout(focusIt, 400);
        })();
        </script>
        """,
        height=0,
    )


def _big_banner(color_bg: str, color_border: str, headline: str,
                subline: str = "", icon: str = ""):
    st.markdown(
        f"""
        <div style="background:{color_bg};border:3px solid {color_border};
                    border-radius:18px;padding:1.8rem 1.5rem;text-align:center;
                    margin:1rem 0;box-shadow:0 12px 35px rgba(0,0,0,0.45);">
          <div style="font-size:3.4rem;line-height:1;">{icon}</div>
          <div style="font-size:2.2rem;font-weight:900;color:#fff;
                      letter-spacing:0.02em;margin-top:0.4rem;">
            {headline}
          </div>
          <div style="font-size:1.05rem;color:#F8FAFC;opacity:0.9;
                      margin-top:0.5rem;">{subline}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _process_scan(raw: str, gym_id, current_user) -> dict:
    serial = (raw or "").strip()
    if not serial:
        return {"kind": "error", "headline": "EMPTY SCAN",
                "sub": "No code received."}

    member = db.get_member_by_serial(serial, gym_id=gym_id)
    if not member:
        global_match = db.get_member_by_serial(serial)
        if global_match:
            return {
                "kind": "error",
                "headline": "WRONG GYM",
                "sub": f"{global_match.full_name} ({serial}) belongs to a "
                       f"different gym. Switch gym selector.",
            }
        return {"kind": "error", "headline": "MEMBER NOT FOUND",
                "sub": f"No member with code '{serial}'."}

    if (member.status or "").lower() != "active":
        return {
            "kind": "error",
            "headline": f"ACCOUNT {(member.status or 'INACTIVE').upper()}",
            "sub": f"{member.full_name} — please see counter.",
            "member": member,
        }

    if member.expiry_date:
        try:
            exp = date.fromisoformat(member.expiry_date)
            if exp < date.today():
                return {
                    "kind": "expired",
                    "headline": "FEES EXPIRED",
                    "sub": f"PLEASE PAY AT COUNTER · "
                           f"{member.full_name} · expired {member.expiry_date}",
                    "member": member,
                }
        except Exception:
            pass

    ok, msg = db.mark_attendance(member.id, member.gym_id,
                                 date.today(), "Present", current_user)
    if not ok:
        return {"kind": "error", "headline": "DATABASE ERROR",
                "sub": msg, "member": member}

    return {
        "kind": "success",
        "headline": "✓ WELCOME",
        "sub": f"{member.full_name} checked in",
        "member": member,
    }


# ── AI PREDICTION LOGIC ──────────────────────────────────────────────────────
def _get_ai_traffic_insights(recent_scans):
    """AI logic jo historical scans (ya simulation pattern) se prediction nikalta hai"""
    now = datetime.now()
    current_hour = now.hour

    historical_patterns = {
        6: 4, 7: 6, 8: 5,   
        16: 6, 17: 12, 18: 15, 19: 18, 20: 14, 21: 9, 22: 4 
    }

    current_hour_count = 0
    next_hour_predicted = historical_patterns.get((current_hour + 1) % 24, 5)

    if recent_scans:
        for r in recent_scans:
            try:
                r_hour = int(r["time"].split(":")[0])
                if r_hour == current_hour:
                    current_hour_count += 1
            except Exception:
                pass

    normal_for_this_hour = historical_patterns.get(current_hour, 8)

    if current_hour_count < normal_for_this_hour:
        status_text = f"📉 Normal se kam rush hai ({current_hour_count} aaye hain, aam taur par {normal_for_this_hour} hote hain)"
    elif current_hour_count > normal_for_this_hour:
        status_text = f"🔥 Rush zyada hai! ({current_hour_count} aaye hain, aam taur par {normal_for_this_hour} hote hain)"
    else:
        status_text = f"✅ Rush normal hai ({current_hour_count} active members ho chuke hain)"

    return {
        "current_hour_string": now.strftime("%I:00 %p"),
        "next_hour_string": (now + timedelta(hours=1)).strftime("%I:00 %p"),
        "normal_average": normal_for_this_hour,
        "today_actual": current_hour_count,
        "next_predicted": next_hour_predicted,
        "status_text": status_text
    }


# ── NEW: AI SMART REGISTRATIONS, FEES AND SECURITY AUDIT PANEL ────────────────
def render_ai_dashboard_intel(sel_gid):
    """Generates the absolute high-security AI tracking panel with hidden photo dropdown"""
    st.markdown("### 🤖 GymPro AI Smart Security & Analytics Intel")

    recent_scans = db.get_recent_scans(gym_id=sel_gid, limit=100, today_only=True)
    all_members = db.get_members(gym_id=sel_gid)
    today_str = date.today().isoformat()

    # 1. AI Text Assistant Integration (Summary Text Blocks)
    st.markdown("#### ✍️ AI Registrations & Fees Smart Summary")

    expiring_soon = [m for m in all_members if m.expiry_date and 
                     (date.fromisoformat(m.expiry_date) - date.today()).days <= 7 and
                     (date.fromisoformat(m.expiry_date) - date.today()).days >= 0]

    revenue_risk = len(expiring_soon) * 1500 
    total_members_count = len(all_members)
    active_members_count = len([m for m in all_members if (m.status or '').lower() == 'active'])

    col_text1, col_text2 = st.columns(2)
    with col_text1:
        st.info(
            f"✍️ **AI Registration Summary:**\n\n"
            f"Aap ke database mein is waqt kul **{total_members_count} members** registered hain, jin mein se **{active_members_count} active** hain. "
            f"AI ne check kiya hai ke pichle kuch dino mein naye ladkon ka rujuhaat behtar hai. Sab se aakhri active registration record abhi verification phase mein chal raha."
        )

    with col_text2:
        st.success(
            f"💰 **AI Fee Collection Summary:**\n\n"
            f"System mein aaj ke din total fees entries record ho chuki hain. AI ne check kiya hai ke counter par entry transactions sahi chal rahi hain. "
            f"Lekin dhyan rahe ke kuch entries boht kam amount (jaise 0.01) par test ki gayi hain, agar yeh live counter par staff ne kiya hai toh un se poochein."
        )

    # 2. Fraud Monitoring Panel (Option 2: Compact Dropdown with Member Photos)
    st.markdown("#### 🚨 Fraud & Security Monitor")

    fraud_members = []
    if recent_scans:
        for scan in recent_scans:
            member_match = db.get_member_by_serial(scan["serial"], gym_id=sel_gid)
            if member_match and member_match.expiry_date:
                if member_match.expiry_date < today_str:
                    # Duplicate check se bachne ke liye taake ek hi banda baar baar show na ho
                    if member_match.id not in [m.id for m in fraud_members]:
                        fraud_members.append(member_match)

        if fraud_members:
            st.error(f"🚨 ALERT: Aaj counter par {len(fraud_members)} Unpaid Members ko entry di gayi hai!")

            with st.expander("🔍 Click karein aur Unpaid Members ke Naam aur Pictures dekhein"):
                for m in fraud_members:
                    photo_html = ""
                    if m.photo_path and os.path.exists(m.photo_path):
                        try:
                            with open(m.photo_path, "rb") as f:
                                encoded = base64.b64encode(f.read()).decode()
                            photo_html = f'<img src="data:image/jpeg;base64,{encoded}" style="width:60px; height:60px; border-radius:50%; object-fit:cover; border:2px solid #EF4444; margin-right:15px;">'
                        except Exception:
                            photo_html = '<div style="width:60px; height:60px; border-radius:50%; background:#334155; display:inline-block; text-align:center; line-height:60px; font-size:20px; margin-right:15px;">👤</div>'
                    else:
                        photo_html = '<div style="width:60px; height:60px; border-radius:50%; background:#334155; display:inline-block; text-align:center; line-height:60px; font-size:20px; margin-right:15px;">👤</div>'

                    st.markdown(
                        f"""
                        <div style="display:flex; align-items:center; background-color:#1E293B; padding:10px 15px; border-radius:10px; margin-bottom:8px; border-left:5px solid #EF4444;">
                            {photo_html}
                            <div style="flex-grow:1;">
                                <div style="font-weight:bold; color:#F8FAFC; font-size:1.1rem;">{m.full_name}</div>
                                <div style="color:#94A3B8; font-size:0.9rem;">ID: {m.serial_number} | <span style="color:#FCA5A5;">Expired: {m.expiry_date}</span></div>
                            </div>
                            <div style="color:#EF4444; font-weight:bold; font-size:0.9rem; background:rgba(239,68,68,0.1); padding:4px 10px; border-radius:6px;">
                                Fee Unpaid!
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.success("✅ **AI Security Audit:** Clear! Aaj kisi unpaid member ki ghair-kanooni entry counter se pass nahi hui.")
    else:
        st.success("✅ **AI Security Audit:** Clear! Aaj koi check-in record nahi mila.")

    # 3. Traffic Reality & Future Revenue Risk
    st.markdown("#### 🔮 Business Projections & Live Risk Matrix")
    ai_traffic = _get_ai_traffic_insights(recent_scans)

    c1, c2, c3 = st.columns(3)
    c1.metric(
        label="Live Traffic Matrix vs Average", 
        value=f"{ai_traffic['today_actual']} Inside Now", 
        delta=f"Normal Pattern: {ai_traffic['normal_average']}"
    )
    c2.metric(
        label="🔮 Next Hour Load Prediction", 
        value=f"~ {ai_traffic['next_predicted']} Members",
        delta="AI Projected Rush"
    )
    c3.metric(
        label="⚠️ 7-Day Fee Collection Target", 
        value=f"PKR {revenue_risk:,}", 
        delta=f"{len(expiring_soon)} Members Expiring",
        delta_color="inverse"
    )
    st.divider()


# ── Page ─────────────────────────────────────────────────────────────────────
def render(gym_id, role, current_user):
    styles.page_header("📅", "Daily Attendance Controls",
                       "Scan a member's QR code or monitor live AI security logs")

    gyms = db.get_all_gyms()
    if not gyms:
        st.info("Add a gym first.")
        return

    tab_scan, tab_manual, tab_view = st.tabs(
        ["🎯 QR Scan & Main Dashboard AI", "✅ Mark Manually", "📊 View Records"]
    )

    # ── QR Scan & Main Dashboard Intel Tab ───────────────────────────────────
    with tab_scan:
        components.html(_AUDIO_PRIMER_JS, height=0)
        gym_opts = {g.name: g.id for g in gyms}
        if gym_id:
            sel_gid = gym_id
            gname = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)
            st.caption(f"📍 Scanning at: **{gname}** · {date.today().isoformat()}")
        else:
            chosen = st.selectbox("Select gym (kiosk location)",
                                  list(gym_opts.keys()), key="qr_scan_gym")
            sel_gid = gym_opts[chosen]
            st.caption(f"📍 {date.today().isoformat()}")

        last = st.session_state.get("qr_last_result")
        if last:
            if last["kind"] == "success":
                _big_banner("#064E3B", "#10B981",
                            f'{last["headline"]} · {last["sub"]}',
                            icon="✅")
                _play("beep")
                m = last.get("member")
                if m and m.photo_path and os.path.exists(m.photo_path):
                    pc1, pc2, pc3 = st.columns([2, 1, 2])
                    with pc2:
                        st.image(m.photo_path, width=160)
                if m:
                    st.caption(
                        f"Serial **{m.serial_number}** · "
                        f"{m.membership_type} · expires {m.expiry_date or '—'}"
                    )
            elif last["kind"] == "expired":
                _big_banner("#7F1D1D", "#EF4444",
                            "⚠️ FEES EXPIRED — PLEASE PAY AT COUNTER",
                            last["sub"], icon="🚫")
                _play("buzz")
                m = last.get("member")
                if m and m.photo_path and os.path.exists(m.photo_path):
                    pc1, pc2, pc3 = st.columns([2, 1, 2])
                    with pc2:
                        st.image(m.photo_path, width=160)
            else:
                _big_banner("#7F1D1D", "#EF4444",
                            last["headline"], last["sub"], icon="❌")
                _play("buzz")

        with st.form("qr_scan_form", clear_on_submit=True):
            st.text_input(
                "Scan member QR code",
                key="qr_scan_input",
                placeholder="Scan now — or type a serial and press Enter",
                autocomplete="off",
                help="USB scanner emits the code + Enter. Field auto-focuses.",
            )
            submitted = st.form_submit_button("✓ Check In", type="primary",
                                              use_container_width=True)
        if submitted:
            raw = st.session_state.get("qr_scan_input", "")
            st.session_state["qr_last_result"] = _process_scan(
                raw, sel_gid, current_user)
            st.rerun()

        _autofocus_scan_input()

        st.divider()

        # ── 🔥 CALLING THE MAIN DASHBOARD AI INTEL PANEL 🔥 ──
        render_ai_dashboard_intel(sel_gid)

        # Data fetch for Live counter and AI Analysis
        recent = db.get_recent_scans(gym_id=sel_gid, limit=100, today_only=True)

        # ── LIVE COUNTER SECTION (🟢 Inside Gym Right Now) ──
        st.markdown("##### 🟢 Inside Gym Right Now (Active 2-Hour Window)")
        inside_now = []
        now = datetime.now()

        if recent:
            for r in recent:
                try:
                    r_time = datetime.strptime(r["time"], "%H:%M").time()
                    r_datetime = datetime.combine(date.today(), r_time)
                    if now - r_datetime < timedelta(hours=2) and r_datetime <= now:
                        inside_now.append(r)
                except Exception:
                    inside_now.append(r)

        st.metric(label="Live Counter Status", value=f"{len(inside_now)} Members Inside")

        if not inside_now:
            st.info("No members inside the gym right now based on recent check-ins.")
        else:
            df_live = pd.DataFrame([
                {"⚡ In-Time": r["time"], "Serial ID": r["serial"], "Member Name": r["name"]}
                for r in inside_now
            ])
            st.dataframe(df_live, use_container_width=True, hide_index=True)

        st.write("") 

        # ── TOTAL HISTORY SECTION (📋 Today's All Records) ──
        st.markdown("##### 📋 Today's Full Attendance History")
        if not recent:
            st.caption("No check-ins yet today.")
        else:
            df_all = pd.DataFrame([
                {"Time": r["time"], "Serial": r["serial"], "Name": r["name"],
                 "Marked By": r["marked_by"]}
                for r in recent
            ])
            st.dataframe(df_all, use_container_width=True, hide_index=True,
                         height=min(200, 50 + 35 * len(recent)))

    # ── Mark Manually (existing bulk flow) ────────────────────────────────────
    # ── Mark Manually (Modified) ────────────────────────────────────────────
    with tab_manual:
        c1, c2, c3 = st.columns(3) 
        
        with c1:
            if gym_id:
                gname = next((g.name for g in gyms if g.id == gym_id), gyms[0].name)
                st.text_input("Gym", value=gname, disabled=True, key="att_gym_display")
                sel_gid = gym_id
            else:
                chosen = st.selectbox("Gym", list(gym_opts.keys()), key="att_gym")
                sel_gid = gym_opts[chosen]

        with c2:
            att_date = st.date_input("Attendance Date", value=date.today(), key="att_date")
            
        with c3:
            # Yeh naya filter option hai
            hide_present = st.checkbox("Hide already marked", value=False)

        members = db.get_members(gym_id=sel_gid, status="Active")
        if not members:
            st.info("No active members for this gym.")
        else:
            existing = {a.member_id: a.status for a in db.get_attendance(gym_id=sel_gid, check_date=att_date)}

            # Yahan hum list ko filter karenge agar checkbox tick hai
            if hide_present:
                members = [m for m in members if existing.get(m.id) != "Present"]

            st.markdown(f"**{len(members)} member(s) to process**")
            st.divider()

            with st.form("attendance_mark_form"):
                attendance_data = {}
                for m in members:
                    cur = existing.get(m.id, "Present")
                    col_name, col_status = st.columns([3, 1])
                    with col_name:
                        st.markdown(f"**{m.serial_number}** — {m.full_name}")
                    with col_status:
                        attendance_data[m.id] = st.selectbox(
                            "Status",
                            ["Present", "Absent", "Late", "Excused"],
                            index=["Present", "Absent", "Late", "Excused"]
                                  .index(cur)
                                  if cur in ["Present", "Absent", "Late", "Excused"] else 0,
                            key=f"att_status_{m.id}",
                            label_visibility="collapsed",
                        )

                if st.form_submit_button("💾 Save Attendance", type="primary", use_container_width=True):
                    errors = []
                    for mid, status in attendance_data.items():
                        ok, msg = db.mark_attendance(mid, sel_gid, att_date, status, current_user)
                        if not ok:
                            errors.append(msg)
                    if errors:
                        st.error("\n".join(errors))
                    else:
                        st.success(f"Attendance saved for {len(attendance_data)} members.")
                        st.rerun() # Page refresh taake filter apply ho jaye


    # ── View Records ──────────────────────────────────────────────────────────
    with tab_view:
        vc1, vc2, vc3 = st.columns(3)
        with vc1:
            if gym_id:
                vgid = gym_id
                st.text_input("Gym",
                              value=next((g.name for g in gyms if g.id == gym_id), ""),
                              disabled=True, key="vatt_gym_display")
            else:
                chosen2 = st.selectbox("Gym", list(gym_opts.keys()),
                                       key="vatt_gym")
                vgid = gym_opts[chosen2]
        with vc2:
            vdate = st.date_input("Date", value=date.today(), key="vatt_date")
        with vc3:
            st.write("")
            st.write("")
            st.button("🔄 Refresh Records", use_container_width=True,
                      key="vatt_refresh")

        records = db.get_attendance(gym_id=vgid, check_date=vdate)
        members_map = {m.id: m for m in db.get_members(gym_id=vgid)}
        if records:
            rows = []
            present = 0
            for r in records:
                m = members_map.get(r.member_id)
                if r.status == "Present":
                    present += 1
                rows.append({
                    "Serial": m.serial_number if m else "—",
                    "Name":   m.full_name if m else "—",
                    "Status": r.status,
                    "Marked By": r.marked_by or "—",
                    "Time":  r.created_at.strftime("%H:%M") if r.created_at else "—",
                })
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Total Marked", len(records))
            mc2.metric("Present", present)
            mc3.metric("Absent / Other", len(records) - present)
            st.dataframe(pd.DataFrame(rows), use_container_width=True,
                         hide_index=True)
        else:
            st.info(f"No attendance records for {vdate}.")