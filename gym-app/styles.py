GLOBAL_CSS = """
<style>
/* ── Layout ─────────────────────────────────────────────────── */
.main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
section[data-testid="stSidebar"] { background: #0F172A; border-right: 1px solid #1E293B; }

/* ── Metric Cards ────────────────────────────────────────────── */
.metric-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.75rem;
}
.metric-card .label {
    color: #94A3B8;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.metric-card .value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #E2E8F0;
    line-height: 1;
}
.metric-card .sub {
    font-size: 0.75rem;
    color: #64748B;
    margin-top: 0.25rem;
}
.metric-purple .value { color: #A78BFA; }
.metric-green  .value { color: #34D399; }
.metric-red    .value { color: #F87171; }
.metric-blue   .value { color: #60A5FA; }
.metric-amber  .value { color: #FBBF24; }

/* ── Status badges ───────────────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.badge-green  { background: #064E3B; color: #34D399; }
.badge-red    { background: #450A0A; color: #F87171; }
.badge-amber  { background: #451A03; color: #FBBF24; }
.badge-blue   { background: #0C1A3A; color: #60A5FA; }
.badge-gray   { background: #1E293B; color: #94A3B8; }

/* ── Page header ─────────────────────────────────────────────── */
.page-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #1E293B;
}
.page-header .icon { font-size: 1.8rem; }
.page-header h1 {
    font-size: 1.7rem;
    font-weight: 800;
    color: #E2E8F0;
    margin: 0;
}
.page-header .sub {
    color: #64748B;
    font-size: 0.85rem;
}

/* ── Table styles ────────────────────────────────────────────── */
.stDataFrame thead th { background: #1E293B !important; color: #7C3AED !important; font-weight: 700 !important; }
.stDataFrame tbody tr:hover td { background: #1E3A5F22 !important; }

/* ── Sidebar nav button ──────────────────────────────────────── */
.nav-btn button {
    background: transparent !important;
    border: none !important;
    color: #94A3B8 !important;
    font-size: 0.9rem !important;
    text-align: left !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 8px !important;
    transition: all 0.15s !important;
}
.nav-btn button:hover {
    background: #1E293B !important;
    color: #E2E8F0 !important;
}
.nav-btn-active button {
    background: #3B1B8C !important;
    color: #C4B5FD !important;
    font-weight: 700 !important;
}

/* ── WhatsApp link ───────────────────────────────────────────── */
.wa-link a {
    color: #34D399;
    font-weight: 600;
    text-decoration: none;
}
.wa-link a:hover { text-decoration: underline; }

/* ── Divider ─────────────────────────────────────────────────── */
hr { border-color: #1E293B !important; }

/* ── Responsive shrink ───────────────────────────────────────── */
@media (max-width: 768px) {
    .main .block-container { padding: 0.75rem 0.5rem; }
    .metric-card .value { font-size: 1.4rem; }
    .page-header h1 { font-size: 1.3rem; }
}
</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    # Belt-and-braces hide of Streamlit's auto page nav (the list that
    # showed "app / admin dashboard / attendance / …" derived from the
    # `pages/` folder). The config option `client.showSidebarNavigation`
    # already disables it, but this CSS ensures it stays hidden on older
    # Streamlit versions and through any future renames of the testid.
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarNavSeparator"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value, sub="", color=""):
    cls = f"metric-{color}" if color else ""
    return f"""
    <div class="metric-card {cls}">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        {"<div class='sub'>" + sub + "</div>" if sub else ""}
    </div>"""


def page_header(icon, title, sub=""):
    import streamlit as st
    st.markdown(f"""
    <div class="page-header">
        <span class="icon">{icon}</span>
        <div>
            <h1>{title}</h1>
            {"<div class='sub'>" + sub + "</div>" if sub else ""}
        </div>
    </div>""", unsafe_allow_html=True)


def badge(text, color="gray"):
    return f'<span class="badge badge-{color}">{text}</span>'

