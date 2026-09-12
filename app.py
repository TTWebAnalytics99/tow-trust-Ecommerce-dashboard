import os
import psycopg2
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="TT SWPTA", layout="wide")

DB_URI = st.secrets.get("DATABASE_URL") or os.getenv("DATABASE_URL")
API_KEY = st.secrets.get("PAGESPEED_API_KEY") or os.getenv("PAGESPEED_API_KEY", "")

def authenticate():
    auto_viewer = str(st.secrets.get("AUTO_LOGIN_VIEWER", "false")).lower() == "true"
    is_kiosk_url = st.query_params.get("mode") == "kiosk"

    if auto_viewer or is_kiosk_url:
        st.session_state["auth_ok"] = True
        st.session_state["role"] = "viewer"
        return

    def check():
        user_input = st.session_state.get("pass_input", "").strip()
        admin_pass = st.secrets.get("ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD")
        viewer_pass = st.secrets.get("VIEWER_PASSWORD") or os.getenv("VIEWER_PASSWORD", "viewer123")

        if admin_pass and user_input == str(admin_pass).strip():
            st.session_state["auth_ok"] = True
            st.session_state["role"] = "admin"
            del st.session_state["pass_input"]
        elif viewer_pass and user_input == str(viewer_pass).strip():
            st.session_state["auth_ok"] = True
            st.session_state["role"] = "viewer"
            del st.session_state["pass_input"]
        else:
            st.session_state["auth_ok"] = False

    if not st.session_state.get("auth_ok", False):
        st.subheader("🔒 Tow-Trust ECommerce Web Performance and Synthetic Testing Application")
        st.text_input("Enter Passkey", type="password", key="pass_input", on_change=check)
        if st.session_state.get("auth_ok") is False:
            st.error("Invalid credentials.")
        st.stop()

    with st.sidebar:
        role_label = "Administrator" if st.session_state.get("role") == "admin" else "Office Kiosk (Viewer)"
        st.write(f"Logged in as **{role_label}**")
        if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
            st.session_state["auth_ok"] = False
            st.session_state["role"] = None
            st.rerun()

authenticate()

def get_db_connection():
    return psycopg2.connect(DB_URI)

is_admin = st.session_state.get("role") == "admin"

if is_admin:
    tab_titles = ["📑 Executive Briefing", "📊 URL Vitals & Trends", "🎨 Asset Bottlenecks"]
else:
    tab_titles = ["📑 Executive Briefing", "📊 URL Vitals & Trends", "🎨 Asset Bottlenecks"]

tabs = st.tabs(tab_titles)

# TAB 1: EXECUTIVE BRIEFING
with tabs[0]:
    st.header("📑 Executive Core Web Vitals Briefing")
    st.caption("Live operational health evaluated against Google Core Web Vitals standards.")

    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM web_performance_logs WHERE recorded_at >= NOW() - INTERVAL '30 days' ORDER BY recorded_at ASC;", conn)

    if df.empty:
        st.info("No performance telemetry recorded yet.")
    else:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True)
        
        avg_lcp = (df["lcp_ms"] / 1000.0).mean()
        avg_tbt = df["tbt_ms"].mean()
        avg_cls = df["cls"].mean()
        sla_passes = len(df[(df["lcp_ms"] <= 2500) & (df["tbt_ms"] <= 200) & (df["cls"] <= 0.10)])
        sla_rate = (sla_passes / len(df)) * 100.0 if len(df) > 0 else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CWV Compliance Rate", f"{sla_rate:.1f}%", "Target: ≥ 90%")
        c2.metric("Avg LCP (Visual Speed)", f"{avg_lcp:.2f} s", "Target: ≤ 2.5s")
        c3.metric("Avg TBT (Interaction Delay)", f"{avg_tbt:.0f} ms", "Target: ≤ 200ms")
        c4.metric("Avg CLS (Stability)", f"{avg_cls:.3f}", "Target: ≤ 0.10")

# TAB 2: URL VITALS
with tabs[1]:
    st.header("📊 Historical URL Vitals")
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM web_performance_logs ORDER BY recorded_at ASC;", conn)

    if not df.empty:
        sel_url = st.selectbox("Select Target URL", df["target_url"].unique())
        filt = df[df["target_url"] == sel_url]
        fig = px.line(filt, x="recorded_at", y=["lcp_ms", "tbt_ms", "ttfb_ms"], title="Latency Evolution (ms)")
        st.plotly_chart(fig, use_container_width=True)

# TAB 3: ASSET BOTTLENECKS
with tabs[2]:
    st.header("🎨 Asset & Resource Bottlenecks")
    with get_db_connection() as conn:
        df_code = pd.read_sql_query("SELECT * FROM web_performance_logs ORDER BY recorded_at DESC LIMIT 1;", conn)
    if not df_code.empty:
        row = df_code.iloc[0]
        st.metric("Unoptimized Image Waste", f"{row.get('unoptimized_images_kb', 0):.1f} KB")
        st.metric("Unused CSS Payload", f"{row.get('unused_css_kb', 0):.1f} KB")
        st.metric("Third-Party Script Drag", f"{row.get('third_party_main_thread_ms', 0):.0f} ms")
